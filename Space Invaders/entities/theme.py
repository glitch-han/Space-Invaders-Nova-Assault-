THEME_ORDER = ["nova", "inferno", "emerald", "frost", "synthwave"]

THEMES = {
    "nova": {
        "name": "NOVA",
        "accent": (0, 229, 255),
        "accent2": (255, 64, 200),
        "gradient": ((225, 252, 255), (0, 190, 255)),
        "nebula": "assets/images/bg_nebula.png",
        "planet": "assets/images/planet.png",
        "stars": ((200, 220, 255), (255, 244, 220), (190, 190, 255), (220, 255, 250)),
        "dim": (2, 4, 16, 150),
    },
    "inferno": {
        "name": "INFERNO",
        "accent": (255, 140, 50),
        "accent2": (255, 70, 90),
        "gradient": ((255, 240, 210), (255, 110, 30)),
        "nebula": "assets/images/bg_inferno.png",
        "planet": "assets/images/planet_inferno.png",
        "stars": ((255, 220, 190), (255, 240, 210), (255, 190, 160), (255, 230, 200)),
        "dim": (14, 3, 4, 150),
    },
    "emerald": {
        "name": "EMERALD",
        "accent": (70, 255, 160),
        "accent2": (250, 220, 80),
        "gradient": ((225, 255, 235), (30, 200, 110)),
        "nebula": "assets/images/bg_emerald.png",
        "planet": "assets/images/planet_emerald.png",
        "stars": ((200, 255, 220), (230, 255, 240), (190, 240, 255), (240, 255, 200)),
        "dim": (2, 12, 8, 150),
    },
    "frost": {
        "name": "FROST",
        "accent": (150, 205, 255),
        "accent2": (190, 150, 255),
        "gradient": ((245, 250, 255), (110, 170, 255)),
        "nebula": "assets/images/bg_frost.png",
        "planet": "assets/images/planet_frost.png",
        "stars": ((220, 235, 255), (255, 255, 255), (200, 220, 255), (230, 245, 255)),
        "dim": (3, 8, 20, 150),
    },
    "synthwave": {
        "name": "SYNTHWAVE",
        "accent": (255, 90, 200),
        "accent2": (255, 210, 70),
        "gradient": ((255, 230, 250), (255, 60, 180)),
        "nebula": "assets/images/bg_synthwave.png",
        "planet": "assets/images/planet_synthwave.png",
        "stars": ((255, 200, 240), (255, 230, 200), (220, 190, 255), (255, 210, 230)),
        "dim": (14, 3, 18, 150),
    },
}


class ThemeState:
    def __init__(self):
        self.key = "nova"
        self.apply("nova")

    def apply(self, key):
        if key not in THEMES:
            key = "nova"
        spec = THEMES[key]
        self.key = key
        self.name = spec["name"]
        self.accent = spec["accent"]
        self.accent2 = spec["accent2"]
        self.gradient = spec["gradient"]
        self.nebula_file = spec["nebula"]
        self.planet_file = spec["planet"]
        self.stars = spec["stars"]
        self.dim = spec["dim"]

    def neighbor(self, direction):
        idx = THEME_ORDER.index(self.key)
        return THEME_ORDER[(idx + direction) % len(THEME_ORDER)]


theme = ThemeState()
