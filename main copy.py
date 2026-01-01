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
running = True

# tlačidlá
BTN_W, BTN_H = 300, 60
BTN_X = (WIDTH - BTN_W) // 2
buttons = {
    "play": pygame.Rect(BTN_X, 300, BTN_W, BTN_H),
    "settings": pygame.Rect(BTN_X, 380, BTN_W, BTN_H),
    "skins": pygame.Rect(BTN_X, 460, BTN_W, BTN_H),
    "quit": pygame.Rect(BTN_X, 540, BTN_W, BTN_H),
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
    pygame.draw.rect(screen, WHITE, rect, border_radius=8)
    text = button_font.render(label, True, BLACK)
    screen.blit(text, text.get_rect(center=rect.center))


def draw_menu():
    screen.fill(PURPLE)
    title = title_font.render("AIR HOCKEY", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
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


def draw_settings():
    screen.fill(PURPLE)
    title = title_font.render("NASTAVENIA", True, WHITE)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))

    # slider
    s_rect = slider_rect()
    handle = slider_handle_rect()
    pygame.draw.rect(screen, WHITE, s_rect)
    pygame.draw.circle(screen, WHITE, handle.center, SLIDER_HANDLE_RADIUS)

    label = small_font.render("Hlasitosť hudby", True, WHITE)
    screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

    volume_text = small_font.render(f"{int(music_volume * 100)}%", True, WHITE)
    screen.blit(volume_text, volume_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    if not mixer_ok:
        warn = small_font.render("Audio sa nespustilo", True, GRAY)
        screen.blit(warn, warn.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 110)))

    hint = small_font.render("ESC - späť do menu", True, GRAY)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))



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
    """Číta odpoveď zo servera: player_x,player_y|puck_x,puck_y,puck_vx,puck_vy"""
    if not str:
        return None, None
    try:
        parts = str.split("|")
        if len(parts) == 2:
            player_pos = read_pos(parts[0])
            puck_parts = parts[1].split(",")
            if len(puck_parts) == 4:
                puck = {
                    'x': float(puck_parts[0]),
                    'y': float(puck_parts[1]),
                    'vx': float(puck_parts[2]),
                    'vy': float(puck_parts[3])
                }
                return player_pos, puck
    except Exception as e:
        print("Error reading response:", e)
    return None, None

def main():
    global mode
    client = Client()
    startPos = read_pos(client.getPos())
    player_is_right = startPos[0] >= WIDTH // 2

    if player_is_right:
        p1_bounds = (WIDTH // 2, WIDTH - 180)
        p2_bounds = (0, WIDTH // 2 - 180)
    else:
        p1_bounds = (0, WIDTH // 2 - 180)
        p2_bounds = (WIDTH // 2, WIDTH - 180)

    player = Player(startPos[0], startPos[1], 180, 180, cerveny_img, *p1_bounds)
    player2 = Player(0, 0, 180, 180, modry_img, *p2_bounds)
    
    player2.update()
    
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

        if mode == "game":
            player.move()
            
            # Kontrola kolízie s pálkou (lokálne pre okamžitú odozvu)
            check_collision_local(puk, player)
            
            # Uloženie predchádzajúcich pozícií
            player.prev_x = player.x
            player.prev_y = player.y
            player2.prev_x = player2.x
            player2.prev_y = player2.y

        # Posielame pozíciu hráča a puku na server, prijímame pozíciu druhého hráča a puk
        response = client.send_with_puck((player.x, player.y), puk)
        if response:
            player2Pos, server_puck = read_response(response)
            if player2Pos:
                player2.x, player2.y = player2Pos
                player2.update()
            if server_puck:
                # Použijeme puk zo servera (autoritatívny)
                puk['x'] = server_puck['x']
                puk['y'] = server_puck['y']
                puk['vx'] = server_puck['vx']
                puk['vy'] = server_puck['vy']
        player2.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if mode == "menu" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if buttons["play"].collidepoint(pos):
                    mode = "game"
                elif buttons["settings"].collidepoint(pos):
                    mode = "settings"
                elif buttons["skins"].collidepoint(pos):
                    mode = "skins"
                elif buttons["quit"].collidepoint(pos):
                    run = False
            if mode != "menu" and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                mode = "menu"
            if mode == "settings":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    s_rect = slider_rect()
                    if slider_hitbox().collidepoint(event.pos):
                        rel_x = max(0, min(s_rect.width, event.pos[0] - s_rect.x))
                        global music_volume, dragging_volume
                        music_volume = rel_x / s_rect.width
                        if mixer_ok:
                            pygame.mixer.music.set_volume(music_volume)
                        dragging_volume = True
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging_volume = False
                if event.type == pygame.MOUSEMOTION and dragging_volume:
                    s_rect = slider_rect()
                    rel_x = max(0, min(s_rect.width, event.pos[0] - s_rect.x))
                    music_volume = rel_x / s_rect.width
                    if mixer_ok:
                        pygame.mixer.music.set_volume(music_volume)

        if mode == "menu":
            draw_menu()
        elif mode == "game":
            draw_game_scene(player, player2, puk)
        elif mode == "settings":
            draw_settings()
        elif mode == "skins":
            draw_placeholder("SKINY (pripravujú sa)")

        pygame.mouse.set_visible(mode != "game")  

        pygame.display.flip()

main()
