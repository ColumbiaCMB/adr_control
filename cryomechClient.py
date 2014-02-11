import pygcp.util.tcpClient as tp
import simplejson as json
import logging

logging.basicConfig()

class cryomechClient():
    def __init__(self, hostname="localhost", port=50002):
        self.logger = logging.getLogger('cryomechClient')
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

    def run_compressor(self, on):
        if on is True:
            s_str = "on"
        elif on is False:
            s_str = "off"
        else:
            self.logger.warn("run_compressor needs to be boolean")
            return -1
        msg = "set run_compressor %s" % s_str
        self.send(msg)
