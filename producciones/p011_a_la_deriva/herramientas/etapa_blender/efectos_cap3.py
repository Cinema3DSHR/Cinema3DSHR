# Luces, mundo, materiales, hologramas y perfil de render del capítulo 3. Se ejecuta dentro de construir_cap3.py (comparte sus variables).
import bpy, math, random
from mathutils import Vector

def gb(x, y, z):            # Godot (x, y, z) → Blender (x, −z, y)
    return Vector((x, -z, y))

# ── perfil de render OBLIGATORIO (docs/METODOLOGIA.md) a 540p horizontal
r = sc.render
r.engine = 'CYCLES'; r.resolution_x = 960; r.resolution_y = 540; r.resolution_percentage = 100
r.fps = 30; r.fps_base = 1.0; r.use_motion_blur = False; r.film_transparent = False
cy = sc.cycles
cy.device = 'CPU'; cy.samples = 6; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 4; cy.glossy_bounces = 4; cy.transmission_bounces = 6; cy.volume_bounces = 0; cy.transparent_max_bounces = 8
if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
cy.seed = 7; cy.use_animated_seed = False
sc.view_settings.view_transform = 'Khronos PBR Neutral'; sc.view_settings.exposure = 0.4
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'

# ── mundo: espacio profundo
w = bpy.data.worlds.new('Espacio'); w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.004, 0.006, 0.014, 1); bg.inputs[1].default_value = 1.0
sc.world = w

# ── luces por sala (coordenadas de Godot: x, y, z). cada una: (x0, x1, z0, z1, filas, columnas, color, energía)
SALAS = {
    'pasillo':   (-19, 19, -1.0, 1.0, 1, 9, (0.80, 0.90, 1.00), 140),
    'comedor':   (-4, 4, -9, -2.5, 2, 3, (1.00, 0.95, 0.88), 220),
    'kate':      (10, 16, -7.2, -2.4, 2, 2, (0.90, 1.00, 0.96), 170),
    'aiden':     (-16, -10, -7.2, -2.4, 2, 2, (1.00, 0.86, 0.68), 170),
    'comunic':   (-16, -10, 2.4, 7.4, 2, 2, (0.75, 0.88, 1.00), 170),
    'centro':    (-32, -22, -5.5, 5.5, 2, 3, (0.75, 0.88, 1.00), 260),
    'botanico':  (-4.5, 10.5, 3.0, 10.5, 3, 4, (0.92, 1.00, 0.94), 230),
    'enferm':    (15, 19, 2.6, 7.4, 1, 2, (1.00, 1.00, 1.00), 120),
}
ALTO = 3.15
col_luz = bpy.data.collections.new('Luces'); sc.collection.children.link(col_luz)
for nombre, (x0, x1, z0, z1, nf, nc, color, e) in SALAS.items():
    for i in range(nf):
        for j in range(nc):
            x = x0 + (x1 - x0) * ((j + 0.5) / nc); z = z0 + (z1 - z0) * ((i + 0.5) / nf)
            ld = bpy.data.lights.new(f'L_{nombre}_{i}{j}', 'AREA'); ld.energy = e * 2.4; ld.color = color
            ld.shape = 'RECTANGLE'; ld.size = 1.2; ld.size_y = 0.7; ld.spread = math.radians(160)
            lo = bpy.data.objects.new(ld.name, ld); lo.location = gb(x, ALTO - 0.08, z); lo.rotation_euler = (0, 0, 0)
            col_luz.objects.link(lo)
# luz de cultivo del botánico (violeta) y brillo azul de EVA
for nombre, pos, col, e, tam in (('cultivo', (3, 2.6, 8.0), (0.8, 0.55, 1.0), 90, 2.0), ('nucleoEVA', (-31.5, 2.2, 0), (0.2, 0.8, 1.0), 120, 1.5)):
    ld = bpy.data.lights.new(f'L_{nombre}', 'POINT'); ld.energy = e; ld.color = col; ld.shadow_soft_size = tam
    lo = bpy.data.objects.new(ld.name, ld); lo.location = gb(*pos); col_luz.objects.link(lo)

# ── materiales: vidrio, piel, hologramas
def principled(m):
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.use_nodes else None

for m in bpy.data.materials:
    p = principled(m)
    if p is None: continue
    n = m.name
    if n.startswith('EM3D_Skin') or n.startswith('EM3D_Nails'):
        for k, v in (('Subsurface Weight', 0.12), ('Roughness', 0.55)):
            try: p.inputs[k].default_value = v
            except Exception: pass
        try: p.inputs['Subsurface Radius'].default_value = (0.9, 0.35, 0.22)
        except Exception: pass
    if n.startswith('EM3D_Cornea'):
        try: p.inputs['Roughness'].default_value = 0.05; p.inputs['Alpha'].default_value = 0.12
        except Exception: pass
    m.use_backface_culling = False
    # el piso de la nave: en Godot llevaba un tinte >1 que el glTF recorta; se devuelve multiplicando la textura
    nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and ('suelo' in nd.image.name.lower()):
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs[0].default_value = 1.0; mx.inputs[7].default_value = (4.2, 4.2, 4.6, 1)
            p.inputs['Metallic'].default_value = 0.0; p.inputs['Roughness'].default_value = 0.5
            nt.links.new(nd.outputs['Color'], mx.inputs[6]); nt.links.new(mx.outputs[2], p.inputs['Base Color'])

# EVA: holograma (azul translúcido con borde brillante, líneas de barrido y parpadeo de proyección)
def material_holograma():
    m = bpy.data.materials.new('EVA_holograma'); m.use_nodes = True; nt = m.node_tree
    for nd in list(nt.nodes): nt.nodes.remove(nd)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    mix = nt.nodes.new('ShaderNodeMixShader'); tra = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission')
    fres = nt.nodes.new('ShaderNodeLayerWeight'); fres.inputs['Blend'].default_value = 0.35
    rampa = nt.nodes.new('ShaderNodeMath'); rampa.operation = 'MULTIPLY'
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ola = nt.nodes.new('ShaderNodeTexWave'); ola.wave_type = 'BANDS'; ola.bands_direction = 'Z'; ola.inputs['Scale'].default_value = 18.0; ola.inputs['Distortion'].default_value = 0.0
    ola_c = nt.nodes.new('ShaderNodeMapRange'); ola_c.inputs[1].default_value = 0.0; ola_c.inputs[2].default_value = 1.0; ola_c.inputs[3].default_value = 0.55; ola_c.inputs[4].default_value = 1.0
    parp = nt.nodes.new('ShaderNodeValue'); parp.name = 'parpadeo'; parp.label = 'parpadeo'; parp.outputs[0].default_value = 1.0
    mul1 = nt.nodes.new('ShaderNodeMath'); mul1.operation = 'MULTIPLY'
    mul2 = nt.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'; mul2.inputs[1].default_value = 0.8
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'MULTIPLY'; fac.inputs[1].default_value = 0.78
    em.inputs['Color'].default_value = (0.04, 0.34, 1.0, 1)
    L = nt.links.new
    L(tc.outputs['Object'], ola.inputs['Vector']); L(ola.outputs['Fac'], ola_c.inputs[0])
    L(fres.outputs['Facing'], add.inputs[0]); L(ola_c.outputs['Result'], mul1.inputs[0]); L(parp.outputs[0], mul1.inputs[1])
    L(mul1.outputs[0], mul2.inputs[0])
    L(mul2.outputs[0], em.inputs['Strength'])
    add.inputs[1].default_value = 0.35
    L(add.outputs[0], fac.inputs[0]); L(mul1.outputs[0], rampa.inputs[0]); rampa.inputs[1].default_value = 1.0
    L(fac.outputs[0], mix.inputs[0]); L(tra.outputs[0], mix.inputs[1]); L(em.outputs[0], mix.inputs[2]); L(mix.outputs[0], out.inputs[0])
    # parpadeo: valor 0.55…1 con ruido de baja frecuencia + caídas bruscas (proyección inestable), animado
    random.seed(4)
    for f in range(1, TOTAL + 1, 3):
        v = 1.0
        if random.random() < 0.08: v = random.uniform(0.2, 0.6)
        else: v = 0.85 + 0.15 * math.sin(f * 0.21)
        parp.outputs[0].default_value = v
        parp.outputs[0].keyframe_insert('default_value', frame=f)
    return m

holo = material_holograma()
objetos_eva = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.split('.')[0].startswith('eva_')] + \
              [o for o in bpy.data.objects if o.type == 'MESH' and 'eva' in [c.name for c in o.users_collection] ]
vistos = set()
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    # los meshes de EVA cuelgan de un esqueleto «EVA»: se reconoce por su raíz
    raiz = o
    while raiz.parent is not None: raiz = raiz.parent
    if raiz.name.split('.')[0] != 'eva': continue
    for i, slot in enumerate(o.material_slots):
        m = slot.material
        if m is None: continue
        p = principled(m)
        if p is not None and p.inputs['Alpha'].default_value < 0.02: continue          # interior de ojos y boca: invisibles
        slot.material = holo
print('LUCES', len(col_luz.objects), 'HOLO', holo.name)
