"""Tutorial animado del sistema electrico de la banda transportadora (Blender 3.6).
Piezas del informe: Arduino, protoboard, HC-06, L298N, motor N20, servo MG996R, 2 microswitch,
adaptador 12 V, cargador 5 V, condensador, fusible y resistencias. Medidas en mm.
  blender -b --factory-startup --python build_electrico.py   ->  electrico.blend"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, math
from math import sin, cos, radians
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
from helpers import *

OUT = os.path.dirname(os.path.abspath(__file__))
NAVY, YEL, ORG, GRN = '#141A22', '#FFC400', '#E8600F', '#2FB36B'
white_e, navy_e = mat('#FFFFFF', emit=True), mat(NAVY, emit=True)
metal, hdr, pcbk = mat('#D5D9E0', 0.3, 0.9), mat('#1B1F24', 0.5), mat('#1B1F24', 0.5)

# ---------- escena base (mismo estilo del video de la banda) ----------
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1920, 1080, FPS
sc.view_settings.view_transform = 'Standard'
ee = sc.eevee
ee.taa_render_samples = 48; ee.use_gtao = True; ee.gtao_distance = 0.012
ee.use_soft_shadows = True; ee.shadow_cube_size = '1024'; ee.shadow_cascade_size = '4096'
w = bpy.data.worlds.new('w'); w.use_nodes = True; sc.world = w
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = srgb('#EEF1F4'); bg.inputs[1].default_value = 0.6
sun = bpy.data.lights.new('sol', 'SUN'); sun.energy = 2.2; sun.angle = radians(6); sun.use_contact_shadow = False
sun.shadow_cascade_max_distance = 3.0
so = link(bpy.data.objects.new('sol', sun)); so.rotation_euler = (radians(45), 0, radians(-100))
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 35; cam_d.clip_start = 0.01; cam_d.clip_end = 30
cam = link(bpy.data.objects.new('Camera', cam_d)); sc.camera = cam
tgt = empty('Objetivo')
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
box(-4000, 4000, -4000, 4000, -2, 0, mat('#E6EAEF', 0.9), 'mesa')

# ---------- cronograma (s) ----------
T_TOUR, TG, N_LAB = 2.8, 0.6, 12
T1 = T_TOUR + N_LAB * TG + 1.2
TS = [T1, T1 + 7.5, T1 + 17.0, T1 + 26.0, T1 + 39.0]      # inicio de los pasos 1..5
T_BELT = T1 + 51.0; T_CODE = T_BELT + 7.0; T_END = T_CODE + 7.0
sc.frame_start, sc.frame_end = 1, fr(T_END)

# ---------- posiciones (mm) ----------
A, BB = (130.0, 0.0), (130.0, 70.0)               # Arduino y protoboard (fijos)
DIG = {'D0': 30.0, 'D1': 27.46, 'D2': 24.92, 'D3': 22.38, 'D4': 19.84, 'D5': 17.3, 'D6': 14.76, 'D7': 12.22,
       'D8': 5.62, 'D9': 3.08, 'D10': 0.54, 'D11': -2.0, 'D12': -4.54, 'D13': -7.08, 'GND': -9.62,
       'AREF': -12.16, 'SDA': -14.7, 'SCL': -17.24}
PWR = {'IOREF': -14.0, 'RESET': -11.46, '3V3': -8.92, '5V': -6.38, 'GND2': -3.84, 'GND3': -1.3, 'VIN': 1.24}
def ardP(n):
    return (A[0] + DIG[n], A[1] + 23.5, 13.1) if n in DIG else (A[0] + PWR[n], A[1] - 23.5, 13.1)
ROWY = {'a': -13.96, 'b': -11.42, 'c': -8.88, 'd': -6.34, 'e': -3.8, 'f': 3.8, 'g': 6.34, 'h': 8.88, 'i': 11.42, 'j': 13.96}
RAILY = {'np': -21, 'nm': -24, 'fp': 21, 'fm': 24}
def bbh(c, r): return (BB[0] + (c - 15.5) * 2.54, BB[1] + ROWY[r], 9.0)
def bbr(c, rail): return (BB[0] + (c - 12.5) * 2.54, BB[1] + RAILY[rail], 9.0)

INV = {'hc06': (-60, -100), 'r1k': (-5, -100), 'r2k': (13, -100), 'cap': (55, -100), 'fuse': (100, -100), 's1': (150, -100),
       's2': (195, -100), 'n20': (245, -100), 'servo': (-30, -175), 'l298': (75, -175), 'adapter': (185, -175), 'charger': (290, -175)}
L298 = (45.0, -25.0)                              # centro final del L298N
X0 = -510.0                                       # rodillo libre; el motriz queda en X0 + 450
FIN = {'hc06': (BB[0] + (12.5 - 15.5) * 2.54, BB[1] - 3.8, 7.5), 'r1k': (BB[0] + 0.5 * 2.54, BB[1] - 11.42, 9.5),
       'r2k': (BB[0] + (14 - 15.5) * 2.54, BB[1] - 18.98, 9.5), 'cap': (BB[0] + 7.5 * 2.54, BB[1] + 22.5, 8.5),
       'fuse': (14, -70, 3), 's1': (X0 + 394, -64, 0), 's2': (X0 + 428, 64, 0), 'n20': (X0 + 450, -105, 16.7),
       'servo': (X0 + 274, 100, 0), 'l298': (L298[0], L298[1], 0), 'adapter': (60, -95, 0), 'charger': (215, 60, 0)}

# ---------- Arduino y protoboard ----------
def make_arduino():
    r = empty('Arduino', V(A[0], A[1], 0))
    box(-34.3, 34.3, -26.7, 26.7, 0, 1.6, mat('#0F7B86', 0.45), 'placa', parent=r)
    box(-36, -22, 3, 19, 1.6, 12.6, mat('#C9CED6', 0.3, 0.9), 'USB', parent=r)
    box(-36, -25, -21, -7, 1.6, 12.6, pcbk, 'jack', parent=r)
    box(-12, 23, -8, -0.4, 1.6, 5.1, pcbk, 'chip', parent=r)
    text('ARDUINO', 6.5, white_e, (2, 10, 1.7), parent=r)
    for x0, x1, y in ((12.22, 30, 23.5), (-17.24, 5.62, 23.5), (-14, 1.24, -23.5), (8, 20.7, -23.5)):
        box(x0 - 1.27, x1 + 1.27, y - 1.3, y + 1.3, 1.6, 10.1, hdr, 'cab', parent=r)
    for n, dx in DIG.items():
        box(dx - .35, dx + .35, 23.15, 23.85, 10.1, 13.1, metal, 'pin', parent=r)
        text(n, 1.7, white_e, (dx, 19.8, 1.7), parent=r)
    for n, dx in PWR.items():
        box(dx - .35, dx + .35, -23.85, -23.15, 10.1, 13.1, metal, 'pin', parent=r)
        text(n.rstrip('23') if n.startswith('GND') else n, 1.7, white_e, (dx, -19.8, 1.7), parent=r)
    for i in range(6):
        box(8 + 2.54 * i - .35, 8 + 2.54 * i + .35, -23.85, -23.15, 10.1, 13.1, metal, 'pin', parent=r)
    return r

def make_bb():
    r = empty('Protoboard', V(BB[0], BB[1], 0))
    box(-42.5, 42.5, -27.5, 27.5, 0, 8.5, mat('#EFEADF', 0.6), 'base', parent=r)
    box(-42.5, 42.5, -1.3, 1.3, 8.5, 8.6, mat('#C9C3B5'), 'canal', parent=r)
    for y, col in ((-19.2, '#E53935'), (-25.8, '#2F6FDE'), (19.2, '#E53935'), (25.8, '#2F6FDE')):
        box(-33, 33, y - .3, y + .3, 8.5, 8.6, mat(col), 'linea', parent=r)
    bm = bmesh.new()
    def sq(x, y):
        bm.faces.new([bm.verts.new(((x + dx) * S, (y + dy) * S, 8.62 * S)) for dx, dy in ((-.6, -.6), (.6, -.6), (.6, .6), (-.6, .6))])
    for c in range(1, 31):
        for y in ROWY.values(): sq((c - 15.5) * 2.54, y)
    for c in range(1, 26):
        for y in RAILY.values(): sq((c - 12.5) * 2.54, y)
    me = bpy.data.meshes.new('agujeros'); bm.to_mesh(me); bm.free(); me.materials.append(mat('#2A2F36'))
    h = link(bpy.data.objects.new('agujeros', me)); h.parent = r; h.visible_shadow = False
    for y, s_, col in ((-21, '+', '#E53935'), (-24, '−', '#2F6FDE'), (21, '+', '#E53935'), (24, '−', '#2F6FDE')):
        text(s_, 2.6, mat(col, emit=True), (-38.5, y, 8.7), parent=r)
    return r

# ---------- piezas sueltas (origen local = punto de apoyo) ----------
def make_hc06(p):
    r = empty('HC-06', V(*p))
    box(-14, 14, -2, 14, 6, 7.6, mat('#1E4FA3', 0.45), 'pcb', parent=r)
    box(-5.1, 5.1, -1.3, 1.3, 2, 6, hdr, 'cab', parent=r)
    for i in range(4): box((i - 1.5) * 2.54 - .32, (i - 1.5) * 2.54 + .32, -.32, .32, 0, 7, metal, 'pin', parent=r)
    box(-9, 3, 3, 11, 7.6, 9.8, mat('#C9CED6', 0.3, 0.8), 'lata', parent=r)
    box(6, 10, 4, 8, 7.6, 8.6, mat('#FF3B30', 0.4), 'led', parent=r)
    text('HC-06', 3.0, navy_e, (-3, 7, 9.9), parent=r)
    for i, n in enumerate(('VCC', 'GND', 'TXD', 'RXD')): text(n, 1.5, white_e, ((i - 1.5) * 2.54, 1.0, 7.7), parent=r)
    return r

def make_res(name, bands, spacing, p):
    r = empty(name, V(*p)); body = mat('#D8C9A6', 0.6)
    cyl(1.3, 6.3, body, (0, 0, 4), 'X', 'cuerpo', r, 16); cyl(.3, spacing, metal, (0, 0, 4), 'X', 'hilo', r, 8)
    for i, col in enumerate(bands): cyl(1.38, .7, mat(col), (-2 + i * 1.3, 0, 4), 'X', 'banda', r, 16)
    for sg in (-1, 1): cyl(.3, 7, metal, (sg * spacing / 2, 0, .5), 'Z', 'pata', r, 8)
    return r

def make_cap(p):
    r = empty('Condensador', V(*p))
    cyl(4.5, 12, mat('#1D3A7A', 0.4), (0, 0, 11), 'Z', 'cuerpo', r, 32);     text('1000 µF', 2.4, white_e, (0, 0, 17.05), parent=r)
    for y in (-1.5, 1.5): cyl(.3, 8, metal, (0, y, 1), 'Z', 'pata', r, 8)
    return r

def make_fuse(p):
    r = empty('Fusible', V(*p))
    cyl(3, 18, mat('#E8DCC0', 0.2), (0, 0, 3), 'X', 'vidrio', r); box(-9, 9, -.4, .4, 2.6, 3.4, mat('#FF8A00'), 'filamento', parent=r)
    for sg in (-1, 1): cyl(3.3, 3, metal, (sg * 9.5, 0, 3), 'X', 'tapa', r)
    return r

def make_l298(p):
    r = empty('L298N', V(*p)); blue = mat('#1F6FD1', 0.5)
    box(-21.5, 21.5, -21.5, 21.5, 0, 1.6, mat('#B3202A', 0.45), 'pcb', parent=r)
    box(-4, 14, -6, 12, 1.6, 16, pcbk, 'disipador', parent=r)
    text('L298N', 4.2, white_e, (5, 3, 16.1), parent=r)
    box(-21.5, -14, -6, 6, 1.6, 11.6, blue, 'bornes salida', parent=r)
    box(-9, 9, -21.5, -14, 1.6, 11.6, blue, 'bornes pot', parent=r)
    for (x, y) in ((-17.5, 3), (-17.5, -3), (-5, -17.7), (0, -17.7), (5, -17.7)): cyl(1.8, .8, metal, (x, y, 12), 'Z', 'tornillo', r, 16)
    box(18.2, 20.8, -7.5, 10, 1.6, 6.1, hdr, 'cab', parent=r)
    for i, n in enumerate(('ENA', 'IN1', 'IN2', 'IN3', 'IN4', 'ENB')):
        y = 8 - i * 2.54
        box(19.15, 19.85, y - .35, y + .35, 6.1, 9.1, metal, 'pin', parent=r)
        text(n, 1.6, white_e, (16.6, y, 1.7), 'RIGHT', r)
    for n, x, y in (('OUT1', -11.4, 3), ('OUT2', -11.4, -3)): text(n, 1.7, white_e, (x, y, 1.7), 'RIGHT', r)
    for n, x in (('12V', -5), ('GND', 0), ('5V', 5)): text(n, 1.7, white_e, (x, -12.2, 1.7), parent=r)
    return r
def l298P(k):                                      # puntos de conexion en mm (mundo, posicion final)
    x, y = L298
    return {'ENA': (x + 19.5, y + 8, 9.1), 'IN1': (x + 19.5, y + 5.46, 9.1), 'IN2': (x + 19.5, y + 2.92, 9.1),
            'OUT1': (x - 17.5, y + 3, 12.6), 'OUT2': (x - 17.5, y - 3, 12.6), '12V': (x - 5, y - 17.7, 12.6),
            'GND': (x, y - 17.7, 12.6)}[k]

def make_n20(p):
    r = empty('Motor N20', V(*p))
    cyl(5, 15, mat('#9AA4AE', 0.35, 0.8), (0, -17.5, 0), 'Y', 'motor', r); box(-6, 6, -10, 0, -6, 6, mat('#D8B04A', 0.4, 0.7), 'reductor', parent=r)
    cyl(1.5, 10, metal, (0, 5, 0), 'Y', 'eje', r, 16)
    for sx in (-2, 2): box(sx - .5, sx + .5, -26, -24.5, -1, 1, metal, 'borne', parent=r)
    return r

def make_switch(name, d, p):
    r = empty(name, V(*p))
    y0, y1 = (-11, 1) if d > 0 else (-1, 11)
    box(-7, 7, y0, y1, 0, 28, mat('#D9B77E', 0.7), 'soporte', parent=r)
    box(-6, 6, -10 if d > 0 else 0, 0 if d > 0 else 10, 28, 40, mat(YEL, 0.5), 'cuerpo', parent=r)
    box(-1, 1, 0 if d > 0 else -25, 25 if d > 0 else 0, 32.5, 35.5, mat('#2A3340', 0.5, 0.3), 'palanca', parent=r)
    cyl(3, 4, mat('#2A3340', 0.5, 0.3), (0, 25 * d, 34), 'Z', 'rodillo', r, 16)
    for sx in (-3, 3): box(sx - .5, sx + .5, -12 if d > 0 else 10, -10 if d > 0 else 12, 30, 32, metal, 'borne', parent=r)
    text(name, 5, navy_e, (0, -5 if d > 0 else 5, 40.1), parent=r)
    return r
def swP(name, d, sx):                               # borne trasero del microswitch (mundo)
    p = FIN['s1' if d > 0 else 's2']; return (p[0] + sx, p[1] + (-12 if d > 0 else 12), 31)

def make_servo(p):
    r = empty('Servo MG996R', V(*p)); dk = mat('#1A1F26', 0.4)
    box(-10, 10, -10, 30, 0, 34, dk, 'cuerpo', parent=r); box(-14, 14, -3, 3, 28, 31, dk, 'orejas', parent=r)
    cyl(3, 6, metal, (0, 0, 37), 'Z', 'eje', r, 16); cyl(7, 2, mat('#F2F4F7', 0.4), (0, 0, 39), 'Z', 'cuerno', r, 24)
    pad = empty('paleta', V(0, 0, 0), r)
    box(0, 120, -1.5, 1.5, 40, 65, mat(ORG, 0.5), 'paleta', parent=pad); box(92, 120, -2.5, 2.5, 40, 65, mat('#C9A36A', 0.9), 'forro EVA', parent=pad)
    pad.scale = (0.001,) * 3
    text('MG996R', 4.5, white_e, (0, 14, 34.1), parent=r)
    return r
def servoP(dx): return (FIN['servo'][0] + dx, FIN['servo'][1] + 30.5, 20)

def make_adapter(p):
    r = empty('Adaptador 12 V', V(*p))
    box(-35, 35, -20, 20, 0, 32, mat('#22272E', 0.4), 'caja', bevel=1.5, parent=r)
    text('12 V · 2 A', 6, white_e, (0, 0, 32.1), parent=r); cyl(2.5, 10, mat('#22272E'), (-40, 0, 16), 'X', 'cable', r, 16)
    return r
def make_charger(p):
    r = empty('Cargador 5 V', V(*p))
    box(-20, 20, -20, 20, 0, 25, mat('#F4F6F8', 0.4), 'caja', bevel=1.5, parent=r)
    text('5 V · 2 A', 5, navy_e, (0, 0, 25.1), parent=r); cyl(2, 10, mat('#F4F6F8'), (-25, 0, 12), 'X', 'cable', r, 16)
    return r

arduino, bb = make_arduino(), make_bb()
parts = {'hc06': make_hc06((*INV['hc06'], 0)), 'r1k': make_res('1 kΩ', ('#7B4A2B', '#111111', '#E53935'), 10.16, (*INV['r1k'], 0)),
         'r2k': make_res('2 kΩ', ('#E53935', '#111111', '#E53935'), 10.04, (*INV['r2k'], 0)), 'cap': make_cap((*INV['cap'], 0)),
         'fuse': make_fuse((*INV['fuse'], 3)), 's1': make_switch('S1', +1, (*INV['s1'], 0)), 's2': make_switch('S2', -1, (*INV['s2'], 0)),
         'n20': make_n20((*INV['n20'], 6)), 'servo': make_servo((*INV['servo'], 0)), 'l298': make_l298((*INV['l298'], 0)),
         'adapter': make_adapter((*INV['adapter'], 0)), 'charger': make_charger((*INV['charger'], 0))}

def glide(key, t0, dur=1.4, rz=None):
    o, f = parts[key], FIN[key]; a = Vector(o.location) / S
    o.location = o.location; K(o, 'location', fr(t0))
    mid = (a + Vector(f)) / 2; o.location = V(mid.x, mid.y, max(a.z, f[2]) + 30); K(o, 'location', fr(t0 + dur / 2))
    o.location = V(*f); K(o, 'location', fr(t0 + dur))
    if rz is not None:
        o.rotation_euler = (0, 0, 0); K(o, 'rotation_euler', fr(t0)); o.rotation_euler = (0, 0, radians(rz)); K(o, 'rotation_euler', fr(t0 + dur))

# ---------- cables, rotulos y etiquetas ----------
def pop(o, t_in, t_out=None):
    o.scale = (0.001,) * 3; K(o, 'scale', 1, 'CONSTANT')
    K(o, 'scale', fr(t_in), 'LINEAR'); o.scale = (1, 1, 1); K(o, 'scale', fr(t_in) + 8)
    if t_out is not None:
        K(o, 'scale', fr(t_out), 'LINEAR'); o.scale = (0.001,) * 3; K(o, 'scale', fr(t_out) + 8)

def callout(txt, anchor, off, t_in, t_out=None, size=7, pill=NAVY, line=True):
    root = empty('rot ' + txt, V(*anchor)); ox, oy, oz = off
    t = text(txt, size, white_e, off, parent=root, name='rotulo')
    k = t.constraints.new('TRACK_TO'); k.target = cam; k.track_axis = 'TRACK_Z'; k.up_axis = 'UP_Y'
    wd = width(t, size, txt)
    box(-wd / 2 - size * .35, wd / 2 + size * .35, -size * .62, size * .62, -.2, -.1, mat(pill, emit=True), 'pastilla', parent=t, shadow=False)
    if line:
        L = math.sqrt(ox * ox + oy * oy + oz * oz)
        ln = cyl(size * .035, L, navy_e, (ox / 2, oy / 2, oz / 2), 'Z', 'guia', root, 8, shadow=False)
        ln.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector((ox, oy, oz))).to_euler()
        cyl(size * .13, size * .13, navy_e, (0, 0, 0), 'Z', 'punto', root, 12, shadow=False)
    pop(root, t_in, t_out)

def wire(a, b, col, t0, dur=0.8, h=22, r=0.9, via=None):
    up = min(h * .5, 9); (ax, ay, az), (bx, by, bz) = a, b
    mid = [((ax + bx) / 2, (ay + by) / 2, max(az, bz) + h)] if via is None else list(via)
    pts = [a, (ax, ay, az + up)] + mid + [(bx, by, bz + up), b]
    cu = bpy.data.curves.new('cable', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r * S; cu.bevel_resolution = 3
    cu.resolution_u = 14; cu.materials.append(mat(col, 0.45))
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = V(*p); bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = link(bpy.data.objects.new('cable', cu)); o.visible_shadow = True
    cu.bevel_factor_end = 0.0; K(cu, 'bevel_factor_end', 1, 'LINEAR'); K(cu, 'bevel_factor_end', fr(t0), 'LINEAR')
    cu.bevel_factor_end = 1.0; K(cu, 'bevel_factor_end', fr(t0 + dur))

RED, BLK, GRNW, BLUW, ORGW, YELW = '#E53935', '#262B33', '#2E9E4F', '#2F6FDE', '#FB8C00', '#E0B400'
PUR, TEAL, PINK, BRN = '#8E44AD', '#16A085', '#E056A0', '#7B4A2B'

# ---------- recorrido de las piezas ----------
tour = [  # texto, pieza (ancla), posicion del rotulo (mm)
    ('Arduino', (A[0] + 5, A[1], 6), (45, 30, 40)), ('Protoboard', (BB[0] - 30, BB[1] + 20, 9), (130, 125, 40)),
    ('Bluetooth HC-06', (*INV['hc06'], 9), (-75, -68, 40)), ('Resistencias 1 kΩ y 2 kΩ', (INV['r1k'][0] + 4, INV['r1k'][1], 5), (10, -62, 66)),
    ('Condensador 1000 µF', (*INV['cap'], 17), (60, -68, 40)), ('Fusible 2 A', (*INV['fuse'], 6), (115, -62, 66)),
    ('Microswitch ×2 (S1 y S2)', (INV['s1'][0], INV['s1'][1], 40), (175, -66, 42)), ('Motor N20', (INV['n20'][0], INV['n20'][1] - 10, 12), (265, -62, 66)),
    ('Servo MG996R', (INV['servo'][0], INV['servo'][1] + 10, 34), (-75, -140, 46)), ('Driver L298N', (INV['l298'][0], INV['l298'][1], 16), (75, -140, 46)),
    ('Adaptador 12 V', (INV['adapter'][0], INV['adapter'][1], 32), (185, -140, 46)), ('Cargador 5 V', (INV['charger'][0], INV['charger'][1], 25), (290, -140, 46))]
for i, (txt, a, o) in enumerate(tour): callout(txt, a, tuple(o[k] - a[k] for k in range(3)), T_TOUR + i * TG, T1 - 0.2, 9, NAVY)

tsz = [3.4, 3.0, 5.0, 5.0, 6.5]                        # tamano de las etiquetas por paso
def tags(step, t0, items):                           # (texto, punto, desplazamiento x, y en mm)
    for txt, p, dx, dy in items:
        callout(txt, p, (dx, dy, 3 + tsz[step] * .5), t0, TS[step + 1] - 0.3 if step < 4 else T_BELT - 0.3, tsz[step], line=False)

# Paso 1: 5 V y GND a la protoboard
t = TS[0] + 1.0
wire(ardP('5V'), bbr(6, 'np'), RED, t, 1.0, 26); wire(ardP('GND'), bbr(8, 'nm'), BLK, t + 1.6, 0.8, 18)
tags(0, t + 1.4, [('5V', ardP('5V'), 0, -8), ('riel +', bbr(6, 'np'), -13, 2), ('GND', ardP('GND'), -11, 6), ('riel −', bbr(8, 'nm'), 14, -3)])
# Paso 2: HC-06 y divisor
t = TS[1] + 0.5
glide('hc06', t, 1.4); glide('r1k', t + 1.4, 1.2); glide('r2k', t + 2.6, 1.2, rz=90)
t += 4.0
wire(bbh(11, 'd'), bbr(8, 'np'), RED, t, 0.5, 8); wire(bbh(12, 'c'), bbr(9, 'nm'), BLK, t + 0.7, 0.5, 8)
wire(bbh(13, 'b'), ardP('D0'), GRNW, t + 1.4, 0.9, 22); wire(ardP('D1'), bbh(18, 'a'), BLUW, t + 2.5, 0.9, 20)
tags(1, t + 1.6, [('TXD', bbh(13, 'b'), -12, -4), ('D0', ardP('D0'), 9, 5), ('D1', ardP('D1'), -3, 11)])
callout('1 kΩ', (FIN['r1k'][0], FIN['r1k'][1], 14), (12, -3, 6), t + 3.4, TS[2] - 0.3, 3.0, line=False)
callout('2 kΩ', (FIN['r2k'][0], FIN['r2k'][1], 14), (-12, -5, 6), t + 3.6, TS[2] - 0.3, 3.0, line=False)
# Paso 3: microswitch
t = TS[2] + 0.5
glide('s1', t, 1.6); glide('s2', t + 0.4, 1.6)
t += 2.4
wire(swP('S1', +1, -3), ardP('D2'), ORGW, t, 1.2, 55); wire(swP('S1', +1, 3), bbr(3, 'nm'), BLK, t + 1.4, 1.2, 50)
wire(swP('S2', -1, -3), ardP('D3'), YELW, t + 2.8, 1.2, 40); wire(swP('S2', -1, 3), bbr(5, 'nm'), BLK, t + 4.2, 1.2, 36)
tags(2, t + 1.0, [('S1', swP('S1', +1, 0), -10, -6), ('D2', ardP('D2'), 11, 7), ('S2', swP('S2', -1, 0), -10, 6), ('D3', ardP('D3'), -2, 13), ('GND', bbr(3, 'nm'), -12, -2)])
# Paso 4: L298N, motor, adaptador de 12 V con fusible
t = TS[3] + 0.5
glide('l298', t, 1.4); glide('n20', t + 0.6, 1.4); glide('adapter', t + 1.2, 1.4); glide('fuse', t + 1.8, 1.2)
t += 3.4
for k, (pin, col) in enumerate((('ENA', PUR), ('IN1', TEAL), ('IN2', PINK))):
    wire(ardP(('D5', 'D6', 'D7')[k]), l298P(pin), col, t + k * 0.9, 0.9, 22 + 4 * k)
wire((FIN['n20'][0] + 2, FIN['n20'][1] - 26, 16.7), l298P('OUT1'), RED, t + 3.0, 1.0, 30); wire((FIN['n20'][0] - 2, FIN['n20'][1] - 26, 16.7), l298P('OUT2'), BLK, t + 3.9, 1.0, 26)
ad = (FIN['adapter'][0] - 45, FIN['adapter'][1], 16)
wire(ad, (FIN['fuse'][0] - 11.5, FIN['fuse'][1], 6), RED, t + 4.8, 0.7, 14); wire((FIN['fuse'][0] + 11.5, FIN['fuse'][1], 6), l298P('12V'), RED, t + 5.5, 0.7, 14)
wire(ad, l298P('GND'), BLK, t + 6.2, 0.8, 16); wire(ad, (A[0] - 36, A[1] - 14, 7), '#3A4048', t + 7.0, 1.0, 20, r=2.0)
wire(l298P('GND'), ardP('GND2'), BLK, t + 8.0, 0.9, 28)
tags(3, t + 0.5, [('D5→ENA', l298P('ENA'), 14, 8), ('D6→IN1', l298P('IN1'), 14, 0), ('D7→IN2', l298P('IN2'), 14, -8), ('OUT1', l298P('OUT1'), -12, 5),
                   ('OUT2', l298P('OUT2'), -12, -5), ('12 V', l298P('12V'), -10, -8), ('GND común', ardP('GND2'), 4, -10)])
# Paso 5: servo, cargador de 5 V y condensador
t = TS[4] + 0.5
glide('servo', t, 1.8); glide('charger', t + 0.8, 1.4); glide('cap', t + 1.6, 1.2)
t += 3.2
wire(servoP(-3), ardP('D9'), ORGW, t, 1.4, 60); wire(servoP(0), bbr(2, 'fp'), RED, t + 1.6, 1.4, 50); wire(servoP(3), bbr(4, 'fm'), BRN, t + 3.0, 1.4, 46)
wire((FIN['charger'][0] - 30, FIN['charger'][1], 12), bbr(24, 'fp'), RED, t + 4.6, 0.8, 20); wire((FIN['charger'][0] - 30, FIN['charger'][1], 12), bbr(24, 'fm'), BLK, t + 5.3, 0.8, 16)
wire(bbr(1, 'fm'), bbr(1, 'nm'), BLK, t + 6.1, 0.8, 22)
tags(4, t + 1.0, [('señal → D9', ardP('D9'), 0, 14), ('5 V servo', bbr(2, 'fp'), -16, 3), ('GND', bbr(4, 'fm'), -12, 7), ('cargador 5 V', (FIN['charger'][0], FIN['charger'][1], 28), 0, 0),
                   ('condensador', (FIN['cap'][0], FIN['cap'][1], 18), 0, 14), ('GND unido', bbr(1, 'nm'), -16, -4)])

# ---------- la banda (simple) llega al final ----------
belt_o, belt_m, BELT_L = make_belt(16.7, 16.7, 450)
cinta = empty('cinta', V(X0, 0, 0)); belt_o.parent = cinta
rod = []
for nm, x in (('libre', 0), ('motriz', 450)):
    e = empty('rodillo ' + nm, V(x, 0, 16.7), cinta); rod.append(e)
    cyl(16.7, 130, mat('#DDE2E8', 0.5), (0, 0, 0), 'Y', 'tubo', e, 48)
    cyl(4, 190, mat('#AEB8C2', 0.35, 0.8), (0, 0, 0), 'Y', 'eje', e, 24)
    for sg in (-1, 1):
        cyl(14, 3, mat('#C9A36A', 0.7), (0, sg * 66.5, 0), 'Y', 'tapon', e, 32)
        box(x - 12, x + 12, sg * 80 - 10, sg * 80 + 10, 0, 30, mat('#D9B77E', 0.7), 'apoyo', parent=cinta)
PER = BELT_L / 25.0
glide_t = T_BELT + 0.3
pad = [o for o in parts['servo'].children if o.name.startswith('paleta')][0]
K(pad, 'scale', 1, 'CONSTANT'); K(pad, 'scale', fr(glide_t + 1.0), 'LINEAR'); pad.scale = (1, 1, 1); K(pad, 'scale', fr(glide_t + 2.2))
cinta.scale = (0.001,) * 3; K(cinta, 'scale', 1, 'CONSTANT'); K(cinta, 'scale', fr(glide_t), 'LINEAR'); cinta.scale = (1, 1, 1); K(cinta, 'scale', fr(glide_t + 1.4))
TRAV = 320.0
for tt, b in ((0, 0), (glide_t + 1.8, 0), (T_END, TRAV)):
    belt_m.node_tree.nodes['Offset'].outputs[0].default_value = b / PER; K(belt_m.node_tree, 'nodes["Offset"].outputs[0].default_value', fr(tt), 'LINEAR')
    for r_ in rod: r_.rotation_euler = (0, b / 17.1, 0); K(r_, 'rotation_euler', fr(tt), 'LINEAR')
tb = glide_t + 2.0
for txt, a, o in (('Motor N20 → rodillo motriz', (FIN['n20'][0], FIN['n20'][1] - 10, 20), (FIN['n20'][0] + 40, FIN['n20'][1] - 55, 60)),
                  ('Servo + paleta', (FIN['servo'][0], FIN['servo'][1] + 10, 45), (FIN['servo'][0] - 20, FIN['servo'][1] + 40, 75)),
                  ('Microswitch S1', (FIN['s1'][0], FIN['s1'][1], 42), (FIN['s1'][0] - 50, FIN['s1'][1] - 55, 60)),
                  ('Microswitch S2', (FIN['s2'][0], FIN['s2'][1], 42), (FIN['s2'][0] - 30, FIN['s2'][1] + 50, 70)),
                  ('Arduino + protoboard', (A[0], BB[1] + 10, 12), (A[0] + 10, 130, 70)), ('Banda', (X0 + 200, 0, 34), (X0 + 200, -30, 100))):
    callout(txt, a, tuple(o[k] - a[k] for k in range(3)), tb, None, 16)
    tb += 0.45

# ---------- camara ----------
POSE = {'tour': (-12, 48, 0.68, 105, -60), 's1': (-5, 52, 0.34, 128, 20), 's2': (-5, 58, 0.30, 128, 44), 's3': (-8, 50, 0.55, 20, 5),
        's4': (-8, 50, 0.50, 40, -55), 's5': (-8, 52, 0.58, -5, 40), 'belt': (-12, 48, 0.95, -150, -10)}
WP = [(0, *POSE['tour']), (T1 - 0.5, -18, 48, 0.72, 105, -60)]
for k, (a, b) in enumerate(zip(TS, TS[1:] + [T_BELT])):
    WP += [(a + 1.2, *POSE['s%d' % (k + 1)]), (b - 1.2, *POSE['s%d' % (k + 1)])]
WP += [(T_BELT + 1.4, *POSE['belt']), (T_END, *POSE['belt'])]
for fi in list(range(1, fr(T_END), 4)) + [fr(T_END)]:
    tt = min((fi - 1) / FPS, T_END)
    for a, b in zip(WP, WP[1:]):
        if a[0] <= tt <= b[0]:
            u = sm((tt - a[0]) / max(b[0] - a[0], 1e-6)); v = [a[i] + (b[i] - a[i]) * u for i in range(1, 6)]; break
    az, el, d, tx, ty = radians(v[0]), radians(v[1]), v[2], v[3] * S, v[4] * S
    tgt.location = (tx, ty, 0); K(tgt, 'location', fi, 'LINEAR')
    cam.location = (tx + d * sin(az) * cos(el), ty - d * cos(az) * cos(el), d * sin(el)); K(cam, 'location', fi, 'LINEAR')

# ---------- HUD ----------
HZ = 0.0
HUD = empty('HUD', (0, 0, -0.2), cam); HUD.scale = (0.4, 0.4, 0.4)
def hide_between(o, a, b):
    o.hide_render = True; K(o, 'hide_render', 1); o.hide_render = False; K(o, 'hide_render', fr(a)); o.hide_render = True; K(o, 'hide_render', fr(b))
title = empty('titulo', (-0.235, 0.118, HZ), HUD)
t1 = text('ARMA EL SISTEMA', 20, navy_e, (0, 0, 0), 'LEFT', title)
t2 = text('ELÉCTRICO', 20, navy_e, (0, -21, 0), 'LEFT', title); w2 = width(t2, 20, 'ELÉCTRICO') * S / 0.4
rect(-0.0025, w2 + 0.0025, -0.0335, -0.0085, -0.0004, -0.0002, mat(YEL, emit=True), title)
sub = text('Banda transportadora de bajo presupuesto · paso a paso', 9, navy_e, (0, -44, 0), 'LEFT', title)
hide_between(sub, 0, 2.2)
title.scale = (1, 1, 1); K(title, 'scale', 1, 'LINEAR'); K(title, 'scale', fr(1.8), 'LINEAR'); title.scale = (0.5, 0.5, 0.5); K(title, 'scale', fr(2.6))
rect(-0.26, 0.26, -0.1446, -0.1126, HZ - 0.0002, HZ, mat(NAVY, emit=True), HUD)
CAPS = [(2.6, T1, 'Estas son las piezas que vamos a conectar', 'PIEZAS'),
        (TS[0], TS[1], '5 V y GND del Arduino a los rieles de la protoboard', 'PASO 1'),
        (TS[1], TS[2], 'Bluetooth HC-06 en D0 y D1 · divisor de 1 kΩ + 2 kΩ en el pin RX', 'PASO 2'),
        (TS[2], TS[3], 'Microswitch S1 a D2 y S2 a D3 · el otro cable de cada uno a GND', 'PASO 3'),
        (TS[3], TS[4], 'Driver L298N en D5, D6, D7 · motor en OUT1/OUT2 · 12 V con fusible de 2 A', 'PASO 4'),
        (TS[4], T_BELT, 'Servo: señal a D9 · energía de un cargador de 5 V aparte, con GND unido', 'PASO 5'),
        (T_BELT, T_CODE, 'Así se reparte sobre la banda: motor, servo y microswitch', 'EN LA BANDA'),
        (T_CODE, T_END + 1, 'Código de prueba del informe (5 minutos)', 'CÓDIGO')]
hide_between(rect(0.125, 0.245, 0.105, 0.132, HZ - 0.0002, HZ, mat(YEL, emit=True), HUD), 2.6, T_END + 1)
for a, b, s, bd in CAPS:
    ct = text(s, 10, white_e, (0, 0, 0), 'LEFT', HUD, 'leyenda'); ct.location = (-0.245, -0.1286, HZ + 0.0002); hide_between(ct, a, b)
    bt = text(bd, 9, navy_e, (0, 0, 0), 'CENTER', HUD, 'insignia'); bt.location = (0.185, 0.1185, HZ + 0.0002); hide_between(bt, a, b)
CODE = ('#include <Servo.h>\nServo s;\nvoid setup() {\n  Serial.begin(9600);\n  pinMode(LED_BUILTIN, OUTPUT);\n  s.attach(9);\n}\n'
        'void loop() {\n  digitalWrite(LED_BUILTIN, HIGH); s.write(0);  delay(700);\n  digitalWrite(LED_BUILTIN, LOW);  s.write(90); delay(700);\n'
        '  Serial.println("ok");\n}')
card = rect(-0.14, 0.14, -0.098, 0.084, HZ - 0.0008, HZ - 0.0006, mat(NAVY, emit=True), HUD); hide_between(card, T_CODE, T_END + 1)
ct = text('PRUEBA DE 5 MINUTOS · servo en D9 y LED de la placa', 8.5, mat(YEL, emit=True), (0, 0, 0), 'LEFT', HUD, 'codigo t'); ct.location = (-0.128, 0.070, HZ - 0.0004); hide_between(ct, T_CODE, T_END + 1)
cd = text(CODE, 9.2, white_e, (0, 0, 0), 'LEFT', HUD, 'codigo', MONO, 'TOP'); cd.data.space_line = 1.18; cd.location = (-0.128, 0.054, HZ - 0.0004); hide_between(cd, T_CODE, T_END + 1)

bpy.ops.file.pack_all()
sc.render.filepath = '//electrico_'
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'; sc.render.ffmpeg.ffmpeg_preset = 'GOOD'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'electrico.blend'))
print('FRAMES', sc.frame_end, 'T', round(T_END, 1), 'T1', round(T1, 1), 'TS', [round(x, 1) for x in TS], 'BELT', round(T_BELT, 1), 'CODE', round(T_CODE, 1))
