"""BLEND de un DUELO (IA contra IA, campo de prácticas; escopeta, subfusil, fusil, rifle .50) del trailer de extracción: importa el GLB (ya sin KHR_node_visibility), clasifica objetos, pone luz y agrega los EFECTOS que no viajan en el GLB
a partir de escena_pistolas_disparos.json + sonidos.csv: sangre (chorros y charcos), fogonazos con luz, trazadoras, humo, chispas en metal, polvo en hormigón y astillas/ruptura de madera.
Los cuadros de salida son 30 fps; la animación del GLB queda a 24 (1 s = 24 cuadros de acción): cuadro de salida k ↔ cuadro de acción (k-1)*0.8.
Uso: /opt/tools/blendenv/bin/python construir_pistolas.py GLB_OK DISPAROS.json SONIDOS.csv SALIDA.blend"""
import bpy, bmesh, sys, json, csv, math, random
from mathutils import Vector, Quaternion
GLB, DISP, SON, SAL = sys.argv[-4:]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=GLB)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
FPS_S = 30; NK = 694                                       # cuadros de salida
def fa(k): return (k - 1) * 0.8                            # cuadro de acción del cuadro de salida k
def kk(t): return int(round(t * FPS_S)) + 1
def G(x, y, z): return Vector((x, -z, y))                  # Godot (x,y,z) → Blender
def anc(o):
    while o: yield o.name; o = o.parent
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    ns = list(anc(o))
    if o.name.startswith(('Sangre', 'Mancha')): o['clase'] = 'sangre'
    elif 'Anatomia' in ns or 'Anatomia2' in ns: o['clase'] = 'anat'
    elif any(n.startswith('Miembro') for n in ns): o['clase'] = 'anat'
    elif 'Mapa' in ns: o['clase'] = 'fondo'
    else: o['clase'] = 'auto'
    if any(n.startswith('Arma_') and n.endswith('_browning') for n in ns) and False: pass
cam = bpy.data.objects['Camara3D']; sc.camera = cam; cam.data.clip_start = 0.1; cam.data.clip_end = 200
# ───────── luz y mundo ─────────
sol = bpy.data.lights.new('Sol', 'SUN'); sol.energy = 2.4; sol.angle = math.radians(3); so = bpy.data.objects.new('Sol', sol); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(48), math.radians(-18), math.radians(25))
w = bpy.data.worlds.new('Mundo'); w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.62, 0.64, 0.68, 1); bg.inputs[1].default_value = 0.5; sc.world = w
# ───────── materiales de los efectos ─────────
def mat(nombre, col, emis=0.0, rug=0.5):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial')
    if emis > 0:
        e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*col, 1); e.inputs['Strength'].default_value = emis; nt.links.new(e.outputs[0], out.inputs[0])
    else:
        b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rug; nt.links.new(b.outputs[0], out.inputs[0])
    return m
M_SANGRE = mat('FX_sangre', (0.85, 0.015, 0.03), 0, 0.15); M_FLASH = mat('FX_fogonazo', (1.0, 0.72, 0.22), 60); M_NUCLEO = mat('FX_nucleo', (1.0, 0.95, 0.75), 120)
M_TRAZ = mat('FX_trazadora', (1.0, 0.85, 0.45), 40); M_CHISPA = mat('FX_chispa', (1.0, 0.62, 0.18), 50); M_POLVO = mat('FX_polvo', (0.72, 0.70, 0.66), 0, 1.0)
M_HUMO = mat('FX_humo', (0.55, 0.55, 0.55), 0, 1.0); M_MADERA = mat('FX_madera', (0.50, 0.31, 0.14), 0, 0.8); M_MADERA2 = mat('FX_madera_clara', (0.72, 0.55, 0.32), 0, 0.8)
def malla(nombre, tipo):
    me = bpy.data.meshes.new(nombre); bm = bmesh.new()
    if tipo == 'esfera': bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    elif tipo == 'cubo': bmesh.ops.create_cube(bm, size=1.0)
    elif tipo == 'cono':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.5, radius2=0.0, depth=1.0); bmesh.ops.translate(bm, vec=(0, 0, 0.5), verts=bm.verts)
    elif tipo == 'barra':
        bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.translate(bm, vec=(0, 0, 0.5), verts=bm.verts)
    bm.to_mesh(me); bm.free(); me.materials.append(M_POLVO); return me
ME = {t: malla('FX_' + t, t) for t in ('esfera', 'cubo', 'cono', 'barra')}
COLFX = bpy.data.collections.new('Efectos'); sc.collection.children.link(COLFX)
N = {'n': 0}
def nuevo(tipo, m, clase, pos=(0, 0, 0)):
    N['n'] += 1; o = bpy.data.objects.new(f'FX_{tipo}_{N["n"]}', ME[tipo])
    COLFX.objects.link(o); o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = m      # material por objeto: las mallas se comparten
    o.location = pos; o['clase'] = clase; o.scale = (0, 0, 0); return o
def clave(o, k, loc=None, esc=None, rot=None):
    f = fa(k)
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if esc is not None: o.scale = esc if not isinstance(esc, (int, float)) else (esc, esc, esc); o.keyframe_insert('scale', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)
def vida(o, k0, k1, esc, loc=None):
    clave(o, 0 + 1, esc=(0, 0, 0)); 
    if k0 > 1: clave(o, k0 - 1, esc=(0, 0, 0))
    clave(o, k0, esc=esc)
    if k1 is not None: clave(o, k1, esc=esc); clave(o, k1 + 1, esc=(0, 0, 0))
# ───────── datos ─────────
disp = json.load(open(DISP)); filas = list(csv.DictReader(open(SON)))
def pos_csv(s): return tuple(float(x) for x in s.strip('()').split(','))
ARMAS = {'shot_shotgun': 1.7, 'shot_smg': 0.8, 'bv_rifle_shot': 1.0, 'bv_sniper_shot': 2.1, 'bv_pistol_shot': 0.8}       # tamaño relativo del fogonazo
tiros = [{'t': float(f['segundo']), 'pos': G(*pos_csv(f['posicion_mundo'])), 'jug': f['sonido'] == 'bv_pistol_shot', 'k': ARMAS[f['sonido']]} for f in filas if f['sonido'] in ARMAS]
rnd = random.Random(26)
def tiro_de(e):
    p = G(e['x'], e['y'], e['z']); c = [s for s in tiros if -0.02 <= e['t'] - s['t'] <= 0.25]
    if not c: return None
    mt = max(s['t'] for s in c); c = [s for s in c if s['t'] >= mt - 0.05]                # el disparo más reciente (varios tiradores a la vez: el más lejano al impacto)
    return max(c, key=lambda s: (s['pos'] - p).length)
# ───────── fogonazos, humo, trazadoras ─────────
for s in tiros:
    k0 = kk(s['t']); d = Vector((1, 0, 0)) if (s['jug'] or s['pos'].x < 14.5) else Vector((-1, 0, 0))
    objetivos = [G(e['x'], e['y'], e['z']) for e in disp if tiro_de(e) is s]
    if objetivos: d = (objetivos[0] - s['pos']).normalized()
    q = d.to_track_quat('Z', 'Y'); m = s['pos'] + d * 0.05
    for i, (l, a, mm) in enumerate(((0.75, 0.16, M_FLASH), (0.42, 0.10, M_NUCLEO), (0.55, 0.30, M_FLASH))):
        o = nuevo('cono', mm, 'fx', m); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = q @ Quaternion((0, 0, 1), rnd.uniform(0, 6.28)) if i == 2 else q
        o.rotation_mode = 'XYZ'; o.rotation_euler = o.rotation_quaternion.to_euler() if False else (q @ Quaternion((0, 0, 1), rnd.uniform(0, 6.28))).to_euler()
        vida(o, k0, k0 + 1, (a * s['k'] ** 0.5, a * s['k'] ** 0.5, l * s['k']))
    g = nuevo('esfera', M_NUCLEO, 'fx', m); vida(g, k0, k0 + 1, (0.11 * s['k'] ** 0.5,) * 3)
    luz = bpy.data.lights.new('Fogonazo', 'POINT'); luz.energy = 0; luz.shadow_soft_size = 0.08; luz.color = (1.0, 0.72, 0.38); lo = bpy.data.objects.new('Fogonazo', luz); lo.location = m + d * 0.3; sc.collection.objects.link(lo)
    for kx, en in ((1, 0), (k0 - 1, 0), (k0, 130 * s['k']), (k0 + 1, 80 * s['k']), (k0 + 2, 0)): luz.energy = en; luz.keyframe_insert('energy', frame=fa(kx))
    for j in range(4):                                    # humo de la boca del arma: bolitas grises que suben y crecen
        o = nuevo('esfera', M_HUMO, 'fx'); v = Vector((d.x * 0.5, d.y * 0.2, 0.25)) + Vector((rnd.uniform(-.1, .1), rnd.uniform(-.1, .1), rnd.uniform(0, .25))); p = m + d * (0.1 + j * 0.1)
        clave(o, 1, esc=(0, 0, 0)); clave(o, k0 - 1, esc=(0, 0, 0))
        for i in range(0, 34, 3): clave(o, k0 + 1 + i, loc=p + v * (i / 30.0), esc=0.05 + 0.12 * math.sin(min(i / 33.0, 1) * math.pi * 0.8) + 0.03)
        clave(o, k0 + 36, esc=(0, 0, 0))
    for e in disp:                                        # trazadora hasta cada impacto de este disparo
        if tiro_de(e) is not s: continue
        p1 = G(e['x'], e['y'], e['z']); vec = p1 - m; L = vec.length
        if L < 0.3: continue
        o = nuevo('barra', M_TRAZ, 'fx', m); o.rotation_euler = vec.normalized().to_track_quat('Z', 'Y').to_euler(); vida(o, k0, k0, (0.022, 0.022, L))
# ───────── impactos ─────────
SANG = {'head': 30, 'neck': 26, 'torso': 24, 'arm': 14, 'leg': 14, 'hand': 10, 'pelvis': 16}
sonidos_imp = [(float(f['segundo']), f['sonido'], G(*pos_csv(f['posicion_mundo']))) for f in filas if f['sonido'].startswith(('impact_', 'wood_'))]
def tipo_mundo(e):
    p = G(e['x'], e['y'], e['z'])
    c = [x for x in sonidos_imp if abs(x[0] - e['t']) < 0.06 and x[1] != 'impact_flesh']
    return min(c, key=lambda x: (x[2] - p).length)[1] if c else 'impact_concrete'
GR = 9.8
def balistico(o, k0, p, v, vida_k, escala, flat=True, rebote=False):
    clave(o, 1, esc=(0, 0, 0)); clave(o, k0 - 1, esc=(0, 0, 0)); clave(o, k0, loc=p, esc=escala)
    pos = Vector(p); vel = Vector(v); k = k0
    for i in range(1, vida_k + 1):
        vel.z -= GR / FPS_S; pos = pos + vel / FPS_S; k = k0 + i
        if pos.z <= 0.015:
            pos.z = 0.015; clave(o, k, loc=pos, esc=(escala[0] * 1.6, escala[1] * 1.6, escala[2] * 0.25) if flat else escala); return
        clave(o, k, loc=pos)
for e in disp:
    p = G(e['x'], e['y'], e['z']); s = tiro_de(e); n_b = G(e['nx'], e['ny'], e['nz']); n_b = n_b.normalized() if n_b.length > 0 else Vector((0, -1, 0))
    d = (p - s['pos']).normalized() if s else Vector((1, 0, 0))
    k0 = kk(e['t'])
    if e['tipo'] == 'bullet':
        for i in range(SANG.get(e['zona'], 14)):
            o = nuevo('esfera', M_SANGRE, 'sangre'); r = rnd.uniform(0.02, 0.06)
            v = d * rnd.uniform(1.2, 5.5) + n_b * rnd.uniform(0.3, 2.8) + Vector((rnd.gauss(0, 1.0), rnd.gauss(0, 1.0), rnd.gauss(0, 1.0))) + Vector((0, 0, rnd.uniform(0.2, 1.8)))
            balistico(o, k0, p + Vector((rnd.gauss(0, .02), rnd.gauss(0, .02), rnd.gauss(0, .02))), v, 70, (r, r, r))
        for i in range(2):                               # bolas grandes (sangre que sale a chorro)
            o = nuevo('esfera', M_SANGRE, 'sangre'); r = rnd.uniform(0.07, 0.11); v = d * rnd.uniform(1.0, 2.6) + n_b * rnd.uniform(0.3, 1.0) + Vector((0, rnd.gauss(0, .4), rnd.uniform(0.3, 1.2)))
            balistico(o, k0, p, v, 60, (r, r, r))
    else:
        tp = tipo_mundo(e)
        if tp == 'impact_metal':                          # chispas
            for i in range(18):
                o = nuevo('esfera', M_CHISPA, 'fx'); r = rnd.uniform(0.012, 0.03); v = n_b * rnd.uniform(1.5, 5.0) + Vector((rnd.gauss(0, 1.8), rnd.gauss(0, 1.8), rnd.gauss(0, 1.8)))
                balistico(o, k0, p, v, 14, (r, r, r), flat=False); clave(o, k0 + 15, esc=(0, 0, 0))
        elif tp in ('impact_concrete',):                  # polvo y esquirlas
            for i in range(4):
                o = nuevo('esfera', M_POLVO, 'fx'); v = n_b * rnd.uniform(0.2, 0.8) + Vector((rnd.gauss(0, .3), rnd.gauss(0, .3), rnd.uniform(0.1, 0.6)))
                clave(o, 1, esc=(0, 0, 0)); clave(o, k0 - 1, esc=(0, 0, 0))
                for j in range(0, 22, 3): clave(o, k0 + j, loc=p + v * (j / 30.0), esc=0.05 + 0.20 * math.sin(min(j / 21.0, 1) * math.pi * 0.9) * (0.7 + 0.5 * i / 4))
                clave(o, k0 + 24, esc=(0, 0, 0))
            for i in range(10):
                o = nuevo('cubo', M_POLVO, 'fx'); r = rnd.uniform(0.012, 0.04); v = n_b * rnd.uniform(1.0, 3.5) + Vector((rnd.gauss(0, 1.2), rnd.gauss(0, 1.2), rnd.gauss(0, 1.2)))
                balistico(o, k0, p, v, 60, (r, r, r), flat=False)
        elif tp.startswith('impact_wood') or tp.startswith('wood'):
            for i in range(9):
                o = nuevo('cubo', M_MADERA2, 'fx'); v = n_b * rnd.uniform(1.0, 3.5) + Vector((rnd.gauss(0, 1.5), rnd.gauss(0, 1.5), rnd.uniform(0.5, 2.5)))
                balistico(o, k0, p, v, 60, (rnd.uniform(0.01, 0.025), rnd.uniform(0.02, 0.07), rnd.uniform(0.01, 0.025)), flat=False)
# ───────── ruptura del cajón de madera (sonido wood_break): lluvia de tablas y astillas ─────────
for t, snd, p in sonidos_imp:
    if snd != 'wood_break': continue
    k0 = kk(t)
    for i in range(34):
        o = nuevo('cubo', M_MADERA if i % 2 else M_MADERA2, 'fx'); big = i < 10
        esc = (rnd.uniform(0.03, 0.06), rnd.uniform(0.22, 0.45), rnd.uniform(0.02, 0.04)) if big else (rnd.uniform(0.02, 0.05), rnd.uniform(0.04, 0.12), rnd.uniform(0.015, 0.03))
        v = Vector((rnd.gauss(0, 1.8), rnd.gauss(0, 1.0), rnd.uniform(1.5, 4.5)))
        o.rotation_euler = (rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)); w = Vector((rnd.gauss(0, 6), rnd.gauss(0, 6), rnd.gauss(0, 6)))
        clave(o, 1, esc=(0, 0, 0)); clave(o, k0 - 1, esc=(0, 0, 0)); clave(o, k0, loc=p, esc=esc, rot=o.rotation_euler)
        pos = Vector(p); vel = v.copy(); rot = Vector(o.rotation_euler)
        for j in range(1, 70):
            vel.z -= GR / FPS_S; pos = pos + vel / FPS_S; rot = rot + w / FPS_S
            if pos.z <= max(esc) * 0.5:
                pos.z = max(esc) * 0.5; clave(o, k0 + j, loc=pos, rot=(rot.x, rot.y, rot.z)); break
            clave(o, k0 + j, loc=pos, rot=(rot.x, rot.y, rot.z))
    for i in range(6):                                  # polvo de la rotura
        o = nuevo('esfera', M_POLVO, 'fx'); v = Vector((rnd.gauss(0, .7), rnd.gauss(0, .5), rnd.uniform(0.2, 0.9)))
        clave(o, 1, esc=(0, 0, 0)); clave(o, k0 - 1, esc=(0, 0, 0))
        for j in range(0, 30, 3): clave(o, k0 + j, loc=p + v * (j / 30.0), esc=0.08 + 0.32 * math.sin(min(j / 29.0, 1) * math.pi * 0.9))
        clave(o, k0 + 31, esc=(0, 0, 0))
# ───────── render ─────────
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 1280, 720, 100, 30
cy = sc.cycles; cy.device = 'CPU'; cy.samples = 12; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.max_bounces = 6; cy.seed = 26
if hasattr(cy, 'use_light_tree'): cy.use_light_tree = True
sc.view_settings.view_transform = 'Standard'; sc.frame_start, sc.frame_end = 1, 1000
for o in bpy.data.objects:                              # nubes sin material del GLB (humo del juego): gris liso y color directo en el estilo E
    if o.type == 'MESH' and o.name.startswith('Icosphere') and not o.data.materials: o.data.materials.append(M_HUMO); o['clase'] = 'fx'
bpy.ops.wm.save_as_mainfile(filepath=SAL, compress=True)
print('DISPAROS por tipo:', {x['k'] for x in tiros}); print('GUARDADO', SAL, 'efectos:', N['n'], 'disparos:', len(tiros), 'impactos:', len(disp))
