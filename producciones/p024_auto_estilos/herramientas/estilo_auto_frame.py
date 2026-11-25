"""Renderiza cuadros del giro alrededor del auto y los compone en los 5 tratamientos: original (Blender con todos sus efectos), C contorno de silueta, D líneas de pantalla,
E combinado (toon + silueta + pliegues) e híbrido «lápices de color». Mide tiempo por pasada, memoria y CPU.
Uso: python estilo_auto_frame.py BLEND DESDE HASTA SALIDA   (bpy 5.3 como módulo o /opt/tools/blendenv/bin/python)"""
import bpy, sys, os, json, time, math, resource, platform
import numpy as np
from PIL import Image, ImageFilter
BLEND, DESDE, HASTA, SAL = sys.argv[-4], int(sys.argv[-3]), int(sys.argv[-2]), sys.argv[-1]
for e in ('original', 'C', 'D', 'E', 'hibrido'): os.makedirs(f'{SAL}/{e}', exist_ok=True)
os.makedirs(f'{SAL}/pasadas', exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND); sc = bpy.context.scene; r = sc.render
W, H = r.resolution_x, r.resolution_y
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
orig = {o.name: list(o.data.materials) for o in meshes}
def clase(o): return o.get('clase', 'auto')
T = {}
def cuadros(): return range(DESDE, HASTA + 1)
def cycles(muestras, filtro=1.5, denoise=False, rebotes=4):
    cy = sc.cycles; cy.samples = muestras; cy.use_adaptive_sampling = muestras > 2; cy.use_denoising = denoise; cy.max_bounces = rebotes; cy.pixel_filter_type = 'BLACKMAN_HARRIS'; cy.filter_width = filtro
def render(nombre, f):
    sc.frame_set(f); r.filepath = f'{SAL}/pasadas/{nombre}_{f:04d}.png'; t = time.time(); bpy.ops.render.render(write_still=True); T.setdefault(nombre, []).append(round(time.time() - t, 2))
def mat_tipo(tipo, col=None):
    m = bpy.data.materials.new('P_' + tipo); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); out = nt.nodes.new('ShaderNodeOutputMaterial')
    if tipo == 'transparente':
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); nt.links.new(tr.outputs[0], out.inputs[0]); return m
    if tipo == 'arcilla':
        bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1); bs.inputs['Roughness'].default_value = 1.0; nt.links.new(bs.outputs[0], out.inputs[0]); return m
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(em.outputs[0], out.inputs[0])
    if tipo == 'normal':
        g = nt.nodes.new('ShaderNodeNewGeometry'); mv = nt.nodes.new('ShaderNodeVectorMath'); mv.operation = 'MULTIPLY_ADD'; mv.inputs[1].default_value = (0.5, 0.5, 0.5); mv.inputs[2].default_value = (0.5, 0.5, 0.5); nt.links.new(g.outputs['Normal'], mv.inputs[0]); nt.links.new(mv.outputs[0], em.inputs['Color'])
    elif tipo == 'prof':
        cd = nt.nodes.new('ShaderNodeCameraData'); dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = 128.0; nt.links.new(cd.outputs['View Z Depth'], dv.inputs[0]); nt.links.new(dv.outputs[0], em.inputs['Color'])
    else: em.inputs['Color'].default_value = (*col, 1)
    return m
def poner(fn):
    for o in meshes: fn(o)
def asignar(o, m): o.data.materials.clear(); o.data.materials.append(m)
def restaurar():
    for o in meshes:
        o.data.materials.clear()
        for m in orig[o.name]: o.data.materials.append(m)
t0 = time.time()
# 1) COLOR: el render «normal» de Blender (32 muestras, OIDN, desenfoque de profundidad, reflejos, rebotes)
cy = sc.cycles; cy.samples = 32; cy.use_denoising = True
for f in cuadros(): render('color', f)
# 2) ARCILLA (blanca con luz y sombra)
MT = mat_tipo('transparente'); MA = mat_tipo('arcilla'); cycles(8, 1.5, True, 3)
poner(lambda o: asignar(o, MT if 'lights' in ' '.join(m.name for m in orig[o.name] if m) and False else MA))
for f in cuadros(): render('arcilla', f)
# 3) NORMALES, PROFUNDIDAD y CLASES (1 muestra, emisión; sin desenfoque de profundidad)
sc.camera.data.dof.use_dof = False
w0 = sc.world; wn = bpy.data.worlds.new('N'); wn.use_nodes = True; wn.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1); sc.world = wn
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
cycles(1, 1.0, False, 0)
MN = mat_tipo('normal'); poner(lambda o: asignar(o, MN))
for f in cuadros(): render('normales', f)
r.image_settings.color_depth = '16'; r.image_settings.color_mode = 'BW'
MD = mat_tipo('prof'); poner(lambda o: asignar(o, MD))
for f in cuadros(): render('prof', f)
r.image_settings.color_depth = '8'; r.image_settings.color_mode = 'RGB'
COL = {'auto': (1, 0, 0), 'suelo': (0, 1, 0), 'fondo': (1, 1, 0)}
cycles(1, 0.01, False, 0)
MC = {k: mat_tipo('c', v) for k, v in COL.items()}; poner(lambda o: asignar(o, MC[clase(o)]))
for f in cuadros(): render('clases', f)
T['pasadas_total_s'] = round(time.time() - t0, 1)
# cámara: datos para reconstruir la posición (toon: vector a la cámara)
sol = bpy.data.objects['Sol']; dsol = (sol.matrix_world.to_3x3() @ __import__('mathutils').Vector((0, 0, -1))).normalized()
# ───────────────── composición (numpy) ─────────────────
PAPEL = np.array([0.97, 0.965, 0.95], dtype=np.float32); FONDO = 0.84; TINTA = np.array([0.07, 0.07, 0.08], dtype=np.float32)
lum = lambda x: x[..., 0] * 0.299 + x[..., 1] * 0.587 + x[..., 2] * 0.114
def sup(m, rr=0.7): return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rr)), dtype=np.float32) / 255.0
def ensanchar(m, rad):
    out = m.copy()
    for dx in range(-rad, rad + 1):
        for dy in range(-rad, rad + 1):
            if dx * dx + dy * dy <= rad * rad + 1: out = np.maximum(out, np.roll(np.roll(m, dx, 1), dy, 0))
    return out
rng = np.random.default_rng(5); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
grano = rng.normal(0, 1, (H, W)).astype(np.float32); grano = sup(np.clip(grano * 0.5 + 0.5, 0, 1), 0.6) - 0.5          # papel: grano fijo
fibra = sup(np.clip(rng.normal(0, 1, (H, W)).astype(np.float32) * 0.5 + 0.5, 0, 1), 3.0) - 0.5
TC = {}
def _t(k, t): TC[k] = TC.get(k, 0.0) + (time.time() - t)
def compuesto(f):
    _t0 = time.time()
    rgb = lambda n: np.asarray(Image.open(f'{SAL}/pasadas/{n}_{f:04d}.png').convert('RGB'), dtype=np.float32) / 255.0
    color, arcilla, nor, cla = rgb('color'), rgb('arcilla'), rgb('normales'), rgb('clases')
    pro = np.asarray(Image.open(f'{SAL}/pasadas/prof_{f:04d}.png')).astype(np.float32); pro = pro / (65535.0 if pro.max() > 255 else 255.0)
    z = pro * 128.0; cielo = (z < 0.5); n = nor * 2 - 1
    es = lambda c, tol=0.3: np.all(np.abs(cla - np.array(c, dtype=np.float32)) < tol, axis=-1)
    m_auto = es((1, 0, 0)); m_suelo = es((0, 1, 0)); m_fondo = es((1, 1, 0))
    lit = np.clip(lum(arcilla) / 0.80, 0, 1); alb = np.clip(lum(color) / np.maximum(lit, 0.25), 0, 1)
    # --- aristas ---
    zz = np.maximum(z, 0.3)
    def lin_edges(th=0.04, w=1.5):
        e = np.zeros_like(zz); k = int(round(w))
        for dx, dy in ((k, 0), (0, k), (-k, 0), (0, -k)): e = np.maximum(e, (np.abs(np.roll(np.roll(zz, dx, 1), dy, 0) - zz) > th * zz).astype(np.float32))
        return e
    e_prof = lin_edges(); g = np.maximum(np.abs(np.roll(cla, -1, 1) - cla), np.abs(np.roll(cla, -1, 0) - cla)).max(axis=-1); g[-1, :] = 0; g[:, -1] = 0; e_clase = (g > 0.3).astype(np.float32)
    plieg = np.zeros_like(e_prof)
    for dx, dy in ((1, 0), (0, 1)):
        nn = np.roll(np.roll(n, -dx, 1), -dy, 0); zn = np.roll(np.roll(z, -dx, 1), -dy, 0)
        plieg = np.maximum(plieg, ((np.abs((n * nn).sum(-1)) < 0.90) & (np.abs(zn - z) < 0.03 * zz)).astype(np.float32))
    plieg[cielo] = 0
    k2 = 2; segunda = (np.maximum(np.abs(np.roll(zz, k2, 1) + np.roll(zz, -k2, 1) - 2 * zz), np.abs(np.roll(zz, k2, 0) + np.roll(zz, -k2, 0) - 2 * zz)) > 0.010 * zz) & ~cielo
    cl = lum(color); gx = np.abs(np.roll(cl, -1, 1) - cl) + np.abs(np.roll(cl, -1, 0) - cl); detalle = ((gx > 0.10) & m_auto).astype(np.float32)      # juntas de chapa, vidrios, parrilla, llantas
    sil = np.maximum(e_prof, e_clase)
    pix_m = (2 * np.maximum(z, 1.0) * math.tan(sc.camera.data.angle_y / 2)) / H
    ancho = np.clip(0.012 * np.clip(z * 0.35, 0.6, 3.0) * 1.1 / pix_m, 1.0, 2.7)
    silu = np.maximum(ensanchar(sil * (ancho < 1.5), 0), ensanchar(sil * (ancho >= 1.5), 1)); silu = sup(silu, 0.55)
    def tinta(img, m, kk=1.0, col=TINTA): return img * (1 - (m * kk)[..., None]) + col[None, None, :] * (m * kk)[..., None]
    _t('comun_lectura_y_aristas', _t0); _t0 = time.time()
    # --- A plano (base para C) ---
    nz, nx, ny = n[..., 2], n[..., 0], n[..., 1]
    tt = np.where(nz > 0.6, 1.0, np.where(nz < -0.6, 0.8, np.where(np.abs(ny) > np.abs(nx), 0.93, 0.86)))
    tint = 0.50 + 0.50 * np.clip(alb * 1.3, 0, 1); A = PAPEL[None, None, :] * (tt * (0.35 + 0.65 * tint))[..., None]; A[cielo] = FONDO
    Cimg = tinta(A, silu); _t('C_plano_y_silueta', _t0); _t0 = time.time()
    # --- D líneas de pantalla: profundidad + 2.ª derivada + juntas del auto; 4 tonos de papel ---
    g4 = np.floor(cl * 4.0 + 0.5) / 4.0; Dm = (g4 * 0.2 + 0.8)[..., None] * np.ones((1, 1, 3), dtype=np.float32); Dm[cielo] = FONDO
    Dm = tinta(Dm, sup(np.maximum(np.maximum(e_prof, segunda.astype(np.float32) * 0.8), detalle * 0.7), 0.5))
    _t('D_lineas_pantalla', _t0); _t0 = time.time()
    # --- E combinado: toon con sombra + silueta + pliegues finos + juntas ---
    band = np.floor(lit * 3.0 + 0.5) / 3.0; sombra = 0.64 + 0.36 * band; tn = 0.72 + 0.28 * np.clip(alb * 1.35, 0, 1)
    sx = (xx + 0.5) / W * 2 - 1; sy = 1 - (yy + 0.5) / H * 2
    M = sc.camera.matrix_world; fwd = -(M.to_3x3() @ __import__('mathutils').Vector((0, 0, 1))); rig = M.to_3x3() @ __import__('mathutils').Vector((1, 0, 0)); upv = M.to_3x3() @ __import__('mathutils').Vector((0, 1, 0))
    tv = math.tan(sc.camera.data.angle_y / 2); thh = tv * W / H
    ray = np.array(fwd)[None, None, :] + np.array(rig)[None, None, :] * (sx * thh)[..., None] + np.array(upv)[None, None, :] * (sy * tv)[..., None]
    P = np.array(M.translation)[None, None, :] + ray * z[..., None]; V = np.array(M.translation)[None, None, :] - P; V /= np.maximum(np.linalg.norm(V, axis=-1, keepdims=True), 1e-6)
    Ld = -np.array(dsol)[None, None, :]; Hv = Ld + V; Hv /= np.maximum(np.linalg.norm(Hv, axis=-1, keepdims=True), 1e-6)
    ndl = np.clip((n * Ld).sum(-1), 0, 1); espec = (np.power(np.clip((n * Hv).sum(-1), 0, 1), 24) * (lit > 0.6)) > 0.90; rim = np.power(1 - np.clip((n * V).sum(-1), 0, 1), 3.0) * ndl * 0.18
    B = (tn * sombra + rim)[..., None] * PAPEL[None, None, :]; B = np.where(espec[..., None], np.clip(B + 0.2, 0, 1), B); B[cielo] = FONDO
    Eimg = tinta(B, sup(np.maximum(plieg, detalle * 0.8), 0.5), 0.75); Eimg = tinta(Eimg, silu, 0.95)
    _t('E_toon_y_pliegues', _t0); _t0 = time.time()
    # --- original: grano de película, viñeta suave y brillo (bloom) sobre el render de Blender ---
    brillo = sup(np.clip(lum(color) - 0.80, 0, 1) * 3.0, 6.0)[..., None] * 0.35; vig = 1 - 0.18 * np.clip(((sx ** 2) * 0.6 + (sy ** 2) * 0.4), 0, 1)[..., None]
    Orig = np.clip((color + brillo) * vig, 0, 1)
    _t('original_bloom_vineta', _t0); _t0 = time.time()
    # --- híbrido «lápices de color»: D con colores tenues, sombreado rayado, brillos blancos, papel con grano ---
    gris = lum(color)[..., None]; pastel = gris + (color - gris) * 0.45; pastel = pastel * 0.74 + PAPEL[None, None, :] * 0.26
    niv = np.round(gris * 6) / 6.0; pastel = pastel * (0.55 + 0.45 * (niv / np.maximum(gris, 0.05)))
    sombra_m = (lit < 0.55) & ~cielo; hondo = (lit < 0.28) & ~cielo
    trama1 = ((xx + yy) % 6.0) < 1.25; trama2 = ((xx - yy) % 6.0) < 1.0
    lapiz = (sombra_m & trama1).astype(np.float32) * 0.62 + (hondo & trama2).astype(np.float32) * 0.55
    lapiz *= (0.8 + 0.4 * (grano + 0.5))
    base_oscura = pastel * 0.55
    H_ = pastel * (1 - sup(lapiz, 0.5)[..., None]) + base_oscura * sup(lapiz, 0.5)[..., None]
    cielo_c = np.array([0.80, 0.85, 0.90], dtype=np.float32)[None, None, :] * 0.5 + PAPEL[None, None, :] * 0.5; H_[cielo] = cielo_c[0, 0]
    H_ = np.where((cl > 0.88)[..., None] & ~cielo[..., None], np.clip(H_ + 0.35, 0, 1), H_)                                    # brillos: papel blanco
    lineas = sup(np.maximum(np.maximum(e_prof, segunda.astype(np.float32) * 0.8), np.maximum(detalle * 0.8, ensanchar(sil, 1) * 0.9)), 0.55)
    lineas *= (0.70 + 0.45 * (grano + 0.5)); lineas = np.clip(lineas, 0, 1)
    lapiz_col = np.array([0.20, 0.19, 0.24], dtype=np.float32)
    H_ = H_ * (1 - (lineas * 0.85)[..., None]) + lapiz_col[None, None, :] * (lineas * 0.85)[..., None]
    H_ = np.clip(H_ * (1 + 0.05 * grano[..., None] + 0.04 * fibra[..., None]), 0, 1)
    _t('hibrido_lapices', _t0); _t0 = time.time()
    for nombre, img in (('original', Orig), ('C', Cimg), ('D', Dm), ('E', Eimg), ('hibrido', H_)):
        Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'{SAL}/{nombre}/f_{f:04d}.png')
t1 = time.time()
for f in cuadros(): compuesto(f)
T['composicion_total_s'] = round(time.time() - t1, 1); T['composicion_por_estilo_s'] = {k: round(v / max(HASTA - DESDE + 1, 1), 2) for k, v in TC.items()}; T['tiempo_total_s'] = round(time.time() - t0, 1)
T['cuadros'] = HASTA - DESDE + 1; T['memoria_max_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 0); T['cpus'] = os.cpu_count(); T['maquina'] = platform.processor() or platform.machine()
json.dump(T, open(f'{SAL}/informe_{DESDE:04d}_{HASTA:04d}.json', 'w'), indent=1); print('LISTO', json.dumps({k: v for k, v in T.items() if not isinstance(v, list)}))
