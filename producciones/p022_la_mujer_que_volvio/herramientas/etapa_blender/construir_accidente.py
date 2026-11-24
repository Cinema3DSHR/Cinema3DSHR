"""Etapa Blender del ACCIDENTE (cap. 1, «La mujer que volvió de la muerte»): importa el GLB de Godot (accidente.glb + .json) y agrega lo visual:
asfalto mojado con charcos, negro brillante del auto, vidrios, luces y niebla, LLUVIA REAL (nodos de geometría, determinista por cuadro: se puede
renderizar cualquier cuadro por separado), salpicaduras de la lluvia en el suelo, agua que levanta el auto al pisar charcos, relámpagos.
Perfil de render obligatorio: 540×960 (vertical), Cycles CPU, 6 muestras, adaptativo 0,05, OpenImageDenoise, 6 rebotes, Light Tree, semilla fija, 30 fps.
Uso: /opt/tools/blendenv/bin/python construir_accidente.py SALIDA.blend [GLB] [JSON]"""
import bpy, sys, json, math, os, random
from mathutils import Vector, Matrix

SALIDA = sys.argv[1]
GLB = sys.argv[2] if len(sys.argv) > 2 else '/home/user/cap1_noir/salida/accidente.glb'
JS = json.load(open(sys.argv[3] if len(sys.argv) > 3 else GLB.replace('.glb', '.json')))
FPS = int(JS['fps']); TOTAL = int(JS['frames']); EV = JS['eventos']

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.context.preferences.edit.use_global_undo = False
bpy.ops.import_scene.gltf(filepath=GLB)
sc.frame_start, sc.frame_end = 1, TOTAL
def gb(v): return Vector((v[0], -v[2], v[1]))           # Godot (x, y, z) → Blender (x, −z, y)

# ── animación: el importador deja las pistas NLA silenciadas
for o in bpy.data.objects:
    for idb in (o, o.data if o.data else None):
        ad = getattr(idb, 'animation_data', None) if idb else None
        if ad:
            for tr in ad.nla_tracks: tr.mute = False

# ── perfil de render obligatorio
r = sc.render
r.engine = 'CYCLES'; r.resolution_x = 540; r.resolution_y = 960; r.resolution_percentage = 100
r.fps = FPS; r.fps_base = 1.0; r.use_motion_blur = False; r.film_transparent = False
cy = sc.cycles
cy.device = 'CPU'; cy.samples = 6; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 4; cy.glossy_bounces = 6; cy.transmission_bounces = 6; cy.volume_bounces = 0; cy.transparent_max_bounces = 10
if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
cy.seed = 11; cy.use_animated_seed = False
sc.view_settings.view_transform = 'Khronos PBR Neutral'; sc.view_settings.exposure = 1.0
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'

# ── mundo: noche de tormenta + niebla/neblina baja (volumen) para ver los conos de los faros
w = bpy.data.worlds.new('Tormenta'); w.use_nodes = True; nt = w.node_tree
nt.nodes.clear()
sal = nt.nodes.new('ShaderNodeOutputWorld')
cielo = nt.nodes.new('ShaderNodeBackground'); cielo.inputs[0].default_value = (0.012, 0.018, 0.035, 1); cielo.inputs[1].default_value = 1.0
grad = nt.nodes.new('ShaderNodeTexGradient'); texco = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
nt.links.new(texco.outputs['Generated'], mp.inputs[0]); nt.links.new(mp.outputs[0], grad.inputs[0])
rampa = nt.nodes.new('ShaderNodeValToRGB'); rampa.color_ramp.elements[0].color = (0.004, 0.006, 0.012, 1); rampa.color_ramp.elements[1].color = (0.05, 0.065, 0.10, 1)
nt.links.new(grad.outputs[0], rampa.inputs[0]); nt.links.new(rampa.outputs[0], cielo.inputs[0])
vol = nt.nodes.new('ShaderNodeVolumeScatter'); vol.inputs['Density'].default_value = 0.0065; vol.inputs['Anisotropy'].default_value = 0.35
vol.inputs['Color'].default_value = (0.6, 0.68, 0.8, 1)
nt.links.new(cielo.outputs[0], sal.inputs['Surface']); nt.links.new(vol.outputs[0], sal.inputs['Volume'])
sc.world = w

# ── ayudas de materiales
def principled(m):
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.use_nodes else None
def reconstruir(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0]); return nt, bs, out
def entrada(bs, *nombres):
    for n in nombres:
        if n in bs.inputs: return bs.inputs[n]
    raise KeyError(nombres)

# ── ASFALTO MOJADO con charcos (procedural: la máscara de charcos manda sobre rugosidad, color y relieve)
def material_asfalto():
    m = bpy.data.materials.new('Asfalto_mojado'); nt, bs, out = reconstruir(m)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.045, 0.045, 0.045)
    ruido = nt.nodes.new('ShaderNodeTexNoise'); ruido.inputs['Scale'].default_value = 1.6; ruido.inputs['Detail'].default_value = 5.0; ruido.inputs['Roughness'].default_value = 0.55
    nt.links.new(tc.outputs['Object'], mp.inputs[0]); nt.links.new(mp.outputs[0], ruido.inputs['Vector'])
    mask = nt.nodes.new('ShaderNodeMapRange'); mask.inputs['From Min'].default_value = 0.50; mask.inputs['From Max'].default_value = 0.56; mask.inputs['To Min'].default_value = 0.0; mask.inputs['To Max'].default_value = 1.0
    nt.links.new(ruido.outputs['Fac'], mask.inputs['Value'])
    grano = nt.nodes.new('ShaderNodeTexNoise'); grano.inputs['Scale'].default_value = 140.0; grano.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], grano.inputs['Vector'])
    rug = nt.nodes.new('ShaderNodeMapRange'); rug.inputs['To Min'].default_value = 0.30; rug.inputs['To Max'].default_value = 0.012      # seco 0,30 → charco 0,012
    nt.links.new(mask.outputs[0], rug.inputs['Value'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt.links.new(mask.outputs[0], inv.inputs[1])
    nt.links.new(grano.outputs['Fac'], bump.inputs['Height'])
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['A'].default_value = (0.020, 0.020, 0.024, 1); col.inputs['B'].default_value = (0.004, 0.004, 0.006, 1)
    nt.links.new(mask.outputs[0], col.inputs['Factor'])
    nt.links.new(col.outputs['Result'], entrada(bs, 'Base Color')); nt.links.new(rug.outputs[0], entrada(bs, 'Roughness'))
    nt.links.new(bump.outputs[0], entrada(bs, 'Normal'))
    entrada(bs, 'Specular IOR Level', 'Specular').default_value = 0.8
    return m
def material_charco():       # charcos grandes explícitos: espejo oscuro con ondas por la lluvia (relieve animado por el cuadro)
    m = bpy.data.materials.new('Charco_agua'); nt, bs, out = reconstruir(m)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (6.0, 6.0, 6.0)
    ond = nt.nodes.new('ShaderNodeTexWave'); ond.wave_type = 'RINGS'; ond.inputs['Scale'].default_value = 3.0; ond.inputs['Distortion'].default_value = 6.0; ond.inputs['Detail'].default_value = 2.0
    br = nt.nodes.new('ShaderNodeBump'); br.inputs['Strength'].default_value = 0.05
    nt.links.new(tc.outputs['Object'], mp.inputs[0]); nt.links.new(mp.outputs[0], ond.inputs['Vector']); nt.links.new(ond.outputs[0], br.inputs['Height'])
    bs.inputs['Base Color'].default_value = (0.003, 0.004, 0.006, 1); entrada(bs, 'Roughness').default_value = 0.0
    nt.links.new(br.outputs[0], entrada(bs, 'Normal'))
    # el patrón de ondas se desplaza con el cuadro (lluvia golpeando)
    d = mp.inputs['Location'].driver_add('default_value', 0)
    d.driver.type = 'SCRIPTED'; d.driver.expression = 'frame * 0.011'
    return m
M_ASFALTO = material_asfalto(); M_CHARCO = material_charco()

# ── PINTURA negra brillante (barniz), vidrios, gomas
def material_pintura():
    m = bpy.data.materials.new('Pintura_negra'); nt, bs, out = reconstruir(m)
    bs.inputs['Base Color'].default_value = (0.004, 0.004, 0.005, 1); entrada(bs, 'Metallic').default_value = 0.35; entrada(bs, 'Roughness').default_value = 0.28
    entrada(bs, 'Coat Weight', 'Clearcoat').default_value = 1.0; entrada(bs, 'Coat Roughness', 'Clearcoat Roughness').default_value = 0.012
    return m
def material_vidrio(roto=False):
    m = bpy.data.materials.new('Vidrio'); nt, bs, out = reconstruir(m)
    bs.inputs['Base Color'].default_value = (0.02, 0.03, 0.035, 1); entrada(bs, 'Roughness').default_value = 0.01
    entrada(bs, 'Transmission Weight', 'Transmission').default_value = 0.92; entrada(bs, 'IOR').default_value = 1.45
    return m
M_PINTURA = material_pintura(); M_VIDRIO = material_vidrio()
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for i, sl in enumerate(o.material_slots):
        m = sl.material
        if not m: continue
        p = principled(m)
        if p is None: continue
        bc = p.inputs['Base Color'].default_value
        met = p.inputs['Metallic'].default_value; ro = p.inputs['Roughness'].default_value
        if bc[0] < 0.02 and bc[1] < 0.02 and met > 0.85 and ro < 0.15 and 'Auto' in (o.parent.parent.name if o.parent and o.parent.parent else '') + (o.parent.name if o.parent else ''):
            sl.material = M_PINTURA
        if o.name.startswith(('glass', 'headlightRglass', 'taillight_glass')) or m.name in ('mirror',):
            if o.name.startswith('glass'): sl.material = M_VIDRIO
        if o.name == 'Asfalto': sl.material = M_ASFALTO
print('materiales ok')

# ── cámaras: lente en mm, sensor vertical 24; cortes por marcadores
camaras = []
for tm in JS['tomas']:
    cam = bpy.data.objects[tm['camara']]
    cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24.0; cam.data.lens = float(tm['lente_mm']); cam.data.clip_start = 0.05; cam.data.clip_end = 900
    camaras.append((int(tm['frame_inicio']), cam))
for f, cam in sorted(camaras, key=lambda x: x[0]):
    mk = sc.timeline_markers.new(cam.name, frame=f); mk.camera = cam
sc.camera = sorted(camaras, key=lambda x: x[0])[0][1]

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'efectos_accidente.py')).read())
for _im in bpy.data.images:
    if _im.source == 'FILE' and not _im.packed_file: _im.pack()           # el BLEND queda autónomo (texturas adentro)
bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
print('GUARDADO', SALIDA, os.path.getsize(SALIDA))
