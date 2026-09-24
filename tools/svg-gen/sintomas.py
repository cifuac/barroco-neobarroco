from comun import *
import random

W, H = 1728, 760
p = [cabecera('sint', W, H,
              'Seis síntomas de un corte epistémico',
              'Seis pictogramas, cada uno con un estado anterior en gris y el posterior en color (Sarduy 1972, l. 55-71). '
              'Iglesia: del eje único a varios trayectos, un laberinto. Ciudad: pierde su trama ortogonal y sus fosos, '
              'ríos y murallas; queda una trama irregular. Literatura: el renglón recto se enrosca, deja el nivel '
              'denotativo. Astros: del círculo con un centro a la elipse de Kepler con dos focos, uno vacío. Harvey: '
              'la circulación de la sangre. Dios: el punto central se dispersa en cogitos y mónadas.')]

ANTES = 'class="f-none s-azogue w3 redondo" opacity=".75"'
LIN = 'class="f-none s-nacar w3 redondo"'
CIAN = 'class="f-none s-cian w3 redondo"'


def pos(x, y):
    return f'transform="translate({n(x)} {n(y)})"'


# ---------- pictogramas en coordenadas locales (centro 0,0) ----------
def iglesia_antes():
    return (f'<path {ANTES} d="M-12 70 L-44 70 L-44 -58 L-20 -58 A20 20 0 0 1 20 -58 L44 -58 L44 70 L12 70"/>'
            f'<line class="f-none s-azogue w3 dash-fino" opacity=".75" x1="0" y1="62" x2="0" y2="-54"/>'
            + punta(0, -70, -90, L=16, W=7, cls='f-azogue', extra='opacity=".75" '))


def iglesia_despues():
    s = [f'<path {LIN} d="M18 92 L82 92 L82 58 A20 20 0 0 0 82 18 L82 -18 A20 20 0 0 0 82 -58 L82 -84 L34 -84 '
         f'A34 34 0 0 0 -34 -84 L-82 -84 L-82 -58 A20 20 0 0 0 -82 -18 L-82 18 A20 20 0 0 0 -82 58 L-82 92 L-18 92"/>']
    rutas = ['M0 96 C -10 60, -70 70, -86 38',
             'M0 96 C 20 40, -60 10, -88 -38',
             'M0 96 C 30 60, 70 70, 86 38',
             'M0 96 C -30 20, 70 10, 88 -38',
             'M0 96 C 40 20, -40 -20, 0 -60 S 10 -100, 0 -104']
    for r in rutas:
        s.append(f'<path {CIAN} d="{r}"/>')
    for (x, y) in [(-86, 38), (-88, -38), (86, 38), (88, -38), (0, -104)]:
        s.append(f'<circle class="f-cian" cx="{x}" cy="{y}" r="5"/>')
    return ''.join(s)


def ciudad_antes():
    s = [f'<rect {ANTES} x="-46" y="-46" width="92" height="92"/>',
         f'<rect class="f-none s-azogue w3 dash-fino" opacity=".7" x="-58" y="-58" width="116" height="116"/>']
    for v in (-23, 0, 23):
        s.append(f'<line class="s-azogue w3" opacity=".6" x1="{v}" y1="-46" x2="{v}" y2="46"/>')
        s.append(f'<line class="s-azogue w3" opacity=".6" x1="-46" y1="{v}" x2="46" y2="{v}"/>')
    s.append(f'<path {ANTES} d="M-78 -70 C -66 -40, -86 -20, -72 10 S -80 50, -70 76"/>')
    return ''.join(s)


def ciudad_despues():
    P = [(-96, -72), (-38, -86), (22, -74), (88, -90), (-82, -14), (-24, -32), (38, -20), (98, -38),
         (-102, 46), (-48, 30), (6, 42), (62, 18), (104, 58), (-68, 92), (-8, 96), (52, 86)]
    E = [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (8, 9), (9, 10), (10, 11), (11, 12), (13, 14), (14, 15),
         (0, 4), (1, 5), (2, 6), (3, 7), (4, 9), (5, 10), (6, 11), (7, 12), (9, 13), (10, 14), (11, 15), (12, 15),
         (1, 6), (9, 5)]
    s = []
    for a, b in E:
        s.append(f'<line class="s-nacar w3 redondo" x1="{P[a][0]}" y1="{P[a][1]}" x2="{P[b][0]}" y2="{P[b][1]}"/>')
    for a, (x, y) in [(3, (126, -108)), (8, (-130, 64)), (14, (-14, 126)), (0, (-120, -98))]:
        s.append(f'<line class="s-nacar w3 redondo" x1="{P[a][0]}" y1="{P[a][1]}" x2="{x}" y2="{y}"/>')
    return ''.join(s)


def literatura_antes():
    return ''.join(f'<line {ANTES} x1="-56" y1="{y}" x2="{x2}" y2="{y}"/>' for y, x2 in [(-30, 56), (0, 56), (30, 20)])


def espiral(cx, cy, r0, r1, vueltas, fi0=90):
    pts = []
    N = 160
    for i in range(N + 1):
        t = i / N
        fi = math.radians(fi0 - 360 * vueltas * t)
        r = r0 + (r1 - r0) * t
        pts.append((cx + r * math.cos(fi), cy + r * math.sin(fi)))
    return pts


def literatura_despues():
    pts = [(-120, 46), (40, 46)] + espiral(40, -8, 54, 6, 2.1)
    d = 'M' + ' L'.join(f'{n(x)} {n(y)}' for x, y in pts)
    return (f'<line class="f-none s-azogue w3 dash-fino" opacity=".6" x1="40" y1="46" x2="140" y2="46"/>'
            f'<path {LIN} d="{d}"/>')


def astros_antes():
    return (f'<circle {ANTES} r="50"/>'
            f'<circle class="f-azogue" opacity=".75" r="6"/>')


def astros_despues():
    a, b = 108, 72
    c = math.sqrt(a * a - b * b)
    px, py = a * math.cos(math.radians(62)), -b * math.sin(math.radians(62))
    return (f'<ellipse {LIN} rx="{a}" ry="{b}"/>'
            f'<circle class="f-oro" cx="{n(-c)}" cy="0" r="12"/>'
            f'<circle class="f-none s-azogue w3" style="stroke-dasharray:5 5" cx="{n(c)}" cy="0" r="11"/>'
            f'<circle class="f-nacar" cx="{n(px)}" cy="{n(py)}" r="6"/>')


def harvey_antes():
    return (f'<line {ANTES} x1="0" y1="-44" x2="0" y2="44"/>'
            + punta(0, -60, -90, L=16, W=7, cls='f-azogue', extra='opacity=".75" ')
            + punta(0, 60, 90, L=16, W=7, cls='f-azogue', extra='opacity=".75" '))


def harvey_despues():
    d = ('M0 -18 C 44 -30, 40 -96, 0 -96 C -40 -96, -44 -30, 0 -18 '
         'C 96 -4, 104 100, 0 100 C -104 100, -96 -4, 0 -18')
    return (f'<path {CIAN} d="{d}"/>'
            + punta(-10, -96, 180, L=18, W=8, cls='f-cian')
            + punta(-10, 100, 180, L=18, W=8, cls='f-cian')
            + '<path class="f-nacar" d="M0 -30 L12 -18 L0 -6 L-12 -18 Z"/>')


def dios_antes():
    return (f'<circle class="f-oro" opacity=".85" r="13"/>'
            f'<circle class="f-none s-azogue w3" opacity=".75" r="30"/>')


def dios_despues():
    rnd = random.Random(7)
    pts = []
    while len(pts) < 24:
        x, y = rnd.uniform(-118, 118), rnd.uniform(-100, 100)
        if (x / 118) ** 2 + (y / 100) ** 2 > 1:
            continue
        if all(math.hypot(x - a, y - b) > 34 for a, b in pts):
            pts.append((x, y))
    s = []
    for i, (x, y) in enumerate(pts):
        if i % 8 == 0:
            s.append(f'<circle class="f-oro" cx="{n(x)}" cy="{n(y)}" r="5"/>')
        elif i % 3 == 0:
            s.append(f'<circle class="f-none s-nacar w3" cx="{n(x)}" cy="{n(y)}" r="7"/>'
                     f'<circle class="f-nacar" cx="{n(x)}" cy="{n(y)}" r="2.5"/>')
        else:
            s.append(f'<circle class="f-nacar" cx="{n(x)}" cy="{n(y)}" r="4"/>')
    return ''.join(s)


celdas = [
    ('Iglesia', '', 'del eje único a varios trayectos', iglesia_antes, iglesia_despues),
    ('Ciudad', '', 'pierde fosos, ríos y murallas', ciudad_antes, ciudad_despues),
    ('Literatura', '', 'el renglón recto se enrosca', literatura_antes, literatura_despues),
    ('Astros', 'Kepler 1609', 'el centro único se hace doble', astros_antes, astros_despues),
    ('Harvey', '1628', 'la circulación de la sangre', harvey_antes, harvey_despues),
    ('Dios', '', 'se dispersa en cogitos y mónadas', dios_antes, dios_despues),
]
XS = [288, 864, 1440]
YS = [158, 540]
for i, (tit, fecha, desc, fa, fd) in enumerate(celdas):
    cx, cy = XS[i % 3], YS[i // 3]
    g = [f'<g data-from="{i + 1}">',
         f'<g {pos(cx - 140, cy)}>{fa()}</g>',
         f'<line class="s-azogue w3" opacity=".7" x1="{cx - 72}" y1="{cy}" x2="{cx - 44}" y2="{cy}"/>',
         punta(cx - 30, cy, 0, L=14, W=6, cls='f-azogue', extra='opacity=".7" '),
         f'<g {pos(cx + 90, cy)}>{fd()}</g>']
    t = tit + (f' <tspan class="f-azogue" font-size="28">· {fecha}</tspan>' if fecha else '')
    g.append(txt(cx, cy + 172, t, 'neo f-perla', 36, 'middle'))
    g.append(txt(cx, cy + 212, desc, 'f-nacar', 28, 'middle'))
    g.append('</g>')
    p.append('\n'.join(g))

# costuras finas entre celdas
p.append('<g opacity=".25">'
         '<line class="s-azogue w3" x1="576" y1="40" x2="576" y2="720"/>'
         '<line class="s-azogue w3" x1="1152" y1="40" x2="1152" y2="720"/>'
         '<line class="s-azogue w3" x1="60" y1="398" x2="1668" y2="398"/></g>')
guardar('sintomas.svg', p)
