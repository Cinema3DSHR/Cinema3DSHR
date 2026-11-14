"""Vehículos: modelo procedural de respaldo, importación de modelos (GLB/GLTF/FBX) y animación por recorrido.

Un vehículo expone siempre la misma estructura (sea procedural o importado):
  raiz            objeto vacío que se mueve por el recorrido (origen = centro del eje trasero en el suelo, +Y adelante)
  ruedas          lista de objetos que giran sobre su eje X local
  luces           faros y luces traseras (objetos de luz)
  anclas          puntos para cámaras y ocupantes: asiento_conductor, puerta_conductor, rueda_del_izq, capot, baul…

Los modelos importados describen sus anclas en `catalogo/vehiculos.json` (nombres de nodos de ruedas, puertas,
asientos y escala). Sin ese dato se usan proporciones estándar de un sedán.

Licencias: no usar marcas, logos ni diseños protegidos de fabricantes reales sin derechos; el modelo procedural
es genérico a propósito.
"""
from __future__ import annotations
import math
from mathutils import Vector
from estudio.blender import kit as K


def sedan_procedural(nombre="auto", color=(0.05, 0.06, 0.08), col=None) -> dict:
    """Sedán genérico de líneas modernas (sin marca). Largo 4,8 m, ancho 1,9 m."""
    col = col or K.coleccion("vehiculos")
    pintura = K.material(f"pintura_{nombre}", color, 0.22, 0.85)
    goma = K.material("goma", (0.02, 0.02, 0.02), 0.85)
    llanta = K.material("llanta_aluminio", (0.6, 0.6, 0.62), 0.25, 1.0)
    vidrio = K.vidrio("vidrio_auto", (0.05, 0.06, 0.07), 0.55)
    faro = K.emisivo("faro_auto", (1.0, 0.97, 0.9), 40.0)
    trasera = K.emisivo("luz_trasera", (1.0, 0.03, 0.02), 12.0)
    cromo = K.material("cromo", (0.8, 0.8, 0.8), 0.1, 1.0)

    raiz = K.vacio(f"{nombre}_raiz", (0, 0, 0), col, "ARROWS")
    piezas = []
    cuerpo = K.caja(f"{nombre}_cuerpo", (0, 1.35, 0.74), (1.72, 4.7, 0.56), pintura, col, bisel=0.12)
    cabina = K.caja(f"{nombre}_cabina", (0, 1.1, 1.24), (1.5, 2.5, 0.48), vidrio, col, bisel=0.14)
    techo = K.caja(f"{nombre}_techo", (0, 1.0, 1.49), (1.4, 1.8, 0.05), pintura, col, bisel=0.02)
    parrilla = K.caja(f"{nombre}_parrilla", (0, 3.71, 0.66), (1.1, 0.04, 0.2), cromo, col)
    piezas += [cuerpo, cabina, techo, parrilla]
    for lado in (-1, 1):
        piezas.append(K.caja(f"{nombre}_faro_{lado}", (lado * 0.62, 3.69, 0.82), (0.36, 0.05, 0.09), faro, col))
        piezas.append(K.caja(f"{nombre}_trasera_{lado}", (lado * 0.62, -1.01, 0.88), (0.4, 0.05, 0.08), trasera, col))
    for p in piezas:
        K.padre(p, raiz)
    ruedas = []
    for i, (x, y) in enumerate(((-0.86, 0), (0.86, 0), (-0.86, 2.85), (0.86, 2.85))):
        piv = K.vacio(f"{nombre}_rueda_{i}", (x, y, 0.36), col)
        g = K.cilindro(f"{nombre}_goma_{i}", (x, y, 0.36), 0.36, 0.26, goma, col, lados=24, eje="X")
        l = K.cilindro(f"{nombre}_llanta_{i}", (x + (0.12 if x > 0 else -0.12), y, 0.36), 0.25, 0.04, llanta, col,
                       lados=12, eje="X")
        K.padre(g, piv)
        K.padre(l, piv)
        K.padre(piv, raiz)
        ruedas.append(piv)
    luces = []
    for lado in (-1, 1):
        L = K.luz(f"{nombre}_luz_faro_{lado}", "SPOT", (lado * 0.68, 3.75, 0.72), 2200, (1, 0.95, 0.85), col,
                  rot=(math.radians(85), 0, 0), angulo_spot=math.radians(50), radio=0.05)
        # el spot mira a −Z local: lo giramos para que apunte hacia +Y (adelante) y un poco abajo
        L.rotation_euler = (math.radians(-84), 0, math.radians(180))
        K.padre(L, raiz)
        luces.append(L)
        R = K.luz(f"{nombre}_luz_trasera_{lado}", "POINT", (lado * 0.7, -1.1, 0.78), 8, (1, 0.05, 0.02), col,
                  radio=0.05, sombra=False)
        K.padre(R, raiz)
        luces.append(R)
    anclas = {
        "asiento_conductor": (-0.4, 0.9, 0.9), "puerta_conductor": (-1.05, 1.2, 0.8),
        "rueda_del_izq": (-0.86, 2.85, 0.36), "rueda_tras_izq": (-0.86, 0.0, 0.36),
        "capot": (0, 3.2, 1.0), "baul": (0, -0.8, 1.0), "techo": (0, 1.0, 1.45),
    }
    return {"raiz": raiz, "ruedas": ruedas, "luces": luces, "anclas": anclas, "radio_rueda": 0.36,
            "nombre": nombre}


# ---------------------------------------------------------------------------------------------- recorridos

def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def muestrear_recorrido(puntos, paso=0.05):
    """Curva suave (Catmull-Rom) por los puntos.

    Devuelve (densa, largos, largo_en_punto): puntos densos, largo acumulado de cada uno y el largo acumulado
    en cada punto de paso original (sirve para cronometrar el recorrido).
    """
    P = [Vector(p) for p in puntos]
    P = [P[0] + (P[0] - P[1])] + P + [P[-1] + (P[-1] - P[-2])]
    densa, indices = [], []
    for i in range(1, len(P) - 2):
        indices.append(len(densa))
        n = max(8, int((P[i + 1] - P[i]).length / paso))
        for k in range(n):
            densa.append(_catmull(P[i - 1], P[i], P[i + 1], P[i + 2], k / n))
    indices.append(len(densa))
    densa.append(P[-2])
    largos = [0.0]
    for a, b in zip(densa, densa[1:]):
        largos.append(largos[-1] + (b - a).length)
    return densa, largos, [largos[i] for i in indices]


def _pchip(xs, ys):
    """Interpolación cúbica monótona (Fritsch–Carlson): avanza sin retroceder y frena suave en las paradas."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    # extremos: si el tramo es una parada, velocidad 0
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = max(k for k in range(n - 1) if xs[k] <= x)
        t = (x - xs[i]) / h[i]
        h00, h10 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t
        h01, h11 = -2 * t**3 + 3 * t**2, t**3 - t**2
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f


def _en_distancia(densa, largos, d):
    d = max(0.0, min(largos[-1], d))
    lo, hi = 0, len(largos) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if largos[mid] <= d:
            lo = mid
        else:
            hi = mid
    seg = largos[hi] - largos[lo] or 1e-6
    t = (d - largos[lo]) / seg
    pos = densa[lo].lerp(densa[hi], t)
    i0, i1 = max(0, lo - 10), min(len(densa) - 1, hi + 10)
    direc = (densa[i1] - densa[i0]).normalized()
    return pos, direc


def animar_por_recorrido(veh: dict, puntos, frame_inicio: int, tiempos, fps=30, duracion_s=None):
    """Mueve el vehículo por `puntos` (curva suave) cumpliendo `tiempos`.

    tiempos: lista de (indice_de_punto, segundo_relativo). Dos entradas seguidas con el mismo índice = parada
    (p. ej. [(0, 0), (3, 9.5), (3, 12.5), (4, 16)] → llega al punto 3 a los 9,5 s, espera hasta 12,5 s y sigue).
    El avance usa interpolación monótona: acelera y frena suave, nunca retrocede.
    Graba una clave por fotograma (posición, rumbo, giro de ruedas) y devuelve la trayectoria
    {frame: (pos, rumbo, velocidad_m_s)} para cámaras de seguimiento y para el sonido del motor.
    """
    densa, largos, en_punto = muestrear_recorrido(puntos)
    ts = [float(t) for _, t in tiempos]
    ds = [en_punto[int(i)] for i, _ in tiempos]
    # una parada se modela con dos tiempos para el mismo largo
    s_de_t = _pchip(ts, ds)
    total_s = duracion_s or ts[-1]
    raiz = veh["raiz"]
    tray = {}
    nf = int(round(total_s * fps))
    d_prev = s_de_t(0.0)
    giro = 0.0
    rumbo_prev = None
    for f in range(nf + 1):
        t = f / fps
        d = s_de_t(t)
        v = (d - d_prev) * fps
        giro += (d - d_prev) / veh["radio_rueda"]
        d_prev = d
        pos, direc = _en_distancia(densa, largos, d)
        rumbo = math.atan2(-direc.x, direc.y)  # +Y local hacia adelante
        if rumbo_prev is not None:  # continuidad del ángulo (sin saltos de 2π)
            while rumbo - rumbo_prev > math.pi:
                rumbo -= 2 * math.pi
            while rumbo - rumbo_prev < -math.pi:
                rumbo += 2 * math.pi
        rumbo_prev = rumbo
        fr = frame_inicio + f
        raiz.location = pos
        raiz.rotation_euler = (0, 0, rumbo)
        raiz.keyframe_insert("location", frame=fr)
        raiz.keyframe_insert("rotation_euler", frame=fr)
        for r in veh["ruedas"]:
            r.rotation_euler = (giro, 0, 0)
            r.keyframe_insert("rotation_euler", frame=fr, index=0)
        tray[fr] = (pos.copy(), rumbo, v)
    return tray


def punto_en_vehiculo(tray_frame, ancla_local):
    pos, rumbo, _ = tray_frame
    x, y, z = ancla_local
    c, s = math.cos(rumbo), math.sin(rumbo)
    return Vector((pos.x + x * c - y * s, pos.y + x * s + y * c, pos.z + z))
