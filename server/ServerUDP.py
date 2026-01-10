import socket
from _thread import *
import sys
import math
import time
import threading

server = "192.168.0.192"
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((server, port))
except socket.error as e:
    print("Bind failed:", e)
    sys.exit(1)

s.listen(2)
print("Waiting for a connection, Server Started",(server))

def read_pos(str):
    str = str.split(",")
    return int(str[0]), int(str[1])

def read_puck(str):
    """Číta pozíciu a rýchlosť puku: x,y,vx,vy"""
    if not str:
        return None
    try:
        parts = str.split(",")
        if len(parts) == 4:
            return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    except:
        pass
    return None

def make_pos(tup):
    return str(tup[0]) + "," + str(tup[1])

def make_puck(puck):
    """Vytvorí reťazec pre puk: x,y,vx,vy"""
    return f"{puck['x']:.2f},{puck['y']:.2f},{puck['vx']:.2f},{puck['vy']:.2f}"

def make_response(player_pos, puck, players_ready=0):
    """Vytvorí odpoveď: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy|players_ready"""
    return make_pos(player_pos) + "|" + make_puck(puck) + "|" + str(players_ready)

def read_response(str):
    """Číta odpoveď: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy"""
    if not str:
        return None, None
    try:
        parts = str.split("|")
        if len(parts) == 2:
            player_pos = read_pos(parts[0])
            puck_data = read_puck(parts[1])
            return player_pos, puck_data
    except:
        pass
    return None, None

# Starting positions: player 0 on left half, player 1 on right half
WIDTH = 1280
HEIGHT = 700
# Player 0 (červený) - ľavá polovica, Player 1 (modrý) - pravá polovica
pos = [(200, 350), (1080, 350)]
prev_pos = [None, None]  # Predchádzajúce pozície pre výpočet rýchlosti
initial_positions = [(200, 350), (1080, 350)]  # Počiatočné pozície pre detekciu

# Sledovanie hráčov
connected_players = 0
players_in_game = [False, False]  # Sleduje, ktorí hráči sú na hracej ploche (stlačili Hrať)
game_started = False
countdown_started = False

# Thread lock pre bezpečný prístup k zdieľaným premenným
game_lock = threading.Lock()

# Puk - spoločný pre oboch hráčov
puck = {
    'x': 640.0,  # WIDTH // 2
    'y': 350.0,  # HEIGHT // 2
    'vx': 0.0,
    'vy': 0.0
}

def check_collision_server(puck, player_pos, player_prev_pos, WIDTH=1280):
    """Kontroluje kolíziu medzi pukom a pálkou na serveri"""
    puck_radius = 40
    player_radius = 90
    player_width = 180
    player_height = 180
    
    # Stred pálky
    player_center_x = player_pos[0] + player_width // 2
    player_center_y = player_pos[1] + player_height // 2
    
    # Vzdialenosť medzi stredmi
    dx = puck['x'] - player_center_x
    dy = puck['y'] - player_center_y
    distance = math.sqrt(dx*dx + dy*dy)
    
    # Ak sú v kolízii
    if distance < (puck_radius + player_radius):
        # Normalizovaný vektor smeru
        if distance > 0:
            nx = dx / distance
            ny = dy / distance
        else:
            nx, ny = 1, 0
        
        # Presun puku mimo kolízie
        overlap = (puck_radius + player_radius) - distance
        puck['x'] += nx * overlap
        puck['y'] += ny * overlap
        
        # Rýchlosť pálky (zmena pozície)
        if player_prev_pos:
            player_vel_x = player_pos[0] - player_prev_pos[0]
            player_vel_y = player_pos[1] - player_prev_pos[1]
        else:
            player_vel_x = 0
            player_vel_y = 0
        
        # Relatívna rýchlosť
        relative_vel_x = puck['vx'] - player_vel_x * 0.1
        relative_vel_y = puck['vy'] - player_vel_y * 0.1
        
        # Odraz - odrazíme rýchlosť podľa normály
        dot_product = relative_vel_x * nx + relative_vel_y * ny
        puck['vx'] = relative_vel_x - 2 * dot_product * nx + player_vel_x * 0.1
        puck['vy'] = relative_vel_y - 2 * dot_product * ny + player_vel_y * 0.1
        
        # Pridáme silu od pálky
        force = 8.0
        puck['vx'] += nx * force
        puck['vy'] += ny * force
        
        return True
    return False

def update_puck_server(puck, pos, prev_pos, WIDTH=1280, HEIGHT=700):
    """Aktualizuje puk na serveri"""
    puck_radius = 40
    
    # Kontrola kolízie s pálkami (iba ak sú pozície validné)
    if pos[0] and (pos[0][0] > 0 or pos[0][1] > 0):
        check_collision_server(puck, pos[0], prev_pos[0] if prev_pos and len(prev_pos) > 0 else None, WIDTH)
    
    if pos[1] and (pos[1][0] > 0 or pos[1][1] > 0):
        check_collision_server(puck, pos[1], prev_pos[1] if prev_pos and len(prev_pos) > 1 else None, WIDTH)
    
    # Trenie (aplikujeme pred aktualizáciou pozície)
    friction = 0.985
    puck['vx'] *= friction
    puck['vy'] *= friction
    
    # Zastavíme puk, ak je rýchlosť veľmi malá
    if abs(puck['vx']) < 0.05:
        puck['vx'] = 0
    if abs(puck['vy']) < 0.05:
        puck['vy'] = 0
    
    # Aktualizácia pozície
    puck['x'] += puck['vx']
    puck['y'] += puck['vy']
    
    # Odraz od stien (horizontálne)
    if puck['x'] - puck_radius < 0:
        puck['x'] = puck_radius
        puck['vx'] = -puck['vx'] * 0.8
    elif puck['x'] + puck_radius > WIDTH:
        puck['x'] = WIDTH - puck_radius
        puck['vx'] = -puck['vx'] * 0.8
    
    # Odraz od stien (vertikálne)
    if puck['y'] - puck_radius < 90:
        puck['y'] = 90 + puck_radius
        puck['vy'] = -puck['vy'] * 0.8
    elif puck['y'] + puck_radius > HEIGHT - 90:
        puck['y'] = HEIGHT - 90 - puck_radius
        puck['vy'] = -puck['vy'] * 0.8

def threaded_client(conn, player):
    # Pošleme počiatočnú pozíciu hráča a puk
    initial_response = make_response(pos[1 if player == 0 else 0], puck, 0)
    conn.send(str.encode(initial_response))
    
    while True:
        try:
            data = conn.recv(2048).decode()
            if not data:
                print("Disconnected")
                break
            
            # Formát: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy
            # Alebo starý formát len: player_x,player_y
            with game_lock:
                if "|" in data:
                    player_data, puck_data = read_response(data)
                    if player_data:
                        prev_pos[player] = pos[player]  # Uložíme predchádzajúcu pozíciu
                        # Obmedzíme pozíciu hráča na jeho polovicu
                        player_width = 180
                        if player == 0:
                            # Player 0 (červený) - ľavá polovica (0 až WIDTH//2 - player_width)
                            x = max(0, min(player_data[0], WIDTH // 2 - player_width))
                        else:
                            # Player 1 (modrý) - pravá polovica (WIDTH//2 až WIDTH - player_width)
                            x = max(WIDTH // 2, min(player_data[0], WIDTH - player_width))
                        y = max(90, min(player_data[1], HEIGHT - 90 - player_width // 2))
                        pos[player] = (x, y)
                        
                        # Hráč je na hracej ploche, ak posiela aktívnu pozíciu (nie počiatočnú) a je v platnej oblasti
                        # Detekujeme aktívnu pozíciu - ak sa pozícia líši od počiatočnej alebo zmenila sa
                        pos_changed = (prev_pos[player] is not None and prev_pos[player] != (x, y))
                        is_not_initial = (x, y) != initial_positions[player]
                        
                        if (is_not_initial or pos_changed) and y >= 90:
                            # Hráč posiela aktívnu pozíciu (nie počiatočnú alebo sa zmenila) - je na hracej ploche
                            players_in_game[player] = True
                        # Puck dáta z klienta ignorujeme - server je autoritatívny
                else:
                    # Starý formát - len pozícia hráča
                    player_data = read_pos(data)
                    if player_data:
                        prev_pos[player] = pos[player]  # Uložíme predchádzajúcu pozíciu
                        # Obmedzíme pozíciu hráča na jeho polovicu
                        player_width = 180
                        if player == 0:
                            # Player 0 (červený) - ľavá polovica (0 až WIDTH//2 - player_width)
                            x = max(0, min(player_data[0], WIDTH // 2 - player_width))
                        else:
                            # Player 1 (modrý) - pravá polovica (WIDTH//2 až WIDTH - player_width)
                            x = max(WIDTH // 2, min(player_data[0], WIDTH - player_width))
                        y = max(90, min(player_data[1], HEIGHT - 90 - player_width // 2))
                        pos[player] = (x, y)
                        
                        # Hráč je na hracej ploche, ak posiela aktívnu pozíciu (nie počiatočnú) a je v platnej oblasti
                        # Detekujeme aktívnu pozíciu - ak sa pozícia líši od počiatočnej alebo zmenila sa
                        pos_changed = (prev_pos[player] is not None and prev_pos[player] != (x, y))
                        is_not_initial = (x, y) != initial_positions[player]
                        
                        if (is_not_initial or pos_changed) and y >= 90:
                            # Hráč posiela aktívnu pozíciu (nie počiatočnú alebo sa zmenila) - je na hracej ploche
                            players_in_game[player] = True
                
                # Počítame, koľko hráčov je na hracej ploche
                players_ready_count = sum(players_in_game)
                
                # Pošleme pozíciu druhého hráča a aktuálny stav puku (v locku pre thread safety)
                # Vytvoríme kópiu puku, aby sa nezmenil počas odosielania
                puck_copy = {'x': puck['x'], 'y': puck['y'], 'vx': puck['vx'], 'vy': puck['vy']}
                if player == 1:
                    reply = make_response(pos[0], puck_copy, players_ready_count)
                else:
                    reply = make_response(pos[1], puck_copy, players_ready_count)

            print("Received from player", player, ": ", data[:50])
            print("Sending to player", player, ": ", reply[:50], f"players_ready: {players_ready_count}, pos[0]: {pos[0]}, pos[1]: {pos[1]}")

            conn.sendall(str.encode(reply))
        except Exception as e:
            print("Error in threaded_client:", e)
            break

    print("Lost connection")
    # Keď sa hráč odpojí, resetujeme jeho stav
    players_in_game[player] = False
    pos[player] = initial_positions[player]
    prev_pos[player] = None
    conn.close()

def game_loop():
    """Samostatný thread, ktorý aktualizuje puk neustále (60 FPS)"""
    global puck, pos, prev_pos
    while True:
        with game_lock:
            # Aktualizujeme puk ak sú obaja hráči v hre (aj počas countdownu a hry)
            players_ready_count = sum(players_in_game)
            if players_ready_count >= 2:
                # Aktualizujeme puk (fyzika beží neustále počas hry)
                update_puck_server(puck, pos, prev_pos, WIDTH, HEIGHT)
        
        # Čakáme ~16ms pre 60 FPS
        time.sleep(1.0 / 60.0)

# Spustíme game loop thread
start_new_thread(game_loop, ())

currentPlayer = 0
while True:
    conn, addr = s.accept()
    print("Connected to:", addr)

    if currentPlayer >= len(pos):
        print("Server full, closing connection", addr)
        conn.close()
        continue

    start_new_thread(threaded_client, (conn, currentPlayer))
    currentPlayer += 1