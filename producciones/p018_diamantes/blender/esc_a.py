"""p018 · escenas s0 (gancho), s1 (gigantes helados) y s2 (descenso con presión y temperatura)."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import comun as K
import saldo as SAL
import guion


def sol_escena(col, nombre, energia, rot, f0, f1, color=(1, 1, 1)):
    lo = K.sol(col, nombre, 0.0, rot, color)
    d = lo.data
    for f_, e_ in ((0, 0.0), (max(0, f0 - 1), 0.0), (f0, energia), (f1, energia), (f1 + 1, 0.0)):
        d.energy = e_
        d.keyframe_insert("energy", frame=f_)
    lib._interp_id(d, "CONSTANT")
    return lo


def construir(ctx, i, f0, f1):
    [s0, s1, s2][i](ctx, i, f0, f1)


COL_NEP = ((0.005, 0.02, 0.18), (0.03, 0.14, 0.62), (0.12, 0.42, 0.95))
COL_URA = ((0.15, 0.45, 0.5), (0.3, 0.7, 0.75), (0.5, 0.88, 0.9))


def s0(ctx, i, f0, f1):
    col = coleccion("S0_Gancho")
    O = Vector(ctx.desp(i))
    p, h = K.planeta("neptuno0", O, 6.0, col, COL_NEP, bandas=2.6)
    sol_escena(col, "sol_s0", 2.6, (math.radians(70), 0, math.radians(35)), f0, f1, (1.0, 0.95, 0.9))
    c = Camara("cam_s0", col, 32.0)
    n = f1 - f0
    c.claves(f0, f1 - 1, lambda f: O + Vector((lerp(-3.0, 3.0, suave((f - f0) / n)), -lerp(27.0, 17.0, (f - f0) / n), lerp(2.5, 0.5, (f - f0) / n))), lambda f: O + Vector((0, 0, 0.3)), paso=1)
    ctx.dir.corte(f0, c, velo=False)
    ctx.escena_activa(col, f0, f1)


def s1(ctx, i, f0, f1):
    col = coleccion("S1_Gigantes")
    O = Vector(ctx.desp(i))
    pn, hn = K.planeta("neptuno1", O + Vector((0, 0, -7.6)), 5.2, col, COL_NEP, bandas=2.6)
    pu, hu = K.planeta("urano1", O + Vector((0, 0, 7.6)), 4.6, col, COL_URA, bandas=2.0, halo=(0.5, 0.95, 0.95), inclin=98.0)
    anillo = toro("anillo_urano", O + Vector((0, 0, 7.6)), 6.6, 0.07, col, mat("anillo_u", (0.8, 0.9, 0.9), rug=0.6, emis=(0.5, 0.7, 0.7), fuerza=0.6), rot=(math.radians(90), 0, math.radians(78)))
    sol_escena(col, "sol_s1", 2.6, (math.radians(70), 0, math.radians(30)), f0, f1, (1.0, 0.95, 0.9))
    et_u = SAL.etiqueta(col, "URANO", alto_m=1.3, fuerza=3.0)
    et_u.location = O + Vector((0, -6.0, 7.6))
    et_n = SAL.etiqueta(col, "NEPTUNO", alto_m=1.3, fuerza=3.0)
    et_n.location = O + Vector((0, -6.5, -7.6))
    et_g = SAL.etiqueta(col, "GIGANTES HELADOS", alto_m=0.9, color=(190, 235, 255, 255), fuerza=3.0)
    et_g.location = O + Vector((0, -7.0, 1.2))
    et_h = SAL.etiqueta(col, "H₂ · He · CH₄", alto_m=0.9, color=(255, 255, 255, 255), fuerza=3.0)
    et_h.location = O + Vector((0, -7.0, -0.4))
    for e_ in (et_u, et_n, et_g, et_h):
        K.aparecer(e_, f0 + 12, f0 + 24)
    c = Camara("cam_s1", col, 28.0)
    n = f1 - f0
    c.claves(f0, f1 - 1, lambda f: O + Vector((lerp(-1.5, 1.5, (f - f0) / n), -lerp(38.0, 33.0, (f - f0) / n), lerp(1.2, -1.2, (f - f0) / n))), lambda f: O + Vector((0, 0, 0)), paso=1)
    ctx.dir.corte(f0, c, velo=False)
    ctx.escena_activa(col, f0, f1)


def mat_nube(nombre, color, fuerza=1.6, escala=0.07, umbral=0.45):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = escala * 8
    ns.inputs["Detail"].default_value = 6.0
    ns.inputs["Roughness"].default_value = 0.6
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = umbral - 0.12
    cr.color_ramp.elements[1].position = umbral + 0.18
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = fuerza
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    L = nt.links.new
    L(tc.outputs["Object"], ns.inputs["Vector"])
    L(ns.outputs["Fac"], cr.inputs["Fac"])
    L(cr.outputs["Color"], mz.inputs["Fac"])
    L(tr.outputs[0], mz.inputs[1])
    L(em.outputs[0], mz.inputs[2])
    L(mz.outputs[0], out.inputs["Surface"])
    return m


def s2(ctx, i, f0, f1):
    col = coleccion("S2_Descenso")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    rng = random.Random(5)
    # capas de nubes cada 38 m hacia abajo: de blanco azulado (atmósfera) a verde-azulado profundo (manto)
    for k in range(12):
        u = k / 11.0
        cc = (lerp(0.55, 0.06, u), lerp(0.8, 0.45, u), lerp(1.0, 0.55, u))
        m = mat_nube(f"nube_{k}", cc, fuerza=lerp(0.55, 0.4, u), escala=0.05 + 0.01 * (k % 3), umbral=0.55)
        pl = plano(f"nube_{k}", O + Vector((rng.uniform(-6, 6), rng.uniform(-6, 6), 40.0 - 38.0 * k)), 140, 140, col, m)
        pl.visible_shadow = False
    # motas luminosas para dar sensación de velocidad
    for k in range(260):
        p = O + Vector((rng.uniform(-14, 14), rng.uniform(-14, 14), rng.uniform(-380, 60)))
        e = esfera(f"mota_{k}", p, rng.uniform(0.05, 0.14), col, mat_emisivo("mota_d", (0.7, 0.9, 1.0), 6.0), 6, 4)
        e.visible_shadow = False
    c = Camara("cam_s2", col, 28.0)
    z = lambda f: lerp(60.0, -300.0, suave((f - f0) / n * 0.5 + 0.5) * 2 - 1 if False else ((f - f0) / n) ** 1.0)
    c.claves(f0, f1 - 1, lambda f: O + Vector((2.0 * math.sin((f - f0) / 60.0), 1.5 * math.sin((f - f0) / 90.0 + 1), z(f))), lambda f: O + Vector((0, 9.0, z(f) - 30.0)), paso=1)
    ctx.dir.corte(f0, c, velo=False)
    # tablero: presión y temperatura que suben mientras se desciende (odómetros 3D pegados a la cámara)
    raiz = bpy.data.objects.new("hud_s2", None)
    col.objects.link(raiz)
    raiz.parent = c.o
    raiz.location = (0, 0.26, -1.0)
    raiz.rotation_euler = (math.radians(-90), 0, 0)
    od_p = SAL.Odometro(col, "od_presion", 7, 0.034, 0.055, color=(0.6, 0.95, 1.0), fuerza=3.2)
    od_p.raiz.parent = raiz
    od_p.raiz.location = (0, 0, 0)
    et_p = SAL.etiqueta(col, "PRESIÓN (atmósferas)", alto_m=0.033, color=(200, 225, 255, 255), fuerza=2.4, tam=90, pad=8)
    et_p.parent = raiz
    et_p.location = (0, 0, 0.05)
    od_t = SAL.Odometro(col, "od_temp", 4, 0.034, 0.055, color=(1.0, 0.75, 0.4), fuerza=3.2, con_puntos=False)
    od_t.raiz.parent = raiz
    od_t.raiz.location = (0, 0, -0.17)
    et_t = SAL.etiqueta(col, "TEMPERATURA (kelvin)", alto_m=0.033, color=(255, 215, 170, 255), fuerza=2.4, tam=90, pad=8)
    et_t.parent = raiz
    et_t.location = (0, 0, -0.12)
    od_p.poner(1, f0)
    od_p.contar(1, 1500000, f0 + 6, f1 - 14)
    od_p.poner(1500000, f1 - 1)
    od_t.poner(55, f0)
    od_t.contar(55, 5000, f0 + 6, f1 - 14)
    od_t.poner(5000, f1 - 1)
    od_p.fin()
    od_t.fin()
    ctx.escena_activa(col, f0, f1)
