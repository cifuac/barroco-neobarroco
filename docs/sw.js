// Modo sin conexión: «Preparar clase» guarda todo el sitio en la caché del navegador.
const CACHE = 'sarduy-v1';
self.addEventListener('install', (e) => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('message', (ev) => {
  if (!ev.data || ev.data.type !== 'precargar') return;
  const port = ev.ports[0];
  ev.waitUntil((async () => {
    const lista = await fetch('cache-lista.json', { cache: 'no-store' }).then((r) => r.json());
    const cache = await caches.open(CACHE);
    let hechos = 0, errores = 0;
    for (const url of lista) {
      try { const r = await fetch(url, { cache: 'reload', mode: url.startsWith('http') ? 'no-cors' : 'same-origin' }); await cache.put(url, r); }
      catch (e) { errores++; }
      hechos++;
      if (hechos % 8 === 0 && port) port.postMessage({ progreso: `${Math.round(100 * hechos / lista.length)} %` });
    }
    // fuentes de Google (hojas y archivos) se capturan al vuelo en fetch
    if (port) port.postMessage({ listo: true, errores });
  })());
});
self.addEventListener('fetch', (ev) => {
  const req = ev.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const esFuente = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (url.origin !== location.origin && !esFuente) return;
  ev.respondWith((async () => {
    const cache = await caches.open(CACHE);
    // red primero (para ver siempre la última versión); si falla, caché
    try {
      const r = await fetch(req);
      if (r && (r.ok || r.type === 'opaque') && (esFuente || (await cache.match(req, { ignoreSearch: true })))) cache.put(req, r.clone());
      return r;
    } catch (e) {
      const c = await cache.match(req, { ignoreSearch: true }) || await cache.match(url.pathname.endsWith('/') ? url.pathname + 'index.html' : req, { ignoreSearch: true });
      if (c) return c;
      throw e;
    }
  })());
});
