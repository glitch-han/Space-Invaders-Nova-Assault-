import math
import random
import pygame
from entities.sprites import load_sprite, draw_glow
from entities.ships import SHIPS, DEFAULT_SHIP, ship_info

_composed = {}


def compose_ship(size, tint, model=DEFAULT_SHIP):
    key = (model, size, tuple(tint))
    ship = _composed.get(key)
    if ship is None:
        base = ship_info(model)["file"]
        hull = load_sprite("assets/images/%s.png" % base, (size, size))
        accent = load_sprite("assets/images/%s_accent.png" % base, (size, size)).copy()
        accent.fill((*tint, 255), special_flags=pygame.BLEND_RGBA_MULT)
        ship = hull.copy()
        ship.blit(accent, (0, 0))
        _composed[key] = ship
    return ship


def draw_engine_flames(screen, x, y, size, tint, tick, thrust=1.0, model=DEFAULT_SHIP):
    for i, (ex, ey, scale) in enumerate(ship_info(model)["engines"]):
        cx = x + ex * size
        cy = y + ey * size
        flicker = 0.78 + 0.22 * math.sin(tick * 0.85 + i * 1.7) + random.uniform(-0.06, 0.06)
        length = size * 0.17 * flicker * thrust * (0.9 + 0.1 * scale)
        half = size * 0.028 * scale
        draw_glow(screen, (cx, cy + length * 0.35), size * 0.15, tint, 0.95)
        outer = [(cx - half * 1.5, cy - 1), (cx + half * 1.5, cy - 1), (cx, cy + length)]
        inner = [(cx - half * 0.7, cy - 1), (cx + half * 0.7, cy - 1), (cx, cy + length * 0.62)]
        mixed = tuple(int(c * 0.35 + 255 * 0.65) for c in tint)
        pygame.draw.polygon(screen, mixed, outer)
        pygame.draw.polygon(screen, (255, 255, 255), inner)


class Player:
    def __init__(self, screen_width, screen_height, model=DEFAULT_SHIP):
        info = ship_info(model)
        self.model = model if model in SHIPS else DEFAULT_SHIP
        self.width = 108
        self.height = 108
        self.speed = info["speed"]
        self.bolt_speed = info["bolt_speed"]
        self.hit_scale = info["hit_scale"]
        self.starts_shielded = info["shield_start"]
        self.tint = (200, 235, 255)
        self.image = compose_ship(self.width, self.tint, self.model)
        self.x = screen_width // 2 - self.width // 2
        self.y = screen_height - self.height - 32
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tick = 0
        self.thrust = 1.0

        self.is_blinking = False
        self.blink_timer = 0
        self.visible = True

    def set_tint(self, color_rgb):
        self.tint = tuple(color_rgb)
        self.image = compose_ship(self.width, self.tint, self.model)

    def move_left(self):
        if not self.is_blinking:
            self.x -= self.speed

    def move_right(self):
        if not self.is_blinking:
            self.x += self.speed

    def keep_inside_screen(self):
        self.x = max(0, min(self.x, self.screen_width - self.width))

    def get_rect(self):
        base_w = self.width * 0.40
        base_h = self.height * 0.74
        w = int(base_w * self.hit_scale)
        h = int(base_h * self.hit_scale)
        cx = self.x + self.width / 2
        cy = self.y + self.height * 0.12 + base_h / 2
        return pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)

    def get_full_rect(self):
        return pygame.Rect(int(self.x) + 10, int(self.y) + 8, self.width - 20, self.height - 16)

    def center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    def update_blink(self):
        if self.is_blinking:
            self.blink_timer += 1
            if self.blink_timer % 10 == 0:
                self.visible = not self.visible
        else:
            self.visible = True

    def draw(self, screen):
        self.tick += 1
        if self.visible:
            draw_engine_flames(screen, self.x, self.y, self.width, self.tint, self.tick, self.thrust, self.model)
            screen.blit(self.image, (int(self.x), int(self.y)))
