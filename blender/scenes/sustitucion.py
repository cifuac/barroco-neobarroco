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
TW, TH, TD = 1.15, 0.42, 0.14   # tablilla

fig = bb.grupo('figura')
# Sdo.: tablilla de oro bajo la barra
sdo = bb.caja('sdo', (TW, TD, TH), (FX, 0, -0.36), M('significado'), fig, bevel=0.025)
barra = bb.caja('barra', (TW * 1.22, 0.06, 0.045), (FX, 0, 0.0), M('lamina'), fig, bevel=0.01)
# Snte. (tachado): tablilla de nácar sobre la barra + tachadura bermellón
snte = bb.caja('snte', (TW, TD, TH), (FX, 0, 0.36), M('significante'), fig, bevel=0.025)
tach = bb.caja('tachadura', (TW * 1.18, 0.05, 0.05), (FX, -TD / 2 - 0.03, 0.36), M('ausencia'), fig)
tach.rotation_euler = (0, math.radians(-12), 0)
# «clásico»: significante sin tachar, adherido (sólo visible en la transición de la falla)
clasico = bb.caja('snte_clasico', (TW, TD, TH), (FX, 0, 0.36), M('significante', 'significante_clasico'), fig, bevel=0.025)

# flecha plana (figura original): de la fracción hacia la derecha, a la altura de la barra
p0 = (FX + 0.85, 0, 0.12)
p1 = (DX - 0.78, 0, 0.12)
flecha_plana = bb.grupo('flecha_plana', p0, fig)
bb.polilinea_punteada('flecha_plana_guiones', [(0, 0, 0), (p1[0] - p0[0], 0, 0)], guion=0.2, hueco=0.13, r=0.028,
                      material=M('trayecto'), parent=flecha_plana, flecha={'r': 0.1, 'largo': 0.26})
# Snte.¹ en su lugar plano
snte1 = bb.grupo('snte1', (DX, 0, 0.12))
bb.caja('snte1_tablilla', (TW, TD, TH), (0, 0, 0), M('significante'), snte1, bevel=0.025)

# flecha profunda: la distancia semántica se vuelve distancia espacial
LEJOS = (2.6, 7.5, 0.12)
d = (LEJOS[0] - p0[0], LEJOS[1] - p0[1], 0)
L = math.hypot(d[0], d[1])
ang = math.atan2(d[1], d[0])
flecha_prof = bb.grupo('flecha_profunda', p0)
flecha_prof.rotation_euler = (0, 0, ang)
bb.polilinea_punteada('flecha_profunda_guiones', [(0, 0, 0), (L - 0.85, 0, 0)], guion=0.22, hueco=0.14, r=0.03,
                      material=M('trayecto'), parent=flecha_prof, flecha={'r': 0.11, 'largo': 0.28})

# contexto: envolvente translúcida que liga los dos términos
ctx = bb.grupo('contexto', ((FX + LEJOS[0]) / 2, LEJOS[1] / 2, 0.1))
env = bb.esfera('contexto_envolvente', 1.0, (0, 0, 0), M('vidrio'), ctx, subdiv=5)
env.scale = (3.0, 4.9, 1.0)
env.rotation_euler = (0, 0, ang - math.radians(90) + math.radians(8))

# velo cálido (papaya: erotiza la totalidad de la obra)
halo = bb.grupo('halo', ((FX + LEJOS[0]) / 2, LEJOS[1] / 2, 0.1))
hv = bb.esfera('halo_velo', 1.0, (0, 0, 0), M('calido'), halo, subdiv=5)
hv.scale = (3.4, 5.4, 1.3)
hv.rotation_euler = (0, 0, ang - math.radians(90) + math.radians(8))

# ---------------------------------------------------------------- etiquetas (anclas)
S.etiqueta('snte', '<s>Snte.</s>', (FX, -0.25, 0.36), clase='grande tachado')
S.etiqueta('sdo', 'Sdo.', (FX, -0.25, -0.36), clase='grande sdo')
S.etiqueta('snte1', 'Snte.<sup>1</sup>', (0, -0.25, 0), parent=snte1, clase='grande snte')
S.etiqueta('clasico', 'Snte.', (FX, -0.3, 0.36), clase='grande snte')
S.etiqueta('falla', 'abertura, falla', (0.2, 3.6, 0.9), clase='serif')
S.etiqueta('contexto', 'contexto (l. 156-157)', (-2.6, 4.2, 1.6), clase='nota')
S.etiqueta('ej_sdo', '«virilidad»', (FX, -0.3, -0.95), clase='sdo')
S.etiqueta('ej_snte1', '«el aguijón del leptosomático macrogenitoma»', (0, -0.3, -0.62), parent=snte1, clase='snte')
S.etiqueta('porro_sdo', 'canal de desagüe', (FX, -0.3, -0.95), clase='sdo')
S.etiqueta('porro_tach', '<s>gárgola</s>  (significante codificado)', (FX, -0.3, 0.95), clase='tachado')
S.etiqueta('porro_snte1', 'flauta, fémur o falo', (0, -0.3, -0.62), parent=snte1, clase='snte')
S.etiqueta('papaya_sdo', 'fuente', (FX, -0.3, -0.95), clase='sdo')
S.etiqueta('papaya_snte1', 'papaya', (0, -0.3, -0.62), parent=snte1, clase='snte')
S.etiqueta('papaya_nota', 'en argot cubano, también el sexo femenino: erotiza la obra entera', (0.0, 1.5, -0.45), clase='nota')

# ---------------------------------------------------------------- línea de tiempo
C = 'CONSTANT'
X0, X1 = (0.0001, 1, 1), (1, 1, 1)
# estado 2 (0.6 → 3.0 s): la flecha gira hacia la profundidad y Snte.¹ se aleja
S.clave(flecha_plana, 0.7, esc=1.0); S.clave(flecha_plana, 1.2, esc=0.0001)
S.clave(flecha_prof, 0, esc=X0, interp=C); S.clave(flecha_prof, 1.0, esc=X0); S.clave(flecha_prof, 2.6, esc=X1, interp=C)
S.mover(snte1, 0.8, 2.9, (DX, 0, 0.12), LEJOS)
S.clave(snte1, 0, esc=1.0, interp=C)
S.clave(clasico, 0, esc=0.0001, interp=C)
S.clave(tach, 0, esc=1.0, interp=C)
S.clave(snte, 0, esc=1.0, interp=C)
# estado 3 (3.0 → 5.5 s): adherencia clásica → abertura barroca (deslizador entre 3.5 y 5.5)
S.salto(tach, 3.1, 1.0, 0.0001); S.salto(snte, 3.1, 1.0, 0.0001); S.salto(clasico, 3.1, 0.0001, 1.0)
S.salto(flecha_prof, 3.1, X1, X0); S.salto(snte1, 3.1, 1.0, 0.0001)
#   3.5 → 4.2: el significante es escamoteado (la tachadura cae sobre él)
S.salto(clasico, 3.8, 1.0, 0.0001); S.salto(snte, 3.8, 0.0001, 1.0)
S.clave(tach, 3.8, esc=0.0001); S.clave(tach, 4.2, esc=1.0)
#   4.3 → 5.5: la flecha crece hacia lo lejos y aparece otro nombrante
S.clave(flecha_prof, 4.3, esc=X0); S.clave(flecha_prof, 5.2, esc=X1)
S.clave(snte1, 5.0, esc=0.0001); S.clave(snte1, 5.5, esc=1.0)
# estado 4 (5.7 → 6.7 s): contexto
S.mostrar(ctx, 5.7, 6.7)
# estado 7 (8.0 → 8.8 s): velo cálido (papaya)
S.mostrar(halo, 8.0, 8.8)

# ---------------------------------------------------------------- estados
FRENTE = dict(cam=(0.15, -64, 0.35), look=(0.15, 0, 0.35), fov=5.6)
OBL = dict(cam=(-4.6, -6.2, 2.6), look=(0.2, 2.3, -0.35), fov=33)
LADO = dict(cam=(-3.2, -8.8, 1.7), look=(0.9, 3.0, -0.1), fov=35)
ALTO = dict(cam=(-1.2, -7.6, 9.4), look=(0.5, 2.7, -0.4), fov=40)

S.estado('Figura 1', 'La figura tal como la dibuja Sarduy: el significante que corresponde al significado queda <b>tachado</b>; otro, lejano, ocupa su lugar a distancia.',
         'Sarduy 1972 · figura 1 (l. 159-162)', etiquetas=['snte', 'sdo', 'snte1'], orbita=False, t1=0, **FRENTE)
S.estado('Volumen', 'Lo mismo, visto en volumen: la barra separa y a la vez une; el nombre tachado sigue ahí, como hueco.',
         'l. 151-157', etiquetas=['snte', 'sdo', 'snte1'], t1=0.5, **OBL)
S.estado('Distancia', 'La distancia semántica se vuelve distancia espacial: Snte.¹ no ocupa el hueco; funciona <em>desde lejos</em>.',
         'l. 154-157', etiquetas=['snte', 'sdo', 'snte1'], t1=3.0, pregunta='¿Dónde queda el nuevo significante respecto del hueco?', **OBL)
S.estado('Falla', 'Del arte clásico (adherencia de los dos términos del signo) a la <b>abertura</b> barroca. Mueve el deslizador.',
         '«Abertura, falla entre lo [nombrante] y lo nombrado» (l. 192)', etiquetas=['sdo', 'snte1', 'snte', 'falla'], t1=5.5,
         slider={'tipo': 'tiempo', 't0': 3.5, 't1': 5.5, 'etiqueta': 'distancia entre nombrante y nombrado',
                 'min_txt': 'adherencia clásica', 'max_txt': 'abertura barroca'}, **LADO)
S.estado('Contexto', 'El sustituto sólo significa dentro de un contexto que liga los dos términos a distancia.',
         '«sólo en el contexto erótico del relato funciona» (l. 156)', etiquetas=['snte', 'sdo', 'snte1', 'contexto'], t1=6.7, **ALTO)
S.estado('Lezama', 'En <em>Paradiso</em>, el significante de «virilidad» es escamoteado y sustituido por otro, totalmente alejado.',
         'Lezama Lima, Paradiso · l. 151-157', etiquetas=['snte', 'ej_sdo', 'snte1', 'ej_snte1'], t1=6.7, **OBL)
S.estado('Porro', 'En la arquitectura de Ricardo Porro, el desagüe no se vuelve gárgola (el significante ya codificado) sino flauta, fémur o falo.',
         'l. 173-180', etiquetas=['porro_sdo', 'porro_tach', 'snte1', 'porro_snte1'], t1=6.7, **OBL)
S.estado('Papaya', 'Una fuente con forma de papaya: la sustitución no es simple permutación, <b>erotiza la totalidad</b> de la obra.',
         'l. 180-186', etiquetas=['papaya_sdo', 'snte', 'snte1', 'papaya_snte1', 'papaya_nota'], t1=8.8, **ALTO)

S.exportar()
