from binascii import *
from time import sleep

class smdp:
    def __init__(self,address,use_srlnum=True):

        self.use_srlnum = use_srlnum
        self.address = chr(address)
        self.stx = '\x02'
        self.wtf = '\x80'
        self.eol = ''
        self.zero_d = '\x07\x31'
        self.zero_two = '\x07\x30'
        self.zero_seven = '\x07\x32'
        self.serlnum=0x41
        self.start_str = self.stx+self.address
        if self.use_srlnum is True:
            self.chk_add = 0x40
        else:
            self.chk_add = 0x30

    def construct_msg(self,cmd):
        self.cmd = cmd
        self.st_send = self.start_str + self.wtf
        self.rep_cmd = ''
        #Look for replacements
        for c in self.cmd:
            if c == '\x0D':
                self.rep_cmd = self.rep_cmd + self.zero_d
            elif c == '\x02':
                self.rep_cmd = self.rep_cmd + self.zero_two
            elif c == '\x07':
                self.rep_cmd = self.rep_cmd + self.zero_seven
            else:
                self.rep_cmd = self.rep_cmd + c

        self.st_send = self.st_send + self.rep_cmd
        if self.use_srlnum is True:
            self.st_send = self.st_send + chr(self.serlnum)

        self.chk_sum = self.compute_checksum()
        self.st_send = self.st_send + self.chk_sum + self.eol
        return self.st_send

    def compute_checksum(self):
        #Strip out first character
        if self.use_srlnum is True:
            chk_cmd = self.address+self.wtf+self.cmd+chr(self.serlnum)
        else:
            chk_cmd = self.address+self.wtf+self.cmd

        chksum = 0
        for c in chk_cmd:
            chksum = chksum + int(b2a_hex(c),16)

        chksum = chksum & 0xFF
        chk_one = ((chksum & 0xF0) >> 0x04) + self.chk_add
        chk_two = (chksum & 0x0F) + self.chk_add

        return chr(chk_one)+chr(chk_two)

    def destruct_answer(self,result):
        temp_result = result

        #We need to find any occourances of special character
        result = result.replace(self.zero_d,'\x0d')
        result = result.replace(self.zero_two, '\x02')
        result = result.replace(self.zero_seven, '\x07')
        
        if len(result) != 15:
            print temp_result
            print len(result), b2a_hex(result)
            print "SMDP - STUPID protocol will fail with this"
            print "You will get gibberish"

        #Split up into consitiuant parts
        header = result[0:2]
        #Just read backwards to get the data
        data = result[-8:-4]
        srnum = result[-4]
        chksum = result[-3:-1]

        #Should put full error checking in but will just
        #Use serial if present

        if self.use_srlnum is True:
            if srnum != chr(self.serlnum):
                print "SMDP - Serial Numbers do not match"
                self.result = -99
                return -1
    
        #We should have a good reply so increase serial number
        self.serlnum = (self.serlnum + 1) & 0xFF
        if self.serlnum < 0x10:
            self.serlnum = 0x11

        #Convert data to int
        
        sign = int(b2a_hex(data[0]),16) >> 0x07 
        result = int(b2a_hex(data),16) & 0x7FFFFFFF
        if sign == 1:
            result = result - 0x7FFFFFFF -0x01 
        
        self.result = result

        return self.result




                                
            

