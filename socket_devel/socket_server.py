import Pyro4
import time
import locked_sim900_socket
import threading

generic_command_dictionary={
                                    1:
                                        [{'command':'TVAL?','name':'bridge_temp','scaling':1.0}],
                                    5:
                                        [{'command':'TVAL? 1','name':'50k_temp','scaling':1.0},{'command':'TVAL? 3','name':'4k_temp','scaling':1.0}],
                                    7:
                                        [{'command':'VOLT? 1','name':'mag_volt','scaling':1.0},{'command':'VOLT? 2','name':'mag_current','scaling':1.0}]
                                }


class sim900Client():

# This server will register in pyro namespace, continuously run, and push commands from adr_controller to the sim900.

    def __init__(self, command_dictionary=generic_command_dictionary, hostname="localhost", port=50001):
        self.local_terminator = "\n\r"
        self.data={"bridge_temperature_setpoint":0.2}
        self.start_time=time.time()
        
        self.lock=threading.Lock()
        self.sock=locked_sim900_socket.CleanSocket(self.lock)
        
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
        
            for i in self.command_dictionary.keys():
            # Cycles over all the ports
                port=i
                for j in self.command_dictionary[i]:
                # cycles over all the commands for each port.
                    msg=j['command']
                    result=self.sock.query_port(port,msg)
                    self.data[j['name']]=result
                    # replace the 0.0 with whatever locked_socket.query returns. Perhaps recast as float and multiply by scaling function.
            self.data['time']=time.time()
            print self.data
            
            #time.sleep(1.0)
            # Take this out when connected to server.
        
    def fetchDict(self):
        return self.data
        
    def send(self,msg):
        # Note that this method has no error checking to make sure the command is valid. That needs to happen before this method is called.
        
        self.sock.send(msg)
        
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
    sim900=sim900Client(hostname="192.168.1.152")
    Pyro4.Daemon.serveSimple(
            {
                sim900: "sim900server"
            },
            ns=True)

if __name__=="__main__":
    main()

