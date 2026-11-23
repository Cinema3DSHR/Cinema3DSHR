"""Biblioteca de plantas REALES para la nave (Blender): hojas con nervaduras y translucidez, rosas con pétalos en capas, ficus, helecho, enredadera y planta de hojas anchas.
Cada planta es UN objeto con 3 formas (shape keys) de viento/aleteo animadas en bucle (3,2 s) → se exportan a GLB y Godot las reproduce solas.
Uso: blender -b -P plantas.py -- salida_dir"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix, Euler
SAL = sys.argv[sys.argv.index('--') + 1]
os.makedirs(SAL, exist_ok=True)
TEX = os.path.join(SAL, "tex"); os.makedirs(TEX, exist_ok=True)
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# ───────────────────────── texturas de hoja (nervadura central y laterales, variación de color)
def tex_hoja(nombre, base, borde, vena, ancho=256, alto=512, laterales=11, seed=1):
    rng = np.random.default_rng(seed)
    im = Image.new("RGB", (ancho, alto)); px = np.zeros((alto, ancho, 3), np.float32)
    yy, xx = np.mgrid[0:alto, 0:ancho]
    u = yy / alto; v = np.abs(xx - ancho / 2) / (ancho / 2)
    t = np.clip(u * 0.8 + v * 0.5, 0, 1)[..., None]
    px[:] = np.array(base) * (1 - t) + np.array(borde) * t
    ruido = rng.random((alto // 16, ancho // 16)).astype(np.float32)
    ruido = np.asarray(Image.fromarray((ruido * 255).astype(np.uint8)).resize((ancho, alto), Image.BICUBIC), np.float32) / 255
    px *= (0.85 + 0.3 * ruido)[..., None]
    im = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.line([(ancho / 2, alto), (ancho / 2, 0)], fill=tuple(vena), width=7)
    for k in range(laterales):
        y0 = alto - (k + 0.6) * alto / (laterales + 1)
        for s in (-1, 1):
            d.line([(ancho / 2, y0), (ancho / 2 + s * ancho * 0.46, y0 - alto * 0.16)], fill=tuple(vena), width=3)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    ruta = os.path.join(TEX, nombre + ".png"); im.save(ruta); return ruta

def mat_hoja(nombre, ruta):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(ruta)
    nt.links.new(tx.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.42
    for k, v in (('Subsurface Weight', 0.2), ('Specular IOR Level', 0.5)):
        try: p.inputs[k].default_value = v
        except Exception: pass
    try: p.inputs['Subsurface Radius'].default_value = (0.3, 0.5, 0.1)
    except Exception: pass
    m.use_backface_culling = False
    return m

def mat_simple(nombre, col, rug=0.6, met=0.0, sheen=0.0, sss=0.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rug; p.inputs['Metallic'].default_value = met
    for k, v in (('Sheen Weight', sheen), ('Subsurface Weight', sss)):
        try: p.inputs[k].default_value = v
        except Exception: pass
    return m

def mat_petalo(nombre, centro, borde):
    """Pétalo con degradado centro→borde por UV.y, como imagen (así viaja en el GLB; un degradado procedural se exportaba blanco)."""
    from PIL import Image
    n = 64
    im = Image.new('RGB', (4, n))
    for j in range(n):
        f = j / (n - 1)
        c = tuple(int(255 * (((centro[i] * (1 - f) + borde[i] * f)) ** (1 / 2.2))) for i in range(3))
        for i in range(4): im.putpixel((i, j), c)
    ruta = os.path.join(TEX, nombre + '_%d%d%d.png' % tuple(int(x * 9) for x in borde)); im.save(ruta)
    m = bpy.data.materials.new(nombre); m.use_nodes = True; nt = m.node_tree; p = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(ruta); tx.interpolation = 'Linear'; tx.extension = 'EXTEND'
    nt.links.new(tx.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.5
    for k, v in (('Sheen Weight', 0.8), ('Subsurface Weight', 0.3)):
        try: p.inputs[k].default_value = v
        except Exception: pass
    m.use_backface_culling = False
    return m

# ───────────────────────── geometría base
def nuevo():
    return bmesh.new()

def hoja_bm(bm, L=0.25, W=0.1, bend=0.4, fold=0.3, mat=0, nu=12, nv=6, punta=0.7, M=Matrix.Identity(4), ondul=0.0, seed=0):
    rng = random.Random(seed)
    filas = []
    for i in range(nu + 1):
        u = i / nu
        w = W * (math.sin(math.pi * min(1.0, u ** 0.8)) ** 0.9) * (1 - 0.35 * u) if punta else W * math.sin(math.pi * u)
        fila = []
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            x = v * w; y = u * L
            z = bend * L * u * u - fold * abs(v) * w + ondul * math.sin(u * 9 + v * 3) * w * 0.25
            vert = bm.verts.new(M @ Vector((x, y, z)))
            fila.append((vert, (j / nv, u)))
        filas.append(fila)
    uv = bm.loops.layers.uv.verify()
    for i in range(nu):
        for j in range(nv):
            a, b, c, d = filas[i][j], filas[i][j + 1], filas[i + 1][j + 1], filas[i + 1][j]
            try: f = bm.faces.new((a[0], b[0], c[0], d[0]))
            except ValueError: continue
            f.material_index = mat; f.smooth = True
            for l, pt in zip(f.loops, (a, b, c, d)): l[uv].uv = pt[1]
    return filas

def tallo_bm(bm, puntos, r0, r1, mat, seg=6):
    """Tubo a lo largo de una polilínea (radios r0→r1)."""
    anillos = []
    n = len(puntos)
    for i, p in enumerate(puntos):
        t = i / (n - 1); r = r0 + (r1 - r0) * t
        d = (puntos[min(i + 1, n - 1)] - puntos[max(i - 1, 0)]).normalized()
        a = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        ex = d.cross(a).normalized(); ey = d.cross(ex).normalized()
        anillos.append([bm.verts.new(p + (ex * math.cos(2 * math.pi * k / seg) + ey * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)])
    for i in range(n - 1):
        for k in range(seg):
            f = bm.faces.new((anillos[i][k], anillos[i][(k + 1) % seg], anillos[i + 1][(k + 1) % seg], anillos[i + 1][k])); f.material_index = mat; f.smooth = True

def curva(p0, p1, p2, n=10):
    return [((1 - t) ** 2) * p0 + 2 * (1 - t) * t * p1 + t * t * p2 for t in [i / (n - 1) for i in range(n)]]

def maceta_bm(bm, radio=0.14, alto=0.2, mat=0):
    anillos = []
    perf = [(radio * 0.78, 0), (radio * 0.8, 0.01), (radio * 0.95, alto * 0.9), (radio, alto), (radio * 0.93, alto), (radio * 0.9, alto - 0.015), (radio * 0.7, 0.03)]
    for (r, z) in perf:
        anillos.append([bm.verts.new((math.cos(2 * math.pi * k / 24) * r, math.sin(2 * math.pi * k / 24) * r, z)) for k in range(24)])
    for i in range(len(anillos) - 1):
        for k in range(24):
            f = bm.faces.new((anillos[i][k], anillos[i][(k + 1) % 24], anillos[i + 1][(k + 1) % 24], anillos[i + 1][k])); f.material_index = mat; f.smooth = True
    # tierra
    c = bm.verts.new((0, 0, alto - 0.03)); borde = [bm.verts.new((math.cos(2 * math.pi * k / 24) * radio * 0.9, math.sin(2 * math.pi * k / 24) * radio * 0.9, alto - 0.03)) for k in range(24)]
    for k in range(24):
        f = bm.faces.new((c, borde[(k + 1) % 24], borde[k])); f.material_index = mat + 1

# ───────────────────────── rosa
def petalo_bm(bm, M, R=0.03, alto=0.04, abre=0.4, mat=0, n=7):
    filas = []
    for i in range(n + 1):
        t = i / n
        fila = []
        for j in range(n + 1):
            a = -1 + 2 * j / n
            ang = a * 1.0
            x = math.sin(ang) * R * (0.55 + 0.45 * t)
            yb = (1 - math.cos(ang)) * R * 0.5
            y = -yb - abre * R * (t ** 2) * 1.4
            z = alto * t * (1 - 0.35 * a * a) + (abre * R * 0.4 * (t ** 3))
            # borde superior ondulado y rizado hacia fuera
            if t > 0.8: y -= abre * R * 0.6 * (t - 0.8) * 4 * (0.6 + 0.4 * math.cos(a * 2))
            fila.append((bm.verts.new(M @ Vector((x, y - R * 0.55, z))), (j / n, t)))
        filas.append(fila)
    uv = bm.loops.layers.uv.verify()
    for i in range(n):
        for j in range(n):
            a, b, c, d = filas[i][j], filas[i][j + 1], filas[i + 1][j + 1], filas[i + 1][j]
            f = bm.faces.new((a[0], b[0], c[0], d[0])); f.material_index = mat; f.smooth = True
            for l, pt in zip(f.loops, (a, b, c, d)): l[uv].uv = pt[1]

def flor_rosa_bm(bm, centro, M, matp, mats, escala=1.0, seed=0):
    rng = random.Random(seed)
    # capas de pétalos: (cantidad, radio, inclinación, abre)
    capas = [(3, 0.012, 2, 0.0), (4, 0.017, 5, 0.0), (5, 0.022, 9, 0.02), (6, 0.027, 14, 0.06), (7, 0.032, 20, 0.12), (8, 0.037, 27, 0.2), (9, 0.042, 34, 0.3)]
    base = M @ Matrix.Translation(centro)
    for k, (n, R, inc, ab) in enumerate(capas):
        for i in range(n):
            ang = (i / n) * 2 * math.pi + k * 0.83 + rng.uniform(-0.12, 0.12)
            Mp = base @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation((0, -R * 0.25, k * 0.004)) @ Matrix.Rotation(math.radians(inc + rng.uniform(-4, 4)), 4, 'X') @ Matrix.Scale(escala, 4)
            petalo_bm(bm, Mp, R * escala, 0.085 * escala * (1 + 0.06 * k), ab, matp)
    # cáliz: sépalos
    for i in range(5):
        ang = i / 5 * 2 * math.pi
        Ms = base @ Matrix.Translation((0, 0, -0.012)) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Rotation(math.radians(115), 4, 'X')
        hoja_bm(bm, 0.05 * escala, 0.008 * escala, 0.1, 0.1, 2, 6, 3, M=Ms)

def rosa(nombre_mat, col_centro, col_borde, alto=0.55, seed=0, flores=1, M0=Matrix.Identity(4)):
    pass

# ───────────────────────── ensamblado
def objeto_desde(bm, nombre, mats):
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(nombre, me); bpy.context.scene.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    return o

def viento(o, altura, amp=0.05, flutter=0.015, periodo=96, seed=0):
    """3 formas: A (flexión hacia +X), B (flexión hacia +Y / torsión) y C (aleteo de hojas por ruido). Animación en bucle con senos."""
    rng = random.Random(seed)
    me = o.data
    o.shape_key_add(name='Basis')
    ks = [o.shape_key_add(name=n) for n in ('viento_A', 'viento_B', 'aleteo')]
    base = [v.co.copy() for v in me.vertices]
    fase = {}
    for i, v in enumerate(base):
        h = max(0.0, v.z) / max(altura, 0.01)
        f = h ** 1.6
        ks[0].data[i].co = v + Vector((amp * f, 0.2 * amp * f * math.sin(h * 5), -0.2 * amp * f * f))
        ks[1].data[i].co = v + Vector((0.3 * amp * f, amp * f, 0.0))
        # aleteo: ruido espacial (grupos por celda de 3 cm)
        cx, cy, cz = int(v.x / 0.03), int(v.y / 0.03), int(v.z / 0.03)
        r = random.Random(hash((cx, cy, cz, seed)) & 0xffff)
        ks[2].data[i].co = v + Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * flutter * (0.3 + h)
    sc = bpy.context.scene; sc.render.fps = 30
    for k, (key, ph, f) in enumerate(zip(ks, (0.0, 1.9, 0.6), (1, 1, 3))):
        for fr in range(0, periodo + 1, 4):
            key.value = 0.5 + 0.5 * math.sin(2 * math.pi * f * fr / periodo + ph); key.keyframe_insert('value', frame=fr + 1)
    if me.shape_keys.animation_data and me.shape_keys.animation_data.action:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(me.shape_keys.animation_data.action, me.shape_keys.animation_data.action_slot)
        for fc in (cb.fcurves if cb else []):
            for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
    sc.frame_start, sc.frame_end = 1, periodo + 1

def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for a in list(bpy.data.images): bpy.data.images.remove(a)

def exportar(o, nombre):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=os.path.join(SAL, nombre + ".glb"), export_format='GLB', use_selection=True, export_morph=True, export_animations=True,
                              export_animation_mode='ACTIONS', export_apply=False, export_image_format='AUTO', export_yup=True)
    print("EXPORTADO", nombre, len(o.data.vertices), "vértices", flush=True)

def maceta_mats():
    return [mat_simple('maceta', (0.72, 0.70, 0.66), 0.55), mat_simple('tierra', (0.10, 0.06, 0.04), 0.95)]

def luz_demo(sc):
    w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.5, 0.55, 0.62, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0; sc.world = w
    l = bpy.data.lights.new('s', 'SUN'); l.energy = 3.0; lo = bpy.data.objects.new('s', l); sc.collection.objects.link(lo); lo.rotation_euler = (math.radians(55), 0, math.radians(35))

# ───────────────────────── plantas
def planta_rosal(nombre, col_c, col_b, seed, flores=5, h=0.7):
    limpiar()
    t1 = tex_hoja('rosa_hoja', (46, 128, 44), (26, 84, 30), (140, 200, 110), seed=seed)
    mh = mat_hoja('hoja_rosa', t1); mv = mat_simple('tallo', (0.18, 0.32, 0.12), 0.6)
    mp = mat_petalo('petalo', col_c, col_b); ms = mat_simple('sepalo', (0.18, 0.4, 0.15), 0.5)
    mm, mt = maceta_mats()
    bm = nuevo(); rng = random.Random(seed)
    maceta_bm(bm, 0.17, 0.22, 4)
    for f in range(flores):
        ang = f / flores * 2 * math.pi + rng.uniform(-0.3, 0.3); rad = rng.uniform(0.03, 0.09)
        base = Vector((math.cos(ang) * rad, math.sin(ang) * rad, 0.2))
        alt = h * rng.uniform(0.7, 1.05)
        punta = base + Vector((math.cos(ang) * rng.uniform(0.05, 0.14), math.sin(ang) * rng.uniform(0.05, 0.14), alt))
        pts = curva(base, base + Vector((0, 0, alt * 0.6)) + Vector((math.cos(ang), math.sin(ang), 0)) * 0.03, punta, 14)
        tallo_bm(bm, pts, 0.0065, 0.005, 1, 6)
        # espinas
        for k in range(2, 12, 2):
            p = pts[k]; d = (pts[k + 1] - pts[k - 1]).normalized(); nx = d.cross(Vector((0, 0, 1))).normalized() if abs(d.z) < 0.95 else Vector((1, 0, 0))
            tallo_bm(bm, [p, p + nx * 0.012 + d * 0.004], 0.0025, 0.0004, 1, 4)
        # hojas compuestas (3 foliolos) cada tramo
        for k in (3, 6, 9):
            p = pts[k]; az = rng.uniform(0, 6.28)
            for s, (da, ln, dist) in enumerate(((0, 0.085, 0.0), (-1.0, 0.065, 0.02), (1.0, 0.065, 0.02))):
                Mx = Matrix.Translation(p) @ Matrix.Rotation(az + da, 4, 'Z') @ Matrix.Translation((0, 0.01, 0)) @ Matrix.Rotation(math.radians(62 + rng.uniform(-8, 8)), 4, 'X')
                hoja_bm(bm, ln, ln * 0.5, 0.35, 0.25, 0, 10, 4, M=Mx, ondul=0.4, seed=seed + k + s)
        flor_rosa_bm(bm, Vector((0, 0, 0.02)), Matrix.Translation(punta) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, 'Z'), 3, 2 + 0, 1.0 + rng.uniform(-0.15, 0.2), seed + f)
    o = objeto_desde(bm, nombre, [mh, mv, ms, mp, mm, mt])
    # orden de materiales: 0 hoja, 1 tallo, 2 sépalo… ajustar: hojas usan 0, tallos 2 (→ usamos índice real)
    return o

def exportar_planta(o, nombre, altura):
    viento(o, altura, amp=0.04, flutter=0.008, seed=hash(nombre) & 0xff)
    exportar(o, nombre)
    sc = bpy.context.scene; luz_demo(sc)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
    sc.render.resolution_x = 480; sc.render.resolution_y = 600; sc.view_settings.view_transform = 'Khronos PBR Neutral'
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]; mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (mn + mx) / 2; r = (mx - mn).length
    cam.data.lens = 50; cam.location = c + Vector((0.5, -1.0, 0.2)).normalized() * r * 1.5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for fr, tag in ((1, 'a'), (25, 'b')):
        sc.frame_set(fr); sc.render.filepath = os.path.join(SAL, f"{nombre}_{tag}.png"); bpy.ops.render.render(write_still=True)

def planta_ficus():
    limpiar()
    t1 = tex_hoja('ficus_hoja', (38, 112, 40), (18, 70, 28), (150, 205, 120), seed=2)
    mh = mat_hoja('hoja_ficus', t1); mv = mat_simple('tronco', (0.28, 0.2, 0.14), 0.8); mm, mt = maceta_mats()
    bm = nuevo(); rng = random.Random(5)
    maceta_bm(bm, 0.28, 0.4, 2)
    ramas = []
    def rama(p0, d, largo, r, prof):
        pts = [p0 + d * (largo * i / 6) + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.015 * i for i in range(7)]
        tallo_bm(bm, pts, r, r * 0.55, 1, 7)
        if prof == 0:
            ramas.append((pts[-1], d)); return
        for k in range(rng.randint(2, 3)):
            ang = rng.uniform(0, 6.28); nd = (d + Vector((math.cos(ang), math.sin(ang), 0)) * rng.uniform(0.5, 0.9)).normalized()
            rama(pts[-1] if k == 0 else pts[3 + k], nd, largo * 0.72, r * 0.62, prof - 1)
        # hojas en la rama
        for i in range(1, 7):
            for s2 in range(5):
                az = rng.uniform(0, 6.28)
                Mx = Matrix.Translation(pts[i]) @ Matrix.Rotation(az, 4, 'Z') @ Matrix.Rotation(math.radians(rng.uniform(30, 85)), 4, 'X')
                hoja_bm(bm, 0.26, 0.11, 0.3, 0.2, 0, 8, 4, M=Mx, ondul=0.3, seed=i + s2)
    rama(Vector((0, 0, 0.35)), Vector((0, 0, 1)), 0.75, 0.032, 3)
    for p, d in ramas:
        for k in range(28):
            az = rng.uniform(0, 6.28)
            Mx = Matrix.Translation(p + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) ) * 0.05) @ Matrix.Rotation(az, 4, 'Z') @ Matrix.Rotation(math.radians(rng.uniform(25, 95)), 4, 'X')
            hoja_bm(bm, 0.26, 0.11, 0.3, 0.22, 0, 8, 4, M=Mx, ondul=0.3, seed=k)
    return objeto_desde(bm, 'ficus', [mh, mv, mm, mt])

def planta_helecho():
    limpiar()
    t1 = tex_hoja('helecho_hoja', (52, 140, 50), (32, 100, 40), (120, 190, 100), seed=4, laterales=6)
    mh = mat_hoja('hoja_helecho', t1); mm, mt = maceta_mats(); mv = mat_simple('raquis', (0.25, 0.45, 0.2), 0.6)
    bm = nuevo(); rng = random.Random(8)
    maceta_bm(bm, 0.2, 0.26, 2)
    for f in range(16):
        ang = f / 16 * 2 * math.pi + rng.uniform(-0.2, 0.2); largo = rng.uniform(0.5, 0.75)
        d = Vector((math.cos(ang), math.sin(ang), 0)); base = Vector((0, 0, 0.24)) + d * 0.02
        pts = curva(base, base + d * 0.1 + Vector((0, 0, largo * 0.7)), base + d * largo * 0.85 + Vector((0, 0, largo * 0.35)), 16)
        tallo_bm(bm, pts, 0.004, 0.0015, 1, 5)
        for i in range(2, 16):
            t = i / 15; ln = 0.12 * (1 - 0.8 * (t ** 1.5)) + 0.02
            tan = (pts[min(i + 1, 15)] - pts[i - 1]).normalized()
            lado = tan.cross(Vector((0, 0, 1))).normalized()
            for s2 in (-1, 1):
                Mx = Matrix.Translation(pts[i]) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Rotation(math.radians(90 + s2 * 78), 4, 'Z') @ Matrix.Rotation(math.radians(20), 4, 'X')
                hoja_bm(bm, ln, ln * 0.22, 0.3, 0.15, 0, 5, 2, punta=0.8, M=Mx, seed=i)
    return objeto_desde(bm, 'helecho', [mh, mv, mm, mt])

def planta_enredadera():
    limpiar()
    t1 = tex_hoja('pothos_hoja', (60, 150, 52), (40, 110, 42), (190, 220, 110), seed=6, laterales=7)
    mh = mat_hoja('hoja_pothos', t1); mv = mat_simple('hebra', (0.2, 0.4, 0.15), 0.6); mm, mt = maceta_mats()
    bm = nuevo(); rng = random.Random(12)
    maceta_bm(bm, 0.14, 0.18, 2)
    for f in range(7):
        ang = f / 7 * 2 * math.pi; d = Vector((math.cos(ang), math.sin(ang), 0)); largo = rng.uniform(0.7, 1.3)
        base = Vector((0, 0, 0.17)) + d * 0.05
        pts = [base + d * (0.14 * (i / 12) + 0.04 * math.sin(i)) * 1.0 + Vector((0, 0, -largo * ((i / 12) ** 1.6) + 0.12 * math.sin(i / 12 * 3.14))) + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.01 for i in range(13)]
        tallo_bm(bm, pts, 0.003, 0.002, 1, 5)
        for i in range(1, 13):
            az = ang + rng.uniform(-1.2, 1.2) + (3.14 if i % 2 else 0)
            Mx = Matrix.Translation(pts[i]) @ Matrix.Rotation(az, 4, 'Z') @ Matrix.Rotation(math.radians(rng.uniform(80, 120)), 4, 'X')
            hoja_bm(bm, 0.11, 0.06, 0.2, 0.15, 0, 7, 4, punta=0.0, M=Mx, seed=i)
    return objeto_desde(bm, 'enredadera', [mh, mv, mm, mt])

def planta_hojas_anchas():
    limpiar()
    t1 = tex_hoja('ancha_hoja', (30, 100, 44), (16, 64, 32), (170, 220, 140), seed=9, laterales=14)
    mh = mat_hoja('hoja_ancha', t1); mv = mat_simple('peciolo', (0.22, 0.42, 0.2), 0.6); mm, mt = maceta_mats()
    bm = nuevo(); rng = random.Random(15)
    maceta_bm(bm, 0.24, 0.34, 2)
    for f in range(13):
        ang = f / 13 * 2 * math.pi + rng.uniform(-0.2, 0.2); alt = rng.uniform(0.45, 0.85); d = Vector((math.cos(ang), math.sin(ang), 0))
        base = Vector((0, 0, 0.3)) + d * 0.03; punta = base + d * rng.uniform(0.1, 0.28) + Vector((0, 0, alt))
        pts = curva(base, base + Vector((0, 0, alt * 0.8)) + d * 0.05, punta, 10)
        tallo_bm(bm, pts, 0.006, 0.004, 1, 6)
        Mx = Matrix.Translation(punta) @ Matrix.Rotation(ang - math.pi / 2, 4, 'Z') @ Matrix.Rotation(math.radians(rng.uniform(-35, 5)), 4, 'X') @ Matrix.Rotation(math.radians(0), 4, 'Y')
        hoja_bm(bm, rng.uniform(0.35, 0.5), rng.uniform(0.15, 0.2), 0.45, 0.25, 0, 14, 6, M=Mx, ondul=0.6, seed=f)
    return objeto_desde(bm, 'planta_hojas_anchas', [mh, mv, mm, mt])


def planta_rosa_unica(nombre='rosa_unica', col_c=(0.85,0.04,0.06), col_b=(0.35,0.0,0.02), seed=5, largo=0.42):
    """Una sola rosa real con tallo, espinas y hojas (para tenerla en la mano). Origen en la base del tallo, el tallo sube por +Z."""
    limpiar()
    t1 = tex_hoja('rosa_hoja', (46, 128, 44), (26, 84, 30), (140, 200, 110), seed=seed)
    mh = mat_hoja('hoja_rosa', t1); mv = mat_simple('tallo', (0.18, 0.32, 0.12), 0.6)
    mp = mat_petalo('petalo', col_b, col_c); ms = mat_simple('sepalo', (0.18, 0.4, 0.15), 0.5)
    bm = nuevo(); rng = random.Random(seed)
    base = Vector((0, 0, 0)); punta = Vector((0.0, 0.03, largo))
    pts = curva(base, Vector((0.0, -0.012, largo * 0.55)), punta, 14)
    tallo_bm(bm, pts, 0.0048, 0.0036, 1, 6)
    for k in range(2, 12, 2):
        p = pts[k]; d = (pts[k + 1] - pts[k - 1]).normalized(); nx = d.cross(Vector((0, 0, 1))).normalized() if abs(d.z) < 0.95 else Vector((1, 0, 0))
        tallo_bm(bm, [p, p + nx * 0.011 + d * 0.004], 0.0022, 0.0004, 1, 4)
    for k, az0 in ((4, 0.4), (8, 3.5)):
        p = pts[k]
        for s, (da, ln) in enumerate(((0, 0.07), (-1.0, 0.055), (1.0, 0.055))):
            Mx = Matrix.Translation(p) @ Matrix.Rotation(az0 + da, 4, 'Z') @ Matrix.Translation((0, 0.008, 0)) @ Matrix.Rotation(math.radians(64), 4, 'X')
            hoja_bm(bm, ln, ln * 0.5, 0.35, 0.25, 0, 10, 4, M=Mx, ondul=0.4, seed=seed + k + s)
    flor_rosa_bm(bm, Vector((0, 0, 0.02)), Matrix.Translation(punta) @ Matrix.Rotation(0.6, 4, 'Z'), 3, 2, 1.1, seed)
    return objeto_desde(bm, nombre, [mh, mv, ms, mp])

if __name__ == '__main__':
    quien = os.environ.get('QUE', 'rosa_roja').split(',')
    if 'rosa_roja' in quien: o = planta_rosal('rosal_rojo', (0.35, 0.0, 0.02), (0.85, 0.04, 0.06), 3, 5); exportar_planta(o, 'rosal_rojo', 0.8)
    if 'rosa_blanca' in quien: o = planta_rosal('rosal_blanco', (0.9, 0.85, 0.7), (0.99, 0.98, 0.95), 7, 4); exportar_planta(o, 'rosal_blanco', 0.8)
    if 'rosa_amarilla' in quien: o = planta_rosal('rosal_amarillo', (0.85, 0.55, 0.05), (1.0, 0.85, 0.2), 11, 4); exportar_planta(o, 'rosal_amarillo', 0.8)

    if 'ficus' in quien: o = planta_ficus(); exportar_planta(o, 'ficus', 1.9)
    if 'helecho' in quien: o = planta_helecho(); exportar_planta(o, 'helecho', 0.7)
    if 'enredadera' in quien: o = planta_enredadera(); exportar_planta(o, 'enredadera', 0.3)
    if 'anchas' in quien: o = planta_hojas_anchas(); exportar_planta(o, 'planta_hojas_anchas', 1.0)
    if 'rosa_unica' in quien:
        o = planta_rosa_unica(); exportar(o, 'rosa_unica')
