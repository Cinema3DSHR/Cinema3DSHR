"""Tren de película: locomotora + vagones (modelos entregados por el dueño) sobre una vía, con bogies y ruedas de acero.

Cada vagón: raíz (posición = punto medio entre sus dos bogies sobre la vía, rumbo = dirección bogie trasero → delantero,
así en curva el vagón «corta» la cuerda como uno real) → carrocería (modelo GLB) + bogies (cada uno sigue la tangente
de la vía en su punto) + ejes que giran según la distancia recorrida. Los acoples unen los extremos.
La carga (autos de Dream Rally) va sobre las plataformas, con cuñas y cadenas.

Convenciones: +Y local = adelante; la vía está en el plano z = Z_RIEL (tope del riel).
"""
from __future__ import annotations
import math
import bpy
from mathutils import Vector
from estudio.blender import kit as K, ruedas as RU, animar as AN, vehiculos_dr as VD

Z_RIEL = 0.45          # tope del riel sobre el terreno (balasto + durmiente)
R_RUEDA = 0.46
TIPOS = {
    #            modelo                                             largo  eje   bogies(±y)  alto carrocería  entre ejes
    "loco":    ("mixamo:modelos_pelicula/locomotora_diesel.glb",     18.0, "Y",  5.9,        0.62,            2.9),
    "plano":   ("mixamo:modelos_pelicula/vagon_plano.glb",           14.0, "Y",  5.2,        0.55,            2.4),
    "cerrado": ("mixamo:modelos_pelicula/vagon_cerrado.glb",         13.7, "X",  5.0,        0.55,            2.4),
}
SEPARACION = 0.9       # entre topes de dos vagones


class Via:
    """Polilínea densa de la vía con largo acumulado: punto y tangente a cualquier distancia s."""

    def __init__(self, puntos: list):
        pts = [Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0)) for p in puntos]
        # muestreo cada ~1 m con Catmull-Rom para curvas suaves
        self.p = []
        for i in range(len(pts) - 1):
            p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
            n = max(2, int((p2 - p1).length))
            for k in range(n):
                t = k / n
                t2, t3 = t * t, t * t * t
                self.p.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
        self.p.append(pts[-1])
        self.s = [0.0]
        for i in range(1, len(self.p)):
            self.s.append(self.s[-1] + (self.p[i] - self.p[i - 1]).length)
        self.largo = self.s[-1]

    def en(self, s: float):
        s = max(0.0, min(self.largo, s))
        lo, hi = 0, len(self.s) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if self.s[m] <= s:
                lo = m
            else:
                hi = m
        seg = self.s[hi] - self.s[lo] or 1e-6
        t = (s - self.s[lo]) / seg
        pos = self.p[lo].lerp(self.p[hi], t)
        tan = (self.p[hi] - self.p[lo]).normalized()
        return pos, tan


def _rumbo(t: Vector) -> float:
    return math.atan2(-t.x, t.y)


def _modelo(tipo: str, col):
    ref, largo, eje, *_ = TIPOS[tipo]
    sop, objs = VD._importar(ref, col, normalizar_largo=largo, eje_largo=eje)
    return sop, objs


def construir(nombre: str, col, composicion: list[str], carga: dict | None = None, col_carga=None) -> dict:
    """composicion: ["loco", "plano", "cerrado", …] (de adelante hacia atrás). carga: {índice: [id_dream_rally, …]}.
    Los modelos se importan una vez por tipo y se duplican compartiendo la malla (poca memoria)."""
    protos = {}
    carros = []
    offset = 0.0
    for i, tipo in enumerate(composicion):
        ref, largo, eje, by, alto, ee = TIPOS[tipo]
        raiz = K.vacio(f"{nombre}_{i:02d}_{tipo}", (0, 0, 0), col)
        if tipo not in protos:
            sop, objs = _modelo(tipo, col)
            protos[tipo] = (sop, objs)
            cuerpo = sop
        else:
            psop, pobjs = protos[tipo]
            cuerpo = psop.copy()
            col.objects.link(cuerpo)
            for o in pobjs:
                if o.parent == psop:
                    c = o.copy()
                    col.objects.link(c)
                    c.parent = cuerpo
        cuerpo.parent = raiz
        cuerpo.location = (0, 0, Z_RIEL + alto)
        bogies = []
        for k, yb in enumerate((by, -by)):
            b = RU.bogie(f"{nombre}_{i:02d}_b{k}", col, ee, R_RUEDA)
            b["raiz"].parent = raiz
            b["raiz"].location = (0, yb, Z_RIEL + R_RUEDA)
            b["y"] = yb
            bogies.append(b)
        for yf in (largo / 2 + 0.2, -largo / 2 - 0.2):     # topes/acoples
            ac = K.caja(f"{nombre}_{i:02d}_acople_{'d' if yf > 0 else 't'}", (0, yf, Z_RIEL + 0.95), (0.3, 0.55, 0.22),
                        bpy.data.materials.get("bastidor_bogie"), col, bisel=0.03)
            ac.parent = raiz
        centro = offset + largo / 2
        carros.append({"indice": i, "tipo": tipo, "raiz": raiz, "cuerpo": cuerpo, "bogies": bogies, "largo": largo,
                       "offset_centro": centro, "alto": alto})
        offset += largo + SEPARACION
    # carga sobre las plataformas
    for i, ids in (carga or {}).items():
        c = carros[i]
        if c["tipo"] != "plano":
            continue
        y = c["largo"] / 2 - 0.5
        for j, id_dr in enumerate(ids):
            lo = not id_dr.endswith("!")          # "id!" = modelo completo (planos cercanos)
            id_dr = id_dr.rstrip("!")
            meta = VD.meta_dr(id_dr)
            largo_auto = meta.get("L", 4.5)
            y -= largo_auto / 2
            v = VD.vehiculo(f"{nombre}_{i:02d}_carga{j}", col_carga or col, dr=id_dr, variante="_lo" if lo else "")
            v["raiz"].parent = c["raiz"]
            v["raiz"].location = (0, y, Z_RIEL + c["alto"] + _alto_cubierta(c))
            v["raiz"].rotation_euler = (0, 0, math.pi if j % 2 else 0)
            for sx in (-1, 1):                    # cuñas de las ruedas
                for yy in (meta["arches"][0]["z"], meta["arches"][1]["z"]):
                    K.caja(f"{v['nombre']}_cuna_{sx}_{yy:.1f}", (sx * (meta["arches"][0]["x_out"] - 0.15), yy + 0.5, 0.06),
                           (0.25, 0.18, 0.12), bpy.data.materials.get("amarillo_cuna") or K.material("amarillo_cuna", (0.75, 0.55, 0.05), 0.6),
                           col_carga or col).parent = v["raiz"]
            c.setdefault("carga", []).append(v)
            y -= largo_auto / 2 + 0.6
    return {"nombre": nombre, "carros": carros, "largo": offset - SEPARACION}


def _alto_cubierta(c) -> float:
    """Altura de la cubierta de la plataforma sobre la base del modelo (medida del GLB: 0,101 del largo; la cubierta
    de madera está un poco por debajo del borde)."""
    return 0.101 * c["largo"] * 0.82


def animar(tren: dict, via: Via, frames: list[int], s_cabeza: list[float]):
    """Mueve el tren: s_cabeza[i] = distancia sobre la vía del frente de la locomotora en frames[i].
    Devuelve {id_carro: trayectoria {frame: (pos, rumbo, v)}} para cámaras."""
    trays = {}
    fps = bpy.context.scene.render.fps
    for c in tren["carros"]:
        pos, rot, rb = [], [], [[], []]
        for s0 in s_cabeza:
            sc = s0 - c["offset_centro"]
            pd, td = via.en(sc + c["bogies"][0]["y"])
            pt, tt = via.en(sc + c["bogies"][1]["y"])
            centro = (pd + pt) / 2
            d = (pd - pt).normalized()
            r = _rumbo(d)
            pos.append((centro.x, centro.y, centro.z))
            rot.append(r)
            rb[0].append(_rumbo(td) - r)
            rb[1].append(_rumbo(tt) - r)
        rot = AN.desenrollar(rot)
        AN.transformacion(c["raiz"], frames, pos, [(0, 0, r) for r in rot])
        for k, b in enumerate(c["bogies"]):
            AN.curva(b["raiz"], "rotation_euler", 2, frames, AN.desenrollar(rb[k]))
            for e in b["ejes"]:
                AN.curva(e, "rotation_euler", 0, frames, [-(s - c["offset_centro"]) / R_RUEDA for s in s_cabeza])
        vel = [0.0] + [(s_cabeza[i] - s_cabeza[i - 1]) * fps / max(1, frames[i] - frames[i - 1]) for i in range(1, len(frames))]
        vel[0] = vel[1] if len(vel) > 1 else 0.0
        trays[c["raiz"].name] = {f: (Vector(pos[i]), rot[i], vel[i]) for i, f in enumerate(frames)}
    return trays
