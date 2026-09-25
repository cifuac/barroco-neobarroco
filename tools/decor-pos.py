# Genera docs/3d/decor/<id>.json ubicando cada imagen en un punto de la PANTALLA de un estado
# (coordenadas normalizadas del encuadre incrustado 2.12:1: x -1 izq … 1 der, y -1 abajo … 1 arriba)
# a una distancia dada de la cámara, orientada hacia ella y con un alto igual a una fracción del alto visible.
# Uso: python3 tools/decor-pos.py <escena> <plan.json>
# plan.json: [{"src": "...", "estado": 3, "estados": [3], "x": -0.6, "y": 0.4, "dist": 1.1 (× distancia al objetivo),
#              "alto": 0.35 (fracción del alto visible), "tipo": "cuadro", "pie": "...", ...resto de opciones de decor.js}]
import json, sys, os, math, subprocess
import numpy as np
id, plan_f = sys.argv[1], sys.argv[2]
aqui = os.path.dirname(os.path.abspath(__file__))
docs = os.path.join(aqui, '..', 'docs', '3d')
salida = subprocess.run([sys.executable, os.path.join(aqui, 'nodos3d.py'), id], capture_output=True, text=True).stdout
cams = {}
for l in salida.split('estados (cámara → objetivo, fov):')[1].strip().splitlines():
    k = int(l.split()[0])
    c = [float(v) for v in l.split('cam=(')[1].split(')')[0].split(',')]
    lk = [float(v) for v in l.split('look=(')[1].split(')')[0].split(',')]
    fov = float(l.split('fov=')[1].split()[0])
    cams[k] = (np.array(c), np.array(lk), fov)
ASP = 1920 / 904
from PIL import Image
out = []
for p in json.load(open(plan_f)):
    cam, look, fov = cams[p['estado']]
    d = look - cam; D = np.linalg.norm(d); f = d / D
    der = np.cross(f, [0, 1, 0]); der /= np.linalg.norm(der)
    arr = np.cross(der, f)
    dist = D * p.get('dist', 1.0)
    h = 2 * dist * math.tan(math.radians(fov) / 2)
    img = Image.open(os.path.join(docs, p['src']))
    r = p.get('recorte', [0, 0, 1, 1])
    asp = (r[3] - r[1]) * img.size[1] / ((r[2] - r[0]) * img.size[0])
    tipo = p.get('tipo', 'cuadro')
    alto = h * p.get('alto', 0.35)
    ancho = alto if tipo == 'disco' else alto / asp
    # semiancho en coordenadas de pantalla (con marco); «izq»/«der» fijan el borde en vez del centro.
    # Para que tampoco se corte en pantalla completa (16:9), los bordes deben quedar dentro de ±0.8.
    semi = (ancho / 2) * (1.0 if tipo == 'fondo' else 1.14) / (h * ASP / 2)
    x = p['x'] if 'x' in p else (p['izq'] + semi if 'izq' in p else p['der'] - semi)
    pos = cam + f * dist + der * (x * h * ASP / 2) + arr * (p['y'] * h / 2)
    e = {k: v for k, v in p.items() if k not in ('estado', 'x', 'y', 'dist', 'alto', 'izq', 'der')}
    e.update({'tipo': tipo, 'ancho': round(float(ancho), 3), 'pos': [round(float(v), 3) for v in pos], 'mira': f"cam_{p['estado']}"})
    e.setdefault('estados', [p['estado']])
    out.append(e)
os.makedirs(os.path.join(docs, 'decor'), exist_ok=True)
json.dump({'imagenes': out}, open(os.path.join(docs, 'decor', id + '.json'), 'w'), ensure_ascii=False, indent=1)
print(f'{len(out)} imágenes → docs/3d/decor/{id}.json')
