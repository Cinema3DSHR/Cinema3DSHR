"""s9 «El generoso» (1440–1662): casa sencilla y familia que festeja, un aula con becas, cajas de ayuda y un frasco de ahorro con una planta que crece (el futuro)."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import sh3d
import casa as CASA
import saldo as SAL
import personas as P
import guion


def construir(ctx, i, f0, f1):
    col = coleccion("S9_Generoso")
    O = Vector(ctx.desp(i))
    rng = random.Random(33)
    ctx.amb.append((f0 - 1, (0.45, 0.6, 0.85), 1.3))
    # ─── a) casa sencilla con la familia en el frente (Kate y Aiden festejan; dos clones de invitados)
    CASA.casa(col, O, 8.0, 6.0, 2.5, estilo="clasica", rng=rng, color=(0.9, 0.85, 0.72), techo_color=(0.3, 0.14, 0.1))
    CASA.jardin(col, O, 8.0, 6.0, rng, arboles=4)
    sol = bpy.data.lights.new("sol_s9", "SUN")
    sol.energy = 5.5
    sol.color = (1.0, 0.9, 0.75)
    sol.angle = math.radians(2.0)
    so = bpy.data.objects.new("sol_s9", sol)
    col.objects.link(so)
    so.rotation_euler = (math.radians(55), 0, math.radians(-25))
    ka = ctx.kate
    ai = ctx.aiden
    a, b = f0, f0 + 70
    pos_k = O + Vector((-1.2, -3.2, 0.15))
    pos_a = O + Vector((1.2, -3.2, 0.15))
    P.colocar(ka, [(a - 1, (0, 0, -800), 0), (a, pos_k, ka.mirar(0, -1)), (b, pos_k, ka.mirar(0, -1))])
    P.colocar(ai, [(a, pos_a, ai.mirar(0, -1)), (b, pos_a, ai.mirar(0, -1))])
    P.clip(ka, "festejar", a, b, mapa=lambda f: (f - a) * 0.9)
    P.clip(ai, "aplaudir", a, b, mapa=lambda f: (f - a) * 0.9 + 4)
    # ─── b) aula: pupitres de Sweet Home mirando al pizarrón, estantes con libros, cartel BECAS
    A = O + Vector((40.0, 0, 0))
    piso = mat("piso_aula", (0.35, 0.27, 0.18), rug=0.4)
    pared = mat("pared_aula", (0.8, 0.82, 0.75), rug=0.7)
    caja("piso_a", A + Vector((0, 4.0, -0.05)), (8.0, 9.0, 0.1), col, piso)
    caja("techo_a", A + Vector((0, 4.0, 3.05)), (8.0, 9.0, 0.1), col, pared)
    caja("pared_af", A + Vector((0, 8.55, 1.5)), (8.0, 0.1, 3.0), col, pared)
    caja("pared_ai", A + Vector((-4.05, 4.0, 1.5)), (0.1, 9.0, 3.0), col, pared)
    caja("pared_ad", A + Vector((4.05, 4.0, 1.5)), (0.1, 9.0, 3.0), col, pared)
    caja("pared_aa", A + Vector((0, -0.55, 1.5)), (8.0, 0.1, 3.0), col, pared)
    pizarron = mat("pizarron", (0.04, 0.12, 0.08), rug=0.9)
    caja("pizarron", A + Vector((0, 8.45, 1.6)), (5.0, 0.04, 1.4), col, pizarron)
    et = SAL.etiqueta(col, "BECAS PARA ESTUDIAR", alto_m=0.5, color=(255, 255, 255, 255), fuerza=1.5)
    et.location = A + Vector((0, 8.4, 1.7))
    for fila in range(3):
        for k in range(4):
            x = -2.4 + k * 1.6
            y = 2.4 + fila * 1.8
            sh3d.poner("table_school_desk", col, A + Vector((x, y, 0)), frente=(0, 1))          # el frente del pupitre mira al pizarrón (+Y)
            sh3d.poner("chair_class_seat", col, A + Vector((x, y - 0.55, 0)), frente=(0, 1))     # el asiento mira al pupitre y al pizarrón
    for k in range(3):
        sh3d.poner("shelf_bookcase_3", col, A + Vector((-3.7, 1.5 + k * 2.8, 0)), frente=(1, 0))
    lm = mat_emisivo("luz_aula", (1.0, 0.95, 0.85), 2.6)
    for k in range(3):
        caja("panel_a", A + Vector((-2.5 + 2.5 * k, 4.0, 3.0)), (0.6, 7.0, 0.04), col, lm)
    rl = bpy.data.lights.new("luz_aula_a", "AREA")
    rl.energy = 500.0
    rl.size = 4.0
    ro = bpy.data.objects.new("luz_aula_a", rl)
    col.objects.link(ro)
    ro.location = A + Vector((0, 3.0, 2.9))
    # estudiantes: clones de Kate y Aiden detrás de los pupitres aplaudiendo
    estu = []
    for k, base in enumerate((ka, ai, ka)):
        pc = P.clonar(base, f"est{k}", col)
        estu.append(pc)
        px = (-1.6, 0.0, 1.6)[k]
        P.colocar(pc, [(f0 + 69, (0, 0, -800), 0), (f0 + 70, A + Vector((px, 3.3, 0)), pc.mirar(0, -1)), (f0 + 130, A + Vector((px, 3.3, 0)), pc.mirar(0, -1))])
        P.clip(pc, "aplaudir", f0 + 70, f0 + 130, mapa=lambda f, k=k: (f - f0 - 70) * 0.9 + 6 * k)
    # ─── c) cajas de ayuda y alimentos en una mesa larga
    C = O + Vector((80.0, 0, 0))
    caja("piso_c", C + Vector((0, 3.0, -0.05)), (8.0, 8.0, 0.1), col, mat("piso_c", (0.45, 0.42, 0.38), rug=0.6))
    caja("fondo_c", C + Vector((0, 7.05, 1.5)), (8.0, 0.1, 3.0), col, mat("fondo_c", (0.7, 0.72, 0.78), rug=0.7))
    sh3d.poner("table_folding_table", col, C + Vector((0, 4.0, 0)), frente=(0, -1))
    sh3d.poner("table_folding_table", col, C + Vector((2.2, 4.0, 0)), frente=(0, -1))
    for k in range(6):
        sh3d.poner("crate_2", col, C + Vector((-1.0 + k * 0.7, 4.0, 0.75)), frente=(0, -1), escala=0.8)
    for k in range(4):
        sh3d.poner("cardboard_box", col, C + Vector((2.4 + (k % 2) * 0.6, 4.0 + (k // 2) * 0.1, 0.75 + (k // 2) * 0.3)), frente=(0, -1))
    et2 = SAL.etiqueta(col, "AYUDA PARA QUIEN LA NECESITA", alto_m=0.35, color=(255, 255, 255, 255), fuerza=1.5)
    et2.location = C + Vector((0, 6.95, 2.3))
    rl2 = bpy.data.lights.new("luz_c", "AREA")
    rl2.energy = 500.0
    rl2.size = 4.0
    ro2 = bpy.data.objects.new("luz_c", rl2)
    col.objects.link(ro2)
    ro2.location = C + Vector((0, 3.0, 2.8))
    # ─── d) frasco de ahorro con monedas y un brote que crece
    J = O + Vector((120.0, 0, 0))
    caja("mesa_j", J + Vector((0, 2.0, -0.025)), (3.0, 3.0, 0.05), col, mat("mesa_j", (0.35, 0.22, 0.12), rug=0.35))
    vidrio = mat_vidrio_rapido("vidrio_frasco", (0.85, 0.95, 1.0))
    cilindro("frasco", J + Vector((0, 2.0, 0.3)), 0.28, 0.6, col, vidrio, seg=48)
    oro = mat("moneda_frasco", (1.0, 0.72, 0.2), metal=1.0, rug=0.25)
    monedas = []
    for k in range(60):
        m_ = cilindro(f"mon_f_{k}", J + Vector((rng.uniform(-0.12, 0.12), 2.0 + rng.uniform(-0.12, 0.12), 0.03 + 0.0085 * k)), 0.1, 0.02, col, oro, seg=24)
        monedas.append(m_)
        m_.scale = (0.001, 0.001, 0.001)
        m_.keyframe_insert("scale", frame=f0 + 120 + int(k * 0.5))
        m_.scale = (1, 1, 1)
        m_.keyframe_insert("scale", frame=f0 + 124 + int(k * 0.5))
    brote = sh3d.poner("bush_plant_3", col, J + Vector((0, 2.0, 0.62)), frente=(0, -1), escala=0.001)
    for o_ in sh3d.ULTIMOS:
        if o_.parent is None:
            for f_, s_ in ((f0 + 150, 0.001), (f1 - 1, 0.7)):
                o_.scale = (s_, s_, s_)
                o_.keyframe_insert("scale", frame=f_)
    et3 = SAL.etiqueta(col, "AHORRO PARA EL FUTURO", alto_m=0.12, color=(255, 255, 255, 255), fuerza=1.5)
    et3.location = J + Vector((0, 1.8, 1.0))
    rl3 = bpy.data.lights.new("luz_j", "AREA")
    rl3.energy = 120.0
    rl3.size = 1.5
    ro3 = bpy.data.objects.new("luz_j", rl3)
    col.objects.link(ro3)
    ro3.location = J + Vector((0.6, 1.0, 1.8))
    ro3.rotation_euler = (math.radians(35), 0, math.radians(15))
    # ─── cámaras
    cams = []
    c1 = Camara("cam_s9_a", col, 26.0)
    c1.claves(f0, f0 + 70, lambda f: O + Vector((lerp(-3.0, 2.5, (f - f0) / 70.0), -9.0, lerp(1.0, 1.6, (f - f0) / 70.0))), lambda f: O + Vector((0, -3.2, 1.2)), fdof=lambda f: (6.0, 3.5), paso=1)
    c2 = Camara("cam_s9_b", col, 24.0)
    c2.claves(f0 + 70, f0 + 130, lambda f: A + Vector((lerp(-2.5, 2.0, (f - f0 - 70) / 60.0), 0.3, 1.5)), lambda f: A + Vector((0, 6.0, 1.3)), fdof=lambda f: (6.0, 4.0), paso=1)
    c3 = Camara("cam_s9_c", col, 28.0)
    c3.claves(f0 + 130, f0 + 170, lambda f: C + Vector((lerp(-2.0, 1.5, (f - f0 - 130) / 40.0), 0.8, 1.4)), lambda f: C + Vector((0.5, 4.0, 1.0)), fdof=lambda f: (4.0, 3.2), paso=1)
    c4 = Camara("cam_s9_d", col, 40.0)
    c4.claves(f0 + 170, f1, lambda f: J + Vector((lerp(0.9, 0.4, (f - f0 - 170) / (f1 - f0 - 170)), 0.9, lerp(0.5, 0.75, (f - f0 - 170) / (f1 - f0 - 170)))), lambda f: J + Vector((0, 2.0, 0.55)), fdof=lambda f: (1.3, 2.4), paso=1)
    for f_, c_ in ((f0, c1), (f0 + 70, c2), (f0 + 130, c3), (f0 + 170, c4)):
        ctx.dir.corte(f_, c_)
    ctx.escena_activa(col, f0, f1)
