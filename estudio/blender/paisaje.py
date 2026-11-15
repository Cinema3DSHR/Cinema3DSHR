"""Paisaje rural: árboles que se leen llenos de lejos y campos cultivados.

- `arbolar(col)`: los árboles de Sweet Home tienen las hojas como triángulos sueltos (de lejos parecen palos) y algunos
  (pino, acacia) vienen sin material (se ven blancos). Se les pone material (hoja / tronco según el nombre de la
  pieza) y una copa sólida con ruido apenas por dentro de las hojas, del color de la hoja un poco más oscuro.
- `material_campos()`: terreno con parcelas (alfalfa, trigo, rastrojo, tierra arada, soja, pastura) de 120–260 m con
  surcos, mezcladas con pastura natural donde el atributo de punto «campo» vale 0 (el corredor de la vía y la ruta).
"""
from __future__ import annotations
import math
import random
import bmesh
import bpy
from mathutils import Vector, noise
from estudio.blender import kit as K

HOJA = ("leaf", "leaves", "foil", "hoja", "copa")
TRONCO = ("trunk", "branch", "stem", "twig", "tronco")


def _bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def _color_base(m):
    if m is None or not m.use_nodes:
        return (0.18, 0.3, 0.08)
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    return tuple(b.inputs["Base Color"].default_value[:3]) if b else (0.18, 0.3, 0.08)


def arbolar(col, semilla: int = 1) -> None:
    """Arregla un prototipo de árbol (colección) en el lugar."""
    rnd = random.Random(semilla)
    mallas = [o for o in col.objects if o.type == "MESH"]
    hojas = [o for o in mallas if any(k in o.name.lower() for k in HOJA)]
    if not hojas:
        return
    m_hoja = next((o.data.materials[0] for o in hojas if o.data.materials), None)
    if m_hoja is None:
        m_hoja = K.material(f"hoja_{col.name}", (0.13, 0.26, 0.06), 0.8, ruido=0.3, escala_ruido=3)
    m_tronco = K.material("tronco_sh3d", (0.26, 0.2, 0.14), 0.85, ruido=0.3, escala_ruido=8, relieve=0.4)
    for o in mallas:
        if not o.data.materials:
            o.data.materials.append(m_hoja if o in hojas else m_tronco)
    c = _color_base(m_hoja)
    copa_m = K.material(f"copa_{col.name}", tuple(x * 0.45 for x in c), 0.85, ruido=0.55, escala_ruido=1.4, relieve=0.8)
    mn, mx = _bbox(hojas)
    centro = (mn + mx) / 2
    tam = (mx - mn) * 0.5
    # 3 masas: una central grande y dos más chicas corridas (copa irregular)
    bm = bmesh.new()
    for k in range(3):
        f = 0.82 if k == 0 else 0.55
        off = Vector((0, 0, 0)) if k == 0 else Vector((rnd.uniform(-0.35, 0.35) * tam.x, rnd.uniform(-0.35, 0.35) * tam.y,
                                                       rnd.uniform(-0.2, 0.3) * tam.z))
        vs = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)["verts"]
        sem = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), rnd.uniform(0, 50)))
        for v in vs:
            d = v.co.normalized()
            r = 1.0 + 0.28 * noise.noise(d * 2.2 + sem) + 0.12 * noise.noise(d * 5.0 + sem)
            v.co = centro + off + Vector((d.x * tam.x * f * r, d.y * tam.y * f * r, d.z * tam.z * f * r))
    me = bpy.data.meshes.new(f"copa_{col.name}")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(copa_m)
    ob = bpy.data.objects.new(f"copa_{col.name}", me)
    col.objects.link(ob)
    ob["visor_lod"] = "bajo"


def material_campos(nombre: str = "campos") -> bpy.types.Material:
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = K.material(nombre, (0.16, 0.24, 0.07), 0.92)
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    N = nt.nodes.new
    L = nt.links.new
    tc = N("ShaderNodeTexCoord")
    # parcelas: celdas de Voronoi grandes; cada una con su cultivo
    vor = N("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 0.0055
    vor.distance = "MANHATTAN" if hasattr(vor, "distance") else vor.distance
    L(tc.outputs["Object"], vor.inputs["Vector"])
    rampa = N("ShaderNodeValToRGB")
    cr = rampa.color_ramp
    cr.interpolation = "CONSTANT"
    # albedos lineales (Cycles): alfalfa, trigo maduro, tierra arada, soja, rastrojo, pastura
    colores = [(0.0, (0.035, 0.075, 0.012)), (0.17, (0.25, 0.18, 0.055)), (0.33, (0.075, 0.05, 0.03)), (0.5, (0.05, 0.1, 0.015)),
               (0.66, (0.2, 0.15, 0.07)), (0.83, (0.06, 0.09, 0.022))]
    cr.elements[0].position, cr.elements[0].color = colores[0][0], (*colores[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = colores[1][0], (*colores[1][1], 1)
    for pos, colr in colores[2:]:
        e = cr.elements.new(pos)
        e.color = (*colr, 1)
    sep = N("ShaderNodeSeparateColor")
    L(vor.outputs["Color"], sep.inputs[0])
    L(sep.outputs[0], rampa.inputs["Fac"])
    # surcos: ondas a lo largo de X o de Y según la parcela
    onda_x = N("ShaderNodeTexWave")
    onda_x.inputs["Scale"].default_value = 0.9
    onda_x.wave_type = "BANDS"
    onda_x.bands_direction = "X"
    L(tc.outputs["Object"], onda_x.inputs["Vector"])
    onda_y = N("ShaderNodeTexWave")
    onda_y.inputs["Scale"].default_value = 0.9
    onda_y.wave_type = "BANDS"
    onda_y.bands_direction = "Y"
    L(tc.outputs["Object"], onda_y.inputs["Vector"])
    dir_ = N("ShaderNodeMath")
    dir_.operation = "GREATER_THAN"
    dir_.inputs[1].default_value = 0.5
    L(sep.outputs[1], dir_.inputs[0])
    surco = N("ShaderNodeMix")
    surco.data_type = "FLOAT"
    L(dir_.outputs[0], surco.inputs["Factor"])
    L(onda_x.outputs["Fac"], surco.inputs[2])
    L(onda_y.outputs["Fac"], surco.inputs[3])
    oscur = N("ShaderNodeMix")
    oscur.data_type = "RGBA"
    oscur.blend_type = "MULTIPLY"
    oscur.inputs["Factor"].default_value = 0.22
    L(rampa.outputs["Color"], oscur.inputs[6])
    L(surco.outputs[0], oscur.inputs[7])
    # variación fina y pastura natural en el corredor (atributo «campo» = 0)
    ruido = N("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 0.08
    ruido.inputs["Detail"].default_value = 6.0
    L(tc.outputs["Object"], ruido.inputs["Vector"])
    pastura_r = N("ShaderNodeValToRGB")
    pastura_r.color_ramp.elements[0].color = (0.035, 0.065, 0.012, 1)
    pastura_r.color_ramp.elements[1].color = (0.11, 0.12, 0.035, 1)
    L(ruido.outputs["Fac"], pastura_r.inputs["Fac"])
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "campo"
    borde = N("ShaderNodeMapRange")
    borde.inputs["From Min"].default_value = 0.25
    borde.inputs["From Max"].default_value = 0.55
    L(attr.outputs["Fac"], borde.inputs["Value"])
    mezcla = N("ShaderNodeMix")
    mezcla.data_type = "RGBA"
    L(borde.outputs["Result"], mezcla.inputs["Factor"])
    L(pastura_r.outputs["Color"], mezcla.inputs[6])
    L(oscur.outputs[2], mezcla.inputs[7])
    L(mezcla.outputs[2], bsdf.inputs["Base Color"])
    bump = N("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    L(surco.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m
