// node anchos.mjs '<json [{t,cls,size}]>' -> widths in px (1 unit = 1 px), fonts as in svg.css
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('/Users/luiscifuentesacuna/.hermes/hermes-agent/node_modules/playwright');
const items = JSON.parse(process.argv[2]);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(`http://localhost:8765/svg/_prueba.html?f=_nada.svg`, { waitUntil: 'networkidle' });
const res = await page.evaluate(async (items) => {
  document.getElementById('caja').innerHTML = '<svg class="fig" viewBox="0 0 2000 400"></svg>';
  const svg = document.querySelector('#caja svg');
  const txt = items.map(it => `<text class="${it.cls||''}" font-size="${it.size}" x="0" y="100">${it.t}</text>`).join('');
  svg.innerHTML = txt; await document.fonts.ready; await new Promise(r=>setTimeout(r,800));
  return [...svg.querySelectorAll('text')].map(t => Math.round(t.getComputedTextLength()));
}, items);
console.log(JSON.stringify(res));
await browser.close();
