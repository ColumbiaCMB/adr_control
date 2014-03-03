import threading
import time

import Pyro4


class AdrController():
    def __init__(self,client,startup_state="standby"):
        self.exit=False
        self.state=startup_state
        # Sets the current state. Standby by default.
        
        self.active_flag=False
        # This allows the coordination of multiple adr_controllers.
        
        self.refresh_rate=3
        self.ramp_step=0.0
        self.ramp_goal=0.0
        
        self.client=client
        self.data=self.client.fetch_dict()
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
        
    def grab_flag(self):
        if self.active_flag==True:
            print 'You already have the flag.'
        else:
            flag=self.client.get_flag()
            self.active_flag=flag
        
    def give_flag(self):
        if self.active_flag==True:
            self.client.give_flag()
            self.active_flag=False
        
    def request_standby(self):
        #make sure current is zero
        # make sure no PID
        if self.data["dvm_volts1"]!=0:
            print "Set magnet current to zero before standby."
            return
            # use exceptions here instead?
        self.state='standby'
        self.client.set_state('standby')
    
    def request_dwell(self):
        # makes sure system is in dwellable state.
        self.state='dwell'
        self.client.set_state('dwell')
        
    def request_regulate(self):
        # makes sure system is in standby
        # engages PID
        # if current goes below some value (0.15) end regulation (this should actually be in function_loop)
        self.state='regulate'
        self.client.set_state('regulate')
        
    def request_regenerate(self):
        # Do error checking
        self.state='regenerate'
        self.client.set_state('regenerate')
        
    def request_set_bridge_setpoint(self,bridge_setpoint_value):
        print bridge_setpoint_value
        
    def request_manual_output_on(self):
        if data['bridge_output_mode']==1:
            # If the mode is in PID control...
            output_now=data['pid_output_mon']
            # Checks current output.
            msg='MOUT %f'%(output_now)
            self.client.send(3,msg)
            # Sets manual output to that output.
            self.client.send(3,'AMAN 0')
            # Turns manual output on.
        else:
            print 'Output mode already manual.'
            
    def ramp_to(self,rate,goal):
    
        # Do error checking here to make sure I can ramp. Check server state to make sure it isn't already ramping.
        
        self.grab_flag()
        if not self.active_flag:
            return
        # Tries to grab the active flag. If it doesn't get it, it ends.
        # The flag will be given back once the ramping is complete.
        
        if self.data['bridge_output_mode']==1:
            # check that manual output on
            self.request_manual_output_on()
            
        difference=goal-self.data['dvm_volts1']
    
        if rate>0 and difference>0:
            print 'Rate must be negative if ramping current up.'
            self.give_flag()
            return
        if rate<0 and difference<0:
            print 'Rate must be positive if ramping current down.'
            self.give_flag()
            return
        
        self.state='ramping'
        self.client.set_state('ramping')
        self.ramp_step=rate*self.refresh_rate
        self.ramp_goal=goal
        # rate should be in volts/second and refresh rate is the time between function loops.
        return
        
    def function_loop(self):
        while True:
            if self.exit==True:
                return 0
                
            self.data=self.client.fetch_dict()
            
            if self.active_flag==True:
                try:
                    if self.state=="standby":
                        pass
                    if self.state=="regenerate":
                        self.client.regenerate()
                    if self.state=="regulate":
                        pass
                        #self.client.regulate()
                    if self.state=='ramping':
                        if self.data['dvm_volts1']>=9.4:
                            self.state='dwell'
                            raise ValueError('mag_current is at max. State has been set to dwell.')
                        if self.data['dvm_volts1']<=-0.02:
                            self.state='standby'
                            raise ValueError('mag_current is at minimum. State has been set to standby.')
                       # Makes sure the current stays within acceptable bounds. 
                            
                            
                        if self.ramp_step>=0:    
                            if self.data['dvm_volts1']<=self.ramp_goal:
                                # This will never be exact, so we need a fuzzier check.
                                # If going up, check if dvm_volts1 is higher, if going down, do the opposite.
                                self.state='regulate'
                                self.ramp_step=0.0
                                raise ValueError('Ramp goal reached. State switched to regulate.')
                        if self.ramp_step<0:    
                            if self.data['dvm_volts1']>=self.ramp_goal:
                                # This will never be exact, so we need a fuzzier check.
                                # If going up, check if dvm_volts1 is higher, if going down, do the opposite.
                                self.state='regulate'
                                raise ValueError('Ramp goal reached. State switched to regulate.')
                                # stops the ramping once we get to our goal.
                        
                        self.client.set_pid_manual_out(self.data['pid_manual_out']+self.ramp_step)
                        
                    if self.state=="dwell":
                        #make sure nothing is varying wildly.
                        pass
                except ValueError as e:
                    print e
                    self.give_flag()
                except:
                    self.give_flag()
                    raise
                    # Makes sure the flag is given back for other exceptions as well.
            time.sleep(self.refresh_rate)
