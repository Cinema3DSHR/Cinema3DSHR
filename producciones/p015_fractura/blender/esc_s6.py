"""s6 «Oscuro» (3000–3750): Aiden flotando entre restos en la oscuridad. Macros con luz de borde, polvo, bruma volumétrica, ojo, mano y vuelo entre escombros;
al final un anillo de luz crece a su alrededor y llega a la cámara."""
import math
import random
import bpy
from mathutils import Vector, Quaternion, Euler
import lib
from lib import *
import marco
import aiden as AID

T = Tiempo([(3000, 0.0), (3750, 25.0)])


def construir(ctx, i, f0, f1):
    col = coleccion("S6_Oscuro")
    O = Vector(ctx.desp(i))
    r = random.Random(61)
    C = O + Vector((0, 0, 2.0))
    campo_estrellas(col, 250, 300.0, 17)
    for o in col.objects:
        if o.name.startswith("estrella_"):
            o.location += O
    metal = mat_ruido("restos_s6", (0.02, 0.022, 0.026), (0.12, 0.13, 0.15), 3.0, metal=0.85, rug=0.35, bump=0.4)
    quemado = mat("quemado_s6", (0.01, 0.008, 0.007), rug=0.6)
    vidrio = mat_vidrio_rapido("vidrio_s6", (0.75, 0.9, 1.0))
    brasa = mat_emisivo("brasa_s6", (1.0, 0.4, 0.08), 20.0)
    # ───── restos que derivan
    sim = []
    for k in range(46):
        d = Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))).normalized() * r.uniform(2.5, 14.0)
        tipo = r.random()
        if tipo < 0.4:
            o = caja(f"resto_{k}", C + d, (r.uniform(0.6, 3.0), r.uniform(0.05, 0.2), r.uniform(0.6, 2.5)), col, metal)
        elif tipo < 0.75:
            o = cilindro(f"tubo_{k}", C + d, r.uniform(0.04, 0.14), r.uniform(1.0, 4.0), col, metal, seg=10)
        else:
            o = esquirla(f"fragm_{k}", (r.uniform(0.4, 1.4), r.uniform(0.4, 1.4), r.uniform(0.1, 0.4)), 600 + k, col, quemado)
            o.location = C + d
        o.rotation_mode = "QUATERNION"
        sim.append(Fragmento(o, C + d, Vector((r.gauss(0, 0.18), r.gauss(0, 0.18), r.gauss(0, 0.18))), Quaternion((1, 0, 0, 0)), Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * r.uniform(0.05, 0.3)))
    vid = nube_fragmentos("vid_s6", col, [vidrio], 40, C, 7.0, 0.3, 0.15, 63, tam=(0.15, 0.5), gz_up=0.0, w_max=0.8, variantes=6)
    bra = nube_fragmentos("bra_s6", col, [brasa], 70, C, 8.0, 0.35, 0.2, 65, tam=(0.02, 0.06), gz_up=0.0, w_max=2.0, variantes=3)
    sim += vid + bra
    tray = simular(sim, 26.0, g=(0, 0, 0), arrastre=0.0, muestreo=1.0 / 30.0)
    animar_trayectorias(tray, T, f0, f1, paso=6)
    polvo(col, C, (7, 7, 5), 260, 7, T, f0, f1, 0.05, 0.016)
    # ───── Aiden flotando (giro lento)
    arm = ctx.aiden
    AID.segmento(arm, "flotar", f0, f1, mapa=lambda f: (f - f0) * 0.45, ciclo=True)
    raiz = bpy.data.objects["PJ_aiden"]
    raiz.rotation_mode = "XYZ"
    for f in range(f0, f1 + 1, 15):
        u = (f - f0) / 750.0
        raiz.location = C + Vector((0.0, 0.0, 0.18 * math.sin(u * 7.0) - 1.0))
        raiz.rotation_euler = (math.radians(14 * math.sin(u * 5.0)), math.radians(8 * math.sin(u * 3.0 + 1)), math.radians(20 + 300 * u * 0.6))
        raiz.keyframe_insert("location", frame=f)
        raiz.keyframe_insert("rotation_euler", frame=f)
    cabeza = ctx.head
    mano = AID.vacio(col, arm, "mixamorig:RightHand", "AIDEN_mano_der")
    # ───── luces: borde frío desde atrás-arriba, reflejos cálidos, intermitencia roja
    sp = bpy.data.lights.new("borde_s6", "SPOT")
    sp.energy = 6000.0
    sp.spot_size = math.radians(40)
    sp.spot_blend = 0.5
    sp.color = (0.55, 0.78, 1.0)
    sp.shadow_soft_size = 0.4
    spo = bpy.data.objects.new("borde_s6", sp)
    col.objects.link(spo)
    spo.location = C + Vector((-3.0, 5.5, 5.0))
    spo.rotation_euler = (C - spo.location).to_track_quat("-Z", "Y").to_euler()
    for f, e in ((f0, 0.0), (f0 + 60, 1.0), (3640, 1.0), (3700, 0.2)):
        sp.energy = 6000.0 * e
        sp.keyframe_insert("energy", frame=f)
    al = bpy.data.lights.new("alarma_s6", "POINT")
    al.color = (1.0, 0.1, 0.05)
    al.shadow_soft_size = 0.3
    alo = bpy.data.objects.new("alarma_s6", al)
    col.objects.link(alo)
    alo.location = C + Vector((4.5, -3.5, 0.5))
    for f in range(f0, f1 + 1, 6):
        al.energy = 500.0 * (1.0 if (f // 30) % 2 == 0 else 0.1)
        al.keyframe_insert("energy", frame=f)
    ca = bpy.data.lights.new("calida_s6", "AREA")
    ca.energy = 700.0
    ca.size = 2.0
    ca.color = (1.0, 0.6, 0.3)
    cao = bpy.data.objects.new("calida_s6", ca)
    col.objects.link(cao)
    cao.location = C + Vector((3.0, -4.0, 1.0))
    cao.rotation_euler = (C - cao.location).to_track_quat("-Z", "Y").to_euler()
    # ───── haz de luz volumétrico FALSO (cono translúcido, barato): el volumen de verdad costaba más de la mitad del cuadro
    hz = bpy.data.materials.new("haz_s6")
    hz.use_nodes = True
    nt = hz.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em_ = nt.nodes.new("ShaderNodeEmission")
    em_.inputs["Color"].default_value = (0.55, 0.78, 1.0, 1)
    em_.inputs["Strength"].default_value = 0.9
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.3
    ru = nt.nodes.new("ShaderNodeTexNoise")
    ru.inputs["Scale"].default_value = 2.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], ru.inputs["Vector"])
    mulf = nt.nodes.new("ShaderNodeMath")
    mulf.operation = "MULTIPLY"
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.5
    nt.links.new(inv.outputs[0], pw.inputs[0])
    nt.links.new(pw.outputs[0], mulf.inputs[0])
    nt.links.new(ru.outputs["Fac"], mulf.inputs[1])
    esc_ = nt.nodes.new("ShaderNodeMath")
    esc_.operation = "MULTIPLY"
    esc_.inputs[1].default_value = 0.16
    nt.links.new(mulf.outputs[0], esc_.inputs[0])
    nt.links.new(esc_.outputs[0], mz.inputs["Fac"])
    nt.links.new(tr.outputs[0], mz.inputs[1])
    nt.links.new(em_.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], out.inputs["Surface"])
    dirv = (C - spo.location)
    L = dirv.length
    cono = cilindro("haz_s6", spo.location + dirv * 0.5, 1.0, L, col, hz, seg=24)
    cono.rotation_euler = dirv.to_track_quat("Z", "Y").to_euler()
    cono.visible_shadow = False
    cono.visible_glossy = False
    # ───── anillo de luz final
    ar = mat_emisivo("anillo_s6", (0.8, 0.95, 1.0), 40.0)
    an = toro("anillo_s6", C, 1.0, 0.03, col, ar, rot=(math.radians(90), 0, 0), seg=96, seg_r=8)
    an.visible_shadow = False
    for f in range(3640, f1 + 1, 2):
        u = (f - 3640) / 109.0
        s_ = 0.05 + 12.0 * u ** 2.2
        an.scale = (s_, s_, s_)
        an.keyframe_insert("scale", frame=f)
        an.location = C + Vector((0, -0.4 - 5.0 * u, 0))
        an.keyframe_insert("location", frame=f)
    an.hide_render = False
    # ───── cámaras
    cA = Camara("cam_s6_a", col, 30.0)
    cA.seguir(cabeza)
    cA.claves(f0, 3120, lambda f: C + Vector((math.cos(math.radians(lerp(-120, -60, (f - f0) / 120.0))) * 3.4, math.sin(math.radians(lerp(-120, -60, (f - f0) / 120.0))) * 3.4, lerp(0.3, 0.9, (f - f0) / 120.0))), None, fdof=lambda f: (3.4, 2.2))
    cB = Camara("cam_s6_b", col, 70.0)
    cB.seguir(cabeza)
    def rz(f):
        return math.radians(20 + 300 * ((f - f0) / 750.0) * 0.6)

    def delante(f, dist, ang=0.0, alto=0.0):
        a = rz(f) + ang
        return C + Vector((0, 0, 0.75 + alto)) + Vector((math.sin(a) * dist, -math.cos(a) * dist, 0))
    cB.claves(3120, 3250, lambda f: delante(f, lerp(1.5, 1.15, (f - 3120) / 130.0), math.radians(25), 0.05), None, fdof=lambda f: (lerp(1.5, 1.15, (f - 3120) / 130.0), 2.8))
    cC = Camara("cam_s6_c", col, 60.0)
    cC.seguir(mano)
    cC.claves(3250, 3380, lambda f: delante(f, lerp(1.9, 1.4, (f - 3250) / 130.0), math.radians(-70), -0.5), None, fdof=lambda f: (lerp(1.9, 1.4, (f - 3250) / 130.0), 2.8))
    cD = Camara("cam_s6_d", col, 22.0)
    cD.seguir(cabeza)
    cD.claves(3380, 3520, lambda f: C + Vector((lerp(-9.0, -1.8, suave((f - 3380) / 140.0)), lerp(-11.0, -2.6, suave((f - 3380) / 140.0)), lerp(2.5, 0.2, suave((f - 3380) / 140.0)))), None, fdof=lambda f: (lerp(14.0, 3.2, suave((f - 3380) / 140.0)), 2.2))
    cE = Camara("cam_s6_e", col, 20.0)
    cE.seguir(cabeza)
    cE.claves(3520, 3640, lambda f: C + Vector((math.cos(math.radians(lerp(40, 160, (f - 3520) / 120.0))) * 3.0, math.sin(math.radians(lerp(40, 160, (f - 3520) / 120.0))) * 3.0, lerp(-2.4, -1.6, (f - 3520) / 120.0))), None, fdof=lambda f: (3.2, 2.4))
    cF = Camara("cam_s6_f", col, 24.0)
    cF.seguir(cabeza)
    cF.claves(3640, f1, lambda f: C + Vector((0.0, lerp(-3.2, -2.2, (f - 3640) / 109.0), 0.5)), None, fdof=lambda f: (3.0, 3.0))
    for f_, c_ in ((f0, cA), (3120, cB), (3250, cC), (3380, cD), (3520, cE), (3640, cF)):
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 40, 1.0, 0.0, (0, 0, 0), 0.0)
    vF = ctx.dir.velos["cam_s6_f"]
    vF.rampa(3722, 3749, 0.0, 1.0, (0.85, 0.95, 1.0), 12.0)
    ctx.amb.append((f0 - 1, (0.001, 0.0015, 0.003), 0.35))
    ctx.escena_activa(col, f0, f1)
