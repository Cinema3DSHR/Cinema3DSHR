"""Ayudantes de nodos y objetos comunes a las recetas de efectos (bpy). Vienen de la prueba «Casa moderna en
tormenta» (pruebas/godot_blender/blender/b8_efectos.py, que no se modifica): se copiaron generalizados (fps de la
escena en vez de 30 fijo, colecciones del contexto)."""
from __future__ import annotations

import bpy
from mathutils import Vector


class Contexto:
    def __init__(self, receta: dict):
        self.receta = receta
        self.fps = receta["escena"]["fps"]
        self.col_fx = self.coleccion("FX_Blender")
        self.col_oculta = self.coleccion("FX_auxiliares_ocultos", ocultar_render=True)

    @staticmethod
    def coleccion(nombre: str, ocultar_render: bool = False):
        c = bpy.data.collections.get(nombre)
        if c is None:
            c = bpy.data.collections.new(nombre)
            bpy.context.scene.collection.children.link(c)
        c.hide_render = ocultar_render
        return c


def tiempo(nodos, fps: int, x=-1200, y=0):
    """Segundos del cuadro actual con un controlador simple (sin Python): frame / fps."""
    v = nodos.new("ShaderNodeValue")
    v.location = (x, y)
    v.label = "segundos"
    d = v.outputs[0].driver_add("default_value").driver
    d.type = "SCRIPTED"
    d.expression = f"frame / {fps}"
    return v.outputs[0]


def material(nombre):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, m.node_tree.nodes, m.node_tree.links


def mat(nt, op, a=None, b=None, x=0, y=0):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.location = (x, y)
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def caja(nombre, centro, tam, coleccion):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centro)
    o = bpy.context.active_object
    o.name = nombre
    o.scale = tam
    bpy.ops.object.transform_apply(scale=True)
    mover(o, coleccion)
    return o


def mover(o, coleccion):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coleccion.objects.link(o)


def g2b(v):
    """Godot (x, y arriba, z) → Blender (x, −z, y arriba): la misma conversión que hace el importador glTF."""
    return Vector((v[0], -v[2], v[1]))


def ancla_pos(ancla) -> Vector:
    return ancla.matrix_world.translation.copy()


def malla_de(nombre: str):
    """El objeto malla con ese nombre o la primera malla entre sus hijos (los GLB anidan la malla bajo un nodo)."""
    o = bpy.data.objects.get(nombre)
    if o is None:
        raise KeyError(f"no está el objeto «{nombre}» en la escena importada")
    if o.type == "MESH":
        return o
    m = next((h for h in o.children_recursive if h.type == "MESH"), None)
    if m is None:
        raise KeyError(f"«{nombre}» no tiene ninguna malla")
    return m
