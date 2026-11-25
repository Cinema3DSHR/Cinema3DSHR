"""EXPERIMENTO «LÍNEAS TÉCNICAS» (Blender): toma el GLB de Godot (escena_lineas.gd) y renderiza UN cuadro con uno de los cuatro tratamientos, a 720×1280 (vertical).
Para cada estilo genera tres imágenes con el MISMO cuadro y la MISMA cámara: «beauty» (Cycles, 6 muestras, OIDN: el sombreado), «lineas» (Freestyle, contornos limpios y suaves) y «clases»
(máscara plana por tipo de objeto: personajes, arma, arquitectura, vegetación, rojo…). Después `componer.py` las junta con numpy (sombreado por niveles, rojo selectivo, líneas).
Uso: /opt/tools/blendenv/bin/python render_estilo.py ESTILO(A|B|C|D) CUADRO SALIDA_PREFIJO [GLB]"""
import bpy, sys, os, math, time, json
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
ESTILO, CUADRO, PRE = A[0], int(A[1]), A[2]
GLB = A[3] if len(A) > 3 else '/home/user/cap1_noir/estilo/escena.glb'
CAMARA = A[4] if len(A) > 4 else 'Cam_principal'
W, H = 720, 1280
LINEAS = os.environ.get('LINEAS', 'freestyle')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; vl = bpy.context.view_layer
bpy.ops.import_scene.gltf(filepath=GLB)
for o in bpy.data.objects:
    for idb in (o, o.data if o.data else None):
        ad = getattr(idb, 'animation_data', None) if idb else None
        if ad:
            for tr in ad.nla_tracks: tr.mute = False
sc.frame_set(CUADRO)
cam = bpy.data.objects[CAMARA]; sc.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.clip_start = 0.05; cam.data.clip_end = 200
for c in list(bpy.data.objects):
    if c.type == 'CAMERA' and c != cam: bpy.data.objects.remove(c)
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100; r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.film_transparent = False

def ancestros(o):
    while o:
        yield o.name; o = o.parent
def clase(o):
    ns = list(ancestros(o))
    if any(n == 'Rojo_laser' for n in ns): return 'laser'
    if any(n.startswith('Rojo_') for n in ns): return 'rojo'
    if any(n == 'Arma_USP' for n in ns): return 'arma'
    if any(n in ('aiden', 'kate') for n in ns): return 'pj'
    if any(n == 'AutoRaiz' for n in ns): return 'auto'
    if any(n.startswith('Veg_') for n in ns): return 'veg'
    if any(n.startswith('Obj_') for n in ns): return 'obj'
    if any(n.startswith('Arq_') for n in ns): return 'arq'
    return 'auto'
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes: o['clase'] = clase(o)
# sangre (rojo selectivo): charcos planos junto a Aiden
def charco(nombre, x, y, rad, sx=1.0, sy=0.7):
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=rad, fill_type='NGON', location=(x, y, 0.012)); o = bpy.context.active_object; o.name = nombre; o.scale = (sx, sy, 1); o.rotation_euler[2] = 0.5
    o['clase'] = 'rojo'; return o
charco('Rojo_sangre_1', -0.95, -1.15, 0.34); charco('Rojo_sangre_2', -0.55, -0.85, 0.12, 1.0, 0.8); charco('Rojo_sangre_3', -1.35, -1.45, 0.08)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']

# ───── materiales según el estilo ─────
def mat_plano(nombre, col, rough=1.0, emis=0.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = rough
    for k, v in (('Specular IOR Level', 0.0), ('Metallic', 0.0)):
        try: bs.inputs[k].default_value = v
        except Exception: pass
    return m
ROJO = (0.80, 0.02, 0.02)
TONO = {'arq': (0.93, 0.93, 0.92), 'veg': (0.80, 0.80, 0.80), 'obj': (0.88, 0.88, 0.87), 'auto': (0.90, 0.90, 0.90), 'pj': (0.90, 0.90, 0.90), 'arma': (0.70, 0.70, 0.72), 'otro': (0.9, 0.9, 0.9)}
if ESTILO == 'D':
    TONO.update({'arq': (0.96, 0.96, 0.95), 'veg': (0.72, 0.72, 0.72), 'obj': (0.84, 0.84, 0.83), 'auto': (0.88, 0.88, 0.88), 'pj': (0.92, 0.92, 0.92), 'arma': (0.55, 0.55, 0.57)})
M_ROJO = mat_plano('Rojo', ROJO, 0.4)
def tono_parte(o, base):
    n = (o.name + ' ' + ' '.join(m.name for m in o.data.materials if m)).lower()
    if any(k in n for k in ('hair', 'scalp', 'brow', 'lash', 'pelo')): return (0.16, 0.16, 0.17)
    if any(k in n for k in ('zapato', 'pie_', 'shoe')): return (0.28, 0.28, 0.30)
    if 'pantalon' in n: return (0.55, 0.55, 0.57)
    if 'cinturon' in n or 'boton' in n: return (0.35, 0.35, 0.37)
    if any(k in n for k in ('eye', 'teeth', 'tongue')): return (0.92, 0.92, 0.92)
    return base
M_CLASE = {k: mat_plano('Tono_' + k, v) for k, v in TONO.items()}
for o in meshes:
    c = o['clase']
    if c in ('rojo', 'laser'): o.data.materials.clear(); o.data.materials.append(M_ROJO); continue
    blanquear = (ESTILO in ('B', 'D')) or (ESTILO == 'C' and c != 'pj')
    if blanquear:
        t = tono_parte(o, TONO[c]) if c == 'pj' else TONO[c]
        mm = M_CLASE[c] if t == TONO[c] else mat_plano('Tono_pj_' + str(len(bpy.data.materials)), t)
        o.data.materials.clear(); o.data.materials.append(mm)
# suelo claro en D (casi blanco); camino un poco más claro
if ESTILO == 'D':
    for o in meshes:
        if o.name == 'Arq_suelo': o.data.materials.clear(); o.data.materials.append(mat_plano('Suelo', (0.97, 0.97, 0.96)))
        if o.name == 'Arq_camino': o.data.materials.clear(); o.data.materials.append(mat_plano('Camino', (1.0, 1.0, 1.0)))

# ───── luz y mundo ─────
w = bpy.data.worlds.new('Mundo'); w.use_nodes = True; bg = w.node_tree.nodes['Background']
bg.inputs[0].default_value = {'A': (0.80, 0.82, 0.86, 1), 'B': (0.95, 0.95, 0.95, 1), 'C': (0.93, 0.93, 0.94, 1), 'D': (0.60, 0.60, 0.62, 1)}[ESTILO]; bg.inputs[1].default_value = {'A': 0.75, 'B': 0.42, 'C': 0.42, 'D': 0.45}[ESTILO]; sc.world = w
sol = bpy.data.lights.new('Sol', 'SUN'); sol.energy = {'A': 2.2, 'B': 1.1, 'C': 1.1, 'D': 1.0}[ESTILO]; sol.angle = math.radians(3 if ESTILO != 'D' else 25)
so = bpy.data.objects.new('Sol', sol); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(8), math.radians(35))
if ESTILO == 'D': sol.use_shadow = False
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'

# ───── 1) BEAUTY (Cycles, perfil del estudio: 6 muestras, adaptativo 0,05, OIDN, 6 rebotes, semilla fija) ─────
def cycles():
    r.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'; cy.samples = 6; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
    cy.max_bounces = 6 if ESTILO == 'A' else 3; cy.seed = 13; cy.use_animated_seed = False
    if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
r.use_freestyle = False; vl.use_freestyle = False; cycles()
t0 = time.time(); r.filepath = PRE + '_beauty.png'; bpy.ops.render.render(write_still=True); t_beauty = time.time() - t0

# ───── auxiliares planos (Cycles con materiales de emisión: sin ruido, sin depender de GPU) ─────
def mat_emision(nombre, col):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = 1.0; nt.links.new(em.outputs[0], out.inputs[0]); return m
def plano_cycles(muestras, filtro, fondo):
    r.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'; cy.samples = muestras; cy.use_adaptive_sampling = False; cy.use_denoising = False; cy.max_bounces = 0; cy.seed = 13; cy.pixel_filter_type = 'BLACKMAN_HARRIS'; cy.filter_width = filtro
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    for o in bpy.data.objects:
        if o.type == 'LIGHT': o.hide_render = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*fondo, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
if LINEAS == 'pasadas':
    # 2) LÍNEAS POR PASADAS: normales y profundidad en materiales de emisión (1 muestra), los bordes se detectan en espacio de imagen (componer.py)
    def mat_geo(nombre, tipo):
        m = bpy.data.materials.new(nombre); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], out.inputs[0])
        if tipo == 'normal':
            g = nt.nodes.new('ShaderNodeNewGeometry'); mv = nt.nodes.new('ShaderNodeVectorMath'); mv.operation = 'MULTIPLY_ADD'; mv.inputs[1].default_value = (0.5, 0.5, 0.5); mv.inputs[2].default_value = (0.5, 0.5, 0.5)
            nt.links.new(g.outputs['Normal'], mv.inputs[0]); nt.links.new(mv.outputs[0], em.inputs['Color'])
        else:
            cd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 3.0; mr.inputs['From Max'].default_value = 40.0; nt.links.new(cd.outputs['View Z Depth'], mr.inputs['Value'])
            nt.links.new(mr.outputs[0], em.inputs['Color'])
        return m
    plano_cycles(1, 1.0, (0, 0, 0)); t1 = time.time()
    r.image_settings.color_depth = '16'
    for o in meshes: o.data.materials.clear(); o.data.materials.append(mat_geo('Normal', 'normal'))
    r.filepath = PRE + '_normales.png'; bpy.ops.render.render(write_still=True)
    for o in meshes: o.data.materials.clear(); o.data.materials.append(mat_geo('Prof', 'prof'))
    r.filepath = PRE + '_prof.png'; bpy.ops.render.render(write_still=True)
    r.image_settings.color_depth = '8'
    t_lineas = time.time() - t1
else:
    # 2) LÍNEAS (Freestyle): se aíslan restando el mismo cuadro sin y con líneas sobre blanco emisivo
    for o in meshes: o.data.materials.clear(); o.data.materials.append(mat_emision('Blanco', (1, 1, 1)))
    plano_cycles(2, 1.5, (1, 1, 1))
    t1 = time.time()
    r.use_freestyle = True; vl.use_freestyle = True; fs = vl.freestyle_settings
    for ls in list(fs.linesets): fs.linesets.remove(ls)
    fs.crease_angle = math.radians(35)
    GROSOR = {'A': 1.9, 'B': 1.6, 'C': 1.7, 'D': 1.4}[ESTILO]
    def lineset(nombre, grosor, clases=None, crease=True):
        # (crease=False: sólo contornos y bordes)
        ls = fs.linesets.new(nombre); st = bpy.data.linestyles.new(nombre); ls.linestyle = st
        ls.select_silhouette = True; ls.select_border = True; ls.select_crease = crease; ls.select_contour = True; ls.select_external_contour = False; ls.select_material_boundary = False
        ls.visibility = 'VISIBLE'; st.color = (0, 0, 0); st.thickness = grosor; st.use_chaining = True; st.chaining = 'PLAIN'
        st.caps = 'ROUND'
        m = st.thickness_modifiers.new('Dist', 'DISTANCE_FROM_CAMERA'); m.range_min = 4.0; m.range_max = 22.0; m.value_min = grosor * 1.15; m.value_max = grosor * 0.55     # más finas con la distancia: profundidad
        if clases is not None:
            col = bpy.data.collections.new('L_' + nombre); sc.collection.children.link(col)
            for o in meshes:
                if o['clase'] in clases:
                    for c in list(o.users_collection): c.objects.unlink(o)
                    col.objects.link(o)
            ls.select_by_collection = True; ls.collection = col; ls.select_by_visibility = True; ls.select_by_image_border = False
        return ls
    if ESTILO == 'C':
        lineset('pj', GROSOR * 1.25, ('pj',), crease=False); lineset('arma', GROSOR * 0.7, ('arma',)); lineset('resto', GROSOR * 0.95, ('arq', 'veg', 'obj', 'auto', 'rojo', 'otro'))
    else:
        lineset('pj', GROSOR * 1.1, ('pj',), crease=False); lineset('arma', GROSOR * 0.75, ('arma',)); lineset('resto', GROSOR, ('arq', 'veg', 'obj', 'auto', 'rojo', 'otro'))
    r.filepath = PRE + '_lineas_c.png'; bpy.ops.render.render(write_still=True); t_lineas = time.time() - t1
    r.use_freestyle = False; vl.use_freestyle = False


# 3) CLASES (máscara plana, sin suavizado de bordes)
COL = {'pj': (1, 0, 0), 'arma': (0, 1, 0), 'arq': (0, 0, 1), 'veg': (1, 1, 0), 'obj': (1, 0, 1), 'auto': (0, 1, 1), 'rojo': (1, 1, 1), 'laser': (1, 1, 1), 'otro': (0.5, 0.5, 0.5)}
MC = {k: mat_emision('Clase_' + k, v) for k, v in COL.items()}
for o in meshes: o.data.materials.clear(); o.data.materials.append(MC[o['clase']])
plano_cycles(1, 0.01, (0, 0, 0))
t2 = time.time(); r.filepath = PRE + '_clases.png'; bpy.ops.render.render(write_still=True); t_clases = time.time() - t2
json.dump({'estilo': ESTILO, 'cuadro': CUADRO, 'segundos_beauty_cycles': round(t_beauty, 1), 'segundos_lineas': round(t_lineas, 1), 'segundos_clases': round(t_clases, 1), 'resolucion': [W, H]}, open(PRE + '_info.json', 'w'))
print('LISTO', ESTILO, 'beauty', round(t_beauty, 1), 'lineas', round(t_lineas, 1), 'clases', round(t_clases, 1), 's')
