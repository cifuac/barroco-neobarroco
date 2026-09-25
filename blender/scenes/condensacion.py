"""N3 · Condensación — la figura 3 de Sarduy con el lector dentro.

Figura 3 (Sarduy 1972, l. 322-327), dos esquemas lado a lado:
  · «Permutación»: [Fonema¹… Fonema²… etc.] bajo un corchete = «Significante¹»; [F¹… F²… etc.] bajo otro
    corchete = «Snte.²»; ambos sobre UNA barra larga; debajo, «Significado».
  · «Condensación»: «Snte.¹» ⇄ signo central «Snte.³ / Sdo.» ⇄ «Snte.²» (un par de flechas opuestas
    entre cada extremo y el centro: la superior entra al centro, la inferior vuelve al extremo).

Estados:
  0 Figura 3 literal (tele frontal): letras de la figura como geometría (tinta; Significado/Sdo. en oro), trazos finos.
  1 Permutación en volumen: tablillas-letra sobre plintos bajos; y/ll se intercambian («vaya un gallo» → «valla
    un gayo», lectura docente de «O se me valla un gayo», l. 341); el Significado (tablilla de oro) no se mueve.
  2 Condensación: letras viajan desde AMO y desde ESCLAVO y componen AMOSCLAVO; los laterales PERMANECEN
    («puesta en escena», l. 399-404).
  3 El lector dentro: 24 listones de perfil trapezoidal sobre la barra y el Sdo.; caras izquierdas AMO,
    derechas ESCLAVO, de frente AMOSCLAVO (texto como geometría proyectada desde la posición del lector).
    Slider de azimut. AMO y ESCLAVO (los laterales) entran en el dispositivo y dejan la escena.
  4 MAQUINOSCRITO: el mismo mecanismo con MÁQUINA / MANUSCRITO (l. 341-342).

Dirección de arte («lámina de museo»): trazos finos, sólidos delgados con bisel pequeño, oro sólo para el
Significado, grafito para los significantes, esmeralda para los trayectos; rótulos grabados en los plintos en
lugar de etiquetas pegadas. Todo se posa en un mismo piso (PISO, medido en tools/pisos.json).

Nota: el tercer término (l. 320-321) no es el «cuarto elemento» de Cruz-Diez (l. 358-359).
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bb
import bpy, bmesh
from mathutils import Vector, Matrix

S = bb.Escena('condensacion', 'Permutación y condensación: la figura 3 con el lector dentro', dur=12.3)
M = bb.mat
TINY = 0.0001
T3 = (TINY, TINY, TINY)
C = 'CONSTANT'
LIN = 'LINEAR'
FPS = bb.FPS

# tipografía: Big Caslon (pariente de la Libre Caslon de la presentación); cifras voladas de Times (de caja alta:
# las elzevirianas de Caslon/Georgia hacen que el «1» volado se lea como una «I»); títulos en Georgia cursiva.
_F_CASLON = '/System/Library/Fonts/Supplemental/BigCaslon.ttf'
_F_TIMES = '/System/Library/Fonts/Supplemental/Times New Roman.ttf'
FUENTE = _F_CASLON if os.path.exists(_F_CASLON) else bb.FUENTES['serif']
F_NUM = _F_TIMES if os.path.exists(_F_TIMES) else bb.FUENTES['serif']
F_ITAL = bb.FUENTES['serif_it']

PISO = -0.254        # z del piso de toda la escena (base de las tablillas de oro): ver tools/pisos.json


# ================================================================ materiales
def mat_propio(nombre, hexcol, rough=0.6, metal=0.0):
    """Material liso con color propio (rol «otro» en estudio.js: conserva color y rugosidad)."""
    if nombre in bb._MATS:
        return bb._MATS[nombre]
    m = bpy.data.materials.new(nombre)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = bb.lin(hexcol)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    m.diffuse_color = bb.lin(hexcol)
    bb._MATS[nombre] = m
    return m


INK = M('soporte', 'grafito_linea')     # trazos y corchetes: tinta
BARRA = M('soporte', 'grafito_barra')   # la barra de la fracción: tinta
LACA = M('significante')                # letras-significante en volumen: grafito lacado
# oro liso (sin la trama del pan de oro, que en tablillas de 1 m se leía como azulejos) y letras de tinta mate
# (de frente, la laca reflejaba el estudio y la figura se veía gris): rol «otro» + ajustes en S.estudio.
ORO = mat_propio('dorado_tablilla', '#D8AE48', 0.32, 0.85)
ORO_L = mat_propio('dorado_letra', '#8A650C', 0.6, 0.15)
TINTA_L = mat_propio('letra_tinta', '#232220', 0.85)
ESM = M('trayecto')                     # trayectos y relaciones: esmeralda
TESELA = mat_propio('tesela_piedra', '#ECE6DB', 0.55)
PLINTO = mat_propio('plinto_piedra', '#DED7CB', 0.7)
LISTON = mat_propio('liston_piedra', '#F0EBE2', 0.6)
TABLERO = mat_propio('tablero_piedra', '#E2DBCF', 0.85)
S.estudio = {'materiales': {
    'dorado_tablilla': {'color': '#DDB34C', 'metalness': 0.85, 'roughness': 0.3, 'clearcoat': 0.4, 'clearcoatRoughness': 0.15,
                        'envMapIntensity': 1.7, 'emissive': '#B8891A', 'emissiveIntensity': 0.45},
    'dorado_letra': {'color': '#8A650C', 'metalness': 0.15, 'roughness': 0.6, 'envMapIntensity': 0.35,
                     'emissive': '#5A420A', 'emissiveIntensity': 0.15},
    'grafito_barra': {'roughness': 0.55, 'clearcoat': 0.25, 'clearcoatRoughness': 0.3, 'envMapIntensity': 0.5},
    'letra_tinta': {'color': '#232220', 'roughness': 0.85, 'metalness': 0, 'envMapIntensity': 0.25},
    'tesela_piedra': {'color': '#ECE6DB', 'roughness': 0.55, 'clearcoat': 0.25, 'clearcoatRoughness': 0.35, 'envMapIntensity': 0.8},
    'plinto_piedra': {'color': '#DED7CB', 'roughness': 0.7, 'clearcoat': 0.15, 'clearcoatRoughness': 0.4, 'envMapIntensity': 0.7},
    'liston_piedra': {'color': '#F0EBE2', 'roughness': 0.6, 'clearcoat': 0.2, 'clearcoatRoughness': 0.35, 'envMapIntensity': 0.8},
    'tablero_piedra': {'color': '#E2DBCF', 'roughness': 0.85, 'envMapIntensity': 0.6},
}}


# ================================================================ helpers locales (no tocan bb.py)
def malla(nombre, verts, caras, material=None, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in caras])
    me.update()
    try:
        me.shade_flat()
    except Exception:
        for p in me.polygons:
            p.use_smooth = False
    if material:
        me.materials.append(material)
    ob = bpy.data.objects.new(nombre, me)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def tubo(nombre, pts, r, material, parent=None, segs=10):
    """Tubo barrido a lo largo de una polilínea (sin torsión)."""
    pts = [Vector(p) for p in pts]
    bm = bmesh.new()
    anillos = []
    n = len(pts)
    for i, p in enumerate(pts):
        if i == 0:
            tg = (pts[1] - pts[0]).normalized()
        elif i == n - 1:
            tg = (pts[-1] - pts[-2]).normalized()
        else:
            tg = ((pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()).normalized()
        ref = Vector((0, 1, 0)) if abs(tg.y) < 0.9 else Vector((1, 0, 0))
        u = tg.cross(ref).normalized()
        v = tg.cross(u).normalized()
        anillos.append([bm.verts.new(p + r * (math.cos(2 * math.pi * k / segs) * u + math.sin(2 * math.pi * k / segs) * v))
                        for k in range(segs)])
    for a, b in zip(anillos[:-1], anillos[1:]):
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    bm.faces.new(list(reversed(anillos[0])))
    bm.faces.new(anillos[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bb._obj_from_bm(nombre, bm, material, parent)


def centrar_origen(ob):
    """Lleva el origen al centro de la caja envolvente (para que escale en su sitio)."""
    vs = [v.co for v in ob.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    c = (lo + hi) / 2
    for v in ob.data.vertices:
        v.co -= c
    ob.location = Vector(ob.location) + c
    return ob


def corchete(nombre, x0, x1, zb, zt, r=0.006, rc=0.03, material=None, parent=None, y=0.0):
    """Corchete inferior con ganchos hacia arriba y esquinas redondeadas (plano XZ)."""
    pts = [(x0, y, zt)]
    for k in range(9):  # esquina izquierda
        a = math.radians(180 + 90 * k / 8)
        pts.append((x0 + rc + rc * math.cos(a), y, zb + rc + rc * math.sin(a)))
    for k in range(9):  # esquina derecha
        a = math.radians(270 + 90 * k / 8)
        pts.append((x1 - rc + rc * math.cos(a), y, zb + rc + rc * math.sin(a)))
    pts.append((x1, y, zt))
    return centrar_origen(tubo(nombre, pts, r, material, parent))


def flecha(nombre, a, b, r=0.0045, rc=0.015, lc=0.065, material=None, parent=None):
    """Flecha fina (asta + punta esbelta) en un grupo con origen en la cola: escalar el grupo la hace crecer."""
    a, b = Vector(a), Vector(b)
    g = bb.grupo(nombre, tuple(a), parent)
    d = b - a
    u = d.normalized()
    base = u * (d.length - lc)
    tubo(nombre + '_asta', [(0, 0, 0), tuple(base + u * 0.006)], r, material, g)
    bb.cono(nombre + '_punta', tuple(base), tuple(d), r=rc, material=material, parent=g)
    return g


def reparentar(ob, padre):
    """Cuelga ob (sin padre, sin giro) de un grupo sin giro ni escala, conservando su posición."""
    ob.parent = padre
    ob.location = Vector(ob.location) - Vector(padre.location)


# ---------------------------------------------------------------- texto como geometría
RES_TEXTO = 4


def texto_malla(nombre, cuerpo, size=1.0, extrude=0.0, fuente=FUENTE, res=RES_TEXTO):
    """Como bb.texto (curva de texto → malla), con resolución de curva controlada para el peso del GLB."""
    cu = bpy.data.curves.new(nombre, 'FONT')
    cu.body = cuerpo
    cu.size = size
    cu.extrude = extrude
    cu.align_x = 'LEFT'
    cu.align_y = 'CENTER'
    cu.resolution_u = res
    cu.font = bpy.data.fonts.load(fuente, check_existing=True)
    ob = bpy.data.objects.new(nombre, cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active


_CAPS = {}


def cap_de(fuente):
    """(línea de base, altura de la H) de la fuente a tamaño 1."""
    if fuente not in _CAPS:
        ob = texto_malla('_refH', 'H', size=1.0, extrude=0.0, fuente=fuente)
        ys = [v.co.y for v in ob.data.vertices]
        me = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
        _CAPS[fuente] = (min(ys), max(ys) - min(ys))
    return _CAPS[fuente]


def glifos(cuerpo, cap, extrude, fuente=FUENTE):
    """Devuelve (lista de glifos, ancho total, x0). Cada glifo: dict(cx, x0, x1, verts, caras) con verts en
    coordenadas del texto (x, y, z), línea de base en y=0; se agrupan componentes que se solapan en x (tildes)."""
    base1, cap1 = cap_de(fuente)
    size = cap / cap1
    ob = texto_malla('_tmp', cuerpo, size=size, extrude=extrude, fuente=fuente)
    me = ob.data
    base = base1 * size
    V = [Vector((v.co.x, v.co.y - base, v.co.z)) for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    padre = list(range(len(V)))

    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a
    for f in F:
        r0 = raiz(f[0])
        for v in f[1:]:
            rv = raiz(v)
            if rv != r0:
                padre[rv] = r0
    comp = {}
    for i, f in enumerate(F):
        comp.setdefault(raiz(f[0]), []).append(i)
    partes = []
    for fs in comp.values():
        vs = sorted({v for i in fs for v in F[i]})
        xs = [V[v].x for v in vs]
        partes.append([min(xs), max(xs), fs])
    partes.sort(key=lambda p: p[0])
    grupos = []
    for p in partes:
        if grupos and p[0] < grupos[-1][1] - 0.15 * (p[1] - p[0]) and p[1] <= grupos[-1][1] + 0.3 * (grupos[-1][1] - grupos[-1][0]):
            g = grupos[-1]
            g[0], g[1] = min(g[0], p[0]), max(g[1], p[1])
            g[2] = g[2] + p[2]
        else:
            grupos.append([p[0], p[1], list(p[2])])
    out = []
    for x0, x1, fs in grupos:
        vs = sorted({v for i in fs for v in F[i]})
        idx = {v: k for k, v in enumerate(vs)}
        out.append(dict(cx=(x0 + x1) / 2, x0=x0, x1=x1, verts=[V[v].copy() for v in vs],
                        caras=[tuple(idx[v] for v in F[i]) for i in fs]))
    ancho = out[-1]['x1'] - out[0]['x0']
    return out, ancho, out[0]['x0']


def de_pie(v, cx):
    """(x, y, z) del texto → objeto de pie en XZ mirando a -Y, origen en (cx, base)."""
    return (v.x - cx, -v.z, v.y)


def palabra_objetos(nombre, cuerpo, cap, extrude, material, parent, loc, fuente=FUENTE):
    """Palabra de pie centrada en loc (línea de base en loc.z); un objeto por letra. Devuelve [(obj, cx_rel)]."""
    gl, ancho, x0 = glifos(cuerpo, cap, extrude, fuente)
    xc = x0 + ancho / 2
    res = []
    for k, g in enumerate(gl):
        ob = malla(f'{nombre}_{k}', [de_pie(v, g['cx']) for v in g['verts']], g['caras'], material, parent,
                   (loc[0] + g['cx'] - xc, loc[1], loc[2]))
        res.append((ob, g['cx'] - xc))
    return res, ancho


def glifo_unico(nombre, cuerpo, cap, extrude, material, parent, loc, fuente=FUENTE):
    """Varios caracteres como un solo objeto (p. ej. «LL»), centrado en x, base en loc.z."""
    gl, ancho, x0 = glifos(cuerpo, cap, extrude, fuente)
    xc = x0 + ancho / 2
    verts, caras = [], []
    for g in gl:
        n0 = len(verts)
        verts += [de_pie(v, xc) for v in g['verts']]
        caras += [tuple(n0 + i for i in f) for f in g['caras']]
    return malla(nombre, verts, caras, material, parent, loc), ancho


def palabra_plana_bm(cuerpo, cap, fuente=FUENTE):
    """Palabra plana (sin grosor) como bmesh en el plano del tablero: vértices (x, 0, z), base en z=0, centrada en x=0."""
    gl, ancho, x0 = glifos(cuerpo, cap, 0.0, fuente)
    xc = x0 + ancho / 2
    bm = bmesh.new()
    for g in gl:
        vv = [bm.verts.new((v.x - xc, 0.0, v.y)) for v in g['verts']]
        for f in g['caras']:
            try:
                bm.faces.new([vv[i] for i in f])
            except ValueError:
                pass
    bm.verts.ensure_lookup_table()
    return bm, ancho


# renglones con cifras voladas: tramos (texto, fuente, escala, subida, espacio_antes) — subida y espacio en «caps»
def T(txt, esp=0.0):
    return (txt, FUENTE, 1.0, 0.0, esp)


def SUP(d, esp=0.045):
    return (d, F_NUM, 0.6, 0.5, esp)


ESP = 0.36   # espacio entre palabras (en alturas de mayúscula)


def renglon(nombre, tramos, cap, material, centro, parent=None, extrude=0.003):
    """Renglón de pie (plano XZ, mirando a -Y) centrado en `centro` (x, y, z del centro óptico: base = z − cap/2)."""
    verts, caras = [], []
    cur = 0.0
    for txt, fuente, esc, subida, esp in tramos:
        gl, ancho, x0 = glifos(txt, cap * esc, extrude, fuente)
        cur += esp * cap
        dx = cur - x0
        for g in gl:
            n0 = len(verts)
            verts += [Vector((v.x + dx, v.y + subida * cap, v.z)) for v in g['verts']]
            caras += [tuple(n0 + i for i in f) for f in g['caras']]
        cur += ancho
    xs = [v.x for v in verts]
    xc = (min(xs) + max(xs)) / 2
    ob = malla(nombre, [de_pie(v, xc) for v in verts], caras, material, None,
               (centro[0], centro[1], centro[2] - cap / 2))
    if parent is not None:
        reparentar(ob, parent)
    return ob


def inscripcion(nombre, tramos, cap, material, cara_y, zc, parent, x=0.0, relieve=0.0012):
    """Rótulo grabado sobre la cara frontal (y = cara_y) de un sólido, en coordenadas locales de `parent`."""
    ob = renglon(nombre, tramos, cap, material, (x, cara_y - relieve - 0.0004, zc), None, extrude=relieve)
    ob.parent = parent
    return ob


# ---------------------------------------------------------------- animación
# Blender 5.x ignora preferences.edit.keyframe_new_interpolation_type en keyframe_insert: se registra la
# interpolación deseada de cada clave y se aplica al final (sin tocar bb.py).
_INTERP = {}
_clave_bb = S.clave


def _clave(ob, t, loc=None, rot=None, esc=None, interp=None):
    _clave_bb(ob, t, loc=loc, rot=rot, esc=esc, interp=interp)
    fr = S.f(t)
    for dp, val in (('location', loc), ('rotation_euler', rot), ('scale', esc)):
        if val is not None:
            _INTERP[(ob.name, dp, fr)] = interp or 'BEZIER'


S.clave = _clave


def saltar(ob, t, antes, despues):
    """Cambio instantáneo de escala en el fotograma de t (dos claves CONSTANT en fotogramas consecutivos)."""
    f = S.f(t)
    S.clave(ob, (f - 1) / FPS, esc=antes, interp=C)
    S.clave(ob, f / FPS, esc=despues, interp=C)


def _fcurves(act):
    try:
        return list(act.fcurves)
    except AttributeError:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out += list(cb.fcurves)
        return out


def aplicar_interpolaciones():
    n = 0
    for ob in bpy.data.objects:
        ad = ob.animation_data
        if not ad or not ad.action:
            continue
        for fc in _fcurves(ad.action):
            for k in fc.keyframe_points:
                it = _INTERP.get((ob.name, fc.data_path, int(round(k.co[0]))))
                if it and k.interpolation != it:
                    k.interpolation = it
                    n += 1
            fc.update()
    print(f'[condensacion] interpolaciones ajustadas: {n}')


def fijar(ob, loc=None, esc=None):
    """Clave inicial en t=0 (estado de partida)."""
    S.clave(ob, 0, loc=loc, esc=esc, interp=C)


def aparecer(ob, t0, t1, base=(1, 1, 1)):
    fijar(ob, esc=T3)
    S.clave(ob, t0, esc=T3)
    S.clave(ob, t1, esc=base)


def desaparecer(ob, t0, t1, base=(1, 1, 1)):
    S.clave(ob, t0, esc=base)
    S.clave(ob, t1, esc=T3)


def ease(u):
    return u * u * (3 - 2 * u)


def trayecto_puntos(p0, p1, alto, adelante, n=40, u_fn=lambda u: u):
    p0, p1 = Vector(p0), Vector(p1)
    out = []
    for k in range(n + 1):
        u = u_fn(k / n)
        b = math.sin(math.pi * u)
        out.append(p0.lerp(p1, u) + Vector((0, -adelante * b, alto * b)))
    return out


def recorrer(ob, t0, t1, p0, p1, alto, adelante, n=12):
    """Mueve ob por un arco (claves lineales sobre muestras con aceleración suave)."""
    for k in range(n + 1):
        tau = k / n
        u = ease(tau)
        b = math.sin(math.pi * u)
        p = Vector(p0).lerp(Vector(p1), u) + Vector((0, -adelante * b, alto * b))
        S.clave(ob, t0 + (t1 - t0) * tau, loc=tuple(p), interp=LIN)


# ================================================================ medidas comunes de la «fracción»
H_ORO = 0.11              # tablilla de oro (Significado / Sdo.), apoyada en el piso
H_BAR = 0.016             # la barra: una tablilla delgada de tinta
Z_BAR = H_ORO + H_BAR / 2  # centro de la barra (local a los grupos, cuyo origen está en el piso)
Z_BT = H_ORO + H_BAR       # cara superior de la barra
BEV = 0.004               # bisel de las tablillas

# ================================================================ geometría de la figura 3
# Escaneo (1550×390 px): figura en x 40-1387, y 33-277. Se escala a 6,6 m de ancho, centrada en el origen.
ESC = 6.6 / 1347.0
def fx(px): return (px - 713.5) * ESC
def fz(py): return (155.0 - py) * ESC


# ---------------------------------------------------------------- estado 0: la figura, grabada (plano XZ, de frente a -Y)
plana_i = bb.grupo('plana_permutacion', (fx(467), 0, 0))
plana_d = bb.grupo('plana_condensacion', (fx(1157), 0, 0))
R0 = 0.0062                 # trazo de la figura
CAP0 = 0.1                  # altura de mayúscula de la figura
Y0 = 0.0
piezas_i, piezas_d = [], []
piezas_i.append(corchete('corchete1_plano', fx(41), fx(540), fz(143), fz(108), r=R0, rc=0.03, material=INK))
piezas_i.append(corchete('corchete2_plano', fx(584), fx(891), fz(143), fz(108), r=R0, rc=0.03, material=INK))
piezas_i.append(tubo('barra_plana', [(fx(40), Y0, fz(221.5)), (fx(895), Y0, fz(221.5))], R0 * 1.25, INK))
piezas_d.append(tubo('fraccion_plana', [(fx(1110), Y0, fz(160.7)), (fx(1205), Y0, fz(160.7))], R0 * 1.25, INK))
FA = dict(r=0.0052, rc=0.018, lc=0.075, material=ESM)
piezas_d += [flecha('flecha_plana_si', (fx(1038), 0, fz(160.7)), (fx(1096), 0, fz(160.7)), **FA),
             flecha('flecha_plana_sd', (fx(1277), 0, fz(160.7)), (fx(1219), 0, fz(160.7)), **FA),
             flecha('flecha_plana_ii', (fx(1104), 0, fz(203)), (fx(1030), 0, fz(182)), **FA),
             flecha('flecha_plana_id', (fx(1210), 0, fz(203)), (fx(1284), 0, fz(181)), **FA)]
# letras de la figura (tinta; el Significado en oro)
piezas_i += [
    renglon('titulo_permutacion', [(u'Permutación', F_ITAL, 1.0, 0.0, 0.0)], 0.088, TINTA_L, (fx(151), Y0, fz(46))),
    renglon('p_fonemas', [T('Fonema'), SUP('1'), T('…', 0.03), T('Fonema', ESP), SUP('2'), T('…', 0.03), T('etc.', ESP)],
            CAP0, TINTA_L, (fx(290), Y0, fz(113))),
    renglon('p_significante1', [T('Significante'), SUP('1')], CAP0, TINTA_L, (fx(290), Y0, fz(179))),
    renglon('p_f', [T('F'), SUP('1'), T('…', 0.03), T('F', ESP), SUP('2'), T('…', 0.03), T('etc.', ESP)],
            CAP0, TINTA_L, (fx(737), Y0, fz(113))),
    renglon('p_snte2', [T('Snte.'), SUP('2')], CAP0, TINTA_L, (fx(737), Y0, fz(179))),
    renglon('significado_plano', [T('Significado')], CAP0 * 1.05, ORO_L, (fx(467), Y0, fz(258))),
]
piezas_d += [
    renglon('titulo_condensacion', [(u'Condensación', F_ITAL, 1.0, 0.0, 0.0)], 0.088, TINTA_L, (fx(1085), Y0, fz(46))),
    renglon('c_snte1', [T('Snte.'), SUP('1')], CAP0, TINTA_L, (fx(980), Y0, fz(164))),
    renglon('c_snte3', [T('Snte.'), SUP('3')], CAP0, TINTA_L, (fx(1157), Y0, fz(131))),
    renglon('sdo_plano', [T('Sdo.')], CAP0 * 1.05, ORO_L, (fx(1157), Y0, fz(192))),
    renglon('c_snte2', [T('Snte.'), SUP('2')], CAP0, TINTA_L, (fx(1337), Y0, fz(164))),
]
for ob in piezas_i:
    reparentar(ob, plana_i) if ob.parent is None else None
for ob in piezas_d:
    reparentar(ob, plana_d) if ob.parent is None else None
for g in (plana_i, plana_d):
    fijar(g, esc=(1, 1, 1))
    saltar(g, 0.3, 1.0, TINY)


# ---------------------------------------------------------------- estado 1: permutación en volumen
XP = -1.2
perm = bb.grupo('permutacion', (XP, 0, PISO))
fijar(perm, esc=(1, 1, 1))
desaparecer(perm, 3.55, 3.95)

CAP_T = 0.1
TW, TLL, TH, TD = 0.148, 0.222, 0.185, 0.022   # tablillas: ancho, ancho de LL, alto, grosor
GAP, ESPT = 0.016, 0.07
RH = 0.11                  # alto del plinto de cada cadena
PD = 0.15                  # fondo del plinto
Z_T = Z_BT + RH            # base de las tablillas (local al grupo)
Y_T = -PD / 2 + 0.03       # y del centro de las tablillas (cerca del canto frontal del plinto)


def disposicion(chars):
    xs, cur = [], 0.0
    for ch in chars:
        if ch == ' ':
            xs.append(None)
            cur += ESPT
            continue
        w = TLL if ch == 'LL' else TW
        xs.append(cur + w / 2)
        cur += w + GAP
    ancho = cur - GAP
    return [None if x is None else x - ancho / 2 for x in xs], ancho


FILA = ['V', 'A', 'Y', 'A', ' ', 'U', 'N', ' ', 'G', 'A', 'LL', 'O']
FILA2 = ['V', 'A', 'LL', 'A', ' ', 'U', 'N', ' ', 'G', 'A', 'Y', 'O']
xs1, ANCHO_F = disposicion(FILA)
xs2, _ = disposicion(FILA2)
SEP = 0.34
CX = [-(ANCHO_F / 2 + SEP / 2), (ANCHO_F / 2 + SEP / 2)]
L_BAR1 = 2 * ANCHO_F + SEP + 0.34

oro1 = bb.caja('significado', (1.5, 0.24, H_ORO), (0, 0.0, H_ORO / 2), ORO, perm, bevel=0.006)
inscripcion('significado_inscripcion', [T('Significado')], 0.054, TINTA_L, -0.12, 0.0, oro1)
barra1 = bb.caja('barra_perm', (L_BAR1, 0.24, H_BAR), (0, 0, Z_BAR), BARRA, perm, bevel=BEV)
aparecer(barra1, 0.2, 0.75)
aparecer(oro1, 0.35, 0.9)


def tesela(nombre, ch, loc, parent):
    """Tablilla delgada de piedra clara con la letra (o el dígrafo LL, un solo fonema) en grafito."""
    g = bb.grupo(nombre, loc, parent)
    w = TLL if ch == 'LL' else TW
    bb.caja(nombre + '_cuerpo', (w, TD, TH), (0, 0, TH / 2), TESELA, g, bevel=0.0035)
    glifo_unico(nombre + '_letra', ch, CAP_T, 0.0025, LACA, g, (0, -TD / 2 - 0.0028, TH / 2 - CAP_T / 2))
    return g


filas, teselas = [], [[], []]
ETQ_PL = ([T('Significante'), SUP('1')], [T('Snte.'), SUP('2')])
for r in range(2):
    cx = CX[r]
    zocalo = bb.caja(f'zocalo_{r}', (ANCHO_F + 0.12, PD, RH), (cx, 0.0, Z_BT + RH / 2), PLINTO, perm, bevel=BEV)
    inscripcion(f'zocalo_{r}_inscripcion', ETQ_PL[r], 0.05, TINTA_L, -PD / 2, -0.013, zocalo)
    aparecer(zocalo, 0.3 + 0.1 * r, 0.8 + 0.1 * r)
    corch = corchete(f'corchete_{r}', cx - ANCHO_F / 2 - 0.035, cx + ANCHO_F / 2 + 0.035, Z_T - 0.021, Z_T + 0.075,
                     r=0.0042, rc=0.022, material=INK, parent=perm, y=-PD / 2 - 0.006)
    aparecer(corch, 0.55 + 0.1 * r, 1.0 + 0.1 * r)
    fila = bb.grupo(f'fila_{r}', (cx, Y_T, Z_T), perm)
    filas.append(fila)
    fijar(fila, esc=T3)
    saltar(fila, 0.5 + 0.2 * r, T3, (1, 1, TINY))
    S.clave(fila, 1.0 + 0.2 * r, esc=(1, 1, 1))
    for i, ch in enumerate(FILA):
        teselas[r].append(None if ch == ' ' else tesela(f'tesela_{r}_{i}', ch, (xs1[i], 0, 0), fila))

# permutación y ↔ ll en la segunda cadena (Snte.²): la y va por delante, la ll por detrás
TS, TE = 1.5, 3.3
iY, iLL = 2, 10
cx2 = CX[1]
fila2 = filas[1]
medio = bb.grupo('fila_1_medio', (0, 0, 0), fila2)
for i in range(iY + 1, iLL):
    g = teselas[1][i]
    if g is not None:
        g.parent = medio
fijar(medio, loc=(0, 0, 0))
S.clave(medio, TS + 0.3 * (TE - TS), loc=(0, 0, 0))
S.clave(medio, TS + 0.7 * (TE - TS), loc=(TLL - TW, 0, 0))
gY, gLL = teselas[1][iY], teselas[1][iLL]
pY0, pY1 = Vector((xs1[iY], 0, 0)), Vector((xs2[iLL], 0, 0))
pL0, pL1 = Vector((xs1[iLL], 0, 0)), Vector((xs2[iY], 0, 0))
ALTO_Y, ADEL_Y, ALTO_L, ADEL_L = 0.42, 0.16, 0.28, -0.2
fijar(gY, loc=tuple(pY0))
fijar(gLL, loc=tuple(pL0))
recorrer(gY, TS, TE, pY0, pY1, ALTO_Y, ADEL_Y)
recorrer(gLL, TS, TE, pL0, pL1, ALTO_L, ADEL_L)

# trazas punteadas de los dos recorridos (esmeralda = trayecto), sobre el canto superior de las tablillas
for nombre, p0, p1, alto, adel in (('arco_y', pY0, pY1, ALTO_Y, ADEL_Y), ('arco_ll', pL0, pL1, ALTO_L, ADEL_L)):
    off = Vector((cx2, Y_T, Z_T + TH + 0.03))
    pts = [tuple(p) for p in trayecto_puntos(p0 + off, p1 + off, alto, adel, n=64)]
    g = bb.grupo(nombre, (0, 0, 0), perm)
    bb.polilinea_punteada(nombre + '_guiones', pts, guion=0.034, hueco=0.026, r=0.0042, material=ESM, parent=g,
                          flecha={'r': 0.014, 'largo': 0.058})
    fijar(g, esc=T3)
    saltar(g, 1.3, TINY, 1.0)

APEX_Y = XP + cx2 + (xs1[iY] + xs1[iLL]) / 2
S.etiqueta('e1_yll', 'y ⇄ ll', (APEX_Y, -0.08, PISO + Z_T + TH + 0.03 + ALTO_Y + 0.1), clase='trayecto')


# ---------------------------------------------------------------- estado 2: condensación (AMO ⇄ AMOSCLAVO ⇄ ESCLAVO)
XC = fx(1157)
cond = bb.grupo('condensacion', (XC, 0, PISO))
YC = 0.0
CAP_L = 0.2
EXT_L = 0.012
BAR_W = 1.95
H_PL = 0.03                 # plintos bajos de los laterales
Y_LAT = -0.62               # los laterales, adelantados: el tercer término queda al fondo, sobre el Sdo.

barra2 = bb.caja('barra_cond', (BAR_W, 0.22, H_BAR), (0, YC, Z_BAR), BARRA, cond, bevel=BEV)
oro2 = bb.caja('sdo', (0.8, 0.24, H_ORO), (0, YC, H_ORO / 2), ORO, cond, bevel=0.006)
inscripcion('sdo_inscripcion', [T('Sdo.')], 0.056, TINTA_L, -0.12, 0.0, oro2)

T2A = 3.75  # aparición del aparato de condensación
fijar(barra2, esc=T3)
S.clave(barra2, T2A, esc=T3)
S.clave(barra2, T2A + 0.5, esc=(1, 1, 1))
aparecer(oro2, T2A + 0.1, T2A + 0.6)

# posiciones de las ranuras de AMOSCLAVO (sólo medición)
gl_c, ancho_c, x0_c = glifos('AMOSCLAVO', CAP_L, EXT_L)
ranuras = [g['cx'] - (x0_c + ancho_c / 2) for g in gl_c]
assert len(ranuras) == 9, len(ranuras)

INNER2 = BAR_W / 2 + 0.3     # borde interior de los laterales en el estado 2


def lateral(nombre, cuerpo, lado, inner):
    gl, ancho, x0 = glifos(cuerpo, CAP_L, EXT_L)
    cxw = lado * (inner + ancho / 2)
    g = bb.grupo(nombre, (cxw, Y_LAT, 0.0), cond)
    letras, _ = palabra_objetos(nombre + '_l', cuerpo, CAP_L, EXT_L, LACA, g, (0, 0, H_PL))
    bb.caja(nombre + '_plinto', (ancho + 0.16, 0.2, H_PL), (0, 0, H_PL / 2), PLINTO, g, bevel=BEV)
    return g, letras, ancho, cxw


g_amo, l_amo, w_amo, cx_amo = lateral('amo', 'AMO', -1, INNER2)
g_esc, l_esc, w_esc, cx_esc = lateral('esclavo', 'ESCLAVO', 1, INNER2)
aparecer(g_amo, T2A + 0.2, T2A + 0.7)
aparecer(g_esc, T2A + 0.25, T2A + 0.75)

# flechas opuestas (ida arriba, hacia el tercer término; vuelta abajo, desde el Sdo.), como en la figura
FB = dict(r=0.0045, rc=0.015, lc=0.065, material=ESM)
ZA_SUP, ZA_INF = Z_BT + 0.6 * CAP_L, 0.06
ZL_SUP, ZL_INF = H_PL + 0.8 * CAP_L, H_PL + 0.25 * CAP_L
XL = INNER2 - 0.05
a_si = flecha('flecha_si', (-XL, Y_LAT + 0.03, ZL_SUP), (-BAR_W / 2 - 0.04, YC - 0.03, ZA_SUP), parent=cond, **FB)
a_ii = flecha('flecha_ii', (-0.4 - 0.05, YC - 0.03, ZA_INF), (-XL, Y_LAT + 0.03, ZL_INF), parent=cond, **FB)
a_sd = flecha('flecha_sd', (XL, Y_LAT + 0.03, ZL_SUP), (BAR_W / 2 + 0.04, YC - 0.03, ZA_SUP), parent=cond, **FB)
a_id = flecha('flecha_id', (0.4 + 0.05, YC - 0.03, ZA_INF), (XL, Y_LAT + 0.03, ZL_INF), parent=cond, **FB)
aparecer(a_si, 4.4, 4.8)
aparecer(a_sd, 4.45, 4.85)

# letras viajeras: copias que salen de AMO y de ESCLAVO (los originales permanecen)
TV = 1.35
orden = [(l_amo[2], cx_amo, 2, 4.9), (l_esc[1], cx_esc, 3, 4.95),
         (l_amo[1], cx_amo, 1, 5.15), (l_esc[2], cx_esc, 4, 5.2),
         (l_amo[0], cx_amo, 0, 5.4), (l_esc[3], cx_esc, 5, 5.45),
         (l_esc[4], cx_esc, 6, 5.7), (l_esc[5], cx_esc, 7, 5.95), (l_esc[6], cx_esc, 8, 6.2)]
viajeras = []
for (ob_o, cx_rel), cxw, ranura, t0 in orden:
    cp = ob_o.copy()
    cp.data = ob_o.data
    cp.name = f'viajera_{ranura}'
    bpy.context.scene.collection.objects.link(cp)
    cp.parent = cond
    p0 = Vector((cxw + cx_rel, Y_LAT, H_PL))
    p1 = Vector((ranuras[ranura], YC, Z_BT))
    fijar(cp, loc=tuple(p0), esc=T3)
    saltar(cp, t0, TINY, 1.0)
    recorrer(cp, t0, t0 + TV, p0, p1, 0.4, 0.0)
    viajeras.append(cp)
aparecer(a_ii, 7.2, 7.6)
aparecer(a_id, 7.25, 7.65)

S.etiqueta('e2_snte1', 'Snte.<sup>1</sup>', (0, -0.17, -0.02), parent=g_amo, clase='snte')
S.etiqueta('e2_snte2', 'Snte.<sup>2</sup>', (0, -0.17, -0.02), parent=g_esc, clase='snte')
S.etiqueta('e2_snte3', 'Snte.<sup>3</sup>', (XC, YC + 0.05, PISO + Z_BT + CAP_L + 0.12), clase='snte')


# ---------------------------------------------------------------- estado 3: el lector dentro (listones trapezoidales)
NF = 24
P_ = 0.1          # paso
B_ = 0.016        # ancho en la base (contra el tablero)
T_ = 0.008        # ancho del canto frontal
D_ = 0.17         # fondo del listón
H_ = 0.62         # alto
EPS = 0.0015      # separación del texto respecto de la cara
RECORTE = 0.004   # el texto lateral no llega al canto frontal (evita astillas vistas desde el otro lado)
XS = [(j - (NF - 1) / 2) * P_ for j in range(NF)]
W_ = XS[-1] - XS[0] + B_
Z_PB = Z_BT       # base del panel (sobre la barra), local a cond
Y_PB = 0.085      # tablero + listones (0,19 m de fondo) centrados sobre la barra (0,22 m)

panel = bb.grupo('panel', (0, Y_PB, Z_PB), cond)
bm = bmesh.new()
for x in XS:
    q = [(x - B_ / 2, 0.0), (x + B_ / 2, 0.0), (x + T_ / 2, -D_), (x - T_ / 2, -D_)]
    lo = [bm.verts.new((a, b, 0.0)) for a, b in q]
    hi = [bm.verts.new((a, b, H_)) for a, b in q]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for k in range(4):
        bm.faces.new((lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
listones = bb._obj_from_bm('listones', bm, LISTON, panel)
for p in listones.data.polygons:
    p.use_smooth = False
tablero = bb.caja('tablero', (W_ + 0.004, 0.022, H_ + 0.004), (0, 0.011, H_ / 2), TABLERO, panel, bevel=0.002)

BAR3 = (W_ + 0.1) / BAR_W

# cámaras de los estados 3 y 4 (el slider de azimut gira alrededor de la vertical que pasa por el objetivo)
RH3 = 24.0
ELEV3 = math.radians(5.0)
LOOK3 = Vector((XC - 0.058, 0.0, PISO + 0.12))
CAM3 = LOOK3 + Vector((0, -RH3, RH3 * math.tan(ELEV3)))
VIS_H3 = 2.1                   # alto visible (m) a la distancia del objetivo
AZ = 40.0


def cam_az(phi_deg, cam=None, look=None):
    cam = Vector(cam) if cam is not None else CAM3
    look = Vector(look) if look is not None else LOOK3
    ph = math.radians(phi_deg)
    off = cam - look
    return look + Vector((off.x * math.cos(ph) - off.y * math.sin(ph), off.x * math.sin(ph) + off.y * math.cos(ph), off.z))


ORIG_P = Vector((XC, Y_PB, PISO + Z_PB))
C_F = CAM3 - ORIG_P
C_L = cam_az(-AZ) - ORIG_P
C_R = cam_az(AZ) - ORIG_P


def proy_x(Cc, P):
    s = (0.0 - Cc.y) / (P.y - Cc.y)
    return Cc.x + s * (P.x - Cc.x)


def a_cara(Cc, Q, B, n):
    d = Q - Cc
    s = n.dot(B - Cc) / n.dot(d)
    return Cc + d * s + n * EPS


def recortar(bm_src, xa, xb):
    b2 = bm_src.copy()
    bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], dist=1e-7,
                           plane_co=(xa, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
    bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], dist=1e-7,
                           plane_co=(xb, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    return b2


def colocar(cuerpo, xc, zc, ancho_max, cap_max, fuente=FUENTE):
    bm1, a1 = palabra_plana_bm(cuerpo, 1.0, fuente)
    cap = min(cap_max, ancho_max / a1)
    for v in bm1.verts:
        v.co = Vector((xc + v.co.x * cap, 0.0, zc - cap / 2 + v.co.z * cap))
    return bm1, cap


def acumular(acc, b2, fmap):
    V, F = acc
    n0 = len(V)
    b2.verts.index_update()
    for v in b2.verts:
        V.append(tuple(fmap(v.co)))
    for f in b2.faces:
        F.append(tuple(n0 + v.index for v in f.verts))


avisos = []


def desfase_optimo(bm1, bandas, semiancho, paso=0.002, rango=None, dx=0.001):
    """Desplazamiento horizontal de la palabra que menos trazo esconde detrás de los listones (vista frontal)."""
    b2 = bm1.copy()
    bmesh.ops.triangulate(b2, faces=b2.faces[:])
    tris = [[(v.co.x, v.co.z) for v in f.verts] for f in b2.faces]
    b2.free()
    x0 = min(p[0] for t in tris for p in t)
    x1 = max(p[0] for t in tris for p in t)
    n = int((x1 - x0) / dx) + 2
    cob = [0.0] * n
    for t in tris:
        xs_ = [p[0] for p in t]
        i0, i1 = int((min(xs_) - x0) / dx), int((max(xs_) - x0) / dx)
        for i in range(i0, i1 + 1):
            x = x0 + i * dx
            zs = []
            for (ax, az), (bx, bz) in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                if (ax - x) * (bx - x) <= 0 and ax != bx:
                    zs.append(az + (bz - az) * (x - ax) / (bx - ax))
            if len(zs) >= 2:
                cob[i] += max(zs) - min(zs)
    rango = rango or P_ / 2
    mejor, oculto_min = 0.0, None
    k = -int(rango / paso)
    while k * paso <= rango:
        o = k * paso
        oculto = 0.0
        for i, c in enumerate(cob):
            if c:
                x = x0 + i * dx + o
                j = round(x / P_ + (NF - 1) / 2)
                if 0 <= j < NF and abs(x - XS[j]) <= semiancho:
                    oculto += c
        if oculto_min is None or oculto < oculto_min - 1e-9:
            mejor, oculto_min = o, oculto
        k += 1
    total = sum(cob)
    return mejor, (oculto_min / total if total else 0.0)


def texto_panel(nombre, izq, frente, der, parent, fuente=FUENTE):
    """Tres palabras en un mismo relieve: cada una proyectada desde la posición del lector que debe leerla."""
    acc = ([], [])
    zc = H_ / 2
    # --- de frente: sobre el tablero, entre listones
    bmF, capF = colocar(frente, 0.0, zc, 0.86 * W_, 0.3, fuente)
    o, frac = desfase_optimo(bmF, XS, B_ / 2 + 0.003)
    for v in bmF.verts:
        v.co.x += o
    print(f'[condensacion] {frente}: desfase {o * 1000:.0f} mm, trazo oculto tras listones {frac * 100:.1f} %')
    for j in range(NF - 1):
        b2 = recortar(bmF, XS[j] + B_ / 2, XS[j + 1] - B_ / 2)
        acumular(acc, b2, lambda co: (co.x, -EPS, co.z))
        b2.free()
    # --- desde la izquierda: caras izquierdas de los listones
    x_ini, x_fin = XS[0] - B_ / 2, proy_x(C_L, Vector((XS[-1] + T_ / 2, -D_, 0)))
    bmL, capL = colocar(izq, (x_ini + x_fin) / 2, zc, 0.86 * (x_fin - x_ini), 0.42, fuente)
    nL = Vector((-D_, -(B_ - T_) / 2, 0)).normalized()
    for j in range(NF):
        Bj, Fj = Vector((XS[j] - B_ / 2, 0, 0)), Vector((XS[j] - T_ / 2, -D_, 0))
        xa = Bj.x if j == 0 else proy_x(C_L, Vector((XS[j - 1] + T_ / 2, -D_, 0)))
        xb = proy_x(C_L, Fj + (Bj - Fj).normalized() * RECORTE)
        if j > 0 and xa < Bj.x - 1e-5:
            avisos.append(f'{nombre}: surco visible desde la izquierda en listón {j}')
        b2 = recortar(bmL, xa, xb)
        acumular(acc, b2, lambda co, B=Bj: a_cara(C_L, Vector(co), B, nL))
        b2.free()
    # --- desde la derecha: caras derechas
    x_ini, x_fin = proy_x(C_R, Vector((XS[0] - T_ / 2, -D_, 0))), XS[-1] + B_ / 2
    bmR, capR = colocar(der, (x_ini + x_fin) / 2, zc, 0.86 * (x_fin - x_ini), 0.42, fuente)
    nR = Vector((D_, -(B_ - T_) / 2, 0)).normalized()
    for j in range(NF):
        Bj, Fj = Vector((XS[j] + B_ / 2, 0, 0)), Vector((XS[j] + T_ / 2, -D_, 0))
        xa = proy_x(C_R, Fj + (Bj - Fj).normalized() * RECORTE)
        xb = XS[-1] + B_ / 2 if j == NF - 1 else proy_x(C_R, Vector((XS[j + 1] - T_ / 2, -D_, 0)))
        if j < NF - 1 and xb > Bj.x + 1e-5:
            avisos.append(f'{nombre}: surco visible desde la derecha en listón {j}')
        b2 = recortar(bmR, xa, xb)
        acumular(acc, b2, lambda co, B=Bj: a_cara(C_R, Vector(co), B, nR))
        b2.free()
    for b_ in (bmF, bmL, bmR):
        b_.free()
    print(f'[condensacion] {nombre}: cap frente {capF:.3f}, izq {capL:.3f}, der {capR:.3f}')
    return malla(nombre, acc[0], acc[1], LACA, parent)


txtA = texto_panel('texto_amosclavo', 'AMO', 'AMOSCLAVO', 'ESCLAVO', panel)
txtB = texto_panel('texto_maquinoscrito', 'MÁQUINA', 'MAQUINOSCRITO', 'MANUSCRITO', panel)

# animación del estado 3 (8.6 → 10.3): las flechas se vuelven el recorrido del lector (slider)
T3A = 8.6
for a in (a_si, a_ii, a_sd, a_id):
    desaparecer(a, T3A, T3A + 0.35)
S.clave(barra2, T3A, esc=(1, 1, 1))
S.clave(barra2, T3A + 0.6, esc=(BAR3, 1, 1))
# AMO y ESCLAVO entran en el dispositivo (van hacia los cantos del panel y se desvanecen): en los estados 3 y 4
# no queda ningún lateral en la escena, así que nada asoma por los bordes en ningún punto del deslizador.
for g, lado in ((g_amo, -1), (g_esc, 1)):
    p = Vector(g.location)
    q = Vector((lado * (W_ / 2 - 0.2), YC, p.z))
    fijar(g, loc=tuple(p))
    S.clave(g, T3A, loc=tuple(p), esc=(1, 1, 1))
    S.clave(g, T3A + 0.8, loc=tuple(q), esc=T3)
for cp in viajeras:
    desaparecer(cp, T3A + 0.15, T3A + 0.55)
fijar(panel, esc=T3)
S.clave(panel, 8.9, esc=T3, interp=C)
S.clave(panel, 8.9 + 1.0 / FPS, esc=(1, 1, 0.002))
S.clave(panel, 10.2, esc=(1, 1, 1))
fijar(txtA, esc=(1, 1, 1))
fijar(txtB, esc=T3)

# Las etiquetas HTML no cambian con el deslizador: un «Snte.³» fijo rotularía mal AMO (Snte.¹) y ESCLAVO (Snte.²)
# vistos de lado. Se usa una leyenda breve que vale para las tres posiciones del lector.
S.etiqueta('e3_leyenda', 'izquierda: Snte.<sup>1</sup> · de frente: <b>Snte.<sup>3</sup></b> · derecha: Snte.<sup>2</sup>',
           (XC, Y_PB - D_ / 2, PISO + Z_PB + H_ + 0.075), clase='snte')
# (la aclaración sobre Cruz-Diez / Le Parc está en la diapositiva 20: no se rotula en la escena)

# ---------------------------------------------------------------- estado 4: MAQUINOSCRITO (mismos listones)
T4A = 10.6
S.clave(panel, T4A, esc=(1, 1, 1))
S.clave(panel, T4A + 0.45, esc=(1, 1, 0.002))
saltar(txtA, T4A + 0.5, 1.0, TINY)
saltar(txtB, T4A + 0.5, TINY, 1.0)
S.clave(panel, T4A + 0.55, esc=(1, 1, 0.002))
S.clave(panel, T4A + 1.5, esc=(1, 1, 1))

for a in avisos:
    print('[condensacion] AVISO', a)

# ================================================================ estados
# cámara horizontal por debajo del centro de la figura: la figura sube en el cuadro y deja libre la tarjeta
FRENTE = dict(cam=(0.0, -38.0, -0.52), look=(0.0, 0.0, -0.52), fov=6.3)


def orbita(look, dist, elev, az=0.0):
    """Cámara a `dist` del objetivo, `elev` grados sobre la horizontal y `az` grados a la derecha del eje -Y."""
    look = Vector(look)
    e, a = math.radians(elev), math.radians(az)
    return tuple(look + dist * Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))), tuple(look)


c1_, l1_ = orbita((XP - 0.07, 0.0, PISO + 0.02), 5.6, 19.0, -8.0)
E1 = dict(cam=c1_, look=l1_, fov=30)
c2_, l2_ = orbita((XC + 0.33, -0.3, PISO - 0.22), 6.25, 30.0, -3.0)
E2 = dict(cam=c2_, look=l2_, fov=30)
E3 = dict(cam=tuple(CAM3), look=tuple(LOOK3), fov=2 * math.degrees(math.atan(VIS_H3 / 2 / (CAM3 - LOOK3).length)))
SLIDER_LECTOR = {'tipo': 'azimut', 'min': -AZ, 'max': AZ, 'etiqueta': 'posición del lector',
                 'min_txt': 'izquierda', 'max_txt': 'derecha'}

S.estado('Figura 3',
         'La figura tal como la dibuja Sarduy: a la izquierda, la <b>permutación</b> (dos cadenas, un solo Significado); '
         'a la derecha, la <b>condensación</b> (surge un tercer término).',
         'Figura 3 según Sarduy 1972, reconstrucción · l. 317-327', etiquetas=[], orbita=False, t1=0, **FRENTE)
S.estado('Permutación',
         'La y de «vaya» y la ll de «gallo» cambian de lugar: «valla un gayo». Dos significantes, un solo '
         '<b>Significado</b>, que no se mueve. (La lectura y/ll es interpretación docente.)',
         'Cabrera Infante, «O se me valla un gayo» · l. 322-324 · l. 341',
         etiquetas=['e1_yll'], t1=3.4,
         slider={'tipo': 'tiempo', 't0': 1.45, 't1': 3.35, 'etiqueta': 'permutación y ⇄ ll',
                 'min_txt': 'vaya un gallo', 'max_txt': 'valla un gayo'}, **E1)
# Estado 2: la pregunta de predicción no se responde en el texto (se ve en la escena). Con la curva de
# aceleración del visor, el viaje de las letras dura ~1 s en tiempo real: el deslizador permite recorrerlo despacio.
S.estado('Condensación',
         'Letras de AMO y de ESCLAVO viajan y componen AMOSCLAVO, el tercer término, sobre el Sdo. '
         'Mira los laterales: es la «puesta en escena» de dos significantes.',
         'Cabrera Infante, «amosclavo» · «puesta en escena» · l. 341-342 · l. 399-404',
         etiquetas=['e2_snte1', 'e2_snte2', 'e2_snte3'], t1=7.9,
         slider={'tipo': 'tiempo', 't0': 4.85, 't1': 7.9, 'etiqueta': 'condensación',
                 'min_txt': 'AMO · ESCLAVO', 'max_txt': 'AMOSCLAVO'},
         pregunta='¿Desaparecen AMO y ESCLAVO cuando surge el tercer término?', **E2)
# Estado 3: el tercer término no es la «vista verdadera»; la obra es el recorrido (Sarduy sobre Cruz-Diez).
S.estado('El lector dentro',
         'Desde la izquierda, AMO; desde la derecha, ESCLAVO; de frente, AMOSCLAVO. Ninguna vista sola es la obra: '
         'el desplazamiento del lector, «comparable a la lectura», condensa las tres.',
         'Sarduy sobre Cruz-Diez · l. 320-321 · l. 353-359',
         etiquetas=['e3_leyenda'], t1=10.3, orbita=False, slider=SLIDER_LECTOR, **E3)
S.estado('Maquinoscrito',
         'El mismo mecanismo: MÁQUINA desde la izquierda, MANUSCRITO desde la derecha y, de frente, '
         'el tercer término, MAQUINOSCRITO.',
         'Cabrera Infante, «maquinoscrito» · l. 341-342',
         etiquetas=['e3_leyenda'], t1=12.1, orbita=False, slider=SLIDER_LECTOR, **E3)

# ---------------------------------------------------------------- recuento
tris = 0
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
print(f'[condensacion] triángulos ≈ {tris} (las viajeras comparten malla con los originales)')

aplicar_interpolaciones()


# ---------------------------------------------------------------- informe de encuadre (sólo consola)
def _proy(cam, look, fov, asp, P):
    cam, look = Vector(cam), Vector(look)
    f = (look - cam).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f)
    d = Vector(P) - cam
    z = d.dot(f)
    th = math.tan(math.radians(fov) / 2)
    return d.dot(r) / z / (th * asp), d.dot(u) / z / th


def informe_encuadre():
    sc = bpy.context.scene
    for n, e in enumerate(S.estados):
        sc.frame_set(S.f(e['t1']))
        azs = [0.0]
        if e.get('slider') and e['slider'].get('tipo') == 'azimut':
            azs = [e['slider']['min'], 0.0, e['slider']['max']]
        for az in azs:
            cam = cam_az(az, e['_cam'], e['_look'])
            for vista, W, H in (('embed', 1920, 983), ('visor', 1920, 1080)):
                x0 = y0 = 1e9
                x1 = y1 = -1e9
                for ob in bpy.data.objects:
                    if ob.type != 'MESH' or min(ob.matrix_world.to_scale()) < 0.01:
                        continue
                    for c in ob.bound_box:
                        x, y = _proy(cam, e['_look'], e['fov'], W / H, ob.matrix_world @ Vector(c))
                        px, py = (x + 1) / 2 * W, (1 - y) / 2 * H
                        x0, x1, y0, y1 = min(x0, px), max(x1, px), min(y0, py), max(y1, py)
                print(f'[encuadre] e{n} az={az:+.0f} {vista}: x {x0:.0f}–{x1:.0f}  y {y0:.0f}–{y1:.0f}')
    sc.frame_set(0)


informe_encuadre()

S.exportar()
