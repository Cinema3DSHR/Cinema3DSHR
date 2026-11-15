"""Secuencia 3 (v2) del Tren Fantasma — EL AUTO RAMPA. Coreografía del dueño, toda con la física de Dream Rally:

1. El Colossus Titán T4 (el camión gris) tira del acoplado por el carril derecho; arriba, el auto rampa con un doble
   de riesgo (piloto del juego con casco). El doble lo baja MARCHA ATRÁS por la cola del acoplado en movimiento: es el
   único salto del auto rampa. Cae a la ruta (física en el marco del acoplado → en el aire pasa al marco del mundo).
2. Acelera, pasa al camión por el carril izquierdo y alcanza a la escolta de Halcón Negro: la cuña levanta una moto y
   después al blindado, que salen volando y dando vueltas (cuerpo rígido con gravedad, rebotes y fricción).
3. Trompo de 180° con freno de mano y se planta de frente, con la cuña mirando hacia atrás.
4. Lucía viene con el Bisonte XR (Mateo al lado: la cabina del juego con los dos), sube por la cuña y el techo del
   auto rampa, vuela por encima de la ruta y cae en el último vagón (el 20, libre); frena contra los autos amarrados
   del vagón 19. Mateo se baja para robarse un auto del tren.

`planificar` corre las simulaciones que no dependen del tren y decide dónde tiene que estar el tren (para que el
vagón 20 pase justo bajo el Bisonte); `construir` hace la última (el aterrizaje en el vagón) y arma todo en Blender.
"""
from __future__ import annotations
import math
import random
import bpy
from mathutils import Vector, Matrix, Euler
from estudio import fisica_dr as FD
from estudio.blender import kit as K, vehiculos_dr as VD, animar as AN, salto_tren as ST

CAMA = ST.CAMA
CUBIERTA = ST.CUBIERTA
V_CAMION = 20.0
V_ESCOLTA = 20.0
LADO_RUTA = 7.6                   # ruta pegada a las vías: carril izquierdo a 5,7 m del eje de la vía
T_REVERSA = 3.0                   # el doble mete reversa
VUELTA = 9.5                      # segundos después de caer a la ruta empieza el trompo
PERFIL_RAMPA = [(2.55, 0.07), (2.4, 0.29), (2.0, 0.47), (1.6, 0.66), (1.2, 0.83), (0.8, 0.92), (0.4, 1.11), (0.0, 1.31),
                (-0.4, 1.43), (-0.8, 1.44), (-1.25, 1.42)]   # lomo del auto rampa (y, z) en su marco: cuña → techo
DOBLE = {"ref": "rally:godot/game/models/pilot.glb", "altura": 1.78}
PILOTOS_BISONTE = ST.PILOTOS                  # Lucía al volante, Mateo de acompañante
PARAMS_ESCALA = {}


def _carril(via, s, lateral):
    pp, tt = via.en(s)
    n = Vector((tt.y, -tt.x, 0)).normalized()
    q = pp + n * lateral
    return q, math.atan2(-tt.x, tt.y)


def _ruta(via, s0, s1, lateral_de_s, paso=2.0):
    pts, s = [], s0
    while s <= s1:
        q, _ = _carril(via, s, lateral_de_s(s))
        pts.append([round(q.x, 3), round(q.y, 3)])
        s += paso
    return pts


def _proyectar(via, q2, s_aprox, radio=150.0):
    mejor, dmin, s = s_aprox, 1e18, s_aprox - radio
    while s <= s_aprox + radio:
        d = (via.en(s)[0].to_2d() - q2).length_squared
        if d < dmin:
            dmin, mejor = d, s
        s += 0.5
    return mejor


def _largos(pts):
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return acc


def _horario(acc_inicio, t0, v0, tramos, t_fin, dt=0.1):
    """s(t) desde s=acc_inicio en t0 a velocidad v0, siguiendo tramos [(t, v)] (lineal)."""
    out, t, s = [], t0 - 2.0, acc_inicio - v0 * 2.0
    def vel(tt):
        if tt <= tramos[0][0]:
            return v0 + (tramos[0][1] - v0) * max(0.0, (tt - t0)) / max(1e-6, tramos[0][0] - t0)
        for (a, va), (b, vb) in zip(tramos, tramos[1:]):
            if tt <= b:
                return va + (vb - va) * (tt - a) / max(1e-6, b - a)
        return tramos[-1][1]
    while t <= t_fin:
        out.append([round(t, 3), round(s, 3)])
        s += (v0 if t < t0 else vel(t)) * dt
        t += dt
    return out


def _cajas_lomo(pose):
    """El lomo del auto rampa quieto como piso para el Bisonte: rampas giradas entre los puntos del perfil."""
    x0, y0, r = pose
    adelante = Vector((-math.sin(r), math.cos(r)))
    cajas = []
    for (ya, za), (yb, zb) in zip(PERFIL_RAMPA, PERFIL_RAMPA[1:]):
        c = Vector((x0, y0)) + adelante * ((ya + yb) / 2)
        cajas.append({"cx": c.x, "cy": c.y, "ang": r + math.pi, "largo": abs(ya - yb), "ancho": 2.0,
                      "h0": za, "h1": zb, "sup": 0})
    return cajas


def _pose_final(reg, i=-1):
    p, R = reg["pos"][i], reg["rot"][i]
    return (p[0], p[1], math.atan2(-R[1], R[4]))


def planificar(via, p, fps):
    """Simulaciones que no dependen del tren. Devuelve todo lo necesario y la cabeza del tren al empezar."""
    dur = p["duracion_s"]
    nf = int(round(dur * fps))
    S0 = p.get("s_camion", 900.0)                          # posición del acoplado (sobre la vía) en t = 0
    L_der, L_izq = LADO_RUTA + 1.875, LADO_RUTA - 1.875

    def pose_acoplado(t):
        q, r = _carril(via, S0 + V_CAMION * t, L_der)
        return [q.x, q.y, r]

    poses_ac = [pose_acoplado((f - 1) / fps) for f in range(1, nf + 3)]
    mundo = [[0.0, 0.0, 0.0]] * (nf + 2)

    # 1) el auto rampa: reversa por la cola del acoplado, cae a la ruta, pasa al camión y alcanza a la escolta
    controles_ar = [{"t0": -10, "t1": T_REVERSA, "gas": 0.0, "freno": 1.0, "freno_mano": True}]
    plan0 = {"fps": fps, "hz": 120, "cuadros": nf, "marcos": {"remolque": {"poses": poses_ac}, "mundo": {"poses": mundo}},
             "vehiculos": [{"id": "ar", "dr": "gt3", "params": ST.PARAMS_RAMPA, "marco": "remolque",
                            "inicio_local": [0.2, -1.8, 0.0], "previo_s": 1.0,
                            "suelo_local": {"remolque": {"base": 0.06, "faldon": 1.0, "cajas": ST._cajas_acoplado()[:1]}},
                            "controles": controles_ar + [{"t0": T_REVERSA, "t1": 999, "gas": 0.0, "freno": 1.0}]}]}
    r0 = FD.simular(plan0)["vehiculos"]["ar"]
    t_aire = next(i / fps for i in range(1, nf) if i / fps > T_REVERSA and r0["pos"][i][2] < CAMA - 0.25)
    # posición sobre la ruta al caer: el cambio de carril (para pasar al camión) empieza 25 m después
    pw = Vector(r0["pos"][int(t_aire * fps) + 6][:2])
    s_cae = _proyectar(via, pw, S0 + V_CAMION * t_aire)
    ruta_ar = _ruta(via, s_cae - 40, s_cae + 1100, lambda s: L_der if s < s_cae + 25 else (L_izq if s > s_cae + 80 else
                                                                                       L_der + (L_izq - L_der) * (s - s_cae - 25) / 55))
    acc = _largos(ruta_ar)
    k = min(range(len(ruta_ar)), key=lambda i: (Vector(ruta_ar[i]) - pw).length)
    t_ruta = t_aire + 0.3
    v_caida = V_CAMION - 6.0
    t_vuelta = t_ruta + VUELTA
    hor = _horario(acc[k], t_ruta, v_caida, [(t_ruta + 1.0, v_caida), (t_ruta + 5.0, 27.0), (t_vuelta, 27.0)], dur + 2)
    controles = controles_ar + [
        {"t0": T_REVERSA, "t1": t_aire, "gas": 0.0, "freno": 1.0},                       # reversa (el juego la pone)
        {"t0": t_aire, "t1": t_ruta, "gas": 0.0, "freno": 0.0},
        # trompo de 180° hacia la derecha (se abre a la banquina, lejos del tren): el doble patea la cola con el de mano y
        # lleva el rumbo hasta la contramano; apunta 21° más allá porque el auto sigue rotando cuando frena (medido)
        {"t0": t_vuelta, "t1": t_vuelta + 0.45, "gas": 0.3, "freno": 0.0, "volante": 1.0, "freno_mano": True},
        {"t0": t_vuelta + 0.45, "t1": t_vuelta + 4.0, "rumbo_deg": 125.0, "gas": 0.35, "mano_hasta_deg": 40, "anticipa_s": 0.4},
        {"t0": t_vuelta + 4.0, "t1": t_vuelta + 4.6, "gas": 0.0, "freno": 1.0, "volante": 0.0},
        {"t0": t_vuelta + 4.6 + 7.6, "t1": 999, "gas": 0.0, "freno": 1.0, "freno_mano": True}]   # plantado
    # después del trompo VUELVE: a contramano por el carril pegado a las vías y se planta alineado, con la cuña mirando
    # hacia atrás (al Bisonte que viene)
    t_ret = t_vuelta + 4.6
    t_planta = t_ret + 7.0
    vuelta_pts = _ruta(via, s_cae + 120, s_cae + 900, lambda s: L_izq)[::-1]        # carril izquierdo, a contramano
    plan_ar = {"fps": fps, "hz": 120, "cuadros": nf,
               "marcos": {"remolque": {"poses": poses_ac}, "mundo": {"poses": mundo}},
               "vehiculos": [{"id": "auto_rampa", "dr": "gt3", "params": {**ST.PARAMS_RAMPA, "tractionControl": True, "tcSlip": 0.12},
                              "marco": "remolque", "gas_max": 0.6,     # un doble dosifica: el auto rampa es de tracción trasera
                              "inicio_local": [0.2, -1.8, 0.0], "previo_s": 1.0, "muestras_por_cuadro": 4,
                              "suelo_local": {"remolque": {"base": 0.06, "faldon": 1.0, "cajas": ST._cajas_acoplado()[:1]},
                                              "mundo": {"base": 0.06}},
                              "cambios": [{"t": t_aire + 0.05, "a": "mundo"}],
                              "rutas_local": {"mundo": {"ruta": ruta_ar, "horario": hor}},
                              "rutas_extra": [{"t0": t_ret, "marco": "mundo", "ruta": vuelta_pts,
                                               "horario_rel": [[-1, 0], [0, 0], [1.5, 4.0], [3.0, 14.0], [5.0, 28.0],
                                                               [6.3, 34.0], [7.0, 35.5], [30, 35.5]]}],
                              "controles": controles,
                              "cabina": {"tipo": "gt3", "pintura": [0.03, 0.03, 0.035], "acento": [0.8, 0.45, 0.05],
                                         "pilotos": [DOBLE, DOBLE]}}]}
    fis_ar = FD.simular(plan_ar)
    ar = fis_ar["vehiculos"]["auto_rampa"]
    n4 = len(ar["pos"])
    pose_ar = _pose_final(ar)
    t_quieto = next(((ar["cuadros"][i] - 1) / fps for i in range(n4) if (ar["cuadros"][i] - 1) / fps > t_vuelta + 4.6 + 3.0
                     and abs(ar["v"][i]) < 0.2), t_vuelta + 12.5)

    # 2) el Bisonte: viene por el carril izquierdo, cruza en diagonal sobre el lomo del auto rampa (hacia las vías)
    t_salto = t_quieto + 3.0
    _, r_ruta = _carril(via, _proyectar(via, Vector(pose_ar[:2]), S0 + 300, radio=600), 0.0)
    adelante = Vector((-math.sin(r_ruta), math.cos(r_ruta)))                                   # sentido de la ruta
    hacia_via = Vector((adelante.y, -adelante.x)) * -1.0                                    # izquierda del salto
    ang = math.radians(p.get("angulo_salto_deg", 4.0))
    dir_b = (adelante * math.cos(ang) + hacia_via * math.sin(ang)).normalized()
    centro = Vector(pose_ar[:2])
    v_b = p.get("v_bisonte", 23.0)
    atras = int(v_b * (t_salto + 1.5) + 30)
    ruta_b = [list(centro + dir_b * d) for d in range(-atras, 160, 2)]
    s_rampa = atras - 2.6                                   # la punta de la cuña
    hor_b = [[round(t, 3), round(s_rampa + v_b * (t - t_salto), 3)] for t in [x * 0.25 - 2 for x in range(int((dur + 4) * 4))]]
    s_ini = s_rampa - v_b * (t_salto + 1.0)                 # dónde tiene que estar en t = −1 (arranca con el horario)
    q_ini = centro + dir_b * (s_ini - atras)
    inicio_b = [q_ini.x, q_ini.y, math.atan2(-dir_b.x, dir_b.y)]
    suelo_b = {"base": 0.06, "faldon": 1.0, "cajas": _cajas_lomo(pose_ar)}
    plan_b0 = {"fps": fps, "hz": 120, "cuadros": nf, "marcos": {"mundo": {"poses": mundo}},
               "vehiculos": [{"id": "bisonte", "dr": "genesis", "marco": "mundo",
                              "inicio_local": inicio_b, "previo_s": 1.0,
                              "suelo_local": {"mundo": suelo_b},
                              "rutas_local": {"mundo": {"ruta": ruta_b, "horario": hor_b}},
                              "controles": [{"t0": t_salto + 0.3, "t1": 999, "gas": 0.0, "freno": 0.0}]}]}
    b0 = FD.simular(plan_b0)["vehiculos"]["bisonte"]
    sale = next(i for i in range(int(t_salto * fps) - 10, nf) if not any(b0["contacto"][i]))
    i_land = next(i for i in range(sale + 3, nf) if b0["pos"][i][2] <= CUBIERTA + 0.05 and b0["pos"][i][2] < b0["pos"][i - 1][2])
    t_land = i_land / fps
    land = Vector(b0["pos"][i_land][:2])
    # el tren: el centro del vagón 20 tiene que pasar por ahí (un poco adelante: frena contra el 19)
    return {"S0": S0, "poses_ac": poses_ac, "fis_ar": fis_ar, "plan_ar": plan_ar, "t_aire": t_aire, "t_ruta": t_ruta,
            "t_vuelta": t_vuelta, "t_quieto": t_quieto, "pose_ar": pose_ar, "t_salto": t_salto, "t_land": t_land,
            "land": land, "ruta_b": ruta_b, "hor_b": hor_b, "suelo_b": suelo_b, "b0": b0, "sale": sale / fps,
            "inicio_b": inicio_b,
            "altura_max": max(q[2] for q in b0["pos"][sale:i_land + 1]), "ruta_ar": ruta_ar}


def offsets_tren(composicion):
    """Distancia de la cabeza al centro de cada vagón (como tren.construir)."""
    from estudio.blender import tren as TR
    out, off = [], 0.0
    for tipo in composicion:
        largo = TR.TIPOS[tipo][1]
        out.append(off + largo / 2)
        off += largo + TR.SEPARACION
    return out


def s_cabeza_para(via, pl, composicion, v_tren):
    """Cabeza del tren en t=0 para que el vagón 20 pase bajo el Bisonte al aterrizar: cae 3 m detrás del centro del
    vagón (adelante del Bisonte quedan 10 m de cubierta y después los autos amarrados del vagón 19)."""
    s_land = _proyectar(via, pl["land"], via.largo / 2, radio=via.largo / 2)
    return s_land + 3.0 + offsets_tren(composicion)[20] - v_tren * pl["t_land"]


# ------------------------------------------------------------------------------------------- vuelo de enemigos

def volar(dims, p0, r0, v0, w0, t0, frames, fps, piso=0.06, rest=0.25, fric=0.55, semilla=1):
    """Cuerpo rígido (caja) lanzado por la cuña: gravedad, rebotes y fricción contra el piso en las 8 esquinas, a 240 Hz.
    p0 posición del centro, r0 rumbo, v0 velocidad (m/s), w0 velocidad angular (rad/s, ejes del mundo).
    Devuelve [(pos, euler)] por cuadro desde t0 (antes de t0: None)."""
    hx, hy, hz = dims[0] / 2, dims[1] / 2, dims[2] / 2
    m = 1.0
    Ib = Vector(((dims[1] ** 2 + dims[2] ** 2) / 12, (dims[0] ** 2 + dims[2] ** 2) / 12, (dims[0] ** 2 + dims[1] ** 2) / 12))
    pos, vel, w = Vector(p0), Vector(v0), Vector(w0)
    R = Euler((0, 0, r0)).to_matrix()
    esquinas = [Vector((sx * hx, sy * hy, sz * hz)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    h = 1.0 / 240
    out, t = [], t0
    def inv_I(Rm):
        Iw = Rm @ Matrix.Diagonal(Ib) @ Rm.transposed()
        return Iw.inverted()
    for f in frames:
        tf = (f - 1) / fps
        if tf < t0:
            out.append(None)
            continue
        while t < tf:
            vel.z -= 9.81 * h
            Ii = inv_I(R)
            for c in esquinas:
                r = R @ c
                pc = pos + r
                if pc.z < piso:
                    vc = vel + w.cross(r)
                    n = Vector((0, 0, 1))
                    vn = vc.dot(n)
                    if vn < 0:
                        k = (Ii @ r.cross(n)).cross(r).dot(n) + 1 / m
                        jn = -(1 + rest) * vn / k
                        vt = vc - n * vn
                        jt = min(fric * jn, vt.length / k) if vt.length > 1e-6 else 0.0
                        imp = n * jn - (vt.normalized() * jt if vt.length > 1e-6 else Vector())
                        vel += imp / m
                        w += Ii @ r.cross(imp)
                    pos.z += (piso - pc.z) * 0.5
            pos += vel * h
            ang = w.length * h
            if ang > 1e-9:
                R = Matrix.Rotation(ang, 3, w.normalized()) @ R
                R = R.to_quaternion().normalized().to_matrix()
            w *= 0.9995
            t += h
        out.append((pos.copy(), R.copy()))
    return out


def _hornear(obj, frames, estados, antes):
    """Pone el vuelo en el objeto; antes del lanzamiento sigue `antes(f)` → (pos, rumbo)."""
    pos, rot, prev = [], [], None
    for f, e in zip(frames, estados):
        if e is None:
            q, r = antes(f)
            eu = Euler((0, 0, r))
            pos.append(tuple(q))
        else:
            pos.append(tuple(e[0]))
            eu = e[1].to_euler("XYZ", prev) if prev is not None else e[1].to_euler("XYZ")
        rot.append(tuple(eu))
        prev = eu
    AN.transformacion(obj, frames, pos, rot)


def construir(via, tren, trays, frames, fps, c_veh, p, moviles, pl) -> dict:
    nf = len(frames)
    # ---------------------------------------------------- acoplado y Titán por el carril derecho
    acop = VD.vehiculo("acoplado", c_veh, ref=ST.ACOPLADO, largo=13.0, ruedas=ST.RUEDAS_ACOPLADO)
    pos_ac = [(q[0], q[1], 0.0) for q in pl["poses_ac"][:nf]]
    AN.transformacion(acop["raiz"], frames, pos_ac, [(0, 0, r) for r in AN.desenrollar([q[2] for q in pl["poses_ac"][:nf]])])
    for w in acop["ruedas"]:
        AN.curva(w["giro"], "rotation_euler", 0, frames, [-(V_CAMION * (f - 1) / fps) / w["radio"] for f in frames])
    moviles["acoplado"] = {"tray": {f: (Vector(pos_ac[i]), pl["poses_ac"][i][2], V_CAMION) for i, f in enumerate(frames)},
                           "anclas": {"": (0, 0, 2.0), "cama": (0, 0, CAMA), "cola": (0, -6.5, CAMA)}}
    camion = VD.vehiculo("camion", c_veh, dr="titan")
    pos_cam = []
    for i in range(nf):
        x, y, r = pl["poses_ac"][i]
        pos_cam.append(tuple(Vector((x, y, 0)) + Vector((-math.sin(r), math.cos(r), 0)) * 7.7))
    moviles["camion"] = {"tray": VD.animar(camion, frames, pos_cam, fps), "anclas": VD.ANCLAS_VEHICULO}

    # ---------------------------------------------------- auto rampa (doble de riesgo)
    ar = pl["fis_ar"]["vehiculos"]["auto_rampa"]
    rig = VD.vehiculo("auto_rampa", c_veh, ref=ST.FBX_RAMPA, largo=5.0, ruedas=ST.RUEDAS_RAMPA)
    rig["ventanas"] = ST.VENTANAS_RAMPA
    tray_ar = VD.aplicar_fisica(rig, ar, frames)
    VD.cabina(rig, ar["cabina"], c_veh, exterior=True, desplazamiento=ST.CABINA_DESP)
    moviles["auto_rampa"] = {"tray": tray_ar, "objeto": rig["raiz"],
                             "rpm": [ar["rpm"][min(i * 4, len(ar["rpm"]) - 1)] for i in range(nf)],
                             "anclas": {**VD.ANCLAS_VEHICULO, "interior": (0.0, 0.22, 1.06), "capo": (0, 1.5, 1.05),
                                        "cabina": (0.0, -0.6, 1.08), "rueda_tra_izq": (-0.95, -1.52, 0.3),
                                        "cuna": (0, 2.2, 0.4)}}

    # ---------------------------------------------------- escolta: una moto y un blindado salen volando por la cuña
    t_c = pl["t_vuelta"] - 2.2                               # el auto rampa llega a la escolta antes del trompo
    i_c = int(round(t_c * fps))
    p_c = tray_ar[min(i_c + 1, nf)][0]
    r_c = tray_ar[min(i_c + 1, nf)][1]
    v_ar = tray_ar[min(i_c + 1, nf)][2]
    fwd = Vector((-math.sin(r_c), math.cos(r_c), 0))
    rnd = random.Random(7)
    enemigos = {}
    for nombre, ref, largo, dims, adelanto, dt_choque, w_extra in (
            ("moto_1", None, 2.0, (0.7, 2.0, 1.1), 3.4, -1.3, (2.5, -6.0, 1.5)),
            ("escolta_1", "mixamo:modelos_pelicula/vehiculo_blindado_policial.glb", 5.6, (2.2, 5.6, 2.3), 3.9, 0.0,
             (4.5, -3.5, 0.8))):
        tc = t_c + dt_choque
        # posición del enemigo en el choque: justo delante de la cuña; antes iba a V_ESCOLTA por el carril
        q_choque = p_c + fwd * (adelanto + (dt_choque * v_ar))
        def antes(f, qc=q_choque, tc_=tc):
            t = (f - 1) / fps
            return (qc + fwd * (V_ESCOLTA * (t - tc_))), r_c
        v_rel = max(6.0, v_ar - V_ESCOLTA)
        v0 = fwd * (V_ESCOLTA + v_rel * 0.6) + Vector((0, 0, v_rel * 0.75 + 3.0))
        w0 = Vector((w_extra[0] * math.cos(r_c), w_extra[0] * math.sin(r_c), 0)) + Vector((0, 0, w_extra[2]))
        w0 += Vector((math.cos(r_c + math.pi / 2), math.sin(r_c + math.pi / 2), 0)) * w_extra[1]
        p0 = q_choque + Vector((0, 0, dims[2] / 2 + 0.06))
        estados = volar(dims, p0, r_c, v0, w0, tc, frames, fps, semilla=rnd.randint(0, 99))
        if ref:
            ruedas_b = [{"x": sx * 0.95, "y": yy, "z": 0.46, "radio": 0.46, "ancho": 0.34, "lado": sx, "delantera": yy > 0}
                        for yy in (1.72, -1.55) for sx in (-1, 1)]
            rig_e = VD.vehiculo(nombre, c_veh, ref=ref, largo=largo, ruedas=ruedas_b, alto_caja=0.18, giro_modelo=math.pi / 2)
            raiz = rig_e["raiz"]
            off = -(dims[2] / 2 + 0.06)
        else:
            raiz = K.vacio(f"VEH_{nombre}", (0, 0, 0), c_veh)
            from estudio.escenarios import tren_fantasma as TF
            m = K.instancia(f"{nombre}_modelo", TF._sh3d("sc_yamaha_yzr_r6", TF.PROTOS), (0, 0, 0), 0.0, 1.0, c_veh)
            m.parent = raiz
            off = -(dims[2] / 2 + 0.06)
        # el centro del cuerpo rígido es el centro de la caja; el origen del modelo está en el piso
        hijo = K.vacio(f"{nombre}_centro", (0, 0, 0), c_veh)
        for o in list(c_veh.objects):
            if o.parent == raiz and o is not hijo:
                o.parent = hijo
        hijo.parent = raiz
        hijo.location = (0, 0, off)
        _hornear(raiz, frames, estados, lambda f, a=antes, d=dims: (a(f)[0] + Vector((0, 0, d[2] / 2 + 0.06)), a(f)[1]))
        enemigos[nombre] = {"t": tc, "tray": {f: ((e[0] if e else antes(f)[0]), r_c, 0.0) for f, e in zip(frames, estados)}}
        moviles[nombre] = {"tray": enemigos[nombre]["tray"], "anclas": {"": (0, 0, 0.0)}}

    # ---------------------------------------------------- Bisonte con Lucía y Mateo: sube por el auto rampa al tren
    carro20 = tren["carros"][20]
    t20 = trays[carro20["raiz"].name]
    poses_20 = [[t20[min(f, nf)][0].x, t20[min(f, nf)][0].y, t20[min(f, nf)][1]] for f in range(1, nf + 3)]
    cajas20 = [{"x0": -1.4, "x1": 1.4, "y0": -7.0, "y1": 7.0, "h0": CUBIERTA, "h1": CUBIERTA, "sup": 2},
               {"x0": -1.4, "x1": 1.4, "y0": ST.LARGO_PLANO - 7.0, "y1": ST.LARGO_PLANO + 7.0, "h0": CUBIERTA, "h1": CUBIERTA, "sup": 2}]
    t_land = pl["t_land"]
    plan_b = {"fps": fps, "hz": 120, "cuadros": nf,
              "marcos": {"mundo": {"poses": [[0.0, 0.0, 0.0]] * (nf + 2)}, "carro": {"poses": poses_20}},
              "vehiculos": [{"id": "bisonte", "dr": "genesis", "marco": "mundo", "muestras_por_cuadro": 4,
                             "inicio_local": pl["inicio_b"], "previo_s": 1.0,
                             "suelo_local": {"mundo": pl["suelo_b"], "carro": {"base": 0.25, "faldon": 1.0, "cajas": cajas20}},
                             "rutas_local": {"mundo": {"ruta": pl["ruta_b"], "horario": pl["hor_b"]}},
                             "cambios": [{"t": t_land - 0.15, "a": "carro"}],
                             "controles": [{"t0": pl["t_salto"] + 0.3, "t1": t_land + 0.05, "gas": 0.0, "freno": 0.0},
                                           {"t0": t_land + 0.05, "t1": 999, "gas": 0.0, "freno": 1.0, "freno_mano": True,
                                            "volante": 0.0}],
                             "cabina": {"tipo": "genesis", "pintura": [0.05, 0.05, 0.055], "pilotos": PILOTOS_BISONTE}}]}
    fis_b = FD.simular(plan_b)
    rb = fis_b["vehiculos"]["bisonte"]
    rig_b = VD.vehiculo("bisonte", c_veh, dr="genesis")
    tray_b = VD.aplicar_fisica(rig_b, rb, frames)
    VD.cabina(rig_b, rb["cabina"], c_veh, exterior=True)
    moviles["bisonte"] = {"tray": tray_b, "objeto": rig_b["raiz"],
                          "rpm": [rb["rpm"][min(i * 4, len(rb["rpm"]) - 1)] for i in range(nf)],
                          "anclas": {**VD.ANCLAS_VEHICULO, "interior": (0.0, 0.55, 1.42), "cabina": (0.0, -0.45, 1.3),
                                     "capo": (0, 1.9, 1.3), "rueda_del_izq": (-1.05, 1.53, 0.45)}}
    # dónde quedó el Bisonte sobre el vagón 20 (marco del vagón) para que Mateo se baje
    i_fin = len(rb["pos"]) - 1
    f_fin = frames[-1]
    pv, rv = poses_20[f_fin - 1], poses_20[f_fin - 1][2]
    d = Vector(rb["pos"][i_fin][:2]) - Vector(pv[:2])
    local = Vector((d.x * math.cos(rv) + d.y * math.sin(rv), -d.x * math.sin(rv) + d.y * math.cos(rv)))
    rumbo_b = math.atan2(-rb["rot"][i_fin][1], rb["rot"][i_fin][4]) - rv
    info = {"t_reversa": T_REVERSA, "t_cae_ruta": pl["t_aire"], "t_choque": t_c, "t_vuelta": pl["t_vuelta"],
            "t_quieto": pl["t_quieto"], "t_salto": pl["t_salto"], "t_aterriza": t_land, "altura_max_bisonte": pl["altura_max"],
            "bisonte_en_vagon": [round(local.x, 2), round(local.y, 2), round(math.degrees(rumbo_b), 1)],
            "enemigos": {k: round(v["t"], 2) for k, v in enemigos.items()}}
    # Mateo se baja: el acompañante de la cabina desaparece y aparece el Mateo que camina sobre el vagón
    t_baja = round(t_land + 3.2, 2)
    f_baja = int(round(t_baja * fps)) + 1
    for o in rig_b.get("cabina", []):
        if o.type == "MESH" and o.find_armature() and o.name.startswith("tripo_node_83c2a1e7"):
            for fr, v in ((1, False), (f_baja, True)):
                o.hide_render = o.hide_viewport = v
                o.keyframe_insert("hide_render", frame=fr)
                o.keyframe_insert("hide_viewport", frame=fr)
    rb_rad = math.radians(rumbo_b)
    der = Vector((math.cos(rb_rad), math.sin(rb_rad)))          # derecha del Bisonte (lado del acompañante)
    puerta = local + der * 1.35 + Vector((-math.sin(rb_rad), math.cos(rb_rad))) * -0.2
    info["personajes"] = [{
        "id": "mateo", "modelo": "pelicula:mateo", "sobre": "tren_20_plano", "aparece_s": t_baja,
        "acciones": [{"clip": "mixamo:animaciones/sentado_manejar/Exiting_Car.fbx", "inicio_s": t_baja,
                      "pos": [round(puerta.x, 3), round(puerta.y, 3), round(CUBIERTA, 3)], "mirando_deg": round(rumbo_b + 90, 1)},
                     {"clip": "mixamo:packs/Pro_Rifle_Pack/walk_forward.fbx", "inicio_s": round(t_baja + 4.0, 2),
                      "repetir": 3, "mirando_deg": 90, "giro_s": 0.6, "encadenar": True}]}]
    info["t_mateo_baja"] = t_baja
    print("auto_rampa_s03:", {k: v for k, v in info.items() if k != "personajes"})
    return info
