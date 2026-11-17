"""Genera las texturas del prototipo real (Pillow). Uso:  py -3 texturas_banda_real.py
Salida (carpeta tex/ junto a este archivo): banda_tela.png (lazo completo de la tela) y protoboard.png.
La tela se parece a las fotos del 17-nov-2026: blanca, dos franjas negro-gris-negro, borde en cuerda
(rayitas blanco/rosa/morado) a cada lado y una costura transversal. Medidas aproximadas, no medidas."""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, 'tex'); os.makedirs(OUT, exist_ok=True)

# --- mismas constantes que build_banda_real.py (mm) ---
XL, RM, ANCHO = 300.0, 18.0, 115.0            # entre ejes, radio medio de la banda, ancho de la tela
LAZO = 2 * XL + 2 * math.pi * RM              # largo del lazo del modelo (mm)

SS = 2                                         # supersampling
W, H = 4096, 640
PXMM_U, PXMM_V = W / LAZO * SS, H / ANCHO * SS

TELA, NEGRO, GRIS = (243, 240, 232), (26, 26, 28), (176, 179, 186)
CUERDA = [(247, 244, 238), (214, 172, 192), (150, 112, 158)]     # blanco, rosa, morado
N_RAYAS = 66                                   # entero y multiplo de 3: la tela cierra sin salto

img = Image.new('RGB', (W * SS, H * SS), TELA)
d = ImageDraw.Draw(img)
V = lambda mm: mm * PXMM_V                    # mm desde el borde superior (= lado +y, el del servo)

def banda_h(a, b, color):                      # franja horizontal (a lo largo del lazo), de a a b mm
    d.rectangle([0, V(a), W * SS, V(b)], fill=color)

def cuerda(a, b):                              # borde: linea negra, rayitas inclinadas, linea negra
    banda_h(a, a + 0.9, NEGRO); banda_h(b - 0.9, b, NEGRO)
    y0, y1 = V(a + 0.9), V(b - 0.9)
    paso = W * SS / N_RAYAS; desf = 0.55 * (y1 - y0)
    for i in range(N_RAYAS):
        x = i * paso
        pts = [(x, y1), (x + paso * 0.9, y1), (x + paso * 0.9 + desf, y0), (x + desf, y0)]
        d.polygon(pts, fill=CUERDA[i % 3], outline=NEGRO)
        # la rayita inclinada se sale por la derecha: se repite al otro lado para cerrar el lazo
        if i == N_RAYAS - 1:
            d.polygon([(px - W * SS, py) for px, py in pts], fill=CUERDA[i % 3], outline=NEGRO)

def franja(a, b):                              # negro - gris - negro
    banda_h(a, b, GRIS); banda_h(a, a + 1.3, NEGRO); banda_h(b - 1.3, b, NEGRO)

cuerda(6, 13.5); franja(31, 44); franja(60, 77); cuerda(96, 110)

# puntadas de borde (gris claro, discontinuas) y costura transversal
for y in (2.5, 112.5 + 0.0):
    for x in np.arange(0, W * SS, 28):
        d.line([x, V(y), x + 16, V(y)], fill=(214, 210, 200), width=2)
xs = 0.30 * W * SS
for y in np.arange(0, ANCHO, 2.6):
    d.line([xs, V(y), xs, V(y + 1.4)], fill=(205, 200, 190), width=3)

img = img.resize((W, H), Image.LANCZOS)
# fibras: ruido muy suave para que no se vea plana
a = np.asarray(img).astype(np.float32)
rng = np.random.default_rng(7)
a += rng.normal(0, 2.2, a.shape[:2])[..., None]
for _ in range(900):                           # nudos cortos y mas oscuros
    x, y = int(rng.integers(0, W - 8)), int(rng.integers(0, H))
    a[y, x:x + int(rng.integers(2, 8))] -= 9
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'banda_tela.png'), optimize=True)

# ---------------- protoboard 830 puntos (165 x 55 mm, 10 px/mm) ----------------
PX = 10
pb = Image.new('RGB', (165 * PX, 55 * PX), (238, 237, 231)); dp = ImageDraw.Draw(pb)
def agujero(cx, cy): dp.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(58, 58, 62))
paso = 2.54 * PX
x0 = (165 * PX - 62 * paso) / 2
for c in range(63):                            # 63 columnas x 2 bloques de 5 filas
    for r in range(5):
        agujero(x0 + c * paso, 27.5 * PX - 3.0 * PX - r * paso)
        agujero(x0 + c * paso, 27.5 * PX + 3.0 * PX + r * paso)
for fila, col in ((5.5, (200, 60, 60)), (8.1, (60, 90, 200)), (46.9, (60, 90, 200)), (49.5, (200, 60, 60))):
    dp.line([x0, fila * PX - 14, 165 * PX - x0, fila * PX - 14], fill=col, width=3)
    for c in range(50):                        # rieles: 10 grupos de 5 agujeros
        agujero(x0 + 2 * paso + (c + c // 5) * paso, fila * PX)
dp.rectangle([0, 27.5 * PX - 12, 165 * PX, 27.5 * PX + 12], fill=(214, 213, 206))   # canal central
pb.save(os.path.join(OUT, 'protoboard.png'), optimize=True)
print('LAZO mm', round(LAZO, 1), 'texturas en', OUT)
