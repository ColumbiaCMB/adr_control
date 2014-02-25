import Pyro4
import time
import threading

class sim900Client():

# This server will register in pyro namespace, continuously run, and push commands from adr_controller to the sim900.

    def __init__(self, hostname="localhost", port=50001):
        #self.data={"time":0,"bridge_temperature_setpoint":1,"bridge_temp_value":1,"therm_temperature":[0,0,0],"dvm_volts":[0,0]}
        self.data={'bridge_temperature_setpoint':0.0}
        
        self.command_dictionary={   1:
                                        [{'command':'TVAL?','name':'bridge_temp','scaling':1.0}],
                                    5:
                                        [{'command':'TVAL? 1','name':'50k_temp','scaling':1.0},{'command':'TVAL? 3','name':'4k_temp','scaling':1.0}],
                                    7:
                                        [{'command':'VOLT? 1','name':'mag_volt','scaling':1.0},{'command':'VOLT? 2','name':'mag_current','scaling':1.0}]
                                }
        # Eventually, this will be a passed argument.
        # Note that I have to figure out what to do when querying a port multiple times. I will need some sort of list, whether it is a list of dictionaries under the port, a list of commands, or 
        # a list of names, and then input the data as a list. The last seems most simple, except if I need to query TVAL and VOLT on one port (which is likely).
        
        
        self.lock=threading.Lock()
        
        
        self.loop_thread=None
        self.start_loop_thread()
        
        
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
        
            for i in self.command_dictionary.keys():
            # Cycles over all the ports
                port=i
                for j in self.command_dictionary[i]:
                # cycles over all the commands for each port.
                    msg=j['command']
                    # self.locked_socket.query(port,msg)
                    self.data[j['name']]=0.0
                    # replace the 0.0 with whatever locked_socket.query returns. Perhaps recast as float and multiply by scaling function.
            self.data['time']=time.time()
            print self.data
            
            time.sleep(2.0)
            # Take this out when connected to server.
        
        
    def fetchDict(self):
        # This is camel case for legacy reasons. Once a final server is programmed, name this fetch_dict.
        return self.data
        
def main():
    sim900=sim900Client(hostname="192.168.1.152")
    Pyro4.Daemon.serveSimple(
            {
                sim900: "sim900server"
            },
            ns=True)

if __name__=="__main__":
    main()

        
