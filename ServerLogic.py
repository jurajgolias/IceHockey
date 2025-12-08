import socket
import threading

clients = []

def handle_client(conn, player_id):
    conn.send(f"CONNECTED {player_id}".encode())

    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            print(f"Hráč {player_id} poslal:", data)
        except:
            break

    conn.close()
    print(f"Hráč {player_id} odpojený")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5555))
    server.listen(2)

    print("Server beží, čaká na hráčov...")

    for player_id in [1, 2]:
        conn, addr = server.accept()
        print(f"Hráč {player_id} pripojený: {addr}")
        clients.append(conn)

        threading.Thread(target=handle_client, args=(conn, player_id), daemon=True).start()

if __name__ == "__main__":
    start_server()
