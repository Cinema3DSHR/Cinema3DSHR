"""Vía férrea con detalle real, a lo largo de cualquier `tren.Via`: terraplén de balasto de piedra partida, durmientes
de quebracho con variación, rieles de perfil Vignole (patín, alma y hongo; banda de rodadura brillante y costados
oxidados), placas de asiento y clips en cada durmiente, eclisas en las juntas, tendido telegráfico con crucetas,
aisladores y cables con catenaria, alambrado de 5 hilos, mojones hectométricos y carteles kilométricos, señales
luminosas con gabinete, paso a nivel con tablones y cruces de San Andrés, y una línea de media tensión.

Todo se arma en pocas mallas combinadas (barato de construir y de renderizar). Las piezas finas (placas, clips,
eclisas) se ponen sólo en el tramo [s_detalle0, s_detalle1] donde la cámara se acerca; no se exportan al visor del
EDITOR 3D (`visor_omitir`).

Alturas (m sobre el terreno): tope del riel = `tren.Z_RIEL` (0,45); riel de 0,172 → patín a 0,278; placa de 14 mm;
durmiente de 0,14 con su cara superior a 0,264; balasto hasta 0,245 (los durmientes asoman apenas, como en una vía real).
"""
from __future__ import annotations
import math
import random
import bmesh
import bpy
from mathutils import Vector, Euler
from estudio.blender import kit as K, tren as TR

ALTO_RIEL = 0.172
Z_PATIN = TR.Z_RIEL - ALTO_RIEL
Z_DURMIENTE = Z_PATIN - 0.014
TROCHA = 1.435
MEDIA = TROCHA / 2 + 0.036        # eje del hongo de cada riel (0,7535)


# ------------------------------------------------------------------------------------------------ materiales

def mat_balasto():
    m = bpy.data.materials.get("balasto_piedra")
    if m:
        return m
    m = K.material("balasto_piedra", (0.36, 0.34, 0.31), 0.93)
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 30.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    # piedras: color por celda + bordes oscuros
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.13, 0.12, 0.11, 1)
    ramp.color_ramp.elements[1].color = (0.36, 0.33, 0.29, 1)
    nt.links.new(vor.outputs["Color"], ramp.inputs["Fac"])
    dist = nt.nodes.new("ShaderNodeTexVoronoi")
    dist.feature = "DISTANCE_TO_EDGE"
    dist.inputs["Scale"].default_value = 30.0
    nt.links.new(tc.outputs["Object"], dist.inputs["Vector"])
    borde = nt.nodes.new("ShaderNodeMapRange")
    borde.inputs["From Min"].default_value = 0.0
    borde.inputs["From Max"].default_value = 0.12
    nt.links.new(dist.outputs["Distance"], borde.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMixRGB")
    mul.blend_type = "MULTIPLY"
    mul.inputs["Fac"].default_value = 0.85
    nt.links.new(ramp.outputs["Color"], mul.inputs["Color1"])
    nt.links.new(borde.outputs["Result"], mul.inputs["Color2"])
    nt.links.new(mul.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.9
    bump.inputs["Distance"].default_value = 0.03
    nt.links.new(borde.outputs["Result"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def _mats():
    M = K.material
    return {
        "durmiente": M("durmiente_quebracho", (0.2, 0.15, 0.1), 0.88, ruido=0.45, escala_ruido=7, relieve=0.35),
        "riel": M("riel_oxido", (0.29, 0.17, 0.1), 0.7, 0.55, ruido=0.35, escala_ruido=14, relieve=0.15),
        "banda": M("riel_banda", (0.72, 0.71, 0.7), 0.16, 1.0, ruido=0.08, escala_ruido=40),
        "fijacion": M("fijacion_acero", (0.12, 0.11, 0.1), 0.55, 0.85, ruido=0.2, escala_ruido=20),
        "poste": M("poste_madera_gris", (0.33, 0.29, 0.24), 0.86, ruido=0.35, escala_ruido=6, relieve=0.2),
        "aislador": M("aislador_vidrio", (0.42, 0.62, 0.55), 0.08, 0.0, transmision=0.3),
        "cable": M("cable_cobre", (0.17, 0.12, 0.08), 0.45, 0.9),
        "alambre": M("alambre", (0.45, 0.45, 0.46), 0.4, 1.0),
        "hormigon": M("hormigon_mojon", (0.78, 0.77, 0.74), 0.8, ruido=0.2, escala_ruido=10),
        "negro": M("senal_negro", (0.02, 0.02, 0.02), 0.5),
        "verde": K.emisivo("senal_verde", (0.1, 1.0, 0.35), 18.0),
        "rojo_apag": M("senal_rojo_apagado", (0.25, 0.02, 0.02), 0.2),
        "blanco": M("cartel_blanco", (0.88, 0.88, 0.85), 0.5),
        "rojo": M("cartel_rojo", (0.62, 0.04, 0.04), 0.5),
        "tierra": M("camino_tierra", (0.36, 0.28, 0.2), 0.95, ruido=0.4, escala_ruido=1.2, relieve=0.3),
        "gabinete": M("gabinete_gris", (0.5, 0.52, 0.5), 0.5, 0.6),
    }


# ------------------------------------------------------------------------------------------------ geometría

def marco(via, s: float):
    """(punto, tangente, normal derecha, ángulo de la tangente)."""
    p, t = via.en(s)
    n = Vector((t.y, -t.x, 0)).normalized()
    return p, t, n, math.atan2(t.y, t.x)


_CUBO_V = [(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
           (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)]
_CUBO_F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


class Lote:
    """Muchas cajas y cilindros en una sola malla. tam = (lateral, a lo largo, alto) en el marco de la vía.
    Junta vértices y caras en listas y crea la malla de una vez (bmesh se vuelve cuadrático con miles de piezas)."""

    def __init__(self):
        self.v: list = []
        self.f: list = []

    def caja(self, centro: Vector, ang: float, tam, giro_extra: float = 0.0, inclinar=(0.0, 0.0)):
        e = Euler((inclinar[0], inclinar[1], ang - math.pi / 2 + giro_extra), "XYZ").to_matrix()
        b = len(self.v)
        for x, y, z in _CUBO_V:
            self.v.append(tuple(e @ Vector((x * tam[0], y * tam[1], z * tam[2])) + centro))
        self.f.extend(tuple(b + i for i in cara) for cara in _CUBO_F)

    def cilindro(self, base: Vector, radio: float, alto: float, lados: int = 8, radio_tope: float | None = None):
        rt = radio if radio_tope is None else radio_tope
        b = len(self.v)
        for k in range(lados):
            a = 2 * math.pi * k / lados
            self.v.append((base.x + math.cos(a) * radio, base.y + math.sin(a) * radio, base.z))
        for k in range(lados):
            a = 2 * math.pi * k / lados
            self.v.append((base.x + math.cos(a) * rt, base.y + math.sin(a) * rt, base.z + alto))
        for k in range(lados):
            k2 = (k + 1) % lados
            self.f.append((b + k, b + k2, b + lados + k2, b + lados + k))
        self.f.append(tuple(b + lados + k for k in range(lados)))
        self.f.append(tuple(b + k for k in reversed(range(lados))))

    def objeto(self, nombre, mat, col, omitir_visor=False):
        me = bpy.data.meshes.new(nombre)
        me.from_pydata(self.v, [], self.f)
        me.update()
        ob = bpy.data.objects.new(nombre, me)
        me.materials.append(mat)
        col.objects.link(ob)
        if omitir_visor:
            ob["visor_omitir"] = True
        return ob


def tira(nombre, via, s0, s1, paso, perfil, mat, col, desp=0.0, z0=0.0, cerrar=False, suave=False, uv_escala=0.25):
    """Malla extruida a lo largo de la vía: perfil [(x_lateral, z)…] (x positivo = derecha)."""
    bm = bmesh.new()
    pf = list(perfil) + ([perfil[0]] if cerrar else [])
    anillos = []
    s = s0
    while True:
        p, t, n, _ = marco(via, min(s, s1))
        anillos.append([bm.verts.new(p + n * (desp + x) + Vector((0, 0, z0 + z))) for x, z in pf])
        if s >= s1:
            break
        s += paso
    for a, b in zip(anillos, anillos[1:]):
        for j in range(len(pf) - 1):
            bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (l.vert.co.x * uv_escala, l.vert.co.y * uv_escala + l.vert.co.z * uv_escala)
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    if suave:
        for f in me.polygons:
            f.use_smooth = True
    ob = bpy.data.objects.new(nombre, me)
    me.materials.append(mat)
    col.objects.link(ob)
    return ob


def cables(nombre, tramos: list[list[Vector]], radio: float, mat, col, omitir_visor=True):
    """Curvas (cables, alambres) con espesor real: una spline por tramo."""
    cu = bpy.data.curves.new(nombre, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radio
    cu.bevel_resolution = 1
    cu.use_fill_caps = False
    for pts in tramos:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, q in enumerate(pts):
            sp.points[i].co = (q.x, q.y, q.z, 1.0)
    ob = bpy.data.objects.new(nombre, cu)
    cu.materials.append(mat)
    col.objects.link(ob)
    if omitir_visor:
        ob["visor_omitir"] = True
    return ob


def catenaria(a: Vector, b: Vector, flecha: float, n: int = 10) -> list[Vector]:
    out = []
    for i in range(n + 1):
        k = i / n
        q = a.lerp(b, k)
        q.z -= flecha * 4 * k * (1 - k)
        out.append(q)
    return out


PERFIL_RIEL = [(-0.075, 0.0), (-0.075, 0.011), (-0.02, 0.025), (-0.009, 0.042), (-0.009, 0.124), (-0.033, 0.137),
               (-0.036, 0.163), (-0.03, 0.172), (0.03, 0.172), (0.036, 0.163), (0.033, 0.137), (0.009, 0.124),
               (0.009, 0.042), (0.02, 0.025), (0.075, 0.011), (0.075, 0.0)]


def construir(via, col, *, s0: float = 0.0, s1: float | None = None, s_detalle0: float = 0.0, s_detalle1: float | None = None,
              lado_ruta: float = 34.0, semilla: int = 7, pasos_a_nivel=(), senales=(), km_inicial: float = 312.0) -> dict:
    """Arma la vía entre s0 y s1. Devuelve {"postes": [...], "pasos_a_nivel": [...]} para ubicar otras cosas."""
    s1 = via.largo if s1 is None else s1
    sd0, sd1 = max(s0, s_detalle0), min(s1, via.largo if s_detalle1 is None else s_detalle1)
    rnd = random.Random(semilla)
    m = _mats()

    # terraplén de balasto (taludes + banquina de piedra) y una franja de tierra apisonada al pie
    tira("terraplen", via, s0, s1, 3.0, [(-4.4, -0.06), (-3.0, 0.15), (-1.7, 0.245), (1.7, 0.245), (3.0, 0.15), (4.4, -0.06)],
         mat_balasto(), col, uv_escala=1.0)
    tira("pie_terraplen", via, s0, s1, 4.0, [(-6.0, -0.045), (-4.3, -0.04)], m["tierra"], col)
    tira("pie_terraplen_d", via, s0, s1, 4.0, [(4.3, -0.04), (6.0, -0.045)], m["tierra"], col)

    # durmientes con variación (posición, giro, altura y largo: madera vieja, no clonada)
    dur = Lote()
    s = s0
    while s <= s1:
        p, t, n, ang = marco(via, s + rnd.uniform(-0.025, 0.025))
        c = p + n * rnd.uniform(-0.03, 0.03) + Vector((0, 0, Z_DURMIENTE - 0.07 - rnd.uniform(0, 0.012)))
        dur.caja(c, ang, (2.75 + rnd.uniform(-0.05, 0.05), 0.24 + rnd.uniform(-0.015, 0.015), 0.14),
                 giro_extra=math.radians(rnd.uniform(-1.6, 1.6)))
        s += 0.65
    dur.objeto("durmientes", m["durmiente"], col)

    # rieles (perfil Vignole) con la banda de rodadura pulida arriba
    for lado in (-1, 1):
        tira(f"riel_{'i' if lado < 0 else 'd'}", via, s0, s1, 2.0, PERFIL_RIEL, m["riel"], col, desp=lado * MEDIA,
             z0=Z_PATIN, cerrar=True)
        tira(f"riel_banda_{'i' if lado < 0 else 'd'}", via, s0, s1, 2.0, [(-0.027, 0.1722), (0.027, 0.1722)], m["banda"], col,
             desp=lado * MEDIA, z0=Z_PATIN)

    # placas de asiento, clips elásticos y tirafondos (sólo en el tramo de detalle)
    fij = Lote()
    s = sd0
    while s <= sd1:
        p, t, n, ang = marco(via, s)
        for lado in (-1, 1):
            cr = p + n * (lado * MEDIA)
            fij.caja(cr + Vector((0, 0, Z_DURMIENTE + 0.007)), ang, (0.34, 0.17, 0.014))
            for k in (-1, 1):
                q = cr + n * (k * 0.092)
                fij.caja(q + Vector((0, 0, Z_PATIN + 0.016)), ang, (0.05, 0.075, 0.03))
                fij.cilindro(q + n * (k * 0.06) + Vector((0, 0, Z_DURMIENTE + 0.014)), 0.016, 0.02, 6)
        s += 0.65
    # eclisas (juntas cada 18 m: también marcan el «tac-tac» del sonido)
    s = sd0 - (sd0 % 18.0)
    while s <= sd1:
        p, t, n, ang = marco(via, s)
        for lado in (-1, 1):
            for k in (-1, 1):
                fij.caja(p + n * (lado * MEDIA + k * 0.017) + Vector((0, 0, Z_PATIN + 0.083)), ang, (0.018, 0.62, 0.075))
        s += 18.0
    fij.objeto("fijaciones", m["fijacion"], col, omitir_visor=True)

    # tendido telegráfico: postes de madera, 2 crucetas, 8 aisladores y 8 cables con catenaria
    postes, tram = [], []
    pos_l = Lote()
    cru = Lote()
    ais = Lote()
    s = s0 + 30
    while s <= s1 - 30:
        p, t, n, ang = marco(via, s)
        base = p + n * -7.6 + Vector((0, 0, -0.3))
        incl = (math.radians(rnd.uniform(-1.2, 1.2)), math.radians(rnd.uniform(-1.2, 1.2)))
        pos_l.cilindro(base, 0.13, 8.4, 8, 0.1)
        tope = base + Vector((0, 0, 8.4))
        ptos = []
        for k, zc in enumerate((7.85, 7.2)):
            cc = base + Vector((0, 0, zc))
            cru.caja(cc, ang, (1.9, 0.1, 0.11))
            for j, x in enumerate((-0.82, -0.36, 0.36, 0.82)):
                q = cc + n * x
                ais.cilindro(q + Vector((0, 0, 0.055)), 0.035, 0.1, 8, 0.022)
                ptos.append(q + Vector((0, 0, 0.13)))
        postes.append((s, base, ang))
        tram.append(ptos)
        s += 55.0
    pos_l.objeto("postes_telegrafo", m["poste"], col)
    cru.objeto("crucetas", m["poste"], col)
    ais.objeto("aisladores", m["aislador"], col, omitir_visor=True)
    hilos = []
    for a, b in zip(tram, tram[1:]):
        for qa, qb in zip(a, b):
            hilos.append(catenaria(qa, qb, 0.42 + rnd.uniform(-0.05, 0.05), 12))
    cables("cables_telegrafo", hilos, 0.006, m["cable"], col)

    # alambrado de 5 hilos a ambos lados de la franja ferroviaria (postes cada 4 m, esquineros cada 100 m)
    d_der = min(22.0, lado_ruta - 8.5) if lado_ruta - 8.5 > 5.0 else lado_ruta + 7.5   # ruta pegada: alambrado del otro lado
    for lado, d in ((-1, 22.0), (1, d_der)):
        pl = Lote()
        hilos_a = [[] for _ in range(5)]
        s, k = s0, 0
        while s <= s1:
            p, t, n, ang = marco(via, s)
            base = p + n * (lado * d) + Vector((0, 0, -0.05))
            if k % 25 == 0:
                pl.cilindro(base, 0.09, 1.55, 8)
            else:
                pl.caja(base + Vector((0, 0, 0.62)), ang + rnd.uniform(-0.1, 0.1), (0.075, 0.075, 1.25))
            for h in range(5):
                hilos_a[h].append(base + Vector((0, 0, 0.3 + h * 0.21)))
            s += 4.0
            k += 1
        pl.objeto(f"alambrado_postes_{'i' if lado < 0 else 'd'}", m["poste"], col)
        cables(f"alambrado_hilos_{'i' if lado < 0 else 'd'}", hilos_a, 0.0022, m["alambre"], col)

    # mojones hectométricos y carteles kilométricos (con el número)
    moj = Lote()
    s = s0 - (s0 % 100.0) + 100.0
    while s <= s1:
        p, t, n, ang = marco(via, s)
        moj.caja(p + n * 3.9 + Vector((0, 0, 0.35)), ang, (0.16, 0.16, 0.8))
        if int(round(s)) % 1000 == 0:
            q = p + n * 4.4
            moj.caja(q + Vector((0, 0, 1.1)), ang, (0.08, 0.08, 2.2))
            km = km_inicial + s / 1000.0
            tx = bpy.data.curves.new(f"km_{int(s)}", "FONT")
            tx.body = f"{km:.0f}"
            tx.size = 0.36
            tx.align_x = "CENTER"
            tx.extrude = 0.004
            o = bpy.data.objects.new(f"cartel_km_{int(s)}", tx)
            tx.materials.append(m["negro"])
            col.objects.link(o)
            o.location = q + Vector((0, 0, 2.05)) - n * 0.03
            o.rotation_euler = (math.pi / 2, 0, ang + math.pi)
            K.caja(f"cartel_km_tabla_{int(s)}", q + Vector((0, 0, 2.15)), (0.9, 0.04, 0.55), m["blanco"], col, rot_z=ang)
        s += 100.0
    moj.objeto("mojones", m["hormigon"], col)

    # señales luminosas (mástil, pantalla negra, foco verde encendido y rojo apagado, gabinete al pie)
    for sn in senales:
        p, t, n, ang = marco(via, sn)
        base = p + n * 2.9
        K.cilindro(f"senal_{int(sn)}_mastil", base + Vector((0, 0, 2.6)), 0.08, 5.2, m["gabinete"], col, lados=10)
        K.caja(f"senal_{int(sn)}_pantalla", base + Vector((0, 0, 5.0)) - t * 0.12, (0.62, 0.08, 1.05), m["negro"], col, rot_z=ang)
        for z, mt in ((5.25, m["verde"]), (4.8, m["rojo_apag"])):
            o = K.cilindro(f"senal_{int(sn)}_foco_{z}", base + Vector((0, 0, z)) - t * 0.17, 0.11, 0.04, mt, col, lados=16, eje="Y")
            o.rotation_euler.z = ang - math.pi / 2
        K.caja(f"senal_{int(sn)}_gabinete", base + n * 1.2 + Vector((0, 0, 0.6)), (0.6, 0.45, 1.2), m["gabinete"], col, rot_z=ang)

    # pasos a nivel: camino de tierra que cruza, tablones entre rieles y cruces de San Andrés
    pn = []
    for sp_ in pasos_a_nivel:
        p, t, n, ang = marco(via, sp_)
        bm = bmesh.new()
        filas = []
        for i in range(-60, int(lado_ruta / 2.0) + 1):
            d = i * 2.0
            z = -0.04 + (TR.Z_RIEL - 0.03 + 0.04) * max(0.0, 1.0 - max(0.0, abs(d) - 3.0) / 9.0)
            fila = [bm.verts.new(p + n * d + t * w + Vector((0, 0, z))) for w in (-3.2, 3.2)]
            filas.append(fila)
        for a, b in zip(filas, filas[1:]):
            bm.faces.new((a[0], a[1], b[1], b[0]))
        me = bpy.data.meshes.new(f"paso_nivel_{int(sp_)}")
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(me.name, me)
        me.materials.append(m["tierra"])
        col.objects.link(ob)
        tab = Lote()
        for x in (-0.47, 0.0, 0.47, -1.08, 1.08):
            tab.caja(p + n * x + Vector((0, 0, TR.Z_RIEL - 0.02)), ang + math.pi / 2, (6.0, 0.3 if abs(x) < 1 else 0.42, 0.06))
        tab.objeto(f"paso_nivel_{int(sp_)}_tablones", m["durmiente"], col)
        for k in (-1, 1):
            q = p + n * (k * 4.2) + t * (k * 3.8)
            K.cilindro(f"cruz_{int(sp_)}_{k}_poste", q + Vector((0, 0, 1.6)), 0.05, 3.2, m["blanco"], col, lados=8)
            for g in (1, -1):
                b = K.caja(f"cruz_{int(sp_)}_{k}_{g}", q + Vector((0, 0, 2.9)), (1.25, 0.03, 0.2), m["rojo" if g > 0 else "blanco"], col)
                b.rotation_euler = (0, math.radians(35 * g), ang)
        pn.append((sp_, p, n))

    # línea de media tensión del otro lado de la ruta (postes de hormigón, ménsula y 3 cables)
    mt = Lote()
    tramos_mt = []
    s = s0 + 15
    while s <= s1 - 15:
        p, t, n, ang = marco(via, s)
        base = p + n * (lado_ruta + 12.0) + Vector((0, 0, -0.3))
        mt.cilindro(base, 0.16, 10.5, 10, 0.1)
        mt.caja(base + Vector((0, 0, 9.9)), ang, (1.6, 0.12, 0.14))
        tramos_mt.append([base + Vector((0, 0, 10.05)) + n * x for x in (-0.7, 0.0, 0.7)])
        s += 80.0
    mt.objeto("postes_media_tension", m["hormigon"], col)
    cab = []
    for a, b in zip(tramos_mt, tramos_mt[1:]):
        for qa, qb in zip(a, b):
            cab.append(catenaria(qa, qb, 0.9, 12))
    cables("cables_media_tension", cab, 0.008, m["alambre"], col)

    # delineadores de la ruta (postes blancos con reflectante) cada 40 m en las dos banquinas
    dl = Lote()
    s = s0
    while s <= s1:
        p, t, n, ang = marco(via, s)
        for x in (-5.6, 5.6):
            if lado_ruta + x < 5.0:
                continue                     # no sobre el terraplén de la vía
            dl.caja(p + n * (lado_ruta + x) + Vector((0, 0, 0.55)), ang, (0.1, 0.1, 1.1))
        s += 40.0
    dl.objeto("delineadores", m["blanco"], col)
    return {"postes": postes, "pasos_a_nivel": pn}
