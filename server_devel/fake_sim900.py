import socket
import threading
import time

# A program that behaves like a very simple (fake) sim900.

class FakeSim900():
    def __init__(self):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.address=('localhost',13579)
        self.sock.bind(self.address)
        self.loop_thread=None
        self.start_loop_thread()
        
        
    def start_loop_thread(self):
        if self.loop_thread:
            if self.loop_thread.is_alive():
                print "loop already running"
                return
        self.loop_thread=threading.Thread(target=self.handle)
        self.loop_thread.daemon=True
        self.loop_thread.start()
        
    def handle(self):
        while 1:
            self.sock.listen(1)
            self.conn, self.addr = self.sock.accept()
            while 1:
                data=self.conn.recv(1024)
                if not data:
                    break
                print data
                if data[:4]=='GETN':
                    #time.sleep(0.5)
                    #self.conn.send('#3012helloworld\r\njunkcharactersarehere')
                    self.conn.send('#300713579\r\n\n')
                    #self.conn.send('#300513579\r\n')
                    # Note: an error that could arise came here: if it says 5 characters, but those don't include the \r\n,
                    # then it will never find the terminator flag. Can this happen in practice?
            self.conn.close()
            
            
    def close(self):
        self.sock.close()
