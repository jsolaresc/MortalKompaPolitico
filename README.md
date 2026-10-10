# Mortal Kompa Político — V.0.1

Juego de pelea en el navegador, hermano de Mortal Kompa: misma jugabilidad,
luchadores de la política argentina. No se instala: se juega desde una página
web (PC, celular o tablet).

## Cómo se juega
- **PC:** teclado o joystick (PlayStation / Xbox / genérico).
  - J1: `A D` moverse · `W` saltar · `S` agacharse · `J` puño · `K` patada · `I` a distancia · `L` especial · `O` cubrirse · `ENTER` pausa.
  - J2: flechas · `1` puño · `2` patada · `3` a distancia · `4` cubrirse · `5` especial (fila de números o teclado numérico).
  - Joystick: □/X puño · ✕/A patada · ○/B distancia · △/Y especial · R1/RB cubrirse · START pausa.
  - Las teclas se cambian en Opciones > Controles.
- **Celular:** el juego lo detecta solo y muestra joystick + botones en pantalla. Si conectás
  un joystick por Bluetooth, los botones táctiles se esconden y se juega con el joystick
  (con dos joysticks se puede jugar de a dos en el mismo celular).
- El **Especial** se habilita después de recibir 5 golpes. 2% de golpes críticos en puño/patada.
  Muerte súbita si empatan 1 a 1. Flawless si ganás un round sin perder vida.
- **Escenario secreto:** en la elección de escenario, apretá START / ENTER.

## Modos
- 1 Jugador: **Torre de Batalla** (todos contra todos, cada piso más difícil, jefe misterioso al final) y **Pelea contra CPU** (dificultad 1 a 10).
- Multijugador: **2 Jugadores** y **Torneo** (3 a 16) en el mismo equipo.
- **Online: invitar por link.** Se abre una sala y aparece el link: *Copiar link*,
  *WhatsApp*, *Mail* o *Compartir…* (en el celular abre el menú de compartir).
  Quien abre el link entra directo. En la sala elegís **Pelea 1 vs 1** (con el primero
  que entró; el resto mira) o **Torneo** (todos los de la sala, cada uno elige su luchador
  en su pantalla).

## Probarlo en tu PC
Los navegadores no dejan abrir el juego con doble clic en `index.html`
(bloquean la carga de archivos). Usá **`Jugar en mi PC.bat`** (necesita Python),
o cualquier servidor local, y entrá a `http://localhost:8000`.

Para probar el online en una sola PC sin internet: `http://localhost:8000/?net=local`,
creá la sala y abrí el link de invitación en otra pestaña del mismo navegador.

## Publicarlo en GitHub Pages
1. Creá un repositorio (ej. `mortal-kompa-politico`) y subí **el contenido de esta carpeta**
   (que `index.html` quede en la raíz del repo).
2. En el repo: *Settings > Pages > Build and deployment* → *Deploy from a branch* →
   rama `main`, carpeta `/ (root)`.
3. En un par de minutos queda en `https://<tu-usuario>.github.io/mortal-kompa-politico/`.
4. **Dominio propio** (ej. `mortalkompa.com`): en *Settings > Pages > Custom domain*
   escribí el dominio; en tu proveedor del dominio creá los registros que te indica
   GitHub (A a las IP de GitHub Pages, o CNAME a `<tu-usuario>.github.io`). Activá
   *Enforce HTTPS* (el online necesita HTTPS).

## Cómo funciona el online
El que invita ("anfitrión") corre la pelea de verdad; los demás le mandan sus botones y
reciben 60 veces por segundo lo que tienen que dibujar. Los navegadores se conectan
directo entre sí (WebRTC). Para "presentarlos" se usa el servidor público gratuito de
PeerJS (no hay servidor propio que mantener).
- Si alguien no logra conectarse nunca (pasa en algunas redes de datos móviles muy
  cerradas), hace falta agregar un servidor TURN en `js/config.js` (`ICE_SERVERS`).
- El invitado siente un pequeño retraso en sus golpes (lo que tarda internet ida y vuelta).

## Cambiar los luchadores provisorios por los reales
Los 9 políticos son **maniquíes provisorios** dibujados por código
(`tools/generar_placeholders.py`). Para poner el arte real de uno, ej. Milei:
1. Reemplazá los PNG de `assets/characters/milei/<animación>/0.png, 1.png...`
   (`idle, walk, jump, punch, kick, special, ranged, ranged_crouch, crouch, block, block_crouch, ko, win`),
   `selection.png` (cuadrado de la grilla), `pose.png` (pose grande) y `projectile/0.png...`.
2. En `data/characters/milei.json`: poné `"placeholder": false`, ajustá `"frames"` de cada
   animación a la cantidad real de PNG (el navegador no puede contar archivos de una carpeta),
   `"scale"` y `"projectile_frames"` / `"projectile_scale"`. El resto de las opciones
   (`damage`, `reach`, `active_frames`, `trajectory`, `kick_height`, `gravity_mult`,
   `extra_scale`, `y_offset`, `no_flip`...) funcionan igual que en Mortal Kompa.
3. Sonidos propios: `"sounds": { "punch": ["sounds/punch/a.mp3"], "hit": [...], "win": [...] }`
   (rutas relativas a la carpeta del personaje). Voz del locutor diciendo el nombre:
   `"announcer": "sounds/nombre.wav"`.
4. Para sumar un luchador nuevo: copiá un JSON y su carpeta, y agregalo en `data/roster.json`.

## Escenarios y música
- `data/stages.json`: nombre, imagen (`.png/.jpg/.webp`) o **video** (`.mp4/.webm`, en loop y
  sin sonido; los GIF no se animan en el navegador, conviene pasarlos a .mp4 o .webm) y música.
  Un escenario más ancho que 16:9 hace scroll con la cámara. `"secret": true` = escenario secreto
  (también es el de la final del Torneo y del jefe de la Torre).
- Música de menú: listala en `data/music.json`. Esta versión no trae música (a pedido).

## Estructura
```
index.html, css/, js/        el juego (JavaScript sin compilar, no hace falta instalar nada)
js/config.js                 constantes y versión (GAME_VERSION)
data/                        roster, personajes, escenarios, música
assets/                      sprites, escenarios, sonidos (efectos y locutor de Mortal Kompa), fuente
lib/peerjs.min.js            conexión online (MIT)
tools/generar_placeholders.py  regenera los luchadores/escenarios provisorios
```
