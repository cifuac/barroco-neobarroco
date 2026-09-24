from comun import *

W, H = 1600, 520
CX, CY, RX, RY = 800, 410, 640, 250
p = [cabecera('gen', W, H,
              'Genealogía del nombre: del Barroco al Transbarroco',
              'Un arco punteado abierto que termina en punta de flecha y «etc.». Sobre él aparecen, uno por paso, los '
              'nombres que según Díaz (2011, nota 13, l. 1366-1375) se engendran uno a otro: Barroco; Neobarroco '
              '(Haroldo de Campos 1955, Sarduy 1972); Neobarroso (Perlongher); Neoborroso (Kamenszain); Hiperbarroco; '
              'Transbarroco (Haroldo de Campos 2004).')]

A0, A1 = 191, -11
x0, y0 = pol(CX, CY, RX, A0, RY)
x1, y1 = pol(CX, CY, RX, A1, RY)
p.append('<g>')
p.append(f'<path class="f-none s-nacar w3" style="stroke-dasharray:14 10" '
         f'd="M{n(x0)} {n(y0)} A{RX} {RY} 0 1 1 {n(x1)} {n(y1)}"/>')
# tangente al final (sentido horario en pantalla)
t = math.radians(A1)
tang = math.degrees(math.atan2(RY * math.cos(t), RX * math.sin(t)))
a = math.radians(tang)
p.append(punta(x1 + math.cos(a) * 26, y1 + math.sin(a) * 26, tang, L=26, W=10))
p.append(txt(x1 + 40, y1 + 34, 'etc.', 'f-nacar', 40))
p.append(txt(CX, 500, 'Díaz 2011, nota 13 · l. 1366-1375', 'neo f-azogue', 28, 'middle'))
p.append('</g>')

nodos = [pol(CX, CY, RX, ang, RY) for ang in (170, 138, 107, 73, 42, 10)]

datos = [
    ('Barroco', 'serif it f-perla', 52, []),
    ('Neobarroco', 'neo f-perla', 36, ['Haroldo de Campos 1955', 'Sarduy 1972']),
    ('Neobarroso', 'neo f-perla', 36, ['Perlongher']),
    ('Neoborroso', 'neo f-perla', 36, ['Kamenszain']),
    ('Hiperbarroco', 'neo f-perla', 36, []),
    ('Transbarroco', 'neo f-perla', 36, ['Haroldo de Campos 2004']),
]
# (anclaje, dx, dy del nombre, subtítulos hacia abajo o hacia arriba)
pos_rot = [('start', 28, 13, 1), ('start', 28, 34, 1), ('middle', 0, -63, 1),
           ('middle', 0, -63, 1), ('end', -28, 34, 1), ('end', -28, 13, 1)]
for k, ((nx, ny), (nom, cls, sz, subs), (anc, dx, dy, _)) in enumerate(zip(nodos, datos, pos_rot), 1):
    lx, ly = nx + dx, ny + dy
    g = [f'<g data-from="{k}">', f'<circle class="f-nacar" cx="{n(nx)}" cy="{n(ny)}" r="10"/>',
         txt(lx, ly, nom, cls, sz, anc)]
    yy = ly + 34
    for s_ in subs:
        g.append(txt(lx, yy, s_, 'f-azogue', 28, anc))
        yy += 32
    g.append('</g>')
    p.append('\n'.join(g))
guardar('genealogia.svg', p)
