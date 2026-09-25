// Imágenes dentro de las escenas 3D (cuadros enmarcados, discos, fondos que se funden, láminas en el suelo).
// Se describen por escena en decor/<id>.json, sin tocar Blender:
// { "imagenes": [ {
//     "src": "../img/pd-arnolfini.webp",     // ruta relativa a docs/3d/
//     "tipo": "cuadro" | "disco" | "fondo" | "suelo",
//     "recorte": [x0, y0, x1, y1],           // opcional, fracciones 0..1 de la imagen (p. ej. un detalle)
//     "ancho": 2.2,                          // metros (el alto sale de la proporción; en «disco», el diámetro)
//     "pos": [x, y, z],                      // coordenadas three.js (Y arriba) = Blender (x, z, -y)
//     "ancla": "nombre_de_nodo",             // opcional: pos se suma a la posición (animada) de ese nodo
//     "rot": [rx, ry, rz],                   // grados; o bien
//     "mira": "cam_3" | "camara",            // orientar hacia un nodo, o hacia la cámara (giro sólo en Y)
//     "marco": "oro" | "fino" | "ninguno",   // por defecto: oro en cuadro/disco, ninguno en fondo/suelo
//     "estados": [2, 3],                     // en qué estados se ve (omitir = siempre)
//     "opacidad": 1,                         // máxima (fondo: 0.85 por defecto)
//     "lavado": 0.35,                        // velo de papel sobre la imagen, 0..1 (fondo: 0.35 por defecto; resto: 0)
//     "pie": "Van Eyck, <i>El matrimonio Arnolfini</i>, 1434"  // rótulo opcional bajo la imagen
// } ] }
import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

const items = [];
const v = new THREE.Vector3();
const DEG = Math.PI / 180;

function lienzo(img, d) {
  const [x0, y0, x1, y1] = d.recorte || [0, 0, 1, 1];
  const sx = x0 * img.naturalWidth, sy = y0 * img.naturalHeight;
  let sw = (x1 - x0) * img.naturalWidth, sh = (y1 - y0) * img.naturalHeight;
  let ox = sx, oy = sy;
  if (d.tipo === 'disco') { const l = Math.min(sw, sh); ox += (sw - l) / 2; oy += (sh - l) / 2; sw = sh = l; }
  const w = Math.round(Math.min(sw, 2048)), h = Math.round(w * sh / sw);
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const g = cv.getContext('2d');
  g.drawImage(img, ox, oy, sw, sh, 0, 0, w, h);
  const lavado = d.lavado ?? (d.tipo === 'fondo' ? 0.35 : 0);   // velo de papel sobre la imagen (0..1)
  if (lavado > 0) { g.fillStyle = `rgba(244,238,227,${lavado})`; g.fillRect(0, 0, w, h); }
  if (d.tipo === 'disco' || d.tipo === 'fondo') {
    g.globalCompositeOperation = 'destination-in';
    if (d.tipo === 'disco') { g.beginPath(); g.arc(w / 2, h / 2, w / 2 - 1, 0, Math.PI * 2); g.fill(); }
    else {
      const m = document.createElement('canvas'); m.width = m.height = 512;
      const mg = m.getContext('2d');
      const gr = mg.createRadialGradient(256, 256, 70, 256, 256, 256);
      gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.55, 'rgba(0,0,0,.85)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      mg.fillStyle = gr; mg.fillRect(0, 0, 512, 512);
      g.drawImage(m, 0, 0, w, h);
    }
  }
  return { cv, asp: h / w };
}

function matOro() {
  return new THREE.MeshPhysicalMaterial({ color: '#E2B650', metalness: 0.9, roughness: 0.3, clearcoat: 0.4, clearcoatRoughness: 0.15,
    envMapIntensity: 1.9, emissive: '#B8891A', emissiveIntensity: 0.12, transparent: true });
}
function matFino() { return new THREE.MeshPhysicalMaterial({ color: '#2F3134', roughness: 0.35, clearcoat: 1, clearcoatRoughness: 0.08, transparent: true }); }

function marcoRect(ancho, alto, tipo) {
  const g = new THREE.Group();
  const b = tipo === 'fino' ? Math.max(0.025, Math.min(ancho, alto) * 0.025) : Math.max(0.05, Math.min(ancho, alto) * 0.07);
  const p = tipo === 'fino' ? 0.04 : 0.07;
  const mat = tipo === 'fino' ? matFino() : matOro();
  const barra = (w, h, x, y) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, p), mat); m.position.set(x, y, p / 2 - 0.01); m.castShadow = true; g.add(m); };
  barra(ancho + 2 * b, b, 0, alto / 2 + b / 2); barra(ancho + 2 * b, b, 0, -alto / 2 - b / 2);
  barra(b, alto, -ancho / 2 - b / 2, 0); barra(b, alto, ancho / 2 + b / 2, 0);
  if (tipo !== 'fino') { // filete interior oscuro
    const f = matFino();
    const fil = (w, h, x, y) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.012), f); m.position.set(x, y, 0.004); g.add(m); };
    const e = b * 0.18;
    fil(ancho, e, 0, alto / 2 - e / 2); fil(ancho, e, 0, -alto / 2 + e / 2); fil(e, alto, -ancho / 2 + e / 2, 0); fil(e, alto, ancho / 2 - e / 2, 0);
  }
  return g;
}

export async function montarDecor({ id, scene, nodos, archivo }) {
  let dec;
  try { const r = await fetch(`decor/${archivo || id}.json`, { cache: 'no-cache' }); if (!r.ok) return; dec = await r.json(); }
  catch (e) { return; }
  const ld = new THREE.ImageLoader();
  for (const d0 of dec.imagenes || []) {
    const d = { tipo: 'cuadro', ...d0 };
    try {
      const img = await ld.loadAsync(d.src);
      const { cv, asp } = lienzo(img, d);
      const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
      const ancho = d.ancho || 2, alto = d.tipo === 'disco' ? ancho : ancho * asp;
      const grupo = new THREE.Group(); grupo.name = 'decor_' + (d.src.split('/').pop() || '');
      const opMax = d.opacidad ?? (d.tipo === 'fondo' ? 0.85 : 1);
      let lamina;
      if (d.tipo === 'fondo') {
        lamina = new THREE.Mesh(new THREE.PlaneGeometry(ancho, alto),
          new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false }));
        lamina.renderOrder = -2;
      } else if (d.tipo === 'disco') {
        lamina = new THREE.Mesh(new THREE.CircleGeometry(ancho / 2, 96),
          new THREE.MeshPhysicalMaterial({ map: tex, roughness: 0.4, clearcoat: 0.6, clearcoatRoughness: 0.12, transparent: true, alphaTest: 0.02 }));
        lamina.position.z = 0.012;
        const marco = d.marco ?? 'oro';
        if (marco !== 'ninguno') {
          const aro = new THREE.Mesh(new THREE.TorusGeometry(ancho / 2 + ancho * 0.03, ancho * 0.035, 20, 128), marco === 'fino' ? matFino() : matOro());
          aro.castShadow = true; grupo.add(aro);
          const dorso = new THREE.Mesh(new THREE.CircleGeometry(ancho / 2 + ancho * 0.05, 96), matFino()); dorso.position.z = -0.01; dorso.rotation.y = Math.PI; grupo.add(dorso);
        }
      } else {
        lamina = new THREE.Mesh(new THREE.PlaneGeometry(ancho, alto),
          new THREE.MeshPhysicalMaterial({ map: tex, roughness: d.tipo === 'suelo' ? 0.75 : 0.5, clearcoat: d.tipo === 'suelo' ? 0.1 : 0.35, clearcoatRoughness: 0.3, transparent: true }));
        lamina.receiveShadow = true;
        const marco = d.marco ?? (d.tipo === 'suelo' ? 'ninguno' : 'oro');
        if (marco !== 'ninguno') grupo.add(marcoRect(ancho, alto, marco));
        if (d.tipo === 'cuadro') { // dorso para que no se vea hueco desde atrás
          const dorso = new THREE.Mesh(new THREE.BoxGeometry(ancho, alto, 0.02), matFino()); dorso.position.z = -0.012; dorso.castShadow = true; grupo.add(dorso);
        }
      }
      grupo.add(lamina);
      if (d.pos) grupo.position.fromArray(d.pos);
      const base = grupo.position.clone();
      if (d.tipo === 'suelo' && !d.rot) grupo.rotation.x = -Math.PI / 2;
      if (d.rot) grupo.rotation.set(d.rot[0] * DEG, d.rot[1] * DEG, d.rot[2] * DEG);
      scene.add(grupo);
      let pie = null;
      if (d.pie) {
        const div = document.createElement('div'); div.className = 'etq pie'; div.innerHTML = d.pie;
        pie = new CSS2DObject(div); pie.center.set(0.5, 0);
        pie.position.set(0, -alto / 2 - (d.marco === 'ninguno' || d.tipo === 'fondo' ? 0.06 : Math.max(0.12, alto * 0.09)), 0.02);
        grupo.add(pie);
      }
      const mats = []; grupo.traverse((o) => { if (o.isMesh) { const ms = Array.isArray(o.material) ? o.material : [o.material]; ms.forEach((m) => { m.transparent = true; mats.push(m); }); } });
      const it = { d, grupo, base, mats, pie, op: 0, meta: 0, opMax };
      if (d.mira && d.mira !== 'camara' && nodos[d.mira]) {
        const nLook = d.mira.startsWith('cam_') ? nodos['look_' + d.mira.slice(4)] : null;
        if (nLook) { // alineada con el encuadre de ese estado: de frente a la cámara y derecha en pantalla
          const cam = new THREE.PerspectiveCamera(); nodos[d.mira].getWorldPosition(cam.position);
          nLook.getWorldPosition(v); cam.lookAt(v); grupo.quaternion.copy(cam.quaternion);
        } else { grupo.updateMatrixWorld(true); nodos[d.mira].getWorldPosition(v); grupo.lookAt(v); }
      }
      aplicarOpacidad(it, 0);
      items.push(it);
    } catch (e) { console.warn('imagen no disponible', d.src, e); }
  }
  items.nodos = nodos;
  return items.length;
}

function aplicarOpacidad(it, op) {
  it.op = op;
  for (const m of it.mats) m.opacity = op * it.opMax;
  it.grupo.visible = op > 0.005;
}

// estado n: qué imágenes deben verse (con retraso opcional para acompañar a la cámara)
export function estadoDecor(n, retrasoMs = 0) {
  for (const it of items) {
    const ver = !it.d.estados || it.d.estados.includes(n);
    clearTimeout(it._t);
    if (!ver) { it.meta = 0; if (it.pie) it.pie.element.classList.remove('on'); }
    else {
      const encender = () => { it.meta = 1; if (it.pie) it.pie.element.classList.add('on'); };
      if (retrasoMs) it._t = setTimeout(encender, retrasoMs); else encender();
    }
  }
}
export function inmediatoDecor() { for (const it of items) aplicarOpacidad(it, it.meta); }

export function animarDecor(dt, camera) {
  for (const it of items) {
    if (it.d.ancla && items.nodos[it.d.ancla]) { items.nodos[it.d.ancla].getWorldPosition(v); it.grupo.position.copy(v).add(it.base); }
    if (it.d.mira === 'camara') { v.copy(camera.position); v.y = it.grupo.position.y; it.grupo.lookAt(v); }
    if (Math.abs(it.meta - it.op) > 0.002) aplicarOpacidad(it, it.op + (it.meta - it.op) * Math.min(1, dt * 3.5));
  }
}
