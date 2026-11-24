# Efectos y materiales de LA CASA. Se ejecuta con exec() desde construir_casa.py (comparte bpy, sc, JS, EV, FPS, TOTAL, gb…).
import bpy, math, random, os, sys
from mathutils import Vector
col_fx = bpy.data.collections.new('Efectos'); sc.collection.children.link(col_fx)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
exec(open(os.path.join(HERE, 'util_nodos.py')).read())
rng_c = random.Random(31)
mesa_c = EV['mesa_centro']; MY = EV['mesa_altura']
def mk(nombre):
    m = bpy.data.materials.new(nombre); nt, bs, out = reconstruir(m); return m, nt, bs, out
def tex(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        try:
            if k.startswith('i_'): n.inputs[k[2:].replace('_', ' ')].default_value = v
            else: setattr(n, k, v)
        except Exception as e_:
            print('AVISO tex', tipo, k, '->', [i_.name for i_ in n.inputs][:14] if k.startswith('i_') else e_)
    return n
def L(nt, a, b): nt.links.new(a, b)
def bump_(nt, bs, altura_socket, fuerza, dist=0.02):
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = fuerza; bp.inputs['Distance'].default_value = dist
    L(nt, altura_socket, bp.inputs['Height']); L(nt, bp.outputs[0], bs.inputs['Normal']); return bp

# ───────────────────────── materiales ─────────────────────────
def mat_piso():
    m, nt, bs, out = mk('Piso_madera'); tc = tex(nt, 'ShaderNodeTexCoord')
    br = tex(nt, 'ShaderNodeTexBrick', i_Scale=1.0, i_Mortar_Size=0.004, i_Bias=0.0, i_Brick_Width=1.4, i_Row_Height=0.14, offset=0.5, offset_frequency=2, squash=1.0, squash_frequency=2)
    br.inputs['Color1'].default_value = (0.30, 0.285, 0.26, 1); br.inputs['Color2'].default_value = (0.43, 0.405, 0.37, 1); br.inputs['Mortar'].default_value = (0.05, 0.045, 0.04, 1)
    L(nt, tc.outputs['Object'], br.inputs['Vector'])
    ve = tex(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', i_Scale=22.0, i_Distortion=4.0, i_Detail=3.0); L(nt, tc.outputs['Object'], ve.inputs['Vector'])
    mx = tex(nt, 'ShaderNodeMix', data_type='RGBA'); mx.inputs['Factor'].default_value = 0.35; L(nt, br.outputs['Color'], [x for x in mx.inputs if x.name == 'A' and x.type == 'RGBA'][0]); L(nt, ve.outputs['Color'], [x for x in mx.inputs if x.name == 'B' and x.type == 'RGBA'][0])
    L(nt, mx.outputs['Result'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.28
    entrada(bs, 'Coat Weight', 'Clearcoat').default_value = 0.45; entrada(bs, 'Coat Roughness', 'Clearcoat Roughness').default_value = 0.08
    bump_(nt, bs, br.outputs['Fac'], 0.4, 0.004); return m
def mat_pared():
    m, nt, bs, out = mk('Pared'); tc = tex(nt, 'ShaderNodeTexCoord'); ns = tex(nt, 'ShaderNodeTexNoise', i_Scale=4.0, i_Detail=8.0); L(nt, tc.outputs['Object'], ns.inputs['Vector'])
    rp = tex(nt, 'ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (0.10, 0.075, 0.055, 1); rp.color_ramp.elements[1].color = (0.20, 0.155, 0.12, 1); L(nt, ns.outputs['Fac'], rp.inputs[0]); L(nt, rp.outputs[0], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.85; bump_(nt, bs, ns.outputs['Fac'], 0.25, 0.01); return m
def mat_techo():
    m, nt, bs, out = mk('Techo'); bs.inputs['Base Color'].default_value = (0.20, 0.19, 0.18, 1); bs.inputs['Roughness'].default_value = 0.9; return m
def mat_madera(nombre='Madera', col1=(0.025, 0.012, 0.006), col2=(0.11, 0.055, 0.026), rough=0.30):
    m, nt, bs, out = mk(nombre); tc = tex(nt, 'ShaderNodeTexCoord')
    ve = tex(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', i_Scale=7.0, i_Distortion=3.5, i_Detail=5.0, i_Detail_Scale=1.5); L(nt, tc.outputs['Object'], ve.inputs['Vector'])
    rp = tex(nt, 'ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (*col1, 1); rp.color_ramp.elements[1].color = (*col2, 1); L(nt, ve.outputs['Fac'], rp.inputs[0]); L(nt, rp.outputs[0], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = rough; entrada(bs, 'Coat Weight', 'Clearcoat').default_value = 0.35; entrada(bs, 'Coat Roughness', 'Clearcoat Roughness').default_value = 0.1
    bump_(nt, bs, ve.outputs['Fac'], 0.15, 0.004); return m
def mat_terciopelo(nombre='Tela', col=(0.16, 0.025, 0.03)):
    m, nt, bs, out = mk(nombre); tc = tex(nt, 'ShaderNodeTexCoord'); ns = tex(nt, 'ShaderNodeTexNoise', i_Scale=420.0, i_Detail=2.0); L(nt, tc.outputs['Object'], ns.inputs['Vector'])
    bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = 0.88
    entrada(bs, 'Sheen Weight', 'Sheen').default_value = 1.0; entrada(bs, 'Sheen Roughness').default_value = 0.35; entrada(bs, 'Sheen Tint').default_value = (0.8, 0.35, 0.35, 1)
    bump_(nt, bs, ns.outputs['Fac'], 0.3, 0.003); return m
def mat_alfombra():
    m, nt, bs, out = mk('Alfombra'); tc = tex(nt, 'ShaderNodeTexCoord'); ch = tex(nt, 'ShaderNodeTexChecker', i_Scale=14.0); L(nt, tc.outputs['Object'], ch.inputs['Vector'])
    ch.inputs['Color1'].default_value = (0.13, 0.025, 0.03, 1); ch.inputs['Color2'].default_value = (0.045, 0.02, 0.02, 1)
    ns = tex(nt, 'ShaderNodeTexNoise', i_Scale=300.0); L(nt, tc.outputs['Object'], ns.inputs['Vector'])
    L(nt, ch.outputs['Color'], bs.inputs['Base Color']); bs.inputs['Roughness'].default_value = 0.95; bump_(nt, bs, ns.outputs['Fac'], 0.5, 0.004); return m
def mat_cortina():
    m, nt, bs, out = mk('Cortina'); tc = tex(nt, 'ShaderNodeTexCoord'); wv = tex(nt, 'ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', i_Scale=26.0, i_Distortion=0.6); L(nt, tc.outputs['Object'], wv.inputs['Vector'])
    bs.inputs['Base Color'].default_value = (0.075, 0.012, 0.018, 1); bs.inputs['Roughness'].default_value = 0.92; entrada(bs, 'Transmission Weight', 'Transmission').default_value = 0.10
    entrada(bs, 'Sheen Weight', 'Sheen').default_value = 0.25; entrada(bs, 'Sheen Tint').default_value = (0.25, 0.06, 0.06, 1); bump_(nt, bs, wv.outputs['Fac'], 0.35, 0.004); return m
def mat_vidrio(nombre='Vidrio', col=(0.9, 0.95, 1.0), ior=1.5, rough=0.01, trans=1.0):
    m, nt, bs, out = mk(nombre); bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = rough
    entrada(bs, 'Transmission Weight', 'Transmission').default_value = trans; entrada(bs, 'IOR').default_value = ior; return m
def mat_ventana():
    m, nt, bs, out = mk('Vidrio_ventana'); tc = tex(nt, 'ShaderNodeTexCoord')
    bs.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1); bs.inputs['Roughness'].default_value = 0.04; entrada(bs, 'Transmission Weight', 'Transmission').default_value = 1.0; entrada(bs, 'IOR').default_value = 1.45
    mp = tex(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (40.0, 40.0, 3.0); L(nt, tc.outputs['Object'], mp.inputs[0])       # gotas y chorros que bajan por el vidrio
    d = mp.inputs['Location'].driver_add('default_value', 2); d.driver.type = 'SCRIPTED'; d.driver.expression = '-frame * 0.012'
    vo = tex(nt, 'ShaderNodeTexVoronoi', i_Scale=1.0, i_Smoothness=0.4, feature='F1'); L(nt, mp.outputs[0], vo.inputs['Vector'])
    mr = tex(nt, 'ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.35; mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0; L(nt, vo.outputs['Distance'], mr.inputs['Value'])
    ns = tex(nt, 'ShaderNodeTexNoise', i_Scale=12.0, i_Detail=4.0); L(nt, mp.outputs[0], ns.inputs['Vector'])
    ad = tex(nt, 'ShaderNodeMath', operation='ADD'); L(nt, mr.outputs[0], ad.inputs[0]); L(nt, ns.outputs['Fac'], ad.inputs[1]); bump_(nt, bs, ad.outputs[0], 0.5, 0.01); return m
def mat_papel(nombre, col): 
    m, nt, bs, out = mk(nombre); bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = 0.8; return m
def mat_metal(nombre, col, rough=0.3, met=1.0):
    m, nt, bs, out = mk(nombre); bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = met; return m
def mat_vino_charco():
    m, nt, bs, out = mk('Vino_derramado'); bs.inputs['Base Color'].default_value = (0.20, 0.0, 0.008, 1); bs.inputs['Roughness'].default_value = 0.025
    entrada(bs, 'Coat Weight', 'Clearcoat').default_value = 1.0; entrada(bs, 'Coat Roughness', 'Clearcoat Roughness').default_value = 0.02; return m
def mat_vino_copa():
    m, nt, bs, out = mk('Vino_copa'); bs.inputs['Base Color'].default_value = (0.28, 0.004, 0.018, 1); bs.inputs['Roughness'].default_value = 0.02; entrada(bs, 'Transmission Weight', 'Transmission').default_value = 0.85; entrada(bs, 'IOR').default_value = 1.34; return m
def mat_whisky():
    m, nt, bs, out = mk('Whisky'); bs.inputs['Base Color'].default_value = (0.50, 0.17, 0.02, 1); bs.inputs['Roughness'].default_value = 0.015; entrada(bs, 'Transmission Weight', 'Transmission').default_value = 0.95; entrada(bs, 'IOR').default_value = 1.36; return m
def mat_brasa():
    m = bpy.data.materials.new('Brasa'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.22, 0.03, 1); L(nt, em.outputs[0], out.inputs[0])
    d = em.inputs['Strength'].driver_add('default_value'); d.driver.type = 'SCRIPTED'; d.driver.expression = '14.0 + 9.0 * sin(frame * 0.115) + 5.0 * sin(frame * 0.31 + 1.3)'      # la brasa late y se aviva sin saltos
    return m
def mat_pantalla():
    m = bpy.data.materials.new('Pantalla_lampara'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.62, 0.30, 1); em.inputs['Strength'].default_value = 7.0; L(nt, em.outputs[0], out.inputs[0]); return m

M = {'piso': mat_piso(), 'pared': mat_pared(), 'techo': mat_techo(), 'madera': mat_madera('Madera_nogal'), 'marco': mat_madera('Madera_marco', (0.02, 0.01, 0.005), (0.07, 0.035, 0.016), 0.35),
     'tela': mat_terciopelo('Terciopelo_sillon'), 'alfombra': mat_alfombra(), 'cortina': mat_cortina(), 'vent': mat_ventana(), 'whisky_v': mat_vidrio('Vidrio_whisky', (0.12, 0.07, 0.02), 1.5, 0.01, 0.9),
     'vino_v': mat_vidrio('Vidrio_botella_vino', (0.012, 0.045, 0.018), 1.5, 0.012, 0.9), 'copa': mat_vidrio('Cristal', (0.95, 0.97, 1.0), 1.5, 0.008), 'cenicero': mat_vidrio('Cristal_cenicero', (0.88, 0.93, 1.0), 1.55, 0.02),
     'whisky': mat_whisky(), 'vino_copa': mat_vino_copa(), 'charco': mat_vino_charco(), 'papel': mat_papel('Papel', (0.78, 0.74, 0.62)), 'filtro': mat_papel('Filtro', (0.55, 0.30, 0.10)), 'ceniza': mat_papel('Ceniza', (0.26, 0.26, 0.27)),
     'colilla': mat_papel('Colilla', (0.60, 0.55, 0.47)), 'brasa': mat_brasa(), 'pistola': mat_metal('Acero_negro', (0.025, 0.027, 0.03), 0.28, 1.0), 'laton': mat_metal('Laton', (0.80, 0.55, 0.24), 0.28), 'pantalla': mat_pantalla(),
     'etiqueta': mat_papel('Etiqueta', (0.78, 0.72, 0.55))}
def asigna(o, m):
    o.data.materials.clear(); o.data.materials.append(m)
for o in list(bpy.data.objects):
    if o.type != 'MESH': continue
    n = o.name
    if n.startswith('Piso'): asigna(o, M['piso'])
    elif n.startswith('Pared'): asigna(o, M['pared'])
    elif n.startswith('Techo'): asigna(o, M['techo'])
    elif n.startswith(('Marco_ventana', 'Cortinero')): asigna(o, M['marco'])
    elif n.startswith('Vidrio_ventana'): asigna(o, M['vent'])
    elif n.startswith('Cortina_'): asigna(o, M['cortina'])
    elif n.startswith('Tela_alfombra'): asigna(o, M['alfombra'])
    elif n.startswith('Tela_'): asigna(o, M['tela'])
    elif n.startswith('Madera_'): asigna(o, M['madera'])
    elif n.startswith('Botella_whisky_vidrio'): asigna(o, M['whisky_v'])
    elif n.startswith('Botella_whisky_liquido'): asigna(o, M['whisky'])
    elif n.startswith('Botella_vino_vidrio') or n.startswith('Botella_aparador'): asigna(o, M['vino_v'])
    elif n.startswith('Botella_etiqueta') or n.startswith('Botella_vino_etiqueta'): asigna(o, M['etiqueta'])
    elif n.startswith('Copa_vidrio'): asigna(o, M['copa'])
    elif n.startswith('Copa_vino'): asigna(o, M['vino_copa'])
    elif n.startswith('Liquido_'): asigna(o, M['charco'])
    elif n == 'Cenicero' or n.startswith('Cenicero'): asigna(o, M['cenicero'])
    elif n.startswith('Colilla'): asigna(o, M['colilla'])
    elif n.startswith('Cigarro_encendido'): asigna(o, M['papel'])
    elif n.startswith('Cigarro_filtro'): asigna(o, M['filtro'])
    elif n.startswith('Cigarro_brasa'): asigna(o, M['brasa'])
    elif n.startswith('Cigarro_ceniza'): asigna(o, M['ceniza'])
    elif n.startswith('Pistola'):
        for _m in o.data.materials:
            if _m and _m.use_nodes:
                for _n in _m.node_tree.nodes:
                    if _n.type == 'BSDF_PRINCIPLED':
                        _n.inputs['Roughness'].default_value = max(min(_n.inputs['Roughness'].default_value, 0.4), 0.18); _n.inputs['Metallic'].default_value = max(_n.inputs['Metallic'].default_value, 0.85)
    elif n.startswith('Lampara_pantalla'): asigna(o, M['pantalla'])
    elif n.startswith(('Lampara_pie', 'Encendedor')): asigna(o, M['laton'])
    # bordes biselados y almohadones redondeados (sólo en Blender)
    if n.startswith(('Madera_', 'Tela_sillon', 'Marco_', 'Pistola_corredera')) and not n.startswith('Tela_alfombra'):
        bv = o.modifiers.new('Bisel', 'BEVEL'); bv.width = 0.035 if n.startswith('Tela_sillon') else 0.006; bv.segments = 5 if n.startswith('Tela_sillon') else 2; bv.limit_method = 'ANGLE'
        if n.startswith('Tela_sillon'):
            sb = o.modifiers.new('Sub', 'SUBSURF'); sb.levels = 1; sb.render_levels = 2
    if n.startswith(('Botella_', 'Copa_', 'Cenicero', 'Colilla', 'Cigarro', 'Lampara')):
        for p in o.data.polygons: p.use_smooth = True
print('materiales de la casa listos')

# ───────────────────────── mundo y luces ─────────────────────────
w = bpy.data.worlds.new('Tormenta_noche'); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
sal = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[0].default_value = (0.018, 0.026, 0.05, 1); bg.inputs[1].default_value = 1.0; L(nt, bg.outputs[0], sal.inputs['Surface'])
vol = nt.nodes.new('ShaderNodeVolumeScatter'); vol.inputs['Density'].default_value = 0.0; sc.world = w
f_flash = [int(t * FPS) + 1 for t in EV['relampagos_s']]
for f0 in f_flash:                                                                       # el cielo se enciende con cada relámpago (doble destello)
    for df, e in ((0, 1.0), (1, 14.0), (3, 3.0), (5, 18.0), (7, 5.0), (12, 1.0)):
        bg.inputs[1].default_value = e; bg.inputs[1].keyframe_insert('default_value', frame=f0 + df)
bg.inputs[1].default_value = 1.0; bg.inputs[1].keyframe_insert('default_value', frame=1)
lampara_pos = gb((-1.75, 1.58, -1.9))
lam = bpy.data.lights.new('Luz_lampara', 'POINT'); lam.color = (1.0, 0.62, 0.30); lam.energy = 85.0; lam.shadow_soft_size = 0.18
lo = bpy.data.objects.new('Luz_lampara', lam); sc.collection.objects.link(lo); lo.location = lampara_pos
for i in range(0, TOTAL, 6):                                                                 # parpadeo muy suave de la lámpara (la tormenta baja la tensión): seno lento, sin ruido por cuadro
    lam.energy = 85.0 * (1.0 + 0.05 * math.sin(i * 0.05) + 0.03 * math.sin(i * 0.19 + 1.0)); lam.keyframe_insert('energy', frame=i + 1)
lun = bpy.data.lights.new('Luz_exterior', 'AREA'); lun.shape = 'RECTANGLE'; lun.size = 7.0; lun.size_y = 3.2; lun.color = (0.48, 0.60, 1.0); lun.energy = 160.0
lu = bpy.data.objects.new('Luz_exterior', lun); sc.collection.objects.link(lu); lu.visible_camera = False; lu.location = (0, 6.4, 1.7); lu.rotation_euler = (math.radians(90), 0, math.radians(180))     # fuera del ventanal, mirando hacia adentro
for f0 in f_flash:
    for df, e in ((0, 160.0), (1, 5200.0), (3, 900.0), (5, 6500.0), (7, 1400.0), (12, 160.0)):
        lun.energy = e; lun.keyframe_insert('energy', frame=f0 + df)
lun.energy = 160.0; lun.keyframe_insert('energy', frame=1)
ember = bpy.data.lights.new('Luz_brasa', 'POINT'); ember.color = (1.0, 0.3, 0.06); ember.energy = 0.35; ember.shadow_soft_size = 0.01
eo = bpy.data.objects.new('Luz_brasa', ember); sc.collection.objects.link(eo); eo.location = gb((mesa_c[0] + 0.095, MY + 0.083, mesa_c[2] + 0.20))
# bruma en la sala: se ven los haces de luz de los relámpagos y la lámpara
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.65)); br = bpy.context.active_object; br.name = 'Bruma_sala'; br.scale = (7.2, 9.2, 3.2)
mvb = bpy.data.materials.new('Bruma'); mvb.use_nodes = True; ntb = mvb.node_tree; ntb.nodes.clear(); ob_ = ntb.nodes.new('ShaderNodeOutputMaterial'); vb = ntb.nodes.new('ShaderNodeVolumePrincipled')
vb.inputs['Density'].default_value = 0.022; vb.inputs['Anisotropy'].default_value = 0.45; vb.inputs['Color'].default_value = (0.8, 0.82, 0.9, 1); L(ntb, vb.outputs[0], ob_.inputs['Volume']); br.data.materials.append(mvb); br.display_type = 'BOUNDS'
for c_ in list(br.users_collection): c_.objects.unlink(br)
col_fx.objects.link(br)

# ───────────────────────── exterior: suelo, pinos, lluvia ─────────────────────────
import assets_reales as AR
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 40, -0.02)); sue = bpy.context.active_object; sue.name = 'Suelo_exterior'
ms = bpy.data.materials.new('Pasto_mojado'); ms.use_nodes = True; nts = ms.node_tree; bss = nts.nodes['Principled BSDF']; bss.inputs['Base Color'].default_value = (0.012, 0.022, 0.012, 1); bss.inputs['Roughness'].default_value = 0.35; sue.data.materials.append(ms)
for c_ in list(sue.users_collection): c_.objects.unlink(sue)
col_fx.objects.link(sue)
variantes = [AR.pino(f'PinoC_v{i}', al, 200 + i) for i, al in enumerate((11.0, 13.0, 15.5, 9.5))]
col_arb = bpy.data.collections.new('Arboles'); sc.collection.children.link(col_arb)
for i in range(46):
    o = bpy.data.objects.new(f'PinoC_{i}', variantes[i % 4]); col_arb.objects.link(o)
    o.location = (rng_c.uniform(-26, 26), rng_c.uniform(8.0, 34.0), 0.0); o.rotation_euler = (0, 0, rng_c.uniform(0, 6.28)); sq = rng_c.uniform(0.8, 1.3); o.scale = (sq, sq, sq)
def mat_lluvia():
    m = bpy.data.materials.new('Lluvia'); m.use_nodes = True; nt_ = m.node_tree; nt_.nodes.clear()
    out = N(nt_, 'ShaderNodeOutputMaterial'); em = N(nt_, 'ShaderNodeEmission'); tr = N(nt_, 'ShaderNodeBsdfTransparent'); mx = N(nt_, 'ShaderNodeMixShader')
    em.inputs['Color'].default_value = (0.78, 0.86, 1.0, 1); em.inputs['Strength'].default_value = 0.8; mx.inputs['Fac'].default_value = 0.25
    nt_.links.new(tr.outputs[0], mx.inputs[1]); nt_.links.new(em.outputs[0], mx.inputs[2]); nt_.links.new(mx.outputs[0], out.inputs[0]); return m
O_GOTA = malla_obj('Gota_lluvia', m_gota, mat_lluvia())
def construir_lluvia():
    g = ng('GN_Lluvia_ext'); sal = N(g, 'NodeGroupOutput')
    grid = N(g, 'GeometryNodeMeshGrid'); grid.inputs['Size X'].default_value = 50.0; grid.inputs['Size Y'].default_value = 34.0; grid.inputs['Vertices X'].default_value = 2; grid.inputs['Vertices Y'].default_value = 2
    dist = N(g, 'GeometryNodeDistributePointsOnFaces', distribute_method='RANDOM'); dist.inputs['Density'].default_value = 5.5; dist.inputs['Seed'].default_value = 5; g.links.new(grid.outputs['Mesh'], dist.inputs['Mesh'])
    tiempo = N(g, 'GeometryNodeInputSceneTime'); r0 = rnd(g, 7); H = 18.0; VEL = 12.0
    caida = mat_(g, 'FLOORED_MODULO', mat_(g, 'ADD', mat_(g, 'MULTIPLY', tiempo.outputs['Seconds'], VEL), mat_(g, 'MULTIPLY', r0, H)), H)
    z = mat_(g, 'SUBTRACT', H, caida)
    sp = N(g, 'GeometryNodeSetPosition'); g.links.new(dist.outputs['Points'], sp.inputs['Geometry']); g.links.new(xyz(g, mat_(g, 'MULTIPLY', z, -0.12), 0.0, z), sp.inputs['Offset'])
    oi = N(g, 'GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = O_GOTA; oi.inputs['As Instance'].default_value = True
    ins = N(g, 'GeometryNodeInstanceOnPoints'); g.links.new(sp.outputs['Geometry'], ins.inputs['Points']); g.links.new(oi.outputs['Geometry'], ins.inputs['Instance']); ins.inputs['Rotation'].default_value = (0.0, math.atan(0.12), 0.0)
    ins.inputs['Scale'].default_value = (1.6, 1.6, 1.6); g.links.new(ins.outputs['Instances'], sal.inputs['Geometry']); return g
rl = objeto_gn('Lluvia_exterior', construir_lluvia()); rl.location = (0, 24, 0)

# ───────────────────────── cortinas con viento (deformación por tiempo) ─────────────────────────
datos_v = bpy.data.objects.new('Datos_viento', None); sc.collection.objects.link(datos_v)
for i in range(TOTAL):
    tt = i / FPS; r_ = 0.28 + 0.14 * math.sin(tt * 0.31)
    for tl in EV['relampagos_s']: r_ += 0.85 * math.exp(-((tt - tl - 0.3) / 1.4) ** 2)
    datos_v.scale = (min(r_, 1.3), 1.0, 1.0); datos_v.keyframe_insert('scale', frame=i + 1)
def construir_viento():
    g = ng('GN_Viento_cortina'); ent = N(g, 'NodeGroupInput'); sal = N(g, 'NodeGroupOutput')
    g.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    d = N(g, 'GeometryNodeObjectInfo'); d.inputs['Object'].default_value = datos_v; A = sep(g, d.outputs['Scale'])[0]
    pos = N(g, 'GeometryNodeInputPosition'); px, py, pz = sep(g, pos.outputs[0])
    tiempo = N(g, 'GeometryNodeInputSceneTime'); T = tiempo.outputs['Seconds']
    h = mat_(g, 'DIVIDE', pz, 3.1)                                                              # 0 abajo … 1 arriba (colgada del cortinero)
    libre = mat_(g, 'POWER', mat_(g, 'MAXIMUM', mat_(g, 'SUBTRACT', 1.0, h), 0.0), 1.35)        # abajo se mueve más
    ola1 = mat_(g, 'SINE', mat_(g, 'MULTIPLY', mat_(g, 'SUBTRACT', mat_(g, 'MULTIPLY', T, 0.55), mat_(g, 'ADD', mat_(g, 'MULTIPLY', h, 1.1), mat_(g, 'MULTIPLY', px, 0.35))), 6.2832))
    ola2 = mat_(g, 'SINE', mat_(g, 'MULTIPLY', mat_(g, 'SUBTRACT', mat_(g, 'MULTIPLY', T, 1.15), mat_(g, 'MULTIPLY', h, 2.3)), 6.2832))
    fuerza = mat_(g, 'MULTIPLY', A, mat_(g, 'ADD', 0.5, mat_(g, 'MULTIPLY', 0.5, ola1)))
    hacia = mat_(g, 'MULTIPLY', libre, mat_(g, 'ADD', mat_(g, 'MULTIPLY', fuerza, 0.55), mat_(g, 'MULTIPLY', mat_(g, 'MULTIPLY', ola2, 0.06), A)))
    pliegue = mat_(g, 'MULTIPLY', mat_(g, 'SINE', mat_(g, 'ADD', mat_(g, 'MULTIPLY', px, 21.0), mat_(g, 'MULTIPLY', ola1, 0.8))), mat_(g, 'MULTIPLY', 0.028, mat_(g, 'ADD', 1.0, libre)))
    # en Blender el espesor de la lámina es el eje Y local: «hacia adentro de la sala» es −Y
    sp = N(g, 'GeometryNodeSetPosition'); g.links.new(ent.outputs[0], sp.inputs['Geometry']); g.links.new(xyz(g, mat_(g, 'MULTIPLY', pliegue, 1.0), mat_(g, 'MULTIPLY', hacia, -1.0), 0.0), sp.inputs['Offset'])
    g.links.new(sp.outputs['Geometry'], sal.inputs['Geometry']); return g
gv = construir_viento()
for o in bpy.data.objects:
    if o.name.startswith('Cortina_') and o.type == 'MESH':
        md = o.modifiers.new('Viento', 'NODES'); md.node_group = gv
        for p in o.data.polygons: p.use_smooth = True

# ───────────────────────── humo del cigarro, brasa y ceniza ─────────────────────────
mesa_c = EV['mesa_centro']; MY = EV['mesa_altura']
punta = gb((mesa_c[0] + 0.05 + 0.047, MY + 0.092, mesa_c[2] + 0.20 + 0.12 * 0 + 0.0))
punta = gb((mesa_c[0] + 0.05 + 0.050, MY + 0.092, mesa_c[2] + 0.17 + 0.03))
origen_humo = bpy.data.objects.new('Humo_cigarro_origen', None); sc.collection.objects.link(origen_humo); origen_humo.location = punta
def mat_humo_fino():
    m = bpy.data.materials.new('Humo_cigarro'); m.use_nodes = True; nt_ = m.node_tree; nt_.nodes.clear(); out = N(nt_, 'ShaderNodeOutputMaterial'); v = N(nt_, 'ShaderNodeVolumeScatter')
    v.inputs['Density'].default_value = 5.0; v.inputs['Color'].default_value = (0.9, 0.9, 0.95, 1); v.inputs['Anisotropy'].default_value = 0.55; nt_.links.new(v.outputs[0], out.inputs['Volume']); return m
O_HUMO = malla_obj('Hilo_humo', m_esfera, mat_humo_fino())
for _p in O_HUMO.data.polygons: _p.use_smooth = True
def construir_humo():
    g = ng('GN_Humo_cigarro'); sal = N(g, 'NodeGroupOutput')
    o_ = N(g, 'GeometryNodeObjectInfo'); o_.inputs['Object'].default_value = origen_humo; O = o_.outputs['Location']
    ml = N(g, 'GeometryNodeMeshLine'); ml.inputs['Count'].default_value = 90; ml.inputs['Start Location'].default_value = (0, 0, 0); ml.inputs['Offset'].default_value = (0, 0, 0)
    tiempo = N(g, 'GeometryNodeInputSceneTime'); ida = N(g, 'GeometryNodeInputIndex').outputs[0]
    r1 = rnd(g, 71, ident=ida); r2 = rnd(g, 72, 0.0, 6.28, ident=ida); r3 = rnd(g, 73, -1.0, 1.0, ident=ida)
    VIDA = 8.0
    u = mat_(g, 'FRACT', mat_(g, 'ADD', mat_(g, 'DIVIDE', tiempo.outputs['Seconds'], VIDA), r1))                  # 0 (en la brasa) … 1 (disipado)
    alto = mat_(g, 'MULTIPLY', mat_(g, 'POWER', u, 0.8), 1.15)
    amp = mat_(g, 'ADD', 0.004, mat_(g, 'MULTIPLY', mat_(g, 'POWER', u, 1.4), 0.20))
    ox = mat_(g, 'MULTIPLY', amp, mat_(g, 'SINE', mat_(g, 'ADD', mat_(g, 'MULTIPLY', u, 11.0), r2)))
    oy = mat_(g, 'MULTIPLY', amp, mat_(g, 'SINE', mat_(g, 'ADD', mat_(g, 'MULTIPLY', u, 8.3), mat_(g, 'ADD', r2, 1.9))))
    pos = vec_(g, 'ADD', O, xyz(g, mat_(g, 'ADD', ox, mat_(g, 'MULTIPLY', r3, 0.006)), oy, alto))
    sp = N(g, 'GeometryNodeSetPosition'); g.links.new(ml.outputs['Mesh'], sp.inputs['Geometry']); g.links.new(pos, sp.inputs['Position'])
    oi = N(g, 'GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = O_HUMO; oi.inputs['As Instance'].default_value = True
    ins = N(g, 'GeometryNodeInstanceOnPoints'); g.links.new(sp.outputs['Geometry'], ins.inputs['Points']); g.links.new(oi.outputs['Geometry'], ins.inputs['Instance'])
    vive = mat_(g, 'MULTIPLY', mat_(g, 'SUBTRACT', 1.0, mat_(g, 'POWER', u, 4.0)), mat_(g, 'MINIMUM', mat_(g, 'MULTIPLY', u, 14.0), 1.0))                # aparece y se desvanece
    tam = mat_(g, 'MULTIPLY', mat_(g, 'ADD', 0.006, mat_(g, 'MULTIPLY', mat_(g, 'POWER', u, 1.2), 0.075)), vive)
    g.links.new(xyz(g, tam, tam, tam), ins.inputs['Scale']); g.links.new(ins.outputs['Instances'], sal.inputs['Geometry']); return g
objeto_gn('Humo_cigarro', construir_humo())
# la ceniza crece despacio y la brasa avanza: el cigarro se consume con el tiempo
cen = bpy.data.objects.get('Cigarro_ceniza')
if cen is not None:
    for f_, k_ in ((1, 0.55), (TOTAL // 2, 1.0), (TOTAL, 1.5)):
        cen.scale = (1, 1, k_); cen.keyframe_insert('scale', frame=f_)

# ───────────────────────── goteos: vino que cae del borde de la mesa y sangre que cae de los dedos ─────────────────────────
def mat_gota(nombre, col):
    m, nt_, bs_, out_ = mk(nombre); bs_.inputs['Base Color'].default_value = (*col, 1); bs_.inputs['Roughness'].default_value = 0.04; entrada(bs_, 'Coat Weight', 'Clearcoat').default_value = 1.0; return m
O_GV = malla_obj('Gota_vino', m_esfera, mat_gota('Gota_vino', (0.2, 0.0, 0.008))); O_GS = malla_obj('Gota_sangre', m_esfera, mat_gota('Gota_sangre', (0.22, 0.0, 0.004)))
for _o in (O_GV, O_GS):
    for _p in _o.data.polygons: _p.use_smooth = True
def construir_goteo(nombre, origen_obj, periodo, caida_m, objeto, radio, semilla):
    g = ng(nombre); sal = N(g, 'NodeGroupOutput'); unir = N(g, 'GeometryNodeJoinGeometry')
    o_ = N(g, 'GeometryNodeObjectInfo'); o_.inputs['Object'].default_value = origen_obj; O = o_.outputs['Location']
    tiempo = N(g, 'GeometryNodeInputSceneTime'); T_c = math.sqrt(2.0 * caida_m / 9.8)
    ph = mat_(g, 'FRACT', mat_(g, 'ADD', mat_(g, 'DIVIDE', tiempo.outputs['Seconds'], periodo), semilla))
    seg = mat_(g, 'MULTIPLY', ph, periodo)                                                    # segundos dentro del ciclo
    cuelga = mat_(g, 'LESS_THAN', seg, periodo - T_c - 0.05)
    t_ = mat_(g, 'MAXIMUM', mat_(g, 'SUBTRACT', seg, periodo - T_c - 0.05), 0.0)               # tiempo de caída libre
    crece = mat_(g, 'MULTIPLY', mat_(g, 'MINIMUM', mat_(g, 'DIVIDE', seg, periodo - T_c - 0.05), 1.0), 1.0)
    z = mat_(g, 'SUBTRACT', 0.0, mat_(g, 'MULTIPLY', mat_(g, 'MULTIPLY', t_, t_), 4.9))
    vive = mat_(g, 'LESS_THAN', t_, T_c)
    ml = N(g, 'GeometryNodeMeshLine'); ml.inputs['Count'].default_value = 1; ml.inputs['Start Location'].default_value = (0, 0, 0); ml.inputs['Offset'].default_value = (0, 0, 0)
    sp = N(g, 'GeometryNodeSetPosition'); g.links.new(ml.outputs['Mesh'], sp.inputs['Geometry']); g.links.new(vec_(g, 'ADD', O, xyz(g, 0.0, 0.0, mat_(g, 'MAXIMUM', z, -caida_m))), sp.inputs['Position'])
    oi = N(g, 'GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = objeto; oi.inputs['As Instance'].default_value = True
    ins = N(g, 'GeometryNodeInstanceOnPoints'); g.links.new(sp.outputs['Geometry'], ins.inputs['Points']); g.links.new(oi.outputs['Geometry'], ins.inputs['Instance'])
    tam = mat_(g, 'MULTIPLY', mat_(g, 'MULTIPLY', radio, mat_(g, 'ADD', 0.35, mat_(g, 'MULTIPLY', 0.65, mat_(g, 'MINIMUM', crece, 1.0)))), vive)
    g.links.new(xyz(g, mat_(g, 'MULTIPLY', tam, 0.85), mat_(g, 'MULTIPLY', tam, 0.85), mat_(g, 'MULTIPLY', tam, mat_(g, 'ADD', 1.0, mat_(g, 'MULTIPLY', 0.5, mat_(g, 'MINIMUM', t_ * 1.0 if False else t_, 0.3))))), ins.inputs['Scale'])
    g.links.new(ins.outputs['Instances'], unir.inputs['Geometry']); g.links.new(unir.outputs['Geometry'], sal.inputs['Geometry']); return g
borde_vino = bpy.data.objects.new('Borde_mesa_vino', None); sc.collection.objects.link(borde_vino); borde_vino.location = gb((mesa_c[0] + 1.15, MY - 0.002, mesa_c[2] - 0.14))
objeto_gn('Goteo_vino', construir_goteo('GN_Goteo_vino', borde_vino, EV['gota_vino_cada_s'], MY, O_GV, 0.011, 0.0))
goteo_s = bpy.data.objects['Goteo_origen']
sc.frame_set(1000); gs = goteo_s.matrix_world.translation.copy(); ALT_GOTEO = max(gs.z, 0.25)
objeto_gn('Goteo_sangre', construir_goteo('GN_Goteo_sangre', goteo_s, EV['gota_sangre_cada_s'], ALT_GOTEO, O_GS, 0.0085, 0.37))
# charcos que crecen despacio bajo el goteo

def mat_sangre_real():
    """Charco de sangre real: contorno irregular y orgánico, borde fino rojo anaranjado, centro espeso casi negro, superficie líquida brillante con menisco y reflejos."""
    m = bpy.data.materials.new('Sangre_real'); m.use_nodes = True; nt_ = m.node_tree; nt_.nodes.clear()
    out = N(nt_, 'ShaderNodeOutputMaterial'); bs_ = N(nt_, 'ShaderNodeBsdfPrincipled'); tr = N(nt_, 'ShaderNodeBsdfTransparent'); mx_ = N(nt_, 'ShaderNodeMixShader')
    tc = N(nt_, 'ShaderNodeTexCoord')
    ru = N(nt_, 'ShaderNodeTexNoise'); ru.inputs['Scale'].default_value = 3.2; ru.inputs['Detail'].default_value = 9.0; ru.inputs['Roughness'].default_value = 0.62; nt_.links.new(tc.outputs['Generated'], ru.inputs['Vector'])
    ru2 = N(nt_, 'ShaderNodeTexNoise'); ru2.inputs['Scale'].default_value = 14.0; ru2.inputs['Detail'].default_value = 4.0; nt_.links.new(tc.outputs['Generated'], ru2.inputs['Vector'])
    gr = N(nt_, 'ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    mp = N(nt_, 'ShaderNodeMapping'); mp.inputs['Location'].default_value = (-0.5, -0.5, -0.5); nt_.links.new(tc.outputs['Generated'], mp.inputs[0]); nt_.links.new(mp.outputs[0], gr.inputs[0])
    inv = N(nt_, 'ShaderNodeMapRange'); inv.inputs['From Min'].default_value = 0.0; inv.inputs['From Max'].default_value = 0.5; inv.inputs['To Min'].default_value = 1.0; inv.inputs['To Max'].default_value = 0.0; nt_.links.new(gr.outputs['Fac'], inv.inputs['Value'])
    ds = N(nt_, 'ShaderNodeMath'); ds.operation = 'ADD'; nt_.links.new(inv.outputs[0], ds.inputs[0]); nz = N(nt_, 'ShaderNodeMapRange'); nz.inputs['To Min'].default_value = -0.30; nz.inputs['To Max'].default_value = 0.30; nt_.links.new(ru.outputs['Fac'], nz.inputs['Value']); nt_.links.new(nz.outputs[0], ds.inputs[1])
    forma = N(nt_, 'ShaderNodeMapRange'); forma.inputs['From Min'].default_value = 0.30; forma.inputs['From Max'].default_value = 0.40; nt_.links.new(ds.outputs[0], forma.inputs['Value'])      # 0 afuera … 1 adentro (borde nítido y orgánico)
    esp = N(nt_, 'ShaderNodeMapRange'); esp.inputs['From Min'].default_value = 0.34; esp.inputs['From Max'].default_value = 0.85; nt_.links.new(ds.outputs[0], esp.inputs['Value'])             # grosor: 0 borde … 1 centro
    col = N(nt_, 'ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['Factor'].default_value = 0.0; nt_.links.new(esp.outputs[0], col.inputs['Factor'])
    for sk, v in (('A', (0.34, 0.012, 0.006, 1)), ('B', (0.035, 0.0, 0.002, 1))): [x for x in col.inputs if x.name == sk and x.type == 'RGBA'][0].default_value = v
    nt_.links.new(col.outputs['Result'], bs_.inputs['Base Color'])
    bs_.inputs['Roughness'].default_value = 0.035; entrada(bs_, 'Coat Weight', 'Clearcoat').default_value = 1.0; entrada(bs_, 'Coat Roughness', 'Clearcoat Roughness').default_value = 0.02; entrada(bs_, 'IOR').default_value = 1.38
    bp = N(nt_, 'ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.7; bp.inputs['Distance'].default_value = 0.006
    hh = N(nt_, 'ShaderNodeMath'); hh.operation = 'ADD'; nt_.links.new(esp.outputs[0], hh.inputs[0]); nt_.links.new(ru2.outputs['Fac'], hh.inputs[1]); hh.inputs[1].default_value = 0.0
    sm = N(nt_, 'ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = 0.08; nt_.links.new(ru2.outputs['Fac'], sm.inputs[0]); nt_.links.new(esp.outputs[0], hh.inputs[0]); nt_.links.new(sm.outputs[0], hh.inputs[1])
    nt_.links.new(hh.outputs[0], bp.inputs['Height']); nt_.links.new(bp.outputs[0], bs_.inputs['Normal'])
    nt_.links.new(forma.outputs[0], mx_.inputs['Fac']); nt_.links.new(tr.outputs[0], mx_.inputs[1]); nt_.links.new(bs_.outputs[0], mx_.inputs[2]); nt_.links.new(mx_.outputs[0], out.inputs[0]); return m
M_SANGRE_REAL = mat_sangre_real()
def mancha_piso(nombre, pos, tam0, tam1, mat_):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(pos[0], pos[1], 0.003)); o = bpy.context.active_object; o.name = nombre; o.data.materials.append(mat_); o.rotation_euler = (0, 0, rng_c.uniform(0, 6.28))
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    col_fx.objects.link(o); o.scale = (tam0, tam0, 1); o.keyframe_insert('scale', frame=1); o.scale = (tam1, tam1, 1); o.keyframe_insert('scale', frame=TOTAL); return o
mancha_piso('Sangre_piso_1', (gs.x, gs.y), 0.18, 0.60, M_SANGRE_REAL); mancha_piso('Sangre_piso_2', (gs.x - 0.10, gs.y + 0.06), 0.07, 0.30, M_SANGRE_REAL)
for k_ in range(7): mancha_piso(f'Sangre_gotas_{k_}', (gs.x + rng_c.uniform(-0.35, 0.35), gs.y + rng_c.uniform(-0.3, 0.3)), 0.025, rng_c.uniform(0.05, 0.11), M_SANGRE_REAL)
mancha_piso('Vino_piso', gb((mesa_c[0] + 1.17, 0, mesa_c[2] - 0.14))[:2], 0.05, 0.28, M['charco'])

# ───────────────────────── sangre en Gabriel (rostro, manos, hombro herido de la camisa) ─────────────────────────
f_imp = 0
exec(open(os.path.join(HERE, 'piel_sangre.py')).read())
m_h = bpy.data.materials.get('EM3D_Skin_Head')
if m_h and m_h.use_nodes: sangre_cara(m_h)
m_a = bpy.data.materials.get('EM3D_Skin_Arm')
if m_a and m_a.use_nodes: sangre_en(m_a, mascara_manos)
def mat_camisa_gabriel(obj):
    """Camisa clara arrugada con la mancha del disparo en el hombro izquierdo: orificio oscuro, mancha que baja por la manga y el pecho."""
    m, nt_, bs_, out_ = mk('Camisa_Gabriel'); vs = [v.co for v in obj.data.vertices]
    LO = Vector((min(c.x for c in vs), min(c.y for c in vs), min(c.z for c in vs))); HI = Vector((max(c.x for c in vs), max(c.y for c in vs), max(c.z for c in vs))); SZ = HI - LO
    tc = tex(nt_, 'ShaderNodeTexCoord'); tej = tex(nt_, 'ShaderNodeTexNoise', i_Scale=700.0, i_Detail=2.0); L(nt_, tc.outputs['Object'], tej.inputs['Vector'])
    pl = tex(nt_, 'ShaderNodeTexNoise', i_Scale=11.0, i_Detail=6.0, i_Roughness=0.6); L(nt_, tc.outputs['Object'], pl.inputs['Vector'])
    bs_.inputs['Base Color'].default_value = (0.60, 0.61, 0.64, 1); bs_.inputs['Roughness'].default_value = 0.82; entrada(bs_, 'Sheen Weight', 'Sheen').default_value = 0.4
    sm = tex(nt_, 'ShaderNodeMath', operation='ADD'); L(nt_, tej.outputs['Fac'], sm.inputs[0]); L(nt_, pl.outputs['Fac'], sm.inputs[1]); bump_(nt_, bs_, sm.outputs[0], 0.5, 0.003)
    def gauss(cm, ax, ay, ang):
        cn = ((cm[0] - LO.x) / SZ.x, (cm[1] - LO.y) / SZ.y, (cm[2] - LO.z) / SZ.z)
        rs = tex(nt_, 'ShaderNodeVectorMath', operation='SUBTRACT'); rs.inputs[1].default_value = cn; L(nt_, tc.outputs['Generated'], rs.inputs[0])
        a_ = tex(nt_, 'ShaderNodeVectorMath', operation='MULTIPLY'); a_.inputs[1].default_value = (SZ.x, SZ.y, SZ.z); L(nt_, rs.outputs[0], a_.inputs[0])
        ro = tex(nt_, 'ShaderNodeVectorRotate', rotation_type='Z_AXIS'); ro.inputs['Angle'].default_value = -ang; L(nt_, a_.outputs[0], ro.inputs['Vector'])
        dv = tex(nt_, 'ShaderNodeVectorMath', operation='DIVIDE'); dv.inputs[1].default_value = (ax, ay, 7.0); L(nt_, ro.outputs[0], dv.inputs[0])
        ln = tex(nt_, 'ShaderNodeVectorMath', operation='LENGTH'); L(nt_, dv.outputs[0], ln.inputs[0])
        sq = tex(nt_, 'ShaderNodeMath', operation='MULTIPLY'); L(nt_, ln.outputs['Value'], sq.inputs[0]); L(nt_, ln.outputs['Value'], sq.inputs[1])
        ng_ = tex(nt_, 'ShaderNodeMath', operation='MULTIPLY'); ng_.inputs[1].default_value = -1.0; L(nt_, sq.outputs[0], ng_.inputs[0])
        ex = tex(nt_, 'ShaderNodeMath', operation='EXPONENT'); L(nt_, ng_.outputs[0], ex.inputs[0]); return ex.outputs[0]
    # el eje vertical de esta malla es Y; el lado izquierdo del personaje es +X
    hombro = (LO.x + SZ.x * 0.88, LO.y + SZ.y * 0.84, LO.z + SZ.z * 0.55)
    manga = (LO.x + SZ.x * 0.92, LO.y + SZ.y * 0.64, LO.z + SZ.z * 0.52)
    pecho = (LO.x + SZ.x * 0.70, LO.y + SZ.y * 0.74, LO.z + SZ.z * 0.62)
    g_ = [gauss(hombro, 0.075 * 100 * 0.01 * 100, 0.085 * 100, 0.2)]
    return m, nt_, bs_, (gauss, hombro, manga, pecho, LO, SZ)
cam_obj = next((o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('CAMISA')), None)
if cam_obj is not None:
    m_c, nt_c, bs_c, (gauss, hombro, manga, pecho, LO_, SZ_) = mat_camisa_gabriel(cam_obj)
    g1 = gauss(hombro, 8.0, 9.5, 0.2); g2 = gauss(manga, 5.0, 16.0, 0.05); g3 = gauss(pecho, 7.0, 10.0, -0.3)
    s1 = tex(nt_c, 'ShaderNodeMath', operation='ADD'); L(nt_c, g1, s1.inputs[0]); L(nt_c, g2, s1.inputs[1]); s2 = tex(nt_c, 'ShaderNodeMath', operation='ADD'); L(nt_c, s1.outputs[0], s2.inputs[0]); L(nt_c, g3, s2.inputs[1])
    cl = tex(nt_c, 'ShaderNodeClamp'); L(nt_c, s2.outputs[0], cl.inputs[0])
    base = bs_c.inputs['Base Color'].default_value[:]
    mx = tex(nt_c, 'ShaderNodeMix', data_type='RGBA'); [x for x in mx.inputs if x.name == 'A' and x.type == 'RGBA'][0].default_value = base; [x for x in mx.inputs if x.name == 'B' and x.type == 'RGBA'][0].default_value = (0.11, 0.003, 0.005, 1)
    L(nt_c, cl.outputs[0], mx.inputs['Factor']); L(nt_c, mx.outputs['Result'], bs_c.inputs['Base Color'])
    rg = tex(nt_c, 'ShaderNodeMix', data_type='FLOAT'); rg.inputs['A'].default_value = 0.82; rg.inputs['B'].default_value = 0.22; L(nt_c, cl.outputs[0], rg.inputs['Factor']); L(nt_c, rg.outputs['Result'], bs_c.inputs['Roughness'])
    asigna(cam_obj, m_c)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('PUNO_'): asigna(o, bpy.data.materials['Camisa_Gabriel'] if 'Camisa_Gabriel' in bpy.data.materials else o.data.materials[0])
    if o.type == 'MESH' and o.name.startswith('PANTALON'):
        mp_, nt_p, bs_p, _o = mk('Pantalon_Gabriel'); bs_p.inputs['Base Color'].default_value = (0.03, 0.031, 0.036, 1); bs_p.inputs['Roughness'].default_value = 0.8
        tcp = tex(nt_p, 'ShaderNodeTexCoord'); nsp = tex(nt_p, 'ShaderNodeTexNoise', i_Scale=600.0); L(nt_p, tcp.outputs['Object'], nsp.inputs['Vector']); bump_(nt_p, bs_p, nsp.outputs['Fac'], 0.4, 0.003); asigna(o, mp_)
    if o.type == 'MESH' and o.name.startswith('ZAPATO'): asigna(o, mat_metal('Cuero_negro', (0.012, 0.01, 0.01), 0.2, 0.0))
    if o.type == 'MESH' and o.name.startswith(('CINTURON', 'BOTON')): asigna(o, bpy.data.materials['Laton'] if o.name.startswith(('CINTURON_hebilla', 'BOTON')) else mat_metal('Cuero_cinturon', (0.02, 0.012, 0.008), 0.35, 0.0))
    if o.type == 'MESH' and o.name.startswith('COLLAR'): asigna(o, bpy.data.materials['Camisa_Gabriel'] if 'Camisa_Gabriel' in bpy.data.materials else o.data.materials[0])

# ───────────────────────── profundidad de campo cinematográfica ─────────────────────────
for tm in JS['tomas']:
    cam = bpy.data.objects[tm['camara']]
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.4 if tm['id'] in ('h2', 'h5', 'h6', 'h7') else 4.0
    cam.data.dof.focus_distance = max((cam.matrix_world.translation - Vector((0, 0, 1.0))).length * 0.0 + {'h1': 5.5, 'h2': 1.1, 'h3': 6.0, 'h4': 2.6, 'h5': 0.95, 'h6': 0.95, 'h7': 1.0, 'h8': 2.0}.get(tm['id'], 3.0), 0.3)
print('casa lista')
