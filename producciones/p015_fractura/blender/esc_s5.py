"""s5 «Colapso» (2400–3000): galería de columnas que se derrumba en dominó tras Aiden, que corre, rueda y salta en cámara lenta hacia una ventana de luz que estalla."""
import math
import random
import bpy
from mathutils import Vector, Quaternion, Euler
import lib
from lib import *
import marco
import aiden as AID

T = Tiempo([(2400, 0.0), (2700, 10.0), (2780, 12.6), (2860, 13.6), (2930, 14.3), (3000, 15.0)])
LARGO = 130.0


def construir(ctx, i, f0, f1):
    col = coleccion("S5_Colapso")
    O = Vector(ctx.desp(i))
    r = random.Random(51)
    piedra = mat_ruido("piedra_s5", (0.04, 0.038, 0.036), (0.2, 0.19, 0.17), 3.5, rug=0.8, bump=0.6)
    losa = mat_ruido("losa_s5", (0.02, 0.02, 0.022), (0.09, 0.09, 0.1), 4.0, metal=0.2, rug=0.35, bump=0.3)
    luzv = mat_emisivo("ventana_s5", (1.0, 0.85, 0.6), 14.0)
    # suelo, paredes y techo con claros
    caja("suelo", O + Vector((0, LARGO / 2, -0.15)), (30, LARGO + 10, 0.3), col, losa)
    caja("pared_i", O + Vector((-14, LARGO / 2, 8)), (0.6, LARGO, 16), col, piedra)
    caja("pared_d", O + Vector((14, LARGO / 2, 8)), (0.6, LARGO, 16), col, piedra)
    caja("fondo", O + Vector((0, -6, 8)), (30, 0.6, 16), col, piedra)
    # ventana final (círculo luminoso) al fondo
    ven = cilindro("ventana", O + Vector((0, 108, 7)), 6.0, 0.3, col, luzv, rot=(math.radians(90), 0, 0), seg=48)
    marco_v = toro("marco_ventana", O + Vector((0, 107.7, 7)), 6.4, 0.4, col, piedra, rot=(math.radians(90), 0, 0), seg=48, seg_r=8)
    caja("muro_v", O + Vector((0, 109.2, 8)), (30, 0.6, 16), col, piedra)
    # columnas por pares en 5 segmentos + vigas + losas de techo
    sim = []
    ys_k = [20 + 10 * k for k in range(10)]
    Tcol = lambda yk: (yk - 4.0) / 6.5 + 0.9      # segundo en que Aiden ya pasó y la columna cae
    for k, yk in enumerate(ys_k):
        for sx in (-1, 1):
            base_t = Tcol(yk) if yk < 62 else (Tcol(yk) if yk > 70 else Tcol(yk) - 0.3)
            for s_ in range(5):
                z = 1.4 + s_ * 2.8
                c = cilindro(f"col_{k}_{sx}_{s_}", O + Vector((sx * 7.0, yk, z)), 0.95 - s_ * 0.02, 2.8, col, piedra, seg=20)
                c.rotation_mode = "QUATERNION"
                fr = Fragmento(c, c.location.copy(), Vector((-sx * r.uniform(0.5, 2.5) * (0.5 + s_ * 0.5), r.uniform(-1.0, 2.5) * 0.5, 0.0)), Quaternion((1, 0, 0, 0)),
                               Vector((r.uniform(-0.8, 0.8) + sx * 0.5 * (s_ + 1) * 0.4, r.uniform(-0.6, 0.6), r.uniform(-0.8, 0.8))))
                fr.t0 = base_t + s_ * 0.06 + (0.0 if sx > 0 else 0.25)
                sim.append(fr)
        # viga transversal
        b = caja(f"viga_{k}", O + Vector((0, yk, 14.2)), (14.6, 1.1, 1.1), col, piedra)
        b.rotation_mode = "QUATERNION"
        fb = Fragmento(b, b.location.copy(), Vector((0, r.uniform(-1, 1), -1.0)), Quaternion((1, 0, 0, 0)), Vector((r.uniform(-0.4, 0.4), r.uniform(-0.4, 0.4), r.uniform(-0.6, 0.6))))
        fb.t0 = Tcol(yk) + 0.3
        sim.append(fb)
        for sx in (-1, 0, 1):
            lz = caja(f"techo_{k}_{sx}", O + Vector((sx * 4.7, yk + 5.0, 15.2)), (4.5, 8.5, 0.5), col, losa)
            lz.rotation_mode = "QUATERNION"
            fl = Fragmento(lz, lz.location.copy(), Vector((r.gauss(0, 0.8), r.gauss(0, 0.8), -1.5)), Quaternion((1, 0, 0, 0)), Vector((r.gauss(0, 0.5), r.gauss(0, 0.5), r.gauss(0, 0.4))))
            fl.t0 = Tcol(yk) + 0.5 + abs(sx) * 0.2
            sim.append(fl)
    esc = nube_fragmentos("esc_s5", col, [piedra, losa], 150, O + Vector((0, 60, 10)), 1.0, 3.0, 2.0, 53, tam=(0.2, 0.9), gz_up=0.2, w_max=6.0, variantes=8)
    for q in esc:
        yk = r.choice(ys_k)
        q.p = O + Vector((r.uniform(-9, 9), yk + r.uniform(-4, 4), r.uniform(8, 15)))
        q.v = Vector((r.gauss(0, 1.2), r.gauss(0, 1.2), r.gauss(0, 1.0)))
        q.t0 = Tcol(yk) + r.uniform(0.2, 1.5)
    sim += esc
    tray = simular(sim, 16.0, g=(0, 0, -9.8), suelo=O.z + 0.0, rest=0.22, arrastre=0.03)
    animar_trayectorias(tray, T, f0, f1, paso=2)
    # ───── Aiden: corre → rueda bajo una columna → corre → salta en cámara lenta hacia la ventana
    arm = ctx.aiden
    run_a, roll0, run_b, jump0 = f0, 2640, 2712, 2780
    ya = lambda f: 4.0 + 6.5 * T(min(f, roll0)) - 6.5 * T(f0)
    y_roll1 = ya(roll0) + 7.1
    y_run_b = y_roll1 + 6.5 * (T(jump0) - T(run_b))
    AID.segmento(arm, "correr", run_a, roll0 - 1, mapa=lambda f: (T(f) - T(f0)) * 30.0, ciclo=True)
    AID.segmento(arm, "rodar", roll0, run_b - 1, mapa=lambda f: (T(f) - T(roll0)) * 30.0)
    AID.segmento(arm, "correr", run_b, jump0 - 1, mapa=lambda f: (T(f) - T(run_b)) * 30.0, ciclo=True)
    AID.segmento(arm, "salto_grande", jump0, f1, mapa=lambda f: (T(f) - T(jump0)) * 30.0)
    pos = []
    for f in range(f0, roll0, 4):
        pos.append((f, O + Vector((0.0, ya(f), 0)), math.pi))
    pos.append((roll0, O + Vector((0, ya(roll0), 0)), math.pi))
    pos.append((roll0 + 1, O + Vector((0, ya(roll0), 0)), math.pi))
    pos.append((run_b - 1, O + Vector((0, ya(roll0), 0)), math.pi))
    pos.append((run_b, O + Vector((0, y_roll1, 0)), math.pi))
    for f in range(run_b, jump0, 4):
        pos.append((f, O + Vector((0, y_roll1 + 6.5 * (T(f) - T(run_b)), 0)), math.pi))
    pos.append((jump0, O + Vector((0, y_run_b, 0)), math.pi))
    pos.append((f1, O + Vector((0, y_run_b, 0)), math.pi))
    AID.colocar(arm, pos)
    hips = ctx.hips
    # ───── luces
    for nom, loc, en, cl, tam in (("claro_a", (0, 50, 22), 450000.0, (0.75, 0.85, 1.0), 14.0), ("claro_b", (0, 85, 22), 450000.0, (0.75, 0.85, 1.0), 14.0), ("calida_v", (0, 98, 7), 500000.0, (1.0, 0.7, 0.4), 12.0)):
        L = bpy.data.lights.new(nom, "AREA")
        L.energy = en
        L.size = tam
        L.color = cl
        lo = bpy.data.objects.new(nom, L)
        col.objects.link(lo)
        lo.location = O + Vector(loc)
        lo.rotation_euler = (math.radians(180), 0, 0) if loc[2] > 10 else (math.radians(90), 0, 0)
    sg = bpy.data.lights.new("aiden_s5", "AREA")
    sg.energy = 1800.0
    sg.size = 3.0
    sg.color = (0.9, 0.95, 1.0)
    so = bpy.data.objects.new("aiden_s5", sg)
    col.objects.link(so)
    for f in range(f0, f1 + 1, 6):
        so.location = hips_pos(O, f, ya, y_roll1, y_run_b, roll0, run_b, jump0, T) + Vector((1.0, -2.0, 4.0))
        so.keyframe_insert("location", frame=f)
    so.rotation_euler = (math.radians(150), 0, 0)
    # haces de luz (conos translúcidos, baratos) por los claros del techo
    haz = bpy.data.materials.new("haz_s5")
    haz.use_nodes = True
    nt = haz.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.95, 0.85, 1)
    em.inputs["Strength"].default_value = 2.5
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.2
    nt.links.new(lw.outputs["Facing"], mz.inputs["Fac"])
    nt.links.new(em.outputs[0], mz.inputs[1])
    nt.links.new(tr.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], out.inputs["Surface"])
    for k, (x, y) in enumerate(((-3, 40), (4, 55), (-2, 70), (3, 88))):
        c = cilindro(f"haz_{k}", O + Vector((x, y, 8)), 2.2, 16, col, haz, seg=24)
        c.scale = (1.0, 1.0, 1.0)
        c.visible_shadow = False
        c.rotation_euler = (math.radians(8), math.radians(-6), 0)
    polvo(col, O + Vector((0, 60, 6)), (12, 60, 7), 300, 5, T, f0, f1, 0.25, 0.03)
    # ───── cámaras
    ap = lambda f: hips_pos(O, f, ya, y_roll1, y_run_b, roll0, run_b, jump0, T)
    cA = Camara("cam_s5_a", col, 22.0)
    cA.claves(f0, 2480, lambda f: ap(f) + Vector((lerp(1.5, -1.0, (f - f0) / 80.0), -5.2, 0.4)), lambda f: ap(f) + Vector((0, 4, 0.0)), fdof=lambda f: (5.2, 2.8))
    cB = Camara("cam_s5_b", col, 30.0)
    cB.claves(2480, 2580, lambda f: ap(f) + Vector((-4.2, lerp(-1.5, 1.5, (f - 2480) / 100.0), 0.5)), lambda f: ap(f) + Vector((0, 0.5, 0.0)), fdof=lambda f: (4.4, 2.4))
    cC = Camara("cam_s5_c", col, 20.0)
    cC.claves(2580, 2680, lambda f: ap(f) + Vector((lerp(1.0, -0.6, (f - 2580) / 100.0), 4.0, 0.3)), lambda f: ap(f) + Vector((0, 0, 0.0)), fdof=lambda f: (4.0, 2.0))
    cD = Camara("cam_s5_d", col, 20.0)
    cD.claves(2680, 2780, lambda f: ap(f) + Vector((0.4, -0.8, 7.5)), lambda f: ap(f) + Vector((0, 1.5, -0.5)), fdof=lambda f: (7.5, 3.5))
    cE = Camara("cam_s5_e", col, 18.0)
    cE.claves(2780, 2900, lambda f: O + Vector((lerp(5.0, -4.0, (f - 2780) / 120.0), lerp(y_run_b - 12, y_run_b - 8, (f - 2780) / 120.0), lerp(1.2, 2.6, (f - 2780) / 120.0))), lambda f: ap(f) + Vector((0, 0, 0.2)), fdof=lambda f: (11.0, 3.0))
    cF = Camara("cam_s5_f", col, 24.0)
    cF.claves(2900, f1, lambda f: O + Vector((0, lerp(y_run_b - 10, y_run_b + 4, suave((f - 2900) / 99.0)), 1.4)), lambda f: O + Vector((0, 108, 7)), flente=lambda f: lerp(24.0, 40.0, suave((f - 2900) / 99.0)), fdof=lambda f: (25.0, 5.0))
    for f_, c_ in ((f0, cA), (2480, cB), (2580, cC), (2680, cD), (2780, cE), (2900, cF)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 20, 1.0, 0.0, (0.75, 0.92, 1.0), 10.0)
    vF = ctx.dir.velos["cam_s5_f"]
    vF.rampa(2950, 2975, 0.0, 1.0, (1.0, 0.85, 0.6), 8.0)
    vF.rampa(2975, 2999, 1.0, 1.0, (0.0, 0.0, 0.0), 0.0)
    ctx.amb.append((f0 - 1, (0.006, 0.007, 0.01), 0.5))
    ctx.escena_activa(col, f0, f1)


def hips_pos(O, f, ya, y_roll1, y_run_b, roll0, run_b, jump0, T):
    """Posición aproximada de la cadera de Aiden (para cámaras y luces), sin depender de la evaluación del NLA."""
    if f < roll0:
        return O + Vector((0, ya(f), 1.0))
    if f < run_b:
        u = (f - roll0) / float(run_b - roll0)
        return O + Vector((0, ya(roll0) + 7.1 * u, 0.7))
    if f < jump0:
        return O + Vector((0, y_roll1 + 6.5 * (T(f) - T(run_b)), 1.0))
    u = suave((f - jump0) / 220.0)
    return O + Vector((0, y_run_b + 12.0 * u, 1.0 + 2.2 * math.sin(math.pi * min(1.0, (f - jump0) / 190.0))))
