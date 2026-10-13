import os
import pygame

FONT_FILES = {
    "title": os.path.join("assets", "fonts", "Audiowide-Regular.ttf"),
    "ui": os.path.join("assets", "fonts", "Rajdhani-Bold.ttf"),
}

_raw = {}
_scaled = {}
_fonts = {}
_glows = {}
_flashed = {}
_rotated = {}


def load_sprite(path, size=None, flip_vertical=False, opaque=False):
    key = (path, size, flip_vertical, opaque)
    sprite = _scaled.get(key)
    if sprite is not None:
        return sprite

    image = _raw.get((path, opaque))
    if image is None:
        loaded = pygame.image.load(path)
        image = loaded.convert() if opaque else loaded.convert_alpha()
        _raw[(path, opaque)] = image

    sprite = image
    if size is not None and tuple(size) != image.get_size():
        sprite = pygame.transform.smoothscale(sprite, size)
    if flip_vertical:
        sprite = pygame.transform.flip(sprite, False, True)

    _scaled[key] = sprite
    return sprite


def flash_sprite(sprite, amount=70):
    key = (id(sprite), amount)
    flashed = _flashed.get(key)
    if flashed is None:
        flashed = sprite.copy()
        flashed.fill((amount, amount, amount, 0), special_flags=pygame.BLEND_RGB_ADD)
        _flashed[key] = flashed
    return flashed


def rotate_sprite(sprite, angle):
    key = (id(sprite), round(angle, 1))
    rotated = _rotated.get(key)
    if rotated is None:
        rotated = pygame.transform.rotate(sprite, -angle)
        _rotated[key] = rotated
    return rotated


def load_font(role, size):
    key = (role, size)
    font = _fonts.get(key)
    if font is None:
        path = FONT_FILES.get(role)
        if path and os.path.exists(path):
            font = pygame.font.Font(path, size)
        else:
            font = pygame.font.SysFont("Arial", size, bold=True)
        _fonts[key] = font
    return font


def make_glow(radius, color, intensity=1.0):
    radius = max(2, int(radius))
    key = (radius, tuple(color), round(intensity, 2))
    glow = _glows.get(key)
    if glow is None:
        glow = pygame.Surface((radius * 2, radius * 2))
        glow.fill((0, 0, 0))
        for r in range(radius, 0, -1):
            falloff = (1 - r / radius) ** 2 * intensity
            shade = tuple(min(255, int(c * falloff)) for c in color)
            pygame.draw.circle(glow, shade, (radius, radius), r)
        _glows[key] = glow
    return glow


def draw_glow(surface, center, radius, color, intensity=1.0):
    glow = make_glow(radius, color, intensity)
    surface.blit(glow, (int(center[0]) - glow.get_width() // 2, int(center[1]) - glow.get_height() // 2),
                 special_flags=pygame.BLEND_RGB_ADD)
