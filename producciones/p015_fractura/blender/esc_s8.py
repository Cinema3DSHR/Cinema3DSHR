"""s8 «Final» (4500–5400): montaje de ecos con distorsiones temporales, la esfera de espejos que se agrieta y estalla (transición G), el ojo del comienzo
reflejando los restos, y una única partícula de luz en la oscuridad."""
import math
import random
import bmesh
import bpy
from mathutils import Vector, Quaternion, Euler
import lib
from lib import *
import marco
import aiden as AID
import guion

RAD = 18.0
TS = 4905                                  # cuadro en que estalla la esfera
# tiempo de Aiden y de los restos: adelante, congelado, retroceso, adelante rápido…
TB = Tiempo([(4500, 0.0), (4540, 1.4), (4560, 1.4), (4590, 3.0), (4640, 3.4), (4660, 2.2), (4700, 1.0), (4730, 1.0), (4760, 4.0), (4800, 5.0), (5000, 9.0), (5400, 13.0)])
TX = Tiempo([(4500, 0.0), (TS, 0.0), (4960, 1.6), (5080, 3.4), (5139, 5.0)])


def sombras_cam(c):
    c.visible_shadow = False


def construir(ctx, i, f0, f1):
    col = coleccion("S8_Final")
    O = Vector(ctx.desp(i))
    r = random.Random(81)
    campo_estrellas(col, 700, 350.0, 21)
    for o in col.objects:
        if o.name.startswith("estrella_"):
            o.location += O
    cromo = mat("cromo_s8", (0.05, 0.08, 0.14), metal=1.0, rug=0.07)
    brasa = mat_emisivo("brasa_s8", (1.0, 0.5, 0.15), 18.0)
    # ───── esfera de espejos hecha de 320 fragmentos (se agrieta con costuras luminosas y estalla)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=RAD)
    caras = [[v.co.copy() for v in f.verts] for f in bm.faces]
    bm.free()
    sim = []
    for k, tri in enumerate(caras):
        c = sum(tri, Vector()) / 3.0
        verts = [(c + (p - c) * 0.985 - c) for p in tri]       # relativo al centro del fragmento, con una rendija
        me = bpy.data.meshes.new(f"frag_esf_{k}")
        me.from_pydata([tuple(v) for v in verts], [], [(0, 1, 2)])
        me.update()
        me.materials.append(cromo)
        o = bpy.data.objects.new(f"frag_esf_{k}", me)
        col.objects.link(o)
        sl = o.modifiers.new("grosor", "SOLIDIFY")
        sl.thickness = 0.12
        o.location = O + c
        o.rotation_mode = "QUATERNION"
        d = c.normalized()
        v = d * r.uniform(5.0, 20.0) + Vector((r.gauss(0, 2), r.gauss(0, 2), r.gauss(0, 2)))
        sim.append(Fragmento(o, O + c, v, Quaternion((1, 0, 0, 0)), Vector((r.gauss(0, 1), r.gauss(0, 1), r.gauss(0, 1))) * r.uniform(0.2, 1.4)))
    brasas = nube_fragmentos("bra_s8", col, [brasa], 120, O, 2.0, 25.0, 12.0, 83, tam=(0.03, 0.1), gz_up=0.0, w_max=10.0, variantes=3)
    sim += brasas
    tray = simular(sim, 7.0, g=(0, 0, 0), arrastre=0.01, muestreo=1.0 / 30.0)
    animar_trayectorias(tray, TX, f0, f1, paso=3)
    # núcleo emisivo: las costuras brillan cada vez más y todo se apaga al estallar
    nm = mat_emisivo("nucleo_esf_s8", (0.55, 0.85, 1.0), 6.0)
    nuc = esfera("nucleo_esf", O, RAD * 0.97, col, nm, 48, 32)
    nuc.visible_shadow = False
    em = nm.node_tree.nodes["Emission"].inputs["Strength"]
    for f, v in ((f0, 0.0), (4640, 0.0), (4800, 3.0), (4900, 9.0), (4906, 12.0), (4930, 0.0), (f1, 0.0)):
        em.default_value = v
        em.keyframe_insert("default_value", frame=f)
    lib._interp_id(nm.node_tree, "LINEAR")
    nuc.hide_render = False
    nuc.scale = (1, 1, 1)
    for f in (4929, 4931):
        nuc.scale = (1, 1, 1) if f < 4930 else (0.001, 0.001, 0.001)
        nuc.keyframe_insert("scale", frame=f)
    lz = bpy.data.lights.new("nucleo_luz_s8", "POINT")
    lz.color = (0.6, 0.85, 1.0)
    lzo = bpy.data.objects.new("nucleo_luz_s8", lz)
    col.objects.link(lzo)
    lzo.location = O
    for f, v in ((f0, 4000.0), (4800, 9000.0), (4906, 80000.0), (4960, 3000.0), (f1, 0.0)):
        lz.energy = v
        lz.keyframe_insert("energy", frame=f)
    # luz de borde cálida para Aiden
    ca = bpy.data.lights.new("calida_s8", "AREA")
    ca.energy = 4000.0
    ca.size = 3.0
    ca.color = (1.0, 0.6, 0.35)
    cao = bpy.data.objects.new("calida_s8", ca)
    col.objects.link(cao)
    cao.location = O + Vector((6, 8, 4))
    cao.rotation_euler = (O - cao.location).to_track_quat("-Z", "Y").to_euler()
    # ───── Aiden: mortal atrás → tornillo → flotando → cayendo, con el tiempo distorsionado
    arm = ctx.aiden
    AID.segmento(arm, "mortal_atras", f0, 4639, mapa=lambda f: TB(f) * 30.0)
    AID.segmento(arm, "tornillo", 4640, 4799, mapa=lambda f: (TB(f) - TB(4640)) * 30.0 + 40.0 * 0)
    AID.segmento(arm, "flotar", 4800, 4999, mapa=lambda f: (f - 4800) * 0.4, ciclo=True)
    AID.segmento(arm, "caida_loop", 5000, 5139, mapa=lambda f: (f - 5000) * 0.35, ciclo=True)
    raiz = bpy.data.objects["PJ_aiden"]
    raiz.rotation_mode = "XYZ"
    for f in range(f0, 5140, 6):
        u = (f - f0) / 640.0
        raiz.location = O + Vector((0, 0, -1.0 + 0.4 * math.sin(u * 9.0)))
        raiz.rotation_euler = (math.radians(10 * math.sin(u * 4.0)), 0, math.radians(30 + 400 * u))
        raiz.keyframe_insert("location", frame=f)
        raiz.keyframe_insert("rotation_euler", frame=f)
    raiz.location = O + Vector((0, 0, -600))
    raiz.keyframe_insert("location", frame=5140)
    cab = ctx.head
    cad = ctx.hips
    mano = AID.vacio(col, arm, "mixamorig:LeftHand", "AIDEN_mano_izq")
    pie = AID.vacio(col, arm, "mixamorig:RightFoot", "AIDEN_pie_der")
    # ───── cámaras del montaje (cada una en el vacío) y ecos de otras escenas
    cams = []

    def nueva(nombre, lente, seguir=None):
        c = Camara(nombre, col, lente)
        if seguir is not None:
            c.seguir(seguir)
        return c

    def orb(centro, rad, a0, a1, h0, h1, f0_, f1_):
        return lambda f: Vector(centro) + Vector((math.cos(math.radians(lerp(a0, a1, (f - f0_) / (f1_ - f0_)))) * rad, math.sin(math.radians(lerp(a0, a1, (f - f0_) / (f1_ - f0_)))) * rad, lerp(h0, h1, (f - f0_) / (f1_ - f0_))))

    plan = []
    c1 = nueva("cam_s8_1", 20.0, cad)
    c1.claves(f0, 4540, orb(O, 6.0, 0, 250, 1.0, 3.0, f0, 4540), None, fdof=lambda f: (6.0, 3.2))
    plan.append((f0, c1))
    c2 = nueva("cam_s8_2", 24.0, cad)
    c2.claves(4540, 4580, lambda f: O + Vector((lerp(-1.5, 1.0, (f - 4540) / 40.0), -2.4, -1.8)), None, fdof=lambda f: (3.0, 2.4))
    plan.append((4540, c2))
    # eco: salón de espejos (escena 4) con las losas flotando
    O4 = Vector(guion.desplazamiento(4))
    e1 = nueva("cam_s8_eco1", 24.0)
    e1.claves(4580, 4600, lambda f: O4 + Vector((lerp(-3.0, 3.0, (f - 4580) / 20.0), lerp(4.0, 12.0, (f - 4580) / 20.0), 1.5)), lambda f: O4 + Vector((0, 40, 3.0)), fdof=lambda f: (20.0, 4.0))
    plan.append((4580, e1))
    c3 = nueva("cam_s8_3", 70.0, mano)
    c3.claves(4600, 4630, lambda f: O + Vector((lerp(1.2, 0.8, (f - 4600) / 30.0), -1.3, 0.3)), None, fdof=lambda f: (1.5, 1.6))
    plan.append((4600, c3))
    # eco: hélice (escena 7) vista desde arriba
    O7 = Vector(guion.desplazamiento(7))
    e2 = nueva("cam_s8_eco2", 22.0)
    e2.claves(4630, 4650, lambda f: O7 + Vector((lerp(2.0, -2.0, (f - 4630) / 20.0), 0.5, 30.0)), lambda f: O7 + Vector((0, 0, 8.0)), fdof=lambda f: (22.0, 5.0))
    plan.append((4630, e2))
    c4 = nueva("cam_s8_4", 18.0, cad)
    c4.claves(4650, 4690, orb(O, 4.0, 90, -200, 0.2, 1.6, 4650, 4690), None, fdof=lambda f: (4.0, 2.4))
    plan.append((4650, c4))
    c5 = nueva("cam_s8_5", 22.0, pie)
    c5.claves(4690, 4730, lambda f: O + Vector((lerp(-3.0, 1.0, (f - 4690) / 40.0), lerp(-1.0, 1.5, (f - 4690) / 40.0), lerp(-1.2, 0.2, (f - 4690) / 40.0))), None, fdof=lambda f: (3.0, 2.0))
    plan.append((4690, c5))
    # eco: plataformas del cero g (escena 2)
    O2 = Vector(guion.desplazamiento(2))
    e3 = nueva("cam_s8_eco3", 20.0)
    e3.claves(4730, 4750, lambda f: O2 + Vector((lerp(-14.0, -6.0, (f - 4730) / 20.0), -12.0, lerp(1.0, 3.0, (f - 4730) / 20.0))), lambda f: O2 + Vector((0, 0, 4.0)), fdof=lambda f: (16.0, 4.0))
    plan.append((4730, e3))
    c6 = nueva("cam_s8_6", 40.0, cab)
    c6.claves(4750, 4790, lambda f: O + Vector((lerp(0.8, 0.5, (f - 4750) / 40.0), lerp(-1.1, -0.8, (f - 4750) / 40.0), 0.1)), None, fdof=lambda f: (1.1, 1.8))
    plan.append((4750, c6))
    c7 = nueva("cam_s8_7", 22.0, cad)
    c7.claves(4790, 4900, lambda f: O + Vector((lerp(2.0, 9.0, suave((f - 4790) / 110.0)), lerp(-3.0, -12.0, suave((f - 4790) / 110.0)), lerp(0.6, 2.5, suave((f - 4790) / 110.0)))), None, fdof=lambda f: (lerp(4.0, 14.0, suave((f - 4790) / 110.0)), 3.0))
    plan.append((4790, c7))
    # estallido: la cámara se aleja por entre los fragmentos
    c8 = nueva("cam_s8_8", 18.0)
    c8.claves(4900, 5140, lambda f: O + Vector((lerp(9.0, 40.0, suave((f - 4900) / 240.0)), lerp(-12.0, -60.0, suave((f - 4900) / 240.0)), lerp(2.5, 14.0, suave((f - 4900) / 240.0)))), lambda f: O + Vector((0, 0, 0)), fdof=lambda f: (lerp(15.0, 70.0, suave((f - 4900) / 240.0)), 5.0))
    plan.append((4900, c8))
    # ───── epílogo: el ojo de la escena 0 refleja los restos y se cierra
    O0 = Vector(guion.desplazamiento(0))
    ce = nueva("cam_s8_ojo", 55.0)
    ce.claves(5140, 5290, lambda f: O0 + Vector((0, lerp(-3.4, -5.2, suave((f - 5140) / 150.0)), 0.0)), lambda f: O0 + Vector((0, 0, 0)), fdof=lambda f: (lerp(2.4, 4.2, suave((f - 5140) / 150.0)), 3.0))
    plan.append((5140, ce))
    for nom, loc, s_ in (("refl_nuevo_a", (-3.0, -5.0, 2.2), 1.0), ("refl_nuevo_b", (3.4, -5.4, -1.2), 0.7), ("refl_nuevo_c", (0.5, -6.0, 3.2), 0.4)):
        em_ = mat_emisivo("refl_nuevo", (0.55, 0.85, 1.0), 10.0)
        e = esfera(nom, O0 + Vector(loc), s_, col, em_, 16, 10)
        e.visible_shadow = False
        e.scale = (0.001,) * 3
        e.keyframe_insert("scale", frame=5138)
        e.scale = (1.0, 1.0, 1.0)
        e.keyframe_insert("scale", frame=5140)
    for o in bpy.data.objects:
        if o.name.startswith("refl_fuego_"):        # los reflejos naranjas del principio se apagan para dar paso a los nuevos
            o.scale = o.scale
            o.keyframe_insert("scale", frame=5138)
            o.scale = (0.001,) * 3
            o.keyframe_insert("scale", frame=5140)
    sup = bpy.data.objects.get("lid_sup")
    inf = bpy.data.objects.get("lid_inf")
    if sup is not None and inf is not None:
        for lid, a0, a1 in ((sup, -38.0, 0.0), (inf, 14.0, 0.0)):
            lid.rotation_euler = (math.radians(a0), 0, 0)
            lid.keyframe_insert("rotation_euler", frame=5200)
            lid.rotation_euler = (math.radians(a1), 0, 0)
            lid.keyframe_insert("rotation_euler", frame=5285)
    # ───── partícula final
    pm = mat_emisivo("particula_s8", (0.75, 0.92, 1.0), 40.0)
    P = O + Vector((0, 0, 0))
    pa = esfera("particula_s8", P + Vector((0, 200, 0)), 0.05, col, pm, 16, 10)
    pa.visible_shadow = False
    cp = nueva("cam_s8_particula", 35.0)
    cp.claves(5290, f1, lambda f: O + Vector((0, 150, 0)) + Vector((0, 0, 0)), lambda f: O + Vector((0, 200, 0)), fdof=lambda f: (50.0, 8.0))
    plan.append((5290, cp))
    for f in range(5290, f1 + 1, 4):
        u = (f - 5290) / (f1 - 5290.0)
        s_ = 0.03 * (0.5 + 0.5 * math.sin(u * 20.0) ** 2) * (1.0 - suave((u - 0.78) / 0.22))
        pa.scale = (s_, s_, s_)
        pa.keyframe_insert("scale", frame=f)
    pa.scale = (0.0001,) * 3
    pa.keyframe_insert("scale", frame=5289)
    for f_, c_ in plan:
        v = ctx.dir.corte(f_, c_)
        if f_ == f0:
            v.rampa(f0, f0 + 16, 1.0, 0.0, (1.0, 1.0, 1.0), 10.0)
    vo = ctx.dir.velos["cam_s8_ojo"]
    vo.rampa(5140, 5156, 1.0, 0.0, (1.0, 1.0, 1.0), 8.0)
    vo.rampa(5270, 5289, 0.0, 1.0, (0, 0, 0), 0.0)
    vp = ctx.dir.velos["cam_s8_particula"]
    vp.clave(5290, 1.0, (0, 0, 0), 0.0)
    vp.clave(5320, 0.0, (0, 0, 0), 0.0)
    vp.clave(f1 - 1, 0.0, (0, 0, 0), 0.0)
    vp.clave(f1, 1.0, (0, 0, 0), 0.0)
    marco.pulso(ctx.comp["disp"], [(f0, 0.1), (f0 + 20, 0.012), (4638, 0.012), (4642, 0.1), (4660, 0.012), (4896, 0.012), (4908, 0.2), (4960, 0.012), (5136, 0.012), (5140, 0.1), (5160, 0.012)])
    marco.pulso(ctx.comp["dist"], [(4896, 0.0), (4908, -0.4), (4930, 0.0)])
    ctx.amb.append((f0 - 1, (0.004, 0.006, 0.014), 0.5))
    ctx.escena_activa(col, f0, f1)
