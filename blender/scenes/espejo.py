"""N4 · Espejo: tres reflejos (Sarduy 1972, b] Espejo, l. 839-883; Díaz 2011, ap. 6, l. 1487-1504).

Capilla octogonal cortada (estuco marfil, 6 emblemas genéricos) con un espejo convexo en el muro del fondo.
Logos: anillo de luz perla, arriba y fuera del eje, exterior a la capilla.
  0 La sala y el espejo   vista frontal tele
  1 Reflejo reductor      el espejo devuelve la sala reducida; una zona empañada «le opone su opacidad»
  2 Reflejo significante  rayos del logos exterior a cada emblema; puntos de vista (ciudad leibniziana)
  3 Pulverización         ~150 facetas rígidas se ordenan en torno a un hueco; el anillo se vuelve pantalla
  4 Pantalla y carencia   la pantalla se retira (logos destronado); hueco con contorno bermellón; trayecto
Geometría original y genérica (el marco no copia el del Arnolfini).
"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bb
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion

random.seed(1972)
S = bb.Escena('espejo', 'Espejo: tres reflejos', dur=14)
M = bb.mat
C = 'CONSTANT'
TINY = 0.0001
ESC = 0.56          # escala global (la cámara del estado 0 debe quedar a ≤ 40 m: OrbitControls.maxDistance)


# ---------------------------------------------------------------- materiales propios (Principled, compatibles glTF)
def mat_prop(nombre, hexcol, met=0.0, rough=0.5, emi=None, emis=0.0, coat=0.0):
    m = bpy.data.materials.new(nombre)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = bb.lin(hexcol)
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    if coat and 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.2
    if emi:
        b.inputs['Emission Color'].default_value = bb.lin(emi)
        b.inputs['Emission Strength'].default_value = emis
    m.diffuse_color = bb.lin(hexcol)
    return m


ESTUCO = mat_prop('estuco', '#E2D9C8', rough=0.82)
EMB = M('significante')                  # emblemas: nácar con barniz
SOP = M('soporte')                       # grafito
MARCO = mat_prop('marco', '#2B2019', rough=0.38, coat=0.6)
FONDO = mat_prop('cartela', '#2A1E17', rough=0.9)
ESPEJO = M('espejo')                     # azogue pulido
VAHO = mat_prop('vaho', '#8E8A83', rough=1.0)
HUECO = mat_prop('hueco', '#070605', rough=1.0)
LOGOS = M('logos')
AUS = M('ausencia')
TRAY = M('trayecto')


# ---------------------------------------------------------------- helpers de geometría (locales a esta escena)
def recalc(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def tubo_bm(bm, pts, r, r1=None, segs=10, cerrado=False, tapas=True):
    """Barrido de un círculo a lo largo de pts (transporte paralelo)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    T = []
    for i in range(n):
        if cerrado:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else:
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        T.append((b - a).normalized())
    ref = Vector((0, 1, 0)) if abs(T[0].y) < 0.9 else Vector((1, 0, 0))
    N = (ref - T[0] * ref.dot(T[0])).normalized()
    rings = []
    for i in range(n):
        N = (N - T[i] * N.dot(T[i])).normalized()
        B = T[i].cross(N)
        rr = r if r1 is None else r + (r1 - r) * i / (n - 1)
        rings.append([bm.verts.new(pts[i] + (N * math.cos(2 * math.pi * k / segs) + B * math.sin(2 * math.pi * k / segs)) * rr)
                      for k in range(segs)])
    m = n if cerrado else n - 1
    for i in range(m):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    if tapas and not cerrado:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])


def esfera_bm(bm, c, r, u=16, v=10):
    g = bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    bmesh.ops.translate(bm, vec=Vector(c), verts=g['verts'])


def caja_bm(bm, c, size, bisel=0.0, segs=2):
    g = bmesh.ops.create_cube(bm, size=1.0)
    vs = g['verts']
    for vv in vs:
        vv.co = Vector((vv.co.x * size[0] + c[0], vv.co.y * size[1] + c[1], vv.co.z * size[2] + c[2]))
    if bisel > 0:
        edges = list({e for vv in vs for e in vv.link_edges})
        bmesh.ops.bevel(bm, geom=edges, offset=bisel, segments=segs, affect='EDGES', profile=0.5)


def cilindro_bm(bm, a, b, r, segs=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    Mx = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Mx, verts=g['verts'])


def objeto(nombre, bm, material, parent=None, loc=(0, 0, 0), liso=True):
    recalc(bm)
    ob = bb._obj_from_bm(nombre, bm, material, parent, loc)
    if not liso:
        for p in ob.data.polygons:
            p.use_smooth = False
    return ob


def fijar_mundo(ob):
    mw = ob.matrix_world.copy()
    ob.parent = None
    ob.matrix_world = mw


def unir(obs, nombre):
    bpy.context.view_layer.update()
    for o in obs:
        fijar_mundo(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = nombre
    return ob


def euler_de(mat3, compat=None):
    e = mat3.to_euler('XYZ')
    if compat is not None:
        e.make_compatible(compat)
    return e


# ---------------------------------------------------------------- emblemas genéricos (plano XZ local, sobresalen hacia -Y)
def emblema(tipo, nombre, parent, k=1.0):
    bm = bmesh.new()
    liso = True
    lo = k < 0.5                      # miniatura: menos resolución
    sg = 6 if lo else 10
    su, sv = (8, 6) if lo else (16, 10)
    if tipo == 'voluta':
        pts, N, vueltas = [], (56 if lo else 110), 2.25
        for i in range(N + 1):
            th = math.pi * 0.5 + i / N * vueltas * 2 * math.pi
            r = 0.045 + 0.255 * i / N
            pts.append((r * math.cos(th) * k, -0.035 * k, r * math.sin(th) * k))
        tubo_bm(bm, pts, 0.012 * k, r1=0.034 * k, segs=sg)
        esfera_bm(bm, (0, -0.035 * k, 0), 0.05 * k, su, sv)
    elif tipo == 'elipse':
        for rx, rz, rt in ((0.32, 0.22, 0.026), (0.19, 0.115, 0.014)):
            nn = 40 if lo else 80
            pts = [(rx * math.cos(2 * math.pi * i / nn) * k, -0.03 * k, rz * math.sin(2 * math.pi * i / nn) * k) for i in range(nn)]
            tubo_bm(bm, pts, rt * k, segs=sg, cerrado=True)
    elif tipo == 'abierto':
        a0, a1, R = math.radians(35), math.radians(325), 0.24
        pts = [(R * math.cos(a0 + (a1 - a0) * i / 70) * k, -0.03 * k, R * math.sin(a0 + (a1 - a0) * i / 70) * k) for i in range(71)]
        tubo_bm(bm, pts[::2] if lo else pts, 0.026 * k, segs=sg)
        for a in (a0, a1):
            esfera_bm(bm, (R * math.cos(a) * k, -0.03 * k, R * math.sin(a) * k), 0.043 * k, su, sv)
    elif tipo == 'monada':
        esfera_bm(bm, (0, -0.02 * k, 0), 0.13 * k, *((12, 8) if lo else (24, 14)))
        pts = [(0.27 * math.cos(2 * math.pi * i / 72) * k, -0.02 * k, 0.27 * math.sin(2 * math.pi * i / 72) * k) for i in range(72)]
        tubo_bm(bm, pts[::2] if lo else pts, 0.015 * k, segs=sg, cerrado=True)
    elif tipo == 'tabla':
        for j, w in enumerate((0.56, 0.42, 0.28, 0.14)):
            caja_bm(bm, (0, -0.035 * k, (-0.18 + 0.12 * j) * k), (w * k, 0.07 * k, 0.11 * k), bisel=0.008 * k, segs=1 if lo else 2)
        liso = False
    elif tipo == 'nucleo':
        ico = bmesh.new()
        bmesh.ops.create_icosphere(ico, subdivisions=1, radius=0.23)
        cy = -0.25
        for e in ico.edges:
            a = e.verts[0].co * k + Vector((0, cy * k, 0))
            b = e.verts[1].co * k + Vector((0, cy * k, 0))
            cilindro_bm(bm, a, b, (0.016 if lo else 0.011) * k, segs=5 if lo else 8)
        for vv in ico.verts:
            esfera_bm(bm, vv.co * k + Vector((0, cy * k, 0)), 0.02 * k, *((6, 4) if lo else (10, 6)))
        ico.free()
        esfera_bm(bm, (0, cy * k, 0), 0.075 * k, su, sv)
        cilindro_bm(bm, (0, 0, 0), (0, (cy + 0.06) * k, 0), 0.012 * k)
    return objeto(nombre, bm, EMB, parent, liso=liso)


# ---------------------------------------------------------------- capilla octogonal cortada
A = 2.8                    # apotema interior
H = 3.6                    # alto de muro
T = 0.25                   # espesor
SLADO = 2 * A * math.tan(math.radians(22.5))
MUROS = {'fondo': 90, 'diag_d': 45, 'der': 0, 'diag_i': 135, 'izq': 180}   # se quitan 225, 270, 315 (el corte)

estuco, soporte, fondos, filetes = [], [], [], []
grupos = {}
for nom, alfa in MUROS.items():
    a = math.radians(alfa)
    g = bb.grupo('muro_' + nom, (A * math.cos(a), A * math.sin(a), 0))
    g.rotation_euler = (0, 0, a - math.pi / 2)
    grupos[nom] = g
    L = SLADO + 2 * T * math.tan(math.radians(22.5))
    estuco.append(bb.caja(nom + '_muro', (L, T, H), (0, T / 2, H / 2), ESTUCO, g))
    estuco.append(bb.caja(nom + '_cornisa1', (L, 0.12, 0.12), (0, -0.04, H - 0.06), ESTUCO, g, bevel=0.012))
    estuco.append(bb.caja(nom + '_cornisa2', (L, 0.07, 0.07), (0, -0.02, H - 0.2), ESTUCO, g, bevel=0.01))
    soporte.append(bb.caja(nom + '_zocalo', (L, 0.06, 0.38), (0, -0.02, 0.19), SOP, g, bevel=0.01))

# pilastras en las esquinas (incluidas las dos del corte)
for beta in (22.5, 67.5, 112.5, 157.5, 202.5, 337.5):
    b = math.radians(beta)
    rc = A / math.cos(math.radians(22.5)) - 0.02
    p = bb.caja('pilastra_%d' % int(beta), (0.26, 0.1, H - 0.02), (rc * math.cos(b), rc * math.sin(b), H / 2 - 0.01), ESTUCO, None, bevel=0.015)
    p.rotation_euler = (0, 0, b - math.pi / 2)
    estuco.append(p)

# suelo: losa octogonal de grafito (radio circunscrito ≈ 3,5 m)
bm = bmesh.new()
g8 = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=(A + T + 0.2) / math.cos(math.radians(22.5)),
                           radius2=(A + T + 0.2) / math.cos(math.radians(22.5)), depth=0.24)
bmesh.ops.rotate(bm, verts=g8['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(22.5), 3, 'Z'))
bmesh.ops.translate(bm, vec=(0, 0, -0.12), verts=g8['verts'])
soporte.append(objeto('suelo', bm, SOP, liso=False))

# cartelas oscuras con filete de nácar + emblemas
EMBLEMAS = [  # (muro, tipo, x local, z)
    ('diag_i', 'voluta', 0.0, 2.38), ('diag_i', 'tabla', 0.0, 1.18),
    ('diag_d', 'elipse', 0.0, 2.38), ('diag_d', 'nucleo', 0.0, 1.18),
    ('izq', 'monada', 0.0, 1.85), ('der', 'abierto', 0.0, 1.85),
]
emb_obs, emb_centros = {}, {}
for muro, tipo, x, z in EMBLEMAS:
    g = grupos[muro]
    W, Hh = 0.84, 0.84
    fondos.append(bb.caja('cartela_' + tipo, (W, 0.03, Hh), (x, -0.012, z), FONDO, g))
    bmf = bmesh.new()
    for (cx, cz, sx, sz) in ((x, z + Hh / 2, W + 0.08, 0.05), (x, z - Hh / 2, W + 0.08, 0.05),
                             (x - W / 2, z, 0.05, Hh + 0.08), (x + W / 2, z, 0.05, Hh + 0.08)):
        caja_bm(bmf, (cx, -0.03, cz), (sx, 0.05, sz), bisel=0.008, segs=1)
    filetes.append(objeto('filete_' + tipo, bmf, EMB, g, liso=False))
    e = bb.grupo('emb_' + tipo, (x, -0.03, z), g)
    emblema(tipo, 'emblema_' + tipo, e)
    emb_obs[tipo] = e

capilla_estuco = unir(estuco, 'capilla_estuco')
capilla_soporte = unir(soporte, 'capilla_soporte')
capilla_cartelas = unir(fondos, 'capilla_cartelas')
capilla_filetes = unir(filetes, 'capilla_filetes')
bpy.context.view_layer.update()
for tipo, e in emb_obs.items():
    emb_centros[tipo] = e.matrix_world @ Vector((0, -0.12, 0))

# ---------------------------------------------------------------- espejo convexo
RS, RCAP = 1.8, 0.6
SAG = RS - math.sqrt(RS * RS - RCAP * RCAP)
YB = A - 0.05              # plano del borde del casquete
ZC = 1.85
CEN = Vector((0, YB - SAG + RS, ZC))      # centro de la esfera del casquete


def cap(u, v, off=0.0):
    p = Vector((u, CEN.y - math.sqrt(RS * RS - u * u - v * v), ZC + v))
    n = (p - CEN).normalized()
    return p + n * off, n


# marco genérico (moldura torneada, sin medallones) + filete de nácar
def torno_bm(bm, perfil, segs=112):
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / segs), -dy, r * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
             for r, dy in perfil]
    for i in range(len(rings) - 1):
        for k in range(segs):
            bm.faces.new((rings[i + 1][k], rings[i + 1][(k + 1) % segs], rings[i][(k + 1) % segs], rings[i][k]))


bm = bmesh.new()
torno_bm(bm, [(0.585, 0.0), (0.585, 0.085), (0.60, 0.115), (0.64, 0.14), (0.69, 0.15), (0.73, 0.135),
              (0.75, 0.105), (0.77, 0.09), (0.80, 0.095), (0.83, 0.075), (0.845, 0.04), (0.85, 0.0)])
marco = bb._obj_from_bm('marco', bm, MARCO, None, (0, A, ZC))
bm = bmesh.new()
tubo_bm(bm, [(0.612 * math.cos(2 * math.pi * i / 120), -0.118, 0.612 * math.sin(2 * math.pi * i / 120)) for i in range(120)],
        0.011, segs=8, cerrado=True)
filete_marco = objeto('marco_filete', bm, EMB, None, (0, A, ZC))

# fondo oscuro detrás del casquete: será el hueco
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=0.6)
bmesh.ops.rotate(bm, verts=bm.verts[:], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
hueco = objeto('hueco', bm, HUECO, None, (0, A - 0.012, ZC), liso=False)

# ---- fractura del casquete: Voronoi por semicírculos, semilla fija
semillas, intentos = [], 0
DMIN = 0.071
while len(semillas) < 150 and intentos < 40000:
    intentos += 1
    rr = RCAP * 1.02 * math.sqrt(random.random())
    aa = random.random() * 2 * math.pi
    p = Vector((rr * math.cos(aa), rr * math.sin(aa)))
    if all((p - q).length >= DMIN for q in semillas):
        semillas.append(p)
disco = [Vector((RCAP * math.cos(2 * math.pi * i / 64), RCAP * math.sin(2 * math.pi * i / 64))) for i in range(64)]


def recortar(poly, a, b):
    """Conserva los puntos p con |p-a| <= |p-b|."""
    d = b - a
    c = (b.length_squared - a.length_squared) / 2
    f = lambda p: p.dot(d) - c
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        fp, fq = f(p), f(q)
        if fp <= 0:
            out.append(p)
        if (fp <= 0) != (fq <= 0):
            t = fp / (fp - fq)
            out.append(p.lerp(q, t))
    return out


def centroide(poly):
    A2, cx, cy = 0.0, 0.0, 0.0
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        cr = p.x * q.y - q.x * p.y
        A2 += cr
        cx += (p.x + q.x) * cr
        cy += (p.y + q.y) * cr
    if abs(A2) < 1e-9:
        return sum(poly, Vector((0, 0))) / len(poly)
    return Vector((cx / (3 * A2), cy / (3 * A2)))


celdas = []
for i, s in enumerate(semillas):
    poly = disco[:]
    for j, o in enumerate(semillas):
        if i != j and (o - s).length < 0.45:
            poly = recortar(poly, s, o)
            if len(poly) < 3:
                break
    if len(poly) >= 3:
        celdas.append(poly)

GROSOR = 0.012
facetas = []
for i, poly in enumerate(celdas):
    c2 = centroide(poly)
    P0, n0 = cap(c2.x, c2.y)
    bm = bmesh.new()
    vc = bm.verts.new(Vector((0, 0, 0)))
    vcb = bm.verts.new(-n0 * GROSOR)
    vf, vb = [], []
    for p in poly:
        pf, nf = cap(p.x, p.y)
        vf.append(bm.verts.new(pf - P0))
        vb.append(bm.verts.new(pf - nf * GROSOR - P0))
    n = len(poly)
    tipos, lat = [], {}
    for k in range(n):
        bm.faces.new((vc, vf[k], vf[(k + 1) % n])); tipos.append('f')
    for k in range(n):
        bm.faces.new((vcb, vb[(k + 1) % n], vb[k])); tipos.append('b')
    for k in range(n):
        f = bm.faces.new((vf[(k + 1) % n], vf[k], vb[k], vb[(k + 1) % n]))
        mid = (vf[k].co + vf[(k + 1) % n].co) / 2
        nl = mid - n0 * mid.dot(n0)
        lat[len(tipos)] = nl.normalized() if nl.length > 1e-6 else n0
        tipos.append('l')
    ob = bb._obj_from_bm('faceta_%03d' % i, bm, ESPEJO, None, P0)
    me = ob.data
    normales = []
    for poly_m in me.polygons:
        tp = tipos[poly_m.index]
        for li in poly_m.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co + P0
            rad = (co - CEN).normalized()
            normales.append(rad if tp == 'f' else (-rad if tp == 'b' else lat[poly_m.index]))
    me.normals_split_custom_set(normales)
    facetas.append((ob, c2, P0, n0))
print('[espejo] facetas:', len(facetas))
bm = bmesh.new()
NRc, NSc = 14, 96
PCc, _ = cap(0, 0, 0.0012)
vcen = bm.verts.new(Vector((0, 0, 0)))
filas_c = []
for ir in range(1, NRc + 1):
    rr = RCAP * ir / NRc
    filas_c.append([bm.verts.new(cap(rr * math.cos(2 * math.pi * js / NSc), rr * math.sin(2 * math.pi * js / NSc), 0.0012)[0] - PCc)
                    for js in range(NSc)])
for js in range(NSc):
    bm.faces.new((vcen, filas_c[0][js], filas_c[0][(js + 1) % NSc]))
for ir in range(NRc - 1):
    for js in range(NSc):
        bm.faces.new((filas_c[ir][js], filas_c[ir + 1][js], filas_c[ir + 1][(js + 1) % NSc], filas_c[ir][(js + 1) % NSc]))
espejo_entero = objeto('espejo_entero', bm, ESPEJO, None, PCc)
me = espejo_entero.data
me.normals_split_custom_set([(me.vertices[me.loops[li].vertex_index].co + PCc - CEN).normalized()
                             for pm in me.polygons for li in pm.loop_indices])

# ---- zona opaca (empañada): mancha irregular hacia arriba-izquierda, del lado del logos
VC2 = Vector((-0.2, 0.24))


def radio_vaho(phi):
    return 0.27 * (1 + 0.16 * math.sin(3 * phi + 0.7) + 0.09 * math.sin(5 * phi + 2.1) + 0.05 * math.sin(9 * phi + 0.3))


def en_vaho(u, v):
    d = Vector((u, v)) - VC2
    return d.length <= radio_vaho(math.atan2(d.y, d.x))


PV, _ = cap(VC2.x, VC2.y, 0.007)
bm = bmesh.new()
NR, NS = 9, 72
centro_v = bm.verts.new(Vector((0, 0, 0)))
anillos = []
for ir in range(1, NR + 1):
    fila = []
    for js in range(NS):
        phi = 2 * math.pi * js / NS
        rr = radio_vaho(phi) * ir / NR
        u, v = VC2.x + rr * math.cos(phi), VC2.y + rr * math.sin(phi)
        m = math.hypot(u, v)
        if m > 0.575:
            u, v = u * 0.575 / m, v * 0.575 / m
        pp, _ = cap(u, v, 0.007)
        fila.append(bm.verts.new(pp - PV))
    anillos.append(fila)
for js in range(NS):
    bm.faces.new((centro_v, anillos[0][js], anillos[0][(js + 1) % NS]))
for ir in range(NR - 1):
    for js in range(NS):
        bm.faces.new((anillos[ir][js], anillos[ir + 1][js], anillos[ir + 1][(js + 1) % NS], anillos[ir][(js + 1) % NS]))
rnd_v = random.Random(850)
for _ in range(95):
    phi = rnd_v.random() * 2 * math.pi
    f = 1.0 + 0.42 * rnd_v.random() ** 1.6
    rr = radio_vaho(phi) * f
    u, v = VC2.x + rr * math.cos(phi), VC2.y + rr * math.sin(phi)
    if math.hypot(u, v) > 0.57:
        continue
    rg = 0.011 * (1.45 - f) + 0.003 * rnd_v.random()
    pc, nc = cap(u, v, 0.007)
    t1 = nc.cross(Vector((0, 0, 1))).normalized()
    t2 = nc.cross(t1)
    c0 = bm.verts.new(pc - PV)
    anillo_g = [bm.verts.new(pc - PV + (t1 * math.cos(2 * math.pi * q / 8) + t2 * math.sin(2 * math.pi * q / 8)) * rg) for q in range(8)]
    for q in range(8):
        bm.faces.new((c0, anillo_g[q], anillo_g[(q + 1) % 8]))
vaho = objeto('vaho_opacidad', bm, VAHO, None, PV)

# ---- la sala reducida: miniaturas de los emblemas sobre el casquete (el emblema tapado por el vaho no aparece)
MINIS = {'monada': 180, 'tabla': 222, 'elipse': 40, 'nucleo': 318, 'abierto': 0, 'voluta': 140}
minis = []
for tipo, ang in MINIS.items():
    u, v = 0.37 * math.cos(math.radians(ang)), 0.37 * math.sin(math.radians(ang))
    if en_vaho(u, v):
        continue
    p, nrm = cap(u, v, 0.002)
    e = bb.grupo('mini_' + tipo, p)
    e.rotation_mode = 'XYZ'
    e.rotation_euler = Vector((0, -1, 0)).rotation_difference(nrm).to_euler('XYZ')
    emblema(tipo, 'mini_emblema_' + tipo, e, k=0.2)
    minis.append(e)
# octógono reducido (la cornisa de la sala) que se interrumpe bajo el vaho
seg_oct = []
for kk in range(8):
    a0 = math.radians(22.5 + 45 * kk)
    a1 = math.radians(22.5 + 45 * (kk + 1))
    pa = Vector((0.5 * math.cos(a0), 0.5 * math.sin(a0)))
    pb = Vector((0.5 * math.cos(a1), 0.5 * math.sin(a1)))
    trozo = []
    for jj in range(13):
        q = pa.lerp(pb, jj / 12)
        if en_vaho(q.x, q.y):
            if len(trozo) > 1:
                seg_oct.append(trozo)
            trozo = []
        else:
            trozo.append(q)
    if len(trozo) > 1:
        seg_oct.append(trozo)
PO, _ = cap(0, 0)
bm = bmesh.new()
for trozo in seg_oct:
    pts = [cap(q.x, q.y, 0.004)[0] - PO for q in trozo]
    tubo_bm(bm, pts, 0.0045, segs=6)
oct_mini = objeto('mini_octogono', bm, EMB, None, PO)
minis.append(oct_mini)

# ---------------------------------------------------------------- logos: anillo de luz perla, arriba y fuera del eje
RL = 1.6
NSEG = 8
TAU = math.radians(24)
PSI = math.radians(-14)
RC = Vector((-1.75, 1.25, 4.72))
Rz = Matrix.Rotation(PSI, 3, 'Z')
E1 = Rz @ Vector((1, 0, 0))
E2 = Rz @ Vector((0, math.cos(TAU), math.sin(TAU)))
NRM = E1.cross(E2)


def lamina_bm(R, ang, w, t, n=16):
    bm = bmesh.new()
    a = math.radians(ang) / 2
    filas = []
    for i in range(n + 1):
        al = -a + 2 * a * i / n
        filas.append([bm.verts.new(((R + dr) * math.sin(al), (R + dr) * math.cos(al) - R, dz))
                      for dr, dz in ((-w / 2, -t / 2), (w / 2, -t / 2), (w / 2, t / 2), (-w / 2, t / 2))])
    for i in range(n):
        for k in range(4):
            bm.faces.new((filas[i][k], filas[i][(k + 1) % 4], filas[i + 1][(k + 1) % 4], filas[i + 1][k]))
    bm.faces.new(filas[0])
    bm.faces.new(list(reversed(filas[-1])))
    return bm


laminas = []
for k in range(NSEG):
    phi = 2 * math.pi * k / NSEG + math.radians(8)
    Tg = -math.sin(phi) * E1 + math.cos(phi) * E2
    U = math.cos(phi) * E1 + math.sin(phi) * E2
    R3 = Matrix((Tg, U, -NRM)).transposed()
    pos = RC + RL * U
    ob = objeto('logos_%02d' % k, lamina_bm(RL, 360 / NSEG - 2.4, 0.2, 0.045, n=24), LOGOS, None, pos, liso=False)
    rot0 = euler_de(R3)
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = rot0
    laminas.append({'ob': ob, 'pos0': pos.copy(), 'rot0': rot0})

# ---------------------------------------------------------------- rayos del logos (consonancia) — estado 2
rayos = []
destinos = [emb_centros[t] for t in ('voluta', 'tabla', 'elipse', 'nucleo', 'monada', 'abierto')] + [Vector((0, YB - SAG - 0.02, ZC + 0.62))]
for i, dst in enumerate(destinos):
    d = dst - RC
    L = d.length - 0.1
    bm = bmesh.new()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.009, radius2=0.005, depth=L)
    bmesh.ops.translate(bm, vec=(0, 0, L / 2), verts=g['verts'])
    ob = objeto('rayo_%d' % i, bm, LOGOS, None, RC)
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler('XYZ')
    rayos.append(ob)

# ---------------------------------------------------------------- puntos de vista (la ciudad leibniziana) — estado 2
PV0 = Vector((0, YB, 1.45))
puntos = bb.grupo('puntos_de_vista', PV0)
RPV = 3.55
arco_pts = [(RPV * math.cos(math.radians(a)), RPV * math.sin(math.radians(a)), 0) for a in [224 + 92 * i / 60 for i in range(61)]]
bb.polilinea_punteada('puntos_arco', arco_pts, guion=0.07, hueco=0.08, r=0.012, material=TRAY, parent=puntos)
bm = bmesh.new()
for i in range(9):
    a = math.radians(230 + 80 * i / 8)
    p = Vector((RPV * math.cos(a), RPV * math.sin(a), 0))
    esfera_bm(bm, p, 0.06, 12, 8)
    dirm = (Vector((0, 0, 0.4)) - p).normalized()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.045, radius2=0.0, depth=0.16)
    q = Vector((0, 0, 1)).rotation_difference(dirm)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(p + dirm * 0.14) @ q.to_matrix().to_4x4(), verts=g['verts'])
objeto('puntos_ojos', bm, TRAY, puntos)

# ---------------------------------------------------------------- neobarroco: contorno del hueco y trayecto
HC = Vector((0, A - 0.1, ZC))
contorno = bb.grupo('contorno_hueco', HC)
circ = [(0.56 * math.cos(2 * math.pi * i / 96), 0, 0.56 * math.sin(2 * math.pi * i / 96)) for i in range(97)]
bb.polilinea_punteada('contorno_guiones', circ, guion=0.085, hueco=0.055, r=0.017, material=AUS, parent=contorno)

TC = Vector((0, A - 0.33, ZC))
trayecto = bb.grupo('trayecto', TC)
tr_pts = bb.arco(0, 0, 0.9, 0.84, 118, 118 - 292, n=120, z=0.0, plano='XZ')
bb.polilinea_punteada('trayecto_guiones', tr_pts, guion=0.1, hueco=0.07, r=0.016, material=TRAY, parent=trayecto,
                      flecha={'r': 0.05, 'largo': 0.14})

# ---------------------------------------------------------------- etiquetas
S.etiqueta('reductor', 'reflejo reductor', (0, YB - 0.3, ZC + 1.12), clase='serif')
S.etiqueta('opaco', 'opacidad', (-1.25, YB - 0.2, ZC + 0.5), clase='serif')
S.etiqueta('sala', 'la sala, reducida', (-1.42, YB - 0.2, ZC - 0.42), clase='')
S.etiqueta('vaneyck', 'Van Eyck, 1434 (aún no barroco) · Góngora: «aunque cóncavo fiel»', (-0.3, YB - 0.2, ZC - 1.03), clase='nota')
S.etiqueta('logos', 'logos exterior', (RC.x - 1.35, RC.y - 0.4, RC.z + 0.55), clase='serif')
S.etiqueta('dios', 'el dios jesuita · el rey', (RC.x + RL + 1.05, RC.y - 0.3, RC.z + 0.15), clase='nota')
S.etiqueta('puntos', 'infinitud de puntos de vista', (0.0, YB - RPV - 0.1, 0.95), clase='trayecto')
S.etiqueta('pantalla', 'el logos: una pantalla', (0, A - 0.45, ZC + 1.05), clase='serif')
S.etiqueta('pulverizado', 'reflejo pulverizado', (-1.95, A - 1.0, ZC + 1.72), clase='serif')
S.etiqueta('carencia', 'carencia', (0, A - 0.2, ZC), clase='grande')
S.etiqueta('trayecto', 'trayecto dividido por la ausencia', (-0.35, A - 0.45, ZC - 1.12), clase='trayecto')
S.etiqueta('destronado', 'logos destronado', (-1.55, 1.05, 0.35), clase='nota')

# ---------------------------------------------------------------- línea de tiempo
# estado 1 (0 → 2,0 s): el vaho se extiende
S.mostrar(vaho, 0.4, 1.8)
# estado 2 (2,0 → 3,8 s): rayos del logos y puntos de vista
for i, r in enumerate(rayos):
    S.clave(r, 0, esc=(1, 1, TINY), interp=C)
    S.clave(r, 2.2 + 0.08 * i, esc=(1, 1, TINY))
    S.clave(r, 3.1 + 0.08 * i, esc=(1, 1, 1))
    S.clave(r, 4.0, esc=(1, 1, 1))
    S.clave(r, 4.5, esc=(1, 1, TINY))
S.mostrar(puntos, 2.4, 3.4)
S.ocultar(puntos, 4.0, 4.5)
# estado 3 (3,8 → 10 s): pulverización
S.clave(espejo_entero, 0, esc=1.0, interp=C)
S.salto(espejo_entero, 4.7, 1.0, TINY)   # relevo exacto por las facetas (sin juntas visibles antes)
S.ocultar(vaho, 4.2, 4.7)
for mn in minis:
    S.clave(mn, 0, esc=1.0)
    S.ocultar(mn, 4.2, 4.7)
for (ob, c2, P0, n0) in facetas:
    rho = c2.length / RCAP
    th = math.atan2(c2.y, c2.x)
    rho2 = 1.05 + 0.74 * min(rho, 1.0) ** 0.9 + random.uniform(-0.06, 0.06)
    th2 = th + 0.32 + random.uniform(-0.1, 0.1)
    x = rho2 * math.cos(th2)
    z = ZC + 0.86 * rho2 * math.sin(th2)
    y = YB - (0.36 + 0.9 * random.random())
    y = min(y, A * math.sqrt(2) - 0.3 - abs(x))
    dest = Vector((x, y, z))
    radial = Vector((math.cos(th2), 0, 0.86 * math.sin(th2))).normalized()
    nt = (Vector((0, -1, 0.3)) + radial * 0.38 + Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * 0.34).normalized()
    q = n0.rotation_difference(nt) @ Quaternion(n0, random.uniform(-1.0, 1.0))
    rot1 = q.to_euler('XYZ')
    ts = 4.7 + 1.5 * random.random()
    du = 1.9 + 0.6 * random.random()
    S.clave(ob, 0, loc=P0, rot=(0, 0, 0), esc=TINY, interp=C)   # oculta: el casquete entero la representa
    S.salto(ob, 4.7, TINY, 1.0)
    S.clave(ob, ts, loc=P0, rot=(0, 0, 0))
    mid = P0.lerp(dest, 0.2) + n0 * 0.28
    S.clave(ob, ts + 0.32 * du, loc=mid, rot=Euler((rot1.x * 0.3, rot1.y * 0.3, rot1.z * 0.3)))
    S.clave(ob, ts + du, loc=dest, rot=rot1)
# emblemas desfasados (la armonía se rompe)
for (tipo, e), ang in zip(emb_obs.items(), (17, -26, 31, -12, 22, -34)):
    S.clave(e, 0, rot=(0, 0, 0))
    S.clave(e, 5.0, rot=(0, 0, 0))
    S.clave(e, 7.2, rot=(0, math.radians(ang), 0))
# el anillo del logos no cae: sus segmentos se reordenan como pantalla delante del hueco
ROT_PANT = Euler((math.pi / 2, 0, 0))
orden = sorted(range(NSEG), key=lambda k: -laminas[k]['pos0'].z)
YP = A - 0.24
for fila, k in enumerate(orden):
    lm = laminas[k]
    lm['pos1'] = Vector((0.0, YP, ZC + 0.03 + (3.5 - fila) * 0.205))
    r1 = ROT_PANT.copy()
    r1.make_compatible(lm['rot0'])
    lm['rot1'] = r1
    lm['orden'] = fila
for k, lm in enumerate(laminas):
    ob = lm['ob']
    ts = 5.9 + 0.14 * lm['orden']
    S.clave(ob, 0, loc=lm['pos0'], rot=lm['rot0'])
    S.clave(ob, ts, loc=lm['pos0'], rot=lm['rot0'])
    S.clave(ob, ts + 2.3, loc=lm['pos1'], rot=lm['rot1'])
# estado 4 (10 → 13,6 s): la pantalla se retira y se deposita (destronada); aparece el hueco
# destronado: la pantalla se retira hacia delante y queda tendida en el suelo (los arcos, anidados, boca abajo)
PSI_S = math.radians(-9)
BASE_S = Vector((-0.45, 1.9, 0.03))
ROT_S = Matrix.Rotation(PSI_S, 3, 'Z') @ Matrix.Rotation(math.pi, 3, 'X')
for k, lm in enumerate(laminas):
    ob = lm['ob']
    o = lm['orden']
    t0 = 10.2 + 0.05 * o
    S.clave(ob, t0, loc=lm['pos1'], rot=lm['rot1'])
    adel = lm['pos1'] + Vector((0, -0.95, -0.05))
    S.clave(ob, t0 + 0.8, loc=adel, rot=lm['rot1'])
    suelo = BASE_S + Matrix.Rotation(PSI_S, 3, 'Z') @ Vector((0.0, -o * 0.215, 0.0))
    r2 = ROT_S.to_euler('XYZ')
    r2.make_compatible(lm['rot1'])
    tl = 11.0 + 0.08 * (7 - o)
    S.clave(ob, tl, loc=adel, rot=lm['rot1'])
    S.clave(ob, tl + 1.1, loc=suelo, rot=r2)
S.mostrar(contorno, 11.4, 12.2)
S.clave(trayecto, 0, esc=TINY, rot=(0, -1.9, 0), interp=C)
S.clave(trayecto, 12.2, esc=TINY, rot=(0, -1.9, 0))
S.clave(trayecto, 13.4, esc=1.0, rot=(0, 0, 0))

# ---------------------------------------------------------------- estados
def vista(cam, look, fov):
    return dict(cam=tuple(c * ESC for c in cam), look=tuple(c * ESC for c in look), fov=fov)


D0 = 39.0 / ESC            # distancia del tele (≤ 40 m reales)
FRENTE = vista((0.0, -D0 * math.cos(math.radians(4.5)), 2.55 + D0 * math.sin(math.radians(4.5))), (0.0, 0, 2.55), 7.0)
CERCA = vista((1.05, A - 5.0, 2.12), (0.62, A, 1.70), 34)
VISTA = vista((5.6, -7.4, 5.6), (0.35, 1.3, 2.95), 42)
NEO = vista((2.8, -5.6, 2.5), (1.35, 2.1, 1.95), 40)
NEO2 = vista((2.4, -5.9, 4.3), (1.25, 2.0, 1.6), 40)

# todo lo construido cuelga de una raíz escalada (las cámaras de los estados se crean después, ya en metros reales)
raiz = bb.grupo('raiz')
for ob in list(bpy.data.objects):
    if ob.parent is None and ob is not raiz and ob.type != 'LIGHT':
        ob.parent = raiz
raiz.scale = (ESC, ESC, ESC)

S.estado('La sala y el espejo',
         'Una capilla barroca abstracta. En su muro, un espejo convexo devuelve la sala reducida: '
         'la estructura barroca es «reflejo reductor» de lo que la envuelve.',
         'Sarduy 1972 · b] Espejo (l. 839-846)', etiquetas=['reductor'], orbita=False, t1=0, **FRENTE)
S.estado('Reflejo reductor',
         'Rasgo de todo barroco: el espejo quiere ser totalizante y minucioso, pero no capta la vastedad '
         'que lo circunscribe; algo «le opone su opacidad».',
         'l. 841-852', etiquetas=['sala', 'opaco', 'vaneyck'], t1=2.0, **CERCA)
S.estado('Reflejo significante',
         'Barroco histórico: universo descentrado «pero aún armónico», en consonancia con un logos exterior. '
         'Ninguna vista agota la ciudad; la estructura la contiene en potencia.',
         'l. 851-867 · la ciudad leibniziana (l. 861-865)', etiquetas=['logos', 'dios', 'puntos'], t1=3.8,
         slider={'tipo': 'azimut', 'min': -65, 'max': 10, 'etiqueta': 'puntos de vista (la ciudad leibniziana)',
                 'min_txt': 'izquierda', 'max_txt': 'derecha'}, **VISTA)
S.estado('Pulverización',
         'Neobarroco: el reflejo se pulveriza en torno a un hueco. El logos ya no organiza desde fuera: '
         'sus segmentos forman «una pantalla que esconde la carencia».',
         'l. 868-876', etiquetas=['pantalla', 'pulverizado'], t1=10.0,
         pregunta='Si el espejo se rompe, ¿qué refleja cada fragmento? ¿Queda un centro?',
         slider={'tipo': 'tiempo', 't0': 3.8, 't1': 10.0, 'etiqueta': 'del reflejo armónico al pulverizado',
                 'min_txt': 'barroco', 'max_txt': 'neobarroco'}, **NEO)
S.estado('Pantalla y carencia',
         'Retirada la pantalla, aparece la carencia: el trayecto gira en torno a esa ausencia. '
         '«Reflejo necesariamente pulverizado»; «arte del destronamiento y la discusión».',
         'l. 876-883 · Díaz 2011, ap. 6: esbozos de la futura retombée (l. 1487-1504)',
         etiquetas=['carencia', 'trayecto', 'destronado', 'pulverizado'], t1=13.6, **NEO2)

S.exportar()


# ---------------------------------------------------------------- compactar la animación del GLB
# El exportador muestrea cada canal a 30 fps en toda la línea de tiempo (421 muestras × ~360 canales).
# Aquí se quitan las muestras redundantes (tramos quietos y tramos que se interpolan bien en línea recta).
def compactar_glb(path, tol=3e-4):
    import struct, json as _json
    data = open(path, 'rb').read()
    jl = struct.unpack_from('<I', data, 12)[0]
    j = _json.loads(data[20:20 + jl])
    off = 20 + jl
    bl = struct.unpack_from('<I', data, off)[0]
    binb = data[off + 8:off + 8 + bl]
    acc, bvs = j['accessors'], j['bufferViews']
    NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

    def leer(ai):
        a = acc[ai]
        v = bvs[a['bufferView']]
        n = NC[a['type']]
        start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = v.get('byteStride', 4 * n)
        return [struct.unpack_from('<%df' % n, binb, start + i * stride) for i in range(a['count'])]

    def rdp(t, v):
        keep = {0, len(t) - 1}
        pila = [(0, len(t) - 1)]
        while pila:
            i, k = pila.pop()
            if k <= i + 1:
                continue
            peor, jmax = -1.0, -1
            for jj in range(i + 1, k):
                f = (t[jj] - t[i]) / (t[k] - t[i])
                e = max(abs(v[jj][c] - (v[i][c] + (v[k][c] - v[i][c]) * f)) for c in range(len(v[jj])))
                if e > peor:
                    peor, jmax = e, jj
            if peor > tol:
                keep.add(jmax)
                pila += [(i, jmax), (jmax, k)]
        return sorted(keep)

    new_acc, new_bv, blob = [], [], bytearray()

    def vista_bin(b, target=None, stride=None):
        while len(blob) % 4:
            blob.append(0)
        vw = {'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(b)}
        if target:
            vw['target'] = target
        if stride:
            vw['byteStride'] = stride
        blob.extend(b)
        new_bv.append(vw)
        return len(new_bv) - 1

    remap, vmap = {}, {}
    usados = []
    for m in j['meshes']:
        for pr in m['primitives']:
            usados += list(pr['attributes'].values()) + ([pr['indices']] if 'indices' in pr else [])
            for tg in pr.get('targets', []):
                usados += list(tg.values())
    for ai in sorted(set(usados)):
        a = dict(acc[ai])
        ov = a['bufferView']
        if ov not in vmap:
            v = bvs[ov]
            st = v.get('byteOffset', 0)
            vmap[ov] = vista_bin(binb[st:st + v['byteLength']], v.get('target'), v.get('byteStride'))
        a['bufferView'] = vmap[ov]
        remap[ai] = len(new_acc)
        new_acc.append(a)
    for m in j['meshes']:
        for pr in m['primitives']:
            pr['attributes'] = {k: remap[x] for k, x in pr['attributes'].items()}
            if 'indices' in pr:
                pr['indices'] = remap[pr['indices']]
            for tg in pr.get('targets', []):
                for k in list(tg):
                    tg[k] = remap[tg[k]]
    antes = despues = 0
    for an in j.get('animations', []):
        for sm in an['samplers']:
            t = [x[0] for x in leer(sm['input'])]
            v = leer(sm['output'])
            n = len(v[0])
            idx = rdp(t, v) if sm.get('interpolation', 'LINEAR') == 'LINEAR' else list(range(len(t)))
            antes += len(t)
            despues += len(idx)
            tb = struct.pack('<%df' % len(idx), *[t[i] for i in idx])
            vb = struct.pack('<%df' % (len(idx) * n), *[c for i in idx for c in v[i]])
            ia = {'bufferView': vista_bin(tb), 'componentType': 5126, 'count': len(idx), 'type': 'SCALAR',
                  'min': [min(t[i] for i in idx)], 'max': [max(t[i] for i in idx)]}
            oa = {'bufferView': vista_bin(vb), 'componentType': 5126, 'count': len(idx),
                  'type': acc[sm['output']]['type']}
            new_acc += [ia, oa]
            sm['input'], sm['output'] = len(new_acc) - 2, len(new_acc) - 1
    while len(blob) % 4:
        blob.append(0)
    j['accessors'], j['bufferViews'] = new_acc, new_bv
    j['buffers'] = [{'byteLength': len(blob)}]
    js = _json.dumps(j, separators=(',', ':')).encode('utf-8')
    while len(js) % 4:
        js += b' '
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(path, 'wb') as fh:
        fh.write(struct.pack('<4sII', b'glTF', 2, total))
        fh.write(struct.pack('<I4s', len(js), b'JSON') + js)
        fh.write(struct.pack('<I4s', len(blob), b'BIN\x00') + bytes(blob))
    print('[espejo] GLB compactado: %d → %d muestras; %d bytes' % (antes, despues, total))


compactar_glb(os.path.join(bb.OUT3D, 'escenas', 'espejo.glb'))
