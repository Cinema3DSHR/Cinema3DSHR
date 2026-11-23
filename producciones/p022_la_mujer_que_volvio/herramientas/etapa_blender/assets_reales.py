# Árboles y rocas reales para el accidente (Blender). Se ejecuta dentro de efectos_accidente.py (comparte bpy, sc, col_fx, random…) o suelto con ver_assets3.py.
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Euler
TEX = '/home/user/cap1_noir/tex'
NEXUS = '/home/user/Rally-Sim-movile/biblioteca/vegetacion_y_suelo/rocas/'

def _mat_corteza():
    m = bpy.data.materials.new('Corteza_pino'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(f'{TEX}/corteza_pino.png'); im.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(tc.outputs['UV'], im.inputs[0])
    ru = nt.nodes.new('ShaderNodeTexNoise'); ru.inputs['Scale'].default_value = 28.0; ru.inputs['Detail'].default_value = 8.0
    nt.links.new(tc.outputs['Object'], ru.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMath'); mix.operation = 'ADD'; nt.links.new(im.outputs['Color'], mix.inputs[0]); nt.links.new(ru.outputs['Fac'], mix.inputs[1])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 1.2; bp.inputs['Distance'].default_value = 0.04; nt.links.new(mix.outputs[0], bp.inputs['Height'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (0.035, 0.024, 0.017, 1); rp.color_ramp.elements[1].color = (0.12, 0.085, 0.06, 1)
    nt.links.new(im.outputs['Color'], rp.inputs[0]); nt.links.new(rp.outputs[0], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.55; nt.links.new(bp.outputs[0], bs.inputs['Normal'])
    return m
def _mat_agujas(nombre):
    m = bpy.data.materials.new('Agujas_' + nombre); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(f'{TEX}/agujas_pino_{nombre}.png'); im.extension = 'CLIP'
    nt.links.new(tc.outputs['UV'], im.inputs[0]); nt.links.new(im.outputs['Color'], bs.inputs['Base Color']); nt.links.new(im.outputs['Alpha'], bs.inputs['Alpha'])
    bs.inputs['Roughness'].default_value = 0.4
    return m
M_CORTEZA = None; M_AGUJAS = {}

def pino(nombre, alto, semilla):
    """Un pino completo (una sola malla con 2 materiales): tronco ahusado con corteza, verticilos de ramas que cuelgan y ramilletes de agujas en cruz."""
    global M_CORTEZA
    rng = random.Random(semilla)
    if M_CORTEZA is None:
        M_CORTEZA = _mat_corteza(); M_AGUJAS['a'] = _mat_agujas('a'); M_AGUJAS['b'] = _mat_agujas('b')
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    lean = Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 0))
    def centro(z): return Vector((lean.x * (z / alto) ** 2, lean.y * (z / alto) ** 2, z))
    def tubo(p0, p1, r0, r1, lados, mat, tramos=1, dd=None):
        d = (p1 - p0); L = d.length; z = d.normalized(); x = z.cross(Vector((0, 0, 1)))
        if x.length < 1e-3: x = Vector((1, 0, 0))
        x.normalize(); y = z.cross(x)
        anillos = []
        for k in range(tramos + 1):
            u = k / tramos; c = p0 + d * u; r = r0 + (r1 - r0) * u
            vs = []
            for i in range(lados):
                a = 2 * math.pi * i / lados
                vs.append(bm.verts.new(c + (x * math.cos(a) + y * math.sin(a)) * r * (1.0 + (rng.uniform(-0.18, 0.18) if mat == 0 else 0))))
            anillos.append(vs)
        for k in range(tramos):
            for i in range(lados):
                f = bm.faces.new((anillos[k][i], anillos[k][(i + 1) % lados], anillos[k + 1][(i + 1) % lados], anillos[k + 1][i])); f.material_index = mat
                for li, lp in enumerate(f.loops):
                    lp[uv].uv = ((i + (1 if li in (1, 2) else 0)) / lados * 2.0, (k + (1 if li in (2, 3) else 0)) / tramos * (L / 1.6))
    # tronco: 26 tramos, raíz ensanchada
    pts = [centro(alto * k / 26) for k in range(27)]
    for k in range(26):
        z0 = pts[k].z / alto; z1 = pts[k + 1].z / alto
        r = lambda z: 0.04 + alto * 0.028 * (1 - z) ** 1.15 + (0.07 * math.exp(-z * 18))
        tubo(pts[k], pts[k + 1], r(z0), r(z1), 12, 0)
    # verticilos de ramas
    z = alto * 0.20
    while z < alto * 0.985:
        t = z / alto
        n = 5 + int(rng.random() * 3) if t < 0.85 else 3
        base_az = rng.uniform(0, 6.28)
        Lmax = alto * 0.40 * (1.0 - t) ** 0.75 + 0.35
        for i in range(n):
            az = base_az + 2 * math.pi * i / n + rng.uniform(-0.35, 0.35)
            L = Lmax * rng.uniform(0.6, 1.0)
            dirh = Vector((math.cos(az), math.sin(az), 0))
            caida = rng.uniform(0.28, 0.5) * (1.0 - t * 0.5)
            origen = centro(z) + Vector((0, 0, rng.uniform(-0.12, 0.12)))
            segs = 4; prev = origen
            for s in range(1, segs + 1):
                u = s / segs
                p = origen + dirh * (L * u) + Vector((0, 0, -caida * L * u * u + (0.12 * L * u if s < 3 else 0)))
                tubo(prev, p, 0.022 * (1 - (s - 1) / segs) + 0.004, 0.022 * (1 - s / segs) + 0.004, 5, 0)
                prev = p
            # ramilletes de agujas a lo largo de la rama: 3 tarjetas en cruz por tramo
            for s in range(1, segs + 1):
                u = s / segs
                p = origen + dirh * (L * u) + Vector((0, 0, -caida * L * u * u + (0.12 * L * u if s < 3 else 0)))
                p_ant = origen + dirh * (L * (u - 1 / segs)) + Vector((0, 0, -caida * L * (u - 1 / segs) ** 2 + (0.12 * L * (u - 1 / segs) if s < 3 else 0)))
                eje = (p - p_ant).normalized(); lado = eje.cross(Vector((0, 0, 1))).normalized()
                tam = L / segs * 1.7; anch = 0.32 + 0.35 * (1 - t)
                for g in (0.0, 1.05, 2.1):
                    r = Matrix.Rotation(g, 3, eje); lat = r @ lado
                    c0 = p_ant + eje * tam * 0.0
                    v = [bm.verts.new(c0 - lat * anch * 0.5), bm.verts.new(c0 + lat * anch * 0.5), bm.verts.new(c0 + lat * anch * 0.5 + eje * tam), bm.verts.new(c0 - lat * anch * 0.5 + eje * tam)]
                    f = bm.faces.new(v); f.material_index = 1 if (s + i) % 2 == 0 else 2
                    for li, lp in enumerate(f.loops): lp[uv].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][li]
        z += rng.uniform(0.35, 0.55)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    me.materials.append(M_CORTEZA); me.materials.append(M_AGUJAS['a']); me.materials.append(M_AGUJAS['b'])
    return me

_ROCAS = []
def rocas_reales():
    """Importa las 3 rocas con foto de la biblioteca de Nexus y les da detalle: subdivisión + desplazamiento fino. Devuelve 3 objetos plantilla ocultos."""
    if _ROCAS: return _ROCAS
    for nom in ('rock_rock.glb', 'rock_rock_2.glb', 'rock_rock_3.glb'):
        antes = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=NEXUS + nom)
        nuevos = [o for o in bpy.data.objects if o not in antes]
        malla = next(o for o in nuevos if o.type == 'MESH')
        bpy.context.view_layer.objects.active = malla
        malla.parent = None; malla.matrix_world = Matrix.Identity(4)
        for o in nuevos:
            if o is not malla: bpy.data.objects.remove(o, do_unlink=True)
        sub = malla.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 3; sub.subdivision_type = 'SIMPLE'
        tex = bpy.data.textures.new('rocadet_' + nom, 'CLOUDS'); tex.noise_scale = 0.16; tex.noise_depth = 3
        dis = malla.modifiers.new('det', 'DISPLACE'); dis.texture = tex; dis.strength = 0.010; dis.mid_level = 0.5
        # materiales mojados y con relieve fino
        for m in malla.data.materials:
            if m and m.use_nodes:
                bs = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bs:
                    bs.inputs['Roughness'].default_value = 0.32
                    ru = m.node_tree.nodes.new('ShaderNodeTexNoise'); ru.inputs['Scale'].default_value = 60.0; ru.inputs['Detail'].default_value = 10.0
                    tc = m.node_tree.nodes.new('ShaderNodeTexCoord'); bp = m.node_tree.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6
                    m.node_tree.links.new(tc.outputs['Object'], ru.inputs['Vector']); m.node_tree.links.new(ru.outputs['Fac'], bp.inputs['Height']); m.node_tree.links.new(bp.outputs[0], bs.inputs['Normal'])
        malla.hide_render = True; malla.hide_viewport = True
        _ROCAS.append(malla)
    return _ROCAS
