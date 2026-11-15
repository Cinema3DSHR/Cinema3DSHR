"""Vehículos de película: autos de Dream Rally (con sus medidas originales) y modelos entregados por el dueño.

Rig: raíz (posición y rumbo en el piso; +Y local = adelante) → caja (suspensión: cabeceo, rolido y rebote) → carrocería.
Las ruedas cuelgan de la raíz (no de la caja: la suspensión mueve la carrocería sobre ellas), con maza (dirección) y
giro (rodadura). Los modelos importados miran a −Y: se giran 180° dentro de la caja.

Dinámica (`animar`): a partir de la trayectoria (posición por cuadro) se calcula velocidad, aceleración longitudinal y
lateral, rumbo y curvatura → giro de ruedas = distancia/radio, dirección = atan(entre_ejes·curvatura), y la
suspensión como un resorte-amortiguador de 2.º orden excitado por las aceleraciones (transferencia de peso) + baches
del camino. Opcional por cuadro: ángulo de derrape (la carrocería apunta fuera de la dirección de avance).

Medidas de Dream Rally (`godot/game/models/cars/<id>.json`): R (radio), arches[{z, x_out}] (ejes y trocha), a/b, lift.
En Blender la rueda va en (±(x_out − ancho/2), −z, R): comprobado contra los arcos de la carrocería.
"""
from __future__ import annotations
import json
import math
import bpy
from mathutils import Vector
from estudio import config
from estudio.blender import kit as K, importar as I, ruedas as RU, animar as AN

DR_AUTOS = "rally:godot/game/models/cars"


def _importar(ref: str, col, escala: float = 1.0, normalizar_largo: float | None = None, eje_largo: str = "Y", mira_y: int = -1):
    objs = I.importar(ref, col)
    raices = [o for o in objs if o.parent is None]
    soporte = bpy.data.objects.new("carroceria_" + ref.split("/")[-1].split(".")[0], None)
    col.objects.link(soporte)
    for o in raices:
        o.parent = soporte
    if normalizar_largo:
        escala = normalizar_largo        # los modelos de Tripo vienen normalizados a 1 m en su lado más largo
    soporte.scale = (escala, escala, escala)
    rz = math.pi if mira_y < 0 else 0.0   # casi todos miran a −Y → girar para que miren a +Y (el auto rampa ya mira a +Y)
    if eje_largo == "X":
        rz = -math.pi / 2                  # vagón cerrado: largo en X
    soporte.rotation_euler = (0, 0, rz)
    for o in objs:
        if o.type == "MESH":
            o["visor_lod"] = "alto"
    return soporte, objs


def meta_dr(id_dr: str) -> dict:
    return json.loads(config.resolver(f"{DR_AUTOS}/{id_dr}.json").read_text())


def ruedas_dr(meta: dict, ancho: float = 0.27) -> list[dict]:
    out = []
    for a in meta["arches"]:
        delantera = a["z"] > 0
        for lado in (-1, 1):
            out.append({"x": lado * (a["x_out"] - ancho / 2 - 0.02), "y": a["z"], "z": meta["R"], "radio": meta["R"],
                        "ancho": ancho, "lado": lado, "delantera": delantera})
    return out


def vehiculo(nombre: str, col, *, dr: str | None = None, variante: str = "", ref: str | None = None, largo: float | None = None,
             ruedas: list[dict] | None = None, color_llanta=(0.55, 0.56, 0.58), material_carroceria=None, alto_caja: float = 0.0,
             mira_y: int = -1):
    """Arma el rig. dr = id de Dream Rally (con su .json) o ref = modelo entregado (normalizado) + largo + ruedas."""
    raiz = K.vacio(f"VEH_{nombre}", (0, 0, 0), col)
    caja = K.vacio(f"VEH_{nombre}_caja", (0, 0, 0), col)
    caja.parent = raiz
    if dr:
        meta = meta_dr(dr)
        sop, objs = _importar(f"{DR_AUTOS}/{dr}{variante}.glb", col)     # variante "_lo": misma forma, menos polígonos
        ruedas = ruedas or ruedas_dr(meta)
        entre_ejes = meta.get("wheelbase", 2.6)
    else:
        meta = {}
        sop, objs = _importar(ref, col, normalizar_largo=largo, mira_y=mira_y)
        sop.location.z = alto_caja
        ys = sorted({r["y"] for r in ruedas})
        entre_ejes = (ys[-1] - ys[0]) if len(ys) > 1 else 2.6
    sop.parent = caja
    if material_carroceria is not None:
        for o in objs:
            if o.type == "MESH":
                o.data.materials.clear()
                o.data.materials.append(material_carroceria)
    rs = []
    for i, r in enumerate(ruedas):
        w = RU.rueda_auto(f"{nombre}_r{i}", r["radio"], r["ancho"], col, r["lado"], color_llanta)
        w["maza"].parent = raiz
        w["maza"].location = (r["x"], r["y"], r["z"])
        w.update(r)
        rs.append(w)
    return {"nombre": nombre, "raiz": raiz, "caja": caja, "carroceria": sop, "ruedas": rs, "meta": meta,
            "entre_ejes": entre_ejes, "objetos": objs}


def animar(rig: dict, frames: list[int], posiciones: list, fps: int = 30, derrape=None, baches: float = 0.006,
           rigidez_hz: float = 1.4, amortiguacion: float = 0.45, cabeceo_por_g: float = 0.045, rolido_por_g: float = 0.07):
    """Hornea el movimiento. posiciones: [(x, y, z)] del centro del vehículo en el piso, uno por cuadro de `frames`.
    derrape: [ángulo_rad] por cuadro (positivo = cola hacia afuera a la izquierda). Devuelve la trayectoria
    {frame: (pos, rumbo, v)} para cámaras y sonido."""
    n = len(frames)
    P = [Vector(p) for p in posiciones]
    dt = 1.0 / fps
    vel = [Vector((0, 0, 0))] * n
    for i in range(n):
        a, b = max(0, i - 1), min(n - 1, i + 1)
        vel[i] = (P[b] - P[a]) / ((b - a) * dt) if b > a else Vector((0, 0, 0))
    rumbo = []
    for i in range(n):
        v = vel[i]
        if v.xy.length > 0.3:
            rumbo.append(math.atan2(-v.x, v.y))
        else:
            rumbo.append(rumbo[-1] if rumbo else 0.0)
    rumbo = AN.desenrollar(rumbo)
    rapidez = [v.xy.length for v in vel]
    # aceleraciones longitudinal y lateral (m/s²)
    a_lon, a_lat, curv = [], [], []
    for i in range(n):
        a, b = max(0, i - 1), min(n - 1, i + 1)
        dv = (rapidez[b] - rapidez[a]) / max(1, b - a) / dt
        dr = (rumbo[b] - rumbo[a]) / max(1, b - a) / dt
        a_lon.append(dv)
        a_lat.append(rapidez[i] * dr)
        curv.append(dr / rapidez[i] if rapidez[i] > 0.5 else 0.0)
    # suspensión: resorte-amortiguador excitado por la transferencia de peso
    w0 = 2 * math.pi * rigidez_hz
    def filtro(x_obj):
        y, yd, out = 0.0, 0.0, []
        for xo in x_obj:
            for _ in range(4):
                h = dt / 4
                ydd = w0 * w0 * (xo - y) - 2 * amortiguacion * w0 * yd
                yd += ydd * h
                y += yd * h
            out.append(y)
        return out
    g = 9.81
    cabeceo = filtro([-cabeceo_por_g * al / g for al in a_lon])     # frena → nariz abajo
    rolido = filtro([rolido_por_g * al / g for al in a_lat])         # curva → se inclina hacia afuera
    import random
    rnd = random.Random(hash(rig["nombre"]) & 0xFFFF)
    fases = [rnd.uniform(0, 6.28) for _ in range(3)]
    dist = [0.0]
    for i in range(1, n):
        dist.append(dist[-1] + (P[i] - P[i - 1]).xy.length)
    rebote = [baches * (math.sin(d * 1.7 + fases[0]) + 0.6 * math.sin(d * 4.1 + fases[1]) + 0.3 * math.sin(d * 9.3 + fases[2])) * min(1.0, rapidez[i] / 8)
              for i, d in enumerate(dist)]
    der = derrape or [0.0] * n
    AN.transformacion(rig["raiz"], frames, [(p.x, p.y, p.z) for p in P], [(0, 0, r + d) for r, d in zip(rumbo, der)])
    AN.transformacion(rig["caja"], frames, [(0, 0, z) for z in rebote], [(c, r, 0) for c, r in zip(cabeceo, rolido)])
    ee = rig["entre_ejes"]
    for w in rig["ruedas"]:
        giro = [d / w["radio"] for d in dist]
        AN.curva(w["giro"], "rotation_euler", 0, frames, [-g_ for g_ in giro])
        if w.get("delantera"):
            ang = [max(-0.6, min(0.6, math.atan(ee * c) + (d * 1.2 if abs(d) > 0.05 else 0))) for c, d in zip(curv, der)]
            AN.curva(w["maza"], "rotation_euler", 2, frames, ang)
    return {f: (P[i], rumbo[i] + der[i], rapidez[i]) for i, f in enumerate(frames)}


ANCLAS_VEHICULO = {"": (0, 0, 0.8), "techo": (0, 0, 1.8), "capo": (0, 1.2, 1.25), "interior": (-0.35, -0.1, 1.15),
                   "rueda_del_izq": (-0.95, 1.4, 0.35), "rueda_tra_izq": (-0.95, -1.4, 0.35), "trasera": (0, -2.2, 1.0)}
