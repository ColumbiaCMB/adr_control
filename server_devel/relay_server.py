import serial
import os
import time
import logging
import threading
import Pyro4


class relayServer():

# This server will register in pyro namespace, and push commands to the relay controller.

    def __init__(self, serial_port='/dev/ttyACM1'):
        self.data = {'group':'relay'}
        self.setup_logger()
        self.serial_port = serial_port
        self.baudrate = 9600
        self.status = 'open'
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
            try:
                raw_data = self.get_raw_integers()
                keys = ['regulate_active', 'mag_current_active', 'touch_50mk',
                        'touch_1k', 'touch_50k', 'hs_opening', 'hs_closing']
                for i in range(len(raw_data)):
                    self.data[keys[i]]=raw_data[i]
                    
                if self.data['hs_opening'] == 1:
                    self.status = 'opening'
                    self.last_status = 'opening'
                elif self.data['hs_closing'] == 1:
                    self.status = 'closing'
                    self.last_status = 'closing'
                else:
                    if self.last_status == 'opening':
                        self.status = 'open'
                        self.last_status = 'open'
                    elif self.last_status == 'closing':
                        self.status = 'closed'
                        self.last_status = 'open'
                    else:
                        self.last_status = self.status
                self.data['status'] = self.status
                
            except Exception as e:
                self.logger.error('ERROR ENCOUNTERED. Loop ended and will start from the beginning after normal wait period.')
                self.logger.error(e)
            self.data['time']=time.time()
            print self.data
            time.sleep(5)
        
    def setup_logger(self,base_dir='/home/adclocal/data/garbage_cooldown_logs/server_logs/relay_server_logs',suffix=''):
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
       
   def regulate_switch(self):
        self.send('a')
        check = self.get_raw_integers()
        if check[0] != 1:
            return False
        return True
            
    def mag_cycle_switch(self):
        self.send('b')
        check = self.get_raw_integers()
        if check[0] != 0:
            return False
        return True
        
    def current_pid_switch(self):
        self.send('c')
        check = self.get_raw_integers()
        if check[1] != 1:
            return False
        return True
        
    def temp_pid_switch(self):
        self.send('d')
        if check[1] != 0:
            return False
        return True
    
    def get_raw_integers(self):
        raw = self.send_and_receive('s')
        raw = raw.strip('\n')
        if len(raw) > 7:
            # If we got overloaded, just return invalid data.
            return [-1]*7
        raw_integers = []
        for character in raw:
            if character == '1':
                raw_integers.append(int(character))
            elif character == '0':
                raw_integers.append(int(character))
            else:
                # Data is invalid - return -1.
                raw_integers.append(-1)
        return raw_integers
        
    def open_heat_switch(self):
        # send heat_switch open command
        pass
        
    def close_heat_switch(self):
        # send heat_switch open command
        pass

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
