from comun import *

W, H = 1200, 620
CX, CY, R = 600, 400, 240
A0, A1 = 195, -13          # arco abierto: nace bajo el diámetro a la izquierda y termina con punta a la derecha
p = [cabecera('fig2', W, H,
              'Figura 2 de Sarduy (1972): la proliferación',
              'En el centro, el significante (Snte.) tachado sobre el significado (Sdo.). Alrededor, un arco punteado '
              'abierto por abajo, más o menos la mitad superior de una circunferencia, pasa por Snte. 1, Snte. 2, '
              'Snte. 3, Snte. 4 y Snte. 5 y termina en una punta de flecha seguida de «etc.»; el arco nunca se cierra. '
              'Paso 1: sobre Snte. 1 a 4, el ejemplo de Carpentier (reloj de sol con horas de luna, balanza que pesa '
              'gatos, telescopio por la luceta rota, astrónomo en lo alto de un armario; l. 234-239). Paso 2, añadido '
              'didáctico: rayos de la lectura radial apuntan hacia el centro y el Sdo. se rotula «desorden».')]

# --- Paso 2 (añadido): lectura radial; va detrás de la figura ---
T = (CX, 344)   # hacia el Snte. tachado
p.append('<g data-from="2">')
for th in (180, 145, 100, 55, 22):
    sx, sy = pol(CX, CY, R - 16, th)
    dx, dy = T[0] - sx, T[1] - sy
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    # detenerse fuera de una elipse de respeto alrededor de la fracción
    k = 1 / math.sqrt((ux / 104) ** 2 + (uy / 70) ** 2)
    ex, ey = T[0] - ux * k, T[1] - uy * k
    p.append(f'<line class="s-cian w3 redondo" x1="{n(sx)}" y1="{n(sy)}" x2="{n(ex - ux*14)}" y2="{n(ey - uy*14)}" opacity=".85"/>')
    p.append(punta(ex, ey, math.degrees(math.atan2(uy, ux)), L=16, W=7, cls='f-cian', extra='opacity=".85" '))
p.append(txt(CX, CY + 70, '«desorden»', 'it f-oro', 36, 'middle'))
p.append(txt(CX, CY + 122, 'lectura radial (añadido)', 'neo f-cian', 28, 'middle'))
p.append('</g>')

# --- Figura literal ---
p.append('<g>')
x0, y0 = pol(CX, CY, R, A0)
x1, y1 = pol(CX, CY, R, A1)
p.append(f'<path class="f-none s-nacar w3" style="stroke-dasharray:16 11" '
         f'd="M{n(x0)} {n(y0)} A{R} {R} 0 1 1 {n(x1)} {n(y1)}"/>')
tang = math.degrees(math.atan2(math.cos(math.radians(A1)), math.sin(math.radians(A1))))
a = math.radians(tang)
p.append(punta(x1 + math.cos(a) * 28, y1 + math.sin(a) * 28, tang, L=28, W=10))
# rótulos por fuera del arco
p.append(txt(338, 418, 'Snte.' + sup('1'), 'f-nacar', 46, 'end'))
p.append(txt(378, 246, 'Snte.' + sup('2'), 'f-nacar', 46, 'end'))
p.append(txt(532, 132, 'Snte.' + sup('3'), 'f-nacar', 46, 'middle'))
p.append(txt(742, 170, 'Snte.' + sup('4'), 'f-nacar', 46))
p.append(txt(846, 282, 'Snte.' + sup('5'), 'f-nacar', 46))
p.append(txt(872, 418, 'etc.', 'f-nacar', 46))
# fracción central: Snte. tachado sobre Sdo.
p.append(txt(CX, 346, 'Snte.', 'f-nacar', 46, 'middle', ' opacity=".62"'))
p.append(f'<line class="s-bermellon w4 redondo" x1="{CX-56}" y1="338" x2="{CX+56}" y2="320"/>')
p.append(f'<line class="s-nacar w3" x1="{CX-56}" y1="362" x2="{CX+56}" y2="362"/>')
p.append(txt(CX, 418, 'Sdo.', 'f-oro', 46, 'middle'))
p.append('</g>')

# --- Paso 1: Carpentier sobre Snte.1-4 ---
p.append('<g data-from="1">')
p.append(txt(338, 338, 'reloj de sol /', 'it f-magenta', 30, 'end'))
p.append(txt(338, 372, 'horas de luna', 'it f-magenta', 30, 'end'))
p.append(txt(378, 202, 'balanza que pesa gatos', 'it f-magenta', 30, 'end'))
p.append(txt(532, 82, 'telescopio por la luceta rota', 'it f-magenta', 30, 'middle'))
p.append(txt(742, 84, 'astrónomo en lo alto', 'it f-magenta', 30))
p.append(txt(742, 118, 'de un armario', 'it f-magenta', 30))
p.append(txt(1190, 566, 'Carpentier, <tspan class="it">El siglo de las luces</tspan> · l. 234-239', 'neo f-cian', 28, 'end'))
p.append('</g>')

p.append(txt(10, 606, 'Figura 2 según Sarduy 1972 · reconstrucción', 'neo f-azogue', 28))
guardar('fig2.svg', p)
