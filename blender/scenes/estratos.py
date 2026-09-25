"""N5 · Estratos — leer en filigrana: cita, reminiscencia y gramas (Sarduy 1972, l. 406-771).

Lámina de museo: papel, tinta y oro. Un bloque-texto de 6 tablillas (4 × 3 × 1,2 m). Coordenadas locales del
grupo «bloque»: acostado, superficie de lectura arriba (z = 0), renglones a lo largo de X, apilados en Y
(primer renglón en +Y). En el estado 0 el bloque está de pie (rot. X +90°): la superficie mira a -Y, como una página.

Estratos (de arriba abajo):
  capa0  superficie: renglones en trazos finos gris cálido (tinta diluida)   → cita: tiras carmín pegadas encima
  capa1  texto en filigrana: versos en grafito (Lope bajo Góngora)            → visible cuando la superficie se
         vuelve una hoja translúcida y se levanta (estado 2)
  capa2-5 geología del texto (papel → gris cálido); en el estado 3 la reminiscencia las tiñe de carmín desde abajo
Gramas (estado 4): la superficie, hoja translúcida levantada; el renglón 9 se alza en letras (palíndromo) entre dos
flechas finas en espejo (→ arriba, ← abajo); grama sémico: dos palabras del último renglón señalan, a través de la
hoja, un ojo DIBUJADO (contorno almendrado bermellón, iris de oro) tendido bajo la línea: «mal de ojo».
Red en volumen (estado 5): despiece vertical con hilos finos punteados; descripción en condicional (l. 459-462).
"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bb
import bpy, bmesh
from mathutils import Vector, Matrix

random.seed(1972)
RNG = random.Random(1972)

S = bb.Escena('estratos', 'Leer en filigrana: cita, reminiscencia y gramas', dur=11.6)
M = bb.mat
C = 'CONSTANT'
OFF = 0.0001


# ---------------------------------------------------------------- helpers propios (no tocan bb.py)
_MIS = {}


def mat_hex(nombre, hexstr, met=0.0, rough=0.6, emi=None, emis=0.0, alpha=1.0, coat=0.0):
    """Material Principled con color libre (misma lógica que bb.mat)."""
    if nombre in _MIS:
        return _MIS[nombre]
    m = bpy.data.materials.new(nombre)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = bb.lin(hexstr)
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    if coat and 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.15
    if emi:
        b.inputs['Emission Color'].default_value = bb.lin(emi)
        b.inputs['Emission Strength'].default_value = emis
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    m.diffuse_color = bb.lin(hexstr, alpha)
    _MIS[nombre] = m
    return m


def bm_caja(bm, size, loc):
    g = bmesh.ops.create_cube(bm, size=1.0)
    for v in g['verts']:
        v.co = Vector((v.co.x * size[0] + loc[0], v.co.y * size[1] + loc[1], v.co.z * size[2] + loc[2]))


def bm_disco(bm, centro, r, h, eje=(0, 0, 1), segs=48):
    """Disco plano (cilindro bajo) centrado en `centro`, con su eje en `eje`."""
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h)
    q = Vector((0, 0, 1)).rotation_difference(Vector(eje).normalized())
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(centro)) @ q.to_matrix().to_4x4(), verts=g['verts'])


def malla(nombre, bm, material, parent=None, loc=(0, 0, 0), bevel=0.0, seg=1):
    ob = bb._obj_from_bm(nombre, bm, material, parent, loc)
    for p in ob.data.polygons:
        p.use_smooth = False
    if bevel > 0:
        mod = ob.modifiers.new('bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = seg
        mod.limit_method = 'ANGLE'
        bb.aplicar(ob)
    return ob


def tubo_bm(bm, puntos, r, lados=8):
    pts = [Vector(p) for p in puntos]
    anillos = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        ref = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
        n = t.cross(ref).normalized()
        b2 = t.cross(n).normalized()
        anillo = []
        for j in range(lados):
            a = 2 * math.pi * j / lados
            anillo.append(bm.verts.new(p + r * (math.cos(a) * n + math.sin(a) * b2)))
        anillos.append(anillo)
    for a0, a1 in zip(anillos[:-1], anillos[1:]):
        for j in range(lados):
            bm.faces.new((a0[j], a0[(j + 1) % lados], a1[(j + 1) % lados], a1[j]))
    bm.faces.new(list(reversed(anillos[0])))
    bm.faces.new(anillos[-1])
    bm.normal_update()


def unir(obs, nombre):
    """Une objetos en uno solo (evita hijos de objetos animados por escala: el exportador los hornea)."""
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = nombre
    return ob


def punteada(nombre, puntos, origen, parent, material, flecha=None, **kw):
    """Línea punteada (con punta opcional) como UN objeto con origen en `origen` (coords del padre)."""
    o = Vector(origen)
    rel = [tuple(Vector(p) - o) for p in puntos]
    ob = bb.polilinea_punteada(nombre, rel, material=material, parent=None, flecha=flecha, **kw)
    if flecha:
        ob = unir([ob, bpy.data.objects[nombre + '_punta']], nombre)
    ob.parent = parent
    ob.location = o
    return ob


_GLIFOS = {}


def glifo(ch, size, extrude, res=3):
    """Malla de una letra (Georgia), de pie mirando a -Y; devuelve (mesh, zmin, alto)."""
    if ch in _GLIFOS:
        return _GLIFOS[ch]
    cu = bpy.data.curves.new('glifo_' + ch, 'FONT')
    cu.body = ch
    cu.size = size
    cu.extrude = extrude
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.resolution_u = res
    cu.font = bpy.data.fonts.load(bb.FUENTES['serif'], check_existing=True)
    ob = bpy.data.objects.new('glifo_' + ch, cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.view_layer.objects.active
    me = ob.data
    for p in me.polygons:
        p.use_smooth = False
    ys = [v.co.y for v in me.vertices]
    bpy.data.objects.remove(ob)
    _GLIFOS[ch] = (me, min(ys), max(ys) - min(ys))
    return _GLIFOS[ch]


def palabras(x0, x1, lmin=0.08, lmax=0.34, gap=0.045):
    """Segmentos-palabra entre x0 y x1 (el último se estira hasta x1: renglón justificado)."""
    out, x = [], x0
    while x < x1 - 1e-6:
        L = RNG.uniform(lmin, lmax)
        if x + L + gap + lmin > x1:
            L = x1 - x
        out.append((x, x + L))
        x += L + gap
    return out


def bez(p0, c, p1, n=30):
    return [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1 for t in (i / n for i in range(n + 1))]


# ---------------------------------------------------------------- materiales
# (nombres elegidos para que el estudio del visor respete el color: ver rol() en docs/3d/estudio.js)
PAPEL = M('lamina')                                              # superficie: papel
NACAR = M('significante')                                        # letras del palíndromo: laca grafito
TRAZO = mat_hex('renglon_trazo', '#8F877D', rough=0.92)          # renglones: tinta diluida, gris cálido
VERSO = mat_hex('verso_grafito', '#4A443E', rough=0.7)           # versos de Lope (filigrana): grafito
VELO = mat_hex('papel_contraluz', '#F1EADC', rough=0.45, emi='#F3EDE2', emis=0.5, alpha=0.42)   # hoja a contraluz
FILETE = mat_hex('filete_grafito', '#4A443E', rough=0.5)         # contorno fino de la hoja translúcida
CARMIN = mat_hex('carmin_cita', '#6B1539', rough=0.62)            # tiras de cita: carmín
TRAZO_CITA = mat_hex('renglon_cita', '#F2E6EA', rough=0.8)       # la frase ajena, clara sobre el carmín
CIAN = M('trayecto')                                             # esmeralda: lectura, flechas, hilos
ORO = M('significado')
BERM = M('ausencia')
PUPILA = mat_hex('pupila_grafito', '#2F2B28', rough=0.5)

# estratos: papel → gris cálido (sin café); tinte de la reminiscencia: del carmín pálido al carmín pleno
COL_PIEDRA = [None, '#DDD6CA', '#CEC6B9', '#BEB6A9', '#ADA599', '#9C9489']
COL_TINTE = [None, None, '#DCC6CB', '#C495A4', '#A35D78', '#7E264D']

S.estudio = {
    'materiales': {
        'lamina': {'color': '#FFFDF9'},                                   # la página se despega del fondo papel
        'renglon_trazo': {'envMapIntensity': 0.3},
        'carmin_cita': {'envMapIntensity': 0.45},
        'verso_grafito': {'envMapIntensity': 0.4},
    },
}
MAT_BASE = [PAPEL] + [mat_hex(f'estrato{k}', COL_PIEDRA[k], rough=0.85) for k in range(1, 6)]
MAT_TINTE = [PAPEL, MAT_BASE[1]] + [mat_hex(f'tinte{k}', COL_TINTE[k], rough=0.8) for k in range(2, 6)]

# ---------------------------------------------------------------- bloque y tablillas
W, D, TH, GAP = 4.0, 3.0, 0.2, 0.022
Y0, Y1 = -D / 2, D / 2
H = TH - GAP
BEV = 0.008
DZ = [(5 - k) * 0.45 for k in range(6)]     # despiece vertical (estado 5)


def zc(k):
    return -k * TH - TH / 2


def ztop(k):
    return zc(k) + H / 2


bloque = bb.grupo('bloque')
capas = [bb.grupo(f'capa{k}', (0, 0, 0), bloque) for k in range(6)]

llenas, llenas_t = {}, {}
for k in range(6):
    llenas[k] = bb.caja(f'losa{k}', (W, D, H), (0, 0, zc(k)), MAT_BASE[k], capas[k], bevel=BEV)
    if k >= 2:
        llenas_t[k] = bb.caja(f'losa{k}_tinte', (W, D, H), (0, 0, zc(k)), MAT_TINTE[k], capas[k], bevel=BEV)

# contorno fino de cada tablilla (como en un grabado): las 12 aristas en grafito
def aristas_bm(bm, hx, hy, hz, r):
    v = [Vector((sx * hx, sy * hy, sz * hz)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    for i in range(8):
        for j in range(i + 1, 8):
            if sum(1 for c in range(3) if v[i][c] != v[j][c]) == 1:
                tubo_bm(bm, [v[i], v[j]], r, 6)


contornos = {}
for k in range(6):
    bm = bmesh.new()
    aristas_bm(bm, W / 2 + 0.0015, D / 2 + 0.0015, H / 2 + 0.0015, 0.0035)
    contornos[k] = bb._obj_from_bm(f'contorno{k}', bm, FILETE, capas[k], (0, 0, zc(k)))

# la superficie a contraluz: una HOJA delgada translúcida (no un bloque de vidrio), con un filete fino de grafito
VT = 0.03
ZV = ztop(0) - VT / 2
velo = bb.caja('hoja_contraluz', (W, D, VT), (0, 0, ZV), VELO, capas[0], bevel=0.004)
bm = bmesh.new()
aristas_bm(bm, W / 2 + 0.003, D / 2 + 0.003, VT / 2 + 0.002, 0.0045)
filete = bb._obj_from_bm('filete_hoja', bm, FILETE, capas[0], (0, 0, ZV))

# ---------------------------------------------------------------- renglones de la superficie (trazos finos)
YL = [1.2 - i * (2.3 / 11) for i in range(12)]
SPEC = {0: (-1.7, 1.7), 1: (-1.7, 1.7), 2: (-1.7, 1.7), 3: (-1.7, 0.35), 4: (-1.45, 1.7), 5: (-1.7, 1.7),
        6: (-1.7, 1.7), 7: (-1.7, 0.9), 8: (-1.45, 1.7), 9: (-1.7, 1.7), 10: (-1.7, 1.7), 11: (-1.7, 1.1)}
IND = [(-1.7, -1.22), (-0.55, 0.22)]           # «mal de muerte», «traspiés en la alabanza»
RY_, RZ_ = 0.042, 0.005                        # ancho (en Y) y alto del trazo
ZR = ztop(0) + RZ_ / 2 - 0.001


def trazos(bm, segs, y, ancho=RY_, alto=RZ_, z=ZR):
    for a, b in segs:
        bm_caja(bm, (b - a, ancho, alto), ((a + b) / 2, y, z))


bm = bmesh.new()
for i, y in enumerate(YL):
    if i in (9, 11):
        continue
    trazos(bm, palabras(*SPEC[i]), y)
trazos(bm, palabras(-1.17, -0.6) + palabras(0.27, 1.1), YL[11])
renglones = malla('renglones', bm, TRAZO, capas[0])

bm = bmesh.new()
trazos(bm, palabras(*SPEC[9]), YL[9])
renglon9 = malla('renglon_palindromo', bm, TRAZO, capas[0])

bm = bmesh.new()
trazos(bm, IND, YL[11])
ind_tinta = malla('indicadores_tinta', bm, TRAZO, capas[0])
bm = bmesh.new()
trazos(bm, IND, YL[11], ancho=0.058, alto=0.012, z=ztop(0) + 0.005)
ind_cian = malla('indicadores', bm, CIAN, capas[0])

# lectura lineal (estado 0): flecha fina esmeralda sobre el primer renglón
ZL = ztop(0) + 0.02
lect = punteada('lectura', [(-1.7, 1.37, ZL), (1.78, 1.37, ZL)], (-1.7, 1.37, ZL), capas[0], CIAN,
                flecha={'r': 0.034, 'largo': 0.15}, guion=0.09, hueco=0.06, r=0.011)

# ---------------------------------------------------------------- texto en filigrana (capa1): versos en grafito
bm = bmesh.new()
for j in range(13):
    y = 1.3 - j * 0.2
    x1 = -1.7 + RNG.uniform(1.7, 2.9)
    trazos(bm, palabras(-1.7, x1, 0.1, 0.42, 0.05), y, ancho=0.028, alto=0.004, z=ztop(1) + 0.0015)
lope = malla('versos_filigrana', bm, VERSO, capas[1])

# ---------------------------------------------------------------- citas: tiras carmín delgadas, con la frase ajena
# (clave, renglón, x, largo, rótulo, giro, desplazamiento del rótulo (dx, dy))
CITAS = [('rulfo', 1, -0.95, 1.1, 'Rulfo · una frase', 2.0, (-0.35, 0.36)),
         ('hugues', 4, 0.8, 0.72, 'Carpentier · Víctor Hugues', -2.5, (0.45, 0.33)),
         ('rocamadour', 6, -0.55, 0.78, 'Cortázar · Rocamadour', 2.5, (-0.35, -0.34)),
         ('cruz', 8, 0.95, 0.72, 'Fuentes · Artemio Cruz', -1.5, (0.4, -0.34))]
PH, PT = 0.19, 0.012
ZP = ztop(0) + RZ_ + PT / 2
citas = []
for clave, i, x, L, html, giro, (ldx, ldy) in CITAS:
    tira = bb.caja('cita_' + clave, (L, PH, PT), (0, 0, 0), CARMIN, None, bevel=0.003)
    bm = bmesh.new()
    trazos(bm, palabras(-L / 2 + 0.07, L / 2 - 0.07, 0.07, 0.24, 0.04), 0, ancho=0.03, alto=0.003, z=PT / 2 + 0.001)
    frase = malla('frase_' + clave, bm, TRAZO_CITA)
    g = unir([tira, frase], 'cita_' + clave)
    g.parent = capas[0]
    g.location = (x, YL[i], ZP)
    g.rotation_euler = (0, 0, math.radians(giro))
    S.etiqueta('c_' + clave, html, (x + ldx, YL[i] + ldy, ZP + 0.03), parent=capas[0], clase='ajeno')
    citas.append(g)

# ---------------------------------------------------------------- grama fonético: palíndromo (l. 655)
FRASE = 'DÁBALE ARROZ A LA ZORRA EL ABAD'
PASO, ESP, TAM = 0.126, 0.065, 0.24
xs, x = [], 0.0
for ch in FRASE:
    if ch == ' ':
        x += ESP
        continue
    xs.append(x)
    x += PASO
sh = -(xs[0] + xs[-1]) / 2 + 0.05
xs = [v + sh for v in xs]
y9 = YL[9]
Z_BASE = 0.3                                   # base de las letras sobre su renglón (relativa a la hoja)
letras = [c for c in FRASE if c != ' ']
obs, altos = [], []
for n, (ch, xv) in enumerate(zip(letras, xs)):
    me, ymin, alto = glifo(ch, TAM, 0.014)
    ob = bpy.data.objects.new(f'letra{n:02d}', me.copy())
    ob.data.materials.clear()
    ob.data.materials.append(NACAR)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = (xv, 0, Z_BASE - ymin)
    bb._link(ob)
    altos.append(alto)
bpy.context.view_layer.update()
pal = unir([bpy.data.objects[f'letra{n:02d}'] for n in range(len(letras))], 'palindromo')
bb.aplicar(pal)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
pal.parent = capas[0]
pal.location = (0, y9, ztop(0))                 # origen en el renglón: al escalar en z, las letras «salen» de él
ALTO = max(altos)
print('[estratos] alto máx. de letra', round(ALTO, 3))
XA, XB = xs[0] - 0.08, xs[-1] + 0.12           # extremos de las flechas del palíndromo
ZI = ztop(0) + Z_BASE + ALTO + 0.085           # → arriba: lectura de izquierda a derecha
ZV_ = ztop(0) + Z_BASE - 0.085                 # ← abajo: de derecha a izquierda
ida = punteada('pal_ida', [(XA, y9, ZI), (XB, y9, ZI)], (XA, y9, ZI), capas[0], CIAN,
               flecha={'r': 0.03, 'largo': 0.13}, guion=0.08, hueco=0.05, r=0.009)
vuelta = punteada('pal_vuelta', [(XB, y9, ZV_), (XA, y9, ZV_)], (XB, y9, ZV_), capas[0], CIAN,
                  flecha={'r': 0.03, 'largo': 0.13}, guion=0.08, hueco=0.05, r=0.009)

# ---------------------------------------------------------------- grama sémico: el ojo dibujado bajo la línea
LIFT2, LIFT4 = 0.75, 0.62          # altura de la hoja levantada en los estados 2 y 4
XE, YE = -0.8, -0.9               # centro del ojo, bajo el último renglón (tendido sobre la capa 1)
EA, EB = 0.6, 0.23                 # semiancho y semialto del contorno almendrado
ZE = ztop(1) + 0.004


def almendra(a, b, signo, n=48):
    """Arco de circunferencia entre (-a, 0) y (a, 0) que pasa por (0, signo·b): medio contorno de un ojo."""
    R = (a * a + b * b) / (2 * b)
    c = b - R
    t0 = math.atan2(-c, a)
    out = []
    for i in range(n + 1):
        t = (math.pi - t0) + (2 * t0 - math.pi) * i / n
        out.append(Vector((R * math.cos(t), signo * (c + R * math.sin(t)), 0)))
    return out


bm = bmesh.new()
tubo_bm(bm, almendra(EA, EB, 1), 0.012, 8)
tubo_bm(bm, almendra(EA, EB, -1), 0.012, 8)
ojo_contorno = bb._obj_from_bm('ojo_contorno', bm, BERM, capas[1], (XE, YE, ZE + 0.012))
bm = bmesh.new()
bm_disco(bm, (0, 0, 0.006), 0.1, 0.012)
ojo_iris = bb._obj_from_bm('ojo_iris', bm, ORO, capas[1], (XE, YE, ZE))
bm = bmesh.new()
bm_disco(bm, (0, 0, 0.014), 0.038, 0.006, segs=32)
ojo_pupila = bb._obj_from_bm('ojo_pupila', bm, PUPILA, capas[1], (XE, YE, ZE))
ojo = [ojo_contorno, ojo_iris, ojo_pupila]

# indicadores: desde cada palabra (sobre la hoja levantada) hasta un ángulo del ojo, a través de la hoja
xi1, xi2 = sum(IND[0]) / 2, sum(IND[1]) / 2
ZH = ztop(0) + LIFT4 + 0.012                   # cara superior de la hoja levantada (coords. del bloque)


def flecha_sem(nombre, p0, p1, curva):
    p0, p1 = Vector(p0), Vector(p1)
    c = (p0 + p1) / 2 + Vector(curva)
    return punteada(nombre, bez(p0, c, p1, 24), p0, bloque, CIAN, flecha={'r': 0.028, 'largo': 0.11},
                    guion=0.065, hueco=0.042, r=0.0085)


fl1 = flecha_sem('indicador1', (xi1, YL[11], ZH), (XE - 0.36, YE + 0.05, ZE + 0.06), (-0.12, 0.0, 0))
fl2 = flecha_sem('indicador2', (xi2, YL[11], ZH), (XE + 0.36, YE + 0.05, ZE + 0.06), (0.12, 0.0, 0))

# ---------------------------------------------------------------- red en volumen: hilos finos entre estratos (despiece)
def zmid_x(k):
    return zc(k) + DZ[k]


# arcos delante del apilado (enlazan estratos no contiguos) y hilos cortos entre estratos contiguos
ARCOS_RED = [(0, 2, -1.45, -0.95), (0, 4, 0.35, 0.95), (1, 3, 1.25, 1.7), (1, 5, -0.6, -0.1),
             (2, 5, -1.75, -1.35), (3, 5, 0.75, 1.25)]
CORTOS_RED = [(0, 1, -0.25, 0.05), (2, 3, 0.15, -0.2), (3, 4, -0.95, -0.6)]
hilos = []
YF = Y0 - 0.004
for n, (a, b, ua, ub) in enumerate(ARCOS_RED + CORTOS_RED):
    p = Vector((ua, YF, zmid_x(a)))
    q = Vector((ub, YF, zmid_x(b)))
    c = (p + q) / 2 + Vector((0, -(0.12 + 0.13 * (b - a)), 0))
    pts = bez(p, c, q, 36)
    ob = punteada(f'hilo{n:02d}', pts, p, bloque, CIAN, guion=0.07, hueco=0.04, r=0.0085)
    bm = bmesh.new()                              # dos nudos planos sobre las caras frontales
    for v in (Vector((0, 0, 0)), q - p):
        bm_disco(bm, v + Vector((0, 0.002, 0)), 0.03, 0.006, eje=(0, 1, 0), segs=28)
    nudos = bb._obj_from_bm(f'hilo{n:02d}_nudos', bm, CIAN, None, (0, 0, 0))
    nudos.location = ob.location
    ob = unir([ob, nudos], f'hilo{n:02d}')
    hilos.append(ob)

# ---------------------------------------------------------------- etiquetas (máx. 4 por estado)
# estado 0
S.etiqueta('lectura', 'lectura lineal', (2.35, 1.37, 0.05), parent=capas[0], clase='trayecto')
# estado 2
S.etiqueta('gongora', 'Góngora: el romance visible', (-0.9, 1.72, ztop(0)), parent=capas[0])
S.etiqueta('lope', 'Lope: el romance anterior, debajo', (-0.55, -1.72, zc(1) - 0.05), parent=capas[1])
# estado 3
S.etiqueta('cita_sup', 'cita: en la superficie', (-0.55, 1.8, 0.08), parent=capas[0], clase='ajeno')
S.etiqueta('remin', 'reminiscencia: tiñe desde abajo', (2.95, -1.2, zc(3)), parent=bloque)
S.etiqueta('ejemplos', 'Lisandro Otero, <i>La situación</i> · Amelia Peláez', (-1.9, -1.62, zc(5) - 0.2), parent=bloque, clase='nota')
# estado 4
S.etiqueta('fonetico', 'palíndromo: se lee en los dos sentidos', (0.05, y9, ZI + 0.16), parent=capas[0], clase='trayecto')
S.etiqueta('ind1', '«mal de muerte»', (xi1 - 0.62, YL[11] - 0.1, ZH - 0.3), parent=bloque, clase='nota')
S.etiqueta('ind2', '«traspiés en la alabanza»', (xi2 + 0.8, YL[11] - 0.1, ZH - 0.3), parent=bloque, clase='nota')
S.etiqueta('ojo', '«mal de ojo»: bajo la línea', (XE + 0.25, YE - 0.62, ZE), parent=capas[1], clase='sdo')
# estado 5
LBL_RX, LBL_RY, LBL_RZ = -2.75, -0.6, 0.05     # rótulos del despiece: a la izquierda de cada estrato
S.etiqueta('r0', 'superficie y citas', (LBL_RX, LBL_RY, zc(0) + LBL_RZ), parent=capas[0], clase='ajeno')
S.etiqueta('r1', 'filigrana', (LBL_RX, LBL_RY, zc(1) + LBL_RZ), parent=capas[1])
S.etiqueta('r3', 'estratos teñidos', (LBL_RX, LBL_RY, zc(3) + LBL_RZ), parent=capas[3], clase='ajeno')
S.etiqueta('rcond', 'Sarduy, en condicional: «se presentaría… como una red»', (0.4, 1.9, zc(0) + 0.35), parent=capas[0], clase='nota')

# ---------------------------------------------------------------- línea de tiempo
# (en Blender 5.2 la preferencia de interpolación no se aplica a keyframe_insert: toda clave nace BEZIER;
#  por eso: saltos con fotogramas exactos y, al final, interpolación fijada a mano en cada F-curve)
def salto(ob, t, antes, despues):
    fr = int(round(t * bb.FPS))
    S.clave(ob, (fr - 1) / bb.FPS, esc=antes)
    S.clave(ob, fr / bb.FPS, esc=despues)


def _fcurves(action):
    try:
        return list(action.fcurves)
    except AttributeError:
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
        return out


def fijar_interpolacion():
    """Tramos con valores iguales o de un fotograma → CONSTANT; el resto BEZIER con asas auto-clamped."""
    for ob in bpy.data.objects:
        ad = ob.animation_data
        if not ad or not ad.action:
            continue
        for fc in _fcurves(ad.action):
            kps = fc.keyframe_points
            for k in kps:
                k.handle_left_type = 'AUTO_CLAMPED'
                k.handle_right_type = 'AUTO_CLAMPED'
            for i in range(len(kps)):
                a = kps[i]
                if i == len(kps) - 1:
                    a.interpolation = 'CONSTANT'
                    continue
                b = kps[i + 1]
                if abs(a.co[1] - b.co[1]) < 1e-6 or (b.co[0] - a.co[0]) <= 1.01:
                    a.interpolation = 'CONSTANT'
                else:
                    a.interpolation = 'BEZIER'
            fc.update()


def aparece(ob, t0, t1, esc=1.0):
    S.clave(ob, 0, esc=OFF, interp=C)
    S.clave(ob, t0, esc=OFF)
    S.clave(ob, t1, esc=esc)


R90, R0 = (math.radians(90), 0, 0), (0, 0, 0)
# ── estado 1 (0 → 2.5 s): la página se acuesta; las citas se pegan encima
ZUP = D / 2 + zc(5) - H / 2      # de pie, la página se apoya en el suelo de sombras (base de la última tablilla)
S.clave(bloque, 0, loc=(0, 0, ZUP), rot=R90, interp=C)
S.clave(bloque, 0.25, loc=(0, 0, ZUP), rot=R90)
S.clave(bloque, 1.5, loc=(0, 0, 0), rot=R0)
S.clave(lect, 0, esc=1.0, interp=C)
S.clave(lect, 0.1, esc=1.0)
S.clave(lect, 0.4, esc=OFF)
for i, g in enumerate(citas):
    base = Vector(g.location)
    alto = base + Vector((0, 0, 0.9))
    t = 1.45 + 0.14 * i
    S.clave(g, 0, loc=alto, esc=OFF, interp=C)
    S.clave(g, t, loc=alto, esc=OFF)
    S.clave(g, t + 0.55, loc=base, esc=1.0)
    # estado 2: se retiran
    S.clave(g, 2.7, loc=base, esc=1.0)
    S.clave(g, 3.0, loc=alto, esc=OFF)
    # estado 3: vuelven (contraste con la reminiscencia)
    t3 = 4.6 + 0.08 * i
    S.clave(g, t3, loc=alto, esc=OFF)
    S.clave(g, t3 + 0.4, loc=base, esc=1.0)
    # estado 4: se retiran
    S.clave(g, 6.05, loc=base, esc=1.0)
    S.clave(g, 6.35, loc=alto, esc=OFF)
    # estado 5: vuelven
    t5 = 8.75 + 0.08 * i
    S.clave(g, t5, loc=alto, esc=OFF)
    S.clave(g, t5 + 0.4, loc=base, esc=1.0)

# ── estado 2 (2.5 → 3.9 s): la superficie se vuelve una hoja translúcida y se levanta: debajo, otro texto
S.clave(llenas[0], 0, esc=1.0, interp=C)
S.clave(contornos[0], 0, esc=1.0, interp=C)
S.clave(velo, 0, esc=OFF, interp=C)
S.clave(filete, 0, esc=OFF, interp=C)
for ob, a, b in ((llenas[0], 1.0, OFF), (contornos[0], 1.0, OFF), (velo, OFF, 1.0), (filete, OFF, 1.0)):
    salto(ob, 3.0, a, b)
for k in range(6):
    S.clave(capas[k], 0, loc=(0, 0, 0), interp=C)
S.clave(capas[0], 3.0, loc=(0, 0, 0))
S.clave(capas[0], 3.8, loc=(0, 0, LIFT2))

# ── estado 3 (3.9 → 6.1 s): la superficie vuelve; la reminiscencia tiñe los estratos desde abajo
S.clave(capas[0], 4.0, loc=(0, 0, LIFT2))
S.clave(capas[0], 4.55, loc=(0, 0, 0))
for ob, a, b in ((llenas[0], OFF, 1.0), (contornos[0], OFF, 1.0), (velo, 1.0, OFF), (filete, 1.0, OFF)):
    salto(ob, 4.6, a, b)
for k, t in zip((5, 4, 3, 2), (4.9, 5.25, 5.6, 5.95)):
    S.clave(llenas[k], 0, esc=1.0, interp=C)
    salto(llenas[k], t, 1.0, OFF)
    S.clave(llenas_t[k], 0, esc=OFF, interp=C)
    salto(llenas_t[k], t, OFF, 1.0)

# ── estado 4 (6.1 → 8.5 s): el tinte se retira (los gramas son intratextuales, l. 606-608); la superficie vuelve
#    a ser hoja translúcida y se levanta; el renglón 9 se alza en letras; bajo la línea, el ojo
for k, t in zip((2, 3, 4, 5), (6.15, 6.22, 6.29, 6.36)):
    salto(llenas_t[k], t, 1.0, OFF)
    salto(llenas[k], t, OFF, 1.0)
for ob, a, b in ((llenas[0], 1.0, OFF), (contornos[0], 1.0, OFF), (velo, OFF, 1.0), (filete, OFF, 1.0)):
    salto(ob, 6.45, a, b)
S.clave(capas[0], 6.5, loc=(0, 0, 0))
S.clave(capas[0], 7.1, loc=(0, 0, LIFT4))
# palíndromo: el renglón se levanta en letras (escala vertical desde el renglón)
S.clave(renglon9, 0, esc=1.0, interp=C)
salto(renglon9, 6.75, 1.0, OFF)
S.clave(pal, 0, esc=OFF, interp=C)
salto(pal, 6.75, OFF, (1, 1, OFF))
S.clave(pal, 7.35, esc=(1, 1, 1))
aparece(ida, 7.35, 7.75)
aparece(vuelta, 7.55, 7.95)
# grama sémico
S.clave(ind_tinta, 0, esc=1.0, interp=C)
salto(ind_tinta, 6.9, 1.0, OFF)
S.clave(ind_cian, 0, esc=OFF, interp=C)
salto(ind_cian, 6.9, OFF, 1.0)
for o in ojo:
    aparece(o, 7.2, 7.6)
S.clave(lope, 0, esc=1.0, interp=C)                 # los versos de Lope se apartan: bajo la hoja, sólo el ojo
salto(lope, 6.45, 1.0, OFF)
salto(lope, 9.0, OFF, 1.0)
for f in (fl1, fl2):
    aparece(f, 7.6, 8.1)

# ── estado 5 (8.5 → 11.4 s): la hoja baja y vuelve a ser superficie; despiece vertical; hilos
T5 = 8.55
S.clave(pal, T5, esc=(1, 1, 1))
S.clave(pal, T5 + 0.3, esc=(1, 1, OFF))
salto(pal, T5 + 0.33, (1, 1, OFF), OFF)
salto(renglon9, T5 + 0.33, OFF, 1.0)
for o in (ida, vuelta, fl1, fl2) + tuple(ojo):
    S.clave(o, T5, esc=1.0)
    S.clave(o, T5 + 0.25, esc=OFF)
salto(ind_cian, T5 + 0.2, 1.0, OFF)
salto(ind_tinta, T5 + 0.2, OFF, 1.0)
S.clave(capas[0], 8.6, loc=(0, 0, LIFT4))
S.clave(capas[0], 9.0, loc=(0, 0, 0))
for ob, a, b in ((llenas[0], OFF, 1.0), (contornos[0], OFF, 1.0), (velo, 1.0, OFF), (filete, 1.0, OFF)):
    salto(ob, 9.0, a, b)
# la reminiscencia vuelve a teñir los estratos profundos (desde abajo) antes del despiece
for k, t in zip((5, 4, 3, 2), (9.0, 9.07, 9.14, 9.21)):
    salto(llenas[k], t, 1.0, OFF)
    salto(llenas_t[k], t, OFF, 1.0)
TE0, TE1 = 9.3, 10.5
for k in range(6):
    S.clave(capas[k], TE0, loc=(0, 0, 0))
    S.clave(capas[k], TE1, loc=(0, 0, DZ[k]))
for n, h in enumerate(hilos):
    t = TE1 + 0.06 * n
    aparece(h, t, t + 0.35)
T_FIN = TE1 + 0.06 * (len(hilos) - 1) + 0.4

# ── rótulos: el visor los enciende al entrar en el estado, antes de que termine la animación.
#    Cada ancla espera «aparcada» fuera del plano lejano de la cámara (el CSS2DRenderer oculta lo que
#    queda fuera de [-1, 1] en z) y salta a su sitio cuando aparece su objeto.
PARK = Vector((0, 0, 900))


def aparcar(clave, t_on):
    ob = bpy.data.objects['lbl_' + clave]
    real = Vector(ob.location)
    fr = int(round(t_on * bb.FPS))
    S.clave(ob, 0, loc=real + PARK)
    S.clave(ob, (fr - 1) / bb.FPS, loc=real + PARK)
    S.clave(ob, fr / bb.FPS, loc=real)


for clave, t_on in [('c_rulfo', 1.45 + 0.4), ('c_hugues', 1.59 + 0.4), ('c_rocamadour', 1.73 + 0.4), ('c_cruz', 1.87 + 0.4),
                    ('gongora', 3.0), ('lope', 3.0),
                    ('cita_sup', 4.95), ('remin', 5.0), ('ejemplos', 5.0),
                    ('ind1', 6.9), ('ind2', 6.9), ('fonetico', 7.4), ('ojo', 7.55),
                    ('rcond', 9.3), ('r0', 10.0), ('r1', 10.0), ('r3', 10.0)]:
    aparcar(clave, t_on)

# ---------------------------------------------------------------- estados
def camara(look, az, el, dist, fov):
    """Cámara orbital: azimut desde el frente (-Y; negativo = desde la izquierda), elevación y distancia."""
    a, e = math.radians(az), math.radians(el)
    cam = (look[0] + dist * math.cos(e) * math.sin(a), look[1] - dist * math.cos(e) * math.cos(a), look[2] + dist * math.sin(e))
    return dict(cam=tuple(round(v, 3) for v in cam), look=look, fov=fov)


# encuadres pensados para el visor incrustado (1920 × 983) y la pantalla completa (16:9): el objeto a la izquierda
# de la tarjeta de texto (abajo a la derecha) y por encima de la barra de estados
FRENTE = camara((0.846, 0.3, 0.224), -13, 8, 24.8, 9.8)
CITA = camara((0.968, -0.35, -0.73), -12, 50, 8.7, 30)
FILI = camara((1.985, -0.2, -0.67), -14, 34, 10.72, 30)
REMI = camara((1.628, -0.2, -1.671), -30, 30, 10.02, 32)
GRAM = camara((0.866, -0.55, -0.378), -8, 26, 7.6, 32)
RED = camara((0.897, 0.0, -0.031), -18, 20, 9.62, 36)

S.estado('Superficie',
         'La página de frente: renglones paralelos y regulares, un solo sentido de lectura. Debajo hay otros textos.',
         '«recorrido lineal, fijado, “normal” de la página» · l. 615',
         etiquetas=['lectura'], orbita=False, t1=0, **FRENTE)
S.estado('Cita',
         'La cita: un texto ajeno pegado sobre la superficie, «sin que su voz se altere». García Márquez incorpora una frase de Rulfo y personajes de otros autores.',
         'Intertextualidad: la cita · l. 530-547',
         etiquetas=['c_rulfo', 'c_hugues', 'c_rocamadour', 'c_cruz'], t1=2.5, **CITA)
S.estado('Filigrana',
         'A contraluz, la superficie se vuelve translúcida y deja ver otro texto debajo: el romance de Lope que el de Góngora desfigura y que «hay que leer en filigrana».',
         'Jammes, cit. por Sarduy · l. 408-424',
         etiquetas=['gongora', 'lope'], t1=3.9,
         pregunta='Para Jammes, esa dependencia la hace «menor». ¿Y para Sarduy?', **FILI)
S.estado('Reminiscencia',
         'A diferencia de la cita, la reminiscencia no aflora: se funde con el texto receptor y lo tiñe desde abajo, «modificando con sus texturas su geología».',
         'l. 533-538; ejemplos, l. 589-602',
         etiquetas=['cita_sup', 'remin', 'ejemplos'], t1=6.1, **REMI)
S.estado('Gramas',
         'Intratextualidad, «escritura entre la escritura». Gramas fonéticos: las letras del renglón admiten otra lectura. Grama sémico: bajo la línea, dos indicadores convergen hacia un idiom que no aflora.',
         'l. 604-686 · Cabrera Infante, l. 655 · Paradiso, l. 670-677',
         etiquetas=['fonetico', 'ind1', 'ind2', 'ojo'], t1=8.5, **GRAM)
S.estado('Red en volumen',
         'Todos los estratos a la vez: una red de conexiones, de sucesivas filigranas. Sarduy lo formula en condicional: su expresión gráfica «no sería lineal… sino en volumen».',
         'l. 459-462 (condicional)',
         etiquetas=['r0', 'r1', 'r3', 'rcond'], t1=round(T_FIN, 2),
         slider={'tipo': 'tiempo', 't0': TE0, 't1': round(T_FIN, 2), 'etiqueta': 'de la página al volumen',
                 'min_txt': 'bloque', 'max_txt': 'red'}, **RED)

fijar_interpolacion()

# pósters (EEVEE): la hoja translúcida se ve casi opaca con las luces de póster; sólo para el render
# de los pósters se aclara (el GLB ya se exportó con los valores del visor).
_posters_bb = S._posters


def _posters_velo(res):
    b = VELO.node_tree.nodes.get('Principled BSDF')
    b.inputs['Alpha'].default_value = 0.16
    b.inputs['Emission Strength'].default_value = 0.0
    _posters_bb(res)


S._posters = _posters_velo
S.exportar()
