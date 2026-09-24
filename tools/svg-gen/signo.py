from comun import *
import random

W, H = 1400, 600
p = [cabecera('signo', W, H,
              'El signo y su distancia',
              'A la izquierda, el signo clásico: significante (Snte.) y significado (Sdo.) adheridos por una barra corta. '
              'A la derecha, el signo barroco: Snte. y Sdo. separados por una grieta dorada, la «abertura, falla» entre '
              'lo nombrante y lo nombrado (Sarduy 1972, l. 190-196); la distancia exagerada es una hipérbole.')]

# --- Izquierda: clásico ---
XL = 340
p.append('<g>')
p.append(txt(XL, 70, 'clásico', 'neo f-azogue', 32, 'middle'))
p.append(txt(XL, 282, 'Snte.', 'f-nacar', 64, 'middle'))
p.append(f'<line class="s-nacar w4" x1="{XL-80}" y1="302" x2="{XL+80}" y2="302"/>')
p.append(txt(XL, 370, 'Sdo.', 'f-oro', 64, 'middle'))
p.append(txt(XL, 470, 'adherencia', 'it f-nacar', 32, 'middle'))
p.append(txt(XL, 512, 'l. 190-191', 'neo f-cian', 28, 'middle'))
p.append('</g>')

# costura
p.append('<line class="s-azogue w3" opacity=".35" x1="700" y1="40" x2="700" y2="560"/>')

# --- Derecha: barroco ---
XR = 1030
rnd = random.Random(11)


# grieta: línea central quebrada; el oro asoma entre dos labios que se ahúsan en los extremos
YG = 300
cort = [0] + sorted(rnd.uniform(0.04, 0.96) for _ in range(13)) + [1]
xs = [XR - 150 + 300 * c for c in cort]
cen = [YG + (0 if i in (0, 14) else rnd.choice((-1, 1)) * rnd.uniform(2, 9)) for i in range(15)]
anc = [24 * math.sin(math.pi * c) ** 0.8 for c in cort]
sup_l = [(x, c - w / 2) for x, c, w in zip(xs, cen, anc)]
inf_l = [(x, c + w / 2) for x, c, w in zip(xs, cen, anc)]
poly = sup_l + list(reversed(inf_l))
d_poly = 'M' + ' L'.join(f'{n(x)} {n(y)}' for x, y in poly) + ' Z'
d_sup = f'M{XR-180} {YG} L' + ' L'.join(f'{n(x)} {n(y)}' for x, y in sup_l) + f' L{XR+180} {YG}'
d_inf = f'M{XR-180} {YG} L' + ' L'.join(f'{n(x)} {n(y)}' for x, y in inf_l) + f' L{XR+180} {YG}'
p.append('<g data-from="1">')
p.append(txt(XR, 70, 'barroco', 'neo f-azogue', 32, 'middle'))
p.append(txt(XR, 182, 'Snte.', 'f-nacar', 64, 'middle'))
p.append(f'<path class="f-oro" opacity=".9" d="{d_poly}"/>')
p.append(f'<path class="f-none s-nacar w3" style="stroke-linejoin:miter" d="{d_sup}"/>')
p.append(f'<path class="f-none s-nacar w3" style="stroke-linejoin:miter" d="{d_inf}"/>')
p.append(txt(XR, 426, 'Sdo.', 'f-oro', 64, 'middle'))
# cota de la distancia
XC = XR + 214
p.append(f'<line class="s-azogue w3" x1="{XC}" y1="150" x2="{XC}" y2="420"/>')
p.append(f'<line class="s-azogue w3" x1="{XC-14}" y1="150" x2="{XC+14}" y2="150"/>')
p.append(f'<line class="s-azogue w3" x1="{XC-14}" y1="420" x2="{XC+14}" y2="420"/>')
p.append(txt(XC + 24, 296, 'distancia', 'it f-azogue', 28))
p.append(txt(XR, 506, '«Abertura, falla»', 'serif it f-perla', 52, 'middle'))
p.append(txt(XR, 548, 'l. 192 · hipérbole, l. 194-195', 'neo f-cian', 28, 'middle'))
p.append('</g>')
guardar('signo.svg', p)
