"""Secuencia 3 (v2) del Tren Fantasma — LA BATALLA DE LAS ESCOLTAS (idea libre que pidió el dueño el 15/11/2026:
«autos todoterreno y superdeportivos … que luchen entre ellos escoltas del tren contra escoltas de los protagonistas»).

Mientras el auto rampa trabaja adelante, 400 m atrás, pegado a la cola del tren, el Bisonte de Lucía y Mateo va por el
carril izquierdo con su escolta:

* LOS NUESTROS: el Vortex Aerion (superdeportivo; al volante EL ZORRO, piloto amigo con casco), el Veltor Max Pro GTR
  (superdeportivo) y el Cóndor Kodiak Raid (todoterreno).
* HALCÓN NEGRO (la retaguardia del tren): el Cóndor T6 Multicam y el Pampero Yaguareté 4x4 (todoterrenos) y el
  Kairós KL5 (superdeportivo).

1. PIT: el T6 se pone a la par del Bisonte y se le tira encima; el Vortex le mete la trompa en la cola y el T6 sale
   dando vueltas al campo (cámara lenta).
2. El Veltor pasa al Bisonte por la banquina del lado de las vías, se le pone adelante y le pega de costado al
   Pampero, que vuelca hacia el campo.
3. El KL5 viene a fondo por la banquina para cerrarle el paso al Bisonte; el Kodiak lo encierra de costado y el KL5
   se va en trompo al campo.
4. Cuando el Bisonte salta, el Vortex lo pasa a fondo por la banquina, por debajo del vuelo.

Todos se manejan con la física REAL de Dream Rally (`estudio.fisica_dr`); cada auto sigue la distancia al Bisonte y el
carril que le toca en cada instante. En el golpe el auto embestido deja la física del juego y sigue como cuerpo rígido
(`auto_rampa_s03.volar`) con la velocidad que traía más el empujón.
"""
from __future__ import annotations
import math
import bpy
from mathutils import Vector, Euler, Matrix
from estudio import fisica_dr as FD
from estudio.blender import vehiculos_dr as VD, auto_rampa_s03 as ARS, animar as AN

L_IZQ = ARS.LADO_RUTA - 1.875        # carriles (lateral a la derecha del eje de la vía)
L_DER = ARS.LADO_RUTA + 1.875
BANQ_DER = ARS.LADO_RUTA + 4.9       # banquina del lado del campo
BANQ_IZQ = ARS.LADO_RUTA - 4.9       # banquina del lado de las vías
TC1, TC2, TC3 = 9.0, 21.0, 24.3      # los tres golpes (tiempo de la escena)

# {id: (dr, bando, nombre, [(t, distancia al Bisonte en m)], [(t, lateral)])}
REPARTO = {
    "condor_t6": ("camo", "halcon", "Cóndor T6 Multicam",
                  [(-3, 30), (0, 22), (8.2, 0.4), (TC1, 0.4), (12, 0)],
                  [(-3, L_DER), (7.9, L_DER), (8.6, 8.05), (60, 8.05)]),
    "vortex": ("hyper", "nuestros", "Vortex Aerion (El Zorro)",
               [(-3, -75), (0, -62), (6.5, -10), (7.5, -8.5), (TC1, -5.6), (10.5, -9), (14, -25), (28, -34), (32.4, -1),
                (36, 30), (43, 100)],
               [(-3, L_DER), (7.0, L_DER), (8.2, 10.25), (8.8, 10.1), (TC1, 9.9), (9.4, 9.75), (10.8, L_DER),
                (26.0, L_DER), (27.4, BANQ_DER - 0.1), (36, BANQ_DER - 0.1), (38.5, L_DER), (60, L_DER)]),
    "pampero": ("pickup", "halcon", "Pampero Yaguareté 4x4",
                [(-3, 95), (0, 90), (10, 60), (17, 22), (TC2, 8.6), (24, 6)],
                [(-3, L_DER), (60, L_DER)]),
    "veltor": ("veltor_gtr", "nuestros", "Veltor Max Pro GTR",
               [(-3, -40), (0, -38), (15, -30), (18.6, -6), (19.8, 2), (20.5, 4.6), (TC2, 5.0), (22.5, 10), (26, 45),
                (30, 95), (43, 330)],
               [(-3, L_IZQ), (17.6, L_IZQ), (18.4, BANQ_IZQ + 0.3), (19.9, BANQ_IZQ + 0.3), (20.5, L_IZQ),
                (20.85, 7.7), (TC2, 8.0), (21.6, 6.8), (22.4, L_IZQ), (24.0, L_IZQ), (25.5, L_DER), (60, L_DER)]),
    "kodiak": ("kodiak", "nuestros", "Cóndor Kodiak Raid",
               [(-3, -18), (0, -15), (14, -14), (17, -12), (TC2, -8), (23.5, 0.5), (TC3, 0.8), (25.0, -4), (26.5, -16),
                (29, -24), (31, -36), (36, -110), (43, -260)],
               [(-3, L_IZQ), (14.5, L_IZQ), (16.5, L_DER), (24.0, L_DER), (TC3, 10.7), (24.8, 10.1), (25.6, L_DER),
                (60, L_DER)]),
    "kl5": ("kl5", "halcon", "Kairós KL5",
            [(-3, -130), (0, -120), (15, -85), (19, -55), (22.2, -22), (TC3, 2.0), (26, 18)],
            [(-3, L_DER), (19.0, L_DER), (20.5, BANQ_DER), (60, BANQ_DER)]),
}
# en el golpe: quién le pega a quién y el empujón (m/s: adelante, derecha, arriba · rad/s: cabeceo, rolido, guiñada)
GOLPES = {
    "condor_t6": {"t": TC1, "por": "vortex", "dv": (2.0, 3.3, 3.6), "w": (0.4, 5.2, -2.2)},
    "pampero": {"t": TC2, "por": "veltor", "dv": (1.0, 3.6, 3.2), "w": (0.8, 6.0, -1.0)},
    "kl5": {"t": TC3, "por": "kodiak", "dv": (-4.0, 3.8, 1.2), "w": (0.3, 1.6, -6.5)},
}
PARAMS_RAPIDOS = {"tractionControl": True, "tcSlip": 0.12}
DOBLE = ARS.DOBLE


def _pchip(knots):
    """Interpolación monótona por tramos (Fritsch–Carlson): pasa por los puntos, velocidad continua."""
    xs = [k[0] for k in knots]
    ys = [k[1] for k in knots]
    n = len(xs)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / d[i], m[i + 1] / d[i]
            s = a * a + b * b
            if s > 9:
                k = 3 / math.sqrt(s)
                m[i], m[i + 1] = k * a * d[i], k * b * d[i]

    def f(x):
        if x <= xs[0]:
            return ys[0] + m[0] * (x - xs[0])
        if x >= xs[-1]:
            return ys[-1] + m[-1] * (x - xs[-1])
        i = max(0, min(n - 2, next(j for j in range(n - 1) if x <= xs[j + 1])))
        h = xs[i + 1] - xs[i]
        u = (x - xs[i]) / h
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        return h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]
    return f


def _suave(knots):
    """Lateral: transición suave (smoothstep) entre puntos."""
    def f(t):
        if t <= knots[0][0]:
            return knots[0][1]
        for (a, la), (b, lb) in zip(knots, knots[1:]):
            if t <= b:
                k = (t - a) / max(1e-6, b - a)
                return la + (lb - la) * k * k * (3 - 2 * k)
        return knots[-1][1]
    return f


def referencia(via, pl, fps):
    """s(t) del Bisonte sobre la vía, medido en su física (antes de la diagonal del salto); después sigue en recta."""
    b0 = pl["b0"]
    ts, ss, s = [], [], None
    t_fin = pl["t_salto"] - 1.5
    for i in range(0, int(t_fin * fps), 3):
        q = Vector(b0["pos"][i][:2])
        s = ARS._proyectar(via, q, s if s else ARS._proyectar(via, q, via.largo / 2, via.largo / 2), radio=30)
        ts.append(i / fps)
        ss.append(s)
    v = (ss[-1] - ss[-11]) / (ts[-1] - ts[-11])
    v0 = (ss[10] - ss[0]) / (ts[10] - ts[0])

    def s_ref(t):
        if t <= ts[0]:
            return ss[0] + v0 * (t - ts[0])
        if t >= ts[-1]:
            return ss[-1] + v * (t - ts[-1])
        k = min(len(ts) - 2, int((t - ts[0]) / (ts[1] - ts[0])))
        u = (t - ts[k]) / (ts[k + 1] - ts[k])
        return ss[k] + (ss[k + 1] - ss[k]) * u
    return s_ref, v


def planificar(via, pl, p, fps):
    """Rutas y horarios de los seis autos y su simulación con la física de Dream Rally."""
    dur = p["duracion_s"]
    nf = int(round(dur * fps))
    s_ref, v_ref = referencia(via, pl, fps)
    plan = {"fps": fps, "hz": 120, "cuadros": nf, "suelo": {"tipo": "plano", "altura": 0.06, "superficie": 0},
            "vehiculos": []}
    funciones = {}
    for vid, (dr, bando, _n, dk, lk) in REPARTO.items():
        d_de, lat_de = _pchip(dk), _suave(lk)
        s_de = (lambda t, d_=d_de: s_ref(t) + d_(t))
        funciones[vid] = (s_de, lat_de)
        pts, hor, acc, t = [], [], 0.0, -3.0
        while t <= dur + 1.0 + 1e-6:
            q, _ = ARS._carril(via, s_de(t), lat_de(t))
            if pts:
                acc += math.hypot(q.x - pts[-1][0], q.y - pts[-1][1])
            pts.append([round(q.x, 3), round(q.y, 3)])
            hor.append([round(t, 3), round(acc, 3)])
            t += 0.1
        veh = {"id": vid, "dr": dr, "ruta": pts, "horario": hor, "previo_s": 1.0,
               "params": PARAMS_RAPIDOS}
        if vid == "vortex":
            veh["cabina"] = {"tipo": "hyper", "pintura": [0.75, 0.42, 0.04], "acento": [0.05, 0.05, 0.06],
                             "pilotos": [DOBLE, DOBLE]}
        plan["vehiculos"].append(veh)
    fis = FD.simular(plan)
    return {"fis": fis, "plan": plan, "s_ref": s_ref, "v_ref": v_ref, "funciones": funciones}


def _dims(dr):
    m = VD.meta_dr(dr)
    return (2 * float(m.get("hw", 1.0)) + 0.1, float(m.get("L", 4.6)), float(m.get("H", 1.4)))


def construir(via, frames, fps, c_veh, p, moviles, pl, bt) -> dict:
    """Arma los seis autos con su física; los embestidos vuelan desde el golpe. Devuelve un resumen para el registro."""
    nf = len(frames)
    fis = bt["fis"]["vehiculos"]
    rigs, trays, info = {}, {}, {"golpes": {}}
    for vid, (dr, bando, nombre, _dk, _lk) in REPARTO.items():
        reg = fis[vid]
        rig = VD.vehiculo(vid, c_veh, dr=dr)
        tray = VD.aplicar_fisica(rig, reg, frames)
        if reg.get("cabina"):
            VD.cabina(rig, reg["cabina"], c_veh, exterior=True)
        rigs[vid], trays[vid] = rig, tray
        moviles[vid] = {"tray": tray, "objeto": rig["raiz"], "rpm": reg["rpm"][:nf],
                        "anclas": {**VD.ANCLAS_VEHICULO, "interior": (0.0, 0.1, 0.95), "cabina": (0.0, -0.6, 0.95)}}
    # ------------------------------------------------------------------ los golpes: el embestido sigue como cuerpo rígido
    for vid, g in GOLPES.items():
        reg, dr = fis[vid], REPARTO[vid][0]
        i = int(round(g["t"] * fps))
        p1, p0 = Vector(reg["pos"][i]), Vector(reg["pos"][i - 1])
        vel = (p1 - p0) * fps
        R0 = reg["rot"][i]
        rumbo = math.atan2(-R0[1], R0[4])
        fwd = Vector((-math.sin(rumbo), math.cos(rumbo), 0))
        der = Vector((math.cos(rumbo), math.sin(rumbo), 0))
        dims = _dims(dr)
        hz = dims[2] / 2
        v0 = vel + fwd * g["dv"][0] + der * g["dv"][1] + Vector((0, 0, g["dv"][2]))
        w0 = der * g["w"][0] + fwd * g["w"][1] + Vector((0, 0, g["w"][2]))
        centro = p1 + Vector((0, 0, hz))
        estados = ARS.volar(dims, centro, rumbo, v0, w0, g["t"], frames, fps, piso=0.03, rest=0.2, fric=0.6)
        raiz = rigs[vid]["raiz"]
        f0 = next(k for k, e in enumerate(estados) if e is not None)
        pos, rot, prev = [], [], None
        for k in range(nf):            # antes del golpe, la física del juego; desde el golpe, el vuelo
            if k < f0:
                r = reg["rot"][k]
                R = Matrix(((r[0], r[1], r[2]), (r[3], r[4], r[5]), (r[6], r[7], r[8])))
                q = Vector(reg["pos"][k])
            else:
                c, R = estados[k]
                q = c + R @ Vector((0, 0, -hz))
            eu = R.to_euler("XYZ", prev) if prev is not None else R.to_euler("XYZ")
            pos.append(tuple(q))
            rot.append(tuple(eu))
            prev = eu
        AN.transformacion(raiz, frames, pos, rot)
        fr, pos, rot = frames[f0:], pos[f0:], rot[f0:]
        tray = trays[vid]
        for f, q, e in zip(fr, pos, rot):
            tray[f] = (Vector(q), e[2], 0.0)
        ultimo = estados[-1][0]
        s_fin = ARS._proyectar(via, ultimo.to_2d(), bt["s_ref"](g["t"]) + 30, radio=120)
        pp, tt = via.en(s_fin)
        lat_fin = (ultimo.to_2d() - pp.to_2d()).dot(Vector((tt.y, -tt.x)).normalized())
        info["golpes"][vid] = {"t": g["t"], "por": g["por"], "queda_lateral": round(lat_fin, 2),
                               "queda_s": round(s_fin, 1), "altura_max": round(max(e[0].z for e in estados[f0:]), 2)}
    # ------------------------------------------------------------------ distancias mínimas (control de la coreografía)
    cerca = {}
    ids = list(REPARTO) + ["bisonte"]
    for f in frames[::3]:
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                ea, eb = moviles.get(ids[a], {}).get("tray", {}).get(f), moviles.get(ids[b], {}).get("tray", {}).get(f)
                if not ea or not eb:
                    continue
                d = (ea[0].to_2d() - eb[0].to_2d()).length
                k = f"{ids[a]}~{ids[b]}"
                if d < cerca.get(k, (1e9,))[0]:
                    cerca[k] = (round(d, 2), round((f - 1) / fps, 2))
    info["mas_cerca"] = {k: v for k, v in sorted(cerca.items(), key=lambda kv: kv[1][0]) if v[0] < 6.0}
    return info
