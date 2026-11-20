"""p016 · coreografía de cámaras (9:16). Cada toma es una función de posición/objetivo por cuadro; la cámara de la pasada recibe la onda (vibración, giro de lente, pérdida y recuperación)."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import marco
import guion

CUADRO_ONDA = 534           # cuando la onda alcanza la cámara de la pasada


def construir(ctx):
    col = coleccion("Camaras")
    y_c = ctx.y_coche
    X = guion.X_CARRIL
    cp = lambda f: Vector((X, y_c(f), 0.0))
    rng = random.Random(1618)
    jit = {f: Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))) for f in range(0, guion.TOTAL + 2)}

    def vibra(f, amp0, tau, f_ini):
        """Desplazamiento aleatorio que decae (la onda sacude la cámara y se recupera)."""
        if f < f_ini:
            return Vector((0, 0, 0))
        a = amp0 * math.exp(-(f - f_ini) / tau)
        return jit[f] * a

    def micro(f, a=0.004):
        return jit[f] * a

    def dist(p, f):
        return max(0.3, (p - cp(f)).length)

    cams = []
    reg = []            # (cuadro_ini, cuadro_fin, función de posición) de cada toma, para el audio
    # ───── 1. aproximación: la cámara espera en la avenida a la altura del coche y lo ve venir desde lejos
    PA = Vector((-4.5, 0.0, 1.25))
    cA = Camara("cam_A_pasada", col, 85.0)
    cA.seguir(ctx.centro)

    def lente_A(f):
        if f < 330:
            return lerp(85.0, 70.0, f / 330.0)
        if f < 530:
            return lerp(70.0, 26.0, ((f - 330) / 200.0) ** 1.8)
        return lerp(26.0, 24.0, min(1.0, (f - 530) / 170.0))
    pos_A = lambda f: PA + vibra(f, 0.22, 40.0, CUADRO_ONDA) + micro(f, 0.003)
    foco_A = lambda f: (dist(pos_A(f), f), 4.0 if f < 520 else 5.6)
    for (a, b) in ((0, 150), (330, 700)):
        cA.claves(a, b, pos_A, None, flente=lente_A, fdof=foco_A, paso=1)
        reg.append((a, b, pos_A))
    # ───── 2. seguimiento lateral a la par del coche (ruedas, reflejos de los edificios)
    cB = Camara("cam_B_lateral_aprox", col, 32.0)
    cB.seguir(ctx.centro)
    pos_B = lambda f: cp(f) + Vector((-6.8, lerp(3.0, -2.5, (f - 150) / 180.0), 0.85)) + micro(f, 0.006)
    reg.append((150, 330, pos_B))
    cB.claves(150, 330, pos_B, None, flente=lambda f: 32.0,
              fdof=lambda f: (6.9, 3.2), paso=1)
    # ───── 3. cámara lenta: seguimiento lateral por el costado derecho; el fondo (vidrieras) estalla
    cC = Camara("cam_C_lateral_slow", col, 20.0)
    cC.seguir(ctx.centro)
    def pos_C(f):
        """Tres cuartos trasero y abierto (nada de plano tapado por una puerta): la cámara va detrás-a la derecha del coche y se abre hacia el costado,
        con la avenida y las fachadas que estallan al fondo."""
        u = (f - 700) / 180.0
        a = math.radians(lerp(28, 62, suave(u)))
        d = lerp(11.0, 9.5, u)
        return cp(f) + Vector((-math.sin(a) * d, math.cos(a) * d, lerp(1.1, 1.6, u))) + micro(f, 0.006)
    reg.append((700, 880, pos_C))
    cC.claves(700, 880, pos_C, None,
              flente=lambda f: 24.0, fdof=lambda f: (10.0, 5.6), paso=2)
    # ───── 4. por delante del coche, mirando hacia atrás: la fachada destruida queda detrás del auto
    cD = Camara("cam_D_frontal_slow", col, 22.0)
    cD.seguir(ctx.centro)

    def pos_D(f):
        u = (f - 880) / 180.0
        a = math.radians(lerp(-28, 24, u))
        d = lerp(7.5, 5.6, u)
        return cp(f) + Vector((math.sin(a) * d, -math.cos(a) * d, lerp(0.7, 1.0, u))) + micro(f, 0.006)
    reg.append((880, 1060, pos_D))
    cD.claves(880, 1060, pos_D, None, flente=lambda f: 22.0, fdof=lambda f: (6.5, 3.5), paso=2)
    # ───── 5. plano general elevado: la onda y la destrucción a lo largo de la avenida
    cE = Camara("cam_E_alta", col, 28.0)
    cE.seguir(ctx.centro)
    pos_E = lambda f: Vector((-14.5, -165.0 + lerp(0.0, -12.0, (f - 1060) / 140.0), lerp(10.5, 12.5, (f - 1060) / 140.0))) + micro(f, 0.01)
    reg.append((1060, 1200, pos_E))
    cE.claves(1060, 1200, pos_E, None,
              flente=lambda f: 28.0, fdof=lambda f: (28.0, 6.0), paso=2)
    # ───── 6. detalle de la rueda delantera derecha rodando
    cF = Camara("cam_F_rueda", col, 35.0)
    cF.seguir(ctx.coche["pivotes"]["FR"])
    pos_F = lambda f: cp(f) + Vector((-2.1, lerp(-1.4, 0.4, (f - 1200) / 130.0), 0.55)) + micro(f, 0.004)
    reg.append((1200, 1330, pos_F))
    cF.claves(1200, 1330, pos_F, None, flente=lambda f: 40.0, fdof=lambda f: (2.0, 2.8), paso=2)
    # ───── 7. aerodinámica: encima del coche, el aire lo recorre
    cG = Camara("cam_G_aero", col, 30.0)
    cG.seguir(ctx.centro)
    pos_G = lambda f: cp(f) + Vector((lerp(-2.8, -3.2, (f - 1330) / 110.0), lerp(3.4, 2.6, (f - 1330) / 110.0), 2.1)) + micro(f, 0.005)
    reg.append((1330, 1440, pos_G))
    cG.claves(1330, 1440, pos_G, None,
              flente=lambda f: 30.0, fdof=lambda f: (4.4, 3.5), paso=2)
    # ───── 8. trasera con orbital parcial: pilotos rojos
    cH = Camara("cam_H_trasera", col, 28.0)
    cH.seguir(ctx.centro)

    def pos_H(f):
        u = (f - 1440) / 180.0
        a = math.radians(lerp(42, 6, suave(u)))
        d = lerp(4.8, 5.8, u)
        return cp(f) + Vector((-math.sin(a) * d, math.cos(a) * d, lerp(1.0, 1.25, u))) + micro(f, 0.006)
    reg.append((1440, 1620, pos_H))
    cH.claves(1440, 1620, pos_H, None, flente=lambda f: 28.0, fdof=lambda f: (5.2, 3.5), paso=2)
    # ───── 9. despedida: la cámara se queda y el coche se aleja por la avenida
    cI = Camara("cam_I_despedida", col, 40.0)
    cI.seguir(ctx.centro)
    PI = Vector((-2.6, y_c(1620) + 9.0, 1.2))
    reg.append((1620, guion.TOTAL, lambda f: PI + micro(f, 0.003)))
    cI.claves(1620, guion.TOTAL - 1, lambda f: PI + micro(f, 0.003), None, flente=lambda f: lerp(40.0, 85.0, (f - 1620) / 180.0),
              fdof=lambda f: (dist(PI, f), 4.5), paso=2)
    todas = [(0, cA), (150, cB), (330, cA), (700, cC), (880, cD), (1060, cE), (1200, cF), (1330, cG), (1440, cH), (1620, cI)]
    velos = {}
    for f, c in todas:
        v = ctx.dir.corte(f, c)
        if v is not None:
            velos[c.o.name] = v
    v0 = ctx.dir.velos["cam_A_pasada"]
    v0.rampa(0, 18, 1.0, 0.0, (0, 0, 0))
    # al pasar la onda por la lente: destello cálido breve (la presión) antes de que la cámara se recupere
    v0.rampa(CUADRO_ONDA - 1, CUADRO_ONDA + 1, 0.0, 0.0, (1.0, 0.85, 0.6), 1.0)
    vI = ctx.dir.velos["cam_I_despedida"]
    vI.rampa(1776, 1799, 0.0, 1.0, (0, 0, 0))
    # distorsión de la lente y dispersión cromática con la llegada de la onda a la cámara y en cada ráfaga de vidrio
    marco.pulso(ctx.comp["disp"], [(0, 0.008), (CUADRO_ONDA - 2, 0.008), (CUADRO_ONDA + 2, 0.22), (CUADRO_ONDA + 24, 0.07), (CUADRO_ONDA + 90, 0.012), (1799, 0.012)])
    marco.pulso(ctx.comp["dist"], [(0, 0.0), (CUADRO_ONDA - 2, 0.0), (CUADRO_ONDA + 2, -0.55), (CUADRO_ONDA + 14, 0.18), (CUADRO_ONDA + 30, -0.08), (CUADRO_ONDA + 70, 0.0), (1799, 0.0)])
    esc = {}
    for a, b, fn in reg:
        for f in range(a, b):
            esc[f] = [float(x) for x in fn(f)]
    ctx.oyente = esc
    ctx.camaras = {"A": cA, "B": cB, "C": cC, "D": cD, "E": cE, "F": cF, "G": cG, "H": cH, "I": cI}
    return col
