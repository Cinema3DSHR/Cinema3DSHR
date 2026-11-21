"""p017 · casas: muros con aberturas reales (puertas y ventanas de Sweet Home 3D calzadas en el hueco), techo, pasto, cerco y árboles.
La fachada principal mira hacia −Y (sur). Los modelos de Sweet Home miran hacia −Y al importarse: una abertura en un muro cuya normal exterior es n usa frente=n."""
import math
import random
import bpy
from mathutils import Vector
import lib
from lib import *
import sh3d

ESP = 0.28


def muro(col, nombre, centro, largo, alto, eje, mat_, aberturas=(), espesor=ESP):
    """Muro a lo largo de `eje` ('x' o 'y') centrado en `centro` (x,y,z base). `aberturas` = [(u, ancho, z0, alto)] con u = posición a lo largo del muro desde su centro."""
    # piezas entre aberturas: se arma por franjas verticales
    ab = sorted(aberturas, key=lambda a: a[0])
    cortes = [-largo / 2]
    piezas = []
    for u, w, z0, h in ab:
        piezas.append((cortes[-1], u - w / 2, 0.0, alto))          # tramo lleno antes de la abertura
        if z0 > 0.01:
            piezas.append((u - w / 2, u + w / 2, 0.0, z0))        # antepecho
        if z0 + h < alto - 0.01:
            piezas.append((u - w / 2, u + w / 2, z0 + h, alto))   # dintel
        cortes.append(u + w / 2)
    piezas.append((cortes[-1], largo / 2, 0.0, alto))
    objs = []
    for a, b, z0, z1 in piezas:
        if b - a < 0.01 or z1 - z0 < 0.01:
            continue
        uc = (a + b) / 2
        if eje == "x":
            c = (centro[0] + uc, centro[1], centro[2] + (z0 + z1) / 2)
            d = (b - a, espesor, z1 - z0)
        else:
            c = (centro[0], centro[1] + uc, centro[2] + (z0 + z1) / 2)
            d = (espesor, b - a, z1 - z0)
        objs.append(caja(nombre, c, d, col, mat_))
    return objs


def casa(col, O, ancho, fondo, alto, estilo="moderna", rng=None, color=(0.75, 0.72, 0.66), interior_luz=(1.0, 0.7, 0.35), techo_color=(0.08, 0.08, 0.09)):
    """Casa de una planta con la fachada hacia −Y. Devuelve datos útiles (posición de la puerta, jardín, etc.)."""
    rng = rng or random.Random(3)
    O = Vector(O)
    pared = mat_ruido("pared_casa_" + estilo, tuple(c * 0.85 for c in color), color, 3.0, rug=0.75, bump=0.15)
    techo = mat("techo_casa_" + estilo, techo_color, rug=0.6)
    piso = mat("piso_casa", (0.32, 0.22, 0.14), rug=0.3)
    inte = mat_emisivo("interior_casa_luz", interior_luz, 2.4)
    # losa
    caja("losa", O + Vector((0, fondo / 2, 0.1)), (ancho + 0.6, fondo + 0.6, 0.2), col, mat("losa", (0.3, 0.3, 0.3), rug=0.8))
    z0 = 0.2
    ab_frente = []
    # puerta + ventanales en el frente
    n_vent = max(2, int(ancho // 3.2))
    puerta_u = 0.0
    ab_frente.append((puerta_u, 1.12, 0.0, 2.05))
    for k in range(n_vent):
        u = -ancho / 2 + (k + 0.5) * ancho / n_vent
        if abs(u - puerta_u) < 1.5:
            continue
        ab_frente.append((u, min(2.6, ancho / n_vent - 0.7), 0.35, 2.2 if estilo == "moderna" else 1.4))
    muro(col, "muro_frente", O + Vector((0, 0.0, z0)), ancho, alto, "x", pared, ab_frente)
    muro(col, "muro_fondo", O + Vector((0, fondo, z0)), ancho, alto, "x", pared)
    muro(col, "muro_izq", O + Vector((-ancho / 2, fondo / 2, z0)), fondo, alto, "y", pared, [(0.0, 1.6, 0.9, 1.3)])
    muro(col, "muro_der", O + Vector((ancho / 2, fondo / 2, z0)), fondo, alto, "y", pared, [(0.0, 1.6, 0.9, 1.3)])
    # interior: piso, techo y un muro emisivo cálido detrás de las aberturas (se ve a través de los vidrios)
    caja("piso_int", O + Vector((0, fondo / 2, z0 + 0.02)), (ancho - 0.4, fondo - 0.4, 0.04), col, piso)
    caja("luz_int", O + Vector((0, fondo - 0.6, z0 + alto / 2)), (ancho - 0.6, 0.05, alto - 0.3), col, inte)
    # techo
    if estilo == "moderna":
        caja("techo", O + Vector((0, fondo / 2, z0 + alto + 0.18)), (ancho + 1.6, fondo + 1.6, 0.36), col, techo)
    else:
        # techo a dos aguas: dos planos inclinados
        h = 1.8
        for sg in (-1, 1):
            c = O + Vector((0, fondo / 2 + sg * (fondo / 4), z0 + alto + h / 2))
            plano = caja("techo_agua", c, (ancho + 1.0, math.hypot(fondo / 2, h) + 0.6, 0.18), col, techo)
            plano.rotation_euler = (sg * math.atan2(h, fondo / 2) * -1 if False else -sg * math.atan2(h, fondo / 2), 0, 0)
    # abertura: puerta de entrada y ventanas de Sweet Home calzadas en los huecos
    sh3d.poner("front_door", col, O + Vector((puerta_u, -0.02, z0)), frente=(0, -1))
    for u, w, zz, hh in ab_frente[1:]:
        sh3d.poner("patio_glass_door_unit" if estilo == "moderna" else "double_window", col, O + Vector((u, -0.02, z0 + zz)), frente=(0, -1), escala=1.0)
    return {"puerta": O + Vector((puerta_u, -0.2, z0)), "alto": alto + z0}


def jardin(col, O, ancho, fondo, rng, arboles=6, cerco=True, pasto_color=(0.09, 0.22, 0.05)):
    O = Vector(O)
    pasto = mat_ruido("pasto_jardin", tuple(c * 0.7 for c in pasto_color), pasto_color, 14.0, rug=0.9, bump=0.5)
    caja("pasto", O + Vector((0, -8.0 + fondo / 2, 0.0)), (ancho + 40, fondo + 40, 0.12), col, pasto)
    camino = mat("camino", (0.35, 0.33, 0.3), rug=0.7)
    caja("camino", O + Vector((0, -5.0, 0.13)), (1.8, 10.0, 0.04), col, camino)
    if cerco:
        for sx in (-1, 1):
            for k in range(14):
                y = -10.0 + k * 0.85
                sh3d.poner("fence_picket", col, O + Vector((sx * (ancho / 2 + 2.2), y, 0.12)), frente=(-sx, 0))
        for k in range(int((ancho + 4.4) / 0.85)):
            x = -(ancho + 4.4) / 2 + k * 0.85 + 0.42
            if abs(x) < 1.2:
                continue
            sh3d.poner("fence_picket", col, O + Vector((x, -10.0, 0.12)), frente=(0, -1))
    sh3d.preparar_arbol("tree_tree", semilla=7, copias=6)
    for k in range(arboles):
        sx = -1 if k % 2 == 0 else 1
        pos = O + Vector((sx * rng.uniform(ancho / 2 + 1.0, ancho / 2 + 6.0), rng.uniform(-9.0, 2.0), 0.1))
        sh3d.poner("tree_tree", col, pos, frente=(0, -1), escala=rng.uniform(0.9, 1.4))
