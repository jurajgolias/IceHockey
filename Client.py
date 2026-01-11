import socket


class Client:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(0.3) 
        self.server = "192.168.68.113" # Zmeniť podľa IP adresy servera
        self.port = 5555
        self.addr = (self.server, self.port)
        self.pos = self.connect()

    def getPos(self):
        return self.pos

    def connect(self):
        try:
            self.client.connect(self.addr)
            self.client.settimeout(2.0) 
            result = self.client.recv(2048).decode()
            self.client.settimeout(0.3)
            return result
        except Exception as e:
            print(f"Connection error: {e}")
            return None

    def send_with_puck(self, player_data, puck_data):
        #Posiela pozíciu hráča a puku: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy
        try:
            puck_str = f"{puck_data['x']:.2f},{puck_data['y']:.2f},{puck_data['vx']:.2f},{puck_data['vy']:.2f}"
            data = f"{player_data[0]},{player_data[1]}|{puck_str}"
            self.client.send(str.encode(data))
            response = self.client.recv(2048).decode()
            if not response:
                print(f"[CLIENT] WARNING: Empty response from server!")
            return response
        except socket.timeout:
            print(f"[CLIENT] WARNING: Socket timeout when sending/receiving!")
            return None
        except socket.error as e:
            print(f"[CLIENT] Send with puck error: {e}")
            return None

Network = Client