import pygame

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


try:
    _loaded_bg = pygame.image.load("images/lad.png").convert()
    background_img = pygame.transform.smoothscale(_loaded_bg, (WIDTH, HEIGHT))
except pygame.error:
    background_img = None

def draw_paddle_follow_mouse():
    if not paddle_img:
        return
    mx, my = pygame.mouse.get_pos()
    mx = max(mx, WIDTH // 2)  
    my = max(90, min(my, HEIGHT - 90))  
    rect = paddle_img.get_rect(center=(mx, my))
    screen.blit(paddle_img, rect)


def draw_game_scene():
    if background_img:
        screen.blit(background_img, (0, 0))
    else:
        screen.fill(WHITE)
    draw_paddle_follow_mouse()
    hint = small_font.render("ESC - späť do menu", True, GRAY)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 30)))


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if mode == "menu" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if buttons["play"].collidepoint(pos):
                mode = "game"
            elif buttons["settings"].collidepoint(pos):
                mode = "settings"
            elif buttons["skins"].collidepoint(pos):
                mode = "skins"
            elif buttons["quit"].collidepoint(pos):
                running = False
        if mode == "settings":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                s_rect = slider_rect()
                if slider_hitbox().collidepoint(event.pos):
                    rel_x = max(0, min(s_rect.width, event.pos[0] - s_rect.x))
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
        if mode != "menu" and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            mode = "menu"

    if mode == "menu":
        draw_menu()
    elif mode == "game":
        draw_game_scene()
    elif mode == "settings":
        draw_settings()
    elif mode == "skins":
        draw_placeholder("SKINY (pripravujú sa)")

    pygame.mouse.set_visible(mode != "game")  

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
