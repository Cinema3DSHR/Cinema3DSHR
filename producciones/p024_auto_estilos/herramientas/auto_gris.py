"""AUTO GRIS ESTACIONADO (Blender): el Hustler del proyecto pintado de gris metalizado en un playón de hormigón rodeado de seto, con luz de sol suave, rebotes en el piso y la cámara girando 5 s a su alrededor:
arranca de frente, rodea por el costado (se queda enfocando el lateral) y termina atrás. Vertical 720×1280, 30 fps, 150 cuadros.
Uso: /opt/tools/blendenv/bin/python auto_gris.py SALIDA.blend [GLB_AUTO]"""
import bpy, math, sys, random
from mathutils import Vector, Matrix
SALIDA = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else sys.argv[1]
GLB = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else '/home/user/Cinema3DSHR/producciones/p022_la_mujer_que_volvio/godot_cap1/assets/hustler.glb'
W, H, FPS, N = 720, 1280, 30, 150
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; rng = random.Random(3)
bpy.ops.import_scene.gltf(filepath=GLB)
car = [o for o in bpy.data.objects if o.type == 'MESH']
raiz = [o for o in bpy.data.objects if o.parent is None][0]
# frente del auto: eje largo (y) y qué lado tiene los faros
def centro(nombre):
    o = bpy.data.objects.get(nombre); return None if o is None else sum((o.matrix_world @ Vector(c) for c in o.bound_box), Vector()) / 8
fa = [centro(n) for n in ('headlightRglass', 'headlights_okidoko') if centro(n)]
tr = centro('taillight_glass')
print('FARO', fa[:1], 'TRASERA', tr)
# materiales: carrocería gris metalizado con barniz, vidrios, llantas y goma
PINT = {'remap_kuzov', 'nodamage_lod0', 'roof'}
def pintura():
    m = bpy.data.materials.new('Pintura_gris'); m.use_nodes = True; bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.20, 0.21, 0.23, 1); bs.inputs['Metallic'].default_value = 0.9; bs.inputs['Roughness'].default_value = 0.28
    for k, v in (('Coat Weight', 1.0), ('Coat Roughness', 0.03), ('Coat IOR', 1.5)):
        try: bs.inputs[k].default_value = v
        except Exception: pass
    return m
MP = pintura()
for o in car:
    for i, m in enumerate(o.data.materials):
        if m is None: continue
        n = m.name
        if n in PINT: o.data.materials[i] = MP
        elif n == 'lights_lod0' or n.startswith('vehiclelights'):
            m.use_nodes = True; b2 = m.node_tree.nodes.get('Principled BSDF')
            if b2:
                for l in list(m.node_tree.links):
                    if l.to_socket == b2.inputs['Base Color']: m.node_tree.links.remove(l)
                b2.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1); b2.inputs['Roughness'].default_value = 0.05
                for k, v in (('Transmission Weight', 0.9), ('IOR', 1.45)):
                    try: b2.inputs[k].default_value = v
                    except Exception: pass
        elif n.startswith('Color_000000') or n == 'carp':
            m.use_nodes = True; bs = m.node_tree.nodes.get('Principled BSDF')
        if m.use_nodes:
            bs = m.node_tree.nodes.get('Principled BSDF')
            if bs and n in ('tire', 'tire_matt'): bs.inputs['Roughness'].default_value = 0.8
for o in car: o['clase'] = 'auto'
raiz.rotation_euler = (0, 0, 0); raiz.location = (0, 0, 0.75)
# ───── playón: hormigón, rayas de estacionamiento, cordón; seto circular y cielo ─────
def mat(nombre, col, rough=0.8, metal=0.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = metal; return m
def hormigon():
    m = bpy.data.materials.new('Hormigon'); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 3.0; ns.inputs['Detail'].default_value = 12.0; nt.links.new(tc.outputs['Object'], ns.inputs['Vector'])
    ns2 = nt.nodes.new('ShaderNodeTexNoise'); ns2.inputs['Scale'].default_value = 90.0; ns2.inputs['Detail'].default_value = 4.0; nt.links.new(tc.outputs['Object'], ns2.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (0.40, 0.40, 0.41, 1); rp.color_ramp.elements[1].color = (0.62, 0.62, 0.63, 1); nt.links.new(ns.outputs['Fac'], rp.inputs[0]); nt.links.new(rp.outputs[0], bs.inputs['Base Color'])
    rg = nt.nodes.new('ShaderNodeMapRange'); rg.inputs['To Min'].default_value = 0.28; rg.inputs['To Max'].default_value = 0.55; nt.links.new(ns2.outputs['Fac'], rg.inputs['Value']); nt.links.new(rg.outputs[0], bs.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.2; bp.inputs['Distance'].default_value = 0.004; nt.links.new(ns2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs[0], bs.inputs['Normal']); return m
def setc(o, c): o['clase'] = c; return o
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=40, fill_type='NGON', location=(0, 0, 0)); sue = bpy.context.active_object; sue.name = 'Suelo'; sue.data.materials.append(hormigon()); setc(sue, 'suelo')
def caja(nombre, c, t, m, clase, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=c); o = bpy.context.active_object; o.name = nombre; o.scale = t; o.rotation_euler = rot; bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); return setc(o, clase)
MB = mat('Pintura_blanca', (0.9, 0.9, 0.88), 0.6); MC = mat('Cordon', (0.55, 0.55, 0.55), 0.8)
caja('Raya_1', (-1.75, 0.0, 0.006), (0.14, 6.2, 0.012), MB, 'suelo'); caja('Raya_2', (1.75, 0.0, 0.006), (0.14, 6.2, 0.012), MB, 'suelo'); caja('Raya_fondo', (0, -3.1, 0.006), (3.64, 0.14, 0.012), MB, 'suelo')
caja('Cordon', (0, -3.9, 0.08), (9.0, 0.35, 0.16), MC, 'suelo')
ML = mat_h = mat('Seto', (0.10, 0.28, 0.08), 0.9)
for k in range(96):                                                                                 # seto: anillo de matas redondas
    a = 2 * math.pi * k / 96; r = 17.0 + rng.uniform(-0.6, 0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rng.uniform(1.1, 1.7), segments=12, ring_count=8, location=(r * math.cos(a), r * math.sin(a), 0.9)); o = bpy.context.active_object; o.name = f'Seto_{k}'; o.scale = (1, 1, 0.85); o.data.materials.append(ML); setc(o, 'fondo')
    for p in o.data.polygons: p.use_smooth = True
for k in range(14):                                                                                 # árboles detrás del seto
    a = 2 * math.pi * k / 14 + 0.2; r = 21.0
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=5, vertices=8, location=(r * math.cos(a), r * math.sin(a), 2.5)); t = bpy.context.active_object; t.name = f'Arbol_tronco_{k}'; t.data.materials.append(mat('Tronco', (0.3, 0.2, 0.12), 0.9)); setc(t, 'fondo')
    bpy.ops.mesh.primitive_uv_sphere_add(radius=3.0, segments=12, ring_count=8, location=(r * math.cos(a), r * math.sin(a), 7.0)); c = bpy.context.active_object; c.name = f'Arbol_copa_{k}'; c.data.materials.append(mat('Copa', (0.16, 0.38, 0.12), 0.9)); setc(c, 'fondo')
    for p in c.data.polygons: p.use_smooth = True
# ───── luces ─────
sol = bpy.data.lights.new('Sol', 'SUN'); sol.energy = 4.2; sol.color = (1.0, 0.93, 0.82); sol.angle = math.radians(2.0)
so = bpy.data.objects.new('Sol', sol); sc.collection.objects.link(so); dsol = Vector((-0.45, -0.55, -0.7)).normalized(); so.rotation_euler = dsol.to_track_quat('-Z', 'Y').to_euler()
for nm, c, e, col, tam in (('Softbox_izq', (-7, 3, 3.2), 380, (0.9, 0.95, 1.0), 4.0), ('Softbox_der', (7, 2, 2.6), 260, (1.0, 0.95, 0.9), 3.5), ('Softbox_atras', (0, 8, 4.0), 300, (1.0, 1.0, 1.0), 5.0)):
    l = bpy.data.lights.new(nm, 'AREA'); l.energy = e; l.color = col; l.size = tam; lo = bpy.data.objects.new(nm, l); sc.collection.objects.link(lo); lo.location = c
    lo.rotation_euler = (Vector((0, 0, 0.8)) - Vector(c)).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new('Cielo'); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'LINEAR'; tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.85, 0.88, 0.95, 1); cr.color_ramp.elements[0].position = 0.45; cr.color_ramp.elements[1].color = (0.35, 0.55, 0.9, 1); cr.color_ramp.elements[1].position = 0.9
nt.links.new(tc.outputs['Generated'], gr.inputs[0]); nt.links.new(gr.outputs['Fac'], cr.inputs[0]); nt.links.new(cr.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.1; nt.links.new(bg.outputs[0], out.inputs[0]); sc.world = w
# ───── cámara: órbita de 5 s ─────
cam = bpy.data.cameras.new('Camara'); cam.sensor_fit = 'VERTICAL'; cam.angle_y = math.radians(40); co = bpy.data.objects.new('Camara', cam); sc.collection.objects.link(co); sc.camera = co
foco = bpy.data.objects.new('Foco', None); sc.collection.objects.link(foco)
cam.dof.use_dof = True; cam.dof.focus_object = foco; cam.dof.aperture_fstop = 3.2
sc.frame_start, sc.frame_end = 1, N
def sm(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def pose(f):
    t = (f - 1) / (N - 1)                                        # 0…1
    # azimut: 0° = de frente; 0–30 %: frente → costado; 30–62 %: se queda en el costado (deriva lenta); 62–100 %: costado → atrás
    if t < 0.30: az = 90 * sm(t / 0.30)
    elif t < 0.62: az = 90 + 14 * (t - 0.30) / 0.32
    else: az = 104 + 80 * sm((t - 0.62) / 0.38)
    lat = math.sin(math.radians(min(az, 180)))                    # 0 de frente/atrás, 1 de costado
    rad = 6.6 + 5.4 * lat ** 2                                    # de costado la cámara se aleja para que entre el auto entero
    alt = 1.25 + 0.5 * lat; mira_z = 0.70 + 0.1 * lat
    # dirección del frente del auto = −Y (cámara en azimut 0° está delante, del lado −Y)
    a = math.radians(az); loc = Vector((rad * math.sin(a) * -1.0 * -1.0, -rad * math.cos(a), alt))
    return loc, Vector((0, 0, mira_z))
for f in range(1, N + 1):
    loc, mira = pose(f); co.location = loc; co.rotation_euler = (mira - loc).to_track_quat('-Z', 'Y').to_euler(); foco.location = mira
    co.keyframe_insert('location', frame=f); co.keyframe_insert('rotation_euler', frame=f); foco.keyframe_insert('location', frame=f)
for ob in (co, foco):
    for fc in ob.animation_data.action.layers[0].strips[0].channelbags[0].fcurves if hasattr(ob.animation_data.action, 'layers') else ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = W, H, 100, FPS
cy = sc.cycles; cy.device = 'CPU'; cy.samples = 32; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.03; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.max_bounces = 6; cy.glossy_bounces = 5; cy.seed = 11; cy.use_animated_seed = False
if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items] else 'None'
bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
print('GUARDADO', SALIDA)
