"""N1 · Sustitución — la figura 1 de Sarduy en profundidad.
Figura original: fracción «Snte.» (tachado) / «Sdo.»; flecha punteada larga → «Snte.¹», solo, lejos, sin barra.
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bb

S = bb.Escena('sustitucion', 'Sustitución: la figura 1 en profundidad', dur=9)
M = bb.mat

# ---------------------------------------------------------------- figura (plano XZ, de frente a -Y)
FX = -3.0          # x de la fracción
DX = 3.3           # x de Snte.¹ en la figura plana
TW, TH, TD = 1.3, 0.46, 0.16   # tablilla
ZS = 0.38          # altura (±) de Snte. y Sdo. respecto de la barra
YF = -TD / 2 - 0.02            # plano de los rótulos: justo delante de la cara de cada tablilla

fig = bb.grupo('figura')
# Sdo.: tablilla de oro bajo la barra
sdo = bb.caja('sdo', (TW, TD, TH), (FX, 0, -ZS), M('significado'), fig, bevel=0.03)
# la barra de la fracción: tinta oscura (se lee sobre el papel claro)
barra = bb.caja('barra', (TW * 1.25, 0.1, 0.06), (FX, 0, 0.0), M('lamina', 'grafito_barra'), fig, bevel=0.012)
# Snte. (tachado): tablilla de laca sobre la barra + tachadura bermellón
snte = bb.caja('snte', (TW, TD, TH), (FX, 0, ZS), M('significante'), fig, bevel=0.03)
tach = bb.caja('tachadura', (TW * 1.18, 0.05, 0.055), (FX, -TD / 2 - 0.03, ZS), M('ausencia'), fig)
tach.rotation_euler = (0, math.radians(-10), 0)
# «clásico»: significante sin tachar, adherido a la barra (sólo visible en la transición de la falla)
ZC = TH / 2 + 0.03
clasico = bb.caja('snte_clasico', (TW, TD, TH), (FX, 0, ZC), M('significante', 'significante_clasico'), fig, bevel=0.03)

# flecha plana (figura original): de la fracción hacia la derecha, a media altura
p0 = (FX + 0.95, 0, 0.12)
p1 = (DX - 0.8, 0, 0.12)
flecha_plana = bb.grupo('flecha_plana', p0, fig)
bb.polilinea_punteada('flecha_plana_guiones', [(0, 0, 0), (p1[0] - p0[0], 0, 0)], guion=0.2, hueco=0.13, r=0.03,
                      material=M('trayecto'), parent=flecha_plana, flecha={'r': 0.1, 'largo': 0.26})
# Snte.¹ en su lugar plano
snte1 = bb.grupo('snte1', (DX, 0, 0.12))
bb.caja('snte1_tablilla', (TW, TD, TH), (0, 0, 0), M('significante'), snte1, bevel=0.03)

# flecha profunda: la distancia semántica se vuelve distancia espacial
LEJOS = (2.6, 7.5, 0.12)
d = (LEJOS[0] - p0[0], LEJOS[1] - p0[1], 0)
L = math.hypot(d[0], d[1])
ang = math.atan2(d[1], d[0])
flecha_prof = bb.grupo('flecha_profunda', p0)
flecha_prof.rotation_euler = (0, 0, ang)
bb.polilinea_punteada('flecha_profunda_guiones', [(0, 0, 0), (L - 1.55, 0, 0)], guion=0.22, hueco=0.14, r=0.032,
                      material=M('trayecto'), parent=flecha_prof, flecha={'r': 0.13, 'largo': 0.38})

# contexto: envolvente translúcida que liga los dos términos (eje mayor = fracción → Snte.¹)
LANG = math.atan2(LEJOS[1], LEJOS[0] - FX)
CTR = ((FX + LEJOS[0]) / 2, LEJOS[1] / 2, 0.05)


def pildora(ob, p=3.2):
    """Deforma una esfera unitaria (eje local Y) en un superelipsoide: flancos casi rectos y puntas redondas,
    para que la fracción y Snte.¹ queden dentro de la envolvente y no en su punta."""
    for v in ob.data.vertices:
        x, y, z = v.co
        s = max(-1.0, min(1.0, y))
        rho = math.hypot(x, z)
        k = ((1 - abs(s) ** p) ** (1 / p)) / rho if rho > 1e-6 else 0.0
        v.co = (x * k, s, z * k)
    ob.data.update()


RP_C, RA_C, RV_C = 1.7, 5.8, 0.82      # contexto: semiejes (transversal, a lo largo, vertical)
RP_H, RA_H, RV_H = 1.95, 6.1, 0.86     # velo cálido, apenas mayor
ctx = bb.grupo('contexto', CTR)
env = bb.esfera('contexto_envolvente', 1.0, (0, 0, 0), M('vidrio'), ctx, subdiv=5)
pildora(env)
env.scale = (RP_C, RA_C, RV_C)
env.rotation_euler = (0, 0, LANG - math.radians(90))

# velo cálido (papaya: erotiza la totalidad de la obra); reemplaza al contexto neutro
halo = bb.grupo('halo', CTR)
hv = bb.esfera('halo_velo', 1.0, (0, 0, 0), M('calido'), halo, subdiv=5)
pildora(hv)
hv.scale = (RP_H, RA_H, RV_H)
hv.rotation_euler = (0, 0, LANG - math.radians(90))

# ---------------------------------------------------------------- etiquetas (anclas)
PERP = (-math.sin(LANG), math.cos(LANG))   # lado «alto» del eje en pantalla
S.etiqueta('snte', '<s>Snte.</s>', (FX, YF, ZS), clase='grande tachado')
S.etiqueta('sdo', 'Sdo.', (FX, YF, -ZS), clase='grande sdo')
S.etiqueta('snte1', 'Snte.<sup>1</sup>', (0, YF, 0), parent=snte1, clase='grande snte')
S.etiqueta('clasico', 'Snte.', (FX, YF, ZC), clase='grande snte')
S.etiqueta('falla', 'abertura, falla', (0.28 + PERP[0] * 1.0, 3.75 + PERP[1] * 1.0, 0.6), clase='serif')
S.etiqueta('contexto', 'contexto (l. 156-157)', (CTR[0] + PERP[0] * (RP_C + 0.5), CTR[1] + PERP[1] * (RP_C + 0.5), 0.7), clase='nota')
EJ_SDO = (FX + 1.6, YF, -ZS)                 # a la derecha de Sdo.
EJ_SNTE1 = (-0.35, YF, 0.62)                 # sobre Snte.¹ (la flecha llega por debajo), algo a la izquierda: margen derecho en 16:9
S.etiqueta('ej_sdo', '«virilidad»', EJ_SDO, clase='sdo')
S.etiqueta('ej_snte1', '«el aguijón del leptosomático macrogenitoma»', EJ_SNTE1, parent=snte1, clase='snte')
S.etiqueta('porro_sdo', 'canal de desagüe', EJ_SDO, clase='sdo')
S.etiqueta('porro_tach', '<s>gárgola</s>  (significante codificado)', (FX, YF, 1.0), clase='tachado')
S.etiqueta('porro_snte1', 'flauta, fémur o falo', EJ_SNTE1, parent=snte1, clase='snte')
S.etiqueta('papaya_sdo', 'fuente', EJ_SDO, clase='sdo')
S.etiqueta('papaya_snte1', 'papaya', EJ_SNTE1, parent=snte1, clase='snte')
S.etiqueta('papaya_nota', 'en argot cubano, también el sexo femenino: erotiza la obra entera',
           (CTR[0] + PERP[0] * (RP_H + 0.55), CTR[1] + PERP[1] * (RP_H + 0.55), 0.75), clase='nota')

# ---------------------------------------------------------------- línea de tiempo
C = 'CONSTANT'
F = 1.0 / bb.FPS
X0, X1, CERO = (0.0001, 0.25, 0.25), (1, 1, 1), (0.0001, 0.0001, 0.0001)   # X0: la flecha nace fina (sin disco suelto)
# estado 2 (0.6 → 3.0 s): la flecha gira hacia la profundidad y Snte.¹ se aleja
S.clave(flecha_plana, 0.7, esc=1.0); S.clave(flecha_plana, 1.2, esc=0.0001)
S.clave(flecha_prof, 0, esc=CERO, interp=C); S.clave(flecha_prof, 1.0 - F, esc=CERO, interp=C)
S.clave(flecha_prof, 1.0, esc=X0); S.clave(flecha_prof, 2.6, esc=X1, interp=C)
S.mover(snte1, 0.8, 2.9, (DX, 0, 0.12), LEJOS)
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
# estado 4 (5.7 → 6.7 s): contexto
S.mostrar(ctx, 5.7, 6.7)
# estado 7 (8.0 → 8.8 s): el contexto neutro se vuelve velo cálido (papaya)
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


limbo('snte', [(0, True), (3.1, False), (3.8, True)], (FX, YF, ZS))
limbo('clasico', [(0, False), (3.1, True), (3.8, False)], (FX, YF, ZC))
limbo('falla', [(0, True), (3.1, False), (4.5, True)], tuple(bb.bpy.data.objects['lbl_falla'].location))
limbo('snte1', [(0, True), (3.1, False), (5.25, True)], (0, YF, 0), padre_escala=0.0001)  # hijo de snte1 (escala 0.0001 ahí)


# ---------------------------------------------------------------- ajustes del estudio (tema claro)
S.estudio = {
    'materiales': {
        'vidrio': {'color': '#7E918B', 'opacity': 0.06, 'roughness': 0.12, 'clearcoat': 1, 'envMapIntensity': 1.2},
        'calido': {'color': '#A3245F', 'opacity': 0.065, 'roughness': 0.25, 'emissive': '#A3245F',
                   'emissiveIntensity': 0.08, 'envMapIntensity': 0.8},
    },
    'sombra': 0.18,
}

# ---------------------------------------------------------------- estados
FRENTE = dict(cam=(0.08, -63.21, 9.71), look=(0.08, 0, -0.3), fov=4.8)
VOL = dict(cam=(-4.62, -10.63, 2.79), look=(-0.33, -0.02, -0.5), fov=24)
DIST = dict(cam=(0.1, -6.71, 1.91), look=(-0.94, 1.42, -0.3), fov=32)
CTX = dict(cam=(0.91, -7.49, 3.62), look=(-1.35, 3.14, -0.77), fov=32)

S.estado('Figura 1', 'La figura tal como la dibuja Sarduy: el significante que corresponde al significado queda <b>tachado</b>; otro, lejano, ocupa su lugar a distancia.',
         'Sarduy 1972 · figura 1 (l. 159-162)', etiquetas=['snte', 'sdo', 'snte1'], orbita=False, t1=0, **FRENTE)
S.estado('Volumen', 'Lo mismo, visto en volumen: la barra separa y a la vez une; el nombre tachado sigue ahí, como hueco.',
         'l. 151-157', etiquetas=['snte', 'sdo', 'snte1'], t1=0.5, **VOL)
S.estado('Distancia', 'La distancia semántica se vuelve distancia espacial: Snte.¹ no ocupa el hueco; funciona <em>desde lejos</em>.',
         'l. 154-157', etiquetas=['snte', 'sdo', 'snte1'], t1=3.0, pregunta='¿Dónde queda el nuevo significante respecto del hueco?', **DIST)
S.estado('Falla', 'Del arte clásico (adherencia de los dos términos del signo) a la <b>abertura</b> barroca. Mueve el deslizador.',
         '«Abertura, falla entre lo [nombrante] y lo nombrado» (l. 192)', etiquetas=['sdo', 'snte1', 'snte', 'clasico', 'falla'], t1=5.5,
         slider={'tipo': 'tiempo', 't0': 3.5, 't1': 5.5, 'etiqueta': 'distancia entre nombrante y nombrado',
                 'min_txt': 'adherencia clásica', 'max_txt': 'abertura barroca'}, **DIST)
S.estado('Contexto', 'El sustituto sólo significa dentro de un contexto que liga los dos términos a distancia.',
         '«sólo en el contexto erótico del relato funciona» (l. 156)', etiquetas=['snte', 'sdo', 'snte1', 'contexto'], t1=6.7, **CTX)
S.estado('Lezama', 'En <em>Paradiso</em>, el significante de «virilidad» es escamoteado y sustituido por otro, totalmente alejado.',
         'Lezama Lima, Paradiso · l. 151-157', etiquetas=['snte', 'sdo', 'ej_sdo', 'snte1', 'ej_snte1'], t1=6.7, **CTX)
S.estado('Porro', 'En la arquitectura de Ricardo Porro, el desagüe no se vuelve gárgola (el significante ya codificado) sino flauta, fémur o falo.',
         'l. 173-180', etiquetas=['snte', 'sdo', 'porro_sdo', 'porro_tach', 'snte1', 'porro_snte1'], t1=6.7, **CTX)
S.estado('Papaya', 'Una fuente con forma de papaya: la sustitución no es simple permutación, <b>erotiza la totalidad</b> de la obra.',
         'l. 180-186', etiquetas=['papaya_sdo', 'snte', 'sdo', 'snte1', 'papaya_snte1', 'papaya_nota'], t1=8.8, **CTX)

S.exportar()
