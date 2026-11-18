"""Pelo esculpido (estilo arcilla) para los personajes humanos de «Un sueño de a dos».

En vez de miles de pelos: una masa de pelo bien formada, como una figura modelada a mano.
  · CASCO: una malla continua sobre el cuero cabelludo (línea de nacimiento con entradas, patillas y nuca), con
    volumen variable por estilo y surcos que marcan los mechones (relieve en la geometría, no sólo en la textura).
  · MECHONES: piezas gruesas, afinadas en la punta, apoyadas sobre el casco siguiendo el peinado:
      «corto_texturizado» (él): mechones de la coronilla hacia adelante que terminan sobre la frente con las puntas
      un poco levantadas; costados cortos hacia atrás.
      «rodete_desprolijo» (ella): mechones tirantes hacia atrás, un rodete alto hecho de tres mechones enroscados y
      dos mechones sueltos que enmarcan la cara.
  · MOVIMIENTO: los mechones sueltos y el rodete tienen formas clave («vaiven_x», «vaiven_y») que mueven la punta;
    `mover()` las anima con un vaivén suave y lento (se ve también en el EDITOR 3D del teléfono).
Todo cuelga del hueso de la cabeza. Coordenadas sobre la cabeza: u (radianes, 0 = frente, + = izquierda del
personaje), v (radianes, 0 = altura de los ojos), «sobre» = altura sobre la piel en radios de la cabeza.
"""
from __future__ import annotations
import math
import random

import bpy
import numpy as np
from mathutils import Vector

from estudio.blender import kit as K
from estudio.blender import stickman as SM


def _lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def _interp(tabla, x):
    xs, ys = zip(*tabla)
    return float(np.interp(abs(x), xs, ys))


LINEA = {   # altura v del nacimiento del pelo según |u| (0 = frente, π = nuca); tercios de la cara: frente alta
    "corto_texturizado": [(0, 0.92), (0.45, 0.86), (0.75, 0.66), (1.0, 0.36), (1.18, 0.0), (1.30, -0.22),
                          (1.40, 0.18), (1.75, 0.12), (2.1, -0.2), (2.6, -0.5), (math.pi, -0.62)],
    "rodete_desprolijo": [(0, 0.90), (0.45, 0.85), (0.75, 0.66), (1.0, 0.40), (1.18, 0.05), (1.30, -0.12),
                          (1.40, 0.20), (1.75, 0.12), (2.1, -0.2), (2.6, -0.5), (math.pi, -0.62)],
}


def _volumen(estilo: str, u: float, v: float) -> float:
    """Grosor del casco (en radios de cabeza): una base fina; el volumen lo dan los mechones."""
    arriba = max(0.0, min(1.0, (v - 0.4) / 0.9))
    if estilo == "corto_texturizado":
        return 0.03 + 0.05 * arriba
    return 0.025 + 0.02 * arriba


def _surcos(estilo: str, u: float, th: float, rnd) -> float:
    """Relieve de mechones esculpidos (0–1) a lo largo de los meridianos."""
    k = 22 if estilo == "corto_texturizado" else 34
    x = 0.5 + 0.5 * math.sin(k * u + 1.7 * math.sin(2.3 * th + u * 3))
    return x ** 2.5


def _malla(nombre: str, pj: dict, verts_modelo, caras, mat, col, formas: dict | None = None):
    M = SM._modelo_a_armadura(pj)
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(M @ Vector(p)) for p in verts_modelo], [], caras)
    me.materials.append(mat)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    if formas:
        ob.shape_key_add(name="Basis")
        for k, pts in formas.items():
            sk = ob.shape_key_add(name=k)
            sk.data.foreach_set("co", np.array([tuple(M @ Vector(p)) for p in pts]).ravel())
    SM._a_hueso(ob, pj)
    sd = ob.modifiers.new("suave", "SUBSURF")
    sd.levels = 1
    sd.render_levels = 2
    return ob


def casco(pj: dict, cab, estilo: str, mat, col):
    """Masa principal del pelo sobre el cuero cabelludo."""
    rnd = random.Random(3)
    NU, NV = 96, 30
    filas = []
    for i in range(NV + 1):
        fila = []
        for j in range(NU):
            u = -math.pi + 2 * math.pi * j / NU
            v_min = _interp(LINEA[estilo], u)
            th = (i + 1) / (NV + 1)                       # 0 coronilla … 1 nacimiento
            v = math.pi / 2 - (math.pi / 2 - v_min) * th
            borde = i == NV
            h = 0.004 if borde else _volumen(estilo, u, v) * min(1.0, (1 - th) * 8 + 0.25)
            h *= 1 + 0.35 * _surcos(estilo, u, th, rnd) * (0.3 if borde else 1.0)
            fila.append(cab.punto(u, v, h))
        filas.append(fila)
    tope = cab.punto(0.0, math.pi / 2, _volumen(estilo, 0.0, 1.4))
    V = [tope] + [p for f in filas for p in f]
    F = [(0, 1 + (j + 1) % NU, 1 + j) for j in range(NU)]
    for i in range(NV):
        for j in range(NU):
            a = 1 + i * NU + j
            b = 1 + i * NU + (j + 1) % NU
            F.append((a, b, b + NU, a + NU))
    return _malla(f"PELO_{pj['id']}", pj, V, F, mat, col)


def _mechon(cab, ruta_uv, ancho: float, grueso: float, sobre0, punta_arriba=0.0, NS=14, NA=8):
    """Mechón esculpido: sección aplanada que se afina hacia la punta, sobre una ruta (u, v) de la cabeza.
    Devuelve (vértices, caras, peso de punta por vértice)."""
    us, vs = zip(*ruta_uv)
    s = np.linspace(0, 1, len(us))
    S = np.linspace(0, 1, NS)
    U = np.interp(S, s, us)
    Vv = np.interp(S, s, vs)
    P = []
    for k in range(NS):
        f = S[k]
        h = sobre0(U[k], Vv[k]) + grueso * 0.6 + punta_arriba * max(0.0, f - 0.6) ** 2 / 0.16
        P.append(np.array(cab.punto(U[k], Vv[k], h)))
    c = np.array(cab.c)
    V, F, W = [], [], []
    for k in range(NS):
        f = S[k]
        t = P[min(k + 1, NS - 1)] - P[max(k - 1, 0)]
        t /= max(1e-9, np.linalg.norm(t))
        n = P[k] - c
        n -= t * np.dot(n, t)
        n /= max(1e-9, np.linalg.norm(n))
        b = np.cross(t, n)
        w = ancho * cab.r * (1 - f ** 1.6) ** 0.8 * (0.85 + 0.15 * math.sin(f * 3)) + 1e-4
        g = grueso * cab.r * (1 - f ** 1.4) ** 0.7 + 1e-4
        for a in range(NA):
            ang = 2 * math.pi * a / NA
            V.append(P[k] + b * w * math.cos(ang) + n * g * math.sin(ang) * (1.0 if math.sin(ang) > 0 else 0.5))
            W.append(f)
    for k in range(NS - 1):
        for a in range(NA):
            i0 = k * NA + a
            i1 = k * NA + (a + 1) % NA
            F.append((i0, i1, i1 + NA, i0 + NA))
    # tapas
    ci = len(V)
    V.append(P[0])
    W.append(0.0)
    for a in range(NA):
        F.append((ci, (a + 1) % NA, a))
    ct = len(V)
    V.append(P[-1] + (P[-1] - P[-2]) * 0.4)
    W.append(1.0)
    for a in range(NA):
        F.append(((NS - 1) * NA + a, (NS - 1) * NA + (a + 1) % NA, ct))
    return V, F, W


def _juntar(piezas):
    V, F, W = [], [], []
    for v, f, w in piezas:
        b = len(V)
        V += v
        W += w
        F += [tuple(x + b for x in c) for c in f]
    return V, F, np.array(W)


def _formas_vaiven(V, W, cab, amp: float):
    """Formas clave para mover las puntas: hacia el costado y hacia adelante/atrás (más en la punta)."""
    V = np.array(V)
    W = np.asarray(W)[:, None] ** 1.6
    a = amp * cab.r
    return {"vaiven_x": list(V + W * np.array([a, 0, 0])), "vaiven_y": list(V + W * np.array([0, a, -0.25 * a]))}


def mechones_el(pj, cab, mat, col):
    """Corte corto texturizado: mechones gruesos de la coronilla hacia adelante, con el jopo levantado sobre la
    frente; costados y nuca cortos peinados hacia atrás."""
    rnd = random.Random(17)
    est = "corto_texturizado"
    sobre = lambda u, v: _volumen(est, u, v)
    piezas = []
    for k in range(30):                                       # arriba
        u0 = rnd.uniform(-0.9, 0.9)
        v0 = rnd.uniform(1.25, 1.5)
        u1 = u0 * 0.75 + rnd.uniform(-0.1, 0.1) + 0.08
        v1 = _interp(LINEA[est], u1) + rnd.uniform(-0.02, 0.06)
        mitad = ((u0 + u1) / 2, (v0 + v1) / 2 + 0.06)
        piezas.append(_mechon(cab, [(u0, v0), mitad, (u1, v1)], rnd.uniform(0.13, 0.18), rnd.uniform(0.06, 0.09),
                              sobre, punta_arriba=rnd.uniform(0.05, 0.12)))
    for k in range(40):                                       # costados y atrás
        lado = rnd.choice((-1, 1))
        u0 = lado * rnd.uniform(0.8, 2.9)
        v0 = rnd.uniform(0.9, 1.25)
        u1 = u0 + lado * rnd.uniform(0.2, 0.4)
        v1 = max(_interp(LINEA[est], u1) + 0.06, v0 - rnd.uniform(0.45, 0.8))
        piezas.append(_mechon(cab, [(u0, v0), (u1, v1)], rnd.uniform(0.11, 0.15), rnd.uniform(0.03, 0.045), sobre))
    V, F, W = _juntar(piezas)
    return _malla(f"MECHONES_{pj['id']}", pj, V, F, mat, col, _formas_vaiven(V, W, cab, 0.015))


def mechones_ella(pj, cab, mat, col):
    rnd = random.Random(29)
    est = "rodete_desprolijo"
    sobre = lambda u, v: _volumen(est, u, v) * 0.6
    piezas = []
    # tirantes hacia el rodete (de la frente y los costados hacia arriba-atrás)
    for k in range(30):
        u0 = rnd.uniform(-1.4, 1.4)
        v0 = _interp(LINEA[est], u0) + 0.03
        ruta = [(u0, v0), (u0 * 1.4, (v0 + 1.3) / 2 + 0.05), (math.copysign(2.6, u0 + 1e-6), 1.3)]
        piezas.append(_mechon(cab, ruta, rnd.uniform(0.10, 0.14), 0.03, sobre, NS=16))
    for k in range(12):                                      # desde la nuca, hacia arriba
        u0 = rnd.uniform(2.2, 4.1)
        u0 = u0 if u0 <= math.pi else u0 - 2 * math.pi
        ruta = [(u0, -0.45), (u0 * 0.97, 0.3), (math.copysign(2.9, u0), 1.2)]
        piezas.append(_mechon(cab, ruta, 0.09, 0.02, sobre, NS=16))
    V, F, W = _juntar(piezas)
    ob1 = _malla(f"MECHONES_{pj['id']}", pj, V, F, mat, col)
    # rodete: tres mechones gruesos enroscados alrededor de un eje que sale de la coronilla hacia atrás
    c = np.array(cab.c)
    base = np.array(cab.punto(math.pi, 1.2, 0.05))
    eje = base - c
    eje /= np.linalg.norm(eje)
    e1 = np.cross(eje, [1.0, 0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(eje, e1)
    piezas = []
    r = cab.r
    for m in range(3):
        fase = m * 2 * math.pi / 3
        P = []
        for k in range(40):
            f = k / 39
            a = fase + f * 2 * math.pi * 1.25
            rad = r * (0.20 - 0.07 * f) * (1 + 0.08 * math.sin(a * 2 + m))
            alto = r * (0.05 + 0.20 * f + 0.03 * math.sin(a * 1.5))
            P.append(base + eje * alto + (e1 * math.cos(a) + e2 * math.sin(a)) * rad)
        piezas.append(_tubo_afinado(P, 0.085 * r, 0.04 * r, c))
    # mechón suelto que se escapa del rodete
    P = [base + eje * r * 0.25 + e1 * r * 0.1 + (e1 * 0.15 + e2 * 0.1 - eje * 0.05 * k) * r * k * 0.12
         for k in range(10)]
    piezas.append(_tubo_afinado(P, 0.025 * r, 0.006 * r, c))
    V, F, W = _juntar(piezas)
    ob2 = _malla(f"RODETE_{pj['id']}", pj, V, F, mat, col, _formas_vaiven(V, W, cab, 0.04))
    # mechones que enmarcan la cara: de la sien hasta la altura del mentón, con una onda en S
    piezas = []
    for lado in (-1, 1):
        for k in range(3):
            u0 = lado * (0.78 + 0.06 * k)
            ruta = [(u0, 0.62 + 0.03 * k), (lado * (0.90 + 0.04 * k), 0.25), (lado * (0.84 + 0.05 * k), -0.25),
                    (lado * (0.92 + 0.05 * k), -0.80 - 0.05 * k)]
            piezas.append(_mechon(cab, ruta, 0.05 - 0.01 * k, 0.012, lambda u, v: 0.05 + 0.03 * k, NS=18))
    V, F, W = _juntar(piezas)
    ob3 = _malla(f"MECHONES_CARA_{pj['id']}", pj, V, F, mat, col, _formas_vaiven(V, W, cab, 0.05))
    return [ob1, ob2, ob3]


def _tubo_afinado(P, r0, r1, centro, NA=10):
    P = [np.asarray(p, dtype=float) for p in P]
    V, F, W = [], [], []
    n = len(P)
    for k in range(n):
        f = k / (n - 1)
        t = P[min(k + 1, n - 1)] - P[max(k - 1, 0)]
        t /= max(1e-9, np.linalg.norm(t))
        a = np.cross(t, [0, 0, 1.0])
        if np.linalg.norm(a) < 1e-6:
            a = np.cross(t, [1.0, 0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(t, a)
        rr = r0 + (r1 - r0) * f ** 1.3
        for j in range(NA):
            ang = 2 * math.pi * j / NA
            V.append(P[k] + (a * math.cos(ang) + b * math.sin(ang) * 0.75) * rr)
            W.append(f)
    for k in range(n - 1):
        for j in range(NA):
            i0 = k * NA + j
            i1 = k * NA + (j + 1) % NA
            F.append((i0, i1, i1 + NA, i0 + NA))
    return V, F, W


def material_pelo(pid: str, color) -> bpy.types.Material:
    """Pelo «de arcilla»: color con variación suave, brillo satinado y vetas finas a lo largo."""
    mat = K.material(f"pelo_{pid}", _lin(color), 0.42, ruido=0.18, escala_ruido=60.0, relieve=0.12)
    b = mat.node_tree.nodes["Principled BSDF"]
    for k, v in (("Sheen Weight", 0.35), ("Sheen Roughness", 0.35), ("Coat Weight", 0.25), ("Coat Roughness", 0.3)):
        try:
            b.inputs[k].default_value = v
        except KeyError:
            pass
    return mat


def construir(pj: dict, estilo: str, color) -> dict:
    cab = pj["cabeza"]
    col = pj["coleccion"]
    mat = material_pelo(pj["id"], color)
    obs = [casco(pj, cab, estilo, mat, col)]
    obs += [mechones_el(pj, cab, mat, col)] if estilo == "corto_texturizado" else mechones_ella(pj, cab, mat, col)
    pj["pelo"] = obs
    return {"objetos": obs}


def mover(pj: dict, fps: int, nf: int, intensidad: float = 1.0):
    """Vaivén suave y lento de los mechones sueltos (formas «vaiven_x/y»), distinto en cada mechón."""
    rnd = random.Random(sum(map(ord, pj["id"])))
    t = np.arange(nf) / fps
    for ob in pj.get("pelo", []):
        sk = ob.data.shape_keys
        if sk is None:
            continue
        sk.animation_data_create()
        act = bpy.data.actions.new(f"vaiven_{ob.name}")
        sk.animation_data.action = act
        for nombre in ("vaiven_x", "vaiven_y"):
            if nombre not in sk.key_blocks:
                continue
            f1, f2 = rnd.uniform(0.25, 0.45), rnd.uniform(0.6, 0.9)
            val = intensidad * (0.6 * np.sin(2 * math.pi * f1 * t + rnd.uniform(0, 6)) +
                                0.3 * np.sin(2 * math.pi * f2 * t + rnd.uniform(0, 6)))
            kb = sk.key_blocks[nombre]
            kb.slider_min, kb.slider_max = -1.0, 1.0
            fc = act.fcurve_ensure_for_datablock(sk, f'key_blocks["{nombre}"].value')
            idx = np.arange(0, nf, 3)
            fc.keyframe_points.add(len(idx))
            co = np.empty(len(idx) * 2)
            co[0::2] = idx + 1
            co[1::2] = val[idx]
            fc.keyframe_points.foreach_set("co", co)
            fc.update()
