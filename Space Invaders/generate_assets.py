import os
import sys
import math
import random
import wave

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("generate_assets.py needs Pillow and numpy:  pip install -r requirements-dev.txt")
    sys.exit(1)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SS = 4
IMG_DIR = os.path.join("assets", "images")


def hex_color(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def ellipse_pts(cx, cy, rx, ry, n=90, start=0.0, end=360.0):
    pts = []
    for i in range(n + 1):
        a = math.radians(start + (end - start) * i / n)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def regular_poly(cx, cy, r, sides, rotation=0.0):
    return [(cx + r * math.cos(math.radians(rotation + 360 * i / sides)),
             cy + r * math.sin(math.radians(rotation + 360 * i / sides)))
            for i in range(sides)]


def mirror(right_pts, cx):
    return right_pts + [(2 * cx - x, y) for x, y in reversed(right_pts[1:])]


def flip_x(pts, cx):
    return [(2 * cx - x, y) for x, y in pts]


class Art:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))

    def scaled(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def polygon_mask(self, pts):
        mask = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(mask).polygon(self.scaled(pts), fill=255)
        return mask

    def composite(self, layer):
        self.img = Image.alpha_composite(self.img, layer)

    def gradient_layer(self, mask, c0, c1, y0, y1, axis="v"):
        w, h = self.img.size
        if axis == "v":
            t = np.clip((np.arange(h) - y0 * SS) / max(1, (y1 - y0) * SS), 0, 1)[:, None] * np.ones((1, w))
        else:
            t = np.clip((np.arange(w) - y0 * SS) / max(1, (y1 - y0) * SS), 0, 1)[None, :] * np.ones((h, 1))
        c0 = np.array(c0, float)
        c1 = np.array(c1, float)
        arr = c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]
        layer = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
        layer.putalpha(mask)
        return layer

    def fill(self, pts, c0, c1=None, y0=None, y1=None, axis="v", outline=None, outline_w=2.0):
        mask = self.polygon_mask(pts)
        if c1 is None:
            c1 = c0
        if y0 is None:
            ys = [p[1] for p in pts] if axis == "v" else [p[0] for p in pts]
            y0, y1 = min(ys), max(ys)
        self.composite(self.gradient_layer(mask, c0, c1, y0, y1, axis))
        if outline:
            self.stroke(pts + [pts[0]], outline, outline_w)

    def stroke(self, pts, color, width=2.0, alpha=255):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        col = tuple(color) + (alpha,)
        d.line(self.scaled(pts), fill=col, width=int(width * SS), joint="curve")
        for x, y in (pts[0], pts[-1]):
            r = width * SS / 2
            d.ellipse((x * SS - r, y * SS - r, x * SS + r, y * SS + r), fill=col)
        self.composite(layer)

    def dot(self, cx, cy, r, color, alpha=255):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS),
                                      fill=tuple(color) + (alpha,))
        self.composite(layer)

    def glow(self, mask, color, radius, strength=1.0):
        blurred = mask.filter(ImageFilter.GaussianBlur(radius * SS))
        alpha = blurred.point(lambda v: int(min(255, v * strength)))
        layer = Image.new("RGBA", self.img.size, tuple(color) + (0,))
        layer.putalpha(alpha)
        self.composite(layer)

    def glow_pts(self, pts, color, radius, strength=1.0):
        self.glow(self.polygon_mask(pts), color, radius, strength)

    def glow_dot(self, cx, cy, r, color, radius, strength=1.0):
        mask = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(mask).ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS), fill=255)
        self.glow(mask, color, radius, strength)

    def finish(self):
        small = self.img.convert("RGBa").resize((self.w, self.h), Image.LANCZOS).convert("RGBA")
        return small


def save(img, name):
    os.makedirs(IMG_DIR, exist_ok=True)
    img.save(os.path.join(IMG_DIR, name), optimize=True)
    print("  wrote", name, img.size)


SHIP_WING = [(136, 100), (158, 120), (216, 168), (228, 198), (202, 206), (152, 194), (138, 184)]
SHIP_POD = [(210, 158), (222, 158), (229, 174), (229, 212), (221, 226), (211, 226), (207, 208)]
SHIP_BARREL = [(215, 136), (221, 136), (221, 160), (215, 160)]
SHIP_CANARD = [(133, 56), (157, 82), (164, 96), (150, 100), (133, 88)]
SHIP_ENGINE = [(126, 184), (141, 188), (143, 222), (125, 224)]
SHIP_NOZZLE = [(124, 220), (144, 220), (141, 230), (127, 230)]
SHIP_BODY = [(120, 12), (129, 40), (134, 78), (137, 120), (136, 166), (132, 204), (127, 222)]


def draw_ship_hull():
    a = Art(240, 240)
    cx = 120
    edge = (22, 26, 40)

    a.glow(a.polygon_mask(mirror(SHIP_BODY, cx)), (80, 120, 200), 3, 0.35)

    for pts in (SHIP_WING, flip_x(SHIP_WING, cx)):
        a.fill(pts, (176, 186, 206), (62, 70, 92), outline=edge, outline_w=2.4)
    for pts in (SHIP_CANARD, flip_x(SHIP_CANARD, cx)):
        a.fill(pts, (196, 206, 224), (86, 94, 116), outline=edge, outline_w=2.0)
    for pts in (SHIP_ENGINE, flip_x(SHIP_ENGINE, cx)):
        a.fill(pts, (120, 130, 152), (40, 46, 62), axis="h", y0=min(p[0] for p in pts), y1=max(p[0] for p in pts),
               outline=edge, outline_w=2.0)
    for pts in (SHIP_NOZZLE, flip_x(SHIP_NOZZLE, cx)):
        a.fill(pts, (58, 62, 78), (18, 20, 28), outline=edge, outline_w=1.8)
    for pts in (SHIP_POD, flip_x(SHIP_POD, cx)):
        a.fill(pts, (170, 180, 200), (56, 62, 82), outline=edge, outline_w=2.2)
    for pts in (SHIP_BARREL, flip_x(SHIP_BARREL, cx)):
        a.fill(pts, (110, 118, 138), (36, 40, 54), outline=edge, outline_w=1.6)

    body = mirror(SHIP_BODY, cx)
    a.fill(body, (246, 250, 255), (96, 106, 130), outline=edge, outline_w=2.6)
    lit = mirror([(120, 20), (124, 44), (127, 80), (128, 120), (127, 168), (124, 200), (122, 214)], cx)
    a.fill(lit, (255, 255, 255), (150, 160, 184))
    a.stroke([(120, 18), (120, 214)], (110, 122, 148), 1.2, 140)

    for side in (1, -1):
        def px(x):
            return 120 + side * (x - 120)
        a.stroke([(px(146), 128), (px(206), 178)], (44, 50, 68), 1.3, 190)
        a.stroke([(px(146), 150), (px(200), 194)], (44, 50, 68), 1.3, 160)
        a.stroke([(px(150), 112), (px(148), 186)], (44, 50, 68), 1.2, 130)
        a.stroke([(px(138), 60), (px(150), 74)], (60, 68, 90), 1.2, 160)
        for i in range(3):
            a.dot(px(133), 130 + i * 18, 1.4, (44, 50, 68))

    canopy = ellipse_pts(120, 90, 12, 27)
    a.fill(canopy, (10, 18, 40), (70, 130, 200), outline=(14, 20, 36), outline_w=2.0)
    shine = ellipse_pts(116, 78, 3.6, 13)
    a.fill(shine, (210, 240, 255), (120, 180, 230))
    return a


def draw_ship_accent():
    a = Art(240, 240)
    cx = 120
    shapes = []
    stripe = [(150, 138), (206, 178), (211, 187), (198, 189), (148, 152)]
    shapes.append(stripe)
    shapes.append(flip_x(stripe, cx))
    inner = [(140, 112), (150, 118), (150, 176), (142, 172)]
    shapes.append(inner)
    shapes.append(flip_x(inner, cx))
    spine = [(118.2, 118), (121.8, 118), (121.8, 200), (118.2, 200)]
    shapes.append(spine)
    canard_edge = [(136, 60), (160, 86), (158, 90), (134, 66)]
    shapes.append(canard_edge)
    shapes.append(flip_x(canard_edge, cx))

    full = Image.new("L", a.img.size, 0)
    d = ImageDraw.Draw(full)
    for s in shapes:
        d.polygon(a.scaled(s), fill=255)
    for cxp in (134, 106):
        d.ellipse(((cxp - 9) * SS, (226 - 9) * SS, (cxp + 9) * SS, (226 + 9) * SS), fill=255)
    for px, py, r in ((222, 176, 4.2), (18, 176, 4.2), (218, 138, 3.4), (22, 138, 3.4), (120, 26, 3.2)):
        d.ellipse(((px - r) * SS, (py - r) * SS, (px + r) * SS, (py + r) * SS), fill=255)
    d.ellipse(((120 - 13.5) * SS, (90 - 29) * SS, (120 + 13.5) * SS, (90 + 29) * SS), outline=255, width=int(2.4 * SS))

    a.glow(full, (255, 255, 255), 7, 1.3)
    a.glow(full, (255, 255, 255), 2.5, 1.6)
    sharp = Image.new("RGBA", a.img.size, (255, 255, 255, 0))
    sharp.putalpha(full)
    a.composite(sharp)
    return a


def finish_glow(a, shapes, dots=(), rings=(), lines=()):
    full = Image.new("L", a.img.size, 0)
    d = ImageDraw.Draw(full)
    for s in shapes:
        d.polygon(a.scaled(s), fill=255)
    for px, py, r in dots:
        d.ellipse(((px - r) * SS, (py - r) * SS, (px + r) * SS, (py + r) * SS), fill=255)
    for cx, cy, rx, ry, w in rings:
        d.ellipse(((cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS), outline=255, width=int(w * SS))
    for pts, w in lines:
        d.line(a.scaled(pts), fill=255, width=int(w * SS), joint="curve")
    a.glow(full, (255, 255, 255), 7, 1.3)
    a.glow(full, (255, 255, 255), 2.5, 1.6)
    sharp = Image.new("RGBA", a.img.size, (255, 255, 255, 0))
    sharp.putalpha(full)
    a.composite(sharp)
    return a


VIPER_BODY = [(120, 6), (126, 34), (130, 78), (132, 128), (131, 178), (128, 212), (124, 228)]
VIPER_WING = [(130, 92), (152, 122), (208, 188), (220, 224), (180, 218), (140, 194), (131, 168)]
VIPER_FIN = [(142, 146), (170, 128), (180, 138), (154, 194)]
VIPER_CANARD = [(129, 54), (152, 74), (157, 88), (130, 84)]


def draw_viper_hull():
    a = Art(240, 240)
    cx = 120
    edge = (14, 20, 40)
    a.glow(a.polygon_mask(mirror(VIPER_BODY, cx)), (90, 130, 220), 3, 0.35)
    for pts in (VIPER_WING, flip_x(VIPER_WING, cx)):
        a.fill(pts, (168, 190, 228), (44, 58, 104), outline=edge, outline_w=2.4)
    for pts in (VIPER_FIN, flip_x(VIPER_FIN, cx)):
        a.fill(pts, (196, 214, 244), (64, 80, 124), outline=edge, outline_w=2.0)
    for pts in (VIPER_CANARD, flip_x(VIPER_CANARD, cx)):
        a.fill(pts, (206, 222, 248), (84, 100, 142), outline=edge, outline_w=1.8)
    a.fill([(107, 208), (133, 208), (136, 232), (104, 232)], (70, 78, 104), (18, 20, 32), outline=edge, outline_w=1.8)
    body = mirror(VIPER_BODY, cx)
    a.fill(body, (236, 244, 255), (74, 92, 136), outline=edge, outline_w=2.6)
    lit = mirror([(120, 16), (123, 44), (125, 84), (126, 130), (125, 176), (123, 208), (121, 222)], cx)
    a.fill(lit, (255, 255, 255), (150, 168, 206))
    for side in (1, -1):
        def px(x):
            return 120 + side * (x - 120)
        a.stroke([(px(148), 128), (px(210), 196)], (36, 48, 84), 1.3, 190)
        a.stroke([(px(146), 150), (px(196), 208)], (36, 48, 84), 1.3, 160)
        a.stroke([(px(152), 140), (px(158), 190)], (36, 48, 84), 1.2, 130)
        for i in range(3):
            a.dot(px(133), 120 + i * 20, 1.3, (36, 48, 84))
    a.fill(ellipse_pts(120, 74, 9, 26), (10, 18, 40), (72, 132, 206), outline=(12, 18, 34), outline_w=2.0)
    a.fill(ellipse_pts(117, 64, 2.6, 12), (214, 242, 255), (124, 184, 232))
    return a


def draw_viper_accent():
    a = Art(240, 240)
    cx = 120
    stripe = [(146, 128), (206, 190), (211, 198), (198, 199), (142, 146)]
    fin_edge = [(144, 148), (170, 130), (173, 135), (148, 156)]
    spine = [(118.6, 100), (121.4, 100), (121.4, 204), (118.6, 204)]
    shapes = [stripe, flip_x(stripe, cx), fin_edge, flip_x(fin_edge, cx), spine]
    dots = [(120, 232, 9.5), (218, 222, 4.2), (22, 222, 4.2), (120, 18, 3.0)]
    rings = [(120, 74, 10.5, 27.5, 2.4)]
    return finish_glow(a, shapes, dots, rings)


TITAN_BODY = [(120, 16), (138, 26), (150, 62), (155, 116), (155, 170), (150, 208), (142, 228)]
TITAN_WING = [(152, 88), (194, 92), (228, 116), (232, 180), (216, 210), (160, 198), (152, 160)]
TITAN_POD = [(168, 146), (196, 146), (200, 214), (174, 226)]
TITAN_POD_NOZZLE = [(172, 218), (200, 214), (198, 230), (176, 234)]
TITAN_BARREL = [(201, 44), (217, 44), (217, 104), (201, 104)]
TITAN_ENGINE = [(124, 204), (144, 204), (146, 232), (122, 232)]


def draw_titan_hull():
    a = Art(240, 240)
    cx = 120
    edge = (22, 22, 30)
    a.glow(a.polygon_mask(mirror(TITAN_BODY, cx)), (150, 150, 190), 3, 0.3)
    for pts in (TITAN_WING, flip_x(TITAN_WING, cx)):
        a.fill(pts, (170, 172, 186), (52, 54, 68), outline=edge, outline_w=2.6)
    for pts in (TITAN_BARREL, flip_x(TITAN_BARREL, cx)):
        a.fill(pts, (140, 142, 158), (36, 38, 50), axis="h", y0=201, y1=217, outline=edge, outline_w=2.0)
        a.fill([(199, 38), (219, 38), (219, 50), (199, 50)],
               (90, 92, 108), (36, 38, 50), outline=edge, outline_w=1.6)
    for pts in (TITAN_POD, flip_x(TITAN_POD, cx)):
        a.fill(pts, (156, 158, 176), (44, 46, 60), axis="h", y0=min(p[0] for p in pts), y1=max(p[0] for p in pts),
               outline=edge, outline_w=2.2)
    for pts in (TITAN_POD_NOZZLE, flip_x(TITAN_POD_NOZZLE, cx)):
        a.fill(pts, (60, 62, 76), (16, 18, 24), outline=edge, outline_w=1.8)
    for pts in (TITAN_ENGINE, flip_x(TITAN_ENGINE, cx)):
        a.fill(pts, (110, 112, 130), (30, 32, 44), axis="h", y0=min(p[0] for p in pts), y1=max(p[0] for p in pts),
               outline=edge, outline_w=2.0)
    body = mirror(TITAN_BODY, cx)
    a.fill(body, (214, 216, 228), (66, 68, 84), outline=edge, outline_w=2.8)
    plate = mirror([(120, 36), (132, 52), (138, 90), (140, 130)], cx)
    a.fill(plate, (238, 240, 248), (118, 120, 138))
    for side in (1, -1):
        def px(x):
            return 120 + side * (x - 120)
        a.stroke([(px(160), 116), (px(226), 140)], (40, 42, 58), 1.6, 200)
        a.stroke([(px(160), 150), (px(224), 176)], (40, 42, 58), 1.6, 180)
        a.stroke([(px(146), 140), (px(146), 200)], (40, 42, 58), 1.4, 150)
        a.stroke([(px(126), 60), (px(146), 84)], (60, 62, 80), 1.4, 170)
        for i in range(4):
            a.dot(px(148), 100 + i * 24, 1.6, (40, 42, 58))
    a.fill(ellipse_pts(120, 88, 15, 24), (10, 14, 30), (76, 120, 190), outline=(10, 12, 24), outline_w=2.2)
    a.fill(ellipse_pts(114, 78, 4.4, 12), (214, 238, 255), (118, 170, 224))
    return a


def draw_titan_accent():
    a = Art(240, 240)
    cx = 120
    stripe = [(160, 122), (224, 146), (224, 156), (160, 134)]
    stripe2 = [(160, 156), (222, 180), (222, 188), (160, 168)]
    reactor = [(116, 118), (124, 118), (124, 196), (116, 196)]
    muzzle = [(199, 38), (219, 38), (219, 44), (199, 44)]
    shapes = [stripe, flip_x(stripe, cx), stripe2, flip_x(stripe2, cx), reactor, muzzle, flip_x(muzzle, cx)]
    dots = [(187, 232, 9), (53, 232, 9), (133, 232, 8.5), (107, 232, 8.5), (120, 30, 3.4)]
    rings = [(120, 88, 16.5, 25.5, 2.6)]
    return finish_glow(a, shapes, dots, rings)


AEGIS_BODY = [(120, 8), (132, 34), (142, 70), (146, 116), (142, 166), (134, 204), (124, 224)]
AEGIS_ARM = [(146, 90), (176, 62), (206, 48), (224, 56), (230, 82), (218, 128), (198, 172), (178, 206), (152, 198), (156, 152), (150, 118)]
AEGIS_TIP = [(214, 30), (224, 30), (226, 60), (212, 62)]


def draw_aegis_hull():
    a = Art(240, 240)
    cx = 120
    edge = (24, 26, 44)
    a.glow(a.polygon_mask(mirror(AEGIS_BODY, cx)), (200, 210, 255), 3, 0.35)
    for pts in (AEGIS_ARM, flip_x(AEGIS_ARM, cx)):
        a.fill(pts, (216, 220, 240), (76, 82, 118), outline=edge, outline_w=2.6)
    for pts in (AEGIS_TIP, flip_x(AEGIS_TIP, cx)):
        a.fill(pts, (150, 156, 184), (44, 48, 72), outline=edge, outline_w=1.8)
    for ex in (108, 132):
        a.fill([(ex - 9, 200), (ex + 9, 200), (ex + 10, 226), (ex - 10, 226)], (110, 114, 140), (28, 30, 44), axis="h",
               y0=ex - 10, y1=ex + 10, outline=edge, outline_w=1.8)
        a.fill([(ex - 10, 222), (ex + 10, 222), (ex + 7, 232), (ex - 7, 232)], (56, 58, 80), (16, 18, 28), outline=edge, outline_w=1.6)
    body = mirror(AEGIS_BODY, cx)
    a.fill(body, (252, 252, 255), (118, 122, 156), outline=edge, outline_w=2.8)
    lit = mirror([(120, 20), (126, 44), (132, 80), (134, 120), (132, 164), (126, 198)], cx)
    a.fill(lit, (255, 255, 255), (196, 200, 226))
    for side in (1, -1):
        def px(x):
            return 120 + side * (x - 120)
        a.stroke([(px(160), 96), (px(214), 76)], (54, 60, 96), 1.5, 180)
        a.stroke([(px(158), 130), (px(216), 108)], (54, 60, 96), 1.5, 170)
        a.stroke([(px(160), 168), (px(204), 148)], (54, 60, 96), 1.5, 160)
        a.stroke([(px(146), 90), (px(150), 190)], (54, 60, 96), 1.2, 120)
    a.fill(ellipse_pts(120, 84, 10, 20), (12, 16, 36), (80, 130, 210), outline=(12, 14, 30), outline_w=2.0)
    a.fill(ellipse_pts(116.5, 76, 3, 9), (220, 242, 255), (128, 184, 232))
    a.dot(120, 140, 17, (34, 38, 64))
    a.stroke(ellipse_pts(120, 140, 17, 17, n=60), (150, 156, 190), 1.8, 255)
    return a


def draw_aegis_accent():
    a = Art(240, 240)
    cx = 120
    stripe = [(158, 92), (206, 68), (214, 74), (212, 82), (160, 106)]
    stripe2 = [(160, 130), (216, 106), (218, 116), (162, 142)]
    tip = [(214, 30), (224, 30), (224, 38), (214, 38)]
    shapes = [stripe, flip_x(stripe, cx), stripe2, flip_x(stripe2, cx), tip, flip_x(tip, cx)]
    dots = [(108, 232, 8.5), (132, 232, 8.5), (120, 140, 8.5), (120, 22, 3.2), (186, 210, 4.2), (54, 210, 4.2)]
    rings = [(120, 84, 10.8, 20.8, 2.2), (120, 140, 17.5, 17.5, 2.4)]
    return finish_glow(a, shapes, dots, rings)


def draw_drone():
    a = Art(200, 200)
    edge = (24, 10, 60)
    a.glow(a.polygon_mask(ellipse_pts(100, 112, 80, 52)), (255, 60, 200), 10, 0.55)
    for lx in (56, 100, 144):
        leg = [(lx - 10, 132), (lx + 10, 132), (lx, 172)]
        a.fill(leg, (120, 70, 200), (40, 16, 92), outline=edge, outline_w=2)
        a.glow_dot(lx, 174, 5, (255, 120, 220), 6, 1.4)
        a.dot(lx, 172, 3.4, (255, 230, 250))
    for sx in (1, -1):
        px = 100 + sx * 30
        a.stroke([(px, 70), (100 + sx * 48, 30)], (150, 110, 230), 3)
        a.glow_dot(100 + sx * 48, 28, 6, (90, 240, 255), 8, 1.6)
        a.dot(100 + sx * 48, 28, 5, (210, 255, 255))
    body = ellipse_pts(100, 116, 82, 36)
    a.fill(body, (196, 140, 255), (50, 18, 108), outline=edge, outline_w=3)
    a.fill(ellipse_pts(100, 128, 66, 18, start=0, end=180), (70, 30, 140), (30, 10, 70))
    a.stroke(ellipse_pts(100, 116, 66, 26, n=60, start=10, end=170), (120, 70, 210), 2, 200)
    for i in range(7):
        x = 34 + i * 22
        y = 116 + 26 * math.sqrt(max(0, 1 - ((x - 100) / 66) ** 2)) * 0.9
        col = (90, 240, 255) if i % 2 == 0 else (255, 110, 220)
        a.glow_dot(x, y, 4.5, col, 5, 1.5)
        a.dot(x, y, 4, (255, 255, 255))
        a.dot(x, y, 3, col)
    dome = ellipse_pts(100, 92, 46, 42, start=180, end=360)
    a.fill(dome, (255, 200, 255), (150, 70, 230), outline=edge, outline_w=3)
    a.fill(ellipse_pts(100, 96, 30, 20), (18, 6, 44), (48, 14, 90), outline=(10, 4, 30), outline_w=1.5)
    a.glow_dot(100, 96, 9, (255, 60, 190), 8, 1.7)
    a.dot(100, 96, 9, (255, 90, 200))
    a.dot(100, 96, 5.5, (255, 200, 240))
    a.dot(98, 94, 2.2, (255, 255, 255))
    a.stroke(ellipse_pts(100, 92, 36, 32, n=40, start=200, end=250), (255, 255, 255), 2.4, 170)
    return a


def draw_dart():
    a = Art(200, 200)
    edge = (60, 12, 8)
    a.glow(a.polygon_mask([(100, 190), (150, 110), (150, 50), (50, 50), (50, 110)]), (255, 110, 30), 10, 0.55)
    blade = [(122, 84), (186, 50), (190, 76), (170, 112), (130, 122)]
    for pts in (blade, flip_x(blade, 100)):
        a.fill(pts, (255, 170, 80), (170, 36, 24), outline=edge, outline_w=2.6)
    a.stroke([(132, 96), (176, 66)], (255, 236, 170), 2, 200)
    a.stroke([(68, 96), (24, 66)], (255, 236, 170), 2, 200)
    body = [(100, 192), (114, 150), (130, 100), (136, 56), (100, 42), (64, 56), (70, 100), (86, 150)]
    a.fill(body, (255, 200, 110), (196, 44, 28), outline=edge, outline_w=3)
    ridge = [(100, 180), (108, 140), (112, 90), (100, 60), (88, 90), (92, 140)]
    a.fill(ridge, (255, 236, 190), (238, 110, 60))
    canopy = [(92, 82), (108, 82), (105, 128), (100, 140), (95, 128)]
    a.fill(canopy, (40, 6, 4), (110, 24, 10), outline=(30, 4, 2), outline_w=1.5)
    a.glow(a.polygon_mask([(96, 92), (104, 92), (103, 118), (97, 118)]), (255, 230, 90), 4, 1.6)
    a.fill([(96, 92), (104, 92), (103, 118), (97, 118)], (255, 240, 130), (255, 180, 40))
    for ex in (78, 122):
        a.glow_dot(ex, 46, 9, (255, 190, 60), 10, 1.5)
        a.dot(ex, 46, 8, (255, 130, 40))
        a.dot(ex, 46, 5, (255, 250, 210))
    return a


def draw_tank():
    a = Art(200, 200)
    edge = (6, 30, 28)
    a.glow(a.polygon_mask(regular_poly(100, 104, 84, 8, 22.5)), (60, 255, 150), 10, 0.5)
    for sx in (1, -1):
        cannon = [(100 + sx * 52, 136), (100 + sx * 36, 136), (100 + sx * 36, 182), (100 + sx * 52, 182)]
        a.fill(cannon, (120, 140, 150), (34, 44, 52), outline=edge, outline_w=2.4)
        a.glow_dot(100 + sx * 44, 184, 6, (120, 255, 170), 7, 1.5)
        a.dot(100 + sx * 44, 183, 4, (220, 255, 230))
        spike = [(100 + sx * 74, 84), (100 + sx * 98, 104), (100 + sx * 74, 124)]
        a.fill(spike, (110, 220, 170), (24, 90, 76), outline=edge, outline_w=2.4)
    hull = regular_poly(100, 104, 78, 8, 22.5)
    a.fill(hull, (140, 240, 190), (18, 80, 70), outline=edge, outline_w=3.4)
    plate = regular_poly(100, 104, 58, 8, 22.5)
    a.fill(plate, (18, 62, 58), (10, 38, 40), outline=(90, 220, 170), outline_w=2)
    for i in range(8):
        ang = math.radians(22.5 + 45 * i)
        x1, y1 = 100 + 44 * math.cos(ang), 104 + 44 * math.sin(ang)
        x2, y2 = 100 + 70 * math.cos(ang), 104 + 70 * math.sin(ang)
        a.stroke([(x1, y1), (x2, y2)], (10, 50, 46), 2.2, 200)
        rx, ry = 100 + 66 * math.cos(ang + math.radians(22.5)), 104 + 66 * math.sin(ang + math.radians(22.5))
        a.dot(rx, ry, 2.6, (210, 255, 230))
    a.glow_dot(100, 104, 26, (150, 255, 90), 14, 1.6)
    a.dot(100, 104, 26, (16, 48, 40))
    a.dot(100, 104, 21, (120, 240, 70))
    a.dot(100, 104, 14, (215, 255, 150))
    a.dot(100, 104, 7, (255, 255, 240))
    a.stroke(ellipse_pts(100, 104, 24, 24, n=40, start=200, end=260), (255, 255, 255), 2.2, 160)
    return a


def draw_boss():
    a = Art(420, 280)
    cx = 210
    edge = (36, 6, 20)
    a.glow(a.polygon_mask(mirror([(210, 20), (300, 54), (410, 120), (340, 170), (256, 236), (210, 268)], cx)),
           (255, 40, 60), 14, 0.5)
    spikes = [(210, 6), (198, 40), (222, 40)]
    for dx in (-70, -35, 0, 35, 70):
        sp = [(x + dx, y + (abs(dx) * 0.28)) for x, y in spikes]
        a.fill(sp, (230, 130, 150), (100, 24, 56), outline=edge, outline_w=2)
    hull_right = [(210, 26), (258, 32), (306, 58), (374, 90), (412, 122), (398, 152), (346, 164), (300, 194),
                  (262, 232), (236, 262), (210, 268)]
    hull = mirror(hull_right, cx)
    a.fill(hull, (222, 96, 120), (54, 14, 44), outline=edge, outline_w=3.6)
    for gx in (112, 168):
        for sx in (1, -1):
            x = cx + sx * (cx - gx)
            barrel = [(x - 9, 168), (x + 9, 168), (x + 8, 236), (x - 8, 236)]
            a.fill(barrel, (140, 130, 150), (36, 30, 44), axis="h", y0=x - 9, y1=x + 9, outline=edge, outline_w=2.4)
            a.fill([(x - 11, 234), (x + 11, 234), (x + 8, 246), (x - 8, 246)], (70, 60, 84), (24, 20, 32), outline=edge)
            a.glow_dot(x, 248, 7, (255, 120, 80), 9, 1.5)
            a.dot(x, 247, 5, (255, 190, 130))
            a.dot(x, 247, 2.6, (255, 250, 230))
    band_right = [(210, 46), (254, 52), (300, 76), (360, 104), (388, 124), (330, 138), (290, 122), (250, 100), (210, 92)]
    a.fill(mirror(band_right, cx), (70, 18, 50), (36, 8, 34), outline=(150, 60, 90), outline_w=1.8)
    for sx in (1, -1):
        def px(x):
            return cx + sx * (x - cx)
        a.stroke([(px(262), 100), (px(392), 128)], (200, 90, 120), 1.6, 200)
        a.stroke([(px(240), 170), (px(330), 156)], (30, 6, 24), 2.0, 200)
        a.stroke([(px(262), 200), (px(300), 176)], (30, 6, 24), 2.0, 200)
        for i in range(6):
            lx = px(270 + i * 22)
            ly = 96 + i * 5.2 + (i * i) * 0.35
            col = (255, 220, 90) if i % 2 == 0 else (255, 90, 90)
            a.glow_dot(lx, ly, 3.4, col, 5, 1.5)
            a.dot(lx, ly, 3.2, col)
            a.dot(lx, ly, 1.5, (255, 255, 255))
        slit = [(px(268), 132), (px(318), 124), (px(322), 130), (px(272), 140)]
        a.glow_pts(slit, (255, 40, 40), 5, 1.6)
        a.fill(slit, (255, 200, 120), (255, 60, 40))
    a.glow_dot(cx, 148, 60, (255, 90, 40), 22, 1.5)
    a.dot(cx, 148, 58, (34, 10, 30))
    a.stroke(ellipse_pts(cx, 148, 56, 56, n=80), (190, 80, 110), 3, 255)
    a.dot(cx, 148, 50, (60, 14, 44))
    for i in range(12):
        ang = math.radians(30 * i)
        a.stroke([(cx + 44 * math.cos(ang), 148 + 44 * math.sin(ang)), (cx + 55 * math.cos(ang), 148 + 55 * math.sin(ang))],
                 (140, 50, 80), 2.4, 255)
    a.glow_dot(cx, 148, 40, (255, 150, 60), 16, 1.6)
    a.dot(cx, 148, 40, (255, 90, 40))
    a.dot(cx, 148, 32, (255, 170, 70))
    a.dot(cx, 148, 22, (255, 232, 150))
    a.dot(cx, 148, 11, (255, 255, 245))
    a.stroke(ellipse_pts(cx, 148, 36, 36, n=40, start=200, end=260), (255, 255, 255), 2.6, 170)
    return a


def draw_player_bolt():
    a = Art(24, 60)
    core = Image.new("L", a.img.size, 0)
    d = ImageDraw.Draw(core)
    d.rounded_rectangle((9 * SS, 6 * SS, 15 * SS, 46 * SS), radius=3 * SS, fill=255)
    a.glow(core, (0, 210, 255), 6, 1.6)
    a.glow(core, (120, 240, 255), 3, 1.2)
    edge = Image.new("RGBA", a.img.size, (90, 230, 255, 0))
    edge.putalpha(core)
    a.composite(edge)
    inner = Image.new("L", a.img.size, 0)
    ImageDraw.Draw(inner).rounded_rectangle((11 * SS, 8 * SS, 13 * SS, 44 * SS), radius=SS, fill=255)
    white = Image.new("RGBA", a.img.size, (255, 255, 255, 0))
    white.putalpha(inner)
    a.composite(white)
    w, h = a.img.size
    arr = np.array(a.img)
    tail = np.clip(1.0 - (np.arange(h) / SS - 20) / 36.0, 0.0, 1.0)
    arr[..., 3] = (arr[..., 3] * tail[:, None]).astype(np.uint8)
    a.img = Image.fromarray(arr, "RGBA")
    return a


def draw_pellet():
    a = Art(16, 40)
    core = Image.new("L", a.img.size, 0)
    ImageDraw.Draw(core).rounded_rectangle((5.5 * SS, 6 * SS, 10.5 * SS, 32 * SS), radius=2.5 * SS, fill=255)
    a.glow(core, (110, 255, 90), 4.5, 1.7)
    body = Image.new("RGBA", a.img.size, (170, 255, 140, 0))
    body.putalpha(core)
    a.composite(body)
    inner = Image.new("L", a.img.size, 0)
    ImageDraw.Draw(inner).rounded_rectangle((7 * SS, 8 * SS, 9 * SS, 30 * SS), radius=SS, fill=255)
    white = Image.new("RGBA", a.img.size, (255, 255, 255, 0))
    white.putalpha(inner)
    a.composite(white)
    arr = np.array(a.img)
    h = arr.shape[0]
    tail = np.clip(1.0 - (np.arange(h) / SS - 14) / 24.0, 0.0, 1.0)
    arr[..., 3] = (arr[..., 3] * tail[:, None]).astype(np.uint8)
    a.img = Image.fromarray(arr, "RGBA")
    return a


def draw_enemy_bolt():
    a = Art(30, 30)
    cx = cy = 15
    a.glow_dot(cx, cy, 7, (255, 70, 30), 6, 1.8)
    a.dot(cx, cy, 9, (150, 20, 20), 200)
    a.dot(cx, cy, 7.5, (255, 90, 40))
    a.dot(cx, cy, 5, (255, 180, 70))
    a.dot(cx, cy, 2.8, (255, 250, 220))
    return a


POWERUP_ART = {
    "rapid": hex_color("#ffd23c"),
    "shield": hex_color("#3ce6ff"),
    "bomb": hex_color("#ff5a46"),
    "freeze": hex_color("#8ab4ff"),
    "life": hex_color("#ff5aa0"),
    "scatter": hex_color("#7dff6e"),
}


def draw_powerup(kind):
    color = POWERUP_ART[kind]
    a = Art(64, 64)
    a.glow_dot(32, 32, 24, color, 5, 1.4)
    a.dot(32, 32, 25, tuple(int(c * 0.9) for c in color))
    a.dot(32, 32, 22.5, (8, 12, 30))
    a.dot(32, 32, 20.5, tuple(int(c * 0.22) for c in color))
    a.stroke(ellipse_pts(32, 32, 24, 24, n=80, start=200, end=290), (255, 255, 255), 2.2, 150)
    white = (255, 255, 255)
    if kind == "rapid":
        for i in range(3):
            y = 21 + i * 9
            a.stroke([(21, y + 6), (32, y - 3), (43, y + 6)], color, 4.2)
            a.stroke([(21, y + 6), (32, y - 3), (43, y + 6)], white, 1.6)
    elif kind == "shield":
        pts = [(32, 14), (46, 20), (45, 35), (32, 50), (19, 35), (18, 20)]
        a.fill(pts, tuple(int(c * 0.55) for c in color), tuple(int(c * 0.25) for c in color), outline=color, outline_w=3)
        a.stroke([(32, 20), (32, 44)], white, 1.8, 200)
        a.stroke([(24, 28), (40, 28)], white, 1.8, 200)
    elif kind == "bomb":
        a.dot(31, 36, 13, (16, 18, 30))
        a.stroke(ellipse_pts(31, 36, 13, 13, n=60), color, 2.6)
        a.stroke([(38, 26), (44, 18), (48, 19)], (210, 190, 150), 2.4)
        a.glow_dot(49, 17, 4, (255, 210, 90), 4, 1.8)
        a.dot(49, 17, 3, (255, 240, 170))
        a.dot(27, 32, 3, (255, 255, 255), 200)
    elif kind == "freeze":
        for ang in (90, 30, -30):
            r = math.radians(ang)
            p1 = (32 + 18 * math.cos(r), 32 + 18 * math.sin(r))
            p2 = (32 - 18 * math.cos(r), 32 - 18 * math.sin(r))
            a.stroke([p1, p2], color, 3.4)
            a.stroke([p1, p2], white, 1.3)
            for s in (1, -1):
                bx, by = 32 + s * 11 * math.cos(r), 32 + s * 11 * math.sin(r)
                for off in (-35, 35):
                    rr = r + math.radians(off) + (math.pi if s < 0 else 0)
                    a.stroke([(bx, by), (bx + 5 * math.cos(rr), by + 5 * math.sin(rr))], color, 2)
    elif kind == "scatter":
        origin = (32, 44)
        for ang in (-46, -23, 0, 23, 46):
            r = math.radians(ang)
            tip = (origin[0] + 21 * math.sin(r), origin[1] - 21 * math.cos(r))
            base = (origin[0] + 8 * math.sin(r), origin[1] - 8 * math.cos(r))
            a.stroke([base, tip], color, 3.4)
            a.stroke([base, tip], white, 1.2)
            a.glow_dot(tip[0], tip[1], 2.6, color, 3, 1.6)
            a.dot(tip[0], tip[1], 2.8, white)
        a.dot(origin[0], origin[1], 4.6, (18, 30, 24))
        a.stroke(ellipse_pts(origin[0], origin[1], 4.6, 4.6, n=40), color, 1.8)
    elif kind == "life":
        heart = []
        for i in range(0, 361, 6):
            t = math.radians(i)
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            heart.append((32 + x * 0.98, 32 + y * 0.98 + 1))
        a.glow(a.polygon_mask(heart), color, 3, 1.4)
        a.fill(heart, (255, 150, 200), (230, 40, 110), outline=(255, 220, 240), outline_w=1.4)
        a.dot(25, 26, 2.6, (255, 255, 255), 200)
    return a


THEME_ART = {
    "nova": {
        "palette": [(84, 38, 170), (34, 78, 190), (170, 40, 140), (20, 130, 160), (96, 44, 200), (50, 40, 150)],
        "base": (4, 6, 16), "seed": 11,
        "planet": {"a": (70, 40, 150), "b": (210, 110, 190), "rim": (110, 150, 255),
                   "rings": ((200, 170, 255, 150), (140, 120, 220, 120), (230, 200, 255, 110))},
        "nebula_file": "bg_nebula.png", "planet_file": "planet.png",
    },
    "inferno": {
        "palette": [(200, 50, 30), (235, 120, 30), (150, 30, 60), (100, 20, 40), (210, 90, 20), (130, 40, 90)],
        "base": (14, 5, 6), "seed": 23,
        "planet": {"a": (110, 30, 20), "b": (255, 175, 70), "rim": (255, 150, 80),
                   "rings": ((255, 200, 140, 150), (200, 110, 70, 120), (255, 220, 170, 110))},
        "nebula_file": "bg_inferno.png", "planet_file": "planet_inferno.png",
    },
    "emerald": {
        "palette": [(20, 150, 90), (10, 110, 120), (70, 175, 60), (20, 80, 110), (30, 145, 130), (80, 125, 40)],
        "base": (3, 10, 9), "seed": 37,
        "planet": {"a": (20, 90, 70), "b": (150, 235, 130), "rim": (120, 255, 200),
                   "rings": ((170, 255, 210, 150), (90, 190, 150, 120), (210, 255, 230, 110))},
        "nebula_file": "bg_emerald.png", "planet_file": "planet_emerald.png",
    },
    "frost": {
        "palette": [(90, 150, 220), (60, 110, 190), (150, 200, 240), (70, 150, 190), (110, 130, 210), (40, 90, 150)],
        "base": (5, 9, 18), "seed": 41,
        "planet": {"a": (60, 100, 170), "b": (225, 240, 255), "rim": (170, 220, 255),
                   "rings": ((220, 240, 255, 150), (150, 190, 230, 120), (240, 250, 255, 110))},
        "nebula_file": "bg_frost.png", "planet_file": "planet_frost.png",
    },
    "synthwave": {
        "palette": [(230, 60, 170), (120, 50, 210), (255, 120, 90), (60, 60, 200), (200, 50, 150), (150, 60, 220)],
        "base": (12, 4, 16), "seed": 53,
        "planet": {"a": (140, 40, 160), "b": (255, 130, 180), "rim": (255, 140, 230),
                   "rings": ((255, 190, 240, 150), (200, 110, 210, 120), (255, 220, 250, 110))},
        "nebula_file": "bg_synthwave.png", "planet_file": "planet_synthwave.png",
    },
}


def luma_of(arr):
    arr = np.asarray(arr, np.float32)
    return float((arr[..., 0] * 0.3 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11).mean())


def draw_nebula(palette=None, base=(4, 6, 16), seed=11, target_luma=None):
    w, h = 800, 1200
    half_w, half_h = w // 2, h // 2
    rng = random.Random(seed)
    palette = palette or THEME_ART["nova"]["palette"]
    acc = np.zeros((half_h * 3, half_w, 3), np.float32)
    for _ in range(22):
        color = rng.choice(palette)
        cxp = rng.randint(-40, half_w + 40)
        cyp = rng.randint(0, half_h) + half_h
        rx = rng.randint(70, 190)
        ry = int(rx * rng.uniform(0.6, 1.5))
        strength = rng.uniform(0.25, 0.6)
        layer = Image.new("RGB", (half_w, half_h * 3), (0, 0, 0))
        d = ImageDraw.Draw(layer)
        for off in (-half_h, 0, half_h):
            d.ellipse((cxp - rx, cyp + off - ry, cxp + rx, cyp + off + ry),
                      fill=tuple(int(c * strength) for c in color))
        layer = layer.filter(ImageFilter.GaussianBlur(45))
        acc += np.array(layer, np.float32) * 0.22
    acc += np.array(base, np.float32)[None, None, :]
    tile = np.clip(acc, 0, 255).astype(np.uint8)
    crop = Image.fromarray(tile[half_h:half_h * 2], "RGB").resize((w, h), Image.BICUBIC)
    arr = np.array(crop, np.float32)
    rng2 = np.random.default_rng(5)
    dust = rng2.normal(0, 1, (h // 4, w // 4)).astype(np.float32)
    dust3 = np.vstack([dust, dust, dust])
    dust3 = (dust3 - dust3.min()) / (dust3.max() - dust3.min())
    dust_img = Image.fromarray((dust3 * 255).astype(np.uint8)).resize((w, h * 3), Image.BICUBIC)
    dust_img = dust_img.filter(ImageFilter.GaussianBlur(6)).crop((0, h, w, h * 2))
    dust = np.array(dust_img, np.float32) / 255.0
    arr *= (0.8 + 0.4 * dust)[..., None]
    if target_luma:
        arr *= target_luma / max(1e-6, luma_of(arr))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def draw_planet(a=(70, 40, 150), b=(210, 110, 190), rim=(110, 150, 255),
                rings=((200, 170, 255, 150), (140, 120, 220, 120), (230, 200, 255, 110))):
    size = 280
    ss = 2
    n = size * ss
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    cx = cy = n / 2
    r = n * 0.30
    nx = (xx - cx) / r
    ny = (yy - cy) / r
    d2 = nx ** 2 + ny ** 2
    inside = d2 <= 1.0
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    light = np.array([-0.55, -0.45, 0.70])
    light /= np.linalg.norm(light)
    diffuse = np.clip(nx * light[0] + ny * light[1] + nz * light[2], 0, 1)
    rng = np.random.default_rng(3)
    bands = np.sin(ny * 9 + np.sin(nx * 3 + ny * 2) * 0.9) * 0.5 + 0.5
    noise = rng.normal(0, 1, (n // 10, n // 10)).astype(np.float32)
    noise = np.array(Image.fromarray(((noise - noise.min()) / (noise.max() - noise.min()) * 255).astype(np.uint8)).resize(
        (n, n), Image.BICUBIC), np.float32) / 255.0
    tex = np.clip(bands * 0.7 + noise * 0.4, 0, 1)
    base_a = np.array(a, np.float32)
    base_b = np.array(b, np.float32)
    col = base_a[None, None, :] * (1 - tex[..., None]) + base_b[None, None, :] * tex[..., None]
    shade = (0.12 + 0.95 * diffuse ** 1.15)[..., None]
    col = col * shade
    rim_color = rim
    rim = np.clip(1 - nz, 0, 1) ** 3 * (0.4 + 0.6 * diffuse)
    col += rim[..., None] * np.array(rim_color, np.float32) * 0.9
    alpha = np.where(inside, 255, 0).astype(np.float32)
    atmos = np.clip(1.0 - (np.sqrt(d2) - 1.0) / 0.10, 0, 1) * (np.sqrt(d2) > 1.0)
    col = np.where(inside[..., None], col, np.array(rim_color, np.float32)[None, None, :])
    alpha = np.maximum(alpha, atmos * 90 * (0.3 + 0.7 * np.clip(diffuse + 0.3, 0, 1)))
    planet = np.dstack([np.clip(col, 0, 255), alpha]).astype(np.uint8)
    img = Image.fromarray(planet, "RGBA")

    ring = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ring_back = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    for layer, start, end in ((ring_back, 180, 360), (ring, 0, 180)):
        d = ImageDraw.Draw(layer)
        for radius, colr, width in ((n * 0.44, rings[0], 10), (n * 0.40, rings[1], 14), (n * 0.36, rings[2], 6)):
            box = (cx - radius, cy - radius * 0.28, cx + radius, cy + radius * 0.28)
            d.arc(box, start, end, fill=colr, width=int(width * ss / 2))
    tilt = -18
    ring_back = ring_back.rotate(tilt, resample=Image.BICUBIC, center=(cx, cy))
    ring = ring.rotate(tilt, resample=Image.BICUBIC, center=(cx, cy))
    out = Image.alpha_composite(ring_back, img)
    out = Image.alpha_composite(out, ring)
    return out.convert("RGBa").resize((size, size), Image.LANCZOS).convert("RGBA")


def compose_icon(hull_img, accent_img):
    tint = (0, 229, 255)
    tinted = accent_img.copy()
    px = np.array(tinted).astype(np.float32)
    px[..., 0] *= tint[0] / 255
    px[..., 1] *= tint[1] / 255
    px[..., 2] *= tint[2] / 255
    tinted = Image.fromarray(px.astype(np.uint8), "RGBA")
    base = Image.alpha_composite(hull_img, tinted)
    bg = Image.new("RGBA", (240, 240), (8, 12, 30, 255))
    mask = Image.new("L", (240, 240), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 239, 239), radius=48, fill=255)
    bg.putalpha(mask)
    ring = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle((3, 3, 236, 236), radius=46, outline=(0, 229, 255, 255), width=5)
    icon = Image.alpha_composite(bg, base.resize((210, 210), Image.LANCZOS).transform(
        (240, 240), Image.AFFINE, (1, 0, -15, 0, 1, -14)))
    icon = Image.alpha_composite(icon, ring)
    return icon.resize((64, 64), Image.LANCZOS)


def generate_images():
    print("Generating images...")
    hull = draw_ship_hull().finish()
    accent = draw_ship_accent().finish()
    save(hull, "ship1.png")
    save(accent, "ship1_accent.png")
    for number, (hull_fn, accent_fn) in enumerate(((draw_viper_hull, draw_viper_accent),
                                                   (draw_titan_hull, draw_titan_accent),
                                                   (draw_aegis_hull, draw_aegis_accent)), start=2):
        save(hull_fn().finish(), "ship%d.png" % number)
        save(accent_fn().finish(), "ship%d_accent.png" % number)
    save(draw_drone().finish(), "enemy_normal.png")
    save(draw_dart().finish(), "enemy_fast.png")
    save(draw_tank().finish(), "enemy_tank.png")
    save(draw_boss().finish(), "enemy_boss.png")
    save(draw_player_bolt().finish(), "bullet.png")
    save(draw_enemy_bolt().finish(), "enemy_bullet.png")
    for kind in POWERUP_ART:
        save(draw_powerup(kind).finish(), "powerup_%s.png" % kind)
    save(draw_pellet().finish(), "pellet.png")
    nova_luma = None
    for key, spec in THEME_ART.items():
        nebula = draw_nebula(spec["palette"], spec["base"], spec["seed"], nova_luma)
        if nova_luma is None:
            nova_luma = luma_of(np.array(nebula))
        save(nebula, spec["nebula_file"])
        planet = spec["planet"]
        save(draw_planet(planet["a"], planet["b"], planet["rim"], planet["rings"]), spec["planet_file"])
    save(compose_icon(hull, accent), "icon.png")
    for legacy in ("enemy1.png",):
        path = os.path.join(IMG_DIR, legacy)
        if os.path.exists(path):
            os.remove(path)
            print("  removed old", legacy)


SFX_RATE = 44100
MUSIC_RATE = 22050
SOUND_DIR = os.path.join("assets", "sounds")
MUSIC_DIR = os.path.join("assets", "music")

RNG = np.random.default_rng(2026)


def midi_freq(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def time_axis(seconds, sr):
    return np.arange(int(seconds * sr)) / sr


def phase_of(freq, sr):
    return 2 * np.pi * np.cumsum(freq) / sr


def wave_of(kind, phase, width=0.5):
    frac = (phase / (2 * np.pi)) % 1.0
    if kind == "sine":
        return np.sin(phase)
    if kind == "saw":
        return 2 * frac - 1
    if kind == "square":
        return np.where(frac < 0.5, 1.0, -1.0)
    if kind == "pulse":
        return np.where(frac < width, 1.0, -1.0) - (2 * width - 1)
    if kind == "tri":
        return 2 * np.abs(2 * frac - 1) - 1
    raise ValueError(kind)


def osc(kind, freq, seconds, sr, width=0.5):
    n = int(seconds * sr)
    freq_arr = np.full(n, freq, float) if np.isscalar(freq) else np.asarray(freq, float)[:n]
    return wave_of(kind, phase_of(freq_arr, sr), width)


def fft_filter(x, sr, low=None, high=None, order=4):
    spectrum = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
    gain = np.ones_like(freqs)
    if high is not None:
        gain *= 1.0 / (1.0 + (freqs / high) ** (2 * order))
    if low is not None:
        gain *= 1.0 - 1.0 / (1.0 + (freqs / max(low, 1.0)) ** (2 * order))
    return np.fft.irfft(spectrum * gain, len(x))


def noise(n):
    return RNG.uniform(-1, 1, n)


def expo(n, sr, rate, attack=0.002, release=0.004):
    t = np.arange(n) / sr
    env = np.exp(-t * rate)
    if attack > 0:
        env *= np.clip(t / attack, 0, 1)
    r = max(1, int(release * sr))
    if n > r:
        env[-r:] *= np.linspace(1, 0, r)
    return env


def shaped_noise(seconds, sr, cutoffs):
    n = int(seconds * sr)
    base = noise(n)
    bands = [fft_filter(base, sr, high=c) for c in cutoffs]
    pos = np.linspace(0, len(cutoffs) - 1, n)
    out = np.zeros(n)
    for i, band in enumerate(bands):
        weight = np.clip(1 - np.abs(pos - i), 0, 1)
        out += band * weight
    return out


def normalize(x, peak):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def save_wav(path, data, sr):
    data = np.clip(data, -1, 1)
    if data.ndim == 1:
        pcm = (data * 32767).astype("<i2")
        channels = 1
    else:
        pcm = (data * 32767).astype("<i2").reshape(-1)
        channels = data.shape[1]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())
    print("  wrote %s (%.1fs, %d KB)" % (path, len(data) / sr, os.path.getsize(path) // 1024))


def sfx_shoot():
    sr, dur = SFX_RATE, 0.17
    t = time_axis(dur, sr)
    f = 1700 * (240 / 1700) ** (t / dur)
    body = wave_of("saw", phase_of(f, sr)) * 0.55 + wave_of("square", phase_of(f * 0.5, sr)) * 0.45
    body = fft_filter(body, sr, high=5200)
    click = noise(len(t)) * np.exp(-t * 600) * 0.5
    return normalize((body * expo(len(t), sr, 17) + click), 0.62)


def sfx_enemy_shoot():
    sr, dur = SFX_RATE, 0.22
    t = time_axis(dur, sr)
    f = 520 * (170 / 520) ** (t / dur) * (1 + 0.03 * np.sin(2 * np.pi * 28 * t))
    body = wave_of("tri", phase_of(f, sr)) * 0.7 + wave_of("sine", phase_of(f * 2, sr)) * 0.3
    return normalize(body * expo(len(t), sr, 11), 0.34)


def sfx_hit():
    sr, dur = SFX_RATE, 0.16
    t = time_axis(dur, sr)
    ping = np.sin(2 * np.pi * 1320 * t) * 0.6 + np.sin(2 * np.pi * 1990 * t) * 0.35 + np.sin(2 * np.pi * 3150 * t) * 0.15
    click = noise(len(t)) * np.exp(-t * 900) * 0.6
    return normalize(ping * expo(len(t), sr, 32) + click, 0.5)


def boom(seconds, sr, sub_start, sub_end, decay, cutoffs):
    t = time_axis(seconds, sr)
    n = len(t)
    body = shaped_noise(seconds, sr, cutoffs) * expo(n, sr, decay, attack=0.003, release=0.05)
    f = sub_start * (sub_end / sub_start) ** np.clip(t / (seconds * 0.85), 0, 1)
    sub = np.sin(phase_of(f, sr)) * expo(n, sr, decay * 0.9, attack=0.004, release=0.05)
    crackle = noise(n) * (RNG.random(n) > 0.995) * expo(n, sr, decay * 1.4)
    return body * 0.85 + sub * 0.9 + crackle * 0.5


def sfx_explosion():
    return normalize(boom(0.95, SFX_RATE, 95, 34, 4.4, [9000, 3200, 1100, 380]), 0.88)


def sfx_bomb():
    sr = SFX_RATE
    whoosh_t = time_axis(0.28, sr)
    whoosh = fft_filter(noise(len(whoosh_t)), sr, low=300, high=4000) * np.linspace(0.05, 1, len(whoosh_t)) ** 2
    main = boom(1.6, sr, 70, 26, 2.8, [8000, 2600, 800, 260, 120])
    out = np.concatenate([whoosh * 0.6, main])
    return normalize(out, 0.95)


def sfx_powerup():
    sr = SFX_RATE
    notes = [72, 76, 79, 84]
    step = 0.075
    total = np.zeros(int(sr * (step * len(notes) + 0.35)))
    for i, m in enumerate(notes):
        n = int(sr * (0.32 if i == len(notes) - 1 else 0.18))
        tone = wave_of("pulse", phase_of(np.full(n, midi_freq(m)), sr), 0.3) * 0.6
        tone += wave_of("sine", phase_of(np.full(n, midi_freq(m + 12)), sr), 0.5) * 0.3
        tone *= expo(n, sr, 9 if i < len(notes) - 1 else 6)
        s = int(i * step * sr)
        total[s:s + n] += tone
    return normalize(fft_filter(total, sr, high=7000), 0.55)


def sfx_shield():
    sr, dur = SFX_RATE, 0.5
    t = time_axis(dur, sr)
    f = 240 * (1250 / 240) ** (t / 0.32)
    f = np.where(t < 0.32, f, 1250)
    body = wave_of("sine", phase_of(f, sr)) * 0.6 + wave_of("saw", phase_of(f * 0.5, sr)) * 0.25
    body *= 0.75 + 0.25 * np.sin(2 * np.pi * 24 * t)
    env = np.clip(t / 0.02, 0, 1) * np.where(t < 0.32, 1.0, np.exp(-(t - 0.32) * 12))
    ping = np.sin(2 * np.pi * 2100 * t) * np.where(t > 0.3, np.exp(-(t - 0.3) * 20), 0) * 0.5
    return normalize(fft_filter(body * env + ping, sr, high=6000), 0.55)


def sfx_levelup():
    sr = SFX_RATE
    notes = [(67, 0.11), (72, 0.11), (76, 0.11), (79, 0.5)]
    total = np.zeros(int(sr * 1.2))
    pos = 0.0
    for m, d in notes:
        n = int(sr * (d + 0.25))
        f = midi_freq(m)
        tone = wave_of("saw", phase_of(np.full(n, f), sr)) * 0.4 + wave_of("square", phase_of(np.full(n, f * 1.005), sr)) * 0.3
        tone = fft_filter(tone, sr, high=4200) * expo(n, sr, 5.5, release=0.06)
        s = int(pos * sr)
        total[s:s + n] += tone
        pos += d
    echo = np.zeros_like(total)
    d = int(0.16 * sr)
    echo[d:] += total[:-d] * 0.35
    return normalize(total + echo, 0.55)


def sfx_gameover():
    sr = SFX_RATE
    notes = [(64, 0.3), (62, 0.3), (60, 0.3), (57, 0.9)]
    total = np.zeros(int(sr * 2.2))
    pos = 0.0
    for i, (m, d) in enumerate(notes):
        n = int(sr * (d + 0.3))
        t = np.arange(n) / sr
        vib = 1 + (0.012 * np.sin(2 * np.pi * 5.5 * t) if i == len(notes) - 1 else 0.0)
        f = np.full(n, midi_freq(m)) * vib
        tone = wave_of("saw", phase_of(f, sr)) * 0.5 + wave_of("sine", phase_of(f * 0.5, sr)) * 0.5
        tone = fft_filter(tone, sr, high=1800) * expo(n, sr, 2.6, attack=0.01, release=0.08)
        s = int(pos * sr)
        total[s:s + n] += tone
        pos += d
    return normalize(total, 0.6)


def sfx_highscore():
    sr = SFX_RATE
    seq = [(72, 0.0, 0.12), (76, 0.12, 0.12), (79, 0.24, 0.12), (84, 0.36, 0.9), (88, 0.36, 0.9), (91, 0.5, 0.75)]
    total = np.zeros(int(sr * 1.9))
    for m, start, d in seq:
        n = int(sr * (d + 0.3))
        f = midi_freq(m)
        tone = wave_of("pulse", phase_of(np.full(n, f), sr), 0.35) * 0.35 + wave_of("sine", phase_of(np.full(n, f * 2), sr)) * 0.2
        tone = tone * expo(n, sr, 3.2 if d > 0.5 else 8, release=0.08)
        s = int(start * sr)
        total[s:s + n] += tone
    shimmer_t = time_axis(0.9, sr)
    for k, m in enumerate((96, 100, 103, 108, 103, 100)):
        n = int(sr * 0.25)
        s = int((0.5 + k * 0.09) * sr)
        blip = np.sin(2 * np.pi * midi_freq(m) * np.arange(n) / sr) * expo(n, sr, 12) * 0.16
        total[s:s + n] += blip
    return normalize(fft_filter(total, sr, high=9000), 0.6)


def sfx_warning():
    sr = SFX_RATE
    total = []
    for i in range(6):
        f = 520 if i % 2 == 0 else 760
        n = int(sr * 0.2)
        t = np.arange(n) / sr
        tone = wave_of("square", phase_of(np.full(n, f) * (1 + 0.02 * np.sin(2 * np.pi * 9 * t)), sr)) * 0.5
        tone += wave_of("saw", phase_of(np.full(n, f * 0.5), sr)) * 0.3
        total.append(fft_filter(tone, sr, high=2600) * expo(n, sr, 2.5, attack=0.01, release=0.02))
    return normalize(np.concatenate(total), 0.5)


def sfx_click():
    sr, dur = SFX_RATE, 0.06
    t = time_axis(dur, sr)
    f = 1200 - 400 * (t / dur)
    return normalize(np.sin(phase_of(f, sr)) * expo(len(t), sr, 60), 0.4)


def sfx_scatter():
    sr, dur = SFX_RATE, 0.55
    rng = np.random.default_rng(777)
    n = int(sr * dur)
    t = np.arange(n) / sr
    base = rng.uniform(-1, 1, n)
    crack = fft_filter(base, sr, low=1500) * np.exp(-t * 90)
    bands = [fft_filter(base, sr, high=c) for c in (7000, 2500, 900)]
    pos = np.clip(t / 0.25, 0, 2)
    body = np.zeros(n)
    for i, band in enumerate(bands):
        body += band * np.clip(1 - np.abs(pos - i), 0, 1)
    body *= np.exp(-t * 11)
    f = 130 * (42 / 130) ** np.clip(t / 0.3, 0, 1)
    thump = np.sin(phase_of(f, sr)) * np.exp(-t * 13)
    pellets = np.zeros(n)
    for start in rng.uniform(0.04, 0.32, 9):
        s = int(start * sr)
        length = int(0.03 * sr)
        tick = fft_filter(rng.uniform(-1, 1, length), sr, low=2500) * np.exp(-np.arange(length) / sr * 130)
        pellets[s:s + length] += tick * rng.uniform(0.15, 0.35)
    out = crack * 0.8 + body * 0.8 + thump * 0.9 + pellets
    return normalize(out, 0.9)


def pad_to(x, seconds, sr):
    n = int(seconds * sr)
    return np.concatenate([x, np.zeros(max(0, n - len(x)))])[:n]


class Track:
    def __init__(self, bpm, bars, sr=MUSIC_RATE, beats_per_bar=4):
        self.sr = sr
        self.bpm = bpm
        self.spb = 60.0 / bpm
        self.bars = bars
        self.beats = bars * beats_per_bar
        self.n = int(round(self.beats * self.spb * sr))
        self.left = np.zeros(self.n)
        self.right = np.zeros(self.n)

    def place(self, beat, signal, pan=0.0, gain=1.0, bus=None):
        start = int(round(beat * self.spb * self.sr)) % self.n
        end = start + len(signal)
        target_l, target_r = (self.left, self.right) if bus is None else bus
        gl = gain * np.cos((pan + 1) * np.pi / 4)
        gr = gain * np.sin((pan + 1) * np.pi / 4)
        if end <= self.n:
            target_l[start:end] += signal * gl
            target_r[start:end] += signal * gr
        else:
            k = self.n - start
            target_l[start:] += signal[:k] * gl
            target_r[start:] += signal[:k] * gr
            rest = min(end - self.n, self.n)
            target_l[:rest] += signal[k:k + rest] * gl
            target_r[:rest] += signal[k:k + rest] * gr

    def seconds(self, beats):
        return beats * self.spb


def synth_bass(f, seconds, sr, drive=1.0):
    n = int(seconds * sr)
    ph = phase_of(np.full(n, f), sr)
    tone = wave_of("saw", ph) * 0.55 + wave_of("square", ph * 0.5) * 0.35 + np.sin(ph) * 0.5
    tone = np.tanh(tone * drive)
    return tone * expo(n, sr, 3.2 / max(seconds, 0.05) + 1.5, attack=0.004, release=0.02)


def synth_pluck(f, seconds, sr, width=0.28, decay=9.0):
    n = int(seconds * sr)
    tone = wave_of("pulse", phase_of(np.full(n, f), sr), width) * 0.6 + wave_of("saw", phase_of(np.full(n, f * 1.004), sr)) * 0.3
    return tone * expo(n, sr, decay, attack=0.002, release=0.01)


def synth_pad(f, seconds, sr):
    n = int(seconds * sr)
    tone = np.zeros(n)
    for detune in (0.994, 1.0, 1.006):
        tone += wave_of("saw", phase_of(np.full(n, f * detune), sr)) / 3
    t = np.arange(n) / sr
    env = np.clip(t / 0.35, 0, 1) * np.clip((seconds - t) / 0.4, 0, 1)
    return tone * env


def synth_lead(f, seconds, sr, vibrato=0.006, drive=1.0):
    n = int(seconds * sr)
    t = np.arange(n) / sr
    vib = 1 + vibrato * np.sin(2 * np.pi * 5.6 * t) * np.clip(t / 0.15, 0, 1)
    ph = phase_of(f * vib, sr)
    tone = wave_of("saw", ph) * 0.5 + wave_of("square", ph * 1.003) * 0.35
    tone = np.tanh(tone * drive)
    env = expo(n, sr, 1.6, attack=0.012, release=0.04)
    return tone * env


def synth_bell(f, seconds, sr):
    n = int(seconds * sr)
    t = np.arange(n) / sr
    tone = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6) + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 10)
    return tone * expo(n, sr, 2.4, attack=0.003, release=0.05)


def drum_kick(sr):
    n = int(0.3 * sr)
    t = np.arange(n) / sr
    f = 45 + 130 * np.exp(-t * 32)
    body = np.sin(phase_of(f, sr)) * np.exp(-t * 11)
    click = noise(n) * np.exp(-t * 500) * 0.25
    return body + click


def drum_snare(sr):
    n = int(0.22 * sr)
    t = np.arange(n) / sr
    nz = fft_filter(noise(n), sr, low=1200, high=9000) * np.exp(-t * 20)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 26) * 0.6
    return nz * 0.75 + tone


def drum_hat(sr, open_hat=False):
    n = int((0.16 if open_hat else 0.05) * sr)
    t = np.arange(n) / sr
    return fft_filter(noise(n), sr, low=6000) * np.exp(-t * (18 if open_hat else 70)) * 0.5


def chord_notes(root, kind):
    return {"min": (0, 3, 7), "maj": (0, 4, 7), "sus": (0, 5, 7)}[kind]


def echo_circular(x, sr, delays_s, gains):
    out = x.copy()
    for d, g in zip(delays_s, gains):
        out += np.roll(x, int(d * sr)) * g
    return out


def sidechain(track_n, sr, kick_beats, spb, depth=0.55, release=0.16):
    env = np.ones(track_n)
    t = np.arange(track_n) / sr
    for b in kick_beats:
        s = int(round(b * spb * sr))
        idx = (np.arange(track_n) - s) % track_n
        dt = idx / sr
        env = np.minimum(env, 1 - depth * np.exp(-dt / release) * (dt >= 0))
    return env


def build_theme():
    tr = Track(bpm=128, bars=8)
    sr, spb = tr.sr, tr.spb
    prog = [(57, "min"), (53, "maj"), (48, "maj"), (55, "maj")]
    bass_l, bass_r = np.zeros(tr.n), np.zeros(tr.n)
    arp_l, arp_r = np.zeros(tr.n), np.zeros(tr.n)
    pad_l, pad_r = np.zeros(tr.n), np.zeros(tr.n)
    lead_l, lead_r = np.zeros(tr.n), np.zeros(tr.n)
    drum_l, drum_r = np.zeros(tr.n), np.zeros(tr.n)
    for bar in range(8):
        root, kind = prog[bar // 2]
        tones = [root + i for i in chord_notes(root, kind)]
        bass_root = root - 24 + (12 if root - 24 < 33 else 0)
        for i, off in enumerate([0, 0, 12, 0, 0, 0, 12, 0]):
            beat = bar * 4 + i * 0.5
            tr.place(beat, synth_bass(midi_freq(bass_root + off), 0.5 * spb * 0.95, sr), 0.0, 0.5, (bass_l, bass_r))
        arp_tones = [tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[0] + 24]
        pattern = [0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 2, 1, 3, 2]
        for i, idx in enumerate(pattern):
            beat = bar * 4 + i * 0.25
            accent = 1.0 if i % 4 == 0 else 0.7
            tr.place(beat, synth_pluck(midi_freq(arp_tones[idx]), 0.25 * spb * 2.2, sr), -0.5 if i % 2 == 0 else 0.5,
                     0.3 * accent, (arp_l, arp_r))
        if bar % 2 == 0:
            for m in tones:
                tr.place(bar * 4, synth_pad(midi_freq(m), 8 * spb, sr), 0.0, 0.16, (pad_l, pad_r))
                tr.place(bar * 4, synth_pad(midi_freq(m + 12), 8 * spb, sr), 0.0, 0.10, (pad_l, pad_r))
    melody = {
        4: [(0, 1.5, 76), (1.5, 0.5, 79), (2, 1, 76), (3, 1, 74)],
        5: [(0, 1.5, 72), (1.5, 0.5, 74), (2, 2, 76)],
        6: [(0, 1.5, 74), (1.5, 0.5, 71), (2, 1, 74), (3, 1, 79)],
        7: [(0, 2, 79), (2, 1, 76), (3, 1, 74)],
        0: [(2, 1, 69), (3, 1, 72)],
        1: [(0, 1.5, 76), (1.5, 0.5, 74), (2, 2, 72)],
        2: [(0, 1.5, 72), (1.5, 0.5, 69), (2, 1, 72), (3, 1, 77)],
        3: [(0, 2, 76), (2, 1, 74), (3, 1, 72)],
    }
    for bar, notes in melody.items():
        for off, d, m in notes:
            tr.place(bar * 4 + off, synth_lead(midi_freq(m), d * spb * 0.95, sr), 0.15, 0.32 if bar >= 4 else 0.2, (lead_l, lead_r))
    kick, snare, hat, ohat = drum_kick(sr), drum_snare(sr), drum_hat(sr), drum_hat(sr, True)
    kick_beats = []
    for bar in range(8):
        for b in range(4):
            tr.place(bar * 4 + b, kick, 0.0, 0.95, (drum_l, drum_r))
            kick_beats.append(bar * 4 + b)
            if b in (1, 3):
                tr.place(bar * 4 + b, snare, 0.0, 0.55, (drum_l, drum_r))
            tr.place(bar * 4 + b + 0.5, ohat if b == 3 else hat, 0.25, 0.32, (drum_l, drum_r))
            tr.place(bar * 4 + b, hat, -0.25, 0.14, (drum_l, drum_r))
    duck = sidechain(tr.n, sr, kick_beats, spb)
    out = []
    for bus_l, bus_r, low, high, g in ((bass_l, bass_r, 40, 900, 1.0), (arp_l, arp_r, 200, 5200, 0.9),
                                        (pad_l, pad_r, 120, 2600, 0.8), (lead_l, lead_r, 200, 4200, 0.8)):
        pair = []
        for ch in (bus_l, bus_r):
            ch = fft_filter(ch, sr, low=low, high=high)
            pair.append(ch * duck * g)
        out.append(pair)
    arp_l_f, arp_r_f = out[1]
    arp_l_f = echo_circular(arp_l_f, sr, [spb * 0.75, spb * 1.5], [0.32, 0.18])
    arp_r_f = echo_circular(arp_r_f, sr, [spb * 0.75 + 0.01, spb * 1.5 + 0.01], [0.32, 0.18])
    left = out[0][0] + arp_l_f + out[2][0] + out[3][0] + drum_l
    right = out[0][1] + arp_r_f + out[2][1] + out[3][1] + drum_r
    return finish_music(left, right)


def build_menu():
    tr = Track(bpm=88, bars=8)
    sr, spb = tr.sr, tr.spb
    prog = [(57, "min"), (53, "maj"), (48, "maj"), (55, "maj")]
    pad_l, pad_r = np.zeros(tr.n), np.zeros(tr.n)
    bell_l, bell_r = np.zeros(tr.n), np.zeros(tr.n)
    sub_l, sub_r = np.zeros(tr.n), np.zeros(tr.n)
    for bar in range(8):
        root, kind = prog[bar // 2]
        tones = [root + i for i in chord_notes(root, kind)]
        if bar % 2 == 0:
            for m in tones:
                tr.place(bar * 4, synth_pad(midi_freq(m), 8 * spb, sr), 0.0, 0.22, (pad_l, pad_r))
                tr.place(bar * 4, synth_pad(midi_freq(m + 12), 8 * spb, sr), 0.0, 0.14, (pad_l, pad_r))
            tr.place(bar * 4, synth_bass(midi_freq(root - 24 + (12 if root - 24 < 33 else 0)), 8 * spb * 0.98, sr) * 0.6, 0.0, 0.5,
                     (sub_l, sub_r))
        arp = [tones[0] + 24, tones[2] + 12, tones[1] + 24, tones[2] + 24, tones[0] + 24, tones[1] + 12, tones[2] + 24, tones[1] + 24]
        for i, m in enumerate(arp):
            tr.place(bar * 4 + i * 0.5, synth_bell(midi_freq(m), 2.0, sr), -0.6 if i % 2 == 0 else 0.6, 0.12 if i % 2 == 0 else 0.08,
                     (bell_l, bell_r))
    melody = [(16, 1.5, 81), (17.5, 0.5, 79), (18, 2, 76), (20, 2, 77), (22, 2, 74), (24, 1.5, 76), (25.5, 0.5, 72),
              (26, 2, 74), (28, 3, 79)]
    for beat, d, m in melody:
        tr.place(beat, synth_bell(midi_freq(m), 3.0, sr), 0.2, 0.22, (bell_l, bell_r))
    pad_l = fft_filter(pad_l, sr, low=100, high=1800)
    pad_r = fft_filter(pad_r, sr, low=100, high=1800)
    sub_l = fft_filter(sub_l, sr, low=35, high=300)
    sub_r = fft_filter(sub_r, sr, low=35, high=300)
    bell_l = echo_circular(bell_l, sr, [spb * 0.75, spb * 1.5, spb * 2.25], [0.4, 0.28, 0.18])
    bell_r = echo_circular(bell_r, sr, [spb * 0.75 + 0.012, spb * 1.5 + 0.012, spb * 2.25 + 0.012], [0.4, 0.28, 0.18])
    left = pad_l + bell_l + sub_l
    right = pad_r + bell_r + sub_r
    return finish_music(left, right, rms_target=0.12)


def build_boss():
    tr = Track(bpm=148, bars=8)
    sr, spb = tr.sr, tr.spb
    prog = [(52, "min"), (53, "maj"), (52, "min"), (53, "maj"), (52, "min"), (52, "min"), (48, "maj"), (47, "maj")]
    bass_l, bass_r = np.zeros(tr.n), np.zeros(tr.n)
    arp_l, arp_r = np.zeros(tr.n), np.zeros(tr.n)
    lead_l, lead_r = np.zeros(tr.n), np.zeros(tr.n)
    pad_l, pad_r = np.zeros(tr.n), np.zeros(tr.n)
    drum_l, drum_r = np.zeros(tr.n), np.zeros(tr.n)
    for bar in range(8):
        root, kind = prog[bar]
        tones = [root + i for i in chord_notes(root, kind)]
        bass_root = root - 12 if root - 12 >= 36 else root
        gallop = [0, 0, 12, 0, 0, 12, 0, 0, 0, 12, 0, 0, 12, 0, 12, 0]
        for i, off in enumerate(gallop):
            tr.place(bar * 4 + i * 0.25, synth_bass(midi_freq(bass_root + off), 0.25 * spb * 0.9, sr, drive=2.2), 0.0, 0.42,
                     (bass_l, bass_r))
        tr.place(bar * 4, synth_pad(midi_freq(tones[0] + 12), 4 * spb, sr), 0.0, 0.12, (pad_l, pad_r))
        tr.place(bar * 4, synth_pad(midi_freq(tones[1] + 12), 4 * spb, sr), 0.0, 0.10, (pad_l, pad_r))
        tr.place(bar * 4, synth_pad(midi_freq(tones[2] + 12), 4 * spb, sr), 0.0, 0.10, (pad_l, pad_r))
        arp_tones = [tones[0] + 24, tones[2] + 24, tones[1] + 24, tones[2] + 24]
        for i in range(16):
            m = arp_tones[[0, 1, 2, 3][i % 4]] + (12 if i % 8 == 7 else 0)
            tr.place(bar * 4 + i * 0.25, synth_pluck(midi_freq(m), 0.4 * spb, sr, 0.22, 14), -0.4 if i % 2 else 0.4, 0.2 if i % 4 else 0.28,
                     (arp_l, arp_r))
    riff = {
        0: [(0, 0.5, 76), (0.5, 0.5, 76), (1, 0.5, 79), (1.5, 0.5, 78), (2, 1, 76), (3, 0.5, 74), (3.5, 0.5, 76)],
        1: [(0, 0.5, 77), (0.5, 0.5, 77), (1, 0.5, 81), (1.5, 0.5, 79), (2, 1, 77), (3, 1, 76)],
        2: [(0, 0.5, 76), (0.5, 0.5, 76), (1, 0.5, 79), (1.5, 0.5, 78), (2, 1, 76), (3, 0.5, 74), (3.5, 0.5, 76)],
        3: [(0, 0.5, 77), (0.5, 0.5, 77), (1, 0.5, 81), (1.5, 0.5, 84), (2, 2, 81)],
        4: [(0, 1, 88), (1, 0.5, 86), (1.5, 0.5, 83), (2, 1, 84), (3, 1, 83)],
        5: [(0, 1, 79), (1, 0.5, 83), (1.5, 0.5, 86), (2, 2, 88)],
        6: [(0, 1, 84), (1, 1, 79), (2, 1, 76), (3, 1, 79)],
        7: [(0, 1, 83), (1, 1, 78), (2, 1, 75), (3, 1, 71)],
    }
    for bar, notes in riff.items():
        for off, d, m in notes:
            tr.place(bar * 4 + off, synth_lead(midi_freq(m), d * spb * 0.9, sr, 0.004, drive=2.0), 0.1, 0.24, (lead_l, lead_r))
    kick, snare, hat, ohat = drum_kick(sr), drum_snare(sr), drum_hat(sr), drum_hat(sr, True)
    kick_beats = []
    for bar in range(8):
        for b in range(4):
            tr.place(bar * 4 + b, kick, 0.0, 1.0, (drum_l, drum_r))
            kick_beats.append(bar * 4 + b)
            if b in (1, 3):
                tr.place(bar * 4 + b, snare, 0.0, 0.7, (drum_l, drum_r))
            if bar % 2 == 1 and b == 3:
                tr.place(bar * 4 + b + 0.5, kick, 0.0, 0.7, (drum_l, drum_r))
                tr.place(bar * 4 + b + 0.75, snare, 0.0, 0.4, (drum_l, drum_r))
            for k in range(4):
                tr.place(bar * 4 + b + k * 0.25, ohat if (b == 3 and k == 2) else hat, 0.3 if k % 2 else -0.3, 0.24 if k % 2 == 0 else 0.14,
                         (drum_l, drum_r))
    duck = sidechain(tr.n, sr, kick_beats, spb, depth=0.45, release=0.10)
    parts = []
    for bus_l, bus_r, low, high, g in ((bass_l, bass_r, 40, 1400, 1.0), (arp_l, arp_r, 250, 6000, 0.8),
                                        (lead_l, lead_r, 300, 4800, 0.85), (pad_l, pad_r, 150, 2500, 0.8)):
        parts.append([fft_filter(ch, sr, low=low, high=high) * duck * g for ch in (bus_l, bus_r)])
    arp_l_f = echo_circular(parts[1][0], sr, [spb * 0.75], [0.3])
    arp_r_f = echo_circular(parts[1][1], sr, [spb * 0.75 + 0.008], [0.3])
    left = parts[0][0] + arp_l_f + parts[2][0] + parts[3][0] + drum_l
    right = parts[0][1] + arp_r_f + parts[2][1] + parts[3][1] + drum_r
    return finish_music(left, right, rms_target=0.16)


def finish_music(left, right, rms_target=0.14):
    stereo = np.stack([left, right], axis=1)
    stereo = np.tanh(stereo * 1.1)
    rms = np.sqrt(np.mean(stereo ** 2))
    stereo *= rms_target / max(rms, 1e-6)
    peak = np.max(np.abs(stereo))
    if peak > 0.92:
        stereo *= 0.92 / peak
    return stereo


def generate_sounds():
    print("Generating sound effects...")
    effects = {
        "shoot": sfx_shoot, "enemy_shoot": sfx_enemy_shoot, "hit": sfx_hit, "explosion": sfx_explosion,
        "bomb": sfx_bomb, "powerup": sfx_powerup, "shield": sfx_shield, "levelup": sfx_levelup,
        "gameover": sfx_gameover, "highscore": sfx_highscore, "warning": sfx_warning, "click": sfx_click,
        "scatter": sfx_scatter,
    }
    for name, fn in effects.items():
        save_wav(os.path.join(SOUND_DIR, name + ".wav"), fn(), SFX_RATE)
    print("Generating music...")
    for name, fn in (("theme", build_theme), ("menu", build_menu), ("boss", build_boss)):
        save_wav(os.path.join(MUSIC_DIR, name + ".wav"), fn(), MUSIC_RATE)


def main():
    target = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    if target not in ("all", "images", "audio"):
        print("usage: python generate_assets.py [images|audio]")
        sys.exit(1)
    if target in ("all", "images"):
        generate_images()
    if target in ("all", "audio"):
        generate_sounds()
    print("Done.")


if __name__ == "__main__":
    main()
