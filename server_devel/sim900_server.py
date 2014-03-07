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
        self.data={}
        self.state='standby'
        
        self.server_lock=threading.Lock()
        # Make sure server methods don't collide. In particular, I don't want to try sending a command while the follow_command_dict
        # is talking to a specific port.
        
        self.communicator=sim900_communicator.CleanComm()
        # Start up to connect to real sim900
        
        #self.communicator=sim900_communicator.CleanComm(self.communicator_lock,host='localhost',port=13579)
        # Start up to connect to fake sim900
        
        self.command_dictionary=command_dictionary
        
        
        self.loop_thread=None
        self.start_loop_thread()
        
        self.state=0
        self.fixing=False
        
        self.flag_available=True
        
        
    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                print "loop already running"
                return
        self.loop_thread=threading.Thread(target=self.follow_command_dict)
        self.loop_thread.daemon=True
        self.loop_thread.start()
            
    def follow_command_dict(self):
    
        self.communicator.send('xyx')
        # Makes sure we always start at the top level of the sim900.
        
        while True:
        
            start=time.time()
        
            for i in self.command_dictionary.keys():
            # Cycles over all the ports
            
            
                #start_port_time=time.time()
                port=i
                connect_msg='CONN %d, "xyx"'%(port)
                
                self.server_lock.acquire()
                
                try:
                    # Makes sure communicator will send the 'xyx' to go back to sim900.
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
                    raise e
                finally:
                    #end_port_time=time.time()
                    #print 'Port %d done, it took %f seconds'%(port,(end_port_time-start_port_time))
                    self.server_lock.release()
                    self.communicator.send('xyx')
            self.data['time']=time.time()
            
            print "Total data loading took %f seconds" %(self.data['time']-start)
            print 'self.flag_available is %s'%(str(self.flag_available))
            
            if self.data['bridge_overload_status']>0:
                print 'Bridge is overloaded'
                if self.data['bridge_autorange_gain']!=1:
                    print 'Sending correction'
                    self.send(1,'AGAI ON')
                else:
                    print 'Correction in progress'
        
    def fetch_dict(self):
        return self.data
        
    def fetch_state(self):
        return self.state
        
    def set_state(self,state):
        self.state=state
        
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
        
    # These methods are used to coordinate with the controller.
        
    def regenerate(self):
        # Just a test that is very easy to observe (all PID lights go on and off)
        
        self.server_lock.acquire()
        try:
            self.communicator.send('xyx')
            # Makes sure we always start at the top level of the sim900.
            print 'regenerate'
            if self.state==0:
                self.communicator.send('SNDT 3, "PCTL 1"')
                self.communicator.send('SNDT 3, "ICTL 1"')
                self.communicator.send('SNDT 3, "DCTL 1"')
                self.state=1
            else:
                self.communicator.send('SNDT 3, "PCTL 0"')
                self.communicator.send('SNDT 3, "ICTL 0"')
                self.communicator.send('SNDT 3, "DCTL 0"')
                self.state=0
        except:
            raise
        finally:
            self.server_lock.release()
        
    def send_direct(self,port,msg):
        # Sends directly. Use only once the lock is acquired.
        self.communicator.send('xyx')
        new_msg='SNDT %d, "%s"'%(port,msg)
        self.communicator.send(new_msg)
        
        
    def send(self,port,msg):
        # Wraps send_direct in locks, makes sure locks are released.
        self.server_lock.acquire()
        try:
            self.send_direct(port,msg)
        except:
            raise
        finally:
            self.server_lock.release()
        
    def query_port(self,port,msg):
        # Wraps query_port_direct in locks, makes sure locks are released.
        # For querying ports when not in CONN mode.
        # Originally, this was used to populate the dictionary rather than the CONN method.
        # However it was slower (by a factor of 2).
        # It is simpler and faster for individual queries, however.
        self.server_lock.acquire()
        try:
            result=self.query_port_direct(port,msg)
            return result
        except:
            raise
        finally:
            self.server_lock.release()
            
    def query_port_direct(self,port,msg):
        # Query port directly. Use only once lock is acquired.
        self.communicator.send('xyx')
        result=self.communicator.query_port(port,msg)
        if port in self.command_dictionary:
            for each in self.command_dictionary[port]:
                if each['command']==msg:
                    self.data[each['name']]=float(result)
                    print 'out of date value updated'
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

