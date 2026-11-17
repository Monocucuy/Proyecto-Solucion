# Renderizar el modelo 3D de la banda en el otro PC

1. Copia esta carpeta completa (`banda_real.py`, `RENDERIZAR_BANDA.bat`, la carpeta `tex`) al otro PC.
2. Ten instalado Blender (sirve 3.6 LTS, 4.x o 5.x; se probó en 5.1).
3. Doble clic en `RENDERIZAR_BANDA.bat`. No abre Blender: arma la escena, guarda `banda_real.blend` y renderiza.
4. Resultado en `salida/`:
   - `render_01_vista_general.png` … `render_06_celular_desviado.png` (1920×1080).
   - `banda_real_10s_1080p60_0001-0600.mp4` (10 s, 60 fps).
5. Solo imágenes: abre una consola en la carpeta y escribe `RENDERIZAR_BANDA.bat stills`. Solo video: `RENDERIZAR_BANDA.bat video`.

Qué muestra: estructura Lego Technic de 45 cm, tela de 11,5 cm sobre rodillos (34 cm visibles), N20, servo MG90S con la viga como compuerta, los 2 microswitches de S1, Arduino, protoboard y ESP32. En el video el celular avanza, se detiene en S1, la compuerta gira a 33° y lo desvía (revisión).
Límites: es un modelo simplificado (no es cada pieza Lego); la velocidad de la banda (4,5 cm/s) es supuesta, no medida.
