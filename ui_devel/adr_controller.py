import threading
import time

import Pyro4

import data_logger

class AdrController():
    def __init__(self,client,startup_state="standby"):
        self.exit=False
        self.state=startup_state
        # Sets the current state. Standby by default.
        self.data_logger=data_logger.DataFile()
        
        self.client=client
        self.data=self.client.fetchDict()
        self.mag_goal=None
        self.loop_thread=None
        
        self.start_loop_thread()
        
    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                print "loop already running"
                return
        self.loop_thread=threading.Thread(target=self.function_loop)
        self.loop_thread.daemon=True
        self.loop_thread.start()
        
    def request_standby(self):
        #make sure current is zero
        # make sure no PID
        if self.data["dvm_volts"][1]!=0:
            print "Set magnet current to zero before standby."
            return
            # use exceptions here instead?
        self.state="standby"
    
    def request_mag_up(self):
        # Makes sure current is not at max
        # asks for ramp rate
        # asks for max current
        if self.data['dvm_volts'][1]>=9.4:
            print "current already at max"
            return
        self.state="mag_up"
    
    def request_dwell(self):
        # makes sure system is in dwellable state.
        self.state="dwell"
    def request_mag_down(self):
        # makes sure current is not at min
        # ramp rate
        # min current
        if self.data['dvm_volts'][1]<=0.0:
            print "current already at min"
            return
        self.state="mag_down"
    
    def request_regulate(self):
        # makes sure system is in standby
        # engages PID
        # if current goes below some value (0.15) end regulation (this should actually be in function_loop)
        self.state="regulate"
        
    def request_regenerate(self):
        # Do error checking
        self.state="regenerate"
        
    def request_set_bridge_setpoint(self,bridge_setpoint_value):
        print bridge_setpoint_value
        
    
    def function_loop(self):
        while True:
            if self.exit==True:
                return 0
            self.data=self.client.fetchDict()
            self.data_logger.update(self.data)
            
            pid_manual_out=float(self.data['pid_manual_out'])
            
            try:
                if self.state=="standby":
                    pass
                if self.state=="regenerate":
                    self.client.regenerate()
                if self.state=="regulate":
                    pass
                    #self.client.regulate()
                if self.state=="mag_up":
                    #if temp>6:
                        #raise ValueError('Temperature too high for mag_up')
                    if pid_manual_out<9.4:
                        self.client.set_pid_manual_out(pid_manual_out+0.1)
                    if pid_manual_out>=9.4:
                        self.state="dwell"
                        raise ValueError('mag_current is at max. State has been set to dwell.')
                if self.state=="mag_down":
                    #if temp>6:
                        #raise ValueError('Temperature too high for mag_down')
                    if pid_manual_out>0.0:
                        self.client.set_pid_manual_out(pid_manual_out-0.1)
                    if pid_manual_out<=0.0:
                        self.state="standby"
                        raise ValueError('mag_current is at minimum. State has been set to standby.')
                if self.state=="dwell":
                    #make sure nothing is varying wildly.
                    pass
            except ValueError as e:
                print e
            time.sleep(3)
            
    def ramp(self,goal):
        self.state="mag_up"
        self.mag_goal=goal
