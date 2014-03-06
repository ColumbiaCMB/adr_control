import threading
import time

import Pyro4


class AdrController():
    def __init__(self,client,gui_input=False,startup_state="standby"):
        self.exit=False
        self.state=startup_state
        # Sets the current state. Standby by default.
        
        self.active_flag=False
        # This allows the coordination of multiple adr_controllers.
        
        self.refresh_rate=3
        self.ramp_step=0.0
        self.ramp_goal=0.0
        self.pid_goal=0.0
        self.pid_step=0.001
        # parameters for ramping current and pid_setpoint
        
        self.gui_input=gui_input
        self.gui_response=False
        self.message_for_gui=None
        
        self.client=client
        
        self.loop_thread=None
        self.command_thread=None
        self.start_loop_thread()
        
        
### Loop thread and function loop ###
        
    def start_loop_thread(self):
    # starts the loop_thread (function loop)
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
                
            self.data=self.client.fetch_dict()
            
            if self.active_flag==True:
                try:
                
                    fixing_flag = (self.data['bridge_overload_status']>0) or (self.data['bridge_autorange_gain']>0)
                    # tells whether the bridge is using AGAI to fix and overload or not.
                    
                    if self.state=="regulate":
                    
                        if not fixing_flag:
                        # Business as usual.
                        
                            if self.data['pid_manual_status']==0:
                                # Switches from the manual output that happens during an overload back to PID control
                                # once the fixing is done.
                                print 'Switching to PID output.'
                                self.request_pid_output_on()
                    
                            if self.data['dvm_volts1']<0.03:
                                print 'Current too low to regulate. Ramping to zero current.'
                                self.ramp_to(0.005,0.0)
                                
                        
                            difference=self.pid_goal - self.data['pid_setpoint']
                            if difference >=0.01:
                                #ramp setpoint up
                                msg='SETP %f'%(self.data['pid_setpoint']+(self.pid_step*self.refresh_rate))
                                self.client.send(3,msg)
                            if difference < -0.01:
                                #ramp setpoint down.
                                msg='SETP %f'%(self.data['pid_setpoint']-(self.pid_step*self.refresh_rate))
                                self.client.send(3,msg)
                                
                        if fixing_flag:
                            if self.data['pid_manual_status']==1:
                                print 'Switching to manual output until autorange gain finished.'
                                self.request_manual_output_on()
                                # Holds the output constant until the overload is fixed.
                            
                        
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
                        
                        #self.client.set_pid_manual_out(self.data['pid_manual_out']+self.ramp_step)
                        msg='MOUT %f'%(self.data['pid_manual_out']+self.ramp_step)
                        self.client.send(3,msg)
                        
                    if self.state=="dwell":
                        pass
                    if self.state=="standby":
                        pass
                        
                    
                except ValueError as e:
                    # Deals with the system reaching certain values.
                    print e
                    self.give_flag()
                except:
                    self.give_flag()
                    raise
                    # Makes sure the flag is given back for other exceptions as well, but doesn't catch them.
            time.sleep(self.refresh_rate)
        
### Flag Handling ###
        
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
            
### User Input ###
            
    def request_user_input(self,message=''):
        if self.gui_input==False:
            response=''
            while response != 'yes':
                print message+' Type yes to continue.'
                response=raw_input()
            return
        else:
            self.message_for_gui=message
            while self.gui_response != True:
                pass
                # function returns true/false after popping up an alert in the GUI.
            self.message_for_gui=None
            self.gui_response=False
            return
            
### Regenerate Thread and Methods ###
            
    def request_regenerate(self,bridge_setpoint_value):
        self.grab_flag()
        if not self.active_flag:
            print 'Controller does not have active_flag.'
            return
        
        try:
            self.start_command_thread()
        except:
            self.give_flag()
            raise
        
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
    
        self.request_user_input(message='Switch to Mag Cycle.')
        self.request_user_input(message='Close heat switch.')
        
        print '3'
        '''self.magup()
        self.wait()
        self.demag()
        self.wait()
        self.request_regulate(bridge_setpoint_value)'''
                
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
        
### Ramping methods ###
        
    def ramp_to(self,rate,goal):
    
        # Do error checking here to make sure I can ramp. Check server state to make sure it isn't already ramping.
        
        self.grab_flag()
        if not self.active_flag:
            print 'Controller does not have active_flag.'
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
            
### Regulate Methods ###

    def request_pid_output_on(self):
        # Private method.
        
        self.data=self.client.fetch_dict()
        # Gets fresh data
        
        output_now=self.data['pid_measure_mon']
        msg='SETP %f'%(output_now)
        # matches input voltage at front panel, not data from bridge, since there can be a voltage offset.
        # Note that there is a small ~0.05 offset between pid setpoint and bridge_temperature.
        
        # There is still an offset between pid_setpoint and pid_measure_mon (less than with bridge_temperature), which initially causes
        # a small jolt to the output (and thus to the incoming measure_mon a small time later)
        self.client.send(3,msg)
        
        result=''
        # Grab new value and compare them to make sure the command went through.
        start=time.time()
        # Grab new value and compare them to make sure the command went through.
        difference=1
        start=time.time()
        while difference>0.01:
            result=float(self.client.query_port(3,'SETP?'))
            print result
            print output_now
            difference=abs(result-output_now)
            tic=time.time()
            if tic-start>2.0:
                print 'Reponse for request_manual_output timed out.'
                return
            
            
        if self.data['pid_manual_status']==0:
            
            self.client.send(3,'AMAN 1')
            # Turns pid output on.
        else:
            print 'Output mode already PID.'
            
    def request_regulate(self,pid_setpoint_goal):
        self.grab_flag()
        if not self.active_flag:
            print 'Controller does not have active_flag.'
            return
        self.request_pid_output_on()
        self.pid_goal=pid_setpoint_goal
        self.state='regulate'
        self.client.set_state('regulate')

### Other ###
        
    def request_standby(self):
        self.state='standby'
        self.client.set_state('standby')
        
    def request_manual_output_on(self):
        # Private method.
        
        self.data=self.client.fetch_dict()
        # Gets fresh data
        output_now=self.data['pid_output_mon']
        # Checks current output.
        msg='MOUT %f'%(output_now)
        self.client.send(3,msg)
        # Sets manual output to that output.
        
        # Grab new value and compare them to make sure the command went through.
        difference=1
        start=time.time()
        while difference>0.01:
            result=float(self.client.query_port(3,'MOUT?'))
            print result
            print output_now
            difference=abs(result-output_now)
            tic=time.time()
            if tic-start>2.0:
                print 'Reponse for request_manual_output timed out.'
                return
        
        if self.data['pid_manual_status']==1:
            # If the mode is in PID control...
            self.client.send(3,'AMAN 0')
            # Turns manual output on.
        else:
            print 'Output mode already manual.'
