import Pyro4
import time
import sim900_communicator
import threading
import numpy as np

downstairs_command_dictionary={
                                    1:
                                        [
                                        {'command':'TVAL?','name':'bridge_temp_value','scaling':1.0},
                                        {'command':'TDEV?','name':'bridge_temp_deviation','scaling':1.0},
                                        {'command':'RVAL?','name':'bridge_res_value','scaling':1.0},
                                        {'command':'RDEV?','name':'bridge_res_deviation','scaling':1.0},
                                        {'command':'PHAS?','name':'bridge_phase','scaling':1.0},
                                        {'command':'FREQ?','name':'bridge_frequency','scaling':1.0},
                                        {'command':'RANG?','name':'bridge_range','scaling':1.0},
                                        {'command':'EXCI?','name':'bridge_excitation','scaling':1.0},
                                        {'command':'EXON?','name':'bridge_excitation_on','scaling':1.0},
                                        {'command':'MODE?','name':'bridge_excitation_mode','scaling':1.0},
                                        {'command':'IEXC?','name':'bridge_excitation_current','scaling':1.0},
                                        {'command':'VEXC?','name':'bridge_excitation_volt','scaling':1.0},
                                        {'command':'ATEM?','name':'bridge_output_temperature','scaling':1.0},
                                        {'command':'RSET?','name':'bridge_res_setpoint','scaling':1.0},
                                        {'command':'TSET?','name':'bridge_temperature_setpoint','scaling':1.0},
                                        {'command':'VOHM?','name':'bridge_volts_ohms','scaling':1.0},
                                        {'command':'VKEL?','name':'bridge_volts_kelvin','scaling':1.0},
                                        {'command':'AMAN?','name':'bridge_output_mode','scaling':1.0},
                                        {'command':'AOUT?','name':'bridge_output_value','scaling':1.0},
                                        {'command':'OVCR?','name':'bridge_overload_status','scaling':1.0},
                                        {'command':'AGAI?','name':'bridge_autorange_gain','scaling':1.0}
                                        ],
                                    3:
                                        [
                                        {'command':'SMON?','name':'pid_setpoint_mon','scaling':1.0},
                                        {'command':'SETP?','name':'pid_setpoint','scaling':1.0},
                                        {'command':'MMON?','name':'pid_measure_mon','scaling':1.0},
                                        {'command':'EMON?','name':'pid_error_mon','scaling':1.0},
                                        {'command':'OMON?','name':'pid_output_mon','scaling':1.0},
                                        {'command':'PCTL?','name':'pid_propor_on','scaling':1.0},
                                        {'command':'ICTL?','name':'pid_integral_on','scaling':1.0},
                                        {'command':'DCTL?','name':'pid_deriv_on','scaling':1.0},
                                        {'command':'OCTL?','name':'pid_offset_on','scaling':1.0},
                                        {'command':'GAIN?','name':'pid_propor_gain','scaling':1.0},
                                        {'command':'APOL?','name':'pid_polarity','scaling':1.0},
                                        {'command':'INTG?','name':'pid_integral_gain','scaling':1.0},
                                        {'command':'DERV?','name':'pid_deriv_gain','scaling':1.0},
                                        {'command':'OFST?','name':'pid_offset','scaling':1.0},
                                        {'command':'RATE?','name':'pid_ramp_rate','scaling':1.0},
                                        {'command':'RAMP?','name':'pid_ramp_on','scaling':1.0},
                                        {'command':'RMPS?','name':'pid_ramp_status','scaling':1.0},
                                        {'command':'MOUT?','name':'pid_manual_out','scaling':1.0},
                                        {'command':'AMAN?','name':'pid_manual_status','scaling':1.0}
                                        ],
                                    
                                    5:
                                        [
                                        {'command':'TVAL? 0','name':'therm_temperature','scaling':1.0, 'n_elements':4},
                                        {'command':'VOLT? 0','name':'therm_volts','scaling':1.0, 'n_elements':4}
                                        ],
                                        
                                    6:
                                        [
                                        {'command':'CHAN?','name':'mx_channel','scaling':1.0}
                                        ],
                                    7:
                                        [
                                        {'command':'VOLT? 0','name':'dvm_volts','scaling':1.0, 'n_elements':4},
                                        {'command':'VGND? 0','name':'dvm_gnd','scaling':1.0, 'n_elements':4},
                                        {'command':'VREF? 0','name':'dvm_ref','scaling':1.0, 'n_elements':4}
                                        ]
                                        
                                }
                                
                                


class sim900Server():

# This server will register in pyro namespace, continuously run, and push commands from adr_controller to the sim900.

    def __init__(self, command_dictionary=downstairs_command_dictionary, hostname="localhost", port=50001):
        self.data={'group':'sim900'}
        self.state='standby'
        
        self.communicator_lock=threading.Lock()
        
        self.server_lock=threading.Lock()
        # Make sure server methods don't collide. In particular, I don't want to try sending a command while the follow_command_dict
        # is talking to a specific port.
        
        self.communicator=sim900_communicator.CleanComm(self.communicator_lock)
        # Start up to connect to real sim900
        
        #self.communicator=sim900_communicator.CleanComm(self.communicator_lock,host='localhost',port=13579)
        # Start up to connect to fake sim900
        
        self.command_dictionary=command_dictionary
        
        
        self.loop_thread=None
        self.start_loop_thread()
        
        self.state=0
        self.fixing=False
        
        self.flag_available=True
        
        self.overload_wait=0
        
        
    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                print "loop already running"
                return
        self.loop_thread=threading.Thread(target=self.follow_command_dict)
        self.loop_thread.daemon=True
        self.loop_thread.start()
            
# Functional loop (following the command dictionary to populate data)
            
    def follow_command_dict(self):
    
        self.go_to_mainframe()
        # Makes sure we always start at the top level of the sim900.
        
        while True:
        
            start=time.time()
        
            for i in self.command_dictionary.keys():
            # Cycles over all the ports
            
            
                #start_port_time=time.time()
                port=i
                connect_msg='CONN %d, "xxx"'%(port)
                
                self.server_lock.acquire()
                
                try:
                    # Makes sure communicator will send the 'xxx' to go back to sim900.
                    # It doesn't work. After shutting down unexpectedly, it gets stuck in another sim module.
                    self.communicator.send(connect_msg)
                    
                    for j in self.command_dictionary[i]:
                    # cycles over all the commands for each port.
                    
                        #tic=time.time()
                        
                        msg=j['command']
                        result=self.communicator.fast_send_and_receive(msg)
                        if 'n_elements' in j:
                        # check whether there are more than one element in the query.
                        # if so, we need to slice them up.
                            results=result.split(',')
                            for i in range(len(results)):
                                # Slices lists into separate dictionary entries.
                                results[i]=float(results[i])
                                newkey=j['name']+str(i)
                                try:
                                    self.data[newkey]=results[i]
                                except ValueError as e:
                                    print 'Value error in key %s. NaN inserted. Error printed below.'%(key)
                                    print e
                                    self.data[newkey]=np.nan
                            
                        else:
                            # Error catching for unconvertable strings.
                            try:
                                self.data[j['name']]=float(result)
                            except ValueError as e:
                                print 'Value error in key %s. NaN inserted. Error printed below.'%(key)
                                print e
                                self.data[j['name']]=np.nan
                            
                        #toc=time.time()
                        #print '%s took %f seconds' % (msg,(toc-tic))
                except Exception as e:
                
                    print 'ERROR ENCOUNTERED. Loop ended, lock released, and system will try to go back to mainframe.'
                    print e
                    
                finally:
                    #end_port_time=time.time()
                    #print 'Port %d done, it took %f seconds'%(port,(end_port_time-start_port_time))
                    self.server_lock.release()
                    self.go_to_mainframe()
                    
            self.data['time']=time.time()
            
            print "Total data loading took %f seconds" %(self.data['time']-start)
            print 'self.flag_available is %s'%(str(self.flag_available))
            
            if self.data['bridge_overload_status']>0:
                # Waits for five cycles to see if the error fixes itself, then sends a command to autorange gain.
                print 'Bridge is overloaded %d'%(self.data['bridge_overload_status'])
                
                if self.data['bridge_autorange_gain']==1:
                    print 'Correction in progress'
                    
                else:
                    if self.overload_wait<5:
                        self.overload_wait+=1
                    else:
                        print 'Sending correction'
                        self.send(1,'AGAI ON')
                        self.overload_wait=0
                    
# Simple getting functions
        
    def fetch_dict(self):
        return self.data
        
    def fetch_state(self):
        return self.state
        
    def set_state(self,state):
        self.state=state
        
### Flag handling
    # These methods are used to coordinate with the controller.
    def get_flag(self):
    # Used by controller to get action flag.
        if self.flag_available:
            self.flag_available=False
            return True
        else:
            return False
            
    def give_flag(self):
    # Used by controller to give back action flag.
        self.flag_available=True
        
### Stub sending functions

    def set_pid_setpoint(self, setpoint):
        msg='SETP %f'%(setpoint)
        return self.send(3,msg)
        
    def query_pid_setpoint(self):
        result=self.query_port(3,'SETP?')
        if result==False:
            return False
        else:
            try:
                return float(result)
            except ValueError as e:
                print e
                return False
        
    def set_manual_output(self,manual_out):
        msg='MOUT %f'%(manual_out)
        return self.send(3,msg)
        
    def query_manual_output(self):
        result=self.query_port(3,'MOUT?')
        if result==False:
            return False
        else:
            try:
                return float(result)
            except ValueError as e:
                print e
                return False
    
    def set_pid_manual_status(self,manual_status):
        msg='AMAN %d'%(manual_status)
        return self.send(3,msg)
        
### Manual sending functions    
        
    def go_to_mainframe(self):
        self.server_lock.acquire()
        try:
            self.communicator.send('xxx')
            return True
        except Exception as e:
            print 'Error encountered when sending CONN terminator ("xxx").'
            print e
            return False
            
            # Need more error checking?
            
        finally:
            self.server_lock.release()
        
    def send_direct(self,port,msg):
        # Sends directly. Use only once the lock is acquired.
        new_msg='SNDT %d, "%s"'%(port,msg)
        self.communicator.send(new_msg)
        
        
    def send(self,port,msg):
        # Wraps send_direct in locks, makes sure locks are released.
        
        self.go_to_mainframe()
        
        self.server_lock.acquire()
        try:
            self.send_direct(port,msg)
            return True
        except Exception as e:
            print 'Error encountered when sending message %s to port %d'%(msg,port)
            print e
            return False
        finally:
            self.server_lock.release()
        
        
        
    def query_port(self,port,msg):
        # Wraps query_port_direct in locks, makes sure locks are released.
        # For querying ports when not in CONN mode.
        # Originally, this was used to populate the dictionary rather than the CONN method.
        # However it was slower (by a factor of 2).
        # It is simpler and faster for individual queries, however.
        
        self.go_to_mainframe()
        
        self.server_lock.acquire()
        try:
            result=self.query_port_direct(port,msg)
            return result
        except Exception as e:
            print 'Error encountered when sending message %s to port %d'%(msg,port)
            print e
            return False
        finally:
            self.server_lock.release()
            
    def query_port_direct(self,port,msg):
        # Query port directly. Use only once lock is acquired.
        result=self.communicator.query_port(port,msg)
        
        if port in self.command_dictionary:
            for each in self.command_dictionary[port]:
                if each['command']==msg:
                    try:
                        self.data[each['name']]=float(result)
                        print 'out of date value updated, %s is now %f'%(each['name'],float(result))
                    except ValueError as e:
                        print e
        return result
        # If the result belongs in self.data, the value is updated. Query_port is often used for verification after setting
        # pid_manual_out or pid_setpoint to a new value. It takes ~2.5 seconds for the server to 'catch up' to this reset on its own,
        # which causes problems when we rely on the new information (such as ramping up or down).
        # The solution is to manually update the server's data dictionary.

def main():
    sim900=sim900Server(hostname="192.168.1.152")
    Pyro4.Daemon.serveSimple(
            {
                sim900: "sim900server"
            },
            ns=True)

if __name__=="__main__":
    main()

