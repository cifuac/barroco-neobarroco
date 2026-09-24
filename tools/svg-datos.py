# Empaqueta los SVG de docs/svg en docs/js/svg-datos.js para que se vean también al abrir index.html como archivo local.
import os, json, glob
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs')
datos = {f'svg/{os.path.basename(f)}': open(f, encoding='utf-8').read() for f in sorted(glob.glob(D + '/svg/*.svg'))}
open(D + '/js/svg-datos.js', 'w', encoding='utf-8').write('window.SVG_DATOS = ' + json.dumps(datos, ensure_ascii=False) + ';\n')
print(len(datos), 'SVG empaquetados')
