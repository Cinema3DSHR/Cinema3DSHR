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
        for df, e in ((0, 0.0), (1, 220.0), (8, 220.0), (9, 0.0)):
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
    out = N(nt, 'ShaderNodeOutputMaterial'); v = N(nt, 'ShaderNodeVolumeScatter'); v.inputs['Density'].default_value = 7.0; v.inputs['Color'].default_value = (0.85, 0.9, 1.0, 1)
    nt.links.new(v.outputs[0], out.inputs['Volume']); return m
def mat_rocio(op):
    m = bpy.data.materials.new('Rocio'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = N(nt, 'ShaderNodeOutputMaterial'); em = N(nt, 'ShaderNodeEmission'); tr = N(nt, 'ShaderNodeBsdfTransparent'); mx = N(nt, 'ShaderNodeMixShader')
    em.inputs['Color'].default_value = (0.8, 0.88, 1.0, 1); em.inputs['Strength'].default_value = 0.16; mx.inputs['Fac'].default_value = op
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0]); return m
O_GOTA = malla_obj('Gota_lluvia', m_gota, mat_lluvia())
O_ANILLO = malla_obj('Anillo_lluvia', m_anillo, mat_anillo())
O_ROCIO = malla_obj('Gota_rocio', m_esfera, mat_rocio(0.40)); O_NIEBLA = malla_obj('Niebla_rocio', m_esfera, mat_niebla())
for _o in (O_ROCIO, O_NIEBLA):
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
