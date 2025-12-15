import socket

class Client:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "192.168.137.225"
        self.port = 5678
        self.addr = (self.server, self.port)
        self.pos = self.connect()

    def getPos(self):
        return self.pos
    
    def connect(self):
        try:
            self.client.connect(self.addr)
            return self.client.recv(1024).decode()
        except:
            pass
    
    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return self.client.recv(1024).decode()
        except socket.error as e:
            print(e)
