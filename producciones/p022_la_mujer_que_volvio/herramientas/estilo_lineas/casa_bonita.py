"""CASITA BONITA (Blender): casa pequeña con ventanas de vidrio por donde entra el sol, mesa servida, muchas luces (pantalla, apliques, velas, guirnalda, faroles), jardín con césped, flores,
paisaje de colinas y pinos al fondo, garaje y auto parado. Escena hecha «como para renderizar tal cual»; después `efectos_pdf.py` le aplica los efectos de la guía de Extracción Vertical.
Uso: /opt/tools/blendenv/bin/python casa_bonita.py SALIDA.blend"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix
sys.path.insert(0, '/home/user/Cinema3DSHR/producciones/p022_la_mujer_que_volvio/herramientas/etapa_blender')
SALIDA = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else sys.argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
rng = random.Random(5)
W, H = 720, 1280

# ───────── materiales ─────────
def mat(nombre, col, rough=0.7, metal=0.0, **kw):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = metal
    for k, v in kw.items():
        try: bs.inputs[k.replace('_', ' ')].default_value = v
        except Exception: pass
    return m
def mat_ruido(nombre, c0, c1, escala=8.0, rough=0.8, bump=0.3):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = escala; ns.inputs['Detail'].default_value = 8.0
    nt.links.new(tc.outputs['Object'], ns.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (*c0, 1); rp.color_ramp.elements[1].color = (*c1, 1); nt.links.new(ns.outputs['Fac'], rp.inputs[0]); nt.links.new(rp.outputs[0], bs.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.02; nt.links.new(ns.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs[0], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = rough; return m
def mat_vidrio():
    m = bpy.data.materials.new('Vidrio'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); mx = nt.nodes.new('ShaderNodeMixShader'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); fr = nt.nodes.new('ShaderNodeFresnel')
    tr.inputs['Color'].default_value = (0.92, 0.97, 1.0, 1); gl.inputs['Roughness'].default_value = 0.02; fr.inputs['IOR'].default_value = 1.45
    nt.links.new(fr.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0]); return m
def mat_emision(nombre, col, fuerza):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = fuerza; nt.links.new(em.outputs[0], out.inputs[0]); return m
M = {'yeso': mat_ruido('Yeso', (0.80, 0.74, 0.62), (0.90, 0.85, 0.74), 14.0, 0.9, 0.15), 'yeso_int': mat('Yeso_int', (0.88, 0.82, 0.72), 0.9), 'techo': mat_ruido('Teja', (0.42, 0.17, 0.12), (0.58, 0.28, 0.18), 26.0, 0.7, 0.4),
     'madera': mat_ruido('Madera', (0.22, 0.12, 0.06), (0.42, 0.25, 0.12), 6.0, 0.55, 0.15), 'madera_clara': mat_ruido('Madera_clara', (0.55, 0.38, 0.2), (0.72, 0.52, 0.3), 5.0, 0.55, 0.1),
     'blanco': mat('Blanco', (0.93, 0.93, 0.9), 0.5), 'verde_post': mat('Postigo', (0.12, 0.38, 0.34), 0.6), 'cesped': mat_ruido('Cesped', (0.10, 0.28, 0.06), (0.22, 0.50, 0.12), 40.0, 0.9, 0.6),
     'grava': mat_ruido('Grava', (0.45, 0.42, 0.38), (0.72, 0.68, 0.6), 70.0, 0.95, 0.8), 'vidrio': mat_vidrio(), 'metal': mat('Metal', (0.55, 0.57, 0.6), 0.35, 1.0), 'garaje': mat('Garaje', (0.62, 0.66, 0.7), 0.5, 0.2),
     'piso': mat_ruido('Piso', (0.30, 0.17, 0.08), (0.48, 0.30, 0.16), 4.0, 0.4, 0.1), 'alfombra': mat('Alfombra', (0.55, 0.16, 0.14), 0.95), 'ceramica': mat('Ceramica', (0.95, 0.95, 0.92), 0.25),
     'hoja': mat('Hoja', (0.13, 0.42, 0.12), 0.7), 'tronco': mat('Tronco', (0.30, 0.20, 0.12), 0.9), 'copa': mat_ruido('Copa', (0.10, 0.34, 0.08), (0.25, 0.55, 0.14), 14.0, 0.8, 0.3),
     'luz_calida': mat_emision('Luz_calida', (1.0, 0.72, 0.38), 25.0), 'llama': mat_emision('Llama', (1.0, 0.55, 0.15), 40.0), 'guirnalda': mat_emision('Guirnalda', (1.0, 0.85, 0.55), 30.0), 'cuero': mat('Cuero', (0.35, 0.16, 0.1), 0.5)}
FLORES = [mat('Flor_rosa', (0.9, 0.25, 0.4), 0.5), mat('Flor_amarilla', (0.95, 0.78, 0.15), 0.5), mat('Flor_lila', (0.55, 0.4, 0.85), 0.5), mat('Flor_blanca', (0.95, 0.95, 0.92), 0.5), mat('Flor_naranja', (0.95, 0.5, 0.12), 0.5)]

# ───────── primitivas ─────────
def pon(o, m, clase):
    o.data.materials.clear(); o.data.materials.append(m); o['clase'] = clase; return o
def caja(nombre, c, tam, m, clase, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=c); o = bpy.context.active_object; o.name = nombre; o.scale = tam; o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True); return pon(o, m, clase)
def cil(nombre, c, r, alto, m, clase, rot=(0, 0, 0), seg=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=alto, vertices=seg, location=c, rotation=rot); o = bpy.context.active_object; o.name = nombre
    for p in o.data.polygons: p.use_smooth = True
    return pon(o, m, clase)
def esf(nombre, c, r, m, clase, esc=(1, 1, 1), seg=20):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2, location=c); o = bpy.context.active_object; o.name = nombre; o.scale = esc
    for p in o.data.polygons: p.use_smooth = True
    return pon(o, m, clase)
def luz(nombre, tipo, c, energia, color, radio=0.1, **kw):
    l = bpy.data.lights.new(nombre, tipo); l.energy = energia; l.color = color
    if tipo == 'POINT': l.shadow_soft_size = radio
    o = bpy.data.objects.new(nombre, l); sc.collection.objects.link(o); o.location = c; return o
def prisma(nombre, pts2d, y0, y1, m, clase):
    """Prisma extruido a lo largo de Y (frontón de la casa)."""
    bm = bmesh.new(); a = [bm.verts.new((x, y0, z)) for x, z in pts2d]; b = [bm.verts.new((x, y1, z)) for x, z in pts2d]
    bm.faces.new(a[::-1]); bm.faces.new(b)
    for i in range(len(pts2d)): bm.faces.new((a[i], a[(i + 1) % len(a)], b[(i + 1) % len(a)], b[i]))
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(nombre, me); sc.collection.objects.link(o); return pon(o, m, clase)

# ───────── suelo, camino, colinas ─────────
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 20, 0)); g = bpy.context.active_object; g.name = 'Suelo_cesped'; pon(g, M['cesped'], 'suelo')
caja('Camino', (0, -5.2, 0.01), (1.3, 7.2, 0.02), M['grava'], 'suelo'); caja('Camino_entrada', (0, -2.6, 0.012), (1.8, 1.0, 0.02), M['grava'], 'suelo')
for i in range(3):                                                                              # colinas lejanas (mallas desplazadas)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=90, y_subdivisions=60, size=1.0, location=(rng.uniform(-14, 14), 34 + i * 20, 0)); h = bpy.context.active_object; h.name = f'Colina_{i}'; h.scale = (70, 30, 1)
    bpy.ops.object.transform_apply(scale=True)
    for v in h.data.vertices:
        d = abs(v.co.x) / 35.0; v.co.z = max(0.0, (7.0 + 5 * i) * math.exp(-(v.co.x / (14 + 3 * i)) ** 2) * (1 - (v.co.y / 30.0) ** 2) * 0.5 + 1.5 * math.sin(v.co.x * 0.3 + i)) * (0.55 + 0.45 * math.cos(v.co.y * 0.1))
    pon(h, M['cesped'], 'suelo')
    for p in h.data.polygons: p.use_smooth = True

# ───────── la casa ─────────
ANCHO, PROF, ALTO, E = 4.8, 4.0, 2.6, 0.16
frente = [(-2.4, -1.9, 0, 2.6), (-1.9, -1.0, 0, 0.9), (-1.9, -1.0, 2.0, 2.6), (-1.0, -0.475, 0, 2.6), (-0.475, 0.475, 2.0, 2.6), (0.475, 1.0, 0, 2.6), (1.0, 1.9, 0, 0.9), (1.0, 1.9, 2.0, 2.6), (1.9, 2.4, 0, 2.6)]
for i, (x0, x1, z0, z1) in enumerate(frente):
    caja(f'Casa_frente_{i}', ((x0 + x1) / 2, -PROF / 2, (z0 + z1) / 2), (x1 - x0, E, z1 - z0), M['yeso'], 'casa')
caja('Casa_fondo', (0, PROF / 2, ALTO / 2), (ANCHO, E, ALTO), M['yeso'], 'casa')
caja('Casa_lado_izq', (-ANCHO / 2, 0, ALTO / 2), (E, PROF, ALTO), M['yeso'], 'casa'); caja('Casa_lado_der', (ANCHO / 2, 0, ALTO / 2), (E, PROF, ALTO), M['yeso'], 'casa')
caja('Casa_zocalo', (0, -PROF / 2 - 0.02, 0.18), (ANCHO + 0.1, 0.05, 0.36), M['grava'], 'casa')
caja('Piso_interior', (0, 0, 0.04), (ANCHO - 0.1, PROF - 0.1, 0.08), M['piso'], 'casa'); caja('Techo_interior', (0, 0, ALTO + 0.05), (ANCHO, PROF, 0.1), M['yeso_int'], 'casa')
for lado in (-1, 1):                                                                              # techo a dos aguas con alero
    caja('Techo_agua_%s' % ('L' if lado < 0 else 'R'), (lado * 1.35, 0, ALTO + 0.72), (3.0, PROF + 0.9, 0.12), M['techo'], 'casa', (0, math.radians(-lado * 28), 0))
prisma('Frontón_frente', [(-2.4, ALTO + 0.1), (2.4, ALTO + 0.1), (0, ALTO + 1.45)], -PROF / 2, -PROF / 2 + E, M['yeso'], 'casa'); prisma('Frontón_fondo', [(-2.4, ALTO + 0.1), (2.4, ALTO + 0.1), (0, ALTO + 1.45)], PROF / 2 - E, PROF / 2, M['yeso'], 'casa')
caja('Chimenea', (1.5, 0.6, ALTO + 1.5), (0.5, 0.5, 1.1), M['techo'], 'casa'); caja('Chimenea_tapa', (1.5, 0.6, ALTO + 2.08), (0.62, 0.62, 0.08), M['grava'], 'casa')
# puerta, ventanas, postigos, canteros
caja('Puerta', (0, -PROF / 2 + 0.01, 1.0), (0.92, 0.07, 2.0), M['madera'], 'casa'); caja('Puerta_vidrio', (0, -PROF / 2 - 0.03, 1.45), (0.5, 0.02, 0.6), M['vidrio'], 'vidrio')
caja('Puerta_marco', (0, -PROF / 2 - 0.02, 2.04), (1.1, 0.12, 0.1), M['blanco'], 'casa'); esf('Puerta_picaporte', (0.34, -PROF / 2 - 0.06, 1.0), 0.035, M['metal'], 'obj')
caja('Escalon', (0, -PROF / 2 - 0.45, 0.08), (1.5, 0.7, 0.16), M['grava'], 'casa'); caja('Escalon_2', (0, -PROF / 2 - 0.9, 0.04), (1.7, 0.4, 0.08), M['grava'], 'casa')
for sx in (-1, 1):
    cx = sx * 1.45
    caja(f'Ventana_vidrio_{sx}', (cx, -PROF / 2, 1.45), (0.9, 0.02, 1.1), M['vidrio'], 'vidrio')
    for nm, c, t in (('arriba', (cx, 2.0 + 0.0, 0), (1.06, 0.1, 0.08)), ('abajo', (cx, 0.9, 0), (1.06, 0.14, 0.07)), ('izq', (cx - 0.49, 1.45, 0), (0.07, 0.1, 1.16)), ('der', (cx + 0.49, 1.45, 0), (0.07, 0.1, 1.16)), ('cruz_v', (cx, 1.45, 0), (0.04, 0.06, 1.1)), ('cruz_h', (cx, 1.45, 0), (0.9, 0.06, 0.04))):
        z = c[1] if nm in ('arriba', 'abajo') else c[1]
        zc = 2.0 if nm == 'arriba' else 0.9 if nm == 'abajo' else 1.45
        caja(f'Ventana_marco_{sx}_{nm}', (c[0], -PROF / 2 - 0.04, zc), t if nm in ('arriba', 'abajo') else ((t[0], t[1], t[2]) ), M['blanco'], 'casa')
    caja(f'Postigo_{sx}_a', (cx - 0.68 * 1.0, -PROF / 2 - 0.05, 1.45), (0.42, 0.04, 1.14), M['verde_post'], 'casa'); caja(f'Postigo_{sx}_b', (cx + 0.68, -PROF / 2 - 0.05, 1.45), (0.42, 0.04, 1.14), M['verde_post'], 'casa')
    caja(f'Cantero_{sx}', (cx, -PROF / 2 - 0.28, 0.72), (1.1, 0.26, 0.2), M['madera_clara'], 'obj')
    for k in range(9):                                                                              # flores del cantero
        fx = cx - 0.45 + 0.11 * k; zt = 0.86
        cil(f'Cantero_tallo_{sx}_{k}', (fx, -PROF / 2 - 0.28 + rng.uniform(-0.05, 0.05), zt + 0.1), 0.006, 0.2, M['hoja'], 'veg', seg=6)
        esf(f'Cantero_flor_{sx}_{k}', (fx, -PROF / 2 - 0.28, zt + 0.22), 0.055, FLORES[(k + sx) % 5], 'veg', (1, 1, 0.6), 10)
# interior: mesa servida, sillas, alfombra, estante, lámparas
caja('Alfombra', (-0.1, 0.2, 0.09), (2.2, 1.6, 0.02), M['alfombra'], 'obj')
caja('Mesa_tapa', (-0.1, 0.2, 0.76), (1.3, 0.8, 0.05), M['madera_clara'], 'obj')
for dx in (-0.58, 0.58):
    for dy in (-0.33, 0.33): caja('Mesa_pata', (-0.1 + dx, 0.2 + dy, 0.37), (0.06, 0.06, 0.74), M['madera'], 'obj')
for k, (cx, cy, rz) in enumerate(((-0.1, -0.5, 0.0), (-0.1, 0.9, math.pi))):
    caja(f'Silla_asiento_{k}', (cx, cy, 0.46), (0.42, 0.42, 0.05), M['madera'], 'obj', (0, 0, rz)); caja(f'Silla_respaldo_{k}', (cx, cy + (0.2 if k == 0 else -0.2) * -1 * 1, 0.8), (0.42, 0.04, 0.5), M['madera'], 'obj')
    for dx in (-0.18, 0.18):
        for dy in (-0.18, 0.18): caja(f'Silla_pata_{k}', (cx + dx, cy + dy, 0.22), (0.04, 0.04, 0.44), M['madera'], 'obj')
cil('Mesa_florero', (-0.1, 0.2, 0.9), 0.07, 0.24, M['ceramica'], 'obj'); 
for k in range(7): 
    a = k / 7 * math.tau; esf(f'Florero_flor_{k}', (-0.1 + 0.07 * math.cos(a), 0.2 + 0.07 * math.sin(a), 1.08 + 0.04 * (k % 2)), 0.05, FLORES[k % 5], 'veg', (1, 1, 0.6), 10)
cil('Mesa_tetera', (0.22, 0.05, 0.84), 0.07, 0.12, M['ceramica'], 'obj'); cil('Mesa_taza_1', (-0.4, 0.0, 0.81), 0.04, 0.07, M['ceramica'], 'obj'); cil('Mesa_taza_2', (-0.4, 0.42, 0.81), 0.04, 0.07, M['ceramica'], 'obj')
cil('Mesa_plato_1', (-0.1, -0.1, 0.79), 0.12, 0.015, M['ceramica'], 'obj'); cil('Mesa_plato_2', (-0.1, 0.5, 0.79), 0.12, 0.015, M['ceramica'], 'obj')
cil('Vela', (0.35, 0.4, 0.84), 0.02, 0.1, M['blanco'], 'obj'); esf('Vela_llama', (0.35, 0.4, 0.92), 0.018, M['llama'], 'luz', (1, 1, 1.6), 8)
caja('Estante', (-1.8, 1.7, 1.5), (0.7, 0.28, 0.05), M['madera'], 'obj'); caja('Estante_2', (-1.8, 1.7, 1.05), (0.7, 0.28, 0.05), M['madera'], 'obj')
for k, c in enumerate((0.08, 0.1, 0.07, 0.09)): caja(f'Libro_{k}', (-2.0 + 0.1 * k, 1.7, 1.55 + c / 2), (0.07, 0.2, c), mat(f'Libro_{k}', [(0.6, 0.15, 0.15), (0.15, 0.3, 0.5), (0.7, 0.6, 0.2), (0.2, 0.45, 0.3)][k], 0.6), 'obj')
cil('Pantalla_colgante', (-0.1, 0.2, 2.05), 0.22, 0.2, M['luz_calida'], 'luz'); cil('Pantalla_cable', (-0.1, 0.2, 2.35), 0.008, 0.5, M['metal'], 'obj')
cil('Lampara_pie_poste', (1.9, 1.3, 0.7), 0.02, 1.4, M['metal'], 'obj'); cil('Lampara_pie_pantalla', (1.9, 1.3, 1.5), 0.16, 0.26, M['luz_calida'], 'luz'); cil('Lampara_pie_base', (1.9, 1.3, 0.03), 0.12, 0.05, M['metal'], 'obj')
for sx in (-1, 1):
    caja(f'Aplique_{sx}', (sx * 1.6, PROF / 2 - 0.12, 1.9), (0.1, 0.1, 0.16), M['luz_calida'], 'luz')
caja('Cuadro', (0.6, PROF / 2 - 0.1, 1.6), (0.8, 0.03, 0.6), M['blanco'], 'obj'); caja('Cuadro_tela', (0.6, PROF / 2 - 0.12, 1.6), (0.68, 0.02, 0.48), mat('Cuadro_pintura', (0.2, 0.45, 0.6), 0.8), 'obj')
# fuera: farol del porche, guirnalda, faroles de jardín
cil('Farol_porche', (0.8, -PROF / 2 - 0.12, 1.75), 0.06, 0.18, M['luz_calida'], 'luz'); caja('Farol_porche_soporte', (0.8, -PROF / 2 - 0.05, 1.9), (0.02, 0.1, 0.02), M['metal'], 'obj')
for k in range(13):
    x = -2.3 + 4.6 * k / 12; z = 2.5 - 0.1 * math.sin(math.pi * k / 12 * 1.0) * 1.0
    esf(f'Guirnalda_{k}', (x, -PROF / 2 - 0.5, 2.36 - 0.14 * math.sin(math.pi * (k % 6) / 6)), 0.035, M['guirnalda'], 'luz', seg=8)
for k, (x, y) in enumerate(((-1.3, -5.4), (1.3, -5.4), (-1.3, -8.0), (1.3, -8.0))):
    cil(f'Farol_jardin_{k}', (x, y, 0.25), 0.02, 0.5, M['metal'], 'obj', seg=8); esf(f'Farol_jardin_luz_{k}', (x, y, 0.55), 0.06, M['guirnalda'], 'luz', seg=10)
# garaje y auto
GX, GY = 5.7, 1.2
caja('Garaje_paredes', (GX, GY, 1.2), (3.4, 4.2, 2.4), M['garaje'], 'garaje'); caja('Garaje_techo', (GX, GY, 2.5), (3.7, 4.5, 0.15), M['techo'], 'garaje')
caja('Garaje_portón', (GX - 0.1, GY - 2.12, 1.05), (2.5, 0.06, 2.1), M['metal'], 'garaje')
for k in range(7): caja(f'Garaje_portón_nervio_{k}', (GX - 0.1, GY - 2.17, 0.15 + 0.3 * k), (2.5, 0.03, 0.04), M['garaje'], 'garaje')
caja('Garaje_marco', (GX - 0.1, GY - 2.14, 2.15), (2.7, 0.1, 0.1), M['blanco'], 'garaje')
caja('Garaje_ventana', (GX + 1.72, GY - 0.8, 1.4), (0.04, 0.8, 0.6), M['vidrio'], 'vidrio'); caja('Garaje_cartel', (GX - 0.1, GY - 2.2, 2.32), (0.8, 0.03, 0.14), M['verde_post'], 'garaje')
bpy.ops.import_scene.gltf(filepath='/home/user/Cinema3DSHR/producciones/p022_la_mujer_que_volvio/godot_cap1/assets/hustler.glb')
car = [o for o in bpy.data.objects if o.type == 'MESH' and 'clase' not in o.keys()]
padre = bpy.data.objects.new('Auto', None); sc.collection.objects.link(padre)
for o in list(bpy.data.objects):
    if o.parent is None and o not in car and o.name not in ('Auto',) and o.type in ('EMPTY',) and 'clase' not in o.keys() and o.name.lower().startswith(('sketchfab', 'root', 'auto', 'hustler')): pass
roots = [o for o in bpy.data.objects if o.parent is None and ('clase' not in o.keys()) and o.name != 'Auto' and o.type in ('EMPTY', 'MESH') and (o in car or o.type == 'EMPTY')]
for o in roots: o.parent = padre
padre.location = (-1.8, -4.4, 0.75); padre.rotation_euler = (0, 0, math.radians(18))
for o in car: o['clase'] = 'auto'
# ───────── vegetación ─────────
import assets_reales as AR
variantes = [AR.pino(f'Pino_{i}', alto, 300 + i) for i, alto in enumerate((7.0, 9.0, 11.0, 8.0))]
col_arb = bpy.data.collections.new('Arboles'); sc.collection.children.link(col_arb)
for i in range(34):
    o = bpy.data.objects.new(f'Pinar_{i}', variantes[i % 4]); col_arb.objects.link(o)
    o.location = (rng.uniform(-34, 34), rng.uniform(9.0, 42.0), 0); o.rotation_euler = (0, 0, rng.uniform(0, 6.28)); s = rng.uniform(0.85, 1.4); o.scale = (s, s, s); o['clase'] = 'veg'
for k, (x, y, h) in enumerate(((-4.6, -0.5, 3.8), (4.2, -3.2, 3.2), (-5.4, 4.0, 4.4), (1.8, 7.0, 4.6))):                    # árboles de hoja ancha junto a la casa
    cil(f'Arbol_tronco_{k}', (x, y, h * 0.3), 0.13, h * 0.6, M['tronco'], 'veg', seg=10)
    for j, (dx, dy, dz, r) in enumerate(((0, 0, 0.78, 0.34), (0.42, 0.1, 0.62, 0.24), (-0.4, -0.1, 0.66, 0.26), (0.05, 0.38, 0.62, 0.22))):
        esf(f'Arbol_copa_{k}_{j}', (x + dx * h * 0.45, y + dy * h * 0.45, h * dz), h * r, M['copa'], 'veg', seg=14)
for k in range(26):                                                                                   # arbustos y matas
    x = rng.uniform(-9, 9); y = rng.uniform(-9, 6)
    if abs(x) < 3.0 and -9.5 < y < -2: continue
    if (x > 3.5 and y > -1.5) or (abs(x - (-1.8)) < 1.6 and abs(y + 4.4) < 2.6): continue
    esf(f'Arbusto_{k}', (x, y, 0.28), rng.uniform(0.35, 0.7), M['copa'], 'veg', (1, 1, 0.7), 12)
# macizo de flores en primer plano (izquierda) y a lo largo del camino
for k in range(90):
    x = rng.choice((-1, 1)) * rng.uniform(1.0, 3.6); y = rng.uniform(-9.0, -5.0)
    h = rng.uniform(0.25, 0.5)
    cil(f'Flor_tallo_{k}', (x, y, h / 2), 0.006, h, M['hoja'], 'veg', seg=6)
    esf(f'Flor_{k}', (x, y, h), rng.uniform(0.04, 0.065), FLORES[k % 5], 'veg', (1, 1, 0.55), 10)
for k in range(14):                                                                                   # piedras del camino
    esf(f'Piedra_{k}', (rng.uniform(-0.9, 0.9) + (0.7 if k % 2 else -0.7), rng.uniform(-9.5, -3.2), 0.05), rng.uniform(0.1, 0.22), M['grava'], 'suelo', (1, 1, 0.55), 10)
for k in range(30):                                                                                   # valla baja de madera
    caja(f'Valla_poste_{k}', (-6.2 + 0.4 * k, -10.0, 0.4), (0.07, 0.07, 0.8), M['blanco'], 'obj') if abs(-6.2 + 0.4 * k) > 0.9 else None
caja('Valla_riel_1', (-3.8, -10.0, 0.62), (5.0, 0.04, 0.06), M['blanco'], 'obj'); caja('Valla_riel_2', (3.8, -10.0, 0.62), (5.0, 0.04, 0.06), M['blanco'], 'obj')

# ───────── luces ─────────
sol = bpy.data.lights.new('Sol', 'SUN'); sol.energy = 5.0; sol.color = (1.0, 0.86, 0.68); sol.angle = math.radians(1.6)
so = bpy.data.objects.new('Sol', sol); sc.collection.objects.link(so); dirsol = -Vector((3.6, -5.6, 3.2)).normalized(); so.rotation_euler = dirsol.to_track_quat('-Z', 'Y').to_euler()
luz('Luz_pantalla', 'POINT', (-0.1, 0.2, 1.95), 90, (1.0, 0.7, 0.4), 0.2); luz('Luz_pie', 'POINT', (1.9, 1.3, 1.45), 35, (1.0, 0.72, 0.42), 0.15)
for sx in (-1, 1): luz(f'Luz_aplique_{sx}', 'POINT', (sx * 1.6, 1.9, 1.88), 18, (1.0, 0.75, 0.45), 0.08)
luz('Luz_vela', 'POINT', (0.35, 0.4, 0.95), 4, (1.0, 0.55, 0.2), 0.02); luz('Luz_porche', 'POINT', (0.8, -2.2, 1.7), 25, (1.0, 0.75, 0.42), 0.08)
for k in range(0, 13, 3): luz(f'Luz_guirnalda_{k}', 'POINT', (-2.3 + 4.6 * k / 12, -2.5, 2.3), 8, (1.0, 0.85, 0.55), 0.05)
for k, (x, y) in enumerate(((-1.3, -5.4), (1.3, -5.4), (-1.3, -8.0), (1.3, -8.0))): luz(f'Luz_farol_{k}', 'POINT', (x, y, 0.6), 6, (1.0, 0.85, 0.55), 0.06)
luz('Luz_relleno_interior', 'POINT', (0, 0.4, 2.3), 12, (1.0, 0.85, 0.7), 0.3)
w = bpy.data.worlds.new('Cielo'); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); sk = nt.nodes.new('ShaderNodeTexSky'); sk.sky_type = 'MULTIPLE_SCATTERING'; sk.sun_disc = False; sk.sun_elevation = math.radians(30); sk.sun_rotation = math.radians(-30); sk.air_density = 1.0
nt.links.new(sk.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.9; nt.links.new(bg.outputs[0], out.inputs[0]); sc.world = w
# bruma suave alrededor de la casa: los rayos de sol se ven entrar por las ventanas
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.6, -1.0, 2.5)); bz = bpy.context.active_object; bz.name = 'Bruma'; bz.scale = (13.0, 11.0, 5.0); bz['clase'] = 'bruma'
mb = bpy.data.materials.new('Bruma'); mb.use_nodes = True; ntb = mb.node_tree; ntb.nodes.clear(); ob = ntb.nodes.new('ShaderNodeOutputMaterial'); vb = ntb.nodes.new('ShaderNodeVolumePrincipled'); vb.inputs['Density'].default_value = 0.012; vb.inputs['Anisotropy'].default_value = 0.5
ntb.links.new(vb.outputs[0], ob.inputs['Volume']); bz.data.materials.append(mb)
# cámara (vertical 720×1280)
cam = bpy.data.cameras.new('Camara'); cam.lens_unit = 'FOV'; cam.sensor_fit = 'VERTICAL'; cam.angle_y = math.radians(46); co = bpy.data.objects.new('Camara', cam); sc.collection.objects.link(co)
co.location = (2.7, -15.2, 2.3); co.rotation_euler = (Vector((0.0, 0.0, 1.9)) - co.location).to_track_quat('-Z', 'Y').to_euler(); sc.camera = co
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
cy = sc.cycles; cy.device = 'CPU'; cy.samples = 16; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.max_bounces = 5; cy.volume_bounces = 1; cy.transparent_max_bounces = 12
if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
cy.seed = 21
sc.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items] else 'Standard'; sc.view_settings.exposure = 0.2
bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
print('GUARDADO', SALIDA, 'objetos', len(bpy.data.objects))
