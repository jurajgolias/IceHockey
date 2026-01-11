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
    print("Bind failed:", e)
    sys.exit(1)

s.listen(2)
print("Waiting for a connection, Server Started",(server))

def read_pos(str):
    parts = str.split(",")
    if len(parts) == 2:
        return int(parts[0]), int(parts[1]), "cerveny"
    elif len(parts) == 3:
        return int(parts[0]), int(parts[1]), parts[2]
    else:
        return 0, 0, "cerveny"

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
    return str(tup[0]) + "," + str(tup[1]) + "," + str(tup[2])

def make_puck(puck):
    """Vytvorí reťazec pre puk: x,y,vx,vy"""
    return f"{puck['x']:.2f},{puck['y']:.2f},{puck['vx']:.2f},{puck['vy']:.2f}"

def make_response(player_pos, puck, players_ready=0, scores=None):
    """Vytvorí odpoveď: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy|players_ready|score0,score1"""
    score_str = f"{scores[0]},{scores[1]}" if scores else "0,0"
    return make_pos(player_pos) + "|" + make_puck(puck) + "|" + str(players_ready) + "|" + score_str

def read_response(str):
    """Číta odpoveď: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy|players_ready|score0,score1"""
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
        print(f"Error reading response: {e}, str: {str[:100]}")
    return None, None, 0, [0, 0]

# Starting positions: player 0 on left half, player 1 on right half
WIDTH = 1280
HEIGHT = 700
# Player 0 (červený) - ľavá polovica, Player 1 (modrý) - pravá polovica
pos = [(200, 350, "cerveny"), (1080, 350, "modry")]
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
        
        # Vždy aplikujeme silu - jednoduchá a spoľahlivá logika
        puck_speed_before = math.sqrt(puck['vx']**2 + puck['vy']**2)
        player_speed = math.sqrt(player_vel_x**2 + player_vel_y**2)
        
        # Ak je puk statický alebo má veľmi malú rýchlosť, použijeme väčšiu silu
        if puck_speed_before < 0.5:
            # Puk je statický alebo sa pohybuje veľmi pomaly - použitie jednoduchej sily
            if player_speed > 0.1:
                # Hráč sa pohybuje - použijeme rýchlosť hráča
                speed_factor = min(player_speed * 4.0, 25.0)
                puck['vx'] = nx * speed_factor + player_vel_x * 0.8
                puck['vy'] = ny * speed_factor + player_vel_y * 0.8
            else:
                # Hráč stojí - minimálna sila
                base_force = 15.0
                puck['vx'] = nx * base_force
                puck['vy'] = ny * base_force
        else:
            # Puk sa pohybuje - kombinácia odrazu a sily
            # Relatívna rýchlosť
            relative_vel_x = puck['vx'] - player_vel_x * 0.1
            relative_vel_y = puck['vy'] - player_vel_y * 0.1
            
            # Odraz - odrazíme rýchlosť podľa normály
            dot_product = relative_vel_x * nx + relative_vel_y * ny
            puck['vx'] = relative_vel_x - 2 * dot_product * nx + player_vel_x * 0.1
            puck['vy'] = relative_vel_y - 2 * dot_product * ny + player_vel_y * 0.1
            
            # Pridáme silu od pálky
            base_force = 10.0
            puck['vx'] += nx * base_force
            puck['vy'] += ny * base_force
        
        return True
    return False

def update_puck_server(puck, pos, prev_pos, WIDTH=1280, HEIGHT=700):
    """Aktualizuje puk na serveri"""
    puck_radius = 26
    goal_width = 12
    goal_top = 90
    goal_bottom = HEIGHT - 90
    
    # VŽDY najprv kontrolujeme kolízie s pálkami (PRED čímkoľvek iným)
    # Toto musí byť PRVÉ, aby kolízie fungovali aj keď je puk statický
    # ODSTRÁNIME podmienky pre pozície - kontrolujeme vždy ak existujú pozície
    collision_occurred = False
    if pos[0] is not None:
        collision_occurred = check_collision_server(puck, pos[0], prev_pos[0] if prev_pos and len(prev_pos) > 0 and prev_pos[0] else None, WIDTH) or collision_occurred
    
    if pos[1] is not None:
        collision_occurred = check_collision_server(puck, pos[1], prev_pos[1] if prev_pos and len(prev_pos) > 1 and prev_pos[1] else None, WIDTH) or collision_occurred
    
    # AK bola kolízia, NEAKTUALIZUJEME trenie a rýchlosť - kolízia už nastavila rýchlosť
    # Len ak NEBOLA kolízia, aplikujeme trenie
    if not collision_occurred:
        # Trenie aplikujeme len keď nebola kolízia
        friction = 0.985
        puck['vx'] *= friction
        puck['vy'] *= friction
        
        # Zastavíme puk len ak je rýchlosť veľmi malá a NEbola kolízia
        min_velocity_threshold = 0.1
        if abs(puck['vx']) < min_velocity_threshold:
            puck['vx'] = 0
        if abs(puck['vy']) < min_velocity_threshold:
            puck['vy'] = 0
    
    # Aktualizácia pozície (vždy, aj keď je rýchlosť 0)
    puck['x'] += puck['vx']
    puck['y'] += puck['vy']
    
    # Kontrola gólov a odraz od stien (horizontálne)
    if puck['x'] - puck_radius < 0:
        if puck['y'] >= goal_top and puck['y'] <= goal_bottom:
            # Gól pre hráča 1 (pravý hráč)
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
            # Gól pre hráča 0 (ľavý hráč)
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
    
    # Nastavíme timeout na socket, aby sa neblokovalo nekonečne
    conn.settimeout(0.5)  # 500ms timeout pre recv
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
                    player_data, puck_data, _, _ = read_response(data)  # Ignorujeme players_ready a scores, lebo to je len pre prichádzajúce dáta
                    if player_data:
                        prev_pos[player] = (pos[player][0], pos[player][1])  # Uložíme predchádzajúcu pozíciu
                        # Obmedzíme pozíciu hráča na jeho polovicu
                        player_width = 120
                        if player == 0:
                            # Player 0 (cervený) - ľavá polovica (0 až WIDTH//2 - player_width)
                            x = max(0, min(player_data[0], WIDTH // 2 - player_width))
                        else:
                            # Player 1 (modrý) - pravá polovica (WIDTH//2 až WIDTH - player_width)
                            x = max(WIDTH // 2, min(player_data[0], WIDTH - player_width))
                        y = max(0, min(player_data[1], HEIGHT - player_width))
                        pos[player] = (x, y, player_data[2])  # (x, y, skin)
                        
                        # Hráč je na hracej ploche, keď pošle pozíciu
                        if not players_in_game[player]:
                            players_in_game[player] = True
                        # Ak už je hráč v hre, zostane v hre (nič nerobíme, len necháme ho v hre)
                        # Puck dáta z klienta ignorujeme - server je autoritatívny
                else:
                    # Starý formát - len pozícia hráča
                    player_data = read_pos(data)
                    if player_data:
                        prev_pos[player] = pos[player]  # Uložíme predchádzajúcu pozíciu
                        # Obmedzíme pozíciu hráča na jeho polovicu
                        player_width = 120
                        if player == 0:
                            # Player 0 (červený) - ľavá polovica (0 až WIDTH//2 - player_width)
                            x = max(0, min(player_data[0], WIDTH // 2 - player_width))
                        else:
                            # Player 1 (modrý) - pravá polovica (WIDTH//2 až WIDTH - player_width)
                            x = max(WIDTH // 2, min(player_data[0], WIDTH - player_width))
                        y = max(0, min(player_data[1], HEIGHT - player_width))
                        pos[player] = (x, y)
                        
                        # Hráč je na hracej ploche, keď pošle pozíciu
                        if not players_in_game[player]:
                            players_in_game[player] = True
                        # Ak už je hráč v hre, zostane v hre (nič nerobíme, len necháme ho v hre)
                
                # Počítame, koľko hráčov je na hracej ploche
                players_ready_count = sum(players_in_game)
                
                # Pošleme pozíciu druhého hráča a aktuálny stav puku (v locku pre thread safety)
                # Vytvoríme kópiu puku, aby sa nezmenil počas odosielania
                puck_copy = {'x': puck['x'], 'y': puck['y'], 'vx': puck['vx'], 'vy': puck['vy']}
                if player == 1:
                    reply = make_response(pos[0], puck_copy, players_ready_count, scores)
                else:
                    reply = make_response(pos[1], puck_copy, players_ready_count, scores)
                
                # DEBUG: Vypíšeme stav puku, ktorý posielame (menej často, aby sa znížil výstup)
                # print(f"[SERVER->CLIENT {player}] Sending puck: pos=({puck_copy['x']:.1f},{puck_copy['y']:.1f}), vel=({puck_copy['vx']:.2f},{puck_copy['vy']:.2f}), players_ready={players_ready_count}")

            print("Received from player", player, ": ", data[:50])
            # Odoslanie mimo locku, aby sa znížil čas držania locku
            conn.sendall(str.encode(reply))
        except socket.timeout:
            # Timeout pri recv - normálne, keď klient neposiela
            continue
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
    global puck, pos, prev_pos, players_in_game
    update_count = 0
    while True:
        # Skontrolujeme počet hráčov a aktualizujeme puk - držíme lock čo najkratšie
        with game_lock:
            players_ready_count = sum(players_in_game)
            if players_ready_count >= 2:
                # Aktualizujeme puk (fyzika beží neustále počas hry)
                # update_puck_server modifikuje puck priamo, takže musí byť v locku
                update_puck_server(puck, pos, prev_pos, WIDTH, HEIGHT)
                update_count += 1
                # Debug výpis každých 60 rámcov (1 sekunda)
                if update_count % 60 == 0:
                    print(f"[GAME_LOOP] Puck updated: pos=({puck['x']:.1f},{puck['y']:.1f}), vel=({puck['vx']:.2f},{puck['vy']:.2f}), players_ready={players_ready_count}")
            elif players_ready_count > 0:
                # Debug: len jeden hráč je v hre
                if update_count % 60 == 0:
                    print(f"[GAME_LOOP] Waiting for second player. players_ready={players_ready_count}")
        
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