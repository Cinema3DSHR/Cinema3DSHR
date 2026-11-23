"""Variante de estudio/blender/retarget.py que conserva la dirección de los huesos del origen (p015)."""
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
             escala_pos: float | None = None, fotogramas: tuple[int, int] | None = None,
             nombres: dict | None = None, cadera_origen: str | None = None, giro_z: float = 0.0, quitar_raiz: bool = True):
    """`nombres` = {hueso destino: hueso origen} cuando los esqueletos nombran distinto lo mismo (p. ej. el futbolista
    del juego usa «mixamorig_Hips» y el de Mixamo «mixamorig:Hips»)."""
    return _retarget(origen, accion_origen, destino, nombre, hueso_cadera, escala_pos, fotogramas,
                     nombres or {}, cadera_origen or hueso_cadera, giro_z, quitar_raiz)


def _retarget(origen, accion_origen, destino, nombre, hueso_cadera, escala_pos, fotogramas, nombres, cadera_origen,
              giro_z=0.0, quitar_raiz=True):
    """giro_z: cuánto hay que girar (en Z) el marco del origen para llevarlo al del destino cuando no miran al mismo lado
    (el futbolista del juego mira a +X y los modelos Mixamo a −Y: −90°). Sin esto, un brazo que va adelante en el origen
    iba al costado en el destino (brazos y piernas torcidos)."""
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
    o_de = lambda n: nombres.get(n, n)
    comunes = [n for n in _orden_jerarquico(destino) if o_de(n) in origen.pose.bones]
    if escala_pos is None:
        h_o = altura_hueso(origen, cadera_origen)
        h_d = altura_hueso(destino, hueso_cadera)
        escala_pos = h_d / h_o if h_o else 1.0
    f0, f1 = fotogramas or (int(accion_origen.frame_range[0]), int(accion_origen.frame_range[1]))
    rest_o = {n: _mundo_hueso(origen, o_de(n), pose=False) for n in comunes}
    rest_d = {n: _mundo_hueso(destino, n, pose=False) for n in comunes}
    for pb in destino.pose.bones:
        pb.rotation_mode = "QUATERNION"
    mw_d_inv = destino.matrix_world.inverted()
    escala_obj = destino.matrix_world.to_scale()
    cad0 = cad1 = None
    raiz_xy = []
    C = Quaternion((0, 0, 1), giro_z)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for n in comunes:
            pose_o = _mundo_hueso(origen, o_de(n), pose=True)
            # p015: se conserva la DIRECCIÓN del hueso del origen (aunque los reposos difieran, p. ej. brazos en T vs. en A);
            # del reposo sólo se toma el giro propio (torsión) alrededor del eje del hueso
            Q = rest_o[n].to_quaternion().inverted() @ rest_d[n].to_quaternion()
            tw = Quaternion((Q.w, 0.0, Q.y, 0.0))
            tw = tw.normalized() if tw.magnitude > 1e-6 else Quaternion((1, 0, 0, 0))
            qo = pose_o.to_quaternion()
            if giro_z:
                qo = C @ qo @ C.inverted()
            if any(k in n for k in ("Spine", "Neck", "Head")) and "End" not in n:
                # p017: columna, cuello y cabeza del destino tienen un reposo curvo (cabeza adelantada 19°); se aplica el giro RELATIVO al reposo
                # del origen sobre el reposo del destino (si no, la cabeza se tira hacia atrás y se separa del cuello)
                qr = rest_o[n].to_quaternion()
                if giro_z:
                    qr = C @ qr @ C.inverted()
                q_obj = (qo @ qr.inverted()) @ rest_d[n].to_quaternion()
            else:
                q_obj = qo @ tw
            if n == hueso_cadera:
                despl = (pose_o.translation - rest_o[n].translation) * escala_pos
                if giro_z:
                    despl = C @ despl
                pos = rest_d[n].translation + despl
                cad0 = pos.copy() if cad0 is None else cad0
                cad1 = pos.copy()
                if quitar_raiz:
                    raiz_xy += [pos.x - cad0.x, pos.y - cad0.y]
                    pos = Vector((cad0.x, cad0.y, pos.z))
            else:
                pos = None
            pb = destino.pose.bones[n]
            if pos is None:
                # posición = la que resulta de la cadena de padres con el reposo: se conserva la cabeza actual
                pos = destino.matrix_world @ pb.head
            # la escala MUNDO del hueso es la del objeto (p. ej. ×1,7): si se pusiera 1, el hueso quedaría a 1/1,7
            m_mundo = Matrix.LocRotScale(pos, q_obj, escala_obj)
            pb.matrix = mw_d_inv @ m_mundo
            if n != hueso_cadera:
                # sólo la cadera se traslada: si no, el resto de los huesos guarda una posición sin clave que se
                # acumula cuadro a cuadro (el Stickman definitivo terminaba a kilómetros de su esqueleto)
                pb.location = (0.0, 0.0, 0.0)
            bpy.context.view_layer.update()
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if n == hueso_cadera:
                pb.keyframe_insert("location", frame=f)
    ad_o.action = previa_o
    ad_o.use_nla = nla_o
    for pb in destino.pose.bones:
        if pb.name != hueso_cadera:
            pb.location = (0.0, 0.0, 0.0)
    if cad0 is not None:
        # cuánto avanzó la cadera en todo el clip (m, mundo, con el personaje sin girar): sirve para encadenar clips
        nueva["desplazamiento_cadera_m"] = [cad1.x - cad0.x, cad1.y - cad0.y, cad1.z - cad0.z]
    if quitar_raiz:
        nueva['raiz_xy'] = [round(v, 4) for v in raiz_xy]
    ad_d.action = None
    return nueva
