import threading
import time

import Pyro4


class AdrController():
    def __init__(self,client,gui_input=None,startup_state="standby"):
        self.exit=False
        self.state=startup_state
        # Sets the current state. Standby by default.
        
        self.active_flag=False
        # This allows the coordination of multiple adr_controllers.
        
        self.refresh_rate=3
        self.ramp_step=0.0
        self.ramp_goal=0.0
        # parameters for ramping
        
        self.gui_input=gui_input
        self.gui_response=False
        
        self.client=client
        
        self.loop_thread=None
        self.command_thread=None
        self.start_loop_thread()
        # starts the loop_thread (function loop)
        
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
            
    def request_user_input(self,message=''):
        if self.gui_input==None:
            response=''
            while response != 'yes':
                print message+' Type yes to continue.'
                response=raw_input()
            return
        else:
            while self.gui_response != True:
                self.gui_input(message)
                # function returns true/false after popping up an alert in the GUI.
            self.gui_response=False
            return
            
    def request_regenerate(self,bridge_setpoint_value):
        self.grab_flag()
        if not self.active_flag:
            return
            
        print '1'
        
        try:
            self.start_command_thread()
        except:
            self.give_flag()
            raise
        
    '''def request_regenerate(self,value):
        self.request_user_input(message='Switch to Mag Cycle.')
        self.request_user_input(message='Close heat switch.')'''
        
    def start_command_thread(self):
        if self.command_thread:
            if self.command_thread.is_alive():
                print "loop already running"
                return
                
        print '2'
        self.command_thread=threading.Thread(target=self.regenerate_loop)
        self.command_thread.daemon=True
        self.command_thread.start()
        
    def regenerate_loop(self):
        print '3'
        self.magup()
        self.wait()
        self.demag()
        self.wait()
        self.request_regulate(bridge_setpoint_value)
                
    def magup(self):
        print '4'
        self.request_user_input(message='Switch to Mag Cycle.')
        print '5'
        self.request_user_input(message='Close heat switch.')
        self.ramp_to(-0.005,0.1)
        
    def wait(self, wait_time=30):
        while self.state != 'dwell':
            time.sleep(30)
        time.sleep(wait_time)
        
    def demag(self):
        self.request_user_input(message='Open heat switch.')
        
        self.ramp_to(0.005,0.5)
        
        
    def request_standby(self):
        self.state='standby'
        self.client.set_state('standby')
        
    def request_regulate(self,bridge_setpoint_value):
    
        self.grab_flag()
        if not self.active_flag:
            return
    
        self.request_set_bridge_setpoint(bridge_setpoint_value)
        self.request_pid_output_on()
        self.state='regulate'
        self.client.set_state('regulate')
        
    def request_pid_output_on(self):
    
        self.grab_flag()
        if not self.active_flag:
            return
    
        if self.data['pid_manual_status']==0:
            self.client.send(3,'AMAN 1')
            # Turns manual output on.
        else:
            print 'Output mode already PID.'
            
    def request_set_bridge_setpoint(self,bridge_setpoint_value):
    
        self.grab_flag()
        if not self.active_flag:
            return
        msg='SETP %f'%(bridge_setpoint_value)
        self.client.send(3,msg)
        
    def request_manual_output_on(self):
        # Note that this shouldn't be used directly by the user. Method ramp_to has the correct error-catching.
        if self.data['pid_manual_status']==1:
            # If the mode is in PID control...
            output_now=self.data['pid_output_mon']
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
        
        try:
        
            if self.data['pid_manual_status']==1:
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
        except:
            # Except block is meant to return flag, and then raise exception. I don't want the active_flag disappearing with 
            # a crashed program.
            # I don't use finally because I only want to give the flag back upon an error (or when I specifically say so)
            # NOT after this transaction otherwise.
            self.give_flag()
            raise
        
    def function_loop(self):
        while True:
            if self.exit==True:
                return 0
                
            self.data=self.client.fetch_dict()
            
            if self.active_flag==True:
                try:
                    if self.state=="standby":
                        pass
                    if self.state=="regulate":
                        # if current goes below some value (0.15) end regulation
                        pass
                    if self.state=="dwell":
                        pass
                        
                    if self.state=='ramping':
                    # Makes sure the current stays within acceptable bounds. 
                        if self.data['dvm_volts1']>=9.7:
                            self.state='dwell'
                            raise ValueError('mag_current is at max. State has been set to dwell.')
                        if self.data['dvm_volts1']<=-0.1:
                            self.state='standby'
                            raise ValueError('mag_current is at minimum. State has been set to standby.')
                            
                        if self.ramp_step>=0:    
                            if self.data['dvm_volts1']<=self.ramp_goal:
                                # If going down, we stop once we are at or below our goal.
                                self.state='dwell'
                                raise ValueError('Ramp goal reached. State switched to dwell.')
                        if self.ramp_step<0:    
                            if self.data['dvm_volts1']>=self.ramp_goal:
                                # If going up, we stop once we are at or above our goal.
                                self.state='dwell'
                                raise ValueError('Ramp goal reached. State switched to dwell.')
                        
                        self.client.set_pid_manual_out(self.data['pid_manual_out']+self.ramp_step)
                        
                    
                except ValueError as e:
                    # Deals with the system reaching certain values.
                    print e
                    self.give_flag()
                except:
                    self.give_flag()
                    raise
                    # Makes sure the flag is given back for other exceptions as well, but doesn't catch them.
            time.sleep(self.refresh_rate)
