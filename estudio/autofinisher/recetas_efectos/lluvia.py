"""Receta LLUVIA (bpy, determinista por cuadro): gotas en una caja alrededor del vacío FX_lluvia que caen en bucle
(fract(fase + t·v/alto)), con deriva de viento, y se borran al pasar por debajo de la primera superficie que encuentra
un rayo vertical (objetos y cajas de choque elegidos) o al llegar al piso. Las gotas son instancias de un cilindro fino
inclinado con el viento. Valores por defecto: los de la prueba «Casa moderna en tormenta» (como la lluvia de Godot)."""
from __future__ import annotations

import math

import bpy

from estudio.autofinisher.recetas_efectos import nodos as K

PARAMETROS_POR_DEFECTO = {
    "cantidad": 9000, "mitad_x": 16.0, "mitad_y": 11.0, "alto": 12.5,
    "velocidad": [11.0, 14.0], "viento": 0.12, "semillas": [3, 9], "piso_z": -0.07, "largo_rayo": 40.0,
    "choque_objetos": [],           # nombres de objetos (su malla real: las copias reducidas dejaban pasar gotas)
    "cajas_choque": [],             # [{nombre, centro (Blender) | centro_godot, tam}]
    "gota": {"radio": 0.006, "largo": 0.55, "vertices": 5, "color": [0.8, 0.85, 0.95], "alfa": 0.35,
             "emision_color": [0.7, 0.78, 0.95], "emision": 0.25, "rugosidad": 0.15},
}


def aplicar(ancla, p: dict, ctx: K.Contexto) -> dict:
    fx = K.ancla_pos(ancla)
    choques = []
    for c in p["cajas_choque"]:
        centro = K.g2b(c["centro_godot"]) if "centro_godot" in c else c["centro"]
        choques.append(K.caja(c.get("nombre", "Choque_lluvia"), centro, tuple(c["tam"]), ctx.col_oculta))
    caras = {}
    for nombre in p["choque_objetos"]:
        m = K.malla_de(nombre)
        choques.append(m)
        caras[nombre] = len(m.data.polygons)
    g = p["gota"]
    bpy.ops.mesh.primitive_cylinder_add(vertices=g["vertices"], radius=g["radio"], depth=g["largo"], location=(0, 0, -50))
    gota = bpy.context.active_object
    gota.name = "Gota_lluvia"
    K.mover(gota, ctx.col_oculta)
    m, n, l = K.material("gota_lluvia")
    out = n.new("ShaderNodeOutputMaterial")
    b = n.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*g["color"], 1)
    b.inputs["Roughness"].default_value = g["rugosidad"]
    b.inputs["Alpha"].default_value = g["alfa"]
    b.inputs["Emission Color"].default_value = (*g["emision_color"], 1)
    b.inputs["Emission Strength"].default_value = g["emision"]
    l.new(b.outputs[0], out.inputs["Surface"])
    gota.data.materials.append(m)

    me = bpy.data.meshes.new("Lluvia")
    o = bpy.data.objects.new("Lluvia", me)
    ctx.col_fx.objects.link(o)
    ng = bpy.data.node_groups.new("Lluvia_nodos", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    salida = N.new("NodeGroupOutput")
    salida.location = (1600, 0)
    X0, X1 = fx.x - p["mitad_x"], fx.x + p["mitad_x"]
    Y0, Y1 = fx.y - p["mitad_y"], fx.y + p["mitad_y"]
    ARRIBA, ALTO = fx.z, p["alto"]
    pts = N.new("GeometryNodePoints")
    pts.inputs["Count"].default_value = p["cantidad"]
    pts.inputs["Radius"].default_value = 0.01
    rnd = N.new("FunctionNodeRandomValue")
    rnd.data_type = "FLOAT_VECTOR"
    rnd.inputs["Seed"].default_value = p["semillas"][0]
    rnd.location = (-1200, 0)
    rv = N.new("FunctionNodeRandomValue")
    rv.data_type = "FLOAT"
    rv.inputs["Seed"].default_value = p["semillas"][1]
    for sk in rv.inputs:                       # Min/Max del tipo flotante (hay uno por tipo de dato)
        if sk.type == "VALUE" and sk.name in ("Min", "Max"):
            sk.default_value = p["velocidad"][0] if sk.name == "Min" else p["velocidad"][1]
    rv.location = (-1200, -300)
    sep = N.new("ShaderNodeSeparateXYZ")
    sep.location = (-1000, 0)
    L.new(rnd.outputs["Value"], sep.inputs[0])
    t = N.new("GeometryNodeInputSceneTime")
    t.location = (-1200, -500)

    def gm(op, a, bb=None, x=0, y=0):
        return K.mat(ng, op, a, bb, x, y)
    x = gm("MULTIPLY_ADD", sep.outputs[0], X1 - X0, -800, 200)
    N[x.node.name].inputs[2].default_value = X0
    y = gm("MULTIPLY_ADD", sep.outputs[1], Y1 - Y0, -800, 0)
    N[y.node.name].inputs[2].default_value = Y0
    vt = gm("MULTIPLY", t.outputs["Seconds"], rv.outputs[0], -900, -400)
    vh = gm("DIVIDE", vt, ALTO, -750, -400)
    fa = gm("ADD", vh, sep.outputs[2], -600, -400)
    fr = gm("FRACT", fa, None, -450, -400)
    caida = gm("MULTIPLY", fr, ALTO, -300, -400)
    z = gm("SUBTRACT", ARRIBA, caida, -150, -400)
    viento = gm("MULTIPLY_ADD", caida, p["viento"], -150, 200)
    N[viento.node.name].inputs[2].default_value = 0.0
    xv = gm("ADD", x, viento, 0, 200)
    pos = N.new("ShaderNodeCombineXYZ")
    pos.location = (150, 0)
    L.new(xv, pos.inputs[0]); L.new(y, pos.inputs[1]); L.new(z, pos.inputs[2])
    L.new(pos.outputs[0], pts.inputs["Position"])
    pts.location = (350, 0)
    borrar = gm("LESS_THAN", z, p["piso_z"], 750, -500)
    if choques:
        origen = N.new("ShaderNodeCombineXYZ")
        origen.location = (150, -250)
        L.new(xv, origen.inputs[0]); L.new(y, origen.inputs[1]); origen.inputs[2].default_value = ARRIBA + 1
        union = N.new("GeometryNodeJoinGeometry")
        union.location = (150, -500)
        for i, ob in enumerate(choques):
            oi = N.new("GeometryNodeObjectInfo")
            oi.transform_space = "RELATIVE"
            oi.inputs["Object"].default_value = ob
            oi.location = (-100, -600 - 150 * i)
            L.new(oi.outputs["Geometry"], union.inputs[0])
        rc = N.new("GeometryNodeRaycast")
        rc.location = (400, -350)
        L.new(union.outputs[0], rc.inputs["Target Geometry"])
        L.new(origen.outputs[0], rc.inputs["Source Position"])
        rc.inputs["Ray Direction"].default_value = (0, 0, -1)
        rc.inputs["Ray Length"].default_value = p["largo_rayo"]
        hz = N.new("ShaderNodeSeparateXYZ")
        hz.location = (600, -350)
        L.new(rc.outputs["Hit Position"], hz.inputs[0])
        debajo = gm("LESS_THAN", z, hz.outputs[2], 750, -300)
        pego = gm("MULTIPLY", debajo, rc.outputs["Is Hit"], 900, -300)
        borrar = gm("MAXIMUM", pego, borrar, 1050, -350)
    dl = N.new("GeometryNodeDeleteGeometry")
    dl.domain = "POINT"
    dl.location = (1100, 0)
    L.new(pts.outputs[0], dl.inputs["Geometry"])
    L.new(borrar, dl.inputs["Selection"])
    gi = N.new("GeometryNodeObjectInfo")
    gi.inputs["Object"].default_value = gota
    gi.location = (1100, -250)
    ip = N.new("GeometryNodeInstanceOnPoints")
    ip.location = (1350, 0)
    L.new(dl.outputs[0], ip.inputs["Points"])
    L.new(gi.outputs["Geometry"], ip.inputs["Instance"])
    ip.inputs["Rotation"].default_value = (0.0, math.atan(p["viento"]), 0.0)
    L.new(ip.outputs[0], salida.inputs[0])
    o.modifiers.new("Lluvia", "NODES").node_group = ng
    return {"gotas": p["cantidad"], "caja_x": [round(X0, 2), round(X1, 2)], "caja_y": [round(Y0, 2), round(Y1, 2)],
            "superficies_de_choque": [c.name for c in choques], "caras_choque": caras}
