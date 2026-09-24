/* Íconos lineales (24×24, trazo) compartidos por la presentación y el visor 3D.
   Uso: <button class="btn-icono" data-icono="expandir" data-tip="Pantalla completa (F)" aria-label="Pantalla completa"></button>
   pintarIconos() inserta el SVG; cambiarIcono(el, 'contraer') lo reemplaza. */
(function () {
  'use strict';
  const ICONOS = {
    expandir: '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
    contraer: '<path d="M8 3v3a2 2 0 0 1-2 2H3"/><path d="M21 8h-3a2 2 0 0 1-2-2V3"/><path d="M3 16h3a2 2 0 0 1 2 2v3"/><path d="M16 21v-3a2 2 0 0 1 2-2h3"/>',
    indice: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    cubo: '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
    volver: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    cerrar: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    play: '<path d="M7 4.8v14.4a1 1 0 0 0 1.52.85l11.5-7.2a1 1 0 0 0 0-1.7L8.52 3.95A1 1 0 0 0 7 4.8Z"/>',
    pausa: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
    descargar: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
    listo: '<path d="M20 6 9 17l-5-5"/>',
    mas: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  };
  const svg = (n) => `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONOS[n] || ''}</svg>`;
  function pintarIconos(root) {
    (root || document).querySelectorAll('[data-icono]').forEach((el) => {
      const previo = el.querySelector(':scope > svg');
      if (previo) previo.outerHTML = svg(el.dataset.icono);
      else el.insertAdjacentHTML('afterbegin', svg(el.dataset.icono));
    });
  }
  function cambiarIcono(el, nombre) {
    if (!el) return;
    el.dataset.icono = nombre;
    const s = el.querySelector(':scope > svg');
    if (s) s.innerHTML = ICONOS[nombre] || '';
  }
  window.ICONOS = ICONOS;
  window.pintarIconos = pintarIconos;
  window.cambiarIcono = cambiarIcono;
  if (document.readyState !== 'loading') pintarIconos();
  else document.addEventListener('DOMContentLoaded', () => pintarIconos());
})();
