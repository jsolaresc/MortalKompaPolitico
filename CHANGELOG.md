# Cambios

## V.0.6
- Se copió la versión navegador actualizada de Mortal Kompa (jugabilidad, menús y apps):
  - Jugabilidad: golpe crítico = doble daño; daño fijo al cubrirse según el ataque (puño/patada
    0,5 · distancia 0,1). Los especiales de Mortal Kompa Político siguen siendo invocaciones
    (17% / 4% cubriéndose).
  - Menús como la versión de PC/Android (selección de personaje, torre, torneo, opciones en
    Sonido / Pantalla / Controles, volumen aparte para la música del escenario, títulos largos en
    varios renglones, menús tipo "pastilla" en celular).
  - Online: Crear sala / Unirse con código de 6 letras; 1 vs 1 o torneo según cuántos entren;
    reconexión en el torneo con pausa esperando al que se fue; se aguantan cortes del servidor
    de partidas.
  - App Android (APK) con el mismo juego adentro: botones INSTALAR (web) y ACTUALIZAR (app),
    "atrás" del celular, juego cruzado app ↔ página. iPhone: instrucciones para agregar el ícono.
  - Ícono de app y vista previa para compartir de Mortal Kompa Político.

## V.0.5
- Nuevos ataques especiales "externos": el luchador da una orden y aparece una invocación que
  ataca sola. 17% de daño (4% cubriéndose) y se pueden esquivar.
  Milei: león · Cristina: satélite con lásers · Bullrich: bomba de 2 s con daño en área ·
  Macri: ola de agua · Massa: ola de billetes · Bregman: tanque que dispara un cohete ·
  Kicillof: movilización de la UOCRA · Alberto y Scioli: provisorios (notas musicales / lancha).
- Sprites y efectos de sonido provisorios para cada invocación; lugar para la voz de cada
  personaje comandando el ataque.
- La CPU usa el especial a cualquier distancia y trata de esquivar/cubrirse de los del rival.

## V.0.4
- Controles táctiles con la misma ubicación, tamaño y comportamiento que Mortal Kompa Android
  (abanico de botones para el pulgar, joystick flotante en la mitad izquierda, especial con
  aro de carga de 5 partes).
- Con los controles táctiles en pantalla se ocultan los pips de especial del HUD (el botón de
  Especial ya muestra la carga).
- Botón de pausa arriba a la izquierda, debajo del nombre del J1.

## V.0.3
- En celular el juego siempre se ve en horizontal: en vertical se dibuja ya girado (sin pedir que
  gires el teléfono ni depender de la rotación automática). En Android, al primer toque entra en
  pantalla completa y traba la pantalla en horizontal. Se sacó el modo vertical de la V.0.2.

## V.0.2
- Interfaz visual de Mortal Kompa: logo (con cinta "POLÍTICO"), fondos de título / selección /
  torre, marco de vida, timer, puntitos de rounds y especial, cartel de K.O., íconos de
  Aleatorio, botones táctiles (puño, patada, distancia, bloqueo, especial con candado y aro de
  carga, pausa, joystick) e íconos de joystick en los textos de ayuda.
- Celular en vertical: ya no pide girar el teléfono; el juego va arriba y los controles abajo.
- Pantalla completa al primer toque (Android) + botón "Pantalla completa" en el inicio;
  instalable como app (manifest) para pantalla completa en iPhone.

## V.0.1
- Primera versión web de Mortal Kompa Político (juego nuevo, separado de Mortal Kompa).
- Jugabilidad portada de Mortal Kompa V.1.2: rounds al mejor de 3, especial con 5 golpes
  recibidos, críticos, muerte súbita, Flawless, K.O. con rebote, proyectiles recto/arco/pique,
  cámara con escenarios panorámicos, IA de la CPU con sus 10 niveles.
- Modos: Torre de Batalla, Pelea contra CPU, 2 Jugadores, Torneo local (3-16), Online por link
  (1 vs 1 y Torneo para muchos jugadores).
- Detección de celular: controles táctiles; soporte de joystick en PC y celular.
- 9 luchadores provisorios (Milei, Cristina, Alberto, Kicillof, Macri, Scioli, Bregman, Massa,
  Bullrich) y 5 escenarios provisorios (Plaza de Mayo, Congreso, Obelisco, Quinta de Olivos y
  el secreto Destino Final). Efectos de sonido y locutor de Mortal Kompa; sin música.
