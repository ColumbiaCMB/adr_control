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
        except:
            print "Socket unable to connect."
            return
            
        try:
            sock.send(msg+terminator)
        except:
            print "socket unable to send message"
            sock.close()
            return
            
        time.sleep(0.1)
        
        try:
            data = sock.recv(1024)
        except:
            print "Nothing received"
        finally:
            sock.close()
            return data
        
            
    def query_port(self,port, msg, terminator='\r\n'):
        # For easy talking to ports. Sends the question, then retrieves the answer with GETN command to port.
        # Good test: port=3, msg='*IDN?'
        format_msg='SNDT %d, "%s"' % (port,msg)
        recv_msg='GETN? %d,100' % (port)
        self.send(format_msg)
        time.sleep(1)
        print recv_msg
        return self.send_and_receive(recv_msg)
        
        
        
        
        
        
        
        
        
        
        
        
        

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
