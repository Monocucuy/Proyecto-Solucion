# Modelos 3D de la banda (Blender)

Fecha: 17-nov-2026. Los `.blend` están guardados con Blender 5.1 y abren con esa versión o una más nueva. Con una versión anterior, regenerar la escena con el script de cada carpeta.

## Resultado

| Carpeta | Qué es | Video |
|---|---|---|
| [`diseno_v2_3nov/`](diseno_v2_3nov) | Primera idea (informe V2, 3-nov-2026): animación de la banda y tutorial eléctrico | Animación: https://youtu.be/wB2_RyOwL9I |
| [`modelo_final_17nov/`](modelo_final_17nov) | Prototipo final con medidas reales: tela de 11,5 cm, 34 cm útiles, estructura de 45 cm, servo MG90S, 2 microswitches en S1, Arduino, protoboard y ESP32 | Pendiente de render (10 s, 1080p, 60 fps) |

## Diseño V2 (3-nov-2026)

- `banda_transportadora.blend`: animación de la banda del diseño V2 (MG996R, cajas OK y REVISIÓN). Se rearma con `blender -b -P build_banda.py`.
- `electrico.blend`: tutorial eléctrico del diseño V2. Se rearma con `blender -b -P build_electrico.py` (usa `helpers.py`). Video: `renderizar_electrico.bat`.
- Este diseño ya no es el final: el prototipo cambió a Lego Technic, MG90S, sin driver y sin cajas (ver el informe técnico final, sección 4).

## Modelo final (17-nov-2026)

- `banda_real.blend`: escena armada por `banda_real.py`.
- `RENDERIZAR_BANDA.bat`: doble clic; renderiza 6 imágenes PNG 1920×1080 y un video de 10 s a 1080p y 60 fps en `salida/`. Opciones: `stills` o `video`. Detalle en `LEEME_RENDER.md`.
- `borrador_vista_general.jpg` y `borrador_compuerta.jpg`: imágenes de borrador (pocas muestras) hechas el 17-nov-2026 para comprobar la escena.

## Límites

- Modelo simplificado: no reproduce cada pieza Lego.
- La velocidad de la banda en la animación (4,5 cm/s) es supuesta; no se ha medido.
- Las fuentes de Windows (Arial y Consolas) ya no van empaquetadas en los `.blend` porque no se pueden redistribuir; Blender las toma de `C:\Windows\Fonts` y, si no están, usa su fuente interna.
