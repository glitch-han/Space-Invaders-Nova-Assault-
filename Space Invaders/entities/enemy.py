import math
import pygame
from entities.sprites import load_sprite, flash_sprite


class Enemy:
    STATS = {
        "normal": {"hp": 1, "speed": 4.0, "points": 10, "size": (78, 78), "hit": (0.16, 0.20)},
        "fast": {"hp": 1, "speed": 5.5, "points": 20, "size": (72, 72), "hit": (0.16, 0.14)},
        "tank": {"hp": 2, "speed": 2.7, "points": 35, "size": (92, 92), "hit": (0.14, 0.14)},
        "boss": {"hp": 10, "speed": 2.0, "points": 250, "size": (204, 136), "hit": (0.06, 0.10)},
    }
    SWAY = {"normal": (0.02, 20), "fast": (0.06, 35), "tank": (0.025, 15), "boss": (0.03, 170)}
    BOSS_ROW_Y = 108
    ESCORT_ROW_Y = 262

    def __init__(self, index, total_enemies, screen_width, kind="normal", level=1, escort=False, screen_height=600):
        self.kind = kind if kind in self.STATS else "normal"
        stats = self.STATS[self.kind]

        self.width, self.height = stats["size"]
        self.hit_x, self.hit_y = stats["hit"]
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = load_sprite("assets/images/enemy_%s.png" % self.kind, (self.width, self.height))
        self.flash_image = flash_sprite(self.image)

        if self.kind == "boss":
            self.target_mid_x = screen_width // 2 - self.width // 2
            self.target_mid_y = self.BOSS_ROW_Y
        else:
            spacing = screen_width / (total_enemies + 1)
            self.target_mid_x = spacing * (index + 1) - (self.width // 2)
            if escort:
                self.target_mid_y = self.ESCORT_ROW_Y + (36 if index % 2 == 0 else 0)
            elif total_enemies > 10:
                self.target_mid_y = 112 + (0, 46, 92)[index % 3]
            else:
                self.target_mid_y = 112 + (0, 56)[index % 2]

        self.sway_freq, self.sway_amp = self.SWAY[self.kind]
        self.phase = 0.0 if self.kind == "boss" else index * 0.8
        self.x = self.slot_x(0)
        self.y = -self.height
        self.state = "entering"
        self.speed = stats["speed"] * (1 + max(0, level - 1) * 0.04)
        self.dx = 0
        self.dy = 0
        self.hp = stats["hp"] + (max(0, level - 5) // 5 if self.kind == "boss" else 0)
        self.max_hp = self.hp
        self.points = stats["points"] + max(0, level - 1) * (5 if self.kind != "boss" else 20)
        self.age = 0
        self.flash = 0
        self.attack_cooldown = 90
        self.level = level
        self.rebound = 0.0
        self.bounce_point = None
        self.last_blast = None

    def slot_x(self, age=None):
        age = self.age if age is None else age
        return self.target_mid_x + self.sway_amp * math.sin(age * self.sway_freq + self.phase)

    def start_drop(self, target_x, target_y):
        self.state = "dropping"
        distance_x = target_x - self.x
        distance_y = target_y - self.y
        distance = (distance_x ** 2 + distance_y ** 2) ** 0.5
        drop_speed = self.speed
        if distance > 0:
            self.dx = (distance_x / distance) * drop_speed
            self.dy = (distance_y / distance) * drop_speed
        else:
            self.dx = 0
            self.dy = drop_speed

    def take_damage(self):
        self.hp -= 1
        self.flash = 4
        return self.hp <= 0

    def center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    def update(self):
        self.age += 1
        if self.flash > 0:
            self.flash -= 1

        if self.state == "entering":
            self.x = self.slot_x()
            if self.y < self.target_mid_y:
                self.y += max(1.5, self.speed * 0.55)
            else:
                self.y = self.target_mid_y
                self.state = "waiting"

        elif self.state == "waiting":
            self.x = self.slot_x()
            if self.kind == "boss":
                self.attack_cooldown -= 1

        elif self.state == "dropping":
            self.x += self.dx
            self.y += self.dy

            if self.kind == "fast":
                self.x += math.sin(self.age * 0.15 + self.phase) * 1.8

            left_wall = -self.width * 0.25
            right_wall = self.screen_width - self.width * 0.75
            if self.x < left_wall:
                self.x = left_wall
                self.dx = abs(self.dx)
            elif self.x > right_wall:
                self.x = right_wall
                self.dx = -abs(self.dx)

            if self.y + self.height >= self.screen_height:
                self.y = self.screen_height - self.height
                self.state = "returning"
                self.rebound = 1.0
                self.bounce_point = (self.x + self.width / 2, self.screen_height - 4)

        elif self.state == "returning":
            goal_x = self.slot_x()
            step = max(6.0, self.speed * 1.5) * (1 + self.rebound)
            self.rebound = max(0.0, self.rebound - 0.03)
            gx = goal_x - self.x
            gy = self.target_mid_y - self.y
            distance = (gx ** 2 + gy ** 2) ** 0.5
            if distance <= step:
                self.x = goal_x
                self.y = self.target_mid_y
                self.state = "waiting"
            else:
                self.x += gx / distance * step
                self.y += gy / distance * step

    def get_rect(self):
        px = int(self.width * self.hit_x)
        py = int(self.height * self.hit_y)
        return pygame.Rect(int(self.x) + px, int(self.y) + py, self.width - px * 2, self.height - py * 2)

    def draw(self, screen):
        if self.state == "dead":
            return
        bob = 0
        if self.state == "waiting":
            bob = math.sin(self.age * 0.06 + self.phase) * (2 if self.kind == "boss" else 3.5)
        image = self.flash_image if self.flash > 0 else self.image
        screen.blit(image, (int(self.x), int(self.y + bob)))

        if self.kind == "tank" and self.max_hp > 1 and self.state != "entering":
            bar_w = int(self.width * 0.6)
            bar_x = int(self.x + (self.width - bar_w) / 2)
            bar_y = int(self.y + bob) - 4
            pygame.draw.rect(screen, (30, 20, 34), (bar_x, bar_y, bar_w, 5), border_radius=2)
            pygame.draw.rect(screen, (110, 255, 160),
                             (bar_x, bar_y, int(bar_w * max(0, self.hp) / self.max_hp), 5), border_radius=2)
