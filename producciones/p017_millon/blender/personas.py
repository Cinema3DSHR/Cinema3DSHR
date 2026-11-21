"""p017 · personas animadas (Aiden y Kate) a partir de las bibliotecas retargeteadas (/home/user/millon/personas_<nombre>.blend).
Orientación (verificada): con la raíz PJ en yaw=π el personaje mira hacia +Y y camina hacia +Y; con yaw=0 mira hacia −Y. `mirar(p, dx, dy)` gira la raíz para que su frente mire hacia (dx, dy)."""
import math
import os
import bpy
from mathutils import Vector, Euler

BIB = os.environ.get("MILLON_BIB", "/home/user/millon")
_cache = {}


class Persona:
    def __init__(self, nombre, raiz, arm, objs):
        self.nombre = nombre
        self.raiz = raiz
        self.arm = arm
        self.objs = objs
        self.pistas = []

    def mirar(self, dx, dy):
        """Yaw de la raíz para que el frente mire hacia (dx, dy): el frente es (sin yaw, −cos yaw) ⇒ yaw=π mira a +Y, yaw=0 a −Y."""
        return math.atan2(dx, -dy)


def cargar(nombre, col):
    """Trae del blend de la biblioteca todos los objetos y acciones del personaje y los deja en `col` (visibles)."""
    ruta = os.path.join(BIB, f"personas_{nombre}.blend")
    antes = set(bpy.data.objects.keys())
    with bpy.data.libraries.load(ruta, link=False) as (df, dt):
        dt.objects = list(df.objects)
        dt.actions = list(df.actions)
    nuevos = [o for o in dt.objects if o is not None]
    for o in nuevos:
        col.objects.link(o)
    for a in dt.actions:
        if a is not None:
            a.use_fake_user = True
    raiz = next(o for o in nuevos if o.name.startswith("PJ_") and o.parent is None)
    arm = next(o for o in nuevos if o.type == "ARMATURE")
    raiz.animation_data_clear()
    raiz.rotation_mode = "XYZ"
    return Persona(nombre, raiz, arm, nuevos)


def clonar(base, nombre_nuevo, col, tinte_traje=None):
    """Copia independiente (propia armadura y NLA) del personaje: para fiestas y multitudes. Las mallas comparten datos."""
    mapa = {}
    for o in base.objs:
        n = o.copy()
        if o.type == "ARMATURE":
            n.data = o.data.copy()
        n.name = o.name + "_" + nombre_nuevo
        n.animation_data_clear()
        col.objects.link(n)
        mapa[o] = n
    for o, n in mapa.items():
        if o.parent in mapa:
            n.parent = mapa[o.parent]
        for m in n.modifiers:
            if m.type == "ARMATURE" and m.object in mapa:
                m.object = mapa[m.object]
    raiz = mapa[base.raiz]
    arm = mapa[base.arm]
    return Persona(base.nombre + "_" + nombre_nuevo, raiz, arm, list(mapa.values()))


def accion(p, clip):
    return bpy.data.actions.get(f"{p.nombre.split('_')[0]}_{clip}")


def clip(p, nombre_clip, f0, f1, mapa=None, ciclo=False, mezcla=0):
    """Reproduce un clip del personaje entre los cuadros f0 y f1 por NLA con tiempo animado (cámara lenta, retroceso y ciclos exactos)."""
    a = accion(p, nombre_clip)
    ad = p.arm.animation_data or p.arm.animation_data_create()
    tr = ad.nla_tracks.new()
    tr.name = f"{nombre_clip}@{f0}"
    st = tr.strips.new(nombre_clip, int(f0) - int(mezcla), a)
    st.extrapolation = "NOTHING"
    st.blend_type = "REPLACE"
    if mezcla:
        st.blend_in = float(mezcla)          # fundido con el clip anterior (sin salto de pose)
    st.use_animated_time = True
    a0, a1 = a.frame_range
    n = max(1.0, a1 - a0)
    st.frame_end = float(f1)
    mp = mapa or (lambda f: f - f0)
    for f in range(int(f0) - int(mezcla), int(f1) + 1):
        u = mp(f)
        u = (u % n) if ciclo else max(0.0, min(n, u))
        st.strip_time = a0 + u
        st.keyframe_insert("strip_time", frame=f)
    return st


def colocar(p, claves):
    """claves = [(cuadro, (x,y,z), yaw)]: posición y giro de la raíz."""
    p.raiz.rotation_mode = "XYZ"
    ult = getattr(p, "_ult", None)
    if ult is not None and claves and claves[0][0] - 1 > ult[0]:
        # mantener la posición anterior hasta justo antes del nuevo tramo (sin deslizarse entre escenas lejanas)
        f = int(claves[0][0]) - 1
        p.raiz.location, p.raiz.rotation_euler = ult[1], (0, 0, ult[2])
        p.raiz.keyframe_insert("location", frame=f)
        p.raiz.keyframe_insert("rotation_euler", frame=f)
    if claves:
        p._ult = (int(claves[-1][0]), tuple(claves[-1][1]), claves[-1][2])
    for f, pos, yaw in claves:
        p.raiz.location = pos
        p.raiz.rotation_euler = (0, 0, yaw)
        p.raiz.keyframe_insert("location", frame=int(f))
        p.raiz.keyframe_insert("rotation_euler", frame=int(f))


def ocultar_fuera(p, lejos=(0, 0, -800), frames=()):
    """Mientras la persona no está en escena espera lejos (la visibilidad por colección no se anima)."""
    for f in frames:
        p.raiz.location = lejos
        p.raiz.keyframe_insert("location", frame=int(f))


def vacio(p, hueso, nombre, col, frac=None):
    """Vacío que acompaña a un hueso (objetivo de cámara). Con `frac` queda a esa fracción del largo del hueso (0,5 en Head ≈ centro de la cara)."""
    e = bpy.data.objects.new(nombre, None)
    col.objects.link(e)
    if frac is None:
        c = e.constraints.new("COPY_LOCATION")
        c.target = p.arm
        c.subtarget = hueso
    else:
        e.parent = p.arm
        e.parent_type = "BONE"
        e.parent_bone = hueso
        e.location = (0.0, -(1.0 - frac) * p.arm.data.bones[hueso].length, 0.0)
    return e
