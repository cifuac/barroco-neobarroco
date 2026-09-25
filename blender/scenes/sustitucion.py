"""N1 · Sustitución — la figura 1 de Sarduy en profundidad.
Figura original: fracción «Snte.» (tachado) / «Sdo.»; flecha punteada larga → «Snte.¹», solo, lejos, sin barra.

Lenguaje «lámina de museo»: tablillas delgadas con letras de Caslon grabadas (el nombre tachado queda
calado, como hueco), barra y tachadura como hilos, flecha de guiones finos con punta esbelta, y el contexto
como una elipse fina trazada en el piso (esmeralda; carmín en «Papaya») con un tinte plano muy tenue.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bb
import bpy, bmesh
from mathutils import Vector

S = bb.Escena('sustitucion', 'Sustitución: la figura 1 en profundidad', dur=9)
M = bb.mat

CASLON = '/System/Library/Fonts/Supplemental/BigCaslon.ttf'      # la Caslon de los títulos del mazo
FUENTE = CASLON if os.path.exists(CASLON) else bb.FUENTES['serif']

# ---------------------------------------------------------------- medidas
FX = -3.0                   # x de la fracción
DX = 3.3                    # x de Snte.¹ en la figura plana
TW, TH, TD = 1.2, 0.40, 0.05  # tablilla delgada
BIS = 0.012                 # bisel pequeño
ZS = 0.33                   # centro de Snte. y Sdo. (±) respecto de la barra
ZF = 0.12                   # altura de la flecha y de Snte.¹
ZP = -0.81                  # piso (plano de la elipse del contexto)
CAP = 0.155                 # altura de mayúscula de las letras grabadas
YF = -TD / 2 - 0.02         # plano de los rótulos: justo delante de la cara de cada tablilla


# ---------------------------------------------------------------- letras (texto → malla, de pie mirando a -Y)
def _curva_a_malla(cuerpo, extrude, fuente=FUENTE):
    cu = bpy.data.curves.new('tx', 'FONT')
    cu.body = cuerpo
    cu.size = 1.0
    cu.extrude = extrude
    cu.align_x = 'LEFT'
    cu.align_y = 'CENTER'
    cu.resolution_u = 5
    cu.font = bpy.data.fonts.load(fuente, check_existing=True)
    ob = bpy.data.objects.new('tx', cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active


_H = {}


def _medir_H(fuente=FUENTE):
    if fuente in _H:
        return _H[fuente]
    ob = _curva_a_malla('H', 0.0, fuente)
    ys = [v.co.y for v in ob.data.vertices]
    me = ob.data
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    _H[fuente] = (min(ys), max(ys) - min(ys))
    return _H[fuente]


BASE_H, CAP_H = _medir_H()
# el «1» de la Caslon es de estilo antiguo (parece una I): el superíndice usa el 1 de la Times
TIMES = '/System/Library/Fonts/Supplemental/Times New Roman.ttf'
FUENTE_SUP = TIMES if os.path.exists(TIMES) else bb.FUENTES['serif']


def letras(nombre, cuerpo, centro, material, parent, grosor=0.006, cap=CAP, fuente=FUENTE):
    """Palabra en relieve (o cortador): centrada en x, altura de mayúscula centrada en z."""
    base_h, cap_h = _medir_H(fuente)
    s = cap / cap_h
    ob = _curva_a_malla(cuerpo, grosor / (2 * s), fuente)
    me = ob.data
    xs = [v.co.x for v in me.vertices]
    cx = (min(xs) + max(xs)) / 2
    for v in me.vertices:
        x, y, z = v.co
        v.co = ((x - cx) * s, -z * s, (y - base_h) * s - cap / 2)
    me.update()
    ob.name = nombre
    me.name = nombre
    me.materials.clear()
    if material:
        me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = False
    ob.parent = parent
    ob.location = centro
    return ob


RD = 0.012                  # profundidad del grabado hundido (el nombre tachado, «como hueco»)


def palabra(nombre, cuerpo, centro, material, parent, grosor=0.006, sup=None):
    """Palabra centrada; «sup» agrega un superíndice (p. ej. '1') a la derecha, a la altura de la mayúscula."""
    ob = letras(nombre, cuerpo, centro, material, parent, grosor)
    if not sup:
        return [ob]
    xs = [v.co.x for v in ob.data.vertices]
    capS = CAP * 0.56
    so = letras(nombre + '_sup', sup, centro, material, parent, grosor, cap=capS, fuente=FUENTE_SUP)
    sx = [v.co.x for v in so.data.vertices]
    sw = max(sx) - min(sx)
    gap = CAP * 0.1
    dx = max(xs) + gap + sw / 2
    for v in so.data.vertices:
        v.co.x += dx
        v.co.z += CAP / 2 - capS / 2 + CAP * 0.1
    corr = -(gap + sw) / 2
    for o in (ob, so):
        for v in o.data.vertices:
            v.co.x += corr
        o.data.update()
    return [ob, so]


def tablilla(nombre, loc, material, parent, cuerpo, mat_letra, hundido=False, sup=None):
    """Tablilla delgada con la palabra grabada: en relieve, o hundida con fondo de marfil (hundido=True)."""
    tb = bb.caja(nombre, (TW, TD, TH), loc, material, parent, bevel=BIS)
    if hundido:
        cort = letras(nombre + '_corte', cuerpo, (0, -TD / 2, 0), None, tb, grosor=2 * RD)
        bpy.context.view_layer.update()
        mod = tb.modifiers.new('hueco', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cort
        try:
            mod.solver = 'EXACT'
        except Exception:
            pass
        bb.aplicar(tb)
        me = cort.data
        bpy.data.objects.remove(cort)
        bpy.data.meshes.remove(me)
        for p in tb.data.polygons:
            p.use_smooth = False
        letras(nombre + '_letras', cuerpo, (0, -TD / 2 + RD + 0.001, 0), mat_letra, tb, grosor=0.004)
    else:
        palabra(nombre + '_letras', cuerpo, (0, -TD / 2 - 0.0025, 0), mat_letra, tb, sup=sup)
    return tb


def montura(nombre, base_z, top_z, parent, x=0.0, y=0.0):
    """Montura de museo: varilla fina de tinta detrás de la pieza, sobre un plinto bajo de mármol."""
    PL = (0.62, 0.34, 0.045)
    bb.caja(nombre + '_plinto', PL, (x, y, base_z + PL[2] / 2), M('soporte'), parent, bevel=0.01)
    bb.cilindro_entre(nombre + '_varilla', (x, y + TD / 2 + 0.018, base_z + PL[2]), (x, y + TD / 2 + 0.018, top_z),
                      r=0.011, material=M('lamina', 'grafito_varilla'), parent=parent, segs=10)


# ---------------------------------------------------------------- hilos (tubos finos) y elipses en el piso
def tubo_cerrado(nombre, pts, r, material, parent=None, segs=8):
    """Tubo fino a lo largo de una polilínea cerrada (anillos perpendiculares a la tangente)."""
    P = [Vector(p) for p in pts]
    n = len(P)
    bm = bmesh.new()
    anillos = []
    for i in range(n):
        t = (P[(i + 1) % n] - P[i - 1]).normalized()
        u = t.cross(Vector((0, 0, 1)))
        if u.length < 1e-6:
            u = t.cross(Vector((1, 0, 0)))
        u.normalize()
        w = t.cross(u).normalized()
        anillos.append([bm.verts.new(P[i] + (u * math.cos(2 * math.pi * k / segs) + w * math.sin(2 * math.pi * k / segs)) * r)
                        for k in range(segs)])
    for i in range(n):
        a, b = anillos[i], anillos[(i + 1) % n]
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    bm.normal_update()
    ob = bb._obj_from_bm(nombre, bm, material, parent)
    return ob


def elipse_piso(nombre, a, b, r, mat_linea, mat_tinte, parent, n=220):
    """Elipse trazada en el piso (eje mayor = x local) + tinte plano muy tenue dentro."""
    pts = [(a * math.cos(2 * math.pi * i / n), b * math.sin(2 * math.pi * i / n), r) for i in range(n)]
    tubo_cerrado(nombre + '_linea', pts, r, mat_linea, parent)
    bm = bmesh.new()
    c = bm.verts.new((0, 0, 0.0015))
    borde = [bm.verts.new((a * math.cos(2 * math.pi * i / n), b * math.sin(2 * math.pi * i / n), 0.0015)) for i in range(n)]
    for i in range(n):
        bm.faces.new((c, borde[i], borde[(i + 1) % n]))
    bm.normal_update()
    ob = bb._obj_from_bm(nombre + '_tinte', bm, mat_tinte, parent)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


# ---------------------------------------------------------------- figura (plano XZ, de frente a -Y)
LAMINA_LETRA = M('lamina', 'lamina_letras')    # marfil sobre la laca grafito
TINTA_LETRA = M('lamina', 'grafito_letras')    # tinta sobre el oro

fig = bb.grupo('figura')
# Sdo.: tablilla de oro bajo la barra, letras en tinta
sdo = tablilla('sdo', (FX, 0, -ZS), M('significado'), fig, 'Sdo.', TINTA_LETRA)
# la barra de la fracción: un hilo de tinta
barra = bb.cilindro_entre('barra', (FX - TW * 0.62, 0, 0), (FX + TW * 0.62, 0, 0), r=0.016,
                          material=M('lamina', 'grafito_barra'), parent=fig, segs=14)
# Snte. tachado: la palabra queda hundida en la laca (el nombre sigue ahí, como hueco) + tachadura bermellón fina
snte = tablilla('snte', (FX, 0, ZS), M('significante'), fig, 'Snte.', LAMINA_LETRA, hundido=True)
YT = -TD / 2 - 0.022
tach = bb.cilindro_entre('tachadura', (FX - 0.56, YT, ZS - 0.085), (FX + 0.56, YT, ZS + 0.085), r=0.014,
                         material=M('ausencia'), parent=fig, segs=12)
montura('figura_montura', ZP, ZS, fig, x=FX)
# «clásico»: significante sin tachar, adherido a la barra (sólo en la transición de la falla)
ZC = TH / 2 + 0.022
clasico = tablilla('snte_clasico', (FX, 0, ZC), M('significante', 'significante_clasico'), fig, 'Snte.', LAMINA_LETRA)

# flecha plana (figura original): de la fracción hacia la derecha, a media altura
p0 = (FX + TW * 0.62 + 0.14, 0, ZF)
p1 = (DX - TW / 2 - 0.12, 0, ZF)
flecha_plana = bb.grupo('flecha_plana', p0, fig)
bb.polilinea_punteada('flecha_plana_guiones', [(0, 0, 0), (p1[0] - p0[0], 0, 0)], guion=0.15, hueco=0.1, r=0.012,
                      material=M('trayecto'), parent=flecha_plana, flecha={'r': 0.042, 'largo': 0.24})
# Snte.¹ en su lugar plano
snte1 = bb.grupo('snte1', (DX, 0, ZF))
tablilla('snte1_tablilla', (0, 0, 0), M('significante'), snte1, 'Snte.', LAMINA_LETRA, sup='1')
montura('snte1_montura', ZP - ZF, 0.0, snte1)

# flecha profunda: la distancia semántica se vuelve distancia espacial
LEJOS = (2.6, 7.5, ZF)
d = (LEJOS[0] - p0[0], LEJOS[1] - p0[1], 0)
L = math.hypot(d[0], d[1])
ang = math.atan2(d[1], d[0])
flecha_prof = bb.grupo('flecha_profunda', p0)
flecha_prof.rotation_euler = (0, 0, ang)
bb.polilinea_punteada('flecha_profunda_guiones', [(0, 0, 0), (L - 1.45, 0, 0)], guion=0.17, hueco=0.11, r=0.013,
                      material=M('trayecto'), parent=flecha_prof, flecha={'r': 0.05, 'largo': 0.36})

# contexto: elipse fina trazada en el piso que abraza los dos términos (eje mayor = fracción → Snte.¹)
LANG = math.atan2(LEJOS[1], LEJOS[0] - FX)
CTR = ((FX + LEJOS[0]) / 2, LEJOS[1] / 2, ZP)
EA, EB = 5.6, 1.4
ctx = bb.grupo('contexto', CTR)
ctx.rotation_euler = (0, 0, LANG)
elipse_piso('contexto', EA, EB, 0.011, M('trayecto', 'trayecto_contexto'), M('trayecto', 'tinte_contexto'), ctx)
# papaya: el mismo contexto, ahora carmín (erotiza la totalidad de la obra)
halo = bb.grupo('halo', CTR)
halo.rotation_euler = (0, 0, LANG)
elipse_piso('halo', EA + 0.08, EB + 0.08, 0.011, M('ajeno', 'ajeno_contexto'), M('ajeno', 'tinte_papaya'), halo)

# ---------------------------------------------------------------- etiquetas (anclas)
PERP = (-math.sin(LANG), math.cos(LANG))   # lado «alto» del eje en pantalla
S.etiqueta('falla', 'abertura, falla', (0.28 + PERP[0] * 1.0, 3.75 + PERP[1] * 1.0, 0.6), clase='serif')
AX = (math.cos(LANG), math.sin(LANG))       # eje fracción → Snte.¹ en el piso
# «contexto»: junto al borde cercano de la elipse, bajo la flecha
S.etiqueta('contexto', 'contexto', (CTR[0] - PERP[0] * (EB + 0.3) - AX[0] * 1.5, CTR[1] - PERP[1] * (EB + 0.3) - AX[1] * 1.5, ZP + 0.2),
           clase='trayecto')
EJ_SDO = (FX + 1.5, YF, -ZS)                 # a la derecha de Sdo.
EJ_SNTE1 = (-0.2, YF, 0.5)                   # sobre Snte.¹, algo a la izquierda: margen derecho en 16:9
S.etiqueta('ej_sdo', '«virilidad»', EJ_SDO, clase='sdo')
S.etiqueta('ej_snte1', '«el aguijón del leptosomático macrogenitoma»', EJ_SNTE1, parent=snte1, clase='snte')
S.etiqueta('porro_sdo', 'canal de desagüe', EJ_SDO, clase='sdo')
S.etiqueta('porro_tach', '<s>gárgola</s> (significante codificado)', (FX, YF, ZS + 0.5), clase='tachado')
S.etiqueta('porro_snte1', 'flauta, fémur o falo', EJ_SNTE1, parent=snte1, clase='snte')
S.etiqueta('papaya_sdo', 'fuente', EJ_SDO, clase='sdo')
S.etiqueta('papaya_snte1', 'papaya', EJ_SNTE1, parent=snte1, clase='snte')
# nota: fuera de la elipse, junto a su borde cercano (no cruza la línea ni la flecha)
S.etiqueta('papaya_nota', 'en argot cubano, también el sexo femenino', (1.1, 1.1, ZP + 0.2), clase='nota')

# ---------------------------------------------------------------- línea de tiempo
C = 'CONSTANT'
F = 1.0 / bb.FPS
X0, X1, CERO = (0.0001, 0.25, 0.25), (1, 1, 1), (0.0001, 0.0001, 0.0001)   # X0: la flecha nace fina (sin disco suelto)
# estado 2 (0.6 → 3.0 s): la flecha gira hacia la profundidad y Snte.¹ se aleja
S.clave(flecha_plana, 0.7, esc=1.0); S.clave(flecha_plana, 1.2, esc=0.0001)
S.clave(flecha_prof, 0, esc=CERO, interp=C); S.clave(flecha_prof, 1.0 - F, esc=CERO, interp=C)
S.clave(flecha_prof, 1.0, esc=X0); S.clave(flecha_prof, 2.6, esc=X1, interp=C)
S.mover(snte1, 0.8, 2.9, (DX, 0, ZF), LEJOS)
S.clave(snte1, 0, esc=1.0, interp=C)
S.clave(clasico, 0, esc=0.0001, interp=C)
S.clave(tach, 0, esc=1.0, interp=C)
S.clave(snte, 0, esc=1.0, interp=C)
# estado 3 (3.0 → 5.5 s): adherencia clásica → abertura barroca (deslizador entre 3.5 y 5.5)
S.salto(tach, 3.1, 1.0, 0.0001); S.salto(snte, 3.1, 1.0, 0.0001); S.salto(clasico, 3.1, 0.0001, 1.0)
S.salto(flecha_prof, 3.1, X1, CERO); S.salto(snte1, 3.1, 1.0, 0.0001)
#   3.5 → 4.2: el significante es escamoteado (la tachadura cae sobre él)
S.salto(clasico, 3.8, 1.0, 0.0001); S.salto(snte, 3.8, 0.0001, 1.0)
S.clave(tach, 3.8, esc=0.0001); S.clave(tach, 4.2, esc=1.0)
#   4.3 → 5.5: la flecha crece hacia lo lejos y aparece otro nombrante
S.clave(flecha_prof, 4.3 - F, esc=CERO, interp=C); S.clave(flecha_prof, 4.3, esc=X0); S.clave(flecha_prof, 5.2, esc=X1)
S.clave(snte1, 5.0, esc=0.0001); S.clave(snte1, 5.5, esc=1.0)
# estado 4 (5.7 → 6.7 s): contexto (la elipse se abre desde su centro, plana sobre el piso)
S.mostrar(ctx, 5.7, 6.7)
# estado 7 (8.0 → 8.8 s): el contexto esmeralda se vuelve carmín (papaya)
S.ocultar(ctx, 8.0, 8.8)
S.mostrar(halo, 8.0, 8.8)

# rótulos que siguen a su objeto dentro del deslizador de la falla: fuera de cuadro («limbo») mientras
# su objeto no está (el visor no oculta un rótulo por la escala de su padre)
LIMBO = 1000.0


def limbo(clave, claves, base, padre_escala=1.0):
    """claves: [(t, visible), ...] con interpolación constante; oculto = ancla muy por encima del cuadro."""
    ob = bb.bpy.data.objects['lbl_' + clave]
    lejos = (base[0], base[1], base[2] + LIMBO / padre_escala)
    for t, vis in claves:
        S.clave(ob, t, loc=base if vis else lejos, interp=C)


limbo('falla', [(0, True), (3.1, False), (4.5, True)], tuple(bb.bpy.data.objects['lbl_falla'].location))


# ---------------------------------------------------------------- ajustes del estudio (tema claro)
S.estudio = {
    'materiales': {
        # tintes planos, mates y casi transparentes, dentro de la elipse del contexto
        'tinte_contexto': {'color': '#16795A', 'opacity': 0.025, 'roughness': 0.95, 'envMapIntensity': 0.2},
        'tinte_papaya': {'color': '#A3245F', 'opacity': 0.025, 'roughness': 0.95, 'envMapIntensity': 0.2},
        # letras grabadas: marfil mate sobre la laca; tinta sobre el oro
        'lamina_letras': {'color': '#F1EADC', 'roughness': 0.6, 'envMapIntensity': 0.5},
    },
    'sombra': 0.18,
}

# ---------------------------------------------------------------- estados
FRENTE = dict(cam=(0.08, -63.21, 9.71), look=(0.08, 0, -0.3), fov=4.3)
VOL = dict(cam=(-4.62, -10.63, 2.79), look=(-0.33, -0.02, -0.5), fov=24)
DIST = dict(cam=(0.1, -6.71, 1.91), look=(-0.94, 1.42, -0.3), fov=32)
FALLA = dict(cam=(-0.12, -7.69, 2.31), look=(-1.35, 1.9, -0.3), fov=33)      # un paso atrás: sitio para las dos columnas
CTX = dict(cam=(0.91, -7.49, 3.62), look=(-1.35, 3.14, -0.77), fov=32)
PAPAYA = dict(cam=(0.6, -7.9, 3.8), look=(-1.2, 3.3, -0.7), fov=32)          # algo a la izquierda: sitio para la fuente

S.estado('Figura 1', 'La figura tal como la dibuja Sarduy: el significante que corresponde al significado queda <b>tachado</b>; otro, lejano, ocupa su lugar a distancia.',
         'Sarduy 1972 · figura 1 (l. 159-162)', etiquetas=[], orbita=False, t1=0, **FRENTE)
S.estado('Volumen', 'Lo mismo, visto en volumen: la barra separa y a la vez une; el nombre tachado sigue ahí, como hueco.',
         'l. 151-157', etiquetas=[], t1=0.5, **VOL)
S.estado('Distancia', 'La distancia semántica se vuelve distancia espacial: Snte.¹ no ocupa el hueco; funciona <em>desde lejos</em>.',
         'l. 154-157', etiquetas=[], t1=3.0, pregunta='¿Dónde queda el nuevo significante respecto del hueco?', **DIST)
S.estado('Falla', 'Del arte clásico (adherencia de los dos términos del signo) a la <b>abertura</b> barroca. Mueve el deslizador.',
         '«Abertura, falla entre lo [nombrante] y lo nombrado» (l. 192)', etiquetas=['falla'], t1=5.5,
         slider={'tipo': 'tiempo', 't0': 3.5, 't1': 5.5, 'etiqueta': 'distancia entre nombrante y nombrado',
                 'min_txt': 'adherencia clásica', 'max_txt': 'abertura barroca'}, **FALLA)
S.estado('Contexto', 'El sustituto sólo significa dentro de un contexto que liga los dos términos a distancia.',
         '«sólo en el contexto erótico del relato funciona» (l. 156)', etiquetas=['contexto'], t1=6.7, **CTX)
S.estado('Lezama', 'En <em>Paradiso</em>, el significante de «virilidad» es escamoteado y sustituido por otro, totalmente alejado.',
         'Lezama Lima, Paradiso · l. 151-157', etiquetas=['ej_sdo', 'ej_snte1'], t1=6.7, **CTX)
S.estado('Porro', 'En la arquitectura de Ricardo Porro, el desagüe no se vuelve gárgola (el significante ya codificado) sino flauta, fémur o falo.',
         'l. 173-180', etiquetas=['porro_sdo', 'porro_tach', 'porro_snte1'], t1=6.7, **CTX)
S.estado('Papaya', 'Una fuente con forma de papaya: la sustitución no es simple permutación, <b>erotiza la totalidad</b> de la obra.',
         'l. 180-186', etiquetas=['papaya_sdo', 'papaya_snte1', 'papaya_nota'], t1=8.8, **PAPAYA)

S.exportar()
