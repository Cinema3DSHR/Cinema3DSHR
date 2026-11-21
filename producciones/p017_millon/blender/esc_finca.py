"""s2–s7 «El impulsivo»: una finca (mansión moderna, pileta con reposeras, el McLaren F1 del dueño, sala con pantalla gigante, fiesta de noche) filmada con
cortes que acompañan cada compra. El tablero SALDO (USD) cuelga de cada cámara y baja con cada compra (cuentas.json: 1.000.000 → 750.000 → 350.000 → 290.000 → 270.000 → 0)."""
import math
import random
import sys
import bpy
from mathutils import Vector, Euler
import lib
from lib import *
import marco
import sh3d
import casa as CASA
import saldo as SAL
import personas as P
import guion

SALDOS = [1000000, 750000, 350000, 290000, 270000, 0]
ETIQ = ["−250.000", "−400.000", "−60.000", "−20.000", "−270.000"]


def mat_pantalla_viva(nombre):
    """Pantalla de TV encendida: bandas de color que se mueven (ruido 4D animado por el tiempo), brillo tipo película."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ru = nt.nodes.new("ShaderNodeTexNoise")
    ru.noise_dimensions = "4D"
    ru.inputs["Scale"].default_value = 2.5
    ru.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["UV"], ru.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    cr = rp.color_ramp
    cr.elements[0].position = 0.25
    cr.elements[0].color = (0.05, 0.15, 0.9, 1)
    e1 = cr.elements.new(0.5)
    e1.color = (0.9, 0.15, 0.6, 1)
    cr.elements[-1].position = 0.8
    cr.elements[-1].color = (1.0, 0.85, 0.2, 1)
    nt.links.new(ru.outputs["Fac"], rp.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.2
    nt.links.new(rp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m, ru.inputs["W"]


def agua(col, nombre, centro, ancho, largo, prof=0.0):
    """Superficie de agua de pileta: vidrio celeste con reflejo y ondas suaves (bump) animadas."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    gl = nt.nodes.new("ShaderNodeBsdfGlass")
    gl.inputs["Color"].default_value = (0.35, 0.8, 0.95, 1)
    gl.inputs["Roughness"].default_value = 0.02
    gl.inputs["IOR"].default_value = 1.33
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ru = nt.nodes.new("ShaderNodeTexNoise")
    ru.noise_dimensions = "4D"
    ru.inputs["Scale"].default_value = 3.0
    ru.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], ru.inputs["Vector"])
    bu = nt.nodes.new("ShaderNodeBump")
    bu.inputs["Strength"].default_value = 0.15
    nt.links.new(ru.outputs["Fac"], bu.inputs["Height"])
    nt.links.new(bu.outputs["Normal"], gl.inputs["Normal"])
    ab = nt.nodes.new("ShaderNodeBsdfDiffuse")
    ab.inputs["Color"].default_value = (0.1, 0.55, 0.75, 1)
    mz = nt.nodes.new("ShaderNodeMixShader")
    mz.inputs["Fac"].default_value = 0.55
    nt.links.new(gl.outputs[0], mz.inputs[1])
    nt.links.new(ab.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], out.inputs["Surface"])
    o = caja(nombre, centro, (ancho, largo, 0.02), col, m)
    for f in range(0, guion.TOTAL, 12):
        ru.inputs["W"].default_value = f / 40.0
        ru.inputs["W"].keyframe_insert("default_value", frame=f)
    lib._interp_id(m.node_tree, "LINEAR")
    return o


def hud(ctx, cam, col, f0, f1, f_compra):
    """Tablero SALDO colgado de la cámara: 'SALDO USD' + odómetro; baja cuando empieza cada compra (f_compra = {indice: cuadro}) y muestra la resta."""
    raiz = bpy.data.objects.new("hud_" + cam.o.name, None)
    col.objects.link(raiz)
    raiz.parent = cam.o
    raiz.location = (0, 0, -1.0)         # a 1 m delante de la cámara (ejes locales de la cámara: −Z adelante)
    raiz.rotation_euler = (math.radians(-90), 0, 0)      # los planos del HUD (en XZ, mirando −Y) pasan a mirar +Z → hacia la cámara
    # tarjeta oscura semitransparente
    tarjeta = mat("hud_tarjeta", (0.02, 0.03, 0.05), rug=0.5)
    od = SAL.Odometro(col, "hud_od_" + cam.o.name, 7, 0.042, 0.068, color=(0.55, 1.0, 0.75), fuerza=3.2)
    od.raiz.parent = raiz
    od.raiz.location = (0.0, 0.0, 0.0)
    et1 = SAL.etiqueta(col, "SALDO  USD", alto_m=0.04, color=(190, 200, 215, 255), fuerza=2.0, tam=90, pad=8)
    et1.parent = raiz
    et1.location = (0.0, 0.0, 0.06)
    # posición del HUD: parte alta del cuadro (cámara 9:16 con sensor vertical de 24 mm)
    raiz.location = (0, 0.27, -1.0)
    restas = []
    for k, ft in f_compra.items():
        e = SAL.etiqueta(col, ETIQ[k], alto_m=0.055, color=(255, 90, 90, 255), fuerza=3.0, tam=100, pad=8)
        e.parent = raiz
        e.location = (0.0, 0.0, -0.075)
        e.hide_render = True
        e.keyframe_insert("hide_render", frame=0)
        e.hide_render = False
        e.keyframe_insert("hide_render", frame=int(ft))
        e.hide_render = True
        e.keyframe_insert("hide_render", frame=int(ft) + 50)
        lib._interp(e, "CONSTANT")
        restas.append(e)
        od.contar(SALDOS[k], SALDOS[k + 1], int(ft) + 8, int(ft) + 34)
    od.poner(SALDOS[min(f_compra)] if f_compra else SALDOS[0], 0)
    od.fin()
    # visible sólo durante el tramo de la cámara
    for o in [raiz] + list(raiz.children_recursive):
        pass
    return raiz, od


def finca(ctx, O, col, rng):
    pasto = mat_ruido("pasto_finca", (0.05, 0.14, 0.03), (0.1, 0.25, 0.06), 12.0, rug=0.9, bump=0.5)
    caja("pasto", O + Vector((0, 15, -0.05)), (140, 120, 0.1), col, pasto)
    asfalto = mat("asfalto_acc", (0.07, 0.07, 0.08), rug=0.6)
    caja("acceso", O + Vector((-3.0, -18.0, 0.02)), (5.0, 40.0, 0.04), col, asfalto)
    caja("plaza", O + Vector((-3.0, -2.0, 0.02)), (10.0, 8.0, 0.04), col, mat("plaza_adoq", (0.4, 0.38, 0.34), rug=0.5))
    info = CASA.casa(col, O + Vector((6.0, 4.0, 0)), 16.0, 10.0, 3.4, estilo="moderna", rng=rng, color=(0.9, 0.88, 0.82), interior_luz=(1.0, 0.72, 0.4), techo_color=(0.05, 0.05, 0.06))
    # volumen superior flotando (look de mansión moderna)
    caja("piso_alto", O + Vector((6.0, 7.0, 4.3)), (12.0, 6.0, 1.0), col, mat("volumen_alto", (0.12, 0.12, 0.14), metal=0.5, rug=0.3))
    # pileta de Sweet Home con agua, reposeras y sombrillas, a la derecha de la mansión
    pos_p = O + Vector((24.0, 6.0, 0))
    sh3d.poner("swimming_pool", col, pos_p, frente=(0, -1))
    agua(col, "agua_pileta", pos_p + Vector((0, 0, 0.0)), 7.6, 2.9, 0.0)
    for k in range(4):
        sh3d.poner("bench_pool_lounge", col, pos_p + Vector((-3.0 + k * 2.0, -3.0, 0)), frente=(0, 1))      # miran hacia la pileta (+Y)
    for k in range(2):
        sh3d.poner("garden_umbrella", col, pos_p + Vector((-2.0 + k * 4.0, -3.4, 0)), frente=(0, -1))
    # árboles y cerco de plantas
    sh3d.preparar_arbol("tree_tree", semilla=5, copias=6)
    for k in range(10):
        sh3d.poner("tree_tree", col, O + Vector((rng.uniform(-14, 36), rng.uniform(16, 34), 0)), frente=(0, -1), escala=rng.uniform(1.0, 1.6))
    return info


def construir(ctx, i, f0, f1):
    # f0 = inicio de s2; esta escena cubre s2…s7 (hasta el fin de s7)
    f1 = guion.rango(7)[1]
    col = coleccion("S2_7_Finca")
    O = Vector(ctx.desp(2))
    rng = random.Random(21)
    ctx.amb.append((f0 - 1, (0.35, 0.45, 0.68), 1.2))
    fin = finca(ctx, O, col, rng)
    # ─── luz de la tarde (dorada) que se vuelve noche en la fiesta
    sol = bpy.data.lights.new("sol_finca", "SUN")
    sol.energy = 5.0
    sol.color = (1.0, 0.78, 0.55)
    sol.angle = math.radians(2.0)
    so = bpy.data.objects.new("sol_finca", sol)
    col.objects.link(so)
    so.rotation_euler = (math.radians(62), 0, math.radians(-30))
    f_noche = guion.rango(7)[0]
    for f, e in ((f0, 5.0), (guion.rango(6)[0] - 1, 5.0), (f_noche, 0.0), (f1, 0.0)):
        sol.energy = e
        sol.keyframe_insert("energy", frame=f)
    ctx.amb.append((f_noche - 1, (0.05, 0.07, 0.16), 0.9))
    ctx.sol_finca = sol
    # ─── el McLaren F1 del dueño (GLB original; ruedas izquierdas giradas; matrículas; apoyo de cada rueda medido) en la plaza, mirando hacia la calle (−Y)
    import coche as C
    car = C.cargar(col)
    raiz_c = car["raiz"]
    raiz_c.rotation_mode = "XYZ"
    CP = O + Vector((-3.0, -2.0, 0.0))
    raiz_c.location = (CP.x, CP.y, car["z_suelo"] + 0.04)      # la plaza de adoquines tiene su cara superior a 4 cm
    raiz_c.rotation_euler = (0, 0, math.radians(200))
    ctx.coche = car
    print("APOYO ruedas (z mundo del punto más bajo; suelo = 0.04):", {k: round(v + car["z_suelo"] + 0.04, 4) for k, v in car["fondo_ruedas"].items()}, flush=True)
    # ─── sala con pantalla gigante (recinto aparte)
    S = O + Vector((80.0, 0, 0))
    sala(ctx, col, S, rng)
    # ─── personas: impulsivo = Kate; invitados = clones
    ka = ctx.kate
    ai = ctx.aiden
    # ─── cámaras y tablero
    cams = []

    def cam(nombre, f_a, f_b, fpos, ftgt, lente=28.0, dof=None, paso=1, hud_k=None):
        c = Camara(nombre, col, lente)
        c.claves(f_a, f_b, fpos, ftgt, flente=(lente if callable(lente) else None) if False else None, fdof=dof, paso=paso)
        cams.append((f_a, c))
        return c

    inicio = {k: guion.f(v) for k, v in guion.INICIO_S.items()}
    cm = lambda x, y, z: CP + Vector((x, y, z))
    # s2 montaje (cortes de ~1 s): auto, mansión, pileta, baile, auto, casa
    a2, b2 = guion.rango(2)
    tramos = [(a2, a2 + 40), (a2 + 40, a2 + 80), (a2 + 80, a2 + 125), (a2 + 125, a2 + 165), (a2 + 165, a2 + 210), (a2 + 210, b2)]
    cam("cam_f_m1", *tramos[0], lambda f: cm(lerp(2.5, -0.5, (f - tramos[0][0]) / 40.0), 2.2, 0.55), lambda f: cm(0, 0, 0.5), lente=26.0, dof=lambda f: (3.3, 3.0))
    cam("cam_f_m2", *tramos[1], lambda f: O + Vector((lerp(-6, 6, (f - tramos[1][0]) / 40.0), -16.0, 2.0)), lambda f: O + Vector((6.0, 4.0, 2.2)), lente=22.0, dof=lambda f: (18.0, 5.6))
    cam("cam_f_m3", *tramos[2], lambda f: O + Vector((22.0 + lerp(-2, 2, (f - tramos[2][0]) / 45.0), -2.5, 1.8)), lambda f: O + Vector((24.0, 6.0, 0.9)), lente=26.0, dof=lambda f: (9.0, 5.6))
    cam("cam_f_m4", *tramos[3], lambda f: O + Vector((17.0, lerp(-2, 1, (f - tramos[3][0]) / 40.0), 1.3)), lambda f: O + Vector((24.0, 4.8, 1.0)), lente=30.0, dof=lambda f: (7.0, 3.5))
    cam("cam_f_m5", *tramos[4], lambda f: cm(lerp(-3.0, 1.0, (f - tramos[4][0]) / 45.0), -4.0, 0.7), lambda f: cm(0, 0, 0.45), lente=24.0, dof=lambda f: (4.2, 3.0))
    cam("cam_f_m6", *tramos[5], lambda f: O + Vector((lerp(-2.0, 10.0, (f - tramos[5][0]) / (b2 - tramos[5][0])), -13.0, lerp(1.2, 3.5, (f - tramos[5][0]) / (b2 - tramos[5][0])))), lambda f: O + Vector((6.0, 4.0, 2.0)), lente=24.0, dof=lambda f: (14.0, 5.6))
    # s3 superdeportivo: órbita baja alrededor del auto
    a3, b3 = guion.rango(3)
    c3 = cam("cam_f_auto", a3, b3, lambda f: CP + Vector((math.sin(math.radians(lerp(-70, 60, (f - a3) / (b3 - a3)))) * 6.2, -math.cos(math.radians(lerp(-70, 60, (f - a3) / (b3 - a3)))) * 6.2 - 0.0, lerp(0.7, 1.3, (f - a3) / (b3 - a3)))), lambda f: CP + Vector((0, 0, 0.5)), lente=28.0, dof=lambda f: (6.2, 3.5))
    # s4 casa: grúa desde el auto hacia la fachada
    a4, b4 = guion.rango(4)
    c4 = cam("cam_f_casa", a4, b4, lambda f: O + Vector((lerp(-2.0, 8.0, (f - a4) / (b4 - a4)), lerp(-14.0, -17.0, (f - a4) / (b4 - a4)), lerp(1.2, 6.5, suave((f - a4) / (b4 - a4))))), lambda f: O + Vector((6.0, 4.0, lerp(1.5, 3.0, (f - a4) / (b4 - a4)))), lente=24.0, dof=lambda f: (17.0, 5.6))
    # s5 piscina
    a5, b5 = guion.rango(5)
    pp = O + Vector((24.0, 6.0, 0))
    c5 = cam("cam_f_pileta", a5, b5, lambda f: pp + Vector((lerp(-5.0, 4.5, (f - a5) / (b5 - a5)), -8.5, lerp(1.8, 2.4, (f - a5) / (b5 - a5)))), lambda f: pp + Vector((0, 0.5, 0.8)), lente=30.0, dof=lambda f: (9.0, 5.6))
    # s6 pantalla gigante (sala)
    a6, b6 = guion.rango(6)
    c6 = cam("cam_f_tv", a6, b6, lambda f: S + Vector((lerp(-1.5, 1.2, (f - a6) / (b6 - a6)), 0.5, 2.1)), lambda f: S + Vector((0, 6.4, 1.2)), lente=24.0, dof=lambda f: (6.2, 5.6))
    # s7 fiesta (noche en la pileta)
    a7, b7 = guion.rango(7)
    c7 = cam("cam_f_fiesta", a7, b7, lambda f: pp + Vector((lerp(-6.0, 6.0, suave((f - a7) / (b7 - a7))), -12.5, lerp(1.7, 2.8, (f - a7) / (b7 - a7)))), lambda f: pp + Vector((0, -5.0, 1.0)), lente=30.0, dof=lambda f: (8.0, 5.6))
    # ─── personas (Kate protagonista de las compras; en la fiesta Kate, Aiden y clones). Todas mirando hacia donde caminan o hacia lo que miran.
    def v2(p, q):
        return (q.x - p.x, q.y - p.y)
    # s3: Kate junto al auto celebrando
    pk3 = CP + Vector((3.0, -1.4, 0.04))
    P.colocar(ka, [(a3 - 1, (0, 0, -800), 0), (a3, pk3, ka.mirar(*v2(pk3, CP))), (b3 - 2, pk3, ka.mirar(*v2(pk3, CP)))])
    P.clip(ka, "senalar", a3, a3 + 40)
    P.clip(ka, "victoria", a3 + 41, b3 - 1)
    # s4: Kate camina feliz hacia la puerta de la casa (la mirada sigue la dirección de marcha)
    p_ini = O + Vector((1.6, -5.0, 0.0))
    p_fin = O + Vector((5.4, -1.6, 0.0))
    d4 = v2(p_ini, p_fin)
    P.colocar(ka, [(a4 - 1, (0, 0, -800), 0), (a4, p_ini, ka.mirar(*d4)), (b4 - 2, p_fin, ka.mirar(*d4))])
    P.clip(ka, "caminar_feliz", a4, b4 - 1, ciclo=True)
    # s5: Kate festeja a la orilla de la pileta, mirando al agua
    pk5 = pp + Vector((-1.0, -2.0, 0.0))
    P.colocar(ka, [(a5 - 1, (0, 0, -800), 0), (a5, pk5, ka.mirar(0, 1)), (b5 - 2, pk5, ka.mirar(0, 1))])
    P.clip(ka, "festejar", a5, b5 - 1, ciclo=True)
    # s6: Kate disfruta frente a la pantalla gigante (de espaldas a la cámara, mirando la tele)
    pk6 = S + Vector((-0.5, 3.4, 0.0))
    P.colocar(ka, [(a6 - 1, (0, 0, -800), 0), (a6, pk6, ka.mirar(0, 1)), (b6 - 2, pk6, ka.mirar(0, 1))])
    P.clip(ka, "feliz", a6, b6 - 1, ciclo=True)
    # (Kate se retira de escena entre tramos con claves lejanas; las posiciones se mantienen hasta justo antes del tramo siguiente)
    # s7: fiesta junto a la pileta: Kate, Aiden y cuatro clones bailan mirando hacia el lado de la cámara (−Y)
    baile = [(ka, "samba", -2.6), (ai, "hiphop", -0.9), (P.clonar(ka, "inv1", col), "festejar", 0.9), (P.clonar(ai, "inv2", col), "samba", 2.6),
             (P.clonar(ka, "inv3", col), "hiphop", 4.0), (P.clonar(ai, "inv4", col), "festejar", -4.2)]
    for k_, (p_, clip_, dx_) in enumerate(baile):
        pos7 = pp + Vector((dx_, -5.6 - 0.35 * (k_ % 2), 0.0))
        P.colocar(p_, [(a7 - 1, (0, 0, -800), 0), (a7, pos7, p_.mirar(0, -1)), (b7 - 2, pos7, p_.mirar(0, -1)), (b7 - 1, (0, 0, -800), 0)])
        P.clip(p_, clip_, a7, b7 - 1, ciclo=True)
    # s7 · luces de fiesta nocturna (apagadas hasta la noche): luna fría, reflectores de colores y luz bajo el agua
    def luz_noche(nombre, tipo, pos, color, energia, rot=None):
        ld = bpy.data.lights.new(nombre, tipo)
        ld.color = color
        if tipo == "SUN":
            ld.angle = math.radians(3)
        else:
            ld.shadow_soft_size = 0.6
        lo = bpy.data.objects.new(nombre, ld)
        col.objects.link(lo)
        lo.location = pos
        if rot:
            lo.rotation_euler = rot
        for f_, e_ in ((0, 0.0), (a7 - 1, 0.0), (a7, energia), (b7, energia)):
            ld.energy = e_
            ld.keyframe_insert("energy", frame=f_)
    luz_noche("luna_f", "SUN", O + Vector((0, 0, 30)), (0.55, 0.65, 1.0), 1.6, (math.radians(50), 0, math.radians(20)))
    luz_noche("fiesta_mag", "POINT", pp + Vector((-5.0, -4.0, 3.0)), (1.0, 0.2, 0.8), 3500.0)
    luz_noche("fiesta_cian", "POINT", pp + Vector((5.0, -4.0, 3.0)), (0.2, 0.8, 1.0), 3500.0)
    luz_noche("fiesta_calida", "POINT", pp + Vector((0.0, -7.0, 3.5)), (1.0, 0.75, 0.45), 4500.0)
    luz_noche("pileta_luz", "POINT", pp + Vector((0.0, 0.0, 0.6)), (0.3, 0.9, 1.0), 900.0)
    for f_, c_ in cams:
        ctx.dir.corte(f_, c_)
    # tablero SALDO en las cinco compras y el cero (cámaras s3–s7)
    compras = {0: inicio["b05_auto"], 1: inicio["b06_casa"], 2: inicio["b07_piscina"], 3: inicio["b08_tele"], 4: inicio["b09_resto"]}
    for nombre_cam, fa, fb in (("cam_f_auto", a3, b3), ("cam_f_casa", a4, b4), ("cam_f_pileta", a5, b5), ("cam_f_tv", a6, b6), ("cam_f_fiesta", a7, b7)):
        cc = next(c for f_, c in cams if c.o.name == nombre_cam)
        k = [kk for kk, ft in compras.items() if fa <= ft < fb]
        fc = {kk: compras[kk] for kk in k}
        hud(ctx, cc, col, fa, fb, fc)
    ctx.escena_activa(col, f0, f1)
    return col


def sala(ctx, col, S, rng):
    """Sala de lujo: pantalla gigante en la pared del fondo, sofás de Sweet Home enfrentados a ella, alfombra, plantas y luces cálidas."""
    pared = mat("pared_sala", (0.18, 0.17, 0.2), rug=0.5)
    piso = mat_ruido("piso_sala", (0.25, 0.16, 0.1), (0.38, 0.25, 0.16), 4.0, rug=0.2, bump=0.1)
    caja("piso_s", S + Vector((0, 3.5, -0.05)), (9.0, 8.0, 0.1), col, piso)
    caja("techo_s", S + Vector((0, 3.5, 3.05)), (9.0, 8.0, 0.1), col, pared)
    caja("pared_f", S + Vector((0, 7.55, 1.5)), (9.0, 0.1, 3.0), col, pared)
    caja("pared_i", S + Vector((-4.55, 3.5, 1.5)), (0.1, 8.0, 3.0), col, pared)
    caja("pared_d", S + Vector((4.55, 3.5, 1.5)), (0.1, 8.0, 3.0), col, pared)
    caja("pared_a", S + Vector((0, -0.55, 1.5)), (9.0, 0.1, 3.0), col, pared)
    # televisor gigante (marco + pantalla viva)
    m_tv, w_sock = mat_pantalla_viva("pantalla_tv")
    marco_tv = mat("marco_tv", (0.01, 0.01, 0.012), metal=0.6, rug=0.3)
    caja("marco_tv", S + Vector((0, 7.4, 1.55)), (4.4, 0.08, 2.5), col, marco_tv)
    o_tv = caja("pantalla_tv", S + Vector((0, 7.35, 1.55)), (4.2, 0.02, 2.3), col, m_tv)
    for f in range(0, guion.TOTAL, 6):
        w_sock.default_value = f / 25.0
        w_sock.keyframe_insert("default_value", frame=f)
    lib._interp_id(m_tv.node_tree, "LINEAR")
    # sofás mirando a la pantalla (el frente del sofá apunta hacia +Y), sillones laterales, mesa ratona
    sh3d.poner("sofa_corner_sofa_3", col, S + Vector((0, 2.2, 0)), frente=(0, 1))
    sh3d.poner("armchair_armchair_9", col, S + Vector((-3.0, 4.2, 0)), frente=(1, 0.3))
    sh3d.poner("armchair_armchair_10", col, S + Vector((3.0, 4.2, 0)), frente=(-1, 0.3))
    sh3d.poner("table_marble_table", col, S + Vector((0, 4.3, 0)), frente=(0, 1))
    sh3d.poner("grand_piano", col, S + Vector((-3.4, 6.2, 0)), frente=(1, 0))
    sh3d.poner("bush_indoor_plant", col, S + Vector((3.8, 6.8, 0)), frente=(0, 1), escala=1.6)
    alfombra = mat("alfombra_sala", (0.45, 0.1, 0.12), rug=0.95)
    caja("alfombra", S + Vector((0, 3.8, 0.01)), (5.2, 4.2, 0.02), col, alfombra)
    # luces cálidas de techo (paneles) + resplandor de la tele
    lm = mat_emisivo("luz_sala", (1.0, 0.72, 0.4), 3.0)
    for k in range(3):
        caja("panel_s", S + Vector((-2.5 + 2.5 * k, 3.5, 3.0)), (0.7, 6.0, 0.04), col, lm)
    rl = bpy.data.lights.new("luz_tv", "AREA")
    rl.energy = 600.0
    rl.size = 3.0
    rl.color = (0.7, 0.55, 1.0)
    ro = bpy.data.objects.new("luz_tv", rl)
    col.objects.link(ro)
    ro.location = S + Vector((0, 6.5, 1.8))
    ro.rotation_euler = (math.radians(90), 0, 0)
