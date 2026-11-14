"""Retargeting de animaciones entre esqueletos con los MISMOS nombres de hueso (p. ej. Mixamo `mixamorig:*`).

Por qué hace falta (medido): aplicar a ciegas un clip FBX de Mixamo sobre otro personaje con los mismos nombres de
hueso lo deja en T-pose (Blender 5 liga cada acción a un «slot») y, asignando el slot, la cadera viaja a −77 m: el
FBX está en centímetros, el personaje mide 1 m y sus huesos pueden tener otros ejes locales.

Método (en espacio mundo, hueso por hueso, padres primero):
  rotación objetivo = (rotación_pose_origen · rotación_reposo_origen⁻¹) · rotación_reposo_objetivo
  → el hueso objetivo gira lo mismo que el de origen respecto de su reposo, sin depender de los ejes locales.
  posición: sólo la cadera se desplaza (desvío del origen respecto de su reposo × cociente de alturas); el resto
  de los huesos queda donde lo lleva la cadena de padres.
Resultado: una acción NUEVA con una clave por fotograma (el original no se toca).
"""
from __future__ import annotations
import bpy
from mathutils import Matrix, Quaternion, Vector


def _mundo_hueso(arm, nombre, pose=True):
    b = arm.pose.bones[nombre] if pose else arm.data.bones[nombre]
    m = b.matrix if pose else b.matrix_local
    return arm.matrix_world @ m


def _orden_jerarquico(arm):
    res = []

    def rec(h):
        res.append(h.name)
        for c in h.children:
            rec(c)
    for r in arm.data.bones:
        if r.parent is None:
            rec(r)
    return res


def altura_hueso(arm, nombre) -> float:
    """Altura (m, mundo) de la cabeza del hueso en reposo."""
    return (arm.matrix_world @ arm.data.bones[nombre].head_local).z


def retarget(origen, accion_origen, destino, nombre: str, hueso_cadera="mixamorig:Hips",
             escala_pos: float | None = None, fotogramas: tuple[int, int] | None = None):
    """Devuelve una acción nueva para `destino` con la animación de `accion_origen` (que anima `origen`)."""
    sc = bpy.context.scene
    ad_o = origen.animation_data_create()
    previa_o, nla_o = ad_o.action, ad_o.use_nla
    ad_o.use_nla = False
    ad_o.action = accion_origen
    if accion_origen.slots:
        ad_o.action_slot = accion_origen.slots[0]
    ad_d = destino.animation_data_create()
    ad_d.action = None
    nueva = bpy.data.actions.new(nombre)
    ad_d.action = nueva
    try:
        ad_d.action_slot = nueva.slots.new(destino.id_type, destino.name) if not nueva.slots else nueva.slots[0]
    except Exception:
        pass
    comunes = [n for n in _orden_jerarquico(destino) if n in origen.pose.bones]
    if escala_pos is None:
        h_o = altura_hueso(origen, hueso_cadera)
        h_d = altura_hueso(destino, hueso_cadera)
        escala_pos = h_d / h_o if h_o else 1.0
    f0, f1 = fotogramas or (int(accion_origen.frame_range[0]), int(accion_origen.frame_range[1]))
    rest_o = {n: _mundo_hueso(origen, n, pose=False) for n in comunes}
    rest_d = {n: _mundo_hueso(destino, n, pose=False) for n in comunes}
    for pb in destino.pose.bones:
        pb.rotation_mode = "QUATERNION"
    mw_d_inv = destino.matrix_world.inverted()
    escala_obj = destino.matrix_world.to_scale()
    cad0 = cad1 = None
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for n in comunes:
            pose_o = _mundo_hueso(origen, n, pose=True)
            delta = pose_o.to_quaternion() @ rest_o[n].to_quaternion().inverted()
            q_obj = delta @ rest_d[n].to_quaternion()
            if n == hueso_cadera:
                despl = (pose_o.translation - rest_o[n].translation) * escala_pos
                pos = rest_d[n].translation + despl
                cad0 = pos.copy() if cad0 is None else cad0
                cad1 = pos.copy()
            else:
                pos = None
            pb = destino.pose.bones[n]
            if pos is None:
                # posición = la que resulta de la cadena de padres con el reposo: se conserva la cabeza actual
                pos = destino.matrix_world @ pb.head
            # la escala MUNDO del hueso es la del objeto (p. ej. ×1,7): si se pusiera 1, el hueso quedaría a 1/1,7
            m_mundo = Matrix.LocRotScale(pos, q_obj, escala_obj)
            pb.matrix = mw_d_inv @ m_mundo
            bpy.context.view_layer.update()
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if n == hueso_cadera:
                pb.keyframe_insert("location", frame=f)
    ad_o.action = previa_o
    ad_o.use_nla = nla_o
    if cad0 is not None:
        # cuánto avanzó la cadera en todo el clip (m, mundo, con el personaje sin girar): sirve para encadenar clips
        nueva["desplazamiento_cadera_m"] = [cad1.x - cad0.x, cad1.y - cad0.y, cad1.z - cad0.z]
    ad_d.action = None
    return nueva
