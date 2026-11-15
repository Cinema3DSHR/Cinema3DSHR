"""Escenario procedural: interior de la mansión para una entrada táctica (CQB): pasillo oscuro, puerta pivotante y un
estudio de lujo con biblioteca, escritorio, sofá, alfombra, cuadros y ventanales con luz de día.

Ejes (mismos que el resto del estudio): Z arriba. El pasillo corre a lo largo de +Y y termina en la puerta (y = 0);
la habitación está en y > 0. Eje de la puerta en x = 0. Todo es geometría procedural + materiales procedurales
(sin recursos externos), con instancias para los libros y luces sin sombra donde no se notan.

Anclas: puerta, pasillo, centro_sala, enemigo (detrás del escritorio), escritorio, ventanal, sofa, biblioteca.
Eventos: abrir_puerta (patada: se abre de golpe con un pequeño rebote) y chispa (impacto de bala: destello breve).
"""
from __future__ import annotations
import math
import random
from estudio.blender import kit as K

PARAMETROS = {"semilla": 11, "luz_dia": 1.0}

ALTO = 3.2
ANCLAS_DOC = {"puerta": "centro de la puerta (y = 0)", "enemigo": "detrás del escritorio, mirando a la puerta"}


def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    rnd = random.Random(p["semilla"])
    s = K.bpy.context.scene
    K.cielo_dia(s, cenit=(0.12, 0.30, 0.78), horizonte=(0.62, 0.74, 0.92), fuerza=1.1 * p["luz_dia"])
    col = K.coleccion("ESCENARIO_cqb")
    c_arq, c_mob = K.coleccion("arquitectura", col), K.coleccion("mobiliario", col)
    c_luz, c_anim, c_fx = K.coleccion("luces", col), K.coleccion("animado", col), K.coleccion("efectos", col)
    M, caja, cil, esf = K.material, K.caja, K.cilindro, K.esfera

    # ------------------------------------------------------------------ materiales
    pared = M("pared_crema", (0.5, 0.46, 0.4), 0.85, ruido=0.05, escala_ruido=6)
    pared_osc = M("pared_pasillo", (0.38, 0.33, 0.28), 0.8, ruido=0.08, escala_ruido=5)
    boiserie = M("boiserie", (0.55, 0.5, 0.42), 0.55)
    techo = M("techo", (0.5, 0.49, 0.47), 0.9)
    parquet = M("parquet", (0.30, 0.17, 0.09), 0.3, ladrillo=((0.22, 0.12, 0.065), 9.0), ruido=0.04, escala_ruido=30, rug_var=0.05)
    alfombra = M("alfombra", (0.22, 0.03, 0.04), 0.95, ruido=0.2, escala_ruido=30)
    alfombra_borde = M("alfombra_borde", (0.82, 0.7, 0.45), 0.9, ruido=0.1, escala_ruido=40)
    runner = M("alfombra_pasillo", (0.12, 0.1, 0.14), 0.95, ruido=0.15, escala_ruido=30)
    nogal = M("nogal", (0.16, 0.08, 0.04), 0.35, ruido=0.2, escala_ruido=14, ladrillo=((0.12, 0.06, 0.03), 8.0))
    nogal_claro = M("roble", (0.4, 0.25, 0.12), 0.45, ruido=0.2, escala_ruido=12)
    cuero = M("cuero", (0.2, 0.1, 0.06), 0.4, ruido=0.25, escala_ruido=60)
    tela = M("tela_gris", (0.32, 0.33, 0.36), 0.95, ruido=0.1, escala_ruido=50)
    cortina = M("cortina", (0.55, 0.5, 0.42), 0.95, ruido=0.08, escala_ruido=35)
    latón = M("laton", (0.8, 0.6, 0.25), 0.25, 1.0)
    metal_neg = M("metal_negro", (0.03, 0.03, 0.035), 0.4, 0.9)
    vid = K.vidrio("vidrio_ventanal", (0.75, 0.85, 0.9), 0.08)
    cielo_em = K.emisivo("exterior_brillante", (0.7, 0.82, 1.0), 1.6)
    lampara = K.emisivo("pantalla_lampara", (1.0, 0.78, 0.5), 9.0)
    aplique = K.emisivo("aplique_pasillo", (1.0, 0.7, 0.4), 12.0)
    marco = M("marco_cuadro", (0.5, 0.36, 0.14), 0.35, 0.8)
    arte = [M(f"cuadro_{i}", c, 0.7, ruido=0.6, escala_ruido=4) for i, c in
            enumerate(((0.12, 0.25, 0.4), (0.5, 0.2, 0.1), (0.18, 0.32, 0.2)))]
    hojas = M("hojas_interior", (0.05, 0.16, 0.05), 0.7, ruido=0.4, escala_ruido=7)
    maceta = M("maceta", (0.7, 0.68, 0.64), 0.5)
    libros = [M(f"libro_{i}", c, 0.7, ruido=0.2) for i, c in enumerate(
        ((0.35, 0.05, 0.05), (0.05, 0.12, 0.3), (0.08, 0.25, 0.12), (0.4, 0.3, 0.12), (0.12, 0.1, 0.1), (0.55, 0.5, 0.4)))]
    papel = M("papel", (0.85, 0.85, 0.8), 0.9)
    pant = M("pantalla_laptop", (0.02, 0.03, 0.05), 0.2, emision=(0.3, 0.5, 0.8), fuerza=1.2)

    # ------------------------------------------------------------------ pasillo (y de −11 a 0)
    Y0, X = -11.0, 1.1
    caja("piso_pasillo", (0, (Y0) / 2, -0.05), (2 * X, -Y0 + 0.3, 0.1), parquet, c_arq)
    caja("alfombra_pasillo", (0, Y0 / 2, 0.012), (1.3, -Y0 - 0.4, 0.02), runner, c_arq)
    caja("techo_pasillo", (0, Y0 / 2, ALTO + 0.05), (2 * X + 0.4, -Y0 + 0.3, 0.1), techo, c_arq)
    for sx in (-1, 1):
        caja(f"pared_pasillo_{sx}", (sx * (X + 0.1), Y0 / 2, ALTO / 2), (0.2, -Y0 + 0.3, ALTO), pared_osc, c_arq)
        caja(f"friso_pasillo_{sx}", (sx * (X - 0.01), Y0 / 2, 0.55), (0.04, -Y0, 1.1), boiserie, c_arq)
        caja(f"zocalo_pasillo_{sx}", (sx * (X - 0.02), Y0 / 2, 0.08), (0.05, -Y0, 0.16), nogal, c_arq)
    caja("pared_fondo_pasillo", (0, Y0 - 0.1, ALTO / 2), (2 * X + 0.4, 0.2, ALTO), pared_osc, c_arq)
    # apliques del pasillo: poca luz cálida (el pasillo queda en penumbra frente a la habitación luminosa)
    for i, y in enumerate((-9.2, -6.2, -3.2)):
        for sx in (-1, 1):
            caja(f"aplique_{i}_{sx}", (sx * (X - 0.08), y, 2.0), (0.1, 0.12, 0.3), aplique, c_luz)
            K.luz(f"luz_aplique_{i}_{sx}", "POINT", (sx * (X - 0.3), y, 2.1), 28, (1.0, 0.68, 0.4), c_luz, radio=0.08,
                  sombra=False)
    # mesa de arrimo con jarrón al fondo del pasillo
    caja("arrimo", (0, Y0 + 0.3, 0.45), (1.0, 0.35, 0.9), nogal, c_mob, bisel=0.01)
    cil("jarron", (0, Y0 + 0.3, 1.05), 0.11, 0.4, maceta, c_mob)

    # ------------------------------------------------------------------ muro de la puerta (y = 0) y marco
    for nombre, cx, w in (("muro_puerta_o", -2.8, 4.4), ("muro_puerta_e", 2.8, 4.4)):
        caja(nombre, (cx, 0, ALTO / 2), (w, 0.3, ALTO), pared, c_arq)
    caja("muro_puerta_dintel", (0, 0, 2.7), (1.2, 0.3, 1.0), pared, c_arq)
    for sx in (-1, 1):
        caja(f"jamba_{sx}", (sx * 0.58, 0, 1.2), (0.08, 0.34, 2.4), nogal, c_arq)
    caja("dintel_marco", (0, 0, 2.43), (1.24, 0.34, 0.08), nogal, c_arq)
    # hoja de la puerta: bisagra a la izquierda (x = −0.5); se abre hacia la habitación (rotación +Z)
    piv = K.vacio("puerta_bisagra", (-0.5, 0.0, 0.0), c_anim)
    hoja = caja("puerta_hoja", (0.0, 0.0, 1.2), (1.0, 0.07, 2.4), nogal, c_anim, bisel=0.01)
    K.padre(hoja, piv)
    for j, (zc, h) in enumerate(((0.55, 0.7), (1.45, 0.9), (2.1, 0.3))):
        pn = caja(f"puerta_panel_{j}", (0.0, 0.045, zc), (0.7, 0.02, h), M(f"panel_puerta_{j}", (0.2, 0.1, 0.05), 0.4), c_anim)
        K.padre(pn, piv)
    tir = cil("puerta_tirador", (0.4, 0.06, 1.05), 0.02, 0.14, latón, c_anim, eje="Y")
    K.padre(tir, piv)

    # ------------------------------------------------------------------ habitación: estudio de lujo (x ±5, y 0.15 a 8.6)
    XR, YF = 5.0, 8.6
    caja("piso_sala", (0, YF / 2, -0.05), (2 * XR, YF + 0.3, 0.1), parquet, c_arq)
    caja("techo_sala", (0, YF / 2, ALTO + 0.05), (2 * XR + 0.6, YF + 0.3, 0.1), techo, c_arq)
    for k in range(3):   # casetones del techo
        caja(f"casetón_{k}", (0, 1.8 + k * 2.7, ALTO - 0.05), (7.6, 0.12, 0.1), boiserie, c_arq)
    caja("muro_izq", (-XR - 0.15, YF / 2, ALTO / 2), (0.3, YF + 0.3, ALTO), pared, c_arq)
    # muro derecho con ventanal (hueco entre y 2.2 y 6.6, z 0.7 a 2.7)
    caja("muro_der_a", (XR + 0.15, 1.1, ALTO / 2), (0.3, 2.2, ALTO), pared, c_arq)
    caja("muro_der_b", (XR + 0.15, 7.6, ALTO / 2), (0.3, 2.0, ALTO), pared, c_arq)
    caja("muro_der_bajo", (XR + 0.15, 4.4, 0.35), (0.3, 4.4, 0.7), pared, c_arq)
    caja("muro_der_alto", (XR + 0.15, 4.4, 2.95), (0.3, 4.4, 0.5), pared, c_arq)
    caja("vidrio_der", (XR + 0.15, 4.4, 1.7), (0.04, 4.4, 2.0), vid, c_arq)
    # muro del fondo con gran ventanal (x −3.4 a 3.4)
    caja("muro_fondo_o", (-4.2, YF + 0.15, ALTO / 2), (1.6, 0.3, ALTO), pared, c_arq)
    caja("muro_fondo_e", (4.2, YF + 0.15, ALTO / 2), (1.6, 0.3, ALTO), pared, c_arq)
    caja("muro_fondo_bajo", (0, YF + 0.15, 0.4), (6.8, 0.3, 0.8), pared, c_arq)
    caja("muro_fondo_alto", (0, YF + 0.15, 3.0), (6.8, 0.3, 0.4), pared, c_arq)
    caja("vidrio_fondo", (0, YF + 0.15, 1.8), (6.8, 0.04, 2.0), vid, c_arq)
    for i in range(5):   # parantes del ventanal
        caja(f"parante_fondo_{i}", (-3.4 + i * 1.7, YF + 0.12, 1.8), (0.06, 0.08, 2.05), metal_neg, c_arq)
    for i in range(3):
        caja(f"parante_der_{i}", (XR + 0.12, 2.2 + i * 2.2, 1.7), (0.08, 0.06, 2.05), metal_neg, c_arq)
    # exterior luminoso y luz de día entrando por los dos ventanales
    # exterior: jardín y árboles lejanos (se ven por los ventanales); el cielo es el del mundo
    verde = M("pasto_exterior", (0.1, 0.22, 0.06), 0.9, ruido=0.4, escala_ruido=3)
    K.plano("jardin_exterior", (0, 4, -0.02), (400, 400, 1), verde, c_fx)
    for k in range(40):
        ang = rnd.uniform(0, math.tau)
        d = rnd.uniform(25, 90)
        tx, ty = math.cos(ang) * d, math.sin(ang) * d + 4
        if abs(tx) < 12 and ty < 14:
            continue
        h = rnd.uniform(5, 11)
        cil(f"tronco_ext_{k}", (tx, ty, h / 4), 0.3, h / 2, M("tronco_ext", (0.1, 0.06, 0.03), 0.9), c_fx, lados=6)
        esf(f"copa_ext_{k}", (tx, ty, h * 0.7), h * 0.4, M("copa_ext", (0.06, 0.2, 0.05), 0.8, ruido=0.4), c_fx, escala=(1, 1, 1.1))
    K.luz("sol_ventanal", "SUN", (0, 20, 20), 4.2 * p["luz_dia"], (1.0, 0.93, 0.8), c_luz,
          rot=(math.radians(62), 0, math.radians(18)))
    for nom, pos, rot, tam, en in (("dia_fondo", (0, YF + 1.2, 1.9), (math.radians(90), 0, 0), 6.4, 420),
                                   ("dia_derecha", (XR + 1.2, 4.4, 1.8), (0, math.radians(-90), 0), 4.2, 320)):
        lz = K.luz(nom, "AREA", pos, en * p["luz_dia"], (0.8, 0.9, 1.0), c_luz, rot=rot, tam=tam, sombra=False)
        lz.visible_camera = False          # ilumina la sala pero no se ve como un panel blanco por la ventana
    # zócalo y boiserie
    for nombre, c, t in (("izq", (-XR + 0.02, YF / 2, 0.55), (0.04, YF, 1.1)),):
        caja(f"friso_{nombre}", c, t, boiserie, c_arq)
    caja("zocalo_izq", (-XR + 0.03, YF / 2, 0.09), (0.06, YF, 0.18), nogal, c_arq)
    caja("zocalo_fondo_o", (-4.2, YF - 0.03, 0.09), (1.6, 0.06, 0.18), nogal, c_arq)
    caja("zocalo_fondo_e", (4.2, YF - 0.03, 0.09), (1.6, 0.06, 0.18), nogal, c_arq)

    for k in range(5):      # boiserie: paneles enmarcados en el muro izquierdo y junto a la puerta
        yc = 0.9 + k * 1.65
        if not (0.8 < yc + 0.8 and yc - 0.8 < 2.6 or 6.4 < yc + 0.8) or True:
            for dz, hh in ((0.62, 0.85),):
                caja(f"panel_izq_{k}", (-XR + 0.05, yc + 0.35, dz + 0.1), (0.03, 1.35, hh), boiserie, c_arq)
    # ------------------------------------------------------------------ alfombra, sofá, mesa baja
    caja("alfombra_borde", (0, 4.2, 0.011), (5.4, 3.8, 0.02), alfombra_borde, c_mob)
    caja("alfombra_centro", (0, 4.2, 0.022), (5.0, 3.4, 0.02), alfombra, c_mob)
    # sofá de cuero contra el muro izquierdo
    caja("sofa_asiento", (-3.9, 4.6, 0.32), (1.0, 2.4, 0.42), cuero, c_mob, bisel=0.06)
    caja("sofa_respaldo", (-4.4, 4.6, 0.72), (0.25, 2.4, 0.8), cuero, c_mob, bisel=0.06)
    for sy in (-1, 1):
        caja(f"sofa_brazo_{sy}", (-3.9, 4.6 + sy * 1.25, 0.5), (1.0, 0.18, 0.62), cuero, c_mob, bisel=0.05)
    for k in range(3):
        caja(f"almohadón_{k}", (-3.72, 3.9 + k * 0.7, 0.62), (0.7, 0.62, 0.1), tela, c_mob, bisel=0.04)
    caja("mesa_baja", (-1.7, 4.6, 0.22), (1.1, 1.5, 0.05), nogal, c_mob, bisel=0.01)
    for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        caja(f"pata_mesa_{sx}{sy}", (-1.7 + sx * 0.48, 4.6 + sy * 0.68, 0.1), (0.05, 0.05, 0.2), latón, c_mob)
    esf("jarron_mesa", (-1.7, 4.6, 0.38), 0.12, cuero, c_mob, escala=(1, 1, 1.3))
    for k, (cx, cy) in enumerate(((-2.8, 3.0), (-2.8, 6.1))):   # sillones laterales
        caja(f"sillón_{k}", (cx, cy, 0.3), (0.85, 0.85, 0.42), tela, c_mob, bisel=0.06, rot_z=math.radians(30 if k == 0 else -30))
        caja(f"sillón_resp_{k}", (cx - 0.35, cy, 0.7), (0.15, 0.85, 0.8), tela, c_mob, bisel=0.05, rot_z=math.radians(30 if k == 0 else -30))

    # ------------------------------------------------------------------ escritorio ejecutivo (cobertura del enemigo)
    DX, DY = 3.1, 6.5
    caja("escritorio_tapa", (DX, DY, 0.76), (2.4, 1.1, 0.07), nogal, c_mob, bisel=0.015)
    caja("escritorio_frente", (DX, DY - 0.5, 0.4), (2.3, 0.06, 0.7), nogal, c_mob)
    for sx in (-1, 1):
        caja(f"escritorio_lado_{sx}", (DX + sx * 1.1, DY, 0.4), (0.08, 1.0, 0.7), nogal, c_mob)
        caja(f"escritorio_cajon_{sx}", (DX + sx * 0.8, DY, 0.4), (0.5, 0.9, 0.6), nogal_claro, c_mob)
    pc = caja("laptop_base", (DX - 0.5, DY - 0.1, 0.8), (0.34, 0.24, 0.015), metal_neg, c_mob)
    pt = caja("laptop_pantalla", (DX - 0.5, DY + 0.06, 0.92), (0.34, 0.012, 0.22), pant, c_mob)
    pt.rotation_euler = (math.radians(-12), 0, 0)
    cil("lampara_pie", (DX + 0.8, DY + 0.2, 0.9), 0.025, 0.28, latón, c_mob)
    esf("lampara_pantalla", (DX + 0.8, DY + 0.2, 1.12), 0.12, lampara, c_mob, escala=(1, 1, 0.8))
    for k in range(4):
        pp = caja(f"papeles_{k}", (DX + 0.1 + k * 0.05, DY - 0.2 + k * 0.04, 0.8 + k * 0.004), (0.3, 0.21, 0.004), papel, c_mob)
        pp.rotation_euler = (0, 0, math.radians(rnd.uniform(-20, 20)))
    cil("vaso", (DX - 0.1, DY - 0.35, 0.83), 0.035, 0.1, K.vidrio("vidrio_vaso", (0.9, 0.7, 0.4), 0.3), c_mob)
    sil = caja("silla_asiento", (DX + 1.5, DY + 1.3, 0.5), (0.6, 0.6, 0.1), cuero, c_mob, bisel=0.03, rot_z=math.radians(-35))
    caja("silla_resp", (DX + 1.65, DY + 1.55, 0.9), (0.6, 0.1, 0.8), cuero, c_mob, bisel=0.03, rot_z=math.radians(-35))
    cil("silla_pie", (DX + 1.5, DY + 1.3, 0.22), 0.04, 0.44, metal_neg, c_mob)

    # ------------------------------------------------------------------ biblioteca en el muro izquierdo (fondo) y libros instanciados
    BX = -XR + 0.35
    for i, (y0, y1) in enumerate(((0.8, 2.6), (6.4, 8.2))):
        w = y1 - y0
        cy = (y0 + y1) / 2
        caja(f"biblio_lado_a_{i}", (BX, y0, 1.35), (0.45, 0.05, 2.7), nogal, c_mob)
        caja(f"biblio_lado_b_{i}", (BX, y1, 1.35), (0.45, 0.05, 2.7), nogal, c_mob)
        caja(f"biblio_fondo_{i}", (BX - 0.2, cy, 1.35), (0.03, w, 2.7), nogal, c_mob)
        for h in (0.1, 0.6, 1.1, 1.6, 2.1, 2.62):
            caja(f"estante_{i}_{h}", (BX, cy, h), (0.45, w, 0.04), nogal, c_mob)
    proto = K.prototipo("PROTO_libros")
    x = 0.0
    for k in range(9):
        w = rnd.uniform(0.035, 0.06)
        h = rnd.uniform(0.2, 0.3)
        caja(f"libro_{k}", (0, x + w / 2, h / 2), (0.18, w, h), libros[k % len(libros)], proto)
        x += w + 0.004
    anch = x
    for i, (y0, y1) in enumerate(((0.8, 2.6), (6.4, 8.2))):
        for fila, h in enumerate((0.12, 0.62, 1.12, 1.62, 2.12)):
            y = y0 + 0.08
            while y + anch < y1 - 0.05:
                if rnd.random() < 0.8:
                    K.instancia(f"libros_{i}_{fila}_{int(y * 10)}", proto, (BX + 0.02, y, h), 0, 1.0, c_mob)
                y += anch + rnd.uniform(0.0, 0.25)
    # ------------------------------------------------------------------ cuadros, cortinas, plantas, lámpara de pie
    for k, (yc, w, h, a) in enumerate(((2.2, 1.0, 0.7, 0), (4.4, 1.4, 0.9, 1), (6.2, 0.8, 1.0, 2))):
        caja(f"cuadro_marco_{k}", (-XR + 0.03, yc, 1.9), (0.04, w + 0.1, h + 0.1), marco, c_arq)
        caja(f"cuadro_{k}", (-XR + 0.055, yc, 1.9), (0.02, w, h), arte[a], c_arq)
    for sx in (-1, 1):
        caja(f"cortina_fondo_{sx}", (sx * 3.7, YF - 0.2, 1.65), (0.5, 0.18, 2.9), cortina, c_mob, bisel=0.04)
    for sy in (2.0, 6.8):
        caja(f"cortina_der_{sy}", (XR - 0.2, sy, 1.65), (0.18, 0.5, 2.9), cortina, c_mob, bisel=0.04)
    for k, (px, py) in enumerate(((-4.3, 8.0), (4.3, 1.2))):
        cil(f"maceta_{k}", (px, py, 0.25), 0.22, 0.5, maceta, c_mob)
        for j in range(4):
            esf(f"hojas_{k}_{j}", (px + rnd.uniform(-0.15, 0.15), py + rnd.uniform(-0.15, 0.15), 0.75 + j * 0.22), 0.3 - j * 0.04,
                hojas, c_mob, escala=(1, 1, 0.8))
    cil("pie_lampara", (-4.3, 3.0, 0.75), 0.02, 1.5, latón, c_mob)
    esf("pantalla_pie", (-4.3, 3.0, 1.6), 0.2, lampara, c_mob, escala=(1, 1, 0.8))
    K.luz("luz_lampara_pie", "POINT", (-4.3, 3.0, 1.6), 160, (1.0, 0.75, 0.5), c_luz, radio=0.2, sombra=False)
    K.luz("luz_lampara_escritorio", "POINT", (DX + 0.8, DY + 0.2, 1.12), 90, (1.0, 0.75, 0.5), c_luz, radio=0.12, sombra=False)
    # lámpara de techo (aro de esferas)
    for k in range(8):
        a = k * math.tau / 8
        esf(f"candil_{k}", (math.cos(a) * 0.55, 4.2 + math.sin(a) * 0.55, ALTO - 0.45), 0.07, lampara, c_mob)
    cil("candil_eje", (0, 4.2, ALTO - 0.2), 0.02, 0.4, latón, c_mob)
    K.luz("luz_candil", "AREA", (0, 4.2, ALTO - 0.15), 200, (1.0, 0.82, 0.62), c_luz, tam=2.6, sombra=False)
    K.luz("luz_relleno_sala", "AREA", (0, 3.0, ALTO - 0.05), 120, (0.95, 0.92, 0.9), c_luz, tam=5.0, sombra=False)
    K.luz("luz_pasillo_puerta", "AREA", (0, -1.2, ALTO - 0.05), 60, (1.0, 0.8, 0.6), c_luz, tam=1.6, sombra=False)

    anclas = {
        "puerta": (0.0, 0.0, 0.0), "pasillo": (0.0, -3.0, 0.0), "centro_sala": (0.0, 4.2, 0.0), "enemigo": (1.2, 6.9, 0.0),
        "escritorio": (DX, DY, 0.8), "ventanal": (0.0, YF, 1.6), "sofa": (-3.9, 4.6, 0.5), "biblioteca": (BX, 7.3, 1.2),
    }
    return {"anclas": anclas, "animables": {"puerta": piv, "col_fx": c_fx}, "parametros": p}


def abrir_puerta(animables, frame_inicio: int, duracion_f: int = 9, angulo_deg: float = 104.0):
    """Patada: la hoja sale de golpe hacia la habitación, pasa un poco del tope y rebota."""
    piv = animables["puerta"]
    K.clave(piv, "rotation_euler", frame_inicio, 0.0, 2)
    K.clave(piv, "rotation_euler", frame_inicio + duracion_f, math.radians(angulo_deg), 2)
    K.clave(piv, "rotation_euler", frame_inicio + duracion_f + 5, math.radians(angulo_deg - 9), 2)
    K.clave(piv, "rotation_euler", frame_inicio + duracion_f + 10, math.radians(angulo_deg - 6), 2)


def chispa(animables, frame_inicio: int, pos, duracion_f: int = 2, energia: float = 90.0, tam: float = 0.028):
    """Destello breve de un impacto de bala en `pos` (esfera emisiva + luz puntual visibles `duracion_f` fotogramas)."""
    col = animables["col_fx"]
    mat = K.emisivo("chispa_impacto", (1.0, 0.85, 0.5), 60.0)
    n = f"chispa_{frame_inicio}_{int(abs(pos[0]) * 10)}_{int(abs(pos[1]) * 10)}"
    e = K.esfera(n, tuple(pos), tam, mat, col, subdiv=2)
    l = K.luz(n + "_luz", "POINT", tuple(pos), energia, (1.0, 0.8, 0.5), col, radio=0.04, sombra=False)
    for ob in (e, l):
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=frame_inicio)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=frame_inicio + duracion_f)
        for fc in K._fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
