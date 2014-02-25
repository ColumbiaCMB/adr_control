import socket
import threading
import time

class server():
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
                    time.sleep(0.5)
                    self.conn.send('#3012helloworld\r\njunkcharactersarehere')
            self.conn.close()
            
        # Note that right now, this can't handle inputs that DON'T expect a response (like send).
        # That is why it gets errno 104 for send, as well as query_port and get_data, both of which include send.
        # Fix this by changing behavior based on input.
            
            
    def close(self):
        self.sock.close()
