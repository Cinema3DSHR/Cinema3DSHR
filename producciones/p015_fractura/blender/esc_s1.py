"""s1 «Corredor» (180–660): Aiden corre por un pasillo infinito; una explosión lo persigue; la onda de choque alcanza la cámara (transición F)."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import marco
import aiden as AID

LARGO = 130.0
ANCHO = 5.2
ALTO = 4.4
V = 6.5          # m/s de carrera
Y0 = 4.0


def pasillo(col, O):
    paredes = mat_ruido("pared_s1", (0.025, 0.03, 0.04), (0.10, 0.11, 0.13), 3.0, metal=0.7, rug=0.35, bump=0.25)
    suelo = mat_ruido("suelo_s1", (0.015, 0.017, 0.022), (0.07, 0.075, 0.09), 5.0, metal=0.85, rug=0.18, bump=0.15)
    costilla = mat("costilla_s1", (0.05, 0.055, 0.065), metal=0.9, rug=0.3)
    luz_c = mat_emisivo("tira_cian", (0.35, 0.85, 1.0), 14.0)
    luz_b = mat_emisivo("tira_blanca", (1.0, 0.96, 0.9), 9.0)
    luz_r = mat_emisivo("tira_roja", (1.0, 0.1, 0.05), 6.0)
    caja("suelo", O + Vector((0, LARGO / 2, -0.1)), (ANCHO, LARGO, 0.2), col, suelo)
    caja("techo", O + Vector((0, LARGO / 2, ALTO + 0.1)), (ANCHO, LARGO, 0.2), col, paredes)
    caja("pared_i", O + Vector((-ANCHO / 2 - 0.1, LARGO / 2, ALTO / 2)), (0.2, LARGO, ALTO), col, paredes)
    caja("pared_d", O + Vector((ANCHO / 2 + 0.1, LARGO / 2, ALTO / 2)), (0.2, LARGO, ALTO), col, paredes)
    caja("fondo_atras", O + Vector((0, -0.4, ALTO / 2)), (ANCHO + 0.4, 0.4, ALTO + 0.4), col, paredes)
    caja("fondo_fin", O + Vector((0, LARGO + 0.4, ALTO / 2)), (ANCHO + 0.4, 0.4, ALTO + 0.4), col, luz_b)
    r = random.Random(11)
    y = 1.5
    k = 0
    while y < LARGO:
        # costillas (arcos) cada 3 m
        caja(f"cost_t_{k}", O + Vector((0, y, ALTO - 0.15)), (ANCHO, 0.35, 0.3), col, costilla)
        caja(f"cost_i_{k}", O + Vector((-ANCHO / 2 + 0.12, y, ALTO / 2)), (0.25, 0.35, ALTO), col, costilla)
        caja(f"cost_d_{k}", O + Vector((ANCHO / 2 - 0.12, y, ALTO / 2)), (0.25, 0.35, ALTO), col, costilla)
        # tiras de luz en el techo y al ras del piso
        mm = luz_c if (k % 5) else luz_b
        caja(f"tira_t_{k}", O + Vector((0, y + 1.5, ALTO - 0.03)), (0.5, 1.6, 0.04), col, mm)
        caja(f"tira_i_{k}", O + Vector((-ANCHO / 2 + 0.02, y + 1.5, 0.35)), (0.04, 1.8, 0.1), col, luz_c)
        caja(f"tira_d_{k}", O + Vector((ANCHO / 2 - 0.02, y + 1.5, 0.35)), (0.04, 1.8, 0.1), col, luz_r if k % 7 == 3 else luz_c)
        # paneles con relieve
        if r.random() < 0.7:
            caja(f"panel_{k}", O + Vector((r.choice((-1, 1)) * (ANCHO / 2 - 0.08), y + 0.75, r.uniform(1.0, 3.0))), (0.12, 1.1, r.uniform(0.5, 1.2)), col, costilla)
        y += 3.0
        k += 1


def construir(ctx, i, f0, f1):
    col = coleccion("S1_Corredor")
    O = Vector(ctx.desp(i))
    pasillo(col, O)
    # --- mapa de tiempo: real hasta 540, después cámara lenta extrema
    T = Tiempo([(f0, 0.0), (540, (540 - f0) / 30.0), (600, (540 - f0) / 30.0 + 0.55), (660, (540 - f0) / 30.0 + 0.8)])
    ay = lambda f: Y0 + V * min(T(f), 12.0) + (0 if f < 540 else 0)
    # --- Aiden
    arm = ctx.aiden
    AID.segmento(arm, "correr", f0, 560, mapa=lambda f: T(f) * 30.0, ciclo=True)
    AID.segmento(arm, "salto_grande", 561, 660, mapa=lambda f: (T(f) - T(561)) * 30.0)
    yaw = math.pi
    pos = []
    for f in range(f0, 561, 3):
        pos.append((f, O + Vector((0, ay(f), 0)), yaw))
    pos.append((561, O + Vector((0, ay(561), 0)), yaw))
    pos.append((660, O + Vector((0, ay(561), 0)), yaw))
    AID.colocar(arm, pos)
    # --- explosión que persigue: bola de fuego, onda, luz y escombros
    t_e = Tiempo([(420, 0.0), (540, 4.0), (600, 4.7), (660, 5.0)])
    fy = lambda f: ay(f) - lerp(30.0, 2.0, suave((f - 420) / 200.0)) - 7.0 * suave((f - 420) / 60.0)
    fb = bola_fuego("bola_s1", O + Vector((0, 20, 2.0)), 9.0, col, t_e, 420, 660, tau=0.6, semilla=3.0, emi=2.5)
    for f in range(420, 661, 2):
        fb.location = O + Vector((0, fy(f), 2.0))
        fb.keyframe_insert("location", frame=f)
    luz = bpy.data.lights.new("luz_explosion_s1", "POINT")
    luz.energy = 0.0
    luz.shadow_soft_size = 3.0
    luz.color = (1.0, 0.45, 0.12)
    lo = bpy.data.objects.new("luz_explosion_s1", luz)
    col.objects.link(lo)
    for f in range(420, 661, 4):
        k = suave((f - 420) / 40.0)
        luz.energy = 30000.0 * k
        luz.keyframe_insert("energy", frame=f)
        lo.location = O + Vector((0, fy(f) + 6.0, 2.2))
        lo.keyframe_insert("location", frame=f)
    # onda de choque: cáscara de vidrio que alcanza a la cámara cerca de f=640
    ond = onda_choque("onda_s1", O + Vector((0, 0, 2.0)), 40.0, col, t_e, 420, 660, vel=1.0)
    for f in range(420, 661, 2):
        t = t_e(f)
        c = fy(f) + 7.0
        # frente de la onda = 3 m por delante de la bola, siempre tangente al pasillo: se desplaza con ella
        r = 4.0 + 28.0 * suave((f - 420) / 235.0)
        ond.scale = (r, r, r)
        ond.keyframe_insert("scale", frame=f)
        ond.location = O + Vector((0, ay(min(f, 561)) - 20 + 24 * suave((f - 420) / 235.0) - (r - 4.0) + 20 * suave((f - 540) / 100.0), 2.0))
        ond.keyframe_insert("location", frame=f)
    # escombros que vuelan pasillo adelante
    mats = [mat("escombro_s1", (0.07, 0.07, 0.08), metal=0.6, rug=0.4), mat("escombro_s1b", (0.04, 0.04, 0.045), metal=0.9, rug=0.3)]
    fr = nube_fragmentos("esc_s1", col, mats, 150, O + Vector((0, 20, 2.0)), 4.0, 14.0, 6.0, 5, tam=(0.15, 0.55), gz_up=0.2, w_max=8.0, variantes=6)
    for q in fr:
        q.v = Vector((q.v.x * 0.15, abs(q.v.y) * 1.6 + 6.0, q.v.z * 0.4 + 1.0))
        q.p = Vector((q.p.x * 0.4, fy(420) + 4.0 + q.p.y * 0.3, abs(q.p.z) * 0.6 + 0.5)) + O
    tray = simular(fr, 8.0, g=(0, 0, -9.0), suelo=O.z + 0.05, rest=0.35)
    animar_trayectorias(tray, Tiempo([(420, 0.0), (540, 4.0), (600, 4.7), (660, 5.0)]), 420, 660, paso=3)
    # chispas: motas calientes
    # luz que acompaña a Aiden (frío arriba/atrás) y luz de relleno cálida desde adelante
    for nom, off, col_l, en, sz in (("aiden_key_s1", (0.8, -1.8, 3.6), (0.7, 0.85, 1.0), 900.0, 2.5), ("aiden_kick_s1", (-0.6, 3.2, 2.0), (1.0, 0.7, 0.45), 500.0, 1.5)):
        ll = bpy.data.lights.new(nom, "AREA")
        ll.energy = en
        ll.size = sz
        ll.color = col_l
        lo2 = bpy.data.objects.new(nom, ll)
        col.objects.link(lo2)
        for f in range(f0, 661, 6):
            lo2.location = O + Vector((0, ay(min(f, 561)), 0)) + Vector(off)
            lo2.keyframe_insert("location", frame=f)
        lo2.rotation_euler = (math.radians(180 if off[2] > 3 else 100), 0, 0) if off[2] > 3 else (math.radians(-80), 0, math.radians(180))
    # --- cámaras
    cams = []

    def aid(f):
        return O + Vector((0, ay(min(f, 561)), 0))

    def cabeza(f):
        return aid(f) + Vector((0, 0, 1.25))

    # 1) travelling hacia atrás por delante de Aiden (baja, gran angular)
    c1 = Camara("cam_s1_a", col, 24.0)
    c1.claves(f0, 270, lambda f: cabeza(f) + Vector((lerp(0.4, -0.5, suave((f - f0) / 90.0)), 5.0, -0.55)), lambda f: cabeza(f) + Vector((0, 0, -0.1)),
              flente=lambda f: lerp(24.0, 30.0, suave((f - f0) / 90.0)), fdof=lambda f: (5.0, 2.4))
    # 2) lateral con teleobjetivo y poca profundidad
    c2 = Camara("cam_s1_b", col, 30.0)
    c2.claves(270, 360, lambda f: aid(f) + Vector((-2.3, lerp(1.5, -2.0, suave((f - 270) / 90.0)), 1.1)), lambda f: aid(f) + Vector((0, 0.3, 1.05)),
              fdof=lambda f: (2.4, 2.8))
    # 3) cenital siguiéndolo
    c3 = Camara("cam_s1_c", col, 26.0)
    c3.claves(360, 450, lambda f: aid(f) + Vector((0.3, -1.0, 3.7)), lambda f: aid(f) + Vector((0, 1.5, 0.0)), fdof=lambda f: (3.7, 3.0))
    # 4) seguimiento desde atrás a ras de piso, con la explosión creciendo
    c4 = Camara("cam_s1_d", col, 20.0)
    c4.claves(450, 540, lambda f: aid(f) + Vector((lerp(1.2, -0.4, suave((f - 450) / 90.0)), -3.4, 0.55)), lambda f: aid(f) + Vector((0, 2.5, 1.2)),
              flente=lambda f: lerp(20.0, 28.0, suave((f - 450) / 90.0)), fdof=lambda f: (5.0, 3.5))
    # 5) la onda de choque nos alcanza: la cámara frena detrás de Aiden, ya en cámara lenta
    c5 = Camara("cam_s1_e", col, 24.0)
    base5 = lambda f: aid(f) + Vector((-0.5, -3.6, 1.0))
    c5.claves(540, 660, lambda f: base5(540) + Vector((0.0, 4.0 * (T(f) - T(540)) / 0.8 * 0.9, 0.0)) + Vector((0, 0, 0.35 * suave((f - 540) / 120.0))),
              lambda f: aid(561) + Vector((0, 2.5 + 3.0 * suave((f - 561) / 90.0), 1.3 + 0.8 * suave((f - 561) / 90.0))),
              flente=lambda f: lerp(24.0, 17.0, suave((f - 540) / 120.0)), fdof=lambda f: (4.5, 3.0))
    for f_, c_ in ((f0, c1), (270, c2), (360, c3), (450, c4), (540, c5)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 4, 1.0, 0.0, (0, 0, 0))
    v5 = ctx.dir.velos["cam_s1_e"]
    v5.rampa(628, 650, 0.0, 1.0, (1.0, 0.85, 0.6), 6.0)
    v5.clave(659, 1.0, (1.0, 0.85, 0.6), 6.0)
    # aberración cromática y destello de la onda
    marco.pulso(ctx.comp["disp"], [(f0, 0.012), (610, 0.012), (640, 0.12), (659, 0.2)])
    marco.pulso(ctx.comp["dist"], [(f0, 0.0), (610, 0.0), (645, -0.25), (659, -0.5)])
    ctx.amb.append((f0, (0.01, 0.015, 0.025), 0.4))
    ctx.escena_activa(col, f0, f1)
