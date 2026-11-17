"""DÚO CERO — Episodio 01 «Un minuto para saltar» (producción p009): noche, región industrial y montañosa.

Un solo mundo para las 6 escenas, con un reloj único del episodio (T = 0…180 s): la escena N construye el mismo
escenario con «escena» = N y anima el tren desde T0 de esa escena, así la posición del tren es continua entre cortes.

- Vía de ~6 km que baja de la sierra y entra derecha (hacia +Y) a la zona industrial; tren de carga (locomotora +
  vagones cerrados y plataformas con contenedores) a ~80 km/h que frena a ~41 km/h al pasar la zona de carga.
- El vagón de Nico y Luna (índice HEROE) se arma aparte: paredes planas, por fuera rojo óxido con nervaduras y por
  dentro tablones, puerta corrediza abierta del lado derecho (+X, el de la base), farol, cajas, mochilas y la radio.
- Zona de carga junto a la vía (plataforma de hormigón, cajas, contenedores, poste de luz, montículo de arena donde
  aterrizan) y la base: cerco, cuatro torres con reflectores, edificio central con ventanas encendidas, contenedores.
Convención del tren (estudio/blender/tren.py): +Y local = adelante; la puerta abierta mira a +X local.
"""
from __future__ import annotations
import math
import random

import bpy
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

from estudio.blender import kit as K, tren as TR, via_ferrea as VF, armas_stickman as AS

DEPENDENCIAS = [
    "mixamo:modelos_pelicula/locomotora_diesel.glb", "mixamo:modelos_pelicula/vagon_plano.glb",
    "mixamo:modelos_pelicula/vagon_cerrado.glb",
    "subidas:stickman/armas_stickman/",
]

PARAMETROS = {"escena": 1, "semilla": 5}

# reloj del episodio: comienzo y duración de cada escena (s)
ESCENAS = {1: (0.0, 30.0), 2: (30.0, 35.0), 3: (65.0, 30.0), 4: (95.0, 30.0), 5: (125.0, 35.0), 6: (160.0, 20.0)}
T_SALTO = 117.0                 # Nico salta (01:57 del episodio); Luna 0,6 s después
HEROE = 6                       # índice del vagón de Nico y Luna en la composición
COMPOSICION = ["loco"] + ["cerrado", "cerrado", "plano", "cerrado", "plano", "cerrado", "cerrado", "plano",
                          "cerrado", "cerrado", "plano", "cerrado", "cerrado", "plano", "cerrado", "cerrado"]
PUNTOS = [(-1300, -4400), (-1150, -3800), (-900, -3200), (-650, -2700), (-380, -2200), (-140, -1700), (30, -1200),
          (70, -750), (35, -380), (0, -120), (0, 0), (0, 220), (0, 520), (-40, 900), (-200, 1450), (-430, 2000),
          (-700, 2600), (-950, 3200), (-1150, 3800)]
PISO = 1.60                     # piso del vagón del héroe sobre el terreno
ANCHO_V, LARGO_V, ALTO_V = 3.0, 13.6, 2.75
PUERTA = 1.6                    # media abertura de la puerta (a lo largo)


def via():
    return TR.Via([(x, y, 0.0) for x, y in PUNTOS])


def velocidad(T: float) -> float:
    """m/s del tren: 22 (80 km/h) → frena a 11,5 al llegar a la zona de carga → vuelve a acelerar (relativo al salto)."""
    ts = _CACHE.get("T_salto", T_SALTO)
    tabla = [(-60, 22.0), (ts - 30, 22.0), (ts - 9, 11.5), (ts + 22, 11.5), (ts + 46, 20.0), (ts + 300, 20.0)]
    for (t0, v0), (t1, v1) in zip(tabla, tabla[1:]):
        if T <= t1:
            k = max(0.0, (T - t0) / (t1 - t0))
            k = k * k * (3 - 2 * k)
            return v0 + (v1 - v0) * k
    return tabla[-1][1]


def _integral(Ta: float, Tb: float, paso: float = 0.02) -> float:
    s, sg = 0.0, 1.0
    if Tb < Ta:
        Ta, Tb, sg = Tb, Ta, -1.0
    t = Ta
    while t < Tb - 1e-9:
        h = min(paso, Tb - t)
        s += (velocidad(t) + velocidad(t + h)) / 2 * h
        t += h
    return s * sg


_CACHE: dict = {}


def s_salto(v=None) -> float:
    """Distancia sobre la vía del punto (0, 0): ahí pasa la puerta del vagón del héroe en el momento del salto."""
    if "s_salto" not in _CACHE:
        v = v or via()
        best = min(range(0, int(v.largo), 1), key=lambda s: v.en(s)[0].length)
        _CACHE["s_salto"] = float(best)
    return _CACHE["s_salto"]


def offset_heroe() -> float:
    off = 0.0
    for i, tipo in enumerate(COMPOSICION):
        largo = TR.TIPOS[tipo][1]
        if i == HEROE:
            return off + largo / 2
        off += largo + TR.SEPARACION
    raise ValueError


def s_cabeza(T: float, v=None) -> float:
    """Frente de la locomotora sobre la vía en el instante T del episodio."""
    return s_salto(v) + offset_heroe() + _integral(_CACHE.get("T_salto", T_SALTO), T)


def s_heroe(T: float, v=None) -> float:
    return s_cabeza(T, v) - offset_heroe()


# ------------------------------------------------------------------------------------------------ materiales
def _mats():
    M = K.material
    return {
        "oxido": M("vagon_oxido", (0.30, 0.065, 0.04), 0.7, 0.15, ruido=0.25, escala_ruido=6, relieve=0.15),
        "oxido_osc": M("vagon_oxido_osc", (0.16, 0.04, 0.03), 0.75, 0.1, ruido=0.2, escala_ruido=8),
        "techo": M("vagon_techo", (0.07, 0.07, 0.075), 0.6, 0.3, ruido=0.2, escala_ruido=5),
        "tablon": M("vagon_tablon", (0.24, 0.15, 0.08), 0.75, ladrillo=((0.17, 0.10, 0.05), 1.6), relieve=0.1),
        "piso": M("vagon_piso", (0.16, 0.10, 0.055), 0.8, ladrillo=((0.11, 0.07, 0.04), 2.2), relieve=0.15),
        "caja": M("caja_madera", (0.42, 0.29, 0.15), 0.75, ruido=0.3, escala_ruido=10, relieve=0.2),
        "caja_osc": M("caja_madera_osc", (0.25, 0.17, 0.09), 0.8, ruido=0.3, escala_ruido=10, relieve=0.2),
        "caja_verde": M("caja_militar", (0.12, 0.15, 0.07), 0.6, 0.05, ruido=0.15, escala_ruido=12),
        "mochila": M("mochila", (0.13, 0.15, 0.07), 0.85, ruido=0.2, escala_ruido=20),
        "negro": M("plastico_negro", (0.015, 0.015, 0.017), 0.45),
        "metal": M("metal_gris", (0.35, 0.35, 0.36), 0.35, 0.8),
        "led_verde": M("led_verde", (0.1, 1.0, 0.2), 0.3, emision=(0.1, 1.0, 0.2), fuerza=8.0),
        "led_rojo": M("led_rojo", (1.0, 0.05, 0.02), 0.3, emision=(1.0, 0.05, 0.02), fuerza=12.0),
        "hormigon": M("hormigon", (0.25, 0.25, 0.24), 0.9, ruido=0.25, escala_ruido=3, relieve=0.1),
        "arena": M("arena", (0.42, 0.34, 0.22), 0.95, ruido=0.25, escala_ruido=6, relieve=0.4),
        "tierra": M("tierra_noche", (0.11, 0.105, 0.09), 0.95, ruido=0.4, escala_ruido=0.08, relieve=0.2),
        "monte": M("monte_noche", (0.05, 0.055, 0.062), 0.95, ruido=0.3, escala_ruido=0.004),
        "fachada": M("fachada_fabrica", (0.10, 0.10, 0.105), 0.85, ventanas=((1.0, 0.72, 0.38), 0.32), fuerza=1.6,
                     ruido=0.15, escala_ruido=2),
        "fachada_base": M("fachada_base", (0.17, 0.17, 0.165), 0.85, ventanas=((1.0, 0.86, 0.62), 0.4), fuerza=2.2,
                          ruido=0.12, escala_ruido=2),
        "chapa": M("chapa_galpon", (0.20, 0.21, 0.22), 0.55, 0.6, ruido=0.2, escala_ruido=3),
        "lampara_sodio": M("lampara_sodio", (1.0, 0.55, 0.15), 0.3, emision=(1.0, 0.55, 0.15), fuerza=40.0),
        "lampara_blanca": M("lampara_blanca", (0.9, 0.95, 1.0), 0.3, emision=(0.9, 0.95, 1.0), fuerza=60.0),
        "haz": M("haz_reflector", (0.9, 0.95, 1.0), 0.3, emision=(0.9, 0.95, 1.0), fuerza=0.35, alfa=0.08,
                 mezcla="BLENDED"),
        "alambre": M("malla_cerco", (0.30, 0.31, 0.32), 0.5, 0.7, alfa=0.35, mezcla="BLENDED"),
        "luna": M("disco_luna", (1, 1, 1), 0.5, emision=(0.85, 0.9, 1.0), fuerza=6.0),
        "pantalla": None,
    }


# ------------------------------------------------------------------------------------------------ cielo y luces
def _cielo_y_luna(sc, col):
    K.cielo_noche(sc, cenit=(0.004, 0.007, 0.02), horizonte=(0.03, 0.03, 0.05), estrellas=True, fuerza=1.6)
    # luz de luna: fría y baja, desde el oeste-sudoeste; el disco de la luna se ve en los planos aéreos
    luna = K.luz("luz_luna", "SUN", (0, 0, 200), 1.1, (0.55, 0.68, 1.0), col,
                 rot=(math.radians(62), 0, math.radians(-115)))
    luna.data.angle = math.radians(0.6)
    d = Vector((-0.75, -0.35, 0.56)).normalized()
    K.esfera("disco_luna", tuple(d * 2600), 45.0, _mats()["luna"], col, subdiv=3)["visor_omitir"] = True


# ------------------------------------------------------------------------------------------------ terreno y sierra
def _terreno(col, v, M, s0, s1):
    """Llanura con lomas suaves (plana a lo largo de la vía) + cordones de sierra lejos, sólo de silueta."""
    kd = KDTree(int(v.largo / 4) + 1)
    for i, s in enumerate(range(0, int(v.largo), 4)):
        kd.insert(v.en(s)[0], i)
    kd.balance()
    p0, p1 = v.en(s0)[0], v.en(s1)[0]
    cx, cy = (p0.x + p1.x) / 2, (p0.y + p1.y) / 2
    ext = max(2400.0, (p1 - p0).length / 2 + 1400)
    n = 150
    rnd = random.Random(3)
    from mathutils import noise
    verts, caras = [], []
    for j in range(n + 1):
        for i in range(n + 1):
            x = cx - ext + 2 * ext * i / n
            y = cy - ext + 2 * ext * j / n
            _, _, dist = kd.find((x, y, 0))
            h = noise.noise(Vector((x / 380, y / 380, 0.3))) * 9 + noise.noise(Vector((x / 90, y / 90, 1.7))) * 2.0
            k = min(1.0, max(0.0, (dist - 30) / 120))
            verts.append((x, y, -0.08 + h * k * k))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            caras.append((a, a + 1, a + n + 2, a + n + 1))
    me = bpy.data.meshes.new("terreno")
    me.from_pydata(verts, [], caras)
    for f in me.polygons:
        f.use_smooth = True
    ob = bpy.data.objects.new("terreno", me)
    me.materials.append(M["tierra"])
    col.objects.link(ob)
    # sierra: tres cordones de silueta, lejos al oeste y al este (con picos nevados apenas iluminados por la luna)
    for k, (ox, oy, largo, alto, ang) in enumerate(((-2600, 0, 9000, 520, 0.08), (2900, -600, 8000, 380, -0.12),
                                                    (-900, 4200, 6000, 640, 1.45))):
        nv, nu = 80, 6
        vs, fs = [], []
        for i in range(nv + 1):
            u = -0.5 + i / nv
            base_h = alto * (0.55 + 0.45 * noise.noise(Vector((u * 7 + k, 0.5, 0.0))) + 0.25 * noise.noise(Vector((u * 23, 2.0, k))))
            for j in range(nu + 1):
                w = j / nu
                prof = (w - 0.5) * 900
                hh = max(0.0, base_h * (1 - abs(w - 0.5) * 2) ** 0.8)
                x0, y0 = u * largo, prof
                c, s_ = math.cos(ang), math.sin(ang)
                vs.append((ox + x0 * c - y0 * s_ if ang > 1 else ox + y0, oy + x0 * s_ + y0 * c if ang > 1 else oy + x0, hh - 5))
        for i in range(nv):
            for j in range(nu):
                a = i * (nu + 1) + j
                fs.append((a, a + 1, a + nu + 2, a + nu + 1))
        me = bpy.data.meshes.new(f"sierra_{k}")
        me.from_pydata(vs, [], fs)
        for f in me.polygons:
            f.use_smooth = True
        sob = bpy.data.objects.new(f"sierra_{k}", me)
        me.materials.append(M["monte"])
        col.objects.link(sob)
    return ob


# ------------------------------------------------------------------------------------------------ zona industrial
def _poste_luz(lote_poste, lote_lamp, luces, pos: Vector, alto: float, brazo: Vector, col, M, color, energia, nombre):
    lote_poste.cilindro(pos, 0.11, alto, 8, 0.08)
    cab = pos + Vector((0, 0, alto)) + brazo
    lote_poste.caja(pos + Vector((0, 0, alto)) + brazo / 2, math.atan2(brazo.y, brazo.x), (0.08, brazo.length, 0.08))
    lote_lamp.caja(cab + Vector((0, 0, -0.08)), math.atan2(brazo.y, brazo.x), (0.32, 0.6, 0.12))
    l = K.luz(nombre, "SPOT", tuple(cab + Vector((0, 0, -0.2))), energia, color, col, angulo_spot=math.radians(120), radio=0.15)
    l.rotation_euler = (0, 0, 0)
    luces.append(l)


def _industria(col, v, M, rnd, s0, s1):
    """Postes de sodio a lo largo de la vía, galpones con ventanas, tanques, chimeneas con balizas rojas."""
    postes, lamps, luces = VF.Lote(), VF.Lote(), []
    s = max(s0, s_salto(v) - 1300)
    fin = min(s1, s_salto(v) + 700)
    k = 0
    while s < fin:
        p, t, n, ang = VF.marco(v, s)
        lado = 1 if k % 2 == 0 else -1
        base = p + n * (lado * 9.5)
        _poste_luz(postes, lamps, luces, base, 9.0, n * (-lado * 2.2), col, M, (1.0, 0.6, 0.25), 900, f"sodio_{k}")
        s += 45.0
        k += 1
    postes.objeto("postes_luz_via", M["metal"], col)
    lamps.objeto("lamparas_via", M["lampara_sodio"], col)
    # galpones y fábricas (fachadas planas con ventanas al azar), lejos de la base
    edif = VF.Lote()
    chap = VF.Lote()
    tanques = VF.Lote()
    balizas = []
    for i in range(26):
        y = rnd.uniform(-1500, 650)
        lado = rnd.choice((-1, 1))
        x = lado * rnd.uniform(45, 330)
        if 100 < x < 340 and -90 < y < 200:          # ahí está la base
            continue
        d = v.en(max(0.0, s_salto(v) + y))[0]
        x += d.x
        w, l, h = rnd.uniform(18, 45), rnd.uniform(25, 70), rnd.uniform(8, 22)
        if rnd.random() < 0.65:
            edif.caja(Vector((x, y, h / 2)), math.radians(90 + rnd.uniform(-8, 8)), (w, l, h))
            chap.caja(Vector((x, y, h + 0.8)), math.radians(90), (w * 1.02, l * 1.02, 1.6))
        else:
            for j in range(rnd.randint(2, 4)):
                tanques.cilindro(Vector((x + j * 14, y, 0)), rnd.uniform(5, 7), rnd.uniform(10, 18), 20)
        if rnd.random() < 0.45:
            hc = rnd.uniform(28, 48)
            tanques.cilindro(Vector((x + w / 2 + 4, y, 0)), 1.6, hc, 14, 1.1)
            balizas.append(Vector((x + w / 2 + 4, y, hc + 0.5)))
    edif.objeto("fabricas", M["fachada"], col)
    chap.objeto("techos_fabricas", M["chapa"], col)
    tanques.objeto("tanques_chimeneas", M["chapa"], col)
    bz = VF.Lote()
    for b in balizas:
        bz.caja(b, 0.0, (0.7, 0.7, 0.7))
    if balizas:
        ob = bz.objeto("balizas_rojas", M["led_rojo"], col)
        ob["visor_omitir"] = True
    return luces


def _contenedor(lote, centro: Vector, ang: float, largo=12.2):
    lote.caja(centro, ang, (2.44, largo, 2.59))


def _base(col, M, rnd):
    """La instalación: cerco, torres con reflectores, edificio central, contenedores. Devuelve anclas útiles."""
    x0, x1, y0, y1 = 150.0, 330.0, -60.0, 170.0
    # cerco perimetral (postes + malla semitransparente + concertina)
    postes = VF.Lote()
    malla = VF.Lote()
    for (ax, ay), (bx, by) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        largo = math.hypot(bx - ax, by - ay)
        ang = math.atan2(by - ay, bx - ax)
        n = int(largo / 3.5)
        for i in range(n + 1):
            p = Vector((ax + (bx - ax) * i / n, ay + (by - ay) * i / n, 0))
            postes.cilindro(p, 0.05, 3.2, 6)
        mid = Vector(((ax + bx) / 2, (ay + by) / 2, 1.5))
        malla.caja(mid, ang + math.pi / 2, (0.02, largo, 3.0))
    postes.objeto("cerco_postes", M["metal"], col)
    malla.objeto("cerco_malla", M["alambre"], col)
    # edificio central y anexos (fachadas planas iluminadas)
    ed = VF.Lote()
    ed.caja(Vector((250, 70, 9)), math.radians(90), (55, 34, 18))
    ed.caja(Vector((205, 120, 5)), math.radians(90), (28, 20, 10))
    ed.caja(Vector((290, 0, 4.5)), math.radians(90), (24, 30, 9))
    ed.objeto("base_edificios", M["fachada_base"], col)
    te = VF.Lote()
    te.caja(Vector((250, 70, 18.6)), math.radians(90), (56, 35, 1.2))
    te.caja(Vector((205, 120, 10.5)), math.radians(90), (29, 21, 1.0))
    te.caja(Vector((290, 0, 9.5)), math.radians(90), (25, 31, 1.0))
    te.objeto("base_techos", M["chapa"], col)
    # contenedores apilados dentro
    cont = VF.Lote()
    for i in range(7):
        cont.caja(Vector((180 + i * 3.0, 20, 1.3)), 0.0, (2.44, 12.2, 2.59))
        if i % 2 == 0:
            cont.caja(Vector((180 + i * 3.0, 20, 3.9)), 0.0, (2.44, 12.2, 2.59))
    cont.objeto("base_contenedores", K.material("contenedor_azul", (0.03, 0.09, 0.22), 0.6, 0.4, ruido=0.2), col)
    # torres de vigilancia con reflector (luz spot + haz visible que barre)
    torres = VF.Lote()
    cabinas = VF.Lote()
    reflectores = []
    for k, (tx, ty) in enumerate(((x0 + 4, y0 + 4), (x1 - 4, y0 + 4), (x1 - 4, y1 - 4), (x0 + 4, y1 - 4))):
        for dx in (-1.3, 1.3):
            for dy in (-1.3, 1.3):
                torres.cilindro(Vector((tx + dx, ty + dy, 0)), 0.12, 9.0, 6, 0.1)
        cabinas.caja(Vector((tx, ty, 10.2)), 0.0, (3.6, 3.6, 2.4))
        torres.caja(Vector((tx, ty, 11.7)), 0.0, (4.2, 4.2, 0.3))
        piv = K.vacio(f"torre_{k}_reflector", (tx, ty, 11.0), col)
        luz = K.luz(f"torre_{k}_luz", "SPOT", (0, 0, 0), 9000, (0.9, 0.95, 1.0), col, angulo_spot=math.radians(16),
                    radio=0.25)
        luz.parent = piv
        luz.rotation_euler = (math.radians(65), 0, 0)
        haz = K.cilindro(f"torre_{k}_haz", (0, 0, 0), 0.4, 60, M["haz"], col, lados=16)
        haz["visor_omitir"] = True
        # cono: el tope del cilindro se abre
        me = haz.data
        for vtx in me.vertices:                     # cono: angosto en el reflector, ancho a 60 m
            vtx.co.z += 30
            if vtx.co.z > 1:
                vtx.co.x *= 22
                vtx.co.y *= 22
        haz.parent = piv
        haz.rotation_euler = (math.radians(65 + 180), 0, 0)
        haz.location = (0, 0, 0)
        haz.visible_shadow = False
        reflectores.append(piv)
    torres.objeto("torres", M["metal"], col)
    cabinas.objeto("torres_cabinas", M["fachada_base"], col)
    # mástiles de iluminación del playón
    mast = VF.Lote()
    lamps = VF.Lote()
    for k, (mx, my) in enumerate(((200, 30), (300, 120), (240, -30))):
        mast.cilindro(Vector((mx, my, 0)), 0.25, 18, 8, 0.15)
        lamps.caja(Vector((mx, my, 18.3)), 0.0, (2.2, 0.5, 0.6))
        l = K.luz(f"mastil_{k}", "SPOT", (mx, my, 18.0), 60000, (0.85, 0.9, 1.0), col, angulo_spot=math.radians(110),
                  radio=0.4)
    mast.objeto("mastiles", M["metal"], col)
    lamps.objeto("mastiles_lamparas", M["lampara_blanca"], col)
    # luces del edificio (tenues, para que se lea el volumen)
    for k, (lx, ly) in enumerate(((222, 50), (278, 90), (250, 35))):
        K.luz(f"base_luz_{k}", "POINT", (lx, ly, 6), 4000, (1.0, 0.85, 0.65), col, radio=1.0)
    return {"reflectores": reflectores, "centro": (250.0, 70.0, 6.0), "porton": (x0, 40.0, 1.5),
            "torre_sur": (x0 + 4, y0 + 4, 11.0)}


def _animar_reflectores(reflectores, frames, T0, fps):
    for k, piv in enumerate(reflectores):
        for f in frames[::6] + [frames[-1]]:
            T = T0 + (f - 1) / fps
            piv.rotation_euler = (0, 0, math.radians(200 + 70 * math.sin(T * 0.28 + k * 1.7) + k * 90))
            piv.keyframe_insert("rotation_euler", frame=f)


def _zona_carga(col, M, rnd):
    """Playa de carga junto a la vía (lado +X, a la altura del salto) y el montículo de arena donde caen."""
    K.caja("zona_losa", (24, 15, -0.02), (36, 90, 0.12), M["hormigon"], col)
    # montículo de arena (cúpula alargada) donde aterrizan
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=1.0)
    for vv in bm.verts:
        vv.co.x *= 3.6
        vv.co.y *= 8.5
        vv.co.z = max(0.0, vv.co.z) * 1.15
    me = bpy.data.meshes.new("monticulo_arena")
    bm.to_mesh(me)
    bm.free()
    for f in me.polygons:
        f.use_smooth = True
    ob = bpy.data.objects.new("monticulo_arena", me)
    me.materials.append(M["arena"])
    col.objects.link(ob)
    ob.location = (7.5, 14.0, -0.05)
    # pilas de cajas y contenedores (coberturas del tiroteo)
    cajas = VF.Lote()
    cajas_v = VF.Lote()
    # P1 (12, 26,5): cobertura de Luna · P2 (17, 19): la de Nico · el resto, decorado lejos del camino de los guardias
    pilas = [(11.4, 26.5, 2, 2), (16.6, 19.0, 2, 2), (30, 8, 3, 3), (36, 28, 2, 2), (18, 46, 2, 2), (40, 16, 1, 2)]
    for (px, py, nx, nz) in pilas:
        for i in range(nx):
            for j in range(nz - (i % 2)):
                tam = 1.2
                (cajas if (i + j) % 3 else cajas_v).caja(Vector((px + i * 1.25, py + rnd.uniform(-0.1, 0.1), 0.6 + j * 1.2)),
                                                       math.radians(90 + rnd.uniform(-4, 4)), (tam, tam, tam))
    cajas.objeto("zona_cajas", M["caja"], col)
    cajas_v.objeto("zona_cajas_verdes", M["caja_verde"], col)
    cont = VF.Lote()
    cont.caja(Vector((36, -6, 1.3)), 0.0, (2.44, 12.2, 2.59))
    cont.caja(Vector((38.6, -6, 1.3)), 0.0, (2.44, 12.2, 2.59))
    cont.caja(Vector((37.3, -6, 3.9)), 0.0, (2.44, 12.2, 2.59))
    cont.caja(Vector((34, 50, 1.3)), math.radians(90), (2.44, 12.2, 2.59))
    cont.objeto("zona_contenedores", K.material("contenedor_naranja", (0.35, 0.10, 0.02), 0.6, 0.3, ruido=0.25), col)
    # poste con lámpara blanca y otro de sodio
    pl, lp, luces = VF.Lote(), VF.Lote(), []
    _poste_luz(pl, lp, luces, Vector((22, 26, 0)), 10.0, Vector((-2.0, 0, 0)), col, M, (0.85, 0.9, 1.0), 2500, "zona_luz_a")
    _poste_luz(pl, lp, luces, Vector((40, 8, 0)), 10.0, Vector((-2.0, 0, 0)), col, M, (1.0, 0.62, 0.3), 1800, "zona_luz_b")
    pl.objeto("zona_postes", M["metal"], col)
    lp.objeto("zona_lamparas", M["lampara_blanca"], col)
    return {"arena": (7.5, 14.0, 1.0), "zona": (22.0, 18.0, 1.0), "coberturas": [(12.0, 26.5), (17.2, 19.0)]}


# ------------------------------------------------------------------------------------------------ el vagón de los héroes
def _vagon_heroe(carro: dict, col, M, rnd) -> dict:
    """Reemplaza la carrocería del vagón por uno armado (por fuera igual de rojo, por dentro tablones) con la puerta
    corrediza abierta del lado +X. Todo cuelga de la raíz del vagón (sigue la vía). Devuelve anclas locales."""
    raiz = carro["raiz"]
    for o in [carro["cuerpo"]] + list(carro["cuerpo"].children_recursive):
        o.hide_render = o.hide_viewport = True
        o["visor_omitir"] = True
    W, L, H, z0 = ANCHO_V, LARGO_V, ALTO_V, PISO
    e = 0.06
    piezas = []

    def caja(n, c, t, m, b=0.0):
        ob = K.caja(f"heroe_{n}", c, t, m, col, bisel=b)
        ob.parent = raiz
        piezas.append(ob)
        return ob
    # bastidor, piso, paredes (la derecha con la abertura), testeros y techo
    caja("bastidor", (0, 0, z0 - 0.28), (W - 0.2, L, 0.5), M["oxido_osc"])
    caja("piso", (0, 0, z0 - 0.03), (W, L, 0.06), M["piso"])
    caja("pared_izq_ext", (-W / 2 - e / 2, 0, z0 + H / 2), (e, L, H), M["oxido"])
    caja("pared_izq_int", (-W / 2 + 0.02, 0, z0 + H / 2), (0.02, L - 0.1, H), M["tablon"])
    yb = (L / 2 + PUERTA) / 2
    largo_lado = L / 2 - PUERTA
    for sg in (-1, 1):
        caja(f"pared_der_ext_{sg}", (W / 2 + e / 2, sg * yb, z0 + H / 2), (e, largo_lado, H), M["oxido"])
        caja(f"pared_der_int_{sg}", (W / 2 - 0.02, sg * yb, z0 + H / 2), (0.02, largo_lado, H), M["tablon"])
        caja(f"testero_ext_{sg}", (0, sg * (L / 2 + e / 2), z0 + H / 2), (W + 2 * e, e, H), M["oxido"])
        caja(f"testero_int_{sg}", (0, sg * (L / 2 - 0.02), z0 + H / 2), (W - 0.1, 0.02, H), M["tablon"])
    caja("dintel", (W / 2 + e / 2, 0, z0 + 2.45 + (H - 2.45) / 2), (e, 2 * PUERTA, H - 2.45), M["oxido"])
    caja("techo", (0, 0, z0 + H + 0.06), (W + 0.25, L + 0.15, 0.12), M["techo"])
    caja("techo_int", (0, 0, z0 + H - 0.01), (W - 0.1, L - 0.1, 0.02), M["tablon"])
    # nervaduras exteriores y riel de la puerta
    nerv = VF.Lote()
    for sg_x in (-1, 1):
        y = -L / 2 + 0.35
        while y < L / 2 - 0.3:
            if not (sg_x > 0 and abs(y) < PUERTA + 0.15):
                nerv.caja(Vector((sg_x * (W / 2 + e + 0.025), y, z0 + H / 2)), math.pi / 2, (0.05, 0.09, H - 0.05))
            y += 0.68
    nerv.caja(Vector((W / 2 + e + 0.07, 1.2, z0 + 2.55)), math.pi / 2, (0.08, 7.6, 0.1))
    nob = nerv.objeto("heroe_nervaduras", M["oxido"], col)
    nob.parent = raiz
    # puerta corrediza abierta (corrida hacia adelante, por fuera de la pared)
    caja("puerta_corrediza", (W / 2 + e + 0.12, PUERTA + 1.7, z0 + 1.25), (0.06, 3.4, 2.5), M["oxido"])
    caja("puerta_manija", (W / 2 + e + 0.17, PUERTA + 0.15, z0 + 1.2), (0.05, 0.08, 0.6), M["metal"])
    # carga: cajas de madera, cajones militares, mochilas, la radio y la tableta
    caja("banco_cajon", (-W / 2 + 0.42, 0.0, z0 + 0.24), (0.8, 2.6, 0.48), M["caja"], 0.02)
    for i, (x, y, t, m) in enumerate(((-0.9, -3.4, (1.1, 1.1, 1.1), "caja"), (-0.9, -4.6, (1.1, 1.1, 1.1), "caja_osc"),
                                      (-0.95, -4.0, (1.0, 1.0, 1.0), "caja"), (0.6, -5.8, (1.2, 1.2, 1.2), "caja_osc"),
                                      (-0.85, 3.2, (1.2, 1.4, 0.9), "caja_verde"), (-0.85, 4.8, (1.2, 1.4, 0.9), "caja_verde"),
                                      (-0.85, 4.0, (1.2, 1.4, 0.9), "caja_verde"), (0.7, 5.6, (1.1, 1.1, 1.1), "caja"),
                                      (0.7, 4.4, (1.0, 1.0, 1.4), "caja_osc"), (-0.9, -5.9, (1.1, 1.1, 0.8), "caja"))):
        zc = z0 + t[2] / 2 + (1.1 if i == 2 else 0) + (0.9 if i == 6 else 0)
        caja(f"carga_{i}", (x, y, zc), t, M[m], 0.02)
    caja("cajita_radio", (-0.55, 1.75, z0 + 0.25), (0.5, 0.4, 0.5), M["caja_verde"], 0.02)
    radio = caja("radio", (-0.55, 1.75, z0 + 0.62), (0.28, 0.12, 0.22), M["negro"], 0.01)
    caja("radio_led", (-0.55, 1.68, z0 + 0.68), (0.03, 0.01, 0.03), M["led_verde"])
    ant = K.cilindro("heroe_radio_antena", (-0.47, 1.75, z0 + 0.73), 0.008, 0.45, M["negro"], col, lados=6)
    ant.parent = raiz
    mochilas = []
    for i, (x, y) in enumerate(((-0.5, -1.55), (-0.45, 1.35))):
        mochilas.append(caja(f"mochila_{i}", (x, y, z0 + 0.3), (0.42, 0.32, 0.6), M["mochila"], 0.08))
    # las dos armas apoyadas contra la pared, junto a cada uno (cañón arriba, un poco inclinadas hacia la pared)
    armas = {}
    for nombre, y, zg in (("fusil", -1.45, 0.27), ("subfusil", 1.45, 0.08)):
        a_ = AS.crear(nombre, f"heroe_{nombre}_apoyado", col)
        a_.parent = raiz
        a_.location = (-W / 2 + 0.16, y, z0 + zg)
        a_.rotation_euler = (math.radians(-90), math.radians(-14), 0.0)
        armas[nombre] = a_
    # farol del pack colgado de un gancho + su luz cálida (con un parpadeo leve)
    farol = AS.crear("farol", "heroe_farol", col)
    farol.parent = raiz
    farol.location = (-1.0, -1.9, z0 + 1.15)
    farol.rotation_euler = (0, 0, math.radians(20))
    soga = K.cilindro("heroe_soga_farol", (-1.0, -1.9, z0 + 1.15 + 0.12 + (H - 1.27) / 2), 0.008, H - 1.27, M["negro"], col, lados=6)
    soga.parent = raiz
    luz = K.luz("heroe_luz_farol", "POINT", (-0.9, -1.75, z0 + 1.2), 45, (1.0, 0.72, 0.42), col, radio=0.06)
    luz.parent = raiz
    luz2 = K.luz("heroe_relleno_techo", "AREA", (0.2, 0.0, z0 + H - 0.15), 25, (1.0, 0.78, 0.55), col, tam=1.2)
    luz2.parent = raiz
    luz2.rotation_euler = (0, 0, 0)
    anclas = {
        "": (0.0, 0.0, z0 + 1.2), "puerta": (W / 2, 0.0, z0 + 1.2), "piso_puerta": (W / 2, 0.0, z0),
        "banco": (-W / 2 + 0.42, 0.0, z0 + 0.48),
        "nico": (-W / 2 + 0.55, -0.48, z0 + 0.48), "luna": (-W / 2 + 0.55, 0.48, z0 + 0.48),
        "nico_cabeza": (-W / 2 + 0.62, -0.48, z0 + 1.42), "luna_cabeza": (-W / 2 + 0.62, 0.48, z0 + 1.36),
        "entre": (-W / 2 + 0.6, 0.0, z0 + 1.25), "fondo": (-W / 2, 0.0, z0 + 1.3),
        "radio": (-0.55, 1.75, z0 + 0.62), "farol": (-1.0, -1.9, z0 + 1.15),
        "afuera": (W / 2 + 6.0, 0.0, z0 + 0.5), "techo": (0.0, 0.0, z0 + H + 0.3),
    }
    return {"anclas": anclas, "luz_farol": luz, "radio": radio, "armas": armas, "mochilas": mochilas}


def _flicker(luz, frames, base):
    rnd = random.Random(7)
    for f in frames[::3]:
        luz.data.energy = base * (0.88 + 0.12 * rnd.random())
        luz.data.keyframe_insert("energy", frame=f)


# ------------------------------------------------------------------------------------------------ construir
def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    esc = int(p["escena"])
    T0, dur = ESCENAS[esc]
    T0, dur = float(p.get("T0", T0)), float(p.get("duracion_escena_s", dur))
    _CACHE["T_salto"] = float(p.get("T_salto", T_SALTO))
    rnd = random.Random(p["semilla"])
    sc = bpy.context.scene
    fps = sc.render.fps
    col = K.coleccion("ESCENARIO_duo_cero")
    c_terr, c_via, c_ind, c_base, c_tren = (K.coleccion(n, col) for n in ("terreno", "via", "industria", "base", "tren"))
    M = _mats()
    v = via()
    nf = int(round(dur * fps))
    frames = list(range(1, nf + 1))
    Ts = [T0 + (f - 1) / fps for f in frames]
    s_heads = [s_cabeza(T, v) for T in Ts]
    largo_tren = sum(TR.TIPOS[t][1] for t in COMPOSICION) + TR.SEPARACION * (len(COMPOSICION) - 1)
    s0 = max(5.0, min(s_heads) - largo_tren - 450)
    s1 = min(v.largo - 5.0, max(s_heads) + 900)

    _cielo_y_luna(sc, col)
    _terreno(c_terr, v, M, s0, s1)
    sh = s_salto(v)
    VF.construir(v, c_via, s0=s0, s1=s1, s_detalle0=sh - 120, s_detalle1=sh + 160, lado_ruta=60.0, semilla=11,
                 km_inicial=88.0)
    for n in ("alambrado_postes_d", "alambrado_hilos_d"):          # del lado de la zona de carga no hay alambrado
        ob = bpy.data.objects.get(n)
        if ob is not None:
            bpy.data.objects.remove(ob)
    luces_via = _industria(c_ind, v, M, rnd, s0, s1)
    base = _base(c_base, M, rnd)
    _animar_reflectores(base["reflectores"], frames, T0, fps)
    zona = _zona_carga(c_base, M, rnd)

    # tren: contenedores en las plataformas
    tren = TR.construir("tren", c_tren, COMPOSICION)
    cont = VF.Lote()
    colores = [(0.03, 0.09, 0.22), (0.35, 0.10, 0.02), (0.05, 0.16, 0.06), (0.25, 0.25, 0.27)]
    lotes = {}
    for c in tren["carros"]:
        if c["tipo"] == "plano":
            m = K.material(f"contenedor_{c['indice'] % 4}", colores[c["indice"] % 4], 0.6, 0.35, ruido=0.25)
            ob = K.caja(f"tren_{c['indice']:02d}_contenedor", (0, 0, TR.Z_RIEL + c["alto"] + 1.45 + 1.3), (2.44, 12.2, 2.59), m,
                        c_tren, bisel=0.02)
            ob.parent = c["raiz"]
    heroe = _vagon_heroe(tren["carros"][HEROE], c_tren, M, rnd)
    # faro y luces de zanja de la locomotora (se ven de lejos en la noche)
    loco = tren["carros"][0]
    largo_l = TR.TIPOS["loco"][1]
    faro = K.luz("loco_faro", "SPOT", (0, largo_l / 2 + 0.3, 3.9), 40000, (1.0, 0.93, 0.8), c_tren,
                 angulo_spot=math.radians(28), radio=0.2)
    faro.parent = loco["raiz"]
    faro.rotation_euler = (math.radians(88), 0, 0)          # el spot mira a −Z: girado +88° en X apunta adelante
    for k, x in enumerate((-0.0, -0.9, 0.9)):
        z = 3.9 if k == 0 else 1.55
        m = K.esfera(f"loco_lampara_{k}", (x, largo_l / 2 + 0.25, z), 0.12 if k == 0 else 0.08, M["lampara_blanca"], c_tren)
        m.parent = loco["raiz"]
    for k, x in enumerate((-0.9, 0.9)):
        zl = K.luz(f"loco_zanja_{k}", "SPOT", (x, largo_l / 2 + 0.3, 1.55), 6000, (1.0, 0.95, 0.85), c_tren,
                   angulo_spot=math.radians(40), radio=0.1)
        zl.parent = loco["raiz"]
        zl.rotation_euler = (math.radians(80), 0, 0)
    trays = TR.animar(tren, v, frames, s_heads)
    # lo que los personajes se llevan del vagón (escena 4): desde ese momento lo tienen encima
    if p.get("radio_en_mano"):                     # escena 3: Nico tiene la radio en la mano (la de la caja no está)
        r0, r1 = p["radio_en_mano"]
        AS.visible(heroe["radio"], [(0, int(round(r0 * fps))), (int(round(r1 * fps)) + 1, nf + 1)])
    for clave, objs in (("fusil_hasta_s", [heroe["armas"]["fusil"]]), ("subfusil_hasta_s", [heroe["armas"]["subfusil"]]),
                        ("mochilas_hasta_s", heroe["mochilas"])):
        if p.get(clave) is not None:
            for ob in objs:
                AS.visible(ob, [(0, int(round(p[clave] * fps)))])
    _flicker(heroe["luz_farol"], frames, 45)

    carro_h = tren["carros"][HEROE]
    moviles = {"vagon": {"tray": trays[carro_h["raiz"].name], "objeto": carro_h["raiz"], "anclas": heroe["anclas"]},
               "loco": {"tray": trays[tren["carros"][0]["raiz"].name], "objeto": tren["carros"][0]["raiz"],
                        "anclas": {"": (0, 0, 3.0), "frente": (0, 9.0, 3.0), "techo": (0, 0, 5.0)}},
               "cola": {"tray": trays[tren["carros"][-1]["raiz"].name], "objeto": tren["carros"][-1]["raiz"],
                        "anclas": {"": (0, 0, 2.5)}}}
    for c in tren["carros"]:                       # cada vagón (los golpes de las ruedas en las juntas del sonido)
        moviles[f"carro_{c['indice']:02d}"] = {"tray": trays[c["raiz"].name], "anclas": {"": (0, 0, 1.5)}}
    pv = v.en(sh)[0]
    anclas = {"salto": (pv.x, pv.y, 1.5), "arena": zona["arena"], "zona": zona["zona"], "base": base["centro"],
              "porton_base": base["porton"], "torre_sur": base["torre_sur"],
              "via_norte": tuple(v.en(sh + 260)[0] + Vector((0, 0, 1.5))),
              "via_sur": tuple(v.en(sh - 260)[0] + Vector((0, 0, 1.5))),
              "sierra": (-1800.0, -1500.0, 250.0)}
    for k, (cx, cy) in enumerate(zona["coberturas"]):
        anclas[f"cobertura_{k}"] = (float(cx), float(cy), 1.0)
    info = {"T0": T0, "duracion_s": dur, "s_salto": sh, "escena": esc, "T_salto": _CACHE["T_salto"],
            "velocidad_salto": velocidad(_CACHE["T_salto"]),
            "vagon_raiz": carro_h["raiz"].name, "puerta_local": heroe["anclas"]["puerta"]}
    return {"anclas": anclas, "moviles": moviles, "animables": {"tren": tren, "via": v}, "parametros": p, "info": info}


# ------------------------------------------------------------------------------------------------ el salto
def pose_vagon(T: float, v=None):
    """(centro, rumbo) del vagón del héroe en el instante T (misma cuenta que tren.animar)."""
    v = v or _via_cache()
    by = TR.TIPOS["cerrado"][3]
    sc = s_heroe(T, v)
    pd, pt = v.en(sc + by)[0], v.en(sc - by)[0]
    d = (pd - pt).normalized()
    return (pd + pt) / 2, math.atan2(-d.x, d.y)


def _via_cache():
    if "via" not in _CACHE:
        _CACHE["via"] = via()
    return _CACHE["via"]


def altura_suelo(x: float, y: float) -> float:
    """Piso de la zona de carga: el montículo de arena (cúpula 3,6 × 8,5 × 1,15 m) o la losa."""
    dx, dy = (x - 7.5) / 3.6, (y - 14.0) / 8.5
    q = 1 - dx * dx - dy * dy
    return max(0.0, 1.15 * math.sqrt(q) - 0.05) if q > 0 else 0.0


def salto(local: tuple, T_j: float, lateral: float = 4.8, arriba: float = 2.3, freno: float = 14.0, fps: int = 30,
          hasta_s: float = 12.0, giro_inicial: float = 0.0):
    """Trayectoria de quien salta por la puerta en T_j desde `local` (marco del vagón). Devuelve una lista por cuadro
    desde T_j: (t desde el salto, posición de los pies, rumbo en grados [0 = +X], en_el_aire)."""
    c, r = pose_vagon(T_j)
    ca, sa = math.cos(r), math.sin(r)
    p = c + Vector((local[0] * ca - local[1] * sa, local[0] * sa + local[1] * ca, local[2]))
    adelante = Vector((-sa, ca, 0.0))
    derecha = Vector((ca, sa, 0.0))
    vt = velocidad(T_j)
    vel = adelante * vt + derecha * lateral + Vector((0, 0, arriba))
    out = []
    dt = 1.0 / fps / 8
    t, aire, ang = 0.0, True, math.degrees(r) + giro_inicial      # mirando la puerta: +X local
    k = 0
    while t <= hasta_s + 1e-9:
        if k % 8 == 0:
            rumbo_v = math.degrees(math.atan2(vel.y, vel.x)) if Vector((vel.x, vel.y)).length > 0.2 else ang
            out.append((t, p.copy(), rumbo_v if aire or Vector((vel.x, vel.y)).length > 0.2 else ang, aire))
            if not aire and Vector((vel.x, vel.y)).length > 0.2:
                ang = rumbo_v
        if aire:
            vel.z -= 9.81 * dt
            p += vel * dt
            if vel.z < 0 and p.z <= altura_suelo(p.x, p.y):
                p.z = altura_suelo(p.x, p.y)
                vel.z = 0.0
                aire = False
                ang = math.degrees(math.atan2(vel.y, vel.x))
        else:
            h = Vector((vel.x, vel.y, 0.0))
            vh = h.length
            if vh > 0:
                nv = max(0.0, vh - freno * dt)
                h = h * (nv / vh)
                vel.x, vel.y = h.x, h.y
            p += Vector((vel.x, vel.y, 0.0)) * dt
            p.z = altura_suelo(p.x, p.y)
        t += dt
        k += 1
    return out


def despues_personajes(info, pjs, ctx, manifiesto, fps):
    """Saltos del tren: hasta el salto el personaje viaja con el vagón (Child Of); desde ahí, trayectoria en el mundo."""
    if manifiesto.get("tiros"):
        from estudio.blender import tiroteo as TI
        TI.preparar(manifiesto["tiros"], pjs, fps)
    saltos = manifiesto.get("saltos") or []
    if not saltos:
        return
    info = info.get("info", info)             # el director pasa lo que devolvió construir()
    vag = bpy.data.objects[info["vagon_raiz"]]
    for sj in saltos:
        pj = pjs[sj["pj"]]
        raiz = pj["raiz"]
        f_j = int(round(sj["t"] * fps)) + 1
        T_j = info["T0"] + sj["t_contenido"] if "t_contenido" in sj else info["T0"] + sj["t"]
        tray = salto(tuple(sj["local"]), T_j, sj.get("lateral", 4.8), sj.get("arriba", 2.3), sj.get("freno", 14.0), fps,
                     giro_inicial=sj.get("giro_inicial", 0.0))
        raiz.parent = None
        con = raiz.constraints.new("CHILD_OF")
        con.target = vag
        con.inverse_matrix = Matrix.Identity(4)
        con.influence = 1.0
        con.keyframe_insert("influence", frame=1)
        con.influence = 1.0
        con.keyframe_insert("influence", frame=f_j - 1)
        con.influence = 0.0
        con.keyframe_insert("influence", frame=f_j)
        ad = raiz.animation_data
        for fc in K._fcurves(ad.action):
            if fc.data_path in ("location", "rotation_euler"):
                for kp in [kp for kp in fc.keyframe_points if kp.co.x >= f_j - 0.5]:
                    fc.keyframe_points.remove(kp, fast=True)
                fc.update()
        frente = pj["info"].get("frente", math.pi / 2)
        nf = int(round(manifiesto["duracion_s"] * fps))
        # la rodada del clip avanza sola (no es «en el lugar»): cuando arranca el clip siguiente, la raíz se adelanta
        # lo mismo en la dirección de la rodada, así el cuerpo no vuelve para atrás
        f_avance = int(round(sj["avance_desde_s"] * fps)) + 1 if sj.get("avance_desde_s") else None
        for j, (t, pos, rumbo, aire) in enumerate(tray):
            f = f_j + j
            if f > nf + 1:
                break
            if f_avance is not None and f >= f_avance:
                pos = pos + Vector((math.cos(math.radians(rumbo)), math.sin(math.radians(rumbo)), 0.0)) * sj.get("avance_m", 2.9)
                pos.z = altura_suelo(pos.x, pos.y)
            raiz.location = pos
            raiz.rotation_euler = (0, 0, math.radians(rumbo) + frente)
            raiz.keyframe_insert("location", frame=f)
            raiz.keyframe_insert("rotation_euler", frame=f)
        for fc in K._fcurves(raiz.animation_data.action):
            for kp in fc.keyframe_points:
                if kp.co.x >= f_j - 0.5:
                    kp.interpolation = "LINEAR"
        for fc in K._fcurves(raiz.constraints[-1].id_data.animation_data.action):
            if "constraints" in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def fin_del_salto(local: tuple, T_j: float, freno: float, avance_m: float = 2.9) -> tuple:
    """Dónde queda (pies) y hacia dónde mira quien saltó, después de la rodada: el comienzo de la escena 5."""
    tray = salto(local, T_j, freno=freno)
    t, pos, rumbo, _ = tray[-1]
    p = pos + Vector((math.cos(math.radians(rumbo)), math.sin(math.radians(rumbo)), 0.0)) * avance_m
    return (round(p.x, 3), round(p.y, 3), round(altura_suelo(p.x, p.y), 3)), round(rumbo, 1)
