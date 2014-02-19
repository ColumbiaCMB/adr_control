import socket
import time

class CleanSocket():
    def __init__(self):
        self.host="192.168.1.151"
        self.port=4001
        self.address=(self.host,self.port)
        
    def send(self,msg,terminator='\r\n'):
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        try:
            sock.connect(self.address)
        except:
            print "Socket unable to connect."
            return
            
        
        try:
            sock.send(msg+terminator)
        except:
            print "socket unable to send message"
        finally:
            sock.close()
            return
        
            
    def send_and_receive(self,msg,terminator='\r\n'):
        # Added the self.terminator option in case CONN is being used and terminator control should be manual (in which case set terminator = None).
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.settimeout(2)
        data=None
        
        try:
            sock.connect(self.address)
        except socket.error:
            print "Socket unable to connect. Check that no other sockets are connected."
            raise
            # Instead of returning None here, raise an exception. Ditto for other parts of this code.
            
        try:
            sock.send(msg+terminator)
        except:
            print "socket unable to send message"
            sock.close()
            raise
            
        time.sleep(0.1)
        
        try:
            data = sock.recv(1024)
        except:
            print "Nothing received"
            raise
        finally:
            sock.close()
            return data
        
            
    def interpret(self,port,timeout=2):
        # grabs data using query_loop
        # runs until timeout or terminator reached (\r\n)
        # discards #3xxx, concatenates middle into a string.
        # Should discard ending as well, but not doing so reveal some interesting information about how the sim900 works.
        
        accumulated_data=''
        terminator_flag=False
        start=time.time()
        tic=time.time()
        
        while terminator_flag==False and tic-start<timeout:
            data=self.query_loop(port)
            for i in range(5,len(data)):
                accumulated_data+=data[i]
                if data[i]=='\r':
                    terminator_flag=True
            tic=time.time()
        return accumulated_data
        
            
    def query_port(self,port, msg, terminator='\r\n'):
        # For easy talking to ports. Sends the question, then retrieves the answer with GETN command to port.
        # Good test: port=3, msg='*IDN?'
        
        format_msg='SNDT %d, "%s"' % (port,msg)
        self.send(format_msg)
        # Sends the message
        
        #time.sleep(0.1)
        # Problem: without this sleep query_loop finds (empty data #3000) before the sim900 has a chance to process the new query.
        # Is the sim900 a stack so we have >sndt >getn ... getn> sndt>?
        # Another problem: the amount of time it takes for the sim900 to give an output changes depending on what you're asking.
        
        '''data='#3000'
        # This is our null result, and we initialize it to this value.
        start=time.time()
        tic=time.time()
        
        while (data[:5] == '#3000') and (tic-start<2):
            # This assumes we will NOT get an empty result back and forces our program to look until
            # time runs out or we find a non-empty answer.
            data=self.query_loop(port)
            tic=time.time()
            
        # Problem: sim writes slowly, each time updating the number of bytes. This means we often get a partial answer.
        # Solutions: check back a couple times to see if any more data is in the buffer?'''
        
        return self.interpret(port)
        
        
    def query_loop(self,port,terminator='\r\n'):
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        try:
            sock.connect(self.address)
            sock.setblocking(0)
        except socket.error:
            print "Socket unable to connect. Check that no other sockets are connected."
            raise
            # Instead of returning None here, raise an exception. Ditto for other parts of this code.
            
        try:
            msg='GETN? %d,100' % (port)
            sock.send(msg+terminator)
        except:
            print "socket unable to send message"
            sock.close()
            raise
            
        start=time.time()
        tic=time.time()
        # For manually limiting the time for my while loop
        
        data=''
        new_data=None
        # data comes in strings. Starts an empty string and sets new_data to None.
        
        expected_data_length=5
        has_extended=False
        # How long should data be, and whether we have adjusted the length based on the data it gives us.
        
        while (tic-start<2) and (len(data)<expected_data_length):
        # This loop constantly looks for new data until 2 seconds have passed, or the data has at least 4 characters.
        # Note that data from the sim900 will ALWAYS have at least 5 characters: #3xxx where xx is the amount of bytes of data
        # following the intro.
        
        # Now... adjust the length requirement based on the xxx.
         
            # print tic-start
            # for debugging
            
            try:
                new_data=sock.recv(1024)
            except:
                #catches timeout, but that isn't an error python recognizes, so I can't refer to it by name...
                # would be good to not catch all errors, just timeout.
                
                #print 'no data'
                #for debugging
                
                new_data=None
                # If new data hasn't come in, there is no new data.
                
            if new_data != None:
                data+=new_data
                # Add new data to total data if there is is new data.
                
            if (has_extended==False) and (len(data)>=5):
                expected_data_length+=int(data[2:5])
                # These digits of data describe the length of the data. Add this number to the data length we're expecting.
                has_extended=True
                # We only want to do this once.
                
                
            #print data
            #for debugging
            
            tic=time.time()
            
        sock.close()
        return data
        
    def get_data(self):
        self.send('SNDT 1, "TVAL?"'+'\r\n')
        # Bridge Temperature
        self.send('SNDT 5, "TVAL? 1"'+'\r\n')
        self.send('SNDT 5, "TVAL? 3"'+'\r\n')
        # 50K and 4K stage temperatures top to bottom
        self.send('SNDT 7, "VOLT? 1"'+'\r\n')
        self.send('SNDT 7, "VOLT? 2"'+'\r\n')
        # Mag V and Mag I top to bottom.
        
        
        
        
        
        
        
        
        
        
        

class socketClass():
    def __init__(self):
        self.host="192.168.1.151"
        self.port=4001
        self.address=(self.host,self.port)
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.settimeout(2)
        self.sock.connect(self.address)
        self.terminator="\r\n"
        
    def send_get(self,msg):
        self.sock.send(msg)
        time.sleep(0.1)
        # Necessary to let the sim900 send back. Otherwise, it just gets the first character.
        return self.sock.recv(1024)
        
    def close_socket(self):
        self.sock.close()
