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


def _importar(ref: str, col, escala: float = 1.0, normalizar_largo: float | None = None, eje_largo: str = "Y", mira_y: int = -1,
              giro: float | None = None):
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
    if giro is not None:
        rz = giro                          # giro explícito (blindado y helicóptero: largo en X, trompa hacia +X → π/2)
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
             mira_y: int = -1, giro_modelo: float | None = None):
    """Arma el rig. dr = id de Dream Rally (con su .json) o ref = modelo entregado (normalizado) + largo + ruedas."""
    raiz = K.vacio(f"VEH_{nombre}", (0, 0, 0), col)
    caja = K.vacio(f"VEH_{nombre}_caja", (0, 0, 0), col)
    caja.parent = raiz
    if dr:
        meta = meta_dr(dr)
        sop, objs = _importar(f"{DR_AUTOS}/{dr}{variante}.glb", col)     # variante "_lo": misma forma, menos polígonos
        if not variante:
            for o in objs:
                if o.type == "MESH":
                    o["visor_lo"] = f"{DR_AUTOS}/{dr}_lo.glb"      # el EDITOR 3D del teléfono usa la versión liviana del juego
        ruedas = ruedas or ruedas_dr(meta)
        entre_ejes = meta.get("wheelbase", 2.6)
    else:
        meta = {}
        sop, objs = _importar(ref, col, normalizar_largo=largo, mira_y=mira_y, giro=giro_modelo)
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


def aplicar_fisica(rig: dict, reg: dict, frames: list[int]) -> dict:
    """Hornea una grabación de la física REAL de Dream Rally (`estudio.fisica_dr.simular`) en el rig: la raíz toma la
    posición y la orientación de la carrocería (cabeceo, rolido, derrape), cada rueda su altura de suspensión, su giro y
    la dirección. Las ruedas se asignan por eje y lado (0 del. izq · 1 del. der · 2 tras. izq · 3 tras. der del juego);
    con más de dos ejes, los intermedios copian el trasero. Devuelve la trayectoria {frame: (pos en el piso, rumbo, v)}."""
    from mathutils import Matrix
    if reg.get("cuadros"):                  # grabación con varias muestras por cuadro (cámara lenta): claves fraccionarias
        frames = reg["cuadros"]
    n = len(frames)
    pos = reg["pos"][:n]
    eul, prev = [], None
    for r in reg["rot"][:n]:
        m = Matrix(((r[0], r[1], r[2]), (r[3], r[4], r[5]), (r[6], r[7], r[8])))
        e = m.to_euler("XYZ", prev) if prev is not None else m.to_euler("XYZ")
        eul.append(tuple(e))
        prev = e
    AN.transformacion(rig["raiz"], frames, pos, eul)
    AN.transformacion(rig["caja"], frames, [(0, 0, 0)] * n, [(0, 0, 0)] * n)
    for w in rig["ruedas"]:
        k = (0 if w.get("delantera") else 2) + (0 if w.get("lado", 1) < 0 else 1)
        AN.curva(w["maza"], "location", 2, frames, [z[k] for z in reg["ruedas_z"][:n]])
        AN.curva(w["giro"], "rotation_euler", 0, frames, [-g[k] for g in reg["ruedas_giro"][:n]])
        if w.get("delantera"):
            AN.curva(w["maza"], "rotation_euler", 2, frames, reg["direccion"][:n])
    rig["telemetria"] = {k: reg[k][:n] for k in ("v", "rpm", "marcha", "desliz", "contacto", "entradas")}
    out = {}
    for i, f in enumerate(frames):
        if abs(f - round(f)) > 1e-3:
            continue                         # la trayectoria de cámaras y sonido va por cuadros enteros
        r = reg["rot"][i]
        rumbo = math.atan2(-r[1], r[4])       # columna Y (adelante) de la orientación
        out[int(round(f))] = (Vector(pos[i]), rumbo, abs(reg["v"][i]))
    return out


# desde afuera sólo queda lo que cabe dentro de la carrocería real: butacas, tablero, consola, piso, jaula, pilotos, volante,
# palancas y pedales (el techo, las puertas, los parantes y el capó del habitáculo del juego están hechos para la cámara de
# adentro: son un poco más grandes que el auto)
VISIBLE_DESDE_AFUERA = ("cab_seat", "cab_dash", "cab_carbon", "cab_floor", "cab_cage", "cab_pad", "cab_metal", "cab_red",
                        "cab_trim", "cab_acc")
MOVILES_CABINA = ("cab_rim", "cab_gear_lever", "cab_hb_lever", "cab_pedal_thr", "cab_pedal_brk")


def cabina(rig: dict, glb: str, col, exterior: bool = True, vidrios_claros: bool = True, desplazamiento=None) -> list:
    """Cuelga del auto la cabina de Dream Rally exportada por `estudio.fisica_dr` (habitáculo, butacas, tablero, volante,
    palancas, pedales y los dos pilotos con su animación cuadro a cuadro). Va en el mismo marco que el modelo del auto
    (la carrocería importada), así que coincide como en el juego. exterior=True esconde lo que en el juego sólo se ve con
    la cámara de adentro (techo, paneles de puertas, vidrios y capó propios del habitáculo); los vidrios del auto pasan a
    translúcidos para que se vea la tripulación (como la opción «Ver los pilotos desde las cámaras de afuera»)."""
    from estudio.blender import vidrios_dr as VI
    escena = bpy.context.scene
    objs = I.importar(glb, col)
    escena.render.fps = escena.render.fps            # el importador lee la hora del GLB con los cuadros por segundo de la escena
    def _cadena(o):
        while o is not None:
            yield o
            o = o.parent
    padre = rig["carroceria"]
    if desplazamiento is not None or not rig.get("meta"):
        # modelo de película (no es un auto del juego): la cabina del juego se acomoda con un corrimiento medido
        padre = K.vacio(f"{rig['nombre']}_cabina", (0, 0, 0), col)
        padre.parent = rig["caja"]
        padre.rotation_euler = (0, 0, math.pi)        # el GLB mira a −Y (como los autos del juego importados)
        padre.location = tuple(desplazamiento or (0, 0, 0))
    for o in objs:
        if o.parent is None:
            o.parent = padre
    for o in objs:
        if o.type != "MESH":
            continue
        o["visor_lod"] = "alto"
        nombres = [a.name for a in _cadena(o)]
        piloto = any(a.type == "ARMATURE" for a in _cadena(o)) or o.find_armature() is not None
        if o.name.startswith("Icosphere"):                 # esfera auxiliar del pilot.glb (el juego la esconde)
            ocultar = True
        elif not exterior:
            ocultar = False
        else:
            ocultar = not (piloto or o.name.startswith(VISIBLE_DESDE_AFUERA)
                           or any(n.startswith(MOVILES_CABINA) for n in nombres))
        if ocultar:
            o.hide_render = True
            o.hide_viewport = True
            o["visor_omitir"] = True
    if rig.get("meta"):
        VI.aplicar(rig["objetos"], rig["meta"], claro=vidrios_claros)
    elif rig.get("ventanas"):
        VI.aplicar_ventanas(rig["objetos"], rig["caja"], rig["ventanas"], claro=vidrios_claros)
    rig["cabina"] = objs
    return objs


def ruta_paralela(via, s0: float, s1: float, lateral, paso: float = 2.0) -> tuple[list, list]:
    """Puntos [(x, y)] de un camino paralelo a `via` (desplazado `lateral(s)` m a la derecha) y su largo acumulado,
    para el conductor de la física. Devuelve (puntos, s_via) con s_via = posición sobre la vía de cada punto."""
    pts, sv = [], []
    s = s0
    while s <= s1:
        pp, t = via.en(s)
        nrm = Vector((t.y, -t.x, 0)).normalized()
        q = pp + nrm * (lateral(s) if callable(lateral) else lateral)
        pts.append([round(q.x, 3), round(q.y, 3)])
        sv.append(s)
        s += paso
    return pts, sv


def horario_siguiendo(pts: list, s_via: list, s_via_de_t, t0: float, t1: float, dt: float = 0.25) -> list:
    """Horario [[t, s_camino]] para que el vehículo vaya a la par de un punto de la vía que avanza según s_via_de_t(t)."""
    import bisect
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    def mapa(sv):
        i = max(1, min(len(s_via) - 1, bisect.bisect_left(s_via, sv)))
        k = (sv - s_via[i - 1]) / max(1e-6, s_via[i] - s_via[i - 1])
        return acc[i - 1] + (acc[i] - acc[i - 1]) * k
    out, t = [], t0
    while t <= t1 + 1e-6:
        out.append([round(t, 3), round(mapa(s_via_de_t(t)), 4)])
        t += dt
    return out


ANCLAS_VEHICULO = {"": (0, 0, 0.8), "techo": (0, 0, 1.8), "capo": (0, 1.2, 1.25), "interior": (-0.35, -0.1, 1.15),
                   "rueda_del_izq": (-0.95, 1.4, 0.35), "rueda_tra_izq": (-0.95, -1.4, 0.35), "trasera": (0, -2.2, 1.0)}
