import threading
import time
import numpy as np

import Pyro4


class AdrController():
    def __init__(self,client,gui_input=False,gui_message_display=None,startup_state="standby"):
        self.exit=False
        self.state=startup_state
        # Sets the current state. Standby by default.
        
        self.refresh_rate=1
        self.ramp_step=0.0
        self.ramp_goal=0.0
        self.pid_goal=0.0
        self.pid_step=0.001
        # parameters for ramping current and pid_setpoint
        
        self.client=client
        self.data=self.client.fetch_dict()
        self.manual_output_now=self.data['pid_manual_out']
        self.pid_setpoint_now=self.data['pid_setpoint']
        # parameters to keep track of the state of the system
        
        self.pid_max_output=0.0
        self.pid_min_output=-7.0
        # Limits to the pid_manual_output
        
        self.recent_current_values = []
        # Use to determine whether to ramp down after regulate.
        # Also perhaps useful in determining a limit to the PID output so that it doesn't go crazy over jolts.
        
        self.gui_input=gui_input
        self.gui_response=False
        self.message_for_gui=None
        self.gui_message_display=gui_message_display
        
        
        
        self.loop_thread=None
        self.command_thread=None
        self.regulate_thread=None
        self.quit_thread=False
        self.start_loop_thread()
        
        
### Loop thread and function loop ###
        
    def start_loop_thread(self):
    # starts the loop_thread (function loop)
        if self.loop_thread:
            if self.loop_thread.is_alive():
                self.show("loop already running")
                return
        self.loop_thread=threading.Thread(target=self.function_loop)
        self.loop_thread.daemon=True
        self.loop_thread.start()
        
    def function_loop(self):
        while True:
            if self.exit==True:
                return 0
                
            self.data=self.client.fetch_dict()
            
            try:
                
                fixing_flag = (self.data['bridge_overload_status']>0) or (self.data['bridge_autorange_gain']>0)
                # tells whether the bridge is using AGAI to fix and overload or not.
                # Probably should just use a flag from the server.
                
                if fixing_flag:
                    # Shows us what the overload status is.
                    self.show('Bridge overload status is %f'%(self.data['bridge_overload_status']))
                    self.show('Bridge autorange gain is %d'%(self.data['bridge_autorange_gain']))
                
                if not fixing_flag and self.data['bridge_temp_value']>6:
                    # Temperature check.
                    self.show('Temperature too high, ramping current to zero.')
                    self.ramp_down()
                
                if self.state=='start_regulate':
                    # Ramps to a minimum regulate current.
                    if self.data['dvm_volts1']>0.04:
                        self.state='regulate'
                    else:
                        if self.data['pid_manual_status']==1:
                            success=self.request_manual_output_on()
                            if success==False:
                                continue
                        
                        success=self.client.set_manual_output(self.manual_output_now-self.ramp_step)
                        # Ramp step is set in request_regulate
                        if success==True:
                            self.manual_output_now-=self.ramp_step
                        
                
                if self.state=='regulate':
                
                    if not fixing_flag:
                    # Business as usual.
                    
                        if self.data['pid_manual_status']==0:
                            # Switches from the manual output to PID.
                            # This could happen from an overload or from start_regulate's ramping to a minimum current.
                            self.show('Switching to PID output.')
                            success=self.request_pid_output_on()
                            if success==False:
                                continue
                
                
                        
                        self.recent_current_values.append(self.data['dvm_volts1'])
                        if len(self.recent_current_values)>20:
                            del self.recent_current_values[0]
                        mean=np.mean(self.recent_current_values)
                        
                        # Checks if the average of the last 20 values is less than 0.03 A. If so, the current is too low to regulate.
                        if len(self.recent_current_values)>=20 and mean<0.03:
                            self.show('Current too low to regulate. Ramping to zero current.')
                            self.recent_current_values=[]
                            self.request_manual_output_on()
                            self.ramp_down()
                            
                            
                        difference=self.pid_goal - self.pid_setpoint_now
                        if difference >0:
                            #self.client.set_pid_setpoint(self.data['pid_setpoint']+(self.pid_step*self.refresh_rate))
                            success=self.client.set_pid_setpoint(self.pid_setpoint_now+self.pid_step)
                            if success==True:
                                self.pid_setpoint_now+=self.pid_step
                        if difference < 0:
                            #ramp setpoint down.
                            success=self.client.set_pid_setpoint(self.pid_setpoint_now-self.pid_step)
                            if success==True:
                                self.pid_setpoint_now-=self.pid_step
                        if abs(difference)<=0.03*self.pid_goal and difference!=0:
                            # Once we are close enough, we simply set the setpoint to our goal.
                            self.client.set_pid_setpoint(self.pid_goal)
                            
                    if fixing_flag:
                        if self.data['pid_manual_status']==1:
                            self.show('Switching to manual output until autorange gain finished.')
                            success=self.request_manual_output_on()
                            if success==False:
                                continue
                            # Holds the output constant until the overload is fixed.
                        
                    
                if self.state=='ramping_up':
                
                    if self.data['pid_manual_status']==1:
                        success=self.request_manual_output_on()
                        if success==False:
                            continue
                
                    # Makes sure the current stays within acceptable bounds. 
                    if self.data['dvm_volts1']>=9.7:
                        self.state='dwell'
                        raise ValueError('Magnet current is at max. State has been set to dwell.')
                    if self.data['dvm_volts1']>=self.ramp_goal:
                        self.state='dwell'
                        raise ValueError('Ramp up goal of %f reached. State switched to dwell.'%(self.ramp_goal))
                    
                    new_output=self.manual_output_now-self.ramp_step
                    if new_output>=self.pid_min_output:
                        success=self.client.set_manual_output(new_output)
                        if success==True:
                            self.manual_output_now-=self.ramp_step
                    else:
                        success=self.client.set_manual_output(self.pid_min_output)
                        if success==True:
                            self.manual_output_now=self.pid_min_output
                            self.state='dwell'
                            raise ValueError('Ramp up ended because pid manual output reached minimum of %f. State switched to dwell.'%(self.pid_min_output))
                    
                    
                if self.state=='ramping_down':
                
                    if self.data['pid_manual_status']==1:
                        # check that manual output on
                        success=self.request_manual_output_on()
                        if success==False:
                            continue
                
                    if self.data['dvm_volts1']<=0:
                        self.state='standby'
                        raise ValueError('Ramp down goal of %f reached. State switched to standby.'%(self.ramp_goal))
                    success=self.client.set_manual_output(self.manual_output_now+self.ramp_step)
                    if success==True:
                        self.manual_output_now+=self.ramp_step
                        
                    new_output=self.manual_output_now+self.ramp_step
                    if new_output<=self.pid_max_output:
                        success=self.client.set_manual_output(new_output)
                        if success==True:
                            self.manual_output_now+=self.ramp_step
                    else:
                        success=self.client.set_manual_output(self.pid_max_output)
                        if success==True:
                            self.manual_output_now=self.pid_max_output
                            self.state='standby'
                            raise ValueError('Ramp down ended because pid manual output reached maximum of %f. State switched to standby.'%(self.pid_max_output))
                    
                if self.state=="dwell":
                    if self.data['pid_manual_status']==1:
                        # check that manual output on
                        success=self.request_manual_output_on()
                        if success==False:
                            continue
                    pass
                if self.state=="standby":
                    if self.data['pid_manual_status']==1:
                        # check that manual output on
                        success=self.request_manual_output_on()
                        if success==False:
                            continue
                    if self.manual_output_now!=0:
                        if abs(self.data['pid_manual_out'])<=0.0001:
                        # If there is a small deviation, manual_output_now should be zero
                            self.manual_output_now=0
                            continue
                        if self.manual_output_now>0:
                            self.ramp_step=0.005*self.refresh_rate
                            new_output=self.manual_output_now-self.ramp_step
                            if new_output<=0:
                                success=self.client.set_manual_output(new_output)
                                if success==True:
                                    self.manual_output_now-=self.ramp_step
                            else:
                                success=self.client.set_manual_output(0)
                        if self.manual_output_now<0:
                            # If below zero (the system started that way, for example) slowly ramp back to zero.
                            # Can't use ramp_up because it uses current.
                            self.ramp_step=0.005*self.refresh_rate
                            new_output=self.manual_output_now+self.ramp_step
                            if new_output<=0:
                                success=self.client.set_manual_output(new_output)
                                if success==True:
                                    self.manual_output_now+=self.ramp_step
                            else:
                                success=self.client.set_manual_output(0)
                            
            except ValueError as e:
                # Deals with the system reaching certain values.
                self.show(str(e))
            time.sleep(self.refresh_rate)

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
                time.sleep(0.001)
                # function returns true/false after popping up an alert in the GUI.
            self.message_for_gui=None
            self.gui_response=False
            return
            
### Regenerate Thread and Methods ###
            
    def request_regenerate(self,pid_setpoint_goal=2.5, peak_current=1.0, ramp_rate_up=-0.005, ramp_rate_down=0.005, pid_step=0.001, pause_time=0.5, dwell_time=0.5):
    
        if self.state!='standby':
            self.show('To regenerate, the controller must be in standby mode.')
            return
        if self.manual_output_now!=0.0:
            self.show('To regenerate, manual output must be zero.')
            return
        self.quit_thread=False
        self.start_command_thread(pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down, pid_step, pause_time, dwell_time)
        
    def start_command_thread(self,pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down, pid_step, pause_time, dwell_time):
        if self.command_thread:
            if self.command_thread.is_alive():
                self.show("loop already running")
                return
                
        self.command_thread=threading.Thread(target=self.regenerate_loop,args=(pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down, pid_step, pause_time, dwell_time))
        self.command_thread.daemon=True
        self.command_thread.start()
        
    def regenerate_loop(self,pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down, pid_step, pause_time, dwell_time):
    
        self.show('Regenerate thread started successfully.')
        self.magup(peak_current,ramp_rate_up)
        if self.quit_thread==True:
            self.show('Regenerate thread exited.')
            return
        self.wait('dwell')
        if self.quit_thread==True:
            self.show('Regenerate thread exited.')
            return
        self.dwell(dwell_time)
        if self.quit_thread==True:
            self.show('Regenerate thread exited.')
            return
        self.demag(ramp_rate_down)
        if self.quit_thread==True:
            self.show('Regenerate thread exited.')
            return
        self.wait('standby')
        if self.quit_thread==True:
            self.show('Regenerate thread exited.')
            return
        #self.pause(pause_time)
        # Regenerate is not included in regenerate right now.
        self.show('Regenerate thread completed successfully.')
        return
                
    def magup(self,peak_current,ramp_rate_up):
        self.request_user_input(message='Switch to Mag Cycle.')
        if self.quit_thread==True:
            self.show('Magup exited.')
            return
        time.sleep(0.5)
        # Make sure the popups don't come up so fast the user clicks both.
        self.request_user_input(message='Close heat switch.')
        if self.quit_thread==True:
            self.show('Magup exited.')
            return
        self.ramp_up(peak_current,ramp_rate_up)
        
    def dwell(self, dwell_time=0.5):
        # Waits an alloted time at the peak current for temperature to equalize.
        dwell_time_in_seconds=dwell_time*60
        start=time.time()
        tic=time.time()
        while tic-start<dwell_time_in_seconds:
            if self.quit_thread==True:
                self.show('Dwell before ramp down exited.')
                return
            time.sleep(0.01)
            tic=time.time()
            
    def pause(self, pause_time=0.5):
        # Waits an alloted time at zero current for temperature to equalize.
        pause_time_in_seconds=pause_time*60
        start=time.time()
        tic=time.time()
        while tic-start<pause_time_in_seconds:
            if self.quit_thread==True:
                self.show('Pause before regulation exited.')
                return
            time.sleep(0.01)
            tic=time.time()
            
    def wait(self,signal):
        # Waits until the system has finished ramping up or down.
        while self.state != signal:
            if self.quit_thread==True:
                self.show('Wait for %s terminated'%(signal))
                return
            time.sleep(0.01)
        
    def demag(self,ramp_rate_down):
        self.request_user_input(message='Open heat switch.')
        if self.quit_thread==True:
        
        # Should probably handle this case. What to do? Still ramp down? That is exactly what this already does.
        
            self.show('Demag exited.')
            return
        self.ramp_down(ramp_rate_down)
        
### Ramping methods ###
        
    def ramp_up(self,goal,rate=0.005):
        self.manual_output_now=self.data['pid_manual_out']
        # This is to make sure that we are ramping off of the correct manual output. If pid switches to manual, this will be redundant, but if we are already in manual mode it is not.
        
        self.ramp_step=rate*self.refresh_rate
        self.ramp_goal=goal
        
        self.state='ramping_up'
        self.client.set_state('ramping_up')
        # rate should be in volts/second and refresh rate is the time between function loops.
        
            
    def ramp_down(self,rate=0.005):
        self.manual_output_now=self.data['pid_manual_out']
        
        self.ramp_step=rate*self.refresh_rate
        self.ramp_goal=0
        
        self.state='ramping_down'
        self.client.set_state('ramping_down')
            
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
                
            self.show('Manual output is now %f'%(result))
            self.show('Output_mon is now %f'%(output_now))
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
            self.show('Output mode already manual.')
           
        self.data=self.client.fetch_dict()
        # Makes sure we see the newest data (and get no boomerang effects where we update values based on out-of-date dictionaries)
        self.manual_output_now=self.data['pid_manual_out']
        # Sets the internal variable to the data value.
        return True
            
### Regulate Methods ###

    def request_pid_output_on(self):
        # Private method.
        # Returns true if executed successfully, false otherwise
        
        self.data=self.client.fetch_dict()
        # Gets fresh data
        output_now=self.data['pid_measure_mon']
        success=self.client.set_pid_setpoint(output_now)
        # Makes sure we see the newest data (and get no boomerang effects where we update values based on out-of-date dictionaries))
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
            
            self.show('Pid_setpoint is now %f'%(result))
            self.show('pid_measure_mon is now %f'%(output_now))
            
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
            self.show('Output mode already PID.')
            
            
        self.data=self.client.fetch_dict()
        # Makes sure we see the newest data (and get no boomerang effects where we update values based on out-of-date dictionaries)
        self.pid_setpoint_now=self.data['pid_setpoint']
        # Sets the internal variable to the data value.
        return True
            
    '''def request_regulate(self,pid_setpoint_goal,pid_step=0.001, ramp_up=0.01):
    
        #self.request_user_input(message='Switch to Regulate.')
        # This doesn't work because request_regulate gets called from the main thread, which means this function freezes everything else, including the method that raises the message box
        # and sets the user response=True
        
        if pid_setpoint_goal<self.data['bridge_temp_value']:
            self.show('Regulate temperature is below current temperature. Must regulate at a temperature higher than temperature now.')
            return
    
        self.pid_goal=pid_setpoint_goal
        self.pid_step=pid_step*self.refresh_rate
        
        self.pid_setpoint_now=self.data['pid_setpoint']
        self.manual_output_now=self.data['pid_manual_out']
        # This is to make sure that we are ramping off of the correct setpoint. If pid switches to pid mode, this will be redundant, but we may change from regulating at one setpoint to regulating at another.
        
        self.ramp_step=ramp_up*self.refresh_rate
        
        self.state='start_regulate'
        self.client.set_state('regulate')'''
        
    def request_regulate(self,pid_setpoint_goal=2.5, ramp_rate_up=-0.005, pid_step=0.001):
    
        if self.state!='standby':
            self.show('To regulate, the controller must be in standby mode.')
            return
        if self.manual_output_now!=0.0:
            self.show('To regulate, manual output must be zero.')
            return
        if pid_setpoint_goal<self.data['bridge_temp_value']:
            self.show('Regulate temperature is below current temperature. Must regulate at a temperature higher than temperature now.')
            return
        self.quit_thread=False
        self.start_regulate_thread(pid_setpoint_goal, ramp_rate_up, pid_step)
        
    def start_regulate_thread(self,pid_setpoint_goal, ramp_rate_up, pid_step):
        if self.regulate_thread:
            if self.regulate_thread.is_alive():
                self.show("loop already running")
                return
                
        self.regulate_thread=threading.Thread(target=self.regulate_loop,args=(pid_setpoint_goal,ramp_rate_up, pid_step))
        self.regulate_thread.daemon=True
        self.regulate_thread.start()
        
        
    def go_to_min_current(self,ramp_rate_up,peak_current=0.04):
        self.request_user_input(message='Switch to Regulate.')
        self.ramp_up(peak_current,ramp_rate_up)
        
    def start_regulate(self, pid_setpoint_goal, pid_step):
        self.pid_setpoint_now=self.data['pid_setpoint']
        self.manual_output_now=self.data['pid_manual_out']
        self.pid_goal=pid_setpoint_goal
        self.pid_step=pid_step*self.refresh_rate
        self.state='start_regulate'
        self.client.set_state('regulate')
        
    def regulate_loop(self,pid_setpoint_goal,ramp_rate_up, pid_step):
        self.show('Regulate thread started successfully.')
        self.go_to_min_current(ramp_rate_up)
        if self.quit_thread==True:
            self.show('Regulate thread exited.')
            return
        self.wait('dwell')
        # Same function from regenerate_loop
        if self.quit_thread==True:
            self.show('Regulate thread exited.')
            return
        self.start_regulate(pid_setpoint_goal,pid_step)
        

### Standby ###
        
    def request_standby(self,ramp_down=0.01):
        self.show('Standby requested.')
        if self.command_thread or self.regulate_thread:
            self.quit_thread=True
        self.recent_current_values=[]
        # Resets the monitor list.
    
        if self.data['dvm_volts1']>=0:
            # Ramps to zero if not already there.
            self.ramp_step=ramp_down*self.refresh_rate
            self.ramp_down()
        else:
            self.request_manual_output_on()
            self.state='standby'
            
### Display messages ###

    def show(self,message):
        if self.gui_message_display==None:
            print str(message)
        else:
            # Push to GUI handling function.
            self.gui_message_display(str(message))
