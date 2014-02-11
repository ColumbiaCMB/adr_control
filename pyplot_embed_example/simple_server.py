import Pyro4
import time
import random
import threading

class simple_server():
    def __init__(self):
        self.data=[]
        self.generate()
        
    def generate(self):
        self.number = random.randint(1,100)
        self.data.append(self.number)
        #print self.data
        # for debugging
        self.timer=threading.Timer(0.5,self.generate)
        self.timer.start()
        
    def fetch_data(self):
        #print "read"
        #print self.data
        #for debugging
        return self.data
    

def main():
    server = simple_server()
    
    Pyro4.Daemon.serveSimple(
            {
                server: "simple_server"
            },
            ns=True)

if __name__=="__main__":
    main()
