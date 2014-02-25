import threading
import time

import Pyro4

class AdrController():
    def __init__(self,parent,client,startup_state="standby"):
        self.exit=False
        self.state=startup_state
        # Sets the current state. Standby by default.
        
        self.parent=parent
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
        if self.data['mag_current']>=9.4:
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
        if self.data['mag_current']<=0.0:
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
        
        
    def request_set_bridge_setpoint(self):
        print self.parent.bridge_setpoint_command_value.value()
        #self.sim900.setBridgeSetpoint(self.bridge_setpoint_command_value.value())
        
    
    def function_loop(self):
        while True:
            if self.exit==True:
                return 0
            self.data=self.client.fetchDict()
            mag_current = self.data['mag_current']
            temp = self.data['bridge_temp']
            
            if self.state=="standby":
                pass
                #self.client.stop()
            if self.state=="regenerate":
                self.client.regenerate()
            if self.state=="regulate":
                pass
                #self.client.regulate()
            if self.state=="mag_up":
                if temp>6:
                    return
                    # Should I use exception try/catch here instead of just returning?
                if mag_current<9.4:
                    pass
                    #self.client.set_current(mag_current+0.1)
                if mag_current>=9.4:
                    pass
                    #self.state="dwell"
            if self.state=="mag_down":
                if temp>6:
                    return
                    # Should I use exception try/catch here instead of just returning?
                if mag_current>0.0:
                    pass
                    #self.client.set_current(mag_current-0.1)
                if mag_current<=0.0:
                    self.state="standby"
            if self.state=="dwell":
                #make sure nothing is varying wildly.
                pass
            time.sleep(1)
            
    def ramp(self,goal):
        self.state="mag_up"
        self.mag_goal=goal
