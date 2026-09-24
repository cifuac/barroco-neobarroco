from comun import *

W, H = 1400, 780
CX, CY = 700, 370
p = [cabecera('mun', W, H,
              'La metáfora al cuadrado: muñecas rusas',
              'Marcos anidados e incompletos, abiertos en una esquina, que aparecen de dentro hacia fuera (Sarduy 1972, '
              'l. 115-132). 0: nivel denotativo, supuesto, un núcleo punteado con la palabra «halcones». 1: la metáfora '
              'poética. 2: Góngora, Soledades: «raudos torbellinos de Noruega». 3: Dámaso Alonso, 1956, que la descifra. '
              '4: Sarduy, 1972, que comenta a Alonso. 5: Díaz, 2011, que anota a Sarduy. 6: esta clase.')]

capas = [  # (número, rótulo, clases de trazo, clases del número, clases del rótulo)
    (0, 'denotativo (supuesto)', 's-azogue dash-fino', 'f-azogue', 'f-azogue'),
    (1, 'metáfora poética', 's-nacar', 'f-nacar', 'f-nacar'),
    (2, 'Góngora, <tspan class="it">Soledades</tspan>', 's-nacar', 'f-magenta', 'f-perla'),
    (3, 'Dámaso Alonso, 1956', 's-nacar', 'f-nacar', 'f-perla'),
    (4, 'Sarduy, 1972', 's-perla', 'f-perla', 'f-perla'),
    (5, 'Díaz, 2011', 's-azogue', 'f-azogue', 'f-azogue'),
    (6, 'esta clase', 's-cian', 'f-cian', 'f-cian'),
]
rot = [f'<tspan class="neo" font-size="28">{k}</tspan>  {r}' for k, r, *_ in capas]
anchos_rot = anchos([(r, '', 30) for r in rot])
CITA = '«raudos torbellinos de Noruega»'
w_cita = anchos([(CITA, 'it', 30)])[0]

RAD = 16


def marco(L, T, R, B, gap_top, gap_bot=None):
    """Marco con esquinas redondeadas, abierto en la esquina inferior derecha y con hueco superior para el rótulo."""
    r = RAD
    g0, g1 = gap_top
    d = [f'M{n(g1)} {T} L{R - r} {T} Q{R} {T} {R} {T + r} L{R} {B - 64}',            # tramo derecho, se corta
         f'M{R - 104} {B} ']                                                         # reanuda en el borde inferior
    if gap_bot:
        b0, b1 = gap_bot
        d.append(f'L{n(b1)} {B} M{n(b0)} {B} ')
    d.append(f'L{L + r} {B} Q{L} {B} {L} {B - r} L{L} {T + r} Q{L} {T} {L + r} {T} L{n(g0)} {T}')
    return ''.join(d)


for i, (k, r, sc, nc, rc) in enumerate(capas):
    hw, hh = 220 + 75 * k, 62 + 46 * k
    L, R, T, B = CX - hw, CX + hw, CY - hh, CY + hh
    lx = L + 30
    gap = (lx - 12, lx + anchos_rot[i] + 12)
    gap_b = (L + 30 - 12, L + 30 + w_cita + 12) if k == 2 else None
    op = {1: '.6', 2: '.75', 3: '.85'}.get(k, '1')
    g = [f'<g data-from="{k}">' if k else '<g>',
         f'<path class="f-none {sc} w3 redondo" opacity="{op}" d="{marco(L, T, R, B, gap, gap_b)}"/>',
         txt(lx, T + 10, f'<tspan class="neo {nc}" font-size="28">{k}</tspan>  {r}', rc, 30)]
    if k == 0:
        g.append(txt(CX, CY + 14, 'halcones', 'it f-nacar', 44, 'middle'))
    if k == 2:
        g.append(txt(L + 30, B + 10, CITA, 'it f-magenta', 30))
    g.append('</g>')
    p.append('\n'.join(g))

p.append(txt(1370, 768, 'Sarduy 1972 · l. 115-132', 'neo f-azogue', 28, 'end'))
guardar('muniecas.svg', p)
