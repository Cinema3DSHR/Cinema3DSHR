"""Pelota de fútbol con la física de Free Kick Swipe (FISICA_E_IA.md, valores reales del juego).

La pelota nunca se "conduce": sale de un IMPULSO (patada) y después la mueve sólo la integración física:
gravedad, arrastre cuadrático, efecto Magnus, botes con restitución, rodadura y la red del arco.
Se simula a 240 Hz y se graba una clave por fotograma (posición + giro), así el resultado es determinista.

Ejes de Blender: X = largo de la cancha (arcos en x = ±52,5), Y = ancho, Z = arriba.
"""
from __future__ import annotations
import math
from mathutils import Vector
from estudio.blender import kit as K

RADIO = 0.11           # el juego usa 0,10 de física y lo dibuja ×1,25; acá 0,11 (tamaño 5 real)
MASA = 0.42
REBOTE = 0.54
CD = 0.25
RHO = 1.2
MAGNUS_K = 0.0018
ROD_A, ROD_C, ROD_VK = 0.3, 1.0, 7.0
G = 9.81
ARCO = {"x": 52.5, "ancho": 7.32, "alto": 2.44, "fondo": 2.0}


def crear(nombre="pelota", col=None):
    blanco = K.material("cuero_blanco", (0.9, 0.9, 0.88), 0.35)
    negro = K.material("cuero_negro", (0.02, 0.02, 0.025), 0.35)
    ob = K.esfera(nombre, (0, 0, RADIO), RADIO, blanco, col, subdiv=3)
    ob.data.materials.append(negro)
    # paneles: las caras cuyo centro cae cerca de los 12 vértices de un icosaedro van en negro (patrón clásico)
    ico = [Vector(v).normalized() for v in [(0, 1, 1.618), (0, -1, 1.618), (0, 1, -1.618), (0, -1, -1.618),
                                              (1, 1.618, 0), (-1, 1.618, 0), (1, -1.618, 0), (-1, -1.618, 0),
                                              (1.618, 0, 1), (-1.618, 0, 1), (1.618, 0, -1), (-1.618, 0, -1)]]
    for p in ob.data.polygons:
        c = p.center.normalized()
        if max(c.dot(v) for v in ico) > 0.94:
            p.material_index = 1
    return ob


def simular(p0, v0, w0=(0, 0, 0), duracion=6.0, dt=1 / 240, arco_x=None):
    """Devuelve lista de (t, pos, vel, w). arco_x: ±52.5 para activar la red de ese arco."""
    p, v, w = Vector(p0), Vector(v0), Vector(w0)
    area = math.pi * RADIO * RADIO
    out = []
    t = 0.0
    en_red = False
    while t <= duracion:
        out.append((t, p.copy(), v.copy(), w.copy()))
        sp = v.length
        en_aire = p.z > RADIO + 0.01
        # arrastre cuadrático
        if sp > 0:
            f = 0.5 * RHO * CD * area * sp * sp
            dv = min(sp, f / MASA * dt)
            v -= v.normalized() * dv
        # Magnus en el aire
        if en_aire and sp > 1.0:
            v += w.cross(v) * (MAGNUS_K / MASA) * dt
        # gravedad
        v.z -= G * dt
        p += v * dt
        # red del arco: tela que absorbe (devuelve ~5 % de la energía)
        if arco_x is not None:
            s = 1 if arco_x > 0 else -1
            dentro = abs(p.y) < ARCO["ancho"] / 2 and p.z < ARCO["alto"]
            if dentro and s * p.x > abs(arco_x):
                en_red = True
            if en_red:
                prof = s * p.x - abs(arco_x)
                v -= Vector((s * 1800 * max(0.0, prof - ARCO["fondo"] * 0.6) * dt, 0, 0))
                v *= max(0.0, 1 - 7 * dt)
                w *= max(0.0, 1 - 7 * dt)
                if s * p.x > abs(arco_x) + ARCO["fondo"]:
                    p.x = s * (abs(arco_x) + ARCO["fondo"])
                    v.x = -s * abs(v.x) * 0.05
        # piso
        if p.z < RADIO:
            p.z = RADIO
            if v.z < -0.6:
                v.z = -v.z * REBOTE
                w *= 0.8
            else:
                v.z = 0.0
                horiz = Vector((v.x, v.y, 0))
                hs = horiz.length
                if hs > 0:
                    dec = (ROD_A + ROD_C * min(hs, ROD_VK)) * dt
                    nuevo = max(0.0, hs - dec)
                    v.x, v.y = v.x * nuevo / hs, v.y * nuevo / hs
                    w *= nuevo / hs if hs else 0
        t += dt
    return out


def resolver_tiro(p0, destino, velocidad, efecto=(0, 0, 0), arco_x=None, iteraciones=40):
    """Busca la dirección inicial para que la pelota pase por `destino` saliendo a `velocidad` m/s
    (con arrastre y Magnus). Devuelve el vector velocidad inicial."""
    p0, destino = Vector(p0), Vector(destino)
    d = destino - p0
    horiz = Vector((d.x, d.y, 0))
    yaw = math.atan2(d.y, d.x)
    pitch = math.atan2(d.z, horiz.length) + 0.08
    for _ in range(iteraciones):
        v0 = Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))) * velocidad
        tray = simular(p0, v0, efecto, duracion=4.0, dt=1 / 240)
        # punto de la trayectoria más cercano al plano del destino (a lo largo de la dirección principal)
        eje = horiz.normalized()
        cerca = min(tray, key=lambda s: abs((s[1] - p0).dot(eje) - horiz.length))
        err = destino - cerca[1]
        lat = Vector((-eje.y, eje.x, 0))
        yaw += err.dot(lat) / max(1.0, horiz.length) * 0.9
        pitch += err.z / max(1.0, horiz.length) * 0.9
        if err.length < 0.03:
            break
    return Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))) * velocidad


def animar(ob, tray, frame_inicio: int, fps=30, reposo=None):
    """Graba la trayectoria simulada en claves (posición y rotación por rodadura/giro)."""
    paso = int(round((1 / fps) / (tray[1][0] - tray[0][0])))
    rot = Vector((0, 0, 0))
    previo = None
    if reposo is not None:
        ob.location = reposo
        ob.keyframe_insert("location", frame=1)
        ob.keyframe_insert("location", frame=max(1, frame_inicio - 1))
    for i in range(0, len(tray), paso):
        t, p, v, w = tray[i]
        f = frame_inicio + i // paso
        if previo is not None:
            desp = p - previo
            if p.z <= RADIO + 0.01:  # rodando: el giro sale del avance
                rot += Vector((-desp.y, desp.x, 0)) / RADIO
            else:
                rot += w / fps
        previo = p.copy()
        ob.location = p
        ob.rotation_euler = rot
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
    return frame_inicio + (len(tray) - 1) // paso
