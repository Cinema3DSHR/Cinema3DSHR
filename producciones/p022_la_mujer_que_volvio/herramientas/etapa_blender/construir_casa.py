"""Etapa Blender de LA CASA (cap. 1): importa casa.glb (Godot) y agrega lo visual (materiales reales, tormenta, cortinas, humo, goteos, relámpagos). Perfil: 540×960, Cycles CPU, 6 muestras, OIDN.
Uso: /opt/tools/blendenv/bin/python construir_casa.py SALIDA.blend [GLB] [JSON]"""
import bpy, sys, json, math, os, random
from mathutils import Vector, Matrix
SALIDA = sys.argv[1]
GLB = sys.argv[2] if len(sys.argv) > 2 else '/home/user/cap1_noir/salida/casa.glb'
JS = json.load(open(sys.argv[3] if len(sys.argv) > 3 else GLB.replace('.glb', '.json')))
FPS = int(JS['fps']); TOTAL = int(JS['frames']); EV = JS['eventos']
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; bpy.context.preferences.edit.use_global_undo = False
bpy.ops.import_scene.gltf(filepath=GLB)
sc.frame_start, sc.frame_end = 1, TOTAL
def gb(v): return Vector((v[0], -v[2], v[1]))
for o in bpy.data.objects:
    for idb in (o, o.data if o.data else None):
        ad = getattr(idb, 'animation_data', None) if idb else None
        if ad:
            for tr in ad.nla_tracks: tr.mute = False
r = sc.render; r.engine = 'CYCLES'; r.resolution_x = 540; r.resolution_y = 960; r.resolution_percentage = 100; r.fps = FPS; r.fps_base = 1.0; r.use_motion_blur = False; r.film_transparent = False
cy = sc.cycles; cy.device = 'CPU'; cy.samples = 6; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 4; cy.glossy_bounces = 6; cy.transmission_bounces = 8; cy.volume_bounces = 0; cy.transparent_max_bounces = 10
if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
cy.seed = 13; cy.use_animated_seed = False
sc.view_settings.view_transform = 'Khronos PBR Neutral'; sc.view_settings.exposure = 1.3
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'
camaras = []
for tm in JS['tomas']:
    cam = bpy.data.objects[tm['camara']]
    cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24.0; cam.data.lens = float(tm['lente_mm']); cam.data.clip_start = 0.04; cam.data.clip_end = 200
    camaras.append((int(tm['frame_inicio']), cam))
for f, cam in sorted(camaras, key=lambda x: x[0]):
    mk = sc.timeline_markers.new(cam.name, frame=f); mk.camera = cam
sc.camera = sorted(camaras, key=lambda x: x[0])[0][1]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'efectos_casa.py')).read())
for _im in bpy.data.images:
    if _im.source == 'FILE' and not _im.packed_file: _im.pack()
bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
print('GUARDADO', SALIDA, os.path.getsize(SALIDA))
