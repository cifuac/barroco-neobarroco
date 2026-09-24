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
NEUTRO = mat_local('gris_neutro', '#8A8A8A', 0.0, 0.55, 0.35)
SOL = M('logos')
# el arco es la cadena de significantes: nácar (como en svg/fig2.svg), levemente emisivo para que el punteado se lea
# igual en el plano y tendido; el cian queda reservado a la lectura (rayos radiales/deceptivos)
ARCO = mat_local('arco_nacar', '#CFC6B8', 0.0, 0.45, 0.55)
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


def encuadre(nombre, puntos, az, el, fov, rect, look0=(0, 0.4, 0.5), dist=9.0):
    """Cámara que encaja `puntos` [(Vector, pad_x, pad_y) en px] dentro de rect=(x0,y0,x1,y1) px,
    vista desde azimut/elevación dados (grados; az=0 → de frente, desde -Y)."""
    a, e = math.radians(az), math.radians(el)
    dv = Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)))
    look = Vector(look0)
    for _ in range(120):
        cam = look + dv * dist
        bx0 = by0 = 1e9
        bx1 = by1 = -1e9
        for p, px, py in puntos:
            x, y = proy(cam, look, fov, p)
            bx0, bx1 = min(bx0, x - px), max(bx1, x + px)
            by0, by1 = min(by0, y - py), max(by1, y + py)
        ratio = max((bx1 - bx0) / (rect[2] - rect[0]), (by1 - by0) / (rect[3] - rect[1]))
        wpp = 2 * dist * math.tan(math.radians(fov) / 2) / 1080
        f = -dv
        r = f.cross(Vector((0, 0, 1))).normalized()
        u = r.cross(f)
        look = look + r * (((bx0 + bx1) / 2 - (rect[0] + rect[2]) / 2) * wpp * 0.8) \
                    - u * (((by0 + by1) / 2 - (rect[1] + rect[3]) / 2) * wpp * 0.8)
        dist = min(max(dist * ratio ** 0.5, 2.0), 38.5)
    cam = look + dv * dist
    print(f'[encuadre] {nombre}: cam={tuple(round(c, 2) for c in cam)} look={tuple(round(c, 2) for c in look)} '
          f'dist={dist:.2f} bbox=({bx0:.0f},{by0:.0f})-({bx1:.0f},{by1:.0f})')
    return dict(cam=tuple(cam), look=tuple(look), fov=fov)


def lbl(clave):
    return bpy.data.objects['lbl_' + clave]


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
barra = bb.caja('barra', (BW * 1.25, 0.07, 0.035), (0, 0, BH + 0.05), LAM, estela, bevel=0.01)
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
S.etiqueta('e_sdo_foco', 'Sdo.<br>foco presente', (0, -0.55, 0.0), sdo_g, 'sdo')        # al pie del foco, en la vista cenital
S.etiqueta('e_snte_foco', '<s>Snte.</s><br>foco ausente', (0, 0.55, 0.0), snte_g, 'tachado')   # arriba: con el círculo, no pisa al del Sdo.
S.etiqueta('cita1974', '<span style="color:var(--azogue)">lectura posterior<br>Sarduy 1974, cit. por Díaz 2011</span>', (0, -1.3, 0.1), orb, 'nota')   # en el lado abierto, abajo
S.etiqueta('e_vacio', 'ningún Sdo.', (0, -0.55, 0.0), estela, 'grande')
S.etiqueta('e3_snte', '<s>Snte.</s>', (0, 0, BH / 2 + 0.24), snte_g, 'grande tachado')
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
caja_punteada('venir_contorno', (0.46, 0.46, 0.8), (0, 0, 0.4), FANT, o5, guion=0.08, hueco=0.06, r=0.012)
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
        S.etiqueta(f'obj{n + 1}', f'Snte.<sup>{n + 1}</sup> · por venir', (0, 0, ALTO[n] + 0.2), o, 'snte nota')

# ---------------------------------------------------------------- tablillas genéricas (estados 3-5)
DESORDEN = [(-18, 5), (24, -4), (-10, -6), (16, 6)]      # giro e inclinación en la lectura deceptiva
MAMP = ['seis cucharas', 'un vaso', 'quizá un plato', 'un ojo sobre una piel']   # l. 262-267
for n in range(4):
    g = bb.grupo(f'tab{n + 1}', (0, 0, 0), BASES[n])
    bb.caja(f'tab{n + 1}_placa', (0.52, 0.1, 0.36), (0, 0, 0.18), NACAR, g, bevel=0.02)
    fuera = Vector((math.cos(TH_S[n]), math.sin(TH_S[n]), 0))
    # en la vista cenital (estados 4-5) el rótulo queda por fuera del arco, como en la figura
    S.etiqueta(f'tab{n + 1}', f'Snte.<sup>{n + 1}</sup>', tuple(fuera * (PL_R[n] + 0.3) + Vector((0, 0, 0.2))), g, 'snte')
    S.etiqueta(f'mamp{n + 1}', f'<span style="{MAG}">{MAMP[n]}</span>', tuple(fuera * (PL_R[n] + 0.42) + Vector((0, 0, 0.1))), g, 'nota')
    TABS.append(g)
fuera5 = Vector((math.cos(TH_S[4]), math.sin(TH_S[4]), 0))
S.etiqueta('tab5', 'Snte.<sup>5</sup>', tuple(fuera5 * (PL_R[4] + 0.3) + Vector((0, 0, 0.2))), o5, 'snte')
S.etiqueta('mamp5', '¿lo que vendría a cerrarla?', (0, 0, 1.0), o5, 'nota')

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
    x, y = P(TH_ETC, k, 1 + 0.36 / ejes(k)[0])
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

# estado 4 · dos focos: la fracción se desdobla; el arco se vuelve elíptico y sigue abierto
ver(barra, (TM0, TM0 + 0.35, 1.0, TINY), inicial=1.0)
clave(sdo_g, 0, loc=(0, 0, 0), interp=C)
clave(plinto_e, 0, loc=(0, 0, 0), interp=C)
clave(snte_g, 0, loc=(0, 0, SNTE_Z0), interp=C)
for t, k in muestras(TM0, TM1):
    c = ejes(k)[2]
    clave(sdo_g, t, loc=(-c, 0, 0), interp=L)
    clave(plinto_e, t, loc=(-c, 0, 0), interp=L)
    clave(snte_g, t, loc=(c, 0, SNTE_Z0 - k * (SNTE_Z0 - BH / 2) + 0.12 * k), interp=L)

# ================================================================ encuadres (cámaras calculadas para caber en el 60 % izquierdo)
RECT = (90, 130, 1070, 955)


def pts_arco(k, paso=10):
    out = []
    for gdeg in range(-15, 195, paso):
        x, y = P(math.radians(gdeg), k)
        out.append((Vector((x, y, ZARC)), 6, 6))
    return out


def pts_eslabones(k, altos, lbl_pad=None, lbl_z=None):
    out = []
    for n in range(5):
        c = mundo_base(n, k)
        for j in range(8):
            t = 2 * math.pi * j / 8
            out.append((c + Vector((PL_R[n] * math.cos(t), PL_R[n] * math.sin(t), -0.06)), 0, 0))
        out.append((c + Vector((0, 0, altos[n])), 0, 0))
        if lbl_pad:
            out.append((c + Vector((0, 0, lbl_z[n])), lbl_pad[n], 26))
    return out


def pt_etc(k):
    x, y = P(TH_ETC, k, 1.2 if k == 0 else 1 + 0.36 / ejes(k)[0])
    return (Vector((x, y, ZARC + 0.1)), 50, 30)


def ejes_cam(cam, look):
    f = (Vector(look) - Vector(cam)).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    return f, r, r.cross(f)


def desproy(E, x, y, prof):
    """Punto del mundo que se ve en el píxel (x, y) a la profundidad `prof` (m) de la cámara E."""
    cam, look = Vector(E['cam']), Vector(E['look'])
    f, r, u = ejes_cam(cam, look)
    wpp = 2 * prof * math.tan(math.radians(E['fov']) / 2) / 1080
    return cam + f * prof + r * ((x - 960) * wpp) - u * ((y - 540) * wpp), wpp


LBL_OBJ = [175, 215, 200, 130, 130]
p1 = pts_arco(0) + pts_eslabones(0, ALTO, LBL_OBJ, [a + 0.2 for a in ALTO]) + [pt_etc(0), (Vector((0, 0, 0.9)), 70, 30)]
CADENA = encuadre('cadena', p1, -16, 34, 34, RECT)
RADIAL = encuadre('radial', p1 + [(Vector((0, -0.62, 0.0)), 170, 30)], -6, 36, 34, RECT)

# ---------------------------------------------------------------- lectura deceptiva (estado 3)
# Los mismos rayos radiales del estado 2, pero cada uno se queda corto y a otra altura: no convergen (l. 255-275).
# Delante del lugar vacío del Sdo., la lista de lecturas que se anulan unas a otras, tachadas y en el orden del texto (l. 269-270).
RAYOS3 = []
LECT = ['Banquete', 'Ojo Profiláctico', 'Primitivismo', 'Ritualidad']
R_FIN = [0.8, 0.8, 1.05, 1.0]          # distancia al eje a la que se detiene cada rayo
DESV = [0.0, 0.0, 0.0, 0.0]            # radiales, como en la lectura radial
H_FIN = [0.22, 1.25, 0.62, 1.0]        # alturas finales, todas distintas: no se encuentran
for n in range(4):
    base = mundo_base(n, 0, 0.0)
    u = Vector((-base.x, -base.y, 0)).normalized()
    pp = Vector((-u.y, u.x, 0))
    a = base + u * (PL_R[n] * 0.6) + Vector((0, 0, 0.36))
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

p3 = pts_arco(0) + pts_eslabones(0, [0.4] * 4 + [0.8], [0, 0, 0, 0, 150], [0.62] * 4 + [1.0]) + [pt_etc(0)]
for n in range(4):
    fu = Vector((math.cos(TH_S[n]), math.sin(TH_S[n]), 0))
    p3.append((mundo_base(n, 0) + fu * (PL_R[n] + 0.42) + Vector((0, 0, 0.1)), 90, 20))
p3 += [(b, 0, 0) for g, a, b in RAYOS3] + [(p, 125, 24) for p in PT_LECT] + [(Vector((0, -0.55, 0)), 110, 28)]
p3 = [q for q in p3 if not (q[1] == 90 and q[2] == 20)]   # sin rótulos de tablilla en este estado
DECEP = encuadre('deceptiva', p3, -12, 42, 34, RECT)

# ---------------------------------------------------------------- dos focos (estado 4): vista casi cenital
# la elipse ha de leerse como deformación de la figura, no como efecto de perspectiva: cámara casi perpendicular al plano
c1 = ejes(1)[2]
p4 = pts_arco(1) + pts_eslabones(1, [0.4] * 4 + [0.8]) + [pt_etc(1)]
for n in range(5):
    fu = Vector((math.cos(TH_S[n]), math.sin(TH_S[n]), 0))
    p4.append((mundo_base(n, 1) + fu * (PL_R[n] + 0.3) + Vector((0, 0, 0.2)), 60, 24))
p4 += [(Vector((-c1, -0.55, 0.0)), 90, 36), (Vector((c1, -0.55, 0.0)), 90, 36), (Vector((0, -1.3, 0.16)), 160, 30)]
FOCOS = encuadre('focos', p4, 0, 76, 34, RECT)

# ---------------------------------------------------------------- Kepler (miniatura aparte: otro trazo, sin rótulos Snte.)
# Misma cámara que «Dos focos»: la miniatura flota arriba a la derecha, sobre el panel, de cara a la cámara.
E_K = 0.5                                        # la elipse de la miniatura (inscrita en el círculo, como en Kepler)
fK, rK, uK = ejes_cam(FOCOS['cam'], FOCOS['look'])
dK = (Vector(FOCOS['look']) - Vector(FOCOS['cam'])).length * 0.72
KPOS, wppK = desproy(FOCOS, 1480, 320, dK)
RK = 180 * wppK
kep = bb.grupo('kepler', tuple(KPOS))
kep.rotation_mode = 'QUATERNION'
kep.rotation_quaternion = (-fK).to_track_quat('-Y', 'Z')
kep_orb = toro('kepler_orbita', RK, 0.011 * RK / 0.78, (0, 0, 0), AZOGUE, kep, nu=128, nv=8, plano='XZ')
kep_sol = bb.esfera('kepler_sol', 0.075 * RK / 0.78, (0, 0, 0), SOL, kep, subdiv=3)
kep_vac = bb.grupo('kepler_foco_vacio', (0, 0, 0), kep)
toro('kepler_foco_vacio_anillo', 0.055 * RK / 0.78, 0.008 * RK / 0.78, (0, 0, 0), NEUTRO, kep_vac, nu=32, nv=6, plano='XZ')
S.etiqueta('kepler', 'Kepler, <em>Astronomia nova</em> (1609)', (0, 0, -RK * 1.25), kep, 'serif')
S.etiqueta('kep_sol', 'sol', (0, 0, 0.2 * RK), kep_sol, 'nota')
S.etiqueta('kep_vacio', 'foco vacío', (0, 0, -0.22 * RK), kep, 'nota')   # ancla propia: con el círculo, los dos focos coinciden en el centro
ver(kep, (TK_A0, TK_A1, TINY, 1.0))
clave(kep_orb, 0, esc=1.0, interp=C)
clave(kep_sol, 0, loc=(0, 0, 0), interp=C)
clave(kep_vac, 0, loc=(0, 0, 0), interp=C)
clave(lbl('kep_vacio'), 0, loc=(0, 0, -0.22 * RK), interp=C)
ver(kep_vac, (TK0, TK0 + 0.3, TINY, 1.0))
for t, k in muestras(TK0, TK1):
    e = E_K * k
    bk = math.sqrt(1 - e * e)                     # semieje menor relativo; el mayor no cambia (elipse inscrita)
    clave(kep_orb, t, esc=(1.0, 1.0, bk), interp=L)
    clave(kep_sol, t, loc=(-e * RK, 0, 0), interp=L)
    clave(kep_vac, t, loc=(e * RK, 0, 0), interp=L)
    clave(lbl('kep_vacio'), t, loc=(e * RK, 0, -0.22 * RK), interp=L)
KEPLER = dict(FOCOS)

ZC0 = Z0 + 0.235     # la figura sube un poco: la punta de flecha no debe rozar el panel (también incrustado, 1920×904)
FRENTE = dict(cam=(-0.165, -39.5, ZC0), look=(-0.165, 0, ZC0), fov=7.0)

# ================================================================ estados
E_FIG = ['snte1', 'snte2', 'snte3', 'snte4', 'snte5', 'etc', 'e_snte', 'e_sdo']
E_OBJ = ['obj1', 'obj2', 'obj3', 'obj4', 'obj5', 'etc']

S.estado('Figura 2',
         'El significante de un significado dado queda tachado; una cadena de significantes, que progresa metonímicamente, traza una órbita a su alrededor. En la figura, el arco queda <b>abierto</b>: etc.',
         'Sarduy 1972 · figura 2 (l. 211-228)', etiquetas=E_FIG, orbita=False, t1=0, **FRENTE)
S.estado('Cadena',
         'Carpentier, <em>El siglo de las luces</em>: reloj de sol vuelto reloj de luna, balanza para pesar gatos, telescopio por una luceta rota, astrónomo sobre un armario. La cadena sigue abierta.',
         'l. 230-239', etiquetas=E_OBJ + ['e_snte', 'e3_sdo'], t1=T1, **CADENA)
S.estado('Lectura radial',
         'De cada objeto la lectura vuelve al centro: el significado, «desorden», está presente; su significante nunca se escribe. Se infiere.',
         'l. 211-217 · l. 230-233 · rayos: añadido didáctico', etiquetas=E_OBJ + ['e_snte', 'e3_desorden'], t1=T2,
         pregunta='¿Y si las lecturas no convergieran en ningún centro?', **RADIAL)
S.estado('Lectura deceptiva',
         'Abreu, <em>Mampulorio</em>: cucharas, un vaso, un ojo sobre una piel. Las lecturas no convergen: los significantes, en vez de completarse, se anulan unos a otros. El centro no se llena.',
         'l. 255-275', etiquetas=['mamp5', 'etc', 'lect1', 'lect2', 'lect3', 'lect4', 'e_vacio'],
         t1=T3F, **DECEP)
S.estado('Dos focos',
         'Lectura posterior: el significante tachado se vuelve un segundo centro, ausente, junto al significado. El círculo se deforma en elipse, que sigue abierta.',
         'Sarduy 1974, cit. por Díaz 2011 (l. 1470-1483)',
         etiquetas=['tab1', 'tab2', 'tab3', 'tab4', 'tab5', 'etc', 'e_sdo_foco', 'e_snte_foco', 'cita1974'], t1=TM1,
         slider={'tipo': 'tiempo', 't0': TM0, 't1': TM1, 'etiqueta': 'excentricidad',
                 'min_txt': 'círculo: un centro', 'max_txt': 'elipse: dos focos'}, **FOCOS)
S.estado('Kepler',
         'Kepler: el trayecto de los astros, que se suponía circular, pierde su centro único «para hacerse doble». Más tarde Sarduy llamará <em>retombée</em> a este parecido: «isomorfía no contigua».',
         'l. 64-67 · Sarduy 1974, cit. por Díaz 2011, l. 1503-1509',
         etiquetas=['kepler', 'kep_sol', 'kep_vacio', 'tab1', 'tab2', 'tab3', 'tab4', 'tab5', 'e_sdo_foco', 'e_snte_foco', 'etc'], t1=TK1,
         slider={'tipo': 'tiempo', 't0': TK0, 't1': TK1, 'etiqueta': 'la órbita de Kepler',
                 'min_txt': 'círculo', 'max_txt': 'elipse'}, **KEPLER)

# ================================================================ control
tri = 0
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ob.data.calc_loop_triangles()
        tri += len(ob.data.loop_triangles)
print(f'[proliferacion] guiones={len(GUIONES)} triángulos={tri} objetos={len(bpy.data.objects)}')
S.exportar(posters=os.environ.get('POSTERS', '1') != '0')
