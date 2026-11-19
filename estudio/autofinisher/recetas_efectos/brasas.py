"""Receta BRASAS (bpy, determinista por cuadro): chispas emisivas (nodos de geometría) que nacen en una franja sobre
el vacío FX_brasas, suben en su vida con un vaivén y se achican; edad = fract(t / vida + fase)."""
from __future__ import annotations

import bpy

from estudio.autofinisher.recetas_efectos import nodos as K

PARAMETROS_POR_DEFECTO = {
    "cantidad": 45, "vida": 2.2, "ancho": 0.6, "fondo": 0.2, "subida": 0.9, "semilla": 5,
    "vaiven": 0.05, "frecuencia": 3.0, "tamano": 0.007, "tamano_min": 0.001,
    "color": [1.0, 0.45, 0.08], "emision": 40.0,
}


def aplicar(ancla, p: dict, ctx: K.Contexto) -> dict:
    b = K.ancla_pos(ancla)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(0, 0, -50))
    chispa = bpy.context.active_object
    chispa.name = "Chispa"
    K.mover(chispa, ctx.col_oculta)
    m, N, L = K.material("chispa")
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*p["color"], 1)
    em.inputs["Strength"].default_value = p["emision"]
    out = N.new("ShaderNodeOutputMaterial")
    L.new(em.outputs[0], out.inputs["Surface"])
    chispa.data.materials.append(m)
    me = bpy.data.meshes.new("Brasas")
    o = bpy.data.objects.new("Brasas_chispas", me)
    ctx.col_fx.objects.link(o)
    ng = bpy.data.node_groups.new("Brasas_nodos", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    sal = N.new("NodeGroupOutput")
    pts = N.new("GeometryNodePoints")
    pts.inputs["Count"].default_value = p["cantidad"]
    rnd = N.new("FunctionNodeRandomValue"); rnd.data_type = "FLOAT_VECTOR"; rnd.inputs["Seed"].default_value = p["semilla"]
    sp = N.new("ShaderNodeSeparateXYZ")
    L.new(rnd.outputs["Value"], sp.inputs[0])
    tm = N.new("GeometryNodeInputSceneTime")
    edad = K.mat(ng, "FRACT", K.mat(ng, "ADD", K.mat(ng, "DIVIDE", tm.outputs["Seconds"], p["vida"]), sp.outputs[2]))
    vaiven = K.mat(ng, "MULTIPLY", K.mat(ng, "SINE", K.mat(ng, "MULTIPLY_ADD", tm.outputs["Seconds"], p["frecuencia"])), p["vaiven"])
    base_x = K.mat(ng, "MULTIPLY_ADD", sp.outputs[0], p["ancho"])
    N[base_x.node.name].inputs[2].default_value = b.x - p["ancho"] / 2
    x = K.mat(ng, "ADD", base_x, vaiven)
    y = K.mat(ng, "MULTIPLY_ADD", sp.outputs[1], p["fondo"])
    N[y.node.name].inputs[2].default_value = b.y - p["fondo"] / 2
    z = K.mat(ng, "MULTIPLY_ADD", edad, p["subida"])
    N[z.node.name].inputs[2].default_value = b.z
    pos = N.new("ShaderNodeCombineXYZ")
    L.new(x, pos.inputs[0]); L.new(y, pos.inputs[1]); L.new(z, pos.inputs[2])
    L.new(pos.outputs[0], pts.inputs["Position"])
    gi = N.new("GeometryNodeObjectInfo"); gi.inputs["Object"].default_value = chispa
    ip = N.new("GeometryNodeInstanceOnPoints")
    L.new(pts.outputs[0], ip.inputs["Points"]); L.new(gi.outputs["Geometry"], ip.inputs["Instance"])
    esc = K.mat(ng, "MULTIPLY_ADD", K.mat(ng, "SUBTRACT", 1.0, edad), p["tamano"])
    N[esc.node.name].inputs[2].default_value = p["tamano_min"]
    L.new(esc, ip.inputs["Scale"])
    L.new(ip.outputs[0], sal.inputs[0])
    o.modifiers.new("Brasas", "NODES").node_group = ng
    return {"brasas": p["cantidad"], "emision": p["emision"]}
