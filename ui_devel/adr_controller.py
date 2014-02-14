from PyQt4.QtCore import *
from PyQt4.QtGui import *
# Only for Qtimer

import threading
import time

import Pyro4

class AdrController():
    def __init__(self,startup_state="standby",client=Pyro4.Proxy("PYRONAME:sim900server")):
        self.exit=False
        self.state=startup_state
        # Sets the current state. Standby by default.
        self.client=client
        self.mag_goal=None
        self.loop_thread=None
        
    def run(self):
        print "starting simple_loop"
        self.simple_loop()
        print "exiting simple_loop"
        
    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                print "loop already running"
                return
        self.loop_thread=threading.Thread(target=self.function_loop)
        self.loop_thread.daemon=True
        self.loop_thread.start()
        
    def function_loop(self):
        while True:
            if self.exit==True:
                return 0
            data=self.client.fetchDict()
            mag_current = data["dvm_volts"][1]
            temp = data["bridge_temp_value"]
            
            if self.state=="standby":
                self.client.stop()
            if self.state=="regenerate":
                self.client.regenerate()
            if self.state=="regulate":
                self.client.regulate()
            if self.state=="mag_up":
                if temp>6:
                    return
                if mag_current<9.4:
                    self.client.increase_current(mag_current+0.1)
                if mag_current>=9.4:
                    self.state="dwell"
            if self.state=="dwell":
                #make sure nothing is varying wildly.
                pass
            time.sleep(1)
    
    
    '''def function_loop(self):
        data=self.client.fetchDict()
        mag_current = data["dvm_volts"][1]
        if self.state=="standby":
            # check current
            if mag_current>0:
                #return an error: unexpected current.
            # Check for other errors
            
            # Don't do anything. If the 
            # return no error. If the loop got here, all is good.
                return 0
        if self.state=="mag_up":
            if temp<6:
                return 0
                if mag_current <= mag_goal:
                    client.setBridgeSetpoint(mag_current+interval)
                    # interval will be determined by ramp rate desired somewhere.
        if self.state=="dwell":
            return 0
            # check deltas from previous reading, if they are too big, do something
        if self.state=="mag_down":
            return 0
            # open heat switch
            # as mag up, but down. Perhaps make a function "ramp"'''
            
    def ramp(self,goal):
        self.state="mag_up"
        self.mag_goal=goal
