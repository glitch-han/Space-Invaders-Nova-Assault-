import math
import random
import pygame
from entities.player import Player, compose_ship, draw_engine_flames
from entities.button import MobileButtons
from entities.enemy import Enemy
from entities.bullet import Bullet
from entities.powerup import PowerUp, POWERUP_TYPES
from entities.effects import Particle, Shockwave, FloatingText, Background
from entities.ships import SHIPS, SHIP_ORDER, DEFAULT_SHIP, ship_info
from entities.theme import theme, THEME_ORDER, THEMES
from entities.sprites import load_font, load_sprite, draw_glow
from entities.ui import (Button, draw_text, draw_glow_text, draw_panel, draw_bar, draw_toggle, render_text, mix,
                         MAGENTA, GOLD, GREEN, RED, ORANGE, VIOLET, WHITE, DIM, INK)
from managers.db_manager import DatabaseManager
from managers.audio_manager import AudioManager
from managers.settings_manager import SettingsManager
from managers.avatar_manager import AvatarManager, pick_image_file

AVATAR_COLORS = {
    "white": (150, 218, 255),
    "cyan": (0, 229, 255),
    "magenta": (255, 64, 200),
    "yellow": (255, 200, 60),
    "green": (80, 255, 150),
}
AVATAR_ORDER = ["white", "cyan", "magenta", "yellow", "green"]
AVATAR_LABELS = {"white": "ICE", "cyan": "CYAN", "magenta": "MAGENTA", "yellow": "GOLD", "green": "LIME"}
ENEMY_COLORS = {
    "normal": (255, 90, 220),
    "fast": (255, 150, 50),
    "tank": (110, 255, 160),
    "boss": (255, 110, 70),
}
MENU_STATES = ("name_entry", "game_over", "leaderboard", "profile", "settings", "hangar")
PLAY_STATES = ("playing", "blinking", "paused")
LEGEND_SHORT = {"rapid": "TRIPLE SHOT", "shield": "BLOCKS A HIT", "bomb": "CLEARS WAVE",
                "freeze": "STOPS FOES", "life": "+1 LIFE", "scatter": "SHOTGUN"}
LEGEND_NAME = {"rapid": "RAPID", "shield": "SHIELD", "bomb": "BOMB", "freeze": "FREEZE", "life": "LIFE",
               "scatter": "SCATTER"}
SCATTER_ANGLES = (-30, -20, -10, 0, 10, 20, 30)


class GameManager:
    def __init__(self, screen, screen_width, screen_height):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.game_surface = pygame.Surface((screen_width, screen_height))
        self.popup_font = load_font("ui", 28)
        self.tick = 0
        self.settings = SettingsManager()
        theme.apply(self.settings.get_theme())
        self.avatars = AvatarManager(self.settings)
        self.file_picker = pick_image_file
        self.gallery_page = 0
        self.ship_badges = {}

        self.settings_button = Button((668, 12, 118, 38), "SETTINGS", theme.accent, 22)
        self.hangar_button = Button((186, 368, 200, 48), "CHOOSE SHIP", MAGENTA, 26)
        self.launch_button = Button((398, 368, 216, 48), "LAUNCH  (ENTER)", GREEN, 26)
        self.hero_rect = pygame.Rect(344, 146, 112, 112)
        self.hangar_prev = Button((52, 196, 44, 60), "<", theme.accent, 34)
        self.hangar_next = Button((344, 196, 44, 60), ">", theme.accent, 34)
        self.hangar_done = Button((300, 516, 200, 46), "DONE", GREEN, 28)
        self.profile_hangar_button = Button((410, 372, 320, 40), "CHANGE SHIP & COLOR", GOLD, 22)
        self.picture_add_button = Button((66, 238, 170, 40), "ADD PICTURE", GOLD, 22)
        self.picture_remove_button = Button((246, 238, 108, 40), "REMOVE", RED, 22)
        self.gallery_prev = Button((288, 302, 30, 24), "<", VIOLET, 18)
        self.gallery_next = Button((324, 302, 30, 24), ">", VIOLET, 18)
        self.gallery_rects = [pygame.Rect(66 + i * 58, 330, 48, 48) for i in range(5)]
        self.reload_button = Button((120, 310, 250, 60), "PLAY AGAIN", GREEN, 30)
        self.leaderboard_button = Button((430, 310, 250, 60), "LEADERBOARD", theme.accent, 30)
        self.profile_button = Button((120, 390, 250, 60), "PROFILE", GOLD, 30)
        self.switch_player_button = Button((430, 390, 250, 60), "SWITCH PILOT", MAGENTA, 30)
        self.back_button = Button((300, 516, 200, 46), "BACK", VIOLET, 28)
        self.resume_button = Button((275, 232, 250, 56), "RESUME", GREEN, 30)
        self.pause_settings_button = Button((275, 302, 250, 56), "SETTINGS", theme.accent, 30)
        self.end_run_button = Button((275, 372, 250, 56), "END RUN", RED, 30)
        self.pause_rect = pygame.Rect(744, 12, 42, 38)

        self.settings_rows = {}
        names = ("sound", "music", "sound_volume", "music_volume", "mobile_controls", "screen_shake", "theme")
        for i, name in enumerate(names):
            self.settings_rows[name] = pygame.Rect(130, 106 + i * 54, 540, 46)
        slider_y = {name: self.settings_rows[name].y + 5 for name in names}
        self.sound_minus = Button((432, slider_y["sound_volume"], 38, 36), "-", RED, 28)
        self.sound_plus = Button((638, slider_y["sound_volume"], 38, 36), "+", GREEN, 28)
        self.music_minus = Button((432, slider_y["music_volume"], 38, 36), "-", RED, 28)
        self.music_plus = Button((638, slider_y["music_volume"], 38, 36), "+", GREEN, 28)
        self.theme_prev = Button((432, slider_y["theme"], 38, 36), "<", theme.accent, 26)
        self.theme_next = Button((638, slider_y["theme"], 38, 36), ">", theme.accent, 26)
        self.sound_bar = pygame.Rect(480, self.settings_rows["sound_volume"].y + 14, 150, 18)
        self.music_bar = pygame.Rect(480, self.settings_rows["music_volume"].y + 14, 150, 18)
        self.toggle_rects = {}
        for name in ("sound", "music", "mobile_controls", "screen_shake"):
            row = self.settings_rows[name]
            self.toggle_rects[name] = pygame.Rect(row.right - 84, row.centery - 17, 76, 34)
        self.accent_buttons = [self.settings_button, self.hangar_prev, self.hangar_next, self.leaderboard_button,
                               self.pause_settings_button, self.theme_prev, self.theme_next]

        self.swatch_rects = [pygame.Rect(100 + i * 50, 352, 40, 40) for i in range(len(AVATAR_ORDER))]
        self.hangar_thumbs = [pygame.Rect(444 + i * 76, 346, 62, 62) for i in range(len(SHIP_ORDER))]

        self.dim_overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.dim_overlay.fill(theme.dim)
        self.black = pygame.Surface((screen_width, screen_height))
        self.black.fill((0, 0, 0))
        self.white = pygame.Surface((screen_width, screen_height))
        self.white.fill((255, 255, 255))
        self.freeze_overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.freeze_overlay.fill((40, 110, 230, 34))
        self.hud_bar = pygame.Surface((screen_width, 64), pygame.SRCALPHA)
        self.build_hud_bar()
        self.shield_bubble = self.build_shield_bubble()

        self.db = DatabaseManager()
        self.audio = AudioManager()
        self.background = Background(screen_width, screen_height)
        self.buttons = MobileButtons(screen_width, screen_height)

        self.player_id = None
        self.username = ""
        self.input_text = ""
        self.leaderboard_cache = []
        self.profile_stats = None
        self.status_message = ""
        self.status_timer = 0
        ship, color = self.settings.get_loadout()
        self.ship_model = ship if ship in SHIPS else DEFAULT_SHIP
        self.selected_avatar_color = color if color in AVATAR_COLORS else "cyan"
        self.loadout_touched = False
        self.hangar_return_state = "name_entry"
        self.settings_return_state = "name_entry"
        self.fade = 0
        self.flash_alpha = 0
        self.pending_track = None
        self.pending_track_timer = 0

        self.game_state = "name_entry"
        self.reset_game()
        self.audio.play_track("menu")

    def build_hud_bar(self):
        self.hud_bar.fill((0, 0, 0, 0))
        for y in range(64):
            pygame.draw.line(self.hud_bar, (5, 8, 26, int(215 - y * 1.6)), (0, y), (self.screen_width, y))
        pygame.draw.line(self.hud_bar, (*theme.accent, 110), (0, 62), (self.screen_width, 62), 2)

    def apply_theme(self, key):
        theme.apply(key)
        self.settings.set_theme(theme.key)
        self.background.apply_theme()
        self.build_hud_bar()
        self.dim_overlay.fill(theme.dim)
        for button in self.accent_buttons:
            button.color = theme.accent

    def cycle_theme(self, direction):
        self.audio.play("click")
        self.apply_theme(theme.neighbor(direction))

    def build_shield_bubble(self):
        size = 150
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        pygame.draw.circle(surf, (60, 240, 210, 34), (c, c), 66)
        for width, alpha in ((7, 40), (5, 70), (3, 150)):
            pygame.draw.circle(surf, (110, 255, 230, alpha), (c, c), 66, width)
        pygame.draw.circle(surf, (230, 255, 250, 210), (c, c), 66, 2)
        return surf

    def reset_game(self):
        self.player = Player(self.screen_width, self.screen_height, self.ship_model)
        self.apply_avatar(self.selected_avatar_color)

        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.score = 0
        self.display_score = 0
        self.level = 1
        self.spawn_number = 5
        self.lives = 3
        self.combo = 0
        self.best_combo = 0

        self.player_history = []
        self.timer = 0
        self.state_timer = 0
        self.fire_cooldown = 0

        self.rapid_fire_timer = 0
        self.scatter_timer = 0
        self.blast_counter = 0
        self.invuln_timer = 0
        self.shield_active = self.player.starts_shielded
        self.freeze_timer = 0
        self.powerup_spawn_timer = 180
        self.active_powerup = None

        self.is_new_high_score = False
        self.level_transition_timer = 0
        self.level_banner = ""
        self.paused = False

        self.particles = []
        self.shockwaves = []
        self.floating_texts = []
        self.blast_queue = []
        self.shake_timer = 0
        self.shake_intensity = 0
        self.flash_alpha = 0

        self.spawn_enemies()

    def apply_avatar(self, color_name):
        tint = AVATAR_COLORS.get(color_name, AVATAR_COLORS["white"])
        self.player.set_tint(tint)
        self.life_icon = compose_ship(30, tint, self.ship_model)
        self.life_icon_dim = self.life_icon.copy()
        self.life_icon_dim.fill((255, 255, 255, 55), special_flags=pygame.BLEND_RGBA_MULT)

    def spawn_enemies(self):
        self.enemies = []
        self.enemy_bullets = []
        self.bullets = []
        self.timer = 0
        self.level_transition_timer = 75

        if self.level % 5 == 0:
            self.enemies.append(Enemy(0, 1, self.screen_width, kind="boss", level=self.level))
            escort_count = min(3, 1 + self.level // 5)
            for i in range(escort_count):
                self.enemies.append(
                    Enemy(i, escort_count, self.screen_width,
                          kind="fast" if i % 2 == 0 else "normal", level=self.level, escort=True)
                )
            self.level_banner = f"BOSS LEVEL {self.level}"
            if self.game_state in PLAY_STATES:
                self.audio.play("warning")
        else:
            count = min(14, 4 + self.level)
            self.spawn_number = count
            for i in range(count):
                roll = random.random()
                if self.level >= 4 and roll < 0.18:
                    kind = "tank"
                elif self.level >= 2 and roll < 0.42:
                    kind = "fast"
                else:
                    kind = "normal"
                self.enemies.append(Enemy(i, count, self.screen_width, kind=kind, level=self.level))
            self.level_banner = f"LEVEL {self.level}"
        self.sync_music()

    def advance_level(self):
        cleared = self.level
        bonus = 100 * cleared
        self.score += bonus
        self.floating_texts.append(
            FloatingText(self.screen_width // 2, 268, f"+{bonus} LEVEL BONUS", (140, 255, 180), self.popup_font)
        )
        self.level += 1
        self.combo = min(self.combo, 10)
        self.active_powerup = None
        self.freeze_timer = 0
        self.spawn_enemies()
        if self.level % 5 != 0:
            self.audio.play("levelup")
        self.show_status(f"LEVEL {self.level} - STAY SHARP!", 120)

    def music_for_state(self):
        if self.game_state in PLAY_STATES or (self.game_state == "settings" and self.settings_return_state == "paused"):
            boss_alive = any(e.kind == "boss" and e.state != "dead" for e in self.enemies)
            return "boss" if boss_alive else "theme"
        return "menu"

    def sync_music(self):
        self.pending_track = None
        self.audio.play_track(self.music_for_state())

    def change_state(self, new_state, sync=True):
        old = self.game_state
        self.game_state = new_state
        if new_state in MENU_STATES and old != new_state:
            self.fade = 200
        if sync:
            self.sync_music()

    def update(self, events):
        self.tick += 1
        self.background.update(0.3 if self.freeze_timer > 0 else (1.0 if self.game_state in PLAY_STATES else 0.6))
        self.particles = [p for p in self.particles if p.is_alive()]
        for p in self.particles:
            p.update()
        self.shockwaves = [s for s in self.shockwaves if s.is_alive()]
        for s in self.shockwaves:
            s.update()
        self.floating_texts = [t for t in self.floating_texts if t.is_alive()]
        for t in self.floating_texts:
            t.update()
        self.process_blast_queue()
        if self.shake_timer > 0:
            self.shake_timer -= 1
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 14)
        if self.fade > 0:
            self.fade = max(0, self.fade - 16)
        if self.pending_track:
            self.pending_track_timer -= 1
            if self.pending_track_timer <= 0:
                self.audio.play_track(self.pending_track)
                self.pending_track = None

        settings_clicked = False
        if self.game_state in ("name_entry", "game_over", "leaderboard", "profile"):
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.settings_button.contains(event.pos):
                        self.audio.play("click")
                        self.settings_return_state = self.game_state
                        self.change_state("settings")
                        settings_clicked = True
                        break

        if not settings_clicked:
            if self.game_state == "name_entry":
                self.update_name_entry(events)
            elif self.game_state == "playing":
                self.update_playing(events)
            elif self.game_state == "blinking":
                self.update_blinking()
            elif self.game_state == "paused":
                self.update_paused(events)
            elif self.game_state == "game_over":
                self.update_game_over(events)
            elif self.game_state == "leaderboard":
                self.update_leaderboard(events)
            elif self.game_state == "profile":
                self.update_profile(events)
            elif self.game_state == "settings":
                self.update_settings(events)
            elif self.game_state == "hangar":
                self.update_hangar(events)

        if self.status_timer > 0:
            self.status_timer -= 1
        self.draw()

    def process_blast_queue(self):
        remaining = []
        for blast in self.blast_queue:
            blast["delay"] -= 1
            if blast["delay"] <= 0:
                self.explode(blast["x"], blast["y"], "boss", small=True)
                self.audio.play("explosion")
            else:
                remaining.append(blast)
        self.blast_queue = remaining

    def pause_game(self):
        self.paused = True
        self.audio.play("click")
        self.change_state("paused")

    def resume_game(self):
        self.paused = False
        self.audio.play("click")
        self.change_state("playing")

    def update_playing(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_p, pygame.K_ESCAPE):
                self.pause_game()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.pause_rect.collidepoint(event.pos):
                    self.pause_game()
                    return

        if self.invuln_timer > 0:
            self.invuln_timer -= 1

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move_right()

        screen_button_fired = False
        if self.settings.get("mobile_controls"):
            screen_button_fired = self.buttons.handle_mouse(self.player, events)
        keyboard_fired = keys[pygame.K_SPACE] or keys[pygame.K_UP]

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

        rapid = self.rapid_fire_timer > 0
        scatter = self.scatter_timer > 0
        if rapid:
            self.rapid_fire_timer -= 1
        if scatter:
            self.scatter_timer -= 1
            can_fire = self.fire_cooldown == 0 and len(self.bullets) < 60
        elif rapid:
            can_fire = len(self.bullets) < 3 and self.fire_cooldown == 0
        else:
            can_fire = len(self.bullets) == 0 and self.fire_cooldown == 0
        self.player.thrust = 1.6 if rapid else 1.0

        if (screen_button_fired or keyboard_fired) and can_fire:
            if scatter:
                self.fire_scatter(rapid)
            else:
                px, _ = self.player.center()
                self.bullets.append(Bullet(px, self.player.y - 22, speed=self.player.bolt_speed))
                self.audio.play("shoot")
                self.fire_cooldown = 7 if rapid else 3

        self.player.keep_inside_screen()
        self.player_history.append((self.player.x, self.player.y))
        if len(self.player_history) > 60:
            self.player_history.pop(0)

        for bullet in self.bullets:
            bullet.update()
        self.bullets = [b for b in self.bullets if b.is_active]

        frozen = self.freeze_timer > 0
        if frozen:
            self.freeze_timer -= 1

        self.timer += 1
        drop_interval = max(80, 180 - self.level * 5)
        if not frozen and self.timer >= drop_interval:
            waiting = [e for e in self.enemies if e.state == "waiting" and e.kind != "boss"]
            if waiting:
                chosen = random.choice(waiting)
                if self.player_history:
                    target_x, target_y = self.player_history[0]
                else:
                    target_x, target_y = self.player.x, self.player.y
                chosen.start_drop(target_x, target_y)
            self.timer = 0

        all_dead = True
        for enemy in self.enemies:
            if not frozen:
                enemy.update()
            if enemy.bounce_point:
                bx, by = enemy.bounce_point
                enemy.bounce_point = None
                color = ENEMY_COLORS.get(enemy.kind, ORANGE)
                self.spawn_particles(bx, by, color, 10)
                self.shockwaves.append(Shockwave(bx, by, color, 54, 16, 4))
                self.audio.play("hit")
            if enemy.state != "dead":
                all_dead = False

            if not frozen and enemy.state == "waiting":
                if enemy.kind == "boss":
                    if enemy.attack_cooldown <= 0 and len(self.enemy_bullets) < 10:
                        self.fire_boss_spread(enemy)
                elif len(self.enemy_bullets) < min(3, 1 + self.level // 3):
                    chance = min(0.012, 0.0025 + self.level * 0.0005)
                    if random.random() < chance:
                        cx, cy = enemy.center()
                        self.enemy_bullets.append(
                            Bullet(cx, cy + enemy.height * 0.3, direction=1, screen_height=self.screen_height)
                        )
                        self.audio.play("enemy_shoot")

        for eb in self.enemy_bullets:
            if not frozen:
                eb.update()
        self.enemy_bullets = [b for b in self.enemy_bullets if b.is_active]

        if all_dead and self.enemies:
            self.advance_level()

        self.powerup_spawn_timer += 1
        powerup_interval = max(240, 520 - self.level * 12)
        if self.powerup_spawn_timer >= powerup_interval and self.active_powerup is None:
            choices = ["rapid", "shield", "bomb", "freeze", "scatter"]
            weights = [25, 25, 18, 18, 18]
            if self.lives < 5:
                choices.append("life")
                weights.append(7)
            kind = random.choices(choices, weights=weights)[0]
            self.active_powerup = PowerUp(
                random.randint(40, self.screen_width - 90),
                self.screen_height,
                kind=kind,
                speed=2.2 + self.level * 0.04
            )
            self.powerup_spawn_timer = 0

        if self.active_powerup:
            self.active_powerup.update()
            if not self.active_powerup.is_active:
                self.active_powerup = None
            elif self.active_powerup.get_rect().colliderect(self.player.get_full_rect()):
                self.collect_powerup(self.active_powerup.kind)
                self.active_powerup = None

        self.check_collisions()

        if self.level_transition_timer > 0:
            self.level_transition_timer -= 1

    def fire_scatter(self, rapid=False):
        px, _ = self.player.center()
        self.blast_counter += 1
        speed = self.player.bolt_speed + 2.5
        muzzle_y = self.player.y - 6
        for base in SCATTER_ANGLES:
            angle = base + random.uniform(-3.5, 3.5)
            rad = math.radians(angle)
            self.bullets.append(
                Bullet(px + math.sin(rad) * 6, 0, speed=speed * math.cos(rad), vx=speed * math.sin(rad), angle=angle,
                       life=36, blast_id=self.blast_counter, center_y=muzzle_y)
            )
        color = POWERUP_TYPES["scatter"]["color"]
        self.spawn_particles(px, muzzle_y, color, 7)
        self.shockwaves.append(Shockwave(px, muzzle_y, color, 46, 10, 4))
        self.audio.play("scatter")
        self.fire_cooldown = 12 if rapid else 22
        self.shake_timer = max(self.shake_timer, 3)
        self.shake_intensity = max(self.shake_intensity, 2)

    def fire_boss_spread(self, boss):
        cx, _ = boss.center()
        count = 3 if boss.level < 15 else 5
        for i in range(count):
            vx = (i - (count - 1) / 2) * 1.9
            self.enemy_bullets.append(
                Bullet(cx, boss.y + boss.height * 0.78, direction=1, screen_height=self.screen_height,
                       vx=vx, speed=5.2)
            )
        boss.attack_cooldown = max(60, 135 - boss.level * 2)
        self.audio.play("enemy_shoot")

    def update_blinking(self):
        self.player.update_blink()
        self.state_timer += 1

        for enemy in self.enemies:
            enemy.update()
        for eb in self.enemy_bullets:
            eb.update()
        self.enemy_bullets = [b for b in self.enemy_bullets if b.is_active]

        if self.state_timer >= 90:
            self.player.is_blinking = False
            self.player.visible = True
            self.player.x = self.screen_width // 2 - self.player.width // 2
            self.change_state("playing")
            self.state_timer = 0
            self.show_status(f"RESPAWNED - {self.lives} LIVES LEFT", 90)

    def update_paused(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_p, pygame.K_ESCAPE):
                self.resume_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.pause_rect.collidepoint(event.pos) or self.resume_button.contains(event.pos):
                    self.resume_game()
                elif self.pause_settings_button.contains(event.pos):
                    self.audio.play("click")
                    self.settings_return_state = "paused"
                    self.change_state("settings")
                elif self.end_run_button.contains(event.pos):
                    self.audio.play("click")
                    self.lives = 0
                    self.finish_run()

    def update_name_entry(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hangar_button.contains(event.pos) or self.hero_rect.collidepoint(event.pos):
                    self.open_hangar("name_entry")
                    return
                if self.launch_button.contains(event.pos):
                    self.audio.play("click")
                    typed = self.input_text.strip()
                    if typed:
                        self.input_text = ""
                        self.submit_name_entry(typed)
                        return
                    self.show_status("TYPE YOUR NAME FIRST", 90)
        self.handle_text_entry(events, self.submit_name_entry)

    def update_game_over(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.reload_button.contains(event.pos):
                    self.start_new_run()
                elif self.leaderboard_button.contains(event.pos):
                    self.audio.play("click")
                    self.leaderboard_cache = self.db.get_leaderboard(10)
                    self.change_state("leaderboard")
                elif self.profile_button.contains(event.pos):
                    self.audio.play("click")
                    self.open_profile_screen()
                elif self.switch_player_button.contains(event.pos):
                    self.audio.play("click")
                    self.switch_player()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.start_new_run()

    def start_new_run(self):
        self.audio.play("click")
        self.reset_game()
        self.change_state("playing")

    def update_leaderboard(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button.contains(event.pos):
                    self.audio.play("click")
                    self.change_state("game_over")
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.change_state("game_over")

    def update_profile(self, events):
        library = self.avatars.library()
        for event in events:
            if event.type == pygame.DROPFILE:
                self.add_picture_from_path(event.file)
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.back_button.contains(pos):
                    self.audio.play("click")
                    self.input_text = ""
                    self.change_state("game_over")
                    return
                if self.profile_hangar_button.contains(pos):
                    self.open_hangar("profile")
                    return
                if self.picture_add_button.contains(pos):
                    self.browse_for_picture()
                elif self.picture_remove_button.contains(pos) and self.avatars.filename_for(self.username):
                    self.avatars.clear(self.username)
                    self.audio.play("click")
                    self.show_status("PICTURE REMOVED", 90)
                elif len(library) > len(self.gallery_rects) and self.gallery_prev.contains(pos):
                    self.gallery_page = max(0, self.gallery_page - 1)
                    self.audio.play("click")
                elif len(library) > len(self.gallery_rects) and self.gallery_next.contains(pos):
                    last_page = (len(library) - 1) // len(self.gallery_rects)
                    self.gallery_page = min(last_page, self.gallery_page + 1)
                    self.audio.play("click")
                else:
                    for idx, rect in enumerate(self.gallery_rects):
                        item = self.gallery_page * len(self.gallery_rects) + idx
                        if item < len(library) and rect.collidepoint(pos):
                            self.avatars.assign(self.username, library[item])
                            self.audio.play("click")
                            self.show_status("PROFILE PICTURE UPDATED!", 90)
        self.handle_text_entry(events, self.submit_profile_rename, allow_cancel=True)

    def browse_for_picture(self):
        self.audio.play("click")
        path = self.file_picker()
        pygame.event.clear()
        if path is None:
            self.show_status("FILE PICKER UNAVAILABLE - DRAG AN IMAGE ONTO THE WINDOW", 180)
        elif path:
            self.add_picture_from_path(path)

    def add_picture_from_path(self, path):
        if not self.username:
            self.show_status("TYPE A PILOT NAME FIRST", 90)
            return False
        filename = self.avatars.add_from_path(path)
        if filename is None:
            self.show_status("COULD NOT READ THAT IMAGE", 120)
            return False
        self.avatars.assign(self.username, filename)
        self.gallery_page = 0
        self.audio.play("powerup")
        self.show_status("PROFILE PICTURE UPDATED!", 100)
        return True

    def ship_badge(self, size):
        key = (self.ship_model, self.selected_avatar_color, size)
        badge = self.ship_badges.get(key)
        if badge is None:
            tint = AVATAR_COLORS[self.selected_avatar_color]
            base = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            pygame.draw.circle(base, (8, 12, 34, 255), (size * 2, size * 2), size * 2)
            badge = pygame.transform.smoothscale(base, (size, size))
            ship = compose_ship(int(size * 0.92), tint, self.ship_model)
            badge.blit(ship, ship.get_rect(center=(size // 2, size // 2)))
            self.ship_badges[key] = badge
        return badge

    def draw_avatar(self, surface, name, center, size, ring=None, ship_fallback=False, glow=False):
        ring = ring or theme.accent
        inner = size - 4
        picture = self.avatars.circle_for(name, inner)
        if picture is None:
            picture = self.ship_badge(inner) if ship_fallback else self.avatars.badge(name, inner)
        if glow:
            draw_glow(surface, center, size, ring, 0.5)
        surface.blit(picture, picture.get_rect(center=center))
        pygame.draw.circle(surface, ring, center, size // 2, 2)

    def open_hangar(self, return_state):
        self.hangar_return_state = return_state
        self.audio.play("click")
        self.change_state("hangar")

    def close_hangar(self):
        self.audio.play("click")
        self.change_state(self.hangar_return_state)

    def update_hangar(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.cycle_ship(-1)
                elif event.key == pygame.K_RIGHT:
                    self.cycle_ship(1)
                elif event.key == pygame.K_UP:
                    self.cycle_avatar_color(-1)
                elif event.key == pygame.K_DOWN:
                    self.cycle_avatar_color(1)
                elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.close_hangar()
                    return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.hangar_prev.contains(pos):
                    self.cycle_ship(-1)
                elif self.hangar_next.contains(pos):
                    self.cycle_ship(1)
                elif self.hangar_done.contains(pos):
                    self.close_hangar()
                    return
                else:
                    for model, rect in zip(SHIP_ORDER, self.hangar_thumbs):
                        if rect.collidepoint(pos):
                            self.select_ship(model)
                    for name, rect in zip(AVATAR_ORDER, self.swatch_rects):
                        if rect.collidepoint(pos):
                            self.select_avatar_color(name)

    def check_collisions(self):
        player_rect = self.player.get_rect()

        for eb in self.enemy_bullets:
            if eb.is_active and eb.get_rect().colliderect(player_rect):
                eb.is_active = False
                self.handle_player_hit()
                return

        for enemy in self.enemies:
            if enemy.state == "dead":
                continue
            enemy_rect = enemy.get_rect()

            if player_rect.colliderect(enemy_rect):
                self.handle_player_hit()
                return

            for bullet in self.bullets:
                if bullet.is_active and bullet.get_rect().colliderect(enemy_rect):
                    if bullet.blast_id is not None:
                        if enemy.last_blast == bullet.blast_id:
                            continue
                        enemy.last_blast = bullet.blast_id
                    bullet.is_active = False
                    defeated = enemy.take_damage()
                    if defeated:
                        enemy.state = "dead"
                        self.handle_enemy_killed(enemy)
                    else:
                        self.spawn_particles(bullet.x + bullet.width / 2, enemy_rect.centery,
                                             (255, 236, 150), 6)
                        self.audio.play("hit")
                    break

    def handle_player_hit(self):
        if self.game_state != "playing" or self.invuln_timer > 0:
            return
        px, py = self.player.center()
        if self.shield_active:
            self.shield_active = False
            self.invuln_timer = 60
            self.spawn_particles(px, py, (110, 255, 230), 22)
            self.shockwaves.append(Shockwave(px, py, (110, 255, 230), 90, 22, 5))
            self.audio.play("shield")
            self.show_status("SHIELD ABSORBED THE HIT!", 90)
            self.shake_timer = 8
            self.shake_intensity = 5
            return

        self.lives -= 1
        self.combo = 0
        self.spawn_particles(px, py, (255, 90, 90), 30)
        self.spawn_particles(px, py, (255, 220, 160), 10)
        self.shockwaves.append(Shockwave(px, py, (255, 90, 90), 110, 26, 6))
        self.shake_timer = 18
        self.shake_intensity = 9
        self.flash_alpha = max(self.flash_alpha, 90)
        self.audio.play("explosion")

        if self.lives <= 0:
            self.finish_run()
            return

        self.change_state("blinking")
        self.player.is_blinking = True
        self.player.visible = False
        self.state_timer = 0
        self.show_status(f"SHIP HIT! {self.lives} LIVES LEFT", 100)

    def finish_run(self):
        self.change_state("game_over", sync=False)
        self.player.is_blinking = False
        self.player.visible = True
        self.save_current_score()
        if not self.is_new_high_score:
            self.audio.play("gameover")
        self.audio.stop_music()
        self.pending_track = "menu"
        self.pending_track_timer = 150

    def explode(self, x, y, kind, small=False):
        color = ENEMY_COLORS.get(kind, ORANGE)
        boss = kind == "boss"
        self.spawn_particles(x, y, color, 14 if small else (34 if boss else 20))
        self.spawn_particles(x, y, (255, 240, 200), 6 if small else 10)
        radius = 150 if (boss and not small) else (80 if boss else 68)
        self.shockwaves.append(Shockwave(x, y, color, radius, 34 if (boss and not small) else 22, 7 if boss else 5))

    def handle_enemy_killed(self, enemy):
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        multiplier = min(5, 1 + self.combo // 5)
        points = enemy.points * multiplier
        self.score += points

        cx, cy = enemy.center()
        self.explode(cx, cy, enemy.kind)

        label = f"+{points}"
        if multiplier > 1:
            label += f" x{multiplier}"
        self.floating_texts.append(FloatingText(cx, cy - 10, label, (255, 226, 130), self.popup_font))
        self.shake_timer = max(self.shake_timer, 8 if enemy.kind == "boss" else 4)
        self.shake_intensity = max(self.shake_intensity, 8 if enemy.kind == "boss" else 3)
        self.audio.play("explosion")

        if enemy.kind == "boss":
            for i in range(7):
                self.blast_queue.append({
                    "delay": 6 + i * 6,
                    "x": cx + random.randint(-int(enemy.width * 0.4), int(enemy.width * 0.4)),
                    "y": cy + random.randint(-int(enemy.height * 0.4), int(enemy.height * 0.4)),
                })
            self.flash_alpha = 190
            self.show_status("BOSS DESTROYED! MASSIVE BONUS!", 150)

    def collect_powerup(self, kind):
        px, py = self.player.center()
        color = POWERUP_TYPES[kind]["color"]
        self.spawn_particles(px, self.player.y, color, 18)
        self.shockwaves.append(Shockwave(px, py, color, 70, 20, 4))
        self.audio.play("shield" if kind == "shield" else ("bomb" if kind == "bomb" else "powerup"))

        if kind == "rapid":
            self.rapid_fire_timer = min(600, self.rapid_fire_timer + 360)
        elif kind == "scatter":
            self.scatter_timer = min(900, self.scatter_timer + 480)
        elif kind == "shield":
            self.shield_active = True
        elif kind == "freeze":
            self.freeze_timer = 300
        elif kind == "life":
            self.lives = min(5, self.lives + 1)
        elif kind == "bomb":
            victims = [e for e in self.enemies if e.state not in ("dead", "entering")]
            destroyed = 0
            for enemy in victims:
                if enemy.kind in ("tank", "boss"):
                    enemy.hp -= 2
                    enemy.flash = 8
                    if enemy.hp <= 0:
                        enemy.state = "dead"
                        destroyed += 1
                        self.score += enemy.points
                else:
                    enemy.state = "dead"
                    destroyed += 1
                    self.score += enemy.points
                ex, ey = enemy.center()
                self.explode(ex, ey, enemy.kind, small=True)
            self.shockwaves.append(Shockwave(px, py, (255, 130, 90), 520, 36, 12))
            self.shake_timer = 20
            self.shake_intensity = 10
            self.flash_alpha = 200
            self.show_status(f"SMART BOMB! {destroyed} ENEMIES CLEARED", 120)
            return

        self.show_status(POWERUP_TYPES[kind]["name"] + "!", 100)

    def submit_name_entry(self, username):
        username = username[:20]
        existing_id = self.db.find_player_by_username(username)
        player_id = existing_id if existing_id is not None else self.db.register_player(username)
        self.username = username
        if player_id is not None:
            self.player_id = player_id
            if existing_id is not None and not self.loadout_touched:
                ship = self.db.get_player_ship(player_id)
                color = self.db.get_player_avatar(player_id)
                if ship in SHIPS:
                    self.ship_model = ship
                if color in AVATAR_COLORS:
                    self.selected_avatar_color = color
                self.settings.set_loadout(self.ship_model, self.selected_avatar_color)
                self.show_status("WELCOME BACK, PILOT!", 90)
            else:
                self.db.update_player_avatar(player_id, self.selected_avatar_color)
                self.db.update_player_ship(player_id, self.ship_model)
                self.show_status("WELCOME, PILOT!", 90)
        else:
            self.player_id = None
            self.show_status("PLAYING OFFLINE - SCORES WON'T BE SAVED", 120)
        self.loadout_touched = False
        self.reset_game()
        self.change_state("playing")

    def save_current_score(self):
        if self.player_id is None:
            self.is_new_high_score = False
            return
        stats_before = self.db.get_player_stats(self.player_id)
        previous_best = stats_before.get("high_score", 0) or 0
        saved = self.db.save_score(self.player_id, self.score, level=self.level)
        self.is_new_high_score = bool(saved and self.score > previous_best and self.score > 0)
        if self.is_new_high_score:
            self.audio.play("highscore")
        else:
            self.show_status("SCORE SAVED!" if saved else "COULD NOT SAVE SCORE", 90)

    def open_profile_screen(self):
        self.profile_stats = (
            self.db.get_player_stats(self.player_id)
            if self.player_id is not None else None
        )
        self.input_text = ""
        self.change_state("profile")

    def submit_profile_rename(self, new_username):
        if self.player_id is None:
            self.show_status("RENAMING NEEDS THE DATABASE", 100)
            return
        if new_username:
            new_username = new_username[:50]
            owner_id = self.db.find_player_by_username(new_username)
            if owner_id is not None and owner_id != self.player_id:
                self.show_status("THAT NAME IS ALREADY TAKEN", 120)
                return
            ok = self.db.update_player_profile(self.player_id, new_username)
            if ok:
                old_name = self.username
                self.username = new_username
                self.avatars.rename(old_name, new_username)
                self.show_status("PROFILE UPDATED!", 90)
            else:
                self.show_status("COULD NOT UPDATE PROFILE", 90)
        self.change_state("game_over")

    def commit_loadout(self):
        self.loadout_touched = True
        self.settings.set_loadout(self.ship_model, self.selected_avatar_color)
        self.apply_avatar(self.selected_avatar_color)
        if self.player_id is not None:
            self.db.update_player_avatar(self.player_id, self.selected_avatar_color)
            self.db.update_player_ship(self.player_id, self.ship_model)

    def select_avatar_color(self, name):
        if name in AVATAR_COLORS:
            self.selected_avatar_color = name
            self.audio.play("click")
            self.commit_loadout()

    def select_ship(self, model):
        if model in SHIPS:
            self.ship_model = model
            self.audio.play("click")
            self.commit_loadout()

    def cycle_avatar_color(self, direction):
        idx = AVATAR_ORDER.index(self.selected_avatar_color)
        self.select_avatar_color(AVATAR_ORDER[(idx + direction) % len(AVATAR_ORDER)])

    def cycle_ship(self, direction):
        idx = SHIP_ORDER.index(self.ship_model)
        self.select_ship(SHIP_ORDER[(idx + direction) % len(SHIP_ORDER)])

    def switch_player(self):
        self.player_id = None
        self.username = ""
        self.input_text = ""
        ship, color = self.settings.get_loadout()
        self.ship_model = ship if ship in SHIPS else DEFAULT_SHIP
        self.selected_avatar_color = color if color in AVATAR_COLORS else "cyan"
        self.loadout_touched = False
        self.reset_game()
        self.change_state("name_entry")

    def spawn_particles(self, x, y, color, count):
        room = max(0, 320 - len(self.particles))
        for _ in range(min(count, room)):
            self.particles.append(Particle(x, y, color))

    def show_status(self, message, frames=150):
        self.status_message = message
        self.status_timer = frames

    def update_settings(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.toggle_rects["sound"].collidepoint(pos) or self.settings_rows["sound"].collidepoint(pos):
                    self.audio.toggle_sound()
                    self.audio.play("click")
                elif self.toggle_rects["music"].collidepoint(pos) or self.settings_rows["music"].collidepoint(pos):
                    self.audio.toggle_music()
                    self.audio.play("click")
                elif self.sound_minus.contains(pos):
                    self.audio.adjust_volume("sound", -0.1)
                    self.audio.play("click")
                elif self.sound_plus.contains(pos):
                    self.audio.adjust_volume("sound", 0.1)
                    self.audio.play("click")
                elif self.music_minus.contains(pos):
                    self.audio.adjust_volume("music", -0.1)
                elif self.music_plus.contains(pos):
                    self.audio.adjust_volume("music", 0.1)
                elif self.sound_bar.inflate(0, 16).collidepoint(pos):
                    self.audio.set_volume("sound", (pos[0] - self.sound_bar.x) / self.sound_bar.w)
                    self.audio.play("click")
                elif self.music_bar.inflate(0, 16).collidepoint(pos):
                    self.audio.set_volume("music", (pos[0] - self.music_bar.x) / self.music_bar.w)
                elif self.theme_prev.contains(pos):
                    self.cycle_theme(-1)
                elif self.theme_next.contains(pos) or self.settings_rows["theme"].collidepoint(pos):
                    self.cycle_theme(1)
                elif self.settings_rows["mobile_controls"].collidepoint(pos):
                    self.settings.toggle("mobile_controls")
                    self.audio.play("click")
                elif self.settings_rows["screen_shake"].collidepoint(pos):
                    self.settings.toggle("screen_shake")
                    self.audio.play("click")
                elif self.back_button.contains(pos):
                    self.audio.play("click")
                    self.change_state(self.settings_return_state)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.change_state(self.settings_return_state)

    def handle_text_entry(self, events, on_submit, allow_cancel=False):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    typed = self.input_text.strip()
                    self.input_text = ""
                    if typed:
                        on_submit(typed)
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE and allow_cancel:
                    self.input_text = ""
                    self.change_state("game_over")
                elif event.unicode.isprintable() and len(self.input_text) < 20:
                    self.input_text += event.unicode

    def draw(self):
        surface = self.game_surface
        self.background.draw(surface)

        state = self.game_state
        in_world = state in PLAY_STATES or (state == "settings" and self.settings_return_state == "paused")
        if in_world:
            self.draw_world(surface)
        else:
            self.draw_effects(surface)

        if state == "paused" or (state == "settings" and self.settings_return_state == "paused"):
            surface.blit(self.dim_overlay, (0, 0))
        if state == "paused":
            self.draw_pause_menu(surface)
        elif state == "name_entry":
            self.draw_title(surface)
        elif state == "game_over":
            self.draw_game_over(surface)
        elif state == "leaderboard":
            self.draw_leaderboard(surface)
        elif state == "profile":
            self.draw_profile(surface)
        elif state == "settings":
            self.draw_settings(surface)
        elif state == "hangar":
            self.draw_hangar(surface)

        if state in ("name_entry", "game_over", "leaderboard", "profile"):
            self.settings_button.draw(surface, pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0])

        self.draw_status(surface)

        if self.flash_alpha > 0:
            self.white.set_alpha(self.flash_alpha)
            surface.blit(self.white, (0, 0))
        if self.fade > 0:
            self.black.set_alpha(self.fade)
            surface.blit(self.black, (0, 0))

        shake_x = shake_y = 0
        if self.shake_timer > 0 and self.shake_intensity > 0 and self.settings.get("screen_shake"):
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity)

        self.screen.fill((0, 0, 0))
        self.screen.blit(surface, (shake_x, shake_y))

    def draw_effects(self, surface):
        for p in self.particles:
            p.draw(surface)
        for s in self.shockwaves:
            s.draw(surface)
        for t in self.floating_texts:
            t.draw(surface)

    def draw_world(self, surface):
        if self.active_powerup:
            self.active_powerup.draw(surface)
        for enemy in self.enemies:
            enemy.draw(surface)
        for eb in self.enemy_bullets:
            eb.draw(surface)
        for bullet in self.bullets:
            bullet.draw(surface)

        if self.settings.get("mobile_controls"):
            held = self.buttons.held() if self.game_state == "playing" else set()
            self.buttons.draw(surface, held)

        self.player.draw(surface)
        if self.player.visible and (self.shield_active or self.invuln_timer > 0):
            self.draw_shield(surface)

        self.draw_effects(surface)

        if self.freeze_timer > 0:
            alpha = 255 if self.freeze_timer > 60 else int(255 * self.freeze_timer / 60)
            self.freeze_overlay.set_alpha(alpha)
            surface.blit(self.freeze_overlay, (0, 0))

        self.draw_hud(surface)
        self.draw_level_banner(surface)

    def draw_shield(self, surface):
        px, py = self.player.center()
        if self.shield_active:
            pulse = 0.82 + 0.18 * math.sin(self.tick * 0.15)
            self.shield_bubble.set_alpha(int(255 * pulse))
        else:
            self.shield_bubble.set_alpha(int(255 * (self.invuln_timer / 60)) if self.invuln_timer % 6 < 4 else 0)
        surface.blit(self.shield_bubble, (int(px - 75), int(py - 75)))

    def draw_hud(self, surface):
        surface.blit(self.hud_bar, (0, 0))
        self.display_score += max(1, int((self.score - self.display_score) * 0.18)) if self.display_score < self.score else 0
        self.display_score = min(self.display_score, self.score)

        draw_text(surface, "SCORE", "ui", 16, DIM, (22, 6), "topleft", shadow=False)
        draw_text(surface, f"{self.display_score}", "ui", 38, WHITE, (22, 18), "topleft")

        boss_level = self.level % 5 == 0
        draw_text(surface, "LEVEL", "ui", 16, DIM, (250, 6), "topleft", shadow=False)
        draw_text(surface, f"{self.level}", "ui", 38, RED if boss_level else theme.accent, (250, 18), "topleft")

        self.draw_avatar(surface, self.username, (358, 32), 40, ship_fallback=True)
        draw_text(surface, "PILOT", "ui", 16, DIM, (386, 6), "topleft", shadow=False)
        name = self.username if self.username else "GUEST"
        draw_text(surface, name[:10].upper(), "ui", 26, WHITE, (386, 22), "topleft")

        draw_text(surface, "LIVES", "ui", 16, DIM, (520, 6), "topleft", shadow=False)
        slots = max(3, self.lives)
        for i in range(slots):
            icon = self.life_icon if i < self.lives else self.life_icon_dim
            surface.blit(icon, (520 + i * 33, 24))

        self.draw_pause_button(surface)
        self.draw_status_chips(surface)
        self.draw_combo(surface)
        self.draw_boss_bar(surface)

    def draw_pause_button(self, surface):
        rect = self.pause_rect
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        draw_panel(surface, rect, (10, 16, 42, 220), theme.accent if hovered else DIM, radius=10, glow=hovered)
        cx, cy = rect.center
        if self.game_state == "paused":
            pygame.draw.polygon(surface, WHITE, [(cx - 5, cy - 9), (cx - 5, cy + 9), (cx + 8, cy)])
        else:
            pygame.draw.rect(surface, WHITE, (cx - 8, cy - 9, 5, 18), border_radius=1)
            pygame.draw.rect(surface, WHITE, (cx + 3, cy - 9, 5, 18), border_radius=1)

    def draw_status_chips(self, surface):
        chips = []
        if self.shield_active:
            chips.append(("shield", 1.0))
        if self.rapid_fire_timer > 0:
            chips.append(("rapid", self.rapid_fire_timer / 600))
        if self.scatter_timer > 0:
            chips.append(("scatter", self.scatter_timer / 900))
        if self.freeze_timer > 0:
            chips.append(("freeze", self.freeze_timer / 300))
        for i, (kind, fraction) in enumerate(chips):
            y = 76 + i * 32
            color = POWERUP_TYPES[kind]["color"]
            draw_panel(surface, (16, y, 168, 28), (6, 10, 30, 190), color, radius=10, glow=False)
            icon = load_sprite("assets/images/powerup_%s.png" % kind, (24, 24))
            surface.blit(icon, (20, y + 2))
            draw_bar(surface, (50, y + 10, 124, 8), fraction, color)

    def draw_combo(self, surface):
        if self.combo < 2:
            return
        multiplier = min(5, 1 + self.combo // 5)
        draw_text(surface, f"{self.combo} COMBO", "ui", 26, GOLD, (782, 74), "topright")
        draw_text(surface, f"x{multiplier}", "ui", 40, ORANGE if multiplier > 1 else WHITE, (782, 96), "topright")
        if multiplier < 5:
            draw_bar(surface, (682, 136, 100, 6), (self.combo % 5) / 5, GOLD)

    def draw_boss_bar(self, surface):
        bosses = [e for e in self.enemies if e.kind == "boss" and e.state != "dead"]
        if not bosses:
            return
        boss = bosses[0]
        draw_text(surface, "MOTHERSHIP", "ui", 18, (255, 170, 170), (400, 78), "center")
        draw_bar(surface, (240, 90, 320, 14), boss.hp / boss.max_hp, (255, 70, 90), back=(40, 10, 24))

    def draw_level_banner(self, surface):
        t = self.level_transition_timer
        if t <= 0:
            return
        alpha = int(max(0, min(255, (75 - t) * 22, t * 10)))
        boss = self.level % 5 == 0
        draw_glow_text(surface, self.level_banner, "title", 52, WHITE, RED if boss else theme.accent, (400, 200), alpha=alpha)
        sub = "WARNING - MOTHERSHIP INCOMING" if boss else "GET READY"
        draw_text(surface, sub, "ui", 28, RED if boss else GOLD, (400, 246), "center", alpha=alpha)

    def status_y(self):
        if self.game_state in PLAY_STATES:
            return 340
        if self.game_state == "name_entry":
            return 426
        if self.game_state == "game_over":
            return 540
        return 564

    def draw_status(self, surface):
        if self.status_timer > 0 and self.status_message:
            alpha = 255 if self.status_timer > 15 else int(255 * self.status_timer / 15)
            text = render_text(self.status_message, "ui", 26, GOLD)
            w = text.get_width() + 44
            rect = pygame.Rect(self.screen_width // 2 - w // 2, self.status_y(), w, 36)
            if alpha < 255:
                shell = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                draw_panel(shell, rect, (6, 10, 30, 205), GOLD, radius=12, glow=False)
                draw_text(shell, self.status_message, "ui", 26, GOLD, rect.center)
                shell.set_alpha(alpha)
                surface.blit(shell, (0, 0))
            else:
                draw_panel(surface, rect, (6, 10, 30, 205), GOLD, radius=12, glow=False)
                draw_text(surface, self.status_message, "ui", 26, GOLD, rect.center)

    def draw_pause_menu(self, surface):
        draw_panel(surface, (225, 130, 350, 340), (6, 10, 30, 215), theme.accent, radius=18)
        draw_glow_text(surface, "PAUSED", "title", 44, WHITE, theme.accent, (400, 184))
        mouse, down = pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]
        self.resume_button.draw(surface, mouse, down)
        self.pause_settings_button.draw(surface, mouse, down)
        self.end_run_button.draw(surface, mouse, down)
        draw_text(surface, "P / ESC to resume", "ui", 20, DIM, (400, 450), shadow=False)

    def draw_title(self, surface):
        surface.blit(self.dim_overlay, (0, 0))
        bob = math.sin(self.tick * 0.05) * 4
        self.draw_db_status(surface)
        tint = AVATAR_COLORS[self.selected_avatar_color]

        draw_glow_text(surface, "SPACE INVADERS", "title", 56, WHITE, theme.accent, (400, 74 + bob * 0.5),
                       gradient=theme.gradient)
        draw_glow_text(surface, " ".join("NOVA ASSAULT").replace("   ", "    "), "title", 22, theme.accent2, theme.accent2, (400, 124))
        for x0, x1 in ((90, 232), (568, 710)):
            for i in range(x1 - x0):
                edge = abs((i / (x1 - x0)) - (0 if x0 < 400 else 1))
                surface.set_at((x0 + i, 124), mix(INK, theme.accent2, 0.85 - 0.7 * edge))
                surface.set_at((x0 + i, 125), mix(INK, theme.accent2, 0.55 - 0.45 * edge))

        hero_y = 146 + bob
        for kind, cx, size, phase, lift in (("tank", 126, 78, 0.8, 34), ("normal", 236, 72, 0.0, 26),
                                            ("fast", 564, 70, 1.6, 26)):
            sprite = load_sprite("assets/images/enemy_%s.png" % kind, (size, size))
            ey = hero_y + lift + math.sin(self.tick * 0.06 + phase) * 6
            draw_glow(surface, (cx, ey + size / 2), 62, ENEMY_COLORS[kind], 0.5)
            surface.blit(sprite, (cx - size // 2, int(ey)))
        boss = load_sprite("assets/images/enemy_boss.png", (112, 75))
        by = hero_y + 42 + math.sin(self.tick * 0.04 + 2.4) * 5
        draw_glow(surface, (674, by + 38), 70, ENEMY_COLORS["boss"], 0.4)
        surface.blit(boss, (618, int(by)))
        ship = compose_ship(112, tint, self.ship_model)
        hover = self.hero_rect.collidepoint(pygame.mouse.get_pos())
        draw_glow(surface, (400, hero_y + 56), 96 if hover else 84, tint, 0.7 if hover else 0.45)
        draw_engine_flames(surface, 344, hero_y, 112, tint, self.tick, 1.2, self.ship_model)
        surface.blit(ship, (344, int(hero_y)))

        draw_text(surface, "PILOT CALLSIGN", "ui", 18, DIM, (400, 290), shadow=False)
        box = pygame.Rect(230, 302, 340, 54)
        draw_panel(surface, box, (6, 10, 30, 225), theme.accent, radius=12)
        if self.input_text:
            rect = draw_text(surface, self.input_text, "ui", 34, WHITE, (box.x + 18, box.centery), "midleft")
            caret_x = rect.right + 4
        else:
            draw_text(surface, "TYPE YOUR NAME", "ui", 30, (90, 104, 148), (box.x + 18, box.centery), "midleft", shadow=False)
            caret_x = box.x + 18
        if (self.tick // 30) % 2 == 0:
            pygame.draw.rect(surface, theme.accent, (caret_x, box.centery - 15, 3, 30))
        draw_text(surface, f"{len(self.input_text)}/20", "ui", 16, DIM, (box.right - 12, box.bottom - 10), "bottomright", shadow=False)
        if self.input_text and self.avatars.filename_for(self.input_text):
            self.draw_avatar(surface, self.input_text, (196, box.centery), 46)

        self.hangar_button.draw(surface, pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0])
        self.launch_button.draw(surface, pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0])

        draw_panel(surface, (40, 432, 720, 136), (6, 10, 30, 210), VIOLET, radius=16)
        draw_text(surface, "CONTROLS", "ui", 20, GOLD, (64, 444), "topleft", shadow=False)
        rows = (("MOVE", "LEFT / RIGHT  or  A / D"), ("FIRE", "SPACE"), ("PAUSE", "P  or  ESC"), ("FULLSCREEN", "F11"))
        for i, (label, value) in enumerate(rows):
            y = 474 + i * 21
            draw_text(surface, label, "ui", 18, DIM, (64, y), "topleft", shadow=False)
            draw_text(surface, value, "ui", 18, WHITE, (170, y), "topleft", shadow=False)
        draw_text(surface, "POWER-UPS", "ui", 20, GOLD, (372, 444), "topleft", shadow=False)
        for i, kind in enumerate(("rapid", "shield", "bomb", "freeze", "life", "scatter")):
            col, row = i % 3, i // 3
            x = 372 + col * 126
            y = 470 + row * 46
            icon = load_sprite("assets/images/powerup_%s.png" % kind, (34, 34))
            surface.blit(icon, (x, y))
            color = POWERUP_TYPES[kind]["color"]
            draw_text(surface, LEGEND_NAME[kind], "ui", 17, color, (x + 42, y + 1), "topleft", shadow=False)
            draw_text(surface, LEGEND_SHORT[kind], "ui", 13, DIM, (x + 42, y + 19), "topleft", shadow=False)
        draw_text(surface, "Space Invaders: Nova Assault  -  by Cordero, Ismail A.", "ui", 15, (90, 104, 148), (400, 587),
                  shadow=False)

    def draw_db_status(self, surface):
        online = self.db.is_connected
        color = GREEN if online else ORANGE
        label = "DATABASE ONLINE" if online else "OFFLINE MODE - SCORES NOT SAVED"
        text = render_text(label, "ui", 17, color)
        rect = pygame.Rect(16, 14, text.get_width() + 40, 30)
        draw_panel(surface, rect, (6, 10, 30, 200), color, radius=14, glow=False)
        pygame.draw.circle(surface, color, (rect.x + 16, rect.centery), 5)
        surface.blit(text, (rect.x + 28, rect.centery - text.get_height() // 2))

    def draw_game_over(self, surface):
        surface.blit(self.dim_overlay, (0, 0))
        draw_glow_text(surface, "GAME OVER", "title", 56, (255, 200, 210), RED, (400, 66),
                       gradient=((255, 220, 225), (255, 60, 90)))
        cards = (("SCORE", f"{self.score}", WHITE), ("LEVEL REACHED", f"{self.level}", theme.accent),
                 ("BEST COMBO", f"{self.best_combo}", GOLD))
        for i, (label, value, color) in enumerate(cards):
            rect = pygame.Rect(70 + i * 230, 128, 210, 88)
            draw_panel(surface, rect, (6, 10, 30, 215), color, radius=14)
            draw_text(surface, label, "ui", 18, DIM, (rect.centerx, rect.y + 20), shadow=False)
            draw_text(surface, value, "ui", 46, color, (rect.centerx, rect.y + 56))

        if self.is_new_high_score:
            pulse = 170 + int(85 * abs(math.sin(self.tick * 0.07)))
            draw_glow_text(surface, "NEW HIGH SCORE!", "title", 30, GOLD, ORANGE, (400, 252), alpha=pulse)
        elif self.player_id is None:
            draw_text(surface, "OFFLINE - THIS RUN WAS NOT SAVED", "ui", 24, ORANGE, (400, 252))
        else:
            message = f"NICE FLYING, {self.username.upper()}"
            text_w = render_text(message, "ui", 26, DIM).get_width()
            start = 400 - (text_w + 46) // 2
            self.draw_avatar(surface, self.username, (start + 18, 252), 36, ship_fallback=True)
            draw_text(surface, message, "ui", 26, DIM, (start + 46, 252), "midleft")

        mouse, down = pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]
        for button in (self.reload_button, self.leaderboard_button, self.profile_button, self.switch_player_button):
            button.draw(surface, mouse, down)
        draw_text(surface, "ENTER  -  play again", "ui", 20, DIM, (400, 500), shadow=False)

    def draw_leaderboard(self, surface):
        surface.blit(self.dim_overlay, (0, 0))
        draw_glow_text(surface, "LEADERBOARD", "title", 44, WHITE, theme.accent, (400, 48), gradient=theme.gradient)
        panel = pygame.Rect(100, 92, 600, 408)
        draw_panel(surface, panel, (6, 10, 30, 220), theme.accent, radius=16)
        draw_text(surface, "#", "ui", 18, DIM, (134, 116), shadow=False)
        draw_text(surface, "PILOT", "ui", 18, DIM, (210, 116), "midleft", shadow=False)
        draw_text(surface, "LEVEL", "ui", 18, DIM, (520, 116), "midright", shadow=False)
        draw_text(surface, "SCORE", "ui", 18, DIM, (668, 116), "midright", shadow=False)
        pygame.draw.line(surface, (*theme.accent, 90), (118, 134), (682, 134), 1)

        if not self.leaderboard_cache:
            message = "NO SCORES YET" if self.db.is_connected else "DATABASE OFFLINE - NO SCORES TO SHOW"
            draw_text(surface, message, "ui", 30, DIM, (400, 300))
        else:
            medals = (GOLD, (200, 210, 225), (220, 140, 80))
            for i, row in enumerate(self.leaderboard_cache[:10]):
                y = 154 + i * 34
                mine = self.username and row["username"].lower() == self.username.lower()
                if mine:
                    draw_panel(surface, (112, y - 15, 576, 32), (0, 80, 110, 120), theme.accent, radius=8, glow=False)
                badge = medals[i] if i < 3 else None
                if badge:
                    pygame.draw.circle(surface, badge, (134, y), 13)
                    draw_text(surface, str(i + 1), "ui", 22, (20, 20, 30), (134, y), shadow=False)
                else:
                    draw_text(surface, str(i + 1), "ui", 22, DIM, (134, y), shadow=False)
                self.draw_avatar(surface, row["username"], (188, y), 26, theme.accent if mine else DIM)
                draw_text(surface, str(row["username"])[:18], "ui", 26, WHITE if not mine else theme.accent, (210, y), "midleft")
                draw_text(surface, f"LV {row['level']}", "ui", 22, DIM, (520, y), "midright", shadow=False)
                draw_text(surface, f"{row['high_score']}", "ui", 28, GOLD if i == 0 else WHITE, (668, y), "midright")
        self.back_button.draw(surface, pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0])

    def draw_profile(self, surface):
        surface.blit(self.dim_overlay, (0, 0))
        draw_glow_text(surface, "PILOT PROFILE", "title", 44, WHITE, theme.accent, (400, 48), gradient=theme.gradient)
        tint = AVATAR_COLORS[self.selected_avatar_color]
        mouse, down = pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]
        info = ship_info(self.ship_model)

        draw_panel(surface, (50, 88, 320, 336), (6, 10, 30, 220), tint, radius=16)
        self.draw_avatar(surface, self.username, (210, 158), 128, tint, ship_fallback=True, glow=True)
        current = self.avatars.filename_for(self.username)
        self.picture_add_button.label = "CHANGE PICTURE" if current else "ADD PICTURE"
        self.picture_add_button.draw(surface, mouse, down)
        if current:
            self.picture_remove_button.draw(surface, mouse, down)
        draw_text(surface, "or drag an image onto the window", "ui", 15, DIM, (210, 288), shadow=False)
        library = self.avatars.library()
        per_page = len(self.gallery_rects)
        self.gallery_page = max(0, min(self.gallery_page, max(0, (len(library) - 1) // per_page)))
        draw_text(surface, "YOUR PICTURES", "ui", 15, DIM, (66, 306), "topleft", shadow=False)
        if len(library) > per_page:
            self.gallery_prev.draw(surface, mouse, down)
            self.gallery_next.draw(surface, mouse, down)
        for idx, rect in enumerate(self.gallery_rects):
            item = self.gallery_page * per_page + idx
            if item < len(library):
                filename = library[item]
                selected = filename == current
                border = tint if selected else (WHITE if rect.collidepoint(mouse) else DIM)
                draw_panel(surface, rect, (10, 16, 44, 235) if selected else (6, 10, 30, 200), border, radius=24,
                           glow=selected)
                thumb = self.avatars.circle_from_file(filename, 42)
                if thumb:
                    surface.blit(thumb, thumb.get_rect(center=rect.center))
            else:
                pygame.draw.circle(surface, (30, 38, 72), rect.center, 22, 1)
        draw_text(surface, "click a picture to use it" if library else "no pictures added yet", "ui", 15, DIM,
                  (210, 396), shadow=False)

        draw_panel(surface, (390, 88, 360, 336), (6, 10, 30, 220), theme.accent, radius=16)
        draw_text(surface, "PILOT", "ui", 18, DIM, (414, 104), "topleft", shadow=False)
        draw_text(surface, (self.username or "GUEST")[:14].upper(), "ui", 38, WHITE, (414, 122), "topleft")
        stats = self.profile_stats
        if stats:
            avg_score = float(stats.get("avg_score") or 0)
            rows = (("GAMES PLAYED", f"{stats.get('games_played', 0)}"),
                    ("PERSONAL BEST", f"{stats.get('high_score', 0)}"),
                    ("AVERAGE SCORE", f"{avg_score:.0f}"),
                    ("BEST COMBO (LAST RUN)", f"{self.best_combo}"))
            for i, (label, value) in enumerate(rows):
                y = 190 + i * 40
                pygame.draw.line(surface, (*theme.accent, 60), (410, y - 20), (730, y - 20), 1)
                draw_text(surface, label, "ui", 20, DIM, (414, y), "midleft", shadow=False)
                draw_text(surface, value, "ui", 30, GOLD if i == 1 else WHITE, (730, y), "midright")
        else:
            draw_text(surface, "OFFLINE - NO SAVED STATS", "ui", 24, ORANGE, (570, 260))
        draw_text(surface, f"SHIP: {info['name']}  -  {AVATAR_LABELS[self.selected_avatar_color]}", "ui", 20, tint, (570, 352))
        self.profile_hangar_button.draw(surface, mouse, down)

        box = pygame.Rect(150, 440, 500, 50)
        draw_panel(surface, box, (6, 10, 30, 225), GOLD, radius=12)
        if self.input_text:
            rect = draw_text(surface, self.input_text, "ui", 30, WHITE, (box.x + 18, box.centery), "midleft")
            caret_x = rect.right + 4
        else:
            hint = "TYPE A NEW NAME + ENTER TO RENAME" if self.player_id is not None else "RENAMING NEEDS THE DATABASE"
            draw_text(surface, hint, "ui", 22, (100, 114, 158), (box.x + 18, box.centery), "midleft", shadow=False)
            caret_x = box.right - 18
        if (self.tick // 30) % 2 == 0 and self.input_text:
            pygame.draw.rect(surface, GOLD, (caret_x, box.centery - 14, 3, 28))
        self.back_button.draw(surface, mouse, down)

    def draw_hangar(self, surface):
        surface.blit(self.dim_overlay, (0, 0))
        draw_glow_text(surface, "HANGAR", "title", 44, WHITE, theme.accent, (400, 46), gradient=theme.gradient)
        tint = AVATAR_COLORS[self.selected_avatar_color]
        info = ship_info(self.ship_model)
        mouse, down = pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]

        draw_panel(surface, (40, 88, 360, 332), (6, 10, 30, 220), tint, radius=16)
        bob = math.sin(self.tick * 0.05) * 4
        draw_glow(surface, (220, 208 + bob), 124, tint, 0.55)
        ship_y = 100 + bob
        draw_engine_flames(surface, 120, ship_y, 200, tint, self.tick, 1.2, self.ship_model)
        surface.blit(compose_ship(200, tint, self.ship_model), (120, int(ship_y)))
        self.hangar_prev.draw(surface, mouse, down)
        self.hangar_next.draw(surface, mouse, down)
        for name, rect in zip(AVATAR_ORDER, self.swatch_rects):
            color = AVATAR_COLORS[name]
            selected = name == self.selected_avatar_color
            pygame.draw.rect(surface, mix(INK, color, 0.85), rect.inflate(-6, -6), border_radius=9)
            pygame.draw.rect(surface, WHITE if selected else mix(color, INK, 0.5), rect, 3 if selected else 2, border_radius=11)
            if rect.collidepoint(mouse) and not selected:
                pygame.draw.rect(surface, color, rect.inflate(6, 6), 1, border_radius=13)
        draw_text(surface, f"HULL ACCENT: {AVATAR_LABELS[self.selected_avatar_color]}", "ui", 20, tint, (220, 404))

        draw_panel(surface, (420, 88, 340, 332), (6, 10, 30, 220), theme.accent, radius=16)
        draw_text(surface, info["name"], "title", 34, WHITE, (444, 104), "topleft")
        draw_text(surface, info["role"], "ui", 22, tint, (444, 148), "topleft")
        for i, (label, rating) in enumerate(zip(("SPEED", "FIRE RATE", "DEFENSE"), info["rating"])):
            y = 186 + i * 34
            draw_text(surface, label, "ui", 20, DIM, (444, y + 8), "midleft", shadow=False)
            for k in range(5):
                seg = pygame.Rect(566 + k * 36, y, 31, 16)
                pygame.draw.rect(surface, tint if k < rating else (22, 28, 58), seg, border_radius=5)
                if k < rating:
                    pygame.draw.rect(surface, mix(tint, WHITE, 0.45), (seg.x + 2, seg.y + 2, seg.w - 4, 4), border_radius=2)
        draw_text(surface, info["perk"], "ui", 19, WHITE, (444, 300), "topleft", shadow=False)
        for model, rect in zip(SHIP_ORDER, self.hangar_thumbs):
            selected = model == self.ship_model
            hovered = rect.collidepoint(mouse)
            border = tint if selected else (WHITE if hovered else DIM)
            draw_panel(surface, rect, (10, 16, 44, 235) if selected else (6, 10, 30, 200), border, radius=10, glow=selected)
            surface.blit(compose_ship(50, tint if selected else mix(tint, (90, 100, 140), 0.55), model),
                         (rect.x + 6, rect.y + 6))
        self.hangar_done.draw(surface, mouse, down)
        draw_text(surface, "LEFT / RIGHT  ships      UP / DOWN  colors      ENTER  done", "ui", 17, DIM, (400, 484),
                  shadow=False)

    def draw_settings(self, surface):
        if self.settings_return_state != "paused":
            surface.blit(self.dim_overlay, (0, 0))
        draw_glow_text(surface, "SETTINGS", "title", 44, WHITE, theme.accent, (400, 48), gradient=theme.gradient)
        draw_panel(surface, (110, 92, 580, 412), (6, 10, 30, 228), theme.accent, radius=16)
        mouse, down = pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]
        labels = {
            "sound": "SOUND EFFECTS", "music": "MUSIC", "sound_volume": "EFFECTS VOLUME",
            "music_volume": "MUSIC VOLUME", "mobile_controls": "MOVE & FIRE BUTTONS", "screen_shake": "SCREEN SHAKE",
            "theme": "GAME THEME",
        }
        for i, (name, row) in enumerate(self.settings_rows.items()):
            if row.collidepoint(mouse) and name not in ("sound_volume", "music_volume"):
                draw_panel(surface, row.inflate(-8, 0), (0, 70, 100, 70), theme.accent, radius=10, glow=False)
            draw_text(surface, labels[name], "ui", 26, WHITE, (row.x + 20, row.centery), "midleft")
            if i < len(self.settings_rows) - 1:
                pygame.draw.line(surface, (*theme.accent, 40), (row.x + 10, row.bottom + 6), (row.right - 10, row.bottom + 6), 1)

        draw_toggle(surface, self.toggle_rects["sound"], self.audio.config["sound_enabled"])
        draw_toggle(surface, self.toggle_rects["music"], self.audio.config["music_enabled"])
        draw_toggle(surface, self.toggle_rects["mobile_controls"], self.settings.get("mobile_controls"))
        draw_toggle(surface, self.toggle_rects["screen_shake"], self.settings.get("screen_shake"))
        states = {
            "sound": (self.audio.config["sound_enabled"], "ON", "OFF"),
            "music": (self.audio.config["music_enabled"], "ON", "OFF"),
            "mobile_controls": (self.settings.get("mobile_controls"), "SHOWN", "HIDDEN"),
            "screen_shake": (self.settings.get("screen_shake"), "ON", "OFF"),
        }
        for name, (on, on_text, off_text) in states.items():
            rect = self.toggle_rects[name]
            draw_text(surface, on_text if on else off_text, "ui", 20, GREEN if on else DIM,
                      (rect.x - 14, rect.centery), "midright", shadow=False)

        for minus, plus, bar, key, name in ((self.sound_minus, self.sound_plus, self.sound_bar, "sound_volume", "sound_volume"),
                                            (self.music_minus, self.music_plus, self.music_bar, "music_volume", "music_volume")):
            minus.draw(surface, mouse, down)
            plus.draw(surface, mouse, down)
            value = self.audio.config[key]
            draw_bar(surface, bar, value, theme.accent)
            draw_text(surface, f"{int(round(value * 100))}%", "ui", 20, theme.accent,
                      (self.settings_rows[name].x + 250, self.settings_rows[name].centery), "midleft", shadow=False)
        self.theme_prev.draw(surface, mouse, down)
        self.theme_next.draw(surface, mouse, down)
        theme_row = self.settings_rows["theme"]
        draw_text(surface, theme.name, "ui", 24, theme.accent, (554, theme_row.centery - 6))
        for i, key in enumerate(THEME_ORDER):
            dot_x = 554 + (i - (len(THEME_ORDER) - 1) / 2) * 15
            pygame.draw.circle(surface, THEMES[key]["accent"], (int(dot_x), theme_row.centery + 13),
                               5 if key == theme.key else 3)
        self.back_button.draw(surface, mouse, down)
