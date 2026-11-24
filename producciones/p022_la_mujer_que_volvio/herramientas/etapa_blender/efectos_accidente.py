# Efectos del accidente: luces, relámpagos, charcos, lluvia real, salpicaduras, agua que levanta el auto. Se ejecuta dentro de construir_accidente.py (comparte sus variables).
import bpy, math, random
from mathutils import Vector, Matrix

# ───────────────────────────── luces
for n, kw in (('Faro_L', {}), ('Faro_R', {})):
    o = bpy.data.objects[n]; L = o.data
    L.energy = 2600.0; L.spot_size = math.radians(52); L.spot_blend = 0.55; L.color = (1.0, 0.93, 0.78); L.shadow_soft_size = 0.06
    if hasattr(L, 'use_shadow'): L.use_shadow = True
bpy.data.objects['Luz_Trasera'].data.energy = 14.0; bpy.data.objects['Luz_Trasera'].data.color = (1, 0.04, 0.02)
bpy.data.objects['Luz_Luna'].data.energy = 1.1; bpy.data.objects['Luz_Luna'].data.color = (0.45, 0.55, 0.85); bpy.data.objects['Luz_Luna'].data.angle = math.radians(8)
ray = bpy.data.objects['Luz_Rayo'].data; ray.color = (0.75, 0.85, 1.0); ray.angle = math.radians(1.5)
def relampago(t0):
    f0 = int(t0 * FPS) + 1
    for df, e in ((0, 0.0), (1, 14.0), (3, 4.0), (5, 18.0), (7, 7.0), (12, 0.0)):
        ray.energy = e; ray.keyframe_insert('energy', frame=f0 + df)
ray.energy = 0.0; ray.keyframe_insert('energy', frame=1)
for t0 in EV['relampagos_s']: relampago(t0)
# luces de balizas (intermitentes) del auto destruido: 2 naranjas que laten a 1,6 Hz desde el reposo
bal = []
for lado in (-1, 1):
    for z, nm in ((-1.95, 'F'), (2.30, 'T')):
        l = bpy.data.lights.new(f'Baliza_{nm}{lado}', 'POINT'); l.color = (1.0, 0.45, 0.03); l.energy = 0.0; l.shadow_soft_size = 0.05
        o = bpy.data.objects.new(f'Baliza_{nm}{lado}', l); sc.collection.objects.link(o)
        o.parent = bpy.data.objects['AutoRaiz']; o.location = gb((lado * 0.62, -0.05, z)); bal.append(l)
f_r = int(EV['balizas_desde_s'] * FPS) + 1
for l in bal:
    l.energy = 0.0; l.keyframe_insert('energy', frame=1)
    f = f_r
    while f < TOTAL:
        for df, e in ((0, 0.0), (1, 38.0), (8, 38.0), (9, 0.0)):
            l.energy = e; l.keyframe_insert('energy', frame=min(f + df, TOTAL))
        f += 19

def mat_luz(nombre, color, fuerza):
    m = bpy.data.materials.new(nombre); nt, bs, out = reconstruir(m)
    bs.inputs['Base Color'].default_value = (color[0] * 0.2, color[1] * 0.2, color[2] * 0.2, 1); entrada(bs, 'Roughness').default_value = 0.05
    entrada(bs, 'Emission Color').default_value = (color[0], color[1], color[2], 1); entrada(bs, 'Emission Strength').default_value = fuerza
    return m
M_FARO = mat_luz('Luz_faro', (1.0, 0.95, 0.85), 3.0); M_TRAS = mat_luz('Luz_trasera', (1.0, 0.03, 0.02), 2.2); M_INTER = mat_luz('Luz_intermitente', (1.0, 0.45, 0.04), 0.6)
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    for sl in o.material_slots:
        m = sl.material
        if not m or not (m.name.startswith('lights_lod0') or m.name.startswith('vehiclelights')): continue
        if o.name.startswith(('taillight', 'taillights')): sl.material = M_TRAS
        elif o.name.startswith(('headlights', 'headlightR', 'lightshidhead')): sl.material = M_FARO
        elif o.name.startswith('svet'): sl.material = M_INTER
# ───────────────────────────── charcos grandes sobre el carril (donde el auto levanta agua)
def a_blender_yaw(yaw): return yaw
col_fx = bpy.data.collections.new('Efectos'); sc.collection.children.link(col_fx)
for k, ch in enumerate(JS['charcos']):
    bpy.ops.mesh.primitive_circle_add(vertices=56, radius=1.0, fill_type='NGON', location=gb((ch['x'], 0.006, ch['z'])))
    o = bpy.context.active_object; o.name = f'Charco_{k}'
    o.scale = (1.9, 5.2, 1.0); o.rotation_euler = (0, 0, a_blender_yaw(ch['yaw']))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(M_CHARCO)
    for c in list(o.users_collection): c.objects.unlink(o)
    col_fx.objects.link(o)

# ───────────────────────────── datos por cuadro del auto: velocidad (ubicación), intensidad del agua levantada (escala x) y fuerza de la salpicadura (escala y)
auto = bpy.data.objects['AutoRaiz']
pos = []
for f in range(1, TOTAL + 1):
    sc.frame_set(f); pos.append(auto.matrix_world.translation.copy())
vel = []
for i in range(TOTAL):
    a = pos[max(i - 1, 0)]; b = pos[min(i + 1, TOTAL - 1)]
    vel.append((b - a) * (FPS / (2.0 if 0 < i < TOTAL - 1 else 1.0)))
datos = bpy.data.objects.new('Datos_Auto', None); datos.empty_display_type = 'PLAIN_AXES'; sc.collection.objects.link(datos)
def gauss(t, t0, s): return math.exp(-((t - t0) / s) ** 2)
for i in range(TOTAL):
    t = i / FPS; sp = vel[i].length
    base = min(sp / 22.0, 1.0) * 0.30
    boost = sum(gauss(t, c['t_paso_s'] + 0.12, 0.38) for c in JS['charcos'])
    derr = 0.55 * min(max((t - EV['derrape_s']) / 0.5, 0.0), 1.0) * (1.0 if t < EV['impacto_s'] else max(0.0, 1.0 - (t - EV['impacto_s']) / 2.5))
    inten = min(1.0, base + 0.65 * boost + derr) * min(sp / 3.0, 1.0)
    spl = 1.0 + 1.6 * min(boost, 1.0) + 1.2 * derr
    datos.location = vel[i]; datos.scale = (inten, spl, 1.0)
    datos.keyframe_insert('location', frame=i + 1); datos.keyframe_insert('scale', frame=i + 1)
print('datos de velocidad listos; velocidad máx', round(max(v.length for v in vel), 1))

# ───────────────────────────── ayudas de nodos de geometría
def ng(nombre):
    g = bpy.data.node_groups.new(nombre, 'GeometryNodeTree')
    g.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    return g
def N(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        if k == 'ops': n.operation = v
        else: setattr(n, k, v)
    return n
def mat_(nt, op, a=None, b=None, c=None):
    n = N(nt, 'ShaderNodeMath', ops=op)
    for idx, v in enumerate((a, b, c)):
        if v is None: continue
        if hasattr(v, 'node'): nt.links.new(v, n.inputs[idx])
        else: n.inputs[idx].default_value = v
    return n.outputs[0]
def vec_(nt, op, a=None, b=None, s=None):
    n = N(nt, 'ShaderNodeVectorMath', operation=op)
    for idx, v in enumerate((a, b)):
        if v is None: continue
        if hasattr(v, 'node'): nt.links.new(v, n.inputs[idx])
        else: n.inputs[idx].default_value = v
    if s is not None:
        if hasattr(s, 'node'): nt.links.new(s, n.inputs['Scale'])
        else: n.inputs['Scale'].default_value = s
    return n.outputs[0]
def rnd(nt, seed, lo=0.0, hi=1.0, ident=None):
    n = N(nt, 'FunctionNodeRandomValue', data_type='FLOAT')
    flo = [s for s in n.inputs if s.name == 'Min' and s.type == 'VALUE'][0]; fhi = [s for s in n.inputs if s.name == 'Max' and s.type == 'VALUE'][0]
    flo.default_value = lo; fhi.default_value = hi
    n.inputs['Seed'].default_value = seed
    if ident is not None: nt.links.new(ident, n.inputs['ID'])
    return [s for s in n.outputs if s.type == 'VALUE'][0]
def xyz(nt, x, y, z):
    n = N(nt, 'ShaderNodeCombineXYZ')
    for k, v in zip(('X', 'Y', 'Z'), (x, y, z)):
        if hasattr(v, 'node'): nt.links.new(v, n.inputs[k])
        else: n.inputs[k].default_value = v
    return n.outputs[0]
def sep(nt, v):
    n = N(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(v, n.inputs[0]); return n.outputs['X'], n.outputs['Y'], n.outputs['Z']
def malla_obj(nombre, bm_fn, mat):
    me = bpy.data.meshes.new(nombre); bm_fn(me); o = bpy.data.objects.new(nombre, me); sc.collection.objects.link(o)
    me.materials.append(mat); o.hide_viewport = True; o.hide_render = True
    for c in list(o.users_collection): c.objects.unlink(o)
    col_fx.objects.link(o); return o
import bmesh
def m_gota(me):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.0035, 0.0035, 0.42), verts=bm.verts); bm.to_mesh(me); bm.free()
def m_anillo(me):
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, radius=1.0, segments=20)
    bmesh.ops.create_circle(bm, cap_ends=False, radius=0.84, segments=20)
    bm.verts.ensure_lookup_table()
    for k in range(20): bm.faces.new((bm.verts[k], bm.verts[(k + 1) % 20], bm.verts[20 + (k + 1) % 20], bm.verts[20 + k]))
    bm.to_mesh(me); bm.free()
def m_esfera(me):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0); bm.to_mesh(me); bm.free()

# materiales de los efectos
def mat_lluvia():
    m = bpy.data.materials.new('Lluvia'); nt = m.node_tree if m.use_nodes else None
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = N(nt, 'ShaderNodeOutputMaterial'); em = N(nt, 'ShaderNodeEmission'); tr = N(nt, 'ShaderNodeBsdfTransparent'); mx = N(nt, 'ShaderNodeMixShader')
    em.inputs['Color'].default_value = (0.78, 0.86, 1.0, 1); em.inputs['Strength'].default_value = 0.45
    mx.inputs['Fac'].default_value = 0.22
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0]); return m
def mat_anillo():
    m = bpy.data.materials.new('Anillo_salpicadura'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = N(nt, 'ShaderNodeOutputMaterial'); em = N(nt, 'ShaderNodeEmission'); tr = N(nt, 'ShaderNodeBsdfTransparent'); mx = N(nt, 'ShaderNodeMixShader')
    at = N(nt, 'ShaderNodeAttribute', attribute_type='INSTANCER', attribute_name='fase')
    inv = N(nt, 'ShaderNodeMath', ops='SUBTRACT'); inv.inputs[0].default_value = 1.0; nt.links.new(at.outputs['Fac'], inv.inputs[1])
    pw = N(nt, 'ShaderNodeMath', ops='POWER'); pw.inputs[1].default_value = 2.0; nt.links.new(inv.outputs[0], pw.inputs[0])
    sc_ = N(nt, 'ShaderNodeMath', ops='MULTIPLY'); sc_.inputs[1].default_value = 0.22; nt.links.new(pw.outputs[0], sc_.inputs[0])
    em.inputs['Color'].default_value = (0.7, 0.8, 0.95, 1); em.inputs['Strength'].default_value = 0.8
    nt.links.new(sc_.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0]); return m
def mat_niebla():
    m = bpy.data.materials.new('Niebla_agua'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = N(nt, 'ShaderNodeOutputMaterial'); v = N(nt, 'ShaderNodeVolumeScatter'); v.inputs['Density'].default_value = 2.2; v.inputs['Color'].default_value = (0.85, 0.9, 1.0, 1)
    nt.links.new(v.outputs[0], out.inputs['Volume']); return m
def mat_rocio(op):
    m = bpy.data.materials.new('Rocio'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = N(nt, 'ShaderNodeOutputMaterial'); em = N(nt, 'ShaderNodeEmission'); tr = N(nt, 'ShaderNodeBsdfTransparent'); mx = N(nt, 'ShaderNodeMixShader')
    em.inputs['Color'].default_value = (0.8, 0.88, 1.0, 1); em.inputs['Strength'].default_value = 0.16; mx.inputs['Fac'].default_value = op
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0]); return m
O_GOTA = malla_obj('Gota_lluvia', m_gota, mat_lluvia())
O_ANILLO = malla_obj('Anillo_lluvia', m_anillo, mat_anillo())
def mat_humo():
    m = bpy.data.materials.new('Humo_motor'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = N(nt, 'ShaderNodeOutputMaterial'); v = N(nt, 'ShaderNodeVolumeScatter'); v.inputs['Density'].default_value = 0.55; v.inputs['Color'].default_value = (0.32, 0.32, 0.34, 1); v.inputs['Anisotropy'].default_value = 0.5
    nt.links.new(v.outputs[0], out.inputs['Volume']); return m
O_ROCIO = malla_obj('Gota_rocio', m_esfera, mat_rocio(0.40)); O_NIEBLA = malla_obj('Niebla_rocio', m_esfera, mat_niebla()); O_HUMO = malla_obj('Bocanada_humo', m_esfera, mat_humo())
for _o in (O_ROCIO, O_NIEBLA, O_HUMO):
    for _p in _o.data.polygons: _p.use_smooth = True
# siguen al auto (sólo posición)
sigue = bpy.data.objects.new('Sigue_auto', None); sc.collection.objects.link(sigue)
cc = sigue.constraints.new('COPY_LOCATION'); cc.target = auto; cc.use_z = False

# ───────────────────────────── LLUVIA REAL: 12.800 trazos que caen y se reciclan según el tiempo de la escena (determinista por cuadro)
def construir_lluvia():
    g = ng('GN_Lluvia'); nt = g.nodes
    ent = N(g, 'NodeGroupInput'); sal = N(g, 'NodeGroupOutput')
    grid = N(g, 'GeometryNodeMeshGrid'); grid.inputs['Size X'].default_value = 36.0; grid.inputs['Size Y'].default_value = 36.0; grid.inputs['Vertices X'].default_value = 2; grid.inputs['Vertices Y'].default_value = 2
    dist = N(g, 'GeometryNodeDistributePointsOnFaces', distribute_method='RANDOM'); dist.inputs['Density'].default_value = 17.0; dist.inputs['Seed'].default_value = 3
    g.links.new(grid.outputs['Mesh'], dist.inputs['Mesh'])
    tiempo = N(g, 'GeometryNodeInputSceneTime')
    r0 = rnd(g, 5)
    H = 17.0; VEL = 11.5
    caida = mat_(g, 'FLOORED_MODULO', mat_(g, 'ADD', mat_(g, 'MULTIPLY', tiempo.outputs['Seconds'], VEL), mat_(g, 'MULTIPLY', r0, H)), H)
    z = mat_(g, 'SUBTRACT', H, caida)
    sp = N(g, 'GeometryNodeSetPosition'); g.links.new(dist.outputs['Points'], sp.inputs['Geometry'])
    g.links.new(xyz(g, mat_(g, 'MULTIPLY', z, -0.11), 0.0, z), sp.inputs['Offset'])
    oi = N(g, 'GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = O_GOTA; oi.inputs['As Instance'].default_value = True
    ins = N(g, 'GeometryNodeInstanceOnPoints'); g.links.new(sp.outputs['Geometry'], ins.inputs['Points']); g.links.new(oi.outputs['Geometry'], ins.inputs['Instance'])
    ins.inputs['Rotation'].default_value = (0.0, math.atan(0.11), 0.0)
    g.links.new(ins.outputs['Instances'], sal.inputs['Geometry'])
    return g
def construir_salpicaduras():
    g = ng('GN_Salpicaduras'); sal = N(g, 'NodeGroupOutput')
    grid = N(g, 'GeometryNodeMeshGrid'); grid.inputs['Size X'].default_value = 26.0; grid.inputs['Size Y'].default_value = 26.0; grid.inputs['Vertices X'].default_value = 2; grid.inputs['Vertices Y'].default_value = 2
    dist = N(g, 'GeometryNodeDistributePointsOnFaces', distribute_method='RANDOM'); dist.inputs['Density'].default_value = 7.0; dist.inputs['Seed'].default_value = 8
    g.links.new(grid.outputs['Mesh'], dist.inputs['Mesh'])
    tiempo = N(g, 'GeometryNodeInputSceneTime'); r0 = rnd(g, 9)
    fase = mat_(g, 'FRACT', mat_(g, 'ADD', mat_(g, 'MULTIPLY', tiempo.outputs['Seconds'], 1.9), r0))
    st = N(g, 'GeometryNodeStoreNamedAttribute', data_type='FLOAT', domain='POINT'); st.inputs['Name'].default_value = 'fase'
    g.links.new(dist.outputs['Points'], st.inputs['Geometry']); g.links.new(fase, st.inputs['Value'])
    oi = N(g, 'GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = O_ANILLO; oi.inputs['As Instance'].default_value = True
    ins = N(g, 'GeometryNodeInstanceOnPoints'); g.links.new(st.outputs['Geometry'], ins.inputs['Points']); g.links.new(oi.outputs['Geometry'], ins.inputs['Instance'])
    radio = mat_(g, 'ADD', 0.015, mat_(g, 'MULTIPLY', fase, 0.085))
    g.links.new(xyz(g, radio, radio, 1.0), ins.inputs['Scale'])
    tr = N(g, 'GeometryNodeTranslateInstances'); g.links.new(ins.outputs['Instances'], tr.inputs['Instances']); tr.inputs['Translation'].default_value = (0, 0, 0.012)
    g.links.new(tr.outputs['Instances'], sal.inputs['Geometry'])
    return g
def construir_rocio():
    g = ng('GN_Rocio'); sal = N(g, 'NodeGroupOutput'); unir = N(g, 'GeometryNodeJoinGeometry')
    dat = N(g, 'GeometryNodeObjectInfo'); dat.inputs['Object'].default_value = datos
    V = dat.outputs['Location']; ESC = dat.outputs['Scale']
    _, vlen_dummy, _ = sep(g, V)
    inten = sep(g, ESC)[0]; splash = sep(g, ESC)[1]
    tiempo = N(g, 'GeometryNodeInputSceneTime')
    nv = vec_(g, 'NORMALIZE', V)
    atras = vec_(g, 'SCALE', nv, s=-1.0)
    lat = vec_(g, 'CROSS_PRODUCT', atras, (0.0, 0.0, 1.0))
    def cadena(rueda, n, tam, op_obj, semilla, vida, vscale, extra_alto):
        w = N(g, 'GeometryNodeObjectInfo'); w.inputs['Object'].default_value = rueda
        W = w.outputs['Location']
        ml = N(g, 'GeometryNodeMeshLine'); ml.inputs['Count'].default_value = n; ml.inputs['Start Location'].default_value = (0, 0, 0); ml.inputs['Offset'].default_value = (0, 0, 0)
        ida = N(g, 'GeometryNodeInputIndex').outputs[0]
        r1 = rnd(g, semilla + 1, ident=ida); r2 = rnd(g, semilla + 2, ident=ida); r3 = rnd(g, semilla + 3, -1.0, 1.0, ident=ida); r4 = rnd(g, semilla + 4, ident=ida); r5 = rnd(g, semilla + 5, ident=ida)
        edad = mat_(g, 'MULTIPLY', mat_(g, 'FRACT', mat_(g, 'ADD', mat_(g, 'DIVIDE', tiempo.outputs['Seconds'], vida), r1)), vida)
        vback = mat_(g, 'MULTIPLY', mat_(g, 'ADD', 0.8, mat_(g, 'MULTIPLY', r2, 3.2)), vscale)
        vlat = mat_(g, 'MULTIPLY', mat_(g, 'MULTIPLY', r3, 2.4), mat_(g, 'MULTIPLY', splash, vscale))
        vup = mat_(g, 'MULTIPLY', mat_(g, 'ADD', 1.4, mat_(g, 'MULTIPLY', r4, extra_alto)), mat_(g, 'ADD', 0.6, mat_(g, 'MULTIPLY', splash, 0.4)))
        v0 = vec_(g, 'ADD', vec_(g, 'ADD', vec_(g, 'SCALE', atras, s=vback), vec_(g, 'SCALE', lat, s=vlat)), xyz(g, 0.0, 0.0, vup))
        despl = vec_(g, 'ADD', vec_(g, 'SCALE', v0, s=edad), vec_(g, 'SCALE', V, s=mat_(g, 'MULTIPLY', edad, -1.0)))
        caida = xyz(g, 0.0, 0.0, mat_(g, 'MULTIPLY', mat_(g, 'MULTIPLY', edad, edad), -4.9))
        pos = vec_(g, 'ADD', vec_(g, 'ADD', W, despl), caida)
        pz = sep(g, pos)
        pos = xyz(g, pz[0], pz[1], mat_(g, 'MAXIMUM', pz[2], 0.03))
        sp = N(g, 'GeometryNodeSetPosition'); g.links.new(ml.outputs['Mesh'], sp.inputs['Geometry']); g.links.new(pos, sp.inputs['Position'])
        visible = mat_(g, 'LESS_THAN', r5, inten)
        oi = N(g, 'GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = op_obj; oi.inputs['As Instance'].default_value = True
        ins = N(g, 'GeometryNodeInstanceOnPoints'); g.links.new(sp.outputs['Geometry'], ins.inputs['Points']); g.links.new(oi.outputs['Geometry'], ins.inputs['Instance'])
        crece = mat_(g, 'MULTIPLY', mat_(g, 'ADD', 0.6, mat_(g, 'MULTIPLY', edad, 1.2)), mat_(g, 'MULTIPLY', visible, tam))
        g.links.new(xyz(g, crece, crece, crece), ins.inputs['Scale'])
        g.links.new(ins.outputs['Instances'], unir.inputs['Geometry'])
    for ruedan in ('Rueda_FL', 'Rueda_FR', 'Rueda_RL', 'Rueda_RR'):
        o = bpy.data.objects[ruedan]
        cadena(o, 210, 0.016, O_ROCIO, 20, 0.85, 1.0, 3.2)        # gotas
        cadena(o, 40, 0.16, O_NIEBLA, 60, 1.25, 0.7, 1.6)          # neblina de agua
    g.links.new(unir.outputs['Geometry'], sal.inputs['Geometry'])
    return g
def objeto_gn(nombre, grupo, sigue_pos=True):
    me = bpy.data.meshes.new(nombre); o = bpy.data.objects.new(nombre, me); col_fx.objects.link(o)
    md = o.modifiers.new('GN', 'NODES'); md.node_group = grupo
    if sigue_pos:
        o.parent = sigue
    return o
objeto_gn('Lluvia', construir_lluvia()); objeto_gn('Salpicaduras', construir_salpicaduras()); objeto_gn('Rocio_ruedas', construir_rocio(), False)
print('efectos listos')

# ═════════════════════════════ ÁRBOLES Y ROCAS REALES (reemplazan a los conos y esferas de Godot) ═════════════════════════════
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assets_reales as AR
rng_a = random.Random(77)
pos_arboles = [o.location.copy() for o in bpy.data.objects if o.name.startswith('Copa_')]
pos_rocas = [o.location.copy() for o in bpy.data.objects if o.name.startswith('Roca_')]
for o in [o for o in bpy.data.objects if o.name.startswith(('Tronco_', 'Copa_', 'Roca_'))]: bpy.data.objects.remove(o, do_unlink=True)
variantes = [AR.pino(f'Pino_v{i}', al, 100 + i) for i, al in enumerate((10.0, 12.0, 14.5, 9.0))]
col_arb = bpy.data.collections.new('Arboles'); sc.collection.children.link(col_arb)
for i, p in enumerate(pos_arboles):
    o = bpy.data.objects.new(f'Pino_{i}', variantes[i % len(variantes)]); col_arb.objects.link(o)
    o.location = (p.x, p.y, 0.0); o.rotation_euler = (0, 0, rng_a.uniform(0, 6.28)); s_ = rng_a.uniform(0.8, 1.25); o.scale = (s_, s_, s_)
R = AR.rocas_reales()
col_roc = bpy.data.collections.new('Rocas'); sc.collection.children.link(col_roc)
# zonas prohibidas para las rocas: por donde pasan las cámaras y Gabriel (para no taparlos)
_zonas = []
for _f in range(1, TOTAL + 1, 12):
    sc.frame_set(_f)
    _zonas.append(sc.camera.matrix_world.translation.copy())
for _sg in EV['ruta_gabriel']:
    for _u in (0.0, 0.5, 1.0):
        _zonas.append(gb((_sg['p0'][0] + (_sg['p1'][0] - _sg['p0'][0]) * _u, 0, _sg['p0'][1] + (_sg['p1'][1] - _sg['p0'][1]) * _u)))
def _libre(p, esc_):
    return all((Vector((p.x, p.y, 0)) - Vector((z.x, z.y, 0))).length > esc_ * 1.0 + 2.6 for z in _zonas)
def poner_roca(p, esc_, rot):
    if not _libre(p, esc_): return
    o = bpy.data.objects.new('Roca', R[rng_a.randrange(3)].data); col_roc.objects.link(o)
    o.location = (p.x, p.y, esc_ * 0.12); o.rotation_euler = rot; o.scale = (esc_, esc_ * rng_a.uniform(0.7, 1.1), esc_ * rng_a.uniform(0.6, 1.0))
    for m in R[0].modifiers:
        n = o.modifiers.new(m.name, m.type)
        if m.type == 'SUBSURF': n.levels = 2; n.render_levels = 3; n.subdivision_type = 'SIMPLE'
        else: n.texture = m.texture; n.strength = m.strength; n.mid_level = m.mid_level
for p in pos_rocas: poner_roca(p, rng_a.uniform(3.2, 7.0), (rng_a.uniform(-0.3, 0.3), rng_a.uniform(-0.3, 0.3), rng_a.uniform(0, 6.28)))
Pimp = gb(EV['punto_impacto']); Dd = gb(EV['dir_deslizamiento']); Ld = Vector((-Dd.y, Dd.x, 0))        # dirección del deslizamiento y su izquierda (plano del suelo)
for k in range(34):                                                                                     # peñascos a lo largo del borde del barranco y entre la ruta y el borde
    q = Pimp + Dd * (12.0 + rng_a.uniform(-0.8, 1.4)) + Ld * rng_a.uniform(-22, 18)
    poner_roca(q, rng_a.uniform(2.0, 5.5), (rng_a.uniform(-0.4, 0.4), rng_a.uniform(-0.4, 0.4), rng_a.uniform(0, 6.28)))
for k in range(26):
    q = Pimp + Dd * rng_a.uniform(-24, 6) + Ld * rng_a.uniform(6, 20)
    poner_roca(q, rng_a.uniform(1.4, 3.8), (rng_a.uniform(-0.4, 0.4), rng_a.uniform(-0.4, 0.4), rng_a.uniform(0, 6.28)))
print('árboles', len(pos_arboles), 'rocas reales listas')

# ═════════════════════════════ ROPA (en lugar del traje espacial), SANGRE EN ROSTRO Y MANOS ═════════════════════════════
def dueno(o):
    while o:
        if o.name in ('gabriel', 'gabriel_fuera', 'elena'): return o.name
        o = o.parent
    return None
for o in bpy.data.objects:
    if o.type == 'MESH' and dueno(o) and o.name.startswith(('VIVO_', 'BOTA_LUZ_', 'EMBLEMA')):
        o.hide_render = True; o.hide_viewport = True
def mat_ropa(nombre, arriba, abajo, gen_z_cadera=0.53):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); sepx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sepx.inputs[0])
    corte = nt.nodes.new('ShaderNodeMath'); corte.operation = 'SMOOTH_MAX' if False else 'GREATER_THAN'; corte.inputs[1].default_value = gen_z_cadera; nt.links.new(sepx.outputs['Z'], corte.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs['A'].default_value = abajo; mix.inputs['B'].default_value = arriba; nt.links.new(corte.outputs[0], mix.inputs['Factor'])
    tej = nt.nodes.new('ShaderNodeTexNoise'); tej.inputs['Scale'].default_value = 900.0; tej.inputs['Detail'].default_value = 2.0; nt.links.new(tc.outputs['Object'], tej.inputs['Vector'])
    arr = nt.nodes.new('ShaderNodeTexNoise'); arr.inputs['Scale'].default_value = 14.0; arr.inputs['Detail'].default_value = 6.0; nt.links.new(tc.outputs['Object'], arr.inputs['Vector'])
    sumar = nt.nodes.new('ShaderNodeMath'); sumar.operation = 'ADD'; nt.links.new(tej.outputs['Fac'], sumar.inputs[0]); nt.links.new(arr.outputs['Fac'], sumar.inputs[1])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.5; bp.inputs['Distance'].default_value = 0.002; nt.links.new(sumar.outputs[0], bp.inputs['Height'])
    nt.links.new(mix.outputs['Result'], bs.inputs['Base Color']); nt.links.new(bp.outputs[0], bs.inputs['Normal']); bs.inputs['Roughness'].default_value = 0.78
    return m
M_ROPA_G = mat_ropa('Ropa_Gabriel', (0.030, 0.034, 0.050, 1), (0.016, 0.016, 0.020, 1)); M_ROPA_E = mat_ropa('Ropa_Elena', (0.22, 0.020, 0.040, 1), (0.018, 0.016, 0.02, 1))
def mat_zapato():
    m = bpy.data.materials.new('Zapatos'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    bs.inputs['Base Color'].default_value = (0.012, 0.010, 0.010, 1); bs.inputs['Roughness'].default_value = 0.25
    return m
M_ZAP = mat_zapato()
for o in bpy.data.objects:
    d = dueno(o)
    if o.type != 'MESH' or not d: continue
    if o.name.startswith('TRAJE_MONO'): o.data.materials.clear(); o.data.materials.append(M_ROPA_E if d == 'elena' else M_ROPA_G)
    elif o.name.startswith(('TRAJE_BOTAS', 'TRAJE_PIE')): o.data.materials.clear(); o.data.materials.append(M_ZAP)
# sangre en la piel (rostro y manos): aparece con el choque y se oscurece con el tiempo; máscaras por coordenadas generadas del cuerpo
f_imp = int(EV['impacto_s'] * FPS) + 1
def _rgba(nodo, nombre):
    return [x for x in nodo.inputs if x.name == nombre and x.type == 'RGBA'][0]
def sangre_en(material, mascara_fn, factor_max=1.0):
    nt = material.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ent = bs.inputs['Base Color']
    origen = ent.links[0].from_socket if ent.links else None; val = tuple(ent.default_value)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ')
    caja = None
    if material.name == 'EM3D_Skin_Head':                       # caja real de la piel de la cabeza (en reposo) para normalizar las coordenadas
        for ob in bpy.data.objects:
            if ob.type == 'MESH' and any(sl.material == material for sl in ob.material_slots):
                idx = [i for i, sl in enumerate(ob.material_slots) if sl.material == material][0]
                vs = {v for pl in ob.data.polygons if pl.material_index == idx for v in pl.vertices}
                if vs:
                    cs = [ob.data.vertices[v].co for v in vs]
                    lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))); hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
                    caja = (lo, hi); break
    if caja:
        mpn = nt.nodes.new('ShaderNodeMapping'); lo, hi = caja; sz = hi - lo
        mpn.inputs['Location'].default_value = (-lo.x / sz.x, -lo.y / sz.y, -lo.z / sz.z); mpn.inputs['Scale'].default_value = (1 / sz.x, 1 / sz.y, 1 / sz.z)
        nt.links.new(tc.outputs['Object'], mpn.inputs[0]); nt.links.new(mpn.outputs[0], sx.inputs[0]); fuente = mpn.outputs[0]
        print('caja de la cabeza', [round(v, 3) for v in lo], [round(v, 3) for v in hi])
    else:
        nt.links.new(tc.outputs['Generated'], sx.inputs[0]); fuente = tc.outputs['Generated']
    ru = nt.nodes.new('ShaderNodeTexNoise'); ru.inputs['Scale'].default_value = 22.0; ru.inputs['Detail'].default_value = 7.0; nt.links.new(fuente, ru.inputs['Vector'])
    m_ = mascara_fn(nt, sx, ru)
    cant = nt.nodes.new('ShaderNodeValue'); cant.outputs[0].default_value = 0.0
    d_ = cant.outputs[0].driver_add('default_value') if False else None
    drv = cant.driver_add('outputs[0].default_value') if False else None
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; nt.links.new(m_, mul.inputs[0]); mul.inputs[1].default_value = 1.0
    d2 = mul.inputs[1].driver_add('default_value'); d2.driver.type = 'SCRIPTED'; d2.driver.expression = f'min(max((frame - {f_imp}) / 40.0, 0.0), 1.0) * {factor_max}'
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; _rgba(mx, 'B').default_value = (0.20, 0.004, 0.006, 1)
    if origen: nt.links.new(origen, _rgba(mx, 'A'))
    else: _rgba(mx, 'A').default_value = val
    cl = nt.nodes.new('ShaderNodeClamp'); nt.links.new(mul.outputs[0], cl.inputs['Value']); nt.links.new(cl.outputs[0], mx.inputs['Factor'])
    nt.links.new(mx.outputs['Result'], ent)
    # brillo húmedo donde hay sangre
    rg = nt.nodes.new('ShaderNodeMix'); rg.data_type = 'FLOAT'; rg.inputs['A'].default_value = bs.inputs['Roughness'].default_value; rg.inputs['B'].default_value = 0.08
    nt.links.new(cl.outputs[0], rg.inputs['Factor']); nt.links.new(rg.outputs['Result'], bs.inputs['Roughness'])
def mascara_cara(nt, sx, ru):          # frente, sienes y mejillas con goteo irregular (simétrica: se ve de cualquier lado)
    zr = nt.nodes.new('ShaderNodeMapRange'); zr.inputs['From Min'].default_value = 0.35; zr.inputs['From Max'].default_value = 0.90; nt.links.new(sx.outputs['Y'], zr.inputs['Value'])      # el eje vertical de esta malla es Y
    mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(zr.outputs[0], mm.inputs[0]); nt.links.new(ru.outputs['Fac'], mm.inputs[1])
    ge = nt.nodes.new('ShaderNodeMath'); ge.operation = 'GREATER_THAN'; ge.inputs[1].default_value = 0.20; nt.links.new(mm.outputs[0], ge.inputs[0]); return ge.outputs[0]
def mascara_manos(nt, sx, ru):         # manos y antebrazos (zona baja a los costados del cuerpo)
    zr = nt.nodes.new('ShaderNodeMapRange'); zr.inputs['From Min'].default_value = 0.52; zr.inputs['From Max'].default_value = 0.40; nt.links.new(sx.outputs['Z'], zr.inputs['Value'])
    mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; nt.links.new(zr.outputs[0], mm.inputs[0]); nt.links.new(ru.outputs['Fac'], mm.inputs[1])
    ge = nt.nodes.new('ShaderNodeMath'); ge.operation = 'GREATER_THAN'; ge.inputs[1].default_value = 0.20; nt.links.new(mm.outputs[0], ge.inputs[0]); return ge.outputs[0]
def sangre_cara(material):
    """Rostro manchado (no chorreado): una heridita en la frente y manchas finas de roce en mejilla, mandíbula, sien y mentón, como de quien se tocó la cara con la mano.
    Cada mancha es una elipse gaussiana definida en el espacio 3D del modelo, centrada en un punto real de la superficie de la cara (se calculan ojos y boca del propio modelo)."""
    ob = next(o for o in bpy.data.objects if o.type == 'MESH' and any(sl.material == material for sl in o.material_slots))
    idx = [i for i, sl in enumerate(ob.material_slots) if sl.material == material][0]
    vs = {v for pl in ob.data.polygons if pl.material_index == idx for v in pl.vertices}
    cs = [ob.data.vertices[v].co for v in vs]
    zmed = sum(c.z for c in cs) / len(cs)
    def verts(prefijo, excluir=None):
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name.startswith(prefijo) and not (excluir and o.name.startswith(excluir)): return [v.co for v in o.data.vertices]
        return []
    ev = verts('EM3D_Base_Eye', 'EM3D_Base_EyeO'); dv = verts('EM3D_Base_Teeth')
    frente = 1.0 if (sum(c.z for c in ev) / max(len(ev), 1)) > zmed else -1.0
    xs = sorted(c.x for c in ev); xm = xs[len(xs) // 2]
    izq = [c for c in ev if c.x < xm]; der = [c for c in ev if c.x >= xm]
    cm_ = lambda L, ax: sum(getattr(c, ax) for c in L) / max(len(L), 1)
    ojo_i = (cm_(izq, 'x'), cm_(izq, 'y')); ojo_d = (cm_(der, 'x'), cm_(der, 'y')); ojo_y = (ojo_i[1] + ojo_d[1]) / 2
    boca_y = cm_(dv, 'y') if dv else ojo_y - 6.0
    D = max(ojo_y - boca_y, 3.0)
    def sup(x, y):                                                           # punto real de la superficie de la cara (el más al frente cerca de x, y)
        cand = [c for c in cs if abs(c.x - x) < 0.7 and abs(c.y - y) < 0.7]
        if not cand: cand = sorted(cs, key=lambda c: (c.x - x) ** 2 + (c.y - y) ** 2)[:6]
        return max(cand, key=lambda c: c.z * frente)
    todos = [v.co for v in ob.data.vertices]
    LO = Vector((min(c.x for c in todos), min(c.y for c in todos), min(c.z for c in todos))); HI = Vector((max(c.x for c in todos), max(c.y for c in todos), max(c.z for c in todos))); SZ = HI - LO
    nt = material.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); ent = bs.inputs['Base Color']
    origen = ent.links[0].from_socket if ent.links else None; val = tuple(ent.default_value)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    def gauss(cx, cy, ax, ay, ang, estrias=0.0):
        c = sup(cx, cy)
        cn = ((c.x - LO.x) / SZ.x, (c.y - LO.y) / SZ.y, (c.z - LO.z) / SZ.z)                 # centro en coordenadas «generadas» (0–1 del modelo en reposo: no siguen la pose)
        rs = nt.nodes.new('ShaderNodeVectorMath'); rs.operation = 'SUBTRACT'; rs.inputs[1].default_value = cn; nt.links.new(tc.outputs['Generated'], rs.inputs[0])
        a_cm = nt.nodes.new('ShaderNodeVectorMath'); a_cm.operation = 'MULTIPLY'; a_cm.inputs[1].default_value = (SZ.x, SZ.y, SZ.z); nt.links.new(rs.outputs[0], a_cm.inputs[0])
        rot = nt.nodes.new('ShaderNodeVectorRotate'); rot.rotation_type = 'Z_AXIS'; rot.inputs['Angle'].default_value = -ang; nt.links.new(a_cm.outputs[0], rot.inputs['Vector'])
        dv_ = nt.nodes.new('ShaderNodeVectorMath'); dv_.operation = 'DIVIDE'; dv_.inputs[1].default_value = (ax, ay, 1.4); nt.links.new(rot.outputs[0], dv_.inputs[0])
        class _M: pass
        mp = _M(); mp.outputs = [dv_.outputs[0]]
        ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(mp.outputs[0], ln.inputs[0])
        sq = nt.nodes.new('ShaderNodeMath'); sq.operation = 'MULTIPLY'; nt.links.new(ln.outputs['Value'], sq.inputs[0]); nt.links.new(ln.outputs['Value'], sq.inputs[1])
        ng = nt.nodes.new('ShaderNodeMath'); ng.operation = 'MULTIPLY'; ng.inputs[1].default_value = -1.0; nt.links.new(sq.outputs[0], ng.inputs[0])
        ex = nt.nodes.new('ShaderNodeMath'); ex.operation = 'EXPONENT'; nt.links.new(ng.outputs[0], ex.inputs[0])
        g = ex.outputs[0]
        if estrias > 0:                                                      # estrías del roce de los dedos
            wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 3.2; wv.inputs['Distortion'].default_value = 1.6; wv.inputs['Detail'].default_value = 1.0
            nt.links.new(mp.outputs[0], wv.inputs['Vector'])
            mw = nt.nodes.new('ShaderNodeMath'); mw.operation = 'MULTIPLY_ADD'; mw.inputs[1].default_value = estrias; mw.inputs[2].default_value = 1.0 - estrias
            nt.links.new(wv.outputs['Fac'], mw.inputs[0])
            pr = nt.nodes.new('ShaderNodeMath'); pr.operation = 'MULTIPLY'; nt.links.new(g, pr.inputs[0]); nt.links.new(mw.outputs[0], pr.inputs[1]); g = pr.outputs[0]
        return g
    def suma(lista):
        acc = lista[0]
        for g in lista[1:]:
            n = nt.nodes.new('ShaderNodeMath'); n.operation = 'ADD'; nt.links.new(acc, n.inputs[0]); nt.links.new(g, n.inputs[1]); acc = n.outputs[0]
        cl = nt.nodes.new('ShaderNodeClamp'); nt.links.new(acc, cl.inputs[0]); return cl.outputs[0]
    def esc_(g, k):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = 'MULTIPLY'; n.inputs[1].default_value = k; nt.links.new(g, n.inputs[0]); return n.outputs[0]
    # manchas de roce (cm del modelo; ax/ay = semiejes; ang en rad)
    manchas = [esc_(gauss(ojo_i[0] - 0.6, ojo_y - 0.55 * D, 2.6, 1.0, -0.35, 0.55), 1.0),               # mejilla
               esc_(gauss(ojo_d[0] + 0.4, boca_y + 0.60 * D, 2.0, 0.85, 0.50, 0.55), 1.0),              # mandíbula del otro lado
               esc_(gauss((ojo_i[0] + ojo_d[0]) / 2 + 0.3, boca_y - 0.62 * D, 1.8, 0.75, 0.08, 0.5), 1.0),   # mentón
               esc_(gauss(ojo_i[0] - 1.2, ojo_y + 0.55 * D, 1.6, 0.70, 0.55, 0.5), 0.95),               # sien
               esc_(gauss(ojo_d[0] + 0.9, ojo_y - 0.15 * D, 1.5, 0.65, -0.4, 0.5), 0.95),               # pómulo del otro lado
               esc_(gauss((ojo_i[0] + ojo_d[0]) / 2 + 0.2, ojo_y + 0.05 * D, 0.55, 1.3, 0.1, 0.0), 0.65),   # puente de la nariz (se la tocó)
               esc_(gauss(ojo_d[0] + 0.5, ojo_y + 0.62 * D, 1.4, 0.55, 0.3, 0.5), 0.85)]               # roce en la frente del otro lado
    heridas = [esc_(gauss(ojo_d[0] + 0.7, ojo_y - 0.30 * D, 0.75, 0.16, -0.5), 0.85), gauss(ojo_i[0] + 0.6, ojo_y + 0.60 * D, 1.05, 0.22, 0.35), esc_(gauss(ojo_i[0] + 0.6, ojo_y + 0.60 * D, 1.8, 0.65, 0.35), 0.55),
               esc_(gauss(ojo_i[0] + 0.4, ojo_y + 0.60 * D - 0.95, 0.16, 0.34, 0.1), 0.75)]                # la heridita y una gotita corta (sin chorro)
    M_s = suma(manchas); M_h = suma(heridas)
    M_s.node.name = 'DBG_Ms'; M_h.node.name = 'DBG_Mh'
    amt = nt.nodes.new('ShaderNodeMath'); amt.operation = 'MULTIPLY'; amt.inputs[0].default_value = 1.0; amt.inputs[1].default_value = 1.0; amt.name = 'AmtSangreCara'
    d1 = amt.inputs[0].driver_add('default_value'); d1.driver.type = 'SCRIPTED'; d1.driver.expression = f'min(max((frame - {f_imp}) / 24.0, 0.0), 1.0)'
    def x_amt(g):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = 'MULTIPLY'; nt.links.new(g, n.inputs[0]); nt.links.new(amt.outputs[0], n.inputs[1]); return n.outputs[0]
    m_s2 = x_amt(M_s); m_h2 = x_amt(M_h)
    mx1 = nt.nodes.new('ShaderNodeMix'); mx1.data_type = 'RGBA'; _rgba(mx1, 'B').default_value = (0.12, 0.005, 0.007, 1)
    if origen: nt.links.new(origen, _rgba(mx1, 'A'))
    else: _rgba(mx1, 'A').default_value = val
    nt.links.new(m_s2, mx1.inputs['Factor'])
    mx2 = nt.nodes.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; _rgba(mx2, 'B').default_value = (0.045, 0.0, 0.002, 1)
    nt.links.new(mx1.outputs['Result'], _rgba(mx2, 'A')); nt.links.new(m_h2, mx2.inputs['Factor'])
    nt.links.new(mx2.outputs['Result'], ent)
    rg = nt.nodes.new('ShaderNodeMix'); rg.data_type = 'FLOAT'; rg.inputs['A'].default_value = bs.inputs['Roughness'].default_value; rg.inputs['B'].default_value = 0.20
    mm_ = nt.nodes.new('ShaderNodeMath'); mm_.operation = 'MAXIMUM'; nt.links.new(m_s2, mm_.inputs[0]); nt.links.new(m_h2, mm_.inputs[1])
    nt.links.new(mm_.outputs[0], rg.inputs['Factor']); nt.links.new(rg.outputs['Result'], bs.inputs['Roughness'])
    print('sangre del rostro lista (3D): ojo_y', round(ojo_y, 1), 'boca_y', round(boca_y, 1), 'D', round(D, 1), 'frente', frente)
m = bpy.data.materials.get('EM3D_Skin_Head')
if m and m.use_nodes: sangre_cara(m)
m = bpy.data.materials.get('EM3D_Skin_Arm')
if m and m.use_nodes: sangre_en(m, mascara_manos)
print('ropa y sangre en piel listas')

# ═════════════════════════════ SANGRE EN EL SUELO, HUMO, NIEBLA BAJA ═════════════════════════════
def mat_sangre_suelo():
    m = bpy.data.materials.new('Sangre_suelo'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    tc = nt.nodes.new('ShaderNodeTexCoord'); ru = nt.nodes.new('ShaderNodeTexNoise'); ru.inputs['Scale'].default_value = 2.8; ru.inputs['Detail'].default_value = 8.0; nt.links.new(tc.outputs['Generated'], ru.inputs['Vector'])
    gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (-0.5, -0.5, -0.5); nt.links.new(tc.outputs['Generated'], mp.inputs[0]); nt.links.new(mp.outputs[0], gr.inputs[0])
    inv = nt.nodes.new('ShaderNodeMapRange'); inv.inputs['From Min'].default_value = 0.5; inv.inputs['From Max'].default_value = 0.95; nt.links.new(gr.outputs['Fac'], inv.inputs['Value'])
    nz = nt.nodes.new('ShaderNodeMapRange'); nz.inputs['To Min'].default_value = 0.35; nz.inputs['To Max'].default_value = 1.15; nt.links.new(ru.outputs['Fac'], nz.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; nt.links.new(inv.outputs[0], mul.inputs[0]); nt.links.new(nz.outputs[0], mul.inputs[1])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.10; mr.inputs['From Max'].default_value = 0.30; nt.links.new(mul.outputs[0], mr.inputs['Value'])
    bs.inputs['Base Color'].default_value = (0.11, 0.0, 0.004, 1); bs.inputs['Roughness'].default_value = 0.04
    nt.links.new(mr.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(bs.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0]); return m
M_SANGRE = mat_sangre_suelo()
def mancha(nombre, pos_gb, tam, t_visible_s):
    bpy.ops.mesh.primitive_plane_add(size=tam, location=(pos_gb.x, pos_gb.y, 0.011)); o = bpy.context.active_object; o.name = nombre
    o.data.materials.append(M_SANGRE); o.rotation_euler = (0, 0, rng_a.uniform(0, 6.28))
    for c in list(o.users_collection): c.objects.unlink(o)
    col_fx.objects.link(o)
    f0 = int(t_visible_s * FPS) + 1
    o.scale = (0.001, 0.001, 0.001); o.keyframe_insert('scale', frame=max(f0 - 1, 1))
    o.scale = (1, 1, 1); o.keyframe_insert('scale', frame=f0 + 45)
# charco bajo la puerta del conductor (donde sale) y rastros por donde camina (gotas más chicas)
rg = EV['ruta_gabriel']
primera = rg[0]; mancha('Sangre_puerta', gb((primera['p0'][0], 0, primera['p0'][1])), 2.3, primera['t0'])
for i, sg in enumerate(rg[1:], 1):
    if sg['clip'] in ('inj_walk', 'sad_walk'):
        n = 6
        for k in range(n):
            u = (k + 0.6) / n; px = sg['p0'][0] + (sg['p1'][0] - sg['p0'][0]) * u; pz = sg['p0'][1] + (sg['p1'][1] - sg['p0'][1]) * u
            mancha(f'Gota_sangre_{i}_{k}', gb((px + rng_a.uniform(-0.15, 0.15), 0, pz + rng_a.uniform(-0.15, 0.15))), rng_a.uniform(0.25, 0.55), sg['t0'] + sg['dur'] * u)
    if sg['clip'] in ('kneel_down', 'fall_fwd'):
        mancha(f'Sangre_caida_{i}', gb((sg['p0'][0], 0, sg['p0'][1])), 1.6, sg['t0'] + 0.6)
# humo del motor (volúmenes que suben y se disipan, deterministas por cuadro) y niebla baja alrededor del accidente
datos_humo = bpy.data.objects.new('Datos_humo', None); sc.collection.objects.link(datos_humo)
for i in range(TOTAL):
    t = i / FPS; v = min(max((t - EV['impacto_s']) / 1.5, 0.0), 1.0)
    datos_humo.scale = (v, 1.0, 1.0); datos_humo.keyframe_insert('scale', frame=i + 1)
origen_humo = bpy.data.objects.new('Humo_origen', None); sc.collection.objects.link(origen_humo); origen_humo.parent = auto; origen_humo.location = gb((0.1, 0.15, -1.55))
def construir_humo():
    g = ng('GN_Humo'); sal = N(g, 'NodeGroupOutput')
    d = N(g, 'GeometryNodeObjectInfo'); d.inputs['Object'].default_value = datos_humo; inten = sep(g, d.outputs['Scale'])[0]
    o_ = N(g, 'GeometryNodeObjectInfo'); o_.inputs['Object'].default_value = origen_humo; O = o_.outputs['Location']
    ml = N(g, 'GeometryNodeMeshLine'); ml.inputs['Count'].default_value = 60; ml.inputs['Start Location'].default_value = (0, 0, 0); ml.inputs['Offset'].default_value = (0, 0, 0)
    tiempo = N(g, 'GeometryNodeInputSceneTime'); ida = N(g, 'GeometryNodeInputIndex').outputs[0]
    r1 = rnd(g, 31, ident=ida); r2 = rnd(g, 32, -1.0, 1.0, ident=ida); r3 = rnd(g, 33, -1.0, 1.0, ident=ida); r4 = rnd(g, 34, ident=ida)
    V = 5.0
    edad = mat_(g, 'MULTIPLY', mat_(g, 'FRACT', mat_(g, 'ADD', mat_(g, 'DIVIDE', tiempo.outputs['Seconds'], V), r1)), V)
    pos = vec_(g, 'ADD', O, xyz(g, mat_(g, 'ADD', mat_(g, 'MULTIPLY', edad, 0.6), mat_(g, 'MULTIPLY', r2, mat_(g, 'MULTIPLY', edad, 0.35))), mat_(g, 'MULTIPLY', r3, mat_(g, 'MULTIPLY', edad, 0.3)), mat_(g, 'MULTIPLY', edad, 1.15)))
    sp = N(g, 'GeometryNodeSetPosition'); g.links.new(ml.outputs['Mesh'], sp.inputs['Geometry']); g.links.new(pos, sp.inputs['Position'])
    oi = N(g, 'GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = O_HUMO; oi.inputs['As Instance'].default_value = True
    ins = N(g, 'GeometryNodeInstanceOnPoints'); g.links.new(sp.outputs['Geometry'], ins.inputs['Points']); g.links.new(oi.outputs['Geometry'], ins.inputs['Instance'])
    crece = mat_(g, 'MULTIPLY', mat_(g, 'ADD', 0.16, mat_(g, 'MULTIPLY', edad, 0.14)), inten)
    g.links.new(xyz(g, crece, crece, crece), ins.inputs['Scale']); g.links.new(ins.outputs['Instances'], sal.inputs['Geometry'])
    return g
objeto_gn('Humo_motor', construir_humo(), False)
# niebla baja: cubo de volumen alrededor del lugar del accidente (se ve con las balizas y los faros)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(Pimp.x + Dd.x * 6, Pimp.y + Dd.y * 6, 1.4)); nb = bpy.context.active_object; nb.name = 'Niebla_baja'; nb.scale = (46, 46, 2.8)
mv = bpy.data.materials.new('Niebla_volumen'); mv.use_nodes = True; ntv = mv.node_tree; ntv.nodes.clear()
ov = ntv.nodes.new('ShaderNodeOutputMaterial'); vv = ntv.nodes.new('ShaderNodeVolumePrincipled'); vv.inputs['Density'].default_value = 0.012; vv.inputs['Color'].default_value = (0.7, 0.75, 0.85, 1); vv.inputs['Anisotropy'].default_value = 0.4
ntv.links.new(vv.outputs[0], ov.inputs['Volume']); nb.data.materials.append(mv)
for c in list(nb.users_collection): c.objects.unlink(nb)
col_fx.objects.link(nb); nb.display_type = 'BOUNDS'
print('suelo, humo y niebla listos')

# luz fría que acompaña a Gabriel cuando sale del auto (y un contraluz azul), para que se lo vea en la noche
g_fuera = bpy.data.objects['gabriel_fuera']
for nm, off, en, col, tam in (('Luz_G_frente', (1.6, -3.4, 3.2), 1600.0, (0.75, 0.85, 1.0), 85), ('Luz_G_contra', (-2.4, 3.0, 3.6), 900.0, (0.45, 0.6, 1.0), 80)):
    l = bpy.data.lights.new(nm, 'SPOT'); l.energy = en; l.color = col; l.spot_size = math.radians(tam); l.spot_blend = 0.8; l.shadow_soft_size = 0.8
    o = bpy.data.objects.new(nm, l); sc.collection.objects.link(o)
    cl = o.constraints.new('COPY_LOCATION'); cl.target = g_fuera; cl.use_offset = True
    o.location = off
    tr = o.constraints.new('TRACK_TO'); tr.target = g_fuera; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
