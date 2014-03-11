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
        
        self.recent_current_values = []
        # Use to determine whether to ramp down after regulate.
        # Also perhaps useful in determining a limit to the PID output so that it doesn't go crazy over jolts.
        
        self.gui_input=gui_input
        self.gui_response=False
        self.message_for_gui=None
        
        self.client=client
        
        self.loop_thread=None
        self.command_thread=None
        self.quit_command_thread=False
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
                    
                    if not fixing_flag and self.data['bridge_temp_value']>6:
                        # Temperature check.
                        print 'Temperature too high, ramping current to zero.'
                        self.ramp_goal=0.0
                        self.ramp_step=0.01
                        # If temperature is above 6K and we are below zero current... something is very odd.
                        self.state='ramping'
                    
                    if self.state=='start_regulate':
                        if self.data['dvm_volts1']>0.04:
                            self.state='regulate'
                        else:
                            if self.data['pid_manual_status']==1:
                                self.request_manual_output_on()
                            self.ramp_step=0.05
                            self.client.set_manual_output(self.data['pid_manual_out']-self.ramp_step)
                            
                    
                    if self.state=='regulate':
                    
                        if not fixing_flag:
                        # Business as usual.
                        
                            if self.data['pid_manual_status']==0:
                                # Switches from the manual output to PID.
                                # This could happen from an overload or from start_regulate's ramping to a minimum current.
                                print 'Switching to PID output.'
                                self.request_pid_output_on()
                    
                    
                            
                            self.recent_current_values.append(self.data['dvm_volts1'])
                            if len(self.recent_current_values)>10:
                                del self.recent_current_values[0]
                            if len(self.recent_current_values)>10 and sum(self.recent_current_values)/len(self.recent_current_values)<0.03:
                                # This list makes sure the system doesn't ramp down due to a single point below 0.03 amps.
                                # It must be there for ten successive data measurements.
                                print 'Current too low to regulate. Ramping to zero current.'
                                self.ramp_down()
                                
                        
                            difference=self.pid_goal - self.data['pid_setpoint']
                            # Change these to percentages?
                            if difference >=0.01:
                                #ramp setpoint upp_bridge = data['bridge_temp_value']
                                self.client.set_pid_setpoint(self.data['pid_setpoint']+(self.pid_step*self.refresh_rate))
                            if difference < -0.01:
                                #ramp setpoint down.
                                self.client.set_pid_setpoint(self.data['pid_setpoint']-(self.pid_step*self.refresh_rate))
                                
                            if abs(difference)<=0.01*self.pid_goal and difference!=0:
                                # Once we are close enough, we simply set the setpoint to our goal.
                                self.client.set_pid_setpoint(self.pid_goal)
                                
                        if fixing_flag:
                            if self.data['pid_manual_status']==1:
                                print 'Switching to manual output until autorange gain finished.'
                                self.request_manual_output_on()
                                # Holds the output constant until the overload is fixed.
                            
                        
                    if self.state=='ramping_up':
                        # Makes sure the current stays within acceptable bounds. 
                        if self.data['dvm_volts1']>=9.7:
                            # Allows you to go down, but not up
                            self.state='dwell'
                            raise ValueError('Magnet current is at max. State has been set to dwell.')
                        if self.data['dvm_volts1']>=self.ramp_goal:
                            self.state='dwell'
                            raise ValueError('Ramp goal reached. State switched to dwell.')
                        self.client.set_manual_output(self.data['pid_manual_out']-self.ramp_step)
                        
                        
                    if self.state=='ramping_down':
                        if self.data['dvm_volts1']<=0:
                            self.state='standby'
                            print 'Ramp down complete. State switched to standby.'
                        self.client.set_manual_output(self.data['pid_manual_out']+self.ramp_step)
                        
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
            
    def request_regenerate(self,pid_setpoint_goal=2.5, peak_current=1.0, ramp_rate_up=-0.05, ramp_rate_down=0.05, wait_time=0.5):
    
        if self.state!='standby':
            print 'To regenerate, the controller must be in standby mode.'
            return
    
        self.grab_flag()
        if not self.active_flag:
            print 'Controller does not have active_flag.'
            return
        
        try:
            self.quit_command_thread=False
            self.start_command_thread(pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down,wait_time)
        except:
            self.give_flag()
            raise
        
    def start_command_thread(self,pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down,wait_time):
        if self.command_thread:
            if self.command_thread.is_alive():
                print "loop already running"
                return
                
        self.command_thread=threading.Thread(target=self.regenerate_loop,args=(pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down,wait_time))
        self.command_thread.daemon=True
        self.command_thread.start()
        
    def regenerate_loop(self,pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down,wait_time):
    
        self.magup(peak_current,ramp_rate_up)
        if self.quit_command_thread==True:
            print 'Regenerate thread exited.'
            return
        self.wait('dwell')
        if self.quit_command_thread==True:
            print 'Regenerate thread exited.'
            return
        self.dwell(wait_time)
        if self.quit_command_thread==True:
            print 'Regenerate thread exited.'
            return
        self.demag(ramp_rate_down)
        if self.quit_command_thread==True:
            print 'Regenerate thread exited.'
            return
        self.wait('standby')
        if self.quit_command_thread==True:
            print 'Regenerate thread exited.'
            return
        self.request_regulate(pid_setpoint_goal)
        return
                
    def magup(self,peak_current,ramp_rate_up):
        self.request_user_input(message='Switch to Mag Cycle.')
        self.request_user_input(message='Close heat switch.')
        self.ramp_up(peak_current,ramp_rate_up)
        
    def dwell(self, wait_time=0.5):
        # Waits an alloted time at the peak current for temperature to equalize.
        wait_time_in_seconds=wait_time*60
        start=time.time()
        tic=time.time()
        while tic-start<wait_time_in_seconds:
            if self.quit_command_thread==True:
                print 'Regenerate thread exited.'
                return
            time.sleep(0.01)
            tic=time.time()
            
    def wait(self,signal):
        # Waits until the system has finished ramping up or down.
        while self.state != signal:
            if self.quit_command_thread==True:
                print 'Regenerate thread exited.'
                return
            time.sleep(0.01)
        
    def demag(self,ramp_rate_down):
        self.request_user_input(message='Open heat switch.')
        
        self.ramp_down(ramp_rate_down)
        
### Ramping methods ###
        
    def ramp_up(self,goal,rate=0.01):
        
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
            
            self.state='ramping_up'
            self.client.set_state('ramping_up')
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
            
    def ramp_down(self,rate=0.01):
        
        self.grab_flag()
        if not self.active_flag:
            print 'Controller does not have active_flag.'
            return
        
        try:
        
            if self.data['pid_manual_status']==1:
                # check that manual output on
                self.request_manual_output_on()
            
            self.state='ramping_down'
            self.client.set_state('ramping_down')
            self.ramp_step=rate*self.refresh_rate
            self.ramp_goal=0
        except:
            self.give_flag()
            raise
            
    def request_manual_output_on(self):
        # Private method.
        # Returns true if executed successfully, false otherwise
        
        self.data=self.client.fetch_dict()
        # Gets fresh data
        output_now=self.data['pid_output_mon']
        # Checks current output.
        success=self.client.set_manual_output(output_now)
        # Sets manual output to that output.
        
        if success == False:
            # Terminate if set_manual_output fails
            return False
        
        # Grab new value and compare them to make sure the command went through.
        difference=1
        start=time.time()
        while difference>0.01:
            result=self.client.query_manual_output()
            if not isinstance(result,float):
                return False
            # Result will not be a float if query_manual_output failed. It will be false.
                
            print result
            print output_now
            difference=abs(result-output_now)
            tic=time.time()
            if tic-start>2.0:
                # Reponse for request_manual_output timed out.
                return False
        
        if self.data['pid_manual_status']==1:
            # If the mode is in PID control...
            success=self.client.set_pid_manual_status(0)
            # Turns manual output on.
            if success==False:
                return False
            
        else:
            print 'Output mode already manual.'
            
        return True
            
### Regulate Methods ###

    def request_pid_output_on(self):
        # Private method.
        # Returns true if executed successfully, false otherwise
        
        self.data=self.client.fetch_dict()
        # Gets fresh data
        output_now=self.data['pid_measure_mon']
        success=self.client.set_pid_setpoint(output_now)
        # matches input voltage at front panel, not data from bridge, since there can be a voltage offset.
        # Note that there is a small ~0.05 offset between pid setpoint and bridge_temperature.
        if success==False:
            return False
        
        # There is still an offset between pid_setpoint and pid_measure_mon (less than with bridge_temperature), which initially causes
        # a small jolt to the output (and thus to the incoming measure_mon a small time later)
        
        result=''
        # Grab new value and compare them to make sure the command went through.
        start=time.time()
        difference=1
        start=time.time()
        while difference>0.01:
            # This will only be a problem is we set the PID setpoint to zero and get a false connection from the server.
            result=self.client.query_pid_setpoint()
            if not isinstance(result,float):
                return False
            # Result will not be a float if query_pid_setpoint failed. It will be false.
            
            print result
            print output_now
            difference=abs(result-output_now)
            tic=time.time()
            if tic-start>2.0:
                #Reponse for request_manual_output timed out.
                return False
            
            
        if self.data['pid_manual_status']==0:
            
            success=self.client.set_pid_manual_status(1)
            # Turns pid output on.
            if success==False:
                return False
        else:
            print 'Output mode already PID.'
            
        return True
            
    def request_regulate(self,pid_setpoint_goal):
        self.grab_flag()
        if not self.active_flag:
            print 'Controller does not have active_flag.'
            return
        self.request_pid_output_on()
        self.pid_goal=pid_setpoint_goal
        self.state='start_regulate'
        self.client.set_state('regulate')

### Standby ###
        
    def request_standby(self):
    
        self.grab_flag()
        if not self.active_flag:
            print 'Controller does not have active_flag.'
            return
    
        if self.command_thread:
            self.quit_command_thread=True
            
    
        if self.data['dvm_volts1']>=0:
            # Ramps to zero if not already there.
            self.ramp_down()
        else:
            self.state='standby'
            self.client.set_state('standby')
