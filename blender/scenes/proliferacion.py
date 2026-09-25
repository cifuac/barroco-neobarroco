"""N2 · Proliferación — del arco abierto a la elipse.
Figura 2 (Sarduy 1972, l. 224-228): en el centro «Snte.» tachado sobre «Sdo.»; alrededor, un arco punteado
ABIERTO (≈ semicircunferencia superior, abierto por abajo) que nace abajo a la izquierda, pasa por Snte.¹…Snte.⁵
y termina en punta de flecha hacia abajo, a la derecha, seguida de «etc.».
Regla: la proliferación nunca se dibuja como anillo cerrado. La elipse de dos focos es lectura posterior
(Sarduy 1974, cit. por Díaz 2011, l. 1470-1483) y se rotula así. La elipse cerrada sólo aparece como miniatura
aparte (Kepler), con otro trazo y sin rótulos Snte.
"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bb
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

random.seed(1972)
S = bb.Escena('proliferacion', 'Proliferación: del arco abierto a la elipse', dur=9)
M = bb.mat
TINY = 0.0001
T3 = (TINY, TINY, TINY)
C = 'CONSTANT'
L = 'LINEAR'


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


def cil(nombre, r, h, loc=(0, 0, 0), mat=None, parent=None, segs=24, r2=None):
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


def punta_x(nombre, r, largo, mat, parent=None, loc=(0, 0, 0), segs=18):
    """Cono con el vértice en el origen y la base hacia -X (punta de flecha que apunta a +X)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=largo)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(-largo / 2, 0, 0), verts=bm.verts)
    ob = bb._obj_from_bm(nombre, bm, mat, parent, loc)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def placa(nombre, pts, esp, loc=(0, 0, 0), mat=None, parent=None, plano='XZ', rot=None):
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
    if rot:
        ob.rotation_euler = rot
    return suave(ob, 30)


def toro(nombre, Rm, r, loc=(0, 0, 0), mat=None, parent=None, nu=96, nv=10, plano='XY'):
    bm = bmesh.new()
    anillos = []
    for i in range(nu):
        u = 2 * math.pi * i / nu
        fila = []
        for j in range(nv):
            v = 2 * math.pi * j / nv
            x = (Rm + r * math.cos(v)) * math.cos(u)
            y = (Rm + r * math.cos(v)) * math.sin(u)
            z = r * math.sin(v)
            fila.append(bm.verts.new((x, y, z) if plano == 'XY' else (x, z, y)))
        anillos.append(fila)
    for i in range(nu):
        for j in range(nv):
            a, b = anillos[i][j], anillos[(i + 1) % nu][j]
            c, d = anillos[(i + 1) % nu][(j + 1) % nv], anillos[i][(j + 1) % nv]
            bm.faces.new((a, b, c, d))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bb._obj_from_bm(nombre, bm, mat, parent, loc)


def caja_punteada(nombre, size, loc, mat, parent=None, guion=0.075, hueco=0.05, r=0.013):
    """Contorno punteado de una caja (12 aristas): un hueco con la forma de lo que falta."""
    g = bb.grupo(nombre, loc, parent)
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    q = [(-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)]
    bb.polilinea_punteada(nombre + '_inf', [(x, y, -sz) for x, y in q + q[:1]], guion, hueco, r, mat, g)
    bb.polilinea_punteada(nombre + '_sup', [(x, y, sz) for x, y in q + q[:1]], guion, hueco, r, mat, g)
    for i, (x, y) in enumerate(q):
        bb.polilinea_punteada(f'{nombre}_v{i}', [(x, y, -sz), (x, y, sz)], guion, hueco, r, mat, g)
    return g


def rayo(nombre, a, b, r=0.013, punta=True, mat=None):
    """Grupo con origen en a y geometría a lo largo de +X local hasta b (crece por escala X desde a)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    Ld = d.length
    g = bb.grupo(nombre, tuple(a))
    g.rotation_euler = (0, -math.asin(d.z / Ld), math.atan2(d.y, d.x))
    lp = 0.11 if punta else 0.0
    barra_x(nombre + '_linea', r, Ld - lp, mat or M('trayecto'), g, centrada=False, segs=10)
    if punta:
        punta_x(nombre + '_punta', r * 3.0, lp, mat or M('trayecto'), g, loc=(Ld, 0, 0))
    return g


from bpy_extras import anim_utils


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



# ================================================================ materiales
NACAR = M('significante')
ORO = M('significado')
BERM = M('ausencia')
CIAN = M('trayecto')
GRAF = M('soporte')
LAM = M('lamina')
FANT = M('fantasma')
CRISTAL = mat_local('cristal', '#B9C6CC', 0.0, 0.08, 0.0, alpha=0.32)
AZOGUE = mat_local('azogue_linea', '#9AA4A8', 0.6, 0.28, 0.9)
VACIO_K = M('ausencia', 'hueco_kepler')   # el foco vacío de Kepler: la misma ausencia (bermellón) que el Snte. tachado
SOL = M('logos')
# el arco es la cadena de significantes: nácar (como en svg/fig2.svg), levemente emisivo para que el punteado se lea
# igual en el plano y tendido; el cian queda reservado a la lectura (rayos radiales/deceptivos)
ARCO = mat_local('arco_nacar', '#CFC6B8', 0.0, 0.45, 0.55)
# ajustes del estudio: el oro menos espejado (el pan de oro no se lee como retícula de facetas), el cristal sin matiz
# celeste (velo de papel: se lee sobre la laca oscura) y el contorno «por venir» con contraste suficiente sobre el papel
S.estudio = {'materiales': {'azogue_linea': {'opacity': 0.995}, 'logos': {'opacity': 0.995},
                            'hueco_kepler': {'opacity': 0.995},
                            'significado': {'roughness': 0.45},
                            'cristal': {'color': '#F4EEE3', 'opacity': 0.24},
                            'fantasma': {'color': '#2F3134', 'opacity': 0.62}}}
MAG = 'color:var(--magenta-claro);font-style:italic'      # palabras citadas de Carpentier / Abreu (cita = magenta)


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


def proy(cam, look, fov, p, W=1920, H=1080):
    f = (look - cam).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f)
    v = Vector(p) - cam
    zc = v.dot(f)
    t = math.tan(math.radians(fov) / 2)
    return ((v.dot(r) / (zc * t * W / H) + 1) / 2 * W, (1 - v.dot(u) / (zc * t)) / 2 * H)


def lbl(clave):
    return bpy.data.objects['lbl_' + clave]


# ---------------------------------------------------------------- encuadre para las dos vistas del visor
# El fov es vertical y común a las dos vistas; en unidades (u, v) = coordenadas de cámara / (z·tan(fov/2)) un punto
# cae en el mismo sitio en ambas; sólo cambian el ancho visible y el tamaño relativo de los rótulos (px fijos).
#   pantalla completa: 1920×1080 · libre x 70-1190, y 125-975 (título arriba; tarjeta desde x≈1229; barra abajo-izq.)
#   incrustado: 1920×904 (bajo la cabecera de 176 px) · libre x 60-1150, y 22-805 (tarjeta desde x≈1180; barra y≥821)
VISTAS = [(1920, 1080, (70, 125, 1190, 975)), (1920, 904, (60, 22, 1150, 805))]
import re


def pad_etq(clave):
    """Semiancho y semialto (px) aproximados del rótulo HTML, según su clase (ver docs/3d/visor.css)."""
    d = S.etiquetas['lbl_' + clave]
    lineas = re.split(r'<br\s*/?>', d['html'])
    lh = 1.25 if 'line-height' in d['html'] else 1.0

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
MARGEN_T = 34      # aire sobre la tarjeta de texto (px)


def encuadre(nombre, t, etiquetas, az, el, fov, extra=(), look0=(0, 0.4, 0.5), dist=10.0, excluir=(), dmax=60.0, sesgo=0.2,
             tarjeta=None):
    """Cámara vista desde azimut/elevación (grados; az=0 → de frente, desde -Y) que encaja lo visible en t
    (mallas + rótulos) en la zona libre de AMBAS vistas, lo más grande posible. En vertical, `sesgo` reparte el margen
    sobrante (0 = arriba del todo, 0,5 = centrado): algo alto, porque en la diapositiva el visor tiene más aire arriba.
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
    tarj = []                                   # por vista: (tope u, tope v) de la esquina de la tarjeta, por punto
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
        """Mayor traslación horizontal que deja todo fuera de la tarjeta, con la vertical tv."""
        for AU, BV in tarj:
            m = tv > BV - s * cv
            if np.any(m):
                hu = min(hu, float(np.min((AU - s * cu)[m])))
        return hu

    def factible(s, cu, cv):
        lu, hu, lv, hv = rect(s, cu, cv)
        if lu > hu or lv > hv:
            return False
        return tope_u(s, cu, cv, lv, hu) >= lu      # la zona libre baja-izquierda: basta probar la esquina (lu, lv)

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
        if tarjeta:
            j = 0 if H == 1080 else 1
            x1, yc = VISTAS[j][2][2], tarjeta[j] - MARGEN_T
            dentro = sum(1 for c, p in zip(cs, pts) if W / 2 + c[0] * h2 + p[1] > x1 + 1 and h2 + c[1] * h2 + p[2] > yc + 1)
            print(f'[encuadre] {nombre} {W}x{H}: puntos sobre la tarjeta = {dentro}')
    print(f'[encuadre] {nombre}: cam={tuple(round(c, 2) for c in cam)} look={tuple(round(c, 2) for c in look)} dist={dist:.2f}')
    return dict(cam=tuple(cam), look=tuple(look), fov=fov)


# ================================================================ geometría del arco (figura 2)
R = 1.8                                          # radio del arco
TH0, TH1 = math.radians(194), math.radians(-15)  # nace abajo-izq., termina abajo-der. (medido sobre el escaneo)
E_FIN = 0.6                                      # excentricidad final (lectura 1974; el PLAN admite 0-0,6)
A_FIN = 1.2 * R
Z0 = 0.9            # altura del centro del arco en la figura plana (estado 0)
ZARC = 0.06         # altura del arco tendido (a ras de los plintos)


B_FIN = A_FIN * math.sqrt(1 - E_FIN ** 2)


def ejes(k):
    """Semiejes y distancia focal para la mezcla k (0 = círculo, 1 = elipse e=0,5). Lineal en k, como la shape key."""
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
T_TEND0, T_TEND1 = 0.05, 0.95          # la figura se tiende en el espacio (breve: el visor muestra los rótulos al entrar)
T1 = 1.75                              # fin estado 1 (cadena)
T2 = 4.0                               # fin estado 2 (lectura radial)
# Tramos cortos a partir del estado 2: el visor anima la línea de tiempo con ease-in-out durante |Δt| s y enciende
# los rótulos del estado nuevo al entrar; con tramos breves, geometría y rótulos llegan casi a la vez.
T3F = 5.1                              # fin estado 3 (lectura deceptiva)
T4P = T3F + 0.2                        # fin del preludio del estado 4 (se recogen rayos, vuelve el Sdo.)
TM0, TM1 = 5.35, 6.85                  # deformación círculo → elipse (deslizador)
TK_A0, TK_A1 = 6.85, 7.15              # aparece la miniatura de Kepler
TK0, TK1 = 7.25, 8.25                  # Kepler: círculo → elipse (deslizador)
NS = 8                                 # muestras de la deformación


def muestras(t0, t1):
    return [(t0 + (t1 - t0) * j / NS, j / NS) for j in range(NS + 1)]


# ---------------------------------------------------------------- órbita: grupo del arco (plano local XY)
orb = bb.grupo('orbita', (0, 0, Z0))

DASH, GAP, RT = 0.19, 0.12, 0.024
L_FL, R_FL = 0.22, 0.07
s_fin = R * (TH0 - TH1) - L_FL
GUIONES = []
s = 0.0
while s < s_fin - 0.04:
    e = min(s + DASH, s_fin - 0.035)
    GUIONES.append((TH0 - ((s + e) / 2) / R, e - s))
    s = e + GAP


def lugar_guion(c, th, k):
    x, y = P(th, k)
    a = ang(th, k)
    T = Vector((math.cos(a), math.sin(a), 0))
    N = Vector((-T.y, T.x, 0))
    return Vector((x, y, 0)) + T * c.z + N * c.x + Vector((0, 0, c.y))


bm = bmesh.new()
regs = []
for th, lg in GUIONES:
    geo = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=RT, radius2=RT, depth=lg)
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
TH_ETC = math.radians(-1)
S.etiqueta('etc', 'etc.', (0, 0, 0), orb, 'grande snte')

# ---------------------------------------------------------------- estela central: la fracción Snte./Sdo.
BW, BD, BH = 0.84, 0.16, 0.36
estela = bb.grupo('estela', (0.1 * R, 0, Z0 - BH / 2))
plinto_e = bb.grupo('estela_plinto', (0, 0, 0), estela)
bb.caja('estela_plinto_malla', (1.12, 0.46, 0.06), (0, 0, -0.03), GRAF, plinto_e, bevel=0.012)
sdo_g = bb.grupo('sdo', (0, 0, 0), estela)
bb.caja('sdo_bloque', (BW, BD, BH), (0, 0, BH / 2), ORO, sdo_g, bevel=0.03)
barra = bb.caja('barra', (BW * 1.25, 0.07, 0.035), (0, 0, BH + 0.05), M('soporte', 'grafito_barra'), estela, bevel=0.01)
SNTE_Z0 = BH + 0.1 + BH / 2
snte_g = bb.grupo('snte_ausente', (0, 0, SNTE_Z0), estela)
caja_punteada('snte_hueco', (BW, BD, BH), (0, 0, 0), BERM, snte_g)
# trazo de tachadura casi paralelo al del rótulo HTML (-8°), para que en la figura plana no se crucen en X
bb.cilindro_entre('snte_tachadura', (-BW * 0.62, -BD / 2 - 0.02, -BH * 0.2), (BW * 0.62, -BD / 2 - 0.02, BH * 0.2),
                  r=0.016, material=BERM, parent=snte_g, segs=10)
fusionar(snte_g, 'snte_ausente_malla')

S.etiqueta('e_snte', '<s>Snte.</s>', (0, -0.2, 0), snte_g, 'grande tachado')
S.etiqueta('e_sdo', 'Sdo.', (0, -0.2, BH / 2), sdo_g, 'grande sdo')
S.etiqueta('e_desorden', 'Sdo. «desorden»', (0, -0.2, BH / 2), sdo_g, 'grande sdo')
S.etiqueta('e_sdo_foco', '<span style="display:inline-block;line-height:1.22">Sdo.<br>foco presente</span>', (0.15, -0.64, 0.0), sdo_g, 'sdo')        # al pie del foco, en la vista cenital (a la derecha: aire respecto al arranque del arco)
S.etiqueta('e_snte_foco', '<span style="display:inline-block;line-height:1.22"><s>Snte.</s><br>foco ausente</span>', (-0.3, 0.6, 0.0), snte_g, 'tachado')   # arriba: con el círculo, no pisa al del Sdo.
S.etiqueta('cita1974', '<span style="display:inline-block;line-height:1.3;color:var(--azogue)">lectura posterior<br>Sarduy 1974, cit. por Díaz 2011</span>', (0, -1.3, 0.1), orb, 'nota')   # en el lado abierto, abajo
S.etiqueta('e_vacio', 'ningún Sdo.', (0, -0.55, 0.0), estela, 'grande')
S.etiqueta('e3_snte', '<s>Snte.</s>', (0, 0, BH / 2 + 0.24), snte_g, 'grande tachado')
S.etiqueta('e1_snte', '<s>Snte.</s>', (BW / 2 + 0.3, -BD / 2, 0.0), snte_g, 'grande tachado')   # a la derecha del hueco (vista oblicua)
S.etiqueta('e3_sdo', 'Sdo.', (0, -0.62, 0.0), sdo_g, 'grande sdo')
S.etiqueta('e3_desorden', 'Sdo. «desorden»', (0, -0.62, 0.0), sdo_g, 'grande sdo')

# ---------------------------------------------------------------- la cadena: plintos sobre el arco
ANG_SNTE = [180, 145, 100, 55, 22]          # posiciones de Snte.¹…⁵ sobre el arco (figura 2)
TH_S = [math.radians(a) for a in ANG_SNTE]
PL_R = [0.33, 0.4, 0.47, 0.44, 0.36]        # radio del plinto de cada eslabón
F_N = [(R + PL_R[n] + 0.1) / R for n in range(5)]   # los objetos quedan justo por fuera del arco
BASES, OBJS, TABS = [], [], []
for n in range(5):
    g = bb.grupo(f'eslabon{n + 1}', (0, 0, 0), orb)
    x, y = P(TH_S[n], 0, F_N[n])
    g.location = (x, y, -ZARC)
    cil(f'eslabon{n + 1}_plinto', PL_R[n], 0.06, (0, 0, -0.06), GRAF, g, segs=48)
    BASES.append(g)


def objeto(n, nombre, yaw):
    g = bb.grupo(nombre, (0, 0, 0), BASES[n])
    g.rotation_euler = (0, 0, math.radians(yaw))
    OBJS.append(g)
    return g


# --- Snte.¹: reloj de sol convertido en reloj de luna
o1 = objeto(0, 'obj_reloj', -15)
bb.caja('reloj_zocalo', (0.4, 0.4, 0.06), (0, 0, 0.03), NACAR, o1, bevel=0.012)
cil('reloj_columna', 0.085, 0.5, (0, 0, 0.06), NACAR, o1, segs=28, r2=0.07)
cil('reloj_capitel', 0.13, 0.04, (0, 0, 0.56), NACAR, o1, segs=32)
cil('reloj_cuadrante', 0.3, 0.035, (0, 0, 0.6), NACAR, o1, segs=64)
ZD = 0.635
for h in range(11):
    a = math.radians(180 + 18 * h)            # horas «invertidas»: las marcas van por la mitad delantera
    tk = bb.caja(f'reloj_hora_{h}', (0.055 if h % 5 else 0.085, 0.012, 0.008), (0.235 * math.cos(a), 0.235 * math.sin(a), ZD + 0.004), GRAF, o1)
    tk.rotation_euler = (0, 0, a)
gn = placa('reloj_gnomon', [(-0.2, 0.0), (0.2, 0.0), (-0.2, 0.19)], 0.014, (0, 0.0, ZD), NACAR, o1)
gn.rotation_euler = (0, 0, math.radians(90))
cre = []
rl, kl = 0.1, 0.45
for j in range(25):
    t = math.radians(90 + 180 * j / 24)
    cre.append((rl * math.cos(t), rl * math.sin(t)))
for j in range(1, 24):
    t = math.radians(-90 + 180 * j / 24)
    cre.append((-kl * rl * math.cos(t), rl * math.sin(t)))
luna = placa('reloj_luna', cre, 0.006, (0.12, -0.1, ZD), GRAF, o1, plano='XY')   # la sombra dibuja una luna
luna.rotation_euler = (0, 0, math.radians(200))
fusionar(o1, 'reloj_malla')

# --- Snte.²: balanza hidrostática (pesa gatos)
o2 = objeto(1, 'obj_balanza', 10)
bb.caja('bal_base', (0.66, 0.28, 0.05), (0, 0, 0.025), NACAR, o2, bevel=0.012)
cil('bal_columna', 0.024, 0.9, (0, 0, 0.05), NACAR, o2, segs=16)
cil('bal_pomo', 0.04, 0.05, (0, 0, 0.95), NACAR, o2, segs=20)
TILT = math.radians(7)                        # el lado del gato pesa más
brazo = bb.grupo('bal_brazo', (0, 0, 0.93), o2)
brazo.rotation_euler = (0, TILT, 0)
bb.caja('bal_cruz', (0.76, 0.028, 0.032), (0, 0, 0), NACAR, brazo, bevel=0.006)
for sgn, nm in ((-1, 'izq'), (1, 'der')):
    ex = sgn * 0.37
    exw = Vector((ex * math.cos(TILT), 0, 0.93 - ex * math.sin(TILT)))
    bot = 0.62 if sgn < 0 else 0.5
    bb.cilindro_entre(f'bal_hilo_{nm}', tuple(exw), (exw.x, 0, bot + 0.02), r=0.006, material=GRAF, parent=o2, segs=6)
    cil(f'bal_platillo_{nm}', 0.13, 0.022, (exw.x, 0, bot), NACAR, o2, segs=32, r2=0.1)
exl = -0.37 * math.cos(TILT)
bb.cilindro_entre('bal_hilo_pesa', (exl, 0, 0.62), (exl, 0, 0.2), r=0.005, material=GRAF, parent=o2, segs=6)
cil('bal_pesa', 0.028, 0.07, (exl, 0, 0.13), NACAR, o2, segs=16)
cil('bal_vaso', 0.085, 0.26, (exl, 0, 0.05), CRISTAL, o2, segs=32)
gato = [(-0.075, 0.0), (-0.07, 0.07), (-0.058, 0.13), (-0.062, 0.165), (-0.074, 0.19), (-0.068, 0.222),
        (-0.07, 0.262), (-0.045, 0.238), (-0.02, 0.24), (-0.004, 0.262), (0.0, 0.215), (-0.006, 0.18),
        (0.03, 0.15), (0.068, 0.09), (0.08, 0.035), (0.11, 0.03), (0.14, 0.06), (0.15, 0.1), (0.162, 0.1),
        (0.158, 0.05), (0.13, 0.008), (0.085, 0.0)]
exr = 0.37 * math.cos(TILT)
placa('bal_gato', [(x * 1.1, z * 1.1) for x, z in gato], 0.05, (exr - 0.02, 0, 0.522), NACAR, o2)
fusionar(o2, 'balanza_malla')

# --- Snte.³: telescopio pequeño sacado por el cristal roto de una luceta
o3 = objeto(2, 'obj_telescopio', 0)
WW, WZ0, WZ1 = 0.76, 0.34, 0.74          # ancho, alféizar, arranque del arco
bb.caja('luc_muro', (WW + 0.08, 0.12, WZ0), (0, 0, WZ0 / 2), NACAR, o3, bevel=0.012)
bb.caja('luc_jamba_i', (0.06, 0.1, WZ1 - WZ0), (-WW / 2 + 0.03, 0, (WZ0 + WZ1) / 2), NACAR, o3, bevel=0.008)
bb.caja('luc_jamba_d', (0.06, 0.1, WZ1 - WZ0), (WW / 2 - 0.03, 0, (WZ0 + WZ1) / 2), NACAR, o3, bevel=0.008)
arco_pts = []
ro, ri = WW / 2, WW / 2 - 0.06
for j in range(33):
    t = math.radians(180 * j / 32)
    arco_pts.append((ro * math.cos(t), WZ1 + ro * math.sin(t)))
for j in range(32, -1, -1):
    t = math.radians(180 * j / 32)
    arco_pts.append((ri * math.cos(t), WZ1 + ri * math.sin(t)))
placa('luc_arco', arco_pts, 0.1, (0, 0, 0), NACAR, o3)
bb.caja('luc_parteluz', (0.025, 0.05, WZ1 - WZ0 + ri), (0.16, 0.02, (WZ0 + WZ1 + ri) / 2), NACAR, o3)
esq = [
    [(-ri, WZ0), (-ri, WZ0 + 0.26), (-0.18, WZ0 + 0.07), (-0.1, WZ0)],
    [(0.16, WZ0), (0.16, WZ0 + 0.3), (ri, WZ0 + 0.22), (ri, WZ0)],
    [(0.16, WZ1 + 0.1), (0.16, WZ1 + 0.3), (0.26, WZ1 + 0.13), (ri, WZ1 + 0.02), (0.24, WZ1 - 0.04)],
    [(-ri, WZ1 - 0.06), (-ri, WZ1 + 0.02), (-0.24, WZ1 + 0.2), (-0.12, WZ1 + ri - 0.02), (-0.2, WZ1 + 0.08), (-0.26, WZ1 - 0.1)],
    [(0.16, WZ0 + 0.3), (0.16, WZ1 + 0.1), (0.24, WZ1 - 0.04), (0.2, WZ0 + 0.36)],
]
for j, pts in enumerate(esq):
    placa(f'luc_esquirla_{j}', pts, 0.008, (0, 0.02, 0), CRISTAL, o3)
tel = bb.grupo('tel', (-0.04, 0.02, 0.72), o3)
tel.rotation_euler = (0, math.radians(10), math.radians(-78))   # el objetivo mira hacia afuera y abajo: a las casas
bb.cilindro_entre('tel_tubo', (-0.42, 0, 0), (0.36, 0, 0), r=0.042, material=NACAR, parent=tel, segs=24)
bb.cilindro_entre('tel_parasol', (0.3, 0, 0), (0.46, 0, 0), r=0.052, material=NACAR, parent=tel, segs=24)
bb.cilindro_entre('tel_ocular', (-0.54, 0, 0), (-0.4, 0, 0), r=0.022, material=GRAF, parent=tel, segs=16)
for j, xx in enumerate((-0.2, 0.08, 0.3)):
    bb.cilindro_entre(f'tel_anillo_{j}', (xx - 0.012, 0, 0), (xx + 0.012, 0, 0), r=0.05, material=GRAF, parent=tel, segs=24)
pie = Vector((0.1, 0.34, 0.66))
for j, (px, py) in enumerate(((0.3, 0.55), (-0.12, 0.62), (0.12, 0.2))):
    bb.cilindro_entre(f'tel_pata_{j}', tuple(pie), (px, py, 0.0), r=0.011, material=GRAF, parent=o3, segs=8)
bb.cilindro_entre('tel_soporte', tuple(pie), (-0.01, 0.14, 0.7), r=0.013, material=GRAF, parent=o3, segs=8)
fusionar(o3, 'telescopio_malla')

# --- Snte.⁴: armario alto, con el astrónomo solitario encima
o4 = objeto(3, 'obj_armario', -12)
AH = 1.34
for j, (px, py) in enumerate(((-0.26, -0.13), (0.26, -0.13), (-0.26, 0.13), (0.26, 0.13))):
    bb.caja(f'arm_pata_{j}', (0.05, 0.05, 0.06), (px, py, 0.03), NACAR, o4)
bb.caja('arm_cuerpo', (0.62, 0.36, AH), (0, 0, 0.06 + AH / 2), NACAR, o4, bevel=0.014)
bb.caja('arm_cornisa', (0.7, 0.42, 0.06), (0, 0, 0.06 + AH + 0.03), NACAR, o4, bevel=0.014)
for j, px in enumerate((-0.148, 0.148)):
    bb.caja(f'arm_puerta_{j}', (0.27, 0.02, AH - 0.2), (px, -0.185, 0.06 + AH / 2), NACAR, o4, bevel=0.008)
    bb.esfera(f'arm_tirador_{j}', 0.016, (math.copysign(0.05, px), -0.205, 0.06 + AH * 0.52), GRAF, o4, subdiv=2)
carlos = [(0.09, 0.0), (0.086, 0.15), (0.074, 0.178), (0.082, 0.2), (0.084, 0.226), (0.072, 0.25), (0.052, 0.258),
          (0.033, 0.248), (0.026, 0.226), (0.033, 0.202), (0.045, 0.188), (0.032, 0.172), (0.024, 0.12),
          (0.02, 0.062), (-0.012, 0.058), (-0.028, 0.046), (-0.033, -0.1), (-0.064, -0.112), (-0.066, -0.128),
          (-0.008, -0.128), (-0.004, -0.1), (0.0, 0.0)]
placa('arm_astronomo', [(x * 1.3, z * 1.3) for x, z in carlos], 0.06, (-0.27, 0.0, 0.06 + AH + 0.06), NACAR, o4)
fusionar(o4, 'armario_malla')

# --- Snte.⁵: contorno vacío «por venir» sobre un plinto que espera
o5 = objeto(4, 'obj_por_venir', 0)
caja_punteada('venir_contorno', (0.46, 0.46, 0.8), (0, 0, 0.4), FANT, o5, guion=0.08, hueco=0.06, r=0.017)
fusionar(o5, 'por_venir_malla')

ALTO = [0.66, 1.0, 1.14, 1.8, 0.8]
# las palabras mismas de la cita (l. 234-239), en magenta: son la voz citada de Carpentier
NOM = ['reloj de sol', 'balanza hidrostática', 'telescopio pequeño', 'armario']
for n, o in enumerate(OBJS):
    if n == 0:   # el reloj queda delante a la izquierda: rótulo al pie, para no tapar la balanza
        S.etiqueta('obj1', f'Snte.<sup>1</sup> · <span style="{MAG}">{NOM[0]}</span>', (-0.05, -0.62, -0.02), o, 'snte')
    elif n < 4:
        S.etiqueta(f'obj{n + 1}', f'Snte.<sup>{n + 1}</sup> · <span style="{MAG}">{NOM[n]}</span>', (0, 0, ALTO[n] + 0.2), o, 'snte')
    else:
        # por encima de la caja (no sobre su cara superior): los guiones del contorno se leen enteros
        S.etiqueta(f'obj{n + 1}', f'Snte.<sup>{n + 1}</sup> · <i style="color:var(--azogue)">por venir</i>', (0.4, 0, ALTO[n] + 0.4), o, 'snte')

# ---------------------------------------------------------------- tablillas genéricas (estados 3-5)
DESORDEN = [(-18, 5), (24, -4), (-10, -6), (16, 6)]      # giro e inclinación en la lectura deceptiva
MAMP = ['seis cucharas', 'un vaso', 'quizá un plato', 'un ojo sobre una piel']   # l. 262-267
for n in range(4):
    g = bb.grupo(f'tab{n + 1}', (0, 0, 0), BASES[n])
    bb.caja(f'tab{n + 1}_placa', (0.52, 0.1, 0.36), (0, 0, 0.18), NACAR, g, bevel=0.02)
    fuera = Vector((math.cos(TH_S[n]), math.sin(TH_S[n]), 0))
    # en la vista cenital (estados 4-5) el rótulo queda por fuera del arco, como en la figura
    # (más lejos cuanto más horizontal: a los lados el rótulo se extiende hacia la tablilla)
    S.etiqueta(f'tab{n + 1}', f'Snte.<sup>{n + 1}</sup>', tuple(fuera * (PL_R[n] + 0.3 + 0.16 * abs(fuera.x)) + Vector((0, 0, 0.2))), g, 'snte')
    S.etiqueta(f'mamp{n + 1}', f'<span style="{MAG}">{MAMP[n]}</span>', tuple(fuera * (PL_R[n] + (0.42 if n < 2 else 0.3)) + Vector((0, 0, 0.1 if n < 2 else 0.3))), g, 'nota')
    TABS.append(g)
fuera5 = Vector((math.cos(TH_S[4]), math.sin(TH_S[4]), 0))
S.etiqueta('tab5', 'Snte.<sup>5</sup>', tuple(fuera5 * (PL_R[4] + 0.3 + 0.16 * abs(fuera5.x)) + Vector((0, 0, 0.2))), o5, 'snte')
S.etiqueta('mamp5', '<i>¿lo que vendría a cerrarla?</i>', (0.86, 0, 0.5), o5, 'snte')   # a la derecha del contorno vacío

# ---------------------------------------------------------------- etiquetas de la figura plana (estado 0)
LBL0 = [(-1.27, 0.0), (-1.1, 0.62), (-0.3, 1.17), (0.73, 1.04), (1.14, 0.57)]   # medidas sobre el escaneo (× R)
for n, (fx, fz) in enumerate(LBL0):
    S.etiqueta(f'snte{n + 1}', f'Snte.<sup>{n + 1}</sup>', (fx * R, -0.3, Z0 + fz * R), clase='grande snte')


# ---------------------------------------------------------------- posiciones en el mundo (órbita tendida)
def mundo_base(n, k=0.0, z=0.0):
    x, y = P(TH_S[n], k, F_N[n])
    return Vector((x, y, z))


# ---------------------------------------------------------------- lectura radial (estado 2): de cada objeto, hacia el hueco
# «órbita de cuya lectura —lectura radial— podemos inferirlo» (l. 215-217): los rayos apuntan al significante ausente
RAYOS2 = []
ALT_R = [0.55, 0.62, 0.62, 0.95]
HUECO = Vector((0, 0, SNTE_Z0))
for n in range(4):
    a = mundo_base(n, 0, ALT_R[n])
    dxy = Vector((-a.x, -a.y, 0)).normalized()
    b = HUECO - dxy * 0.56
    g = rayo(f'rayo_radial_{n + 1}', tuple(a + dxy * (PL_R[n] * 0.75)), tuple(b), r=0.013, punta=True)
    fusionar(g, f'rayo_radial_{n + 1}_malla')
    RAYOS2.append(g)

# ================================================================ línea de tiempo
# estado 0 → 1: la figura se tiende en el espacio
clave(orb, 0, loc=(0, 0, Z0), rot=(math.radians(90), 0, 0), interp=C)
clave(orb, T_TEND0, loc=(0, 0, Z0), rot=(math.radians(90), 0, 0))
clave(orb, T_TEND1, loc=(0, 0, ZARC), rot=(0, 0, 0))
clave(estela, 0, loc=(0.1 * R, 0, Z0 - BH / 2), interp=C)
clave(estela, T_TEND0, loc=(0.1 * R, 0, Z0 - BH / 2))
clave(estela, T_TEND1, loc=(0, 0, 0))


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
x, y = P(TH_ETC, 0, 1.2)
clave(lbl('etc'), 0, loc=(x, y, 0.1), interp=C)
for t, k in muestras(TM0, TM1):
    x, y = P(TH_ETC, k, 1 + (0.36 + 0.18 * k) / ejes(k)[0])
    clave(lbl('etc'), t, loc=(x, y, 0.1), interp=L)
for n, g in enumerate(BASES):
    x, y = P(TH_S[n], 0, F_N[n])
    clave(g, 0, loc=(x, y, -ZARC), interp=C)
    for t, k in muestras(TM0, TM1):
        x, y = P(TH_S[n], k, F_N[n])
        clave(g, t, loc=(x, y, -ZARC), interp=L)

# estado 1 · la cadena: aparecen los eslabones, uno tras otro (pronto: el visor enciende los rótulos al entrar)
ver(plinto_e, (0.2, 0.8, TINY, 1.0))
for n, g in enumerate(BASES):
    t0 = 0.35 + 0.2 * n
    ver(g, (t0, t0 + 0.5, TINY, 1.0))
for n, o in enumerate(OBJS[:4]):
    ver(o, (T2 + 0.02 + 0.03 * n, T2 + 0.28 + 0.03 * n, 1.0, TINY), inicial=1.0)

# estado 2 · lectura radial
for n, g in enumerate(RAYOS2):
    t0 = 2.3 + 0.2 * n
    ver(g, (t0, t0 + 0.6, (TINY, 1, 1), 1.0), (T2, T2 + 0.15, 1.0, (TINY, 1, 1)), (T2 + 0.15, T2 + 0.18, (TINY, 1, 1), T3))

# estado 3 · lectura deceptiva: otra cadena de objetos «vaciados» (tablillas genéricas)
for n, g in enumerate(TABS):
    t0 = T2 + 0.2 + 0.05 * n
    ver(g, (t0, t0 + 0.5, TINY, 1.0))
    yaw, tilt = DESORDEN[n]
    rot_d = (math.radians(tilt), 0, math.radians(yaw))
    clave(g, 0, rot=rot_d, interp=C)
    clave(g, T3F, rot=rot_d)
    clave(g, T4P, rot=(0, 0, 0))
ver(sdo_g, (T2 + 0.03, T2 + 0.3, 1.0, TINY), (T3F, T4P, TINY, 1.0), inicial=1.0)
# sin Sdo. no hay fracción: la barra se va y el hueco tachado baja al plinto vacío (no queda flotando)
ver(barra, (T2 + 0.03, T2 + 0.3, 1.0, TINY), inicial=1.0)
SNTE_Z3 = BH / 2 + 0.015                       # el contorno apoyado sobre el plinto del centro
Y_SNTE4 = 0.45                                 # con el círculo, el hueco queda detrás del Sdo. (arriba en la vista cenital)


def z_snte4(k):
    return BH / 2 + 0.015 + 0.1 * k


# estado 4 · dos focos: la fracción se desdobla; el arco se vuelve elíptico y sigue abierto
clave(sdo_g, 0, loc=(0, 0, 0), interp=C)
clave(plinto_e, 0, loc=(0, 0, 0), interp=C)
clave(snte_g, 0, loc=(0, 0, SNTE_Z0), interp=C)
clave(snte_g, T2 + 0.03, loc=(0, 0, SNTE_Z0))
clave(snte_g, T2 + 0.3, loc=(0, 0, SNTE_Z3))
clave(snte_g, T3F, loc=(0, 0, SNTE_Z3))
for t, k in muestras(TM0, TM1):
    c = ejes(k)[2]
    clave(sdo_g, t, loc=(-c, 0, 0), interp=L)
    clave(plinto_e, t, loc=(-c, 0, 0), interp=L)
    clave(snte_g, t, loc=(c, Y_SNTE4 * (1 - k), z_snte4(k)), interp=L)

# ================================================================ encuadres (cámaras calculadas para la zona libre de ambas vistas)
def ejes_cam(cam, look):
    f = (Vector(look) - Vector(cam)).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    return f, r, r.cross(f)


def desproy(E, x, y, prof):
    """Punto del mundo que se ve en el píxel (x, y) de la vista 1920×1080 a la profundidad `prof` (m) de la cámara E."""
    cam, look = Vector(E['cam']), Vector(E['look'])
    f, r, u = ejes_cam(cam, look)
    wpp = 2 * prof * math.tan(math.radians(E['fov']) / 2) / 1080
    return cam + f * prof + r * ((x - 960) * wpp) - u * ((y - 540) * wpp), wpp


AZ_CAD, EL_CAD = float(os.environ.get('AZ_CAD', -12)), float(os.environ.get('EL_CAD', 34))
AZ_DEC, EL_DEC = float(os.environ.get('AZ_DEC', -12)), float(os.environ.get('EL_DEC', 42))
E_FIG = ['snte1', 'snte2', 'snte3', 'snte4', 'snte5', 'etc', 'e_snte', 'e_sdo']
E_OBJ = ['obj1', 'obj2', 'obj3', 'obj4', 'obj5', 'etc']
# en la vista oblicua el rótulo del Snte. va al lado del hueco: dentro de él, su fondo y la tachadura HTML se cruzaban
# con la barra 3D de tachadura; encima, tapaba el arco y los rayos
E_CAD = E_OBJ + ['e1_snte', 'e3_sdo']
E_RAD = E_OBJ + ['e1_snte', 'e3_desorden']
E_DEC = ['mamp1', 'mamp2', 'mamp3', 'mamp4', 'mamp5', 'etc', 'lect1', 'lect2', 'lect3', 'lect4', 'e3_snte', 'e_vacio']
E_FOC = ['tab1', 'tab2', 'tab3', 'tab4', 'tab5', 'etc', 'e_sdo_foco', 'e_snte_foco', 'cita1974']
E_KEP = ['kepler', 'kep_sol', 'kep_vacio', 'tab1', 'tab2', 'tab3', 'tab4', 'tab5', 'e_sdo_foco', 'e_snte_foco', 'etc']

# figura plana, de frente y casi ortogonal; la cámara queda apenas por debajo del suelo invisible del visor
# (que sólo recibe sombras): visto de canto, ese suelo dibujaría una raya de sombra bajo la figura
FRENTE = encuadre('figura', 0, E_FIG, 0, -3.0, 7.0, look0=(0, 0, 1.4), dist=39.5)
# Cadena y Lectura radial comparten cámara (entre ambas no hay motivo para moverla); la zona libre en L aprovecha
# el espacio sobre la tarjeta (bordes superiores medidos: 684 px a pantalla completa, 549 px incrustado)
CADENA = encuadre('cadena', T2, sorted(set(E_CAD + E_RAD)), AZ_CAD, EL_CAD, 34, tarjeta=(684, 549))
RADIAL = dict(CADENA)

# ---------------------------------------------------------------- lectura deceptiva (estado 3)
# Los mismos rayos radiales del estado 2, pero cada uno se queda corto y a otra altura: no convergen (l. 255-275).
# Delante del lugar vacío del Sdo., la lista de lecturas que se anulan unas a otras, tachadas y en el orden del texto (l. 269-270).
RAYOS3 = []
LECT = ['Banquete', 'Ojo Profiláctico', 'Primitivismo', 'Ritualidad']
# Cada rayo apunta al centro vacío y se detiene antes, a otra altura y en otro punto: no convergen. Ninguno sube
# (en la vista oblicua un rayo que sube parece alejarse del centro) ni termina sobre el arco o junto a otro plinto.
R_FIN = [0.95, 0.8, 1.05, 0.75]        # distancia al eje a la que se detiene cada rayo
DESV = [0.0, 0.0, 0.15, 0.0]           # el 3.º, casi en la visual de la cámara, se desvía un poco para no verse de punta
H_FIN = [0.2, 0.5, 0.3, 0.4]           # alturas finales, todas distintas
for n in range(4):
    base = mundo_base(n, 0, 0.0)
    u = Vector((-base.x, -base.y, 0)).normalized()
    pp = Vector((-u.y, u.x, 0))
    a = base + u * (PL_R[n] * 0.6 + 0.12) + Vector((0, 0, 0.45))     # nace por delante y por encima de la tablilla
    b = -u * R_FIN[n] + pp * DESV[n] + Vector((0, 0, H_FIN[n]))
    g = rayo(f'rayo_deceptivo_{n + 1}', tuple(a), tuple(b), r=0.016, punta=True)
    fusionar(g, f'rayo_deceptivo_{n + 1}_malla')
    RAYOS3.append((g, a, b))
Y_LISTA = [-1.12, -1.56, -2.0, -2.44]   # en el lado abierto del arco, bajo «ningún Sdo.»
PT_LECT = []
for n in range(4):
    pt = Vector((0, Y_LISTA[n], 0.05))
    PT_LECT.append(pt)
    S.etiqueta(f'lect{n + 1}', f'<s>«{LECT[n]}»</s>', tuple(pt), None, 'tachado')
for n, (g, a, b) in enumerate(RAYOS3):
    t0 = T2 + 0.5 + 0.08 * n
    ver(g, (t0, t0 + 0.35, (TINY, 1, 1), 1.0), (T3F, T3F + 0.12, 1.0, (TINY, 1, 1)), (T3F + 0.12, T3F + 0.15, (TINY, 1, 1), T3))

DECEP = encuadre('deceptiva', T3F, E_DEC, AZ_DEC, EL_DEC, 34, tarjeta=(721, 557))

# ---------------------------------------------------------------- dos focos (estado 4): vista casi cenital
# la elipse ha de leerse como deformación de la figura, no como efecto de perspectiva: cámara casi perpendicular al plano
FOCOS = encuadre('focos', TM1, E_FOC, 0, 76, 34)

# ---------------------------------------------------------------- Kepler (miniatura aparte: otro trazo, sin rótulos Snte.)
# Misma cámara que «Dos focos»: la miniatura flota arriba a la derecha, sobre el panel, de cara a la cámara.
E_K = 0.5                                        # la elipse de la miniatura (inscrita en el círculo, como en Kepler)
fK, rK, uK = ejes_cam(FOCOS['cam'], FOCOS['look'])
dK = (Vector(FOCOS['look']) - Vector(FOCOS['cam'])).length * 0.72
# centro en (u, v) = (1,0, -0,5) semialtos y radio 0,3: en ambas vistas queda sobre la tarjeta, con el rótulo encima de ella
KPOS, wppK = desproy(FOCOS, 960 + 1.0 * 540, 540 - 0.5 * 540, dK)
RK = 0.3 * 540 * wppK
kep = bb.grupo('kepler', tuple(KPOS))
kep.rotation_mode = 'QUATERNION'
kep.rotation_quaternion = (-fK).to_track_quat('-Y', 'Z')
kep_orb = toro('kepler_orbita', RK, 0.011 * RK / 0.78, (0, 0, 0), AZOGUE, kep, nu=128, nv=8, plano='XZ')
kep_sol = bb.esfera('kepler_sol', 0.075 * RK / 0.78, (0, 0, 0), SOL, kep, subdiv=3)
kep_vac = bb.grupo('kepler_foco_vacio', (0, 0, 0), kep)
# el anillo del foco vacío es más ancho que el sol: con el círculo lo rodea (los dos focos coinciden) y se ve siempre
toro('kepler_foco_vacio_anillo', 0.115 * RK / 0.78, 0.012 * RK / 0.78, (0, 0, 0), VACIO_K, kep_vac, nu=48, nv=8, plano='XZ')
S.etiqueta('kepler', 'Kepler, <em>Astronomia nova</em> (1609)', (0, 0, -RK * 1.25), kep, 'serif')
S.etiqueta('kep_sol', 'sol', (0, 0, 0.27 * RK), kep_sol, 'nota')
S.etiqueta('kep_vacio', 'foco vacío', (0, 0, -0.27 * RK), kep, 'nota')   # ancla propia: con el círculo, los dos focos coinciden en el centro
ver(kep, (TK_A0, TK_A1, TINY, 1.0))
clave(kep_orb, 0, esc=1.0, interp=C)
clave(kep_sol, 0, loc=(0, 0, 0), interp=C)
clave(kep_vac, 0, loc=(0, 0, 0), interp=C)
clave(lbl('kep_vacio'), 0, loc=(0, 0, -0.27 * RK), interp=C)
for t, k in muestras(TK0, TK1):
    e = E_K * k
    bk = math.sqrt(1 - e * e)                     # semieje menor relativo; el mayor no cambia (elipse inscrita)
    clave(kep_orb, t, esc=(1.0, 1.0, bk), interp=L)
    clave(kep_sol, t, loc=(-e * RK, 0, 0), interp=L)
    clave(kep_vac, t, loc=(e * RK, 0, 0), interp=L)
    clave(lbl('kep_vacio'), t, loc=(e * RK, 0, -0.27 * RK), interp=L)
KEPLER = dict(FOCOS)

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
bpy.context.scene.frame_set(0)
S.exportar(posters=os.environ.get('POSTERS', '1') != '0')
