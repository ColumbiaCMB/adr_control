import Pyro4
import time
import sim900_communicator
import threading

'''generic_command_dictionary={
                                    1:
                                        [{'command':'TVAL?','name':'bridge_temp','scaling':1.0}],
                                    5:
                                        [{'command':'TVAL? 1','name':'50k_temp','scaling':1.0},{'command':'TVAL? 3','name':'4k_temp','scaling':1.0}],
                                    7:
                                        [{'command':'VOLT? 1','name':'mag_volt','scaling':1.0},{'command':'VOLT? 2','name':'mag_current','scaling':1.0}]
                                }'''
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
                                        {'command':'AOUT?','name':'bridge_output_value','scaling':1.0}
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
        self.local_terminator = "\n\r"
        self.data={}
        self.start_time=time.time()
        
        self.lock=threading.Lock()
        
        self.communicator=sim900_communicator.CleanComm(self.lock)
        # Start up to connect to real sim900
        
        #self.communicator=sim900_communicator.CleanComm(self.lock,host='localhost',port=13579)
        # Start up to connect to fake sim900
        
        self.command_dictionary=command_dictionary
        
        
        self.loop_thread=None
        self.start_loop_thread()
        
        self.state=0
        
        
    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                print "loop already running"
                return
        self.loop_thread=threading.Thread(target=self.follow_command_dict)
        self.loop_thread.daemon=True
        self.loop_thread.start()
        
        
    def follow_command_dict(self):
        # Format {'port':[list of queries to that port of the format {query, name , scaling function}
        # Returns dictionary of format {name:value, name2: value2, etc} (already multiplied by scaling function?)
        # Example {4: [{query: TVAL? 1, name: bridge_temp, scaling function: 1.0, value: FILL THIS IN WITH RETURN STATEMENT},{another dict for each other command or make each input a list?}]}
        
        while True:
        
            start=time.time()
        
            for i in self.command_dictionary.keys():
            # Cycles over all the ports
                port=i
                for j in self.command_dictionary[i]:
                # cycles over all the commands for each port.
                    
                    tic=time.time()
                    
                    msg=j['command']
                    result=self.communicator.query_port(port,msg)
                    if 'n_elements' in j:
                    # check whether there are more than one element in the query.
                    # if so, we need to slice them up.
                        results=result.split(',')
                        self.data[j['name']]=results
                    else:
                        self.data[j['name']]=result
                        
                    toc=time.time()
                    print '%s took %f seconds' % (msg,(toc-tic))
                        
            self.data['time']=time.time()
            
            print "Total process took %f seconds" %(self.data['time']-start)
            print
            
            print self.data
        
    def fetchDict(self):
        return self.data
        
    def send(self,msg):
        # Note that this method has no error checking to make sure the command is valid. That needs to happen before this method is called.
        
        self.communicator.send(msg)
        
    def regenerate(self):
        # Just a test
        if self.state==0:
            self.send('SNDT 3, "PCTL 1"')
            self.send('SNDT 3, "ICTL 1"')
            self.send('SNDT 3, "DCTL 1"')
            self.state=1
        else:
            self.send('SNDT 3, "PCTL 0"')
            self.send('SNDT 3, "ICTL 0"')
            self.send('SNDT 3, "DCTL 0"')
            self.state=0

def main():
    sim900=sim900Server(hostname="192.168.1.152")
    Pyro4.Daemon.serveSimple(
            {
                sim900: "sim900server"
            },
            ns=True)

if __name__=="__main__":
    main()

