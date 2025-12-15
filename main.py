import pygame
from Client import Client

# základné nastavenie okna
pygame.init()
WIDTH, HEIGHT = 1280, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Air Hockey")
clock = pygame.time.Clock()

clientNumber = 0
class Player():
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = (x,y,width,height)
        self.vel = 3

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)

    def move(self):
        mx, my = pygame.mouse.get_pos()
        mx = max(mx, WIDTH // 2)
        my = max(90, min(my, HEIGHT - 90))

        self.x = mx - self.width // 2
        self.y = my - self.height // 2

        self.update()

    def update(self):
        self.rect = (self.x, self.y, self.width, self.height)

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

#def draw_paddle_follow_mouse():
#    if not paddle_img:
#       return

#    mx, my = pygame.mouse.get_pos()
#    mx = max(mx, WIDTH // 2)
#    my = max(90, min(my, HEIGHT - 90))
#    rect = paddle_img.get_rect(center=(mx, my))
#    screen.blit(paddle_img, rect)


def draw_game_scene(player, player2):
    if background_img:
        screen.blit(background_img, (0, 0))
    else:
        screen.fill(WHITE)
    #draw_paddle_follow_mouse()
    hint = small_font.render("ESC - späť do menu", True, GRAY)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 30)))
    player.draw(screen)
    player2.draw(screen)

def read_pos(str):
    str = str.split(",")
    return int(str[0]), int(str[1])

def make_pos(tup):
    return str(tup[0]) + "," + str(tup[1])

def main():
    global mode
    client = Client()
    startPos = read_pos(client.getPos())
    player = Player (startPos[0], startPos[1], 180, 180, (255,0,0))
    player2 = Player (0,0, 180, 180, (0,0,255))
    player2.update()
    run = True

    while run:
        clock.tick(60)

        if mode == "game":
            player.move()

        player2Pos = read_pos(client.send(make_pos((player.x, player.y))))
        player2.x, player2.y = player2Pos
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

        if mode == "menu":
            draw_menu()
        elif mode == "game":
            draw_game_scene(player, player2)
        elif mode == "settings":
            draw_placeholder("NASTAVENIA (pripravujú sa)")
        elif mode == "skins":
            draw_placeholder("SKINY (pripravujú sa)")

        pygame.mouse.set_visible(mode != "game")  

        pygame.display.flip()

main()
