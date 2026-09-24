from comun import *

W, H = 1500, 620
CX, CY, R = 750, 440, 262
p = [cabecera('barrueco', W, H,
              'Barrueco: los étimos de «barroco» sobre un arco abierto',
              'La palabra «barroco» en el centro. Alrededor, un arco punteado abierto que termina en punta de flecha y '
              '«etc.»; sobre él aparecen, uno por paso, seis étimos o definiciones que Sarduy acumula (l. 24-35): '
              'la perla irregular (barrueco, berrueco), la roca o nódulo, el pintor Barocci, alumno de los Carracci, '
              'el silogismo escolástico Baroco, la «bizarrería chocante» de Littré y «lo estrambótico… el mal gusto» '
              'de Martínez Amador. Aparte, fuera del arco: «barro», juego fónico (l. 41), no étimo.')]

A0, A1 = 196, -16
x0, y0 = pol(CX, CY, R, A0)
x1, y1 = pol(CX, CY, R, A1)
p.append('<g>')
p.append(f'<path class="f-none s-nacar w3" style="stroke-dasharray:14 10" d="M{n(x0)} {n(y0)} A{R} {R} 0 1 1 {n(x1)} {n(y1)}"/>')
tang = math.degrees(math.atan2(math.cos(math.radians(A1)), math.sin(math.radians(A1))))
a = math.radians(tang)
p.append(punta(x1 + math.cos(a) * 26, y1 + math.sin(a) * 26, tang, L=26, W=10))
p.append(txt(x1 + 44, y1 + 40, 'etc.', 'f-nacar', 40))
p.append(txt(CX, CY + 22, 'barroco', 'serif it f-perla', 104, 'middle'))
p.append('</g>')

# (ángulo, anclaje, líneas [(texto, clases, tamaño)])
etimos = [
    (180, 'end',   [('perla irregular', 'f-perla', 36), ('barrueco, berrueco', 'it f-nacar', 30)]),
    (146, 'end',   [('roca, nódulo', 'f-perla', 36), ('lo nudoso, la piedra', 'it f-nacar', 30)]),
    (112, 'end',   [('Barocci (1528-1612)', 'f-perla', 36), ('alumno de los Carracci', 'f-azogue', 28)]),
    (68,  'start', [('Baroco', 'f-perla', 36), ('silogismo escolástico', 'f-azogue', 28)]),
    (34,  'start', [('«bizarrería chocante»', 'it f-magenta', 36), ('Littré', 'neo f-azogue', 28)]),
    (0,   'start', [('«lo estrambótico…', 'it f-magenta', 36), ('el mal gusto»', 'it f-magenta', 36),
                    ('Martínez Amador', 'neo f-azogue', 28)]),
]
for i, (th, anc, lineas) in enumerate(etimos, 1):
    nx, ny = pol(CX, CY, R, th)
    lx, ly = pol(CX, CY, R + 34, th)
    alto = sum(s * 1.18 for _, _, s in lineas)
    if th in (180, 0):
        yb = ny - alto / 2 + lineas[0][2] * 0.9
        lx = nx + (-30 if anc == 'end' else 30)
    else:
        yb = ly - alto + lineas[0][2] * 0.95 + 6
    g = [f'<g data-from="{i}">',
         f'<circle class="f-nacar" cx="{n(nx)}" cy="{n(ny)}" r="9"/>']
    y = yb
    for (s, c, sz) in lineas:
        g.append(txt(lx, y, s, c, sz, anc))
        y += sz * 1.18
    g.append('</g>')
    p.append('\n'.join(g))

# aparte, fuera del arco: barro (fondo de barro, sin punto sobre el arco)
p.append('<g data-from="7">')
wb = anchos([('barro', 'serif it', 44)])[0]
p.append(f'<circle class="f-tierra" cx="{n(1488 - wb - 22)}" cy="549" r="9"/>')
p.append(txt(1488, 562, 'barro', 'serif it f-nacar', 44, 'end'))
p.append(txt(1488, 602, 'juego fónico (l. 41), no étimo', 'f-azogue', 28, 'end'))
p.append('</g>')

p.append(txt(12, 604, 'Sarduy 1972 · l. 24-35', 'neo f-azogue', 28))
guardar('barrueco.svg', p)
