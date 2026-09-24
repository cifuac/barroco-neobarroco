// node measure.mjs <file.svg> [w] [h]  -> prints bbox (in viewBox units) of every <text> and checks overlaps / out-of-viewBox
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('/Users/luiscifuentesacuna/.hermes/hermes-agent/node_modules/playwright');
const [f, w='1728', h='840'] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(`http://localhost:8765/svg/_prueba.html?f=${f}&w=${w}&h=${h}`, { waitUntil: 'networkidle' });
await page.waitForTimeout(1200);
const res = await page.evaluate(() => {
  const svg = document.querySelector('#caja svg'); const vb = svg.viewBox.baseVal;
  const out = [];
  svg.querySelectorAll('text').forEach((t, i) => {
    const b = t.getBBox(); const g = t.closest('[data-from]'); 
    out.push({ i, s: t.textContent.trim().slice(0, 40), x: Math.round(b.x), y: Math.round(b.y), x2: Math.round(b.x + b.width), y2: Math.round(b.y + b.height), step: g ? g.dataset.from : '0', fs: getComputedStyle(t).fontSize, ff: getComputedStyle(t).fontFamily.split(',')[0] });
  });
  const fonts = [...document.fonts].filter(f=>f.status==='loaded').map(f => f.family + ' ' + f.weight + ' ' + f.style);
  return { vb: [vb.width, vb.height], out, fonts };
});
console.log('viewBox', res.vb.join('x'), '| fonts loaded:', [...new Set(res.fonts)].join('; '));
for (const o of res.out) {
  const oob = (o.x < 0 || o.y < 0 || o.x2 > res.vb[0] || o.y2 > res.vb[1]) ? '  <-- FUERA' : '';
  console.log(`#${o.i} [p${o.step}] ${o.x},${o.y}-${o.x2},${o.y2} ${o.fs} ${o.ff} "${o.s}"${oob}`);
}
// overlaps (texts only, any step pair)
for (let a = 0; a < res.out.length; a++) for (let b = a + 1; b < res.out.length; b++) {
  const A = res.out[a], B = res.out[b];
  if (A.x < B.x2 && B.x < A.x2 && A.y < B.y2 && B.y < A.y2) console.log(`  solapan #${A.i} "${A.s}" y #${B.i} "${B.s}"`);
}
await browser.close();
