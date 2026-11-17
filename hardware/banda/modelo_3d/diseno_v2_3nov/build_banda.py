"""Banda transportadora de bajo presupuesto: escena animada (Blender 3.6).
Medidas del informe en mm (1 BU = 1 m). Uso:
  blender -b --factory-startup --python build_banda.py
Genera banda_transportadora.blend en esta carpeta."""
import bpy, bmesh, math, os
from math import pi, sin, cos, atan, radians
from mathutils import Vector, Matrix

OUT = os.path.dirname(os.path.abspath(__file__))
S, FPS = 0.001, 24
ZC, R = 28.0, 16.7                 # eje y radio de rodillo
TOP = ZC + R + 0.8                 # cara superior de la banda
BED = TOP - 1.1                    # cara superior de la cama
RH = ZC + 10.4                     # altura de los largueros (= cara inferior de la cama)
BZ = TOP + 6                       # centro del bloque sobre la banda
BX0, XL = 90.0, 450.0              # centro inicial del bloque, distancia entre ejes
STOP_R = 308.0                     # centro del bloque en la estacion de revision (S1)
X_END = 453.0                      # centro del bloque cuando cae por el extremo (A)
SPEED = 84.0                       # mm/s (informe)

def fr(sec): return round(sec * FPS) + 1
def V(x, y, z): return Vector((x * S, y * S, z * S))
def sm(u): u = max(0, min(1, u)); return u * u * (3 - 2 * u)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------- materiales ----------
def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)

_m = {}
def mat(h, rough=0.55, metal=0.0, emit=False):
    k = (h, rough, metal, emit)
    if k not in _m:
        m = bpy.data.materials.new(h); m.use_nodes = True; N = m.node_tree.nodes
        if emit:
            m.shadow_method = 'NONE'; N.clear(); e = N.new('ShaderNodeEmission'); e.inputs[0].default_value = srgb(h)
            o = N.new('ShaderNodeOutputMaterial'); m.node_tree.links.new(e.outputs[0], o.inputs[0])
        else:
            b = N['Principled BSDF']; b.inputs['Base Color'].default_value = srgb(h)
            b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
        _m[k] = m
    return _m[k]

NAVY, YEL, ORG, GRN = '#141A22', '#FFC400', '#E8600F', '#2FB36B'

# ---------- primitivas (coordenadas en mm; el padre fija el origen local) ----------
def link(o): sc.collection.objects.link(o); return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = link(bpy.data.objects.new(name, None)); o.location = loc
    if parent: o.parent = parent
    return o

def box(x0, x1, y0, y1, z0, z1, m, name='box', bevel=0, parent=None, shadow=True):
    hx, hy, hz = abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2
    vs = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
          (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([(a * S, b * S, c * S) for a, b, c in vs], [],
                   [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (3, 0, 4, 7), (1, 2, 6, 5)])
    me.update(); me.materials.append(m)
    o = link(bpy.data.objects.new(name, me))
    o.location = V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    o.visible_shadow = shadow
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL'); b.width = bevel * S; b.segments = 2; b.limit_method = 'ANGLE'
    if parent: o.parent = parent
    return o

def cyl(r, length, m, loc, axis='Z', name='cyl', parent=None, seg=48, shadow=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r * S, radius2=r * S, depth=length * S)
    rot = {'Z': Matrix.Identity(4), 'Y': Matrix.Rotation(pi / 2, 4, 'X'), 'X': Matrix.Rotation(pi / 2, 4, 'Y')}[axis]
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.use_auto_smooth = True; me.auto_smooth_angle = radians(35)
    for p in me.polygons: p.use_smooth = True
    me.materials.append(m)
    o = link(bpy.data.objects.new(name, me)); o.location = V(*loc); o.visible_shadow = shadow
    if parent: o.parent = parent
    return o

def rect(x0, x1, y0, y1, z0, z1, m, parent):          # igual que box, pero en metros (HUD)
    return box(x0 / S, x1 / S, y0 / S, y1 / S, z0 / S, z1 / S, m, 'hud', parent=parent, shadow=False)

def K(idb, path, frame, interp='BEZIER'):
    idb.keyframe_insert(path, frame=frame)
    for fc in idb.animation_data.action.fcurves:
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                if kp.co.x == frame: kp.interpolation = interp

# ---------- escena base ----------
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1920, 1080, FPS
sc.view_settings.view_transform = 'Standard'
ee = sc.eevee
ee.taa_render_samples = 48; ee.use_gtao = True; ee.gtao_distance = 0.04
ee.use_soft_shadows = True; ee.shadow_cube_size = '1024'; ee.shadow_cascade_size = '2048'
w = bpy.data.worlds.new('w'); w.use_nodes = True; sc.world = w
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = srgb('#EEF1F4'); bg.inputs[1].default_value = 0.6
sun = bpy.data.lights.new('sol', 'SUN'); sun.energy = 2.2; sun.angle = radians(6); sun.use_contact_shadow = False
so = link(bpy.data.objects.new('sol', sun)); so.rotation_euler = (radians(45), 0, radians(-100))

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 35; cam_d.clip_start = 0.01; cam_d.clip_end = 30
cam = link(bpy.data.objects.new('Camera', cam_d)); sc.camera = cam
tgt = empty('Objetivo')
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'

box(-3000, 3000, -3000, 3000, -2, 0, mat('#E6EAEF', 0.9), 'mesa')

# ---------- estructura ----------
wood, gui, ste = mat('#D9B77E', 0.7), mat(YEL, 0.5), mat('#AEB8C2', 0.35, 0.8)
GAP = (214, 402)                                 # hueco de largueros para la caja REVISION
box(-40, 490, 70, 90, 0, RH, wood, 'larguero+y')
box(-40, GAP[0], -90, -70, 0, RH, wood, 'larguero-y a')
box(GAP[1], 490, -90, -70, 0, RH, wood, 'larguero-y b')
box(-40, -20, -70, 70, 0, RH, wood, 'travesano')
box(470, 490, -70, 70, 0, 34, wood, 'travesano der')
bed = mat('#BFA37C', 0.8)                        # cama con muesca en la estacion
box(18, 436, -55, 55, RH, BED, bed, 'cama'); box(18, 436, 55, 82, RH, BED, bed, 'cama+y')
box(18, 218, -82, -55, RH, BED, bed, 'cama-y a'); box(388, 436, -82, -55, RH, BED, bed, 'cama-y b')
for (a, b) in ((10, 222), (392, 418)): box(a, b, 57, 60, BED, BED + 25, gui, 'guia+y')   # guias abiertas en la estacion
for (a, b) in ((10, 222), (410, 445)): box(a, b, -60, -57, BED, BED + 25, gui, 'guia-y')

# ---------- banda sin fin (UV a lo largo del lazo, dibujo en chevrones que se desplaza) ----------
def make_belt():
    Rc, seg = R + 0.4, 24
    pts = [(0, ZC + Rc)]
    pts += [(XL + Rc * cos(pi / 2 - pi * i / seg), ZC + Rc * sin(pi / 2 - pi * i / seg)) for i in range(seg + 1)]
    pts += [(Rc * cos(-pi / 2 - pi * i / seg), ZC + Rc * sin(-pi / 2 - pi * i / seg)) for i in range(seg)]
    n = len(pts); d = [math.dist(pts[i], pts[(i + 1) % n]) for i in range(n)]; L = sum(d)
    s = [0.0]
    for x in d[:-1]: s.append(s[-1] + x)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    vl = [bm.verts.new((x * S, -55 * S, z * S)) for x, z in pts]
    vr = [bm.verts.new((x * S, 55 * S, z * S)) for x, z in pts]
    for i in range(n):
        j = (i + 1) % n; f = bm.faces.new((vl[i], vl[j], vr[j], vr[i]))
        u0, u1 = s[i] / L, (s[j] / L if j else 1.0)
        for lp, (u, v) in zip(f.loops, [(u0, 0), (u1, 0), (u1, 1), (u0, 1)]): lp[uv].uv = (u, v)
    me = bpy.data.meshes.new('banda'); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    m = bpy.data.materials.new('banda'); m.use_nodes = True; nt = m.node_tree; N, Lk = nt.nodes, nt.links
    N['Principled BSDF'].inputs['Roughness'].default_value = 0.75
    sep = N.new('ShaderNodeSeparateXYZ'); Lk.new(N.new('ShaderNodeTexCoord').outputs['UV'], sep.inputs[0])
    off = N.new('ShaderNodeValue'); off.name = 'Offset'
    def Mt(op, a, b=None):
        n_ = N.new('ShaderNodeMath'); n_.operation = op
        for i, x in enumerate((a, b)):
            if x is None: continue
            if isinstance(x, (int, float)): n_.inputs[i].default_value = x
            else: Lk.new(x, n_.inputs[i])
        return n_.outputs[0]
    arg = Mt('ADD', Mt('MULTIPLY', sep.outputs[0], 25.0),
             Mt('MULTIPLY', Mt('ABSOLUTE', Mt('SUBTRACT', sep.outputs[1], 0.5)), 2.2))
    cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.interpolation = 'CONSTANT'
    cr.color_ramp.elements[0].color = srgb('#1B2431'); e = cr.color_ramp.elements.new(0.8); e.color = srgb('#3E4E63')
    Lk.new(Mt('FRACT', Mt('SUBTRACT', arg, off.outputs[0])), cr.inputs[0])
    Lk.new(cr.outputs[0], N['Principled BSDF'].inputs['Base Color'])
    me.materials.append(m)
    o = link(bpy.data.objects.new('banda', me))
    sd = o.modifiers.new('grosor', 'SOLIDIFY'); sd.thickness = 0.8 * S; sd.offset = 0
    return m, L

belt_m, BELT_L = make_belt()
PER = BELT_L / 25.0                                 # mm por periodo del dibujo

# ---------- rodillos y ejes ----------
pvc, capm, dark = mat('#DDE2E8', 0.5), mat('#C9A36A', 0.7), mat('#2A3340', 0.5, 0.3)
rollers = []
for nm, x in (('libre', 0), ('motriz', XL)):
    e = empty('rodillo ' + nm, V(x, 0, ZC)); rollers.append(e)
    cyl(R, 130, pvc, (0, 0, 0), 'Y', 'tubo', e)
    for sg in (-1, 1):
        cyl(14, 3, capm, (0, sg * 66.5, 0), 'Y', 'tapon', e)
        cyl(2.5, 3, dark, (8, sg * 69.5, 0), 'Y', 'tornillo', e)
    cyl(4, 190, ste, (0, 0, 0), 'Y', 'eje', e)

# motor N20 (lado -y, en el rodillo motriz)
cyl(6, 24, mat('#2A3340', 0.4, 0.6), (XL, -122, ZC), 'Y', 'motor N20')
box(XL - 6, XL + 6, -110, -96, ZC - 6, ZC + 6, mat('#AEB8C2', 0.3, 0.9), 'reductor N20')
cyl(5, 8, ste, (XL, -93, ZC), 'Y', 'acople')

# servo MG996R + paleta de 120 mm
PX, PY = 274.0, 100.0
box(PX - 10, PX + 10, 90, 130, 0, RH, mat(NAVY, 0.4), 'servo')
box(PX - 14, PX + 14, 96, 124, 28, 32, mat(NAVY, 0.4), 'servo orejas')
cyl(3, 8, ste, (PX, PY, RH + 4), 'Z', 'eje servo')
cyl(7, 2, mat('#F2F4F7', 0.4), (PX, PY, 45), 'Z', 'cuerno')
pad = empty('paleta', V(PX, PY, 0))
box(0, 120, -1.5, 1.5, 46, 71, mat(ORG, 0.5), 'paleta', parent=pad)
box(92, 120, -2.5, 2.5, 46, 71, mat('#C9A36A', 0.9), 'forro EVA', parent=pad)

# microswitch con palanca y rodillo (S1 abajo, S2 arriba)
def switch(name, px, py, d):
    box(px - 6, px + 6, py - 10 if d > 0 else py, py if d > 0 else py + 10, RH + 6, RH + 18, gui, name)
    piv = empty(name + ' palanca', V(px, py, 50.5))
    box(-1, 1, 0, 25 * d, -1.5, 1.5, dark, 'palanca', parent=piv)
    cyl(3, 4, dark, (0, 25 * d, 0), 'Z', 'rodillito', piv)
    return piv
S1X, S2X = 394.0, 428.0
S1, S2 = switch('S1', S1X, -64, +1), switch('S2', S2X, 64, -1)

# cajas de destino y rampa
def tray(name, x0, x1, y0, y1, h, color, low):
    m, t = mat(color, 0.6), 3
    box(x0, x1, y0, y1, 0, 3, m, name + ' fondo')
    for k, (a, b, c_, d_) in {'izq': (x0, x0 + t, y0, y1), 'der': (x1 - t, x1, y0, y1),
                              'atras': (x0, x1, y0, y0 + t), 'frente': (x0, x1, y1 - t, y1)}.items():
        box(a, b, c_, d_, 0, h - (5 if k == low else 0), m, name + ' ' + k)
tray('caja REVISION', 214, 400, -160, -58, 22, '#F08A3A', 'frente')
tray('caja OK', 524, 710, -55, 55, 22, '#34B26E', 'izq')
ramp = box(-28.3, 28.3, -45, 45, -1.5, 1.5, mat('#B5BEC8', 0.5), 'rampa')
ramp.location = V(495, 0, 34.5); ramp.rotation_euler = (0, radians(17.5), 0)

# ---------- texto ----------
FONT = bpy.data.fonts.load(r'C:\Windows\Fonts\arialbd.ttf')
def text(s, size, m, loc=(0, 0, 0), align='CENTER', parent=None, name='txt'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = s; cu.size = size * S; cu.font = FONT
    cu.align_x = align; cu.align_y = 'CENTER'; cu.materials.append(m)
    o = link(bpy.data.objects.new(name, cu)); o.location = V(*loc); o.visible_shadow = False
    if parent: o.parent = parent
    return o

def width(o, size, s):                              # ancho del texto en mm
    bpy.context.view_layer.update()
    return o.dimensions.x / S if o.dimensions.x > 0 else len(s) * size * 0.62

white, navy_e = mat('#FFFFFF', emit=True), mat(NAVY, emit=True)

# ---------- bloque rectangular de 172x84x12 mm, 300 g ----------
def make_block(name, stripe):
    b = box(-86, 86, -42, 42, -6, 6, mat('#AEB8C2', 0.4, 0.25), name, bevel=1.5)
    box(66, 82, -38, 38, 6, 6.4, mat(stripe, 0.5), 'franja', parent=b)
    text('300 g', 24, navy_e, (0, 0, 6.6), parent=b)
    return b
bR, bA = make_block('bloque R', ORG), make_block('bloque A', GRN)

# ---------- rotulos con linea guia ----------
labels = []
def label(txt, anchor, off, t_in, keep, pill):
    root = empty('rot ' + txt, V(*anchor)); ox, oy, oz = (off[i] - anchor[i] for i in range(3))
    off = (ox, oy, oz)
    t = text(txt, 18, white, off, parent=root, name='rotulo')
    k = t.constraints.new('TRACK_TO'); k.target = cam; k.track_axis = 'TRACK_Z'; k.up_axis = 'UP_Y'
    wd = width(t, 18, txt)
    box(-wd / 2 - 6, wd / 2 + 6, -9.5, 9.5, -0.8, -0.4, mat(pill, emit=True), 'pastilla', parent=t, shadow=False)
    L = math.sqrt(ox * ox + oy * oy + oz * oz)
    ln = cyl(0.6, L, navy_e, (ox / 2, oy / 2, oz / 2), 'Z', 'guia', root, seg=8, shadow=False)
    ln.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector((ox, oy, oz))).to_euler()
    cyl(2.2, 2.2, navy_e, (0, 0, 0), 'Z', 'punto', root, seg=12, shadow=False)
    root.scale = (0.001,) * 3; K(root, 'scale', 1, 'CONSTANT')
    labels.append((root, t_in, keep))

tour = [  # texto, punto de la pieza, posicion del rotulo (mm), queda en el recorrido, color de pastilla
    ('Bloque 300 g', (90, 0, 58), (40, 40, 150), False, NAVY),
    ('Rodillo libre Ø33', (-17, 20, 28), (-95, 70, 105), False, NAVY),
    ('Banda · 110 mm', (200, 20, TOP), (170, 60, 150), False, NAVY),
    ('Guías laterales', (140, -58.5, 62), (150, -130, 100), False, NAVY),
    ('Servo MG996R + paleta', (PX, 115, 38), (330, 175, 140), True, NAVY),
    ('Microswitch S1', (S1X, -68, 56), (440, -135, 62), True, NAVY),
    ('Caja REVISIÓN (humano)', (300, -160, 15), (290, -215, 45), True, ORG),
    ('Microswitch S2', (S2X, 70, 56), (470, 120, 200), True, NAVY),
    ('Rodillo motriz Ø33', (467, 10, 30), (560, 60, 130), False, NAVY),
    ('Motor N20', (XL, -125, 30), (530, -200, 60), False, NAVY),
    ('Caja OK', (640, -45, 20), (650, -90, 60), True, GRN),
    ('Estructura de madera', (-30, -80, 25), (-110, -95, 55), False, NAVY),
]
T_TOUR, T_GAP = 2.2, 0.62
for i, (txt, a, o, keep, pc) in enumerate(tour): label(txt, a, o, T_TOUR + i * T_GAP, keep, pc)
T_TOUR_END = T_TOUR + len(tour) * T_GAP + 1.4

# ---------- cronograma (s) ----------
T_R0 = T_TOUR_END + 0.8                          # arranca la banda: pasada R
T_R1 = T_R0 + (STOP_R - BX0) / SPEED             # el bloque llega a S1 y la banda frena
T_P0, T_P1 = T_R1 + 0.4, T_R1 + 1.5              # el servo empuja
T_F1 = T_P1 + 0.9                                # el bloque cae a la caja
T_B2 = T_F1 + 1.4                                # entra el 2.o bloque (A)
T_A0 = T_B2 + 1.0
T_A1 = T_A0 + (X_END - BX0) / SPEED              # S2 lo confirma ~1 s antes y la banda frena
T_F2 = T_A1 + 1.7
T_END = T_F2 + 3.2
sc.frame_start, sc.frame_end = 1, fr(T_END)

# ---------- animacion: banda y rodillos (misma ley de avance) ----------
TRAV = (STOP_R - BX0) + (X_END - BX0)
for t, b in [(0, 0.0), (T_R0, 0.0), (T_R1, STOP_R - BX0), (T_A0, STOP_R - BX0), (T_A1, TRAV), (T_END, TRAV)]:
    belt_m.node_tree.nodes['Offset'].outputs[0].default_value = b / PER
    K(belt_m.node_tree, 'nodes["Offset"].outputs[0].default_value', fr(t), 'LINEAR')
    for r in rollers:
        r.rotation_euler = (0, b / (R + 0.4), 0); K(r, 'rotation_euler', fr(t), 'LINEAR')

# ---------- animacion: bloques, paleta y palancas ----------
def put(o, x, y, z, t, rx=0, ry=0, interp='LINEAR'):
    o.location = V(x, y, z); o.rotation_euler = (radians(rx), radians(ry), 0)
    K(o, 'location', fr(t), interp); K(o, 'rotation_euler', fr(t), interp)

put(bR, BX0, 0, BZ, 0); put(bR, BX0, 0, BZ, T_R0); put(bR, STOP_R, 0, BZ, T_R1)
# la punta de la paleta (120 mm) baja el borde del bloque; contacto desde th0
th0 = math.asin((PY - 1.5 - 42) / 120)
def theta(t):
    if t < T_P1: return radians(90) * sm((t - T_P0) / (T_P1 - T_P0))
    return radians(90) * (1 - sm((t - (T_P1 + 0.2)) / 0.9))
pad.rotation_euler = (0, 0, 0); K(pad, 'rotation_euler', 1, 'LINEAR')
for fi in range(fr(T_P0) - 1, fr(T_P1 + 1.2) + 1, 2):
    t = (fi - 1) / FPS; th = theta(t)
    pad.rotation_euler = (0, 0, -th); K(pad, 'rotation_euler', fi, 'LINEAR')
    if T_P0 <= t <= T_P1: put(bR, STOP_R, min(0, PY - 120 * sin(th) - 1.5 - 42), BZ, t)
y_end = PY - 120 - 1.5 - 42
for dt, y, z, rx in ((0.0, y_end, BZ, 0), (0.25, y_end - 9, 50, 28), (0.55, y_end - 28, 40, 38), (0.9, -108, 9, 0)):
    put(bR, STOP_R, y, z, T_P1 + dt, rx=rx, interp='BEZIER')

for o_ in [bA] + list(bA.children):
    o_.hide_render = True; K(o_, 'hide_render', 1)
    o_.hide_render = False; K(o_, 'hide_render', fr(T_B2))
put(bA, BX0, 0, BZ + 110, T_B2, interp='BEZIER'); put(bA, BX0, 0, BZ, T_B2 + 0.3, interp='BEZIER')
put(bA, BX0, 0, BZ, T_A0); put(bA, X_END, 0, BZ, T_A1)
for dt, x, z, ry in ((0.0, X_END, BZ, 0), (0.35, 480, 48.5, 8), (0.8, 508, 40, 15), (1.15, 540, 27, 12), (1.7, 617, 9, 0)):
    put(bA, x, 0, z, T_A1 + dt, ry=ry, interp='BEZIER')

def lever(piv, sgn, x_front, px):                  # angulo = atan((x_frente - pivote)/22), entre -30 y +28 grados
    a = max(-30.0, min(28.0, math.degrees(atan((x_front - px) / 22.0))))
    piv.rotation_euler = (0, 0, radians(sgn * a))
for piv, sgn, px, t0, t1, rel in ((S1, -1, S1X, T_R0, T_R1, T_P1 + 0.2), (S2, +1, S2X, T_A0, T_A1, T_A1 + 0.3)):
    for fi in list(range(fr(t0), fr(t1), 3)) + [fr(t1)]:
        lever(piv, sgn, BX0 + ((fi - 1) / FPS - t0) * SPEED + 86, px); K(piv, 'rotation_euler', fi, 'LINEAR')
    K(piv, 'rotation_euler', fr(rel), 'LINEAR')
    lever(piv, sgn, -999, px); K(piv, 'rotation_euler', fr(rel) + 6, 'BEZIER'); K(piv, 'rotation_euler', 1, 'LINEAR')

# ---------- rotulos: aparecer y (los de pieza suelta) desaparecer ----------
for root, t_in, keep in labels:
    root.scale = (0.001,) * 3; K(root, 'scale', fr(t_in), 'LINEAR')
    root.scale = (1, 1, 1); K(root, 'scale', fr(t_in) + 8, 'BEZIER')
    if not keep:
        K(root, 'scale', fr(T_TOUR_END), 'LINEAR')
        root.scale = (0.001,) * 3; K(root, 'scale', fr(T_TOUR_END) + 8, 'BEZIER')

# ---------- camara: paneo suave alrededor de la banda ----------
WP = [(0, -50, 30, 0.85, 0.15, 0.03), (T_TOUR_END, -30, 36, 1.05, 0.29, 0.04), (T_P0, -24, 38, 1.06, 0.33, 0.04),
      (T_A0, -20, 38, 1.10, 0.42, 0.04), (T_END, -22, 36, 1.15, 0.38, 0.04)]
for fi in list(range(1, fr(T_END), 4)) + [fr(T_END)]:
    t = min((fi - 1) / FPS, T_END)
    for a, b in zip(WP, WP[1:]):
        if a[0] <= t <= b[0]:
            u = sm((t - a[0]) / (b[0] - a[0])); v = [a[i] + (b[i] - a[i]) * u for i in range(1, 6)]; break
    az, el, d, tx, tz = radians(v[0]), radians(v[1]), v[2], v[3], v[4]
    tgt.location = (tx, -0.04, tz); K(tgt, 'location', fi, 'LINEAR')
    cam.location = (tx + d * sin(az) * cos(el), -0.04 - d * cos(az) * cos(el), tz + d * sin(el)); K(cam, 'location', fi, 'LINEAR')

# ---------- HUD pegado a la camara (en metros, a 0.5 m del lente) ----------
HZ = -0.5
title = empty('titulo', (-0.235, 0.118, HZ), cam)
t1 = text('BANDA TRANSPORTADORA', 20, navy_e, (0, 0, 0), 'LEFT', title)
t2 = text('DE BAJO', 20, navy_e, (0, -21, 0), 'LEFT', title)
w2 = width(t2, 20, 'DE BAJO') * S + 0.0045
t3 = text('PRESUPUESTO', 20, navy_e, (0, -21, 0), 'LEFT', title); t3.location = (w2, -0.021, 0)
w3 = width(t3, 20, 'PRESUPUESTO') * S
rect(w2 - 0.0025, w2 + w3 + 0.0025, -0.0335, -0.0085, -0.0004, -0.0002, mat(YEL, emit=True), title)
title.scale = (1, 1, 1); K(title, 'scale', 1, 'LINEAR'); K(title, 'scale', fr(1.0), 'LINEAR')
title.scale = (0.5, 0.5, 0.5); K(title, 'scale', fr(1.8), 'BEZIER')

rect(-0.26, 0.26, -0.1446, -0.1126, HZ - 0.0002, HZ, mat(NAVY, emit=True), cam)
caps = [(1.0, T_TOUR_END, 'Una sola banda que se bifurca · estas son sus piezas'),
        (T_TOUR_END, T_B2 - 0.2, 'R = REVISIÓN · S1 frena la banda y el servo empuja el bloque a la caja'),
        (T_B2 - 0.2, T_F2 + 0.5, 'A = OK · sigue derecho, S2 confirma y cae a la caja OK'),
        (T_F2 + 0.5, T_END + 1, 'Una sola banda · dos destinos · 84 mm/s')]
for a, b, s in caps:
    ct = text(s, 10, white, (0, 0, 0), 'LEFT', cam, name='leyenda'); ct.location = (-0.245, -0.1286, HZ + 0.0002)
    ct.hide_render = True; K(ct, 'hide_render', 1)
    ct.hide_render = False; K(ct, 'hide_render', fr(a))
    ct.hide_render = True; K(ct, 'hide_render', fr(b))

bpy.ops.file.pack_all()
sc.render.filepath = os.path.join(OUT, 'banda_')
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'; sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'MEDIUM'; sc.render.ffmpeg.ffmpeg_preset = 'GOOD'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'banda_transportadora.blend'))
print('FRAMES', sc.frame_end, 'T', round(T_END, 1), 'tour_end', round(T_TOUR_END, 1), 'R', round(T_R0, 1), round(T_R1, 1),
      'push', round(T_P0, 1), round(T_P1, 1), 'B2', round(T_B2, 1), 'A', round(T_A0, 1), round(T_A1, 1))
