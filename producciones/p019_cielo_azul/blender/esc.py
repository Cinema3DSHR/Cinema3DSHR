"""p019 · todas las escenas: pradera con cielo físico, prisma, moléculas, ondas, barras (violeta vs azul), atardecer, espacio y cierre."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import comun as K
import saldo as SAL
import sh3d
import cielo
import guion


def construir(ctx, i, f0, f1):
    [s0, s1, s2, s3, s4, s5, s6, s7, s8][i](ctx, i, f0, f1)


def sky_ctx(ctx, f0, **kw):
    cielo.poner(ctx.cielo, f0 - 1 if f0 > 0 else 0, **kw) if False else cielo.poner(ctx.cielo, f0, **kw)


def paisaje(col, O, semilla, arboles=16, hierba=(0.06, 0.2, 0.04)):
    rng = random.Random(semilla)
    pasto = mat_ruido("pasto_" + col.name, tuple(c * 0.6 for c in hierba), hierba, 16.0, rug=0.9, bump=0.5)
    caja("suelo", O + Vector((0, 60, -0.05)), (400, 400, 0.1), col, pasto)
    sh3d.preparar_arbol("tree_tree", semilla=semilla, copias=6)
    for k in range(arboles):
        a = rng.uniform(-1.1, 1.1)
        r = rng.uniform(14, 70)
        pos = O + Vector((math.sin(a) * r * 1.4, math.cos(a) * r + 6.0, 0.0))
        sh3d.poner("tree_tree", col, pos, frente=(0, -1), escala=rng.uniform(1.1, 2.2))
    # colinas lejanas
    colina = mat_ruido("colina_" + col.name, (0.04, 0.12, 0.05), (0.07, 0.2, 0.07), 6.0, rug=0.95, bump=0.2)
    for k in range(7):
        x = -120 + k * 40 + rng.uniform(-10, 10)
        e = esfera(f"colina_{k}", O + Vector((x, 190 + rng.uniform(0, 40), -10)), rng.uniform(26, 44), col, colina, 24, 14, esc=(1.6, 1.0, 0.45))
        e.visible_shadow = False


def cam_fija(ctx, col, nombre, f0, f1, fpos, ftgt, lente=28.0):
    c = Camara(nombre, col, lente)
    c.data.clip_end = 900.0
    c.claves(f0, f1 - 1, fpos, ftgt, paso=1)
    ctx.dir.corte(f0, c, velo=False)
    return c


def s0(ctx, i, f0, f1):
    col = coleccion("S0_Pradera")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    cielo.poner(ctx.cielo, f0, False, 38.0, 200.0)
    paisaje(col, O, 3)
    cam_fija(ctx, col, "cam_s0", f0, f1, lambda f: O + Vector((0, -6.0, lerp(0.8, 1.6, (f - f0) / n))),
             lambda f: O + Vector((0, 40.0, lerp(1.0, 34.0, suave((f - f0) / n)))))
    ctx.escena_activa(col, f0, f1)


def mat_vidrio_prisma():
    m = bpy.data.materials.new("vidrio_prisma")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.7, 0.85, 1.0, 1)
    em.inputs["Strength"].default_value = 0.9
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    L = nt.links.new
    L(lw.outputs["Fresnel"], mz.inputs["Fac"])
    L(tr.outputs[0], mz.inputs[1])
    L(em.outputs[0], mz.inputs[2])
    L(mz.outputs[0], out.inputs["Surface"])
    return m


def fondo_oscuro(col, O, y=14.0, tam=120.0):
    m = mat_emisivo("fondo_oscuro", (0.008, 0.012, 0.03), 1.0)
    p = plano("fondo_oscuro", O + Vector((0, y, 0)), tam, tam, col, m, rot=(math.radians(90), 0, 0))
    p.visible_shadow = False
    return p


COL_ARCO = [(1.0, 0.05, 0.05), (1.0, 0.45, 0.05), (1.0, 0.9, 0.1), (0.1, 0.9, 0.2), (0.1, 0.5, 1.0), (0.2, 0.2, 0.9), (0.55, 0.1, 0.9)]


def s1(ctx, i, f0, f1):
    col = coleccion("S1_Prisma")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    cielo.poner(ctx.cielo, f0, True)
    fondo_oscuro(col, O, 10.0)
    # prisma triangular (sección en el plano XZ, extruido a lo largo de Y)
    h = 3.0
    pts = [(-1.7, 0, -1.4), (1.7, 0, -1.4), (0, 0, 1.6)]
    verts = [(x, -0.8, z) for x, _, z in pts] + [(x, 0.8, z) for x, _, z in pts]
    caras = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    prisma = malla("prisma", verts, caras, col, mat_vidrio_prisma(), suave=False)
    prisma.location = O
    prisma.visible_shadow = False
    # rayo blanco entra por la cara izquierda; salen 7 colores en abanico por la derecha
    blanco = mat_emisivo("rayo_blanco", (1.0, 1.0, 1.0), 9.0)
    entrada = Vector((-0.55, 0, 0.3))
    r0 = K.cilindro_entre("rayo_in", O + Vector((-7.0, 0, 3.2)), O + entrada, 0.07, col, blanco)
    r1 = K.cilindro_entre("rayo_dentro", O + entrada, O + Vector((0.55, 0, -0.05)), 0.06, col, blanco)
    K.aparecer(r0, f0 + 6, f0 + 20)
    K.aparecer(r1, f0 + 22, f0 + 30)
    for k, cc in enumerate(COL_ARCO):
        ang = math.radians(-3 - k * 3.2)
        fin = O + Vector((0.55, 0, -0.05)) + Vector((math.cos(ang), 0, math.sin(ang))) * 8.0
        e = K.cilindro_entre(f"rayo_c{k}", O + Vector((0.55, 0, -0.05)), fin, 0.07, col, mat_emisivo(f"rc{k}", cc, 8.0))
        K.aparecer(e, f0 + 34 + 4 * k, f0 + 42 + 4 * k)
    sol = K.sol_dummy if False else None
    cam_fija(ctx, col, "cam_s1", f0, f1, lambda f: O + Vector((lerp(-1.0, 1.0, (f - f0) / n), -13.0, lerp(0.6, -0.4, (f - f0) / n))),
             lambda f: O + Vector((1.2, 0, -0.6)), lente=26.0)
    ctx.escena_activa(col, f0, f1)


def s2(ctx, i, f0, f1):
    col = coleccion("S2_Moleculas")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    cielo.poner(ctx.cielo, f0, True)
    fondo_oscuro(col, O, 10.0)
    rng = random.Random(8)
    columna = mat("aire_col", (0.3, 0.55, 1.0), rug=0.2, emis=(0.2, 0.45, 1.0), fuerza=0.35, alfa=0.1)
    caja("columna_aire", O, (7.4, 0.5, 14.0), col, columna).visible_shadow = False
    mm = mat("molecula", (0.7, 0.8, 0.95), rug=0.3, emis=(0.5, 0.6, 1.0), fuerza=0.25)
    base = esfera("mol_base", (0, 0, -9999), 0.13, col, mm, 10, 8)
    base.hide_render = True
    blanco = mat_emisivo("rayo_b2", (1.0, 1.0, 1.0), 4.0)
    azul = mat_emisivo("disp_azul", (0.1, 0.35, 1.0), 3.0)
    # recta del rayo de sol (de arriba-izquierda a abajo-derecha)
    A, B = Vector((-5.0, 0, 6.8)), Vector((5.0, 0, -6.8))
    ray = K.cilindro_entre("rayo_sol", O + A, O + B, 0.09, col, blanco)
    K.aparecer(ray, f0 + 8, f0 + 40)
    ddir = (B - A).normalized()
    for k in range(140):
        p = Vector((rng.uniform(-3.5, 3.5), rng.uniform(-0.2, 0.2), rng.uniform(-6.8, 6.8)))
        mo = K.duplicar(base, f"mol_{k}", col, O + p)
        # molécula sobre el rayo → dispersa luz azul en todas direcciones
    # moléculas que sí chocan con el rayo: estallidos azules escalonados
    for k in range(18):
        u = 0.1 + 0.8 * k / 17.0
        p = A + (B - A) * u
        mo = K.duplicar(base, f"mol_hit_{k}", col, O + p + Vector((0, 0.1, 0)), 1.3)
        t0 = f0 + 30 + int(k * (n - 70) / 18.0)
        for j in range(7):
            a = rng.uniform(0, 2 * math.pi)
            d = Vector((math.cos(a), rng.uniform(-0.15, 0.15), math.sin(a))) * rng.uniform(1.6, 3.2)
            e = K.cilindro_entre(f"disp_{k}_{j}", O + p, O + p + d, 0.04, col, azul)
            K.aparecer(e, t0 + j, t0 + j + 6)
            K.desaparecer(e, t0 + j + 40, t0 + j + 50)
    cam_fija(ctx, col, "cam_s2", f0, f1, lambda f: O + Vector((lerp(-1.0, 1.0, (f - f0) / n), -15.5, lerp(0.8, -0.8, (f - f0) / n))),
             lambda f: O + Vector((0, 0, 0)), lente=28.0)
    ctx.escena_activa(col, f0, f1)


def s3(ctx, i, f0, f1):
    col = coleccion("S3_Ondas")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    cielo.poner(ctx.cielo, f0, True)
    fondo_oscuro(col, O, 10.0)
    mm = mat("molecula3", (0.7, 0.8, 0.95), rug=0.3, emis=(0.5, 0.6, 1.0), fuerza=0.35)
    azul = mat_emisivo("perla_azul", (0.1, 0.35, 1.0), 4.0)
    rojo = mat_emisivo("perla_roja", (1.0, 0.1, 0.05), 4.0)
    NB = 90
    f_hit = f0 + 70
    for nombre, z0, lam, mat_, es_azul in (("az", 3.1, 0.75, azul, True), ("ro", -3.1, 1.9, rojo, False)):
        mol = esfera("mol3_" + nombre, O + Vector((0.5, 0, z0)), 0.45, col, mm, 20, 14)
        base = esfera("perla_base_" + nombre, (0, 0, -9999), 0.06, col, mat_, 8, 6)
        base.hide_render = True
        perlas = []
        for k in range(NB):
            x = -6.5 + k * (6.5 / NB * 1.0)
            o = K.duplicar(base, f"perla_{nombre}_{k}", col, O + Vector((x, 0, z0)))
            perlas.append((o, x))
        for f in range(f0, f1, 2):
            t = (f - f0) / 30.0
            for o, x in perlas:
                z = z0 + 0.55 * math.sin(2 * math.pi * (x / lam - 0.9 * t))
                o.location = O + Vector((x, 0, z))
                o.keyframe_insert("location", frame=f)
        # la onda azul se «apaga» al chocar (se dispersa); la roja sigue de largo
        if es_azul:
            for o, x in perlas:
                if x > -0.3:
                    K.desaparecer(o, f_hit, f_hit + 6)
        else:
            for k in range(NB):
                pass
    # la onda roja continúa hacia la derecha tras la molécula
    base = esfera("perla_base_ro2", (0, 0, -9999), 0.06, col, rojo, 8, 6)
    base.hide_render = True
    for k in range(60):
        x = 0.9 + k * 0.09
        o = K.duplicar(base, f"perla_ro_post_{k}", col, O + Vector((x, 0, -3.1)))
        for f in range(f0, f1, 2):
            t = (f - f0) / 30.0
            o.location = O + Vector((x, 0, -3.1 + 0.45 * math.sin(2 * math.pi * (x / 1.9 - 0.9 * t))))
            o.keyframe_insert("location", frame=f)
        K.aparecer(o, f_hit + 10 + k // 4, f_hit + 14 + k // 4)
    # estallido azul de dispersión (muchos destellos que salen en todas direcciones)
    rng = random.Random(5)
    sc = esfera("chispa_base", (0, 0, -9999), 0.07, col, azul, 8, 6)
    sc.hide_render = True
    for k in range(60):
        a = rng.uniform(0, 2 * math.pi)
        v = rng.uniform(0.04, 0.12)
        o = K.duplicar(sc, f"chispa_{k}", col, O + Vector((0.5, 0, 3.1)))
        o.scale = (0.0001, 0.0001, 0.0001)
        o.keyframe_insert("scale", frame=f_hit)
        o.location = O + Vector((0.5, 0, 3.1))
        o.keyframe_insert("location", frame=f_hit)
        o.scale = (1, 1, 1)
        o.keyframe_insert("scale", frame=f_hit + 3)
        o.location = O + Vector((0.5 + math.cos(a) * v * 70, rng.uniform(-0.3, 0.3), 3.1 + math.sin(a) * v * 70))
        o.keyframe_insert("location", frame=f_hit + 70)
        o.scale = (0.0001, 0.0001, 0.0001)
        o.keyframe_insert("scale", frame=f_hit + 70)
        lib._interp(o, "LINEAR")
    et1 = SAL.etiqueta(col, "AZUL · ONDA CORTA", alto_m=0.42, color=(120, 175, 255, 255), fuerza=3.0)
    et1.location = O + Vector((-2.4, -1.0, 4.6))
    et2 = SAL.etiqueta(col, "ROJO · ONDA LARGA", alto_m=0.42, color=(255, 120, 110, 255), fuerza=3.0)
    et2.location = O + Vector((-2.4, -1.0, -1.6))
    K.aparecer(et1, f0 + 10, f0 + 22)
    K.aparecer(et2, f0 + 24, f0 + 36)
    cam_fija(ctx, col, "cam_s3", f0, f1, lambda f: O + Vector((lerp(-0.4, 0.4, (f - f0) / n), -17.0, 0.0)), lambda f: O + Vector((-0.5, 0, 0.3)), lente=26.0)
    ctx.escena_activa(col, f0, f1)


def s4(ctx, i, f0, f1):
    col = coleccion("S4_Panorama")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    cielo.poner(ctx.cielo, f0, False, 45.0, 200.0)
    paisaje(col, O, 6, arboles=20)
    # giro de 150° de la cámara con la mirada en el cielo: azul en todas las direcciones (movimiento continuo)
    cam_fija(ctx, col, "cam_s4", f0, f1, lambda f: O + Vector((0, -2.0, 1.6)),
             lambda f: O + Vector((60 * math.sin(math.radians(lerp(-55, 55, suave((f - f0) / n)))), 60 * math.cos(math.radians(lerp(-55, 55, suave((f - f0) / n)))) - 2.0, 42.0)), lente=24.0)
    ctx.escena_activa(col, f0, f1)


def s5(ctx, i, f0, f1):
    col = coleccion("S5_Violeta")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    cielo.poner(ctx.cielo, f0, True)
    fondo_oscuro(col, O, 10.0)
    violeta = (0.55, 0.2, 1.0)
    azul = (0.2, 0.5, 1.0)
    filas = [("SE DISPERSA", 1.0, 0.72, 6.0), ("LUZ DEL SOL", 0.5, 0.92, 2.0), ("LO VEN LOS OJOS", 0.3, 0.8, -2.0), ("RESULTADO", None, None, -6.0)]
    cv, ca = None, None
    prod_v, prod_a = 1.0, 1.0
    for nombre, v, a, z in filas:
        if v is None:
            v, a = prod_v, prod_a
        else:
            prod_v *= v
            prod_a *= a
        et = SAL.etiqueta(col, nombre, alto_m=0.45, color=(235, 240, 255, 255), fuerza=3.0)
        et.location = O + Vector((-3.0, -1.0, z + 1.45))
        et.rotation_euler = (0, 0, 0)
        t0 = f0 + 10 + int((z < 5) * 0)
        for k, (val, cc, dz) in enumerate(((v, violeta, 0.45), (a, azul, -0.45))):
            largo = 5.6 * val
            b = caja(f"barra_{nombre}_{k}", O + Vector((-3.4 + largo / 2, 0, z + dz)), (largo, 0.3, 0.7), col, mat_emisivo(f"bar_{nombre}_{k}", cc, 1.6))
            # crece de izquierda a derecha
            b.scale = (0.0001, 1, 1)
            ft = f0 + 12 + int(((6.0 - z) / 12.0) * (n - 70)) + 6 * k
            b.location = O + Vector((-3.4, 0, z + dz))
            b.keyframe_insert("location", frame=max(0, ft - 1))
            b.keyframe_insert("scale", frame=max(0, ft - 1))
            b.scale = (1, 1, 1)
            b.location = O + Vector((-3.4 + largo / 2, 0, z + dz))
            b.keyframe_insert("location", frame=ft + 30)
            b.keyframe_insert("scale", frame=ft + 30)
        K.aparecer(et, f0 + 6 + int(((6.0 - z) / 12.0) * (n - 70)), f0 + 16 + int(((6.0 - z) / 12.0) * (n - 70)))
    lv = SAL.etiqueta(col, "VIOLETA", alto_m=0.4, color=(185, 140, 255, 255), fuerza=3.0)
    lv.location = O + Vector((-1.9, -1.0, 8.0))
    la = SAL.etiqueta(col, "AZUL", alto_m=0.4, color=(120, 175, 255, 255), fuerza=3.0)
    la.location = O + Vector((1.2, -1.0, 8.0))
    il = SAL.etiqueta(col, "ILUSTRATIVO, SIN ESCALA", alto_m=0.28, color=(170, 180, 200, 255), fuerza=2.4)
    il.location = O + Vector((0, -1.0, -8.2))
    cam_fija(ctx, col, "cam_s5", f0, f1, lambda f: O + Vector((0, -19.0, lerp(0.4, -0.4, (f - f0) / n))), lambda f: O, lente=26.0)
    ctx.escena_activa(col, f0, f1)


def s6(ctx, i, f0, f1):
    col = coleccion("S6_Atardecer")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    paisaje(col, O, 12, arboles=14)
    # el Sol baja de 38° a 1° de forma continua: el cielo pasa de azul a naranja y rojo
    for f in range(f0, f1 + 1, 6):
        u = (f - f0) / float(n)
        cielo.poner(ctx.cielo, f, False, lerp(38.0, 0.8, suave(u)), 0.0)
    cam_fija(ctx, col, "cam_s6", f0, f1, lambda f: O + Vector((lerp(-0.8, 0.8, (f - f0) / n), -4.0, 1.5)),
             lambda f: O + Vector((0, 60.0, lerp(14.0, 5.0, suave((f - f0) / n)))), lente=26.0)
    ctx.escena_activa(col, f0, f1)


def mat_tierra():
    m = bpy.data.materials.new("tierra")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 0.55
    ns.inputs["Detail"].default_value = 8.0
    ns.inputs["Roughness"].default_value = 0.6
    tierra = nt.nodes.new("ShaderNodeValToRGB")
    tierra.color_ramp.elements[0].position = 0.5
    tierra.color_ramp.elements[1].position = 0.55
    tierra.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
    tierra.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    nube = nt.nodes.new("ShaderNodeTexNoise")
    nube.inputs["Scale"].default_value = 0.7
    nube.inputs["Detail"].default_value = 7.0
    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    cr2.color_ramp.elements[0].position = 0.52
    cr2.color_ramp.elements[1].position = 0.7
    cr2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
    cr2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    oceano = nt.nodes.new("ShaderNodeMix")
    oceano.data_type = "RGBA"
    oceano.inputs[6].default_value = (0.01, 0.07, 0.35, 1)
    oceano.inputs[7].default_value = (0.12, 0.3, 0.08, 1)
    nubes = nt.nodes.new("ShaderNodeMix")
    nubes.data_type = "RGBA"
    nubes.inputs[7].default_value = (0.95, 0.97, 1.0, 1)
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
    pr.inputs["Roughness"].default_value = 0.6
    L = nt.links.new
    L(tc.outputs["Object"], ns.inputs["Vector"])
    L(ns.outputs["Fac"], tierra.inputs["Fac"])
    L(tierra.outputs["Color"], oceano.inputs[0])
    L(tc.outputs["Object"], nube.inputs["Vector"])
    L(nube.outputs["Fac"], cr2.inputs["Fac"])
    L(oceano.outputs[2], nubes.inputs[6])
    L(cr2.outputs["Color"], nubes.inputs[0])
    L(nubes.outputs[2], pr.inputs["Base Color"])
    L(pr.outputs[0], out.inputs["Surface"])
    return m


def s7(ctx, i, f0, f1):
    col = coleccion("S7_Espacio")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    cielo.poner(ctx.cielo, f0, True)
    # la Tierra vista desde la órbita: planeta con halo azul (la atmósfera) y un cielo negro con estrellas
    p, h = K.planeta("tierra", O + Vector((0, 0, -14.0)), 12.0, col, ((0.01, 0.06, 0.32), (0.03, 0.2, 0.55), (0.85, 0.9, 0.95)), bandas=3.0, halo=(0.25, 0.55, 1.0))
    p.data.materials[0] = mat_tierra()
    K.luz_area(col, "luz_s7", O + Vector((8, -10, 6)), 1500.0, (1.0, 0.97, 0.92), 8.0, (math.radians(60), 0, math.radians(30)))
    sol = bpy.data.lights.new("sol_s7", "SUN")
    sol.energy = 0.0
    so = bpy.data.objects.new("sol_s7", sol)
    col.objects.link(so)
    cam_fija(ctx, col, "cam_s7", f0, f1, lambda f: O + Vector((lerp(-3.0, 3.0, (f - f0) / n), -26.0, lerp(1.0, 2.5, (f - f0) / n))), lambda f: O + Vector((0, 0, lerp(-4.0, -3.0, (f - f0) / n))), lente=30.0)
    ctx.escena_activa(col, f0, f1)


def s8(ctx, i, f0, f1):
    col = coleccion("S8_Cierre")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    cielo.poner(ctx.cielo, f0, False, 48.0, 200.0)
    paisaje(col, O, 19, arboles=18)
    cam_fija(ctx, col, "cam_s8", f0, f1, lambda f: O + Vector((lerp(-1.0, 1.0, (f - f0) / n), -6.0, 1.7)),
             lambda f: O + Vector((0, 50.0, lerp(20.0, 30.0, suave((f - f0) / n)))), lente=24.0)
    ctx.escena_activa(col, f0, f1)
