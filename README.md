# Mortal Kompa Político — V.0.5

Juego de pelea en el navegador, hermano de Mortal Kompa: misma jugabilidad,
luchadores de la política argentina. No se instala: se juega desde una página
web (PC, celular o tablet).

## Cómo se juega
- **PC:** teclado o joystick (PlayStation / Xbox / genérico).
  - J1: `A D` moverse · `W` saltar · `S` agacharse · `J` puño · `K` patada · `I` a distancia · `L` especial · `O` cubrirse · `ENTER` pausa.
  - J2: flechas · `1` puño · `2` patada · `3` a distancia · `4` cubrirse · `5` especial (fila de números o teclado numérico).
  - Joystick: □/X puño · ✕/A patada · ○/B distancia · △/Y especial · R1/RB cubrirse · START pausa.
  - Las teclas se cambian en Opciones > Controles.
- **Celular:** el juego lo detecta solo y muestra joystick + botones en pantalla. Siempre se ve
  **en horizontal**: si el celular está en vertical, el juego aparece ya acostado (solo hay que
  mirarlo de costado, no depende de la rotación automática). Al primer toque pasa a **pantalla
  completa** y, en Android, la pantalla queda trabada en horizontal. En iPhone, Safari no permite
  pantalla completa en páginas: *Compartir > Agregar a pantalla de inicio* y abrilo desde ese ícono.
  Si conectás un joystick por Bluetooth, los botones táctiles se esconden (con dos joysticks se
  juega de a dos en el mismo celular).
- El **Especial** se habilita después de recibir 5 golpes. No es un golpe: el luchador da una orden
  y aparece algo que ataca solo (un león, una ola, un satélite...). Saca **17%** de vida, **4%** si
  el rival se cubre, y se puede **esquivar** (saltando lo que viene por el piso, agachándose ante el
  cohete del tanque, alejándose del láser o de la bomba). 2% de golpes críticos en puño/patada.
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

## Ataques especiales
Se configuran en el JSON de cada personaje, bloque `"special"` (`js/specials.js` explica todo):

| Personaje | Especial | Tipo |
|---|---|---|
| Milei | León que entra desde atrás y cruza corriendo | `rush` (offscreen) |
| Cristina | Satélite que baja y dispara lásers | `satellite` |
| Bullrich | Bomba que explota a los 2 s, daño en área | `bomb` |
| Macri | Ola de agua desde atrás suyo | `rush` (behind) |
| Massa | Ola de billetes de pesos | `rush` (behind) |
| Bregman | Tanque que aparece detrás, dispara un cohete y se va | `tank` |
| Kicillof | Movilización de la UOCRA | `rush` (offscreen) |
| Alberto | *Provisorio:* ola de notas musicales | `rush` (behind) |
| Scioli | *Provisorio:* lancha | `rush` (offscreen) |

- Sprites: `assets/characters/<nombre>/special_fx/main/0.png, 1.png...` (el tanque además
  `special_fx/rocket/`). Cantidad de cuadros en `"fx": {"main": 4}`; alto en pantalla con `"draw_h"`;
  caja de golpe con `"hit_w"`/`"hit_h"`; velocidad con `"speed"`. Dibujados mirando a la derecha.
- La animación `special` del luchador es el **gesto de mando** (señalar); la invocación aparece en
  su cuadro activo (`active_frames`).
- Audios (2 por especial): `"sounds": {"special": ["sounds/voz_orden.mp3"], "special_sfx": ["sounds/rugido.mp3"]}`.
  `special` = voz del personaje comandando (suena al empezar el gesto), `special_sfx` = efecto
  (rugido, agua...). Cuándo suena el efecto: `"sfx_on"`: `spawn` (al aparecer), `fire` (al disparar)
  o `explode` (al explotar). Los efectos actuales son provisorios (sintetizados); las voces faltan.
- Daño: `SPECIAL_SUMMON_DAMAGE` / `SPECIAL_SUMMON_BLOCKED` en `js/config.js`.

## Escenarios y música
- `data/stages.json`: nombre, imagen (`.png/.jpg/.webp`) o **video** (`.mp4/.webm`, en loop y
  sin sonido; los GIF no se animan en el navegador, conviene pasarlos a .mp4 o .webm) y música.
  Un escenario más ancho que 16:9 hace scroll con la cámara. `"secret": true` = escenario secreto
  (también es el de la final del Torneo y del jefe de la Torre).
- Música de menú: listala en `data/music.json`. Esta versión no trae música (a pedido).

## Interfaz
Logo, fondos de menú, marco de la barra de vida, timer, puntitos de rounds y especial,
cartel de K.O., íconos de "Aleatorio", botones táctiles y los íconos de botones de joystick
son los mismos de Mortal Kompa (`assets/ui/`). Reemplazá cualquier PNG/JPG con el mismo
nombre para cambiarlo; si falta uno, el juego dibuja un reemplazo.

## Estructura
```
index.html, css/, js/        el juego (JavaScript sin compilar, no hace falta instalar nada)
js/config.js                 constantes y versión (GAME_VERSION)
data/                        roster, personajes, escenarios, música
assets/                      sprites, escenarios, sonidos (efectos y locutor de Mortal Kompa), fuente
lib/peerjs.min.js            conexión online (MIT)
tools/generar_placeholders.py  regenera los luchadores/escenarios provisorios
```
