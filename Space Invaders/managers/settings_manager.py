import json
import os

DEFAULTS = {"mobile_controls": True, "screen_shake": True}
SECTIONS = {"mobile_controls": "controls", "screen_shake": "display"}
DEFAULT_LOADOUT = {"ship": "falcon", "color": "cyan"}


class SettingsManager:
    def __init__(self, settings_path="settings.json"):
        self.settings_path = settings_path
        self.values = dict(DEFAULTS)
        self.loadout = dict(DEFAULT_LOADOUT)
        self.theme = "nova"
        self.pictures = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                for key, section in SECTIONS.items():
                    value = settings.get(section, {}).get(key)
                    if isinstance(value, bool):
                        self.values[key] = value
                for key in DEFAULT_LOADOUT:
                    value = settings.get("loadout", {}).get(key)
                    if isinstance(value, str):
                        self.loadout[key] = value
                theme = settings.get("display", {}).get("theme")
                if isinstance(theme, str):
                    self.theme = theme
                pictures = settings.get("profile_pictures", {})
                if isinstance(pictures, dict):
                    self.pictures = {str(k): str(v) for k, v in pictures.items() if isinstance(v, str)}
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Settings] Could not read {self.settings_path}, using defaults. ({e})")

    def get(self, key):
        return self.values.get(key, DEFAULTS.get(key, False))

    def get_loadout(self):
        return self.loadout["ship"], self.loadout["color"]

    def set_loadout(self, ship, color):
        self.loadout = {"ship": ship, "color": color}
        self._persist()

    def get_theme(self):
        return self.theme

    def set_theme(self, key):
        self.theme = key
        self._persist()

    def get_picture(self, user_key):
        return self.pictures.get(user_key)

    def set_picture(self, user_key, filename):
        if filename:
            self.pictures[user_key] = filename
        else:
            self.pictures.pop(user_key, None)
        self._persist()

    def rename_picture_owner(self, old_key, new_key):
        if old_key in self.pictures and old_key != new_key:
            self.pictures[new_key] = self.pictures.pop(old_key)
            self._persist()

    def toggle(self, key):
        self.values[key] = not self.get(key)
        self._persist()
        return self.values[key]

    def _persist(self):
        try:
            full_settings = {}
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    full_settings = json.load(f)
            for key, section in SECTIONS.items():
                full_settings.setdefault(section, {})[key] = self.values[key]
            full_settings.setdefault("display", {})["theme"] = self.theme
            full_settings["loadout"] = dict(self.loadout)
            full_settings["profile_pictures"] = dict(self.pictures)
            with open(self.settings_path, "w") as f:
                json.dump(full_settings, f, indent=4)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[Settings] Could not save settings: {e}")
