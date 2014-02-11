#Simple sim900Client
import pygcp.util.tcpClient as tp
import simplejson as json
import logging

logging.basicConfig()
# What does logging do? Is it necessary? Probably should test this out.

# Only thing from original sim900client that wasn't necessary was the limlow and limhigh, which weren't hooked up to anything.
# Actually put them in. They were used by fridgecycle, which I will integrate into the new software.


class sim900Client():
    def __init__(self, hostname="localhost", port=50001):
        self.logger = logging.getLogger('SIM900Client')
        self.logger.setLevel(logging.INFO)
        self.conn = tp.tcpClient(hostname,port,terminator="\n")
        self.conn.connect()
        self.local_terminator = "\n\r"

    def send(self,msg):
        #For some reason the twister code requires another \n\r
        self.conn.send(msg + self.local_terminator)
        
    def fetchDict(self):
        self.send("read")
        self.conn.recv()
        data = self.conn.data_message
        self.data = json.loads(data)
        
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
    
