"""s2 «Cero g» (660–1200): plataformas flotantes, herramientas y cables a la deriva, gravedad que se invierte, objetos congelados, un anillo que se rearma
y una partícula luminosa que la cámara sigue hasta que crece y se vuelve la escena siguiente (transición E)."""
import math
import random
import bpy
from mathutils import Vector, Quaternion
import lib
from lib import *
import marco
import aiden as AID


def herramienta(col, nombre, tipo, mm, r):
    """Pequeñas piezas reconocibles: llave, tornillo, panel, cable (cápsulas encadenadas)."""
    import bmesh
    bm = bmesh.new()
    if tipo == 0:   # llave
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= 0.09
            v.co.y *= 0.9
            v.co.z *= 0.04
        e = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.17, radius2=0.17, depth=0.05, matrix=Matrix.Translation((0, 0.5, 0)))
    elif tipo == 1:  # panel
        bmesh.ops.create_cube(bm, size=1.0)
        s = r.uniform(0.5, 1.4)
        for v in bm.verts:
            v.co.x *= s
            v.co.y *= s * r.uniform(0.6, 1.2)
            v.co.z *= 0.05
    elif tipo == 2:  # perno
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.05, radius2=0.05, depth=0.45)
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.11, radius2=0.11, depth=0.07, matrix=Matrix.Translation((0, 0, 0.26)))
    else:           # tubo
        bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.08, radius2=0.08, depth=r.uniform(0.8, 1.8))
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mm)
    for p in me.polygons:
        p.use_smooth = tipo in (2, 3)
    return me


from mathutils import Matrix
r = random.Random(7)


def construir(ctx, i, f0, f1):
    global r
    col = coleccion("S2_CeroG")
    O = Vector(ctx.desp(i))
    campo_estrellas(col, 500, 380.0, 5)
    for o in col.objects:
        if o.name.startswith("estrella_"):
            o.location += O
    mp = mat_ruido("plat_s2", (0.03, 0.035, 0.045), (0.14, 0.15, 0.17), 2.5, metal=0.8, rug=0.35, bump=0.3)
    borde = mat_emisivo("borde_s2", (0.3, 0.8, 1.0), 12.0)
    ambar = mat_emisivo("ambar_s2", (1.0, 0.45, 0.1), 8.0)
    # plataformas hexagonales flotantes
    plats = []
    r = random.Random(7)
    plats.append((Vector((0, 0, -0.35)), 14.0))
    for k in range(13):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(22, 70)
        plats.append((Vector((math.cos(a) * d, math.sin(a) * d, r.uniform(-18, 22))), r.uniform(4, 13)))
    for k, (p, rad) in enumerate(plats):
        o = cilindro(f"plat_{k}", O + p, rad, 0.7, col, mp, rot=(r.uniform(-0.12, 0.12) if k else 0, r.uniform(-0.12, 0.12) if k else 0, r.uniform(0, 3)), seg=6, suave=False)
        cb = cilindro(f"platb_{k}", O + p + Vector((0, 0, 0.36)), rad * 1.002, 0.04, col, borde if k % 3 else ambar, rot=o.rotation_euler, seg=6, suave=False)
        for j in range(r.randint(2, 5)):   # bloques rotos debajo
            s = r.uniform(rad * 0.15, rad * 0.35)
            caja(f"roca_{k}_{j}", O + p + Vector((r.uniform(-rad, rad) * 0.6, r.uniform(-rad, rad) * 0.6, -s * 0.8 - 0.3)), (s, s * 0.8, s), col, mp, rot=(r.random(), r.random(), r.random()))
    # --- herramientas y cables flotando sobre la plataforma principal
    mats = [mat("metal_a", (0.35, 0.36, 0.4), metal=1.0, rug=0.28), mat("naranja_s2", (0.9, 0.35, 0.05), rug=0.4), mat("gris_s2", (0.12, 0.13, 0.15), metal=0.8, rug=0.45)]
    mallas = {}
    objs = []
    for k in range(110):
        t = r.choice((0, 0, 1, 1, 2, 3, 3))
        key = (t, r.randint(0, 2), r.randint(0, 3))
        if key not in mallas:
            mallas[key] = herramienta(col, f"h{key}", t, mats[key[1]], r)
        o = bpy.data.objects.new(f"obj_{k}", mallas[key])
        col.objects.link(o)
        o.rotation_mode = "QUATERNION"
        objs.append(o)
    frs = []
    for o in objs:
        pos = O + Vector((r.uniform(-9, 9), r.uniform(-9, 9), r.uniform(1.0, 9.0)))
        vel = Vector((r.gauss(0, 0.5), r.gauss(0, 0.5), r.gauss(0, 0.4)))
        q = Quaternion(Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))).normalized(), r.uniform(0, 3.1))
        frs.append(Fragmento(o, pos, vel, q, Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * r.uniform(0.3, 1.4)))
    # gravedad: casi nula → cae hacia la plataforma → se invierte y sube → vuelve a cero
    tray = simular(frs, 14.0, g=(0, 0, -0.15), suelo=O.z + 0.02, rest=0.45,
                   cambios_g=[(2.6, (0, 0, -7.0)), (5.7, (0, 0, 5.5)), (8.4, (0, 0, 0.1))], arrastre=0.02)
    T = Tiempo([(f0, 0.0), (760, 3.3), (830, 5.9), (880, 7.0), (925, 7.0), (1000, 9.0), (1130, 12.0), (f1, 13.0)])
    animar_trayectorias(tray, T, f0, f1, paso=3)
    # cables: cadenas de tubitos ondulantes que se mecen
    cable = mat("cable_s2", (0.02, 0.02, 0.025), rug=0.5)
    for k in range(6):
        o0 = O + Vector((r.uniform(-8, 8), r.uniform(-8, 8), r.uniform(2, 8)))
        pts = []
        for j in range(18):
            pts.append(Vector((math.sin(j * 0.45 + k) * 1.3, j * 0.55 - 5.0, math.cos(j * 0.37 + k * 2.0) * 1.1)))
        verts, caras = [], []
        seg = 6
        for j, p in enumerate(pts):
            for s_ in range(seg):
                a = 2 * math.pi * s_ / seg
                verts.append(p + Vector((math.cos(a) * 0.06, 0, math.sin(a) * 0.06)))
        for j in range(len(pts) - 1):
            for s_ in range(seg):
                caras.append((j * seg + s_, j * seg + (s_ + 1) % seg, (j + 1) * seg + (s_ + 1) % seg, (j + 1) * seg + s_))
        cb = malla(f"cable_{k}", verts, caras, col, cable, True)
        cb.location = o0
        cb.rotation_euler = (r.uniform(-0.4, 0.4), 0, r.uniform(0, 6.28))
        for f in range(f0, f1 + 1, 12):
            tt = T(f - f0 + f0)
            cb.location = o0 + Vector((math.sin(tt * 0.5 + k) * 0.8, math.cos(tt * 0.4 + k * 2) * 0.8, math.sin(tt * 0.3 + k) * 0.6 + (0.9 * suave((tt - 5.7) / 3.0) if tt > 5.7 else 0)))
            cb.keyframe_insert("location", frame=f)
    # --- anillo que se rearma: 40 segmentos que vuelven (tiempo inverso)
    ring_c = O + Vector((0, 0, 4.2))
    segm = []
    em = mat_emisivo("ring_s2", (0.5, 0.85, 1.0), 10.0)
    base = caja("seg_base", (0, 0, -9999), (0.7, 0.45, 0.5), col, mp)
    base.hide_render = True
    fr2 = []
    for k in range(40):
        a = 2 * math.pi * k / 40
        o = bpy.data.objects.new(f"anillo_{k}", base.data)
        col.objects.link(o)
        o.rotation_mode = "QUATERNION"
        p = ring_c + Vector((math.cos(a) * 3.2, 0, math.sin(a) * 3.2))
        q = Quaternion((0, 1, 0), -a)
        d = Vector((math.cos(a), r.uniform(-1, 1) * 0.4, math.sin(a))).normalized()
        fr2.append(Fragmento(o, p, d * r.uniform(2.0, 5.0), q, Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * 1.8))
    tray2 = simular(fr2, 6.0, g=(0, 0, 0), arrastre=0.0)
    # tiempo que corre hacia atrás: 6 s de dispersión pasan al revés entre 900 y 1020 → termina ensamblado
    T2 = Tiempo([(f0, 6.0), (900, 6.0), (1020, 0.0), (f1, 0.0)])
    animar_trayectorias(tray2, T2, f0, f1, paso=3)
    anillo_em = toro("anillo_glow", ring_c, 3.2, 0.03, col, em, rot=(math.radians(90), 0, 0), seg=96, seg_r=6)
    for f, v in ((1000, 0.0), (1030, 1.0)):
        anillo_em.scale = (v, v, v)
        anillo_em.keyframe_insert("scale", frame=f)
    # --- Aiden flotando
    arm = ctx.aiden
    AID.segmento(arm, "flotar", f0, f1, mapa=lambda f: (T(f) * 30.0 * 0.55), ciclo=True)
    pos = []
    for f in range(f0, f1 + 1, 6):
        t = T(f)
        pos.append((f, O + Vector((math.sin(t * 0.3) * 0.5, math.cos(t * 0.25) * 0.5, 2.2 + math.sin(t * 0.5) * 0.3 + 0.5 * suave((t - 5.9) / 2.0))), math.radians(200 + 12 * t)))
    AID.colocar(arm, pos)
    # --- partícula luminosa
    pm = mat_emisivo("particula_s2", (0.7, 0.9, 1.0), 220.0)
    pa = esfera("particula", O + Vector((0, 0, 3)), 1.0, col, pm, 24, 16)
    pa.visible_shadow = False
    luzp = bpy.data.lights.new("luz_particula", "POINT")
    luzp.color = (0.7, 0.9, 1.0)
    lp = bpy.data.objects.new("luz_particula", luzp)
    col.objects.link(lp)

    def ppos(f):
        u = (f - 1000) / 160.0
        a = u * 5.2
        return O + Vector((math.sin(a) * (3 + 14 * u), -2 + 36 * u, 2.0 + math.cos(a * 1.3) * 3.0 + 4 * u))

    for f in range(1000, f1 + 1, 2):
        pa.location = ppos(f)
        u = (f - 1000) / 200.0
        s_ = 0.05 + 0.04 * u + (0.0 if f < 1120 else 8.0 * suave((f - 1120) / 80.0) ** 2.2)
        pa.scale = (s_, s_, s_)
        pa.keyframe_insert("location", frame=f)
        pa.keyframe_insert("scale", frame=f)
        lp.location = pa.location
        luzp.energy = 300.0 + 20000.0 * (0 if f < 1100 else suave((f - 1100) / 80.0))
        lp.keyframe_insert("location", frame=f)
        luzp.keyframe_insert("energy", frame=f)
    # luces de la escena
    kl = bpy.data.lights.new("luz_s2", "AREA")
    kl.energy = 7000.0
    kl.color = (0.55, 0.75, 1.0)
    kl.size = 14.0
    lk = bpy.data.objects.new("luz_s2", kl)
    col.objects.link(lk)
    lk.location = O + Vector((-12, -14, 18))
    lk.rotation_euler = (O + Vector((0, 0, 2)) - lk.location).to_track_quat("-Z", "Y").to_euler()
    kl2 = bpy.data.lights.new("luz_s2b", "AREA")
    kl2.energy = 3500.0
    kl2.color = (1.0, 0.55, 0.3)
    kl2.size = 10.0
    lk2 = bpy.data.objects.new("luz_s2b", kl2)
    col.objects.link(lk2)
    lk2.location = O + Vector((14, 12, 8))
    lk2.rotation_euler = (O + Vector((0, 0, 2)) - lk2.location).to_track_quat("-Z", "Y").to_euler()
    polvo(col, O + Vector((0, 0, 5)), (20, 20, 10), 200, 3, T, f0, f1, 0.08, 0.02)
    # --- cámaras
    aid = lambda f: O + Vector((0, 0, 2.6))
    cA = Camara("cam_s2_a", col, 24.0)
    cA.claves(f0, 760, lambda f: orbita(O, lerp(20, 8, suave((f - f0) / 100.0)), math.radians(-100), math.radians(-40), lerp(5, 2.5, suave((f - f0) / 100.0)), 3.0, (f - f0) / 100.0),
              lambda f: O + Vector((0, 0, 2.6)), fdof=lambda f: (lerp(20, 8, suave((f - f0) / 100.0)), 3.5))
    cB = Camara("cam_s2_b", col, 20.0)
    cB.claves(760, 830, lambda f: O + Vector((lerp(-11, -5, suave((f - 760) / 70.0)), -9, 0.25)), lambda f: O + Vector((0, 1, 3.0)), fdof=lambda f: (11.0, 2.2))
    cC = Camara("cam_s2_c", col, 17.0)
    cC.claves(830, 900, lambda f: O + Vector((lerp(2.0, 4.5, (f - 830) / 70.0), -5.0, lerp(0.3, 4.5, suave((f - 830) / 70.0)))), lambda f: O + Vector((0, 0, 3.0 + 7.0 * suave((f - 830) / 70.0))), fdof=lambda f: (6.0, 2.0))
    cD = Camara("cam_s2_d", col, 100.0)
    cD.claves(900, 1000, lambda f: O + Vector((lerp(-4.0, -3.0, (f - 900) / 100.0), -4.0, lerp(5.0, 5.6, (f - 900) / 100.0))), lambda f: O + Vector((lerp(0.5, -0.5, (f - 900) / 100.0), 0, 5.2)), fdof=lambda f: (5.5, 1.6))
    cE = Camara("cam_s2_e", col, 24.0)
    cE.claves(1000, 1130, lambda f: ppos(f - 7) + Vector((1.6, -4.0, 0.7)), lambda f: ppos(f), fdof=lambda f: (4.4, 2.4))
    cF = Camara("cam_s2_f", col, 24.0)
    cF.claves(1130, f1, lambda f: ppos(f - 7) + Vector((1.6, -4.0, 0.7)) + Vector((0, 2.6 * suave((f - 1130) / 70.0), 0)), lambda f: ppos(f), fdof=lambda f: (4.4, 2.4))
    for f_, c_ in ((f0, cA), (760, cB), (830, cC), (900, cD), (1000, cE), (1130, cF)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 24, 1.0, 0.0, (1.0, 0.9, 0.7), 5.0)
    vF = ctx.dir.velos["cam_s2_f"]
    vF.rampa(1170, 1199, 0.0, 1.0, (0.85, 0.95, 1.0), 8.0)
    ctx.amb.append((f0, (0.004, 0.006, 0.012), 0.6))
    ctx.escena_activa(col, f0, f1)
