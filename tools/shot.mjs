// Capturas headless: node tools/shot.mjs <url> <salida.png> [ancho] [alto] [espera_ms] [js_opcional]
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('/Users/luiscifuentesacuna/.hermes/hermes-agent/node_modules/playwright');
const [url, out, w = '1920', h = '1080', wait = '2500', js = ''] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
const logs = [];
page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) logs.push(`[${m.type()}] ${m.text()}`); });
page.on('pageerror', (e) => logs.push('[pageerror] ' + e.message));
await page.goto(url, { waitUntil: 'networkidle' });
if (js) await page.evaluate(js);
await page.waitForTimeout(+wait);
await page.screenshot({ path: out });
if (logs.length) console.log(logs.join('\n'));
await browser.close();
