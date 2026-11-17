"""Modelo 3D del prototipo final de la banda (17-nov-2026) con medidas reales y servo MG90S.
Uso (lo hace RENDERIZAR_BANDA.bat):  blender -b -P banda_real.py -- [stills|video|todo] [borrador]
Arma la escena desde cero, guarda banda_real.blend y renderiza en la carpeta salida/:
  6 imágenes PNG 1920x1080 (stills) y un video MP4 de 10 s a 1080p y 60 fps (video).
Medidas en cm (DATOS_VERIFICADOS.md): tela 11,5 de ancho, tramo visible 34, estructura 45 x 10 de alto.
Compatible con Blender 3.6 LTS y 4.x (Eevee)."""
import bpy, math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(AQUI, "salida")
os.makedirs(SAL, exist_ok=True)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODO = args[0] if args else "todo"
BORRADOR = "borrador" in args
FPS, SEG = 60, 10
NF = FPS * SEG
C = 0.01  # 1 cm en metros

# ---------- escena limpia ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for motor in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = motor
        break
    except TypeError:
        pass
ee = sc.eevee
ee.taa_render_samples = 16 if BORRADOR else 64
for prop, val in (("use_gtao", True), ("use_soft_shadows", True), ("use_raytracing", True)):
    if hasattr(ee, prop):
        setattr(ee, prop, val)
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = 50 if BORRADOR else 100
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "Filmic" if bpy.app.version < (4, 0, 0) else "AgX"
mundo = bpy.data.worlds.new("cielo")
sc.world = mundo
mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.93, 0.90, 0.85, 1)
mundo.node_tree.nodes["Background"].inputs[1].default_value = 0.35
sc.view_settings.exposure = -0.8  # la mesa clara quemaba el gris Lego


def mat(nombre, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def hexa(h):
    h = h.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))


GRIS_LEGO = mat("lego_gris", hexa("A0A5A9"), 0.35)
NEGRO = mat("negro", hexa("1B1B1F"), 0.4)
AZUL_LEGO = mat("lego_azul", hexa("0055BF"), 0.35)
AMARILLO = mat("lego_amarillo", hexa("F2CD37"), 0.35)
BEIGE = mat("placa_beige", hexa("D9C69A"), 0.5)
CAUCHO = mat("caucho", hexa("202020"), 0.85)
BLANCO = mat("blanco", hexa("F2F2F2"), 0.5)
DORADO = mat("dorado", hexa("C9A227"), 0.3, 1.0)
METAL = mat("metal", hexa("C0C0C0"), 0.25, 1.0)
AZUL_PCB = mat("pcb_azul", hexa("0F5C9E"), 0.45)
AZUL_SERVO = mat("servo_azul", hexa("1F4FA3"), 0.4)
MADERA = mat("mesa", hexa("B89B78"), 0.7)
PANTALLA = mat("pantalla", hexa("0E1A2B"), 0.15)


def tex_mat(nombre, archivo, escala_x=1.0):
    """Material con imagen; devuelve (material, nodo Mapping) para animar el avance de la tela."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.8
    ruta = os.path.join(AQUI, "tex", archivo)
    if not os.path.exists(ruta):
        b.inputs["Base Color"].default_value = (0.95, 0.95, 0.93, 1)
        return m, None
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(ruta)
    img.extension = "REPEAT"
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value[0] = escala_x
    nt.links.new(coord.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], img.inputs["Vector"])
    nt.links.new(img.outputs["Color"], b.inputs["Base Color"])
    return m, mp


TELA, MAP_TELA = tex_mat("tela", "banda_tela.png", 1.0)
PROTO, _ = tex_mat("protoboard", "protoboard.png")


def caja(n, x0, x1, y0, y1, z0, z1, m, bisel=0.15):
    bpy.ops.mesh.primitive_cube_add(location=((x0 + x1) / 2 * C, (y0 + y1) / 2 * C, (z0 + z1) / 2 * C))
    o = bpy.context.object
    o.name = n
    o.scale = ((x1 - x0) / 2 * C, (y1 - y0) / 2 * C, (z1 - z0) / 2 * C)
    bpy.ops.object.transform_apply(scale=True)
    if bisel:
        mod = o.modifiers.new("bisel", "BEVEL")
        mod.width = bisel * C
        mod.segments = 2
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def cil(n, r, largo, pos, m, eje="Z", seg=40):
    rot = {"Z": (0, 0, 0), "X": (0, math.pi / 2, 0), "Y": (math.pi / 2, 0, 0)}[eje]
    bpy.ops.mesh.primitive_cylinder_add(radius=r * C, depth=largo * C, vertices=seg,
                                        location=tuple(v * C for v in pos), rotation=rot)
    o = bpy.context.object
    o.name = n
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def viga_technic(n, x0, x1, y, z, m=GRIS_LEGO, eje="X"):
    """Viga Technic de 0,8 cm con agujeros cada 0,8 cm (paso Lego)."""
    if eje == "X":
        v = caja(n, x0, x1, y - 0.4, y + 0.4, z - 0.36, z + 0.36, m, 0.1)
        k = x0 + 0.4
        while k < x1 - 0.2:
            cil(n + "_ag", 0.24, 0.82, (k, y, z), NEGRO, "Y", 16)
            k += 0.8
    else:
        v = caja(n, y - 0.4, y + 0.4, x0, x1, z - 0.36, z + 0.36, m, 0.1)
    return v


# ---------- medidas ----------
LARGO, ANCHO, ALTO = 45.0, 11.5, 10.0
XA, XB = 5.5, 39.5           # ejes de los rodillos: 34 cm de tramo visible
ZR, RR = 8.2, 1.6            # altura del eje y radio de los rodillos
ZT = ZR + RR                 # cara superior de la tela
X_SERVO = XA + 0.47 * (XB - XA)
X_S1 = X_SERVO - 4.0

# ---------- mesa y estructura ----------
caja("mesa", -40, 90, -45, 50, -1, 0, MADERA, 0)
for y in (-0.9, ANCHO + 0.9):
    viga_technic("viga_sup", 0, LARGO, y, ZR, GRIS_LEGO)
    viga_technic("viga_inf", 1, LARGO - 1, y, 2.0, GRIS_LEGO)
    for x in (2.0, 22.5, 43.0):
        caja("pata", x - 0.4, x + 0.4, y - 0.4, y + 0.4, 0, ZR, GRIS_LEGO, 0.1)
for x in (2.0, 43.0):
    caja("travesano", x - 0.4, x + 0.4, -0.9, ANCHO + 0.9, 1.6, 2.4, AZUL_LEGO, 0.1)

# ---------- rodillos y tela ----------
rodillos = []
for x in (XA, XB):
    eje = cil("eje_palillo", 0.2, ANCHO + 4, (x, ANCHO / 2, ZR), mat("palillo", hexa("D8B98A"), 0.6), "Y")
    rod = cil("rodillo", RR - 0.35, ANCHO - 0.4, (x, ANCHO / 2, ZR), BLANCO, "Y")
    for y in (0.6, ANCHO - 0.6):
        cil("llanta", RR, 1.2, (x, y, ZR), CAUCHO, "Y")
    rodillos.append(rod)
tela_sup = caja("tela_superior", XA, XB, 0, ANCHO, ZT - 0.16, ZT, TELA, 0.05)
caja("tela_inferior", XA, XB, 0, ANCHO, ZR - RR, ZR - RR + 0.16, TELA, 0.05)
for x in (XA, XB):
    bpy.ops.mesh.primitive_cylinder_add(radius=(RR + 0.08) * C, depth=ANCHO * C, vertices=48,
                                        location=(x * C, ANCHO / 2 * C, ZR * C), rotation=(math.pi / 2, 0, 0))
    o = bpy.context.object
    o.name = "tela_curva"
    o.data.materials.append(TELA)
    bpy.ops.object.shade_smooth()

# ---------- motor N20 ----------
caja("n20_caja", XB + 2.4, XB + 3.6, ANCHO + 1.5, ANCHO + 2.5, ZR - 0.5, ZR + 0.5, DORADO, 0.05)
cil("n20_motor", 0.5, 1.5, (XB + 3.0, ANCHO + 3.25, ZR), METAL, "Y")
cil("n20_eje", 0.15, 2.0, (XB + 3.0, ANCHO + 0.8, ZR), METAL, "Y")

# ---------- servo MG90S y brazo ----------
caja("servo_mg90s", X_SERVO - 1.13, X_SERVO + 1.13, -3.2, -2.0, ZR - 1.1, ZR + 1.1, AZUL_SERVO, 0.08)
caja("servo_orejas", X_SERVO - 1.6, X_SERVO + 1.6, -3.2, -2.0, ZR + 0.5, ZR + 0.7, AZUL_SERVO, 0.04)
bpy.ops.object.empty_add(location=(X_SERVO * C, -1.2 * C, (ZT + 0.8) * C))
pivote = bpy.context.object
pivote.name = "pivote_compuerta"
brazo = caja("brazo_viga", -0.4, 0.4, 0, ANCHO + 1.0, -0.36, 0.36, GRIS_LEGO, 0.1)
brazo.location = (0, (ANCHO + 1.0) / 2 * C, 0)  # relativo al pivote: la viga cruza la tela
brazo.parent = pivote
pieza_t = caja("pieza_T", -1.2, 1.2, -0.4, 0.4, -0.36, 0.36, NEGRO, 0.1)
pieza_t.parent = pivote
cil("cuerno_servo", 0.5, 0.4, (X_SERVO, -1.2, ZT + 0.3), BLANCO)

# ---------- sensor S1: dos microswitches ----------
for k, y in enumerate((0.6, 2.0)):
    caja("microswitch", X_S1 - 0.6, X_S1 + 0.6, y - 0.3, y + 0.3, ZT - 0.9, ZT - 0.1, NEGRO, 0.05)
    palanca = caja("palanca", X_S1 - 0.9, X_S1 + 0.5, y - 0.05, y + 0.05, ZT - 0.1, ZT + 0.25, METAL, 0)

# ---------- electrónica al frente ----------
caja("placa_lego", 2, 30, -16, -5, 0, 0.35, BEIGE, 0.05)
for i in range(28):
    for j in range(11):
        if (i + j) % 2 == 0:
            cil("tetón", 0.24, 0.17, (2.4 + i, -15.6 + j, 0.43), BEIGE, "Z", 12)
caja("arduino", 9, 15.9, -14.5, -9.2, 0.35, 0.5, AZUL_PCB, 0.05)
caja("arduino_usb", 8.4, 10.2, -13.8, -12.6, 0.5, 1.6, METAL, 0.05)
caja("arduino_chip", 12.5, 15.3, -12.6, -11.8, 0.5, 0.8, NEGRO, 0.02)
caja("protoboard", 19, 35.5, -13, -7.5, 0, 0.9, PROTO, 0.1)
caja("esp32", 38, 43.5, -12.5, -9.7, 0, 0.5, NEGRO, 0.05)
caja("esp32_modulo", 41, 43.3, -12.3, -9.9, 0.5, 0.8, METAL, 0.03)
for k, (col, y) in enumerate((("D93A3A", -9.5), ("2EA043", -10.0), ("F2CD37", -10.5), ("1F6FEB", -11.0))):
    curva = bpy.data.curves.new("cable", "CURVE")
    curva.dimensions = "3D"
    curva.bevel_depth = 0.06 * C
    sp = curva.splines.new("BEZIER")
    sp.bezier_points.add(1)
    p0, p1 = sp.bezier_points
    p0.co = (15.5 * C, y * C, 0.6 * C)
    p1.co = ((20 + k * 4) * C, -8 * C, 0.9 * C)
    p0.handle_right = (17 * C, y * C, 4 * C)
    p1.handle_left = ((19 + k * 4) * C, -8 * C, 4 * C)
    p0.handle_left, p1.handle_right = p0.co, p1.co
    o = bpy.data.objects.new("cable", curva)
    sc.collection.objects.link(o)
    o.data.materials.append(mat("cable_%d" % k, hexa(col), 0.5))

# ---------- celular de prueba (~300 g, 16 x 7,5 x 0,9 cm) ----------
cel = caja("celular", -8, 8, -3.75, 3.75, 0, 0.9, NEGRO, 0.6)
pant = caja("pantalla", -7.6, 7.6, -3.4, 3.4, 0.9, 0.93, PANTALLA, 0.4)
pant.parent = cel
cel_y = ANCHO / 2

# ---------- luces ----------
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), math.radians(10), math.radians(35)))
bpy.context.object.data.energy = 2.2
bpy.context.object.data.angle = math.radians(8)
bpy.ops.object.light_add(type="AREA", location=(0.2, -0.5, 0.6))
luz = bpy.context.object
luz.data.energy = 120
luz.data.size = 0.6
luz.rotation_euler = (math.radians(55), 0, math.radians(-15))

# ---------- animación (10 s) ----------
# 0-4 s: el celular avanza hasta S1 · 4,5 s: la compuerta gira a 33° (revisión)
# 4,5-8 s: el celular se desvía hacia el borde · 9 s: la compuerta vuelve a 0°
def k(o, ruta, t, val, i=None):
    f = round(t * FPS) + 1
    if i is None:
        setattr(o, ruta, val)
        o.keyframe_insert(ruta, frame=f)
    else:
        getattr(o, ruta)[i] = val
        o.keyframe_insert(ruta, index=i, frame=f)


VEL = 4.5  # cm/s, velocidad aproximada de la banda (no medida)
x_ini = XA + 8.0
x_tope = X_SERVO - 0.4 - 8.0
for t, x, y, rz in ((0, x_ini, cel_y, 0), ((x_tope - x_ini) / VEL, x_tope, cel_y, 0), (4.6, x_tope, cel_y, 0),
                    (8.0, x_tope + 7.0, -3.0, -28), (10, x_tope + 7.5, -3.5, -28)):
    k(cel, "location", t, x * C, 0)
    k(cel, "location", t, y * C, 1)
    k(cel, "location", t, (ZT + 0.02 if y > 0 else ZT - 0.6) * C, 2)
    k(cel, "rotation_euler", t, math.radians(rz), 2)
k(pivote, "rotation_euler", 0, 0.0, 2)
k(pivote, "rotation_euler", 4.0, 0.0, 2)
k(pivote, "rotation_euler", 4.6, math.radians(-33), 2)
k(pivote, "rotation_euler", 8.6, math.radians(-33), 2)
k(pivote, "rotation_euler", 9.2, 0.0, 2)
for r in rodillos:
    k(r, "rotation_euler", 0, 0.0, 1)
    k(r, "rotation_euler", 10, VEL * 10 / RR, 1)
if MAP_TELA:
    MAP_TELA.inputs["Location"].default_value[0] = 0
    MAP_TELA.inputs["Location"].keyframe_insert("default_value", index=0, frame=1)
    MAP_TELA.inputs["Location"].default_value[0] = -VEL * 10 / (XB - XA)
    MAP_TELA.inputs["Location"].keyframe_insert("default_value", index=0, frame=NF)
for o in list(bpy.data.objects) + [TELA.node_tree]:
    ad = o.animation_data
    if ad and ad.action:
        act = ad.action  # Blender 4.4+ guarda las curvas en capas (channelbags)
        fcs = act.fcurves if hasattr(act, "fcurves") else [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER" if o.name.startswith(("pivote", "celular", "video")) else "LINEAR"

# ---------- cámaras ----------
def camara(n, pos, mira, lente=35):
    bpy.ops.object.camera_add(location=tuple(v * C for v in pos))
    cam = bpy.context.object
    cam.name = n
    cam.data.lens = lente
    bpy.ops.object.empty_add(location=tuple(v * C for v in mira))
    obj = bpy.context.object
    obj.name = n + "_mira"
    t = cam.constraints.new("TRACK_TO")
    t.target = obj
    t.track_axis, t.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return cam, obj


STILLS = [  # nombre, posición, mira, lente, segundo de la animación
    ("01_vista_general", (-20, -45, 42), (22, 0, 5), 32, 2.0),
    ("02_cenital_plano", (22.5, -2, 95), (22.5, -2, 0), 35, 0.0),
    ("03_compuerta_detalle", (X_SERVO - 14, -16, 22), (X_SERVO, 3, ZT), 50, 6.0),
    ("04_lateral", (22.5, -70, 12), (22.5, 0, 6), 40, 3.0),
    ("05_electronica", (20, -38, 25), (22, -11, 0), 45, 1.0),
    ("06_celular_desviado", (60, -30, 35), (X_SERVO, 0, ZT), 40, 8.5),
]
for n, pos, mira, lente, _ in STILLS:
    camara(n, pos, mira, lente)

cam_v, mira_v = camara("video", (-25, -50, 40), (20, 0, 6), 32)
for t, pos, mira in ((0, (-25, -50, 40), (20, 0, 6)), (4.5, (0, -42, 30), (X_SERVO, 2, ZT)),
                     (7.5, (40, -40, 32), (X_SERVO + 4, -2, ZT)), (10, (65, -35, 38), (25, 0, 6))):
    for i in range(3):
        k(cam_v, "location", t, pos[i] * C, i)
        k(mira_v, "location", t, mira[i] * C, i)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(AQUI, "banda_real.blend"))

# ---------- render ----------
if MODO in ("stills", "todo", "una"):
    sc.render.image_settings.file_format = "PNG"
    for n, _, _, _, seg in (STILLS[:1] + STILLS[2:3] if MODO == "una" else STILLS):
        sc.camera = bpy.data.objects[n]
        sc.frame_set(round(seg * FPS) + 1)
        sc.render.filepath = os.path.join(SAL, "render_%s.png" % n)
        bpy.ops.render.render(write_still=True)
        print("LISTO", sc.render.filepath)
if MODO in ("video", "todo"):
    sc.camera = cam_v
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.filepath = os.path.join(SAL, "banda_real_10s_1080p60_")
    bpy.ops.render.render(animation=True)
    print("LISTO video en", SAL)
