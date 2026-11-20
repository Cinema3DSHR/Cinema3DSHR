"""s3 «Detonación» (1200–1920): un módulo de estación estalla. Cámara lenta, bullet-time alrededor de Aiden en pleno salto, congelado, retroceso parcial
y zoom hasta el interior de la bola de fuego (transición A)."""
import math
import random
import bpy
from mathutils import Vector, Quaternion
import lib
from lib import *
import marco
import aiden as AID

# tiempo de simulación de la explosión (s) en función del cuadro: 0 antes del estallido (1290), cámara lenta, congelado, retorno y retroceso
T = Tiempo([(1200, 0.0), (1290, 0.0), (1340, 1.0), (1450, 1.5), (1560, 1.85), (1600, 1.85), (1625, 2.6), (1680, 4.4), (1740, 2.6), (1800, 3.6), (1920, 6.0)])


def construir(ctx, i, f0, f1):
    col = coleccion("S3_Detonacion")
    O = Vector(ctx.desp(i))
    r = random.Random(31)
    campo_estrellas(col, 600, 380.0, 9)
    for o in col.objects:
        if o.name.startswith("estrella_"):
            o.location += O
    casco = mat_ruido("casco_s3", (0.03, 0.035, 0.045), (0.16, 0.17, 0.2), 3.0, metal=0.85, rug=0.3, bump=0.3)
    oscuro = mat("oscuro_s3", (0.015, 0.016, 0.02), metal=0.9, rug=0.4)
    vent = mat_emisivo("ventana_s3", (1.0, 0.75, 0.4), 6.0)
    azul = mat_emisivo("azul_s3", (0.25, 0.6, 1.0), 9.0)
    rojo = mat_emisivo("alarma_s3", (1.0, 0.1, 0.05), 12.0)
    C = O + Vector((0, 42, 10))
    # ───── cubierta por donde corre Aiden (de y=34 a y=4), con barandas
    caja("cubierta", O + Vector((0, 19, -0.3)), (9, 30, 0.6), col, casco)
    for k in range(11):
        y = 5 + k * 3
        caja(f"pil_i{k}", O + Vector((-4.4, y, 0.6)), (0.12, 0.12, 1.2), col, oscuro)
        caja(f"pil_d{k}", O + Vector((4.4, y, 0.6)), (0.12, 0.12, 1.2), col, oscuro)
    caja("baranda_i", O + Vector((-4.4, 19, 1.15)), (0.08, 30, 0.08), col, azul)
    caja("baranda_d", O + Vector((4.4, 19, 1.15)), (0.08, 30, 0.08), col, azul)
    for k in range(6):
        caja(f"luz_borde{k}", O + Vector((0, 4.2 + k * 5.5, 0.02)), (7.5, 0.1, 0.03), col, rojo if k % 2 else vent)
    # ───── columna vertebral de la estación en 12 tramos (se vuelven escombros)
    chunks = []
    for k in range(12):
        x = -54.0 + k * 9.8 + 4.9
        c = cilindro(f"tramo_{k}", O + Vector((x, 42, 10)), 6.0, 9.6, col, casco, rot=(0, math.pi / 2, 0), seg=40)
        c.rotation_mode = "QUATERNION"
        c.rotation_quaternion = Euler((0, math.pi / 2, 0)).to_quaternion()
        for a_ in (-0.45, 0.45):
            cr = cilindro(f"aro_{k}_{a_}", (0, 0, 0), 6.25, 0.7, col, oscuro, seg=40)
            cr.parent = c
            cr.location = (0, 0, a_ * 9.6 * 0.95)
        for w in range(14):
            ang = r.uniform(0, 6.28)
            zz = r.uniform(-4.2, 4.2)
            v = caja(f"vent_{k}_{w}", (0, 0, 0), (0.5, 0.35, 0.05), col, vent if r.random() < 0.8 else azul)
            v.parent = c
            v.location = (math.cos(ang) * 6.02, math.sin(ang) * 6.02, zz)
            v.rotation_euler = (0, 0, ang)
            # la ventana mira hacia afuera (eje X local) → rota alrededor de Z local del cilindro
        chunks.append(c)
    # alas solares
    ala_m = mat("ala_s3", (0.02, 0.05, 0.13), metal=0.6, rug=0.25)
    alas = []
    for k, (x, sg) in enumerate(((-30, 1), (-30, -1), (30, 1), (30, -1))):
        a = caja(f"ala_{k}", O + Vector((x, 42, 10 + sg * 17)), (9, 0.12, 22.0), col, ala_m)
        a.rotation_mode = "QUATERNION"
        a.rotation_quaternion = Quaternion((1, 0, 0, 0))
        a.location = O + Vector((x, 42, 10 + sg * 17))
        alas.append(a)
        for g in range(1, 9):
            ln = caja(f"ala_ln_{k}_{g}", (0, 0, 0), (9.05, 0.14, 0.05), col, azul)
            ln.parent = a
            ln.location = (0, 0, -11 + g * 2.4)
    # ───── fragmentos: tramos, alas, escombros, brasas y vidrios
    sim = []
    for c in chunks:
        d = (c.location - C)
        d.z *= 1.0
        dv = d.normalized() if d.length > 0.5 else Vector((0, 0, 1))
        sim.append(Fragmento(c, c.location.copy(), dv * r.uniform(5, 13) + Vector((0, r.uniform(-4, 6), r.uniform(-2, 5))), c.rotation_quaternion.copy(),
                             Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * r.uniform(0.15, 0.55)))
    for a in alas:
        dv = (a.location - C).normalized()
        sim.append(Fragmento(a, a.location.copy(), dv * r.uniform(8, 18), a.rotation_quaternion.copy(), Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * 0.7))
    esc = nube_fragmentos("esc_s3", col, [casco, oscuro], 340, C, 9.0, 36.0, 18.0, 13, tam=(0.4, 1.7), gz_up=0.0, w_max=6.0, variantes=10)
    brasa = mat_emisivo("brasa_s3", (1.0, 0.5, 0.1), 30.0)
    bra = nube_fragmentos("bra_s3", col, [brasa], 260, C, 5.0, 60.0, 30.0, 17, tam=(0.05, 0.16), gz_up=0.0, w_max=14.0, variantes=4)
    vid = mat_vidrio_rapido("vidrio_s3")
    J0 = O + Vector((0, 6, 1.3))
    vidr = nube_fragmentos("vid_s3", col, [vid], 90, J0 + Vector((0, 3, 0.5)), 6.0, 2.2, 1.2, 21, tam=(0.3, 0.9), gz_up=0.0, w_max=3.0, variantes=8)
    for q in vidr:
        q.p = J0 + Vector((r.uniform(-4.5, 4.5), r.uniform(-4, 9), r.uniform(-0.8, 4.0)))
    sim += esc + bra + vidr
    tray = simular(sim, 7.0, g=(0, 0, 0), arrastre=0.015)
    animar_trayectorias(tray, T, f0, f1, paso=3)
    # ───── bolas de fuego (la principal y dos secundarias), onda de choque y luces
    bf = bola_fuego("fuego_s3", C, 34.0, col, T, 1290, f1, tau=0.55, semilla=1.0, duracion_s=6.5, emi=2.2)
    bf2 = bola_fuego_barata("fuego_s3b", C + Vector((-18, -4, 4)), 17.0, col, lambda f: T(f) - 0.35, 1290, f1, tau=0.5, semilla=7.0, duracion_s=5.5, emi=7.0)
    bf3 = bola_fuego_barata("fuego_s3c", C + Vector((20, -6, -3)), 14.0, col, lambda f: T(f) - 0.6, 1290, f1, tau=0.5, semilla=13.0, duracion_s=5.0, emi=7.0)
    # mientras el tiempo corre a la inversa las bolas ya se achican solas (usan T)
    onda_choque("onda_s3", C, 260.0, col, T, 1290, f1, vel=38.0)
    lf = bpy.data.lights.new("fuego_luz_s3", "POINT")
    lf.color = (1.0, 0.5, 0.16)
    lf.shadow_soft_size = 8.0
    lo = bpy.data.objects.new("fuego_luz_s3", lf)
    col.objects.link(lo)
    lo.location = C + Vector((0, -16, 2))
    for f in range(f0, f1 + 1, 3):
        t = max(0.0, T(f))
        k = (1.0 - math.exp(-t / 0.15)) * math.exp(-t / 5.0)
        lf.energy = 8.0e5 * k
        lf.keyframe_insert("energy", frame=f)
    kl = bpy.data.lights.new("fria_s3", "AREA")
    kl.energy = 90000.0
    kl.color = (0.5, 0.7, 1.0)
    kl.size = 16.0
    lk = bpy.data.objects.new("fria_s3", kl)
    col.objects.link(lk)
    lk.location = O + Vector((-26, -20, 22))
    lk.rotation_euler = (O + Vector((0, 20, 4)) - lk.location).to_track_quat("-Z", "Y").to_euler()
    # ───── Aiden: corre por la cubierta y salta (el salto sigue el tiempo de la explosión → cámara lenta, congelado y retroceso con él)
    arm = ctx.aiden
    Tj0 = 0.75          # segundo de la simulación en que empieza el salto
    run0, run1 = f0, 1318
    AID.segmento(arm, "correr", run0, run1, mapa=lambda f: (f - run0) * 1.0, ciclo=True)
    AID.segmento(arm, "salto_grande", run1 + 1, f1, mapa=lambda f: max(0.0, (T(f) - T(run1 + 1))) * 30.0 * 1.0)
    pos = []
    for f in range(run0, run1 + 1, 3):
        pos.append((f, O + Vector((0, 6 + 6.5 * (run1 - f) / 30.0, 0)), 0.0))
    pos.append((run1 + 1, O + Vector((0, 6, 0)), 0.0))
    pos.append((f1, O + Vector((0, 6, 0)), 0.0))
    # fuera de su carrera Aiden espera lejos (no se ve): antes de run0 queda en el punto de partida
    pos.insert(0, (f0, O + Vector((0, 6 + 6.5 * (run1 - run0) / 30.0, 0)), 0.0))
    AID.colocar(arm, pos)
    # ───── cámaras
    hips = ctx.hips
    cA = Camara("cam_s3_a", col, 22.0)
    cA.claves(f0, 1290, lambda f: O + Vector((lerp(34, 18, suave((f - f0) / 90.0)), lerp(-22, -9, suave((f - f0) / 90.0)), lerp(11, 4.5, suave((f - f0) / 90.0)))),
              lambda f: O + Vector((lerp(0, 0, 0), lerp(26, 14, suave((f - f0) / 90.0)), lerp(7, 3, suave((f - f0) / 90.0)))), fdof=lambda f: (30.0, 5.6))
    cB = Camara("cam_s3_b", col, 32.0)
    cB.claves(1290, 1380, lambda f: O + Vector((lerp(2.2, 1.1, suave((f - 1290) / 90.0)), lerp(-1.5, -3.6, suave((f - 1290) / 90.0)), lerp(0.5, 1.15, suave((f - 1290) / 90.0)))),
              lambda f: O + Vector((0, 40, 9)), fdof=lambda f: (4.0, 2.0))
    cC = Camara("cam_s3_c", col, 24.0)
    cC.seguir(hips)
    cC.claves(1380, 1500, lambda f: O + Vector((0, 4.2, 1.5)) + Vector((math.cos(math.radians(lerp(-80, 240, suave((f - 1380) / 120.0)))) * 4.6, math.sin(math.radians(lerp(-80, 240, suave((f - 1380) / 120.0)))) * 4.6, lerp(0.2, 1.1, suave((f - 1380) / 120.0)))),
              None, fdof=lambda f: (4.6, 2.0))
    cD = Camara("cam_s3_d", col, 85.0)
    cD.seguir(hips)
    cD.claves(1500, 1560, lambda f: O + Vector((lerp(-2.4, -1.6, (f - 1500) / 60.0), lerp(1.5, 3.0, (f - 1500) / 60.0), lerp(1.8, 2.2, (f - 1500) / 60.0))), None, fdof=lambda f: (lerp(2.5, 4.2, suave((f - 1500) / 60.0)), 1.4))
    cE = Camara("cam_s3_e", col, 20.0)
    cE.claves(1560, 1625, lambda f: O + Vector((lerp(46, 36, (f - 1560) / 65.0), lerp(-42, -52, (f - 1560) / 65.0), lerp(24, 20, (f - 1560) / 65.0))), lambda f: C + Vector((0, -6, -2)), fdof=lambda f: (70.0, 6.0))
    cF = Camara("cam_s3_f", col, 16.0)
    cF.claves(1625, 1740, lambda f: O + Vector((lerp(-6, 8, suave((f - 1625) / 115.0)), lerp(14, 20, suave((f - 1625) / 115.0)), 0.5)), lambda f: C + Vector((0, 0, lerp(2, 10, suave((f - 1625) / 115.0)))), fdof=lambda f: (28.0, 4.0))
    # dolly zoom hacia la explosión
    def ppos(f):
        u = suave((f - 1740) / 175.0)
        return O + Vector((lerp(10, 0, u), lerp(-16, 40, u ** 1.5), lerp(12, 10, u)))
    cG = Camara("cam_s3_g", col, 24.0)
    cG.claves(1740, f1, ppos, lambda f: C + Vector((0, lerp(0, 5, suave((f - 1740) / 175.0)), 0)), flente=lambda f: lerp(32.0, 12.0, suave((f - 1740) / 175.0)), fdof=lambda f: (60.0, 8.0))
    for f_, c_ in ((f0, cA), (1290, cB), (1380, cC), (1500, cD), (1560, cE), (1625, cF), (1740, cG)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 24, 1.0, 0.0, (0.85, 0.95, 1.0), 8.0)
    vG = ctx.dir.velos["cam_s3_g"]
    vG.rampa(1880, 1919, 0.0, 1.0, (1.0, 0.8, 0.5), 10.0)
    # destello y dispersión: golpe al estallar y al salir del congelado
    marco.pulso(ctx.comp["disp"], [(1286, 0.012), (1292, 0.15), (1320, 0.012), (1620, 0.012), (1626, 0.1), (1650, 0.012), (1900, 0.012), (1919, 0.14)])
    marco.pulso(ctx.comp["dist"], [(1286, 0.0), (1292, -0.3), (1320, 0.0), (1900, 0.0), (1919, -0.4)])
    ctx.amb.append((1199, (0.004, 0.006, 0.012), 0.6))
    ctx.escena_activa(col, f0, f1)


from mathutils import Euler
