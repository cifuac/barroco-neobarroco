# Genera docs/cache-lista.json con todos los archivos del sitio (para «Preparar clase»).
import os, json
DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs')
out = ['./', 'index.html']
for raiz, dirs, archivos in os.walk(DOCS):
    for a in sorted(archivos):
        if a.startswith('.') or a in ('cache-lista.json', 'sw.js') or a.startswith('_'):
            continue
        rel = os.path.relpath(os.path.join(raiz, a), DOCS).replace(os.sep, '/')
        if rel != 'index.html':
            out.append(rel)
out.append('https://fonts.googleapis.com/css2?family=Libre+Caslon+Display&family=Libre+Caslon+Text:ital,wght@0,400;0,700;1,400&display=swap')
json.dump(out, open(os.path.join(DOCS, 'cache-lista.json'), 'w'), indent=0)
print(len(out), 'archivos')
