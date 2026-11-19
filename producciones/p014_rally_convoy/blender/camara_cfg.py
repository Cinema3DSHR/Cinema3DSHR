"""p014 · cámara de la dirección de Godot: zoom de lente por cuadro y cortes secos (interpolación en escalón)."""
import math
import bpy


def camara(s, D):
    cam = bpy.data.objects["Camara"]
    s.camera = cam
    cd = cam.data
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36.0
    cd.clip_start = 0.08
    cd.clip_end = 3000.0
    fovs = D["fov_horizontal_por_cuadro"]
    for f, fov in enumerate(fovs):
        cd.lens = (cd.sensor_width * 0.5) / math.tan(math.radians(max(10.0, min(120.0, fov))) * 0.5)
        cd.keyframe_insert("lens", frame=f)
    # cortes de cámara: interpolación en escalón en la posición y la rotación (sin barridos entre planos)
    ad = cam.animation_data
    from bpy_extras import anim_utils
    n_fc = 0
    if ad and ad.action:
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in (cb.fcurves if cb else []):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
            n_fc += 1
    if cd.animation_data and cd.animation_data.action:
        for cap in cd.animation_data.action.layers:
            for ti in cap.strips:
                for cb2 in ti.channelbags:
                    for fc in cb2.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "CONSTANT"
    return n_fc


