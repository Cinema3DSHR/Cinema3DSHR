# Utilidades de nodos y materiales (se ejecuta con exec() dentro de efectos_*.py: comparte bpy, math, sc, col_fx…)
def principled(m):
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.use_nodes else None
def reconstruir(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0]); return nt, bs, out
def entrada(bs, *nombres):
    for n in nombres:
        if n in bs.inputs: return bs.inputs[n]
    raise KeyError(nombres)
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
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    col_fx.objects.link(o); return o
def objeto_gn(nombre, grupo, padre=None):
    me = bpy.data.meshes.new(nombre); o = bpy.data.objects.new(nombre, me); col_fx.objects.link(o)
    md = o.modifiers.new('GN', 'NODES'); md.node_group = grupo
    if padre is not None: o.parent = padre
    return o
import bmesh
def m_esfera(me):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0); bm.to_mesh(me); bm.free()
def m_gota(me):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(0.0035, 0.0035, 0.42), verts=bm.verts); bm.to_mesh(me); bm.free()
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
