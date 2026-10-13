import pygame
from entities.sprites import load_font
from entities.theme import theme

CYAN = (0, 229, 255)
MAGENTA = (255, 64, 200)
GOLD = (255, 200, 60)
GREEN = (80, 255, 150)
RED = (255, 70, 90)
ORANGE = (255, 140, 50)
VIOLET = (150, 100, 255)
WHITE = (240, 246, 255)
DIM = (140, 156, 196)
INK = (6, 9, 26)

_text_cache = {}
_shadow_cache = {}
_panel_cache = {}
_glow_text_cache = {}


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def render_text(text, role, size, color):
    key = (text, role, size, color)
    surf = _text_cache.get(key)
    if surf is None:
        if len(_text_cache) > 500:
            _text_cache.clear()
        surf = load_font(role, size).render(text, True, color)
        _text_cache[key] = surf
    return surf


def render_shadow(text, role, size):
    key = (text, role, size)
    surf = _shadow_cache.get(key)
    if surf is None:
        if len(_shadow_cache) > 500:
            _shadow_cache.clear()
        surf = load_font(role, size).render(text, True, (0, 0, 0))
        surf.set_alpha(150)
        _shadow_cache[key] = surf
    return surf


def draw_text(surface, text, role, size, color, pos, anchor="center", shadow=True, alpha=255):
    surf = render_text(text, role, size, color)
    rect = surf.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        surface.blit(render_shadow(text, role, size), rect.move(2, 2))
    if alpha < 255:
        temp = surf.copy()
        temp.set_alpha(alpha)
        surface.blit(temp, rect)
    else:
        surface.blit(surf, rect)
    return rect


def glow_text_surface(text, role, size, color, glow, gradient=None, spread=10):
    key = (text, role, size, color, glow, gradient)
    cached = _glow_text_cache.get(key)
    if cached is not None:
        return cached
    if len(_glow_text_cache) > 120:
        _glow_text_cache.clear()
    font = load_font(role, size)
    base = font.render(text, True, (255, 255, 255))
    w, h = base.get_size()
    if gradient:
        grad = pygame.Surface((w, h))
        for y in range(h):
            pygame.draw.line(grad, mix(gradient[0], gradient[1], y / max(1, h - 1)), (0, y), (w, y))
        base.blit(grad, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    else:
        base.fill(color, special_flags=pygame.BLEND_RGB_MULT)
    pad = spread * 2
    source = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    source.blit(font.render(text, True, glow), (pad, pad))
    quarter = pygame.transform.smoothscale(source, (max(2, source.get_width() // 4), max(2, source.get_height() // 4)))
    half = pygame.transform.smoothscale(quarter, (max(2, source.get_width() // 2), max(2, source.get_height() // 2)))
    blurred = pygame.transform.smoothscale(half, source.get_size())
    result = pygame.Surface(source.get_size(), pygame.SRCALPHA)
    result.blit(blurred, (0, 0))
    result.blit(blurred, (0, 0))
    result.blit(blurred, (0, 0))
    result.blit(base, (pad, pad))
    _glow_text_cache[key] = result
    return result


def draw_glow_text(surface, text, role, size, color, glow, center, gradient=None, alpha=255):
    surf = glow_text_surface(text, role, size, color, glow, gradient)
    rect = surf.get_rect(center=center)
    if alpha < 255:
        temp = surf.copy()
        temp.set_alpha(alpha)
        surface.blit(temp, rect)
    else:
        surface.blit(surf, rect)
    return rect


def panel_surface(w, h, fill, border, radius, glow):
    key = (w, h, fill, border, radius, glow)
    cached = _panel_cache.get(key)
    if cached is not None:
        return cached
    if len(_panel_cache) > 150:
        _panel_cache.clear()
    m = 8
    surf = pygame.Surface((w + m * 2, h + m * 2), pygame.SRCALPHA)
    body = pygame.Rect(m, m, w, h)
    pygame.draw.rect(surf, fill, body, border_radius=radius)
    if glow:
        for k, a in ((6, 18), (4, 32), (2, 60)):
            pygame.draw.rect(surf, (*border, a), body.inflate(k * 2, k * 2), width=2, border_radius=radius + k)
    pygame.draw.rect(surf, (*border, 235), body, 2, border_radius=radius)
    hi = pygame.Rect(m + radius, m + 3, w - radius * 2, 1)
    if hi.width > 0:
        pygame.draw.rect(surf, (255, 255, 255, 45), hi)
    _panel_cache[key] = surf
    return surf


def draw_panel(surface, rect, fill=(8, 12, 34, 205), border=None, radius=14, glow=True):
    rect = pygame.Rect(rect)
    if border is None:
        border = theme.accent
    surf = panel_surface(rect.w, rect.h, tuple(fill), tuple(border), radius, glow)
    surface.blit(surf, (rect.x - 8, rect.y - 8))


def draw_bar(surface, rect, fraction, color, back=(14, 18, 42)):
    rect = pygame.Rect(rect)
    fraction = max(0.0, min(1.0, fraction))
    radius = rect.h // 2
    pygame.draw.rect(surface, back, rect, border_radius=radius)
    fill_w = int(rect.w * fraction)
    if fill_w > 0:
        fill_rect = pygame.Rect(rect.x, rect.y, max(fill_w, rect.h), rect.h)
        pygame.draw.rect(surface, color, fill_rect, border_radius=radius)
        shine = pygame.Rect(fill_rect.x + 3, fill_rect.y + 2, max(1, fill_rect.w - 6), max(1, rect.h // 3))
        pygame.draw.rect(surface, mix(color, (255, 255, 255), 0.4), shine, border_radius=radius)
    pygame.draw.rect(surface, mix(color, (0, 0, 0), 0.35), rect, 1, border_radius=radius)


def draw_toggle(surface, rect, on):
    rect = pygame.Rect(rect)
    track = GREEN if on else (70, 78, 108)
    pygame.draw.rect(surface, mix(INK, track, 0.35), rect, border_radius=rect.h // 2)
    pygame.draw.rect(surface, track, rect, 2, border_radius=rect.h // 2)
    r = rect.h // 2 - 4
    cx = rect.right - rect.h // 2 if on else rect.x + rect.h // 2
    pygame.draw.circle(surface, track if on else (120, 128, 160), (cx, rect.centery), r)
    pygame.draw.circle(surface, (255, 255, 255), (cx - 2, rect.centery - 2), max(2, r // 3))


class Button:
    def __init__(self, rect, label, color, size=28):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.size = size

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface, mouse_pos, mouse_down=False):
        hovered = self.rect.collidepoint(mouse_pos)
        fill = (*mix(INK, self.color, 0.42 if hovered else 0.2), 225)
        border = mix(self.color, (255, 255, 255), 0.25) if hovered else self.color
        rect = self.rect.move(0, 2) if (hovered and mouse_down) else self.rect
        draw_panel(surface, rect, fill, border, radius=12, glow=hovered)
        text_color = (255, 255, 255) if hovered else mix(self.color, (255, 255, 255), 0.72)
        draw_text(surface, self.label, "ui", self.size, text_color, rect.center)
