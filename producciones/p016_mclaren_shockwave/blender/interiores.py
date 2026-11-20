"""p016 · interiores comerciales detrás de las vidrieras, hechos con muebles de Sweet Home 3D (orientación verificada: el frente mira hacia −Y al importar).
Tres rubros: restaurante (mesas con sillas enfrentadas, barra con banquetas, lámparas colgantes), supermercado (góndolas mirando a la vidriera, heladeras, cajones de fruta)
y tienda de muebles (sofás y sillones mirando a la calle, mesas ratonas, bibliotecas)."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import sh3d

PROF = 12.5          # profundidad que se amuebla (m); más atrás hay un muro


def _mat_piso(nombre, color, rug=0.35):
    return mat(nombre, color, rug=rug)


def mat_productos():
    """Fondo de góndola: bloques de colores vivos (envases) con brillo suave."""
    m = bpy.data.materials.get("productos_gondola")
    if m:
        return m
    m = bpy.data.materials.new("productos_gondola")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    M = lambda op, a=None, c=None: lib._mm(nt, op, a, c)
    cu = M("MULTIPLY", sep.outputs["X"], 4.0)
    cv = M("MULTIPLY", sep.outputs["Z"], 3.0)
    vc = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(M("FLOOR", cu), vc.inputs["X"])
    nt.links.new(M("FLOOR", cv), vc.inputs["Y"])
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    nt.links.new(vc.outputs[0], wn.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.9
    hsv.inputs["Value"].default_value = 1.0
    nt.links.new(wn.outputs["Value"], hsv.inputs["Hue"])
    hsv.inputs["Color"].default_value = (0.9, 0.2, 0.2, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(hsv.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.4
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def _caparazon(col, y0, sx, largo, pared, piso, luz_color, luz_fuerza, rng):
    X0 = ciudadX = 17.0
    xc = sx * (X0 + 0.25 + PROF / 2)
    caja("piso_int", (xc, y0 + largo / 2, 0.03), (PROF, largo, 0.06), col, piso)
    caja("muro_fondo", (sx * (X0 + 0.25 + PROF + 0.1), y0 + largo / 2, 4.1), (0.2, largo, 8.2), col, pared)
    caja("techo_int", (xc, y0 + largo / 2, 8.2), (PROF, largo, 0.1), col, pared)
    em = mat_emisivo("luz_techo_" + str(int(luz_fuerza * 10)), luz_color, luz_fuerza)
    for k in range(7):
        caja("panel_luz", (xc, y0 + 2.0 + k * (largo - 4.0) / 6.0, 8.1), (PROF - 1.5, 0.45, 0.04), col, em)


def restaurante(col, y0, sx, largo, rng):
    pared = mat("pared_rest", (0.45, 0.32, 0.2), rug=0.6)
    piso = mat("piso_rest", (0.16, 0.1, 0.06), rug=0.3)
    _caparazon(col, y0, sx, largo, pared, piso, (1.0, 0.68, 0.32), 2.6, rng)
    lamp = mat_emisivo("lampara_colgante", (1.0, 0.72, 0.35), 18.0)
    sillas = ["chair_cafe_chair", "chair_oak_chair", "chair_chair_6"]
    sx_ = sx
    por_mesa = []
    for fila, d in enumerate((2.3, 5.6, 8.6)):
        n = 5
        for i in range(n):
            u = 2.7 + i * (largo - 5.4) / (n - 1)
            pos = Vector((sx * (17.0 + 0.6 + d), y0 + u + rng.uniform(-0.3, 0.3), 0))
            grande = (i + fila) % 2 == 0
            mesa = "table_oak_table" if grande else "table_cafe_table"
            sh3d.poner(mesa, col, pos, frente=(1, 0))
            r = 0.95 if grande else 0.62
            n_sillas = 4 if grande else 2
            ang0 = rng.uniform(0, 1.5)
            for s in range(n_sillas):
                a = ang0 + s * (2 * math.pi / n_sillas) if n_sillas == 4 else ang0 + s * math.pi
                sp = pos + Vector((math.cos(a) * r, math.sin(a) * r, 0))
                sh3d.poner(rng.choice(sillas), col, sp, frente=(-math.cos(a), -math.sin(a)))     # el frente de la silla mira a la mesa
            esfera("lampara", pos + Vector((0, 0, 3.0)), 0.17, col, lamp, 10, 6)
    # barra al fondo con banquetas enfrentadas
    for i in range(8):
        u = 2.0 + i * (largo - 4.0) / 7.0
        sh3d.poner("table_bar_table", col, Vector((sx * (17.0 + 0.6 + 11.3), y0 + u, 0)), frente=(-sx, 0))
        sh3d.poner("chair_bar_stool_2", col, Vector((sx * (17.0 + 0.6 + 10.3), y0 + u, 0)), frente=(sx, 0))
    for i in range(3):      # plantas
        sh3d.poner("bush_plant_3", col, Vector((sx * (17.0 + 1.0), y0 + 1.5 + i * 12.0, 0)), frente=(-sx, 0), escala=1.3)


def supermercado(col, y0, sx, largo, rng):
    pared = mat("pared_super", (0.8, 0.8, 0.78), rug=0.5)
    piso = mat("piso_super", (0.3, 0.3, 0.28), rug=0.2)
    _caparazon(col, y0, sx, largo, pared, piso, (0.95, 0.97, 1.0), 3.2, rng)
    prod = mat_productos()
    for fila, d in enumerate((3.4, 6.6, 9.8)):
        xg = sx * (17.0 + 0.6 + d)
        # fondo de colores vivos detrás de las góndolas (se ve a través de los estantes)
        pl = caja("productos", (xg + sx * 0.18, y0 + largo / 2, 1.0), (0.02, largo - 1.5, 1.8), col, prod)
        n = int((largo - 2.0) / 0.8)
        for i in range(n):
            sh3d.poner("shelf_steel_shelves", col, Vector((xg, y0 + 1.0 + i * 0.8 + 0.4, 0)), frente=(-sx, 0))
    for i in range(12):
        sh3d.poner("fridge_large_fridge", col, Vector((sx * (17.0 + 0.6 + 11.6), y0 + 1.4 + i * (largo - 2.8) / 11, 0)), frente=(-sx, 0))
    # cajones de fruta junto a la vidriera
    frutas = [mat_emisivo("fruta_" + n, c, 0.9) for n, c in (("roja", (0.9, 0.05, 0.03)), ("naranja", (0.95, 0.4, 0.02)), ("verde", (0.25, 0.7, 0.05)), ("amarilla", (0.95, 0.8, 0.05)))]
    for i in range(6):
        u = 3.0 + i * (largo - 6.0) / 5
        for k in range(2):
            base = Vector((sx * (17.0 + 0.9 + k * 0.5), y0 + u, 0))
            sh3d.poner("crate_crate", col, base, frente=(-sx, 0))
            for q in range(7):
                esfera("fruta", base + Vector((rng.uniform(-0.2, 0.2), rng.uniform(-0.15, 0.15), 0.23)), 0.05, col, rng.choice(frutas), 8, 6)


def muebles(col, y0, sx, largo, rng):
    pared = mat("pared_mueb", (0.55, 0.5, 0.42), rug=0.5)
    piso = mat("piso_mueb", (0.22, 0.2, 0.17), rug=0.3)
    _caparazon(col, y0, sx, largo, pared, piso, (1.0, 0.8, 0.5), 2.2, rng)
    alfombra = mat("alfombra", (0.35, 0.12, 0.1), rug=0.9)
    sofas = ["sofa_sofa_2", "sofa_couch_2", "sofa_large_couch", "sofa_sofa_3"]
    sillones = ["armchair_armchair_9", "armchair_armchair_10", "armchair_armchair_13"]
    for i in range(3):
        u = 5.0 + i * (largo - 10.0) / 2
        xs = sx * (17.0 + 0.6 + 3.2)
        caja("alfombra", (xs, y0 + u, 0.07), (4.0, 4.6, 0.02), col, alfombra)
        # sofá de espaldas al fondo, mirando a la calle; sillones laterales enfrentados; mesa ratona al centro
        sh3d.poner(sofas[i % len(sofas)], col, Vector((sx * (17.0 + 0.6 + 4.7), y0 + u, 0)), frente=(-sx, 0))
        for lado in (-1, 1):
            sh3d.poner(sillones[(i + lado) % len(sillones)], col, Vector((sx * (17.0 + 0.6 + 3.2), y0 + u + lado * 2.1, 0)), frente=(0, -lado))
        sh3d.poner("sofa_couch_table", col, Vector((sx * (17.0 + 0.6 + 3.2), y0 + u, 0)), frente=(-sx, 0))
        sh3d.poner("table_bedside_table", col, Vector((sx * (17.0 + 0.6 + 4.9), y0 + u + 2.0, 0)), frente=(-sx, 0))
        sh3d.poner("table_desk_lamp", col, Vector((sx * (17.0 + 0.6 + 4.9), y0 + u + 2.0, 0.55)), frente=(-sx, 0))
    for i in range(10):
        sh3d.poner("shelf_bookcase_3", col, Vector((sx * (17.0 + 0.6 + 11.5), y0 + 1.6 + i * 2.9, 0)), frente=(-sx, 0))
    for i in range(2):
        sh3d.poner("bush_plant_3", col, Vector((sx * (17.0 + 1.0), y0 + 2.0 + i * 24.0, 0)), frente=(-sx, 0), escala=1.4)


TIPOS = [restaurante, supermercado, muebles]
