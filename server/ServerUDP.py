import socket
from _thread import *
import sys
import math
import time
import threading

server = "0.0.0.0"
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((server, port))
except socket.error as e:
    print("Nepodarilo sa viazať socket:", e)
    sys.exit(1)

s.listen(2)
print("Čaká sa na pripojenie, Server beží",(server))

def read_pos(str):
    parts = str.split(",")
    if len(parts) == 2:
        return int(parts[0]), int(parts[1]), "cerveny"
    elif len(parts) == 3:
        return int(parts[0]), int(parts[1]), parts[2]
    else:
        return 0, 0, "cerveny"

def read_puck(str):
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
    return str(tup[0]) + "," + str(tup[1]) + "," + str(tup[2])

def make_puck(puck):
    return f"{puck['x']:.2f},{puck['y']:.2f},{puck['vx']:.2f},{puck['vy']:.2f}"

def make_response(player_pos, puck, players_ready=0, scores=None):
    score_str = f"{scores[0]},{scores[1]}" if scores else "0,0"
    return make_pos(player_pos) + "|" + make_puck(puck) + "|" + str(players_ready) + "|" + score_str

def read_response(str):
    if not str:
        return None, None, 0, [0, 0]
    try:
        parts = str.split("|")
        if len(parts) >= 2:
            player_pos = read_pos(parts[0])
            puck_data = read_puck(parts[1])
            players_ready = int(parts[2]) if len(parts) > 2 else 0
            scores = [0, 0]
            if len(parts) > 3:
                score_parts = parts[3].split(",")
                if len(score_parts) == 2:
                    scores = [int(score_parts[0]), int(score_parts[1])]
            return player_pos, puck_data, players_ready, scores
    except Exception as e:
        print(f"Chyba pri čítaní odpovede: {e}, str: {str[:100]}")
    return None, None, 0, [0, 0]

# Počiatočné nastavenia hry
WIDTH = 1280
HEIGHT = 700
pos = [(200, 350, "cerveny"), (1080, 350, "modry")]
prev_pos = [None, None]  
initial_positions = [(200, 350), (1080, 350)] 

# Sledovanie hráčov
connected_players = 0
players_in_game = [False, False]
game_started = False
countdown_started = False

# Thread lock pre bezpečný prístup k zdieľaným premenným
game_lock = threading.Lock()

# Puk
puck = {
    'x': 640.0,  
    'y': 350.0,  
    'vx': 0.0,
    'vy': 0.0
}

# Skóre hráčov
scores = [0, 0]

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
    
    if distance < (puck_radius + player_radius):
        if distance > 0:
            nx = dx / distance
            ny = dy / distance
        else:
            nx, ny = 1, 0
        
        overlap = (puck_radius + player_radius) - distance
        puck['x'] += nx * overlap
        puck['y'] += ny * overlap
        
        # Rýchlosť pálky
        if player_prev_pos:
            player_vel_x = player_pos[0] - player_prev_pos[0]
            player_vel_y = player_pos[1] - player_prev_pos[1]
        else:
            player_vel_x = 0
            player_vel_y = 0
        
        # Fyzika kolízie
        puck_speed_before = math.sqrt(puck['vx']**2 + puck['vy']**2)
        player_speed = math.sqrt(player_vel_x**2 + player_vel_y**2)
        
        if puck_speed_before < 0.5:
            if player_speed > 0.1:
                speed_factor = min(player_speed * 4.0, 25.0)
                puck['vx'] = nx * speed_factor + player_vel_x * 0.8
                puck['vy'] = ny * speed_factor + player_vel_y * 0.8
            else:
                base_force = 15.0
                puck['vx'] = nx * base_force
                puck['vy'] = ny * base_force
        else:
            relative_vel_x = puck['vx'] - player_vel_x * 0.1
            relative_vel_y = puck['vy'] - player_vel_y * 0.1
            
            # Odraz puku
            dot_product = relative_vel_x * nx + relative_vel_y * ny
            puck['vx'] = relative_vel_x - 2 * dot_product * nx + player_vel_x * 0.1
            puck['vy'] = relative_vel_y - 2 * dot_product * ny + player_vel_y * 0.1
            
            # Pridanie sily od pálky
            base_force = 10.0
            puck['vx'] += nx * base_force
            puck['vy'] += ny * base_force
        
        return True
    return False

def update_puck_server(puck, pos, prev_pos, WIDTH=1280, HEIGHT=700):
    puck_radius = 26
    goal_width = 12
    goal_top = 90
    goal_bottom = HEIGHT - 90
    
    # Vždy najprv kontrolujeme kolízie s pálkami
    collision_occurred = False
    if pos[0] is not None:
        collision_occurred = check_collision_server(puck, pos[0], prev_pos[0] if prev_pos and len(prev_pos) > 0 and prev_pos[0] else None, WIDTH) or collision_occurred
    
    if pos[1] is not None:
        collision_occurred = check_collision_server(puck, pos[1], prev_pos[1] if prev_pos and len(prev_pos) > 1 and prev_pos[1] else None, WIDTH) or collision_occurred
    
    if not collision_occurred:
        friction = 0.985
        puck['vx'] *= friction
        puck['vy'] *= friction
        
        min_velocity_threshold = 0.1
        if abs(puck['vx']) < min_velocity_threshold:
            puck['vx'] = 0
        if abs(puck['vy']) < min_velocity_threshold:
            puck['vy'] = 0
    
    puck['x'] += puck['vx']
    puck['y'] += puck['vy']
    
    if puck['x'] - puck_radius < 0:
        if puck['y'] >= goal_top and puck['y'] <= goal_bottom:
            scores[1] += 1
            puck['x'] = WIDTH // 2
            puck['y'] = HEIGHT // 2
            puck['vx'] = 0
            puck['vy'] = 0
        else:
            puck['x'] = puck_radius
            puck['vx'] = -puck['vx'] * 0.8
    elif puck['x'] + puck_radius > WIDTH:
        if puck['y'] >= goal_top and puck['y'] <= goal_bottom:
            scores[0] += 1
            puck['x'] = WIDTH // 2
            puck['y'] = HEIGHT // 2
            puck['vx'] = 0
            puck['vy'] = 0
        else:
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
    initial_response = make_response(pos[1 if player == 0 else 0], puck, 0, scores)
    conn.send(str.encode(initial_response))
    
    conn.settimeout(0.5)
    while True:
        try:
            data = conn.recv(2048).decode()
            if not data:
                print("Disconnected")
                break
            
            with game_lock:
                if "|" in data:
                    player_data, puck_data, _, _ = read_response(data)
                    if player_data:
                        prev_pos[player] = (pos[player][0], pos[player][1]) 
                        # Obmedzenie pozície hráča na jeho polovicu
                        player_width = 120
                        if player == 0:
                            x = max(0, min(player_data[0], WIDTH // 2 - player_width))
                        else:
                            x = max(WIDTH // 2, min(player_data[0], WIDTH - player_width))
                        y = max(0, min(player_data[1], HEIGHT - player_width))
                        pos[player] = (x, y, player_data[2])  # (x, y, skin)
                        
                        if not players_in_game[player]:
                            players_in_game[player] = True
                else:

                    player_data = read_pos(data)
                    if player_data:
                        prev_pos[player] = pos[player]
                        player_width = 120
                        if player == 0:
                            x = max(0, min(player_data[0], WIDTH // 2 - player_width))
                        else:
                            x = max(WIDTH // 2, min(player_data[0], WIDTH - player_width))
                        y = max(0, min(player_data[1], HEIGHT - player_width))
                        pos[player] = (x, y)
                        
                        if not players_in_game[player]:
                            players_in_game[player] = True
                
                players_ready_count = sum(players_in_game)
                
                # Kópia puku, aby sa nezmenil počas odosielania
                puck_copy = {'x': puck['x'], 'y': puck['y'], 'vx': puck['vx'], 'vy': puck['vy']}
                if player == 1:
                    reply = make_response(pos[0], puck_copy, players_ready_count, scores)
                else:
                    reply = make_response(pos[1], puck_copy, players_ready_count, scores)
                
            print("Dáta od hráča", player, ": ", data[:50])
            conn.sendall(str.encode(reply))
        except socket.timeout:
            continue
        except Exception as e:
            print("Chyba v threaded_client:", e)
            break

    print("Stratené pripojenie s hráčom", player)
    # Keď sa hráč odpojí, resetujeme jeho stav
    players_in_game[player] = False
    pos[player] = initial_positions[player]
    prev_pos[player] = None
    conn.close()

def game_loop():
    #Samostatný thread, ktorý aktualizuje puk
    global puck, pos, prev_pos, players_in_game
    update_count = 0
    while True:
        with game_lock:
            players_ready_count = sum(players_in_game)
            if players_ready_count >= 2:
                update_puck_server(puck, pos, prev_pos, WIDTH, HEIGHT)
                update_count += 1
                if update_count % 60 == 0:
                    print(f"[GAME_LOOP] Puk aktualizovaný: pozícia=({puck['x']:.1f},{puck['y']:.1f}), rýchlosť=({puck['vx']:.2f},{puck['vy']:.2f}), hráči pripravení={players_ready_count}")
            elif players_ready_count > 0:
                # Debug: len jeden hráč je v hre
                if update_count % 60 == 0:
                    print(f"[GAME_LOOP] Čakáme na druhého hráča. hráči pripravení={players_ready_count}")
        
        # Čakáme ~16ms pre 60 FPS
        time.sleep(1.0 / 60.0)

# Spustíme game loop thread
start_new_thread(game_loop, ())

currentPlayer = 0
while True:
    conn, addr = s.accept()
    print("Pripojené k:", addr)

    if currentPlayer >= len(pos):
        print("Server plný, zatváram pripojenie", addr)
        conn.close()
        continue

    start_new_thread(threaded_client, (conn, currentPlayer))
    currentPlayer += 1