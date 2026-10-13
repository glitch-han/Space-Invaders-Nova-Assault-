import math
import random
import pygame
from entities.sprites import load_sprite, make_glow
from entities.theme import theme


class Particle:
    def __init__(self, x, y, color, power=1.0):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.2, 5.6) * power
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = random.randint(22, 42)
        self.max_life = self.life
        self.size = random.choice((2, 2, 3, 3, 4))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.965
        self.vy = self.vy * 0.965 + 0.05
        self.life -= 1

    def is_alive(self):
        return self.life > 0

    def draw(self, screen):
        fade = max(0.0, self.life / self.max_life)
        level = max(1, int(fade * 5))
        glow = make_glow(self.size * 3 + 2, self.color, 0.35 + level * 0.13)
        screen.blit(glow, (int(self.x) - glow.get_width() // 2, int(self.y) - glow.get_height() // 2),
                    special_flags=pygame.BLEND_RGB_ADD)
        core = tuple(min(255, int(c * 0.4 + 255 * 0.6 * fade)) for c in self.color)
        pygame.draw.circle(screen, core, (int(self.x), int(self.y)), max(1, int(self.size * (0.5 + 0.5 * fade))))


class Shockwave:
    def __init__(self, x, y, color, max_radius=90, life=24, width=6):
        self.x = x
        self.y = y
        self.color = color
        self.max_radius = max_radius
        self.life = life
        self.max_life = life
        self.width = width

    def update(self):
        self.life -= 1

    def is_alive(self):
        return self.life > 0

    def draw(self, screen):
        t = 1 - self.life / self.max_life
        radius = max(3, int(self.max_radius * (1 - (1 - t) ** 2)))
        alpha = int(230 * (1 - t))
        width = max(1, int(self.width * (1 - t)))
        size = radius * 2 + 6
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (size // 2, size // 2), radius, width)
        if t < 0.35:
            pygame.draw.circle(surf, (255, 255, 255, int(120 * (1 - t / 0.35))), (size // 2, size // 2), max(2, radius // 2))
        screen.blit(surf, (int(self.x) - size // 2, int(self.y) - size // 2))


class FloatingText:
    def __init__(self, x, y, text, color=(255, 255, 255), font=None):
        self.x = x
        self.y = y
        self.life = 46
        self.max_life = 46
        shadow = font.render(text, True, (0, 0, 0))
        body = font.render(text, True, color)
        self.surface = pygame.Surface((body.get_width() + 2, body.get_height() + 2), pygame.SRCALPHA)
        self.surface.blit(shadow, (2, 2))
        self.surface.blit(body, (0, 0))

    def update(self):
        self.y -= 1.1
        self.life -= 1

    def is_alive(self):
        return self.life > 0

    def draw(self, screen):
        fade = max(0.0, self.life / self.max_life)
        self.surface.set_alpha(int(255 * min(1.0, fade * 1.6)))
        screen.blit(self.surface, (int(self.x - self.surface.get_width() / 2), int(self.y)))


class Star:
    LAYERS = (
        {"speed": (0.25, 0.5), "size": 1, "bright": (70, 130)},
        {"speed": (0.7, 1.2), "size": 1, "bright": (120, 190)},
        {"speed": (1.6, 2.6), "size": 2, "bright": (170, 240)},
    )
    TINTS = ((200, 220, 255), (255, 244, 220), (190, 190, 255), (220, 255, 250))

    def __init__(self, screen_width, screen_height, layer=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.layer = layer if layer is not None else random.choices((0, 1, 2), weights=(6, 4, 2))[0]
        spec = self.LAYERS[self.layer]
        self.x = random.randint(0, screen_width)
        self.y = random.randint(0, screen_height)
        self.speed = random.uniform(*spec["speed"])
        self.size = spec["size"]
        self.brightness = random.randint(*spec["bright"])
        self.tint = random.choice(self.TINTS)
        self.twinkle = random.uniform(0, math.tau)
        self.twinkle_speed = random.uniform(0.03, 0.09)

    def update(self, speed=1.0):
        self.y += self.speed * speed
        self.twinkle += self.twinkle_speed
        if self.y > self.screen_height:
            self.y = -2
            self.x = random.randint(0, self.screen_width)

    def draw(self, screen):
        k = (self.brightness * (0.75 + 0.25 * math.sin(self.twinkle))) / 255
        color = (int(self.tint[0] * k), int(self.tint[1] * k), int(self.tint[2] * k))
        screen.fill(color, (int(self.x), int(self.y), self.size, self.size))


class Background:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.scroll = 0.0
        self.planet_x = random.randint(380, 600)
        self.planet_y = 40.0
        self.stars = [Star(screen_width, screen_height) for _ in range(110)]
        self.apply_theme()

    def apply_theme(self):
        self.nebula = load_sprite(theme.nebula_file, opaque=True)
        self.nebula_h = self.nebula.get_height()
        self.planet = load_sprite(theme.planet_file)
        Star.TINTS = tuple(theme.stars)
        for star in self.stars:
            star.tint = random.choice(Star.TINTS)

    def update(self, speed=1.0):
        self.scroll = (self.scroll + 0.3 * speed) % self.nebula_h
        self.planet_y += 0.16 * speed
        if self.planet_y > self.screen_height + 40:
            self.planet_y = -self.planet.get_height() - 40
            self.planet_x = random.randint(-40, self.screen_width - 200)
        for star in self.stars:
            star.update(speed)

    def draw(self, surface):
        y = int(self.scroll)
        surface.blit(self.nebula, (0, y - self.nebula_h))
        surface.blit(self.nebula, (0, y))
        surface.blit(self.planet, (int(self.planet_x), int(self.planet_y)))
        for star in self.stars:
            star.draw(surface)
