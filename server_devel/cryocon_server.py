import Pyro4
import sim900_communicator
import threading
import os
import time
import logging
import numpy as np

float_params = [('SYSTEM:HTRH?','heatsink_temp'),
                ('SYSTEM:AMBIENT?','ambient_temp'),
                ('INPUT A:TEMP?', 'input_a_temp'),
                ('INPUT B:TEMP?', 'input_b_temp'),
                ('INPUT A:SENPR?', 'input_a_raw'),
                ('INPUT B:SENPR?', 'input_b_raw'),
                ('LOOP 1:SETPT?','loop_1_setpoint'),
                ('LOOP 2:SETPT?','loop_2_setpoint'),
                ('LOOP 1:OUTPWR?','loop_1_output'),
                ('LOOP 2:OUTPWR?','loop_2_output'),
                ]

class CryoconServer():

# This server will register in pyro namespace, continuously run, and push commands from adr_controller to the sim900.

    def __init__(self):
        self.data={'group':'cryocon'}

        self.communicator_lock=threading.Lock()

        self.communicator=sim900_communicator.CleanComm(self.communicator_lock,port=4002)
        # Start up to connect to real sim900


        self.setup_logger()

        self.check_communication()

        self.loop_thread=None
        self.start_loop_thread()

    def check_communication(self):
        result = self.send_get("*IDN?")
        self.logger.info("identification request response: %s" % repr(result))

    def setup_logger(self,base_dir='/data/adc/cooldown_logs/server_logs/cryocon_server_logs',
                     suffix=''):
        base_dir=os.path.expanduser(base_dir)

        fn=time.strftime('%Y-%m-%d_%H-%M-%S')
        if suffix:
            suffix=suffix.replace(' ','_')
            fn+=('_'+suffix)
        fn+='.log'
        fn = os.path.join(base_dir,fn)
        self.filename=fn
        # Creates filename based on timestamp (year,month,day,hr,min,sec,suffix)

        self.logger=logging.getLogger('sim900_logger')
        self.logger.setLevel(logging.DEBUG)
        self.formatter=logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.file_handler=logging.FileHandler(filename=fn)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        self.logger.info('Logger started.')

    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                self.logger.warning("loop already running")
                return
        self.loop_thread=threading.Thread(target=self.update_data)
        self.loop_thread.daemon=True
        self.loop_thread.start()

    def update_data(self):
        while True:
            try:
                tic=time.time()
                for msg,name in float_params:
                    response = self.send_get(msg)
                    if response.startswith('.'):
                        value = -1
                    try:
                        value = float(response)
                    except ValueError:
                        try:
                            value = float(response[:-1])
                        except:
                            value = -1
                    self.data[name] = value
#                response = self.send_get("LOOP 1:TYPE?")
#                self.data['loop_1_status'] = response
#                response = self.send_get("LOOP 2:TYPE?")
#                self.data['loop_2_status'] = response
                toc=time.time()
                self.logger.info('Updating values took %.3f seconds'%(toc-tic))
            except Exception as e:
                self.logger.error('ERROR ENCOUNTERED. Loop ended and will start from the beginning after normal wait period.')
                self.logger.error(e)
            self.data['time']=time.time()
            time.sleep(1)

    def send_get(self,msg):
        return self.communicator.fast_send_and_receive(msg,terminator='\n',end_of_response='\n')

    def get_data(self):
        return self.data


def main():
    cryocon=CryoconServer()
    Pyro4.Daemon.serveSimple(
            {
                cryocon : "cryocon"
            },
            ns=True)

if __name__=="__main__":
    main()
