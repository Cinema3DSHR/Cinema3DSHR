"""BLEND del diálogo para el estilo E: importa el GLB de Godot (dialogo_lineas.gd), clasifica los objetos (personajes / fondo / piso), pone el sol de frente-izquierda, un relleno suave y el mundo gris.
Uso: /opt/tools/blendenv/bin/python construir_dialogo.py GLB SALIDA.blend"""
import bpy, math, sys
from mathutils import Vector
GLB, SAL = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=GLB)
for o in bpy.data.objects:
    for idb in (o, o.data if o.data else None):
        ad = getattr(idb, 'animation_data', None) if idb else None
        if ad:
            for tr in ad.nla_tracks: tr.mute = False
def anc(o):
    while o: yield o.name; o = o.parent
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    ns = list(anc(o))
    o['clase'] = 'auto' if any(n in ('aiden', 'kate') for n in ns) else ('suelo' if o.name == 'Arq_piso' else 'fondo')       # 'auto' = clase de los sujetos (rojo en la máscara)
cam = bpy.data.objects['Cam_principal']; sc.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.clip_start = 0.05; cam.data.clip_end = 100
sol = bpy.data.lights.new('Sol', 'SUN'); sol.energy = 3.4; sol.angle = math.radians(4); so = bpy.data.objects.new('Sol', sol); sc.collection.objects.link(so)
so.rotation_euler = Vector((0.5, 0.7, -0.5)).normalized().to_track_quat('-Z', 'Y').to_euler()
al = bpy.data.lights.new('Relleno', 'AREA'); al.energy = 90; al.size = 2.5; al.color = (0.9, 0.93, 1.0); lo = bpy.data.objects.new('Relleno', al); sc.collection.objects.link(lo); lo.location = (1.6, -2.2, 1.6)
lo.rotation_euler = (Vector((0, 0, 1.2)) - Vector(lo.location)).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new('Mundo'); w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.62, 0.64, 0.68, 1); bg.inputs[1].default_value = 0.55; sc.world = w
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 720, 1280, 100, 30
cy = sc.cycles; cy.device = 'CPU'; cy.samples = 12; cy.use_adaptive_sampling = True; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.max_bounces = 4; cy.seed = 5
if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
sc.view_settings.view_transform = 'Standard'; sc.frame_start, sc.frame_end = 1, 301
bpy.ops.wm.save_as_mainfile(filepath=SAL, compress=True)
print('GUARDADO', SAL)
