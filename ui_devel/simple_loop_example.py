import threading
import time

class loop(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.exit=False
        self.count=1
        self.state="Odd"
    def run(self):
        while True:
            if self.exit==True:
                return 0
            print self.state
            self.count+=1
            self.switch()
            time.sleep(3)
            
    def switch(self):
        if self.count%2==0:
            self.state="Even"
        else:
            self.state="Odd"
    def a(self):
        if self.exit==False:
            self.exit=True
        else:
            self.exit=False
