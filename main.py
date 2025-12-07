# Example file showing a basic pygame "game loop"
import pygame

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 700))
pygame.display.set_caption("Air Hockey")
clock = pygame.time.Clock()
running = True


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

title_font = pygame.font.Font(None, 72)
button_font = pygame.font.Font(None, 48)

def draw_button(screen, text, x, y, width, height, color=WHITE, text_color=BLACK):
    pygame.draw.rect(screen, color, (x, y, width, height))
    text_surface = button_font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surface, text_rect)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")
    # RENDER YOUR GAME HERE
    # Nadpis
    title_text = title_font.render("AIR HOCKEY", True, WHITE)
    title_rect = title_text.get_rect(center=(1280 // 2, 150))
    screen.blit(title_text, title_rect)

    # Tlačidlá
    button_width = 300
    button_height = 60
    button_x = (1280 - button_width) // 2
    
    draw_button(screen, "Hrať", button_x, 300, button_width, button_height)
    draw_button(screen, "Nastavenia", button_x, 380, button_width, button_height)
    draw_button(screen, "Skiny", button_x, 460, button_width, button_height)
    draw_button(screen, "Ukončiť", button_x, 540, button_width, button_height)

    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()