// =====================================================================
// touch.js — controles táctiles para celular (joystick + botones)
// Izquierda: joystick flotante (aparece donde apoyás el dedo).
// Derecha: Puño, Patada, Distancia, Bloqueo y Especial (con carga).
// Solo se muestran en las pantallas de pelea; en los menús se toca
// directo la opción.
// =====================================================================
import * as C from "./config.js";
import { text, IMG } from "./ui.js";

export const IS_TOUCH_DEVICE = (() => {
  const coarse = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
  return !!(coarse || ("ontouchstart" in window && navigator.maxTouchPoints > 0));
})();

const BUTTONS = [
  { a: "punch", label: "PUÑO", color: "#d84a3a" },
  { a: "kick", label: "PATADA", color: "#3a8ad8" },
  { a: "ranged", label: "DIST.", color: "#3aa860" },
  { a: "block", label: "BLOQ.", color: "#8a8a96" },
  { a: "special", label: "ESP.", color: "#e0a020" },
];

export class TouchControls {
  constructor() {
    this.pointers = new Map(); // id -> {kind:'joy'|'btn', ...}
    this.joy = null;           // {bx, by, x, y, id}
    this.fightMode = false;
    this.visible = false;
    this.pauseTapped = false;
    this.edges = new Set();   // botones tocados desde el último cuadro (toques cortísimos)
    this.specialCharge = 0;
    this.scale = 1;
    this.layoutFor({ w: C.BASE_W, pad: 0 });
  }

  // Posiciones en coordenadas del lienzo COMPLETO (en vertical el juego
  // ocupa la franja de arriba y los controles van en la zona de abajo).
  layoutFor(view) {
    const s = this.scale;
    const w = view.w;
    let u, cx, cy, joyHome, joyZone, pause;
    if (view.portrait) {
      const top = view.oy + C.BASE_H + 20;
      const A = Math.max(200, view.fullH - top - 20);
      u = Math.min((A * 0.8) / 250, (w * 0.56) / 240) * s;
      cx = w * 0.70; cy = top + Math.min(A * 0.58, A - 140 * u);
      joyHome = { x: w * 0.22, y: cy + 20 * u };
      joyZone = { x: 0, y: top - 10, w: w * 0.48, h: A + 30 };
      pause = { x: w / 2, y: top + Math.min(70, A * 0.12), r: 22 * u };
    } else {
      u = s;
      cx = w - 66 * u - 82 * u; cy = C.BASE_H - 70 * u - 80 * u;
      joyHome = { x: 110, y: C.BASE_H - 110 };
      joyZone = { x: 0, y: 120, w: w * 0.45, h: C.BASE_H - 120 };
      pause = { x: w / 2, y: 108, r: 20 };
    }
    const bx = cx + 82 * u, by = cy + 80 * u;
    this.R = 36 * u;
    this.btnPos = {
      block: { x: bx, y: by - 70 * u },
      kick: { x: bx - 82 * u, y: by + 8 * u },
      punch: { x: bx - 164 * u, y: by - 40 * u },
      ranged: { x: bx - 82 * u, y: by - 96 * u },
      special: { x: bx - 2 * u, y: by - 168 * u },
    };
    this.pausePos = pause;
    this.joyZone = joyZone;
    this.joyHome = joyHome;
    this.portrait = !!view.portrait;
    this.view = view;
  }

  buttonAt(x, y) {
    let best = null, bestD = Infinity;
    for (const b of BUTTONS) {
      const p = this.btnPos[b.a];
      const d = Math.hypot(x - p.x, y - p.y);
      if (d < this.R * 1.25 && d < bestD) { best = b.a; bestD = d; }
    }
    return best;
  }

  down(id, x, y) {
    if (!this.visible || !this.fightMode) return false;
    if (Math.hypot(x - this.pausePos.x, y - this.pausePos.y) < this.pausePos.r * 1.6) {
      this.pauseTapped = true;
      return true;
    }
    const b = this.buttonAt(x, y);
    if (b) { this.pointers.set(id, { kind: "btn", a: b }); this.edges.add(b); return true; }
    const z = this.joyZone;
    if (x >= z.x && x <= z.x + z.w && y >= z.y) {
      this.joy = { id, bx: x, by: y, x, y };
      this.pointers.set(id, { kind: "joy" });
      return true;
    }
    return false;
  }

  move(id, x, y) {
    const p = this.pointers.get(id);
    if (!p) return;
    if (p.kind === "joy" && this.joy) {
      this.joy.x = x; this.joy.y = y;
      // el centro "persigue" al dedo si se aleja mucho
      const R = this.R * 1.4;
      const dx = x - this.joy.bx, dy = y - this.joy.by;
      const d = Math.hypot(dx, dy);
      if (d > R * 1.6) { this.joy.bx = x - (dx / d) * R * 1.6; this.joy.by = y - (dy / d) * R * 1.6; }
    } else if (p.kind === "btn") {
      const b = this.buttonAt(x, y);
      if (b) p.a = b;
    }
  }

  up(id) {
    const p = this.pointers.get(id);
    if (p && p.kind === "joy") this.joy = null;
    this.pointers.delete(id);
  }

  releaseAll() { this.pointers.clear(); this.joy = null; }

  isPressed(action) {
    if (!this.visible || !this.fightMode) return false;
    if (action === "start" && this.pauseTapped) return true;
    if (this.edges.has(action)) return true;
    for (const p of this.pointers.values()) if (p.kind === "btn" && p.a === action) return true;
    if (this.joy) {
      const dx = this.joy.x - this.joy.bx, dy = this.joy.y - this.joy.by;
      const dz = this.R * 0.45;
      if (action === "left") return dx < -dz;
      if (action === "right") return dx > dz;
      if (action === "up") return dy < -dz * 1.3 && Math.abs(dy) > Math.abs(dx) * 0.6;
      if (action === "down") return dy > dz * 1.3 && Math.abs(dy) > Math.abs(dx) * 0.6;
    }
    return false;
  }

  endFrame() { this.pauseTapped = false; this.edges.clear(); }

  draw(ctx) {
    if (!this.visible || !this.fightMode) return;
    ctx.save();
    const img = (k, x, y, size, alpha) => {
      const im = IMG[k];
      if (!im) return false;
      ctx.globalAlpha = alpha;
      ctx.drawImage(im, x - size / 2, y - size / 2, size, size);
      return true;
    };
    // pausa
    const pp = this.pausePos;
    if (!img("t_pause", pp.x, pp.y, pp.r * 2, 0.8)) {
      ctx.globalAlpha = 0.75;
      ctx.beginPath(); ctx.arc(pp.x, pp.y, pp.r, 0, Math.PI * 2);
      ctx.fillStyle = "#1c1c24"; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = "#fff"; ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.fillRect(pp.x - 7, pp.y - 8, 5, 16); ctx.fillRect(pp.x + 2, pp.y - 8, 5, 16);
    }
    // joystick (aparece donde apoyás el dedo; si no, queda de guía en su lugar)
    const jr = this.R * 1.4;
    const base = this.joy ? { x: this.joy.bx, y: this.joy.by } : this.joyHome;
    let kx = base.x, ky = base.y;
    if (this.joy) {
      const dx = this.joy.x - this.joy.bx, dy = this.joy.y - this.joy.by;
      const d = Math.hypot(dx, dy), m = Math.min(d, jr);
      kx += d ? (dx / d) * m : 0; ky += d ? (dy / d) * m : 0;
    }
    const ja = this.joy ? 0.85 : 0.45;
    if (!img("t_joy_base", base.x, base.y, jr * 2, ja)) {
      ctx.globalAlpha = ja * 0.5;
      ctx.beginPath(); ctx.arc(base.x, base.y, jr, 0, Math.PI * 2);
      ctx.fillStyle = "#fff"; ctx.fill();
    }
    if (!img("t_joy_knob", kx, ky, jr, ja)) {
      ctx.globalAlpha = ja;
      ctx.beginPath(); ctx.arc(kx, ky, jr * 0.5, 0, Math.PI * 2);
      ctx.fillStyle = "#fff"; ctx.fill();
    }
    // botones
    const pressed = new Set([...this.pointers.values()].filter((p) => p.kind === "btn").map((p) => p.a));
    for (const b of BUTTONS) {
      const p = this.btnPos[b.a];
      const on = pressed.has(b.a);
      const ready = b.a !== "special" || this.specialCharge >= C.SPECIAL_HITS_REQUIRED;
      const r = this.R * (on ? 0.92 : 1);
      const key = b.a === "special" ? (ready ? "t_special" : "t_special_locked") : "t_" + b.a;
      if (b.a === "special" && ready) {
        // brillo del especial habilitado
        ctx.globalAlpha = 0.35 + 0.25 * Math.sin(performance.now() / 150);
        ctx.beginPath(); ctx.arc(p.x, p.y, this.R * 1.25, 0, Math.PI * 2);
        ctx.fillStyle = "#ffd040"; ctx.fill();
      }
      if (!img(key, p.x, p.y, r * 2, on ? 1 : 0.7)) {
        ctx.globalAlpha = on ? 0.9 : ready ? 0.62 : 0.32;
        ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = b.color; ctx.fill();
        ctx.lineWidth = 3; ctx.strokeStyle = "rgba(255,255,255,0.9)"; ctx.stroke();
        ctx.globalAlpha = 1;
        text(ctx, b.label, p.x, p.y + 1, { size: 13 * (this.R / 36), shadow: false });
      }
      if (b.a === "special" && !ready) {
        // aro de carga de 5 partes
        ctx.globalAlpha = 0.95;
        ctx.lineWidth = Math.max(4, this.R * 0.13);
        const n = C.SPECIAL_HITS_REQUIRED, gap = 0.12;
        for (let i = 0; i < n; i++) {
          const a0 = -Math.PI / 2 + (i / n) * Math.PI * 2 + gap / 2;
          const a1 = -Math.PI / 2 + ((i + 1) / n) * Math.PI * 2 - gap / 2;
          ctx.beginPath(); ctx.arc(p.x, p.y, this.R + ctx.lineWidth, a0, a1);
          ctx.strokeStyle = i < this.specialCharge ? "#ffd040" : "rgba(255,255,255,0.3)";
          ctx.stroke();
        }
      }
    }
    ctx.restore();
  }
}
