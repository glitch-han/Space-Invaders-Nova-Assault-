import math
import random
import pygame
from entities.sprites import load_sprite, draw_glow


POWERUP_TYPES = {
    "rapid": {"color": (255, 210, 60), "name": "RAPID FIRE", "desc": "3 bolts at once"},
    "shield": {"color": (60, 230, 255), "name": "SHIELD", "desc": "absorbs one hit"},
    "bomb": {"color": (255, 90, 70), "name": "SMART BOMB", "desc": "blasts the wave"},
    "freeze": {"color": (138, 180, 255), "name": "TIME FREEZE", "desc": "stops enemies"},
    "life": {"color": (255, 90, 160), "name": "EXTRA LIFE", "desc": "+1 life, max 5"},
    "scatter": {"color": (125, 255, 110), "name": "SCATTER SHOT", "desc": "shotgun spread"},
}


class PowerUp:
    def __init__(self, x, screen_height, kind=None, speed=2.2):
        self.kind = kind or random.choice(list(POWERUP_TYPES.keys()))
        self.width = 46
        self.height = 46
        self.x = x
        self.y = -self.height
        self.speed = speed
        self.screen_height = screen_height
        self.is_active = True
        self.pulse = 0
        self.image = load_sprite("assets/images/powerup_%s.png" % self.kind, (self.width, self.height))

    def update(self):
        self.y += self.speed
        self.pulse += 1
        if self.y > self.screen_height:
            self.is_active = False

    def get_rect(self):
        return pygame.Rect(int(self.x) - 4, int(self.y) - 4, self.width + 8, self.height + 8)

    def draw(self, screen):
        color = POWERUP_TYPES[self.kind]["color"]
        wobble = 3 * math.sin(self.pulse * 0.1)
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2 + wobble
        draw_glow(screen, (cx, cy), 38 + 5 * math.sin(self.pulse * 0.16), color, 0.9)
        screen.blit(self.image, (int(self.x), int(self.y + wobble)))
