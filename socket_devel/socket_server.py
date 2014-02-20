import Pyro4
import simplejson as json
import random
import time
import sim900_socket
import threading

class sim900Client():

# This server will register in pyro namespace, continuously run, and push commands from adr_controller to the sim900.

    def __init__(self, hostname="localhost", port=50001):
        self.local_terminator = "\n\r"
        self.data={"time":0,"bridge_temperature_setpoint":1,"bridge_temp_value":1,"therm_temperature":[0,0,0],"dvm_volts":[0,0]}
        self.start_time=time.time()
        self.sock=sim900_socket.CleanSocket()
        
        self.loop_thread=None
        self.start_loop_thread()
        
        self.state=0
        
        
    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                print "loop already running"
                return
        self.loop_thread=threading.Thread(target=self.load_loop)
        self.loop_thread.daemon=True
        self.loop_thread.start()
        
    def load_loop(self):
        while True:
            self.load_data()
            print self.data
            #time.sleep(.5)
            
    def load_data(self):
    # Loads up an empty dict for now.
        tic=time.time()
        new_data=self.sock.get_data()
        self.data["time"]=tic-self.start_time
        self.data["bridge_temp_value"]=new_data['bridge_temp']
        self.data["therm_temperature"][0]=new_data['50k_temp']
        self.data["therm_temperature"][2]=new_data['4k_temp']
        self.data["dvm_volts"][0]=new_data['mag_volt']
        self.data["dvm_volts"][1]=new_data['mag_current']
        
    def fetchDict(self):
        return self.data
        
    def send(self,msg):
        # Note that this method has no error checking to make sure the command is valid. That needs to happen before this method is called.
        self.sock.send(msg)
        
    def regenerate(self):
        # Just a test
        if self.state==0:
            self.send('SNDT 3, "PCTL 1"')
            self.send('SNDT 3, "ICTL 1"')
            self.send('SNDT 3, "DCTL 1"')
            self.state=1
        else:
            self.send('SNDT 3, "PCTL 0"')
            self.send('SNDT 3, "ICTL 0"')
            self.send('SNDT 3, "DCTL 0"')
            self.state=0

def main():
    sim900=sim900Client(hostname="192.168.1.152")
    Pyro4.Daemon.serveSimple(
            {
                sim900: "sim900server"
            },
            ns=True)

if __name__=="__main__":
    main()

