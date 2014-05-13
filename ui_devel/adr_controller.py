import threading
import time
import numpy as np

import Pyro4


class AdrController():
    def __init__(self, sim900_server, relay_server, gui_input=False, gui_message_display=None, startup_state="standby", loop=True):
        self.server = sim900_server
        self.relay_server = relay_server
        self.data=self.server.fetch_dict()
        # Client connection
        
        self.gui_input=gui_input
        self.gui_response=False
        self.message_for_gui=None
        self.gui_message_display=gui_message_display
        # GUI connection
        
        self.exit=False
        self.change_state(startup_state)
        # Sets the current state. Standby by default.
        
        self.refresh_rate=1
        self.ramp_step=0.0
        self.ramp_goal=0.0
        self.pid_goal=0.0
        self.pid_step=0.001
        # parameters for ramping current and pid_setpoint
        
        self.manual_output_now=self.data['pid_manual_out']
        self.pid_setpoint_now=self.data['pid_setpoint']
        # parameters to keep track of the state of the system
        
        self.setup_constants()
        
        
        self.loop_thread=None
        self.command_thread=None
        self.regulate_thread=None
        self.quit_thread=False
        if loop==True:
            self.start_loop_thread()
        
    def setup_constants(self):
        self.pid_max_output=0.0
        self.pid_min_output=-7.0
        # Limits to the pid_manual_output
        
        self.mag_cycle_gain=-1.6
        self.regulate_gain=-11.0
        
    def change_state(self,state):
        self.state=state
        self.server.set_state(state)
        self.show('State changed to %s'%(state))
        
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
                
            self.data=self.server.fetch_dict()
            
            try:
                
                fixing_flag = (self.data['bridge_overload_status']>0) or (self.data['bridge_autorange_gain']>0)
                # tells whether the bridge is using AGAI to fix and overload or not.
                # Probably should just use a flag from the server.
                
                if fixing_flag and (self.data['therm_temperature1'] <= 15 or self.data['therm_temperature2'] <= 15):
                    # Shows us what the overload status is, but only if magnet or floating diode is below 15 K.
                    self.show('Bridge overload status is %f'%(self.data['bridge_overload_status']))
                    self.show('Bridge autorange gain is %d'%(self.data['bridge_autorange_gain']))
                
                if not fixing_flag and self.data['bridge_temp_value']>6:
                    # Temperature check.
                    if not self.state=='standby':
                    # prevents constantly trying to ramp down if already in standby.
                        self.show('Temperature too high, ramping current to zero.')
                        self.ramp_down()
                        # Problem if this case occurs in regulate... Just switch state to standby instead?
                
                if self.state=='regulate':
                
                    if not fixing_flag:
                    # Business as usual.
                    
                        if self.data['pid_manual_status']!=1:
                            # PID was shut off for some reason - probably fixing flag correction.
                            success=self.server.unpause_ramp()
                            if success==False:
                                self.show('Ramp unpause command failed.')
                                continue
                            start=time.time()
                            result=self.data['pid_ramp_status']
                            # Ramp status paused = 3.
                            while result==3:
                                result=self.server.query_pid_ramp_status()
                                tic=time.time()
                                if tic-start>4.0:
                                    break
                            if result==3:
                                self.show('Ramp unpause command sent, but not processed.')
                                continue
                            self.show('Ramp unpaused.')
                            success=self.server.set_pid_manual_status(1)
                            if success==False:
                                self.show('Setting PID on failed.')
                                continue
                            start=time.time()
                            result=self.data['pid_manual_status']
                            while result!=1:
                                result=self.server.query_pid_manual_status()
                                tic=time.time()
                                if tic-start>4.0:
                                    break
                            if result!=1:
                                self.show('PID command sent, but not processed.')
                                continue
                            self.show('PID set to on.')
                    
                        tic=time.time()
                        regulate_time=tic-self.regulate_start
                        if regulate_time>60.0:
                            if self.data['dvm_volts1']<0.01:
                            # If regulate has been running for 60 seconds and the current is too low, it goes to zero current.
                                self.show('Current too low to regulate. Switching to standby.')
                                self.change_state('standby')
                                # This will manually ramp the output to zero... best way to do this?
                        
                            
                    if fixing_flag:
                        if self.data['pid_manual_status']==1:
                            self.show('Switching to manual output and pausing ramp until autorange gain finished.')
                            success=self.server.pause_ramp()
                            if success==False:
                                self.show('Ramp pause command failed.')
                                continue
                            start=time.time()
                            result=self.data['pid_ramp_status']
                            # Ramp status paused = 3, idle = 0
                            while result!=3:
                                result=self.server.query_pid_ramp_status()
                                self.show(str(result))
                                tic=time.time()
                                if result == 0:
                                    break
                                if tic-start>4.0:
                                    break
                            if result!=3:
                                if result!=0:
                                    self.show('Ramp pause command sent, but not processed.')
                                    continue
                                else:
                                    self.show('Ramp in idle mode.')
                            self.show('Ramp paused or idle.')
                            success=self.request_manual_output_on()
                            if success==False:
                                continue
                            self.show('Manual output on.')
                            # Holds the output constant until the overload is fixed.
                        
                if self.state=='starting_ramp':
                    # Ramp is in the process of being called. This state makes sure dwell and standby don't try to toggle something while self.ramp is running.
                    pass
                if self.state=='starting_regulate':
                    # Ramp is in the process of being called. This state makes sure dwell and standby don't try to toggle something while self.ramp is running.
                    pass
                        
                if self.state=='ramping_up':
                    # Make sure the limits haven't been reached.
                    # Make sure current stays within acceptable bounds.
                    # Pid control should stay on.
                    
                    # if goal reached, switch states to either dwell or standby.
                    # if max pid output reached, do the same.
                    if self.data['dvm_volts1']>=self.ramp_goal-0.004:
                        self.request_dwell()
                        raise ValueError('Ramp up goal of %f reached. State switched to dwell.'%(self.ramp_goal))
                    if self.data['pid_output_mon']<=self.pid_min_output:
                        self.request_dwell_at_limit()
                        raise ValueError('Ramp up ended because pid output reached minimum of %f. State switched to dwell.'%(self.pid_min_output))
                        
                if self.state=='ramping_down':
                    if self.data['dvm_volts1']<=self.ramp_goal+0.004:
                        self.change_state('standby')
                        raise ValueError('Ramp down goal of %f reached. State switched to standby.'%(self.ramp_goal))
                    if self.data['dvm_volts1']<=0.0:
                        self.change_state('standby')
                        raise ValueError('Magnet current is at min. State has been set to standby.')
                    if self.data['pid_output_mon']>=self.pid_max_output:
                        self.change_state('standby')
                        raise ValueError('Ramp down ended because pid output reached maximum of %f. State switched to standby.'%(self.pid_max_output))
                        
                        
                        
                if self.state=="dwell":
                    pass
                    
                    # No need to add switching to manual status if we see a fixing flag. PID control based off current, not temperature.
                    
                if self.state=="standby":
                    if self.data['pid_manual_status']==1:
                        # check that manual output on
                        success=self.request_manual_output_on()
                        if success==False:
                            continue
                    if self.data['pid_ramp_on']==1:
                    # check that ramping is off.
                        success=self.server.set_ramp_on(0)
                        if success==False:
                            continue
                    if self.manual_output_now!=0:
                        if abs(self.data['pid_manual_out'])<=0.0001:
                        # If there is a small deviation, manual_output_now should be zero
                            self.manual_output_now=0
                            continue
                        if self.manual_output_now>0:
                            self.ramp_step=0.03*self.refresh_rate
                            new_output=self.manual_output_now-self.ramp_step
                            if abs(self.data['dvm_volts0'])>0.15:
                                # Makes sure the voltage doesn't go above 200 mV
                                time.sleep(self.refresh_rate)
                                continue
                            if new_output<=0:
                                success=self.server.set_manual_output(new_output)
                                if success==True:
                                    self.manual_output_now-=self.ramp_step
                            else:
                                success=self.server.set_manual_output(0)
                        if self.manual_output_now<0:
                            # If below zero (the system started that way, for example) slowly ramp back to zero.
                            # Can't use ramp_up because it uses current.
                            self.ramp_step=0.03*self.refresh_rate
                            new_output=self.manual_output_now+self.ramp_step
                            if abs(self.data['dvm_volts0'])>0.15:
                                # Makes sure the voltage doesn't go above 200 mV
                                self.show('Voltage too high to do another manual step down.')
                                time.sleep(self.refresh_rate)
                                continue
                            if new_output<=0:
                                success=self.server.set_manual_output(new_output)
                                if success==True:
                                    self.manual_output_now+=self.ramp_step
                            else:
                                success=self.server.set_manual_output(0)
                            
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
            
    def request_regenerate(self,pid_setpoint_goal=2.5, peak_current=1.0, ramp_rate_up=-0.005, ramp_rate_down=0.005, dwell_time=0.5):
    
        if self.state!='standby':
            self.show('To regenerate, the controller must be in standby mode.')
            return
        if self.manual_output_now!=0.0:
            self.show('To regenerate, manual output must be zero.')
            return
        if peak_current>9.4:
            self.show('Peak current must be below 9.4.')
            return
        self.quit_thread=False
        self.start_command_thread(pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down, dwell_time)
        
    def start_command_thread(self,pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down, dwell_time):
        if self.command_thread:
            if self.command_thread.is_alive():
                self.show("loop already running")
                return
                
        self.command_thread=threading.Thread(target=self.regenerate_loop,args=(pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down, dwell_time))
        self.command_thread.daemon=True
        self.command_thread.start()
        
    def regenerate_loop(self,pid_setpoint_goal,peak_current,ramp_rate_up, ramp_rate_down, dwell_time):
    
        self.show('Regenerate thread started successfully.')
        self.set_gain(self.mag_cycle_gain)
        if self.quit_thread==True:
            self.show('Regenerate thread exited.')
            return
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
        self.show('Regenerate thread completed successfully.')
        return
                
    def magup(self,peak_current,ramp_rate_up):
        self.request_user_input(message='Switch PID measurement to current.')
        if self.quit_thread==True:
            self.show('Magup exited.')
            return
        time.sleep(0.5)
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
        
### Setting and checking gain. ###

    def set_gain(self,gain):
        gain_now=self.data['pid_propor_gain']
        start=time.time()
        while gain_now!=gain:
            tic=time.time()
            if tic-start>4.0:
                break
            success=self.server.set_pid_propor_gain(gain)
            if success==False:
                continue
            gain_now=self.server.query_pid_propor_gain()
        if gain_now!=gain:
            self.show('Set gain failed.')
            return False
        self.show('Set gain at %f succeeded.'%(gain))
        return True
        
        
### Setting dwell. ###

    def request_dwell_at_limit(self):
        self.change_state('starting_dwell')
        self.request_manual_output_on()
        # Holds manual at steady value
        success=self.set_and_verify_ramp(0)
        if success==False:
            self.show('Turn ramp off in dwell failed.')
            return False
        # Turns ramp off
        output_now=self.data['pid_measure_mon']
        output_now=min(output_now,self.ramp_goal)
        # Chooses the minimum of output_now and the ramp_goal.
        success=self.server.set_pid_setpoint(output_now)
        if success==False:
            self.show('Setting setpoint to output_now unsuccessful in request dwell.')
        # Sets pid setpoint to the value now.
        start=time.time()
        difference=1
        start=time.time()
        while difference>0.1:
            result=self.server.query_pid_setpoint()
            if not isinstance(result,float):
                success=False
                break
            difference=abs(result-output_now)
            tic=time.time()
            if tic-start>3.0:
                success=False
                break
        if success==False:
            self.show('Setpoint output_now command sent, but setpoint not changed in dwell request.')
            return False
        # Checks that the setpoint has actually been set to output now
        success=self.server.set_pid_manual_status(1)
        if success==False:
            self.show('Setting pid output on in request_dwell unsuccessful.')
            return False
        # Turn PID control on.
        
        self.change_state('dwell')
        
    def request_dwell(self):
        self.change_state('dwell')
        
### Ramping methods ###

    def set_and_verify_setpoint(self,setpoint):
        self.server.set_pid_setpoint(setpoint)
        result=self.server.query_pid_setpoint()
        if result!=setpoint:
            self.show('Result of setpoint query was %f'%(result))
            self.set_and_verify_setpoint(setpoint)
        
    '''def set_and_verify_ramp(self,ramp_on):
        if not self.start_recursion:
            self.start_recursion=time.time()
        self.server.set_ramp_on(ramp_on)
        result=self.server.query_pid_ramp_on()
        if not isinstance(result,float):
            self.show('Result of ramp query was %b'%(result))
            self.set_and_verify_ramp(ramp_on)
        if result!=ramp_on:
            self.show('Result of ramp query was %f'%(result))
            self.set_and_verify_ramp(ramp_on)'''
            
    def set_and_verify_ramp(self,ramp_on):
        start_loop=time.time()
        time_passed=0.0
        result=-1
        while result!=ramp_on:
            if time_passed>5.0:
                return False
            self.server.set_ramp_on(ramp_on)
            result=self.server.query_pid_ramp_on()
            time_passed=time.time()-start_loop
            

    def ramp(self,goal,rate):
        # Returns true if everything works, false if there is an error.
        # Switch BNC on measure from bridge to current.

        self.change_state('starting_ramp')
        # Generic state that doesn't do anything to prevent collisions with standby or dwell states.
        
        
        success=self.request_manual_output_on()
        if success==False:
            self.show('Request_manual_output in ramp failed.')
            return False
        success=self.set_and_verify_ramp(0)
        if success==False:
            self.show('Turning ramp off failed')
            return False
        
        
        
        output_now=self.data['pid_measure_mon']
        success=self.server.set_pid_setpoint(output_now)
        if success==False:
            self.show('Setting setpoint to output_now unsuccessful.')
        # Sets pid setpoint to the value now.
        start=time.time()
        difference=1
        start=time.time()
        while difference>0.1:
            result=self.server.query_pid_setpoint()
            if not isinstance(result,float):
                success=False
                break
            difference=abs(result-output_now)
            tic=time.time()
            if tic-start>3.0:
                success=False
                break
        if success==False:
            self.show('Setpoint output_now command sent, but setpoint not changed.')
            return False
        # Checks that the setpoint has actually been set to output now
        success=self.server.set_ramp_rate(rate)
        if success==False:
            self.show('Setting ramp rate in ramp method unsuccessful.')
            return False
        # Set ramp rate
        success=self.server.set_ramp_on(1)
        if success==False:
            self.show('Setting ramp status in ramp method unsuccessful.')
            return False
        # Set ramp on
        success=self.server.set_pid_setpoint(goal)
        if success==False:
            self.show('Setting setpoint goal in ramp method unsuccessful.')
            return False
        # Set new setpoint
        start=time.time()
        difference=1
        start=time.time()
        while difference>0.1:
            result=self.server.query_pid_setpoint()
            if not isinstance(result,float):
                success=False
                break
            difference=abs(result-goal)
            tic=time.time()
            if tic-start>3.0:
                success=False
                break
        if success==False:
            self.show('Setpoint goal command sent, but setpoint not changed.')
            return False
        # Checks that the setpoint has actually been set.
        success=self.server.set_pid_manual_status(1)
        if success==False:
            self.show('Setting pid output on in ramp method unsuccessful.')
            return False
        # Switch from manual to PID
        self.ramp_goal=goal
        self.ramp_step=rate
        self.show('Ramp started with a goal of %f and a rate of %f'%(goal,rate))
        return True
        
    def ramp_up(self,goal,rate=0.005):
        success=self.ramp(goal,rate)
        if success==True:
            self.change_state('ramping_up')
            
    def ramp_down(self,rate=0.005):
        success=self.ramp(0.0,rate)
        if success==True:
            self.change_state('ramping_down')
            
            
### Toggle PID and manual Output ###
            
    def request_manual_output_on(self):
        # Private method.
        # Returns true if executed successfully, false otherwise
        
        self.data=self.server.fetch_dict()
        # Gets fresh data
        output_now=self.data['pid_output_mon']
        # Checks current output.
        success=self.server.set_manual_output(output_now)
        # Sets manual output to that output.
        
        if success == False:
            # Terminate if set_manual_output fails
            return False
        
        # Grab new value and compare them to make sure the command went through.
        difference=1
        start=time.time()
        while difference>0.01:
            result=self.server.query_manual_output()
            if not isinstance(result,float):
                return False
            # Result will not be a float if query_manual_output failed. It will be false.
                
            #self.show('Manual output is now %f'%(result))
            #self.show('Output_mon is now %f'%(output_now))
            difference=abs(result-output_now)
            tic=time.time()
            if tic-start>2.0:
                # Reponse for request_manual_output timed out.
                return False
        
        if self.data['pid_manual_status']==1:
            # If the mode is in PID control...
            success=self.server.set_pid_manual_status(0)
            # Turns manual output on.
            if success==False:
                return False
            
        else:
            self.show('Output mode already manual.')
           
        self.data=self.server.fetch_dict()
        # Makes sure we see the newest data (and get no boomerang effects where we update values based on out-of-date dictionaries)
        self.manual_output_now=self.data['pid_manual_out']
        # Sets the internal variable to the data value.
        self.show('Request manual output on executed successfully.')
        return True

    def request_pid_output_on(self):
        # Private method.
        # Returns true if executed successfully, false otherwise
        
        self.data=self.server.fetch_dict()
        # Gets fresh data
        output_now=self.data['pid_measure_mon']
        success=self.server.set_pid_setpoint(output_now)
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
            result=self.server.query_pid_setpoint()
            if not isinstance(result,float):
                return False
            # Result will not be a float if query_pid_setpoint failed. It will be false.
            
            #self.show('Pid_setpoint is now %f'%(result))
            #self.show('pid_measure_mon is now %f'%(output_now))
            
            difference=abs(result-output_now)
            tic=time.time()
            if tic-start>2.0:
                #Reponse for request_manual_output timed out.
                return False
            
            
        if self.data['pid_manual_status']==0:
            
            success=self.server.set_pid_manual_status(1)
            # Turns pid output on.
            if success==False:
                return False
        else:
            self.show('Output mode already PID.')
            
            
        self.data=self.server.fetch_dict()
        # Makes sure we see the newest data (and get no boomerang effects where we update values based on out-of-date dictionaries)
        self.pid_setpoint_now=self.data['pid_setpoint']
        # Sets the internal variable to the data value.
        self.show('Request pid output on executed successfully.')
        return True
            
            
### Regulate methods and threading ###
        
    def request_regulate(self,pid_setpoint_goal=2.5, pid_ramp_rate=0.001):
    
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
        self.start_regulate_thread(pid_setpoint_goal, pid_ramp_rate)
        
    def start_regulate_thread(self,pid_setpoint_goal,pid_ramp_rate):
        if self.regulate_thread:
            if self.regulate_thread.is_alive():
                self.show("loop already running")
                return
                
        self.regulate_thread=threading.Thread(target=self.regulate_loop,args=(pid_setpoint_goal,pid_ramp_rate))
        self.regulate_thread.daemon=True
        self.regulate_thread.start()
        
    def raise_regulate_user_inputs(self):
        self.request_user_input(message='Switch to regulate resistor.')
        time.sleep(0.5)
        self.request_user_input(message='Switch to BNC PID input to bridge temperature.')
        
    def regulate_loop(self,pid_setpoint,pid_ramp_rate):
        self.raise_regulate_user_inputs()
        self.start_regulate(pid_setpoint,pid_ramp_rate)
        self.show('Regulate loop finished successfully')
        
    def start_regulate(self,pid_setpoint,pid_ramp_rate):
        self.set_gain(self.regulate_gain)
        self.ramp(pid_setpoint,pid_ramp_rate)
        self.regulate_start=time.time()
        self.change_state('regulate')
        
    def update_setpoint(self,setpoint):
        if self.state!='regulate':
            self.show('You cannot update the setpoint outside of regulate.')
            return False
        if self.data['pid_manual_status']!=1:
            self.show('Manual control is on. Wait until PID control is back.')
            return False
        if self.data['pid_ramp_on']!=1:
            self.show('Turning ramp on.')
            success=self.set_and_verify_ramp(1)
            if success==False:
                self.show('Turning ramp on failed.')
                return False
        success=self.server.set_pid_setpoint(setpoint)
        if success==False:
            self.show('Updating setpoint unsuccessful.')
            return False
        # Set new setpoint
        start=time.time()
        difference=1
        start=time.time()
        while difference>0.1:
            result=self.server.query_pid_setpoint()
            if not isinstance(result,float):
                success=False
                break
            difference=abs(result-setpoint)
            tic=time.time()
            if tic-start>3.0:
                success=False
                break
        if success==False:
            self.show('Setpoint goal command sent, but setpoint not changed. Likely reason is PID is in the process of ramping.')
            return False
        self.show('Setpoint update successfully.')
        return True
        

### Standby ###
        
    def request_standby(self,ramp_down=0.005):
        self.show('Standby requested.')
        if self.command_thread or self.regulate_thread:
            self.quit_thread=True
    
        
        if self.state!='regulate' and self.data['dvm_volts1']>=0:
            self.ramp_down(ramp_down)
        else:
            self.request_manual_output_on()
            self.change_state('standby')
            
### Display messages ###

    def show(self,message):
        if self.gui_message_display==None:
            print str(message)
        else:
            # Push to GUI handling function.
            self.gui_message_display(str(message))
            
### Relay commands ###
