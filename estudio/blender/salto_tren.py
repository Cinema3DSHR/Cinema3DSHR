"""Secuencia 3 del Tren Fantasma: el auto rampa se baja del acoplado del camión en marcha y vuela hasta la plataforma 9.

Es el ÚNICO salto del auto rampa en la película (pedido del dueño). Todo con la física real de Dream Rally
(`estudio.fisica_dr`): el auto arranca quieto sobre el acoplado que viaja por la ruta (la física corre en el marco del
acoplado, donde la cama está quieta), acelera, sube la rampa diagonal de la punta del acoplado y despega; en el aire
pasa al marco de la plataforma 9 (misma posición y velocidad en el mundo) y aterriza sobre la madera, donde la
suspensión, las gomas y el freno del juego hacen el resto. La cabina del juego viaja adentro con Lucía al volante y
Mateo al lado, movidos por la misma física (fuerzas G, golpe del aterrizaje).

Se calcula en dos pasadas: (1) el salto con el acoplado quieto, para saber dónde y cuándo cae el auto respecto del
acoplado; (2) con eso se ubica el camión en la ruta (carril y adelanto) para que caiga en la mitad de atrás de la
plataforma 9, y se simula de verdad con los dos marcos móviles.
"""
from __future__ import annotations
import math
import bpy
from mathutils import Vector
from estudio import fisica_dr as FD
from estudio.blender import kit as K, vehiculos_dr as VD, animar as AN

FBX_RAMPA = "mixamo:vehiculos_pelicula/auto_rampa/tripo_convert_c55be429-e003-45f0-afff-4bc05c1d9fdf.fbx"
# medidas tomadas sobre el modelo entregado (escala 5 m; la cuña adelante): ejes a +0,93 y −1,52 m, rueda de 0,34 m
RUEDAS_RAMPA = [{"x": sx * 0.93, "y": yy, "z": 0.34, "radio": 0.34, "ancho": 0.32, "lado": sx, "delantera": yy > 0}
                for yy in (0.93, -1.52) for sx in (-1, 1)]
# física: la del Altair GT3 RS del juego con las medidas y el peso del auto rampa (la cuña de acero carga la trompa)
PARAMS_RAMPA = {"wheelBase": 2.45, "weightFront": 0.62, "trackF": 1.72, "trackR": 1.72, "wheelRadius": 0.34,
                "rideOffset": 0.0, "comHeight": 0.5, "mass": 1650.0, "travel": 0.24}
VENTANAS_RAMPA = [{"tipo": "lado", "poly": [(-1.1, 0.95), (0.12, 0.95), (0.12, 1.18), (-1.1, 1.18)], "x_min": 0.62},
                  {"tipo": "plano", "a": (0.73, 0.9), "b": (0.13, 1.25), "semiancho": 0.62}]
# cabina del GT3 del juego dentro del auto rampa: ojos del piloto (−0,37; −0,37; 1,17) en el rig
CABINA_DESP = (0.0, -0.35, 0.13)
PILOTOS = [{"ref": "mixamo:personajes_pelicula/protagonista_femenina/tripo_convert_5669269a-5647-4c37-ad7b-71abe72fe517.fbx",
            "altura": 1.68},
           {"ref": "mixamo:personajes_pelicula/protagonista_masculino/tripo_convert_83c2a1e7-3bcc-46c6-b430-400ef54f0b81.fbx",
            "altura": 1.80}]

# acoplado (chasis portacontenedores entregado): 13 m, cama a 1,59 m, tres ejes atrás
ACOPLADO = "mixamo:modelos_pelicula/trailer_plano_camion.glb"
CAMA = 1.59
# gemelas bajo los guardabarros (el chasis tiene 1,69 m de semiancho con los guardabarros)
RUEDAS_ACOPLADO = [{"x": sx * x, "y": yy, "z": 0.52, "radio": 0.52, "ancho": 0.34, "lado": sx, "delantera": False}
                   for yy in (-4.9, -3.0, -1.25) for sx in (-1, 1) for x in (1.36, 0.98)]
# rampa en la punta, 24° hacia la izquierda (hacia las vías), de la cama a 3,0 m en 3 m: cruza 3,6 m de costado y cae casi paralelo al tren
RAMPA = {"cx": -0.35, "cy": 4.4, "ang": math.radians(24), "largo": 3.0, "ancho": 2.0, "h0": CAMA, "h1": 3.0}
INICIO_LOCAL = (0.3, -4.3, 0.0)        # ruedas traseras dentro de la cama (termina en −6,5)
_EJE = (-math.sin(RAMPA["ang"]), math.cos(RAMPA["ang"]))
# como un doble de riesgo: derecho por el centro de la cama y en los últimos metros dobla hacia la rampa
RUTA_LOCAL = [[0.3, -8.0], [0.3, -4.0], [0.3, 0.6]] + [[RAMPA["cx"] + _EJE[0] * u, RAMPA["cy"] + _EJE[1] * u]
                                                     for u in (-1.5, 0.0, 1.5, 4.0, 8.0, 14.0, 22.0)]
CUBIERTA = 0.45 + 0.55 + 0.101 * 14 * 0.82        # cubierta de una plataforma (tren.py)
LARGO_PLANO = 14.0 + 0.9


def _cajas_acoplado():
    cajas = [{"x0": -1.25, "x1": 1.25, "y0": -6.5, "y1": 6.5, "h0": CAMA, "h1": CAMA, "sup": 0}]
    cajas.append({**RAMPA, "sup": 0})               # rampa girada con pendiente continua (placa de acero)
    return cajas


def _cajas_tren():
    cajas = []
    for k in (-1, 0, 1):                               # plataformas 8, 9 y 10 (todas planas)
        y0 = k * LARGO_PLANO
        cajas.append({"x0": -1.4, "x1": 1.4, "y0": y0 - 7.0, "y1": y0 + 7.0, "h0": CUBIERTA, "h1": CUBIERTA, "sup": 2})
    return cajas


def _controles(t_go: float, t_aterriza: float):
    return [{"t0": -10, "t1": t_go, "gas": 0.0, "freno": 1.0, "freno_mano": True},   # con el de mano: el juego no pone reversa
            {"t0": t_go, "t1": t_aterriza - 0.25, "gas": 1.0},
            {"t0": t_aterriza - 0.25, "t1": t_aterriza + 0.05, "gas": 0.0},
            {"t0": t_aterriza + 0.05, "t1": t_aterriza + 2.6, "freno": 1.0, "freno_mano": True},
            {"t0": t_aterriza + 2.6, "t1": 999, "freno": 0.6}]


def prevuelo(fps: int, t_go: float) -> dict:
    """Salto con el acoplado quieto en el origen: dónde y cuándo el auto baja a la altura de la cubierta del tren."""
    nf = int((t_go + 5) * fps)
    plan = {"fps": fps, "hz": 120, "cuadros": nf, "marcos": {"remolque": {"poses": [[0.0, 0.0, 0.0]] * (nf + 2)}},
            "vehiculos": [{"id": "auto_rampa", "dr": "gt3", "params": PARAMS_RAMPA, "marco": "remolque",
                           "inicio_local": list(INICIO_LOCAL), "previo_s": 1.0, "ruta_local": RUTA_LOCAL,
                           "suelo_local": {"remolque": {"base": -30.0, "faldon": 1.0, "cajas": _cajas_acoplado()}},
                           "controles": _controles(t_go, 99.0)}]}
    reg = FD.simular(plan)["vehiculos"]["auto_rampa"]
    pos = reg["pos"]
    sale = None
    for i in range(1, len(pos)):
        if sale is None and not any(reg["contacto"][i]) and (i / fps) > t_go:
            sale = i
        if sale is not None and pos[i][2] <= CUBIERTA and pos[i][2] < pos[i - 1][2]:
            v = ((pos[i][0] - pos[i - 1][0]) * fps, (pos[i][1] - pos[i - 1][1]) * fps)
            return {"t": i / fps, "x": pos[i][0], "y": pos[i][1], "t_sale": sale / fps, "v": v,
                    "altura_max": max(p[2] for p in pos[sale:i + 1])}
    raise RuntimeError("salto: el auto no despegó del acoplado (revisar rampa y aceleración)")


def construir(via, tren, trays, frames, fps, c_veh, p, moviles) -> dict:
    t_go = p.get("t_acelera", 15.0)
    pv = prevuelo(fps, t_go)
    t_land = pv["t"]
    # carril: el centro del acoplado a D metros a la derecha de la vía, para caer sobre el eje de la plataforma
    D = -pv["x"] + 0.45
    v_tren = p["velocidad_tren"]
    v_camion = v_tren + 3.5 - pv["v"][1]               # el auto llega a la plataforma 3,5 m/s más rápido que el tren
    carro9 = tren["carros"][9]
    s9_land = p["s_cabeza_inicial"] + v_tren * t_land - carro9["offset_centro"]
    s_obj = s9_land - 3.0                              # mitad de atrás de la plataforma (adelante va el deportivo)
    s_tr0 = s_obj - pv["y"] - v_camion * t_land
    nf = len(frames)

    def pose_acoplado(t):
        pp, tt = via.en(s_tr0 + v_camion * t)
        n = Vector((tt.y, -tt.x, 0)).normalized()
        q = pp + n * D
        return (q.x, q.y, math.atan2(-tt.x, tt.y))

    poses_ac = [list(pose_acoplado((f - 1) / fps)) for f in range(1, nf + 3)]
    t9 = trays[carro9["raiz"].name]
    poses_9 = [[t9[min(f, nf)][0].x, t9[min(f, nf)][0].y, t9[min(f, nf)][1]] for f in range(1, nf + 3)]
    plan = {"fps": fps, "hz": 120, "cuadros": nf,
            "marcos": {"remolque": {"poses": poses_ac}, "carro": {"poses": poses_9}},
            "vehiculos": [{"id": "auto_rampa", "dr": "gt3", "params": PARAMS_RAMPA, "marco": "remolque",
                           "inicio_local": list(INICIO_LOCAL), "previo_s": 1.0, "muestras_por_cuadro": 4,
                           "ruta_local": RUTA_LOCAL,
                           "suelo_local": {"remolque": {"base": 0.06, "faldon": 1.0, "cajas": _cajas_acoplado()},
                                           "carro": {"base": 0.25, "faldon": 1.0, "cajas": _cajas_tren()}},
                           "cambios": [{"t": t_land - 0.12, "a": "carro"}],
                           "controles": _controles(t_go, t_land),
                           "cabina": {"tipo": "gt3", "pintura": [0.03, 0.03, 0.035], "acento": [0.8, 0.45, 0.05],
                                      "pilotos": PILOTOS}}]}
    fis = FD.simular(plan)
    reg = fis["vehiculos"]["auto_rampa"]

    # acoplado y camión (Colossus Titán T4 del juego) por la ruta
    acop = VD.vehiculo("acoplado", c_veh, ref=ACOPLADO, largo=13.0, ruedas=RUEDAS_ACOPLADO)
    pos_ac, rot_ac = [], []
    for f in frames:
        x, y, r = pose_acoplado((f - 1) / fps)
        pos_ac.append((x, y, 0.0))
        rot_ac.append((0, 0, r))
    AN.transformacion(acop["raiz"], frames, pos_ac, [(0, 0, r) for r in AN.desenrollar([q[2] for q in rot_ac])])
    for w in acop["ruedas"]:
        AN.curva(w["giro"], "rotation_euler", 0, frames, [-(v_camion * (f - 1) / fps) / w["radio"] for f in frames])
    # rampa de acero sobre la punta del acoplado (la misma geometría que pisa la física)
    acero = K.material("rampa_acero", (0.08, 0.08, 0.085), 0.45, 0.8, ruido=0.25, escala_ruido=6)
    a, L = RAMPA["ang"], RAMPA["largo"]
    alto = RAMPA["h1"] - RAMPA["h0"]
    largo_incl = math.hypot(L, alto)
    placa = K.caja("rampa_acoplado", (0, 0, 0), (RAMPA["ancho"], largo_incl, 0.06), acero, c_veh)
    placa.parent = acop["raiz"]
    placa.location = (RAMPA["cx"], RAMPA["cy"], (RAMPA["h0"] + RAMPA["h1"]) / 2)
    placa.rotation_euler = (math.atan2(alto, L), 0, a)
    for sx in (-1, 1):
        pata = K.caja(f"rampa_pata_{sx}", (0, 0, 0), (0.08, 0.08, alto), acero, c_veh)
        pata.parent = acop["raiz"]
        fin = Vector((RAMPA["cx"], RAMPA["cy"])) + Vector((-math.sin(a), math.cos(a))) * (L / 2 - 0.1) + \
            Vector((math.cos(a), math.sin(a))) * sx * (RAMPA["ancho"] / 2 - 0.1)
        pata.location = (fin.x, fin.y, RAMPA["h0"] + alto / 2)
    tray_ac = {f: (Vector(pos_ac[i]), rot_ac[i][2], v_camion) for i, f in enumerate(frames)}
    moviles["acoplado"] = {"tray": tray_ac, "anclas": {"": (0, 0, 2.0), "cama": (0, 0, CAMA), "rampa": (RAMPA["cx"], RAMPA["cy"], 2.6)}}
    camion = VD.vehiculo("camion", c_veh, dr="titan")      # el camión gris (Colossus Titán T4) tira del acoplado
    pos_cam = []
    for f in frames:
        x, y, r = pose_acoplado((f - 1) / fps)
        fwd = Vector((-math.sin(r), math.cos(r), 0))
        pos_cam.append(tuple(Vector((x, y, 0)) + fwd * 7.7))     # la punta del acoplado apoya sobre la quinta rueda
    moviles["camion"] = {"tray": VD.animar(camion, frames, pos_cam, fps), "anclas": VD.ANCLAS_VEHICULO}

    # auto rampa con su física y la cabina del juego con Lucía y Mateo
    rig = VD.vehiculo("auto_rampa", c_veh, ref=FBX_RAMPA, largo=5.0, ruedas=RUEDAS_RAMPA)
    rig["ventanas"] = VENTANAS_RAMPA
    tray = VD.aplicar_fisica(rig, reg, frames)
    VD.cabina(rig, reg["cabina"], c_veh, exterior=True, desplazamiento=CABINA_DESP)
    moviles["auto_rampa"] = {"tray": tray, "objeto": rig["raiz"], "rpm": [reg["rpm"][min(i * 4, len(reg["rpm"]) - 1)] for i in range(nf)],
                             "anclas": {**VD.ANCLAS_VEHICULO, "interior": (0.0, 0.22, 1.06), "capo": (0, 1.5, 1.05),
                                        "rueda_tra_izq": (-0.95, -1.52, 0.3), "cabina": (0.0, -0.6, 1.08)}}
    info = {"t_acelera": t_go, "t_despega": pv["t_sale"], "t_aterriza": t_land, "carril_m": D, "v_camion": v_camion,
            "altura_max": pv["altura_max"], "huella_fisica": fis.get("huella")}
    print("salto:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in info.items()})
    return info
