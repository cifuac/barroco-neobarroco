from comun import *

W, H = 1200, 400
BAR_Y = 170
FX = 175            # centro de la fracción
p = [cabecera('fig1', W, H,
              'Figura 1 de Sarduy (1972): la sustitución',
              'A la izquierda, una fracción: el significante (Snte.) tachado sobre la barra y el significado (Sdo.) debajo. '
              'Desde la barra sale hacia la derecha una flecha punteada larga que termina en «Snte. 1», solo y lejos, '
              'sin barra y sin significado debajo. Paso 1: bajo Sdo., «virilidad»; bajo Snte. 1, «el aguijón del '
              'leptosomático macrogenitoma» (Lezama, Paradiso, l. 151-152). Paso 2, añadido didáctico: un halo del '
              'contexto (l. 156-157) envuelve a distancia los dos términos.')]

# --- Paso 2 (añadido didáctico): halo del contexto, detrás de todo ---
p.append('<defs><radialGradient id="fig1-halo" cx="50%" cy="50%" r="50%">'
         '<stop offset="0" style="stop-color:var(--azogue);stop-opacity:.20"/>'
         '<stop offset=".62" style="stop-color:var(--azogue);stop-opacity:.09"/>'
         '<stop offset="1" style="stop-color:var(--azogue);stop-opacity:0"/></radialGradient></defs>')
cx, cy, rx, ry = 592, 214, 612, 178
p.append('<g data-from="2">')
p.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#fig1-halo)"/>')
# dos paréntesis amplios que envuelven sin cerrar
p.append(f'<path class="f-none s-azogue w3 redondo" opacity=".75" d="M64 84 Q14 214 64 344"/>')
p.append(f'<path class="f-none s-azogue w3 redondo" opacity=".75" d="M1150 84 Q1198 214 1150 344"/>')
p.append(txt(600, 44, 'contexto <tspan class="f-cian" font-size="28">· l. 156-157</tspan>', 'neo f-azogue', 32, 'middle'))
p.append(txt(1190, 386, 'añadido didáctico', 'neo f-azogue', 28, 'end'))
p.append('</g>')

# --- Figura literal ---
p.append('<g>')
# Snte. tachado
p.append(txt(FX, BAR_Y - 20, 'Snte.', 'f-nacar', 56, 'middle', ' opacity=".62"'))
p.append(f'<line class="s-bermellon w4 redondo" x1="{FX-68}" y1="{BAR_Y-26}" x2="{FX+68}" y2="{BAR_Y-47}"/>')
# barra
p.append(f'<line class="s-nacar w3" x1="{FX-72}" y1="{BAR_Y}" x2="{FX+72}" y2="{BAR_Y}"/>')
# Sdo.
p.append(txt(FX, BAR_Y + 56, 'Sdo.', 'f-oro', 56, 'middle'))
# flecha punteada larga con punta llena
p.append(f'<line class="s-nacar w3" style="stroke-dasharray:24 16" x1="290" y1="{BAR_Y}" x2="826" y2="{BAR_Y}"/>')
p.append(punta(852, BAR_Y, 0, L=30, W=11))
# Snte.1, solo y lejos
p.append(txt(874, BAR_Y + 20, 'Snte.' + sup('1'), 'f-nacar', 56))
p.append('</g>')

# --- Paso 1: ejemplos de Lezama ---
p.append('<g data-from="1">')
p.append(txt(FX, BAR_Y + 118, '«virilidad»', 'it f-oro', 36, 'middle'))
p.append(txt(926, BAR_Y + 86, '«el aguijón del', 'it f-magenta', 32, 'middle'))
p.append(txt(926, BAR_Y + 124, 'leptosomático macrogenitoma»', 'it f-magenta', 32, 'middle'))
p.append(txt(926, BAR_Y + 166, 'Lezama, <tspan class="it">Paradiso</tspan> · l. 151-152', 'neo f-cian', 28, 'middle'))
p.append('</g>')

# crédito
p.append(txt(20, 386, 'Figura 1 según Sarduy 1972 · reconstrucción', 'neo f-azogue', 28))
guardar('fig1.svg', p)
