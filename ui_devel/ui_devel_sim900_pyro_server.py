import Pyro4
import simplejson as json
import random

class sim900Client():
    def __init__(self, hostname="localhost", port=50001):
        self.local_terminator = "\n\r"
        self.fakedata={"bridge_temperature_setpoint":1,"bridge_temp_value":1,"therm_temperature":[0,0,0],"dvm_volts":[0,0]}
        
    def send(self,msg):
    # This is just for testing for now. Eventually it should send a command to the socket which is connected to the sim900.
    # Also, the msg should be machine readable, rather than the current syntax.
        print msg
        
    def fetchDict(self):
    # Loads up an empty dict for now.
        self.send("read")
        btv=random.uniform(0.99,1.01)
        self.fakedata["bridge_temp_value"]=btv
        return self.fakedata
        
        
    def regulate(self):
        msg = "regulate"
        self.send(msg)
    def regenerate(self):
        msg = "regenerate"
        self.send(msg)
    def stop(self):
        msg = "stop"
        self.send(msg)
    # These are placeholders for the clickbutton commands.
    
    def increase_current(self,current):
        self.fakedata["dvm_volts"][1]=current
        
    def setSetpoint(self, setpoint):
        msg = "set setpoint %f" % setpoint
        self.send(msg)
        
    def setPIDSetpoint(self, setpoint):
        msg = "set pid_setpoint %f" % setpoint
        self.send(msg)

    def setBridgeSetpoint(self, setpoint):
        msg = "set bridge_setpoint %f" % setpoint
        self.send(msg)
        
    def setRampOn(self, on):
        msg = "set ramp_state %i" % int(on)
        self.send(msg)

    def setRampRate(self, rate):
        msg = "set ramp_rate %f" % rate
        self.send(msg)
        
    def setPropOn(self, on):
        msg = "set prop_state %i" % int(on)
        self.send(msg)

    def setPropGain(self, rate):
        msg = "set prop_gain %f" % rate
        self.send(msg)

    def setIntOn(self, on):
        msg = "set int_state %i" % int(on)
        self.send(msg)

    def setIntGain(self, rate):
        msg = "set int_gain %f" % rate
        self.send(msg)

    def setDerivOn(self, on):
        msg = "set deriv_state %i" % int(on)
        self.send(msg)

    def setDerivGain(self, rate):
        msg = "set deriv_gain %f" % rate
        self.send(msg)

    def setOffsetOn(self, on):
        msg = "set offset_state %i" % int(on)
        self.send(msg)

    def setOffset(self, rate):
        msg = "set offset %f" % rate
        self.send(msg)
        
    def setManualOutput(self,voltage):
        msg = "set manual_output %f" % voltage
        self.send(msg)
    
    def setPIDControl(self,on):
        msg = "set pid_state %i" % int(on)
        self.send(msg)
        
    def setLimLow(self, low):
        msg = "set low_lim %f" % low
        self.send(msg)

    def setLimHigh(self, high):
        msg = "set upper_lim %f" % high
        self.send(msg)

def main():
    sim900=sim900Client(hostname="192.168.1.152")
    Pyro4.Daemon.serveSimple(
            {
                sim900: "sim900server"
            },
            ns=True)

if __name__=="__main__":
    main()

