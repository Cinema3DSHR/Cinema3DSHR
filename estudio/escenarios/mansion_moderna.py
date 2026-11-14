"""Escenario procedural: mansión moderna de lujo (noche por defecto).

Incluye fachada de dos volúmenes (planta baja vidriada + planta alta en voladizo revestida de madera), garaje con
portón seccional, sala de seguridad con monitores, living, cocina, dormitorio, piscina iluminada, jardín con
árboles y arbustos instanciados, muro perimetral con portón batiente, camino de entrada de asfalto mojado,
balizas, apliques de fachada, calle con farolas y una silueta de ciudad lejana (geometría simplificada).

Técnicas: geometría modular, instanciación (árboles, arbustos, balizas), materiales procedurales en coordenadas de
mundo, fondo lejano de baja complejidad y luces sin sombra donde no se notan (para abaratar el render).

Devuelve los PUNTOS DE INTERÉS (anclas) que usan las cámaras, los vehículos y los personajes. Ejes: X a lo largo
de la calle, Y hacia el fondo del terreno, Z arriba. La calle está en y = −31, el frente del terreno en y = −24.
"""
from __future__ import annotations
import math
import random
from estudio.blender import kit as K

PARAMETROS = {
    "hora": "noche",          # noche | atardecer (por ahora sólo noche)
    "suelo_mojado": True,      # asfalto con charcos y reflejos
    "niebla": 0.0,             # densidad de niebla volumétrica (0 = sin niebla, más barato)
    "arboles": 26,
    "arbustos": 70,
    "ciudad_fondo": True,
    "semilla": 7,
}

ANCLAS_DOC = {
    "porton": "centro del portón del frente (por donde entran los vehículos)",
    "garaje": "frente del portón del garaje",
    "entrada": "puerta principal de la casa",
    "piscina": "centro de la piscina",
    "sala_seguridad": "centro de la sala de seguridad (monitores)",
    "camara_vigilancia": "cámara de seguridad del muro (mira al camino de entrada)",
    "calle_oeste / calle_este": "extremos de la calle",
    "living": "centro del living",
}


def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    rnd = random.Random(p["semilla"])
    s = K.bpy.context.scene
    K.cielo_noche(s, niebla=p["niebla"])

    col = K.coleccion("ESCENARIO_mansion")
    c_arq = K.coleccion("arquitectura", col)
    c_int = K.coleccion("interiores", col)
    c_jar = K.coleccion("jardin", col)
    c_luz = K.coleccion("luces", col)
    c_fondo = K.coleccion("fondo", col)
    c_animado = K.coleccion("animado", col)

    # ---------------------------------------------------------------- materiales
    M = K.material
    hormigon = M("hormigon_claro", (0.62, 0.6, 0.57), 0.75, ruido=0.12, escala_ruido=3, relieve=0.08)
    hormigon_osc = M("hormigon_oscuro", (0.18, 0.18, 0.19), 0.7, ruido=0.1, relieve=0.05)
    madera = M("madera_revestimiento", (0.32, 0.18, 0.09), 0.55, ruido=0.25, escala_ruido=18,
               ladrillo=((0.22, 0.12, 0.06), 6.0))
    piedra = M("piedra_muro", (0.27, 0.26, 0.24), 0.85, ladrillo=((0.2, 0.19, 0.18), 2.2), relieve=0.2)
    metal_osc = M("metal_negro", (0.03, 0.03, 0.035), 0.35, 0.9)
    aluminio = M("aluminio", (0.55, 0.56, 0.58), 0.3, 1.0)
    vid = K.vidrio("vidrio_fachada", (0.45, 0.55, 0.6), 0.28)
    cesped = M("cesped", (0.035, 0.09, 0.025), 0.9, ruido=0.35, escala_ruido=1.5, relieve=0.3)
    asfalto = M("asfalto_mojado" if p["suelo_mojado"] else "asfalto", (0.035, 0.035, 0.038),
                0.18 if p["suelo_mojado"] else 0.8, ruido=0.25, escala_ruido=0.6, relieve=0.05,
                rug_var=0.35 if p["suelo_mojado"] else 0.0)
    vereda = M("vereda", (0.25, 0.25, 0.24), 0.6, ladrillo=((0.21, 0.21, 0.2), 1.4), rug_var=0.2)
    deck = M("deck_madera", (0.22, 0.13, 0.07), 0.5, ladrillo=((0.18, 0.1, 0.05), 3.0))
    agua = M("agua_piscina", (0.02, 0.18, 0.22), 0.04, transmision=0.6, ior=1.33, relieve=0.25,
             escala_ruido=1.2, animar_ruido=0.6)
    azulejo = K.emisivo("azulejo_piscina_luz", (0.05, 0.45, 0.7), 0.7)
    seto = M("seto", (0.02, 0.06, 0.02), 0.85, ruido=0.4, escala_ruido=6, relieve=0.6)
    hojas = M("hojas", (0.025, 0.07, 0.025), 0.8, ruido=0.45, escala_ruido=5, relieve=0.5)
    tronco = M("tronco", (0.08, 0.05, 0.03), 0.9, ruido=0.3, escala_ruido=10)
    luz_calida = K.emisivo("emisor_calido", (1.0, 0.72, 0.42), 18.0)
    luz_sodio = K.emisivo("emisor_sodio", (1.0, 0.55, 0.2), 25.0)
    tela = M("tela_sofa", (0.55, 0.5, 0.44), 0.95, ruido=0.08, escala_ruido=40)
    tela_osc = M("tela_oscura", (0.08, 0.08, 0.09), 0.9)
    marmol = M("marmol", (0.85, 0.84, 0.82), 0.15, ruido=0.1, escala_ruido=2)
    piso_int = M("piso_interior", (0.42, 0.36, 0.3), 0.35, ladrillo=((0.38, 0.32, 0.27), 1.0))
    pared_int = M("pared_interior", (0.78, 0.75, 0.7), 0.9)
    pantalla = M("pantalla_vigilancia", (0.0, 0.0, 0.0), 0.3, emision=(0.3, 0.5, 0.42), fuerza=0.55,
                 ruido=0.9, escala_ruido=9, animar_ruido=3.0, ruido_en_emision=True)
    ciudad = M("edificio_lejano", (0.006, 0.006, 0.009), 0.9, fuerza=1.4,
               ventanas=((1.0, 0.72, 0.42), 0.3))  # fachada oscura con ventanas encendidas al azar

    caja, cil = K.caja, K.cilindro

    # ---------------------------------------------------------------- terreno, calle, vereda
    K.plano("cesped_terreno", (0, 3, 0), (64, 54), cesped, c_jar)
    K.plano("suelo_lejano", (0, 0, -0.05), (900, 900), M("suelo_noche", (0.02, 0.025, 0.02), 0.95), c_fondo)
    caja("calle", (0, -31.5, -0.04), (220, 9, 0.1), asfalto, c_arq)
    caja("vereda_frente", (0, -25.8, 0.06), (220, 2.6, 0.12), vereda, c_arq)
    caja("vereda_enfrente", (0, -37.2, 0.06), (220, 2.4, 0.12), vereda, c_arq)
    # camino de entrada (asfalto) y sendero a la puerta
    caja("camino_entrada", (14, -13.5, 0.02), (6.4, 21, 0.06), asfalto, c_arq)
    caja("explanada_garaje", (14, -2.0, 0.025), (9, 4.5, 0.06), asfalto, c_arq)
    for i in range(7):
        caja(f"sendero_{i}", (-2, -2.2 - i * 1.6, 0.03), (1.6, 1.1, 0.06), vereda, c_arq)

    # ---------------------------------------------------------------- muro perimetral y portón
    alto_muro = 2.2
    for nombre, cx, ancho in (("muro_frente_o", -9.5, 41), ("muro_frente_e", 24.5, 15)):
        caja(nombre, (cx, -24, alto_muro / 2), (ancho, 0.4, alto_muro), piedra, c_arq, bisel=0.02)
        caja(nombre + "_tapa", (cx, -24, alto_muro + 0.05), (ancho + 0.1, 0.5, 0.1), hormigon_osc, c_arq)
    for nombre, cx in (("muro_lado_o", -30), ("muro_lado_e", 32)):
        caja(nombre, (cx, 3, alto_muro / 2), (0.4, 54, alto_muro), piedra, c_arq)
    caja("muro_fondo", (1, 30, alto_muro / 2), (62, 0.4, alto_muro), piedra, c_arq)
    for x in (10.8, 17.2):
        caja(f"pilar_porton_{x}", (x, -24, 1.4), (0.7, 0.7, 2.8), hormigon_osc, c_arq, bisel=0.03)
        K.esfera(f"farol_pilar_{x}", (x, -24, 2.95), 0.18, luz_calida, c_luz)
        K.luz(f"luz_pilar_{x}", "POINT", (x, -24.5, 3.0), 60, (1, 0.75, 0.45), c_luz, radio=0.15)
    # portón batiente de dos hojas (barrotes); bisagras en x = 11.1 y 16.9
    hojas_porton = []
    for lado, bis in (("izq", 11.15), ("der", 16.85)):
        piv = K.vacio(f"porton_bisagra_{lado}", (bis, -24, 0), c_animado)
        sentido = 1 if lado == "izq" else -1
        partes = [caja(f"porton_{lado}_marco_inf", (bis + sentido * 1.42, -24, 0.25), (2.8, 0.08, 0.08), metal_osc),
                  caja(f"porton_{lado}_marco_sup", (bis + sentido * 1.42, -24, 2.3), (2.8, 0.08, 0.08), metal_osc)]
        for i in range(12):
            partes.append(caja(f"porton_{lado}_barra_{i}", (bis + sentido * (0.12 + i * 0.24), -24, 1.25),
                               (0.04, 0.04, 2.3), metal_osc))
        hoja = K.unir(partes, f"porton_hoja_{lado}")
        K.padre(hoja, piv)
        hojas_porton.append((piv, sentido))
    # cámara de seguridad en el pilar derecho (prop visible)
    cam_prop = caja("camara_seguridad_prop", (17.6, -23.6, 3.1), (0.18, 0.35, 0.16), aluminio, c_arq, bisel=0.02)
    cam_prop.rotation_euler = (math.radians(-25), 0, math.radians(30))

    # ---------------------------------------------------------------- casa: planta baja vidriada
    # losa y piso
    caja("losa_pb", (-1, 6, 0.1), (24, 13, 0.2), hormigon, c_arq)
    caja("piso_pb", (-1, 6, 0.205), (23.6, 12.6, 0.01), piso_int, c_int)
    # fachada frontal: vidrio con parantes de aluminio negro (y = 0)
    caja("vidrio_frente_pb", (-3, -0.3, 1.9), (17.6, 0.04, 3.2), vid, c_arq)
    for i in range(10):
        caja(f"parante_{i}", (-11.8 + i * 1.96, -0.3, 1.9), (0.07, 0.12, 3.25), metal_osc, c_arq)
    caja("dintel_pb", (-3, -0.3, 3.52), (17.8, 0.2, 0.15), metal_osc, c_arq)
    # muros laterales y del fondo (hormigón)
    caja("muro_pb_oeste", (-12.9, 6, 1.9), (0.3, 13, 3.4), hormigon, c_arq)
    caja("muro_pb_fondo", (-1, 12.4, 1.9), (24, 0.3, 3.4), hormigon, c_arq)
    caja("muro_pb_este", (10.2, 6, 1.9), (0.3, 13, 3.4), hormigon, c_arq)  # medianera con el garaje
    # bloque de la puerta y la sala de seguridad (frente macizo entre x = 5.8 y 10)
    caja("frente_macizo", (7.95, -0.3, 1.9), (4.5, 0.3, 3.4), hormigon_osc, c_arq, bisel=0.01)
    caja("ventana_seguridad", (8.6, -0.48, 2.2), (1.6, 0.04, 0.6), vid, c_arq)
    caja("muro_seguridad", (5.8, 3.2, 1.9), (0.2, 6.4, 3.4), pared_int, c_int)
    caja("muro_seguridad_fondo", (8.0, 6.4, 1.9), (4.4, 0.2, 3.4), pared_int, c_int)
    # puerta principal pivotante (alta, de madera) en x = −2
    piv_puerta = K.vacio("puerta_principal_pivote", (-2.9, -0.35, 0.2), c_animado)
    puerta = caja("puerta_principal", (-2.0, -0.35, 1.7), (1.8, 0.08, 3.0), madera, c_arq, bisel=0.01)
    K.padre(puerta, piv_puerta)
    caja("tirador_puerta", (-1.3, -0.45, 1.6), (0.04, 0.05, 1.1), aluminio, c_arq)
    # alero de entrada
    caja("alero_entrada", (-2, -1.6, 3.65), (4.5, 2.6, 0.18), hormigon_osc, c_arq)

    # ---------------------------------------------------------------- planta alta en voladizo
    caja("losa_pa", (-6, 5.5, 3.75), (21, 15, 0.3), hormigon, c_arq, bisel=0.02)
    caja("volumen_pa_frente", (-6, -1.9, 5.45), (21, 0.3, 3.1), madera, c_arq)
    caja("banda_vidrio_pa", (-6.5, -2.1, 5.35), (16, 0.05, 1.5), vid, c_arq)
    caja("volumen_pa_oeste", (-16.4, 5.5, 5.45), (0.3, 15, 3.1), madera, c_arq)
    caja("volumen_pa_este", (4.4, 5.5, 5.45), (0.3, 15, 3.1), madera, c_arq)
    caja("volumen_pa_fondo", (-6, 12.9, 5.45), (21, 0.3, 3.1), madera, c_arq)
    caja("techo", (-6, 5.5, 7.1), (21.6, 15.6, 0.3), hormigon_osc, c_arq, bisel=0.02)
    caja("piso_pa", (-6, 5.5, 3.91), (20.4, 14.4, 0.02), piso_int, c_int)
    # baranda de vidrio de la terraza sobre el garaje
    caja("losa_terraza", (14, 5, 3.55), (8.4, 10.4, 0.25), hormigon, c_arq)
    caja("baranda_terraza", (14, -0.15, 4.2), (8.2, 0.03, 1.0), vid, c_arq)

    # ---------------------------------------------------------------- garaje
    caja("garaje_oeste", (10.2, 5, 1.7), (0.3, 10, 3.4), hormigon, c_arq)
    caja("garaje_este", (18.1, 5, 1.7), (0.3, 10, 3.4), hormigon, c_arq)
    caja("garaje_fondo", (14, 10, 1.7), (8, 0.3, 3.4), hormigon, c_arq)
    caja("garaje_dintel", (14, 0, 3.1), (8, 0.3, 0.6), hormigon_osc, c_arq)
    caja("garaje_piso", (14, 5, 0.05), (7.8, 10, 0.1), hormigon_osc, c_int)
    porton_garaje = caja("porton_garaje", (14, 0.05, 1.4), (6.0, 0.1, 2.8), aluminio, c_animado)
    for i in range(6):  # nervaduras del portón seccional
        r = caja(f"porton_garaje_panel_{i}", (14, -0.02, 0.25 + i * 0.47), (5.9, 0.04, 0.03), metal_osc)
        K.padre(r, porton_garaje)
    K.luz("luz_garaje_interior", "AREA", (14, 5, 3.2), 120, (1, 0.95, 0.85), c_luz,
          rot=(0, 0, 0), tam=3.0)
    for x in (10.7, 17.3):
        caja(f"aplique_garaje_{x}", (x, -0.25, 2.6), (0.12, 0.2, 0.5), metal_osc, c_arq)
        K.luz(f"luz_aplique_garaje_{x}", "SPOT", (x, -0.45, 2.5), 140, (1, 0.78, 0.5), c_luz,
              rot=(0, 0, 0), angulo_spot=math.radians(70))

    # ---------------------------------------------------------------- interiores
    # living
    caja("sofa_base", (-6, 4, 0.45), (3.2, 1.0, 0.5), tela, c_int, bisel=0.06)
    caja("sofa_respaldo", (-6, 4.45, 0.85), (3.2, 0.25, 0.6), tela, c_int, bisel=0.06)
    caja("sofa_lateral", (-8.2, 3.0, 0.45), (1.0, 2.6, 0.5), tela, c_int, bisel=0.06)
    caja("mesa_ratona", (-6, 2.3, 0.4), (1.6, 0.9, 0.08), marmol, c_int, bisel=0.01)
    caja("alfombra", (-6, 3, 0.215), (5, 4, 0.01), tela_osc, c_int)
    cil("lampara_pie", (-4, 4.6, 0.9), 0.03, 1.6, metal_osc, c_int)
    K.esfera("lampara_pantalla", (-4, 4.6, 1.75), 0.22, luz_calida, c_int)
    K.luz("luz_living", "AREA", (-6, 4, 3.3), 260, (1, 0.8, 0.6), c_luz, tam=2.5)
    K.luz("luz_lampara", "POINT", (-4, 4.6, 1.75), 40, (1, 0.7, 0.4), c_luz, radio=0.2, sombra=False)
    # comedor y cocina
    caja("mesa_comedor", (0.5, 7.5, 0.76), (2.6, 1.1, 0.06), madera, c_int)
    for dx in (-1.1, 1.1):
        caja(f"pata_mesa_{dx}", (0.5 + dx, 7.5, 0.38), (0.08, 0.9, 0.76), metal_osc, c_int)
    caja("isla_cocina", (-4, 9.8, 0.47), (3.4, 1.0, 0.94), marmol, c_int, bisel=0.01)
    caja("mueble_cocina", (-4, 11.9, 1.2), (6, 0.6, 2.4), M("laca_oscura", (0.05, 0.05, 0.05), 0.25), c_int)
    for i in range(3):
        K.esfera(f"colgante_{i}", (-5 + i, 9.8, 2.6), 0.14, luz_calida, c_int)
    K.luz("luz_cocina", "AREA", (-4, 9.8, 3.3), 180, (1, 0.85, 0.7), c_luz, tam=2.0)
    # dormitorio planta alta
    caja("cama", (-10, 6, 4.25), (2.0, 2.2, 0.5), tela, c_int, bisel=0.05)
    caja("cabecera", (-10, 7.2, 4.7), (2.2, 0.12, 1.2), madera, c_int)
    K.luz("luz_dormitorio", "AREA", (-9, 4, 6.7), 150, (1, 0.75, 0.55), c_luz, tam=2.0)
    K.luz("luz_pa_pasillo", "AREA", (-1, 3, 6.7), 120, (1, 0.8, 0.6), c_luz, tam=2.0)
    # sala de seguridad: escritorio + 6 monitores
    caja("escritorio_seguridad", (8.0, 4.8, 0.75), (3.6, 1.0, 0.06), metal_osc, c_int)
    monitores = []
    for i in range(3):
        for j in range(2):
            m = caja(f"monitor_{i}_{j}", (6.8 + i * 1.2, 5.6, 1.25 + j * 0.62), (1.1, 0.06, 0.58), pantalla, c_int)
            monitores.append(m)
    caja("silla_seguridad", (8.0, 3.6, 0.55), (0.6, 0.6, 0.1), tela_osc, c_int)
    caja("silla_respaldo", (8.0, 3.3, 0.95), (0.6, 0.08, 0.8), tela_osc, c_int)
    K.luz("luz_seguridad", "AREA", (8.0, 3.5, 3.3), 25, (0.6, 0.75, 1.0), c_luz, tam=1.2)
    K.luz("luz_monitores", "AREA", (8.0, 5.2, 1.5), 30, (0.5, 0.8, 0.7), c_luz,
          rot=(math.radians(90), 0, math.radians(180)), tam=3.0, sombra=False)

    # ---------------------------------------------------------------- piscina y deck
    caja("piscina_vaso", (-8, -8.5, -0.7), (12, 5.0, 1.5), azulejo, c_jar)
    for nombre, c, t in (("n", (-8, -5.85, 0.13), (12.6, 0.3, 0.04)), ("s", (-8, -11.15, 0.13), (12.6, 0.3, 0.04)),
                         ("o", (-14.15, -8.5, 0.13), (0.3, 5.6, 0.04)), ("e", (-1.85, -8.5, 0.13), (0.3, 5.6, 0.04))):
        caja(f"piscina_borde_{nombre}", c, t, hormigon, c_jar)
    # el deck tiene un hueco donde va la piscina: se arma con 4 tablas alrededor
    for nombre, c, t in (("n", (-8, -4.9, 0.06), (16, 1.8, 0.12)), ("s", (-8, -12.4, 0.06), (16, 2.2, 0.12)),
                         ("o", (-15.1, -8.5, 0.06), (1.8, 5.2, 0.12)), ("e", (-0.9, -8.5, 0.06), (1.8, 5.2, 0.12))):
        caja(f"deck_{nombre}", c, t, deck, c_jar)

    caja("piscina_agua", (-8, -8.5, 0.0), (11.9, 4.9, 0.1), agua, c_jar)
    K.luz("luz_piscina", "AREA", (-8, -8.5, -0.6), 90, (0.3, 0.8, 1.0), c_luz, tam=8.0, sombra=False)
    for i, x in enumerate((-13, -10, -6)):
        caja(f"reposera_{i}", (x, -12.3, 0.35), (0.7, 1.9, 0.12), tela, c_jar, bisel=0.03)

    # ---------------------------------------------------------------- jardín: prototipos instanciados
    proto_arbol = K.prototipo("PROTO_arbol")
    K.cilindro("arbol_tronco", (0, 0, 1.6), 0.16, 3.2, tronco, proto_arbol, lados=10)
    for i, (dx, dy, dz, r) in enumerate(((0, 0, 3.6, 1.5), (0.7, 0.3, 3.0, 1.1), (-0.6, -0.4, 3.2, 1.2),
                                          (0.1, 0.6, 4.4, 1.0))):
        K.esfera(f"arbol_copa_{i}", (dx, dy, dz), r, hojas, proto_arbol, subdiv=2, escala=(1, 1, 0.85))
    proto_arbusto = K.prototipo("PROTO_arbusto")
    K.esfera("arbusto", (0, 0, 0.35), 0.55, seto, proto_arbusto, subdiv=2, escala=(1, 1, 0.7))
    proto_baliza = K.prototipo("PROTO_baliza")
    K.cilindro("baliza_cuerpo", (0, 0, 0.35), 0.07, 0.7, metal_osc, proto_baliza, lados=12)
    K.cilindro("baliza_luz", (0, 0, 0.66), 0.075, 0.08, luz_calida, proto_baliza, lados=12)

    zonas_libres = [(-15, -13, -1, -3.5), (9, -25, 19, 1), (-14, -1, 11, 13), (9.5, -1, 19, 11),
                    (-3.5, -14, -0.5, 0)]

    def libre(x, y, margen=1.5):
        for x0, y0, x1, y1 in zonas_libres:
            if x0 - margen < x < x1 + margen and y0 - margen < y < y1 + margen:
                return False
        return True

    n = 0
    intentos = 0
    while n < p["arboles"] and intentos < 2000:
        intentos += 1
        x, y = rnd.uniform(-28, 30), rnd.uniform(-22, 28)
        if libre(x, y, 2.5):
            K.instancia(f"arbol_{n}", proto_arbol, (x, y, 0), rnd.uniform(0, 6.28), rnd.uniform(0.8, 1.35), c_jar)
            n += 1
    n = 0
    intentos = 0
    while n < p["arbustos"] and intentos < 3000:
        intentos += 1
        x, y = rnd.uniform(-29, 31), rnd.uniform(-23, 29)
        if libre(x, y, 0.6):
            K.instancia(f"arbusto_{n}", proto_arbusto, (x, y, 0), rnd.uniform(0, 6.28), rnd.uniform(0.6, 1.4), c_jar)
            n += 1
    # setos junto al muro del frente
    for i in range(16):
        x = -28.5 + i * 2.4
        if x < 9:
            K.instancia(f"seto_frente_{i}", proto_arbusto, (x, -22.8, 0), 0, 1.5, c_jar)
    # balizas a los costados del camino de entrada (luces sin sombra: baratas)
    for i in range(6):
        y = -22 + i * 3.6
        for x in (10.6, 17.4):
            K.instancia(f"baliza_{x}_{i}", proto_baliza, (x, y, 0), 0, 1.0, c_jar)
            K.luz(f"luz_baliza_{x}_{i}", "POINT", (x, y, 0.75), 6, (1, 0.72, 0.42), c_luz, radio=0.05, sombra=False)
    # balizas del sendero
    for i in range(4):
        K.instancia(f"baliza_sendero_{i}", proto_baliza, (-3.2, -3 - i * 3, 0), 0, 0.9, c_jar)
        K.luz(f"luz_baliza_sendero_{i}", "POINT", (-3.2, -3 - i * 3, 0.7), 5, (1, 0.72, 0.42), c_luz, radio=0.05,
              sombra=False)
    # apliques de fachada: bañadores hacia arriba sobre la madera
    for i, x in enumerate((-15, -11, -7, -3, 1)):
        K.luz(f"bañador_fachada_{i}", "SPOT", (x, -2.6, 3.85), 90, (1, 0.7, 0.45), c_luz,
              rot=(math.radians(-8), 0, 0), angulo_spot=math.radians(55))
    # luces de los árboles cercanos (spots desde el suelo)
    K.luz("spot_jardin_1", "SPOT", (-20, -16, 0.2), 200, (0.9, 0.85, 0.7), c_luz, rot=(math.radians(15), 0, 0),
          angulo_spot=math.radians(45))

    # ---------------------------------------------------------------- calle: farolas y ciudad de fondo
    for i, x in enumerate(range(-60, 70, 22)):
        K.cilindro(f"farola_poste_{i}", (x, -36.5, 3.5), 0.09, 7, metal_osc, c_arq, lados=10)
        K.caja(f"farola_brazo_{i}", (x, -35.6, 6.95), (0.12, 1.9, 0.1), metal_osc, c_arq)
        K.caja(f"farola_cabeza_{i}", (x, -34.7, 6.85), (0.35, 0.6, 0.12), luz_sodio, c_arq)
        K.luz(f"luz_farola_{i}", "SPOT", (x, -34.7, 6.75), 900, (1, 0.6, 0.28), c_luz,
              angulo_spot=math.radians(110), radio=0.3)
    if p["ciudad_fondo"]:
        for i in range(70):
            ang = rnd.uniform(math.radians(200), math.radians(340))
            dist = rnd.uniform(480, 800)
            x, y = math.cos(ang) * dist * -1, math.sin(ang) * dist * -1 + 40
            if y < 120:
                continue
            h = rnd.uniform(15, 75)
            ed = K.caja(f"edificio_{i}", (x, y, h / 2 - 2), (rnd.uniform(14, 30), rnd.uniform(14, 30), h),
                        ciudad, c_fondo, rot_z=rnd.uniform(0, 1.5))
            ed.visible_shadow = False
    # luna (sol frío y tenue) + luz de relleno del cielo
    K.luz("luna", "SUN", (0, 0, 50), 0.45, (0.55, 0.65, 1.0), c_luz,
          rot=(math.radians(55), 0, math.radians(-35)))

    # ---------------------------------------------------------------- anclas (puntos de interés)
    anclas = {
        "porton": (14.0, -24.0, 0.0),
        "garaje": (14.0, -0.5, 0.0),
        "explanada_garaje": (14.0, -3.5, 0.0),
        "entrada": (-2.0, -0.6, 0.0),
        "piscina": (-8.0, -8.5, 0.0),
        "sala_seguridad": (8.0, 4.5, 1.2),
        "monitores": (8.0, 5.6, 1.55),
        "living": (-6.0, 3.5, 1.0),
        "camara_vigilancia": (17.6, -23.6, 3.1),
        "calle_oeste": (-60.0, -31.0, 0.0),
        "calle_este": (60.0, -31.0, 0.0),
        "centro_casa": (-1.0, 5.0, 3.5),
    }
    # objetos animables que exponen al director
    animables = {
        "porton_hojas": hojas_porton,       # lista de (pivote, sentido)
        "porton_garaje": porton_garaje,
        "puerta_principal": piv_puerta,
    }
    return {"anclas": anclas, "animables": animables, "parametros": p}


def abrir_porton(animables, frame_inicio: int, duracion_f: int = 75, angulo_deg: float = 95.0):
    """Anima la apertura del portón batiente (las hojas giran hacia adentro del terreno)."""
    for piv, sentido in animables["porton_hojas"]:
        K.clave(piv, "rotation_euler", frame_inicio, 0.0, 2)
        K.clave(piv, "rotation_euler", frame_inicio + duracion_f, math.radians(angulo_deg) * sentido, 2)


def abrir_garaje(animables, frame_inicio: int, duracion_f: int = 90):
    pg = animables["porton_garaje"]
    K.clave(pg, "location", frame_inicio, 1.4, 2)
    K.clave(pg, "location", frame_inicio + duracion_f, 4.1, 2)
