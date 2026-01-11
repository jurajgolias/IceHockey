import socket


class Client:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(0.3)  # Timeout 300ms, aby sa neblokovalo (zvýšené kvôli lock contention na serveri)
        self.server = "192.168.68.110"
        self.port = 5555
        self.addr = (self.server, self.port)
        self.pos = self.connect()

    def getPos(self):
        return self.pos

    def connect(self):
        try:
            self.client.connect(self.addr)
            self.client.settimeout(2.0)  # Pri pripojení dlhší timeout
            result = self.client.recv(2048).decode()
            self.client.settimeout(0.3)  # Potom vrátime timeout 300ms
            return result
        except Exception as e:
            print(f"Connection error: {e}")
            return None

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return self.client.recv(2048).decode()
        except socket.timeout:
            return None
        except socket.error as e:
            print(f"Send error: {e}")
            return None
    
    def send_with_puck(self, player_data, puck_data):
        """Posiela pozíciu hráča a puku: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy"""
        try:
            puck_str = f"{puck_data['x']:.2f},{puck_data['y']:.2f},{puck_data['vx']:.2f},{puck_data['vy']:.2f}"
            data = f"{player_data[0]},{player_data[1]}|{puck_str}"
            self.client.send(str.encode(data))
            response = self.client.recv(2048).decode()
            # DEBUG: Vypíšeme, ak timeout alebo chyba
            if not response:
                print(f"[CLIENT] WARNING: Empty response from server!")
            return response
        except socket.timeout:
            print(f"[CLIENT] WARNING: Socket timeout when sending/receiving!")
            return None
        except socket.error as e:
            print(f"[CLIENT] Send with puck error: {e}")
            return None


# Alias used by main.py to keep naming consistent
Network = Client