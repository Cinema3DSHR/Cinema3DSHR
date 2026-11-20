"""s4 «Espejos» (1920–2400): salón de espejos infinitos; Aiden salta contra el espejo mayor, que estalla en cientos de esquirlas (transición C);
detrás hay un vacío con una esquirla de cristal gigante que la cámara atraviesa (transición D)."""
import math
import random
import bpy
from mathutils import Vector, Quaternion, Euler
import lib
from lib import *
import marco
import aiden as AID

YM = 46.0       # posición del espejo mayor
TS = 2262       # cuadro en que se rompe
T_ROMPE = Tiempo([(1920, 0.0), (TS, 0.0), (2300, 1.1), (2340, 1.8), (2400, 3.2)])


def construir(ctx, i, f0, f1):
    col = coleccion("S4_Espejos")
    O = Vector(ctx.desp(i))
    r = random.Random(41)
    espejo = mat_espejo("espejo_s4", (0.92, 0.96, 1.0))
    negro = mat("negro_s4", (0.01, 0.011, 0.014), metal=0.9, rug=0.05)
    suelo = mat("suelo_espejo_s4", (0.02, 0.025, 0.035), metal=1.0, rug=0.06)
    cian = mat_emisivo("cian_s4", (0.3, 0.8, 1.0), 10.0)
    mag = mat_emisivo("magenta_s4", (1.0, 0.2, 0.7), 8.0)
    blanca = mat_emisivo("blanca_s4", (1.0, 0.97, 0.92), 12.0)
    ANCHO, ALTO, LARGO = 16.0, 12.0, 80.0
    caja("suelo", O + Vector((0, LARGO / 2 - 4, -0.1)), (ANCHO, LARGO, 0.2), col, suelo)
    caja("techo", O + Vector((0, LARGO / 2 - 4, ALTO)), (ANCHO, LARGO, 0.2), col, negro)
    caja("pared_i", O + Vector((-ANCHO / 2, LARGO / 2 - 4, ALTO / 2)), (0.3, LARGO, ALTO), col, espejo)
    caja("pared_d", O + Vector((ANCHO / 2, LARGO / 2 - 4, ALTO / 2)), (0.3, LARGO, ALTO), col, espejo)
    caja("fondo_atras", O + Vector((0, -4.3, ALTO / 2)), (ANCHO, 0.3, ALTO), col, espejo)
    # tiras de luz que se reflejan hasta el infinito
    for k in range(18):
        y = 2 + k * 4.4
        caja(f"tira_t{k}", O + Vector((0, y, ALTO - 0.15)), (ANCHO * 0.7, 0.18, 0.06), col, cian if k % 3 else mag)
        caja(f"colg_i{k}", O + Vector((-ANCHO / 2 + 0.5, y, ALTO - 0.6)), (0.06, 0.06, 1.0), col, blanca)
        caja(f"colg_d{k}", O + Vector((ANCHO / 2 - 0.5, y, ALTO - 0.6)), (0.06, 0.06, 1.0), col, blanca)
    # losas de espejo flotando y girando despacio
    losas = []
    for k in range(16):
        o = caja(f"losa_{k}", O + Vector((r.uniform(-6, 6), 8 + k * 2.4, r.uniform(1.5, 8.0))), (r.uniform(1.5, 3.0), 0.08, r.uniform(2.5, 5.0)), col, espejo,
                 rot=(r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), r.uniform(0, 3.1)))
        losas.append(o)
        a0 = o.rotation_euler.z
        for f in range(f0, f1 + 1, 24):
            o.rotation_euler = (o.rotation_euler.x, o.rotation_euler.y, a0 + (f - f0) * 0.004 * (1 if k % 2 else -1))
            o.keyframe_insert("rotation_euler", frame=f)
    # ───── el espejo mayor: mosaico de 7×5 baldosas que se desintegra
    tiles = []
    nx, nz = 9, 6
    tw, th = ANCHO / nx, ALTO / nz
    sim = []
    for a in range(nx):
        for b in range(nz):
            c = O + Vector((-ANCHO / 2 + tw * (a + 0.5), YM, th * (b + 0.5)))
            ob = caja(f"baldosa_{a}_{b}", c, (tw * 0.985, 0.12, th * 0.985), col, espejo)
            ob.rotation_mode = "QUATERNION"
            ob.rotation_quaternion = Quaternion((1, 0, 0, 0))
            # velocidad: sale hacia +Y (el vacío) y se abre desde el punto de impacto (centro, z≈1.4)
            d = (c - (O + Vector((0, YM, 1.5)))) * Vector((1, 0, 1))
            dist = d.length
            v = Vector((d.x * 0.9 + r.gauss(0, 1.4), 6.0 + r.uniform(0, 6) + (4.5 - min(dist, 4.5)) * 1.8, d.z * 0.9 + r.gauss(0, 1.4)))
            sim.append(Fragmento(ob, c, v, Quaternion((1, 0, 0, 0)), Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * r.uniform(0.6, 2.6)))
    # esquirlas pequeñas adicionales
    esq = nube_fragmentos("esq_s4", col, [espejo], 160, O + Vector((0, YM, 1.5)), 3.0, 10.0, 5.0, 43, tam=(0.1, 0.45), gz_up=0.1, w_max=9.0, variantes=8)
    for q in esq:
        q.v.y = abs(q.v.y) + 3.0
    sim += esq
    tray = simular(sim, 4.0, g=(0, 0, -1.2), arrastre=0.02)
    animar_trayectorias(tray, T_ROMPE, f0, f1, paso=2)
    # ───── Aiden: trote lento y salto contra el espejo
    arm = ctx.aiden
    run0, run1 = f0, 2204
    AID.segmento(arm, "correr", run0, run1, mapa=lambda f: (f - run0) * 0.5, ciclo=True)
    AID.segmento(arm, "salto_grande", run1 + 1, f1, mapa=lambda f: (f - run1) * 0.55)
    ys = lambda f: 4.0 + 3.0 * (min(f, run1) - f0) / 30.0
    pos = [(f, O + Vector((0, ys(f), 0)), math.pi) for f in range(f0, run1 + 1, 6)]
    pos.append((run1 + 1, O + Vector((0, ys(run1), 0)), math.pi))
    pos.append((f1, O + Vector((0, ys(run1), 0)), math.pi))
    AID.colocar(arm, pos)
    # ───── luces
    for nom, loc, en, cl in (("frio_s4", (3, 14, 9.5), 12000.0, (0.6, 0.8, 1.0)), ("mag_s4", (-3, 30, 9.0), 9000.0, (1.0, 0.3, 0.8))):
        L = bpy.data.lights.new(nom, "AREA")
        L.energy = en
        L.size = 5.0
        L.color = cl
        lo = bpy.data.objects.new(nom, L)
        col.objects.link(lo)
        lo.location = O + Vector(loc)
        lo.rotation_euler = (math.radians(180), 0, 0)
    seguir = bpy.data.lights.new("aiden_s4", "AREA")
    seguir.energy = 1200.0
    seguir.size = 3.0
    seguir.color = (0.8, 0.9, 1.0)
    ls = bpy.data.objects.new("aiden_s4", seguir)
    col.objects.link(ls)
    for f in range(f0, f1 + 1, 6):
        ls.location = O + Vector((0.8, ys(f) - 2.0, 3.6))
        ls.keyframe_insert("location", frame=f)
    ls.rotation_euler = (math.radians(150), 0, 0)
    # ───── el vacío detrás del espejo: estrellas, esquirla gigante de cristal con luz interior
    V = O + Vector((0, YM + 70, 6))
    for nom, (x, y, z) in (("v", (0, 0, 0)),):
        pass
    campo_estrellas(col, 400, 300.0, 11)
    for o in col.objects:
        if o.name.startswith("estrella_"):
            o.location += V
    cristal = mat_vidrio("cristal_gig_s4", (0.7, 0.9, 1.0), 0.0, 1.6)
    sh = esquirla("esquirla_gig", (3.2, 1.6, 5.5), 77, col, cristal)
    sh.location = V + Vector((0, 22, 0))
    sh.rotation_euler = (0.3, 0.2, 0.6)
    for f in range(2330, f1 + 1, 4):
        sh.rotation_euler = (0.3 + (f - 2330) * 0.004, 0.2, 0.6 + (f - 2330) * 0.01)
        sh.keyframe_insert("rotation_euler", frame=f)
    nucleo = mat_emisivo("nucleo_s4", (0.5, 0.85, 1.0), 20.0)
    esfera("nucleo", V + Vector((0, 22, 0)), 0.5, col, nucleo, 16, 10).visible_shadow = False
    lv = bpy.data.lights.new("luz_vacio", "POINT")
    lv.energy = 40000.0
    lv.color = (0.6, 0.85, 1.0)
    lvo = bpy.data.objects.new("luz_vacio", lv)
    col.objects.link(lvo)
    lvo.location = V + Vector((3, 18, 3))
    # ───── cámaras
    aid = lambda f: O + Vector((0, ys(f), 0))
    cA = Camara("cam_s4_a", col, 22.0)
    cA.claves(f0, 2040, lambda f: aid(f) + Vector((lerp(0.6, -0.4, (f - f0) / 120.0), -5.5, 0.35)), lambda f: aid(f) + Vector((0, 2.0, 1.2)), fdof=lambda f: (5.5, 2.8))
    cB = Camara("cam_s4_b", col, 28.0)
    cB.claves(2040, 2160, lambda f: aid(f) + Vector((math.cos(math.radians(lerp(-90, 120, (f - 2040) / 120.0))) * 4.2, math.sin(math.radians(lerp(-90, 120, (f - 2040) / 120.0))) * 4.2, lerp(1.0, 2.0, (f - 2040) / 120.0))),
              lambda f: aid(f) + Vector((0, 0, 1.2)), fdof=lambda f: (4.2, 2.8))
    cC = Camara("cam_s4_c", col, 24.0)
    cC.claves(2160, 2262, lambda f: aid(f) + Vector((lerp(-0.7, 0.7, (f - 2160) / 102.0), lerp(-3.4, -4.4, (f - 2160) / 102.0), lerp(1.7, 1.2, (f - 2160) / 102.0))),
              lambda f: O + Vector((0, YM, 1.6)), fdof=lambda f: (8.0, 3.0))
    cD = Camara("cam_s4_d", col, 20.0)
    cD.claves(2262, 2330, lambda f: O + Vector((lerp(0.0, 0.0, 0), lerp(YM - 9, YM + 3.5, suave((f - 2262) / 68.0)), lerp(1.7, 1.5, (f - 2262) / 68.0))),
              lambda f: O + Vector((0, YM + 10, 1.6)), fdof=lambda f: (6.0, 2.4))
    cE = Camara("cam_s4_e", col, 24.0)
    cE.claves(2330, f1, lambda f: V + Vector((lerp(2.0, 0.0, suave((f - 2330) / 69.0)), lerp(-4.0, 20.6, suave((f - 2330) / 69.0) ** 1.6), lerp(1.0, 0.0, suave((f - 2330) / 69.0)))),
              lambda f: V + Vector((0, 22, 0)), flente=lambda f: lerp(24.0, 16.0, suave((f - 2330) / 69.0)), fdof=lambda f: (20.0, 4.0))
    for f_, c_ in ((f0, cA), (2040, cB), (2160, cC), (2262, cD), (2330, cE)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 22, 1.0, 0.0, (1.0, 0.8, 0.5), 10.0)
    vE = ctx.dir.velos["cam_s4_e"]
    vE.rampa(2385, 2399, 0.0, 1.0, (0.75, 0.92, 1.0), 12.0)
    vD = ctx.dir.velos["cam_s4_d"]
    vD.rampa(2262, 2266, 0.0, 0.35, (1.0, 1.0, 1.0), 4.0)
    vD.rampa(2266, 2280, 0.35, 0.0, (1.0, 1.0, 1.0), 4.0)
    marco.pulso(ctx.comp["disp"], [(2255, 0.012), (2264, 0.16), (2300, 0.012), (2380, 0.012), (2399, 0.12)])
    ctx.amb.append((f0 - 1, (0.003, 0.004, 0.009), 0.5))
    ctx.escena_activa(col, f0, f1)
