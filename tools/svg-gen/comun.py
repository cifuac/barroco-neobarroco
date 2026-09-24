"""Utilidades comunes para generar los SVG en línea de la clase (Sarduy 1972).

Regenerar (con el servidor local en http://localhost:8765/ sirviendo docs/):
    cd repo/tools/svg-gen && python3 fig2.py          # escribe docs/svg/fig2.svg
Comprobar textos (cajas, solapes, fuera del viewBox):
    node measure.mjs fig2.svg
Los anchos de texto se miden en el navegador con las fuentes reales (anchos.mjs).
"""
import math, json, subprocess, os

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'docs', 'svg')) + '/'
AQUI = os.path.dirname(os.path.abspath(__file__))


def n(v):
    """Número compacto para atributos."""
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def sup(s):
    return f'<tspan baseline-shift="super" font-size="60%">{s}</tspan>'


def pol(cx, cy, r, ang, ry=None):
    """Punto sobre círculo/elipse; ang en grados matemáticos (y hacia arriba)."""
    ry = r if ry is None else ry
    a = math.radians(ang)
    return cx + r * math.cos(a), cy - ry * math.sin(a)


def punta(tx, ty, ang, L=26, W=10, cls='f-nacar', extra=''):
    """Punta de flecha llena con muesca; ang = dirección de avance en grados de pantalla (0 = derecha, 90 = abajo)."""
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    bx, by = tx - dx * L, ty - dy * L
    px, py = -dy, dx
    mx, my = tx - dx * L * 0.78, ty - dy * L * 0.78
    return (f'<path class="{cls}" {extra}d="M{n(tx)} {n(ty)} L{n(bx + px * W)} {n(by + py * W)} '
            f'L{n(mx)} {n(my)} L{n(bx - px * W)} {n(by - py * W)} Z"/>')


def ang_pantalla(x1, y1, x2, y2):
    return math.degrees(math.atan2(y2 - y1, x2 - x1))


def txt(x, y, s, cls='', size=40, anchor=None, extra=''):
    a = f' text-anchor="{anchor}"' if anchor else ''
    c = f' class="{cls}"' if cls else ''
    return f'<text{c} x="{n(x)}" y="{n(y)}" font-size="{size}"{a}{extra}>{s}</text>'


def anchos(items):
    """items: lista de (texto, clases, tamaño) -> anchos medidos en el navegador con las fuentes reales."""
    js = json.dumps([{'t': t, 'cls': c, 'size': s} for t, c, s in items])
    r = subprocess.run(['node', os.path.join(AQUI, 'anchos.mjs'), js], capture_output=True, text=True)
    return json.loads(r.stdout.strip().splitlines()[-1])


def cabecera(clave, W, H, titulo, desc):
    return (f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-labelledby="{clave}-titulo {clave}-desc">\n'
            f'<title id="{clave}-titulo">{titulo}</title>\n'
            f'<desc id="{clave}-desc">{desc}</desc>\n')


def guardar(nombre, partes):
    s = '\n'.join(partes) + '\n</svg>\n'
    with open(OUT + nombre, 'w', encoding='utf-8') as fh:
        fh.write(s)
    print('escrito', nombre, len(s), 'bytes')
