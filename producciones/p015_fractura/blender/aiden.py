"""p015 · Aiden: se incorpora desde la biblioteca de clips ya retargeteados y se anima por NLA con tiempo animado
(strip_time por cuadro → cámara lenta, congelado y retroceso exactos)."""
import json
import math
import bpy
from mathutils import Vector

import os
BIB = os.environ.get("FRACTURA_BIB", "/home/user/fractura/aiden_clips.blend")
INFO = {}


def cargar(col):
    """Trae objetos y acciones de la biblioteca. Devuelve la armadura de Aiden."""
    global INFO
    with bpy.data.libraries.load(BIB, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
        dst.actions = [n for n in src.actions]
    for o in dst.objects:
        if o is not None:
            col.objects.link(o)
    try:
        INFO = json.load(open(BIB.replace(".blend", ".json")))
    except Exception:
        INFO = {}
    arm = bpy.data.objects["Aiden_armadura"]
    raiz = bpy.data.objects["PJ_aiden"]
    raiz.animation_data_clear()
    for a in bpy.data.actions:
        a.use_fake_user = True
    return arm


def accion(nombre):
    return bpy.data.actions.get(f"aiden_{nombre}")


def largo(nombre):
    a = accion(nombre)
    return a.frame_range[1] - a.frame_range[0]


def segmento(arm, nombre, f0, f1, mapa=None, ciclo=False, track=None):
    """Reproduce el clip entre los cuadros f0..f1. mapa(f) → cuadro de la acción (0-based desde su inicio); por omisión 1:1 a 30 fps.
    ciclo=True repite el clip. El strip no extrapola, así que fuera de f0..f1 no actúa."""
    a = accion(nombre)
    ad = arm.animation_data or arm.animation_data_create()
    tr = track or ad.nla_tracks.new()
    tr.name = f"{nombre}@{f0}"
    st = tr.strips.new(nombre, int(f0), a)
    st.extrapolation = "NOTHING"
    st.blend_type = "REPLACE"
    st.use_animated_time = True
    st.use_animated_influence = False
    a0, a1 = a.frame_range
    n = max(1.0, a1 - a0)
    st.frame_end = float(f1) + 0.0
    mp = mapa or (lambda f: f - f0)
    for f in range(int(f0), int(f1) + 1):
        u = mp(f)
        if ciclo:
            u = u % n
        else:
            u = max(0.0, min(n, u))
        st.strip_time = a0 + u
        st.keyframe_insert("strip_time", frame=f)
    ac = ad.action
    return st


def constante(idb):
    from bpy_extras import anim_utils
    ad = idb.animation_data
    if ad and ad.action:
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in (cb.fcurves if cb else []):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def colocar(arm, claves, interp="LINEAR"):
    """claves = [(cuadro, (x,y,z), yaw)] posición y giro del objeto armadura."""
    raiz = bpy.data.objects["PJ_aiden"]       # raíz del personaje (escala 1,9355); yaw=π → mira hacia +Y, yaw=0 → hacia −Y
    raiz.rotation_mode = "XYZ"
    for f, p, yaw in claves:
        raiz.location = p
        raiz.rotation_euler = (0, 0, yaw)
        raiz.keyframe_insert("location", frame=int(f))
        raiz.keyframe_insert("rotation_euler", frame=int(f))
    if interp != "LINEAR":
        constante(raiz)


def vacio(col, arm, hueso, nombre, frac=None):
    """Vacío que acompaña a un hueso (cadera, cabeza…): objetivo para las cámaras. Con `frac` (0–1) se coloca a esa fracción del largo del hueso
    (p. ej. 0,45 en «Head» cae en el centro de la cara)."""
    e = bpy.data.objects.new(nombre, None)
    col.objects.link(e)
    if frac is None:
        c = e.constraints.new("COPY_LOCATION")
        c.target = arm
        c.subtarget = hueso
    else:
        e.parent = arm
        e.parent_type = "BONE"
        e.parent_bone = hueso
        e.location = (0.0, -(1.0 - frac) * arm.data.bones[hueso].length, 0.0)
    return e
