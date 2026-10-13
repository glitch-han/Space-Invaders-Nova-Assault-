import os
import sys
import pygame
from entities.sprites import load_font

FOLDER = "profile_pictures"
EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tga")
PICTURE_SIZE = 256
MAX_BYTES = 40 * 1024 * 1024
MAX_PIXELS = 50_000_000
BADGE_COLORS = ((0, 229, 255), (255, 64, 200), (255, 200, 60), (80, 255, 150), (150, 100, 255), (255, 140, 50))


def user_key(username):
    return (username or "").strip().lower()


def pick_image_file():
    if sys.platform == "darwin":
        return None
    try:
        import tkinter
        from tkinter import filedialog
    except ImportError:
        return None
    try:
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Choose a profile picture",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tga"), ("All files", "*.*")],
        )
        root.destroy()
    except Exception as e:
        print(f"[Avatar] File dialog unavailable: {e}")
        return None
    return path or None


def crop_square(surface):
    w, h = surface.get_size()
    side = min(w, h)
    return surface.subsurface(pygame.Rect((w - side) // 2, (h - side) // 2, side, side)).copy()


def circle_from_surface(surface, size):
    scaled = pygame.transform.smoothscale(crop_square(surface).convert_alpha(), (size, size))
    picture = pygame.Surface((size, size), pygame.SRCALPHA)
    picture.fill((8, 12, 34, 255))
    picture.blit(scaled, (0, 0))
    mask = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size * 2, size * 2), size * 2)
    mask = pygame.transform.smoothscale(mask, (size, size))
    picture.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return picture


class AvatarManager:
    def __init__(self, settings, folder=FOLDER):
        self.settings = settings
        self.folder = folder
        self._circles = {}
        self._badges = {}

    def library(self):
        if not os.path.isdir(self.folder):
            return []
        files = [f for f in os.listdir(self.folder)
                 if f.lower().endswith(EXTENSIONS) and os.path.isfile(os.path.join(self.folder, f))]
        files.sort(key=lambda f: os.path.getmtime(os.path.join(self.folder, f)), reverse=True)
        return files

    def next_name(self):
        n = 1
        while os.path.exists(os.path.join(self.folder, "pic_%03d.png" % n)):
            n += 1
        return "pic_%03d.png" % n

    def add_from_path(self, path):
        try:
            if not path or not os.path.isfile(path) or os.path.getsize(path) > MAX_BYTES:
                return None
            image = pygame.image.load(path)
            if image.get_width() * image.get_height() > MAX_PIXELS:
                return None
            picture = pygame.transform.smoothscale(crop_square(image.convert_alpha()), (PICTURE_SIZE, PICTURE_SIZE))
            os.makedirs(self.folder, exist_ok=True)
            name = self.next_name()
            pygame.image.save(picture, os.path.join(self.folder, name))
            return name
        except (pygame.error, OSError) as e:
            print(f"[Avatar] Could not add {path}: {e}")
            return None

    def filename_for(self, username):
        filename = self.settings.get_picture(user_key(username))
        if filename and os.path.isfile(os.path.join(self.folder, filename)):
            return filename
        return None

    def assign(self, username, filename):
        self.settings.set_picture(user_key(username), filename)

    def clear(self, username):
        self.settings.set_picture(user_key(username), None)

    def rename(self, old_name, new_name):
        self.settings.rename_picture_owner(user_key(old_name), user_key(new_name))

    def circle_from_file(self, filename, size):
        key = (filename, size)
        circle = self._circles.get(key)
        if circle is None:
            try:
                image = pygame.image.load(os.path.join(self.folder, filename)).convert_alpha()
                circle = circle_from_surface(image, size)
            except (pygame.error, OSError):
                circle = False
            self._circles[key] = circle
        return circle or None

    def circle_for(self, username, size):
        filename = self.filename_for(username)
        return self.circle_from_file(filename, size) if filename else None

    def badge(self, username, size):
        key = (user_key(username), size)
        badge = self._badges.get(key)
        if badge is None:
            name = user_key(username) or "?"
            color = BADGE_COLORS[sum(ord(c) for c in name) % len(BADGE_COLORS)]
            badge = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            pygame.draw.circle(badge, (*[int(c * 0.28) + 8 for c in color], 255), (size * 2, size * 2), size * 2)
            badge = pygame.transform.smoothscale(badge, (size, size))
            letter = load_font("ui", max(12, int(size * 0.62))).render(name[0].upper(), True, color)
            badge.blit(letter, letter.get_rect(center=(size // 2, size // 2 + 1)))
            self._badges[key] = badge
        return badge
