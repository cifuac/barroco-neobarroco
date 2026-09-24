"""bb.py — librería común para las escenas 3D de «El barroco y el neobarroco».

Cada escena (repo/blender/scenes/<id>.py) hace:

    import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
    import bb
    S = bb.Escena('sustitucion', 'Sustitución: la figura 1 en profundidad')
    ... construir geometría con los helpers, animar con S.mostrar()/S.mover() ...
    S.estado(nombre=..., texto=..., ref=..., cam=(x,y,z), look=(x,y,z), fov=35, t1=segundos, etiquetas=[...])
    S.exportar()

Ejecutar (headless):
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P repo/blender/scenes/<id>.py

Salida (en repo/docs/3d/):
    escenas/<id>.glb     geometría + un clip de animación (modo SCENE)
    escenas/<id>.json    manifiesto: estados, cámaras, etiquetas, sliders
    posters/<id>-<n>.webp  póster por estado (1600×900) y posters/<id>.webp (estado 0)

Convenciones de nombres de nodos (el visor las busca en el GLB):
    lbl_<clave>   empty: ancla de una etiqueta HTML (texto en el manifiesto)
    cam_<n>, look_<n>  empties: posición y objetivo de la cámara del estado n (los crea S.estado)
    Todo lo demás: libre, pero con nombres legibles.

Coordenadas: Blender Z arriba, metros. Mantener la escena dentro de ±8 m.
"""
import bpy, bmesh, math, json, os, sys
from mathutils import Vector, Matrix, Quaternion

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, '..', '..'))
OUT3D = os.path.join(REPO, 'docs', '3d')
FPS = 30

# ---------------------------------------------------------------- color
TOK = {
    'tinta': '#14100D', 'barro': '#241A14', 'tierra': '#5A4030', 'perla': '#F3EDE2',
    'nacar': '#CFC6B8', 'oro': '#D4A62A', 'oro_viejo': '#7A5A10', 'bermellon': '#C8372D',
    'cian': '#3BB8D6', 'magenta': '#E23C8E', 'azogue': '#9AA4A8', 'grafito': '#4A443E',
    'marfil': '#E9E1D2',
}

def _s2l(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lin(hexstr, a=1.0):
    h = hexstr.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (_s2l(r), _s2l(g), _s2l(b), a)

# ---------------------------------------------------------------- materiales por rol
_MATS = {}
ROLES = {
    # rol: (color, metallic, roughness, emission_color, emission_strength, alpha, coat)
    'significado': ('oro', 1.0, 0.28, None, 0.0, 1.0, 0.0),        # Sdo.: oro, foco lleno
    'significante': ('nacar', 0.0, 0.42, None, 0.0, 1.0, 0.6),      # Snte. presente: nácar con barniz
    'ausencia': ('bermellon', 0.0, 0.5, 'bermellon', 1.6, 1.0, 0.0), # tachadura, contorno del ausente
    'trayecto': ('cian', 0.0, 0.4, 'cian', 1.4, 1.0, 0.0),          # flechas, lectura radial, lector
    'ajeno': ('magenta', 0.0, 0.45, 'magenta', 0.8, 1.0, 0.0),      # cita, lo ajeno
    'soporte': ('grafito', 0.0, 0.88, None, 0.0, 1.0, 0.0),         # plintos, zócalos
    'lamina': ('marfil', 0.0, 0.7, None, 0.0, 1.0, 0.0),            # lámina/papel
    'barro': ('barro', 0.0, 0.95, None, 0.0, 1.0, 0.0),
    'logos': ('perla', 0.0, 0.3, 'perla', 2.5, 1.0, 0.0),           # logos exterior (luz)
    'espejo': ('azogue', 1.0, 0.04, None, 0.0, 1.0, 0.0),
    'vidrio': ('nacar', 0.0, 0.15, None, 0.0, 0.09, 0.0),           # velo translúcido (contexto, envolventes)
    'calido': ('oro', 0.0, 0.3, 'oro', 0.5, 0.11, 0.0),             # velo cálido translúcido
    'fantasma': ('nacar', 0.0, 0.6, None, 0.0, 0.35, 0.0),          # contorno de algo por venir
}

def mat(rol, nombre=None):
    """Material Principled BSDF compatible con glTF para un rol semántico."""
    key = nombre or rol
    if key in _MATS:
        return _MATS[key]
    col, met, rough, emi, emis, alpha, coat = ROLES[rol]
    m = bpy.data.materials.new(key)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = lin(TOK[col])
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    if coat and 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.15
    if emi:
        b.inputs['Emission Color'].default_value = lin(TOK[emi])
        b.inputs['Emission Strength'].default_value = emis
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    m.diffuse_color = lin(TOK[col], alpha)
    _MATS[key] = m
    return m

# ---------------------------------------------------------------- objetos básicos
def _link(ob, parent=None):
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob

def vacio(nombre, loc=(0, 0, 0), parent=None, size=0.1):
    e = bpy.data.objects.new(nombre, None)
    e.empty_display_size = size
    e.location = loc
    return _link(e, parent)

def grupo(nombre, loc=(0, 0, 0), parent=None):
    """Empty que agrupa (se anima escala/posición del grupo completo)."""
    return vacio(nombre, loc, parent, 0.2)

def _obj_from_bm(nombre, bm, material=None, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nombre, me)
    ob.location = loc
    if material:
        me.materials.append(material)
    _link(ob, parent)
    for p in me.polygons:
        p.use_smooth = True
    return ob

def caja(nombre, size=(1, 1, 1), loc=(0, 0, 0), material=None, parent=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = _obj_from_bm(nombre, bm, material, parent, loc)
    for p in ob.data.polygons:
        p.use_smooth = False
    if bevel > 0:
        mod = ob.modifiers.new('bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = 'ANGLE'
        aplicar(ob)
    return ob

def esfera(nombre, r=0.2, loc=(0, 0, 0), material=None, parent=None, subdiv=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    return _obj_from_bm(nombre, bm, material, parent, loc)

def cilindro_entre(nombre, a, b, r=0.02, material=None, parent=None, segs=12):
    """Cilindro de a a b (en coordenadas del padre)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=L)
    ob = _obj_from_bm(nombre, bm, material, parent, (a + b) / 2)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return ob

def cono(nombre, base, punta, r=0.08, material=None, parent=None, segs=16):
    """Punta de flecha: cono con base en `base` y vértice en `punta`."""
    base, punta = Vector(base), Vector(punta)
    d = punta - base
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.0, depth=d.length)
    ob = _obj_from_bm(nombre, bm, material, parent, (base + punta) / 2)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob

def polilinea_punteada(nombre, puntos, guion=0.16, hueco=0.11, r=0.022, material=None, parent=None, flecha=None):
    """Línea punteada 3D a lo largo de `puntos` (lista de (x,y,z)). Devuelve un objeto único.
    flecha: None o dict(r=0.08, largo=0.22) → agrega punta llena al final según la tangente."""
    pts = [Vector(p) for p in puntos]
    # longitud acumulada
    segs = []
    total = 0.0
    for i in range(len(pts) - 1):
        L = (pts[i + 1] - pts[i]).length
        segs.append((pts[i], pts[i + 1], total, L))
        total += L
    def punto_en(s):
        for a, b, s0, L in segs:
            if s <= s0 + L or (a, b, s0, L) == segs[-1]:
                t = 0 if L == 0 else (s - s0) / L
                return a.lerp(b, max(0, min(1, t)))
        return pts[-1]
    fin = total - (flecha['largo'] if flecha else 0.0)
    bm = bmesh.new()
    s = 0.0
    while s < fin - 1e-4:
        e = min(s + guion, fin)
        a, b = punto_en(s), punto_en(e)
        d = b - a
        if d.length > 1e-4:
            geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=r, depth=d.length)
            q = Vector((0, 0, 1)).rotation_difference(d.normalized())
            M = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
            bmesh.ops.transform(bm, matrix=M, verts=geom['verts'])
        s = e + hueco
    ob = _obj_from_bm(nombre, bm, material, parent)
    if flecha:
        base = punto_en(fin)
        cono(nombre + '_punta', base, pts[-1], r=flecha.get('r', 0.08), material=material, parent=parent)
    return ob

def arco(cx, cy, rx, ry, a0, a1, n=96, z=0.0, plano='XZ'):
    """Puntos de un arco elíptico entre ángulos a0→a1 (grados). plano 'XZ' (vertical, de frente a -Y) o 'XY' (horizontal)."""
    out = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        u, v = cx + rx * math.cos(t), cy + ry * math.sin(t)
        out.append((u, z, v) if plano == 'XZ' else (u, v, z))
    return out

def texto(nombre, cuerpo, size=0.3, loc=(0, 0, 0), extrude=0.02, material=None, parent=None,
          fuente=None, align='CENTER', rot=(math.radians(90), 0, 0)):
    """Texto 3D convertido a malla (para letras que deben ser geometría). Por defecto de pie mirando a -Y."""
    cu = bpy.data.curves.new(nombre, 'FONT')
    cu.body = cuerpo
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = 'CENTER'
    if fuente and os.path.exists(fuente):
        cu.font = bpy.data.fonts.load(fuente, check_existing=True)
    ob = bpy.data.objects.new(nombre, cu)
    ob.location = loc
    ob.rotation_euler = rot
    _link(ob, None)
    if material:
        cu.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.view_layer.objects.active
    ob.name = nombre
    if parent is not None:
        mw = ob.matrix_world.copy()
        ob.parent = parent
        ob.matrix_world = mw
    return ob

FUENTES = {
    'serif': '/System/Library/Fonts/Supplemental/Georgia.ttf',
    'serif_it': '/System/Library/Fonts/Supplemental/Georgia Italic.ttf',
    'sans': '/System/Library/Fonts/Supplemental/Arial.ttf',
    'sans_bold': '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
}

def aplicar(ob):
    """Aplica todos los modificadores (obligatorio antes de exportar)."""
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    return ob

# ---------------------------------------------------------------- escena, animación, estados
class Escena:
    def __init__(self, id, titulo, fondo='#14100D', dur=None):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.id, self.titulo, self.fondo = id, titulo, fondo
        self.estados, self.etiquetas = [], {}
        sc = bpy.context.scene
        sc.render.fps = FPS
        sc.frame_start = 0
        sc.frame_end = int((dur or 10) * FPS)
        prefs = bpy.context.preferences.edit
        prefs.keyframe_new_interpolation_type = 'BEZIER'
        try:
            prefs.keyframe_new_handle_type = 'AUTO_CLAMPED'
        except Exception:
            pass
        w = bpy.data.worlds.new('mundo')
        sc.world = w
        try:
            w.use_nodes = True
        except Exception:
            pass
        bg = w.node_tree.nodes.get('Background')
        if bg:
            bg.inputs['Color'].default_value = lin(fondo)
            bg.inputs['Strength'].default_value = 1.0
        self._luces_poster()

    # --- animación (todo con claves de transformación; visibilidad = escala)
    def f(self, t):
        return int(round(t * FPS))

    def clave(self, ob, t, loc=None, rot=None, esc=None, interp=None):
        prefs = bpy.context.preferences.edit
        old = prefs.keyframe_new_interpolation_type
        if interp:
            prefs.keyframe_new_interpolation_type = interp
        fr = self.f(t)
        if loc is not None:
            ob.location = loc
            ob.keyframe_insert('location', frame=fr)
        if rot is not None:
            ob.rotation_mode = 'XYZ'
            ob.rotation_euler = rot
            ob.keyframe_insert('rotation_euler', frame=fr)
        if esc is not None:
            ob.scale = esc if isinstance(esc, (tuple, list)) else (esc, esc, esc)
            ob.keyframe_insert('scale', frame=fr)
        prefs.keyframe_new_interpolation_type = old

    def mostrar(self, ob, t0, t1=None, desde=0.0001):
        """Aparece por escala entre t0 y t1 (si t1 es None, aparece de golpe en t0). Antes de t0 está oculto."""
        base = tuple(ob.scale)
        if t0 > 0:
            self.clave(ob, 0, esc=tuple(desde for _ in base), interp='CONSTANT')
        if t1 is None:
            self.clave(ob, t0, esc=base, interp='CONSTANT')
        else:
            self.clave(ob, t0, esc=tuple(desde for _ in base))
            self.clave(ob, t1, esc=base)

    def ocultar(self, ob, t0, t1=None, hasta=0.0001):
        base = tuple(ob.scale)
        if t1 is None:
            self.clave(ob, t0 - 1.0 / FPS, esc=base, interp='CONSTANT')
            self.clave(ob, t0, esc=tuple(hasta for _ in base), interp='CONSTANT')
        else:
            self.clave(ob, t0, esc=base)
            self.clave(ob, t1, esc=tuple(hasta for _ in base))

    def salto(self, ob, t, antes, despues):
        """Cambio instantáneo de escala en t (sin interpolación que se filtre desde claves anteriores).
        antes/despues: escalar o tupla. Úsalo para aparecer/desaparecer de golpe a mitad de la línea de tiempo."""
        self.clave(ob, t - 1.0 / FPS, esc=antes, interp='CONSTANT')
        self.clave(ob, t, esc=despues, interp='CONSTANT')

    def mover(self, ob, t0, t1, a, b):
        self.clave(ob, t0, loc=a)
        self.clave(ob, t1, loc=b)

    # --- etiquetas HTML (ancladas a empties lbl_<clave>)
    def etiqueta(self, clave, html, loc, parent=None, clase=''):
        """Crea el empty lbl_<clave> y registra el HTML (usa <s>…</s> para tachado, <sup> para superíndices).
        clases disponibles en el visor: '' (normal), 'sdo' (oro), 'snte' (nácar), 'tachado' (bermellón),
        'trayecto' (cian), 'ajeno' (magenta), 'nota' (pequeña), 'grande'."""
        vacio('lbl_' + clave, loc, parent, 0.05)
        self.etiquetas['lbl_' + clave] = {'html': html, 'clase': clase}

    # --- estados narrativos
    def estado(self, nombre, texto, ref, cam, look, fov=35, t1=0.0, etiquetas=(), orbita=True,
               slider=None, pregunta=None):
        """Registra un estado. Al entrar, el visor anima la línea de tiempo hasta t1 (segundos)
        y lleva la cámara a cam/look con fov vertical (grados).
        slider: None | {'tipo':'tiempo','t0':a,'t1':b,'etiqueta':'…','min':'…','max':'…'}
                     | {'tipo':'azimut','min':-45,'max':45,'etiqueta':'…'}"""
        n = len(self.estados)
        vacio(f'cam_{n}', cam, None, 0.05)
        vacio(f'look_{n}', look, None, 0.05)
        e = {'nombre': nombre, 'texto': texto, 'ref': ref, 'cam': f'cam_{n}', 'look': f'look_{n}',
             'fov': fov, 't1': t1, 'etiquetas': ['lbl_' + k if not k.startswith('lbl_') else k for k in etiquetas],
             'orbita': orbita, 'slider': slider, 'pregunta': pregunta,
             '_cam': tuple(cam), '_look': tuple(look)}
        self.estados.append(e)
        return n

    # --- luces sólo para pósters (el visor usa sus propias luces)
    def _luces_poster(self):
        def luz(nombre, tipo, loc, energia, color=(1, 1, 1), size=3.0):
            d = bpy.data.lights.new(nombre, tipo)
            d.energy = energia
            d.color = color
            if tipo == 'AREA':
                d.size = size
            ob = bpy.data.objects.new(nombre, d)
            ob.location = loc
            ob.rotation_mode = 'QUATERNION'
            ob.rotation_quaternion = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y')
            bpy.context.scene.collection.objects.link(ob)
            ob['poster_only'] = True
            return ob
        luz('clave', 'AREA', (-5, -6, 6), 1400, (1.0, 0.93, 0.82), 4)
        luz('relleno', 'AREA', (6, -5, 2), 350, (0.75, 0.88, 1.0), 5)
        luz('contra', 'AREA', (0, 6, 5), 700, (1.0, 0.95, 0.9), 4)

    # --- exportación
    def exportar(self, posters=True, res=(1600, 900)):
        os.makedirs(os.path.join(OUT3D, 'escenas'), exist_ok=True)
        os.makedirs(os.path.join(OUT3D, 'posters'), exist_ok=True)
        sc = bpy.context.scene
        ult = max([e['t1'] for e in self.estados] + [0.1])
        sc.frame_end = max(sc.frame_end, self.f(ult) + 1)
        # 1) GLB (sin luces ni cámaras)
        for ob in bpy.data.objects:
            ob.select_set(False)
        glb = os.path.join(OUT3D, 'escenas', self.id + '.glb')
        luces = [o for o in bpy.data.objects if o.type == 'LIGHT']
        for o in luces:
            o.hide_render = True
        kw = dict(filepath=glb, export_format='GLB', export_apply=True, export_extras=True,
                  export_yup=True, export_animations=True, export_cameras=False, export_lights=False,
                  export_materials='EXPORT')
        try:
            bpy.ops.export_scene.gltf(export_animation_mode='SCENE', **kw)
        except TypeError:
            bpy.ops.export_scene.gltf(**kw)
        for o in luces:
            o.hide_render = False
        # 2) manifiesto
        man = {
            'id': self.id, 'titulo': self.titulo, 'fondo': self.fondo, 'fps': FPS,
            'duracion': sc.frame_end / FPS,
            'estados': [{k: v for k, v in e.items() if not k.startswith('_')} for e in self.estados],
            'etiquetas': self.etiquetas,
        }
        with open(os.path.join(OUT3D, 'escenas', self.id + '.json'), 'w', encoding='utf-8') as fh:
            json.dump(man, fh, ensure_ascii=False, indent=1)
        # 3) pósters por estado
        if posters:
            self._posters(res)
        print(f'[bb] exportado {self.id}: {len(self.estados)} estados → {glb}')

    def _posters(self, res):
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_EEVEE'
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.resolution_percentage = 100
        try:
            sc.view_settings.view_transform = 'Khronos PBR Neutral'
        except Exception:
            pass
        try:
            sc.eevee.taa_render_samples = 48
        except Exception:
            pass
        sc.render.image_settings.file_format = 'WEBP'
        sc.render.image_settings.quality = 82
        cd = bpy.data.cameras.new('cam_poster')
        cd.sensor_fit = 'VERTICAL'
        cam = bpy.data.objects.new('cam_poster', cd)
        sc.collection.objects.link(cam)
        sc.camera = cam
        for n, e in enumerate(self.estados):
            sc.frame_set(self.f(e['t1']))
            cam.location = e['_cam']
            d = Vector(e['_look']) - Vector(e['_cam'])
            cam.rotation_mode = 'QUATERNION'
            cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
            cd.angle_y = math.radians(e['fov'])
            sc.render.filepath = os.path.join(OUT3D, 'posters', f'{self.id}-{n}.webp')
            bpy.ops.render.render(write_still=True)
            if n == 0:
                sc.render.filepath = os.path.join(OUT3D, 'posters', f'{self.id}.webp')
                bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)
