"""p018 · s6 laboratorio: un láser golpea una lámina de plástico (hidrocarburo), la onda de choque la comprime y rayos X «ven» nacer diminutos diamantes."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import comun as K
import saldo as SAL


def construir(ctx, i, f0, f1):
    col = coleccion("S6_Laboratorio")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    rng = random.Random(12)
    S = O + Vector((0, 0, 1.2))
    mesa = mat("mesa_lab", (0.05, 0.06, 0.08), metal=0.6, rug=0.25)
    caja("mesa", O + Vector((0, 0, -0.05)), (30, 30, 0.1), col, mesa)
    muro = mat("muro_lab", (0.03, 0.04, 0.06), rug=0.7)
    caja("muro", O + Vector((0, 9, 3)), (30, 0.2, 12), col, muro)
    # lámina de plástico (muestra) en su soporte
    plast = mat("plastico", (0.8, 0.75, 0.55), rug=0.3, emis=(0.9, 0.7, 0.3), fuerza=0.25)
    muestra = caja("muestra", S, (0.12, 1.4, 1.4), col, plast)
    soporte = mat("soporte", (0.3, 0.3, 0.33), metal=0.8, rug=0.3)
    cilindro("soporte_v", O + Vector((0, 0, 0.25)), 0.06, 0.5, col, soporte, seg=16)
    caja("base_sop", O + Vector((0, 0, 0.03)), (0.9, 0.9, 0.06), col, soporte)
    # fuente láser (izquierda) y rayo; fuente de rayos X (arriba/atrás) y detector (abajo/adelante)
    cilindro("laser_cuerpo", O + Vector((-2.7, 0, 1.2)), 0.3, 1.6, col, soporte, rot=(0, math.radians(90), 0), seg=24)
    f_disp = f0 + 100
    haz = cilindro("laser_haz", O + Vector((-0.98, 0, 1.2)), 0.04, 1.84, col, mat_emisivo("haz_laser", (1.0, 0.18, 0.1), 14.0), rot=(0, math.radians(90), 0), seg=12)
    haz.visible_shadow = False
    K.aparecer(haz, f_disp - 1, f_disp + 1)
    K.desaparecer(haz, f_disp + 16, f_disp + 18)
    cilindro("rx_cuerpo", O + Vector((1.6, 2.2, 2.8)), 0.24, 1.2, col, soporte, rot=(math.radians(55), 0, math.radians(35)), seg=24)
    d_rx = (S - (O + Vector((1.6, 2.2, 2.8))))
    rx = K.cilindro_entre("rayos_x", O + Vector((1.6, 2.2, 2.8)) + d_rx.normalized() * 0.6, S, 0.025, col, mat_emisivo("haz_rx", (0.7, 0.55, 1.0), 10.0))
    rx.visible_shadow = False
    K.aparecer(rx, f_disp + 20, f_disp + 24)
    det = caja("detector", O + Vector((1.4, -1.8, 0.8)), (1.6, 0.12, 1.2), col, mat("detector", (0.08, 0.09, 0.12), metal=0.4, rug=0.3, emis=(0.3, 0.5, 1.0), fuerza=0.15))
    det.rotation_euler = (0, 0, math.radians(-30))
    # destello y onda de choque en el impacto
    fl = esfera("flash", S + Vector((-0.1, 0, 0)), 0.5, col, mat_emisivo("flash_m", (1.0, 0.9, 0.7), 40.0), 20, 12)
    fl.visible_shadow = False
    fl.scale = (0.0001, 0.0001, 0.0001)
    fl.keyframe_insert("scale", frame=f_disp)
    fl.scale = (1.8, 1.8, 1.8)
    fl.keyframe_insert("scale", frame=f_disp + 4)
    fl.scale = (0.0001, 0.0001, 0.0001)
    fl.keyframe_insert("scale", frame=f_disp + 22)
    for k in range(2):
        t0 = f_disp + 4 + 8 * k
        ring = toro(f"onda_{k}", S, 0.6, 0.03, col, mat_emisivo(f"onda_m{k}", (1.0, 0.7, 0.4), 6.0), rot=(0, math.radians(90), 0), seg=64)
        ring.visible_shadow = False
        ring.scale = (0.0001, 0.0001, 0.0001)
        ring.keyframe_insert("scale", frame=t0)
        ring.scale = (3.0, 3.0, 3.0)
        ring.keyframe_insert("scale", frame=t0 + 40)
        ring.scale = (0.0001, 0.0001, 0.0001)
        ring.keyframe_insert("scale", frame=t0 + 41)
    # luz del destello
    lp = bpy.data.lights.new("luz_flash", "POINT")
    lp.energy = 0.0
    lp.shadow_soft_size = 0.4
    lo = bpy.data.objects.new("luz_flash", lp)
    col.objects.link(lo)
    lo.location = S + Vector((-0.6, -0.3, 0.2))
    for f_, e_ in ((f0, 0.0), (f_disp, 0.0), (f_disp + 3, 5000.0), (f_disp + 20, 0.0)):
        lp.energy = e_
        lp.keyframe_insert("energy", frame=f_)
    K.luz_area(col, "luz_lab_a", O + Vector((-3, -6, 4)), 1200.0, (0.8, 0.9, 1.0), 5.0, (math.radians(60), 0, math.radians(-25)))
    K.luz_area(col, "luz_lab_b", O + Vector((4, -5, 3)), 700.0, (1.0, 0.85, 0.7), 5.0, (math.radians(70), 0, math.radians(30)))
    # diminutos diamantes que nacen en la muestra tras el choque (cara hacia −Y, donde mira la cámara)
    mg = K.mat_gema("gema_lab", (0.65, 0.93, 1.0), 4.0)
    base = K.malla_gema("base_lab", col, mg, radio=1.0, alto=1.5, lados=6)
    base.hide_render = True
    for k in range(120):
        p = S + Vector((-0.1, rng.uniform(-0.62, 0.62), rng.uniform(-0.62, 0.62)))
        t = rng.uniform(0.008, 0.026)
        g = K.duplicar(base, f"nano_{k}", col, p, 0.0001, (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3)))
        t0 = f_disp + 36 + int(rng.uniform(0, 50))
        g.keyframe_insert("scale", frame=t0)
        g.scale = (t, t, t)
        g.keyframe_insert("scale", frame=t0 + 12)
    # rótulos 3D de la vista general (con aparición escalonada)
    def rot3d(txt, pos, f_a, f_b, color=(255, 255, 255, 255), alto=0.38):
        e = SAL.etiqueta(col, txt, alto_m=alto, color=color, fuerza=3.0)
        e.location = pos
        K.aparecer(e, f_a, f_a + 10)
        K.desaparecer(e, f_b, f_b + 10)
    rot3d("LÁSER", O + Vector((-2.7, -0.9, 2.3)), f0 + 8, f_disp - 6, (255, 150, 120, 255), 0.34)
    rot3d("PLÁSTICO", S + Vector((0, -0.9, 1.1)), f0 + 20, f_disp - 6, (255, 235, 180, 255), 0.3)
    rot3d("RAYOS X", O + Vector((1.6, 1.9, 3.8)), f0 + 32, f_disp - 6, (215, 190, 255, 255), 0.34)
    # cámara: vista general y luego acercamiento continuo hasta el macro (curva suave, sin saltos)
    c = Camara("cam_s6", col, 34.0)
    f_macro = f_disp + 30
    def pos(f):
        u = suave((f - f_macro) / float(f1 - 40 - f_macro))
        base_p = O + Vector((-1.3 + 0.4 * math.sin((f - f0) / 80.0), -9.5, 2.3))
        macro_p = S + Vector((-1.15, -0.45, 0.05))
        return base_p.lerp(macro_p, u)
    def tgt(f):
        u = suave((f - f_macro) / float(f1 - 40 - f_macro))
        return (O + Vector((-0.6, 0, 1.3))).lerp(S + Vector((-0.1, 0, 0.0)), u)
    c.claves(f0, f1 - 1, pos, tgt, flente=lambda f: lerp(20.0, 45.0, suave((f - f_macro) / float(f1 - 40 - f_macro))), fdof=lambda f: ((pos(f) - tgt(f)).length, 3.2), paso=1)
    ctx.dir.corte(f0, c, velo=False)
    ctx.escena_activa(col, f0, f1)
