"""p018 · piezas comunes: mundo de estrellas, planetas procedurales, gemas (bipirámides facetadas) y utilidades de animación."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *


def mundo_estrellas(s, color=(0.004, 0.006, 0.018)):
    """Cielo con estrellas procedurales (Voronoi en el mundo) y un fondo azul muy oscuro."""
    w = bpy.data.worlds.new("Cosmos")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "F1"
    vo.inputs["Scale"].default_value = 110.0
    vo.inputs["Randomness"].default_value = 1.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 0.07
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    mr.clamp = True
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    mu = nt.nodes.new("ShaderNodeMath")
    mu.operation = "MULTIPLY"
    mu.inputs[1].default_value = 25.0
    ad = nt.nodes.new("ShaderNodeMix")
    ad.data_type = "RGBA"
    ad.blend_type = "ADD"
    ad.inputs[0].default_value = 1.0
    ad.inputs[6].default_value = (*color, 1.0)
    L = nt.links.new
    L(tc.outputs["Generated"], vo.inputs["Vector"])
    L(vo.outputs["Distance"], mr.inputs["Value"])
    L(mr.outputs["Result"], pw.inputs[0])
    L(pw.outputs[0], mu.inputs[0])
    L(mu.outputs[0], ad.inputs[7])
    L(ad.outputs[2], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    L(bg.outputs[0], out.inputs["Surface"])
    return bg


def mat_planeta(nombre, c1, c2, c3, bandas=2.6, dist=3.6, emis=0.12):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = bandas
    wv.inputs["Distortion"].default_value = dist
    wv.inputs["Detail"].default_value = 2.0
    wv.inputs["Detail Scale"].default_value = 1.0
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*c1, 1)
    cr.color_ramp.elements[1].color = (*c3, 1)
    e = cr.color_ramp.elements.new(0.5)
    e.color = (*c2, 1)
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
    pr.inputs["Roughness"].default_value = 0.55
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = emis
    ad = nt.nodes.new("ShaderNodeAddShader")
    L = nt.links.new
    L(tc.outputs["Object"], wv.inputs["Vector"])
    L(wv.outputs["Color"], cr.inputs["Fac"])
    L(cr.outputs["Color"], pr.inputs["Base Color"])
    L(cr.outputs["Color"], em.inputs["Color"])
    L(pr.outputs[0], ad.inputs[0])
    L(em.outputs[0], ad.inputs[1])
    L(ad.outputs[0], out.inputs["Surface"])
    return m


def mat_halo(nombre, color, fuerza=2.5, potencia=2.5):
    """Atmósfera: cascarón que sólo brilla en el borde (Fresnel) y es transparente en el centro."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = potencia
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = fuerza
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mz = nt.nodes.new("ShaderNodeMixShader")
    L = nt.links.new
    L(lw.outputs["Facing"], pw.inputs[0])
    L(pw.outputs[0], mz.inputs["Fac"])
    L(tr.outputs[0], mz.inputs[1])
    L(em.outputs[0], mz.inputs[2])
    L(mz.outputs[0], out.inputs["Surface"])
    m.use_backface_culling = True
    return m


def planeta(nombre, centro, radio, col, colores, bandas=7.0, halo=(0.25, 0.55, 1.0), inclin=0.0):
    m = mat_planeta(nombre, *colores, bandas=bandas)
    p = esfera(nombre, centro, radio, col, m, 64, 40)
    p.rotation_euler = (math.radians(inclin), 0, 0)
    h = esfera(nombre + "_atm", centro, radio * 1.045, col, mat_halo(nombre + "_halo", halo), 48, 32)
    h.visible_shadow = False
    return p, h


def mat_gema(nombre, color=(0.55, 0.9, 1.0), brillo=3.0):
    """Diamante barato y bonito: el borde (cara de perfil) brilla y el centro es oscuro y vítreo; sin transmisión real (Cycles a 6 muestras)."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.0, 0.03, 0.09, 1)
    cr.color_ramp.elements[0].position = 0.12
    cr.color_ramp.elements[1].color = (*color, 1)
    cr.color_ramp.elements[1].position = 1.0
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = brillo
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.03
    gl.inputs["Color"].default_value = (0.35, 0.45, 0.5, 1)
    ad = nt.nodes.new("ShaderNodeAddShader")
    L = nt.links.new
    # sombreado por cara: producto punto de la normal con una luz fija → facetas bien marcadas
    ng = nt.nodes.new("ShaderNodeNewGeometry")
    dt = nt.nodes.new("ShaderNodeVectorMath")
    dt.operation = "DOT_PRODUCT"
    dt.inputs[1].default_value = (0.45, -0.55, 0.7)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0
    sm = nt.nodes.new("ShaderNodeMath")
    sm.operation = "ADD"
    L(ng.outputs["Normal"], dt.inputs[0])
    L(dt.outputs["Value"], mr.inputs["Value"])
    L(lw.outputs["Fresnel"], sm.inputs[0])
    L(mr.outputs["Result"], sm.inputs[1])
    sm.use_clamp = True
    sc2 = nt.nodes.new("ShaderNodeMath")
    sc2.operation = "MULTIPLY"
    sc2.inputs[1].default_value = 0.55
    L(sm.outputs[0], sc2.inputs[0])
    L(sc2.outputs[0], cr.inputs["Fac"])
    L(cr.outputs["Color"], em.inputs["Color"])
    L(em.outputs[0], ad.inputs[0])
    L(gl.outputs[0], ad.inputs[1])
    L(ad.outputs[0], out.inputs["Surface"])
    return m


def malla_gema(nombre, col, mat_, radio=1.0, alto=1.5, lados=8, base=0.32):
    """Bipirámide facetada (forma de diamante en bruto). Devuelve el objeto base (ocultar y duplicar con la misma malla)."""
    v = []
    for k in range(lados):
        a = 2 * math.pi * k / lados
        v.append((math.cos(a) * radio, math.sin(a) * radio, 0.0))
    v.append((0, 0, alto))
    v.append((0, 0, -alto * 0.8))
    caras = []
    for k in range(lados):
        k2 = (k + 1) % lados
        caras.append((k, k2, lados))
        caras.append((k2, k, lados + 1))
    o = malla(nombre, v, caras, col, mat_, suave=False)
    return o


def duplicar(base, nombre, col, pos, esc=1.0, rot=(0, 0, 0)):
    o = bpy.data.objects.new(nombre, base.data)
    col.objects.link(o)
    o.location = pos
    o.rotation_euler = rot
    o.scale = (esc, esc, esc) if not hasattr(esc, "__len__") else esc
    o.visible_shadow = False
    return o


def cilindro_entre(nombre, a, b, radio, col, mat_):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = cilindro(nombre, (a + b) / 2, radio, d.length, col, mat_, seg=10)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return o


def aparecer(o, f_ini, f_fin, esc=1.0):
    """Escala 0 → esc entre f_ini y f_fin (oculto antes por escala 0)."""
    o.scale = (0.0001, 0.0001, 0.0001)
    o.keyframe_insert("scale", frame=max(0, int(f_ini) - 1))
    s = esc if hasattr(esc, "__len__") else (esc, esc, esc)
    o.scale = s
    o.keyframe_insert("scale", frame=int(f_fin))


def desaparecer(o, f_ini, f_fin):
    s = tuple(o.scale)
    o.scale = s
    o.keyframe_insert("scale", frame=int(f_ini))
    o.scale = (0.0001, 0.0001, 0.0001)
    o.keyframe_insert("scale", frame=int(f_fin))


def luz_area(col, nombre, pos, energia, color=(1, 1, 1), tam=6.0, rot=(0, 0, 0)):
    ld = bpy.data.lights.new(nombre, "AREA")
    ld.energy = energia
    ld.size = tam
    ld.color = color
    lo = bpy.data.objects.new(nombre, ld)
    col.objects.link(lo)
    lo.location = pos
    lo.rotation_euler = rot
    return lo


def sol(col, nombre, energia, rot, color=(1, 1, 1)):
    ld = bpy.data.lights.new(nombre, "SUN")
    ld.energy = energia
    ld.color = color
    ld.angle = math.radians(2.0)
    lo = bpy.data.objects.new(nombre, ld)
    col.objects.link(lo)
    lo.rotation_euler = rot
    return lo
