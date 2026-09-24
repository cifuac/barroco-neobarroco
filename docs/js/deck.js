/* Motor de diapositivas — lienzo fijo 1920×1080, sin scroll.
   Teclas: → Espacio AvPág Intro = avanzar · ← RePág Retroceso = retroceder · Inicio/Fin
           número + Intro = ir a diapositiva · O = índice · F = pantalla completa · B = pantalla negra
           T = iniciar/pausar temporizador · E = abrir el 3D de la diapositiva a pantalla completa */
(function () {
  'use strict';
  const W = 1920, H = 1080;
  const qs = new URLSearchParams(location.search);
  const temaQS = (qs.get('tema') ? '&tema=' + qs.get('tema') : '') + (qs.get('acento') ? '&acento=' + qs.get('acento') : '');
  const stage = document.getElementById('stage');
  const slides = Array.from(stage.querySelectorAll('.slide'));
  const N = slides.length;
  let idx = 0, paso = 0, numBuf = '', numTimer = null;

  // ---------- escala
  function escalar() {
    const s = Math.min(innerWidth / W, innerHeight / H);
    stage.style.transform = `translate(${(innerWidth - W * s) / 2}px, ${(innerHeight - H * s) / 2}px) scale(${s})`;
  }
  addEventListener('resize', escalar);
  escalar();

  // ---------- SVG en línea (data-svg="svg/x.svg")
  const svgCache = {};
  function cargarSVG(el) {
    if (el.dataset.cargado) return Promise.resolve();
    const url = el.dataset.svg;
    el.dataset.cargado = '1';
    const p = svgCache[url] || (svgCache[url] = fetch(url).then((r) => r.text()));
    return p.then((t) => { el.innerHTML = t; aplicarPasos(el.closest('.slide')); });
  }

  // ---------- pasos
  function maxPasos(sl) {
    let m = parseInt(sl.dataset.pasos || '0', 10) || 0;
    const e3 = sl.querySelector('.embed3d[data-estados]');
    if (e3) m = Math.max(m, e3.dataset.estados.split(',').length - 1);
    sl.querySelectorAll('[data-from]').forEach((e) => { m = Math.max(m, parseInt(e.dataset.from, 10) || 0); });
    sl.querySelectorAll('[data-until]').forEach((e) => { m = Math.max(m, parseInt(e.dataset.until, 10) || 0); });
    return m;
  }
  function aplicarPasos(sl) {
    if (!sl) return;
    const p = sl === slides[idx] ? paso : 0;
    sl.dataset.paso = p;
    sl.querySelectorAll('[data-from]').forEach((e) => e.classList.toggle('on', p >= (parseInt(e.dataset.from, 10) || 0)));
    sl.querySelectorAll('[data-until]').forEach((e) => e.classList.toggle('off', p >= (parseInt(e.dataset.until, 10) || 0)));
    // 3D: estado según el paso
    const e3 = sl.querySelector('.embed3d');
    if (e3 && e3._iframe && e3.dataset.estados) {
      const est = e3.dataset.estados.split(',').map(Number);
      const n = est[Math.min(p, est.length - 1)];
      if (e3._estado !== n) { e3._estado = n; enviar3D(e3, { type: 'estado', n }); }
    }
  }

  // ---------- imágenes diferidas (data-src) para la diapositiva actual y vecinas
  function precargar(i) {
    for (let k = i - 1; k <= i + 2; k++) {
      const sl = slides[k]; if (!sl) continue;
      sl.querySelectorAll('img[data-src]').forEach((im) => { im.src = im.dataset.src; im.removeAttribute('data-src'); });
      sl.querySelectorAll('[data-bg]').forEach((d) => { d.style.backgroundImage = `url("${d.dataset.bg}")`; d.removeAttribute('data-bg'); });
      sl.querySelectorAll('[data-svg]').forEach(cargarSVG);
    }
  }

  // ---------- 3D incrustado (un solo contexto WebGL a la vez)
  function montar3D(sl) {
    sl.querySelectorAll('.embed3d').forEach((e3) => {
      if (e3._iframe) return;
      const est = (e3.dataset.estados || '0').split(',').map(Number);
      const n = est[Math.min(paso, est.length - 1)];
      const f = document.createElement('iframe');
      f.src = `3d/visor.html?e=${e3.dataset.escena}&s=${n}&embed=1${e3.dataset.panel === '0' ? '&panel=0' : ''}${temaQS}`;
      f.title = e3.dataset.titulo || 'Esquema 3D';
      f.setAttribute('allow', 'fullscreen');
      e3.appendChild(f);
      e3._iframe = f; e3._estado = n;
      f.addEventListener('load', () => {
        try { // mismo origen: reenviar teclas de navegación del iframe al mazo
          f.contentWindow.addEventListener('keydown', (ev) => {
            if (ev.target && ev.target.tagName === 'INPUT' && /Arrow/.test(ev.key)) return;
            teclado(ev);
          });
        } catch (err) { /* file:// u otro origen: el visor reenvía por postMessage */ }
      });
    });
  }
  function desmontar3D(sl) {
    sl.querySelectorAll('.embed3d').forEach((e3) => {
      if (!e3._iframe) return;
      try { e3._iframe.contentWindow.postMessage({ type: 'liberar' }, '*'); } catch (e) {}
      e3._iframe.remove(); e3._iframe = null; e3._estado = null;
    });
  }
  function enviar3D(e3, msg) { try { e3._iframe.contentWindow.postMessage(msg, '*'); } catch (e) {} }
  addEventListener('message', (ev) => {
    const d = ev.data || {};
    if (d.fuente !== 'visor3d') return;
    if (d.type === 'tecla') teclado({ key: d.key, preventDefault() {}, target: document.body });
    if (d.type === 'listo') { const e3 = slides[idx].querySelector('.embed3d'); if (e3 && e3._iframe && e3._estado != null) enviar3D(e3, { type: 'estado', n: e3._estado }); }
  });
  function abrir3D() {
    const e3 = slides[idx].querySelector('.embed3d');
    if (!e3) return;
    const f = e3._iframe;
    if (document.fullscreenElement && document.fullscreenElement === f) { document.exitFullscreen(); return; }
    if (f && f.requestFullscreen) {
      f.requestFullscreen().then(() => { try { f.contentWindow.focus(); } catch (e) {} })
        .catch(() => irAlVisor(e3));
    } else irAlVisor(e3);
  }
  function irAlVisor(e3) {
    const n = e3._estado || 0;
    location.href = `3d/visor.html?e=${e3.dataset.escena}&s=${n}&volver=${encodeURIComponent('#/' + (idx + 1))}`;
  }
  document.querySelectorAll('[data-accion="pantalla-3d"]').forEach((b) => b.addEventListener('click', (ev) => { ev.stopPropagation(); abrir3D(); }));

  // ---------- navegación
  function ir(i, p = 0, desdeHash = false) {
    i = Math.max(0, Math.min(N - 1, i));
    const ant = slides[idx];
    if (i !== idx || !ant.classList.contains('activa')) {
      if (ant && ant !== slides[i]) { ant.classList.remove('activa'); ant.setAttribute('aria-hidden', 'true'); ant.inert = true; desmontar3D(ant); pararTemporizadores(ant); }
      idx = i;
    }
    const sl = slides[idx];
    paso = Math.max(0, Math.min(p, maxPasos(sl)));
    sl.classList.add('activa'); sl.removeAttribute('aria-hidden'); sl.inert = false;
    precargar(idx);
    aplicarPasos(sl);
    montar3D(sl);
    actualizarPie();
    if (!desdeHash) history.replaceState(null, '', `#/${idx + 1}${paso ? '/' + paso : ''}`);
    document.getElementById('vivo').textContent = `Diapositiva ${idx + 1} de ${N}: ${sl.dataset.titulo || ''}`;
    window.scrollTo(0, 0);
  }
  function siguiente() { const m = maxPasos(slides[idx]); if (paso < m) { paso++; aplicarPasos(slides[idx]); history.replaceState(null, '', `#/${idx + 1}/${paso}`); } else if (idx < N - 1) ir(idx + 1, 0); }
  function anterior() { if (paso > 0) { paso--; aplicarPasos(slides[idx]); history.replaceState(null, '', `#/${idx + 1}${paso ? '/' + paso : ''}`); } else if (idx > 0) ir(idx - 1, maxPasos(slides[idx - 1])); }

  function desdeHash() {
    const m = location.hash.match(/^#\/(\d+)(?:\/(\d+))?/);
    if (m) ir(parseInt(m[1], 10) - 1, parseInt(m[2] || '0', 10), true);
    else ir(0, 0, true);
  }
  addEventListener('hashchange', desdeHash);

  // ---------- pie: número y módulo
  const modulos = Array.from(document.querySelectorAll('.pie .modulos li'));
  function actualizarPie() {
    document.getElementById('num').textContent = String(idx + 1).padStart(2, '0');
    document.getElementById('total').textContent = String(N).padStart(2, '0');
    const mod = slides[idx].dataset.modulo || '';
    modulos.forEach((li) => li.classList.toggle('actual', li.dataset.modulo === mod));
    document.body.classList.toggle('sin-pie', slides[idx].classList.contains('sin-pie'));
    document.body.classList.toggle('pie-claro', slides[idx].classList.contains('claro'));
    document.getElementById('progreso').style.setProperty('--p', ((idx) / (N - 1)).toFixed(4));
  }

  // ---------- temporizadores de actividad
  function iconoTemp(t) { const b = t.querySelector('.btn-icono'); if (b && window.cambiarIcono) cambiarIcono(b, t._int ? 'pausa' : 'play'); }
  function pararTemporizadores(sl) { sl.querySelectorAll('.temporizador').forEach((t) => { clearInterval(t._int); t._int = null; t.classList.remove('corriendo'); iconoTemp(t); }); }
  function fmt(s) { const m = Math.floor(s / 60), r = s % 60; return `${m}:${String(r).padStart(2, '0')}`; }
  document.querySelectorAll('.temporizador').forEach((t) => {
    t._rest = parseInt(t.dataset.seg, 10);
    t.querySelector('.tiempo').textContent = fmt(t._rest);
    t.addEventListener('click', () => alternarTemporizador(t));
  });
  function alternarTemporizador(t) {
    if (!t) return;
    if (t._int) { clearInterval(t._int); t._int = null; t.classList.remove('corriendo'); iconoTemp(t); return; }
    if (t._rest <= 0) { t._rest = parseInt(t.dataset.seg, 10); t.classList.remove('fin'); }
    t.classList.add('corriendo');
    t._int = setInterval(() => {
      t._rest--; t.querySelector('.tiempo').textContent = fmt(Math.max(0, t._rest));
      if (t._rest <= 0) { clearInterval(t._int); t._int = null; t.classList.remove('corriendo'); t.classList.add('fin'); iconoTemp(t); }
    }, 1000);
    iconoTemp(t);
  }

  // ---------- índice (O)
  const indice = document.getElementById('indice');
  const lista = indice.querySelector('ol');
  slides.forEach((sl, i) => {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.type = 'button';
    b.innerHTML = `<span class="n">${String(i + 1).padStart(2, '0')}</span>${sl.dataset.titulo || 'Diapositiva ' + (i + 1)}`;
    b.addEventListener('click', () => { cerrarIndice(); ir(i, 0); });
    li.appendChild(b); lista.appendChild(li);
  });
  function abrirIndice() { indice.hidden = false; lista.children[idx].querySelector('button').focus(); }
  function cerrarIndice() { indice.hidden = true; }
  document.getElementById('btn-indice').addEventListener('click', () => (indice.hidden ? abrirIndice() : cerrarIndice()));
  indice.querySelector('.cerrar').addEventListener('click', cerrarIndice);

  // ---------- teclado
  function teclado(ev) {
    const k = ev.key;
    if (ev.target && /INPUT|TEXTAREA|SELECT/.test(ev.target.tagName)) return;
    if (!indice.hidden) { if (k === 'Escape' || k === 'o' || k === 'O') { cerrarIndice(); ev.preventDefault && ev.preventDefault(); } return; }
    if (/^[0-9]$/.test(k)) { numBuf += k; clearTimeout(numTimer); numTimer = setTimeout(() => { numBuf = ''; }, 1500); return; }
    switch (k) {
      case 'ArrowRight': case 'PageDown': case ' ': case 'Spacebar': case 'next':
        ev.preventDefault && ev.preventDefault(); siguiente(); break;
      case 'Enter':
        ev.preventDefault && ev.preventDefault();
        if (numBuf) { const n = parseInt(numBuf, 10); numBuf = ''; ir(n - 1, 0); } else siguiente();
        break;
      case 'ArrowLeft': case 'PageUp': case 'Backspace': case 'prev':
        ev.preventDefault && ev.preventDefault(); anterior(); break;
      case 'Home': ir(0, 0); break;
      case 'End': ir(N - 1, 0); break;
      case 'o': case 'O': abrirIndice(); break;
      case 'f': case 'F': pantallaCompleta(); break;
      case 'b': case 'B': case '.': document.body.classList.toggle('negro'); break;
      case 't': case 'T': alternarTemporizador(slides[idx].querySelector('.temporizador')); break;
      case 'e': case 'E': abrir3D(); break;
      default: break;
    }
  }
  addEventListener('keydown', teclado);

  function pantallaCompleta() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen().catch(() => {});
    else document.exitFullscreen && document.exitFullscreen();
  }
  document.addEventListener('fullscreenchange', () => {
    const b = document.getElementById('btn-pantalla');
    const en = document.fullscreenElement === document.documentElement;
    window.cambiarIcono && cambiarIcono(b, en ? 'contraer' : 'expandir');
    b.dataset.tip = en ? 'Salir de pantalla completa (F)' : 'Pantalla completa (F)';
    b.setAttribute('aria-label', en ? 'Salir de pantalla completa' : 'Pantalla completa');
    if (!document.fullscreenElement) { try { window.focus(); } catch (e) {} }
  });
  document.getElementById('btn-pantalla').addEventListener('click', pantallaCompleta);

  // ---------- clic y gestos: clic en el tercio derecho avanza, izquierdo retrocede (fuera de controles)
  stage.addEventListener('click', (ev) => {
    if (ev.target.closest('a, button, input, iframe, .embed3d, .temporizador, .interactivo, label')) return;
    const r = stage.getBoundingClientRect();
    const x = (ev.clientX - r.left) / r.width;
    if (x > 0.62) siguiente(); else if (x < 0.2) anterior();
  });
  let tx = null, ty = null;
  stage.addEventListener('pointerdown', (e) => { if (e.pointerType === 'touch') { tx = e.clientX; ty = e.clientY; } });
  stage.addEventListener('pointerup', (e) => {
    if (tx === null) return;
    const dx = e.clientX - tx, dy = e.clientY - ty; tx = null;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) (dx < 0 ? siguiente : anterior)();
  });
  document.addEventListener('wheel', (e) => e.preventDefault(), { passive: false });

  // ---------- elementos interactivos: contador de ángeles
  document.querySelectorAll('[data-angeles]').forEach((box) => {
    const btn = box.querySelector('button'); const cont = box.querySelector('.cuenta'); const campo = box.querySelector('.campo');
    let n = 0;
    btn.addEventListener('click', () => {
      n++; cont.textContent = n;
      const a = document.createElement('span'); a.className = 'angel'; a.textContent = '✦';
      a.style.left = (8 + Math.random() * 84) + '%'; a.style.top = (8 + Math.random() * 84) + '%';
      a.style.fontSize = (22 + Math.random() * 30) + 'px'; a.style.transform = `rotate(${Math.random() * 360}deg)`;
      campo.appendChild(a);
    });
  });

  // ---------- modo sin conexión («Preparar clase»)
  const btnPrep = document.getElementById('btn-preparar');
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
    const txtPrep = btnPrep.querySelector('.txt');
    btnPrep.addEventListener('click', async () => {
      txtPrep.textContent = 'Guardando…'; btnPrep.disabled = true;
      try {
        const reg = await navigator.serviceWorker.ready;
        const canal = new MessageChannel();
        canal.port1.onmessage = (ev) => {
          const d = ev.data || {};
          if (d.progreso) txtPrep.textContent = `Guardando… ${d.progreso}`;
          if (d.listo) { txtPrep.textContent = d.errores ? `Listo (con ${d.errores} fallos)` : 'Listo para clase sin conexión'; btnPrep.disabled = false; if (!d.errores && window.cambiarIcono) cambiarIcono(btnPrep, 'listo'); }
        };
        reg.active.postMessage({ type: 'precargar' }, [canal.port2]);
      } catch (e) { txtPrep.textContent = 'No se pudo preparar'; btnPrep.disabled = false; }
    });
  } else { btnPrep.hidden = true; }

  desdeHash();
})();
