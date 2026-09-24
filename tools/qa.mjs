// QA: node tools/qa.mjs [ancho] [alto] [desde] [hasta] → capturas en /tmp/.../qa y reporte de desbordes
import { createRequire } from 'module';
import fs from 'fs';
const require = createRequire(import.meta.url);
const { chromium } = require('/Users/luiscifuentesacuna/.hermes/hermes-agent/node_modules/playwright');
const [w = '1920', h = '1080', desde = '1', hasta = '99', out = '/private/tmp/claude-501/-Users-luiscifuentesacuna-Downloads-Barroco-y-neobarroco/c288b4e2-05fe-455f-9fda-1ad56af291e5/scratchpad/qa'] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
const logs = [];
page.on('pageerror', (e) => logs.push('[pageerror] ' + e.message));
page.on('console', (m) => { if (m.type() === 'error') logs.push('[console] ' + m.text()); });
await page.goto('http://localhost:8765/index.html#/1', { waitUntil: 'networkidle' });
await page.waitForTimeout(1200);
const N = await page.evaluate(() => document.querySelectorAll('.slide').length);
const reporte = [];
for (let i = +desde; i <= Math.min(N, +hasta); i++) {
  await page.evaluate((i) => { location.hash = `#/${i}/99`; }, i);
  const es3d = await page.evaluate((i) => !!document.querySelectorAll('.slide')[i - 1].querySelector('.embed3d'), i);
  await page.waitForTimeout(es3d ? 5500 : 1300);
  const r = await page.evaluate(() => {
    const sl = document.querySelector('.slide.activa');
    const problemas = [];
    if (sl.scrollHeight > sl.clientHeight + 1) problemas.push(`scroll vertical en la diapositiva (${sl.scrollHeight} > ${sl.clientHeight})`);
    const st = document.getElementById('stage').getBoundingClientRect();
    const k = st.width / 1920;
    sl.querySelectorAll('h2, p, li, figure, .tarjeta, .figura, table, .versos, img').forEach((e) => {
      if (getComputedStyle(e).display === 'none') return;
      const b = e.getBoundingClientRect(); if (!b.width) return;
      const x0 = (b.left - st.left) / k, y0 = (b.top - st.top) / k, x1 = (b.right - st.left) / k, y1 = (b.bottom - st.top) / k;
      if (x1 > 1920 + 2 || y1 > 1080 + 2 || x0 < -2 || y0 < -2) problemas.push(`fuera del lienzo: <${e.tagName.toLowerCase()} class="${e.className}"> ${Math.round(x0)},${Math.round(y0)}→${Math.round(x1)},${Math.round(y1)} «${(e.textContent || '').trim().slice(0, 40)}»`);
      if (e.scrollHeight > e.clientHeight + 2 && getComputedStyle(e).overflow !== 'visible' && e.tagName !== 'IMG') problemas.push(`contenido recortado en <${e.tagName.toLowerCase()} class="${e.className}">`);
    });
    // pie: solapamiento del contenido con la zona del pie (y > 1010) en diapositivas con pie
    const conPie = !sl.classList.contains('sin-pie');
    if (conPie) sl.querySelectorAll('p, li, .tarjeta, figure').forEach((e) => {
      const b = e.getBoundingClientRect(); if (!b.width) return;
      const y1 = (b.bottom - st.top) / k; if (y1 > 1012 && getComputedStyle(e).opacity !== '0') problemas.push(`invade el pie: «${(e.textContent || '').trim().slice(0, 40)}» (y=${Math.round(y1)})`);
    });
    return { titulo: sl.dataset.titulo, problemas: [...new Set(problemas)] };
  });
  await page.screenshot({ path: `${out}/s${String(i).padStart(2, '0')}.png` });
  reporte.push(`${i} ${r.titulo}: ${r.problemas.length ? '\n   - ' + r.problemas.join('\n   - ') : 'OK'}`);
}
console.log(reporte.join('\n'));
if (logs.length) console.log('ERRORES:\n' + [...new Set(logs)].join('\n'));
await browser.close();
