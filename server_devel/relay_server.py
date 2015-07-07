import serial
import os
import time
import logging
import threading
import Pyro4


class relayServer():

# This server will register in pyro namespace, and push commands to the relay controller.

    def __init__(self, serial_port='/dev/ttyACM0'):
        self.data = {'group':'relay'}
        self.setup_logger()
        self.serial_port = serial_port
        self.baudrate = 9600
        
        self.relay_server_lock = threading.Lock()
        # used to make sure the send commands and the do_loop don't collide.
        # We have had issues with collisions before.
        
        self.status = 'unknown'
        self.last_status = 'open'
        self.loop_thread=None
        
    def fetch_dict(self):
        return self.data
        
    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                self.logger.warning("loop already running")
                return
        self.loop_thread=threading.Thread(target=self.do_loop)
        self.loop_thread.daemon=True
        self.loop_thread.start()
        
    def do_loop(self):
        while True:
            self.relay_server_lock.acquire()
            try:    
                try:
                    raw_data = self.get_raw_integers()
                    keys = ['regulate_active', 'mag_current_active', 'touch_50mk',
                            'touch_1k', 'touch_50k', 'hs_opening', 'hs_closing']
                    for i in range(len(raw_data)):
                        self.data[keys[i]]=raw_data[i]
                    # Need to turn status into a value convertable to a float for data logging:
                    if self.status == 'open':
                        self.data['heat_switch_status'] = 1
                    elif self.status == 'closed':
                        self.data['heat_switch_status'] = 0
                    else:
                        self.data['heat_switch_status'] = -1
                    
                except Exception as e:
                    self.logger.error('ERROR ENCOUNTERED. Loop ended and will start from the beginning after normal wait period.')
                    self.logger.error(e)
                self.data['time']=time.time()
            finally:
                self.relay_server_lock.release()
            time.sleep(5)
        
    def setup_logger(self,base_dir='/data/adc/cooldown_logs/server_logs/relay_server_logs',suffix=''):
        base_dir=os.path.expanduser(base_dir)
        
        fn=time.strftime('%Y-%m-%d_%H-%M-%S')
        if suffix:
            suffix=suffix.replace(' ','_')
            fn+=('_'+suffix)
        fn+='.log'
        fn = os.path.join(base_dir,fn)
        self.filename=fn
        # Creates filename based on timestamp (year,month,day,hr,min,sec,suffix)
        
        self.logger=logging.getLogger('relay_logger')
        self.logger.setLevel(logging.DEBUG)
        self.formatter=logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.file_handler=logging.FileHandler(filename=fn)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        self.logger.info('Logger started.')
        
    def send(self, msg):
        ser = serial.Serial(self.serial_port, baudrate=self.baudrate)
        try:
            ser.write(msg)
            self.logger.info('Sent message %s' % msg)
        except Exception as e:
            print e
            raise e
        finally:
            ser.close()
            
    def read_until_terminator(self, ser):
        message = ''
        new_char = None
        while new_char != '\n':
            new_char = ser.read(1)
            if new_char == '':
                print 'Serial port timed out while reading.'
                break
            message += new_char
        return message
            
    def send_and_receive(self, msg):
        ser = serial.Serial(self.serial_port, baudrate=self.baudrate)
        try:
            ser.write(msg)
            self.logger.info('Sent message %s' % msg)
            response = self.read_until_terminator(ser)
            self.logger.info('Read message %s' % response)
            return response
        except Exception as e:
            print e
            raise e
        finally:
            ser.close()
            
    def insert_resistor_for_regulate(self):
        self.relay_server_lock.acquire()
        try:
            self.logger.info('Tried inserting resistor for regulate.')
            self.send('a')
            check = self.get_raw_integers()
            if check[0] != 1:
                self.logger.info('Failed at inserting resistor for regulate.')
                return False
            self.logger.info('Succeeded at inserting resistor for regulate.')
            return True
        finally:
            self.relay_server_lock.release()
            
    def remove_resistor_for_mag_cycle(self):
        self.relay_server_lock.acquire()
        try:
            self.logger.info('Tried removing resistor for mag cycle.')
            self.send('b')
            check = self.get_raw_integers()
            if check[0] != 0:
                self.logger.info('Failed at removing resistor for mag cycle.')
                return False
            self.logger.info('Succeeded at removing resistor for mag cycle.')
            return True
        finally:
            self.relay_server_lock.release()
        
    def switch_to_magnet_current_pid_control(self):
        self.relay_server_lock.acquire()
        try:
            self.logger.info('Tried switching pid control to magnet current.')
            self.send('c')
            check = self.get_raw_integers()
            if check[1] != 1:
                self.logger.info('Failed at switching pid control to magnet current.')
                return False
            self.logger.info('Succeeded at switching pid control to magnet current.')
            return True
        finally:
            self.relay_server_lock.release()
        
    def switch_to_bridge_temp_pid_control(self):
        self.relay_server_lock.acquire()
        try:
            self.logger.info('Tried switching pid control to bridge temp.')
            self.send('d')
            check = self.get_raw_integers()
            if check[1] != 0:
                self.logger.info('Failed at switching pid control to bridge temp.')
                return False
            self.logger.info('Succeeded at switching pid control to bridge temp.')
            return True
        finally:
            self.relay_server_lock.release()
    
    def get_raw_integers(self):
        raw = self.send_and_receive('s')
        raw = raw.strip('\n')
        if len(raw) > 7:
            # If we got overloaded, just return invalid data.
            return [-1]*7
        raw_integers = []
        for character in raw[:2]:
            if character == '1':
                raw_integers.append(int(character))
            elif character == '0':
                raw_integers.append(int(character))
            else:
                # Data is invalid - return -1.
                raw_integers.append(-1)
                
        # For the remaining characters we have backwards logic because we use a pullup.
        # This code fixes it to be what we would expect (false = 0, true = 1)
                
        for character in raw[2:]:
            if character == '1':
                raw_integers.append(0)
            elif character == '0':
                raw_integers.append(1)
            else:
                # Data is invalid - return -1.
                raw_integers.append(-1)
        return raw_integers
        
    def open_heat_switch(self):
        # send heat_switch open command
        self.relay_server_lock.acquire()
        try:
            self.logger.info('Tried opening heat switch.')
            if self.status == 'open':
                self.logger.info('Heat switch is already open.')
                return True
            self.send('e')
            check = self.get_raw_integers()
            if check[5] != 1:
                if self.status == 'unknown':
                    # We assume the heatswitch was already open.
                    self.logger.info('Heat switch status changed from unknown to open.')
                    self.status = 'open'
                    return True
                self.logger.info('Failed to open heat switch.')
                return False
            self.logger.info('Succeeded at opening heat switch.')
            self.status = 'open'
            return True
        finally:
            self.relay_server_lock.release()
        
    def close_heat_switch(self):
        # send heat_switch open command
        self.relay_server_lock.acquire()
        try:
            self.logger.info('Tried closing heat switch.')
            if self.status == 'closed':
                self.logger.info('Heat switch is already closed.')
                return True
            self.send('f')
            check = self.get_raw_integers()
            if check[6] != 1:
                if self.status == 'unknown':
                    # We assume the heatswitch was already closed.
                    self.logger.info('Heat switch status changed from unknown to closed.')
                    self.status = 'closed'
                    return True
                self.logger.info('Failed to close heat switch.')
                return False
            self.logger.info('Succeeded at closing heat switch.')
            self.status = 'closed'
            return True
        finally:
            self.relay_server_lock.release()

def main():
    relay = relayServer()
    relay.start_loop_thread()
    Pyro4.Daemon.serveSimple(
        {
            relay: 'relayserver'
        },
        ns=True,# PYRO_MULTITHREADING=0
        )
        
if __name__ == '__main__':
    main()
