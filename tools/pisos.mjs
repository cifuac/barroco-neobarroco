// Lee la altura del piso (y) de cada escena desde el visor y la guarda en tools/pisos.json (la usa decor-pos.py).
// Uso: node tools/pisos.mjs [base=http://localhost:8765] [escena...]
import { createRequire } from 'module';
import fs from 'fs';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('/Users/luiscifuentesacuna/.hermes/hermes-agent/node_modules/playwright');
const [base = 'http://localhost:8765', ...pedidas] = process.argv.slice(2);
const archivo = fileURLToPath(new URL('pisos.json', import.meta.url));
const pisos = fs.existsSync(archivo) ? JSON.parse(fs.readFileSync(archivo, 'utf8')) : {};
const escenas = pedidas.length ? pedidas : ['sustitucion', 'proliferacion', 'condensacion', 'estratos', 'espejo'];
const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const id of escenas) {
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.goto(`${base}/3d/visor.html?e=${id}&poster=1`, { waitUntil: 'load' });
  await p.waitForFunction(() => document.documentElement.dataset.piso, null, { timeout: 90000 });
  pisos[id] = parseFloat(await p.evaluate(() => document.documentElement.dataset.piso));
  console.log(id, pisos[id]); await p.close();
}
await b.close();
const actual = fs.existsSync(archivo) ? JSON.parse(fs.readFileSync(archivo, 'utf8')) : {};
for (const id of escenas) actual[id] = pisos[id];
fs.writeFileSync(archivo, JSON.stringify(actual, null, 1));
