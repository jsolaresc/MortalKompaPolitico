"""
especiales_placeholder.py
--------------------------
Sprites y sonidos PROVISORIOS de los ataques especiales (invocaciones):
león, satélite, bomba, ola de agua, tanque + cohete, ola de billetes,
movilización, etc. Lo usa tools/generar_placeholders.py.

Cada especial vive en assets/characters/<nombre>/special_fx/<parte>/N.png
y su sonido de efecto en assets/characters/<nombre>/sounds/special_sfx.wav.
La VOZ del personaje "comandando" el ataque va en el JSON:
  "sounds": {"special": ["sounds/special_voz.mp3"], "special_sfx": [...]}
"""

import math
import os
import random
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SS = 2
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(HERE), "assets", "fonts", "Roboto-Black.ttf")
OUT = (16, 16, 20)

# ---------------------------------------------------------------------
# Configuración de juego de cada especial (va al JSON, bloque "special")
# ---------------------------------------------------------------------
SPECIALS = {
    "milei": {"_que_es": "Un león aparece desde atrás (fuera de pantalla) y cruza corriendo a ras del piso.",
              "type": "rush", "spawn": "offscreen", "draw_h": 125, "hit_w": 130, "hit_h": 100, "speed": 13,
              "fx": {"main": 4}, "fx_fps": 12, "sfx_on": "spawn"},
    "cristina": {"_que_es": "Baja un satélite hasta la altura de los nombres y dispara lásers al rival (se esquivan moviéndose).",
                 "type": "satellite", "draw_h": 70, "hover_y": 88, "shots": 3, "aim_time": 0.55, "lock_time": 0.35, "beam_time": 0.28,
                 "beam_w": 46, "fx": {"main": 2}, "fx_fps": 6, "sfx_on": "fire"},
    "bullrich": {"_que_es": "Tira una bomba que explota a los 2 segundos con daño en área.",
                 "type": "bomb", "draw_h": 46, "throw_range": 260, "fuse": 2.0, "radius": 150,
                 "fx": {"main": 2}, "fx_fps": 8, "sfx_on": "explode"},
    "macri": {"_que_es": "Una ola de agua sale desde atrás suyo y cruza todo el escenario.",
              "type": "rush", "spawn": "behind", "draw_h": 140, "hit_w": 140, "hit_h": 100, "speed": 11,
              "fx": {"main": 4}, "fx_fps": 10, "sfx_on": "spawn"},
    "massa": {"_que_es": "Una ola de billetes de pesos sale desde atrás suyo y cruza todo el escenario.",
              "type": "rush", "spawn": "behind", "draw_h": 140, "hit_w": 140, "hit_h": 100, "speed": 11,
              "fx": {"main": 4}, "fx_fps": 10, "sfx_on": "spawn"},
    "bregman": {"_que_es": "Aparece un tanque detrás de ella, dispara un cohete hacia adelante y se vuelve a ir (el cohete se esquiva agachándose).",
                "type": "tank", "draw_h": 130, "hit_w": 230, "behind_offset": 160, "speed": 9,
                "rocket_height": 150, "rocket_speed": 13, "fx": {"main": 2, "rocket": 2}, "fx_fps": 10, "sfx_on": "fire"},
    "kicillof": {"_que_es": "Una movilización de la UOCRA arrasa desde atrás suyo corriendo hacia el otro extremo.",
                 "type": "rush", "spawn": "offscreen", "draw_h": 150, "hit_w": 200, "hit_h": 110, "speed": 12,
                 "fx": {"main": 4}, "fx_fps": 10, "sfx_on": "spawn"},
    "alberto": {"_que_es": "PROVISORIO (a definir): una ola de notas musicales desde atrás suyo.",
                "type": "rush", "spawn": "behind", "draw_h": 120, "hit_w": 140, "hit_h": 100, "speed": 11,
                "fx": {"main": 4}, "fx_fps": 10, "sfx_on": "spawn"},
    "scioli": {"_que_es": "PROVISORIO (a definir): una lancha cruza a toda velocidad.",
               "type": "rush", "spawn": "offscreen", "draw_h": 110, "hit_w": 150, "hit_h": 90, "speed": 15,
               "fx": {"main": 2}, "fx_fps": 10, "sfx_on": "spawn"},
}

FX_KIND = {"milei": "lion", "cristina": "satellite", "bullrich": "bomb", "macri": "water", "massa": "money",
           "bregman": "tank", "kicillof": "crowd", "alberto": "notes", "scioli": "boat"}


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def P(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def ell(self, x0, y0, x1, y1, fill, ow=4):
        if ow:
            self.d.ellipse([(x0 - ow) * SS, (y0 - ow) * SS, (x1 + ow) * SS, (y1 + ow) * SS], fill=OUT)
        self.d.ellipse([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill)

    def poly(self, pts, fill, ow=4):
        self.d.polygon(self.P(pts), fill=fill, outline=OUT if ow else None, width=ow * SS if ow else 0)

    def line(self, pts, fill, w):
        self.d.line(self.P(pts), fill=OUT, width=(w + 6) * SS, joint="curve")
        self.d.line(self.P(pts), fill=fill, width=w * SS, joint="curve")

    def rect(self, x0, y0, x1, y1, fill, ow=4, r=0):
        if ow:
            self.d.rounded_rectangle([(x0 - ow) * SS, (y0 - ow) * SS, (x1 + ow) * SS, (y1 + ow) * SS], r * SS, fill=OUT)
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], r * SS, fill=fill)

    def text(self, xy, s, size, fill):
        f = font(size * SS)
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=fill, anchor="mm")

    def done(self):
        im = self.img.resize((self.w, self.h), Image.LANCZOS)
        bb = im.getbbox()
        return im.crop((bb[0], bb[1], bb[2], im.height)) if bb else im  # recorta a los costados y arriba; el piso queda abajo


# ---------------------------------------------------------------------
# Dibujos (todos mirando a la DERECHA, apoyados abajo)
# ---------------------------------------------------------------------
def lion(i):
    c = Canvas(420, 260)
    gy = 250
    ph = i * math.pi / 2
    body = (196, 150, 70)
    # patas (de atrás oscuras)
    for k, (bx, off) in enumerate([(130, 0), (290, math.pi), (150, math.pi), (310, 0)]):
        a = math.sin(ph + off) * 0.6
        col = body if k >= 2 else (160, 118, 50)
        c.line([(bx, 170), (bx + math.sin(a) * 50, gy - 8)], col, 26)
    c.line([(90, 150), (40, 110), (25, 140)], body, 14)  # cola
    c.ell(18, 128, 44, 154, (110, 60, 20), 3)
    c.ell(80, 110, 340, 200, body)
    c.ell(270, 60, 410, 200, (150, 80, 25))   # melena
    c.ell(300, 95, 390, 175, body)            # cara
    c.ell(355, 135, 392, 165, (230, 200, 150), 3)
    c.ell(360, 112, 374, 126, OUT, 0)
    c.poly([(384, 140), (398, 146), (384, 152)], (60, 30, 20), 0)
    c.line([(352, 160), (390, 160)], (60, 30, 20), 3)
    return c.done()


def satellite(i):
    c = Canvas(300, 150)
    c.rect(20, 50, 110, 100, (40, 70, 160), 4, 4)
    c.rect(190, 50, 280, 100, (40, 70, 160), 4, 4)
    for x in range(30, 110, 20):
        c.d.line([(x * SS, 52 * SS), (x * SS, 98 * SS)], fill=(120, 160, 240), width=2 * SS)
    for x in range(200, 280, 20):
        c.d.line([(x * SS, 52 * SS), (x * SS, 98 * SS)], fill=(120, 160, 240), width=2 * SS)
    c.line([(110, 75), (190, 75)], (150, 150, 160), 8)
    c.rect(115, 40, 185, 110, (200, 200, 210), 4, 8)
    c.ell(130, 100, 170, 140, (230, 230, 240))
    c.ell(145, 112, 155, 122, (255, 60, 60) if i == 0 else (120, 20, 20), 0)
    c.text((150, 70), "AR", 18, (60, 140, 220))
    return c.done()


def bomb(i):
    c = Canvas(130, 150)
    c.ell(15, 40, 115, 140, (30, 30, 36))
    c.ell(35, 58, 55, 78, (110, 110, 120), 0)
    c.rect(52, 26, 78, 46, (80, 80, 90), 3, 3)
    c.line([(65, 26), (75, 10), (90, 6)], (150, 120, 80), 4)
    sc = (255, 220, 60) if i == 0 else (255, 120, 30)
    for k in range(6):
        a = k * math.pi / 3 + i * 0.5
        c.d.line([(90 * SS, 6 * SS), ((90 + math.cos(a) * 12) * SS, (6 + math.sin(a) * 12) * SS)], fill=sc, width=3 * SS)
    return c.done()


def wave_shape(c, col, foam, i, w=420, h=300):
    gy = h - 4
    pts = [(0, gy)]
    for x in range(0, w + 1, 10):
        t = x / w
        y = gy - (40 + 190 * t ** 1.6) - 10 * math.sin(x / 25 + i * 1.5)
        pts.append((x, y))
    pts += [(w - 10, gy - 200), (w - 4, gy - 120), (w, gy)]
    c.poly(pts, col)
    # rulo de espuma
    for k in range(9):
        a = math.pi * 0.2 + k * 0.32 + i * 0.1
        r = 18 + (k % 3) * 6
        cx = w - 70 + math.cos(a) * 55
        cy = gy - 215 + math.sin(a) * 40
        c.ell(cx - r, cy - r, cx + r, cy + r, foam, 0)


def water(i):
    c = Canvas(420, 300)
    wave_shape(c, (40, 120, 210), (235, 248, 255), i)
    for k in range(5):
        x = 60 + k * 70 + (i * 15) % 70
        c.d.arc([(x - 30) * SS, 200 * SS, (x + 30) * SS, 240 * SS], 200, 340, fill=(160, 210, 250), width=4 * SS)
    return c.done()


def money(i):
    c = Canvas(420, 300)
    wave_shape(c, (120, 150, 110), (210, 230, 200), i)
    rnd = random.Random(10 + i)
    cols = [(110, 160, 110), (120, 110, 170), (190, 120, 90), (90, 150, 190)]
    for k in range(26):
        x = rnd.randint(30, 400)
        maxh = 40 + 200 * (x / 420) ** 1.6
        y = 296 - rnd.uniform(10, maxh)
        ang = rnd.uniform(-35, 35)
        bill = Image.new("RGBA", (70 * SS, 34 * SS), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bill)
        col = rnd.choice(cols)
        bd.rounded_rectangle([0, 0, 70 * SS - 1, 34 * SS - 1], 4 * SS, fill=col, outline=OUT, width=3 * SS)
        bd.ellipse([24 * SS, 6 * SS, 46 * SS, 28 * SS], outline=(240, 240, 220), width=2 * SS)
        bd.text((35 * SS, 17 * SS), "$", font=font(18 * SS), fill=(250, 250, 230), anchor="mm")
        bill = bill.rotate(ang, expand=True, resample=Image.BICUBIC)
        c.img.alpha_composite(bill, (int((x - 35) * SS), int((y - 17) * SS)))
    return c.done()


def notes(i):
    c = Canvas(380, 260)
    rnd = random.Random(30 + i)
    for k in range(10):
        x = rnd.randint(20, 340)
        y = rnd.randint(40, 230)
        col = rnd.choice([(250, 200, 60), (120, 180, 240), (240, 240, 250)])
        c.ell(x, y, x + 34, y + 26, col, 4)
        c.line([(x + 31, y + 12), (x + 31, y - 50)], col, 5)
        if k % 2:
            c.line([(x + 31, y - 50), (x + 55, y - 35)], col, 5)
    return c.done()


def tank(i):
    c = Canvas(460, 260)
    olive = (90, 100, 60)
    c.rect(20, 160, 420, 245, (50, 50, 50), 4, 40)           # orugas
    for k in range(8):
        x = 55 + k * 47 + (i * 12)
        c.ell(x - 18, 182, x + 18, 218, (110, 110, 110), 3)
    c.poly([(30, 165), (60, 120), (390, 120), (430, 165)], olive)
    c.rect(130, 70, 300, 125, olive, 4, 20)                   # torreta
    c.rect(290, 85, 455, 105, (70, 80, 50), 4, 4)             # cañón
    c.poly([(205, 82), (212, 100), (230, 100), (215, 110), (221, 128), (205, 117), (189, 128), (195, 110), (180, 100), (198, 100)], (210, 30, 30), 0)
    return c.done()


def rocket(i):
    c = Canvas(160, 60)
    c.poly([(30, 18), (120, 18), (150, 30), (120, 42), (30, 42)], (200, 200, 205))
    c.poly([(30, 18), (12, 6), (40, 18)], (180, 30, 30))
    c.poly([(30, 42), (12, 54), (40, 42)], (180, 30, 30))
    fl = (255, 200, 40) if i == 0 else (255, 120, 20)
    c.poly([(28, 22), (0 + i * 6, 30), (28, 38)], fl, 0)
    return c.done()


def crowd(i):
    c = Canvas(520, 300)
    gy = 296
    rnd = random.Random(7)
    people = [(60 + k * 82 + rnd.randint(-12, 12), rnd.uniform(0.85, 1.05)) for k in range(6)]
    for k, (x, s) in enumerate(people):
        ph = i * math.pi / 2 + k * 1.3
        h = 230 * s
        top = gy - h
        a = math.sin(ph) * 0.5
        skin = rnd.choice([(230, 190, 150), (200, 150, 110), (170, 120, 90)])
        c.line([(x, top + h * 0.62), (x + math.sin(a) * 30, gy - 6)], (40, 70, 140), 16)
        c.line([(x, top + h * 0.62), (x - math.sin(a) * 30, gy - 6)], (30, 55, 115), 16)
        c.rect(x - 22, top + h * 0.25, x + 22, top + h * 0.65, (50, 90, 170), 4, 8)
        c.line([(x + 10, top + h * 0.3), (x + 34, top + h * 0.12 + math.sin(ph) * 10)], skin, 10)
        c.ell(x - 20, top + 30, x + 20, top + 70, skin)
        c.poly([(x - 26, top + 44), (x - 20, top + 22), (x + 20, top + 22), (x + 26, top + 44)], (250, 210, 30))
        if k == 2:
            c.line([(x + 34, top + 30), (x + 34, top - 70)], (120, 90, 60), 5)
            c.rect(x + 36, top - 70, x + 136, top - 18, (240, 240, 240), 4, 2)
            c.text((x + 86, top - 44), "UOCRA", 20, (30, 60, 150))
    return c.done()


def boat(i):
    c = Canvas(420, 220)
    c.poly([(20, 140), (380, 140), (410, 110), (330, 110), (300, 80), (200, 80), (180, 110), (40, 110)], (240, 120, 30))
    c.poly([(20, 140), (380, 140), (360, 175), (60, 175)], (250, 250, 250))
    c.rect(210, 90, 290, 110, (120, 180, 230), 3, 4)
    for k in range(5):
        x = 30 + k * 30 - i * 10
        c.ell(x - 20, 175 + (k % 2) * 6, x + 20, 205, (220, 240, 255), 0)
    c.ell(-10, 170, 60, 215, (200, 230, 255), 0)
    return c.done()


DRAW = {"lion": lion, "satellite": satellite, "bomb": bomb, "water": water, "money": money,
        "tank": tank, "crowd": crowd, "notes": notes, "boat": boat}


def make_fx(slug, base):
    kind = FX_KIND[slug]
    cfg = SPECIALS[slug]
    for part, count in cfg["fx"].items():
        folder = os.path.join(base, "special_fx", part)
        os.makedirs(folder, exist_ok=True)
        fn = rocket if part == "rocket" else DRAW[kind]
        for i in range(count):
            fn(i).save(os.path.join(folder, f"{i}.png"), optimize=True)


# ---------------------------------------------------------------------
# Sonidos provisorios (sintetizados)
# ---------------------------------------------------------------------
SR = 22050


def _env(n, a=0.02, r=0.4):
    t = np.arange(n) / SR
    dur = n / SR
    e = np.minimum(1, t / a) * np.clip((dur - t) / r, 0, 1)
    return e


def _noise(n, seed=0):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def sfx(kind):
    if kind == "lion":
        n = int(SR * 1.3); t = np.arange(n) / SR
        f = 90 + 40 * np.sin(t * 9)
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + _lowpass(_noise(n, 1), 6) * 0.8
        x = _lowpass(x, 5) * _env(n, 0.15, 0.6)
    elif kind == "satellite":
        n = int(SR * 0.35); t = np.arange(n) / SR
        f = 2400 - 1900 * t / t[-1]
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.005, 0.2)
    elif kind == "bomb":
        n = int(SR * 1.2)
        x = _lowpass(_noise(n, 2), 12) * 2.5 * np.exp(-np.arange(n) / SR * 4)
    elif kind in ("water", "money"):
        n = int(SR * 1.6); t = np.arange(n) / SR
        k = 4 if kind == "water" else 2
        x = _lowpass(_noise(n, 3), k) * np.sin(np.pi * t / t[-1]) ** 1.5
        if kind == "money":
            x *= (1 + 0.8 * np.sign(np.sin(2 * np.pi * 22 * t)))
    elif kind == "tank":
        n = int(SR * 0.9)
        x = _lowpass(_noise(n, 4), 8) * 2 * np.exp(-np.arange(n) / SR * 6) + _lowpass(_noise(n, 5), 3) * 0.4 * _env(n, 0.01, 0.6)
    elif kind == "crowd":
        n = int(SR * 1.8); t = np.arange(n) / SR
        x = _lowpass(_noise(n, 6), 10) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 1.7 * t))) * _env(n, 0.2, 0.5) * 1.5
    elif kind == "notes":
        n = int(SR * 1.2); t = np.arange(n) / SR
        x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 3) for f in (196, 247, 294, 392)) * 0.3
    else:  # boat
        n = int(SR * 1.4); t = np.arange(n) / SR
        x = np.sign(np.sin(2 * np.pi * (70 + 30 * t) * t)) * 0.3 + _lowpass(_noise(n, 8), 4) * 0.4
        x = _lowpass(x, 4) * _env(n, 0.1, 0.5)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.85
    return (x * 32767).astype(np.int16)


def make_sfx(slug, base):
    folder = os.path.join(base, "sounds")
    os.makedirs(folder, exist_ok=True)
    data = sfx(FX_KIND[slug])
    path = os.path.join(folder, "special_sfx.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return "sounds/special_sfx.wav"
