// Estudio de render «galería clara»: fondo papel, sombras suaves sobre un suelo invisible,
// reflejos de estudio neutros y materiales físicos recoloreados por rol con la paleta de la presentación.
// Se aplica a cualquier escena exportada desde Blender (los materiales llevan el nombre de su rol).
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export function prepararRender(renderer) {
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.VSMShadowMap;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setClearColor(0x000000, 0);
}

// ------------------------------------------------------------------ paleta (la de tokens.css, tema papel)
export const PALETA = {
  oro: '#E2B650',        // significado: oro pulido
  grafito: '#2F3134',    // significante: laca negra-grafito
  esmeralda: '#16795A',  // trayecto, lectura
  carmin: '#A3245F',     // lo ajeno, la cita
  bermellon: '#B2332A',  // tachadura, ausencia
  piedra: '#D5D0C8',     // plintos y soportes
  marfil: '#F3EEE4',     // lámina, papel, estuco
  tinta: '#2A2B2F',      // renglones, listones
  cristal: '#8FA7AE',    // velos
};

const c = (hex) => new THREE.Color(hex);

// ------------------------------------------------------------------ texturas (papel, mármol, pan de oro, estuco)
// Se proyectan en tres planos en el espacio del objeto: no necesitan UV y no «resbalan» cuando el objeto se mueve.
const TEX = {};
const TEX_NOMBRES = ['papel', 'marmol-claro', 'pan-de-oro', 'estuco'];
let _precarga = null;
export function precargarTexturas(renderer) { return (_precarga ||= _precargar(renderer)); }
async function _precargar(renderer) {
  const ld = new THREE.TextureLoader();
  await Promise.all(TEX_NOMBRES.map(async (n) => {
    try {
      const t = await ld.loadAsync(`texturas/${n}.webp`);
      t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      TEX[n] = t;
    } catch (e) { /* sin textura: material liso */ }
  }));
}
function triplanar(m, nombre, escala, fuerza) {
  const t = TEX[nombre]; if (!t) return m;
  m.onBeforeCompile = (sh) => {
    sh.uniforms.tTri = { value: t }; sh.uniforms.escTri = { value: escala }; sh.uniforms.fzTri = { value: fuerza };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vPosO;\nvarying vec3 vNorO;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvPosO = position;\nvNorO = normal;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D tTri;\nuniform float escTri;\nuniform float fzTri;\nvarying vec3 vPosO;\nvarying vec3 vNorO;')
      .replace('#include <map_fragment>', `#include <map_fragment>
        { vec3 bw = pow(abs(normalize(vNorO)), vec3(4.0)); bw /= (bw.x + bw.y + bw.z + 1e-5);
          vec3 q = vPosO * escTri;
          vec3 tri = texture2D(tTri, q.zy).rgb * bw.x + texture2D(tTri, q.xz).rgb * bw.y + texture2D(tTri, q.xy).rgb * bw.z;
          diffuseColor.rgb *= mix(vec3(1.0), tri * 1.04, fzTri); }`);
  };
  m.customProgramCacheKey = () => `tri-${nombre}-${escala}-${fuerza}`;
  return m;
}
function fisico(orig, extra) {
  return new THREE.MeshPhysicalMaterial({
    name: orig.name,
    color: orig.color ? orig.color.clone() : c('#ffffff'),
    emissive: c('#000000'),
    emissiveIntensity: 0,
    map: orig.map || null,
    vertexColors: !!orig.vertexColors,
    transparent: !!orig.transparent,
    opacity: orig.opacity ?? 1,
    side: orig.side ?? THREE.FrontSide,
    depthWrite: !orig.transparent,
    ...extra,
  });
}

export function rol(nombre) {
  const n = (nombre || '').toLowerCase();
  if (/^(significado|halo_oro|oro)/.test(n)) return 'oro';
  if (/^(significante|arco_nacar|cartela)/.test(n)) return 'laca';
  if (/^(espejo|azogue_facetas)/.test(n)) return 'espejo';
  if (/^(ausencia|hueco)/.test(n)) return 'bermellon';
  if (/^(trayecto|azogue_linea)/.test(n)) return 'esmeralda';
  if (/^(ajeno|costura)/.test(n)) return 'carmin';
  if (/^(soporte|gris_neutro)/.test(n)) return 'piedra';
  if (/^barro/.test(n)) return 'piedra_clara';
  if (/^(grafito|tinta_renglon)/.test(n)) return 'tinta';
  if (/^(sepia_renglon|marco)/.test(n)) return 'propio_oscuro';
  if (/^(lamina|papel|estuco)/.test(n)) return 'marfil';
  if (/^(estrato|tinte)/.test(n)) return 'propio_mate';
  if (/^(vidrio|cristal|vaho|calido)/.test(n)) return 'velo';
  if (/^fantasma/.test(n)) return 'fantasma';
  if (/^logos/.test(n)) return 'luz';
  return 'otro';
}

function mejorar(orig) {
  const m = mejorarBase(orig);
  const n = (orig.name || '').toLowerCase();
  switch (rol(orig.name)) {
    case 'oro': return triplanar(m, 'pan-de-oro', 1.0, 0.9);
    case 'piedra': case 'piedra_clara': return triplanar(m, 'marmol-claro', 0.35, 1.0);
    case 'marfil': return /^estuco/.test(n) ? triplanar(m, 'estuco', 0.45, 1.0) : triplanar(m, 'papel', 0.55, 1.0);
    case 'propio_mate': return triplanar(m, 'papel', 0.55, 0.8);
    default: return m;
  }
}

function mejorarBase(orig) {
  switch (rol(orig.name)) {
    case 'oro':
      return fisico(orig, { color: c(PALETA.oro), metalness: 0.9, roughness: 0.3, clearcoat: 0.4, clearcoatRoughness: 0.15, envMapIntensity: 1.9,
        emissive: c('#B8891A'), emissiveIntensity: 0.12 });
    case 'laca':
      return fisico(orig, { color: c(PALETA.grafito), metalness: 0, roughness: 0.34, clearcoat: 1, clearcoatRoughness: 0.07, envMapIntensity: 1.0 });
    case 'espejo':
      return fisico(orig, { color: c('#E9EDF0'), metalness: 1, roughness: 0.05, envMapIntensity: 1.5 });
    case 'bermellon':
      return fisico(orig, { color: c(PALETA.bermellon), roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.08,
        emissive: c(PALETA.bermellon), emissiveIntensity: 0.12 });
    case 'esmeralda':
      return fisico(orig, { color: c(PALETA.esmeralda), roughness: 0.28, clearcoat: 1, clearcoatRoughness: 0.06,
        emissive: c(PALETA.esmeralda), emissiveIntensity: 0.12 });
    case 'carmin':
      return fisico(orig, { color: c(PALETA.carmin), roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.08,
        emissive: c(PALETA.carmin), emissiveIntensity: 0.1 });
    case 'piedra':
      return fisico(orig, { color: c(PALETA.piedra), roughness: 0.62, clearcoat: 0.25, clearcoatRoughness: 0.4, envMapIntensity: 0.8 });
    case 'piedra_clara':
      return fisico(orig, { color: c('#E6E0D6'), roughness: 0.55, clearcoat: 0.3, clearcoatRoughness: 0.3, envMapIntensity: 0.8 });
    case 'tinta':
      return fisico(orig, { color: c(PALETA.tinta), roughness: 0.45, clearcoat: 0.6, clearcoatRoughness: 0.2 });
    case 'propio_oscuro': {
      const m = fisico(orig, { roughness: 0.4, clearcoat: 0.5, clearcoatRoughness: 0.2 });
      m.color.multiplyScalar(0.8);
      return m;
    }
    case 'marfil':
      return fisico(orig, { color: c(PALETA.marfil), roughness: 0.78, envMapIntensity: 0.7 });
    case 'propio_mate':
      return fisico(orig, { roughness: 0.7, envMapIntensity: 0.7 });
    case 'velo': {
      const m = fisico(orig, { color: c(PALETA.cristal), roughness: 0.1, clearcoat: 1, clearcoatRoughness: 0.05, envMapIntensity: 1.2 });
      m.opacity = Math.min(Math.max(m.opacity, 0.1), 0.16); m.transparent = true; m.depthWrite = false;
      return m;
    }
    case 'fantasma': {
      const m = fisico(orig, { color: c(PALETA.grafito), roughness: 0.5 });
      m.opacity = 0.28; m.transparent = true; m.depthWrite = false;
      return m;
    }
    case 'luz':
      return fisico(orig, { color: c('#E9C46A'), metalness: 0.6, roughness: 0.3, emissive: c('#D9A93A'), emissiveIntensity: 0.35 });
    default:
      return fisico(orig, { roughness: orig.roughness ?? 0.5, metalness: orig.metalness ?? 0 });
  }
}

// ajustes por escena (manifiesto «estudio»): {materiales: {nombre_o_prefijo: {color, roughness, metalness,
// opacity, emissive, emissiveIntensity, clearcoat, envMapIntensity}}, exposicion, entorno, sombra, luz}
function ajustar(m, ajustes) {
  const tabla = (ajustes && ajustes.materiales) || {};
  const nombre = (m.name || '').toLowerCase();
  const clave = Object.keys(tabla).filter((k) => nombre === k.toLowerCase() || nombre.startsWith(k.toLowerCase()))
    .sort((a, b) => b.length - a.length)[0];
  if (!clave) return m;
  for (const [k, v] of Object.entries(tabla[clave])) {
    if (k === 'color' || k === 'emissive' || k === 'sheenColor') m[k] = c(v);
    else if (k in m) m[k] = v;
  }
  if (m.opacity < 1) { m.transparent = true; m.depthWrite = false; }
  m.needsUpdate = true;
  return m;
}

export async function montarEstudio({ renderer, scene, raiz, fijarTiempoFinal, ajustes = {} }) {
  await precargarTexturas(renderer);
  if (ajustes.exposicion) renderer.toneMappingExposure = ajustes.exposicion;
  // 1) entorno de estudio neutro (reflejos limpios en el oro, la laca y el espejo)
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;
  scene.environmentIntensity = ajustes.entorno ?? 0.85;

  // 2) materiales físicos y sombras
  raiz.traverse((o) => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const nuevos = mats.map((m) => (m ? ajustar(mejorar(m), ajustes) : m));
    o.material = Array.isArray(o.material) ? nuevos : nuevos[0];
    const trans = nuevos.some((m) => m && m.transparent);
    o.castShadow = !trans; o.receiveShadow = !trans;
    if (trans) o.renderOrder = 2;
  });

  // 3) medidas de la escena con todo visible (fin de la línea de tiempo)
  if (fijarTiempoFinal) fijarTiempoFinal(true);
  raiz.updateMatrixWorld(true);
  const caja = new THREE.Box3();
  raiz.traverse((o) => {
    if (!o.isMesh || !o.visible) return;
    const b = new THREE.Box3().setFromObject(o);
    const t = b.getSize(new THREE.Vector3());
    if (isFinite(b.min.x) && t.length() < 80 && t.length() > 1e-3) caja.union(b);
  });
  if (fijarTiempoFinal) fijarTiempoFinal(false);
  const centro = caja.getCenter(new THREE.Vector3());
  const tam = caja.getSize(new THREE.Vector3());
  const R = Math.max(tam.x, tam.z, 4) * 0.75 + 3;

  // 4) luces: clave cálida alta con sombra suave, relleno frío, contraluz y cielo
  const clave = new THREE.DirectionalLight(0xfff4e6, ajustes.luz ?? 2.0);
  clave.position.copy(centro).add(new THREE.Vector3(-0.5 * R, 1.6 * R, 0.8 * R));
  clave.target.position.copy(centro);
  clave.castShadow = true;
  clave.shadow.mapSize.set(2048, 2048);
  const sc = clave.shadow.camera; sc.left = -R; sc.right = R; sc.top = R; sc.bottom = -R; sc.near = 0.1; sc.far = R * 6;
  clave.shadow.radius = 14; clave.shadow.blurSamples = 20; clave.shadow.bias = -0.0003; clave.shadow.normalBias = 0.02;
  scene.add(clave, clave.target);
  const relleno = new THREE.DirectionalLight(0xe6eeff, 0.55); relleno.position.copy(centro).add(new THREE.Vector3(R, 0.5 * R, 0.9 * R)); scene.add(relleno);
  const contra = new THREE.DirectionalLight(0xfff2e0, 0.9); contra.position.copy(centro).add(new THREE.Vector3(0.2 * R, 1.0 * R, -1.2 * R)); scene.add(contra);
  scene.add(new THREE.HemisphereLight(0xfffcf6, 0xd8cfc2, 0.45));

  // 5) suelo invisible que sólo recibe sombras (los objetos se posan sobre el papel)
  const suelo = new THREE.Mesh(new THREE.CircleGeometry(R * 1.6, 64),
    new THREE.ShadowMaterial({ color: 0x3a2e24, opacity: ajustes.sombra ?? 0.2, transparent: true, depthWrite: false }));
  suelo.rotation.x = -Math.PI / 2;
  suelo.position.set(centro.x, caja.min.y - 0.012, centro.z);
  suelo.receiveShadow = true; suelo.renderOrder = -1;
  scene.add(suelo);
  return { centro, R, piso: caja.min.y };
}
