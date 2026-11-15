"""Ruedas generadas por código (los GLB de Dream Rally y los modelos de película no traen ruedas).

- `rueda_auto`: cubierta con banda de rodamiento y flancos redondeados + llanta de rayos + disco de freno, con las
  medidas de cada auto (radio y ancho del `.json` de Dream Rally, como hace `wheel_gen.gd` en el juego).
- `bogie`: bogie ferroviario (bastidor lateral, resortes, dos ejes con ruedas de acero con pestaña) para los vagones y
  la locomotora, que en sus modelos sólo tienen bloques oscuros.

Jerarquía de una rueda de auto: maza (dirige: rota en Z) → giro (rueda: rota en X) → cubierta + llanta. El caliper del
freno cuelga de la maza (dirige pero no gira). Eje de la rueda = X local.
"""
from __future__ import annotations
import math
import bmesh
import bpy
from mathutils import Vector
from estudio.blender import kit as K

_MALLAS: dict = {}


def _revolucion(nombre: str, perfil: list[tuple[float, float]], pasos: int = 48):
    """Malla de revolución alrededor del eje X. perfil: [(x, radio)…] en orden alrededor de la sección."""
    clave = (nombre, tuple(perfil), pasos)
    if clave in _MALLAS:
        return _MALLAS[clave]
    bm = bmesh.new()
    anillos = []
    for i in range(pasos):
        a = 2 * math.pi * i / pasos
        anillos.append([bm.verts.new((x, r * math.cos(a), r * math.sin(a))) for x, r in perfil])
    for i in range(pasos):
        A, B = anillos[i], anillos[(i + 1) % pasos]
        for j in range(len(perfil) - 1):
            bm.faces.new((A[j], A[j + 1], B[j + 1], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    try:                                   # cantos vivos (pestaña, flancos): suave sólo entre caras casi paralelas
        me.set_sharp_from_angle(angle=math.radians(35))
    except Exception:
        pass
    _MALLAS[clave] = me
    return me


def _mat_goma():
    m = bpy.data.materials.get("goma_cubierta")
    if m is None:
        m = K.material("goma_cubierta", (0.025, 0.025, 0.027), 0.82, ruido=0.08, escala_ruido=60, relieve=0.35)
    return m


def _mat_llanta(color=(0.55, 0.56, 0.58)):
    n = "llanta_%02x%02x%02x" % tuple(int(c * 255) for c in color)
    return bpy.data.materials.get(n) or K.material(n, color, 0.28, 1.0)


def rueda_auto(nombre: str, radio: float, ancho: float, col, lado: int = 1, color_llanta=(0.55, 0.56, 0.58), rayos: int = 6):
    """Rueda completa. lado = +1 derecha / −1 izquierda (la cara de la llanta mira hacia afuera)."""
    w2 = ancho / 2
    r_llanta = radio * 0.64
    perfil_cubierta = [(-w2 * 0.92, r_llanta), (-w2, r_llanta * 1.06), (-w2, radio * 0.9), (-w2 * 0.8, radio * 0.985),
                       (-w2 * 0.35, radio), (w2 * 0.35, radio), (w2 * 0.8, radio * 0.985), (w2, radio * 0.9),
                       (w2, r_llanta * 1.06), (w2 * 0.92, r_llanta)]
    maza = K.vacio(f"{nombre}_maza", (0, 0, 0), col)
    giro = K.vacio(f"{nombre}_giro", (0, 0, 0), col)
    giro.parent = maza
    giro["visor_sin_anim"] = True
    cub = bpy.data.objects.new(f"{nombre}_cubierta", _revolucion("cubierta_%.3f_%.3f" % (radio, ancho), perfil_cubierta, 56))
    cub.data.materials.append(_mat_goma()) if not cub.data.materials else None
    col.objects.link(cub)
    cub.parent = giro
    # llanta: aro + disco con rayos (cara hacia afuera)
    aro = bpy.data.objects.new(f"{nombre}_aro", _revolucion("aro_%.3f_%.3f" % (r_llanta, ancho),
                                                              [(-w2 * 0.9, r_llanta * 0.97), (w2 * 0.9, r_llanta * 0.97),
                                                               (w2 * 0.9, r_llanta * 1.02), (-w2 * 0.9, r_llanta * 1.02)], 48))
    ml = _mat_llanta(color_llanta)
    if not aro.data.materials:
        aro.data.materials.append(ml)
    col.objects.link(aro)
    aro.parent = giro
    x_cara = lado * w2 * 0.55
    centro = K.cilindro(f"{nombre}_centro", (x_cara, 0, 0), r_llanta * 0.28, 0.06, ml, col, lados=20, eje="X")
    centro.parent = giro
    for k in range(rayos):
        a = 2 * math.pi * k / rayos
        ry = K.caja(f"{nombre}_rayo_{k}", (x_cara, math.cos(a) * r_llanta * 0.6, math.sin(a) * r_llanta * 0.6),
                    (0.04, r_llanta * 0.16, r_llanta * 0.72), ml, col)
        ry.rotation_euler = (a - math.pi / 2, 0, 0)
        ry.parent = giro
    disco = K.cilindro(f"{nombre}_disco", (-lado * w2 * 0.05, 0, 0), r_llanta * 0.82, 0.03,
                       bpy.data.materials.get("disco_freno") or K.material("disco_freno", (0.3, 0.3, 0.31), 0.4, 1.0), col, lados=32, eje="X")
    disco.parent = giro
    cal = K.caja(f"{nombre}_caliper", (lado * w2 * 0.1, -r_llanta * 0.55, r_llanta * 0.35), (0.07, 0.16, 0.1),
                 bpy.data.materials.get("caliper") or K.material("caliper", (0.6, 0.05, 0.03), 0.4, 0.3), col)
    cal.parent = maza
    return {"maza": maza, "giro": giro, "radio": radio}


# ------------------------------------------------------------------------------------------------ ferroviario

def _mat_acero():
    return bpy.data.materials.get("acero_rueda_tren") or K.material("acero_rueda_tren", (0.13, 0.1, 0.08), 0.55, 0.8, ruido=0.35, escala_ruido=30, relieve=0.2)


def _mat_bastidor():
    return bpy.data.materials.get("bastidor_bogie") or K.material("bastidor_bogie", (0.06, 0.055, 0.05), 0.7, 0.4, ruido=0.25, escala_ruido=8)


def rueda_tren(nombre: str, col, radio: float = 0.46, trocha: float = 1.435):
    """Eje montado: dos ruedas de acero con pestaña unidas por el eje. Gira en X (local)."""
    giro = K.vacio(f"{nombre}_eje", (0, 0, 0), col)
    giro["visor_sin_anim"] = True
    perfil = [(-0.07, radio * 0.25), (-0.07, radio * 0.93), (-0.07, radio * 1.07), (-0.045, radio * 1.07),
              (-0.03, radio), (0.07, radio * 0.97), (0.07, radio * 0.25)]
    me = _revolucion("rueda_tren_%.3f" % radio, perfil, 40)
    for sx in (-1, 1):
        o = bpy.data.objects.new(f"{nombre}_rueda_{'d' if sx > 0 else 'i'}", me)
        if not me.materials:
            me.materials.append(_mat_acero())
        col.objects.link(o)
        o.location = (sx * (trocha / 2 + 0.035), 0, 0)
        o.scale = (sx, 1, 1)
        o.parent = giro
    ej = K.cilindro(f"{nombre}_barra", (0, 0, 0), 0.075, trocha + 0.3, _mat_acero(), col, lados=12, eje="X")
    ej.parent = giro
    return giro


def bogie(nombre: str, col, distancia_ejes: float = 2.6, radio: float = 0.46, trocha: float = 1.435):
    """Bogie de dos ejes. Devuelve {raiz, ejes:[giro…]}. Raíz en el centro del bogie, a la altura del eje."""
    raiz = K.vacio(f"{nombre}_bogie", (0, 0, 0), col)
    ejes = []
    for k, y in enumerate((-distancia_ejes / 2, distancia_ejes / 2)):
        g = rueda_tren(f"{nombre}_{k}", col, radio, trocha)
        g.parent = raiz
        g.location = (0, y, 0)
        ejes.append(g)
    mb = _mat_bastidor()
    for sx in (-1, 1):
        x = sx * (trocha / 2 + 0.2)
        partes = [K.caja(f"{nombre}_lat_{sx}", (x, 0, 0.05), (0.14, distancia_ejes + 0.7, 0.32), mb, col, bisel=0.02),
                  K.caja(f"{nombre}_caja_eje_{sx}a", (x, -distancia_ejes / 2, 0), (0.22, 0.32, 0.3), mb, col, bisel=0.02),
                  K.caja(f"{nombre}_caja_eje_{sx}b", (x, distancia_ejes / 2, 0), (0.22, 0.32, 0.3), mb, col, bisel=0.02)]
        for p in partes:
            p.parent = raiz
        for dy in (-0.25, 0.0, 0.25):
            r = K.cilindro(f"{nombre}_resorte_{sx}_{dy}", (x, dy, 0.33), 0.07, 0.3,
                           bpy.data.materials.get("resorte") or K.material("resorte", (0.5, 0.42, 0.1), 0.5, 0.6), col, lados=10)
            r.parent = raiz
    trav = K.caja(f"{nombre}_travesano", (0, 0, 0.32), (trocha + 0.3, 0.5, 0.26), mb, col, bisel=0.02)
    trav.parent = raiz
    return {"raiz": raiz, "ejes": ejes, "radio": radio}
