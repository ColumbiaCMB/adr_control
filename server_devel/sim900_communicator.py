import socket
import time

### This program adds locks to all the socket communications from sim900_socket. Locks are no longer present because server has its own locks to prevent collisions.

class CleanComm():
    def __init__(self, host="192.168.1.151",port=4001,debug=False):
        self.host=host
        self.port=port
        # Defaults for sim900 included.
        
        
        self.address=(self.host,self.port)
        self.debug_flag=debug
        
    def send(self,msg,terminator='\r\n'):
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        try:
            sock.connect(self.address)
        except socket.error:
            print "Socket unable to connect."
            raise
            
        
        try:
            sock.send(msg+terminator)
        except:
            print "socket unable to send message"
        finally:
            sock.close()
            return
        
            
### This method should not be used by the server (since it includes a time.sleep in it). However, it is very useful for debugging.
### It sends a message, waits, sends a request for data (GETN), and receives data.
            
    def send_and_receive(self,msg,terminator='\r\n'):
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.settimeout(2)
        data=None
        
        
        try:
            sock.connect(self.address)
        except socket.error:
            print "Socket unable to connect. Check that no other sockets are connected."
            raise
            
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
            
### The query_port method and associated submethods. Best used for getting specific data from a port. Essentially an upgrade to send_and_receive, since it returns 
### data as fast as it is available.
            
    def query_port(self,port, msg):
        # For easy talking to ports. Sends the question, then retrieves the answer with GETN command to port.
        # Good test: port=3, msg='*IDN?'
        format_msg='SNDT %d, "%s"' % (port,msg)
        self.send(format_msg)
        # Sends the message
        
        return self.query(port)
        # Gets the response
        
        
    def query(self,port,timeout=2):
        
        data=''
        start=time.time()
        tic=time.time()
        mismatch_total=0
        
        while tic-start<timeout:
            raw_data=self.query_loop(port)
            
            if self.debug_flag==True:
                (payload,mismatch)=self.decode(raw_data)
                mismatch_total+=mismatch
            else:
                payload=self.decode(raw_data)
            
            data+=payload
            
            tic=time.time()
            
            index=data.find('\r\n')
            
            if index >= 0:
            
                if self.debug_flag==True:
                    print
                    print 'query took %f sec' % (tic-start)
                    print 'there were %d strings of unexpected length' % (mismatch_total)
                    print
                
                return data[:index]
            
        print 'query timed out'
        return data
        
    def decode(self,raw):
        if raw[:2]=='#3':
        # makes sure the string is formatted in the way we expect
        
            try:
                byte_no=int(raw[2:5])
            except ValueError:
                print raw[2:5] + ' is not an int. Adding empty string.'
                return ''
            
            if len(raw)<5+byte_no:
                # Problem, some data has gone missing
                print "Error: missing data in "+raw
            
            if self.debug_flag==True:
                if len(raw)!=(5+byte_no+1):
                    mismatch=1
                    print raw
                else:
                    mismatch=0
                # This is just for checking out how often we get strings that aren't formatted how we would expect.
                
                return (raw[5:(5+byte_no)], mismatch)
                # We check how many bytes to expect, then  grab that many characters after the header.
                # Needs error checking in case there aren't actually that many bytes.
            else:
                return raw[5:(5+byte_no)]
            
        else:
            print 'Input not formatted #3 or is not a string. Writing empty data.'
            return ''
            
    def query_loop(self,port,terminator='\r\n'):
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        try:
            sock.connect(self.address)
            sock.setblocking(0)
        except socket.error:
            print "Socket unable to connect. Check that no other sockets are connected."
            raise
            
        try:
            msg='GETN? %d,100' % (port)
            sock.send(msg+terminator)
        except:
            print "socket unable to send message"
            sock.close()
            raise
            
        
        
        data=''
        new_data=None
        # data comes in strings. Starts an empty string and sets new_data to None.
        
        expected_data_length=5
        has_extended=False
        # How long should data be, and whether we have adjusted the length based on the data it gives us.
        
        start=time.time()
        tic=time.time()
        # For the timeout
        
        while (tic-start<2) and (len(data)<expected_data_length):
        # This loop constantly looks for new data until 2 seconds have passed, or the data has at least 4 characters.
        # Note that data from the sim900 will ALWAYS have at least 5 characters: #3xxx where xx is the amount of bytes of data
        # following the intro.
            try:
                new_data=sock.recv(1024)
            except socket.error as e:
                #catches all socket errors. Problem in that it raises a different socket error for testing and for using the sim900.
                
                if self.debug_flag==True:
                    print e
                
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
            
            tic=time.time()
            
            
        if self.debug_flag==True:
            print "query_loop took %f sec" % (tic-start)
        sock.close()
        return data
        
            
### The fast_send_and_receive method is a method used to quickly get data when the sim900 is in CONN mode. It is used in the server as the quickest
### way to populate the dictionary.
### It sends a command, and then returns a response as fast as possible. This works once connected to a port in CONN mode since that is how the sim900
### responds. However, when the user/server doesn't want to enter CONN mode, query_port is a better alternative.
            
    def fast_send_and_receive(self,msg,terminator='\r\n',end_of_response='\r\n'):
        # Added the self.terminator option in case CONN is being used and terminator control should be manual (in which case set terminator = None).
        sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.settimeout(2)
        data=None
        try:
            sock.connect(self.address)
            sock.setblocking(0)
        except socket.error:
            print "Socket unable to connect. Check that no other sockets are connected."
            raise
            
        try:
            sock.send(msg+terminator)
        except:
            print "socket unable to send message"
            sock.close()
            raise
        
        # Now for the query_loop-esque code.
        data=''
        expected_data_length=5
        start=time.time()
        tic=time.time()
        
        while (tic-start<2):
            try:
                new_data=sock.recv(1024)
            except socket.error as e:
                #catches all socket errors. Problem in that it raises a different socket error for testing and for using the sim900.
                # print e
                new_data=None
                # If new data hasn't come in, there is no new data.
            if new_data != None:
                data+=new_data
                # Add new data to total data if there is is new data.
            tic=time.time()
            index=data.find(end_of_response)
            if index>=0:
                sock.close()
                return data[:index]
                # Rough slicing from query.
                # Note that we don't need to worry about the leading #3XXX, but we don't know how many bytes to expect.
        print 'fast_send_and_receive timed out.'
        sock.close()
        return data
        # We have problems if we try to convert an empty string to a float, but the logger can deal with ValueErrors.
        
