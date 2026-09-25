# Lista los nodos de una escena 3D con su posición en el mundo (coordenadas three.js, Y arriba) en la pose de reposo,
# y las cámaras de cada estado. Útil para ubicar imágenes en docs/3d/decor/<id>.json.
# Uso: python3 tools/nodos3d.py <escena> [filtro]
import json, struct, sys, os
import numpy as np
id = sys.argv[1]; filtro = sys.argv[2] if len(sys.argv) > 2 else ''
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', '3d', 'escenas')
b = open(os.path.join(base, id + '.glb'), 'rb').read()
l = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + l])
def mat(n):
    t = np.array(n.get('translation', [0, 0, 0])); q = n.get('rotation', [0, 0, 0, 1]); s = np.array(n.get('scale', [1, 1, 1]))
    x, y, z, w = q
    R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    M = np.eye(4); M[:3, :3] = R * s; M[:3, 3] = t; return M
nodos = j['nodes']
def recorrer(i, P):
    n = nodos[i]; M = P @ mat(n); p = M[:3, 3]
    nombre = n.get('name', f'#{i}')
    if filtro.lower() in nombre.lower(): print(f'{nombre:40s} ({p[0]:7.2f}, {p[1]:7.2f}, {p[2]:7.2f})')
    for c in n.get('children', []): recorrer(c, M)
for r in j['scenes'][0]['nodes']: recorrer(r, np.eye(4))
man = json.load(open(os.path.join(base, id + '.json'), encoding='utf-8'))
print('\nestados (cámara → objetivo, fov):')
pos = {}
def todos(i, P):
    n = nodos[i]; M = P @ mat(n); pos[n.get('name')] = M[:3, 3]
    for c in n.get('children', []): todos(c, M)
for r in j['scenes'][0]['nodes']: todos(r, np.eye(4))
for k, e in enumerate(man['estados']):
    c, lk = pos.get(e['cam']), pos.get(e['look'])
    print(f"{k} {e['nombre']:24s} cam=({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f}) look=({lk[0]:.2f}, {lk[1]:.2f}, {lk[2]:.2f}) fov={e['fov']} t1={e['t1']}")
