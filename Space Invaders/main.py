import os
import pygame

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from managers.game_manager import GameManager

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

try:
    pygame.display.set_icon(pygame.image.load("assets/images/icon.png"))
except (pygame.error, FileNotFoundError):
    pass

try:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE)
except pygame.error:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders: Nova Assault by Cordero, Ismail A.")

game = GameManager(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
clock = pygame.time.Clock()
running = True

while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()

    game.update(events)
    pygame.display.update()
    clock.tick(60)

game.db.close()
pygame.quit()
