from comun import *

W, H = 1600, 420
p = [cabecera('fig3', W, H,
              'Figura 3 de Sarduy (1972): permutación y condensación',
              'Dos esquemas lado a lado. A la izquierda, «Permutación»: la cadena «Fonema 1… Fonema 2… etc.» bajo un '
              'corchete rotulado «Significante 1» y la cadena «F 1… F 2… etc.» bajo otro corchete rotulado «Snte. 2»; '
              'ambos sobre una única barra larga con «Significado» debajo: dos cadenas fonéticas y un solo significado. '
              'A la derecha, «Condensación»: Snte. 1 y Snte. 2 a los lados de un signo central, Snte. 3 sobre Sdo.; '
              'entre cada lado y el centro, un par de flechas opuestas. Paso 1: «vaya un gallo» y «valla un gayo» '
              'intercambian y y ll. Paso 2: AMO, AMOSCLAVO, ESCLAVO. Paso 3: MÁQUINA, MAQUINOSCRITO, MANUSCRITO '
              '(Cabrera Infante, l. 341-342).')]


def corchete(x1, x2, yb, yt, r=12):
    return (f'<path class="f-none s-nacar w3 redondo" d="M{x1} {yt} L{x1} {yb-r} Q{x1} {yb} {x1+r} {yb} '
            f'L{x2-r} {yb} Q{x2} {yb} {x2} {yb-r} L{x2} {yt}"/>')


def flecha(xa, ya, xb, yb, cls='s-nacar', fcls='f-nacar'):
    ang = ang_pantalla(xa, ya, xb, yb)
    a = math.radians(ang)
    return (f'<line class="{cls} w3" x1="{n(xa)}" y1="{n(ya)}" x2="{n(xb - math.cos(a)*14)}" y2="{n(yb - math.sin(a)*14)}"/>'
            + punta(xb, yb, ang, L=20, W=8, cls=fcls))


# --- Figura literal ---
p.append('<g>')
# Permutación
p.append(txt(30, 56, 'Permutación', 'it f-nacar', 36))
p.append(txt(270, 148, f'Fonema{sup("1")}… Fonema{sup("2")}… etc.', 'f-nacar', 38, 'middle'))
p.append(corchete(30, 510, 168, 124))
p.append(txt(270, 216, f'Significante{sup("1")}', 'f-nacar', 38, 'middle'))
p.append(txt(700, 148, f'F{sup("1")}… F{sup("2")}… etc.', 'f-nacar', 38, 'middle'))
p.append(corchete(580, 820, 168, 124))
p.append(txt(700, 216, f'Snte.{sup("2")}', 'f-nacar', 38, 'middle'))
p.append('<line class="s-nacar w4" x1="30" y1="246" x2="830" y2="246"/>')
p.append(txt(430, 296, 'Significado', 'f-oro', 38, 'middle'))
# Condensación
XC = 1240
p.append(txt(900, 56, 'Condensación', 'it f-nacar', 36))
p.append(txt(1040, 204, f'Snte.{sup("1")}', 'f-nacar', 40, 'end'))
p.append(txt(1440, 204, f'Snte.{sup("2")}', 'f-nacar', 40))
p.append(txt(XC, 172, f'Snte.{sup("3")}', 'f-nacar', 40, 'middle'))
p.append(f'<line class="s-nacar w3" x1="{XC-76}" y1="190" x2="{XC+76}" y2="190"/>')
p.append(txt(XC, 238, 'Sdo.', 'f-oro', 40, 'middle'))
p.append(flecha(1054, 180, 1152, 180))          # Snte.1 → centro
p.append(flecha(1150, 228, 1056, 208))          # centro (nivel del Sdo.) → Snte.1
p.append(flecha(1426, 180, 1328, 180))          # Snte.2 → centro
p.append(flecha(1330, 228, 1424, 208))          # centro → Snte.2
p.append('</g>')

# --- Paso 1: permutación fonética (y ↔ ll) ---
C = '<tspan class="f-cian" font-weight="700">'
p.append('<g data-from="1">')
p.append(txt(430, 366, f'va{C}y</tspan>a un ga{C}ll</tspan>o <tspan class="f-azogue">⇄</tspan> '
                       f'va{C}ll</tspan>a un ga{C}y</tspan>o', 'it f-magenta', 34, 'middle'))
p.append(txt(1580, 56, 'Cabrera Infante · l. 341-342', 'neo f-cian', 28, 'end'))
p.append('</g>')


def fila(y, izq, centro, der, paso):
    wc = anchos([(centro, '', 28)])[0]
    g = [f'<g data-from="{paso}">']
    g.append(txt(XC - wc / 2 - 14, y, f'{izq} <tspan class="f-azogue">⇄</tspan>', 'f-nacar', 28, 'end'))
    g.append(txt(XC, y, centro, 'f-perla', 28, 'middle', ' font-weight="700"'))
    g.append(txt(XC + wc / 2 + 14, y, f'<tspan class="f-azogue">⇄</tspan> {der}', 'f-nacar', 28))
    g.append('</g>')
    return '\n'.join(g)


p.append(fila(318, 'AMO', 'AMOSCLAVO', 'ESCLAVO', 2))
p.append(fila(368, 'MÁQUINA', 'MAQUINOSCRITO', 'MANUSCRITO', 3))

p.append(txt(30, 410, 'Figura 3 según Sarduy 1972 · reconstrucción', 'neo f-azogue', 28))
guardar('fig3.svg', p)
