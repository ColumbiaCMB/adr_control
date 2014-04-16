import threading
import numpy as np
import os
import logging
import time
import Pyro4
import sim900_communicator
# Includes methods for talking using sockets
import smdp
# Includes method to add per and post hash characters to give the cryomech readable characters.
# Note that I understand how it creates the premessage (it should always be '\x02\x10\x80\x63' where '\x10' is the address (16 in characters) and '\x63' is the query request.
# The postmessage is first an incrementing (in hex) character. The next two characters are a checksum that verifies the message. All of this calculation is taken care of in smdp.

default_query_dictionary=[
                                        {'hashcode':'\x63\x45\x4c\x00','name':"comp_minutes",'scaling':1.0},
                                        {'hashcode':'\x63\x35\x74\x00','name':"cpu_temp",'scaling':1.0},
                                        {'hashcode': '\x63\x0D\x8F\x00','name':"temp_water_in",'scaling':1.0},
                                        {'hashcode':'\x63\x0D\x8F\x01','name':"temp_water_out",'scaling':1.0},
                                        {'hashcode':'\x63\x0D\x8F\x02','name':"temp_helium",'scaling':1.0},
                                        {'hashcode':'\x63\x0D\x8F\x03','name':"temp_oil",'scaling':1.0},
                                        {'hashcode':'\x63\x6E\x58\x00','name':"min_temp_water_in",'scaling':1.0},
                                        {'hashcode':'\x63\x6E\x58\x01','name':"min_temp_water_out",'scaling':1.0},
                                        {'hashcode':'\x63\x6E\x58\x02','name':"min_temp_helium",'scaling':1.0},
                                        {'hashcode':'\x63\x6E\x58\x03','name':"min_temp_oil",'scaling':1.0},
                                        {'hashcode':'\x63\x8A\x1C\x00','name':"max_temp_water_in",'scaling':1.0},
                                        {'hashcode':'\x63\x8A\x1C\x01','name':"max_temp_water_out",'scaling':1.0},
                                        {'hashcode':'\x63\x8A\x1C\x02','name':"max_temp_helium",'scaling':1.0},
                                        {'hashcode':'\x63\x8A\x1C\x03','name':"max_temp_oil",'scaling':1.0},
                                        {'hashcode':'\x63\x6E\x2D\x00','name':"temp_error",'scaling':1.0},
                                        {'hashcode':'\x63\xA3\x7A\x00','name':"batt_ok",'scaling':1.0},
                                        {'hashcode':'\x63\x0B\x8B\x00','name':"batt_low",'scaling':1.0},
                                        {'hashcode':'\x63\x63\x8B\x00','name':"motor_current",'scaling':1.0},
                                        {'hashcode':'\x63\xAA\x50\x00','name':"pressure_high",'scaling':1.0},
                                        {'hashcode':'\x63\xAA\x50\x01','name':"pressure_low",'scaling':1.0},
                                        {'hashcode':'\x63\x5E\x0B\x00','name':"min_pressure_high",'scaling':1.0},
                                        {'hashcode':'\x63\x5E\x0B\x01','name':"min_pressure_low",'scaling':1.0},
                                        {'hashcode':'\x63\x7A\x62\x00','name':"max_pressure_high",'scaling':1.0},
                                        {'hashcode':'\x63\x7A\x62\x01','name':"max_pressure_low",'scaling':1.0},
                                        {'hashcode':'\x63\xF8\x2B\x00','name':"pressure_error",'scaling':1.0},
                                        {'hashcode':'\x63\xBB\x94\x00','name':"avg_pressure_low",'scaling':1.0},
                                        {'hashcode':'\x63\x7E\x90\x00','name':"avg_pressure_high",'scaling':1.0},
                                        {'hashcode':'\x63\x31\x9C\x00','name':"avg_pressure_delta",'scaling':1.0},
                                        {'hashcode':'\x63\x66\xFA\x00','name':"pressure_high_deriv",'scaling':1.0},
                                        {'hashcode':'\x63\x5F\x95\x00','name':"comp_on",'scaling':1.0},
                                        {'hashcode':'\x63\x65\xA4\x00','name':"error_code",'scaling':1.0}
                                        ]
                                                 
class cryomechServer():

# This server will register in pyro namespace, continuously run, and push commands from adr_controller to the sim900.

    def __init__(self, query_dictionary=default_query_dictionary, hostname="localhost", port=50001):
        self.data={'group':'cryomech'}
        
        self.communicator_lock=threading.Lock()
        
        self.smdp=smdp.smdp(address=16,use_srlnum=True)
        
        self.communicator=sim900_communicator.CleanComm(self.communicator_lock,port=4003)
        # Start up to connect to real sim900
        
        self.query_dictionary=query_dictionary
        
        self.setup_logger()
        
        self.loop_thread=None
        self.start_loop_thread()
        
    def setup_logger(self,base_dir='/home/adclocal/data/garbage_cooldown_logs/server_logs/cryomech_server_logs',suffix=''):
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
        self.loop_thread=threading.Thread(target=self.follow_query_dict)
        self.loop_thread.daemon=True
        self.loop_thread.start()
        
    def test_connect(self):
        # Just for debugging.
        for j in self.query_dictionary:
            print j['name']
            q=j['hashcode']
            print q
            m=self.smdp.construct_msg(q)
            print m
            r=self.communicator.fast_send_and_receive(m,terminator='\r',end_of_response='\r')
            print r
            a=self.smdp.destruct_answer(r+'\r')
            print a
            
        
    def follow_query_dict(self):
        # A single loop takes about 0.25 seconds
        while True:
            try:
                tic=time.time()
                for j in self.query_dictionary:
                    msg=self.smdp.construct_msg(j['hashcode'])
                    answer=self.communicator.fast_send_and_receive(msg,terminator='\r',end_of_response='\r')
                    result=self.smdp.destruct_answer(answer+'\r')
                    # fast_send_and_receive slices off the \r so we add it back in to get the correct amount of characters.
                    try:          
                        if j['name']=="error_code" or j['name']=="comp_on" or j['name']== "pressure_error" or j['name']=="temp_error" or j['name']=="batt_ok" or j['name']=="batt_low" or j['name']=="comp_minutes" or j['name']=="motor_current":
                            self.data[j['name']]=float(result)
                        else:
                            # Most of the values need to be divided by ten to have the correct value.
                            self.data[j['name']]=(float(result)/10.0)
                    except ValueError as e:
                        self.logger.warning('Value error in key %s. NaN inserted. Error printed below.'%(j['name']))
                        self.logger.warning(e)
                        self.data[j['name']]=np.nan
                toc=time.time()
                self.logger.info('Loading dictionary took %f seconds'%(toc-tic)) 
            except Exception as e:
                self.logger.error('ERROR ENCOUNTERED. Loop ended and will start from the beginning after normal wait period.')
                self.logger.error(e)
            self.data['time']=time.time()
            time.sleep(5)
            # Not essential that these values are exactly up to date.
            
    def fetch_dict(self):
        return self.data
            
def main():
    cryo=cryomechServer(hostname="192.168.1.152")
    Pyro4.Daemon.serveSimple(
            {
                cryo: "cryomechserver"
            },
            ns=True)

if __name__=="__main__":
    main()
