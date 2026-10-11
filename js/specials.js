// =====================================================================
// specials.js — ataques especiales "externos" (invocaciones)
// ---------------------------------------------------------------------
// El luchador hace un gesto de mando (animación "special") y en el
// cuadro activo aparece algo que ataca solo: un león, una ola, un
// satélite, una bomba, un tanque... Pega UNA sola vez:
//   - 17% de la vida del rival (C.SPECIAL_SUMMON_DAMAGE)
//   - 4% si se está cubriendo (C.SPECIAL_SUMMON_BLOCKED)
//   - se puede esquivar (saltando, agachándose o alejándose, según el tipo)
//
// Tipos (JSON del personaje, bloque "special"):
//   "rush"      algo corre a ras del piso y cruza toda la pantalla.
//               "spawn": "offscreen" (entra desde el borde de atrás) o
//               "behind" (nace justo detrás del luchador, ej. una ola).
//   "satellite" baja hasta la altura de los nombres, apunta al rival y
//               dispara lásers verticales (se esquiva moviéndose).
//   "bomb"      se lanza hacia adelante, cae y explota a los N segundos
//               con daño en área.
//   "tank"      entra un tanque por detrás, dispara un cohete recto y se
//               vuelve a ir (el cohete se esquiva agachándose o saltando).
//
// Sprites: assets/characters/<nombre>/special_fx/<parte>/0.png, 1.png...
// (partes: "main" siempre; "rocket" para el tanque). Si falta un sprite
// se dibuja una forma de reemplazo.
// =====================================================================
import * as C from "./config.js";
import { audio } from "./audio.js";

let SEQ = 0;

function overlap(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function circleRect(cx, cy, r, b) {
  const nx = Math.max(b.x, Math.min(cx, b.x + b.w));
  const ny = Math.max(b.y, Math.min(cy, b.y + b.h));
  return (cx - nx) ** 2 + (cy - ny) ** 2 <= r * r;
}

export class Summon {
  /**
   * @param {object} cfg    bloque "special" del JSON del personaje
   * @param {Character} owner
   * @param {Character} target
   * @param {number} ownerIndex  0/1
   * @param {number} cameraX
   */
  constructor(cfg, owner, target, ownerIndex, cameraX) {
    this.id = ++SEQ;
    this.cfg = cfg;
    this.type = cfg.type || "rush";
    this.owner = owner;
    this.target = target;
    this.o = ownerIndex;
    this.dir = owner.facing;
    this.t = 0;
    this.fi = 0;           // cuadro de animación del sprite principal
    this.ft = 0;
    this.alive = true;
    this.hit = false;
    this.phase = "go";
    this.cam = cameraX;
    this.y = C.GROUND_Y;
    this.dh = cfg.draw_h ?? 120;       // alto de dibujo del sprite principal
    this.hw = cfg.hit_w ?? this.dh;    // caja de golpe
    this.hh = cfg.hit_h ?? this.dh * 0.85;
    const fx = owner.data.special && owner.data.special.fx;
    this.fxCounts = fx || {};

    if (this.type === "rush") {
      if (cfg.spawn === "behind") this.x = owner.x - this.dir * (cfg.behind_offset ?? 70);
      else this.x = this.dir === 1 ? cameraX - this.hw : cameraX + C.BASE_W + this.hw;
      this.speed = cfg.speed ?? 12;
      this.sfx("spawn");
    } else if (this.type === "satellite") {
      this.x = target.x;
      this.y = -60;
      this.hoverY = cfg.hover_y ?? 88;
      this.shots = cfg.shots ?? 3;
      this.aim = cfg.aim_time ?? 0.55;
      this.beamT = cfg.beam_time ?? 0.28;
      this.beamW = cfg.beam_w ?? 46;
      this.phase = "descend";
      this.sfx("spawn");
    } else if (this.type === "bomb") {
      const dist = Math.abs(target.x - owner.x);
      const range = Math.max(90, Math.min(cfg.throw_range ?? 260, dist));
      this.x = owner.x + this.dir * 30;
      this.y = owner.y - 110;
      this.startX = this.x;
      this.endX = owner.x + this.dir * range;
      this.flyT = 0;
      this.flyDur = 0.55;
      this.fuse = cfg.fuse ?? 2.0;
      this.radius = cfg.radius ?? 150;
      this.phase = "fly";
      this.sfx("spawn");
    } else if (this.type === "tank") {
      this.stopX = owner.x - this.dir * (cfg.behind_offset ?? 150);
      // que el tanque quede siempre dentro de la pantalla
      this.stopX = Math.max(cameraX + this.dh * 0.6, Math.min(cameraX + C.BASE_W - this.dh * 0.6, this.stopX));
      this.x = this.dir === 1 ? cameraX - this.hw : cameraX + C.BASE_W + this.hw;
      this.speed = cfg.speed ?? 9;
      this.phase = "enter";
      this.rocket = null;
      this.sfx("spawn");
    }
  }

  sfx(when) {
    const s = this.cfg.sfx_on || "spawn";
    if (s !== when) return;
    const path = this.owner.characterSoundPath("special_sfx");
    if (path) audio.play(path, 1);
  }

  landHit(target) {
    if (this.hit || target.knockedOut) return;
    this.hit = true;
    const blocked = target.blocking;
    target.receiveSpecial(blocked ? C.SPECIAL_SUMMON_BLOCKED : C.SPECIAL_SUMMON_DAMAGE, this.dir);
    if (!blocked) audio.playSfx("special_hit", 1);
  }

  // ---------------------------------------------------------------
  update(dt, cameraX) {
    this.t += dt;
    this.cam = cameraX;
    const fps = this.cfg.fx_fps ?? 12;
    const n = this.fxCounts.main || 1;
    this.ft += dt;
    if (this.ft >= 1 / fps) { this.ft = 0; this.fi = (this.fi + 1) % n; }
    const tgt = this.target;
    const hurt = tgt.getHurtbox();

    if (this.type === "rush") {
      this.x += this.speed * this.dir;
      if (!this.hit && overlap(this.hitbox(), hurt)) this.landHit(tgt);
      const left = cameraX - this.hw * 1.5, right = cameraX + C.BASE_W + this.hw * 1.5;
      if ((this.dir === 1 && this.x > right) || (this.dir === -1 && this.x < left)) this.finish();
    } else if (this.type === "satellite") {
      if (this.phase === "descend") {
        this.y += 7;
        this.x += (tgt.x - this.x) * 0.06;
        if (this.y >= this.hoverY) { this.y = this.hoverY; this.phase = "aim"; this.pt = 0; }
      } else if (this.phase === "aim") {
        this.pt += dt;
        this.x += (tgt.x - this.x) * 0.05;   // sigue al rival, con retraso
        if (this.pt >= this.aim) { this.phase = "lock"; this.pt = 0; this.beamX = this.x; }
      } else if (this.phase === "lock") {
        // mira fija un instante antes del disparo: ahí se esquiva
        this.pt += dt;
        if (this.pt >= (this.cfg.lock_time ?? 0.35)) { this.phase = "beam"; this.pt = 0; this.sfx("fire"); }
      } else if (this.phase === "beam") {
        this.pt += dt;
        const beam = { x: this.beamX - this.beamW / 2, y: this.y, w: this.beamW, h: C.GROUND_Y - this.y };
        if (!this.hit && overlap(beam, hurt)) this.landHit(tgt);
        if (this.pt >= this.beamT) {
          this.shots -= 1;
          this.phase = this.hit || this.shots <= 0 ? "leave" : "aim";
          this.pt = 0;
        }
      } else if (this.phase === "leave") {
        this.y -= 9;
        if (this.y < -80) this.finish();
      }
    } else if (this.type === "bomb") {
      if (this.phase === "fly") {
        this.flyT += dt;
        const k = Math.min(1, this.flyT / this.flyDur);
        this.x = this.startX + (this.endX - this.startX) * k;
        this.y = (this.owner.y - 110) + (C.GROUND_Y - (this.owner.y - 110)) * k - 120 * 4 * k * (1 - k);
        if (k >= 1) { this.phase = "fuse"; this.y = C.GROUND_Y; }
      }
      this.fuse -= dt;
      if (this.phase !== "boom" && this.fuse <= 0) {
        this.phase = "boom";
        this.pt = 0;
        this.sfx("explode");
        audio.playSfx("fall_thud", 1);
        const cy = C.GROUND_Y - 30;
        if (circleRect(this.x, cy, this.radius, hurt)) this.landHit(tgt);
      }
      if (this.phase === "boom") {
        this.pt += dt;
        if (this.pt > 0.55) this.finish();
      }
    } else if (this.type === "tank") {
      if (this.phase === "enter") {
        this.x += this.speed * this.dir;
        if ((this.dir === 1 && this.x >= this.stopX) || (this.dir === -1 && this.x <= this.stopX)) {
          this.x = this.stopX; this.phase = "fire"; this.pt = 0;
        }
      } else if (this.phase === "fire") {
        this.pt += dt;
        if (!this.rocket && this.pt > 0.25) {
          this.rocket = { x: this.x + this.dir * this.dh * 0.9, y: C.GROUND_Y - (this.cfg.rocket_height ?? 150), w: 64, h: 26 };
          this.sfx("fire");
        }
        if (this.pt > 0.7) this.phase = "leave";
      } else if (this.phase === "leave") {
        this.x -= this.speed * this.dir;
        const off = this.dir === 1 ? this.x < cameraX - this.hw * 2 : this.x > cameraX + C.BASE_W + this.hw * 2;
        if (off && !this.rocket) this.finish();
      }
      if (this.rocket) {
        const r = this.rocket;
        r.x += (this.cfg.rocket_speed ?? 13) * this.dir;
        const rb = { x: r.x - r.w / 2, y: r.y - r.h / 2, w: r.w, h: r.h };
        if (!this.hit && overlap(rb, hurt)) { this.landHit(tgt); this.rocket = null; }
        else if (r.x < cameraX - 200 || r.x > cameraX + C.BASE_W + 200) this.rocket = null;
        if (!this.rocket && this.phase === "leave") {
          const off = this.dir === 1 ? this.x < cameraX - this.hw * 2 : this.x > cameraX + C.BASE_W + this.hw * 2;
          if (off) this.finish();
        }
      }
    }
  }

  finish() {
    if (!this.alive) return;
    this.alive = false;
    if (!this.hit) audio.playSfx("special_miss", 1);
  }

  hitbox() {
    return { x: this.x - this.hw / 2, y: C.GROUND_Y - this.hh, w: this.hw, h: this.hh };
  }

  // estado plano para dibujar (local y online)
  snap() {
    const r1 = (v) => Math.round(v * 10) / 10;
    const s = [this.o, this.type, r1(this.x), r1(this.y), this.fi, this.dir, this.phase, r1(this.pt || 0)];
    if (this.type === "satellite") s.push(r1(this.beamX ?? this.x));
    if (this.type === "bomb") s.push(r1(Math.max(0, this.fuse)));
    if (this.type === "tank") s.push(this.rocket ? [r1(this.rocket.x), r1(this.rocket.y)] : null);
    return s;
  }
}

// ---------------------------------------------------------------------
// Dibujo (a partir de snap(): sirve también para el invitado online)
// ---------------------------------------------------------------------
function drawSprite(ctx, img, x, yBottom, h, dir, alpha = 1) {
  const w = (img.naturalWidth / img.naturalHeight) * h;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(x, yBottom);
  if (dir === -1) ctx.scale(-1, 1);
  ctx.drawImage(img, -w / 2, -h, w, h);
  ctx.restore();
}

export function drawSummon(ctx, s, owner, cam, pad) {
  const [, type, wx, wy, fi, dir, phase, pt] = s;
  const cfg = (owner.data.special) || {};
  const fx = owner.specialFx || {};
  const main = fx.main && fx.main.length ? fx.main[fi % fx.main.length] : null;
  const x = wx - cam + pad;
  const dh = cfg.draw_h ?? 120;
  const color = owner.data.accent || "#f0c828";

  if (type === "rush" || type === "tank") {
    if (main) drawSprite(ctx, main, x, wy, dh, dir);
    else { ctx.fillStyle = color; ctx.fillRect(x - dh / 2, wy - dh * 0.8, dh, dh * 0.8); }
    if (type === "tank") {
      const r = s[8];
      if (r) {
        const rx = r[0] - cam + pad;
        const rk = fx.rocket && fx.rocket.length ? fx.rocket[Math.floor(performance.now() / 80) % fx.rocket.length] : null;
        if (rk) drawSprite(ctx, rk, rx, r[1] + 16, 32, dir);
        else { ctx.fillStyle = "#ddd"; ctx.fillRect(rx - 30, r[1] - 10, 60, 20); }
      }
      if (phase === "fire" && pt > 0.25 && pt < 0.45) {
        ctx.save(); ctx.globalAlpha = 0.85; ctx.fillStyle = "#ffcf40";
        ctx.beginPath(); ctx.arc(x + dir * dh * 0.95, C.GROUND_Y - (cfg.rocket_height ?? 150), 26, 0, Math.PI * 2); ctx.fill(); ctx.restore();
      }
    }
    return;
  }

  if (type === "satellite") {
    const bx = s[8] - cam + pad;
    if (phase === "lock") {
      ctx.save();
      ctx.globalAlpha = 0.9;
      ctx.strokeStyle = "#ff2020"; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(bx, wy + 20); ctx.lineTo(bx, C.GROUND_Y); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(bx, C.GROUND_Y - 4, 34, 9, 0, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
    } else if (phase === "aim") {
      // mira: línea punteada roja que sigue al rival
      ctx.save();
      ctx.globalAlpha = 0.5 + 0.4 * Math.sin(performance.now() / 60);
      ctx.strokeStyle = "#ff3030"; ctx.lineWidth = 3; ctx.setLineDash([10, 10]);
      ctx.beginPath(); ctx.moveTo(x, wy + 20); ctx.lineTo(x, C.GROUND_Y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.beginPath(); ctx.ellipse(x, C.GROUND_Y - 4, 34, 9, 0, 0, Math.PI * 2); ctx.stroke();
      ctx.restore();
    } else if (phase === "beam") {
      const w = cfg.beam_w ?? 46;
      ctx.save();
      const g = ctx.createLinearGradient(bx - w / 2, 0, bx + w / 2, 0);
      g.addColorStop(0, "rgba(255,40,80,0)"); g.addColorStop(0.3, "rgba(255,60,100,0.9)");
      g.addColorStop(0.5, "rgba(255,255,255,1)"); g.addColorStop(0.7, "rgba(255,60,100,0.9)"); g.addColorStop(1, "rgba(255,40,80,0)");
      ctx.fillStyle = g;
      ctx.fillRect(bx - w / 2, wy + 10, w, C.GROUND_Y - wy - 10);
      ctx.restore();
    }
    if (main) drawSprite(ctx, main, x, wy + dh / 2, dh, 1);
    else { ctx.fillStyle = "#aab"; ctx.fillRect(x - 40, wy - 15, 80, 30); }
    return;
  }

  if (type === "bomb") {
    const fuse = s[8];
    if (phase !== "boom") {
      const blink = fuse < 2 && Math.floor(fuse * (fuse < 0.7 ? 12 : 5)) % 2 === 0;
      if (main) drawSprite(ctx, main, x, wy, dh, dir);
      else { ctx.fillStyle = "#222"; ctx.beginPath(); ctx.arc(x, wy - dh / 2, dh / 2, 0, Math.PI * 2); ctx.fill(); }
      if (blink) {
        ctx.save(); ctx.globalAlpha = 0.6; ctx.fillStyle = "#ff3030";
        ctx.beginPath(); ctx.arc(x, wy - dh * 0.45, dh * 0.42, 0, Math.PI * 2); ctx.fill(); ctx.restore();
      }
      if (phase === "fuse") {
        // círculo del área de la explosión
        ctx.save(); ctx.globalAlpha = 0.25 + 0.15 * Math.sin(performance.now() / 90);
        ctx.strokeStyle = "#ff4040"; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.ellipse(x, C.GROUND_Y - 2, cfg.radius ?? 150, 18, 0, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
      }
    } else {
      const r = (cfg.radius ?? 150) * (0.5 + pt * 1.4);
      ctx.save();
      ctx.globalAlpha = Math.max(0, 1 - pt / 0.55);
      const g = ctx.createRadialGradient(x, C.GROUND_Y - 30, 5, x, C.GROUND_Y - 30, r);
      g.addColorStop(0, "#fff8c0"); g.addColorStop(0.35, "#ffb030"); g.addColorStop(0.7, "#e03010"); g.addColorStop(1, "rgba(60,20,10,0)");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(x, C.GROUND_Y - 30, r, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
  }
}
