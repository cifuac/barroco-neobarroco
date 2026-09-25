// Captura todos los estados de una escena 3D, tal como se ven en la diapositiva (incrustada) y en el visor a pantalla completa.
// Uso: node tools/estados.mjs <escena> <carpeta_salida> [base=http://localhost:8765] [solo=embed|visor|ambos]
// Salida: <carpeta>/embed-<paso>.png (1920×1080, la diapositiva completa), <carpeta>/visor-<n>.png (1920×1080),
//         <carpeta>/hoja.jpg (hoja de contactos) y errores de consola por pantalla.
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
const require = createRequire(import.meta.url);
const { chromium } = require('/Users/luiscifuentesacuna/.hermes/hermes-agent/node_modules/playwright');

const [id, out, base = 'http://localhost:8765', solo = 'ambos'] = process.argv.slice(2);
if (!id || !out) { console.error('uso: node tools/estados.mjs <escena> <carpeta> [base] [embed|visor|ambos]'); process.exit(1); }
fs.mkdirSync(out, { recursive: true });
const html = fs.readFileSync(new URL('../docs/index.html', import.meta.url), 'utf8');
const secciones = html.split('<section').slice(1);
const nSlide = secciones.findIndex((s) => s.includes(`data-escena="${id}"`)) + 1;
const estadosDeck = (secciones[nSlide - 1] || '').match(/data-estados="([^"]+)"/)?.[1].split(',').map(Number) || [0];
const man = JSON.parse(fs.readFileSync(new URL(`../docs/3d/escenas/${id}.json`, import.meta.url), 'utf8'));

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const archivos = [];
async function captura(url, archivo, esDeck) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const logs = [];
  page.on('console', (m) => { if (m.type() === 'error') logs.push(m.text()); });
  page.on('pageerror', (e) => logs.push('pageerror ' + e.message));
  await page.goto(url, { waitUntil: 'load' });
  const t0 = Date.now();
  while (Date.now() - t0 < 30000) {
    const ok = await page.evaluate((deck) => {
      if (!deck) return document.documentElement.dataset.listo === '1';
      const f = document.querySelector('.slide.activa iframe, .slide.actual iframe, section.slide iframe');
      try { return !!(f && f.contentDocument && f.contentDocument.documentElement.dataset.listo === '1'); } catch (e) { return false; }
    }, esDeck);
    if (ok) break;
    await page.waitForTimeout(400);
  }
  await page.waitForTimeout(2200); // estado aplicado + rótulos visibles
  await page.screenshot({ path: path.join(out, archivo) });
  await page.close();
  archivos.push(archivo);
  if (logs.length) console.log(`[${archivo}] ` + logs.join(' | '));
}
if (solo !== 'visor') for (let k = 0; k < estadosDeck.length; k++)
  await captura(`${base}/index.html#/${nSlide}/${k}`, `embed-${k}-e${estadosDeck[k]}.png`, true);
if (solo !== 'embed') for (let n = 0; n < man.estados.length; n++)
  await captura(`${base}/3d/visor.html?e=${id}&s=${n}`, `visor-${n}.png`, false);
await browser.close();
try {
  execFileSync('python3', ['-c', `
import sys, os
from PIL import Image, ImageDraw
d = sys.argv[1]; fs = sys.argv[2:]
ims = [Image.open(os.path.join(d, f)).resize((960, 540)) for f in fs]
cols = 2; rows = (len(ims) + 1) // 2
W = Image.new('RGB', (cols * 960, rows * 560), 'white')
for i, (im, f) in enumerate(zip(ims, fs)):
    x, y = (i % cols) * 960, (i // cols) * 560
    W.paste(im, (x, y + 20)); ImageDraw.Draw(W).text((x + 8, y + 4), f, fill=(0, 0, 0))
W.save(os.path.join(d, 'hoja.jpg'), quality=82)
`, out, ...archivos]);
} catch (e) { console.log('sin hoja de contactos: ' + e.message); }
console.log(`diapositiva ${nSlide} · pasos del mazo → estados ${estadosDeck.join(',')} · ${man.estados.length} estados en el visor · ${archivos.length} capturas en ${out}`);
