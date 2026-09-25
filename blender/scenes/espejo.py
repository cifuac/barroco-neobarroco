"""N4 · Espejo: tres reflejos (Sarduy 1972, b] Espejo, l. 839-883; Díaz 2011, ap. 6, l. 1487-1504).

Lámina de museo en 3D. Capilla octogonal cortada, de estuco (pilastras, cornisa, nichos ciegos con medallones
ovalados en relieve; los emblemas, dibujados en hilo de grafito) y, en el muro del fondo, un espejo convexo con
marco dorado fino de rayos. El logos: un aro dorado delgado, arriba y fuera del eje, exterior a la capilla.
  0 La sala y el espejo   vista frontal tele
  1 Reflejo reductor      el espejo devuelve la sala reducida; una zona mate y rayada «le opone su opacidad»
  2 Reflejo significante  hilos del logos exterior a cada emblema; ojos dibujados: infinitud de puntos de vista
  3 Pulverización         el espejo se parte en ~35 esquirlas que se ordenan en remolino en torno al hueco;
                          el aro del logos baja y tiende una pantalla delante
  4 Pantalla y carencia   la pantalla se corre; el aro cae partido en el suelo; el hueco es un corte limpio con
                          filo bermellón; el trayecto gira en torno a la ausencia
Geometría original y genérica.
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
# ajustes del visor «galería clara» (docs/3d/estudio.js): estuco piedra clara con relieves más claros; el fondo de
# los nichos, un punto más hondo; el corte del hueco, en sombra; la trama de la zona opaca, en tinta diluida.
S.estudio = {
    'materiales': {
        'estuco': {'color': '#CEC4B4', 'roughness': 0.88},
        'estuco_moldura': {'color': '#E8E1D6', 'roughness': 0.72},
        'estuco_nicho': {'color': '#C4B9A8', 'roughness': 0.9},
        'estuco_campo': {'color': '#F1ECE4', 'roughness': 0.8},
        'estuco_corte': {'color': '#6F675E', 'roughness': 0.95},
        'azogue_facetas': {'color': '#F3F5F6', 'roughness': 0.2, 'envMapIntensity': 1.25},
        'soporte_zocalo': {'color': '#C3BBAE', 'roughness': 0.6, 'clearcoat': 0.2},
        'soporte_suelo': {'color': '#CDC6BA', 'roughness': 0.5, 'clearcoat': 0.3},
        'tinta_renglon': {'color': '#8E867B', 'roughness': 0.7, 'clearcoat': 0},
        'lamina_opaca': {'color': '#EFEAE1', 'roughness': 0.95},
        'lamina_pantalla': {'color': '#F2EDE4', 'roughness': 0.85},
    },
}
TINY = 0.0001
TINY3 = (TINY, TINY, TINY)
ESC = 0.56          # escala global (metros del visor = unidades de escena × ESC)


# ---------------------------------------------------------------- materiales propios (Principled, compatibles glTF)
def mat_prop(nombre, hexcol, met=0.0, rough=0.5):
    m = bpy.data.materials.new(nombre)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = bb.lin(hexcol)
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    m.diffuse_color = bb.lin(hexcol)
    return m


ESTUCO = mat_prop('estuco', '#D8CFC1', rough=0.88)
ESTUCO_M = mat_prop('estuco_moldura', '#E9E3D8', rough=0.72)
NICHO = mat_prop('estuco_nicho', '#CFC5B6', rough=0.9)
CAMPO = mat_prop('estuco_campo', '#EEE9E0', rough=0.8)
CORTE = mat_prop('estuco_corte', '#9C9285', rough=0.95)
SOP = M('soporte', 'soporte_zocalo')
SUELO = M('soporte', 'soporte_suelo')
EMB = M('significante')                         # emblemas: hilo de grafito (laca)
ORO = M('significado', 'oro_marco')             # marco del espejo
ORO_L = M('significado', 'oro_logos')           # aro e hilos del logos, iris de los ojos
ESPEJO = M('espejo')
FACETA = mat_prop('azogue_facetas', bb.TOK['azogue'], met=1.0, rough=0.12)
OPACO = mat_prop('lamina_opaca', '#EFEAE1', rough=0.95)
TRAMA = mat_prop('tinta_renglon', '#8E867B', rough=0.7)
PANT = mat_prop('lamina_pantalla', '#F2EDE4', rough=0.85)
AUS = M('ausencia')
TRAY = M('trayecto')


# ---------------------------------------------------------------- helpers de geometría
def recalc(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def tubo_bm(bm, pts, r, r1=None, segs=10, cerrado=False, tapas=True):
    """Barrido de un círculo a lo largo de pts (transporte paralelo)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    T_ = []
    for i in range(n):
        if cerrado:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else:
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        T_.append((b - a).normalized())
    ref = Vector((0, 1, 0)) if abs(T_[0].y) < 0.9 else Vector((1, 0, 0))
    N = (ref - T_[0] * ref.dot(T_[0])).normalized()
    rings = []
    for i in range(n):
        N = (N - T_[i] * N.dot(T_[i])).normalized()
        B = T_[i].cross(N)
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


def esfera_bm(bm, c, r, u=12, v=8):
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


def disco_bm(bm, c, r, eje=(0, -1, 0), t=0.012, segs=28):
    """Disco plano (cilindro corto) de radio r, con su eje a lo largo de `eje`."""
    c, e = Vector(c), Vector(eje).normalized()
    cilindro_bm(bm, c + e * t / 2, c - e * t / 2, r, segs)


def trazo_bm(bm, pts, r, cerrado=False, segs=8):
    """Polilínea de trazo fino con esquinas vivas: cilindros por tramo y una bolita en cada vértice."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    for i in range(n if cerrado else n - 1):
        cilindro_bm(bm, pts[i], pts[(i + 1) % n], r, segs)
    for p in pts:
        esfera_bm(bm, p, r, 8, 6)


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


def elipse(rx, rz, n=72, y=0.0, cx=0.0, cz=0.0):
    return [(cx + rx * math.cos(2 * math.pi * i / n), y, cz + rz * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ---------------------------------------------------------------- emblemas genéricos, dibujados en hilo (plano XZ local)
def emblema(tipo, nombre, parent, k=1.0):
    bm = bmesh.new()
    lo = k < 0.5                      # miniatura (dentro del espejo): menos resolución, trazo mínimo visible
    sg = 5 if lo else 8
    rl = max(0.0105 * k, 0.0024)
    y0 = -0.012 * k
    if tipo == 'voluta':
        pts, N, vueltas = [], (60 if lo else 120), 2.2
        for i in range(N + 1):
            th = math.pi * 0.5 + i / N * vueltas * 2 * math.pi
            r = 0.035 + 0.215 * i / N
            pts.append((r * math.cos(th) * k, y0, r * math.sin(th) * k))
        tubo_bm(bm, pts, rl * 0.6, r1=rl * 1.25, segs=sg)
        disco_bm(bm, (0, y0, 0), 0.03 * k, t=0.012 * k)
    elif tipo == 'elipse':
        for rx, rz, f in ((0.25, 0.17, 1.0), (0.145, 0.09, 0.8)):
            tubo_bm(bm, [(p[0] * k, y0, p[2] * k) for p in elipse(rx, rz, 40 if lo else 80)], rl * f, segs=sg, cerrado=True)
    elif tipo == 'abierto':
        a0, a1, R = math.radians(40), math.radians(320), 0.2
        n = 36 if lo else 72
        pts = [(R * math.cos(a0 + (a1 - a0) * i / n) * k, y0, R * math.sin(a0 + (a1 - a0) * i / n) * k) for i in range(n + 1)]
        tubo_bm(bm, pts, rl, segs=sg)
        for a in (a0, a1):
            disco_bm(bm, (R * math.cos(a) * k, y0, R * math.sin(a) * k), 0.026 * k, t=0.012 * k)
    elif tipo == 'monada':
        tubo_bm(bm, [(p[0] * k, y0, p[2] * k) for p in elipse(0.21, 0.21, 40 if lo else 80)], rl, segs=sg, cerrado=True)
        disco_bm(bm, (0, y0, 0), 0.065 * k, t=0.014 * k)
    elif tipo == 'tabla':
        esc = [(-0.23, -0.16), (0.23, -0.16), (0.23, -0.07), (0.155, -0.07), (0.155, 0.02), (0.08, 0.02), (0.08, 0.11),
               (0.0, 0.17), (-0.08, 0.11), (-0.08, 0.02), (-0.155, 0.02), (-0.155, -0.07), (-0.23, -0.07)]
        trazo_bm(bm, [(x * k, y0, z * k) for x, z in esc], rl, cerrado=True, segs=sg)
    elif tipo == 'nucleo':
        ico = bmesh.new()
        bmesh.ops.create_icosphere(ico, subdivisions=1, radius=0.17)
        cy = -0.15
        for e in ico.edges:
            a = e.verts[0].co * k + Vector((0, cy * k, 0))
            b = e.verts[1].co * k + Vector((0, cy * k, 0))
            cilindro_bm(bm, a, b, rl * 0.7, segs=5 if lo else 7)
        for vv in ico.verts:
            esfera_bm(bm, vv.co * k + Vector((0, cy * k, 0)), rl * 1.35, 8, 6)
        ico.free()
        cilindro_bm(bm, (0, 0, 0), (0, (cy + 0.1) * k, 0), rl * 0.7, segs=6)
    return objeto(nombre, bm, EMB, parent)


# ---------------------------------------------------------------- capilla octogonal cortada
A = 2.8                    # apotema interior
H = 3.6                    # alto de muro
T = 0.25                   # espesor
TG = math.tan(math.radians(22.5))
SLADO = 2 * A * TG
L = SLADO + 2 * T * TG
MUROS = {'fondo': 90, 'diag_d': 45, 'der': 0, 'diag_i': 135, 'izq': 180}   # se quitan 225, 270, 315 (el corte)
ZC = 1.85                  # altura del centro del espejo (y del hueco)
RH = 0.56                  # radio del hueco (corte a través del muro del fondo)


def perforar(ob, centro, radio):
    """Hueco circular pasante (booleana exacta) a lo largo de Y; el canto del corte lleva el material CORTE."""
    bm = bmesh.new()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=radio, radius2=radio, depth=2.0)
    bmesh.ops.rotate(bm, verts=g['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    cortador = bb._obj_from_bm('cortador', bm, None, None, centro)
    mod = ob.modifiers.new('hueco', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cortador
    try:
        mod.solver = 'EXACT'
    except Exception:
        pass
    bb.aplicar(ob)
    bpy.data.objects.remove(cortador)
    ob.data.materials.append(CORTE)
    mw = ob.matrix_world
    c = Vector(centro)
    for p in ob.data.polygons:
        pc = mw @ p.center
        nw = (mw.to_3x3() @ p.normal).normalized()
        if abs(nw.y) < 0.3 and abs(math.hypot(pc.x - c.x, pc.z - c.z) - radio) < 0.02:
            p.material_index = 1
            p.use_smooth = True


estuco, moldura, nichos, soporte = [], [], [], []
grupos = {}
for nom, alfa in MUROS.items():
    a = math.radians(alfa)
    g = bb.grupo('muro_' + nom, (A * math.cos(a), A * math.sin(a), 0))
    g.rotation_euler = (0, 0, a - math.pi / 2)
    grupos[nom] = g
    muro = bb.caja(nom + '_muro', (L, T, H), (0, T / 2, H / 2), ESTUCO, g)
    estuco.append(muro)
    # albardilla y cornisa de tres escalones
    moldura.append(bb.caja(nom + '_albardilla', (L, T + 0.2, 0.08), (0, T / 2, H + 0.04), ESTUCO_M, g, bevel=0.012))
    for i, (dp, hh, zz) in enumerate(((0.14, 0.07, H - 0.035), (0.095, 0.055, H - 0.1), (0.05, 0.035, H - 0.165))):
        moldura.append(bb.caja('%s_cornisa%d' % (nom, i), (L, dp, hh), (0, -dp / 2, zz), ESTUCO_M, g, bevel=0.008))
    # zócalo con su moldura
    soporte.append(bb.caja(nom + '_zocalo', (L, 0.05, 0.42), (0, -0.025, 0.21), SOP, g, bevel=0.006))
    moldura.append(bb.caja(nom + '_zocalo_cima', (L, 0.075, 0.035), (0, -0.0375, 0.437), ESTUCO_M, g, bevel=0.006))
bpy.context.view_layer.update()
perforar(estuco[0], (0, A + T / 2, ZC), RH)

# pilastras en los rincones (basa, fuste, capitel)
for beta in (22.5, 67.5, 112.5, 157.5):
    b = math.radians(beta)
    rc = A / math.cos(math.radians(22.5)) - 0.02
    for nom, (w, dp, z0, z1) in (('basa', (0.36, 0.13, 0.0, 0.46)), ('fuste', (0.28, 0.08, 0.46, H - 0.3)),
                                 ('capitel', (0.36, 0.13, H - 0.3, H - 0.19))):
        p = bb.caja('pilastra_%s_%d' % (nom, int(beta)), (w, dp, z1 - z0), (rc * math.cos(b), rc * math.sin(b), (z0 + z1) / 2),
                    ESTUCO_M, None, bevel=0.012)
        p.rotation_euler = (0, 0, b - math.pi / 2)
        moldura.append(p)

# antas: los extremos libres de los muros laterales se rematan como pilares (no quedan cantos de cartón)
for nom, lado in (('izq', -1), ('der', 1)):
    g = grupos[nom]
    xe = lado * (L / 2 - 0.19)
    moldura.append(bb.caja(nom + '_anta', (0.38, T + 0.12, H), (xe, T / 2, H / 2), ESTUCO_M, g, bevel=0.012))
    moldura.append(bb.caja(nom + '_anta_basa', (0.44, T + 0.2, 0.46), (xe, T / 2, 0.23), ESTUCO_M, g, bevel=0.012))
    moldura.append(bb.caja(nom + '_anta_capitel', (0.44, T + 0.2, 0.11), (xe, T / 2, H - 0.245), ESTUCO_M, g, bevel=0.012))

# suelo: plinto octogonal bajo, con un escalón de basa
for nom, (rad, z0, z1) in (('suelo_basa', (A + T + 0.3, -0.24, -0.1)), ('suelo', (A + T + 0.2, -0.1, 0.0))):
    bm = bmesh.new()
    R8 = rad / math.cos(math.radians(22.5))
    g8 = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=R8, radius2=R8, depth=z1 - z0)
    bmesh.ops.rotate(bm, verts=g8['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(22.5), 3, 'Z'))
    bmesh.ops.translate(bm, vec=(0, 0, (z0 + z1) / 2), verts=g8['verts'])
    edges = bm.edges[:]
    bmesh.ops.bevel(bm, geom=edges, offset=0.012, segments=2, affect='EDGES', profile=0.5)
    soporte.append(objeto(nom, bm, SUELO, liso=False))


# ---------------------------------------------------------------- nichos ciegos y medallones ovalados
def nicho(g, nom, w=1.24, zb=0.56, zs=2.55):
    """Nicho ciego de medio punto: fondo apenas más hondo de tono, moldura fina en relieve y repisa."""
    bm = bmesh.new()
    contorno = [(-w / 2, zb), (w / 2, zb)] + [(w / 2 * math.cos(math.pi * i / 40), zs + w / 2 * math.sin(math.pi * i / 40)) for i in range(41)]
    vs = [bm.verts.new((x, -0.006, z)) for x, z in contorno]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0.006, 0), verts=[v for v in ext['geom'] if isinstance(v, bmesh.types.BMVert)])
    nichos.append(objeto(nom + '_nicho', bm, NICHO, g, liso=False))
    bm = bmesh.new()
    rm = 0.024
    for sx in (-1, 1):
        cilindro_bm(bm, (sx * w / 2, -0.02, zb), (sx * w / 2, -0.02, zs), rm, 10)
    tubo_bm(bm, [(w / 2 * math.cos(math.pi * i / 48), -0.02, zs + w / 2 * math.sin(math.pi * i / 48)) for i in range(49)], rm, segs=10)
    caja_bm(bm, (0, -0.035, zb - 0.02), (w + 0.14, 0.07, 0.045), bisel=0.008, segs=2)
    moldura.append(objeto(nom + '_nicho_moldura', bm, ESTUCO_M, g))


def medallon(g, nom, x, z, rx=0.28, rz=0.36):
    bm = bmesh.new()
    gg = bmesh.ops.create_cone(bm, cap_ends=True, segments=72, radius1=1.0, radius2=1.0, depth=0.012)
    bmesh.ops.scale(bm, vec=(rx, rz, 1.0), verts=gg['verts'])
    bmesh.ops.rotate(bm, verts=gg['verts'], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    bmesh.ops.translate(bm, vec=(x, -0.014, z), verts=gg['verts'])
    nichos.append(objeto(nom + '_campo', bm, CAMPO, g))
    for f in nichos[-1].data.polygons:
        f.use_smooth = False
    bm = bmesh.new()
    tubo_bm(bm, elipse(rx + 0.02, rz + 0.02, 96, y=-0.022, cx=x, cz=z), 0.017, segs=10, cerrado=True)
    moldura.append(objeto(nom + '_marco', bm, ESTUCO_M, g))


EMBLEMAS = [  # (muro, tipo, z)
    ('diag_i', 'voluta', 2.4), ('diag_i', 'tabla', 1.3),
    ('diag_d', 'elipse', 2.4), ('diag_d', 'nucleo', 1.3),
    ('izq', 'monada', 1.85), ('der', 'abierto', 1.85),
]
for nom in ('diag_i', 'diag_d', 'izq', 'der'):
    nicho(grupos[nom], nom)
emb_obs, emb_centros = {}, {}
for muro, tipo, z in EMBLEMAS:
    g = grupos[muro]
    medallon(g, 'medallon_' + tipo, 0.0, z)
    e = bb.grupo('emb_' + tipo, (0.0, -0.022, z), g)
    emblema(tipo, 'emblema_' + tipo, e, k=0.84)
    emb_obs[tipo] = e

# forro del hueco: prolonga el canto del corte hacia atrás (en sombra), para que se lea la profundidad
bm = bmesh.new()
NF = 96
aros = [[bm.verts.new((RH * math.cos(2 * math.pi * k / NF), yy, ZC + RH * math.sin(2 * math.pi * k / NF))) for k in range(NF)]
        for yy in (A + T - 0.01, A + T + 0.4)]
for k in range(NF):
    bm.faces.new((aros[0][k], aros[1][k], aros[1][(k + 1) % NF], aros[0][(k + 1) % NF]))
ob_forro = bb._obj_from_bm('hueco_forro', bm, CORTE, None)
for f in ob_forro.data.polygons:
    cf = f.center
    if f.normal.dot(Vector((cf.x, 0, cf.z - ZC))) > 0:
        f.flip()
estuco.append(ob_forro)
capilla_estuco = unir(estuco, 'capilla_estuco')
capilla_moldura = unir(moldura, 'capilla_moldura')
capilla_nichos = unir(nichos, 'capilla_nichos')
capilla_soporte = unir(soporte, 'capilla_soporte')
bpy.context.view_layer.update()
for tipo, e in emb_obs.items():
    emb_centros[tipo] = e.matrix_world @ Vector((0, -0.06, 0))

# ---------------------------------------------------------------- espejo convexo
RS, RCAP = 1.8, 0.6
SAG = RS - math.sqrt(RS * RS - RCAP * RCAP)
YB = A - 0.05              # plano del borde del casquete
CEN = Vector((0, YB - SAG + RS, ZC))      # centro de la esfera del casquete


def cap(u, v, off=0.0):
    p = Vector((u, CEN.y - math.sqrt(RS * RS - u * u - v * v), ZC + v))
    n = (p - CEN).normalized()
    return p + n * off, n


def torno_bm(bm, perfil, segs=128):
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / segs), -dy, r * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
             for r, dy in perfil]
    for i in range(len(rings) - 1):
        for k in range(segs):
            bm.faces.new((rings[i + 1][k], rings[i + 1][(k + 1) % segs], rings[i][(k + 1) % segs], rings[i][k]))


# marco dorado fino: moldura estrecha + cordón + 24 rayos esbeltos (largos y cortos alternados)
bm = bmesh.new()
torno_bm(bm, [(0.596, 0.0), (0.596, 0.062), (0.604, 0.079), (0.62, 0.088), (0.638, 0.086), (0.652, 0.074), (0.66, 0.057),
              (0.672, 0.05), (0.686, 0.054), (0.698, 0.046), (0.704, 0.028), (0.706, 0.0)])
tubo_bm(bm, elipse(0.734, 0.734, 144, y=-0.022), 0.009, segs=8, cerrado=True)
for k in range(24):
    ang = 2 * math.pi * k / 24 + math.pi / 2
    largo = k % 2 == 0
    r0, r1 = 0.745, (0.96 if largo else 0.845)
    w0, w1 = (0.0135 if largo else 0.0105), 0.002
    u = Vector((math.cos(ang), 0, math.sin(ang)))
    t = Vector((-math.sin(ang), 0, math.cos(ang)))
    vs = []
    for dy in (-0.012, -0.03):
        vs += [bm.verts.new(u * r0 + t * w0 + Vector((0, dy, 0))), bm.verts.new(u * r1 + t * w1 + Vector((0, dy, 0))),
               bm.verts.new(u * r1 - t * w1 + Vector((0, dy, 0))), bm.verts.new(u * r0 - t * w0 + Vector((0, dy, 0)))]
    a_, b_ = vs[:4], vs[4:]
    bm.faces.new(a_)
    bm.faces.new(list(reversed(b_)))
    for i in range(4):
        bm.faces.new((a_[i], b_[i], b_[(i + 1) % 4], a_[(i + 1) % 4]))
marco = objeto('marco_espejo', bm, ORO, None, (0, A, ZC))

# ---- fractura del casquete: Voronoi de semillas en anillos con giro (esquirlas grandes, alargadas hacia el borde)
semillas = [Vector((0.0, 0.0))]
rnd_s = random.Random(869)
for rr, nn, giro in ((0.25, 7, 0.0), (0.47, 12, 0.22)):
    for i in range(nn):
        a = 2 * math.pi * i / nn + giro + rnd_s.uniform(-0.07, 0.07)
        r_ = rr + rnd_s.uniform(-0.025, 0.025)
        semillas.append(Vector((r_ * math.cos(a), r_ * math.sin(a))))
disco = [Vector((RCAP * math.cos(2 * math.pi * i / 72), RCAP * math.sin(2 * math.pi * i / 72))) for i in range(72)]


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


def refinar(poly, paso=0.03):
    """Subdivide los lados largos (las esquirlas siguen la curvatura del casquete)."""
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        n = max(1, int((q - p).length / paso))
        out += [p.lerp(q, j / n) for j in range(n)]
    return out


celdas = []
for i, s in enumerate(semillas):
    poly = disco[:]
    for j, o in enumerate(semillas):
        if i != j:
            poly = recortar(poly, s, o)
            if len(poly) < 3:
                break
    if len(poly) >= 3:
        celdas.append(refinar(poly))

GROSOR = 0.014
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
        bm.faces.new((vf[(k + 1) % n], vf[k], vb[k], vb[(k + 1) % n]))
        mid = (vf[k].co + vf[(k + 1) % n].co) / 2
        nl = mid - n0 * mid.dot(n0)
        lat[len(tipos)] = nl.normalized() if nl.length > 1e-6 else n0
        tipos.append('l')
    ob = bb._obj_from_bm('faceta_%03d' % i, bm, FACETA, None, P0)
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
print('[espejo] esquirlas:', len(facetas))

# casquete entero (liso) que las esquirlas relevan en el instante de la fractura
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

# ---- zona opaca: un campo mate de contorno limpio, rayado a 45° (grabado), arriba a la izquierda (del lado del logos)
VC2 = Vector((-0.2, 0.22))


def radio_op(phi):
    return 0.25 * (1 + 0.14 * math.sin(3 * phi + 0.7) + 0.07 * math.sin(5 * phi + 2.1))


def dentro_op(u, v, marg=0.0):
    d = Vector((u, v)) - VC2
    return d.length <= radio_op(math.atan2(d.y, d.x)) - marg and math.hypot(u, v) < 0.57


OFF_V = 0.02               # la zona flota sobre las miniaturas (que quedan debajo, tapadas)
PV, _ = cap(VC2.x, VC2.y, OFF_V)
opacidad = bb.grupo('opacidad', PV)
bm = bmesh.new()
NR, NS = 8, 72
centro_v = bm.verts.new(Vector((0, 0, 0)))
anillos, borde = [], []
for ir in range(1, NR + 1):
    fila = []
    for js in range(NS):
        phi = 2 * math.pi * js / NS
        rr = radio_op(phi) * ir / NR
        u, v = VC2.x + rr * math.cos(phi), VC2.y + rr * math.sin(phi)
        m = math.hypot(u, v)
        if m > 0.57:
            u, v = u * 0.57 / m, v * 0.57 / m
        fila.append(bm.verts.new(cap(u, v, OFF_V)[0] - PV))
        if ir == NR:
            borde.append(cap(u, v, OFF_V + 0.002)[0] - PV)
    anillos.append(fila)
for js in range(NS):
    bm.faces.new((centro_v, anillos[0][js], anillos[0][(js + 1) % NS]))
for ir in range(NR - 1):
    for js in range(NS):
        bm.faces.new((anillos[ir][js], anillos[ir + 1][js], anillos[ir + 1][(js + 1) % NS], anillos[ir][(js + 1) % NS]))
objeto('opacidad_campo', bm, OPACO, opacidad)
bm = bmesh.new()
tubo_bm(bm, borde, 0.0034, segs=6, cerrado=True)
objeto('opacidad_contorno', bm, EMB, opacidad)
bm = bmesh.new()
for c in [VC2.x - VC2.y + 0.03 * i for i in range(-14, 15)]:      # rectas u - v = c
    tramo = []
    for j in range(-60, 61):
        s = j * 0.006
        u, v = c / 2 + s, -c / 2 + s
        u, v = u + (VC2.x + VC2.y) / 2, v + (VC2.x + VC2.y) / 2
        if dentro_op(u, v, 0.012):
            tramo.append(cap(u, v, OFF_V + 0.003)[0] - PV)
        elif tramo:
            if len(tramo) > 2:
                tubo_bm(bm, tramo, 0.0021, segs=5)
            tramo = []
    if len(tramo) > 2:
        tubo_bm(bm, tramo, 0.0021, segs=5)
objeto('opacidad_trama', bm, TRAMA, opacidad)

# ---- la sala reducida: miniaturas de los emblemas sobre el casquete (la zona opaca tapa la voluta y un tramo)
MINIS = {'monada': 180, 'tabla': 222, 'elipse': 40, 'nucleo': 318, 'abierto': 0, 'voluta': 140}
minis = []
for tipo, ang in MINIS.items():
    u, v = 0.37 * math.cos(math.radians(ang)), 0.37 * math.sin(math.radians(ang))
    p, nrm = cap(u, v, 0.002)
    e = bb.grupo('mini_' + tipo, p)
    e.rotation_mode = 'XYZ'
    e.rotation_euler = Vector((0, -1, 0)).rotation_difference(nrm).to_euler('XYZ')
    emblema(tipo, 'mini_emblema_' + tipo, e, k=0.2)
    minis.append(e)
oct_pts = []
for kk in range(8):
    a0 = math.radians(22.5 + 45 * kk)
    a1 = math.radians(22.5 + 45 * (kk + 1))
    pa = Vector((0.5 * math.cos(a0), 0.5 * math.sin(a0)))
    pb = Vector((0.5 * math.cos(a1), 0.5 * math.sin(a1)))
    oct_pts += [pa.lerp(pb, jj / 12) for jj in range(12)]
PO, _ = cap(0, 0)
bm = bmesh.new()
tubo_bm(bm, [cap(q.x, q.y, 0.004)[0] - PO for q in oct_pts], 0.0035, segs=6, cerrado=True)
oct_mini = objeto('mini_octogono', bm, EMB, None, PO)
minis.append(oct_mini)

# ---------------------------------------------------------------- logos: aro dorado delgado, arriba y fuera del eje
RL = 1.3                   # radio del aro
RT = 0.028                 # radio del hilo del aro
RC = Vector((2.45, 1.05, 4.8))
TAU = math.radians(26)
PSI = math.radians(10)
Rz = Matrix.Rotation(PSI, 3, 'Z')
E1 = Rz @ Vector((1, 0, 0))
E2 = Rz @ Vector((0, math.cos(TAU), math.sin(TAU)))
NRM = E1.cross(E2)
R_LOGOS = Matrix((E1, E2, NRM)).transposed()
CORTE_A = math.radians(-35)          # el aro está hecho de dos arcos (200° y 160°): cae partido con limpieza


def arco_bm(a0, a1, n=120):
    bm = bmesh.new()
    tubo_bm(bm, [(RL * math.cos(a0 + (a1 - a0) * i / n), RL * math.sin(a0 + (a1 - a0) * i / n), 0) for i in range(n + 1)], RT, segs=10)
    return bm


arcos = []
for nom, (a0, a1) in (('logos_arco_a', (CORTE_A, CORTE_A + math.radians(200))),
                      ('logos_arco_b', (CORTE_A + math.radians(200), CORTE_A + 2 * math.pi))):
    ob = objeto(nom, arco_bm(a0, a1), ORO_L, None, RC)
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = euler_de(R_LOGOS)
    arcos.append({'ob': ob, 'a0': a0, 'a1': a1})

# ---------------------------------------------------------------- hilos del logos (consonancia) — estado 2
rayos = []
destinos = [emb_centros[t] for t in ('voluta', 'tabla', 'elipse', 'nucleo', 'monada', 'abierto')] + [Vector((0, YB - SAG - 0.02, ZC + 0.66))]
for i, dst in enumerate(destinos):
    d = dst - RC
    Ld = d.length - 0.04
    bm = bmesh.new()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.0075, radius2=0.0045, depth=Ld)
    bmesh.ops.translate(bm, vec=(0, 0, Ld / 2), verts=g['verts'])
    ob = objeto('rayo_%d' % i, bm, ORO_L, None, RC)
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler('XYZ')
    rayos.append(ob)

# ---------------------------------------------------------------- puntos de vista (la ciudad leibniziana) — estado 2
# ojos dibujados: contorno almendrado (dos arcos finos, esmeralda) con un iris dorado pequeño; miran al espejo
PV0 = Vector((0, YB, 1.3))
RPV = 3.25
OBJ_OJO = Vector((0, YB, ZC))
puntos = bb.grupo('puntos_de_vista', PV0)
bm_c, bm_i = bmesh.new(), bmesh.new()
OW, OH = 0.42, 0.17
s_ = OH / 2
R_ = ((OW / 2) ** 2 + s_ ** 2) / (2 * s_)
th0 = math.atan2(R_ - s_, OW / 2)
angs = [236 + 68 * i / 6 for i in range(7)]
for a in angs:
    ar = math.radians(a)
    p = Vector((RPV * math.cos(ar), RPV * math.sin(ar), 0))
    pw = PV0 + p
    d = (OBJ_OJO - pw).normalized()
    der = d.cross(Vector((0, 0, 1))).normalized()
    arr = der.cross(d).normalized()
    for sgn in (1, -1):
        pts = []
        for j in range(33):
            t = th0 + (math.pi - 2 * th0) * j / 32
            uu, vv = R_ * math.cos(t), R_ * math.sin(t) - (R_ - s_)
            pts.append(p + der * uu + arr * (vv * sgn))
        tubo_bm(bm_c, pts, 0.0095, segs=8)
    disco_bm(bm_i, p + d * 0.004, 0.05, eje=d, t=0.012, segs=28)
objeto('puntos_ojos', bm_c, TRAY, puntos)
objeto('puntos_iris', bm_i, ORO_L, puntos)
arco_pts = [(RPV * math.cos(math.radians(a)), RPV * math.sin(math.radians(a)), 0) for a in [228 + 84 * i / 80 for i in range(81)]]
bb.polilinea_punteada('puntos_arco', arco_pts, guion=0.05, hueco=0.06, r=0.0075, material=TRAY, parent=puntos)

# ---------------------------------------------------------------- estado 3-4: pantalla, filo del hueco, trayecto
RP = 0.8                                   # radio de la pantalla (cubre la moldura del marco; asoman los rayos)
YP = A - 0.72
PANT_C = Vector((0, YP, ZC))
bm = bmesh.new()
disco_bm(bm, (-RP, 0, 0), RP, t=0.012, segs=96)   # el origen queda en su borde derecho: se corre hacia la derecha
pantalla = objeto('pantalla', bm, PANT, None, PANT_C + Vector((RP, 0, 0)))
for f in pantalla.data.polygons:
    f.use_smooth = False

filo = bb.grupo('filo_hueco', (0, A - 0.006, ZC))
bm = bmesh.new()
tubo_bm(bm, elipse(RH + 0.004, RH + 0.004, 144), 0.011, segs=8, cerrado=True)
objeto('filo_hueco_aro', bm, AUS, filo)

TC = Vector((0, A - 0.5, ZC))
trayecto = bb.grupo('trayecto', TC)
tr_pts = bb.arco(0, 0, 1.04, 1.04, 112, 112 - 300, n=160, z=0.0, plano='XZ')
bb.polilinea_punteada('trayecto_guiones', tr_pts, guion=0.07, hueco=0.055, r=0.0095, material=TRAY, parent=trayecto,
                      flecha={'r': 0.034, 'largo': 0.12})

# ---------------------------------------------------------------- etiquetas
CF = Vector((-1.0, 0.55, 0.0))       # centro del aro caído (estado 4)
SF = 0.62                            # escala del aro caído
S.etiqueta('reductor', 'reflejo reductor', (0.0, YB - 0.1, ZC + 1.32), clase='serif')
S.etiqueta('opaco', 'opacidad', (-0.98, YB - 0.2, ZC + 0.5), clase='serif')
S.etiqueta('sala', 'la sala, reducida', (-1.08, YB - 0.2, ZC - 0.32), clase='')
S.etiqueta('vaneyck', 'Van Eyck, 1434 (aún no barroco)<span style="display:block;margin-top:.35em">Góngora: «aunque cóncavo fiel»</span>',
           (-1.2, YB - 0.2, ZC - 0.72), clase='nota')
S.etiqueta('logos', 'logos exterior', (RC.x + RL + 0.75, RC.y, RC.z + 0.3), clase='serif')
S.etiqueta('dios', 'el dios jesuita · el rey', (RC.x + RL + 0.75, RC.y, RC.z - 0.25), clase='nota')
S.etiqueta('puntos', 'infinitud de puntos de vista', (0.0, YB - RPV - 0.05, 0.62), clase='trayecto')
S.etiqueta('pantalla', 'el logos: una pantalla', (0.0, YP - 0.05, ZC - 0.2), clase='serif')
S.etiqueta('pulverizado', 'reflejo pulverizado', (-1.8, A - 0.9, ZC + 1.6), clase='serif')
S.etiqueta('carencia', 'carencia', (0.0, A - 0.05, ZC - 0.12), clase='grande')
S.etiqueta('trayecto', 'trayecto dividido por la ausencia', (0.35, A - 0.6, ZC - 1.45), clase='trayecto')
S.etiqueta('destronado', 'logos destronado', (CF.x, CF.y - SF * RL - 0.2, 0.05), clase='nota')

# ---------------------------------------------------------------- línea de tiempo
# estado 1 (0 → 2,0 s): la zona opaca se extiende sobre el espejo
S.mostrar(opacidad, 0.4, 1.8)
# estado 2 (2,0 → 3,8 s): hilos del logos y puntos de vista (ocultos por completo fuera de este tramo)
for i, r in enumerate(rayos):
    t0 = 2.2 + 0.08 * i
    S.clave(r, 0, esc=TINY3, interp=C)
    S.clave(r, t0, esc=(1, 1, TINY))
    S.clave(r, t0 + 0.9, esc=(1, 1, 1))
    S.clave(r, 4.0, esc=(1, 1, 1))
    S.clave(r, 4.5, esc=(1, 1, TINY), interp=C)
    S.clave(r, 4.5 + 1.0 / bb.FPS, esc=TINY3, interp=C)
S.mostrar(puntos, 2.4, 3.4)
S.ocultar(puntos, 4.0, 4.5)
# estado 3 (3,8 → 10 s): pulverización
S.clave(espejo_entero, 0, esc=1.0, interp=C)
S.salto(espejo_entero, 4.7, 1.0, TINY)   # relevo exacto por las esquirlas (sin juntas visibles antes)
S.ocultar(opacidad, 4.2, 4.7)
for mn in minis:
    S.clave(mn, 0, esc=1.0)
    S.ocultar(mn, 4.2, 4.7)
# remolino: cada esquirla conserva su vecindad (del centro al borde → de dentro afuera) y gira con la espiral;
# se inclina sobre la tangente como un álabe. Las de dentro quedan más cerca del muro (embudo hacia el hueco).
R_MIN, R_MAX = 1.0, 1.62
ESQ = 1.45                 # las esquirlas se agrandan al abrirse (el reflejo se pulveriza y se esparce)
for (ob, c2, P0, n0) in facetas:
    rho = min(c2.length / RCAP, 1.0)
    th = math.atan2(c2.y, c2.x)
    r2 = R_MIN + (R_MAX - R_MIN) * rho ** 0.85
    f = (r2 - R_MIN) / (R_MAX - R_MIN)
    th2 = th + 0.55 + 1.35 * f
    dest = Vector((r2 * math.cos(th2), A - 0.2 - 0.38 * f, ZC + r2 * math.sin(th2)))
    R_giro = Matrix.Rotation(th2 - th, 3, Vector((0, -1, 0)))
    tg = Vector((-math.sin(th2), 0, math.cos(th2)))
    R_incl = Matrix.Rotation(math.radians(24 + 18 * f + random.uniform(-5, 5)), 3, tg)
    rot1 = (R_incl @ R_giro).to_euler('XYZ')
    ts = 4.75 + 0.8 * (1 - rho) + 0.35 * random.random()
    du = 1.9 + 0.5 * random.random()
    S.clave(ob, 0, loc=P0, rot=(0, 0, 0), esc=TINY, interp=C)   # oculta: el casquete entero la representa
    S.salto(ob, 4.7, TINY, 1.0)
    S.clave(ob, ts, loc=P0, rot=(0, 0, 0), esc=1.0)
    mid = P0.lerp(dest, 0.35) + Vector((0, -0.3, 0))
    S.clave(ob, ts + 0.4 * du, loc=mid, rot=Euler((rot1.x * 0.45, rot1.y * 0.45, rot1.z * 0.45)), esc=1.0 + (ESQ - 1) * 0.5)
    S.clave(ob, ts + du, loc=dest, rot=rot1, esc=ESQ)
# emblemas desfasados (la armonía se rompe)
for (tipo, e), ang in zip(emb_obs.items(), (17, -26, 31, -12, 22, -34)):
    S.clave(e, 0, rot=(0, 0, 0))
    S.clave(e, 5.0, rot=(0, 0, 0))
    S.clave(e, 7.2, rot=(0, math.radians(ang), 0))
# el aro del logos baja delante del hueco y tiende una pantalla (l. 874-876)
R_PANT = Matrix((Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)))).transposed()
SP = (RP + 0.035) / RL
rot0 = euler_de(R_LOGOS)
rot_p = euler_de(R_PANT, compat=rot0)
ANILLO_P = PANT_C + Vector((0, -0.01, 0))
for ar in arcos:
    ob = ar['ob']
    S.clave(ob, 0, loc=RC, rot=rot0, esc=1.0)
    S.clave(ob, 5.9, loc=RC, rot=rot0, esc=1.0)
    S.clave(ob, 7.0, loc=RC.lerp(ANILLO_P, 0.55) + Vector((0, -0.6, 0.25)), rot=Euler([a + (b - a) * 0.6 for a, b in zip(rot0, rot_p)]),
            esc=1.0 + (SP - 1.0) * 0.6)
    S.clave(ob, 8.1, loc=ANILLO_P, rot=rot_p, esc=SP)
    S.clave(ob, 10.2, loc=ANILLO_P, rot=rot_p, esc=SP)
S.clave(pantalla, 0, esc=TINY3, interp=C)
S.clave(pantalla, 7.9, esc=(TINY, 1, 1), interp=C)
S.clave(pantalla, 7.9 + 1.0 / bb.FPS, esc=(TINY, 1, 1))
S.clave(pantalla, 8.9, esc=(1, 1, 1))
# estado 4 (10 → 13,6 s): la pantalla se corre; el aro cae y se parte (l. 871-872 «ruptura ... del logos en tanto
# que absoluto»; l. 883 «destronamiento»); aparece el filo del hueco; luego el trayecto
S.clave(pantalla, 10.2, esc=(1, 1, 1))
S.clave(pantalla, 11.0, esc=(TINY, 1, 1))
S.salto(pantalla, 11.05, (TINY, 1, 1), TINY3)
for i, ar in enumerate(arcos):
    ob = ar['ob']
    beta = math.radians(-18 if i == 0 else 16)
    Rf = Matrix(((math.cos(beta), -math.sin(beta), 0), (math.sin(beta), math.cos(beta), 0), (0, 0, 1)))
    medio = (ar['a0'] + ar['a1']) / 2 + beta
    despl = Vector((math.cos(medio), math.sin(medio), 0)) * (0.36 if i == 1 else 0.0)
    pos = CF + despl + Vector((0, 0, RT * SF + 0.004))
    rf = euler_de(Rf, compat=rot_p)
    t0 = 10.9 + 0.12 * i
    S.clave(ob, t0, loc=ANILLO_P, rot=rot_p, esc=SP)
    S.clave(ob, t0 + 0.5, loc=ANILLO_P + Vector((-0.3, -0.75, -0.35)), rot=Euler([a + (b - a) * 0.35 for a, b in zip(rot_p, rf)]),
            esc=SP + (SF - SP) * 0.4)
    S.clave(ob, t0 + 1.25, loc=pos, rot=rf, esc=SF)
S.mostrar(filo, 11.4, 12.2)
S.clave(trayecto, 0, esc=TINY, rot=(0, -1.9, 0), interp=C)
S.clave(trayecto, 12.2, esc=TINY, rot=(0, -1.9, 0))
S.clave(trayecto, 13.4, esc=1.0, rot=(0, 0, 0))


# ---------------------------------------------------------------- estados
def vista(cam, look, fov):
    return dict(cam=tuple(c * ESC for c in cam), look=tuple(c * ESC for c in look), fov=fov)


def orbita(look, az, el, dist):
    """Cámara a `dist` de `look`, girada `az` grados hacia la derecha (+X) y elevada `el` grados."""
    a, e = math.radians(az), math.radians(el)
    return (look[0] + dist * math.sin(a) * math.cos(e), look[1] - dist * math.cos(a) * math.cos(e), look[2] + dist * math.sin(e))


L0 = (0.75, 0.6, 1.95)
FRENTE = vista(orbita(L0, 3, 13, 44.0), L0, 11.0)          # tele: la capilla como volumen, la figura a su izquierda
L1 = (0.05, A, ZC - 0.1)
CERCA = vista(orbita(L1, 3, 0, 3.05), L1, 40)               # el espejo de cerca (≥ 1,5 m reales: OrbitControls.minDistance)
L2 = (1.5, 0.9, 1.2)
VISTA = vista(orbita(L2, 3, 22, 14.6), L2, 38)             # frontal alta: muros, emblemas, el logos con su cielo, los ojos
L3 = (0.97, 1.0, 0.85)
NEO = vista(orbita(L3, 3, 10, 14.2), L3, 30)
L4 = (0.97, 0.8, 0.78)
NEO2 = vista(orbita(L4, 5, 12, 14.2), L4, 30)              # incluye el aro caído en el suelo y el telón

# todo lo construido cuelga de una raíz escalada (las cámaras de los estados se crean después, ya en metros reales)
raiz = bb.grupo('raiz')
for ob in list(bpy.data.objects):
    if ob.parent is None and ob is not raiz and ob.type != 'LIGHT':
        ob.parent = raiz
raiz.scale = (ESC, ESC, ESC)

S.estado('La sala y el espejo',
         'Una capilla barroca abstracta. En su muro, un espejo convexo devuelve la sala reducida: '
         'la estructura barroca es «reflejo reductor» de lo que la envuelve.',
         'Sarduy 1972 · b] Espejo (l. 841-845)', etiquetas=['reductor'], orbita=False, t1=0, **FRENTE)
S.estado('Reflejo reductor',
         'Rasgo de todo barroco: el espejo quiere ser «totalizante y minucioso», pero no capta '
         '«la vastedad del lenguaje que lo circunscribe»: algo «le opone su opacidad».',
         'l. 844-852', etiquetas=['sala', 'opaco', 'vaneyck'], t1=2.0, **CERCA)
S.estado('Reflejo significante',
         'Barroco histórico: universo descentrado «pero aún armónico», en consonancia con un logos exterior. '
         'Ninguna vista agota la ciudad leibniziana; la estructura la contiene en potencia.',
         'l. 852-867', etiquetas=['logos', 'dios', 'puntos'], t1=3.8,
         slider={'tipo': 'azimut', 'min': -30, 'max': 12, 'etiqueta': 'puntos de vista (la ciudad leibniziana)',
                 'min_txt': 'izquierda', 'max_txt': 'derecha'}, **VISTA)
S.estado('Pulverización',
         'Neobarroco: reflejo estructural de «la inarmonía». El espejo se pulveriza en torno a un hueco; '
         'el logos sólo organiza «una pantalla que esconde la carencia».',
         'l. 869-876', etiquetas=['pantalla', 'pulverizado'], t1=10.0,
         pregunta='Si el espejo se rompe, ¿qué refleja cada fragmento? ¿Queda un centro?',
         slider={'tipo': 'tiempo', 't0': 3.8, 't1': 10.0, 'etiqueta': 'del reflejo armónico al pulverizado',
                 'min_txt': 'barroco', 'max_txt': 'neobarroco'}, **NEO)
S.estado('Pantalla y carencia',
         'Retirada la pantalla, aparece la carencia: el trayecto gira en torno a esa ausencia. '
         '«Reflejo necesariamente pulverizado»; «arte del destronamiento y la discusión».',
         'l. 871-883 · Díaz 2011, ap. 6',
         etiquetas=['carencia', 'trayecto', 'destronado'], t1=13.6,
         slider={'tipo': 'azimut', 'min': -22, 'max': 10, 'etiqueta': 'otro punto de vista, otro reflejo',
                 'min_txt': 'izquierda', 'max_txt': 'derecha'}, **NEO2)

S.exportar()

# datos para las figuras (decor): el centro del aro del logos y la orientación de su plano, en coordenadas three.js
_n = -NRM                                   # el cielo mira hacia abajo, hacia la capilla
_nt = Vector((_n.x, _n.z, -_n.y))
_b = math.asin(max(-1, min(1, _nt.x)))
_a = math.atan2(-_nt.y, _nt.z)
print('[espejo] logos (three): centro=(%.3f, %.3f, %.3f) diametro=%.3f rot=[%.1f, %.1f, 0]'
      % (RC.x * ESC, RC.z * ESC, -RC.y * ESC, 2 * RL * ESC, math.degrees(_a), math.degrees(_b)))


# ---------------------------------------------------------------- compactar la animación del GLB
# El exportador muestrea cada canal a 30 fps en toda la línea de tiempo. Aquí se quitan las muestras redundantes
# (tramos quietos y tramos que se interpolan bien en línea recta).
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
