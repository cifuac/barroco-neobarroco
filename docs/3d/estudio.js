// Estudio de render: entorno con reflejos, luces con sombras suaves, suelo de mármol y materiales físicos.
// Se aplica a cualquier escena exportada desde Blender (materiales por rol: significado, significante, etc.).
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export function prepararRender(renderer) {
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.08;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.VSMShadowMap;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
}

// ------------------------------------------------------------------ materiales
const c = (hex) => new THREE.Color(hex);
function fisico(orig, extra) {
  const m = new THREE.MeshPhysicalMaterial({
    name: orig.name,
    color: orig.color ? orig.color.clone() : c('#ffffff'),
    emissive: orig.emissive ? orig.emissive.clone() : c('#000000'),
    emissiveIntensity: orig.emissiveIntensity ?? 1,
    map: orig.map || null,
    vertexColors: !!orig.vertexColors,
    transparent: !!orig.transparent,
    opacity: orig.opacity ?? 1,
    side: orig.side ?? THREE.FrontSide,
    depthWrite: orig.transparent ? false : true,
    ...extra,
  });
  return m;
}
function rol(nombre) {
  const n = (nombre || '').toLowerCase();
  if (/^(significado|halo_oro|oro)/.test(n)) return 'oro';
  if (/^(significante|arco_nacar|cartela)/.test(n)) return 'nacar';
  if (/^(espejo|azogue_facetas)/.test(n)) return 'espejo';
  if (/^(ausencia|hueco)/.test(n)) return 'laca_roja';
  if (/^(trayecto|azogue_linea)/.test(n)) return 'esmalte';
  if (/^(ajeno|costura)/.test(n)) return 'laca_magenta';
  if (/^(soporte|barro|grafito|marco|tinta_renglon|sepia_renglon)/.test(n)) return 'piedra';
  if (/^(lamina|papel|estuco|estrato|tinte)/.test(n)) return 'papel';
  if (/^(vidrio|cristal|vaho|calido|fantasma)/.test(n)) return 'velo';
  if (/^logos/.test(n)) return 'luz';
  return 'otro';
}
function mejorar(orig) {
  switch (rol(orig.name)) {
    case 'oro': {
      const m = fisico(orig, { metalness: 1, roughness: 0.2, clearcoat: 0.25, clearcoatRoughness: 0.2, envMapIntensity: 1.35 });
      m.color.lerp(c('#E6B54A'), 0.35);
      return m;
    }
    case 'nacar': {
      const m = fisico(orig, {
        metalness: 0, roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.08,
        iridescence: 0.65, iridescenceIOR: 1.32, iridescenceThicknessRange: [180, 560],
        sheen: 0.5, sheenRoughness: 0.4, sheenColor: c('#FFF3E4'), envMapIntensity: 1.1,
      });
      m.color.lerp(c('#F1EBDF'), 0.55);
      return m;
    }
    case 'espejo':
      return fisico(orig, { metalness: 1, roughness: Math.min(orig.roughness ?? 0.05, 0.12), envMapIntensity: 1.7, color: c('#DDE3E6') });
    case 'laca_roja':
      return fisico(orig, { roughness: 0.26, clearcoat: 1, clearcoatRoughness: 0.06, emissiveIntensity: (orig.emissiveIntensity ?? 1) * 0.55, envMapIntensity: 1 });
    case 'esmalte':
      return fisico(orig, { roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.05, emissiveIntensity: (orig.emissiveIntensity ?? 1) * 0.7, envMapIntensity: 1 });
    case 'laca_magenta':
      return fisico(orig, { roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.08, emissiveIntensity: (orig.emissiveIntensity ?? 1) * 0.6 });
    case 'piedra':
      return fisico(orig, { roughness: 0.42, clearcoat: 0.45, clearcoatRoughness: 0.25, metalness: 0, envMapIntensity: 0.8 });
    case 'papel':
      return fisico(orig, { roughness: 0.82, sheen: 0.35, sheenRoughness: 0.7, sheenColor: c('#FFF8EC'), envMapIntensity: 0.55 });
    case 'velo': {
      const m = fisico(orig, { roughness: 0.08, clearcoat: 1, clearcoatRoughness: 0.05, envMapIntensity: 1.2 });
      m.opacity = Math.min(m.opacity, 0.14); m.transparent = true; m.depthWrite = false;
      return m;
    }
    case 'luz':
      return fisico(orig, { roughness: 0.3, emissiveIntensity: (orig.emissiveIntensity ?? 1) * 0.9 });
    default:
      return fisico(orig, { roughness: orig.roughness ?? 0.5, metalness: orig.metalness ?? 0 });
  }
}

// ------------------------------------------------------------------ suelo con desvanecido radial
function texturaDesvanecido() {
  const cv = document.createElement('canvas'); cv.width = cv.height = 512;
  const g = cv.getContext('2d');
  const grd = g.createRadialGradient(256, 256, 0, 256, 256, 256);
  grd.addColorStop(0, '#fff'); grd.addColorStop(0.3, '#eee'); grd.addColorStop(0.65, '#555'); grd.addColorStop(1, '#000');
  g.fillStyle = grd; g.fillRect(0, 0, 512, 512);
  const t = new THREE.CanvasTexture(cv); return t;
}

export async function montarEstudio({ renderer, scene, raiz, fijarTiempoFinal }) {
  // 1) entorno: panorámica de una iglesia barroca (reflejos del oro y del espejo)
  const pmrem = new THREE.PMREMGenerator(renderer);
  try {
    const tex = await new THREE.TextureLoader().loadAsync('texturas/entorno.webp');
    tex.mapping = THREE.EquirectangularReflectionMapping; tex.colorSpace = THREE.SRGBColorSpace;
    scene.environment = pmrem.fromEquirectangular(tex).texture;
    scene.environmentIntensity = 0.95;
    tex.dispose();
  } catch (e) {
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environmentIntensity = 0.6;
  }

  // 2) materiales físicos y sombras
  raiz.traverse((o) => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const nuevos = mats.map((m) => (m ? mejorar(m) : m));
    o.material = Array.isArray(o.material) ? nuevos : nuevos[0];
    const trans = nuevos.some((m) => m && m.transparent);
    o.castShadow = !trans; o.receiveShadow = true;
    if (trans) o.renderOrder = 2;
  });

  // 3) medidas de la escena con todo visible (fin de la línea de tiempo)
  if (fijarTiempoFinal) fijarTiempoFinal(true);
  raiz.updateMatrixWorld(true);
  const caja = new THREE.Box3();
  raiz.traverse((o) => { if (o.isMesh && o.visible) { const b = new THREE.Box3().setFromObject(o); if (isFinite(b.min.x) && b.getSize(new THREE.Vector3()).length() < 80) caja.union(b); } });
  if (fijarTiempoFinal) fijarTiempoFinal(false);
  const centro = caja.getCenter(new THREE.Vector3());
  const tam = caja.getSize(new THREE.Vector3());
  const R = Math.max(tam.x, tam.z, 4) * 0.75 + 3;

  // 4) luces: clave cálida con sombra suave, relleno frío, contraluz
  const clave = new THREE.DirectionalLight(0xfff0dc, 2.1);
  clave.position.copy(centro).add(new THREE.Vector3(-0.55 * R, 1.35 * R, 0.9 * R));
  clave.target.position.copy(centro);
  clave.castShadow = true;
  clave.shadow.mapSize.set(2048, 2048);
  const sc = clave.shadow.camera; sc.left = -R; sc.right = R; sc.top = R; sc.bottom = -R; sc.near = 0.1; sc.far = R * 5;
  clave.shadow.radius = 9; clave.shadow.blurSamples = 16; clave.shadow.bias = -0.0004; clave.shadow.normalBias = 0.02;
  scene.add(clave, clave.target);
  const relleno = new THREE.DirectionalLight(0xcfe0ff, 0.45); relleno.position.copy(centro).add(new THREE.Vector3(R, 0.4 * R, 0.8 * R)); scene.add(relleno);
  const contra = new THREE.DirectionalLight(0xffe9cc, 1.1); contra.position.copy(centro).add(new THREE.Vector3(0.2 * R, 0.9 * R, -1.2 * R)); scene.add(contra);
  scene.add(new THREE.HemisphereLight(0x4a3d33, 0x0c0a09, 0.35));

  // 5) suelo de mármol oscuro que se funde con el fondo
  const suelo = new THREE.Mesh(
    new THREE.CircleGeometry(R * 1.3, 96),
    new THREE.MeshPhysicalMaterial({ color: 0x8f877f, roughness: 0.55, clearcoat: 0.35, clearcoatRoughness: 0.42, specularIntensity: 0.35, envMapIntensity: 0.45, transparent: true, alphaMap: texturaDesvanecido(), depthWrite: false }),
  );
  try {
    const mt = await new THREE.TextureLoader().loadAsync('texturas/marmol.webp');
    mt.colorSpace = THREE.SRGBColorSpace; mt.wrapS = mt.wrapT = THREE.MirroredRepeatWrapping;
    mt.repeat.set(R / 2.2, R / 2.2); mt.anisotropy = renderer.capabilities.getMaxAnisotropy();
    suelo.material.map = mt; suelo.material.color.set(0xb4aca4); suelo.material.needsUpdate = true;
  } catch (e) { suelo.material.color.set(0x2a2521); }
  suelo.rotation.x = -Math.PI / 2;
  suelo.position.set(centro.x, caja.min.y - 0.015, centro.z);
  suelo.receiveShadow = true; suelo.renderOrder = -1;
  // con cámara casi rasante el suelo se vuelve una franja brillante: se desvanece
  const v = new THREE.Vector3();
  suelo.onBeforeRender = (r, s, cam) => {
    v.copy(cam.position).sub(suelo.position);
    const seno = v.y / Math.max(v.length(), 1e-6);
    const k = THREE.MathUtils.smoothstep(seno, 0.1, 0.3);
    suelo.material.opacity = k; suelo.visible = true;
  };
  scene.add(suelo);
  return { centro, R };
}
