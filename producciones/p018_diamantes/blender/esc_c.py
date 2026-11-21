"""p018 · s5 (la lluvia de diamantes), s7 (hipótesis: nadie la ha visto) y s8 (pregunta final)."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import comun as K
import saldo as SAL
from esc_a import sol_escena, mat_nube, COL_NEP


def construir(ctx, i, f0, f1):
    {5: s5, 7: s7, 8: s8}[i](ctx, i, f0, f1)


def mat_gradiente(nombre, abajo, medio, arriba, z0=-60.0, z1=60.0):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = z0
    mr.inputs["From Max"].default_value = z1
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*abajo, 1)
    cr.color_ramp.elements[1].color = (*arriba, 1)
    e = cr.color_ramp.elements.new(0.45)
    e.color = (*medio, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    L = nt.links.new
    L(tc.outputs["Object"], sp.inputs["Vector"])
    L(sp.outputs["Z"], mr.inputs["Value"])
    L(mr.outputs["Result"], cr.inputs["Fac"])
    L(cr.outputs["Color"], em.inputs["Color"])
    L(em.outputs[0], out.inputs["Surface"])
    return m


def lluvia_gemas(col, O, n, f0, f1, semilla, caja_x=12.0, y_rango=(-4.0, 38.0), z_rango=(-16.0, 42.0), vel=(0.10, 0.22), tam=(0.12, 0.45), nombre="gema"):
    rng = random.Random(semilla)
    mg = K.mat_gema("gema_" + nombre, (0.6, 0.92, 1.0), 3.4)
    base = K.malla_gema("base_" + nombre, col, mg, radio=1.0, alto=1.6, lados=8)
    base.hide_render = True
    out = []
    for k in range(n):
        p = O + Vector((rng.uniform(-caja_x, caja_x), rng.uniform(*y_rango), rng.uniform(*z_rango)))
        t = rng.uniform(*tam)
        o = K.duplicar(base, f"{nombre}_{k}", col, p, t, (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3)))
        v = rng.uniform(*vel)
        w = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.03
        o.keyframe_insert("location", frame=f0)
        o.keyframe_insert("rotation_euler", frame=f0)
        o.location = p - Vector((0, 0, v * (f1 - f0)))
        o.rotation_euler = (o.rotation_euler.x + w.x * (f1 - f0), o.rotation_euler.y + w.y * (f1 - f0), o.rotation_euler.z + w.z * (f1 - f0))
        o.keyframe_insert("location", frame=f1)
        o.keyframe_insert("rotation_euler", frame=f1)
        lib._interp(o, "LINEAR")
        out.append(o)
    return out


def s5(ctx, i, f0, f1):
    col = coleccion("S5_Lluvia")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    fondo = plano("fondo_manto", O + Vector((0, 70, 0)), 260, 260, col, mat_gradiente("grad_manto", (1.0, 0.45, 0.1), (0.02, 0.35, 0.4), (0.01, 0.1, 0.2), z0=-25.0, z1=60.0), rot=(math.radians(90), 0, 0))
    fondo.visible_shadow = False
    for k, (y_, cc) in enumerate(((22.0, (0.1, 0.55, 0.6)), (40.0, (0.08, 0.4, 0.5)))):
        nb = plano(f"bruma_{k}", O + Vector((0, y_, 8.0)), 130, 130, col, mat_nube(f"bruma_{k}", cc, fuerza=0.5, escala=0.04, umbral=0.5), rot=(math.radians(90), 0, 0))
        nb.visible_shadow = False
    K.luz_area(col, "luz_s5a", O + Vector((-6, -4, 14)), 1800.0, (0.6, 0.9, 1.0), 8.0, (math.radians(70), 0, math.radians(-20)))
    K.luz_area(col, "luz_s5b", O + Vector((7, -3, -2)), 1200.0, (1.0, 0.75, 0.5), 8.0, (math.radians(100), 0, math.radians(20)))
    lluvia_gemas(col, O, 190, f0, f1, 31)
    c = Camara("cam_s5", col, 30.0)
    c.claves(f0, f1 - 1, lambda f: O + Vector((1.2 * math.sin((f - f0) / 70.0), 0.0, lerp(30.0, -2.0, (f - f0) / n))), lambda f: O + Vector((0.6 * math.sin((f - f0) / 90.0 + 1), 14.0, lerp(30.0, -2.0, (f - f0) / n) - 3.0)), paso=1)
    ctx.dir.corte(f0, c, velo=False)
    ctx.escena_activa(col, f0, f1)


def s7(ctx, i, f0, f1):
    col = coleccion("S7_Hipotesis")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    p, h = K.planeta("neptuno7", O, 5.0, col, COL_NEP, bandas=2.6)
    sol_escena(col, "sol_s7", 2.6, (math.radians(70), 0, math.radians(40)), f0, f1, (1.0, 0.95, 0.9))
    # destellos de diamante flotando alrededor del planeta (sólo ambiente: el mensaje es «hipótesis»)
    lluvia_gemas(col, O, 36, f0, f1, 77, caja_x=9.0, y_rango=(-6.0, 6.0), z_rango=(-6.0, 9.0), vel=(0.01, 0.03), tam=(0.06, 0.16), nombre="gem7")
    c = Camara("cam_s7", col, 34.0)
    c.claves(f0, f1 - 1, lambda f: O + Vector((30.0 * math.sin(math.radians(lerp(-25, 25, (f - f0) / n))), -30.0 * math.cos(math.radians(lerp(-25, 25, (f - f0) / n))), lerp(2.5, 0.8, (f - f0) / n))), lambda f: O, paso=1)
    ctx.dir.corte(f0, c, velo=False)
    ctx.escena_activa(col, f0, f1)


def s8(ctx, i, f0, f1):
    col = coleccion("S8_Pregunta")
    O = Vector(ctx.desp(i))
    n = f1 - f0
    p, h = K.planeta("neptuno8", O + Vector((-4.0, 24.0, -14.0)), 9.0, col, COL_NEP, bandas=2.6)
    sol_escena(col, "sol_s8", 2.4, (math.radians(70), 0, math.radians(40)), f0, f1, (1.0, 0.95, 0.9))
    K.luz_area(col, "luz_s8", O + Vector((-4, -5, 6)), 1500.0, (0.7, 0.95, 1.0), 8.0, (math.radians(70), 0, math.radians(-20)))
    lluvia_gemas(col, O, 70, f0, f1, 55, caja_x=6.0, y_rango=(2.0, 20.0), z_rango=(-4.0, 16.0), vel=(0.04, 0.10), tam=(0.1, 0.5), nombre="gem8")
    c = Camara("cam_s8", col, 30.0)
    c.claves(f0, f1 - 1, lambda f: O + Vector((0.4 * math.sin((f - f0) / 40.0), -2.0, lerp(7.0, 5.0, (f - f0) / n))), lambda f: O + Vector((0, 14.0, lerp(5.0, 2.0, (f - f0) / n))), paso=1)
    ctx.dir.corte(f0, c, velo=False)
    ctx.escena_activa(col, f0, f1)
