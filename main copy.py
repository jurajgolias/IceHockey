import pygame
import math
from Client import Client

# základné nastavenie okna
pygame.init()
music_volume = 1.0
dragging_volume = False
mixer_ok = False
try:
    pygame.mixer.init()
    pygame.mixer.music.load("sounds/soundtrack1.wav")
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play(-1)  # hrá dookola
    mixer_ok = True
except pygame.error as e:
    print("Hudbu sa nepodarilo spustiť:", e)
WIDTH, HEIGHT = 1280, 700
SLIDER_WIDTH, SLIDER_HEIGHT = 400, 8
SLIDER_HANDLE_RADIUS = 14
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Air Hockey")
clock = pygame.time.Clock()

clientNumber = 0
class Player():
    def __init__(self, x, y, width, height, image, x_min=0, x_max=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = image
        self.rect = (x,y,width,height)
        self.vel = 3
        self.x_min = x_min
        self.x_max = WIDTH - width if x_max is None else x_max

    def draw(self, win):
        if self.image:
            img_rect = self.image.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
            win.blit(self.image, img_rect)
        else:
            # Fallback na obdĺžnik, ak obrázok nie je načítaný
            pygame.draw.rect(win, (255, 0, 0), self.rect)

    def move(self):
        mx, my = pygame.mouse.get_pos()
        target_x = mx - self.width // 2
        target_y = my - self.height // 2

        target_x = max(self.x_min, min(target_x, self.x_max))
        target_y = max(90, min(target_y, HEIGHT - 90 - self.height // 2))

        self.x = target_x
        self.y = target_y

        self.update()

    def update(self):
        self.rect = (self.x, self.y, self.width, self.height)
    
    def get_center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# farby a fonty
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (120, 0, 140)
GRAY = (150, 150, 150)
title_font = pygame.font.Font(None, 72)
button_font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 32)

# stavy
mode = "menu"  
game_state = "menu"  # menu, waiting, countdown, playing
running = True
countdown_time = 10
countdown_start_time = 0

# tlačidlá - posunuté trochu vyššie
BTN_W, BTN_H = 300, 60
BTN_X = (WIDTH - BTN_W) // 2
buttons = {
    "play": pygame.Rect(BTN_X, 350, BTN_W, BTN_H),
    "settings": pygame.Rect(BTN_X, 430, BTN_W, BTN_H),
    "skins": pygame.Rect(BTN_X, 510, BTN_W, BTN_H),
    "quit": pygame.Rect(BTN_X, 590, BTN_W, BTN_H),
}


def slider_rect():
    return pygame.Rect(WIDTH // 2 - SLIDER_WIDTH // 2, HEIGHT // 2, SLIDER_WIDTH, SLIDER_HEIGHT)


def slider_handle_rect():
    rect = slider_rect()
    handle_x = rect.x + int(music_volume * rect.width)
    return pygame.Rect(handle_x - SLIDER_HANDLE_RADIUS, rect.centery - SLIDER_HANDLE_RADIUS, SLIDER_HANDLE_RADIUS * 2, SLIDER_HANDLE_RADIUS * 2)


def slider_hitbox():
    # Slightly taller area so clicks near the handle still register
    return slider_rect().inflate(0, 24)


def draw_button(rect, label):
    # Polopriehľadné pozadie tlačidla
    button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(button_surface, (255, 255, 255, 200), button_surface.get_rect(), border_radius=8)
    screen.blit(button_surface, rect)
    
    # Text tlačidla
    text = button_font.render(label, True, BLACK)
    screen.blit(text, text.get_rect(center=rect.center))


def draw_menu():
    # Zobrazenie pozadia menu
    if menu_img:
        screen.blit(menu_img, (0, 0))
    else:
        screen.fill(PURPLE)
    
    # Tlačidlá s pekným umiestnením
    draw_button(buttons["play"], "Hrať")
    draw_button(buttons["settings"], "Nastavenia")
    draw_button(buttons["skins"], "Skiny")
    draw_button(buttons["quit"], "Ukončiť")


def draw_placeholder(text):
    screen.fill(BLACK)
    info = title_font.render(text, True, WHITE)
    screen.blit(info, info.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    hint = small_font.render("ESC - späť do menu", True, GRAY)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))

def draw_waiting_for_opponent(player, player2, puk):
    """Zobrazí obrazovku čakania na súpera na hracej ploche"""
    # Zobrazíme hraciu plochu
    draw_game_scene(player, player2, puk)
    
    # Polopriehľadné pozadie pre text
    waiting_bg = pygame.Surface((500, 150), pygame.SRCALPHA)
    pygame.draw.rect(waiting_bg, (0, 0, 0, 200), waiting_bg.get_rect(), border_radius=20)
    screen.blit(waiting_bg, waiting_bg.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    
    waiting_text = title_font.render("Čaká sa na súpera...", True, WHITE)
    screen.blit(waiting_text, waiting_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    
    hint = small_font.render("ESC - späť do menu", True, GRAY)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))

def draw_countdown(player, player2, puk):
    """Zobrazí countdown na hracej ploche"""
    global game_state, mode
    
    # Najprv zobrazíme hraciu plochu
    draw_game_scene(player, player2, puk)
    
    # Vypočítame zostávajúci čas
    current_time = pygame.time.get_ticks() / 1000.0
    if countdown_start_time > 0:
        elapsed = current_time - countdown_start_time
        remaining = max(0, countdown_time - elapsed)
        
        if remaining > 0:
            # Polopriehľadné pozadie pre countdown
            countdown_bg = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.rect(countdown_bg, (0, 0, 0, 180), countdown_bg.get_rect(), border_radius=20)
            screen.blit(countdown_bg, countdown_bg.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            
            # Veľký countdown text
            countdown_text = title_font.render(str(int(remaining) + 1), True, WHITE)
            screen.blit(countdown_text, countdown_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            
            start_text = small_font.render("Zápas sa začína!", True, WHITE)
            screen.blit(start_text, start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))
        else:
            # Countdown skončil, začneme zápas
            game_state = "playing"
            mode = "game"
    else:
        # Ak ešte nebol spustený countdown, zobrazíme správu
        waiting_bg = pygame.Surface((400, 100), pygame.SRCALPHA)
        pygame.draw.rect(waiting_bg, (0, 0, 0, 180), waiting_bg.get_rect(), border_radius=20)
        screen.blit(waiting_bg, waiting_bg.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        
        waiting_text = title_font.render("Pripravuje sa zápas...", True, WHITE)
        screen.blit(waiting_text, waiting_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


def draw_settings():
    # Zobrazenie pozadia menu aj v nastaveniach
    if menu_img:
        screen.blit(menu_img, (0, 0))
    else:
        screen.fill(PURPLE)
    
    # Nadpis - viac v strede
    title = title_font.render("NASTAVENIA", True, WHITE)
    title_surface = pygame.Surface((title.get_width() + 40, title.get_height() + 20), pygame.SRCALPHA)
    pygame.draw.rect(title_surface, (0, 0, 0, 150), title_surface.get_rect(), border_radius=10)
    screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150)))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150)))

    # Label pre hlasitosť - ako tlačidlo (pod logom)
    label_rect = pygame.Rect(WIDTH // 2 - BTN_W // 2, 350, BTN_W, BTN_H)
    draw_button(label_rect, "Hlasitosť hudby")

    # Slider s pekným pozadím
    s_rect = pygame.Rect(WIDTH // 2 - SLIDER_WIDTH // 2, 430, SLIDER_WIDTH, SLIDER_HEIGHT)
    handle_x = s_rect.x + int(music_volume * s_rect.width)
    handle_rect = pygame.Rect(handle_x - SLIDER_HANDLE_RADIUS, s_rect.centery - SLIDER_HANDLE_RADIUS, SLIDER_HANDLE_RADIUS * 2, SLIDER_HANDLE_RADIUS * 2)
    
    # Pozadie slidera
    slider_bg = pygame.Surface((s_rect.width + 20, s_rect.height + 20), pygame.SRCALPHA)
    pygame.draw.rect(slider_bg, (0, 0, 0, 150), slider_bg.get_rect(), border_radius=10)
    screen.blit(slider_bg, slider_bg.get_rect(center=(WIDTH // 2, 430)))
    
    # Slider track (tmavší)
    pygame.draw.rect(screen, (100, 100, 100), s_rect)
    # Vyplnená časť slidera
    filled_rect = pygame.Rect(s_rect.x, s_rect.y, int(music_volume * s_rect.width), s_rect.height)
    pygame.draw.rect(screen, WHITE, filled_rect)
    # Handle slidera
    pygame.draw.circle(screen, WHITE, handle_rect.center, SLIDER_HANDLE_RADIUS)
    pygame.draw.circle(screen, (200, 200, 200), handle_rect.center, SLIDER_HANDLE_RADIUS - 2)

    # Percentá hlasitosti - ako tlačidlo
    volume_rect = pygame.Rect(WIDTH // 2 - BTN_W // 2, 480, BTN_W, BTN_H)
    draw_button(volume_rect, f"{int(music_volume * 100)}%")

    if not mixer_ok:
        warn = small_font.render("Audio sa nespustilo", True, (255, 100, 100))
        warn_bg = pygame.Surface((warn.get_width() + 20, warn.get_height() + 10), pygame.SRCALPHA)
        pygame.draw.rect(warn_bg, (0, 0, 0, 150), warn_bg.get_rect(), border_radius=8)
        screen.blit(warn_bg, warn_bg.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150)))
        screen.blit(warn, warn.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150)))

    # Hint pre návrat
    hint = small_font.render("ESC - späť do menu", True, GRAY)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 50)))



try:
    _loaded = pygame.image.load("images/palka.png").convert_alpha()
    paddle_img = pygame.transform.smoothscale(_loaded, (180, 180))
except pygame.error:
    paddle_img = None

# Načítanie obrázkov pálok pre hráčov
try:
    _loaded_cerveny = pygame.image.load("images/cerveny.png").convert_alpha()
    cerveny_img = pygame.transform.smoothscale(_loaded_cerveny, (180, 180))
except pygame.error:
    cerveny_img = None

try:
    _loaded_modry = pygame.image.load("images/modry.png").convert_alpha()
    modry_img = pygame.transform.smoothscale(_loaded_modry, (180, 180))
except pygame.error:
    modry_img = None

# Načítanie obrázka puku
try:
    _loaded_puk = pygame.image.load("images/puk.png").convert_alpha()
    puk_img = pygame.transform.smoothscale(_loaded_puk, (80, 80))
except pygame.error:
    puk_img = None

try:
    _loaded_bg = pygame.image.load("images/lad.png").convert()
    background_img = pygame.transform.smoothscale(_loaded_bg, (WIDTH, HEIGHT))
except pygame.error:
    background_img = None

# Načítanie obrázka menu
try:
    _loaded_menu = pygame.image.load("images/menu.png").convert()
    menu_img = pygame.transform.smoothscale(_loaded_menu, (WIDTH, HEIGHT))
except pygame.error:
    menu_img = None

#def draw_paddle_follow_mouse():
#    if not paddle_img:
#       return

#    mx, my = pygame.mouse.get_pos()
#    mx = max(mx, WIDTH // 2)
#    my = max(90, min(my, HEIGHT - 90))
#    rect = paddle_img.get_rect(center=(mx, my))
#    screen.blit(paddle_img, rect)


def check_collision(puck, player):
    """Kontroluje kolíziu medzi pukom a pálkou"""
    puck_radius = 40  # Polomer puku (80/2)
    player_center = player.get_center()
    player_radius = 90  # Polomer pálky (180/2)
    
    # Vzdialenosť medzi stredmi
    dx = puck['x'] - player_center[0]
    dy = puck['y'] - player_center[1]
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
        player_vel_x = player.x - getattr(player, 'prev_x', player.x)
        player_vel_y = player.y - getattr(player, 'prev_y', player.y)
        
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

def check_collision_local(puck, player):
    """Kontroluje kolíziu medzi pukom a pálkou lokálne (pre vizuálnu synchronizáciu)"""
    puck_radius = 40
    player_center = player.get_center()
    player_radius = 90
    
    dx = puck['x'] - player_center[0]
    dy = puck['y'] - player_center[1]
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance < (puck_radius + player_radius):
        if distance > 0:
            nx = dx / distance
            ny = dy / distance
        else:
            nx, ny = 1, 0
        
        # Rýchlosť pálky
        player_vel_x = player.x - getattr(player, 'prev_x', player.x)
        player_vel_y = player.y - getattr(player, 'prev_y', player.y)
        
        # Pridáme silu od pálky
        force = 8.0
        puck['vx'] += nx * force
        puck['vy'] += ny * force
        
        return True
    return False

def update_puck(puck, player, player2):
    """Aktualizuje pozíciu a rýchlosť puku"""
    # Trenie
    friction = 0.98
    puck['vx'] *= friction
    puck['vy'] *= friction
    
    # Zastavíme puk, ak je rýchlosť veľmi malá
    if abs(puck['vx']) < 0.1:
        puck['vx'] = 0
    if abs(puck['vy']) < 0.1:
        puck['vy'] = 0
    
    # Aktualizácia pozície
    puck['x'] += puck['vx']
    puck['y'] += puck['vy']
    
    puck_radius = 40
    
    # Odraz od stien (horizontálne)
    if puck['x'] - puck_radius < 0:
        puck['x'] = puck_radius
        puck['vx'] = -puck['vx'] * 0.8
    elif puck['x'] + puck_radius > WIDTH:
        puck['x'] = WIDTH - puck_radius
        puck['vx'] = -puck['vx'] * 0.8
    
    # Odraz od stien (vertikálne) - s ohraničením pre hru
    if puck['y'] - puck_radius < 90:  # Horná stena
        puck['y'] = 90 + puck_radius
        puck['vy'] = -puck['vy'] * 0.8
    elif puck['y'] + puck_radius > HEIGHT - 90:  # Dolná stena
        puck['y'] = HEIGHT - 90 - puck_radius
        puck['vy'] = -puck['vy'] * 0.8
    
    # Kontrola kolízie s pálkami
    check_collision(puck, player)
    check_collision(puck, player2)
    
    # Uloženie predchádzajúcej pozície pálok pre výpočet rýchlosti
    player.prev_x = player.x
    player.prev_y = player.y
    player2.prev_x = player2.x
    player2.prev_y = player2.y

def draw_game_scene(player, player2, puk):
    if background_img:
        screen.blit(background_img, (0, 0))
    else:
        screen.fill(WHITE)
    #draw_paddle_follow_mouse()
    hint = small_font.render("ESC - späť do menu", True, GRAY)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 30)))
    player.draw(screen)
    player2.draw(screen)
    # Zobrazenie puku
    if puk_img and puk:
        puk_rect = puk_img.get_rect(center=(puk['x'], puk['y']))
        screen.blit(puk_img, puk_rect)

def read_pos(str):
    if not str:
        return 0, 0
    try:
        str = str.split(",")
        return int(str[0]), int(str[1])
    except:
        return 0, 0

def make_pos(tup):
    return str(tup[0]) + "," + str(tup[1])

def read_response(str):
    """Číta odpoveď zo servera: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy|players_ready"""
    if not str:
        return None, None, 0
    try:
        parts = str.split("|")
        if len(parts) >= 2:
            player_pos = read_pos(parts[0])
            puck_parts = parts[1].split(",")
            if len(puck_parts) == 4:
                puck = {
                    'x': float(puck_parts[0]),
                    'y': float(puck_parts[1]),
                    'vx': float(puck_parts[2]),
                    'vy': float(puck_parts[3])
                }
                # Počet hráčov na hracej ploche
                players_ready = int(parts[2]) if len(parts) > 2 else 0
                return player_pos, puck, players_ready
    except Exception as e:
        print("Error reading response:", e)
    return None, None, 0

def main():
    global mode
    client = Client()
    initial_response = client.getPos()
    player2Pos_from_server, initial_puck, _ = read_response(initial_response) if initial_response else (None, None, 0)
    
    if not player2Pos_from_server:
        print("Error: Could not get initial position from server")
        return
    
    # Server pošle pozíciu druhého hráča v počiatočnej odpovedi
    # Player 0 dostane pozíciu player 1 (pravá strana), takže player 0 je na ľavej strane
    # Player 1 dostane pozíciu player 0 (ľavá strana), takže player 1 je na pravej strane
    player2_is_left = player2Pos_from_server[0] < WIDTH // 2

    # Player 0 (červený) - ľavá polovica, Player 1 (modrý) - pravá polovica
    if player2_is_left:
        # Dostali sme pozíciu hráča na ľavej strane, takže sme player 1 (modrý) - pravá polovica
        player = Player(1080, 350, 180, 180, modry_img, WIDTH // 2, WIDTH - 180)
        # player2 je na opačnej strane - ľavá polovica (pozícia zo servera)
        player2 = Player(player2Pos_from_server[0], player2Pos_from_server[1], 180, 180, cerveny_img, 0, WIDTH // 2 - 180)
    else:
        # Dostali sme pozíciu hráča na pravej strane, takže sme player 0 (červený) - ľavá polovica
        player = Player(200, 350, 180, 180, cerveny_img, 0, WIDTH // 2 - 180)
        # player2 je na opačnej strane - pravá polovica (pozícia zo servera)
        player2 = Player(player2Pos_from_server[0], player2Pos_from_server[1], 180, 180, modry_img, WIDTH // 2, WIDTH - 180)
    
    player2.update()
    
    # Počiatočná pozícia pre komunikáciu so serverom
    initial_player_pos = (player.x, player.y)
    
    # Inicializácia puku - bude sa načítať zo servera
    puk = {
        'x': WIDTH // 2,
        'y': HEIGHT // 2,
        'vx': 0.0,
        'vy': 0.0
    }
    
    # Inicializácia predchádzajúcich pozícií pálok
    player.prev_x = player.x
    player.prev_y = player.y
    player2.prev_x = player2.x
    player2.prev_y = player2.y
    
    run = True

    while run:
        clock.tick(60)

        # Povolíme pohyb hráča aj počas čakania, countdownu a hry
        if mode == "waiting" or mode == "game" or mode == "countdown":
            player.move()
            
            # Uloženie predchádzajúcich pozícií
            player.prev_x = player.x
            player.prev_y = player.y
            if hasattr(player2, 'prev_x'):
                player2.prev_x = player2.x
                player2.prev_y = player2.y

        # Posielame pozíciu hráča a puku na server, prijímame pozíciu druhého hráča a puk
        if mode == "waiting" or mode == "countdown" or mode == "game":
            # Pošleme aktuálnu pozíciu hráča (keď klikne na "Hrať", začne posielať pozíciu svojou pálkou)
            current_pos = (int(player.x), int(player.y))
            
            response = client.send_with_puck(current_pos, puk)
            if response:
                player2Pos, server_puck, players_ready = read_response(response)
                if player2Pos:
                    # Aktualizujeme pozíciu druhého hráča
                    player2.x, player2.y = player2Pos
                    player2.update()
                    
                    # Ak sme v stave waiting a obaja hráči sú na hracej ploche (stlačili Hrať)
                    if mode == "waiting" and players_ready >= 2:
                        # Obaja hráči sú na hracej ploche, spustíme countdown
                        print(f"Spúšťam countdown! Počet hráčov: {players_ready}")
                        game_state = "countdown"
                        mode = "countdown"
                        countdown_start_time = pygame.time.get_ticks() / 1000.0
                    elif mode == "waiting":
                        print(f"Čakám na súpera. Počet hráčov: {players_ready}")
                        
                if server_puck:
                    # Použijeme puk zo servera (autoritatívny)
                    puk_before = {'x': puk['x'], 'y': puk['y'], 'vx': puk['vx'], 'vy': puk['vy']}
                    puk['x'] = server_puck['x']
                    puk['y'] = server_puck['y']
                    puk['vx'] = server_puck['vx']
                    puk['vy'] = server_puck['vy']
                    # DEBUG: Vypíšeme, ak sa puk zmenil alebo je nulový
                    if puk['vx'] == 0 and puk['vy'] == 0:
                        print(f"[CLIENT] WARNING: Puck velocity is ZERO! pos=({puk['x']:.1f},{puk['y']:.1f})")
                    elif abs(puk['vx'] - puk_before['vx']) > 0.1 or abs(puk['vy'] - puk_before['vy']) > 0.1:
                        print(f"[CLIENT] Puck updated: pos=({puk['x']:.1f},{puk['y']:.1f}), vel=({puk['vx']:.2f},{puk['vy']:.2f})")
                else:
                    print(f"[CLIENT] WARNING: server_puck is None or empty!")
                    if response:
                        print(f"[CLIENT] Response was: {response[:100]}")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if mode == "menu" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if buttons["play"].collidepoint(pos):
                    # Pripojíme sa do zápasu - čakáme na súpera
                    game_state = "waiting"
                    mode = "waiting"
                    # Pošleme pozíciu hráča, aby server vedel, že sme na hracej ploche
                    # Toto sa pošle v hlavnej slučke
                elif buttons["settings"].collidepoint(pos):
                    mode = "settings"
                elif buttons["skins"].collidepoint(pos):
                    mode = "skins"
                elif buttons["quit"].collidepoint(pos):
                    run = False
            if mode != "menu" and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if mode == "waiting" or mode == "countdown":
                    # Vrátime sa do menu z čakania alebo countdownu
                    game_state = "menu"
                    mode = "menu"
                else:
                    mode = "menu"
            if mode == "settings":
                # Slider v nastaveniach je na pozícii Y=430
                settings_slider_rect = pygame.Rect(WIDTH // 2 - SLIDER_WIDTH // 2, 430, SLIDER_WIDTH, SLIDER_HEIGHT)
                settings_slider_hitbox = settings_slider_rect.inflate(0, 24)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if settings_slider_hitbox.collidepoint(event.pos):
                        rel_x = max(0, min(settings_slider_rect.width, event.pos[0] - settings_slider_rect.x))
                        global music_volume, dragging_volume
                        music_volume = rel_x / settings_slider_rect.width
                        if mixer_ok:
                            pygame.mixer.music.set_volume(music_volume)
                        dragging_volume = True
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging_volume = False
                if event.type == pygame.MOUSEMOTION and dragging_volume:
                    rel_x = max(0, min(settings_slider_rect.width, event.pos[0] - settings_slider_rect.x))
                    music_volume = rel_x / settings_slider_rect.width
                    if mixer_ok:
                        pygame.mixer.music.set_volume(music_volume)

        if mode == "menu":
            draw_menu()
        elif mode == "waiting":
            draw_waiting_for_opponent(player, player2, puk)
        elif mode == "countdown":
            draw_countdown(player, player2, puk)
            # Kontrola, či countdown skončil
            current_time = pygame.time.get_ticks() / 1000.0
            if countdown_start_time > 0 and current_time - countdown_start_time >= countdown_time:
                game_state = "playing"
                mode = "game"
        elif mode == "game":
            draw_game_scene(player, player2, puk)
        elif mode == "settings":
            draw_settings()
        elif mode == "skins":
            draw_placeholder("SKINY (pripravujú sa)")

        pygame.mouse.set_visible(mode != "game")  

        pygame.display.flip()

main()
