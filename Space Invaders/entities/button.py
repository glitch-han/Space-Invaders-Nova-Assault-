import pygame
from entities.sprites import load_font
from entities.ui import draw_panel, mix, INK, RED
from entities.theme import theme


class MobileButtons:
    def __init__(self, screen_width=800, screen_height=600):
        margin = 18
        self.left = pygame.Rect(margin, screen_height - 82, 92, 62)
        self.right = pygame.Rect(margin + 106, screen_height - 82, 92, 62)
        self.fire = pygame.Rect(screen_width - 132, screen_height - 82, 114, 62)
        self.font = load_font("ui", 30)
        self.layer = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

    def draw(self, screen, held=None):
        held = held or set()
        layer = self.layer
        layer.fill((0, 0, 0, 0))
        for rect, name in ((self.left, "left"), (self.right, "right"), (self.fire, "fire")):
            color = RED if name == "fire" else theme.accent
            active = name in held
            fill = (*mix(INK, color, 0.5 if active else 0.16), 150 if active else 105)
            draw_panel(layer, rect, fill, color, radius=14, glow=active)
            if name == "fire":
                text = self.font.render("FIRE", True, (255, 235, 235))
                layer.blit(text, text.get_rect(center=rect.center))
            else:
                self.draw_arrow(layer, rect, -1 if name == "left" else 1)
        screen.blit(layer, (0, 0))

    def draw_arrow(self, surface, rect, direction):
        cx, cy = rect.center
        half_w, half_h = 10, 15
        if direction < 0:
            points = [(cx + half_w, cy - half_h), (cx + half_w, cy + half_h), (cx - half_w, cy)]
        else:
            points = [(cx - half_w, cy - half_h), (cx - half_w, cy + half_h), (cx + half_w, cy)]
        pygame.draw.polygon(surface, (235, 250, 255), points)

    def held(self):
        if not pygame.mouse.get_pressed()[0]:
            return set()
        pos = pygame.mouse.get_pos()
        return {name for name, rect in (("left", self.left), ("right", self.right), ("fire", self.fire))
                if rect.collidepoint(pos)}

    def handle_mouse(self, player, events):
        held = self.held()
        if "left" in held:
            player.move_left()
        if "right" in held:
            player.move_right()
        if "fire" in held:
            return True

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.fire.collidepoint(event.pos):
                    return True
        return False
