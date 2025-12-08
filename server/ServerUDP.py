import socket 
from _thread import *

server = ""
port = 5678

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # vytvorí komunikačný kanál UDP

try: 
    s.bind((server, port)) # priradí kanál k adrese a portu
except socket.error as e:
    print(e)

s.listen(2)
print("Čaka sa na pripojenie, Server beží")

def threaded_client(conn):
    reply = "192.168.137.152"
    while True:
        try:
            data = conn.recv(1024)
            reply = data.decode("utf-8")
            if not data:
                print("Odpojený")
                break
            else:
                print("Prijaté:", reply)
                print("Odoslané:", reply)

            conn.sendall(str.encode(reply))
        except:
            break
                  


while True:
    conn, addr = s.accept()
    print("Pripojený k:", addr)
    start_new_thread(threaded_client, (conn,))
