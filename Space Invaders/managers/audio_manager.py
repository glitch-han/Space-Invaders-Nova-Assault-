import json
import os
import pygame

SOUND_FILES = {
    "shoot": "assets/sounds/shoot.wav",
    "enemy_shoot": "assets/sounds/enemy_shoot.wav",
    "hit": "assets/sounds/hit.wav",
    "explosion": "assets/sounds/explosion.wav",
    "bomb": "assets/sounds/bomb.wav",
    "powerup": "assets/sounds/powerup.wav",
    "shield": "assets/sounds/shield.wav",
    "levelup": "assets/sounds/levelup.wav",
    "gameover": "assets/sounds/gameover.wav",
    "highscore": "assets/sounds/highscore.wav",
    "warning": "assets/sounds/warning.wav",
    "click": "assets/sounds/click.wav",
    "scatter": "assets/sounds/scatter.wav",
}

SOUND_GAIN = {"shoot": 0.75, "enemy_shoot": 0.7, "click": 0.7, "hit": 0.85}

TRACK_FILES = {
    "theme": "assets/music/theme.wav",
    "menu": "assets/music/menu.wav",
    "boss": "assets/music/boss.wav",
}


class AudioManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, settings_path="settings.json"):
        if self._initialized:
            return
        self._initialized = True

        self.settings_path = settings_path
        self.config = self._load_config()
        self.current_track = None
        self.desired_track = "menu"
        self.available = pygame.mixer.get_init() is not None

        self.sounds = {}
        if self.available:
            self._load_sounds()
        else:
            print("[Audio] No audio device found - running without sound.")

    def _load_config(self):
        default_config = {
            "sound_volume": 0.8,
            "music_volume": 0.6,
            "sound_enabled": True,
            "music_enabled": True,
        }
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                    default_config.update(settings.get("audio", {}))
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Audio] Could not read {self.settings_path}, using defaults. ({e})")
        return default_config

    def _load_sounds(self):
        for name, path in SOUND_FILES.items():
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self.config["sound_volume"] * SOUND_GAIN.get(name, 1.0))
                self.sounds[name] = sound
            except (pygame.error, FileNotFoundError) as e:
                print(f"[Audio] Could not load {path}: {e}")

    def play(self, name):
        if not self.available or not self.config.get("sound_enabled", True):
            return
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def play_track(self, name):
        self.desired_track = name
        if not self.available or not self.config.get("music_enabled", True):
            return
        if self.current_track == name and pygame.mixer.music.get_busy():
            return
        path = TRACK_FILES.get(name)
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.config["music_volume"])
            pygame.mixer.music.play(-1)
            self.current_track = name
        except (pygame.error, FileNotFoundError, TypeError) as e:
            print(f"[Audio] Could not load music {path}: {e}")

    def start_music(self):
        self.play_track(self.desired_track)

    def stop_music(self):
        if self.available:
            pygame.mixer.music.stop()
        self.current_track = None

    def toggle_sound(self):
        self.config["sound_enabled"] = not self.config.get("sound_enabled", True)
        self._persist()

    def toggle_music(self):
        self.config["music_enabled"] = not self.config.get("music_enabled", True)
        if self.config["music_enabled"]:
            self.start_music()
        else:
            self.stop_music()
        self._persist()

    def set_volume(self, kind, value):
        key = "sound_volume" if kind == "sound" else "music_volume"
        value = round(min(1.0, max(0.0, value)), 1)
        self.config[key] = value
        if kind == "sound":
            for name, sound in self.sounds.items():
                sound.set_volume(value * SOUND_GAIN.get(name, 1.0))
        elif self.available:
            pygame.mixer.music.set_volume(value)
        self._persist()

    def adjust_volume(self, kind, delta):
        key = "sound_volume" if kind == "sound" else "music_volume"
        self.set_volume(kind, self.config[key] + delta)

    def _persist(self):
        try:
            full_settings = {}
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    full_settings = json.load(f)
            full_settings["audio"] = self.config
            with open(self.settings_path, "w") as f:
                json.dump(full_settings, f, indent=4)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[Audio] Could not save settings: {e}")
