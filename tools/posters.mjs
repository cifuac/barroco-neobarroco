// Pósters de carga de las escenas 3D, capturados desde el propio visor (modo ?poster=1: sin interfaz ni rótulos),
// para que coincidan exactamente con el aspecto web. Uso: node tools/posters.mjs [base=http://localhost:8765] [escena...]
// Escribe docs/3d/posters/<id>-<n>.webp (un póster por estado) y docs/3d/posters/<id>.webp (estado 0).
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
const require = createRequire(import.meta.url);
const { chromium } = require('/Users/luiscifuentesacuna/.hermes/hermes-agent/node_modules/playwright');

const [base = 'http://localhost:8765', ...pedidas] = process.argv.slice(2);
import { fileURLToPath } from 'url';
const docs = fileURLToPath(new URL('../docs/', import.meta.url));
const escenas = pedidas.length ? pedidas : fs.readdirSync(path.join(docs, '3d/escenas')).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5));
const tmp = fs.mkdtempSync('/tmp/posters-');
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const id of escenas) {
  const man = JSON.parse(fs.readFileSync(path.join(docs, `3d/escenas/${id}.json`), 'utf8'));
  for (let n = 0; n < man.estados.length; n++) {
    const page = await browser.newPage({ viewport: { width: 1920, height: 904 }, deviceScaleFactor: 1 });
    await page.goto(`${base}/3d/visor.html?e=${id}&s=${n}&poster=1`, { waitUntil: 'load' });
    await page.waitForFunction(() => document.documentElement.dataset.listo === '1', null, { timeout: 60000 });
    await page.waitForTimeout(1500);
    const png = path.join(tmp, `${id}-${n}.png`);
    await page.screenshot({ path: png });
    await page.close();
    const destinos = [path.join(docs, `3d/posters/${id}-${n}.webp`)];
    if (n === 0) destinos.push(path.join(docs, `3d/posters/${id}.webp`));
    for (const d of destinos) execFileSync('python3', ['-c', 'import sys; from PIL import Image; Image.open(sys.argv[1]).convert("RGB").resize((1600, 753)).save(sys.argv[2], quality=80)', png, d]);
    console.log('póster', id, n);
  }
}
await browser.close();
