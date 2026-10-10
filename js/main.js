// =====================================================================
// main.js — arranque, lienzo, loop de 60 cuadros fijos y escenas
// =====================================================================
import * as C from "./config.js";
import { loadDatabase } from "./assets.js";
import { audio } from "./audio.js";
import { PlayerInput, CombinedInput, pollGamepads, endKeyboardFrame, gamepads, keyboard } from "./input.js";
import { TouchControls, IS_TOUCH_DEVICE } from "./touch.js";
import * as UI from "./ui.js";
import { loadSettings, saveSettings } from "./settings.js";
import { TitleScene } from "./scenes/menus.js";

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

export const app = {
  canvas, ctx,
  view: { w: C.BASE_W, h: C.BASE_H, pad: 0, scale: 1, ox: 0, oy: 0 },
  settings: loadSettings(),
  scene: null,
  t: 0,
  toastText: "", toastUntil: 0,
  touch: new TouchControls(),
  inputs: [],
  isTouchDevice: IS_TOUCH_DEVICE,
  inviteRoom: new URLSearchParams(location.search).get("sala"),
  lastTouchAt: 0,
};

app.inputs = [new PlayerInput(0, app.settings, app.touch), new PlayerInput(1, app.settings, null)];
// "menú": cualquiera de los dos jugadores locales puede navegar
app.menuInput = app.inputs[0];
app.anyInput = new CombinedInput(app.inputs[0], app.inputs[1]);

app.setScene = (scene) => {
  if (app.scene && app.scene.exit) app.scene.exit();
  app.scene = scene;
  app.touch.releaseAll();
  if (scene && scene.enter) scene.enter();
};
app.toast = (msg, secs = 3.5) => { app.toastText = msg; app.toastUntil = performance.now() + secs * 1000; };
app.saveSettings = () => {
  saveSettings(app.settings);
  audio.setVolumes(app.settings.volumes);
};
audio.setVolumes(app.settings.volumes);

// ¿Mostrar controles táctiles? (auto = celular sin joystick conectado)
app.touchVisible = () => {
  const mode = app.settings.touchControls || "auto";
  if (mode === "on") return true;
  if (mode === "off") return false;
  if (!app.isTouchDevice) return false;
  if (gamepads.list.length && gamepads.lastUsed > app.lastTouchAt) return false;
  return true;
};

// ---------------------------------------------------------------------
// Tamaño del lienzo: alto lógico 540; si la pantalla es más ancha que
// 16:9 (celulares), el ancho lógico crece (se ve más escenario); si es
// más angosta, se agregan franjas.
// ---------------------------------------------------------------------
function resize() {
  const W = window.innerWidth, H = window.innerHeight;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const aspect = W / H;
  const v = app.view;
  // Celular en vertical: el juego va arriba (16:9 a todo el ancho) y
  // los controles táctiles en la zona de abajo -- no hace falta girarlo.
  v.portrait = app.isTouchDevice && aspect < 1;
  let vw = C.BASE_W, scale, fullH = C.BASE_H, oy = 0;
  if (v.portrait) {
    scale = W / C.BASE_W;
    fullH = H / scale;
    oy = Math.max(20, Math.min(160, (fullH - C.BASE_H) * 0.12));
  } else if (aspect >= C.BASE_W / C.BASE_H) {
    scale = H / C.BASE_H;
    vw = Math.min(W / scale, C.BASE_H * 2.4);
  } else {
    scale = W / C.BASE_W;
  }
  const cssW = vw * scale, cssH = fullH * scale;
  canvas.style.width = `${cssW}px`;
  canvas.style.height = `${cssH}px`;
  canvas.width = Math.round(cssW * dpr);
  canvas.height = Math.round(cssH * dpr);
  v.w = vw;
  v.pad = (vw - C.BASE_W) / 2;
  v.scale = scale * dpr;
  v.css = scale;
  v.fullH = fullH;
  v.oy = oy;
  app.touch.scale = (app.settings.touchScale || 100) / 100;
  app.touch.layoutFor(v);
  document.body.classList.toggle("portrait", !!v.portrait);
}
window.addEventListener("resize", resize);
document.addEventListener("fullscreenchange", () => setTimeout(resize, 100));
window.addEventListener("orientationchange", () => setTimeout(resize, 200));
app.relayout = resize;

// ---------------------------------------------------------------------
// Dedo / mouse
// ---------------------------------------------------------------------
// coordenadas del lienzo completo (y de 0 a fullH)
function toLogical(e) {
  const r = canvas.getBoundingClientRect();
  return { x: ((e.clientX - r.left) / r.width) * app.view.w, y: ((e.clientY - r.top) / r.height) * app.view.fullH };
}
canvas.addEventListener("pointerdown", (e) => {
  e.preventDefault();
  audio.unlock();
  if (e.pointerType === "touch") app.lastTouchAt = performance.now();
  const p = toLogical(e);
  if (app.touch.down(e.pointerId, p.x, p.y)) {
    canvas.setPointerCapture && canvas.setPointerCapture(e.pointerId);
    return;
  }
  if (!app.fullscreenAsked && app.isTouchDevice) { app.fullscreenAsked = true; app.enterFullscreen(); }
  const gy = p.y - app.view.oy; // coordenadas de la zona de juego
  if (app.scene && app.scene.onPointer && app.scene.onPointer(p.x, gy)) return;
  const h = UI.hitAt(p.x, gy);
  if (h) h.fn();
});
canvas.addEventListener("pointermove", (e) => { const p = toLogical(e); app.touch.move(e.pointerId, p.x, p.y); });
const up = (e) => app.touch.up(e.pointerId);
canvas.addEventListener("pointerup", up);
canvas.addEventListener("pointercancel", up);
canvas.addEventListener("contextmenu", (e) => e.preventDefault());

// Pantalla completa + horizontal en celulares (requiere un toque)
app.enterFullscreen = async () => {
  const el = document.documentElement;
  try {
    // sin bloquear la orientación: se juega en vertical u horizontal
    if (!document.fullscreenElement) {
      if (el.requestFullscreen) await el.requestFullscreen({ navigationUI: "hide" });
      else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    }
  } catch (e) { /* no soportado (iPhone) */ }
};
app.toggleFullscreen = async () => {
  if (document.fullscreenElement) await document.exitFullscreen().catch(() => {});
  else await app.enterFullscreen();
};

// ---------------------------------------------------------------------
// Loop
// ---------------------------------------------------------------------
let last = performance.now();
let acc = 0;
function frame(now) {
  requestAnimationFrame(frame);
  acc += Math.min(0.25, (now - last) / 1000);
  last = now;
  let steps = 0;
  while (acc >= C.DT && steps < 5) {
    pollGamepads();
    app.touch.visible = app.touchVisible();
    for (const i of app.inputs) i.poll();
    if (app.scene && app.scene.update) app.scene.update(C.DT);
    if (app.net && app.net.tick) app.net.tick(C.DT);
    endKeyboardFrame();
    app.touch.endFrame();
    app.t += C.DT;
    acc -= C.DT;
    steps++;
  }
  if (steps === 5) acc = 0;
  draw();
}

function draw() {
  const v = app.view;
  ctx.setTransform(v.scale, 0, 0, v.scale, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  UI.clearHits();
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, v.w, v.fullH);
  if (v.portrait) drawPortraitFrame(v);
  ctx.save();
  ctx.translate(0, v.oy);
  ctx.beginPath(); ctx.rect(0, 0, v.w, C.BASE_H); ctx.clip();
  if (app.scene && app.scene.draw) app.scene.draw(ctx, v);
  ctx.restore();
  app.touch.draw(ctx);
  ctx.save();
  ctx.translate(0, v.oy);
  if (app.toastText && performance.now() < app.toastUntil) {
    const w = UI.measure(ctx, app.toastText, 17) + 40;
    UI.roundRect(ctx, v.w / 2 - w / 2, C.BASE_H - 108, w, 38, 10);
    ctx.fillStyle = "rgba(20,20,26,0.92)";
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = C.COLORS.yellow;
    ctx.stroke();
    UI.text(ctx, app.toastText, v.w / 2, C.BASE_H - 89, { size: 17 });
  }
  ctx.restore();
}

// Vertical: fondo de la zona de controles (debajo del juego)
function drawPortraitFrame(v) {
  const bg = UI.IMG.select_bg;
  if (bg) {
    UI.drawImageCover(ctx, bg, 0, 0, v.w, v.fullH);
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.fillRect(0, 0, v.w, v.fullH);
  }
  ctx.fillStyle = "#000";
  ctx.fillRect(0, v.oy - 4, v.w, C.BASE_H + 8);
  if (!app.touch.visible || !app.touch.fightMode) {
    UI.text(ctx, "Girá el celular para jugar más grande", v.w / 2, v.oy + C.BASE_H + 80, { size: 30, color: "#bbb" });
  }
}

// ---------------------------------------------------------------------
async function boot() {
  resize();
  ctx.setTransform(app.view.scale, 0, 0, app.view.scale, 0, 0);
  try {
    await document.fonts.load("900 20px 'Roboto Black'");
  } catch (e) { /* sigue con fuente de respaldo */ }
  UI.fillBg(ctx, app.view);
  UI.text(ctx, "Cargando...", app.view.w / 2, C.BASE_H / 2, { size: 28 });
  try {
    await UI.loadUiImages();
    await loadDatabase();
  } catch (e) {
    UI.text(ctx, "No se pudo cargar el juego: " + e.message, app.view.w / 2, C.BASE_H / 2 + 40, { size: 16, color: C.COLORS.red });
    console.error(e);
    return;
  }
  app.setScene(new TitleScene(app));
  requestAnimationFrame(frame);
}

window.__app = app; // para pruebas desde la consola
keyboard.listeners.push(() => audio.unlock());
boot();
