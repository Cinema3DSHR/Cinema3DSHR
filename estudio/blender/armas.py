"""Armas en la mano de un personaje con esqueleto mixamorig.

El arma (GLB de Extraction-tactical: origen = centro de la empuñadura, +Z = boca del cañón, +Y arriba, +X izquierda del
tirador) se acopla RÍGIDAMENTE al hueso de la mano derecha. La posición se CALIBRA con una pose de referencia (los clips
de rifle de Mixamo están animados con un arma en las manos): la empuñadura va en la palma derecha y el punto de la mano
izquierda del arma (armas_puntos.json) queda sobre la palma izquierda; el giro sobre el eje del cañón sale de «arriba».
"""
from __future__ import annotations
import json
import math

import bpy
from mathutils import Matrix, Vector, Quaternion
from estudio import config
from estudio.blender import importar as I

ARMAS = {
    "M4A1": "rifle_M4A1", "AK47": "rifle_AK47", "Mossberg": "escopeta_Mossberg", "AWP": "francotirador_AWP", "USP": "pistola_USP",
}
BASE = "extraction:characters/armas"


def puntos(arma: str) -> dict:
    d = json.loads(config.resolver(f"{BASE}/armas_puntos.json").read_text())
    return d[ARMAS[arma]]


def _palma(arm, hueso: str) -> Vector:
    """Centro de la palma: punto medio entre la muñeca y la base del dedo medio (la «cola» del hueso de la mano no sirve:
    el importador de glTF se la inventa y puede medir metros)."""
    dedo = arm.pose.bones.get(hueso + "Middle1")
    pb = arm.pose.bones[hueso]
    cola = dedo.head if dedo is not None else pb.tail
    return arm.matrix_world @ ((pb.head + cola) / 2)


def acoplar(arm, arma: str, accion_ref, frame_ref: int, col=None, mano_der="mixamorig:RightHand", mano_izq="mixamorig:LeftHand"):
    """Importa el arma y la deja acoplada a `mano_der`. `accion_ref`: acción (ya retargeteada) con el arma en posición de
    apuntar; se evalúa en `frame_ref`. Devuelve el objeto (raíz del arma)."""
    sc = bpy.context.scene
    pts = puntos(arma)
    objs = I.importar(f"{BASE}/{ARMAS[arma]}.glb", col)
    # soporte vacío: las piezas importadas conservan su matriz local (incluida la conversión glTF Y-arriba → Blender Z-arriba)
    raiz = bpy.data.objects.new(f"ARMA_{arma}", None)
    raiz.empty_display_type = "ARROWS"
    raiz.empty_display_size = 0.15
    (col or bpy.context.scene.collection).objects.link(raiz)
    for o in objs:
        if o.parent is None:
            o.parent = raiz
    # evaluar la pose de referencia sin NLA
    ad = arm.animation_data_create()
    previa, nla, slot = ad.action, ad.use_nla, getattr(ad, "action_slot", None)
    ad.use_nla = False
    ad.action = accion_ref
    if accion_ref.slots:
        ad.action_slot = accion_ref.slots[0]
    sc.frame_set(frame_ref)
    bpy.context.view_layer.update()
    pd, pi = _palma(arm, mano_der), _palma(arm, mano_izq)
    P = arm.matrix_world @ arm.pose.bones[mano_der].matrix @ Matrix.Translation((0, arm.pose.bones[mano_der].length, 0))  # origen = cola del hueso
    # orientación: el vector empuñadura→mano izquierda del arma se alinea con palma derecha→palma izquierda
    gl = lambda v: Vector((v[0], -v[2], v[1]))      # glTF (x, y, z) → Blender (x, −z, y)
    gd, gi = gl(pts["mano_derecha"]), gl(pts["mano_izquierda"] or (0, 0.06, 0.24))
    v_l, v_w = (gi - gd).normalized(), (pi - pd).normalized()
    R1 = v_l.rotation_difference(v_w)
    arriba_l = R1 @ Vector((0, 0, 1))                 # «arriba» del arma ya en ejes de Blender
    def plano(v, e): return (v - e * v.dot(e)).normalized()
    a, b = plano(arriba_l, v_w), plano(Vector((0, 0, 1)), v_w)
    ang = math.atan2(a.cross(b).dot(v_w), a.dot(b))
    R = Quaternion(v_w, ang) @ R1
    ref_world = Matrix.Translation(pd - R @ gd) @ R.to_matrix().to_4x4()
    raiz.parent = arm
    raiz.parent_type = "BONE"
    raiz.parent_bone = mano_der
    raiz.matrix_parent_inverse = P.inverted()
    raiz.matrix_basis = ref_world
    # restaurar
    ad.action, ad.use_nla = previa, nla
    if slot is not None and previa is not None:
        ad.action_slot = slot
    raiz["arma"] = arma
    raiz["boca_local"] = list(gl(pts["boca_canon"]))
    return raiz
