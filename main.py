import pygame

# základné nastavenie okna
pygame.init()
WIDTH, HEIGHT = 1280, 700
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


#
try:
    _loaded = pygame.image.load("images/palka.png").convert_alpha()
    paddle_img = pygame.transform.smoothscale(_loaded, (180, 180))
except pygame.error:
    paddle_img = None

def draw_paddle_follow_mouse():
    if not paddle_img:
        return
    mx, my = pygame.mouse.get_pos()
    rect = paddle_img.get_rect(center=(mx, my))
    screen.blit(paddle_img, rect)
# ------------------------------------------------------

def draw_game_scene():
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
        if mode != "menu" and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            mode = "menu"

    if mode == "menu":
        draw_menu()
    elif mode == "game":
        draw_game_scene()
    elif mode == "settings":
        draw_placeholder("NASTAVENIA (pripravujú sa)")
    elif mode == "skins":
        draw_placeholder("SKINY (pripravujú sa)")

    pygame.display.flip()
    clock.tick(60)

pygame.quit()