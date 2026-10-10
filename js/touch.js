// =====================================================================
// touch.js — controles táctiles para celular (joystick + botones)
// Izquierda: joystick flotante (aparece donde apoyás el dedo).
// Derecha: Puño, Patada, Distancia, Bloqueo y Especial (con carga).
// Solo se muestran en las pantallas de pelea; en los menús se toca
// directo la opción.
// =====================================================================
import * as C from "./config.js";
import { text } from "./ui.js";

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

  layoutFor(view) {
    const s = this.scale;
    const R = 36 * s;
    const w = view.w;
    const by = C.BASE_H - 70 * s;
    const bx = w - 66 * s;
    this.R = R;
    this.btnPos = {
      block: { x: bx, y: by - 70 * s },
      kick: { x: bx - 82 * s, y: by + 8 * s },
      punch: { x: bx - 164 * s, y: by - 40 * s },
      ranged: { x: bx - 82 * s, y: by - 96 * s },
      special: { x: bx - 2 * s, y: by - 168 * s },
    };
    this.pausePos = { x: view.w / 2, y: 108, r: 20 };
    this.joyZone = { x: 0, y: 120, w: w * 0.45, h: C.BASE_H - 120 };
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
    // pausa
    const pp = this.pausePos;
    ctx.globalAlpha = 0.75;
    ctx.beginPath(); ctx.arc(pp.x, pp.y, pp.r, 0, Math.PI * 2);
    ctx.fillStyle = "#1c1c24"; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = "#fff"; ctx.stroke();
    ctx.fillStyle = "#fff";
    ctx.fillRect(pp.x - 7, pp.y - 8, 5, 16); ctx.fillRect(pp.x + 2, pp.y - 8, 5, 16);
    // joystick
    if (this.joy) {
      ctx.globalAlpha = 0.35;
      ctx.beginPath(); ctx.arc(this.joy.bx, this.joy.by, this.R * 1.4, 0, Math.PI * 2);
      ctx.fillStyle = "#fff"; ctx.fill();
      const dx = this.joy.x - this.joy.bx, dy = this.joy.y - this.joy.by;
      const d = Math.hypot(dx, dy), m = Math.min(d, this.R * 1.4);
      const kx = this.joy.bx + (d ? (dx / d) * m : 0), ky = this.joy.by + (d ? (dy / d) * m : 0);
      ctx.globalAlpha = 0.7;
      ctx.beginPath(); ctx.arc(kx, ky, this.R * 0.7, 0, Math.PI * 2); ctx.fill();
    } else {
      ctx.globalAlpha = 0.18;
      ctx.beginPath(); ctx.arc(110, C.BASE_H - 110, this.R * 1.4, 0, Math.PI * 2);
      ctx.fillStyle = "#fff"; ctx.fill();
      ctx.globalAlpha = 0.5;
      text(ctx, "MOVER", 110, C.BASE_H - 110, { size: 13, shadow: false });
    }
    // botones
    const pressed = new Set([...this.pointers.values()].filter((p) => p.kind === "btn").map((p) => p.a));
    for (const b of BUTTONS) {
      const p = this.btnPos[b.a];
      const on = pressed.has(b.a);
      const ready = b.a !== "special" || this.specialCharge >= C.SPECIAL_HITS_REQUIRED;
      ctx.globalAlpha = on ? 0.9 : ready ? 0.62 : 0.32;
      ctx.beginPath(); ctx.arc(p.x, p.y, this.R * (on ? 0.92 : 1), 0, Math.PI * 2);
      ctx.fillStyle = b.color; ctx.fill();
      ctx.lineWidth = 3; ctx.strokeStyle = "rgba(255,255,255,0.9)"; ctx.stroke();
      if (b.a === "special") {
        const frac = Math.min(1, this.specialCharge / C.SPECIAL_HITS_REQUIRED);
        ctx.globalAlpha = 0.95;
        ctx.beginPath();
        ctx.arc(p.x, p.y, this.R + 6, -Math.PI / 2, -Math.PI / 2 + frac * Math.PI * 2);
        ctx.lineWidth = 5; ctx.strokeStyle = ready ? "#ffe060" : "#fff"; ctx.stroke();
      }
      ctx.globalAlpha = ready ? 1 : 0.6;
      text(ctx, ready || b.a !== "special" ? b.label : "🔒", p.x, p.y + 1, { size: 13 * this.scale, shadow: false });
    }
    ctx.restore();
  }
}
