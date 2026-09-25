"""N2 · Proliferación — del arco abierto a la elipse.
Figura 2 (Sarduy 1972, l. 224-228): en el centro «Snte.» tachado sobre «Sdo.»; alrededor, un arco punteado
ABIERTO (≈ semicircunferencia superior, abierto por abajo) que nace abajo a la izquierda, pasa por Snte.¹…Snte.⁵
y termina en punta de flecha hacia abajo, a la derecha, seguida de «etc.».
Regla: la proliferación nunca se dibuja como anillo cerrado. La elipse de dos focos es lectura posterior
(Sarduy 1974, cit. por Díaz 2011, l. 1470-1483) y se rotula así. La elipse cerrada sólo aparece aparte (Kepler),
con otro trazo y sin rótulos Snte.

Dirección de arte «lámina de museo»: papel, tinta y oro. Las letras de la figura son geometría (tipos Caslon en
relieve, como un grabado), los trayectos son hilos finos, los objetos son modelos esbeltos de grafito sobre plintos
bajos de piedra; el hueco del significante es un contorno fino bermellón con su palabra tachada.
"""
import sys, os, math, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bb
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras import anim_utils

S = bb.Escena('proliferacion', 'Proliferación: del arco abierto a la elipse', dur=10)
M = bb.mat
TINY = 0.0001
T3 = (TINY, TINY, TINY)
C = 'CONSTANT'
L = 'LINEAR'
RAD = math.radians
FUENTE = '/System/Library/Fonts/Supplemental/BigCaslon.ttf'
if not os.path.exists(FUENTE):
    FUENTE = bb.FUENTES['serif']


# ================================================================ helpers locales (no tocan bb.py)
def mat_local(nombre, hexcol, met=0.0, rough=0.5, emi=0.0, alpha=1.0):
    if nombre in bb._MATS:
        return bb._MATS[nombre]
    m = bpy.data.materials.new(nombre)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = bb.lin(hexcol)
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    if emi:
        b.inputs['Emission Color'].default_value = bb.lin(hexcol)
        b.inputs['Emission Strength'].default_value = emi
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    m.diffuse_color = bb.lin(hexcol, alpha)
    bb._MATS[nombre] = m
    return m


def suave(ob, ang=35):
    for p in ob.data.polygons:
        p.use_smooth = True
    try:
        ob.data.set_sharp_from_angle(angle=math.radians(ang))
    except Exception:
        pass
    return ob


def cil(nombre, r, h, loc=(0, 0, 0), mat=None, parent=None, segs=32, r2=None):
    """Cilindro (o tronco de cono) vertical con la base en loc."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=(r if r2 is None else r2), depth=h)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    return suave(bb._obj_from_bm(nombre, bm, mat, parent, loc))


def barra_x(nombre, r, largo, mat, parent=None, loc=(0, 0, 0), segs=12, centrada=True):
    """Cilindro a lo largo del eje X local (centrado en el origen o desde el origen)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=largo)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
    if not centrada:
        bmesh.ops.translate(bm, vec=(largo / 2, 0, 0), verts=bm.verts)
    return suave(bb._obj_from_bm(nombre, bm, mat, parent, loc))


def punta_x(nombre, r, largo, mat, parent=None, loc=(0, 0, 0), segs=20):
    """Cono con el vértice en el origen y la base hacia -X (punta de flecha que apunta a +X)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=largo)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(-largo / 2, 0, 0), verts=bm.verts)
    return suave(bb._obj_from_bm(nombre, bm, mat, parent, loc), 40)


def placa(nombre, pts, esp, loc=(0, 0, 0), mat=None, parent=None, plano='XZ'):
    """Polígono 2D extruido. plano 'XZ': de pie, mirando a -Y (espesor en Y). 'XY': tendido (espesor hacia +Z)."""
    bm = bmesh.new()
    if plano == 'XZ':
        vf = [bm.verts.new((x, -esp / 2, z)) for x, z in pts]
        vb = [bm.verts.new((x, esp / 2, z)) for x, z in pts]
    else:
        vf = [bm.verts.new((x, y, esp)) for x, y in pts]
        vb = [bm.verts.new((x, y, 0.0)) for x, y in pts]
    n = len(pts)
    bm.faces.new(vf)
    bm.faces.new(list(reversed(vb)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vf[i], vf[j], vb[j], vb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = bb._obj_from_bm(nombre, bm, mat, parent, loc)
    return suave(ob, 30)


def tubo(nombre, pts, r, mat=None, parent=None, cerrado=False, segs=10, loc=(0, 0, 0)):
    """Trazo fino: tubo continuo a lo largo de una polilínea, con esquinas a inglete (sin estrechamientos)."""
    P = [Vector(p) for p in pts]
    n = len(P)
    bm = bmesh.new()
    marcos = []
    for i in range(n):
        if cerrado:
            a, b = P[i] - P[i - 1], P[(i + 1) % n] - P[i]
        else:
            a = P[i] - P[i - 1] if i > 0 else P[1] - P[0]
            b = P[i + 1] - P[i] if i < n - 1 else P[-1] - P[-2]
        a, b = a.normalized(), b.normalized()
        t = a + b
        t = b.copy() if t.length < 1e-6 else t.normalized()
        m = b - a
        m = m.normalized() if m.length > 1e-6 else None
        marcos.append((t, m, 1.0 / max(a.dot(t), 0.25)))
    t0 = marcos[0][0]
    ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    u = (ref - ref.dot(t0) * t0).normalized()
    anillos, dirs = [], []
    for i in range(n):
        t, m, s = marcos[i]
        u = (u - u.dot(t) * t).normalized()
        v = t.cross(u)
        an, dd = [], []
        for k in range(segs):
            ph = 2 * math.pi * k / segs
            w = u * math.cos(ph) + v * math.sin(ph)
            dd.append(w.copy())
            if m is not None:
                w = w + (s - 1) * w.dot(m) * m
            an.append(bm.verts.new(P[i] + w * r))
        anillos.append(an)
        dirs.append(dd)

    def unir(r1, r2, off=0):
        for k in range(segs):
            bm.faces.new((r1[k], r1[(k + 1) % segs], r2[(k + 1 + off) % segs], r2[(k + off) % segs]))
    for i in range(n - 1):
        unir(anillos[i], anillos[i + 1])
    if cerrado:
        mejor = min(range(segs), key=lambda o: sum((dirs[-1][k] - dirs[0][(k + o) % segs]).length for k in range(segs)))
        unir(anillos[-1], anillos[0], mejor)
    else:
        bm.faces.new(list(reversed(anillos[0])))
        bm.faces.new(anillos[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return suave(bb._obj_from_bm(nombre, bm, mat, parent, loc), 60)


def circulo(r, n=64, z=0.0, cx=0.0, cy=0.0, plano='XY'):
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        out.append((cx + r * math.cos(t), cy + r * math.sin(t), z) if plano == 'XY' else (cx + r * math.cos(t), z, cy + r * math.sin(t)))
    return out


def torno(nombre, perfil, mat=None, parent=None, loc=(0, 0, 0), segs=48):
    """Superficie de revolución alrededor de Z a partir de un perfil [(r, z), ...] (r = 0 → vértice en el eje)."""
    bm = bmesh.new()
    anillos = []
    for r, z in perfil:
        if r < 1e-6:
            anillos.append([bm.verts.new((0, 0, z))])
        else:
            anillos.append([bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z)) for k in range(segs)])
    for a, b in zip(anillos[:-1], anillos[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for k in range(segs):
                bm.faces.new((a[0], b[k], b[(k + 1) % segs]))
        elif len(b) == 1:
            for k in range(segs):
                bm.faces.new((a[k], b[0], a[(k + 1) % segs]))
        else:
            for k in range(segs):
                bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return suave(bb._obj_from_bm(nombre, bm, mat, parent, loc), 40)


def caja_punteada(nombre, size, loc, mat, parent=None, guion=0.05, hueco=0.035, r=0.005):
    """Contorno punteado de una caja (12 aristas): el lugar de lo que todavía no llega."""
    g = bb.grupo(nombre, loc, parent)
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    q = [(-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)]
    for i in range(4):
        a, b = q[i], q[(i + 1) % 4]
        bb.polilinea_punteada(f'{nombre}_inf{i}', [(a[0], a[1], -sz), (b[0], b[1], -sz)], guion, hueco, r, mat, g)
        bb.polilinea_punteada(f'{nombre}_sup{i}', [(a[0], a[1], sz), (b[0], b[1], sz)], guion, hueco, r, mat, g)
        bb.polilinea_punteada(f'{nombre}_v{i}', [(a[0], a[1], -sz), (a[0], a[1], sz)], guion, hueco, r, mat, g)
    return g


def texto3d(nombre, cuerpo, size, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), align='CENTER', extr=0.004, res=5):
    """Letras de la figura como geometría (tipos Caslon en relieve). En su plano XY mirando a +Z."""
    cu = bpy.data.curves.new(nombre, 'FONT')
    cu.body = cuerpo
    cu.size = size
    cu.extrude = extr
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.resolution_u = res
    cu.font = bpy.data.fonts.load(FUENTE, check_existing=True)
    ob = bpy.data.objects.new(nombre, cu)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        cu.materials.append(mat)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.view_layer.objects.active
    ob.name = nombre
    if parent is not None:
        ob.parent = parent
        ob.matrix_parent_inverse.identity()
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def unir(obs, nombre):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = nombre
    ob.data.name = nombre
    return ob


def centrar_xy(ob):
    """Traslada la malla para que su caja quede centrada en el origen (X e Y locales)."""
    vs = ob.data.vertices
    xs, ys = [v.co.x for v in vs], [v.co.y for v in vs]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    for v in vs:
        v.co.x -= cx
        v.co.y -= cy
    return ob


def palabra(nombre, cuerpo, size, mat, sup=None, extr=0.004):
    """Palabra (con superíndice opcional) centrada en su plano XY, mirando a +Z."""
    base = texto3d(nombre, cuerpo, size, mat, align='LEFT', extr=extr)
    obs = [base]
    if sup:
        w = max(v.co.x for v in base.data.vertices)
        s = texto3d(nombre + '_sup', sup, size * 0.62, mat, align='LEFT', extr=extr)
        for v in s.data.vertices:
            v.co.x += w + size * 0.04
            v.co.y += size * 0.36
        obs.append(s)
    ob = unir(obs, nombre)
    return centrar_xy(ob)


def colocar(ob, parent, loc, rot=(0, 0, 0)):
    ob.parent = parent
    ob.matrix_parent_inverse.identity()
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def rayo(nombre, a, b, r=0.008, punta=True, mat=None):
    """Grupo con origen en a y geometría a lo largo de +X local hasta b (crece por escala X desde a)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    Ld = d.length
    g = bb.grupo(nombre, tuple(a))
    g.rotation_euler = (0, -math.asin(d.z / Ld), math.atan2(d.y, d.x))
    lp = 0.11 if punta else 0.0
    barra_x(nombre + '_linea', r, Ld - lp * 0.8, mat or VERDE, g, centrada=False, segs=10)
    if punta:
        punta_x(nombre + '_punta', r * 3.6, lp, mat or VERDE, g, loc=(Ld, 0, 0))
    return g


def clave(ob, t, loc=None, rot=None, esc=None, interp=None):
    """Como S.clave, pero fija la interpolación de la clave de verdad (en Blender 5.x la preferencia no se aplica)."""
    S.clave(ob, t, loc=loc, rot=rot, esc=esc)
    ad = ob.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    rutas = [r for r, v in (('location', loc), ('rotation_euler', rot), ('scale', esc)) if v is not None]
    fr = S.f(t)
    for fc in cb.fcurves:
        if fc.data_path in rutas:
            for k in fc.keyframe_points:
                if abs(k.co[0] - fr) < 0.5:
                    k.interpolation = interp or 'BEZIER'


def ver(ob, *tramos, inicial=T3):
    """Visibilidad por escala. tramos: (t0, t1, desde, hasta) con escalares o tuplas; clave inicial en t=0."""
    clave(ob, 0, esc=inicial, interp=C)
    for t0, t1, a, b in tramos:
        clave(ob, t0, esc=a)
        clave(ob, t1, esc=b)


def fusionar(g, nombre):
    """Une todas las mallas descendientes de g en una sola malla hija de g (menos nodos y canales en el GLB)."""
    bpy.context.view_layer.update()
    mallas = [o for o in g.children_recursive if o.type == 'MESH']
    subgrupos = [o for o in g.children_recursive if o.type == 'EMPTY' and not o.name.startswith('lbl_')]
    if not mallas:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in mallas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mallas[0]
    if len(mallas) > 1:
        bpy.ops.object.join()
    act = bpy.context.view_layer.objects.active
    act.name = nombre
    act.data.name = nombre
    mw = act.matrix_world.copy()
    act.parent = g
    act.matrix_parent_inverse.identity()
    bpy.context.view_layer.update()
    act.matrix_world = mw
    for v in subgrupos:
        if not v.children:
            bpy.data.objects.remove(v)
    bpy.context.view_layer.update()
    return act


def lbl(clave):
    return bpy.data.objects['lbl_' + clave]


# ================================================================ materiales (papel, tinta y oro)
ORO = M('significado')                 # Sdo.: oro
BERM = M('ausencia')                   # tachadura, hueco del significante
VERDE = M('trayecto')                  # lectura (rayos): esmeralda
PIEDRA = M('soporte')                  # plintos bajos
OBJ = M('significante')                # los significantes (objetos, tablillas): grafito
TINTA = M('soporte', 'grafito_tinta')  # letras en relieve y trazos finos de dibujo
PAPEL = M('lamina')                    # caras de papel (esfera del reloj, armario, tablillas)
FANT = M('fantasma')                   # lo que todavía no llega
ARCO = mat_local('arco_nacar', '#2F3134', 0.0, 0.5)          # la cadena: grafito
PIEL = mat_local('estrato_piel', '#DCD3C6', 0.0, 0.8)        # la piel del ojo de Abreu
KORB = mat_local('azogue_linea', '#16795A', 0.0, 0.4)        # la órbita de Kepler: trayecto (esmeralda)
VACIO_K = M('ausencia', 'hueco_kepler')                      # el foco vacío: la misma ausencia que el Snte. tachado
# ajustes del estudio: grafito mate (no plástico), oro satinado, fantasma legible sobre el papel
S.estudio = {'materiales': {
    'significante': {'roughness': 0.5, 'clearcoat': 0.25, 'clearcoatRoughness': 0.35, 'envMapIntensity': 0.7},
    'arco_nacar': {'roughness': 0.5, 'clearcoat': 0.2, 'clearcoatRoughness': 0.35},
    'grafito_tinta': {'color': '#17181B', 'roughness': 0.85, 'clearcoat': 0.0, 'envMapIntensity': 0.25},
    'significado': {'roughness': 0.42},
    'fantasma': {'opacity': 0.55},
    'estrato_piel': {'color': '#DED6CA'},
}}
MAG = 'color:var(--magenta-claro);font-style:italic'      # palabras citadas de Carpentier (cita = carmín)


# ---------------------------------------------------------------- encuadre para las dos vistas del visor
# El fov es vertical y común a las dos vistas; en unidades (u, v) = coordenadas de cámara / (z·tan(fov/2)) un punto
# cae en el mismo sitio en ambas; sólo cambian el ancho visible y el tamaño relativo de los rótulos (px fijos).
#   pantalla completa: 1920×1080 · libre x 70-1314, y 118-975 (título arriba; tarjeta desde x≈1344; barra abajo-izq.)
#   incrustado: 1920×983 (bajo el título compacto de 97 px) · libre x 60-1304, y 22-875 (tarjeta desde x≈1334)
VISTAS = [(1920, 1080, (70, 118, 1314, 975)), (1920, 983, (60, 22, 1304, 875))]
# bordes superiores de la tarjeta de texto por estado (medidos en el visor: pantalla completa, incrustado)
TARJ = [(774, 679), (774, 679), (745, 672), (774, 679), (733, 638), (708, 613)]


def pad_etq(clave):
    """Semiancho y semialto (px) aproximados del rótulo HTML, según su clase (ver docs/3d/visor.css)."""
    d = S.etiquetas['lbl_' + clave]
    lineas = re.split(r'<br\s*/?>', d['html'])
    lh = 1.3 if 'line-height' in d['html'] else 1.0

    def largo(s):
        s = re.sub(r'<sup>.*?</sup>', 'x', s)
        return len(re.sub(r'<[^>]+>', '', s))
    n = max(largo(x) for x in lineas)
    cl = d['clase'].split()
    if 'grande' in cl:
        fs, k, px, py = 40.3, 0.43, 0.64, 0.18
    elif 'serif' in cl:
        fs, k, px, py = 34.6, 0.43, 1.1, 0.64
    elif 'nota' in cl:
        fs, k, px, py = 19.2, 0.47, 0.0, 0.0
    else:
        fs, k, px, py = 23.4, 0.48, 1.1, 0.64
    return (n * k + px) * fs / 2 + 4, (len(lineas) * lh + py) * fs / 2 + 4


def puntos_visibles(t, etiquetas=(), excluir=()):
    """Vértices (muestreados) de las mallas visibles en el instante t y anclas de los rótulos, con su semitamaño en px."""
    sc = bpy.context.scene
    sc.frame_set(S.f(t))
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for ob in sc.objects:
        if ob.type != 'MESH' or any(ob.name.startswith(e) for e in excluir):
            continue
        ev = ob.evaluated_get(dg)
        mw = ev.matrix_world.copy()
        if abs(mw.to_3x3().determinant()) < 1e-3:       # oculto por escala
            continue
        me = ev.to_mesh()
        vs = me.vertices
        paso = max(1, len(vs) // 400)
        for i in range(0, len(vs), paso):
            out.append((mw @ vs[i].co, 0.0, 0.0))
        ev.to_mesh_clear()
    for k in etiquetas:
        pw, ph = pad_etq(k)
        out.append((lbl(k).matrix_world.translation.copy(), pw, ph))
    return out


XR = 1860          # borde derecho utilizable por encima de la tarjeta (px, ambas vistas)
MARGEN_T = 30      # aire sobre la tarjeta de texto (px)


def encuadre(nombre, t, etiquetas, az, el, fov, extra=(), look0=(0, 0.4, 0.5), dist=10.0, excluir=(), dmax=60.0, sesgo=0.35,
             tarjeta=None):
    """Cámara vista desde azimut/elevación (grados; az=0 → de frente, desde -Y) que encaja lo visible en t
    (mallas + rótulos + puntos extra) en la zona libre de AMBAS vistas, lo más grande posible. En vertical, `sesgo`
    reparte el margen sobrante (0 = arriba del todo, 0,5 = centrado).
    tarjeta: (y_pantalla_completa, y_incrustado), borde superior de la tarjeta de texto de ese estado (px del visor).
    Con ella la zona libre es una L: por encima de la tarjeta la figura puede llegar hasta x = XR."""
    a, e = math.radians(az), math.radians(el)
    dv = Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)))
    pts = puntos_visibles(t, etiquetas, excluir) + list(extra)
    T = math.tan(math.radians(fov) / 2)
    P3 = np.array([[p.x, p.y, p.z] for p, _, _ in pts])
    PW = np.array([pw for _, pw, _ in pts])
    PH = np.array([ph for _, _, ph in pts])
    n = len(pts)
    LU, HU, LV, HV = np.full(n, -9.0), np.full(n, 9.0), np.full(n, -9.0), np.full(n, 9.0)   # unidades de semialto
    tarj = []
    for j, (W, H, (x0, y0, x1, y1)) in enumerate(VISTAS):
        h2 = H / 2
        LU = np.maximum(LU, (x0 - W / 2) / h2 + PW / h2)
        HU = np.minimum(HU, ((XR if tarjeta else x1) - W / 2) / h2 - PW / h2)
        LV = np.maximum(LV, (y0 - h2) / h2 + PH / h2)
        HV = np.minimum(HV, (y1 - h2) / h2 - PH / h2)
        if tarjeta:
            tarj.append(((x1 - W / 2) / h2 - PW / h2, (tarjeta[j] - MARGEN_T - h2) / h2 - PH / h2))
    look = Vector(look0)
    f = -dv
    r = f.cross(Vector((0, 0, 1))).normalized()
    up = r.cross(f)
    Fv, Rv, Uv = np.array(f), np.array(r), np.array(up)

    def uv(cam):
        w = P3 - np.array(cam)
        z = np.maximum(w @ Fv, 1e-3)
        return (w @ Rv) / (z * T), -(w @ Uv) / (z * T)

    def rect(s, cu, cv):
        return np.max(LU - s * cu), np.min(HU - s * cu), np.max(LV - s * cv), np.min(HV - s * cv)

    def tope_u(s, cu, cv, tv, hu):
        for AU, BV in tarj:
            m = tv > BV - s * cv
            if np.any(m):
                hu = min(hu, float(np.min((AU - s * cu)[m])))
        return hu

    def factible(s, cu, cv):
        lu, hu, lv, hv = rect(s, cu, cv)
        if lu > hu or lv > hv:
            return False
        return tope_u(s, cu, cv, lv, hu) >= lu

    def traslacion(s, cu, cv):
        lu, hu, lv, hv = rect(s, cu, cv)
        if not tarj:
            return (lu + hu) / 2, lv + sesgo * (hv - lv)
        obj = lv + sesgo * (hv - lv)
        mejor = None
        for tv in np.linspace(lv, max(hv, lv), 61):
            tp = tope_u(s, cu, cv, tv, hu)
            if tp >= lu and (mejor is None or abs(tv - obj) < mejor[0]):
                mejor = (abs(tv - obj), (lu + tp) / 2, tv)
        return (lu, lv) if mejor is None else (mejor[1], mejor[2])

    for _ in range(90):
        cam = look + dv * dist
        cu, cv = uv(cam)
        s0, s1 = 0.05, 20.0
        for _ in range(40):
            sm = (s0 + s1) / 2
            s0, s1 = (sm, s1) if factible(sm, cu, cv) else (s0, sm)
        s = s0
        du, dvv = traslacion(s, cu, cv)
        look = look + r * (-du * dist * T * 0.7) + up * (dvv * dist * T * 0.7)
        dist = min(max(dist / s ** 0.6, 2.0), dmax)
    cam = look + dv * dist
    cu, cv = uv(cam)
    cs = list(zip(cu.tolist(), cv.tolist()))
    for W, H, _ in VISTAS:
        h2 = H / 2
        xs = [W / 2 + c[0] * h2 + sg * p[1] for c, p in zip(cs, pts) for sg in (-1, 1)]
        ys = [h2 + c[1] * h2 + sg * p[2] for c, p in zip(cs, pts) for sg in (-1, 1)]
        print(f'[encuadre] {nombre} {W}x{H}: x {min(xs):.0f}-{max(xs):.0f}  y {min(ys):.0f}-{max(ys):.0f}')
    print(f'[encuadre] {nombre}: cam={tuple(round(c, 2) for c in cam)} look={tuple(round(c, 2) for c in look)} dist={dist:.2f}')
    return dict(cam=tuple(cam), look=tuple(look), fov=fov)


def piso_elipse(cx, cy, ax, ay, n=24, z=-0.06):
    """Puntos extra (en el piso) del contorno de un calco, para que el encuadre no lo corte."""
    return [(Vector((cx + ax * math.cos(2 * math.pi * i / n), cy + ay * math.sin(2 * math.pi * i / n), z)), 0.0, 0.0) for i in range(n)]


# ================================================================ geometría del arco (figura 2)
R = 1.8                                          # radio del arco
TH0, TH1 = RAD(194), RAD(-15)                    # nace abajo-izq., termina abajo-der. (medido sobre el escaneo)
E_FIN = 0.52                                     # excentricidad final (lectura 1974; el PLAN admite 0-0,6)
A_FIN = 1.2 * R
B_FIN = A_FIN * math.sqrt(1 - E_FIN ** 2)
Z0 = 0.95           # altura del centro del arco en la figura de pie (estado 0)
PISO = -0.06        # piso del estudio (tools/pisos.json)
PL_H = 0.045        # plintos bajos
PT = PISO + PL_H    # cara superior de los plintos
Z_ARC = PISO + 0.016   # el arco tendido: un hilo apenas sobre el piso


def ejes(k):
    """Semiejes y distancia focal para la mezcla k (0 = círculo, 1 = elipse). Lineal en k, como la shape key."""
    a = R + k * (A_FIN - R)
    b = R + k * (B_FIN - R)
    return a, b, math.sqrt(max(a * a - b * b, 0.0))


def P(th, k=0.0, f=1.0):
    a, b, _ = ejes(k)
    return (f * a * math.cos(th), f * b * math.sin(th))


def ang(th, k=0.0):
    a, b, _ = ejes(k)
    return math.atan2(-b * math.cos(th), a * math.sin(th))   # tangente en el sentido del recorrido (θ decreciente)


def desenrollar(a, ref):
    while a - ref > math.pi:
        a -= 2 * math.pi
    while a - ref < -math.pi:
        a += 2 * math.pi
    return a


# tiempos (s)
T_TEND0, T_TEND1 = 0.05, 0.95          # la figura se tiende en el espacio
T1 = 1.75                              # fin estado 1 (cadena)
T2 = 4.0                               # fin estado 2 (lectura radial)
T3F = 5.1                              # fin estado 3 (lectura deceptiva)
T4P = T3F + 0.45                       # fin del preludio del estado 4 (se recogen rayos, vuelve el Sdo., se tienden)
TM0, TM1 = T4P + 0.05, T4P + 1.55      # deformación círculo → elipse (deslizador)
TK_A0, TK_A1 = TM1, TM1 + 0.3          # aparece Kepler
TK0, TK1 = TK_A1 + 0.1, TK_A1 + 1.1    # Kepler: círculo → elipse (deslizador)
NS = 8                                 # muestras de la deformación


def muestras(t0, t1):
    return [(t0 + (t1 - t0) * j / NS, j / NS) for j in range(NS + 1)]


# ---------------------------------------------------------------- órbita: grupo del arco (plano local XY)
orb = bb.grupo('orbita', (0, 0, Z0))

DASH, GAP, RT = 0.1, 0.068, 0.011      # guiones cortos y regulares, hilo fino
L_FL, R_FL = 0.2, 0.036                # punta de flecha esbelta
s_fin = R * (TH0 - TH1) - L_FL
GUIONES = []
s = 0.0
while s < s_fin - 0.03:
    e = min(s + DASH, s_fin - 0.02)
    GUIONES.append((TH0 - ((s + e) / 2) / R, e - s))
    s = e + GAP


def lugar_guion(c, th, k):
    x, y = P(th, k)
    a = ang(th, k)
    Tg = Vector((math.cos(a), math.sin(a), 0))
    N = Vector((-Tg.y, Tg.x, 0))
    return Vector((x, y, 0)) + Tg * c.z + N * c.x + Vector((0, 0, c.y))


bm = bmesh.new()
regs = []
for th, lg in GUIONES:
    geo = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=RT, radius2=RT, depth=lg)
    for v in geo['verts']:
        regs.append((v, th, v.co.copy()))
for v, th, c in regs:
    v.co = lugar_guion(c, th, 0)
bm.verts.index_update()
regs = [(v.index, th, c) for v, th, c in regs]
arco = suave(bb._obj_from_bm('arco_punteado', bm, ARCO, orb))
arco.shape_key_add(name='Basis')
forma_elipse = arco.shape_key_add(name='elipse')
for i, th, c in regs:
    forma_elipse.data[i].co = lugar_guion(c, th, 1)
flecha = punta_x('arco_punta', R_FL, L_FL, ARCO, orb)

# ---------------------------------------------------------------- letras de la figura (relieve de tinta)
TXT = 0.18                                      # cuerpo de las letras de la figura
LBL0 = [(-1.27, 0.0), (-1.1, 0.62), (-0.3, 1.17), (0.73, 1.04), (1.14, 0.57)]   # medidas sobre el escaneo (× R)
FIG_TXT = []
for n, (fx, fy) in enumerate(LBL0):
    ob = palabra(f'fig_snte{n + 1}', 'Snte.', TXT, TINTA, sup=str(n + 1))
    FIG_TXT.append(colocar(ob, orb, (fx * R, fy * R, 0.0)))
TH_ETC = RAD(-4)
etc_txt = colocar(palabra('fig_etc', 'etc.', TXT, TINTA), orb, (0, 0, 0))

# ---------------------------------------------------------------- estela central: la fracción Snte./Sdo.
SW, SD, SH = 0.62, 0.045, 0.27                   # tablilla del Sdo.: delgada, bisel pequeño
Z_BARRA = SH + 0.065
SNTE_Z0 = Z_BARRA + 0.065 + SH / 2               # centro del hueco sobre la barra
FR_H = SNTE_Z0 + SH / 2                          # alto de la fracción
X_FIG = 0.1 * R                                  # en el escaneo la fracción está algo a la derecha del centro
estela = bb.grupo('estela', (X_FIG, 0, Z0 - FR_H / 2))
plinto_e = bb.grupo('estela_plinto', (0, 0, 0), estela)
bb.caja('estela_plinto_malla', (0.96, 0.34, PL_H), (0, 0, -PL_H / 2), PIEDRA, plinto_e, bevel=0.006)
sdo_g = bb.grupo('sdo', (0, 0, 0), estela)
bb.caja('sdo_tablilla', (SW, SD, SH), (0, 0, SH / 2), ORO, sdo_g, bevel=0.006)
colocar(palabra('sdo_letras', 'Sdo.', TXT * 0.95, TINTA, extr=0.003), sdo_g, (0, -SD / 2 - 0.003, SH / 2), (RAD(90), 0, 0))
fusionar(sdo_g, 'sdo_malla')
barra = tubo('barra', [(-0.4, 0, 0), (0.4, 0, 0)], 0.0075, TINTA, estela, segs=12, loc=(0, 0, Z_BARRA))
# el hueco del significante: contorno fino bermellón con la palabra tachada adentro (plano XZ, centro en el origen)
snte_g = bb.grupo('snte_ausente', (0, 0, SNTE_Z0), estela)
tubo('snte_contorno', [(-SW / 2, 0, -SH / 2), (SW / 2, 0, -SH / 2), (SW / 2, 0, SH / 2), (-SW / 2, 0, SH / 2)], 0.0065, BERM,
     snte_g, cerrado=True, segs=10)
colocar(palabra('snte_letras', 'Snte.', TXT * 0.95, TINTA, extr=0.003), snte_g, (0, -0.002, 0), (RAD(90), 0, 0))
tubo('snte_tachadura', [(-0.25, -0.012, -0.035), (0.25, -0.012, 0.035)], 0.0075, BERM, snte_g, segs=10)
fusionar(snte_g, 'snte_ausente_malla')

# ---------------------------------------------------------------- la cadena: plintos sobre el arco
ANG_SNTE = [180, 145, 100, 55, 22]          # posiciones de Snte.¹…⁵ sobre el arco (figura 2)
TH_S = [RAD(a) for a in ANG_SNTE]
PL_R = 0.32                                 # plintos iguales, bajos
F_N = (R + PL_R + 0.1) / R                  # los objetos quedan justo por fuera del arco
BASES, OBJS, ABREU, TABS = [], [], [], []
for n in range(5):
    g = bb.grupo(f'eslabon{n + 1}', (0, 0, 0), orb)
    x, y = P(TH_S[n], 0, F_N)
    g.location = (x, y, PT - Z_ARC)
    cil(f'eslabon{n + 1}_plinto', PL_R, PL_H, (0, 0, -PL_H), PIEDRA, g, segs=64)
    BASES.append(g)


def objeto(n, nombre, yaw, lista):
    g = bb.grupo(nombre, (0, 0, 0), BASES[n])
    g.rotation_euler = (0, 0, RAD(yaw))
    lista.append(g)
    return g


# --- Snte.¹: reloj de sol convertido en reloj de luna (columna esbelta, esfera de papel con horas grabadas)
o1 = objeto(0, 'obj_reloj', -12, OBJS)
bb.caja('reloj_base', (0.18, 0.18, 0.026), (0, 0, 0.013), OBJ, o1, bevel=0.004)
cil('reloj_columna', 0.036, 0.42, (0, 0, 0.026), OBJ, o1, segs=28, r2=0.03)
cil('reloj_capitel', 0.07, 0.016, (0, 0, 0.446), OBJ, o1, segs=32)
ZD = 0.462
RD = 0.21
cil('reloj_esfera', RD, 0.012, (0, 0, ZD), PAPEL, o1, segs=72)
tubo('reloj_canto', circulo(RD, 72, ZD + 0.012), 0.005, OBJ, o1, cerrado=True, segs=8)
tubo('reloj_circ_horas', circulo(RD * 0.62, 64, ZD + 0.0125), 0.0022, TINTA, o1, cerrado=True, segs=6)
for h in range(13):
    a = RAD(180 + 15 * h)                      # horas «invertidas»: las marcas van por la mitad delantera
    r0, r1 = RD * 0.62, RD * (0.9 if h % 3 else 0.97)
    tubo(f'reloj_hora_{h}', [(r0 * math.cos(a), r0 * math.sin(a), ZD + 0.0125), (r1 * math.cos(a), r1 * math.sin(a), ZD + 0.0125)],
         0.0024, TINTA, o1, segs=6)
gn = placa('reloj_gnomon', [(-0.15, 0.0), (0.15, 0.0), (-0.15, 0.13)], 0.006, (0, 0.0, ZD + 0.012), OBJ, o1)
gn.rotation_euler = (0, 0, RAD(90))
cre = []
rl, kl = 0.045, 0.45
for j in range(25):
    t = RAD(90 + 180 * j / 24)
    cre.append((rl * math.cos(t), rl * math.sin(t)))
for j in range(1, 24):
    t = RAD(-90 + 180 * j / 24)
    cre.append((-kl * rl * math.cos(t), rl * math.sin(t)))
luna = placa('reloj_luna', cre, 0.003, (0.095, -0.07, ZD + 0.012), OBJ, o1, plano='XY')   # la sombra dibuja una luna
luna.rotation_euler = (0, 0, RAD(200))
fusionar(o1, 'reloj_malla')

# --- Snte.²: balanza para pesar gatos (hilos finos, platillos delgados)
o2 = objeto(1, 'obj_balanza', -12, OBJS)
bb.caja('bal_base', (0.4, 0.15, 0.018), (0, 0, 0.009), OBJ, o2, bevel=0.004)
cil('bal_columna', 0.011, 0.8, (0, 0, 0.018), OBJ, o2, segs=12)
cil('bal_pomo', 0.02, 0.028, (0, 0, 0.818), OBJ, o2, segs=16)
TILT = RAD(7)                                 # el lado del gato pesa más
ZB = 0.8
BR = 0.31
bb.caja('bal_cruz', (2 * BR + 0.04, 0.014, 0.014), (0, 0, ZB), OBJ, o2, bevel=0.003).rotation_euler = (0, TILT, 0)
for sgn, nm in ((-1, 'izq'), (1, 'der')):
    ex = sgn * BR
    top = Vector((ex * math.cos(TILT), 0, ZB - ex * math.sin(TILT)))
    bot = 0.56 if sgn < 0 else 0.44
    for k in range(3):
        a = RAD(90 + 120 * k)
        tubo(f'bal_hilo_{nm}_{k}', [tuple(top), (top.x + 0.085 * math.cos(a), 0.085 * math.sin(a), bot + 0.012)], 0.0018, TINTA, o2, segs=5)
    cil(f'bal_platillo_{nm}', 0.078, 0.012, (top.x, 0, bot), OBJ, o2, segs=40, r2=0.098)
gato = [(-0.075, 0.0), (-0.07, 0.07), (-0.058, 0.13), (-0.062, 0.165), (-0.074, 0.19), (-0.068, 0.222),
        (-0.07, 0.262), (-0.045, 0.238), (-0.02, 0.24), (-0.004, 0.262), (0.0, 0.215), (-0.006, 0.18),
        (0.03, 0.15), (0.068, 0.09), (0.08, 0.035), (0.11, 0.03), (0.14, 0.06), (0.15, 0.1), (0.162, 0.1),
        (0.158, 0.05), (0.13, 0.008), (0.085, 0.0)]
exr = BR * math.cos(TILT)
placa('bal_gato', [(x * 0.95, z * 0.95) for x, z in gato], 0.03, (exr - 0.02, 0, 0.456), OBJ, o2)
fusionar(o2, 'balanza_malla')

# --- Snte.³: telescopio pequeño, sacado por el cristal roto de una luceta (la luceta: un arco dibujado)
o3 = objeto(2, 'obj_telescopio', -12, OBJS)
HUB = Vector((0.0, -0.02, 0.4))
for k in range(3):
    a = RAD(-90 + 120 * k)
    tubo(f'tel_pata_{k}', [tuple(HUB), (HUB.x + 0.15 * math.cos(a), HUB.y + 0.15 * math.sin(a), 0.0)], 0.0065, OBJ, o3, segs=8)
cil('tel_cabeza', 0.022, 0.04, tuple(HUB - Vector((0, 0, 0.02))), OBJ, o3, segs=16)
tel = bb.grupo('tel', tuple(HUB + Vector((0, 0, 0.035))), o3)
tel.rotation_euler = (0, RAD(-16), RAD(40))   # mira hacia afuera y arriba, a través de la luceta
bb.cilindro_entre('tel_tubo', (-0.26, 0, 0), (0.3, 0, 0), r=0.024, material=OBJ, parent=tel, segs=24)
bb.cilindro_entre('tel_objetivo', (0.28, 0, 0), (0.38, 0, 0), r=0.031, material=OBJ, parent=tel, segs=24)
bb.cilindro_entre('tel_ocular', (-0.36, 0, 0), (-0.25, 0, 0), r=0.011, material=OBJ, parent=tel, segs=12)
for j, xx in enumerate((-0.12, 0.12)):
    bb.cilindro_entre(f'tel_anillo_{j}', (xx - 0.008, 0, 0), (xx + 0.008, 0, 0), r=0.029, material=OBJ, parent=tel, segs=24)
# la luceta: arco de medio punto trazado con un hilo, girado 40° para que el tubo la atraviese de frente
luc = bb.grupo('luceta', (0.08, 0.08, 0.0), o3)
luc.rotation_euler = (0, 0, RAD(40 - 90))
LW, LZ0, LZ1 = 0.22, 0.26, 0.62
luc_pts = [(LW, 0, LZ0)]
for j in range(33):
    t = RAD(180 * j / 32)
    luc_pts.append((LW * math.cos(t), 0, LZ1 + LW * math.sin(t)))
luc_pts.append((-LW, 0, LZ0))
tubo('luc_marco', luc_pts, 0.0065, OBJ, luc, cerrado=True, segs=8)
tubo('luc_alfeizar', [(-LW - 0.04, 0, LZ0 - 0.012), (LW + 0.04, 0, LZ0 - 0.012)], 0.009, OBJ, luc, segs=8)
# el vidrio roto: grietas finas que irradian desde el paso del tubo
CEN = Vector((0.025, 0, 0.47))
for k, (dx, dz) in enumerate(((-0.2, 0.1), (-0.19, -0.12), (0.12, -0.26), (0.19, 0.18), (-0.02, 0.28))):
    mid = CEN + Vector((dx * 0.5 + 0.02 * (-1) ** k, 0, dz * 0.5))
    tubo(f'luc_grieta_{k}', [tuple(CEN), tuple(mid), tuple(CEN + Vector((dx, 0, dz)))], 0.0022, TINTA, luc, segs=5)
for j in range(2):
    tubo(f'luc_pie_{j}', [((-1) ** j * (LW + 0.02), 0, 0.0), ((-1) ** j * (LW + 0.02), 0, LZ0 - 0.02)], 0.0065, OBJ, luc, segs=8)
fusionar(o3, 'telescopio_malla')

# --- Snte.⁴: armario alto (papel con aristas de tinta), con el astrónomo solitario encima
o4 = objeto(3, 'obj_armario', -12, OBJS)
AW, AD, AH, AP = 0.4, 0.25, 0.96, 0.035
for j, (px, py) in enumerate(((-0.17, -0.1), (0.17, -0.1), (-0.17, 0.1), (0.17, 0.1))):
    bb.caja(f'arm_pata_{j}', (0.028, 0.028, AP), (px, py, AP / 2), OBJ, o4)
bb.caja('arm_cuerpo', (AW, AD, AH), (0, 0, AP + AH / 2), PAPEL, o4, bevel=0.003)
bb.caja('arm_cornisa', (AW + 0.06, AD + 0.04, 0.026), (0, 0, AP + AH + 0.013), OBJ, o4, bevel=0.004)
bb.caja('arm_zocalo', (AW + 0.02, AD + 0.02, 0.03), (0, 0, AP + 0.015), OBJ, o4, bevel=0.003)
xa, ya, z0a, z1a = AW / 2, AD / 2, AP + 0.03, AP + AH
for sx in (-1, 1):
    for sy in (-1, 1):
        tubo(f'arm_arista_{sx}{sy}', [(sx * xa, sy * ya, z0a), (sx * xa, sy * ya, z1a)], 0.004, OBJ, o4, segs=6)
yf = -ya - 0.002
for j, sx in enumerate((-1, 1)):                # dos puertas: contornos grabados
    x0, x1 = sx * 0.012, sx * (xa - 0.03)
    tubo(f'arm_puerta_{j}', [(x0, yf, z0a + 0.04), (x1, yf, z0a + 0.04), (x1, yf, z1a - 0.04), (x0, yf, z1a - 0.04)], 0.0028, TINTA, o4,
         cerrado=True, segs=6)
    tubo(f'arm_tablero_{j}', [(x0 + sx * 0.03, yf, z0a + 0.09), (x1 - sx * 0.03, yf, z0a + 0.09), (x1 - sx * 0.03, yf, z1a - 0.09),
                              (x0 + sx * 0.03, yf, z1a - 0.09)], 0.002, TINTA, o4, cerrado=True, segs=6)
    cil(f'arm_tirador_{j}', 0.009, 0.012, (sx * 0.03, yf + 0.001, z0a + AH * 0.5), OBJ, o4, segs=12).rotation_euler = (RAD(90), 0, 0)
carlos = [(0.09, 0.0), (0.086, 0.15), (0.074, 0.178), (0.082, 0.2), (0.084, 0.226), (0.072, 0.25), (0.052, 0.258),
          (0.033, 0.248), (0.026, 0.226), (0.033, 0.202), (0.045, 0.188), (0.032, 0.172), (0.024, 0.12),
          (0.02, 0.062), (-0.012, 0.058), (-0.028, 0.046), (-0.033, -0.1), (-0.064, -0.112), (-0.066, -0.128),
          (-0.008, -0.128), (-0.004, -0.1), (0.0, 0.0)]
placa('arm_astronomo', [(x * 1.2, z * 1.2) for x, z in carlos], 0.03, (-0.14, 0.0, AP + AH + 0.026), OBJ, o4)
fusionar(o4, 'armario_malla')

# --- Snte.⁵: el lugar vacío «por venir» (contorno punteado fino sobre un plinto que espera)
o5 = objeto(4, 'obj_por_venir', -12, OBJS)
caja_punteada('venir_contorno', (0.3, 0.3, 0.5), (0, 0, 0.25), FANT, o5)
fusionar(o5, 'por_venir_malla')

# ---------------------------------------------------------------- lectura deceptiva: los objetos de Abreu
# «seis cucharas, un vaso, quizá un plato, un ojo sobre una piel» (l. 262-267): dibujados en grafito, sin centro
a1 = objeto(0, 'abreu_cucharas', -20, ABREU)
for j in range(6):
    cu = bb.grupo(f'cuchara_{j}', (0, 0, 0), a1)
    cu.rotation_euler = (0, 0, RAD(-150 + 26 * j))
    bb.caja(f'cuchara_{j}_mango', (0.16, 0.013, 0.005), (0.11, 0, 0.0045), OBJ, cu, bevel=0.002)
    bo = cil(f'cuchara_{j}_pala', 0.028, 0.007, (0.215, 0, 0.001), OBJ, cu, segs=24)
    bo.scale = (1.45, 1.0, 1.0)
fusionar(a1, 'cucharas_malla')

a2 = objeto(1, 'abreu_vaso', 0, ABREU)
torno('vaso', [(0, 0.0), (0.062, 0.0), (0.066, 0.004), (0.084, 0.22), (0.077, 0.22), (0.058, 0.012), (0, 0.012)], OBJ, a2, segs=48)
tubo('vaso_labio', circulo(0.0805, 48, 0.22), 0.0045, OBJ, a2, cerrado=True, segs=6)
fusionar(a2, 'vaso_malla')

a3 = objeto(2, 'abreu_plato', -12, ABREU)
pl = bb.grupo('plato', (0, 0.03, 0.0), a3)
pc = bb.grupo('plato_cara', (0, 0, 0.19), pl)
pc.rotation_euler = (RAD(68), 0, 0)             # apoyado de canto, de cara a quien mira
torno('plato_malla0', [(0, 0.0), (0.075, 0.0), (0.075, 0.008), (0.19, 0.028), (0.186, 0.034), (0.07, 0.016), (0, 0.016)], PAPEL, pc, segs=64)
tubo('plato_filo', circulo(0.188, 72, 0.031), 0.0042, TINTA, pc, cerrado=True, segs=6)       # el plato, dibujado: filo y fondo
tubo('plato_fondo', circulo(0.085, 56, 0.0175), 0.0026, TINTA, pc, cerrado=True, segs=6)
tubo('plato_atril', [(-0.07, 0.2, 0.0), (0.0, 0.085, 0.25), (0.07, 0.2, 0.0)], 0.005, OBJ, pl, segs=6)
bb.caja('plato_repisa', (0.24, 0.035, 0.012), (0, -0.075, 0.006), OBJ, pl, bevel=0.003)
fusionar(a3, 'plato_malla')

a4 = objeto(3, 'abreu_ojo', -12, ABREU)
pz = bb.grupo('piel', (0, 0.02, 0.2), a4)
pz.rotation_euler = (RAD(-22), 0, 0)             # la piel, apenas reclinada sobre un atril
piel_pts = []
for j in range(72):
    t = 2 * math.pi * j / 72
    rr = 1 + 0.1 * math.sin(4 * t + 0.5) + 0.05 * math.sin(7 * t + 1.3)
    piel_pts.append((0.24 * rr * math.cos(t), 0.17 * rr * math.sin(t)))
placa('piel_malla0', piel_pts, 0.01, (0, 0, 0), PIEL, pz)
tubo('piel_contorno', [(x, -0.0055, z) for x, z in piel_pts], 0.0032, TINTA, pz, cerrado=True, segs=6)
yo = -0.007
alm_sup = [(0.13 * math.cos(RAD(a)), yo, 0.06 * math.sin(RAD(a))) for a in range(180, -1, -10)]
alm_inf = [(0.13 * math.cos(RAD(a)), yo, 0.045 * math.sin(RAD(a))) for a in range(180, 361, 10)]
tubo('ojo_parpado_sup', alm_sup, 0.0042, TINTA, pz, segs=6)
tubo('ojo_parpado_inf', alm_inf, 0.0042, TINTA, pz, segs=6)
tubo('ojo_iris', circulo(0.034, 40, yo, plano='XZ'), 0.0032, TINTA, pz, cerrado=True, segs=6)
cil('ojo_pupila', 0.015, 0.004, (0, yo + 0.001, 0), TINTA, pz, segs=24).rotation_euler = (RAD(90), 0, 0)
tubo('piel_atril', [(-0.1, 0.2, 0.0), (0.0, 0.08, 0.3), (0.1, 0.2, 0.0)], 0.005, OBJ, a4, segs=6)
bb.caja('piel_repisa', (0.3, 0.035, 0.012), (0, -0.085, 0.006), OBJ, a4, bevel=0.003)
fusionar(a4, 'ojo_malla')

# ---------------------------------------------------------------- tablillas Snte.ⁿ (estados 4-5, vista cenital)
for n in range(5):
    g = bb.grupo(f'tab{n + 1}', (0, 0, 0), BASES[n])
    if n < 4:
        bb.caja(f'tab{n + 1}_placa', (0.56, 0.26, 0.016), (0, 0, 0.008), PAPEL, g, bevel=0.004)
        colocar(palabra(f'tab{n + 1}_letras', 'Snte.', 0.19, TINTA, sup=str(n + 1), extr=0.003), g, (0, 0, 0.0195))
    else:   # la quinta, fantasma: la tablilla que todavía no llega
        for i, (a, b) in enumerate((((-0.28, -0.13), (0.28, -0.13)), ((0.28, -0.13), (0.28, 0.13)), ((0.28, 0.13), (-0.28, 0.13)),
                                    ((-0.28, 0.13), (-0.28, -0.13)))):
            bb.polilinea_punteada(f'tab5_borde{i}', [(a[0], a[1], 0.006), (b[0], b[1], 0.006)], 0.045, 0.03, 0.0045, FANT, g)
        colocar(palabra('tab5_letras', 'Snte.', 0.19, FANT, sup='5', extr=0.003), g, (0, 0, 0.006))
    fusionar(g, f'tab{n + 1}_malla')
    TABS.append(g)


# ---------------------------------------------------------------- posiciones en el mundo (órbita tendida)
def mundo_base(n, k=0.0, z=0.0):
    x, y = P(TH_S[n], k, F_N)
    return Vector((x, y, z))


# ---------------------------------------------------------------- lectura radial (estado 2): de cada objeto, hacia el hueco
# «órbita de cuya lectura —lectura radial— podemos inferirlo» (l. 215-217): los rayos apuntan al significante ausente
RAYOS2 = []
ALT_R = [0.5, 0.52, 0.5, 0.62]
HUECO = Vector((0, 0, PT + SNTE_Z0))
for n in range(4):
    a = mundo_base(n, 0, ALT_R[n])
    dxy = Vector((-a.x, -a.y, 0)).normalized()
    b = HUECO - dxy * 0.42
    g = rayo(f'rayo_radial_{n + 1}', tuple(a + dxy * 0.2), tuple(b), r=0.0075, punta=True)
    fusionar(g, f'rayo_radial_{n + 1}_malla')
    RAYOS2.append(g)

# ---------------------------------------------------------------- lectura deceptiva (estado 3): rayos que no convergen
RAYOS3 = []
R_FIN = [0.95, 0.8, 1.02, 0.78]        # distancia al eje a la que se detiene cada rayo
DESV = [0.0, 0.0, 0.15, 0.0]           # el 3.º, casi en la visual de la cámara, se desvía un poco para no verse de punta
H_FIN = [0.18, 0.46, 0.3, 0.38]        # alturas finales, todas distintas
H_INI = [0.08, 0.26, 0.26, 0.24]       # cada rayo nace en su objeto (cucharas, vaso, plato, ojo)
for n in range(4):
    base = mundo_base(n, 0, 0.0)
    u = Vector((-base.x, -base.y, 0)).normalized()
    pp = Vector((-u.y, u.x, 0))
    a = base + u * 0.2 + Vector((0, 0, PT + H_INI[n]))
    b = -u * R_FIN[n] + pp * DESV[n] + Vector((0, 0, H_FIN[n]))
    g = rayo(f'rayo_deceptivo_{n + 1}', tuple(a), tuple(b), r=0.0075, punta=True)
    fusionar(g, f'rayo_deceptivo_{n + 1}_malla')
    RAYOS3.append(g)

# ---------------------------------------------------------------- Kepler (estado 5): la órbita, tendida en el piso junto a la figura
E_K = 0.55                                       # la elipse del calco (inscrita en el círculo, como en Kepler)
A_K = 0.95
KX, KY = float(os.environ.get('KX', 4.35)), float(os.environ.get('KY', 1.55))
kep = bb.grupo('kepler', (KX, KY, PISO))
kep_orb = tubo('kepler_orbita', circulo(A_K, 128, 0.012), 0.0085, KORB, kep, cerrado=True, segs=8)
kep_sol = bb.grupo('kepler_sol', (0, 0, 0), kep)
cil('kepler_sol_disco', 0.05, 0.01, (0, 0, 0.004), ORO, kep_sol, segs=40)
for j in range(12):
    a = 2 * math.pi * j / 12
    r0, r1 = 0.068, (0.108 if j % 2 else 0.095)
    tubo(f'kepler_sol_rayo_{j}', [(r0 * math.cos(a), r0 * math.sin(a), 0.008), (r1 * math.cos(a), r1 * math.sin(a), 0.008)], 0.004, ORO,
         kep_sol, segs=6)
fusionar(kep_sol, 'kepler_sol_malla')
kep_vac = bb.grupo('kepler_foco_vacio', (0, 0, 0), kep)
# el anillo del foco vacío es más ancho que el sol: con el círculo lo rodea (los dos focos coinciden) y se ve siempre
tubo('kepler_foco_vacio_anillo', circulo(0.125, 64, 0.009), 0.0055, VACIO_K, kep_vac, cerrado=True, segs=8)
fusionar(kep_vac, 'kepler_foco_vacio_malla')
S.etiqueta('kepler', 'Kepler, <em>Astronomia nova</em> (1609)', (0, -A_K * math.sqrt(1 - E_K ** 2) - 0.28, 0.02), kep, '')
S.etiqueta('kep_sol', 'sol', (0, 0.24, 0.02), kep_sol, 'nota')
S.etiqueta('kep_vacio', 'foco vacío', (0, -0.24, 0.02), kep_vac, 'nota')

# ---------------------------------------------------------------- rótulos HTML (pocos, breves)
# estado 1: los nombres de Carpentier, en carmín (cita), junto a cada objeto
NOM = ['reloj de sol', 'balanza', 'telescopio', 'armario']
POS_NOM = [(-0.34, -0.05, 0.62), (0.0, 0.0, 0.98), (0.0, 0.0, 0.98), (0.0, 0.0, 1.52)]
for n in range(4):
    S.etiqueta(f'n{n + 1}', f'<span style="{MAG}">{NOM[n]}</span>', POS_NOM[n], OBJS[n], 'nota')
S.etiqueta('e_desorden', '«desorden»', (0, -0.36, 0.02), sdo_g, 'sdo')
S.etiqueta('e_vacio', 'ningún Sdo.', (0, -0.5, 0.0), estela, 'grande')
LECT = ['Banquete', 'Ojo Profiláctico', 'Primitivismo', 'Ritualidad']
S.etiqueta('lecturas', '<span style="display:inline-block;line-height:1.55;text-align:center">' +
           '<br>'.join(f'<s>«{w}»</s>' for w in LECT) + '</span>', (0, -1.2, 0.0), None, 'nota')
S.etiqueta('e_sdo_foco', '<span style="color:var(--oro)">foco presente</span>', (0, -0.3, 0.0), plinto_e, 'nota')
S.etiqueta('e_snte_foco', '<span style="color:var(--bermellon)">foco ausente</span>', (0, 0, 0), None, 'nota')
S.etiqueta('cita1974', 'lectura posterior · Sarduy 1974, cit. por Díaz 2011', (0, -1.25, 0.0), None, 'nota')

# ================================================================ línea de tiempo
# estado 0 → 1: la figura se tiende en el espacio
clave(orb, 0, loc=(0, 0, Z0), rot=(RAD(90), 0, 0), interp=C)
clave(orb, T_TEND0, loc=(0, 0, Z0), rot=(RAD(90), 0, 0))
clave(orb, T_TEND1, loc=(0, 0, Z_ARC), rot=(0, 0, 0))
clave(estela, 0, loc=(X_FIG, 0, Z0 - FR_H / 2), interp=C)
clave(estela, T_TEND0, loc=(X_FIG, 0, Z0 - FR_H / 2))
clave(estela, T_TEND1, loc=(0, 0, PT))
for ob in FIG_TXT:
    ver(ob, (T_TEND0, 0.4, 1.0, TINY), inicial=1.0)


# el arco (y todo lo que va sobre él) se deforma en el estado 4: shape key lineal
def clave_forma(kb, t, v, interp=L):
    kb.value = v
    kb.keyframe_insert('value', frame=S.f(t))
    ad = kb.id_data.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        for k in fc.keyframe_points:
            if abs(k.co[0] - S.f(t)) < 0.5:
                k.interpolation = interp


clave_forma(forma_elipse, 0, 0.0)
clave_forma(forma_elipse, TM0, 0.0)
clave_forma(forma_elipse, TM1, 1.0)
a0 = ang(TH1, 0)
x, y = P(TH1, 0)
clave(flecha, 0, loc=(x, y, 0), rot=(0, 0, a0), interp=C)
for t, k in muestras(TM0, TM1):
    x, y = P(TH1, k)
    clave(flecha, t, loc=(x, y, 0), rot=(0, 0, desenrollar(ang(TH1, k), a0)), interp=L)


def pos_etc(k):
    x, y = P(TH_ETC, k, 1.0 + 0.3 / ejes(k)[0])
    return (x + 0.12, y, 0.0)


# «etc.» sigue de cara a quien mira mientras la figura se tiende (de pie en los estados 1-3) y se acuesta en el 4
Z_ETC = TXT * 0.42
clave(etc_txt, 0, loc=pos_etc(0), rot=(0, 0, 0), interp=C)
clave(etc_txt, T_TEND0, loc=pos_etc(0), rot=(0, 0, 0))
clave(etc_txt, T_TEND1, loc=pos_etc(0)[:2] + (Z_ETC,), rot=(RAD(90), 0, RAD(-12)))
clave(etc_txt, T3F, loc=pos_etc(0)[:2] + (Z_ETC,), rot=(RAD(90), 0, RAD(-12)))
clave(etc_txt, T4P, loc=pos_etc(0), rot=(0, 0, 0))
for t, k in muestras(TM0, TM1):
    clave(etc_txt, t, loc=pos_etc(k), rot=(0, 0, 0), interp=L)
for n, g in enumerate(BASES):
    x, y = P(TH_S[n], 0, F_N)
    clave(g, 0, loc=(x, y, PT - Z_ARC), interp=C)
    for t, k in muestras(TM0, TM1):
        x, y = P(TH_S[n], k, F_N)
        clave(g, t, loc=(x, y, PT - Z_ARC), interp=L)

# estado 1 · la cadena: aparecen los eslabones, uno tras otro
ver(plinto_e, (0.2, 0.8, TINY, 1.0))
for n, g in enumerate(BASES):
    t0 = 0.35 + 0.2 * n
    ver(g, (t0, t0 + 0.5, TINY, 1.0))
for n, o in enumerate(OBJS[:4]):
    ver(o, (T2 + 0.02 + 0.03 * n, T2 + 0.28 + 0.03 * n, 1.0, TINY), inicial=1.0)
ver(OBJS[4], (T3F, T3F + 0.25, 1.0, TINY), inicial=1.0)

# estado 2 · lectura radial
for n, g in enumerate(RAYOS2):
    t0 = 2.3 + 0.2 * n
    ver(g, (t0, t0 + 0.6, (TINY, 1, 1), 1.0), (T2, T2 + 0.15, 1.0, (TINY, 1, 1)), (T2 + 0.15, T2 + 0.18, (TINY, 1, 1), T3))

# estado 3 · lectura deceptiva: otra cadena de objetos (Abreu), otros rayos
for n, g in enumerate(ABREU):
    t0 = T2 + 0.2 + 0.05 * n
    ver(g, (t0, t0 + 0.5, TINY, 1.0), (T3F, T3F + 0.25, 1.0, TINY))
for n, g in enumerate(RAYOS3):
    t0 = T2 + 0.5 + 0.08 * n
    ver(g, (t0, t0 + 0.35, (TINY, 1, 1), 1.0), (T3F, T3F + 0.12, 1.0, (TINY, 1, 1)), (T3F + 0.12, T3F + 0.15, (TINY, 1, 1), T3))
# sin Sdo. no hay fracción: la tablilla y la barra se van y el hueco baja al plinto vacío (no queda flotando)
ver(sdo_g, (T2 + 0.03, T2 + 0.3, 1.0, TINY), (T3F + 0.05, T4P, TINY, 1.0), inicial=1.0)
ver(barra, (T2 + 0.03, T2 + 0.3, 1.0, TINY), inicial=1.0)
SNTE_Z3 = SH / 2 + 0.004                       # el contorno de pie sobre el plinto del centro

# estado 4 · dos focos: las dos tablillas se tienden (se leen desde arriba) y la fracción se desdobla
for n, g in enumerate(TABS):
    ver(g, (T3F + 0.15 + 0.04 * n, T4P, TINY, 1.0))
FLAT = (RAD(-90), 0, 0)
clave(sdo_g, 0, loc=(0, 0, 0), rot=(0, 0, 0), interp=C)
clave(sdo_g, T3F + 0.04, loc=(0, 0, 0), rot=(0, 0, 0), interp=C)
clave(sdo_g, T3F + 0.05, loc=(0, -SH / 2, SD / 2), rot=FLAT, interp=C)     # vuelve ya tendido (oculto al girar)
clave(plinto_e, 0, loc=(0, 0, 0), interp=C)
clave(snte_g, 0, loc=(0, 0, SNTE_Z0), rot=(0, 0, 0), interp=C)
clave(snte_g, T2 + 0.03, loc=(0, 0, SNTE_Z0), rot=(0, 0, 0))
clave(snte_g, T2 + 0.3, loc=(0, 0, SNTE_Z3), rot=(0, 0, 0))
clave(snte_g, T3F, loc=(0, 0, SNTE_Z3), rot=(0, 0, 0))
Z_SOBRE = SD + 0.012                             # tendido sobre la tablilla del Sdo. (un solo centro)
Z_PISO = PISO + 0.008 - PT                       # tendido en el piso: un corte con filo fino
clave(snte_g, T4P, loc=(0, 0, Z_SOBRE), rot=FLAT)


def z_snte(k):
    return Z_SOBRE + (Z_PISO - Z_SOBRE) * min(1.0, k * 1.6)


for t, k in muestras(TM0, TM1):
    c = ejes(k)[2]
    clave(sdo_g, t, loc=(-c, -SH / 2, SD / 2), rot=FLAT, interp=L)
    clave(plinto_e, t, loc=(-c, 0, 0), interp=L)
    clave(snte_g, t, loc=(c, 0, z_snte(k)), rot=FLAT, interp=L)
    clave(lbl('e_snte_foco'), t, loc=(c, -0.32, PT), interp=L)
clave(lbl('e_snte_foco'), 0, loc=(0, -0.32, PT), interp=C)

# estado 5 · Kepler: aparece la órbita tendida junto a la figura; el deslizador la vuelve elipse
ver(kep, (TK_A0, TK_A1, TINY, 1.0))
clave(kep_orb, 0, esc=1.0, interp=C)
clave(kep_sol, 0, loc=(0, 0, 0), interp=C)
clave(kep_vac, 0, loc=(0, 0, 0), interp=C)
for t, k in muestras(TK0, TK1):
    e = E_K * k
    bk = math.sqrt(1 - e * e)                     # semieje menor relativo; el mayor no cambia (elipse inscrita)
    clave(kep_orb, t, esc=(1.0, bk, 1.0), interp=L)
    clave(kep_sol, t, loc=(-e * A_K, 0, 0), interp=L)
    clave(kep_vac, t, loc=(e * A_K, 0, 0), interp=L)

# ================================================================ encuadres (cámaras calculadas para la zona libre de ambas vistas)
AZ_CAD, EL_CAD = float(os.environ.get('AZ_CAD', -12)), float(os.environ.get('EL_CAD', 32))
AZ_DEC, EL_DEC = float(os.environ.get('AZ_DEC', -12)), float(os.environ.get('EL_DEC', 40))
EL_FOC = float(os.environ.get('EL_FOC', 74))
E_FIG = []
E_CAD = ['n1', 'n2', 'n3', 'n4']
E_RAD = ['e_desorden']
E_DEC = ['e_vacio', 'lecturas']
E_FOC = ['e_sdo_foco', 'e_snte_foco', 'cita1974']
E_KEP = ['kepler', 'kep_sol', 'kep_vacio']

# calcos del piso (docs/3d/decor/proliferacion.json): el encuadre los incluye para que ningún borde quede cortado
W_LAM = float(os.environ.get('W_LAM', 3.3))      # calco-lamina, bajo el arco (estado 1)
W_PLA = float(os.environ.get('W_PLA', 5.4))      # calco-planta-oval, bajo la elipse (estado 4)
W_ORB = A_K / 0.3751                             # calco-orbita, bajo la órbita de Kepler (estado 5)
X_LAM = [(Vector((sx * W_LAM * 0.47, sy * W_LAM * 0.747 * 0.47, PISO)), 0.0, 0.0) for sx in (-1, 1) for sy in (-1, 1)]
X_PLA = piso_elipse(0, 0, W_PLA * 0.485, W_PLA * 0.475)
X_ORB = piso_elipse(KX, KY, W_ORB * 0.44, W_ORB * 0.44)

# figura de pie, de frente y casi ortogonal; la cámara queda apenas por debajo del suelo invisible del visor
FRENTE = encuadre('figura', 0, E_FIG, 0, -3.0, 7.0, look0=(0, 0, 1.4), dist=39.5, tarjeta=TARJ[0], sesgo=0.4)
# Cadena y Lectura radial comparten cámara (entre ambas no hay motivo para moverla)
CADENA = encuadre('cadena', T2, sorted(set(E_CAD + E_RAD)), AZ_CAD, EL_CAD, 34, extra=X_LAM, tarjeta=TARJ[2])
RADIAL = dict(CADENA)
DECEP = encuadre('deceptiva', T3F, E_DEC, AZ_DEC, EL_DEC, 34, tarjeta=TARJ[3])
# dos focos: vista casi cenital (la elipse ha de leerse como deformación de la figura, no como perspectiva)
FOCOS = encuadre('focos', TM1, E_FOC, 0, EL_FOC, 34, extra=X_PLA, tarjeta=TARJ[4])
KEPLER = encuadre('kepler', TK1, E_KEP + ['e_sdo_foco', 'e_snte_foco'], 0, EL_FOC, 34, extra=X_ORB, tarjeta=TARJ[5])

# ================================================================ estados
S.estado('Figura 2',
         'El significante de un significado dado queda tachado; una cadena de significantes, que progresa metonímicamente, traza una órbita a su alrededor. En la figura, el arco queda <b>abierto</b>: etc.',
         'Sarduy 1972 · figura 2 (l. 211-228)', etiquetas=E_FIG, orbita=False, t1=0, **FRENTE)
S.estado('Cadena',
         'Carpentier, <em>El siglo de las luces</em>: reloj de sol vuelto reloj de luna, balanza para pesar gatos, telescopio por una luceta rota, astrónomo sobre un armario. La cadena sigue abierta.',
         'l. 230-239', etiquetas=E_CAD, t1=T1, **CADENA)
S.estado('Lectura radial',
         'De cada objeto la lectura vuelve al centro: el significado, «desorden», está presente; su significante nunca se escribe. Se infiere.',
         'l. 211-217 · l. 230-233 · rayos: añadido didáctico', etiquetas=E_RAD, t1=T2,
         pregunta='¿Y si las lecturas no convergieran en ningún centro?', **RADIAL)
S.estado('Lectura deceptiva',
         'Abreu, <em>Mampulorio</em>: cucharas, un vaso, un ojo sobre una piel. Las lecturas no convergen: los significantes, en vez de completarse, se anulan unos a otros. El centro no se llena.',
         'l. 255-275', etiquetas=E_DEC,
         t1=T3F, **DECEP)
S.estado('Dos focos',
         'Lectura posterior: el significante tachado se vuelve un segundo centro, ausente, junto al significado. El círculo se deforma en elipse, que sigue abierta.',
         'Sarduy 1974, cit. por Díaz 2011 (l. 1470-1483)',
         etiquetas=E_FOC, t1=TM1,
         slider={'tipo': 'tiempo', 't0': TM0, 't1': TM1, 'etiqueta': 'excentricidad',
                 'min_txt': 'círculo: un centro', 'max_txt': 'elipse: dos focos'}, **FOCOS)
S.estado('Kepler',
         'Kepler: el trayecto de los astros, que se suponía circular, pierde su centro único «para hacerse doble». Más tarde Sarduy llamará <em>retombée</em> a este parecido: «isomorfía no contigua».',
         'l. 64-67 · Sarduy 1974, cit. por Díaz 2011, l. 1503-1509',
         etiquetas=E_KEP, t1=TK1,
         slider={'tipo': 'tiempo', 't0': TK0, 't1': TK1, 'etiqueta': 'la órbita de Kepler',
                 'min_txt': 'círculo', 'max_txt': 'elipse'}, **KEPLER)

# ================================================================ control
tri = 0
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ob.data.calc_loop_triangles()
        tri += len(ob.data.loop_triangles)
print(f'[proliferacion] guiones={len(GUIONES)} triángulos={tri} objetos={len(bpy.data.objects)}')
print(f'[proliferacion] calcos: W_LAM={W_LAM:.3f} W_PLA={W_PLA:.3f} W_ORB={W_ORB:.3f} kepler=({KX}, {KY})')
bpy.context.scene.frame_set(0)
S.exportar(posters=os.environ.get('POSTERS', '1') != '0')
