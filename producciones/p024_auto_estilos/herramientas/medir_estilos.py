"""MEDICIÓN POR ESTILO (aparte del render): cuánto cuesta REALMENTE cada video si se renderiza solo, con las pasadas que ese estilo necesita.
Original: color 32 muestras. C: normales+profundidad+clases (1 muestra, sin color). D: color 8 muestras (los 4 tonos) + profundidad + clases. E: arcilla 8 muestras + normales + profundidad + clases.
Híbrido: color 12 muestras + arcilla 8 + profundidad + clases. Mide render por pasada en 5 cuadros repartidos, memoria y CPU; la composición se mide aparte.
Uso: python medir_estilos.py BLEND SALIDA.json"""
import bpy, sys, time, json, os, resource, platform
BLEND, SAL = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=BLEND); sc = bpy.context.scene; r = sc.render
meshes = [o for o in bpy.data.objects if o.type == 'MESH']; orig = {o.name: list(o.data.materials) for o in meshes}
def cycles(spp, filtro=1.5, den=True, reb=6):
    cy = sc.cycles; cy.samples = spp; cy.use_adaptive_sampling = spp > 2; cy.use_denoising = den; cy.max_bounces = reb; cy.filter_width = filtro
def hora(nombre, f, T):
    sc.frame_set(f); r.filepath = f'/tmp/med_{nombre}_{f}.png'; t = time.time(); bpy.ops.render.render(write_still=True); T.setdefault(nombre, []).append(round(time.time() - t, 2))
def mat(tipo):
    m = bpy.data.materials.new(tipo); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial')
    if tipo == 'arcilla':
        bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.inputs['Roughness'].default_value = 1.0; nt.links.new(bs.outputs[0], out.inputs[0]); return m
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], out.inputs[0])
    if tipo == 'normal':
        g = nt.nodes.new('ShaderNodeNewGeometry'); nt.links.new(g.outputs['Normal'], em.inputs['Color'])
    elif tipo == 'prof':
        cd = nt.nodes.new('ShaderNodeCameraData'); nt.links.new(cd.outputs['View Z Depth'], em.inputs['Color'])
    else: em.inputs['Color'].default_value = (1, 0, 0, 1)
    return m
def poner(m):
    for o in meshes: o.data.materials.clear(); o.data.materials.append(m)
def restaurar():
    for o in meshes:
        o.data.materials.clear()
        for m in orig[o.name]: o.data.materials.append(m)
FR = [1, 40, 75, 110, 150]; T = {}
for spp in (32, 12, 8):
    cycles(spp)
    for f in FR: hora(f'color_{spp}', f, T)
cycles(8, 1.5, True, 3); poner(mat('arcilla'))
for f in FR: hora('arcilla_8', f, T)
sc.camera.data.dof.use_dof = False; cycles(1, 1.0, False, 0)
for nm in ('normal', 'prof', 'clases'):
    poner(mat(nm))
    for f in FR: hora(nm, f, T)
M = lambda k: round(sum(T[k]) / len(T[k]), 2)
cuadro = {
    'original': M('color_32'),
    'C_contorno': M('normal') + M('prof') + M('clases'),
    'D_lineas_pantalla': M('color_8') + M('prof') + M('clases'),
    'E_combinado': M('arcilla_8') + M('normal') + M('prof') + M('clases'),
    'hibrido_lapices': M('color_12') + M('arcilla_8') + M('prof') + M('clases')}
json.dump({'pasadas_s_por_cuadro': {k: M(k) for k in T}, 'render_s_por_cuadro_por_estilo': {k: round(v, 2) for k, v in cuadro.items()}, 'memoria_pico_mb': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
          'cpus': os.cpu_count(), 'maquina': platform.processor() or platform.machine()}, open(SAL, 'w'), indent=1)
print(json.dumps({k: round(v, 1) for k, v in cuadro.items()}))
