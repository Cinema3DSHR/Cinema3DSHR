"""s7 «Reconstrucción» (3750–4500): una escalera helicoidal se rearma desde sus fragmentos (tiempo inverso), Aiden la sube corriendo, el tiempo retrocede
y se congela con ondas que se expanden; al final todo se vuelve a ensamblar mientras la cámara asciende."""
import math
import random
import bpy
from mathutils import Vector, Quaternion, Euler
import lib
from lib import *
import marco
import aiden as AID

NB = 150
R = 7.0
TURNS = 4.5
RISE = 0.14
# tiempo de los fragmentos: llegan desde el desorden, se ensamblan, vuelven a soltarse un poco en el retroceso y se congelan; al final se rearman
T = Tiempo([(3750, 6.0), (3950, 0.0), (4100, 0.0), (4180, 1.6), (4250, 3.0), (4400, 3.0), (4500, 0.0)])
# tiempo de Aiden: corre, retrocede (corre hacia atrás), se congela y vuelve a correr
TA = Tiempo([(3850, 0.0), (4100, 8.3), (4250, 5.0), (4400, 5.0), (4500, 7.5)])


def paso(k):
    a = k * (2 * math.pi * TURNS / NB)
    return a, Vector((math.cos(a) * R, math.sin(a) * R, 0.35 + k * RISE))


def construir(ctx, i, f0, f1):
    col = coleccion("S7_Reconstruccion")
    O = Vector(ctx.desp(i))
    r = random.Random(71)
    marmol = mat("marmol_s7", (0.75, 0.73, 0.7), rug=0.18, coat=0.4)
    oro = mat("oro_s7", (1.0, 0.62, 0.18), metal=1.0, rug=0.15)
    nube = mat("nube_s7", (0.95, 0.96, 1.0), rug=1.0)
    # plaza circular y torre central
    cilindro("plaza", O + Vector((0, 0, -0.5)), 34.0, 1.0, col, marmol, seg=64)
    toro("plaza_aro", O + Vector((0, 0, 0.05)), 33.0, 0.18, col, oro, seg=96, seg_r=10)
    for q in range(8):
        a = q * math.pi / 4
        caja(f"pilar_{q}", O + Vector((math.cos(a) * 26.0, math.sin(a) * 26.0, 7.0)), (1.2, 1.2, 14.0), col, marmol)
        esfera(f"orbe_{q}", O + Vector((math.cos(a) * 26.0, math.sin(a) * 26.0, 14.6)), 0.7, col, oro, 24, 16)
    cilindro("eje", O + Vector((0, 0, 11.0)), 0.9, 22.0, col, oro, seg=24)
    # nubes abajo y lejos
    for k in range(60):
        a = r.uniform(0, 6.28)
        d = r.uniform(45, 160)
        s_ = r.uniform(12, 35)
        n = esfera(f"nube_{k}", O + Vector((math.cos(a) * d, math.sin(a) * d, r.uniform(-30, -8))), 1.0, col, nube, 12, 8, esc=(s_, s_ * r.uniform(0.7, 1.2), s_ * 0.35))
        n.visible_shadow = False
    # ───── los escalones: se ensamblan desde el desorden
    base = caja("esc_base", (0, 0, -9999), (1.45, 1.7, 0.5), col, marmol)
    base.hide_render = True
    sim = []
    for k in range(NB):
        a, p = paso(k)
        o = bpy.data.objects.new(f"escalon_{k}", base.data)
        col.objects.link(o)
        o.rotation_mode = "QUATERNION"
        q = Quaternion((0, 0, 1), a)
        d = Vector((math.cos(a) * 0.6 + r.gauss(0, 0.5), math.sin(a) * 0.6 + r.gauss(0, 0.5), r.gauss(0, 0.6) + 0.3)).normalized()
        sim.append(Fragmento(o, O + p, d * r.uniform(1.2, 4.0), q, Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * r.uniform(0.2, 1.1)))
        borde = caja(f"escalon_oro_{k}", (0, 0, 0), (1.46, 0.06, 0.52), col, oro)
        borde.parent = o
        borde.location = (0, 0.84, 0)
    tray = simular(sim, 6.2, g=(0, 0, 0), arrastre=0.0, muestreo=1.0 / 30.0)
    animar_trayectorias(tray, T, f0, f1, paso=3)
    # ───── Aiden corre por la hélice (adelante, atrás, congelado)
    arm = ctx.aiden
    ARUN = 5.0 / R             # rad/s sobre la hélice
    a0 = 0.35
    seg = [(3850, 4100), (4100, 4250), (4250, 4400), (4400, f1)]
    AID.segmento(arm, "correr", 3850, f1, mapa=lambda f: TA(f) * 30.0, ciclo=True)
    raiz = bpy.data.objects["PJ_aiden"]
    raiz.rotation_mode = "XYZ"
    pos_a = lambda f: a0 + ARUN * TA(f)
    cuerpo = lambda f: O + Vector((math.cos(pos_a(f)) * R, math.sin(pos_a(f)) * R, 0.35 + (pos_a(f) / (2 * math.pi * TURNS / NB)) * RISE + 0.25))
    for f in range(f0, f1 + 1, 4):
        ff = max(3850, f)
        if f < 3850:                 # antes de entrar en escena Aiden espera lejos, fuera de cuadro
            raiz.location = O + Vector((0, 0, -400))
            raiz.keyframe_insert("location", frame=f)
            continue
        raiz.location = cuerpo(ff)
        # mira hacia la tangente de la hélice (sentido creciente del ángulo): yaw = ángulo + 90° y el personaje ve hacia +Y local ⇒ +π
        raiz.rotation_euler = (0, 0, pos_a(ff) + math.pi / 2 + math.pi)
        raiz.keyframe_insert("location", frame=f)
        raiz.keyframe_insert("rotation_euler", frame=f)
    cabeza = ctx.head
    hips = ctx.hips
    # ───── luces: sol cálido bajo y cielo
    sol = bpy.data.lights.new("sol_s7", "SUN")
    sol.energy = 5.0
    sol.color = (1.0, 0.82, 0.62)
    sol.angle = math.radians(2.0)
    so = bpy.data.objects.new("sol_s7", sol)
    col.objects.link(so)
    so.rotation_euler = (math.radians(62), math.radians(8), math.radians(35))
    # ───── ondas del congelado
    ond = mat_emisivo("onda_s7", (1.0, 0.85, 0.6), 18.0)
    for k in range(4):
        t = toro(f"onda_s7_{k}", O + Vector((0, 0, 0)), 1.0, 0.025, col, ond, rot=(0, 0, 0), seg=96, seg_r=6)
        t.visible_shadow = False
        for f in range(4250, 4401, 3):
            u = (f - 4250) / 150.0 - k * 0.1
            if u < 0:
                s_ = 0.01
            else:
                s_ = 1.0 + 45.0 * u
            c_ = cuerpo(4300)
            t.location = c_
            t.scale = (s_, s_, s_)
            t.keyframe_insert("location", frame=f)
            t.keyframe_insert("scale", frame=f)
        t.scale = (0.01, 0.01, 0.01)
        t.keyframe_insert("scale", frame=3750)
        t.keyframe_insert("scale", frame=4249)
        t.scale = (0.01, 0.01, 0.01)
        t.keyframe_insert("scale", frame=4402)
    # ───── cámaras
    cA = Camara("cam_s7_a", col, 20.0)
    cA.claves(f0, 3850, lambda f: O + Vector((lerp(-9.0, -3.0, (f - f0) / 100.0), lerp(-9.0, -5.0, (f - f0) / 100.0), 0.6)), lambda f: O + Vector((0, 0, lerp(5.0, 12.0, (f - f0) / 100.0))), fdof=lambda f: (13.0, 3.5))
    cB = Camara("cam_s7_b", col, 26.0)
    cB.seguir(hips)
    cB.claves(3850, 3980, lambda f: cuerpo(f) + Vector((math.cos(pos_a(f) - 0.5) * -2.2, math.sin(pos_a(f) - 0.5) * -2.2, 0.9)), None, fdof=lambda f: (3.6, 2.8))
    cC = Camara("cam_s7_c", col, 22.0)
    cC.seguir(hips)
    cC.claves(3980, 4100, lambda f: cuerpo(f) + Vector((0.0, 0.0, lerp(9.0, 5.0, (f - 3980) / 120.0))) + Vector((math.cos(math.radians(lerp(0, 120, (f - 3980) / 120.0))) * 2.0, math.sin(math.radians(lerp(0, 120, (f - 3980) / 120.0))) * 2.0, 0)), None, fdof=lambda f: (7.0, 3.0))
    cD = Camara("cam_s7_d", col, 20.0)
    cD.seguir(hips)
    cD.claves(4100, 4250, lambda f: O + Vector((lerp(-16.0, -12.0, (f - 4100) / 150.0), lerp(-14.0, -12.0, (f - 4100) / 150.0), lerp(3.0, 6.0, (f - 4100) / 150.0))), None, fdof=lambda f: (18.0, 4.0))
    cE = Camara("cam_s7_e", col, 24.0)
    cE.seguir(hips)
    cE.claves(4250, 4400, lambda f: cuerpo(4300) + Vector((math.cos(math.radians(lerp(0, 220, (f - 4250) / 150.0))) * 3.4, math.sin(math.radians(lerp(0, 220, (f - 4250) / 150.0))) * 3.4, lerp(0.4, 1.6, (f - 4250) / 150.0))), None, fdof=lambda f: (3.4, 2.4))
    cF = Camara("cam_s7_f", col, 24.0)
    cF.claves(4400, f1, lambda f: O + Vector((lerp(-6.0, -20.0, suave((f - 4400) / 99.0)), lerp(-6.0, -20.0, suave((f - 4400) / 99.0)), lerp(4.0, 60.0, suave((f - 4400) / 99.0) ** 1.4))), lambda f: O + Vector((0, 0, lerp(8.0, 2.0, (f - 4400) / 99.0))), fdof=lambda f: (30.0, 6.0))
    raiz.location = O + Vector((0, 0, -400))
    raiz.keyframe_insert("location", frame=3849)
    for f_, c_ in ((f0, cA), (3850, cB), (3980, cC), (4100, cD), (4250, cE), (4400, cF)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 24, 1.0, 0.0, (0.85, 0.95, 1.0), 12.0)
    vF = ctx.dir.velos["cam_s7_f"]
    vF.rampa(4470, 4499, 0.0, 1.0, (1.0, 1.0, 1.0), 10.0)
    marco.pulso(ctx.comp["disp"], [(4096, 0.012), (4104, 0.12), (4140, 0.012), (4246, 0.012), (4254, 0.14), (4290, 0.012)])
    ctx.amb.append((f0 - 1, (0.35, 0.5, 0.85), 1.1))
    ctx.escena_activa(col, f0, f1)
