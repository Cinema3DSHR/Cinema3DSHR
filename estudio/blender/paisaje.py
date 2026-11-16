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


def _material_hojas(nombre: str, color, semilla: int):
    """Hoja con forma (óvalo con punta y nervadura) recortada con transparencia, con variación de color por hoja."""
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    nt = m.node_tree
    N = nt.nodes
    L = nt.links
    N.clear()
    sal = N.new("ShaderNodeOutputMaterial")
    mix = N.new("ShaderNodeMixShader")
    trans = N.new("ShaderNodeBsdfTransparent")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    uv = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sep.inputs[0])

    def op(tipo, a, b=None, k=None):
        n = N.new("ShaderNodeMath")
        n.operation = tipo
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]
    # u ∈ [0,1] a lo ancho, v ∈ [0,1] a lo largo: óvalo que se afina hacia la punta
    x = op("SUBTRACT", sep.outputs["X"], 0.5)
    y = sep.outputs["Y"]
    ancho = op("MULTIPLY", op("POWER", op("MULTIPLY", op("MULTIPLY", y, op("SUBTRACT", 1.0, y)), 4.0), 0.75), 0.5)
    adentro = op("LESS_THAN", op("ABSOLUTE", x), ancho)
    L.new(adentro, mix.inputs["Fac"])
    L.new(trans.outputs[0], mix.inputs[1])
    L.new(bsdf.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], sal.inputs["Surface"])
    # color: varía por hoja (posición del objeto no sirve: son instancias) → ruido en coordenadas generadas
    ruido = N.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 3.0
    L.new(uv.outputs["Object"], ruido.inputs["Vector"])
    rampa = N.new("ShaderNodeValToRGB")
    c = color
    rampa.color_ramp.elements[0].color = (c[0] * 0.55, c[1] * 0.6, c[2] * 0.45, 1)
    rampa.color_ramp.elements[1].color = (min(1, c[0] * 1.35), min(1, c[1] * 1.25), min(1, c[2] * 1.1), 1)
    L.new(ruido.outputs["Fac"], rampa.inputs["Fac"])
    nerv = op("LESS_THAN", op("ABSOLUTE", x), 0.025)
    oscuro = N.new("ShaderNodeMixRGB")
    oscuro.blend_type = "MULTIPLY"
    L.new(nerv, oscuro.inputs["Fac"])
    L.new(rampa.outputs["Color"], oscuro.inputs[1])
    oscuro.inputs[2].default_value = (0.7, 0.8, 0.6, 1)
    L.new(oscuro.outputs[0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.55
    for k in ("Transmission Weight", "Subsurface Weight"):
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = 0.12 if k.startswith("Trans") else 0.0
    return m


VERDES = [(0.10, 0.22, 0.045), (0.13, 0.24, 0.05), (0.08, 0.18, 0.05), (0.15, 0.23, 0.06), (0.09, 0.2, 0.07)]


def vestir(col, semilla: int = 1, color=None, hojas_max: int = 14000, tam: float = 0.22) -> None:
    """Árbol de Sweet Home con follaje de verdad: conserva tronco y ramas del modelo y, donde el modelo tiene sus
    pocas hojas sueltas (y en las puntas altas de las ramas), cuelga racimos densos de hojas con forma y transparencia
    (en vez de una copa maciza). Las hojas originales se quedan, pintadas del mismo verde."""
    rnd = random.Random(semilla)
    color = color or VERDES[semilla % len(VERDES)]
    mallas = [o for o in col.objects if o.type == "MESH"]
    def es_hoja(o):
        n = (o.name + " " + " ".join(m.name for m in o.data.materials if m)).lower()
        return any(k in n for k in HOJA)
    hojas = [o for o in mallas if es_hoja(o)]
    ramas = [o for o in mallas if o not in hojas]
    m_tronco = K.material("tronco_sh3d", (0.2, 0.15, 0.1), 0.88, ruido=0.35, escala_ruido=9, relieve=0.5)
    for o in ramas:
        if not o.data.materials or not any(m and m.node_tree and any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes)
                                           for m in o.data.materials):
            o.data.materials.clear()
            o.data.materials.append(m_tronco)
    m_hoja = _material_hojas(f"hojas_{col.name}", color, semilla)
    for o in hojas:
        o.data.materials.clear()
        o.data.materials.append(m_hoja)
    # dónde van los racimos: centros de las caras de las hojas originales + puntos altos de las ramas
    puntos = []
    for o in hojas:
        mw = o.matrix_world
        for p in o.data.polygons:
            puntos.append(mw @ p.center)
    if ramas:
        mn, mx = _bbox(ramas)
        h0 = mn.z + (mx.z - mn.z) * 0.35
        for o in ramas:
            mw = o.matrix_world
            for p in o.data.polygons:
                q = mw @ p.center
                if q.z > h0 and p.area < 0.08:           # ramitas finas de arriba (no el tronco grueso)
                    puntos.append(q)
    if not puntos:
        return
    rnd.shuffle(puntos)
    por_racimo = 9
    puntos = puntos[: max(1, hojas_max // por_racimo)]
    mn, mx = _bbox(mallas)
    centro = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for q in puntos:
        afuera = (q - centro)
        afuera.z *= 0.3
        afuera = afuera.normalized() if afuera.length > 1e-3 else Vector((0, 0, 1))
        for _ in range(por_racimo):
            c = q + Vector((rnd.gauss(0, 0.3), rnd.gauss(0, 0.3), rnd.gauss(0, 0.24))) + afuera * rnd.uniform(0, 0.25)
            s = tam * rnd.uniform(0.7, 1.3)
            # hoja colgando hacia afuera y algo hacia abajo, girada al azar
            eje = (afuera + Vector((rnd.uniform(-0.7, 0.7), rnd.uniform(-0.7, 0.7), rnd.uniform(-0.9, 0.3)))).normalized()
            lado = eje.cross(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))).normalized() * (s * 0.55)
            largo = eje * s
            vs = [bm.verts.new(c - lado * 0.5), bm.verts.new(c + lado * 0.5), bm.verts.new(c + lado * 0.5 + largo),
                  bm.verts.new(c - lado * 0.5 + largo)]
            f = bm.faces.new(vs)
            for lp, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                lp[uvl].uv = uvv
    me = bpy.data.meshes.new(f"follaje_{col.name}")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m_hoja)
    ob = bpy.data.objects.new(f"follaje_{col.name}", me)
    col.objects.link(ob)
    ob["visor_lod"] = "bajo"
