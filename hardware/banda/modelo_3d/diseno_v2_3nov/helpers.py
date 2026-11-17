"""Utilidades compartidas para los scripts de Blender 3.6 (1 BU = 1 m, coordenadas en mm).
Importar DESPUES de reiniciar la escena (bpy.ops.wm.read_factory_settings)."""
import bpy, bmesh, math
from math import pi, radians, cos, sin
from mathutils import Vector, Matrix

S, FPS = 0.001, 24
sc = bpy.context.scene

def fr(sec): return round(sec * FPS) + 1
def V(x, y, z): return Vector((x * S, y * S, z * S))
def sm(u): u = max(0, min(1, u)); return u * u * (3 - 2 * u)

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
    o.location = V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); o.visible_shadow = shadow
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL'); b.width = bevel * S; b.segments = 2; b.limit_method = 'ANGLE'
    if parent: o.parent = parent
    return o

def cyl(r, length, m, loc, axis='Z', name='cyl', parent=None, seg=32, shadow=True):
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

def rect(x0, x1, y0, y1, z0, z1, m, parent):          # como box pero en metros (HUD)
    return box(x0 / S, x1 / S, y0 / S, y1 / S, z0 / S, z1 / S, m, 'hud', parent=parent, shadow=False)

def K(idb, path, frame, interp='BEZIER'):
    idb.keyframe_insert(path, frame=frame)
    for fc in idb.animation_data.action.fcurves:
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                if kp.co.x == frame: kp.interpolation = interp

FONT = bpy.data.fonts.load(r'C:\Windows\Fonts\arialbd.ttf')
MONO = bpy.data.fonts.load(r'C:\Windows\Fonts\consola.ttf')

def text(s, size, m, loc=(0, 0, 0), align='CENTER', parent=None, name='txt', font=None, valign='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = s; cu.size = size * S; cu.font = font or FONT
    cu.align_x = align; cu.align_y = valign; cu.materials.append(m)
    o = link(bpy.data.objects.new(name, cu)); o.location = V(*loc); o.visible_shadow = False
    if parent: o.parent = parent
    return o

def width(o, size, s):                              # ancho del texto en mm
    bpy.context.view_layer.update()
    return o.dimensions.x / S if o.dimensions.x > 0 else len(s) * size * 0.62

def make_belt(zc, r, xl, name='banda'):
    """Banda sin fin (lazo en XZ, ancho 110 mm en Y) con dibujo de chevrones que se mueve
    animando el nodo 'Offset' (en periodos). Devuelve (objeto, material, largo_mm)."""
    Rc, seg = r + 0.4, 24
    pts = [(0, zc + Rc)]
    pts += [(xl + Rc * cos(pi / 2 - pi * i / seg), zc + Rc * sin(pi / 2 - pi * i / seg)) for i in range(seg + 1)]
    pts += [(Rc * cos(-pi / 2 - pi * i / seg), zc + Rc * sin(-pi / 2 - pi * i / seg)) for i in range(seg)]
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
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, Lk = nt.nodes, nt.links
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
    o = link(bpy.data.objects.new(name, me))
    sd = o.modifiers.new('grosor', 'SOLIDIFY'); sd.thickness = 0.8 * S; sd.offset = 0
    return o, m, L
