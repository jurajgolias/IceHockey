import socket 
from _thread import *

server = "192.168.137.225"
port = 5678

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # vytvorí komunikačný kanál TCP

try: 
    s.bind((server, port)) # priradí kanál k adrese a portu
except socket.error as e:
    print(e)

s.listen(2)
print("Čaka sa na pripojenie, Server beží")

def read_pos(str):
    str = str.split(",")
    return int(str[0]), int(str[1])

def make_pos(tup):
    return str(tup[0]) + "," + str(tup[1])

pos = [(0,0), (100,100)]

def threaded_client(conn, player):
    conn.send(str.encode(make_pos(pos[player])))
    reply = ""
    while True:
        try:
            data = read_pos(conn.recv(1024).decode())
            pos[player] = data

            if not data:
                print("Odpojený")
                break
            else:
                if player == 1:
                    reply = pos[0]
                else:
                    reply = pos[1]
                print("Prijaté:", data)
                print("Odoslané:", reply)

            conn.sendall(str.encode(make_pos(reply)))
        except:
            break
    
    print("Stratené pripojenie")
    conn.close()

currentPlayer = 0 


while True:
    conn, addr = s.accept()
    print("Pripojený k:", addr)
    start_new_thread(threaded_client, (conn, currentPlayer))
    currentPlayer += 1
