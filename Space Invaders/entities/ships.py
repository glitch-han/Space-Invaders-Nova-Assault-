SHIP_ORDER = ["falcon", "viper", "titan", "aegis"]
DEFAULT_SHIP = "falcon"

SHIPS = {
    "falcon": {
        "name": "FALCON",
        "role": "ALL-ROUNDER",
        "file": "ship1",
        "speed": 5.0,
        "bolt_speed": 7,
        "hit_scale": 1.0,
        "shield_start": False,
        "rating": (3, 3, 3),
        "perk": "No weaknesses - a solid pick",
        "engines": ((106 / 240, 226 / 240, 1.0), (134 / 240, 226 / 240, 1.0)),
    },
    "viper": {
        "name": "VIPER",
        "role": "AGILE INTERCEPTOR",
        "file": "ship2",
        "speed": 6.6,
        "bolt_speed": 6,
        "hit_scale": 0.86,
        "shield_start": False,
        "rating": (5, 2, 3),
        "perk": "Fast, small target, slower bolts",
        "engines": ((120 / 240, 232 / 240, 1.5),),
    },
    "titan": {
        "name": "TITAN",
        "role": "HEAVY GUNSHIP",
        "file": "ship3",
        "speed": 3.8,
        "bolt_speed": 10,
        "hit_scale": 1.18,
        "shield_start": False,
        "rating": (2, 5, 2),
        "perk": "Very fast bolts, big slow target",
        "engines": ((57 / 240, 228 / 240, 1.0), (107 / 240, 231 / 240, 0.9),
                    (133 / 240, 231 / 240, 0.9), (183 / 240, 228 / 240, 1.0)),
    },
    "aegis": {
        "name": "AEGIS",
        "role": "DEFENDER",
        "file": "ship4",
        "speed": 4.4,
        "bolt_speed": 7,
        "hit_scale": 1.08,
        "shield_start": True,
        "rating": (3, 3, 5),
        "perk": "Starts every run with a shield",
        "engines": ((108 / 240, 231 / 240, 1.0), (132 / 240, 231 / 240, 1.0)),
    },
}


def ship_info(model):
    return SHIPS.get(model, SHIPS[DEFAULT_SHIP])
