from comun import *

W, H = 1500, 620
p = [cabecera('ret', W, H,
              'Retombée: parecidos sin causa',
              'A la izquierda, la elipse de Kepler (1609) con el sol en un foco y el otro foco vacío. A la derecha, la '
              'planta oval de San Carlo alle Quattro Fontane (Borromini, 1634-41), en esquema; es un ejemplo añadido. '
              'Entre ambas, ondas concéntricas sin flecha. Paso 1: aparece una flecha de causa a efecto. Paso 2: la '
              'flecha se tacha en bermellón y aparece el rótulo «retombée: causalidad acrónica, isomorfía no contigua» '
              '(Sarduy 1974, citado por Díaz 2011, l. 1507-1509).')]

CY = 262
# --- ondas concéntricas, sin flecha, entre las dos figuras ---
p.append('<g>')
for i, r in enumerate((44, 88, 132, 176)):
    op = [.9, .7, .5, .32][i]
    for a0, a1 in ((148, 212), (-32, 32)):
        xa, ya = pol(750, CY, r, a0)
        xb, yb = pol(750, CY, r, a1)
        p.append(f'<path class="f-none s-azogue w3 redondo" opacity="{op}" d="M{n(xa)} {n(ya)} A{r} {r} 0 0 0 {n(xb)} {n(yb)}"/>')
p.append('</g>')

# --- Kepler ---
KX, a, b = 300, 200, 132
c = math.sqrt(a * a - b * b)
px, py = pol(KX, CY, a, 236, b)
p.append('<g>')
p.append(f'<ellipse class="f-none s-nacar w3" cx="{KX}" cy="{CY}" rx="{a}" ry="{b}"/>')
p.append(f'<circle class="f-none s-oro w3" opacity=".45" cx="{n(KX - c)}" cy="{CY}" r="27"/>')
p.append(f'<circle class="f-oro" cx="{n(KX - c)}" cy="{CY}" r="15"/>')
p.append(f'<circle class="f-none s-azogue w3" style="stroke-dasharray:5 5" cx="{n(KX + c)}" cy="{CY}" r="12"/>')
p.append(f'<circle class="f-nacar" cx="{n(px)}" cy="{n(py)}" r="8"/>')
p.append(txt(KX, 470, 'Kepler, 1609', 'neo f-nacar', 32, 'middle'))
p.append(txt(KX, 506, 'elipse: sol en un foco, el otro vacío', 'f-azogue', 28, 'middle'))
p.append('</g>')

# --- San Carlo: esquema de planta oval con cuatro capillas en los ejes y columnas en los encuentros ---
SX, ra, rb = 1200, 100, 128
ht, hs = 46, 40                                     # semiancho de las capillas de los ejes (largo, corto)
yt = rb * math.sqrt(1 - (ht / ra) ** 2)             # encuentro capilla-óvalo en el eje largo
xs_ = ra * math.sqrt(1 - (hs / rb) ** 2)            # encuentro en el eje corto
g1, g2 = SX + ht * math.cos(math.radians(75)), CY + yt + ht * math.sin(math.radians(75))
d = (f'M{n(SX-ht)} {n(CY-yt)} A{ht} {ht} 0 0 1 {n(SX+ht)} {n(CY-yt)} '
     f'A{ra} {rb} 0 0 1 {n(SX+xs_)} {n(CY-hs)} A{hs} {hs} 0 0 1 {n(SX+xs_)} {n(CY+hs)} '
     f'A{ra} {rb} 0 0 1 {n(SX+ht)} {n(CY+yt)} A{ht} {ht} 0 0 1 {n(g1)} {n(g2)} '
     f'M{n(2*SX-g1)} {n(g2)} A{ht} {ht} 0 0 1 {n(SX-ht)} {n(CY+yt)} '
     f'A{ra} {rb} 0 0 1 {n(SX-xs_)} {n(CY+hs)} A{hs} {hs} 0 0 1 {n(SX-xs_)} {n(CY-hs)} '
     f'A{ra} {rb} 0 0 1 {n(SX-ht)} {n(CY-yt)}')
p.append('<g>')
p.append(f'<path class="f-none s-nacar w3 redondo" d="{d}"/>')
p.append(f'<ellipse class="f-none s-nacar w3 dash-fino" opacity=".55" cx="{SX}" cy="{CY}" rx="{ra - 30}" ry="{rb - 34}"/>')
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        p.append(f'<circle class="f-nacar" cx="{n(SX + sx_*ht)}" cy="{n(CY + sy_*yt)}" r="6"/>')
        p.append(f'<circle class="f-nacar" cx="{n(SX + sx_*xs_)}" cy="{n(CY + sy_*hs)}" r="6"/>')
p.append(txt(SX, 470, 'San Carlo, Borromini', 'neo f-nacar', 32, 'middle'))
p.append(txt(SX, 506, 'planta oval, 1634-41 · ejemplo añadido', 'f-azogue', 28, 'middle'))
p.append('</g>')

# --- Paso 1: la tentación causal ---
ARC = 'M392 128 Q750 18 1108 128'
end_ang = ang_pantalla(750, 8, 1080, 117)
p.append('<g data-from="1" data-until="2">')
p.append(f'<path class="f-none s-perla w4 redondo" d="M404 122 Q750 8 1066 112"/>')
p.append(punta(1080, 117, end_ang, L=26, W=10, cls='f-perla'))
p.append(txt(404, 94, 'causa', 'neo f-perla', 28, 'end'))
p.append(txt(1092, 94, 'efecto', 'neo f-perla', 28))
p.append('</g>')
# --- Paso 2: la flecha, tachada; el rótulo de 1974 ---
p.append('<g data-from="2">')
p.append(f'<g opacity=".35"><path class="f-none s-perla w4 redondo" d="M404 122 Q750 8 1066 112"/>'
         + punta(1080, 117, end_ang, L=26, W=10, cls='f-perla')
         + txt(404, 94, 'causa', 'neo f-perla', 28, 'end') + txt(1092, 94, 'efecto', 'neo f-perla', 28) + '</g>')
p.append('<line class="s-bermellon w6 redondo" x1="724" y1="92" x2="776" y2="28"/>')
p.append(txt(750, 570, '«retombée: causalidad acrónica, isomorfía no contigua»', 'serif it f-perla', 44, 'middle'))
p.append(txt(750, 608, 'Sarduy 1974, cit. por Díaz 2011 · l. 1507-1509', 'neo f-azogue', 28, 'middle'))
p.append('</g>')
guardar('retombee.svg', p)
