from comun import *
import random

W, H = 1700, 700
XS = [283, 850, 1417]
MY, RM, RV = 236, 118, 100     # centro del espejo, marco, vidrio
p = [cabecera('refl', W, H,
              'Tres reflejos',
              'Tres columnas, cada una con un espejo convexo esquemático (Sarduy 1972, l. 839-883). Reflejo reductor, '
              'propio de todo barroco: el espejo entero quiere totalizar, pero una mancha opaca le resiste. Reflejo '
              'significante, del barroco histórico: espejo entero, descentrado pero aún armónico, bajo un anillo de logos '
              'exterior (dios, rey). Reflejo estructural, del neobarroco: el espejo se fragmenta alrededor de un hueco, '
              'la carencia, y el logos queda como una pantalla; reflejo pulverizado.')]

p.append('<defs><radialGradient id="refl-vidrio" cx="42%" cy="38%" r="70%">'
         '<stop offset="0" style="stop-color:var(--azogue);stop-opacity:.55"/>'
         '<stop offset=".7" style="stop-color:var(--azogue);stop-opacity:.22"/>'
         '<stop offset="1" style="stop-color:var(--azogue);stop-opacity:.12"/></radialGradient></defs>')

# costuras de azogue
p.append('<g opacity=".3"><line class="s-azogue w3" x1="567" y1="40" x2="567" y2="660"/>'
         '<line class="s-azogue w3" x1="1133" y1="40" x2="1133" y2="660"/></g>')


def brillo(x):
    a0, a1 = math.radians(128), math.radians(162)
    r = RV - 20
    return (f'<path class="f-none s-perla w3 redondo" opacity=".55" d="M{n(x + r*math.cos(a0))} {n(MY - r*math.sin(a0))} '
            f'A{r} {r} 0 0 0 {n(x + r*math.cos(a1))} {n(MY - r*math.sin(a1))}"/>')


def espejo_entero(x):
    return (f'<circle cx="{x}" cy="{MY}" r="{RV}" fill="url(#refl-vidrio)"/>'
            f'<circle class="f-none s-nacar w4" cx="{x}" cy="{MY}" r="{RM}"/>'
            f'<circle class="f-none s-nacar w3" opacity=".45" cx="{x}" cy="{MY}" r="{RM - 12}"/>' + brillo(x))


def mancha(x, y, r, semilla):
    rnd = random.Random(semilla)
    k = 9
    radios = [r * rnd.uniform(.72, 1.18) for _ in range(k)]
    pts = [(x + radios[i] * math.cos(2 * math.pi * i / k), y + radios[i] * math.sin(2 * math.pi * i / k)) for i in range(k)]
    d = f'M{n((pts[0][0] + pts[1][0]) / 2)} {n((pts[0][1] + pts[1][1]) / 2)} '
    for i in range(k):
        a, b = pts[(i + 1) % k], pts[(i + 2) % k]
        d += f'Q{n(a[0])} {n(a[1])} {n((a[0] + b[0]) / 2)} {n((a[1] + b[1]) / 2)} '
    return d + 'Z'


def columna(i, pict, titulo, sub, lineas, ref):
    x = XS[i]
    g = [f'<g data-from="{i + 1}">', pict,
         txt(x, 444, titulo, 'neo f-perla', 40, 'middle'),
         txt(x, 484, sub, 'it f-azogue', 30, 'middle')]
    y = 546
    for l in lineas:
        g.append(txt(x, y, l, 'f-nacar', 28, 'middle'))
        y += 36
    g.append(txt(x, y + 14, ref, 'neo f-cian', 28, 'middle'))
    g.append('</g>')
    return '\n'.join(g)


# 1. reductor: entero, con una mancha opaca
x = XS[0]
pict1 = espejo_entero(x) + f'<path class="f-tinta" d="{mancha(x + 26, MY + 22, 34, 3)}"/>'
p.append(columna(0, pict1, 'Reductor', 'todo barroco',
                 ['quiere ser totalizante y minucioso;', 'algo «le opone su opacidad»'], 'l. 844-850'))

# 2. significante: entero, universo descentrado pero armónico, bajo un logos exterior
x = XS[1]
a, b = 64, 40
c = math.sqrt(a * a - b * b)
pict2 = (espejo_entero(x)
         + f'<ellipse class="f-none s-perla w3" opacity=".7" cx="{x + 8}" cy="{MY + 6}" rx="{a}" ry="{b}"/>'
         + f'<circle class="f-oro" cx="{n(x + 8 - c)}" cy="{MY + 6}" r="7"/>'
         + f'<circle class="f-none s-azogue w3" style="stroke-dasharray:4 4" cx="{n(x + 8 + c)}" cy="{MY + 6}" r="7"/>'
         + f'<ellipse class="f-none s-perla w6" opacity=".18" cx="{x}" cy="46" rx="78" ry="16"/>'
         + f'<ellipse class="f-none s-perla w3" cx="{x}" cy="46" rx="78" ry="16"/>'
         + ''.join(f'<line class="s-azogue w3 dash-fino" opacity=".6" x1="{x + dx}" y1="66" x2="{x + dx * 1.4}" y2="{MY - RM - 8}"/>'
                   for dx in (-44, 0, 44))
         + txt(x + 96, 56, 'logos', 'neo f-perla', 28))
p.append(columna(1, pict2, 'Significante', 'barroco histórico',
                 ['descentrado «pero aún armónico»;', 'logos exterior: dios, rey'], 'l. 852-867'))

# 3. estructural: fragmentos alrededor de un hueco; el logos, una pantalla
x = XS[2]
rnd = random.Random(5)
N = 7
cortes = [14 + k * 360 / N + rnd.uniform(-13, 13) for k in range(N)]
frag = []
for k in range(N):
    a0 = cortes[k] + 3
    a1 = (cortes[(k + 1) % N] + (360 if k == N - 1 else 0)) - 3
    am = math.radians((a0 + a1) / 2)
    off = rnd.uniform(9, 17)
    ox, oy = off * math.cos(am), -off * math.sin(am)
    rin = rnd.uniform(38, 50)
    pts_ext = [pol(x + ox, MY + oy, RV, a0 + (a1 - a0) * t / 6) for t in range(7)]
    mid_in = (a0 + a1) / 2 + rnd.uniform(-8, 8)
    pts_int = [pol(x + ox, MY + oy, rin, a1 - 2), pol(x + ox, MY + oy, rin * rnd.uniform(.8, 1.15), mid_in),
               pol(x + ox, MY + oy, rin, a0 + 2)]
    d = 'M' + ' L'.join(f'{n(px)} {n(py)}' for px, py in pts_ext + pts_int) + ' Z'
    frag.append(f'<path fill="url(#refl-vidrio)" class="s-nacar w3" style="stroke-linejoin:round" d="{d}"/>')
    # tramo del marco que acompaña al fragmento
    fx0, fy0 = pol(x + ox, MY + oy, RM, a0 + 2)
    fx1, fy1 = pol(x + ox, MY + oy, RM, a1 - 2)
    large = 1 if (a1 - a0) > 180 else 0
    frag.append(f'<path class="f-none s-nacar w4" d="M{n(fx0)} {n(fy0)} A{RM} {RM} 0 {large} 0 {n(fx1)} {n(fy1)}"/>')
# astillas sueltas: el reflejo se pulveriza
for k in range(5):
    am = 40 + k * 72 + rnd.uniform(-20, 20)
    rr = rnd.uniform(134, 148)
    cxs, cys = pol(x, MY, rr, am)
    t0 = math.radians(am + 90 + rnd.uniform(-35, 35))
    L, w = rnd.uniform(13, 17), rnd.uniform(5, 6.5)
    tri = [(cxs + L*math.cos(t0), cys - L*math.sin(t0)), (cxs - L*math.cos(t0), cys + L*math.sin(t0)),
           (cxs - w*math.sin(t0), cys - w*math.cos(t0))]
    frag.append('<path class="f-nacar" opacity=".75" d="M' + ' L'.join(f'{n(a_)} {n(b_)}' for a_, b_ in tri) + ' Z"/>')
pict3 = (''.join(frag)
         + f'<circle class="f-none s-bermellon w3" style="stroke-dasharray:6 6" cx="{x}" cy="{MY}" r="24"/>'
         + f'<rect class="f-perla s-perla w3" style="fill-opacity:.08" x="{x - 80}" y="34" width="160" height="26" rx="2"/>'
         + txt(x + 98, 56, 'pantalla', 'neo f-perla', 28))
p.append(columna(2, pict3, 'Estructural', 'neobarroco',
                 ['carencia; el logos, una pantalla;', 'reflejo «necesariamente pulverizado»'], 'l. 869-883'))
guardar('reflejos.svg', p)
