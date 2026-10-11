"""
generar_placeholders.py
------------------------
Genera los sprites PROVISORIOS de Mortal Kompa Político: un maniquí
dibujado por código para cada político (con su color, pelo, saco...),
con todas las animaciones que usa el motor, más los retratos, los
proyectiles y los escenarios de prueba.

Uso (desde la carpeta del juego):
    python tools/generar_placeholders.py            -> genera todo
    python tools/generar_placeholders.py milei      -> solo ese personaje
    python tools/generar_placeholders.py --stages   -> solo escenarios

Cuando tengas el arte real de un personaje, reemplazá los PNG de
assets/characters/<nombre>/<animación>/0.png, 1.png... y actualizá
"frames" en data/characters/<nombre>.json con la cantidad real de
cuadros (el navegador no puede listar carpetas, por eso el JSON dice
cuántos hay). Este script NO pisa un personaje cuyo JSON tenga
"placeholder": false.

Requiere Pillow (pip install pillow).
"""

import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import especiales_placeholder as SP  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_ASSETS = os.path.join(ROOT, "assets", "characters")
CHAR_DATA = os.path.join(ROOT, "data", "characters")
STAGES_DIR = os.path.join(ROOT, "assets", "stages")
FONT_PATH = os.path.join(ROOT, "assets", "fonts", "Roboto-Black.ttf")

SS = 2              # supersampling
CANVAS = 640        # lienzo final de cada cuadro (px)
JSON_SCALE = 0.5    # el motor dibuja a scale * 0.9 -> ~230 px base de alto

# Medidas del maniquí (px del lienzo final, de pie ~505 px)
HEAD_R = 37
NECK = 12
TORSO = 165
UPPER_ARM = 92
FOREARM = 86
THIGH = 122
SHIN = 122
ARM_W = 30
LEG_W = 38
SHOULDER_W = 96
HIP_W = 76
OUTLINE = 5

# ---------------------------------------------------------------------
# Roster provisorio. Los colores/pelo son solo para distinguirlos hasta
# que llegue el arte real.
# ---------------------------------------------------------------------
ROSTER = [
    dict(slug="milei", name="Milei", skin=(236, 196, 160), hair=(92, 58, 34), hair_style="melena",
         sideburns=True, jacket=(30, 30, 34), shirt=(240, 240, 240), tie=(118, 60, 170), pants=(30, 30, 34),
         accent=(150, 80, 220), trajectory="bounce"),
    dict(slug="cristina", name="Cristina", skin=(232, 190, 158), hair=(60, 36, 24), hair_style="largo",
         jacket=(24, 24, 28), shirt=(24, 24, 28), tie=None, pants=(24, 24, 28),
         accent=(90, 170, 230), trajectory="straight"),
    dict(slug="alberto", name="Alberto", skin=(230, 192, 162), hair=(170, 170, 170), hair_style="pelado",
         mustache=True, glasses=True, jacket=(70, 74, 82), shirt=(220, 230, 240), tie=(90, 150, 210), pants=(60, 62, 70),
         accent=(120, 170, 220), trajectory="arc"),
    dict(slug="kicillof", name="Kicillof", skin=(228, 186, 152), hair=(40, 30, 24), hair_style="corto",
         sideburns=True, jacket=(96, 62, 38), shirt=(200, 210, 220), tie=None, pants=(50, 54, 70),
         accent=(70, 140, 200), trajectory="straight"),
    dict(slug="macri", name="Macri", skin=(238, 200, 170), hair=(196, 196, 190), hair_style="corto",
         jacket=None, shirt=(160, 200, 236), tie=None, pants=(60, 64, 80),
         accent=(250, 210, 40), trajectory="arc"),
    dict(slug="scioli", name="Scioli", skin=(226, 182, 150), hair=(200, 200, 200), hair_style="corto",
         jacket=(30, 40, 70), shirt=(240, 240, 240), tie=(240, 130, 30), pants=(30, 40, 70),
         accent=(250, 140, 40), trajectory="straight"),
    dict(slug="bregman", name="Bregman", skin=(236, 198, 168), hair=(120, 60, 40), hair_style="largo",
         jacket=None, shirt=(200, 30, 40), tie=None, pants=(40, 40, 50),
         accent=(230, 40, 50), trajectory="straight"),
    dict(slug="massa", name="Massa", skin=(230, 190, 158), hair=(70, 66, 64), hair_style="corto",
         jacket=(28, 36, 64), shirt=(230, 236, 246), tie=(80, 140, 220), pants=(28, 36, 64),
         accent=(60, 120, 220), trajectory="bounce"),
    dict(slug="bullrich", name="Bullrich", skin=(236, 200, 172), hair=(220, 200, 150), hair_style="carre",
         jacket=(150, 150, 156), shirt=(250, 250, 250), tie=None, pants=(90, 90, 96),
         accent=(250, 200, 40), trajectory="straight"),
]


def darker(c, f=0.55):
    return tuple(max(0, int(v * f)) for v in c)


def lighter(c, f=0.35):
    return tuple(min(255, int(v + (255 - v) * f)) for v in c)


def vec(angle_deg, length):
    """Ángulo medido desde 'hacia abajo', positivo hacia ADELANTE (+x).
    0 = abajo, 90 = adelante, 180 = arriba, -90 = atrás."""
    a = math.radians(angle_deg)
    return (math.sin(a) * length, math.cos(a) * length)


def add(p, v):
    return (p[0] + v[0], p[1] + v[1])


# ---------------------------------------------------------------------
# Dibujo del maniquí
# ---------------------------------------------------------------------
class Painter:
    def __init__(self, size):
        self.img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def S(self, v):
        return v * SS

    def P(self, p):
        return (p[0] * SS, p[1] * SS)

    def capsule(self, a, b, width, color, outline=True):
        w = self.S(width)
        o = self.S(OUTLINE)
        pa, pb = self.P(a), self.P(b)
        if outline:
            self.d.line([pa, pb], fill=(16, 16, 20), width=int(w + 2 * o))
            for p in (pa, pb):
                r = (w + 2 * o) / 2
                self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(16, 16, 20))
        self.d.line([pa, pb], fill=color, width=int(w))
        for p in (pa, pb):
            r = w / 2
            self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)

    def circle(self, c, r, color, outline=True):
        pc = self.P(c)
        rr = self.S(r)
        if outline:
            o = self.S(OUTLINE)
            self.d.ellipse([pc[0] - rr - o, pc[1] - rr - o, pc[0] + rr + o, pc[1] + rr + o], fill=(16, 16, 20))
        self.d.ellipse([pc[0] - rr, pc[1] - rr, pc[0] + rr, pc[1] + rr], fill=color)

    def poly(self, pts, color, outline=True):
        pp = [self.P(p) for p in pts]
        if outline:
            self.d.polygon(pp, fill=color, outline=(16, 16, 20), width=int(self.S(OUTLINE)))
        else:
            self.d.polygon(pp, fill=color)


def default_pose():
    return dict(lean=4, fa=(25, 150), ba=(12, 140), fl=(14, 4), bl=(-12, -6), head=0, effect=None,
                eyes="open", lying=False)


def draw_figure(ch, pose, origin=(0, 0)):
    """Dibuja el maniquí en un lienzo grande y devuelve (imagen, hip_x).
    origin = posición de la cadera."""
    big = CANVAS * 2
    pt = Painter(big * SS)
    hip = (big / 2 + origin[0], big / 2 + origin[1])

    lean = pose["lean"]
    up = vec(180 - lean, TORSO)           # de la cadera al cuello
    neck = add(hip, up)
    perp = (math.cos(math.radians(lean)), math.sin(math.radians(lean)))  # "adelante" del torso
    shoulder_f = add(neck, (perp[0] * 10, perp[1] * 10 + 14))
    shoulder_b = add(neck, (-perp[0] * 10, -perp[1] * 10 + 14))
    hip_f = add(hip, (perp[0] * 8, 0))
    hip_b = add(hip, (-perp[0] * 8, 0))

    def limb(start, angles, l1, l2):
        knee = add(start, vec(angles[0], l1))
        end = add(knee, vec(angles[1], l2))
        return knee, end

    fk, ff = limb(hip_f, pose["fl"], THIGH, SHIN)
    bk, bf = limb(hip_b, pose["bl"], THIGH, SHIN)
    fe, fh = limb(shoulder_f, pose["fa"], UPPER_ARM, FOREARM)
    be, bh = limb(shoulder_b, pose["ba"], UPPER_ARM, FOREARM)

    jacket = ch["jacket"] or ch["shirt"]
    sleeve = jacket
    pants = ch["pants"]
    shoe = (26, 22, 20)

    def foot(knee, end, color):
        # zapato apuntando hacia adelante respecto de la pierna
        d = (end[0] - knee[0], end[1] - knee[1])
        n = math.hypot(*d) or 1
        fwd = (d[1] / n, -d[0] / n)  # perpendicular
        if fwd[0] < 0:
            fwd = (-fwd[0], -fwd[1])
        tip = add(end, (fwd[0] * 26, fwd[1] * 26))
        pt.capsule(end, tip, 22, color)

    # pierna de atrás, brazo de atrás (más oscuros)
    pt.capsule(hip_b, bk, LEG_W, darker(pants, 0.8))
    pt.capsule(bk, bf, LEG_W - 4, darker(pants, 0.8))
    foot(bk, bf, shoe)
    pt.capsule(shoulder_b, be, ARM_W, darker(sleeve, 0.8))
    pt.capsule(be, bh, ARM_W - 4, darker(sleeve, 0.8))
    pt.circle(bh, 15, darker(ch["skin"], 0.9))

    # torso (trapecio)
    def tp(base, along, side):
        return add(base, (perp[0] * side, perp[1] * side))

    torso_pts = [
        tp(hip, 0, -HIP_W / 2), tp(hip, 0, HIP_W / 2),
        tp(add(neck, (0, 6)), 0, SHOULDER_W / 2), tp(add(neck, (0, 6)), 0, -SHOULDER_W / 2),
    ]
    pt.poly(torso_pts, jacket)
    # camisa / corbata (franja frontal)
    if ch["jacket"]:
        mid_top = add(neck, (perp[0] * 22, perp[1] * 22 + 8))
        mid_bot = add(hip, (perp[0] * 22, perp[1] * 22 - 40))
        pt.poly([add(mid_top, (-12, 0)), add(mid_top, (12, 0)), add(mid_bot, (4, 0)), add(mid_bot, (-4, 0))],
                ch["shirt"], outline=False)
        if ch.get("tie"):
            pt.poly([add(mid_top, (-5, 2)), add(mid_top, (5, 2)), add(mid_bot, (6, -10)), add(mid_bot, (0, 4)),
                     add(mid_bot, (-6, -10))], ch["tie"], outline=False)
    # cinturón
    pt.capsule(tp(hip, 0, -HIP_W / 2 + 6), tp(hip, 0, HIP_W / 2 - 6), 10, darker(pants, 0.6), outline=False)

    # pierna de adelante
    pt.capsule(hip_f, fk, LEG_W, pants)
    pt.capsule(fk, ff, LEG_W - 4, pants)
    foot(fk, ff, shoe)

    # cabeza
    head_c = add(neck, vec(180 - lean - pose["head"], NECK + HEAD_R))
    draw_head(pt, ch, head_c, lean + pose["head"], pose["eyes"])

    # brazo de adelante (por encima de todo)
    pt.capsule(shoulder_f, fe, ARM_W, sleeve)
    pt.capsule(fe, fh, ARM_W - 4, sleeve)
    pt.circle(fh, 16, ch["skin"])

    if pose.get("effect") == "glow":
        r = 46
        glow = Image.new("RGBA", pt.img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        c = pt.P(fh)
        col = ch["accent"]
        for i in range(6, 0, -1):
            rr = pt.S(r * i / 6 + 10)
            gd.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=col + (int(40 + 18 * (6 - i)),))
        glow = glow.filter(ImageFilter.GaussianBlur(pt.S(6)))
        pt.img = Image.alpha_composite(pt.img, glow)
    elif pose.get("effect") == "foot_glow":
        glow = Image.new("RGBA", pt.img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        c = pt.P(ff)
        col = ch["accent"]
        for i in range(6, 0, -1):
            rr = pt.S(50 * i / 6 + 10)
            gd.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=col + (int(40 + 18 * (6 - i)),))
        glow = glow.filter(ImageFilter.GaussianBlur(pt.S(6)))
        pt.img = Image.alpha_composite(pt.img, glow)

    return pt.img, hip


def draw_head(pt, ch, c, tilt, eyes):
    skin = ch["skin"]
    hair = ch["hair"]
    style = ch["hair_style"]
    r = HEAD_R
    # pelo largo por detrás de la cabeza
    if style == "largo":
        pt.poly([add(c, (-r - 6, -r * 0.5)), add(c, (r * 0.2, -r - 4)), add(c, (r * 0.5, r * 0.4)),
                 add(c, (-r * 0.6, r * 2.2)), add(c, (-r * 1.25, r * 1.6))], hair)
    if style == "melena":
        pts = []
        for i in range(11):
            a = math.radians(-200 + i * 22)
            rad = r + (16 if i % 2 == 0 else 4)
            pts.append(add(c, (math.cos(a) * rad - 6, math.sin(a) * rad - 4)))
        pts.append(add(c, (-r * 0.9, r * 1.1)))
        pt.poly(pts, hair)
    # oreja + cara
    pt.circle(c, r, skin)
    pt.circle(add(c, (-r * 0.25, 2)), 9, darker(skin, 0.85), outline=False)
    # pelo de arriba
    if style in ("corto", "carre", "largo", "melena"):
        top = [add(c, (-r - 3, 4)), add(c, (-r - 2, -r * 0.6)), add(c, (-r * 0.2, -r - 6)),
               add(c, (r * 0.75, -r * 0.75)), add(c, (r * 0.95, -r * 0.25)), add(c, (r * 0.3, -r * 0.5)),
               add(c, (-r * 0.4, -r * 0.35)), add(c, (-r * 0.55, 6))]
        if style == "carre":
            top += [add(c, (-r * 0.8, r * 0.9)), add(c, (-r - 6, r * 0.8))]
            top = top[:8][::1]
            pt.poly([add(c, (-r - 6, r * 0.9)), add(c, (-r - 4, -r * 0.6)), add(c, (-r * 0.2, -r - 7)),
                     add(c, (r * 0.85, -r * 0.7)), add(c, (r * 1.0, -r * 0.1)), add(c, (r * 0.3, -r * 0.45)),
                     add(c, (-r * 0.4, -r * 0.2)), add(c, (-r * 0.45, r * 0.9))], hair)
        else:
            pt.poly(top, hair)
    elif style == "pelado":
        pt.poly([add(c, (-r - 2, 6)), add(c, (-r, -r * 0.35)), add(c, (-r * 0.55, -r * 0.2)), add(c, (-r * 0.5, 8))], hair)
    if ch.get("sideburns"):
        pt.poly([add(c, (r * 0.15, -r * 0.2)), add(c, (r * 0.35, -r * 0.2)), add(c, (r * 0.32, r * 0.5)),
                 add(c, (r * 0.18, r * 0.5))], hair, outline=False)
    # ojo
    ex, ey = c[0] + r * 0.55, c[1] - r * 0.12
    if eyes == "x":
        s = 7
        pt.d.line([pt.P((ex - s, ey - s)), pt.P((ex + s, ey + s))], fill=(16, 16, 20), width=pt.S(4))
        pt.d.line([pt.P((ex - s, ey + s)), pt.P((ex + s, ey - s))], fill=(16, 16, 20), width=pt.S(4))
    elif eyes == "closed":
        pt.d.line([pt.P((ex - 7, ey)), pt.P((ex + 7, ey))], fill=(16, 16, 20), width=pt.S(4))
    else:
        pt.circle((ex, ey), 5, (16, 16, 20), outline=False)
    # ceja
    pt.d.line([pt.P((ex - 9, ey - 12)), pt.P((ex + 9, ey - 14))], fill=darker(hair, 0.7), width=pt.S(5))
    if ch.get("glasses"):
        pt.d.ellipse([pt.P((ex - 13, ey - 11)), pt.P((ex + 13, ey + 11))], outline=(16, 16, 20), width=pt.S(4))
        pt.d.line([pt.P((ex - 13, ey)), pt.P((c[0] - r * 0.2, ey - 2))], fill=(16, 16, 20), width=pt.S(3))
    # nariz
    pt.poly([add(c, (r * 0.92, -r * 0.05)), add(c, (r * 1.12, r * 0.22)), add(c, (r * 0.9, r * 0.28))],
            darker(skin, 0.92), outline=False)
    if ch.get("mustache"):
        pt.poly([add(c, (r * 0.5, r * 0.38)), add(c, (r * 1.02, r * 0.36)), add(c, (r * 0.95, r * 0.52)),
                 add(c, (r * 0.5, r * 0.55))], darker(hair, 0.75), outline=False)
    # boca
    pt.d.line([pt.P((c[0] + r * 0.55, c[1] + r * 0.6)), pt.P((c[0] + r * 0.85, c[1] + r * 0.58))],
              fill=(120, 50, 50), width=pt.S(4))


def render_frame(ch, pose):
    img, hip = draw_figure(ch, pose)
    small = img.resize((img.width // SS, img.height // SS), Image.LANCZOS)
    hip = (hip[0], hip[1])
    bbox = small.getbbox()
    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    if not bbox:
        return out
    # ancla: cadera centrada en X, borde inferior del contenido abajo de todo
    dx = int(round(CANVAS / 2 - hip[0]))
    if pose.get("lying"):
        dx = int(round(CANVAS / 2 - (bbox[0] + bbox[2]) / 2))
    dy = int(round(CANVAS - 2 - bbox[3]))
    out.paste(small, (dx, dy), small)
    return out


def P(**kw):
    p = default_pose()
    p.update(kw)
    return p


# ---------------------------------------------------------------------
# Animaciones (poses por cuadro)
# ---------------------------------------------------------------------
def animations():
    A = {}
    A["idle"] = [P(lean=4), P(lean=6, fa=(28, 152), ba=(14, 142)), P(lean=5, fa=(26, 148))]
    A["walk"] = [
        P(lean=8, fl=(28, 10), bl=(-22, -30)),
        P(lean=9, fl=(8, -8), bl=(2, -20)),
        P(lean=8, fl=(-22, -30), bl=(28, 10)),
        P(lean=9, fl=(2, -20), bl=(8, -8)),
    ]
    A["jump"] = [
        P(lean=14, fl=(60, -10), bl=(40, -40)),
        P(lean=10, fl=(80, -40), bl=(60, -60), fa=(60, 160)),
        P(lean=10, fl=(85, -30), bl=(70, -50), fa=(70, 170)),
        P(lean=6, fl=(30, 10), bl=(-10, -10)),
    ]
    A["punch"] = [
        P(lean=8, fa=(10, 150), ba=(30, 150)),
        P(lean=16, fa=(66, 66), ba=(10, 150), fl=(24, 6), bl=(-20, -8)),
        P(lean=18, fa=(70, 70), ba=(8, 150), fl=(26, 6), bl=(-22, -8)),
        P(lean=10, fa=(40, 120), ba=(12, 145)),
    ]
    A["kick"] = [
        P(lean=-6, fl=(50, -10), fa=(40, 160)),
        P(lean=-14, fl=(80, 40), bl=(-4, -4), fa=(50, 160), ba=(-30, 120)),
        P(lean=-18, fl=(76, 76), bl=(-6, -6), fa=(50, 160), ba=(-40, 120)),
        P(lean=-6, fl=(40, 0), fa=(35, 150)),
    ]
    # especial = gesto de MANDO (señala hacia adelante); el ataque lo hace
    # la invocación (ver tools/especiales_placeholder.py y js/specials.js)
    A["special"] = [
        P(lean=-6, fa=(-30, 100), ba=(10, 140)),
        P(lean=-10, fa=(140, 175), ba=(5, 130), head=-6),
        P(lean=6, fa=(92, 96), ba=(0, 150), fl=(22, 4), bl=(-18, -8)),
        P(lean=6, fa=(94, 98), ba=(0, 150), fl=(22, 4), bl=(-18, -8)),
    ]
    A["ranged"] = [
        P(lean=-6, fa=(-60, -160), ba=(30, 150)),
        P(lean=-10, fa=(-120, 170), ba=(40, 150)),
        P(lean=16, fa=(80, 86), ba=(10, 140), fl=(24, 6), bl=(-20, -8)),
        P(lean=10, fa=(55, 60), ba=(12, 145)),
    ]
    crouch_legs = dict(fl=(84, 0), bl=(36, -82))
    A["ranged_crouch"] = [
        P(lean=10, fa=(-60, -160), **crouch_legs),
        P(lean=8, fa=(-110, 170), **crouch_legs),
        P(lean=24, fa=(84, 88), **crouch_legs),
        P(lean=18, fa=(60, 70), **crouch_legs),
    ]
    A["crouch"] = [P(lean=16, fa=(40, 150), **crouch_legs), P(lean=18, fa=(42, 152), **crouch_legs)]
    A["block"] = [P(lean=-2, fa=(70, 178), ba=(60, 172)), P(lean=-3, fa=(72, 180), ba=(62, 174))]
    A["block_crouch"] = [P(lean=12, fa=(70, 178), ba=(60, 172), **crouch_legs),
                         P(lean=13, fa=(72, 180), ba=(62, 174), **crouch_legs)]
    A["ko"] = [
        P(lean=-20, fa=(-60, -40), ba=(-80, -60), head=-10, eyes="closed"),
        P(lean=-45, fa=(-100, -80), ba=(-120, -90), fl=(40, 30), bl=(20, 10), head=-15, eyes="closed"),
        P(lean=-70, fa=(-130, -120), ba=(-140, -130), fl=(70, 60), bl=(50, 40), head=-10, eyes="x"),
        P(lean=-88, fa=(-150, -150), ba=(-160, -160), fl=(84, 88), bl=(80, 92), head=0, eyes="x", lying=True),
        P(lean=-90, fa=(-170, -170), ba=(-176, -176), fl=(88, 92), bl=(86, 94), head=0, eyes="x", lying=True),
        P(lean=-90, fa=(-176, -176), ba=(-178, -178), fl=(90, 92), bl=(88, 94), head=0, eyes="x", lying=True),
    ]
    A["win"] = [
        P(lean=0, fa=(160, 175), ba=(-160, -175), eyes="closed"),
        P(lean=0, fa=(170, 178), ba=(-170, -178), fl=(30, 10), bl=(-20, -20), eyes="closed"),
        P(lean=0, fa=(160, 175), ba=(-160, -175)),
        P(lean=2, fa=(150, 170), ba=(-150, -170), fl=(20, -10), bl=(-10, -30)),
    ]
    return A


# Config de juego por animación (calibrada sobre el lienzo base 960x540,
# mismos valores que los personajes de Mortal Kompa)
def anim_config(ch, frames_count):
    traj = ch["trajectory"]
    ranged = {"fps": 14, "loop": False, "damage": 4, "active_frames": [2], "speed": 9,
              "launch_height": "mid", "projectile_mode": "spin", "trajectory": traj}
    if traj == "bounce":
        ranged.update({"launch_height": "low", "kick_height": 200, "gravity_mult": 5, "bounce_damping": 0.55})
    elif traj == "arc":
        ranged.update({"arc_height": 110, "arc_range": 320, "arc_end_height": "mid"})
    cfg = {
        "idle": {"fps": 6, "loop": True},
        "walk": {"fps": 10, "loop": True},
        "jump": {"fps": 8, "loop": False},
        "punch": {"fps": 16, "loop": False, "damage": 8, "reach": 95, "hit_height": 66, "hit_offset_y": 110,
                  "active_frames": [1, 2]},
        "kick": {"fps": 14, "loop": False, "damage": 12, "reach": 115, "hit_height": 72, "hit_offset_y": 83,
                 "active_frames": [2]},
        "special": {"fps": 8, "loop": False, "active_frames": [2],
                    "_comentario": "Gesto de mando: en el cuadro activo aparece la invocación (bloque 'special' del JSON)."},
        "ranged": ranged,
        "ranged_crouch": dict(ranged, launch_height="crouch_mid", trajectory="straight"),
        "crouch": {"fps": 6, "loop": True},
        "block": {"fps": 6, "loop": True},
        "block_crouch": {"fps": 6, "loop": True},
        "ko": {"fps": 6, "loop": False},
        "win": {"fps": 6, "loop": True},
    }
    if traj == "bounce":
        cfg["ranged_crouch"] = dict(ranged, launch_height="crouch_mid", trajectory="straight")
        for k in ("kick_height", "gravity_mult", "bounce_damping"):
            cfg["ranged_crouch"].pop(k, None)
    for k, n in frames_count.items():
        cfg[k]["frames"] = n
    return cfg


def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def make_portrait(ch, idle_img):
    """Retrato cuadrado para la grilla de selección (256x256)."""
    size = 256
    bg = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(bg)
    a = ch["accent"]
    for y in range(size):
        t = y / size
        col = tuple(int(lighter(a, 0.15)[i] * (1 - t) + darker(a, 0.35)[i] * t) for i in range(3))
        d.line([(0, y), (size, y)], fill=col + (255,))
    # recorte cabeza y hombros del idle
    bbox = idle_img.getbbox()
    top = bbox[1]
    crop = idle_img.crop((CANVAS / 2 - 150, top - 20, CANVAS / 2 + 150, top + 280))
    crop = crop.resize((size, int(size * 280 / 300) + 6), Image.LANCZOS)
    bg.alpha_composite(crop, (0, 18))
    return bg


def make_projectile(ch):
    frames = []
    a = ch["accent"]
    for i in range(4):
        s = 96
        img = Image.new("RGBA", (s * SS, s * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        r = 34 * SS
        c = s * SS / 2
        d.ellipse([c - r - 8, c - r - 8, c + r + 8, c + r + 8], fill=(16, 16, 20))
        d.ellipse([c - r, c - r, c + r, c + r], fill=a)
        ang = math.radians(i * 45)
        for k in (0, 1):
            aa = ang + k * math.pi / 2
            d.line([(c - math.cos(aa) * r, c - math.sin(aa) * r), (c + math.cos(aa) * r, c + math.sin(aa) * r)],
                   fill=lighter(a, 0.6), width=8 * SS)
        d.ellipse([c - r * 0.45, c - r * 0.45, c + r * 0.45, c + r * 0.45], fill=lighter(a, 0.8))
        f = font(30 * SS)
        letter = ch["name"][0]
        tw = d.textlength(letter, font=f)
        d.text((c - tw / 2, c - 19 * SS), letter, font=f, fill=darker(a, 0.5))
        frames.append(img.resize((s, s), Image.LANCZOS))
    return frames


def generate_character(ch):
    slug = ch["slug"]
    json_path = os.path.join(CHAR_DATA, f"{slug}.json")
    if os.path.isfile(json_path):
        with open(json_path, encoding="utf-8") as fh:
            existing = json.load(fh)
        if existing.get("placeholder") is False:
            print(f"  {slug}: tiene arte real (placeholder=false), no lo toco")
            return
    base = os.path.join(CHAR_ASSETS, slug)
    counts = {}
    idle0 = None
    for anim, poses in animations().items():
        folder = os.path.join(base, anim)
        os.makedirs(folder, exist_ok=True)
        for f in os.listdir(folder):
            if f.endswith(".png"):
                os.remove(os.path.join(folder, f))
        for i, pose in enumerate(poses):
            img = render_frame(ch, pose)
            if anim == "idle" and i == 0:
                idle0 = img
            img.save(os.path.join(folder, f"{i}.png"), optimize=True)
        counts[anim] = len(poses)
    make_portrait(ch, idle0).save(os.path.join(base, "selection.png"), optimize=True)
    pose_img = idle0.crop(idle0.getbbox())
    pose_img.save(os.path.join(base, "pose.png"), optimize=True)
    SP.make_fx(slug, base)
    sfx_path = SP.make_sfx(slug, base)
    pfolder = os.path.join(base, "projectile")
    os.makedirs(pfolder, exist_ok=True)
    for i, fr in enumerate(make_projectile(ch)):
        fr.save(os.path.join(pfolder, f"{i}.png"), optimize=True)

    data = {
        "_comentario": "Personaje PROVISORIO generado por tools/generar_placeholders.py. Cuando cargues el arte real, poné 'placeholder': false para que el script no lo pise, y ajustá 'frames' de cada animación a la cantidad real de PNG.",
        "placeholder": True,
        "name": ch["name"],
        "sprite_folder": f"assets/characters/{slug}",
        "scale": JSON_SCALE,
        "health": 100,
        "walk_speed": 4,
        "projectile_frames": 4,
        "projectile_scale": 0.5,
        "accent": "#%02x%02x%02x" % ch["accent"],
        "animations": anim_config(ch, counts),
        "special": SP.SPECIALS[slug],
        "sounds": {
            "_comentario": "special = voz del personaje comandando el ataque (grabala y ponela acá); special_sfx = efecto de la invocación (rugido, agua...).",
            "special_sfx": [sfx_path],
        },
    }
    os.makedirs(CHAR_DATA, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"  {slug}: ok")


# ---------------------------------------------------------------------
# Escenarios provisorios
# ---------------------------------------------------------------------
def vgrad(d, w, y0, y1, c0, c1):
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1))
        col = tuple(int(c0[i] * (1 - t) + c1[i] * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=col)


def ground_band(d, w, h, top_col, line_col, tile=None):
    gy = int(h * (495 / 540))
    vgrad(d, w, gy - 30, h, top_col, darker(top_col, 0.6))
    d.line([(0, gy), (w, gy)], fill=line_col, width=4)
    if tile:
        for x in range(0, w, tile):
            d.line([(x, gy), (x - 60, h)], fill=darker(top_col, 0.75), width=3)
    return gy


def stage_plaza(path):
    w, h = 3240, 1080
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    vgrad(d, w, 0, h, (120, 180, 235), (220, 236, 250))
    rnd = random.Random(3)
    for _ in range(14):  # nubes
        x, y = rnd.randint(0, w), rnd.randint(40, 300)
        for k in range(5):
            r = rnd.randint(40, 80)
            d.ellipse([x + k * 50 - r, y - r * 0.6, x + k * 50 + r, y + r * 0.6], fill=(250, 252, 255))
    gy = int(h * (495 / 540))
    # edificios de fondo
    for x in range(0, w, 260):
        bh = rnd.randint(260, 420)
        d.rectangle([x, gy - 120 - bh, x + 230, gy - 120], fill=(176, 186, 200))
        for wx in range(x + 20, x + 210, 40):
            for wy in range(gy - 100 - bh, gy - 140, 50):
                d.rectangle([wx, wy, wx + 18, wy + 28], fill=(150, 160, 178))
    # Casa Rosada (centro)
    cx = w // 2
    pink = (232, 160, 170)
    d.rectangle([cx - 700, gy - 470, cx + 700, gy - 60], fill=pink)
    d.rectangle([cx - 700, gy - 490, cx + 700, gy - 470], fill=darker(pink, 0.85))
    for ax in range(cx - 660, cx + 660, 110):
        for row in (0, 1):
            y0 = gy - 430 + row * 190
            d.rectangle([ax, y0 + 30, ax + 60, y0 + 140], fill=darker(pink, 0.6))
            d.pieslice([ax, y0, ax + 60, y0 + 60], 180, 360, fill=darker(pink, 0.6))
    d.rectangle([cx - 140, gy - 620, cx + 140, gy - 470], fill=pink)
    d.polygon([(cx - 170, gy - 620), (cx + 170, gy - 620), (cx, gy - 700)], fill=darker(pink, 0.85))
    d.rectangle([cx - 60, gy - 300, cx + 60, gy - 60], fill=darker(pink, 0.5))
    # balcón
    d.rectangle([cx - 120, gy - 330, cx + 120, gy - 310], fill=(240, 236, 230))
    # Pirámide de Mayo (izquierda)
    px = 700
    d.rectangle([px - 70, gy - 160, px + 70, gy - 60], fill=(236, 232, 222))
    d.polygon([(px - 40, gy - 160), (px + 40, gy - 160), (px + 18, gy - 520), (px - 18, gy - 520)], fill=(240, 236, 228))
    d.ellipse([px - 26, gy - 580, px + 26, gy - 520], fill=(240, 236, 228))
    # palmeras
    for tx in (300, 1200, 2050, 2950):
        d.rectangle([tx - 12, gy - 330, tx + 12, gy - 60], fill=(120, 90, 60))
        for k in range(7):
            a = math.radians(-160 + k * 23)
            d.line([(tx, gy - 330), (tx + math.cos(a) * 140, gy - 330 + math.sin(a) * 90 + 40)], fill=(60, 140, 70), width=22)
    ground_band(d, w, h, (190, 180, 168), (120, 110, 100), tile=160)
    img.save(path, optimize=True)


def stage_congreso(path):
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    vgrad(d, w, 0, h, (60, 40, 90), (250, 150, 90))
    d.ellipse([1280, 520, 1560, 800], fill=(255, 200, 120))
    gy = int(h * (495 / 540))
    cx = w // 2 - 120
    stone = (210, 200, 180)
    sh = darker(stone, 0.7)
    d.rectangle([cx - 520, gy - 360, cx + 520, gy - 60], fill=stone)
    for x in range(cx - 480, cx + 500, 80):
        d.rectangle([x, gy - 340, x + 34, gy - 90], fill=sh)
    d.rectangle([cx - 180, gy - 480, cx + 180, gy - 360], fill=stone)
    d.rectangle([cx - 120, gy - 600, cx + 120, gy - 480], fill=stone)
    d.pieslice([cx - 170, gy - 800, cx + 170, gy - 460], 180, 360, fill=(120, 150, 130))
    d.rectangle([cx - 14, gy - 860, cx + 14, gy - 790], fill=(120, 150, 130))
    d.ellipse([cx - 24, gy - 890, cx + 24, gy - 842], fill=(120, 150, 130))
    d.polygon([(cx - 240, gy - 360), (cx + 240, gy - 360), (cx, gy - 440)], fill=sh)
    # escalinata
    for i in range(6):
        d.rectangle([cx - 300 - i * 30, gy - 60 - i * 0, cx + 300 + i * 30, gy - 60 + 10], fill=darker(stone, 0.9 - i * 0.04))
    # árboles
    for tx in (200, 420, 1560, 1780):
        d.rectangle([tx - 10, gy - 200, tx + 10, gy - 40], fill=(70, 50, 40))
        d.ellipse([tx - 110, gy - 380, tx + 110, gy - 170], fill=(40, 80, 50))
    ground_band(d, w, h, (150, 140, 130), (90, 80, 70), tile=140)
    img.save(path, optimize=True)


def stage_obelisco(path):
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    vgrad(d, w, 0, h, (10, 14, 40), (50, 40, 90))
    rnd = random.Random(7)
    for _ in range(160):
        x, y = rnd.randint(0, w), rnd.randint(0, 500)
        d.point((x, y), fill=(240, 240, 255))
    gy = int(h * (495 / 540))
    for x in range(0, w, 150):
        bh = rnd.randint(200, 560)
        col = (26 + rnd.randint(0, 20), 26 + rnd.randint(0, 20), 50 + rnd.randint(0, 30))
        d.rectangle([x, gy - bh, x + 140, gy], fill=col)
        for wx in range(x + 14, x + 130, 28):
            for wy in range(gy - bh + 20, gy - 20, 36):
                if rnd.random() < 0.45:
                    d.rectangle([wx, wy, wx + 12, wy + 18], fill=(250, 220, 120))
    cx = w // 2
    d.polygon([(cx - 60, gy), (cx + 60, gy), (cx + 34, gy - 760), (cx - 34, gy - 760)], fill=(236, 232, 220))
    d.polygon([(cx - 34, gy - 760), (cx + 34, gy - 760), (cx, gy - 820)], fill=(236, 232, 220))
    d.rectangle([cx - 18, gy - 740, cx - 6, gy - 728], fill=(40, 40, 50))
    # carteles luminosos
    for bx, col in ((260, (230, 60, 80)), (1500, (60, 200, 230))):
        d.rectangle([bx, gy - 520, bx + 240, gy - 400], fill=col)
        d.rectangle([bx + 10, gy - 510, bx + 230, gy - 410], outline=(255, 255, 255), width=4)
    ground_band(d, w, h, (60, 60, 70), (230, 200, 60), tile=None)
    for x in range(0, w, 120):
        d.rectangle([x, gy + 30, x + 60, gy + 38], fill=(240, 240, 240))
    img.save(path, optimize=True)


def stage_olivos(path):
    w, h = 2400, 1080
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    vgrad(d, w, 0, h, (150, 200, 240), (230, 240, 230))
    gy = int(h * (495 / 540))
    rnd = random.Random(11)
    for x in range(-100, w, 140):
        r = rnd.randint(120, 200)
        d.ellipse([x - r, gy - 260 - r, x + r, gy - 260 + r], fill=(60 + rnd.randint(0, 30), 120 + rnd.randint(0, 40), 70))
    cx = w // 2
    wall = (240, 236, 226)
    d.rectangle([cx - 420, gy - 380, cx + 420, gy - 60], fill=wall)
    d.polygon([(cx - 460, gy - 380), (cx + 460, gy - 380), (cx + 380, gy - 470), (cx - 380, gy - 470)], fill=(150, 80, 70))
    for x in range(cx - 380, cx + 380, 95):
        d.rectangle([x, gy - 330, x + 50, gy - 230], fill=(90, 110, 130))
        d.rectangle([x, gy - 190, x + 50, gy - 90], fill=(90, 110, 130))
    d.rectangle([cx - 50, gy - 190, cx + 50, gy - 60], fill=(110, 70, 50))
    vgrad(d, w, gy - 60, gy, (90, 160, 80), (70, 140, 60))
    ground_band(d, w, h, (80, 150, 70), (50, 110, 40), tile=None)
    img.save(path, optimize=True)


def stage_destino(path):
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    vgrad(d, w, 0, h, (8, 4, 30), (60, 20, 90))
    rnd = random.Random(5)
    for _ in range(300):
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        s = rnd.choice((1, 1, 2, 3))
        d.ellipse([x, y, x + s, y + s], fill=(220, 220, 255))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w // 2 - 600, 100, w // 2 + 600, 800], fill=(140, 80, 255, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)
    gy = int(h * (495 / 540))
    d.polygon([(30, gy), (w - 30, gy), (w - 150, gy + 70), (150, gy + 70)], fill=(50, 50, 70))
    d.line([(30, gy), (w - 30, gy)], fill=(180, 160, 255), width=6)
    d.polygon([(150, gy + 70), (w - 150, gy + 70), (w // 2 + 200, h + 40), (w // 2 - 200, h + 40)], fill=(30, 30, 46))
    img.save(path, optimize=True)


STAGES = {
    "Plaza de Mayo": stage_plaza,
    "Congreso": stage_congreso,
    "Obelisco": stage_obelisco,
    "Quinta de Olivos": stage_olivos,
    "Destino Final": stage_destino,
}


def generate_stages():
    os.makedirs(STAGES_DIR, exist_ok=True)
    for name, fn in STAGES.items():
        fn(os.path.join(STAGES_DIR, f"{name}.png"))
        print(f"  escenario '{name}': ok")


def main():
    args = sys.argv[1:]
    only_stages = "--stages" in args
    names = [a for a in args if not a.startswith("--")]
    if not only_stages:
        for ch in ROSTER:
            if names and ch["slug"] not in names:
                continue
            generate_character(ch)
    if only_stages or not names:
        generate_stages()


if __name__ == "__main__":
    main()
