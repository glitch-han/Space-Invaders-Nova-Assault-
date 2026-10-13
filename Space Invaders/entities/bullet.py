import pygame
from entities.sprites import load_sprite, rotate_sprite


class Bullet:
    def __init__(self, x, y, direction=-1, screen_height=600, vx=0.0, speed=7, angle=0.0, life=None,
                 blast_id=None, center_y=None):
        self.blast_id = blast_id
        self.life = life
        if blast_id is not None:
            self.image = rotate_sprite(load_sprite("assets/images/pellet.png", (12, 30)), angle)
            self.width, self.height = self.image.get_size()
            self.hit_w, self.hit_h = 10, 14
        elif direction < 0:
            self.width, self.height = 18, 45
            self.image = load_sprite("assets/images/bullet.png", (self.width, self.height))
            self.hit_w, self.hit_h = 10, 34
        else:
            self.width, self.height = 28, 28
            self.image = load_sprite("assets/images/enemy_bullet.png", (self.width, self.height))
            self.hit_w, self.hit_h = 14, 14
        self.x = x - self.width / 2
        self.y = center_y - self.height / 2 if center_y is not None else y
        self.vx = vx
        self.speed = speed
        self.direction = direction
        self.screen_height = screen_height
        self.is_active = True

    def update(self):
        self.y += self.speed * self.direction
        self.x += self.vx
        if self.life is not None:
            self.life -= 1
            if self.life <= 0:
                self.is_active = False
        if self.direction < 0 and self.y < -self.height:
            self.is_active = False
        elif self.direction > 0 and self.y > self.screen_height:
            self.is_active = False
        if self.x < -60 or self.x > 860:
            self.is_active = False

    def get_rect(self):
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        return pygame.Rect(int(cx - self.hit_w / 2), int(cy - self.hit_h / 2), self.hit_w, self.hit_h)

    def draw(self, screen):
        if self.is_active:
            screen.blit(self.image, (int(self.x), int(self.y)))
