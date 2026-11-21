"""p018 · s3 (el metano se rompe bajo presión) y s4 (los átomos de carbono se ordenan en un cristal: diamante)."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import comun as K
import saldo as SAL
from esc_a import sol_escena


def construir(ctx, i, f0, f1):
    (s3 if i == 3 else s4)(ctx, i, f0, f1)


def red_diamante(a=1.3, celdas=2):
    """Posiciones de la red cúbica de diamante (FCC + base desplazada 1/4,1/4,1/4) y los enlaces (vecinos a a·√3/4)."""
    base = [(0, 0, 0), (0, .5, .5), (.5, 0, .5), (.5, .5, 0)]
    pts = []
    for cx in range(celdas):
        for cy in range(celdas):
            for cz in range(celdas):
                for b in base:
                    for d in ((0, 0, 0), (.25, .25, .25)):
                        p = Vector(((cx + b[0] + d[0]) * a, (cy + b[1] + d[1]) * a, (cz + b[2] + d[2]) * a))
                        pts.append(p)
    c = sum(pts, Vector()) / len(pts)
    pts = [p - c for p in pts]
    dmax = a * math.sqrt(3) / 4 * 1.05
    enl = [(i, j) for i in range(len(pts)) for j in range(i + 1, len(pts)) if (pts[i] - pts[j]).length < dmax]
    return pts, enl


def s3(ctx, i, f0, f1):
    col = coleccion("S3_Metano")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    rng = random.Random(9)
    sol_escena(col, "sol_s3", 2.2, (math.radians(55), 0, math.radians(25)), f0, f1, (1.0, 0.97, 0.92))
    K.luz_area(col, "luz_s3", O + Vector((-5, -7, 5)), 900.0, (0.8, 0.9, 1.0), 6.0, (math.radians(60), 0, math.radians(-35)))
    mc = mat("carbono", (0.03, 0.03, 0.035), metal=0.2, rug=0.25)
    mh = mat("hidrogeno", (0.95, 0.97, 1.0), rug=0.35, emis=(0.8, 0.9, 1.0), fuerza=0.25)
    mb = mat("enlace_c", (0.7, 0.9, 1.0), metal=0.0, rug=0.3, emis=(0.5, 0.85, 1.0), fuerza=1.5)
    pts, enl = red_diamante()
    pts_o = sorted([O + p for p in pts], key=lambda v: (round(v.x, 3), round(v.y, 3), round(v.z, 3)))
    # 64 moléculas de metano en una caja que se comprime; cada una gira lento y vibra con senos suaves (continuo)
    ini = sorted([O + Vector((rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2))) for _ in range(len(pts))], key=lambda v: (round(v.x, 3), round(v.y, 3), round(v.z, 3)))
    tet = [Vector(v).normalized() for v in ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))]
    f_rotura, f_vuelo, f_red = f0 + int(n * 0.38), f0 + int(n * 0.55), f0 + int(n * 0.82)
    carbonos = []
    for k, p0 in enumerate(ini):
        ph = rng.uniform(0, 6.28)
        c = esfera(f"C_{k}", p0, 0.26, col, mc, 14, 10)
        hs = []
        for j, d in enumerate(tet):
            h = esfera(f"H_{k}_{j}", (0, 0, 0), 0.15, col, mh, 10, 8)
            h.parent = c
            h.location = d * 0.42
            hs.append((h, d))
        carbonos.append((c, hs, p0, pts_o[k], ph))
        c.rotation_mode = "XYZ"
        for f in range(f0, f1, 3):
            t = (f - f0) / 30.0
            u_c = suave((f - f_vuelo) / float(f_red - f_vuelo))
            vib = 1.0 - u_c
            comp = suave((f - f0) / float(f_rotura - f0))             # la caja se comprime: las moléculas se acercan al centro
            base = O + (p0 - O) * lerp(1.0, 0.62, comp)
            jit = Vector((math.sin(t * 2.1 + ph), math.sin(t * 1.7 + ph * 1.3), math.sin(t * 2.4 + ph * 0.7))) * 0.10 * vib * lerp(1.0, 1.6, comp)
            c.location = base.lerp(pts_o[k], u_c) + jit
            c.keyframe_insert("location", frame=f)
            c.rotation_euler = (t * 0.7 + ph, t * 0.5, t * 0.3) if u_c < 0.01 else (t * 0.7 * (1 - u_c) + ph, 0, 0)
            c.keyframe_insert("rotation_euler", frame=f)
        c.location = pts_o[k]
        c.keyframe_insert("location", frame=f1 - 1)
        # hidrógenos: salen disparados al romperse el enlace y se desvanecen
        for h, d in hs:
            h.keyframe_insert("location", frame=f_rotura)
            h.keyframe_insert("scale", frame=f_rotura)
            h.location = d * 4.5
            h.keyframe_insert("location", frame=f_vuelo + 30)
            h.scale = (0.0001, 0.0001, 0.0001)
            h.keyframe_insert("scale", frame=f_vuelo + 30)
    # placas de presión (se acercan) y enlaces del cristal (aparecen cuando los carbonos llegan a su lugar)
    mp = mat("placa_presion", (0.4, 0.8, 1.0), rug=0.2, emis=(0.3, 0.7, 1.0), fuerza=0.6, alfa=0.25)
    for sg in (-1, 1):
        pl = caja(f"placa_{sg}", O + Vector((sg * 3.6, 0, 0)), (0.12, 7.0, 7.0), col, mp)
        pl.location = O + Vector((sg * 3.6, 0, 0))
        pl.keyframe_insert("location", frame=f0)
        pl.location = O + Vector((sg * 2.5, 0, 0))
        pl.keyframe_insert("location", frame=f_rotura)
        pl.keyframe_insert("location", frame=f_vuelo)
        pl.location = O + Vector((sg * 3.2, 0, 0))
        pl.keyframe_insert("location", frame=f_red)
        pl.visible_shadow = False
    dmax = 1.3 * math.sqrt(3) / 4 * 1.05
    enl = [(p, q) for p in range(len(pts_o)) for q in range(p + 1, len(pts_o)) if (pts_o[p] - pts_o[q]).length < dmax]
    for (a, b) in enl:
        e = K.cilindro_entre(f"enlace_{a}_{b}", pts_o[a], pts_o[b], 0.045, col, mb)
        K.aparecer(e, f_red - 10, f_red + 18)
    # rótulos
    e1 = SAL.etiqueta(col, "CH₄", alto_m=0.6, color=(255, 255, 255, 255), fuerza=3.0)
    e1.location = O + Vector((0, -5.5, 2.4))
    K.aparecer(e1, f0 + 4, f0 + 16)
    K.desaparecer(e1, f_rotura + 10, f_rotura + 20)
    c = Camara("cam_s3", col, 32.0)
    c.claves(f0, f1 - 1, lambda f: O + Vector((9.5 * math.sin(math.radians(lerp(-35, 40, (f - f0) / n))), -9.5 * math.cos(math.radians(lerp(-35, 40, (f - f0) / n))) - 3.0, lerp(1.5, 0.6, (f - f0) / n))), lambda f: O, paso=1)
    ctx.dir.corte(f0, c, velo=False)
    ctx.escena_activa(col, f0, f1)


def s4(ctx, i, f0, f1):
    col = coleccion("S4_Cristal")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    sol_escena(col, "sol_s4", 2.0, (math.radians(55), 0, math.radians(25)), f0, f1)
    K.luz_area(col, "luz_s4a", O + Vector((-5, -7, 5)), 900.0, (0.7, 0.9, 1.0), 6.0, (math.radians(60), 0, math.radians(-35)))
    K.luz_area(col, "luz_s4b", O + Vector((6, -5, -2)), 500.0, (1.0, 0.8, 0.6), 6.0, (math.radians(100), 0, math.radians(40)))
    mc = mat("carbono4", (0.03, 0.03, 0.035), metal=0.2, rug=0.25)
    mb = mat("enlace_c4", (0.7, 0.9, 1.0), rug=0.3, emis=(0.5, 0.85, 1.0), fuerza=1.5)
    mg = K.mat_gema("gema_s4", (0.6, 0.92, 1.0), 3.2)
    pts, enl = red_diamante()
    raiz = bpy.data.objects.new("red_raiz", None)
    col.objects.link(raiz)
    raiz.location = O
    g0 = f0 + int(n * 0.50)
    g1 = f0 + int(n * 0.72)
    for k, p in enumerate(pts):
        a = esfera(f"Cr_{k}", p, 0.26, col, mc, 14, 10)
        a.parent = raiz
        K.desaparecer(a, g0, g1)
    for (a, b) in enl:
        e = K.cilindro_entre(f"enl4_{a}_{b}", pts[a], pts[b], 0.045, col, mb)
        e.parent = raiz
        K.desaparecer(e, g0, g1)
    # la red gira de forma continua; el diamante nace en su lugar
    for f in range(f0, f1, 3):
        raiz.rotation_euler = (math.radians(15), 0, math.radians((f - f0) * 0.8))
        raiz.keyframe_insert("rotation_euler", frame=f)
    base = K.malla_gema("gema_base_s4", col, mg, radio=1.5, alto=2.5, lados=8)
    base.hide_render = True
    gem = K.duplicar(base, "diamante", col, O)
    gem.rotation_mode = "XYZ"
    K.aparecer(gem, g0, g1 + 8, 1.0)
    for f in range(g0, f1, 3):
        gem.rotation_euler = (math.radians(12), 0, math.radians((f - g0) * 1.6))
        gem.keyframe_insert("rotation_euler", frame=f)
    # destellos (estrellas de 4 puntas) que pulsan sobre el diamante
    mt = mat_emisivo("destello", (0.9, 1.0, 1.0), 9.0)
    rng = random.Random(4)
    for k in range(7):
        p = O + Vector((rng.uniform(-1.3, 1.3), -1.6, rng.uniform(-1.6, 1.6)))
        dest = plano(f"dest_{k}", p, 0.9, 0.09, col, mt)
        dest2 = plano(f"dest2_{k}", p, 0.09, 0.9, col, mt)
        t0 = g1 + 4 + k * 6
        for d_ in (dest, dest2):
            d_.visible_shadow = False
            d_.scale = (0.0001, 0.0001, 0.0001)
            d_.keyframe_insert("scale", frame=max(0, t0 - 1))
            d_.scale = (1, 1, 1)
            d_.keyframe_insert("scale", frame=t0 + 5)
            d_.scale = (0.0001, 0.0001, 0.0001)
            d_.keyframe_insert("scale", frame=t0 + 12)
    e2 = SAL.etiqueta(col, "DIAMANTE", alto_m=0.6, color=(255, 255, 255, 255), fuerza=3.2)
    e2.location = O + Vector((0, -5.5, 2.6))
    K.aparecer(e2, g1, g1 + 12)
    c = Camara("cam_s4", col, 32.0)
    c.claves(f0, f1 - 1, lambda f: O + Vector((lerp(-1.5, 1.5, (f - f0) / n), -lerp(11.0, 8.5, (f - f0) / n), lerp(0.8, 0.2, (f - f0) / n))), lambda f: O, paso=1)
    ctx.dir.corte(f0, c, velo=False)
    ctx.escena_activa(col, f0, f1)
