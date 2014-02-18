import socket

class server():
    def __init__(self):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.address=('localhost',13579)
        self.sock.bind(self.address)
        self.sock.listen(1)
        self.conn, self.addr = self.sock.accept()
        while 1:
            data=self.conn.recv(1024)
            if not data:
                break
            print data
        conn.close()
        
class client():
    def __init__(self):
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.address=('localhost',13579)
        self.s.connect(self.address)
        
        
# These work. Use ipython to test them out.
