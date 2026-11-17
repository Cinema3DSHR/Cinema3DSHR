"""Armas del pack estilizado que mandó el dueño para «Dúo Cero» (un FBX con 19 piezas sueltas tripo_part_N).

El pack viene con escalas mezcladas (la pistola mide más que el fusil): cada pieza se normaliza a su largo real.
Puntos medidos sobre las vistas de frente del pack (coordenadas del FBX importado, en metros del pack): empuñadura
(palma derecha), mano de apoyo (palma izquierda) y boca del cañón. El soporte de cada arma sigue la convención de
estudio/blender/armas.py (origen = empuñadura, boca hacia −Y, +Z arriba), así efectos.fogonazos sirve tal cual.
"""
from __future__ import annotations
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

from estudio.blender import importar as I

REF = "mixamo:personajes_pelicula/armas_stickman/tripo_convert_e66afd6d-d480-4c93-9ba8-05af98663f39.fbx"

ARMAS = {
    # nombre: pieza, largo real (m), empuñadura, mano izquierda, boca (en el FBX del pack)
    "fusil":     {"parte": 15, "largo_m": 0.95, "empunadura": (0.077, 0.0065, 0.4707), "mano_izq": (-0.046, 0.0065, 0.510),
                  "boca": (-0.126, 0.0065, 0.497)},
    "subfusil":  {"parte": 17, "largo_m": 0.66, "empunadura": (0.1895, 0.0058, 0.7105), "mano_izq": (-0.012, 0.0058, 0.745),
                  "boca": (-0.1163, 0.0058, 0.7528)},
    "ak":        {"parte": 11, "largo_m": 0.88, "empunadura": (-0.3645, 0.0051, 0.455), "mano_izq": (-0.228, 0.0051, 0.500),
                  "boca": (-0.1496, 0.0051, 0.5058)},
    "escopeta":  {"parte": 13, "largo_m": 0.95, "empunadura": (-0.272, 0.0061, 0.604), "mano_izq": (-0.380, 0.0061, 0.618),
                  "boca": (-0.4889, 0.0061, 0.5802)},
    "pistola":   {"parte": 9, "largo_m": 0.24, "empunadura": (-0.212, 0.0063, 0.857), "mano_izq": (-0.225, 0.0063, 0.84),
                  "boca": (-0.488, 0.0063, 0.9327)},
    "francotirador": {"parte": 0, "largo_m": 1.15, "empunadura": (0.395, 0.0074, 0.592), "mano_izq": (0.096, 0.0074, 0.615),
                      "boca": (-0.079, 0.0074, 0.6277)},
    "cuchillo":  {"parte": 5, "largo_m": 0.30},
    "farol":     {"parte": 3, "largo_m": 0.42},
}

_LIB: dict = {}


def _biblioteca():
    """Importa el pack una sola vez (oculto); las armas son copias que comparten la malla."""
    if _LIB.get("col") is not None and _LIB["col"].name in bpy.data.collections:
        return _LIB
    col = bpy.data.collections.new("BIBLIOTECA_armas_stickman")
    bpy.context.scene.collection.children.link(col)
    objs = I.importar(REF, col)
    col.hide_render = col.hide_viewport = True
    bpy.context.view_layer.update()
    _LIB.clear()
    _LIB.update({"col": col, "partes": {o.name.split(".")[0]: o for o in objs if o.type == "MESH"}})
    return _LIB


def _marco(info: dict, parte) -> tuple[Matrix, float]:
    """Matriz pack → soporte (empuñadura al origen, boca hacia −Y, escala al largo real) y el factor de escala."""
    mw = parte.matrix_world
    xs = [(mw @ Vector(c)).x for c in parte.bound_box]
    largo = max(xs) - min(xs)
    s = info["largo_m"] / max(1e-6, largo)
    g = Vector(info.get("empunadura") or ((min(xs) + max(xs)) / 2, 0.0, sum((mw @ Vector(c)).z for c in parte.bound_box) / 8))
    boca = Vector(info["boca"]) if info.get("boca") else g + Vector((-1, 0, 0))
    adelante = -1.0 if boca.x < g.x else 1.0
    rot = Matrix.Rotation(math.pi / 2 * (1 if adelante < 0 else -1), 4, "Z")      # boca del pack → −Y
    return Matrix.Scale(s, 4) @ rot @ Matrix.Translation(-g), s


def crear(nombre_arma: str, nombre_obj: str, col=None):
    """Crea el arma (soporte vacío + pieza) en el origen. Devuelve el soporte con "boca_local" y "mano_izq_local"."""
    lib = _biblioteca()
    info = ARMAS[nombre_arma]
    parte = lib["partes"][f"tripo_part_{info['parte']}"]
    col = col or bpy.context.scene.collection
    sop = bpy.data.objects.new(nombre_obj, None)
    sop.empty_display_type = "ARROWS"
    sop.empty_display_size = 0.12
    col.objects.link(sop)
    pieza = parte.copy()
    col.objects.link(pieza)
    T, s = _marco(info, parte)
    pieza.parent = sop
    pieza.matrix_parent_inverse = Matrix.Identity(4)
    pieza.matrix_basis = T @ parte.matrix_world
    pieza.hide_render = pieza.hide_viewport = False
    sop["boca_local"] = tuple(T @ Vector(info["boca"])) if info.get("boca") else (0.0, -info["largo_m"] / 2, 0.0)
    sop["mano_izq_local"] = tuple(T @ Vector(info["mano_izq"])) if info.get("mano_izq") else (0.0, -0.1, 0.0)
    sop["pieza"] = pieza.name
    return sop


def _palma(arm, hueso: str) -> Vector:
    dedo = arm.pose.bones.get(hueso + "Middle1")
    pb = arm.pose.bones[hueso]
    cola = dedo.head if dedo is not None else pb.tail
    return arm.matrix_world @ ((pb.head + cola) / 2)


def acoplar(pj: dict, nombre_arma: str, accion_ref, frame_ref: int, col=None,
            mano_der="mixamorig:RightHand", mano_izq="mixamorig:LeftHand"):
    """Arma en la mano derecha del personaje, calibrada con una pose de apuntar (clip ya retargeteado)."""
    arm = pj["armadura"]
    sc = bpy.context.scene
    sop = crear(nombre_arma, f"ARMA_{pj['id']}_{nombre_arma}", col)
    ad = arm.animation_data_create()
    previa, nla = ad.action, ad.use_nla
    slot = getattr(ad, "action_slot", None)
    ad.use_nla = False
    ad.action = accion_ref
    if accion_ref.slots:
        ad.action_slot = accion_ref.slots[0]
    raiz = pj["raiz"]
    loc0, rot0 = raiz.location.copy(), raiz.rotation_euler.copy()
    sc.frame_set(frame_ref)
    bpy.context.view_layer.update()
    pd, pi = _palma(arm, mano_der), _palma(arm, mano_izq)
    pb = arm.pose.bones[mano_der]
    P = arm.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))
    gd, gi = Vector((0, 0, 0)), Vector(sop["mano_izq_local"])
    v_l, v_w = (gi - gd).normalized(), (pi - pd).normalized()
    R1 = v_l.rotation_difference(v_w)
    arriba_l = R1 @ Vector((0, 0, 1))

    def plano(v, e):
        return (v - e * v.dot(e)).normalized()
    a, b = plano(arriba_l, v_w), plano(Vector((0, 0, 1)), v_w)
    ang = math.atan2(a.cross(b).dot(v_w), a.dot(b))
    R = Quaternion(v_w, ang) @ R1
    ref_world = Matrix.Translation(pd - R @ gd) @ R.to_matrix().to_4x4()
    sop.parent = arm
    sop.parent_type = "BONE"
    sop.parent_bone = mano_der
    sop.matrix_parent_inverse = P.inverted()
    sop.matrix_basis = ref_world
    ad.action, ad.use_nla = previa, nla
    if slot is not None and previa is not None:
        try:
            ad.action_slot = slot
        except Exception:
            pass
    return sop


def visible(obj, tramos: list[tuple[int, int]]):
    """El arma (y su pieza) se ve sólo en los tramos de cuadros [f0, f1] (p. ej. apoyada en el piso y después en la mano)."""
    objs = [obj] + list(obj.children)
    for o in objs:
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=0)
        for f0, f1 in tramos:
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=f0)
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=f1 + 1)
        if o.animation_data and o.animation_data.action:
            from estudio.blender import kit as K
            for fc in K._fcurves(o.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
