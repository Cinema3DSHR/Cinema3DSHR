"""PASADAS RÁPIDAS para los efectos de la guía de Extracción Vertical sobre la escena de Godot (casa_lineas.gd → GLB):
color (materiales originales, para el filtro de pantalla), arcilla (blanco con luz y sombra, para el toon), normales del mundo, profundidad, clases por tipo de objeto y datos de cámara/sol.
Todo a 720×1280. Cycles CPU, 8 muestras en las dos con luz y 1 muestra en las planas. Uso: render_pdf.py GLB PREFIJO"""
import bpy, sys, os, math, json, time
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
GLB, PRE = A[0], A[1]
W, H = 720, 1280
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; r = sc.render
bpy.ops.import_scene.gltf(filepath=GLB)
cam = bpy.data.objects['Cam_principal']; sc.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.clip_start = 0.05; cam.data.clip_end = 400
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100; r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.film_transparent = False
def ancestros(o):
    while o:
        yield o.name; o = o.parent
def clase(o):
    ns = list(ancestros(o)); n = o.name
    if 'Auto' in ns: return 'auto'
    if n.startswith('Vidrio_'): return 'vidrio'
    if n == 'Arq_suelo' or n.startswith('Arq_camino'): return 'suelo'
    if n.startswith('Arq_colina'): return 'colina'
    if n.startswith('Veg_'): return 'veg'
    if n.startswith('Obj_'): return 'obj'
    if n.startswith('Arq_garaje'): return 'garaje'
    return 'arq'
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes: o['clase'] = clase(o)
orig = {o.name: [m for m in o.data.materials] for o in meshes}
def cycles(muestras, filtro=1.5, denoise=False, rebotes=4):
    r.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'; cy.samples = muestras; cy.use_adaptive_sampling = muestras > 2; cy.adaptive_threshold = 0.05; cy.use_denoising = denoise; cy.denoiser = 'OPENIMAGEDENOISE'
    cy.max_bounces = rebotes; cy.transparent_max_bounces = 16; cy.seed = 7; cy.use_animated_seed = False; cy.pixel_filter_type = 'BLACKMAN_HARRIS'; cy.filter_width = filtro
    if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
def mundo(col, fuerza):
    w = bpy.data.worlds.new('M'); w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (*col, 1); bg.inputs[1].default_value = fuerza; sc.world = w
def mat_emision(col):
    m = bpy.data.materials.new('E'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); nt.links.new(em.outputs[0], out.inputs[0]); return m
def mat_transparente():
    m = bpy.data.materials.new('T'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); nt.links.new(tr.outputs[0], out.inputs[0]); return m
def mat_arcilla(col=(0.9, 0.9, 0.9)):
    m = bpy.data.materials.new('Arcilla'); m.use_nodes = True; bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = 1.0
    try: bs.inputs['Specular IOR Level'].default_value = 0.0
    except Exception: pass
    return m
# luz: sol de frente-izquierda (los rayos viajan hacia +Y y -Z)
dsol = Vector((0.5, 0.72, -0.55)).normalized()
sol = bpy.data.lights.new('Sol', 'SUN'); sol.energy = 3.2; sol.angle = math.radians(2.5); so = bpy.data.objects.new('Sol', sol); sc.collection.objects.link(so); so.rotation_euler = dsol.to_track_quat('-Z', 'Y').to_euler()
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
tiempos = {}
def poner(f):
    for o in meshes: f(o)
def render(nombre):
    t = time.time(); r.filepath = f'{PRE}_{nombre}.png'; bpy.ops.render.render(write_still=True); tiempos[nombre] = round(time.time() - t, 1)
# 1) COLOR (materiales originales de Godot): cielo claro, sol
mundo((0.62, 0.72, 0.9), 0.9); cycles(8, 1.5, True, 4); render('color')
# 2) ARCILLA (blanca con luz y sombra, el vidrio deja pasar la luz)
MA = mat_arcilla(); MT = mat_transparente()
def f_arcilla(o): o.data.materials.clear(); o.data.materials.append(MT if o['clase'] == 'vidrio' else MA)
poner(f_arcilla); mundo((0.75, 0.78, 0.85), 0.55); cycles(8, 1.5, True, 3); render('arcilla')
# 3) NORMALES del mundo y 4) PROFUNDIDAD (1 muestra, emisión)
def mat_geo(tipo):
    m = bpy.data.materials.new('G' + tipo); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], out.inputs[0])
    if tipo == 'n':
        g = nt.nodes.new('ShaderNodeNewGeometry'); mv = nt.nodes.new('ShaderNodeVectorMath'); mv.operation = 'MULTIPLY_ADD'; mv.inputs[1].default_value = (0.5, 0.5, 0.5); mv.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(g.outputs['Normal'], mv.inputs[0]); nt.links.new(mv.outputs[0], em.inputs['Color'])
    else:
        cd = nt.nodes.new('ShaderNodeCameraData'); dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = 128.0
        nt.links.new(cd.outputs['View Z Depth'], dv.inputs[0]); nt.links.new(dv.outputs[0], em.inputs['Color'])
    return m
mundo((0, 0, 0), 1.0); cycles(1, 1.0, False, 0)
MN = mat_geo('n'); MD = mat_geo('d')
r.image_settings.color_depth = '8'
poner(lambda o: (o.data.materials.clear(), o.data.materials.append(MT if o['clase'] == 'vidrio' else MN))); render('normales')
r.image_settings.color_depth = '16'; r.image_settings.color_mode = 'BW'
poner(lambda o: (o.data.materials.clear(), o.data.materials.append(MT if o['clase'] == 'vidrio' else MD))); render('prof')
r.image_settings.color_depth = '8'; r.image_settings.color_mode = 'RGB'
# 5) CLASES (color plano por tipo)
COL = {'arq': (1, 0, 0), 'suelo': (0, 1, 0), 'colina': (0, 0.5, 0), 'veg': (1, 1, 0), 'obj': (1, 0, 1), 'garaje': (0, 0, 1), 'auto': (0, 1, 1), 'vidrio': (0, 0, 0)}
MC = {k: mat_emision(v) for k, v in COL.items()}
cycles(1, 0.01, False, 0)
poner(lambda o: (o.data.materials.clear(), o.data.materials.append(MT if o['clase'] == 'vidrio' else MC[o['clase']]))); render('clases')
M = cam.matrix_world; fwd = -(M.to_3x3() @ Vector((0, 0, 1))); derecha = M.to_3x3() @ Vector((1, 0, 0)); arriba = M.to_3x3() @ Vector((0, 1, 0))
json.dump({'camara': list(M.translation), 'adelante': list(fwd), 'derecha': list(derecha), 'arriba': list(arriba), 'fov_v': cam.data.angle_y, 'sol_dir': list(dsol), 'resolucion': [W, H], 'tiempos_s': tiempos}, open(PRE + '_datos.json', 'w'))
print('LISTO', tiempos)
