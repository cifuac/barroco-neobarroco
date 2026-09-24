# El barroco y el neobarroco — clase con esquemas 3D

Presentación web (16:9, sin scroll) sobre «El barroco y el neobarroco» de Severo Sarduy (1972), con las apostillas de Valentín Díaz (El Cuenco de Plata, 2011). Incluye esquemas 3D generados con Blender y un visor three.js.

## Ver la presentación
- **En línea (GitHub Pages):** Settings → Pages → *Deploy from a branch* → rama `main`, carpeta `/docs`.
- **En local:** `python3 -m http.server 8765 --directory docs` y abrir `http://localhost:8765`.
  (Abrir `index.html` con doble clic no carga los SVG ni el 3D: se necesita un servidor, o GitHub Pages.)

## Teclas
→ / espacio / clic a la derecha: avanzar · ← : retroceder · número + Intro: ir a una diapositiva · O: índice ·
F: pantalla completa · B: pantalla negra · T: temporizador de los talleres · E: abrir el 3D a pantalla completa.

**Sin conexión:** en el índice (tecla O) está el botón «Preparar clase sin conexión», que guarda todo en el navegador.

## Estructura
- `docs/` — el sitio publicado (index.html, css, js, svg, img, 3d).
- `blender/` — scripts bpy que generan las escenas (`blender/lib/bb.py` + `blender/scenes/*.py`).
  Reconstruir una escena: `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P blender/scenes/<id>.py`
- `tools/` — utilidades (capturas, control de calidad, referencias, lista de caché).

## Derechos
Citas breves con fines docentes. Imágenes: dominio público o licencias libres (Wikimedia Commons, acreditadas en la última diapositiva) e imágenes generadas con IA (Gemini · Nano Banana 2), rotuladas con ✦. Los esquemas 3D son dispositivos genéricos y no reproducen obras de ningún artista. El texto de Sarduy **no** se incluye en este repositorio.
