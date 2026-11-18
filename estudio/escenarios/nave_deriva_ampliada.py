"""La nave de «A la deriva» AMPLIADA (desde E02): el mismo centro de operaciones del E01 (nave_deriva, sin tocarlo)
más un recorrido físico y continuo hacia popa, todo sobre el eje x = 0 (se camina derecho hacia −Y):

  centro de operaciones (y 3,0 → −3,2) → pasillo de tránsito (−3,2 → −10,2, el del E01, ahora abierto y con
  señalética) → PASILLO BOTÁNICO (−10,2 → −20,2): incubadoras de vidrio a los dos lados con flores procedurales
  vivas (se mecen con el aire), raíces en el agua, sustrato, gotas en el vidrio y luz de cultivo cálida; bandeja de
  poda con una flor cortada → COMEDOR (−20,2 → −32,2): amplio, institucional, mesas largas, banquetas, estanterías con
  comida sellada no perecedera (raciones, envases, bebidas, botellas de agua), ventanal al espacio; la mesa de Kate
  sola al fondo, con su pantalla personal.

En el centro de operaciones el monitor central muestra la cámara de vigilancia del comedor (CAM 04).
El casco exterior del E01 se quita (sus tapas atravesaban los pasillos nuevos; este capítulo no tiene tomas afuera).

Utilería que pasa de mano en mano (parámetro «utileria» del escenario; la arma `despues_personajes`): cada objeto
tiene tramos «en la bandeja / en la mano de Aiden / sobre la mesa / en la mano de Kate»; en cada tramo se ve una copia.
"""
from __future__ import annotations

import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

from estudio.blender import flores as FL
from estudio.blender import kit as K
from estudio.escenarios import nave_deriva as ND
from estudio.escenarios.nave_deriva import eva_habla, luces_navegacion, estado_kate   # noqa: F401 (eventos)

PLANTAS_SH3D = ["bush_spider_plant", "bush_indoor_plant", "bush_plant_2"]
DEPENDENCIAS = list(ND.DEPENDENCIAS) + [f"sh3d:models/{n}.glb" for n in PLANTAS_SH3D] + \
    ["sh3d:models/bush_indoor_plant_leaf.jpg", "sh3d:models/bush_plant_2_leaf.jpg"]
PARAMETROS = {"semilla": 11, "semilla_flores": 23}

PAS = {"y0": -3.2, "y1": -10.2, "x": 0.95, "alto": 2.5}            # pasillo de tránsito (el del E01)
BOT = {"y0": -10.2, "y1": -20.2, "x": 1.8, "alto": 2.8}            # pasillo botánico
COM = {"y0": -20.2, "y1": -32.2, "x": 6.5, "alto": 3.4}            # comedor
PUERTA = 0.95                                                      # media puerta (todas las puertas del recorrido)
BANDEJA = Vector((-1.12, -15.84, 0.68))                             # bandeja de poda en un carrito (a la derecha de Aiden)
MESA_KATE = Vector((0.0, -30.0, 0.0))                              # mesa de Kate (centro, al piso)
MESA_ALTO = 0.75
KATE_SILLA = Vector((0.0, -30.62, 0.0))                            # Kate sentada, mira a +Y (hacia la puerta)
AIDEN_MESA = Vector((0.0, -29.32, 0.0))                            # donde se para Aiden, del otro lado de la mesa


def _lin(c):
    return ND._lin(c)


# ------------------------------------------------------------------------------------------------ materiales
def _materiales():
    M = {}
    M["pared"] = K.material("pared_panel", (0.20, 0.22, 0.25), 0.55, 0.35, ladrillo=((0.16, 0.17, 0.20), 1.6),
                            relieve=0.15)
    M["gris"] = K.material("metal_gris", (0.32, 0.34, 0.37), 0.4, 0.7, ruido=0.15)
    M["oscuro"] = K.material("metal_oscuro", (0.07, 0.075, 0.085), 0.45, 0.6)
    M["piso"] = K.material("piso_rejilla", (0.10, 0.11, 0.12), 0.6, 0.6, ladrillo=((0.05, 0.05, 0.06), 6.0), relieve=0.3)
    M["tira"] = K.emisivo("tira_azul", (0.25, 0.6, 1.0), 4.0)
    M["plafon"] = K.emisivo("plafon", (0.75, 0.85, 1.0), 3.0)
    M["ambar"] = K.emisivo("led_ambar", (1.0, 0.55, 0.1), 12.0)
    M["rojo"] = K.emisivo("led_rojo", (1.0, 0.06, 0.05), 12.0)
    M["blanco_calido"] = K.emisivo("luz_cultivo", (1.0, 0.86, 0.72), 6.0)
    M["cultivo_rosa"] = K.emisivo("luz_cultivo_rosa", (1.0, 0.55, 0.75), 3.0)
    M["pared_bot"] = K.material("pared_botanica", (0.78, 0.80, 0.78), 0.5, 0.1, ruido=0.08)
    M["piso_bot"] = K.material("piso_botanico", (0.30, 0.31, 0.30), 0.55, 0.2, ladrillo=((0.26, 0.27, 0.26), 3.0),
                               relieve=0.1)
    M["gabinete"] = K.material("gabinete_blanco", (0.82, 0.84, 0.86), 0.35, 0.2)
    M["sustrato"] = K.material("sustrato", (0.09, 0.06, 0.04), 0.9, 0.0, ruido=0.4, escala_ruido=40, relieve=0.4)
    M["raiz"] = K.material("raiz", (0.86, 0.80, 0.66), 0.6, 0.0, ruido=0.2)
    M["agua"] = K.material("agua_tanque", (0.70, 0.88, 0.92), 0.05, 0.0, alfa=0.35, transmision=1.0, ior=1.33,
                           mezcla="BLENDED")
    M["gota"] = K.material("gota", (0.9, 0.95, 1.0), 0.02, 0.0, alfa=0.45, transmision=1.0, ior=1.33, mezcla="BLENDED")
    v = bpy.data.materials.new("vidrio_incubadora")
    v.use_nodes = True
    b = v.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.92, 0.97, 1.0, 1)
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["IOR"].default_value = 1.5
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Alpha"].default_value = 0.10
    v.surface_render_method = "BLENDED"
    v["estudio"] = {"color": [0.92, 0.97, 1.0], "rugosidad": 0.03, "metal": 0.0, "emision": None, "fuerza": 0.0,
                    "alfa": 0.10}
    M["vidrio"] = v
    M["mesa"] = K.material("mesa_comedor", (0.55, 0.57, 0.60), 0.35, 0.3, ruido=0.05)
    M["tapa_mesa"] = K.material("tapa_mesa", (0.80, 0.81, 0.82), 0.3, 0.0, ruido=0.04)
    M["asiento"] = K.material("asiento", (0.18, 0.30, 0.42), 0.6, 0.0)
    M["estante"] = K.material("estante", (0.40, 0.42, 0.45), 0.4, 0.6)
    M["pared_com"] = K.material("pared_comedor", (0.55, 0.58, 0.60), 0.6, 0.15, ladrillo=((0.50, 0.53, 0.56), 1.2),
                                relieve=0.08)
    M["piso_com"] = K.material("piso_comedor", (0.22, 0.24, 0.26), 0.45, 0.1, ladrillo=((0.19, 0.21, 0.23), 2.0),
                               relieve=0.1)
    M["botella"] = K.material("botella_agua", (0.75, 0.88, 0.95), 0.05, 0.0, alfa=0.4, transmision=1.0, ior=1.33,
                              mezcla="BLENDED")
    M["tapa_azul"] = K.material("tapa_botella", (0.10, 0.35, 0.80), 0.4, 0.0)
    for nom, colr in (("racion_blanca", (0.85, 0.86, 0.84)), ("racion_naranja", (0.85, 0.45, 0.15)),
                      ("racion_verde", (0.30, 0.55, 0.35)), ("racion_gris", (0.45, 0.47, 0.50)),
                      ("racion_azul", (0.25, 0.40, 0.65)), ("lata", (0.70, 0.72, 0.74))):
        M[nom] = K.material(nom, colr, 0.5 if nom != "lata" else 0.25, 0.0 if nom != "lata" else 0.9)
    return M


def _pantalla(nombre, im, fuerza=2.0):
    return ND._mat_pantalla(nombre, ND._a_np(im), fuerza)


# ------------------------------------------------------------------------------------------------ imágenes
def ui_vigilancia(rng):
    """Monitor central del puesto: la cámara del comedor (CAM 04), esquemática, con Kate como un punto solo."""
    from PIL import ImageDraw
    im, d = ND._lienzo(960, 600)
    f, fc = ND._fuente(30), ND._fuente(20)
    d.text((24, 18), "CAM 04 · COMEDOR", font=f, fill=ND.CIAN)
    d.text((700, 22), "● REC", font=f, fill=ND.ROJO)
    # perspectiva del comedor: piso en trapecio, mesas vacías en filas
    d.polygon([(120, 560), (840, 560), (640, 150), (320, 150)], outline=(40, 110, 150), width=2)
    for fila, (y, esc) in enumerate(((470, 1.0), (330, 0.72), (230, 0.52))):
        for x in (-0.62, -0.3, 0.3, 0.62):
            cx = 480 + x * 560 * esc
            w, h = 70 * esc, 26 * esc
            d.rectangle([cx - w, y - h, cx + w, y + h], outline=(70, 140, 180), width=2)
    # Kate: sola al fondo
    d.ellipse([468, 162, 492, 186], fill=ND.AMBAR)
    d.rectangle([450, 188, 510, 204], outline=ND.AMBAR, width=2)
    d.text((515, 150), "KATE", font=fc, fill=ND.AMBAR)
    d.text((24, 560), "TRIPULANTES EN EL MÓDULO: 1", font=fc, fill=ND.CIAN)
    return im


def ui_mensaje(texto: str, cursor: bool, enviar_activo: bool):
    """Pantalla personal de Kate: el chat con Aiden y el mensaje que escribe."""
    from PIL import Image, ImageDraw
    W, H = 600, 420
    im = Image.new("RGB", (W, H), (8, 14, 22))
    d = ImageDraw.Draw(im)
    f, fp, fc = ND._fuente(26), ND._fuente(22), ND._fuente(18)
    d.rectangle([0, 0, W, 54], fill=(14, 30, 46))
    d.text((20, 13), "MENSAJES · AIDEN", font=f, fill=(170, 220, 255))
    # mensajes viejos de Aiden, sin respuesta
    for k, (y, t) in enumerate(((78, "¿Estás bien?"), (134, "Keit, avisame si necesitás algo."))):
        tw = d.textlength(t, font=fp)
        d.rounded_rectangle([20, y, 40 + tw, y + 40], 12, fill=(26, 44, 62))
        d.text((30, y + 8), t, font=fp, fill=(200, 215, 230))
    d.text((22, 182), "hace 9 días", font=fc, fill=(90, 110, 130))
    # caja de texto
    d.rounded_rectangle([18, H - 92, W - 150, H - 30], 14, outline=(70, 130, 170), width=2, fill=(12, 22, 34))
    d.text((34, H - 76), texto + ("|" if cursor else ""), font=fp, fill=(235, 240, 245))
    col = (90, 200, 255) if enviar_activo else (40, 70, 90)
    d.rounded_rectangle([W - 136, H - 92, W - 18, H - 30], 14, fill=col)
    d.text((W - 118, H - 75), "ENVIAR", font=fp, fill=(8, 14, 22) if enviar_activo else (90, 120, 140))
    return im


def _cartel(texto, sub, w=900, h=220, color=(255, 176, 60)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (10, 12, 14))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, w - 5, h - 5], outline=color, width=6)
    d.text((40, 30), texto, font=ND._fuente(86), fill=color)
    d.text((44, 140), sub, font=ND._fuente(40), fill=(200, 200, 200))
    return im


# ------------------------------------------------------------------------------------------------ módulos
def pasillo_transito(col, M):
    """El pasillo del E01 queda igual; se abre su fondo y se le suma señalética y tapas de servicio."""
    y0, y1, x, h = PAS["y0"], PAS["y1"], PAS["x"], PAS["alto"]
    for nombre in ("pasillo_fondo",):
        o = bpy.data.objects.get(nombre)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    c = _pantalla("cartel_botanico", _cartel("BOTÁNICO", "MÓDULO 3 · COMEDOR ↓"), 1.4)
    ND._plano_uv("CARTEL_botanico", (x - 0.035, -6.2, 1.85), 0.7, 0.17, c, col,
                 (math.radians(90), 0, math.radians(-90)))
    for k, y in enumerate((-4.6, -7.6)):
        K.caja(f"tapa_servicio_{k}", (-x + 0.04, y, 1.0), (0.04, 0.8, 1.1), M["gris"], col, 0.01)
        K.caja(f"tapa_servicio_led_{k}", (-x + 0.065, y + 0.3, 1.45), (0.01, 0.05, 0.05), M["ambar"], col)


def _marco_puerta(nombre, y, x_ancho, alto, x_puerta, h_puerta, M, col, mat=None):
    """Tabique en y con una puerta centrada (ancho 2·x_puerta, alto h_puerta)."""
    mat = mat or M["pared"]
    lado = x_ancho - x_puerta
    for sgn in (-1, 1):
        K.caja(f"{nombre}_{sgn}", (sgn * (x_puerta + lado / 2), y, alto / 2), (lado, 0.12, alto), mat, col)
    K.caja(f"{nombre}_dintel", (0, y, (h_puerta + alto) / 2), (2 * x_puerta, 0.12, alto - h_puerta), mat, col)
    K.caja(f"{nombre}_marco", (0, y + 0.02, h_puerta + 0.04), (2 * x_puerta + 0.1, 0.14, 0.08), M["ambar"], col)


def incubadora(nombre, centro: Vector, lado: int, largo: float, M, col, rng, plantas: list):
    """Gabinete blanco + caja de vidrio. Abajo un tanque con agua y raíces, el sustrato, las plantas arriba, la luz
    de cultivo y gotas de condensación en el vidrio del lado del pasillo. lado = −1 (izquierda, x<0) / +1."""
    x_in = centro.x - lado * 0.27            # cara que da al pasillo
    zb, zt, zs = 0.70, 2.02, 0.98            # base, techo de la caja, superficie del sustrato
    K.caja(f"{nombre}_gabinete", (centro.x, centro.y, zb / 2), (0.56, largo, zb), M["gabinete"], col, 0.01)
    K.caja(f"{nombre}_zocalo", (x_in - lado * 0.01, centro.y, 0.05), (0.04, largo, 0.1), M["oscuro"], col)
    K.caja(f"{nombre}_fondo", (centro.x + lado * 0.27, centro.y, (zb + zt) / 2), (0.02, largo, zt - zb), M["gabinete"], col)
    K.caja(f"{nombre}_techo", (centro.x, centro.y, zt + 0.04), (0.58, largo + 0.02, 0.08), M["gabinete"], col, 0.01)
    # vidrio: frente y extremos
    K.caja(f"{nombre}_vidrio_frente", (x_in, centro.y, (zb + zt) / 2), (0.012, largo, zt - zb), M["vidrio"], col)
    for s in (-1, 1):
        K.caja(f"{nombre}_vidrio_{s}", (centro.x, centro.y + s * largo / 2, (zb + zt) / 2), (0.54, 0.012, zt - zb),
               M["vidrio"], col)
        K.caja(f"{nombre}_parante_{s}", (x_in, centro.y + s * largo / 2, (zb + zt) / 2), (0.03, 0.03, zt - zb),
               M["gris"], col)
    # tanque con agua (abajo, se ven las raíces) y sustrato encima
    K.caja(f"{nombre}_agua", (centro.x, centro.y, (zb + zs - 0.03) / 2), (0.5, largo - 0.04, zs - 0.03 - zb),
           M["agua"], col)
    K.caja(f"{nombre}_sustrato", (centro.x, centro.y, zs - 0.015), (0.5, largo - 0.04, 0.03), M["sustrato"], col)
    # raíces: hilos que bajan del sustrato al agua
    R = FL._Malla()
    for _ in range(int(largo * 26)):
        p = Vector((centro.x + rng.uniform(-0.2, 0.2), centro.y + rng.uniform(-largo / 2 + 0.06, largo / 2 - 0.06), zs - 0.03))
        pts = [p.copy()]
        d = Vector((rng.normal(0, 0.3), rng.normal(0, 0.3), -1)).normalized()
        for k in range(6):
            d = (d + Vector((rng.normal(0, 0.25), rng.normal(0, 0.25), -0.6))).normalized()
            p = p + d * rng.uniform(0.025, 0.045)
            p.z = max(p.z, zb + 0.02)
            pts.append(p.copy())
        R.tubo(pts, list(np.linspace(0.0025, 0.0008, len(pts))), 0, lados=3)
    R.objeto(f"{nombre}_raices", [M["raiz"]], col)
    # luz de cultivo: tira cálida y una tenue rosada, más una luz de área suave hacia abajo
    K.caja(f"{nombre}_luz", (centro.x, centro.y, zt - 0.015), (0.3, largo - 0.1, 0.012), M["blanco_calido"], col)
    K.caja(f"{nombre}_luz_rosa", (centro.x + lado * 0.18, centro.y, zt - 0.02), (0.03, largo - 0.1, 0.01),
           M["cultivo_rosa"], col)
    K.luz(f"{nombre}_area", "AREA", (centro.x, centro.y, zt - 0.06), 14, (1.0, 0.88, 0.78), col, tam=0.4,
          sombra=True)
    # plantas: en hileras irregulares, de alturas variadas (las más altas atrás)
    n = int(rng.integers(7, 11))
    for k in range(n):
        y = centro.y + (k + 0.5) / n * (largo - 0.12) - (largo - 0.12) / 2 + rng.normal(0, 0.03)
        fondo = rng.uniform(0, 1)
        x = centro.x + lado * (-0.17 + 0.32 * fondo)
        alto = min(0.95, rng.uniform(0.3, 0.55) + 0.35 * fondo)
        pl = FL.planta(f"{nombre}_p{k}", (x, y, zs), rng, col, alto=alto)
        plantas.append(pl)
    # gotas de condensación en el vidrio del frente (adentro), más abajo que arriba
    G = FL._Malla()
    for _ in range(int(largo * 120)):
        z = zb + (zt - zb) * (rng.uniform(0, 1) ** 1.6)
        r = rng.uniform(0.0012, 0.0035)
        G.esfera((x_in + lado * 0.008, centro.y + rng.uniform(-largo / 2, largo / 2), z), r, 0,
                 escala=(0.45, 1, 1.25), seg=6, an=3)
    G.objeto(f"{nombre}_gotas", [M["gota"]], col)


def pasillo_botanico(col, M, rng, BANDEJA=BANDEJA):
    y0, y1, x, h = BOT["y0"], BOT["y1"], BOT["x"], BOT["alto"]
    L = y0 - y1
    yc = (y0 + y1) / 2
    K.caja("bot_piso", (0, yc, -0.05), (2 * x, L, 0.1), M["piso_bot"], col)
    K.caja("bot_techo", (0, yc, h + 0.05), (2 * x, L, 0.1), M["pared_bot"], col)
    for s in (-1, 1):
        K.caja(f"bot_pared_{s}", (s * (x + 0.05), yc, h / 2), (0.1, L, h), M["pared_bot"], col)
        K.caja(f"bot_tira_piso_{s}", (s * 1.18, yc, 0.02), (0.03, L - 0.4, 0.015), M["tira"], col)
    # tabique de entrada (del pasillo de tránsito, 1,9 m, al botánico, 3,6 m) y de salida al comedor
    _marco_puerta("bot_entrada", y0, x, h, PUERTA, PAS["alto"], M, col, M["pared_bot"])
    _marco_puerta("bot_salida", y1, x, h, PUERTA, 2.3, M, col, M["pared_bot"])
    # paneles de luz en el techo: suaves y limpios
    for k in range(5):
        y = y0 - 1.0 - k * 2.0
        K.caja(f"bot_plafon_{k}", (0, y, h - 0.01), (1.2, 0.6, 0.02), M["plafon"], col)
        K.luz(f"bot_luz_{k}", "AREA", (0, y, h - 0.06), 55, (0.95, 0.97, 1.0), col, tam=1.0)
    # incubadoras
    plantas = []
    n, largo, gap = 6, 1.45, 0.17
    for s in (-1, 1):
        for k in range(n):
            y = y0 - 0.55 - largo / 2 - k * (largo + gap)
            incubadora(f"inc_{'i' if s < 0 else 'd'}{k}", Vector((s * 1.5, y, 0)), s, largo, M, col, rng, plantas)
    # bandeja de poda con la flor cortada (la que lleva Aiden)
    K.caja("bandeja_soporte", (BANDEJA.x - 0.06, BANDEJA.y, BANDEJA.z - 0.04), (0.18, 0.36, 0.02), M["gris"], col)
    K.caja("bandeja", (BANDEJA.x, BANDEJA.y, BANDEJA.z - 0.02), (0.22, 0.34, 0.025), M["gabinete"], col, 0.004)
    K.caja("tijera_poda", (BANDEJA.x + 0.03, BANDEJA.y + 0.11, BANDEJA.z), (0.03, 0.09, 0.006), M["gris"], col)
    cartel = _pantalla("cartel_poda", _cartel("PODA PROGRAMADA", "BANDEJA DE MANTENIMIENTO", 900, 220,
                                              (90, 230, 160)), 1.2)
    ND._plano_uv("CARTEL_poda", (BANDEJA.x - 0.33, BANDEJA.y, 1.35), 0.32, 0.08, cartel, col,
                 (math.radians(90), 0, math.radians(90)))
    return plantas


def _botella(nombre, pos, M, col, escala=1.0):
    b = K.cilindro(f"{nombre}_cuerpo", (pos[0], pos[1], pos[2] + 0.1 * escala), 0.033 * escala, 0.2 * escala,
                   M["botella"], col, 16)
    t = K.cilindro(f"{nombre}_tapa", (pos[0], pos[1], pos[2] + 0.215 * escala), 0.016 * escala, 0.03 * escala,
                   M["tapa_azul"], col, 12)
    return [b, t]


def comedor(col, M, rng):
    y0, y1, x, h = COM["y0"], COM["y1"], COM["x"], COM["alto"]
    L = y0 - y1
    yc = (y0 + y1) / 2
    K.caja("com_piso", (0, yc, -0.05), (2 * x, L, 0.1), M["piso_com"], col)
    K.caja("com_techo", (0, yc, h + 0.05), (2 * x, L, 0.1), M["gris"], col)
    K.caja("com_fondo", (0, y1 - 0.05, h / 2), (2 * x, 0.1, h), M["pared_com"], col)
    _marco_puerta("com_entrada", y0 - 0.06, x, h, PUERTA, 2.3, M, col, M["pared_com"])
    K.caja("com_pared_izq", (-x - 0.05, yc, h / 2), (0.1, L, h), M["pared_com"], col)
    # ventanal al espacio en la pared derecha (x > 0): marco y vidrio
    vz0, vz1, vy0, vy1 = 1.0, 2.7, y0 - 2.0, y1 + 2.0
    K.caja("com_der_bajo", (x + 0.05, yc, vz0 / 2), (0.1, L, vz0), M["pared_com"], col)
    K.caja("com_der_alto", (x + 0.05, yc, (vz1 + h) / 2), (0.1, L, h - vz1), M["pared_com"], col)
    for s, (ya, yb) in ((0, (y0, vy0)), (1, (vy1, y1))):
        K.caja(f"com_der_tramo_{s}", (x + 0.05, (ya + yb) / 2, (vz0 + vz1) / 2), (0.1, abs(ya - yb), vz1 - vz0),
               M["pared_com"], col)
    K.caja("com_ventanal", (x + 0.05, (vy0 + vy1) / 2, (vz0 + vz1) / 2), (0.02, abs(vy0 - vy1), vz1 - vz0),
           bpy.data.materials["vidrio_ventanal"], col)
    for k in range(5):
        y = vy0 + (vy1 - vy0) * k / 4
        K.caja(f"com_nervio_{k}", (x, y, (vz0 + vz1) / 2), (0.08, 0.08, vz1 - vz0), M["oscuro"], col)
    # luz: paneles del techo (algunos apagados: la nave está gastada) y luz de área tenue
    for i, yy in enumerate(np.linspace(y0 - 1.5, y1 + 1.5, 5)):
        for j, xx in enumerate((-3.4, 0.0, 3.4)):
            prendido = not ((i, j) in ((1, 0), (3, 2), (2, 2)))
            K.caja(f"com_plafon_{i}_{j}", (xx, yy, h - 0.01), (1.6, 0.5, 0.02),
                   M["plafon"] if prendido else M["oscuro"], col)
            if prendido:
                K.luz(f"com_luz_{i}_{j}", "AREA", (xx, yy, h - 0.08), 70, (0.88, 0.93, 1.0), col, tam=1.4)
    # mesas largas con banquetas, en filas cerca de la entrada (vacías)
    for fy in (-23.6, -26.8):
        for fx in (-4.6, -2.4, 2.4, 4.6):
            K.caja(f"mesa_{fx}_{fy}_tapa", (fx, fy, 0.74), (0.85, 2.6, 0.04), M["tapa_mesa"], col, 0.01)
            K.caja(f"mesa_{fx}_{fy}_pie", (fx, fy, 0.36), (0.12, 2.0, 0.72), M["mesa"], col)
            for s in (-1, 1):
                for k in range(3):
                    K.cilindro(f"banqueta_{fx}_{fy}_{s}_{k}", (fx + s * 0.62, fy - 0.85 + k * 0.85, 0.45), 0.17, 0.06,
                               M["asiento"], col, 16)
                    K.cilindro(f"banqueta_pie_{fx}_{fy}_{s}_{k}", (fx + s * 0.62, fy - 0.85 + k * 0.85, 0.21), 0.03,
                               0.42, M["mesa"], col, 8)
            # bandejas y paquetes cerrados que nadie usó
            if rng.uniform() < 0.6:
                K.caja(f"mesa_{fx}_{fy}_bandeja", (fx + rng.uniform(-0.1, 0.1), fy + rng.uniform(-0.8, 0.8), 0.77),
                       (0.32, 0.42, 0.02), M["racion_gris"], col, 0.005)
    # estanterías con comida sellada a lo largo de la pared izquierda y el fondo
    tipos = ["racion_blanca", "racion_naranja", "racion_verde", "racion_azul", "lata"]
    for k, yy in enumerate(np.linspace(y0 - 1.2, y1 + 1.5, 6)):
        _estante(f"est_i{k}", Vector((-x + 0.3, yy, 0)), 0, M, col, rng, tipos)
    for k, xx in enumerate((-4.5, -2.6, 2.6, 4.5)):
        _estante(f"est_f{k}", Vector((xx, y1 + 0.3, 0)), 1, M, col, rng, tipos)
    # dispensador de agua y botellas en el fondo
    K.caja("dispensador", (-1.1, y1 + 0.35, 0.9), (0.6, 0.45, 1.8), M["gabinete"], col, 0.02)
    K.caja("dispensador_pantalla", (-1.1, y1 + 0.58, 1.35), (0.3, 0.01, 0.18), M["tira"], col)
    for k in range(10):
        _botella(f"bot_disp_{k}", (-1.35 + (k % 5) * 0.12, y1 + 0.35 - 0.12 * (k // 5), 1.81), M, col)
    # la mesa de Kate, sola al fondo: más chica, con su silla, su pantalla, una ración cerrada
    mk = MESA_KATE
    K.caja("mesa_kate_tapa", (mk.x, mk.y, MESA_ALTO - 0.02), (1.6, 0.85, 0.04), M["tapa_mesa"], col, 0.01)
    K.caja("mesa_kate_pie", (mk.x, mk.y, (MESA_ALTO - 0.04) / 2), (0.14, 0.5, MESA_ALTO - 0.04), M["mesa"], col)
    K.caja("mesa_kate_base", (mk.x, mk.y, 0.015), (0.6, 0.6, 0.03), M["mesa"], col)
    ks = KATE_SILLA
    K.caja("silla_kate_asiento", (ks.x, ks.y - 0.08, 0.44), (0.46, 0.44, 0.05), M["asiento"], col, 0.01)
    K.caja("silla_kate_respaldo", (ks.x, ks.y - 0.3, 0.75), (0.46, 0.04, 0.5), M["asiento"], col, 0.01)
    K.cilindro("silla_kate_pie", (ks.x, ks.y - 0.08, 0.21), 0.03, 0.42, M["mesa"], col, 8)
    K.caja("racion_kate", (mk.x - 0.45, mk.y - 0.12, MESA_ALTO + 0.03), (0.16, 0.22, 0.05), M["racion_naranja"], col,
           0.004)
    return _pantalla_kate(col)


def _estante(nombre, base: Vector, frente_y: int, M, col, rng, tipos):
    """Estantería metálica de 4 niveles llena de envases sellados. frente_y = 0: da a +X; 1: da a +Y."""
    ancho, prof, alto = 1.6, 0.45, 2.1
    sx, sy = (prof, ancho) if frente_y == 0 else (ancho, prof)
    for k in range(5):
        K.caja(f"{nombre}_tabla_{k}", (base.x, base.y, 0.08 + k * 0.5), (sx, sy, 0.025), M["estante"], col)
    for dx in (-1, 1):
        for dy in (-1, 1):
            K.caja(f"{nombre}_parante_{dx}_{dy}", (base.x + dx * (sx / 2 - 0.02), base.y + dy * (sy / 2 - 0.02), alto / 2),
                   (0.03, 0.03, alto), M["estante"], col)
    for k in range(4):
        z = 0.08 + k * 0.5 + 0.0125
        n = int(rng.integers(5, 9))
        for j in range(n):
            if rng.uniform() < 0.12:
                continue                                      # huecos: lo que ya se consumió
            t = tipos[int(rng.integers(0, len(tipos)))]
            u = (j + 0.5) / n - 0.5
            if t == "lata":
                p = (base.x + (u * sx if frente_y else 0), base.y + (0 if frente_y else u * sy), z + 0.06)
                K.cilindro(f"{nombre}_{k}_{j}", p, 0.04, 0.12, M[t], col, 12)
            else:
                w, d, hh = rng.uniform(0.12, 0.18), rng.uniform(0.2, 0.3), rng.uniform(0.08, 0.2)
                p = (base.x + (u * sx if frente_y else 0), base.y + (0 if frente_y else u * sy), z + hh / 2)
                K.caja(f"{nombre}_{k}_{j}", p, (w, d, hh) if frente_y else (d, w, hh), M[t], col, 0.004)


def _pantalla_kate(col):
    """La tablet de Kate sobre la mesa, inclinada hacia ella: una copia por estado del mensaje."""
    estados = {"inicio": ("", False, False)}
    texto = "Gracias por la flor"
    for i in range(1, len(texto) + 1):
        estados[f"t{i:02d}"] = (texto[:i], True, False)
    estados["listo"] = (texto, True, True)
    centro = Vector((MESA_KATE.x + 0.28, MESA_KATE.y - 0.12, MESA_ALTO + 0.06))
    rot = (math.radians(62), 0, 0)                      # la pantalla mira a −Y (a Kate) y hacia arriba
    K.caja("tablet_kate", centro + Vector((0, 0.008, -0.004)), (0.31, 0.012, 0.22), bpy.data.materials["metal_oscuro"],
           col).rotation_euler = (math.radians(62 - 90), 0, 0)
    planos = {}
    for nom, (t, cur, env) in estados.items():
        m = _pantalla(f"ui_msj_{nom}", ui_mensaje(t, cur, env), 1.4)
        o = ND._plano_uv(f"PANTALLA_msj_{nom}", centro, 0.28, 0.196, m, col, rot)
        planos[nom] = o
    return planos


def _plantas_sweet_home(col):
    """Plantas en maceta de Sweet Home 3D (reutilizadas) junto al ventanal del comedor y a la entrada."""
    from estudio.blender import importar as I
    for nombre, pos, rz in (("bush_spider_plant", (5.9, -22.6, 0.0), 0.4), ("bush_indoor_plant", (5.9, -29.9, 0.0), 1.2),
                            ("bush_plant_2", (-1.6, -20.75, 0.0), 2.0), ("bush_plant_2", (1.6, -20.75, 0.0), 0.7)):
        objs = I.importar(f"sh3d:models/{nombre}.glb", col)
        for o in objs:
            if o.parent is None:
                o.location = pos
                o.rotation_mode = "XYZ"
                o.rotation_euler = (0, 0, rz)


# ------------------------------------------------------------------------------------------------ construir
def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    info = ND.construir({"semilla": p["semilla"]})
    # sin casco exterior (atravesaba los pasillos nuevos); este capítulo no tiene tomas afuera
    ce = bpy.data.collections.get("nave_exterior")
    if ce:
        for o in list(ce.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    info["animables"]["luces_nav"] = []
    rng = np.random.default_rng(p["semilla_flores"])
    FL.reiniciar()
    M = _materiales()
    raiz = bpy.data.collections.get("ESCENARIO_nave_deriva")
    c_pas, c_bot, c_com = (K.coleccion(n, raiz) for n in ("pasillo_transito", "pasillo_botanico", "comedor"))
    # monitor central del puesto: la cámara del comedor
    pv = bpy.data.objects.get("PANTALLA_trayectoria")
    if pv is not None:
        pv.data.materials.clear()
        pv.data.materials.append(_pantalla("ui_vigilancia", ui_vigilancia(rng), 2.2))
    pasillo_transito(c_pas, M)
    global BANDEJA
    if p.get("bandeja"):
        BANDEJA = Vector(p["bandeja"])
    plantas = pasillo_botanico(c_bot, M, rng, BANDEJA)
    _plantas_sweet_home(c_com)
    msj = comedor(c_com, M, rng)
    # botella de agua sobre la consola, al lado de Aiden (la lleva al comedor)
    a = info["anclas"]
    info["anclas"].update({
        "puerta_sala": (0.0, PAS["y0"], 1.3),
        "pasillo": (0.0, (PAS["y0"] + PAS["y1"]) / 2, 1.4),
        "botanico_entrada": (0.0, BOT["y0"], 1.4),
        "botanico": (0.0, (BOT["y0"] + BOT["y1"]) / 2, 1.3),
        "bandeja": tuple(BANDEJA),
        "comedor_entrada": (0.0, COM["y0"], 1.4),
        "comedor": (0.0, (COM["y0"] + COM["y1"]) / 2, 1.2),
        "mesa_kate": (MESA_KATE.x, MESA_KATE.y, MESA_ALTO),
        "kate": (KATE_SILLA.x, KATE_SILLA.y + 0.05, 1.15),
        "pantalla_kate": (MESA_KATE.x + 0.28, MESA_KATE.y - 0.12, MESA_ALTO + 0.06),
        "flor_mesa": tuple(p.get("flor_mesa", (MESA_KATE.x - 0.08, MESA_KATE.y + 0.08, MESA_ALTO + 0.01))),
        "flor_mesa2": tuple(p.get("flor_mesa2", (MESA_KATE.x - 0.2, MESA_KATE.y - 0.18, MESA_ALTO))),
        "botella_mesa": tuple(p.get("botella_mesa", (MESA_KATE.x - 0.3, MESA_KATE.y + 0.15, MESA_ALTO))),
        "botella_consola": (0.62, a["consola"][1] - 0.35, 0.86),
        "vigilancia_comedor": (-5.9, COM["y0"] - 0.6, 3.05),
    })
    info["animables"].update({"plantas": plantas, "mensaje": msj})
    return info


# ------------------------------------------------------------------------------------------------ eventos
def plantas_vivas(animables: dict, frame_inicio: int = 1, nf: int = 3600, fps: int = 30, **_):
    """Las flores se mecen todo el capítulo (circulación de aire de las incubadoras)."""
    FL.mecer(animables["plantas"], nf, fps, paso=4, rng=np.random.default_rng(7))


def mensaje_kate(animables: dict, frame_inicio: int = 1, escribir_s: float = 0.0, fin_s: float = 0.0, fps: int = 30,
                 **_):
    """La pantalla de Kate: el chat quieto; desde `escribir_s` aparece letra por letra «Gracias por la flor» y queda
    con el cursor sobre ENVIAR (no lo manda)."""
    planos = animables["mensaje"]
    texto = [k for k in planos if k.startswith("t")]
    f_ini = int(round(escribir_s * fps)) + 1
    f_list = int(round(fin_s * fps)) + 1 if fin_s else f_ini + 15 * len(texto)
    tramos = {"inicio": (1, f_ini)}
    paso = max(2, (f_list - f_ini) // (len(texto) + 1))
    for i, k in enumerate(sorted(texto)):
        tramos[k] = (f_ini + i * paso, f_ini + (i + 1) * paso)
    tramos["listo"] = (f_ini + len(texto) * paso, 10 ** 6)
    for k, o in planos.items():
        a, b = tramos[k]
        for fr, oculto in ((1, a > 1), (a, False), (b, True)):
            if fr < 1 or fr > 10 ** 5:
                continue
            o.hide_render = o.hide_viewport = oculto
            o.keyframe_insert("hide_render", frame=fr)
            o.keyframe_insert("hide_viewport", frame=fr)
        for fc in K._fcurves(o.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


# ------------------------------------------------------------------------------------------------ utilería
def _flor_suelta(nombre, col, rng):
    pl = FL.planta(nombre, (0, 0, 0), np.random.default_rng(91), col, especie="anemona", alto=0.24, paleta=3,
                   escala=1.15, cortada=True)
    return pl


def _hueso_mundo(arm, hueso: str, f: int) -> Matrix:
    bpy.context.scene.frame_set(f)
    return arm.matrix_world @ arm.pose.bones[hueso].matrix


def despues_personajes(info, pjs, ctx, manifiesto, fps):
    """Arma la utilería que pasa de mano en mano (parámetro «utileria» del escenario):
    {"objeto": "flor" | "botella", "tramos": [{"desde_s": 0, "en": "bandeja" | "mesa" | "consola" | "mano",
     "personaje": "aiden", "mano": "R" | "L"}, …]}. Cada tramo es una copia visible sólo en su intervalo."""
    esp = manifiesto["escenario"].get("parametros", {}).get("utileria", [])
    if not esp:
        return
    col = K.coleccion("UTILERIA")
    nf = int(round(manifiesto["duracion_s"] * fps))
    anclas = info["anclas"]
    for u in esp:
        tr = u["tramos"]
        for i, t in enumerate(tr):
            f0 = int(round(t["desde_s"] * fps)) + 1
            f1 = int(round(tr[i + 1]["desde_s"] * fps)) + 1 if i + 1 < len(tr) else nf + 2
            nombre = f"{u['objeto']}_{i}_{t['en']}"
            if u["objeto"] == "flor":
                pl = _flor_suelta(nombre, col, None)
                objs = [pl["tallo"], pl["cabeza"]]
                raiz = pl["tallo"]
            else:
                objs = _botella(nombre, (0, 0, 0), _mats_botella(), col)
                raiz = bpy.data.objects.new(f"{nombre}_raiz", None)
                col.objects.link(raiz)
                for o in objs:
                    o.parent = raiz
            if t["en"] == "mano":
                pj = pjs[t["personaje"]]
                arm = pj["armadura"]
                hueso = f"mixamorig:{'Right' if t.get('mano', 'R') == 'R' else 'Left'}Hand"
                if hueso not in arm.pose.bones:
                    hueso = next(b.name for b in arm.pose.bones if b.name.endswith(hueso.split(":")[-1]))
                fr = min(f1 - 1, f0 + 3)
                Mh = _hueso_mundo(arm, hueso, fr)
                # en la palma: un poco hacia los dedos (y del hueso) y hacia la palma (z del hueso)
                lado = 1 if t.get("mano", "R") == "R" else -1
                if u["objeto"] == "flor":
                    off = Matrix.Translation((0.0, 0.075, 0.025)) @ Matrix.Rotation(math.radians(-80 * lado), 4, "Z") \
                        @ Matrix.Rotation(math.radians(90), 4, "Y")
                else:
                    off = Matrix.Translation((0.0, 0.07, 0.035)) @ Matrix.Rotation(math.radians(90), 4, "X")
                raiz.parent = arm
                raiz.parent_type = "BONE"
                raiz.parent_bone = hueso
                bpy.context.view_layer.update()
                raiz.matrix_world = Mh @ off
            else:
                pos = Vector(anclas[{"bandeja": "bandeja", "mesa": f"{u['objeto']}_mesa", "mesa2": f"{u['objeto']}_mesa2",
                                     "consola": f"{u['objeto']}_consola"}[t["en"]]])
                if u["objeto"] == "flor":
                    raiz.rotation_euler = (0, math.radians(90), math.radians(t.get("rumbo_deg", 20)))
                    raiz.location = pos + Vector((0, 0, 0.012))
                else:
                    raiz.location = pos
            for o in [raiz] + objs:
                for fr, oculto in ((1, f0 > 1), (f0, False), (f1, True)):
                    if fr > nf + 1:
                        continue
                    o.hide_render = o.hide_viewport = oculto
                    o.keyframe_insert("hide_render", frame=fr)
                    o.keyframe_insert("hide_viewport", frame=fr)
                if o.animation_data and o.animation_data.action:
                    for fc in K._fcurves(o.animation_data.action):
                        if fc.data_path.startswith("hide"):
                            for kp in fc.keyframe_points:
                                kp.interpolation = "CONSTANT"


def _mats_botella():
    class _M(dict):
        pass
    m = _M()
    m["botella"] = bpy.data.materials["botella_agua"]
    m["tapa_azul"] = bpy.data.materials["tapa_botella"]
    return m
