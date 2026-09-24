"""N5 · Estratos — leer en filigrana: cita, reminiscencia y gramas (Sarduy 1972, l. 406-771).

Un bloque-texto de 6 losas (4 × 3 × 1,2 m). Coordenadas locales del grupo «bloque»: acostado,
superficie de lectura arriba (z = 0), renglones a lo largo de X, apilados en Y (primer renglón en +Y).
En el estado 0 el bloque está de pie (rot. X +90°): la superficie mira a -Y, como una página.

Estratos (de arriba abajo):
  capa0  superficie: el texto visible (marfil, renglones de tinta)      → cita (placas magenta encima)
  capa1  texto en filigrana (nácar, versos en sepia)                    → parodia: Góngora sobre Lope
  capa2-5 geología del texto (piedra); en el estado 3 las tiñe desde abajo la reminiscencia (magenta fundido)
Gramas (estado 4): palíndromo en tipos de tinta con arcos de lectura; grama sémico: dos indicadores
convergen hacia una cámara bajo el último renglón («mal de ojo», oro).
Red en volumen (estado 5): despiece vertical con hilos; descripción en condicional (l. 459-462).
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


def tubo(nombre, puntos, r, material, parent=None, loc=(0, 0, 0), lados=8):
    """Tubo continuo (barrido) a lo largo de `puntos` (coordenadas relativas a loc)."""
    bm = bmesh.new()
    tubo_bm(bm, puntos, r, lados)
    return bb._obj_from_bm(nombre, bm, material, parent, loc)


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
    """Malla compartida de una letra (Georgia), de pie mirando a -Y; devuelve (mesh, zmin, alto)."""
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


def palabras(x0, x1, lmin=0.1, lmax=0.42, gap=0.05):
    """Segmentos-palabra entre x0 y x1 (el último se estira hasta x1: renglón justificado)."""
    out, x = [], x0
    while x < x1 - 1e-6:
        L = RNG.uniform(lmin, lmax)
        if x + L + gap + lmin > x1:
            L = x1 - x
        out.append((x, x + L))
        x += L + gap
    return out


# ---------------------------------------------------------------- materiales
PAPEL = M('lamina')                         # superficie: el texto visible
NACAR = M('significante')                   # texto en filigrana
TINTA = mat_hex('tinta_renglon', '#3A322B', rough=0.5)
SEPIA = mat_hex('sepia_renglon', '#7A4024', rough=0.55)
VELO = mat_hex('papel_contraluz', '#F1EADC', rough=0.45, emi='#F3EDE2', emis=0.5, alpha=0.36)   # único translúcido (luz a contraluz)
MAG = M('ajeno')
COSTURA = mat_hex('costura', '#F3EDE2', rough=0.5)
CIAN = M('trayecto')
ORO = M('significado')
BERM = M('ausencia')
HUECO = mat_hex('hueco', '#1A1310', rough=0.95)

COL_PIEDRA = ['#E9E1D2', '#CFC6B8', '#B9AFA1', '#A59B8E', '#92887C', '#7F766B']
COL_TINTE = [None, None, '#C69EA2', '#C27A91', '#C65A8A', '#D4448A']   # la reminiscencia tiñe hacia arriba
MAT_BASE = [PAPEL, NACAR] + [mat_hex(f'estrato{k}', COL_PIEDRA[k], rough=0.8) for k in range(2, 6)]
MAT_TINTE = [PAPEL, NACAR] + [mat_hex(f'tinte{k}', COL_TINTE[k], rough=0.55, coat=0.25) for k in range(2, 6)]

# ---------------------------------------------------------------- bloque y losas
W, D, TH, GAP = 4.0, 3.0, 0.2, 0.008
Y0, Y1 = -D / 2, D / 2
YC = -1.22                 # plano del corte del estado 4 (cara frontal nueva)
H = TH - GAP
BEV = 0.012
DZ = [(5 - k) * 0.45 for k in range(6)]     # despiece vertical (estado 5)


def zc(k):
    return -k * TH - TH / 2


def ztop(k):
    return zc(k) + H / 2


bloque = bb.grupo('bloque')
capas = [bb.grupo(f'capa{k}', (0, 0, 0), bloque) for k in range(6)]

llenas, llenas_t, cortadas = {}, {}, {}
for k in range(6):
    llenas[k] = bb.caja(f'losa{k}', (W, D, H), (0, 0, zc(k)), MAT_BASE[k], capas[k], bevel=BEV)
    if k >= 2:
        llenas_t[k] = bb.caja(f'losa{k}_tinte', (W, D, H), (0, 0, zc(k)), MAT_TINTE[k], capas[k], bevel=BEV)
    cortadas[k] = bb.caja(f'losa{k}_corte', (W, Y1 - YC, H), (0, (YC + Y1) / 2, zc(k)), MAT_BASE[k], capas[k], bevel=BEV)
velo = bb.caja('losa0_velo', (W, D, H), (0, 0, zc(0)), VELO, capas[0], bevel=BEV)

# cámara oval bajo el último renglón (grama sémico): hueco por Boolean en las losas cortadas
XC, ZC = -0.85, -0.5
RX, RY, RZ = 0.5, 0.3, 0.24
cort = bb.esfera('cortador', 1.0, (XC, YC, ZC), HUECO, None, subdiv=3)
cort.scale = (RX, RY, RZ)
bpy.context.view_layer.update()
for k in (1, 2, 3):
    ob = cortadas[k]
    mod = ob.modifiers.new('camara', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cort
    try:
        mod.solver = 'EXACT'
    except Exception:
        pass
    try:
        mod.material_mode = 'TRANSFER'
    except Exception:
        pass
    bb.aplicar(ob)
    for p in ob.data.polygons:
        p.use_smooth = False
bpy.data.objects.remove(cort)

# rebanada frontal que cae en el estado 4 (colores finales)
piezas = [bb.caja(f'rebanada{k}', (W, YC - Y0, H), (0, 0, zc(k) + 0.6), MAT_BASE[k], None, bevel=BEV) for k in range(6)]
reb = unir(piezas, 'rebanada')
reb.parent = bloque
reb.location = (0, (Y0 + YC) / 2, -0.6)

# ---------------------------------------------------------------- renglones de la superficie (tinta)
YL = [1.2 - i * (2.3 / 11) for i in range(12)]
SPEC = {0: (-1.7, 1.7), 1: (-1.7, 1.7), 2: (-1.7, 1.7), 3: (-1.7, 0.35), 4: (-1.45, 1.7), 5: (-1.7, 1.7),
        6: (-1.7, 1.7), 7: (-1.7, 0.9), 8: (-1.45, 1.7), 9: (-1.7, 1.7), 10: (-1.7, 1.7), 11: (-1.7, 1.1)}
IND = [(-1.7, -1.22), (-0.55, 0.22)]           # «mal de muerte», «traspiés en la alabanza»
BY, BZ = 0.07, 0.022
ZB = ztop(0) + BZ / 2 - 0.002


def barras(bm, segs, y, h=BZ, z=ZB, ancho=BY):
    for a, b in segs:
        bm_caja(bm, (b - a, ancho, h), ((a + b) / 2, y, z))


bm = bmesh.new()
for i, y in enumerate(YL):
    if i in (9, 11):
        continue
    barras(bm, palabras(*SPEC[i]), y)
barras(bm, palabras(-1.17, -0.6) + palabras(0.27, 1.1), YL[11])
renglones = malla('renglones', bm, TINTA, capas[0])

bm = bmesh.new()
barras(bm, palabras(*SPEC[9]), YL[9])
renglon9 = malla('renglon_palindromo', bm, TINTA, capas[0])

bm = bmesh.new()
barras(bm, IND, YL[11])
ind_tinta = malla('indicadores_tinta', bm, TINTA, capas[0])
bm = bmesh.new()
barras(bm, IND, YL[11], h=0.034, z=ztop(0) + 0.015, ancho=0.085)
ind_cian = malla('indicadores', bm, CIAN, capas[0])

# lectura lineal (estado 0): flecha cian sobre el primer renglón
ZL = ztop(0) + 0.03
lect = punteada('lectura', [(-1.7, 1.375, ZL), (1.74, 1.375, ZL)], (0, 1.375, ZL), capas[0], CIAN,
                flecha={'r': 0.05, 'largo': 0.13}, guion=0.13, hueco=0.08, r=0.016)

# ---------------------------------------------------------------- texto en filigrana (capa1): versos en sepia
bm = bmesh.new()
for j in range(13):
    y = 1.3 - j * 0.2
    x1 = -1.7 + RNG.uniform(1.6, 2.7)
    barras(bm, palabras(-1.7, x1, 0.12, 0.5, 0.06), y, h=0.016, z=ztop(1) + 0.006, ancho=0.075)
lope = malla('renglones_filigrana', bm, SEPIA, capas[1])

# ---------------------------------------------------------------- citas: placas magenta de borde vivo, con costura
CITAS = [('rulfo', 1, -0.95, 1.1, 'una frase de Rulfo', 2.5),
         ('hugues', 4, 0.8, 0.7, 'Víctor Hugues · Carpentier', -3.0),
         ('rocamadour', 6, -0.55, 0.76, 'Rocamadour · Cortázar', 3.0),
         ('cruz', 8, 0.95, 0.7, 'Artemio Cruz · Fuentes', -2.0)]
PH, PT = 0.25, 0.05
ZP = ztop(0) + BZ + PT / 2
citas = []
for clave, i, x, L, html, giro in CITAS:
    placa = bb.caja('cita_' + clave, (L, PH, PT), (0, 0, 0), MAG, None)
    ix, iy = L / 2 - 0.036, PH / 2 - 0.036
    rect = [(-ix, -iy, PT / 2 + 0.002), (ix, -iy, PT / 2 + 0.002), (ix, iy, PT / 2 + 0.002),
            (-ix, iy, PT / 2 + 0.002), (-ix, -iy, PT / 2 + 0.002)]
    cos_ = bb.polilinea_punteada('costura_' + clave, rect, guion=0.045, hueco=0.03, r=0.008, material=COSTURA, parent=None)
    g = unir([placa, cos_], 'cita_' + clave)
    g.parent = capas[0]
    g.location = (x, YL[i], ZP)
    g.rotation_euler = (0, 0, math.radians(giro))
    S.etiqueta('c_' + clave, html, (x, YL[i] + 0.08, ZP + 0.22), parent=capas[0], clase='ajeno')
    citas.append(g)

# ---------------------------------------------------------------- gramas fonéticos: palíndromo (l. 655)
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
# letras sueltas: comparten malla por letra; el grupo sólo se TRASLADA (aparcado dentro de la losa 1,
# emerge por el renglón 9 y queda suspendido sobre él en el estado 4): el exportador no hornea a los hijos.
Z_PAL_ARRIBA = ztop(0) + 0.3                   # base de las letras, suspendidas sobre su renglón
Z_PAL_ABAJO = ztop(1) - 0.186                  # aparcado dentro de la losa 1 (opaca)
pal = bb.grupo('palindromo', (0, y9, Z_PAL_ABAJO), capas[1])
letras = [c for c in FRASE if c != ' ']
altos = []
for n, (ch, xv) in enumerate(zip(letras, xs)):
    me, ymin, alto = glifo(ch, TAM, 0.016)
    if not me.materials:
        me.materials.append(NACAR)
    ob = bpy.data.objects.new(f'letra{n:02d}', me)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = (xv, 0, -ymin)
    bb._link(ob, pal)
    altos.append(alto)
print('[estratos] alto máx. de letra', round(max(altos), 3), 'losa', round(H, 3))
Z0 = Z_PAL_ARRIBA + sorted(altos)[len(altos) // 2] + 0.045      # arranque común de los arcos
arcos = []
for k in range(12):
    a, b = xs[k], xs[24 - k]
    cx, rx = (a + b) / 2, (b - a) / 2
    ry = 0.05 + 0.24 * rx
    pts = bb.arco(0, 0, rx, ry, 180, 0, n=40 + int(rx * 30), z=0, plano='XZ')
    arcos.append(tubo(f'arco{k:02d}', pts, 0.0095, CIAN, capas[0], (cx, y9, Z0)))
ALTO_ARCO = 0.05 + 0.24 * (xs[24] - xs[0]) / 2

# ---------------------------------------------------------------- grama sémico: cámara, núcleo, indicadores
nucleo = bb.esfera('nucleo_mal_de_ojo', 1.0, (XC, YC + 0.1, ZC), ORO, bloque, subdiv=3)
nucleo.scale = (0.3, 0.13, 0.14)
NUC = (0.3, 0.13, 0.14)
cont = bb.polilinea_punteada('contorno_camara', bb.arco(0, 0, RX + 0.035, RZ + 0.035, 90, 450, n=140, z=0, plano='XZ'),
                             guion=0.085, hueco=0.05, r=0.017, material=BERM, parent=bloque)
cont.location = (XC, YC - 0.02, ZC)


def flecha_sem(nombre, pts):
    return punteada(nombre, pts, pts[0], bloque, CIAN, flecha={'r': 0.042, 'largo': 0.11},
                    guion=0.06, hueco=0.04, r=0.013)


xi1, xi2 = sum(IND[0]) / 2, sum(IND[1]) / 2
zf = ztop(0) + 0.05
fl1 = flecha_sem('indicador1', [(xi1, YL[11], zf), (xi1 + 0.04, YC - 0.03, 0.0), (XC - 0.43, YC - 0.03, ZC + 0.13)])
fl2 = flecha_sem('indicador2', [(xi2, YL[11], zf), (xi2 - 0.06, YC - 0.03, 0.0), (XC + 0.43, YC - 0.03, ZC + 0.13)])

# ---------------------------------------------------------------- red en volumen: hilos entre estratos (posiciones del despiece)
def zbot_x(k):
    return ztop(k) - H + DZ[k]


def ztop_x(k):
    return ztop(k) + DZ[k]


def zmid_x(k):
    return zc(k) + DZ[k]


def bez(p0, c, p1, n=30):
    return [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1 for t in (i / n for i in range(n + 1))]


# arcos delante del apilado (enlazan estratos no contiguos) y hilos cortos en los intersticios (contiguos)
ARCOS_RED = [(0, 2, -1.55, -0.95), (0, 4, -0.3, 0.4), (1, 3, 0.85, 1.45), (1, 5, -0.95, -0.3),
             (2, 4, -1.8, -1.35), (3, 5, 0.45, 1.05), (0, 3, 1.25, 1.8), (2, 5, 0.1, -0.5)]
GAPS_RED = [(0, -0.75, -0.45), (1, 0.35, 0.8), (2, -1.25, -0.9), (3, 1.3, 0.95), (4, -0.2, 0.25)]
hilos = []
YF = Y0 - 0.006
for n, (a, b, ua, ub) in enumerate(ARCOS_RED):
    p = Vector((ua, YF, zmid_x(a)))
    q = Vector((ub, YF, zmid_x(b)))
    c = (p + q) / 2 + Vector((0, -(0.32 + 0.1 * (b - a)), 0))
    bm = bmesh.new()
    tubo_bm(bm, [v - p for v in bez(p, c, q)], 0.014, 8)
    for v in (Vector((0, 0, 0)), q - p):
        gs = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.042)
        bmesh.ops.translate(bm, vec=v, verts=gs['verts'])
    hilos.append(bb._obj_from_bm(f'hilo{n:02d}', bm, CIAN, bloque, tuple(p)))
for m, (k, ua, ub) in enumerate(GAPS_RED):
    p = Vector((ua, Y0 + 0.22, ztop(k) - H + DZ[k]))
    q = Vector((ub, Y0 + 0.32, ztop(k + 1) + DZ[k + 1]))
    bm = bmesh.new()
    tubo_bm(bm, [Vector((0, 0, 0)), q - p], 0.013, 8)
    for v in (Vector((0, 0, 0)), q - p):
        gs = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.036)
        bmesh.ops.translate(bm, vec=v, verts=gs['verts'])
    hilos.append(bb._obj_from_bm(f'hilo{len(ARCOS_RED) + m:02d}', bm, CIAN, bloque, tuple(p)))

# ---------------------------------------------------------------- anclas de rótulos (coords. del padre)
LBL_RECEPTOR = (-0.3, 1.9, 0.12)
LBL_GONGORA = (-1.0, 1.75, zc(0))
LBL_LOPE = (-0.6, -1.8, zc(1))
LBL_MARCA = (3.1, 0.9, 0.1)
LBL_CITA_SUP = (-0.5, 1.9, 0.15)
LBL_REMIN = (3.1, -1.5, -1.75)
LBL_EJEMPLOS = (-2.35, -1.62, zc(5) - 0.08)
LBL_IND1 = (xi1 - 0.3, YC - 0.05, -0.2)
LBL_IND2 = (xi2 + 0.42, YC - 0.05, -0.2)
LBL_SEMICO = (XC + 1.45, YC - 0.05, ZC + 0.02)
LBL_RCOND = (0.6, 1.95, zc(0) + 0.3)

# ---------------------------------------------------------------- etiquetas
# estado 0
S.etiqueta('lectura', 'lectura lineal', (-2.5, 1.375, 0.05), parent=capas[0], clase='trayecto')
# estado 1
S.etiqueta('receptor', 'texto receptor: García Márquez, <i>Cien años de soledad</i>', LBL_RECEPTOR, parent=capas[0], clase='snte')
# estado 2
S.etiqueta('gongora', 'Góngora: el romance visible', LBL_GONGORA, parent=capas[0], clase='serif')
S.etiqueta('lope', 'Lope: el romance anterior, debajo', LBL_LOPE, parent=capas[1], clase='serif')
S.etiqueta('marca', 'filigrana: la marca de agua, visible a contraluz', LBL_MARCA, parent=capas[0], clase='nota')
# estado 3
S.etiqueta('cita_sup', 'cita: marcas visibles en la superficie', LBL_CITA_SUP, parent=capas[0], clase='ajeno')
S.etiqueta('remin', 'reminiscencia: tiñe desde abajo, sin aflorar', LBL_REMIN, parent=bloque, clase='serif')
S.etiqueta('ejemplos', 'Lisandro Otero, <i>La situación</i> · Amelia Peláez', LBL_EJEMPLOS, parent=capas[5], clase='ajeno')
# estado 4
S.etiqueta('fonetico', 'grama fonético: un palíndromo, legible en los dos sentidos', (xs[12], y9, Z0 + ALTO_ARCO + 0.16), parent=capas[0], clase='trayecto')
S.etiqueta('ind1', '«mal de<br>muerte»', LBL_IND1, parent=bloque, clase='trayecto')
S.etiqueta('ind2', '«traspiés en<br>la alabanza»', LBL_IND2, parent=bloque, clase='trayecto')
S.etiqueta('ojo', '«mal de ojo»', (XC, YC - 0.05, ZC - 0.42), parent=bloque, clase='grande sdo')
S.etiqueta('semico', 'grama sémico, bajo la línea · Lezama, <i>Paradiso</i>', LBL_SEMICO, parent=bloque, clase='nota')
# estado 5
S.etiqueta('r0', 'superficie y citas', (-2.95, 0, zc(0)), parent=capas[0], clase='ajeno')
S.etiqueta('r1', 'texto en filigrana', (-2.95, 0, zc(1)), parent=capas[1], clase='snte')
S.etiqueta('r3', 'estratos teñidos: reminiscencia', (-2.95, 0, zc(3)), parent=capas[3], clase='ajeno')
S.etiqueta('rcond', 'Sarduy, en condicional: «se presentaría… como una red»', LBL_RCOND, parent=capas[0], clase='nota')

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


R90, R0 = (math.radians(90), 0, 0), (0, 0, 0)
LIFT = 0.5
# ── estado 1 (0 → 2.5 s): la página se acuesta; las citas se pegan encima
S.clave(bloque, 0, rot=R90, interp=C)
S.clave(bloque, 0.25, rot=R90)
S.clave(bloque, 1.5, rot=R0)
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

# ── estado 2 (2.5 → 3.9 s): la superficie se vuelve translúcida y se levanta: debajo, otro texto
S.clave(llenas[0], 0, esc=1.0, interp=C)
salto(llenas[0], 3.0, 1.0, OFF)
S.clave(velo, 0, esc=OFF, interp=C)
salto(velo, 3.0, OFF, 1.0)
for k in range(6):
    S.clave(capas[k], 0, loc=(0, 0, 0), interp=C)
S.clave(capas[0], 3.0, loc=(0, 0, 0))
S.clave(capas[0], 3.8, loc=(0, 0, LIFT))

# ── estado 3 (3.9 → 6.1 s): la superficie vuelve; la reminiscencia tiñe los estratos desde abajo
S.clave(capas[0], 4.0, loc=(0, 0, LIFT))
S.clave(capas[0], 4.55, loc=(0, 0, 0))
salto(velo, 4.6, 1.0, OFF)
salto(llenas[0], 4.6, OFF, 1.0)
for k, t in zip((5, 4, 3, 2), (4.9, 5.25, 5.6, 5.95)):
    S.clave(llenas[k], 0, esc=1.0, interp=C)
    salto(llenas[k], t, 1.0, OFF)
    S.clave(llenas_t[k], 0, esc=OFF, interp=C)
    salto(llenas_t[k], t, OFF, 1.0)
S.clave(llenas[1], 0, esc=1.0, interp=C)

# ── estado 4 (6.1 → 8.5 s): el tinte se retira (los gramas son intratextuales, no «alógenos», l. 606-608);
#    corte bajo el renglón; gramas
TCUT = 6.5
for k, t in zip((2, 3, 4, 5), (6.15, 6.22, 6.29, 6.36)):
    salto(llenas_t[k], t, 1.0, OFF)
    salto(llenas[k], t, OFF, 1.0)
arriba = llenas
for k in range(6):
    salto(arriba[k], TCUT, 1.0, OFF)
    S.clave(cortadas[k], 0, esc=OFF, interp=C)
    salto(cortadas[k], TCUT, OFF, 1.0)
p_reb = Vector(reb.location)
S.clave(reb, 0, loc=p_reb, esc=OFF, interp=C)
salto(reb, TCUT, OFF, 1.0)
S.clave(reb, TCUT + 0.05, loc=p_reb)
S.clave(reb, 6.8, esc=1.0)
S.clave(reb, 7.25, loc=p_reb + Vector((0, -0.4, -1.5)), esc=OFF)
# palíndromo: el renglón se levanta en letras
S.clave(renglon9, 0, esc=1.0, interp=C)
salto(renglon9, 6.7, 1.0, OFF)
P_ABAJO, P_ARRIBA = (0, y9, Z_PAL_ABAJO), (0, y9, Z_PAL_ARRIBA)
S.clave(pal, 0, loc=P_ABAJO, interp=C)
S.clave(pal, 6.65, loc=P_ABAJO)
S.clave(pal, 7.3, loc=P_ARRIBA)
for k, a in enumerate(arcos):          # del centro hacia afuera
    t = 7.3 + 0.07 * (11 - k)
    S.clave(a, 0, esc=OFF, interp=C)
    S.clave(a, t, esc=OFF)
    S.clave(a, t + 0.4, esc=1.0)
# grama sémico
S.clave(ind_tinta, 0, esc=1.0, interp=C)
salto(ind_tinta, 6.9, 1.0, OFF)
S.clave(ind_cian, 0, esc=OFF, interp=C)
salto(ind_cian, 6.9, OFF, 1.0)
S.clave(nucleo, 0, esc=OFF, interp=C)
S.clave(nucleo, 7.2, esc=OFF)
S.clave(nucleo, 7.6, esc=NUC)
S.clave(cont, 0, esc=OFF, interp=C)
salto(cont, 7.3, OFF, 1.0)
for f in (fl1, fl2):
    S.clave(f, 0, esc=OFF, interp=C)
    S.clave(f, 7.5, esc=OFF)
    S.clave(f, 8.0, esc=1.0)

# ── estado 5 (8.5 → 11.4 s): se cierra el corte; despiece vertical; hilos
T5 = 8.55
S.clave(pal, T5, loc=P_ARRIBA)
S.clave(pal, T5 + 0.34, loc=P_ABAJO)
salto(renglon9, T5 + 0.36, OFF, 1.0)
for a in arcos:
    S.clave(a, T5, esc=1.0)
    S.clave(a, T5 + 0.3, esc=OFF)
salto(ind_cian, T5 + 0.2, 1.0, OFF)
salto(ind_tinta, T5 + 0.2, OFF, 1.0)
S.clave(nucleo, T5, esc=NUC)
S.clave(nucleo, T5 + 0.3, esc=OFF)
salto(cont, T5 + 0.2, 1.0, OFF)
for f in (fl1, fl2):
    salto(f, T5 + 0.2, 1.0, OFF)
for k in range(6):
    salto(cortadas[k], T5 + 0.36, 1.0, OFF)
    salto(arriba[k], T5 + 0.36, OFF, 1.0)
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
    S.clave(h, 0, esc=OFF, interp=C)
    S.clave(h, t, esc=OFF)
    S.clave(h, t + 0.35, esc=1.0)
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


for clave, t_on in [('receptor', 1.5),
                    ('c_rulfo', 1.45 + 0.4), ('c_hugues', 1.59 + 0.4), ('c_rocamadour', 1.73 + 0.4), ('c_cruz', 1.87 + 0.4),
                    ('gongora', 3.0), ('lope', 3.0), ('marca', 3.0),
                    ('cita_sup', 4.95), ('remin', 5.0), ('ejemplos', 5.0),
                    ('ind1', 6.9), ('ind2', 6.9), ('fonetico', 7.35), ('semico', 7.35), ('ojo', 7.55),
                    ('rcond', 9.3), ('r0', 10.0), ('r1', 10.0), ('r3', 10.0)]:
    aparcar(clave, t_on)

# ---------------------------------------------------------------- estados
FRENTE = dict(cam=(0, -46, -0.35), look=(0, 0, -0.35), fov=6.8)
CITA = dict(cam=(-0.57, -7.29, 4.95), look=(1.8, 0.0, -1.47), fov=34)
FILI = dict(cam=(1.07, -4.09, 8.3), look=(1.5, 0.0, -0.92), fov=34)
REMI = dict(cam=(-4.14, -7.34, 2.07), look=(1.2, 0.0, -1.06), fov=32)
GRAM = dict(cam=(0.72, -6.8, 0.68), look=(0.26, -0.27, -0.12), fov=32)
RED = dict(cam=(-4.95, -9.49, 4.73), look=(1.7, 0.0, 0.05), fov=36)

S.estado('Superficie',
         'La página de frente: renglones paralelos y regulares, un solo sentido de lectura. Debajo hay otros textos.',
         '«recorrido lineal, fijado, “normal” de la página» · l. 615',
         etiquetas=['lectura'], orbita=False, t1=0, **FRENTE)
S.estado('Cita',
         'La cita: un texto ajeno pegado sobre la superficie, «sin que su voz se altere». García Márquez incorpora una frase de Rulfo y personajes de otros autores.',
         'Intertextualidad: la cita · l. 530-547',
         etiquetas=['receptor', 'c_rulfo', 'c_hugues', 'c_rocamadour', 'c_cruz'], t1=2.5, **CITA)
S.estado('Filigrana',
         'A contraluz, la superficie se vuelve translúcida y deja ver otro texto debajo: el romance de Lope que el de Góngora desfigura y que «hay que leer en filigrana».',
         'Jammes, cit. por Sarduy · l. 408-424',
         etiquetas=['gongora', 'lope', 'marca'], t1=3.9,
         pregunta='Para Jammes, esa dependencia la hace «menor». ¿Y para Sarduy?', **FILI)
S.estado('Reminiscencia',
         'A diferencia de la cita, la reminiscencia no aflora: se funde con el texto receptor y lo tiñe desde abajo, «modificando con sus texturas su geología».',
         'l. 533-538; ejemplos, l. 589-602',
         etiquetas=['cita_sup', 'remin', 'ejemplos'], t1=6.1, **REMI)
S.estado('Gramas',
         'Intratextualidad, «escritura entre la escritura». Gramas fonéticos: las letras del renglón admiten otra lectura. Grama sémico: bajo la línea, dos indicadores convergen hacia un idiom que no aflora.',
         'l. 604-686 · Cabrera Infante, l. 655 · Paradiso, l. 670-677',
         etiquetas=['fonetico', 'ind1', 'ind2', 'ojo', 'semico'], t1=8.5, **GRAM)
S.estado('Red en volumen',
         'Todos los estratos a la vez: una red de conexiones, de sucesivas filigranas. Sarduy lo formula en condicional: su expresión gráfica «no sería lineal… sino en volumen».',
         'l. 459-462 (condicional)',
         etiquetas=['r0', 'r1', 'r3', 'rcond'], t1=round(T_FIN, 2),
         slider={'tipo': 'tiempo', 't0': TE0, 't1': round(T_FIN, 2), 'etiqueta': 'de la página al volumen',
                 'min_txt': 'bloque', 'max_txt': 'red'}, **RED)

fijar_interpolacion()

# pósters (EEVEE): el velo translúcido se ve casi opaco con las luces de póster; sólo para el render
# de los pósters se aclara (el GLB ya se exportó con los valores del visor).
_posters_bb = S._posters


def _posters_velo(res):
    b = VELO.node_tree.nodes.get('Principled BSDF')
    b.inputs['Alpha'].default_value = 0.16
    b.inputs['Emission Strength'].default_value = 0.0
    _posters_bb(res)


S._posters = _posters_velo
S.exportar()
