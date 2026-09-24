// Visor 3D genérico: carga escenas/<id>.glb + escenas/<id>.json y recorre sus estados.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const qs = new URLSearchParams(location.search);
if (qs.get('tema')) document.documentElement.dataset.tema = qs.get('tema');
if (qs.get('acento')) document.documentElement.dataset.acento = qs.get('acento');
const ID = qs.get('e') || 'sustitucion';
const EMBED = qs.get('embed') === '1';
const SIN_PANEL = qs.get('panel') === '0';
let estadoInicial = parseInt(qs.get('s') || '0', 10) || 0;

const $ = (id) => document.getElementById(id);
const root = $('visor');
if (EMBED) root.classList.add('embed');
if (SIN_PANEL) root.classList.add('sin-panel');
if (EMBED) $('volver').hidden = true;
else if (qs.get('volver')) $('volver').href = '../index.html' + qs.get('volver');

const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

let man, renderer, labelRenderer, scene, camera, controls, mixer, action, clipDur = 0;
let nodos = {}, etiquetas = {}, actual = -1, tiempo = 0;
let tweenCam = null, tweenT = null, sliderAzimut = null, listo = false;

function post(msg) { if (window.parent !== window) window.parent.postMessage({ fuente: 'visor3d', id: ID, ...msg }, '*'); }

async function init() {
  $('poster').src = `posters/${ID}-${estadoInicial}.webp`;
  $('poster').onerror = () => { $('poster').onerror = null; $('poster').src = `posters/${ID}.webp`; };
  man = await fetch(`escenas/${ID}.json`, { cache: 'no-cache' }).then((r) => { if (!r.ok) throw new Error('manifiesto'); return r.json(); });
  document.title = `${man.titulo} · Esquema 3D`;
  $('titulo').textContent = man.titulo;

  const cont = $('lienzo');
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;
  cont.appendChild(renderer.domElement);
  labelRenderer = new CSS2DRenderer();
  labelRenderer.domElement.style.position = 'absolute';
  labelRenderer.domElement.style.inset = '0';
  labelRenderer.domElement.style.pointerEvents = 'none';
  cont.appendChild(labelRenderer.domElement);

  scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.55;
  const key = new THREE.DirectionalLight(0xffeedd, 2.2); key.position.set(-5, 7, 6); scene.add(key);
  const fill = new THREE.DirectionalLight(0xbfdfff, 0.6); fill.position.set(6, 2, 5); scene.add(fill);
  const rim = new THREE.DirectionalLight(0xfff4e6, 1.1); rim.position.set(0, 5, -7); scene.add(rim);
  scene.add(new THREE.HemisphereLight(0x3a2c22, 0x0d0a08, 0.5));

  camera = new THREE.PerspectiveCamera(35, 16 / 9, 0.05, 200);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.minDistance = 1.5; controls.maxDistance = 220; controls.enablePan = false;
  controls.addEventListener('start', () => { tweenCam = null; });

  const gltf = await new GLTFLoader().loadAsync(`escenas/${ID}.glb`);
  scene.add(gltf.scene);
  gltf.scene.traverse((o) => {
    if (o.name) nodos[o.name] = o;
    if (o.isMesh) {
      const m = o.material;
      if (m && m.transparent) { m.depthWrite = false; o.renderOrder = 2; }
    }
  });
  if (gltf.animations.length) {
    mixer = new THREE.AnimationMixer(gltf.scene);
    const clip = gltf.animations.length === 1 ? gltf.animations[0]
      : new THREE.AnimationClip('todo', -1, gltf.animations.flatMap((c) => c.tracks));
    action = mixer.clipAction(clip);
    action.setLoop(THREE.LoopOnce); action.clampWhenFinished = true; action.play(); action.paused = true;
    clipDur = clip.duration;
  }

  // etiquetas
  for (const [nombre, def] of Object.entries(man.etiquetas || {})) {
    const n = nodos[nombre];
    if (!n) { console.warn('falta ancla', nombre); continue; }
    const div = document.createElement('div');
    div.className = 'etq ' + (def.clase || '');
    div.innerHTML = def.html;
    const obj = new CSS2DObject(div);
    n.add(obj);
    etiquetas[nombre] = div;
  }

  // botones de estado
  const nav = $('estados');
  man.estados.forEach((e, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.innerHTML = `<span class="n">${i + 1}</span>${e.nombre}`;
    b.addEventListener('click', () => ir(i));
    nav.appendChild(b);
  });

  // slider
  $('slider').addEventListener('input', (ev) => {
    const e = man.estados[actual]; if (!e || !e.slider) return;
    const v = ev.target.value / 1000;
    if (e.slider.tipo === 'tiempo') { tweenT = null; fijarTiempo(e.slider.t0 + (e.slider.t1 - e.slider.t0) * v); }
    if (e.slider.tipo === 'azimut') { tweenCam = null; azimut(e.slider.min + (e.slider.max - e.slider.min) * v); }
    post({ type: 'slider', v });
  });

  new ResizeObserver(redimensionar).observe(root);
  redimensionar();
  listo = true;
  ir(Math.min(estadoInicial, man.estados.length - 1), true);
  renderer.setAnimationLoop(bucle);
  requestAnimationFrame(() => $('poster').classList.add('fuera'));
  post({ type: 'listo', estados: man.estados.length, nombres: man.estados.map((e) => e.nombre) });
}

function redimensionar() {
  const w = root.clientWidth, h = root.clientHeight;
  renderer.setSize(w, h, false);
  renderer.domElement.style.width = w + 'px'; renderer.domElement.style.height = h + 'px';
  labelRenderer.setSize(w, h);
  camera.aspect = w / h; camera.updateProjectionMatrix();
}

function pos(nombre) {
  const n = nodos[nombre]; const v = new THREE.Vector3();
  if (n) n.getWorldPosition(v);
  return v;
}

function fijarTiempo(t) {
  tiempo = Math.max(0, Math.min(t, clipDur || t));
  if (action) { action.time = tiempo; mixer.update(0); }
}

function azimut(grados) {
  const e = man.estados[actual];
  const look = pos(e.look), cam0 = pos(e.cam);
  const off = cam0.clone().sub(look);
  off.applyAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(grados));
  camera.position.copy(look).add(off);
  controls.target.copy(look);
  camera.lookAt(look);
}

function ir(n, inmediato = false) {
  if (!man || !listo) { estadoInicial = n; return; }
  n = Math.max(0, Math.min(n, man.estados.length - 1));
  const e = man.estados[n];
  const ant = actual;
  actual = n;
  // cámara
  const destPos = pos(e.cam), destLook = pos(e.look);
  if (inmediato || reduce) {
    camera.position.copy(destPos); controls.target.copy(destLook); camera.fov = e.fov; camera.updateProjectionMatrix();
    tweenCam = null;
  } else {
    tweenCam = { t: 0, dur: 1.3, p0: camera.position.clone(), l0: controls.target.clone(), f0: camera.fov, p1: destPos, l1: destLook, f1: e.fov };
  }
  controls.enabled = e.orbita !== false;
  // línea de tiempo
  if (action) {
    if (inmediato || reduce || n < ant) { tweenT = null; fijarTiempo(e.t1); }
    else tweenT = { t0: tiempo, t1: e.t1, dur: Math.min(Math.max(Math.abs(e.t1 - tiempo), 0.3), 6), t: 0 };
  }
  // etiquetas
  const vis = new Set(e.etiquetas || []);
  clearTimeout(ir._t);
  const retraso = (!inmediato && !reduce && tweenT) ? Math.min(tweenT.dur * 0.8, 3.5) * 1000 : 0;
  for (const [nombre, div] of Object.entries(etiquetas)) {
    if (!vis.has(nombre)) div.classList.remove('on');           // lo que sale, se va de inmediato
    else if (!retraso) div.classList.add('on');
  }
  if (retraso) ir._t = setTimeout(() => { for (const n of vis) if (etiquetas[n]) etiquetas[n].classList.add('on'); }, retraso);
  // textos
  $('texto').innerHTML = e.texto || '';
  $('ref').textContent = e.ref || '';
  $('pregunta').hidden = !e.pregunta; $('pregunta').textContent = e.pregunta || '';
  // slider
  const sc = $('slider-caja');
  sc.hidden = !e.slider;
  if (e.slider) {
    $('slider-etq').textContent = e.slider.etiqueta || '';
    $('slider-min').textContent = e.slider.min_txt || (e.slider.tipo === 'azimut' ? 'izquierda' : '');
    $('slider-max').textContent = e.slider.max_txt || (e.slider.tipo === 'azimut' ? 'derecha' : '');
    const v0 = e.slider.tipo === 'azimut' ? (0 - e.slider.min) / (e.slider.max - e.slider.min) : 1;
    $('slider').value = Math.round(v0 * 1000);
  }
  [...$('estados').children].forEach((b, i) => { if (i === n) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current'); });
  post({ type: 'estado', n });
}

const reloj = new THREE.Clock();
function bucle() {
  const dt = Math.min(reloj.getDelta(), 0.05);
  if (tweenCam) {
    tweenCam.t += dt / tweenCam.dur;
    const k = easeInOut(Math.min(tweenCam.t, 1));
    camera.position.lerpVectors(tweenCam.p0, tweenCam.p1, k);
    controls.target.lerpVectors(tweenCam.l0, tweenCam.l1, k);
    camera.fov = tweenCam.f0 + (tweenCam.f1 - tweenCam.f0) * k; camera.updateProjectionMatrix();
    if (tweenCam.t >= 1) tweenCam = null;
  }
  if (tweenT) {
    tweenT.t += dt / tweenT.dur;
    const k = easeInOut(Math.min(tweenT.t, 1));
    fijarTiempo(tweenT.t0 + (tweenT.t1 - tweenT.t0) * k);
    if (tweenT.t >= 1) tweenT = null;
  }
  controls.update();
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}

// teclado y mensajes
addEventListener('keydown', (ev) => {
  if (ev.target && ev.target.tagName === 'INPUT' && (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight')) return;
  if (EMBED) { // incrustado: la presentación manda (ella misma escucha el teclado de este iframe si es mismo origen)
    try { if (window.parent.document) return; } catch (e) { /* otro origen */ }
    ev.preventDefault(); post({ type: 'tecla', key: ev.key }); return;
  }
  if (ev.key === 'ArrowRight') { ev.preventDefault(); if (actual < man.estados.length - 1) ir(actual + 1); else post({ type: 'tecla', key: 'next' }); }
  else if (ev.key === 'ArrowLeft') { ev.preventDefault(); if (actual > 0) ir(actual - 1); else post({ type: 'tecla', key: 'prev' }); }
  else if (/^[1-9]$/.test(ev.key)) ir(parseInt(ev.key, 10) - 1);
  else if (EMBED) post({ type: 'tecla', key: ev.key });
});
addEventListener('message', (ev) => {
  const d = ev.data || {};
  if (d.type === 'estado' && typeof d.n === 'number') ir(d.n);
  if (d.type === 'liberar' && renderer) { renderer.setAnimationLoop(null); renderer.dispose(); try { renderer.forceContextLoss(); } catch (e) {} }
});
document.addEventListener('visibilitychange', () => { if (!renderer) return; renderer.setAnimationLoop(document.hidden ? null : bucle); });

init().catch((err) => {
  console.error(err);
  $('error').hidden = false;
  $('error').textContent = 'No se pudo cargar el esquema 3D. Se muestra la imagen fija.';
  $('poster').classList.remove('fuera');
});
