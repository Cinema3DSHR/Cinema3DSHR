"""p013 · Mi hogar ideal — diseño de la casa como DATOS (coordenadas de Godot: x este, y arriba, z sur, metros).

Genera `layout.json`, que lee la escena de Godot (godot/herramientas/principal.gd). Todo el diseño está acá: si hay que
mover un mueble, cambiar un recorrido de cámara o la duración de una frase, se edita este archivo y se regenera. El
mismo script valida que la cámara no atraviese paredes ni muebles.

    python3 producciones/p013_mi_hogar_ideal/disenio.py            # escribe layout.json y valida
    python3 producciones/p013_mi_hogar_ideal/disenio.py --duraciones audio/duraciones.json   # con la voz real

Casa moderna de una planta, 18 × 11 m, techo plano. Frente al SUR (z = 11): living, comedor y cocina abiertos con
ventanales; fondo al NORTE (z = 0): habitación principal, baño y dos cuartos. Entrada centrada (x = 9). Cochera al ESTE.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
GUION = json.loads((AQUI / "guion.json").read_text())
MED = json.loads((AQUI / "medidas_modelos.json").read_text())
ALTO = 2.8          # altura de los muros
ESP_EXT, ESP_INT = 0.22, 0.12
YAW = {"S": 0.0, "E": 90.0, "N": 180.0, "O": 270.0}   # el frente de los modelos mira a +Z (sur) con yaw 0

# ───────────────────────────────────────────────────────── tiempos (de la voz real si existe; si no, estimados)
CPS, PAUSA = GUION["velocidad_estimada_caracteres_por_s"], GUION["pausa_entre_frases_s"]
BEATS = GUION["beats"]
if "--duraciones" in sys.argv:
    real = json.loads(Path(sys.argv[sys.argv.index("--duraciones") + 1]).read_text())
    DUR = [round(real[b["id"]] + PAUSA, 2) for b in BEATS]
    FUENTE_TIEMPOS = "voz real (duraciones medidas del audio)"
else:
    DUR = [round(len(b["texto"]) / CPS + PAUSA, 2) for b in BEATS]
    FUENTE_TIEMPOS = "ESTIMADOS por cantidad de caracteres (todavía no hay audio)"
INI = [round(sum(DUR[:i]), 3) for i in range(len(DUR))]
TOTAL = round(sum(DUR), 2)
BI = {b["id"].split("_")[0]: i for i, b in enumerate(BEATS)}      # "b04" -> 3

# ───────────────────────────────────────────────────────── contenedores
items: list[dict] = []        # todo lo que se ve (pared, mueble, procedural)
luces: list[dict] = []
solidos: list[dict] = []      # cajas para validar la cámara (x0,x1,z0,z1,y0,y1)


def aparece(beat: str, off: float = 0.0, hasta: str | None = None, hasta_frac: float | None = None) -> dict:
    """Cuándo se ve: en la apertura (gancho, estado final), se oculta al empezar b02 y reaparece en su beat."""
    t_on = INI[BI[beat]] + off
    t_off = None
    if hasta:
        t_off = INI[BI[hasta]] + (DUR[BI[hasta]] * hasta_frac if hasta_frac is not None else 0.0)
    return {"t_on": round(t_on, 2), "t_off": None if t_off is None else round(t_off, 2)}


def caja(nombre, x, y, z, sx, sy, sz, mat, beat, off=0.0, crece=False, hook=True, solido=True, hasta=None, hasta_frac=None,
         grupo="", mueve=None):
    """Caja con el CENTRO de su base en (x, y, z)."""
    it = {"tipo": "caja", "nombre": nombre, "pos": [x, y, z], "tam": [sx, sy, sz], "mat": mat, "grupo": grupo,
          "vis": aparece(beat, off, hasta, hasta_frac), "hook": hook, "crece": crece, "mueve": mueve}
    items.append(it)
    if solido:
        solidos.append({"n": nombre, "x0": x - sx / 2, "x1": x + sx / 2, "z0": z - sz / 2, "z1": z + sz / 2, "y0": y, "y1": y + sy})
    return it


def cil(nombre, x, y, z, r, h, mat, beat, off=0.0, hook=True, solido=False, hasta=None, hasta_frac=None, grupo=""):
    it = {"tipo": "cil", "nombre": nombre, "pos": [x, y, z], "tam": [r, h, r], "mat": mat, "grupo": grupo,
          "vis": aparece(beat, off, hasta, hasta_frac), "hook": hook, "crece": False, "mueve": None}
    items.append(it)
    if solido:
        solidos.append({"n": nombre, "x0": x - r, "x1": x + r, "z0": z - r, "z1": z + r, "y0": y, "y1": y + h})
    return it


def esfera(nombre, x, y, z, r, mat, beat, off=0.0, esc=(1, 1, 1), hook=True, solido=False, grupo=""):
    it = {"tipo": "esfera", "nombre": nombre, "pos": [x, y, z], "tam": [r * esc[0], r * esc[1], r * esc[2]], "mat": mat,
          "grupo": grupo, "vis": aparece(beat, off), "hook": hook, "crece": False, "mueve": None}
    items.append(it)
    if solido:
        solidos.append({"n": nombre, "x0": x - r * esc[0], "x1": x + r * esc[0], "z0": z - r * esc[2], "z1": z + r * esc[2],
                        "y0": y - r * esc[1], "y1": y + r * esc[1]})
    return it


def mueble(modelo, x, z, mira, beat, off=0.0, y=0.0, esc=1.0, hook=True, hasta=None, hasta_frac=None, mueve=None, grupo="",
           rot_extra=0.0, solido=True):
    """Modelo de la biblioteca (CC0). `mira` = N/S/E/O o grados; las medidas salen de medidas_modelos.json."""
    yaw = YAW[mira] if isinstance(mira, str) else float(mira)
    yaw += rot_extra
    m = MED[modelo]
    it = {"tipo": "modelo", "nombre": modelo, "modelo": modelo, "pos": [x, y, z], "yaw": yaw, "esc": esc, "grupo": grupo,
          "vis": aparece(beat, off, hasta, hasta_frac), "hook": hook, "crece": False, "mueve": mueve}
    items.append(it)
    if solido:
        a = math.radians(yaw)
        w, d = m["w"] * esc, m["d"] * esc
        ex = abs(w * math.cos(a)) + abs(d * math.sin(a))
        ez = abs(w * math.sin(a)) + abs(d * math.cos(a))
        solidos.append({"n": modelo, "x0": x - ex / 2, "x1": x + ex / 2, "z0": z - ez / 2, "z1": z + ez / 2,
                        "y0": y, "y1": y + m["h"] * esc})
    return it


# ───────────────────────────────────────────────────────── arquitectura
def muro(nombre, p1, p2, esp, mat, aberturas, beat, off=0.0, alto=ALTO, marco=True):
    """Muro alineado a un eje con aberturas [{c, a, s, h, tipo}] (c = centro sobre el eje, a = ancho, s = antepecho, h = dintel)."""
    (x1, z1), (x2, z2) = p1, p2
    horiz = abs(z2 - z1) < 1e-6          # corre a lo largo de x
    a0, a1 = (min(x1, x2), max(x1, x2)) if horiz else (min(z1, z2), max(z1, z2))
    fijo = z1 if horiz else x1
    cortes = sorted(aberturas, key=lambda o: o["c"])
    tramos, cur = [], a0
    for o in cortes:
        tramos.append((cur, o["c"] - o["a"] / 2))
        cur = o["c"] + o["a"] / 2
    tramos.append((cur, a1))

    def pieza(n, ini, fin, y0, y1, mt=mat, solido=True):
        if fin - ini < 0.01 or y1 - y0 < 0.01:
            return
        c = (ini + fin) / 2
        L = fin - ini
        if horiz:
            caja(f"{nombre}_{n}", c, y0, fixed(fijo), L, y1 - y0, esp, mt, beat, off, crece=True, solido=solido)
        else:
            caja(f"{nombre}_{n}", fixed(fijo), y0, c, esp, y1 - y0, L, mt, beat, off, crece=True, solido=solido)

    def fixed(v):
        return v

    for i, (ini, fin) in enumerate(tramos):
        pieza(f"t{i}", ini, fin, 0.0, alto)
    for j, o in enumerate(cortes):
        ini, fin = o["c"] - o["a"] / 2, o["c"] + o["a"] / 2
        tipo = o.get("tipo", "ventana")
        sill = 0.0 if tipo in ("puerta", "hueco") else o["s"]
        head = o["h"]
        pieza(f"b{j}", ini, fin, 0.0, sill)
        pieza(f"d{j}", ini, fin, head, alto)
        if tipo == "ventana":
            c = o["c"]
            if horiz:
                caja(f"{nombre}_v{j}", c, sill, fijo, o["a"], head - sill, 0.04, "vidrio", beat, off + 0.5, solido=False)
            else:
                caja(f"{nombre}_v{j}", fijo, sill, c, 0.04, head - sill, o["a"], "vidrio", beat, off + 0.5, solido=False)
            if marco:
                gr = 0.07
                for k, (cx, cy, sx, sy) in enumerate([(c, sill, o["a"], gr), (c, head - gr, o["a"], gr)]):
                    if horiz:
                        caja(f"{nombre}_m{j}{k}", cx, cy, fijo, sx, sy, 0.1, "marco", beat, off + 0.5, solido=False)
                    else:
                        caja(f"{nombre}_m{j}{k}", fijo, cy, cx, 0.1, sy, sx, "marco", beat, off + 0.5, solido=False)
                n_mont = max(2, int(o["a"] // 1.9) + 1)
                for k in range(n_mont + 1):
                    px = ini + (fin - ini) * k / n_mont
                    if horiz:
                        caja(f"{nombre}_p{j}{k}", px, sill, fijo, gr, head - sill, 0.1, "marco", beat, off + 0.5, solido=False)
                    else:
                        caja(f"{nombre}_p{j}{k}", fijo, sill, px, 0.1, head - sill, gr, "marco", beat, off + 0.5, solido=False)


def arquitectura():
    b3 = "b03"
    # losas y piso
    caja("piso_interior", 9.0, -0.12, 5.5, 18.0, 0.12, 11.0, "piso_madera", "b02", crece=False, solido=False)
    caja("piso_bano", 7.5, 0.0, 2.6, 2.8, 0.012, 5.0, "piso_piedra", "b10", crece=False, solido=False, off=0.0)
    caja("terraza", 9.0, -0.12, 12.2, 4.6, 0.14, 2.2, "piso_piedra", "b03", crece=False, solido=False)
    # muros exteriores (frente sur con ventanales y puerta de entrada)
    muro("sur", (0, 11), (18, 11), ESP_EXT, "estuco",
         [{"c": 3.55, "a": 5.7, "s": 0.12, "h": 2.55, "tipo": "ventana"},
          {"c": 9.0, "a": 1.1, "s": 0, "h": 2.2, "tipo": "puerta"},
          {"c": 14.35, "a": 5.9, "s": 0.12, "h": 2.55, "tipo": "ventana"}], "b02")
    muro("norte", (0, 0), (18, 0), ESP_EXT, "estuco",
         [{"c": 3.0, "a": 3.0, "s": 0.9, "h": 2.4, "tipo": "ventana"},
          {"c": 7.5, "a": 1.0, "s": 1.5, "h": 2.3, "tipo": "ventana"},
          {"c": 11.3, "a": 2.4, "s": 0.9, "h": 2.4, "tipo": "ventana"},
          {"c": 15.8, "a": 2.6, "s": 0.9, "h": 2.4, "tipo": "ventana"}], "b02")
    muro("oeste", (0, 0), (0, 11), ESP_EXT, "estuco", [{"c": 2.6, "a": 1.6, "s": 0.9, "h": 2.3, "tipo": "ventana"}], "b02")
    muro("este", (18, 0), (18, 11), ESP_EXT, "estuco", [{"c": 8.2, "a": 1.4, "s": 1.0, "h": 2.3, "tipo": "ventana"}], "b02")
    # pilastras de piedra en el frente (relieve)
    caja("piedra_1", 7.15, 0.0, 11.14, 1.2, ALTO, 0.12, "piedra", "b02", crece=True, solido=False)
    caja("piedra_2", 10.85, 0.0, 11.14, 1.2, ALTO, 0.12, "piedra", "b02", crece=True, solido=False)
    # interiores: tabique de los cuartos con puertas hacia el pasillo, y divisorias
    muro("tabique", (0, 5.2), (18, 5.2), ESP_INT, "estuco_int",
         [{"c": 4.7, "a": 0.95, "tipo": "puerta", "h": 2.1}, {"c": 7.5, "a": 0.85, "tipo": "puerta", "h": 2.1},
          {"c": 11.2, "a": 0.95, "tipo": "puerta", "h": 2.1}, {"c": 15.4, "a": 0.95, "tipo": "puerta", "h": 2.1}],
         "b02", marco=False)
    for n, x in (("div1", 6.0), ("div2", 9.0), ("div3", 13.5)):
        muro(n, (x, 0), (x, 5.2), ESP_INT, "estuco_int", [], "b02", marco=False)
    # techo plano con alero, cochera y columnas
    caja("techo", 9.0, ALTO, 5.5, 19.2, 0.25, 12.6, "hormigon", "b03", crece=False, solido=False)
    caja("cielorraso", 9.0, ALTO - 0.03, 5.5, 17.7, 0.03, 10.7, "cielorraso", "b03", crece=False, solido=False)
    caja("techo_cochera", 21.5, ALTO, 8.2, 6.4, 0.25, 7.6, "hormigon", "b12", crece=False, solido=False)
    caja("col_cochera_1", 24.4, 0.0, 4.6, 0.25, ALTO, 0.25, "hormigon", "b12", crece=True, solido=True)
    caja("col_cochera_2", 24.4, 0.0, 11.8, 0.25, ALTO, 0.25, "hormigon", "b12", crece=True, solido=True)
    caja("piso_cochera", 21.5, -0.12, 11.0, 6.4, 0.13, 14.0, "hormigon_piso", "b12", crece=False, solido=False)


# ───────────────────────────────────────────────────────── ambientes
def sala():
    b = "b04"
    caja("alfombra_sala", 2.45, 0.0, 8.2, 3.3, 0.02, 2.9, "alfombra", b, 0.2, solido=False)
    mueble("sofa_corner_sofa_2", 3.95, 8.3, "O", b, 0.5)
    mueble("armchair_armchair_10", 1.7, 6.5, 135, b, 0.9)
    caja("mesa_ratona", 2.2, 0.0, 8.2, 0.9, 0.38, 1.2, "madera_clara", b, 1.2, solido=True)
    caja("mueble_tv", 0.45, 0.0, 8.2, 0.45, 0.5, 1.9, "madera_oscura", b, 1.5)
    mueble("prop_tv", 0.28, 8.2, "E", b, 1.8, y=0.75, esc=1.9, solido=False)
    for k, (cx, cy, sx, sy, sz) in enumerate([(0.14, 1.78, 0.03, 0.04, 2.5), (0.14, 0.62, 0.03, 0.04, 2.5)]):
        caja(f"neon_tv_h{k}", cx, cy, 8.2, sx, sy, sz, "neon_magenta", b, 2.2, solido=False)
    for k, z in enumerate((6.95, 9.45)):
        caja(f"neon_tv_v{k}", 0.14, 0.62, z, 0.03, 1.2, 0.04, "neon_magenta", b, 2.2, solido=False)
    mueble("shelf_bookcase_7" if "shelf_bookcase_7" in MED else "shelf_shelves_4", 2.6, 5.48, "S", b, 2.4, hook=True)
    mueble("bush_decorative_plant", 0.55, 10.4, "S", b, 2.6)
    mueble("bush_plant_3", 6.0, 10.4, "S", b, 2.8)
    # lámpara de pie
    cil("pie_lampara_poste", 5.0, 0.0, 6.0, 0.015, 1.55, "marco", b, 3.0)
    cil("pie_lampara_pantalla", 5.0, 1.45, 6.0, 0.2, 0.3, "pantalla", b, 3.0)
    # b05: la pared vacía se llena (cuadro + luz indirecta)
    caja("cuadro", 4.4, 1.25, 5.31, 1.5, 1.0, 0.04, "cuadro", "b05", 2.5, solido=False)
    caja("cuadro_marco", 4.4, 1.2, 5.285, 1.62, 1.12, 0.03, "madera_oscura", "b05", 2.4, solido=False)
    caja("luz_indirecta_pared", 4.4, 2.62, 5.3, 3.4, 0.04, 0.06, "luz_calida", "b05", 3.4, solido=False)
    luces.append({"nombre": "Luz_indirecta_pared", "pos": [4.4, 2.5, 5.7], "color": [1.0, 0.78, 0.5], "tipo": "foco", "dir": [0, -0.2, -1]})
    luces.append({"nombre": "Luz_sala_1", "pos": [3.0, 2.55, 8.0], "color": [1.0, 0.8, 0.55], "tipo": "puntual"})
    luces.append({"nombre": "Luz_sala_2", "pos": [1.8, 2.55, 6.4], "color": [1.0, 0.8, 0.55], "tipo": "puntual"})
    luces.append({"nombre": "Luz_neon_tv", "pos": [0.7, 1.2, 8.2], "color": [0.9, 0.2, 0.9], "tipo": "puntual"})


def comedor():
    b = "b06"
    mv = {"dz": 0.85, "off": 3.0, "dur": 1.2}           # se corre hacia el ventanal después de mostrarla
    zc = 8.1
    mueble("table_table_6", 8.9, zc, "E", b, 0.4, mueve=mv, rot_extra=0.0)
    ch = []
    for i, dx in enumerate((-0.8, 0.0, 0.8)):
        mueble("chair_oak_chair", 8.9 + dx, zc - 0.75, "S", b, 0.9 + 0.12 * i, mueve=mv)
        mueble("chair_oak_chair", 8.9 + dx, zc + 0.75, "N", b, 1.2 + 0.12 * i, mueve=mv)
    caja("florero", 8.9, 0.74, zc, 0.12, 0.32, 0.12, "ceramica", b, 2.2, mueve=mv, solido=False)
    esfera("flores", 8.9, 1.13, zc, 0.15, "flor_rosa", b, 2.3, esc=(1, 0.8, 1))
    items[-1]["mueve"] = mv
    for k, dx in enumerate((-0.6, 0.6)):
        cil(f"colgante_cable_{k}", 8.9 + dx, 1.75, zc + mv["dz"], 0.006, 1.05, "marco", b, 3.6)
        cil(f"colgante_pantalla_{k}", 8.9 + dx, 1.55, zc + mv["dz"], 0.17, 0.2, "pantalla_negra", b, 3.6)
        cil(f"colgante_luz_{k}", 8.9 + dx, 1.52, zc + mv["dz"], 0.12, 0.03, "luz_calida", b, 3.6)
    luces.append({"nombre": "Luz_comedor_1", "pos": [8.3, 1.45, zc + mv["dz"]], "color": [1.0, 0.76, 0.48], "tipo": "puntual"})
    luces.append({"nombre": "Luz_comedor_2", "pos": [9.5, 1.45, zc + mv["dz"]], "color": [1.0, 0.76, 0.48], "tipo": "puntual"})


def cocina():
    b = "b07"
    hv = INI[BI[b]] + DUR[BI[b]] * 0.42          # a mitad del beat cambia de propuesta
    zc = 8.3
    # propuesta A: mesa en el medio (se descarta)
    mueble("table_oak_table", 14.8, zc, "S", b, 0.4, hook=False, hasta=b, hasta_frac=0.42, grupo="cocina_A")
    for i, (dx, dz, m) in enumerate(((-0.85, 0, "E"), (0.85, 0, "O"), (0, -0.85, "S"), (0, 0.85, "N"))):
        mueble("chair_chair_12", 14.8 + dx, zc + dz, m, b, 0.7 + 0.1 * i, hook=False, hasta=b, hasta_frac=0.42, grupo="cocina_A")
    # propuesta B (la que queda): módulo contra el tabique + isla
    t = f"+{DUR[BI[b]] * 0.42:.2f}"
    offB = DUR[BI[b]] * 0.44
    mueble("fridge_large_fridge", 12.35, 5.75, "S", b, offB)
    xs = [13.5, 14.1, 14.7, 15.3, 15.9, 16.5]
    modelos = ["cabinet_lower_cabinet", "cabinet_sink_cabinet", "cabinet_lower_cabinet", "stove_double_oven",
               "cabinet_lower_cabinet", "cabinet_lower_cabinet"]
    for i, (x, m) in enumerate(zip(xs, modelos)):
        mueble(m, x, 5.55, "S", b, offB + 0.15 + 0.1 * i)
    mueble("cabinet_lower_corner_cabinet", 17.4, 5.65, "S", b, offB + 0.8)
    caja("mesada", 15.45, 0.89, 5.55, 4.5, 0.04, 0.66, "marmol", b, offB + 0.9, solido=False)
    mueble("stove_range_hood", 15.0, 5.45, "S", b, offB + 1.0, y=1.55, solido=False)
    for i, x in enumerate((13.5, 14.1, 15.9, 16.5)):
        mueble("cabinet_upper_cabinet_2", x, 5.42, "S", b, offB + 1.1 + 0.08 * i, y=1.55, solido=False)
    caja("isla", 14.9, 0.0, 8.35, 2.6, 0.9, 0.95, "madera_clara", b, offB + 1.2)
    caja("isla_tapa", 14.9, 0.9, 8.35, 2.8, 0.05, 1.1, "marmol", b, offB + 1.25, solido=False)
    for i, dx in enumerate((-0.8, 0.0, 0.8)):
        mueble("chair_stool_5", 14.9 + dx, 9.05, "N", b, offB + 1.5 + 0.1 * i)
    cil("colgante_isla_a", 14.1, 1.7, 8.35, 0.006, 1.1, "marco", b, offB + 1.7)
    cil("colgante_isla_b", 15.7, 1.7, 8.35, 0.006, 1.1, "marco", b, offB + 1.7)
    caja("colgante_isla_pa", 14.1, 1.5, 8.35, 0.4, 0.2, 0.4, "pantalla_negra", b, offB + 1.7, solido=False)
    caja("colgante_isla_pb", 15.7, 1.5, 8.35, 0.4, 0.2, 0.4, "pantalla_negra", b, offB + 1.7, solido=False)
    luces.append({"nombre": "Luz_cocina_1", "pos": [14.0, 2.55, 7.0], "color": [1.0, 0.84, 0.62], "tipo": "puntual"})
    luces.append({"nombre": "Luz_cocina_2", "pos": [16.4, 2.55, 7.0], "color": [1.0, 0.84, 0.62], "tipo": "puntual"})
    luces.append({"nombre": "Luz_isla", "pos": [14.9, 1.4, 8.35], "color": [1.0, 0.78, 0.5], "tipo": "puntual"})
    caja("led_bajo_alacena", 15.0, 1.5, 5.4, 3.3, 0.03, 0.05, "luz_calida", b, offB + 1.3, solido=False)


def principal():
    b = "b08"
    caja("alfombra_principal", 3.0, 0.0, 2.6, 3.4, 0.02, 3.2, "alfombra", b, 0.3, solido=False)
    mueble("bed_bed_6", 3.0, 1.35, "S", b, 0.5)
    mueble("table_bedside_table_2", 1.45, 0.5, "S", b, 1.1)
    mueble("table_bedside_table_2", 4.55, 0.5, "S", b, 1.2)
    mueble("table_desk_lamp_4", 1.45, 0.5, "S", b, 1.6, y=0.45, solido=False)
    mueble("table_desk_lamp_4", 4.55, 0.5, "S", b, 1.7, y=0.45, solido=False)
    mueble("closet_wardrobe_3", 0.5, 3.4, "E", b, 2.2)
    mueble("armchair_armchair_9", 4.9, 4.2, 135, b, 2.8)
    caja("neon_cama", 3.0, 1.95, 0.16, 2.7, 0.04, 0.04, "neon_violeta", b, 3.0, solido=False)
    caja("neon_cama_v1", 1.65, 1.0, 0.16, 0.04, 0.95, 0.04, "neon_violeta", b, 3.1, solido=False)
    caja("neon_cama_v2", 4.35, 1.0, 0.16, 0.04, 0.95, 0.04, "neon_violeta", b, 3.1, solido=False)
    mueble("bush_plant_3", 5.4, 0.7, "S", b, 3.4)
    luces.append({"nombre": "Luz_principal_1", "pos": [3.0, 2.55, 2.6], "color": [1.0, 0.78, 0.55], "tipo": "puntual"})
    luces.append({"nombre": "Luz_neon_cama", "pos": [3.0, 1.7, 0.5], "color": [0.75, 0.3, 1.0], "tipo": "puntual"})
    luces.append({"nombre": "Luz_velador_1", "pos": [1.45, 1.0, 0.55], "color": [1.0, 0.7, 0.4], "tipo": "puntual"})
    luces.append({"nombre": "Luz_velador_2", "pos": [4.55, 1.0, 0.55], "color": [1.0, 0.7, 0.4], "tipo": "puntual"})


def cuartos():
    b = "b09"
    mueble("bed_bed_4", 11.2, 1.3, "S", b, 0.3)
    mueble("table_bedside_table_2", 12.55, 0.45, "S", b, 0.8)
    mueble("table_desk_lamp_4", 12.55, 0.45, "S", b, 1.0, y=0.45, solido=False)
    mueble("cabinet_high_cabinet", 9.5, 2.5, "E", b, 1.2)
    caja("alfombra_cuarto2", 11.2, 0.0, 2.7, 2.3, 0.02, 2.4, "alfombra", b, 0.2, solido=False)
    luces.append({"nombre": "Luz_cuarto2", "pos": [11.2, 2.55, 2.6], "color": [1.0, 0.82, 0.6], "tipo": "puntual"})
    # estudio (segunda frase)
    b = "b09b"
    mueble("table_desk_9", 15.7, 0.6, "S", b, 0.3)
    mueble("chair_osaka_chair", 15.7, 1.55, "N", b, 0.9)
    mueble("shelf_vertical_shelves", 17.6, 2.8, "O", b, 1.4)
    mueble("bush_little_plant", 15.2, 0.6, "S", b, 1.9, y=0.72, solido=False)
    luces.append({"nombre": "Luz_estudio", "pos": [15.7, 2.55, 2.6], "color": [0.95, 0.9, 0.8], "tipo": "puntual"})


def bano():
    b = "b10"
    mueble("bath_shower_stall", 8.35, 0.75, "O", b, 0.3)
    mueble("toilet_toilet_unit", 6.55, 1.0, "E", b, 1.0)
    mueble("cabinet_vanity", 6.55, 3.4, "E", b, 1.6)
    caja("espejo", 6.17, 1.1, 3.4, 0.03, 1.0, 0.8, "espejo", b, 2.2, solido=False)
    mueble("bush_little_plant", 6.5, 3.4, "E", b, 2.8, y=0.93, solido=False)
    caja("neon_espejo", 6.19, 2.12, 3.4, 0.03, 0.03, 0.9, "luz_calida", b, 2.4, solido=False)
    luces.append({"nombre": "Luz_bano", "pos": [7.5, 2.5, 2.6], "color": [1.0, 0.95, 0.88], "tipo": "puntual"})


def hacia(x, z, tx, tz):
    """Yaw para que un modelo (frente +Z) mire del punto (x, z) hacia (tx, tz)."""
    return math.degrees(math.atan2(tx - x, tz - z))


def libros(x0, y, z, largo, beat, off, eje="x", n=None, alto=0.26, prof=0.2, nombre="libros"):
    """Fila de libros de colores sobre un estante (cajas finas); eje = dirección de la fila."""
    n = n or max(3, int(largo / 0.045))
    cols = ("libro_a", "libro_b", "libro_c", "libro_d", "libro_e")
    for i in range(n):
        a = largo / n
        pos = x0 + i * a + a / 2
        h = alto * (0.78 + 0.22 * ((i * 7) % 5) / 4)
        if eje == "x":
            caja(f"{nombre}_{i}", pos, y, z, a * 0.86, h, prof, cols[(i * 3) % 5], beat, off + 0.03 * i, solido=False)
        else:
            caja(f"{nombre}_{i}", x0, y, pos, prof, h, a * 0.86, cols[(i * 3) % 5], beat, off + 0.03 * i, solido=False)


def cuadro(nombre, x, y, z, w, h, eje, mat, beat, off):
    """Cuadro con marco sobre un muro. eje: 'z' = pegado a un muro que corre en x; 'x' = a uno que corre en z."""
    if eje == "z":
        caja(nombre + "_m", x, y - 0.04, z, w + 0.1, h + 0.1, 0.035, "madera_oscura", beat, off, solido=False)
        caja(nombre, x, y, z, w, h, 0.045, mat, beat, off + 0.05, solido=False)
    else:
        caja(nombre + "_m", x, y - 0.04, z, 0.035, h + 0.1, w + 0.1, "madera_oscura", beat, off, solido=False)
        caja(nombre, x, y, z, 0.045, h, w, mat, beat, off + 0.05, solido=False)


def cortinas(nombre, x0, x1, z, beat, off, alto=2.65, eje="x"):
    # cortinero: barra de acero con remates y anillas, un poco más ancho que el vano
    if eje == "x":
        caja(nombre + "_barra", (x0 + x1) / 2, alto + 0.04, z, (x1 - x0) + 0.2, 0.025, 0.025, "acero", beat, off, solido=False)
        for k, xr in enumerate((x0 - 0.1, x1 + 0.1)):
            caja(f"{nombre}_remate_{k}", xr, alto + 0.025, z, 0.05, 0.055, 0.05, "acero", beat, off, solido=False)
        for k in range(10):
            caja(f"{nombre}_anilla_{k}", x0 + 0.1 + (x1 - x0 - 0.2) * k / 9, alto + 0.0, z, 0.02, 0.07, 0.04, "acero", beat, off + 0.1, solido=False)
    for k, (c, w) in enumerate(((x0 + 0.65, 1.3), (x1 - 0.65, 1.3))):
        if eje == "x":
            caja(f"{nombre}_{k}", c, 0.0, z, w, alto, 0.05, "cortina", beat, off + 0.2 * k, solido=False)
        else:
            caja(f"{nombre}_{k}", z, 0.0, c, 0.05, alto, w, "cortina", beat, off + 0.2 * k, solido=False)


def auto_dr(nombre, modelo, x, z, mira, beat, off=0.0):
    """Auto de Dream Racing: carrocería del GLB + ruedas generadas con el código del juego (wheel_gen.gd)."""
    yaw = YAW[mira] if isinstance(mira, str) else float(mira)
    items.append({"tipo": "auto_dr", "nombre": nombre, "modelo": modelo, "pos": [x, 0.0, z], "yaw": yaw, "esc": 1.0, "grupo": "",
                  "vis": aparece(beat, off), "hook": True, "crece": False, "mueve": None})
    m = MED[modelo]
    a = math.radians(yaw)
    ex = abs(m["w"] * math.cos(a)) + abs(m["d"] * math.sin(a))
    ez = abs(m["w"] * math.sin(a)) + abs(m["d"] * math.cos(a))
    solidos.append({"n": nombre, "x0": x - ex / 2, "x1": x + ex / 2, "z0": z - ez / 2, "z1": z + ez / 2, "y0": 0.0, "y1": m["h"]})


marcadores: list[dict] = []
LOTE = {"x0": -8.0, "x1": 32.0, "z0": -4.0, "z1": 29.2}


def _cam_muestras():
    out, t = [], 0.0
    while t < TOTAL:
        out.append(pos_cam(t)[0])
        t += 0.5
    return out


def parcela():
    """Terreno, cerco con rejas, portones, calle, árboles reales y colinas: el horizonte nunca queda vacío."""
    import random
    b = "b11"
    x0, x1, z0, z1 = LOTE["x0"], LOTE["x1"], LOTE["z0"], LOTE["z1"]
    # calle y vereda
    caja("calle", 10.0, -0.15, 36.0, 140.0, 0.12, 8.6, "asfalto", "b03", crece=False, solido=False)
    caja("vereda", 10.0, -0.15, 30.2, 140.0, 0.2, 2.0, "vereda", "b03", crece=False, solido=False)
    caja("cordon", 10.0, -0.15, 31.25, 140.0, 0.26, 0.2, "hormigon", "b03", crece=False, solido=False)
    for i in range(-6, 8):
        caja(f"calle_raya_{i}", 10.0 + i * 9.0, -0.03, 36.0, 3.0, 0.01, 0.16, "pintura_vial", "b03", crece=False, solido=False)
    for i, x in enumerate((-2.0, 13.0, 28.0)):
        mueble("streetlight_classic_lamppost", x, 31.0, "S", b, 3.0 + 0.2 * i, esc=1.35)
        luces.append({"nombre": f"Luz_calle_{i + 1}", "pos": [x, 3.4, 31.0], "color": [1.0, 0.8, 0.55], "tipo": "puntual"})
    # autos estacionados en la calle (vida en el barrio)
    auto_dr("auto_calle_1", "gt", -6.0, 33.2, "E", b, 3.4)
    auto_dr("auto_calle_2", "gt", 27.5, 33.2, "O", b, 3.5)
    mueble("sc_sports_car", 35.5, 38.8, "E", b, 3.6)
    # cerco del frente: base de piedra, pilares y rejas; portón peatonal en x = 9 y portón de autos en x = 21.5
    tramos = [(x0, 8.2), (9.8, 19.5), (23.5, x1)]
    for a, c in tramos:
        caja(f"cerco_zocalo_{a:.0f}", (a + c) / 2, 0.0, z1, c - a, 0.42, 0.28, "piedra", b, 2.0, solido=True)
        n = max(1, int((c - a) // 2.0))
        paso = (c - a) / n
        for k in range(n):
            mueble("fence_fence_grid", a + paso * (k + 0.5), z1, "S", b, 2.0 + 0.05 * k, y=0.42, esc=paso / 2.0, solido=False)
    for i, x in enumerate([x0 + 4.0 * k for k in range(int((x1 - x0) // 4) + 1)] + [8.2, 9.8, 19.5, 23.5]):
        caja(f"pilar_{i}", x, 0.0, z1, 0.5, 1.5, 0.5, "piedra", b, 2.2, solido=True)
        caja(f"pilar_tapa_{i}", x, 1.5, z1, 0.6, 0.08, 0.6, "hormigon", b, 2.3, solido=False)
    for i, x in enumerate((8.2, 9.8, 19.5, 23.5)):
        caja(f"pilar_luz_{i}", x, 1.38, z1 - 0.26, 0.14, 0.1, 0.03, "luz_calida", b, 3.0, solido=False)
        luces.append({"nombre": f"Luz_porton_{i + 1}", "pos": [x, 1.2, z1 - 0.5], "color": [1.0, 0.78, 0.5], "tipo": "puntual"})
    mueble("gate_gate_3", 9.0, z1, "S", b, 2.4, esc=0.58, solido=False)
    mueble("gate_gate_3", 20.55, z1, "S", b, 2.5, solido=False)
    mueble("gate_gate_3", 22.45, z1, "S", b, 2.6, solido=False)
    # laterales y fondo: cerco de madera con zócalo
    for lado, xf in (("oeste", x0), ("este", x1)):
        zc = (z0 + z1) / 2
        caja(f"cerco_zocalo_{lado}", xf, 0.0, zc, 0.24, 0.3, z1 - z0, "hormigon", b, 3.0, solido=True)
        n = int((z1 - z0) // 1.8)
        for k in range(n):
            mueble("fence_fence_4", xf, z0 + 1.8 * (k + 0.5), "E", b, 3.0 + 0.03 * k, y=0.3, solido=False)
    caja("cerco_zocalo_fondo", (x0 + x1) / 2, 0.0, z0, x1 - x0, 0.3, 0.24, "hormigon", b, 3.0, solido=True)
    for k in range(int((x1 - x0) // 1.8)):
        mueble("fence_fence_4", x0 + 1.8 * (k + 0.5), z0, "S", b, 3.0 + 0.03 * k, y=0.3, solido=False)
    # seto contra el cerco del frente
    for k, x in enumerate([x0 + 0.8 + 1.15 * i for i in range(int((x1 - x0) / 1.15))]):
        if 7.4 < x < 10.8 or 19.0 < x < 24.0:
            continue
        mueble("bush_plant", x, z1 - 0.95, "S", b, 3.2 + 0.03 * k, esc=1.05 + 0.1 * ((k * 5) % 3), solido=False)
    # árboles de la parcela (reales de Sweet Home): fila de álamos como pantalla, sauce, abedul, palmeras en el portón
    rng = random.Random(11)
    cam = _cam_muestras()

    def arbol(modelo, x, z, esc, off, giro=None):
        m = MED[modelo]
        r = max(m["w"], m["d"]) * esc * 0.5 + 0.8
        for (cx, cy, cz) in cam:
            if cy < m["h"] * esc + 0.5 and (cx - x) ** 2 + (cz - z) ** 2 < r * r:
                return False
        for s in solidos:
            if s["y0"] < 3.0 and s["x0"] - r * 0.6 < x < s["x1"] + r * 0.6 and s["z0"] - r * 0.6 < z < s["z1"] + r * 0.6 and s["n"].startswith(("sur", "norte", "este", "oeste", "tabique", "piso")):
                return False
        mueble(modelo, x, z, giro if giro is not None else rng.uniform(0, 360), b, off, esc=esc, solido=False)
        solidos.append({"n": modelo, "x0": x - 0.35, "x1": x + 0.35, "z0": z - 0.35, "z1": z + 0.35, "y0": 0.0, "y1": 6.0})
        return True

    heroes = [("tree_tree", 2.8, 18.5, 0.9), ("tree_birch", 15.0, 21.5, 0.9), ("tree_weeping_willow", -3.4, 14.0, 0.8),
              ("tree_quaking_aspen", 14.0, 15.5, 0.8), ("tree_black_tupelo", -4.8, 5.5, 0.75), ("tree_sassafras", 27.5, 3.0, 0.7),
              ("tree_fan_palm_tree", 6.4, 27.6, 1.0), ("tree_fan_palm_tree", 11.6, 27.6, 1.0), ("tree_palm_tree", -3.0, 25.0, 0.8),
              ("sc_palm_tree", 28.5, 22.5, 0.75), ("sc_cypress", 5.2, 12.9, 0.6), ("sc_cypress", 12.8, 12.9, 0.6),
              ("sc_acacia", 26.0, 14.0, 0.8), ("sc_pine", -5.5, 20.5, 0.9), ("tree_tree", 18.5, 25.5, 0.8)]
    for k, (mm, x, z, e) in enumerate(heroes):
        arbol(mm, x, z, e, 3.4 + 0.12 * k)
    for k in range(8):                                          # álamos: pantalla viva a ambos lados
        arbol("tree_lombardy_poplar", x0 + 1.3, z0 + 3.5 + k * 3.6, 0.95, 3.8 + 0.1 * k, 0)
        arbol("tree_lombardy_poplar", x1 - 1.3, z0 + 3.5 + k * 3.6, 0.95, 3.8 + 0.1 * k, 0)
    # anillo de arboleda más allá del cerco: cierra el horizonte en todas las direcciones
    especies = ["tree_tree", "tree_black_tupelo", "tree_sassafras", "tree_quaking_aspen", "tree_birch", "sc_acacia", "sc_pine",
                "tree_weeping_willow", "sc_palm_tree", "tree_lombardy_poplar", "sc_pine", "tree_tree"]
    puestos = 0
    intentos = 0
    colocados: list[tuple] = []
    while puestos < 70 and intentos < 4000:
        intentos += 1
        ang = rng.uniform(0, 2 * math.pi)
        rad = rng.uniform(26.0, 62.0)
        x, z = 10.0 + rad * math.cos(ang) * 1.25, 12.0 + rad * math.sin(ang)
        if z > 28.0 and (x0 - 30 < x < x1 + 40):                # lado de la calle: sólo del otro lado, lejos
            if z < 46.0:
                continue
        if x0 - 1.0 < x < x1 + 1.0 and z0 - 1.0 < z < z1 + 1.0:
            continue
        if any((x - cx) ** 2 + (z - cz) ** 2 < 36.0 for cx, cz in colocados):
            continue
        mm = rng.choice(especies)
        if arbol(mm, x, z, rng.uniform(0.85, 1.45), 3.6 + 0.02 * puestos):
            colocados.append((x, z))
            puestos += 1
    # colinas lejanas
    for k, (x, z, rx, rz) in enumerate(((-120, -40, 95, 70), (10, -125, 130, 60), (150, -20, 95, 75), (-130, 60, 90, 80), (140, 80, 95, 70))):
        esfera(f"colina_{k}", x, -6.0, z, 1.0, "colina", "b02", esc=(rx, 17.0, rz))


def exterior():
    b = "b11"
    # canteros con flores (de entrada: hortensias reales y flores)
    for nom, x0, x1 in (("cantero_oeste", 0.4, 6.3), ("cantero_este", 11.7, 17.6)):
        c = (x0 + x1) / 2
        caja(nom + "_borde", c, 0.0, 12.05, x1 - x0, 0.32, 0.9, "piedra", b, 0.4, solido=True)
        caja(nom + "_tierra", c, 0.32, 12.05, x1 - x0 - 0.12, 0.04, 0.78, "tierra", b, 0.5, solido=False)
        n = int((x1 - x0) / 0.62)
        for i in range(n):
            x = x0 + 0.4 + i * (x1 - x0 - 0.8) / max(1, n - 1)
            col = ("flor_violeta", "flor_rosa", "flor_blanca")[i % 3]
            esfera(f"{nom}_flor{i}", x, 0.62, 11.95 + 0.14 * math.sin(i * 1.7), 0.26, col, b, 0.9 + 0.09 * i, esc=(1, 0.85, 1))
        for i in range(4):
            mueble("sc_hydrangea", x0 + 0.8 + i * (x1 - x0 - 1.6) / 3, 12.3, "S", b, 1.0 + 0.1 * i, y=0.32, esc=1.2, solido=False)
        mueble("sc_lavender_bush", x0 + 0.5, 12.35, "S", b, 1.6, y=0.32, esc=1.0, solido=False)
        mueble("sc_lavender_bush", x1 - 0.5, 12.35, "S", b, 1.7, y=0.32, esc=1.0, solido=False)
    # camino de piedras desde la puerta hasta el portón
    for i in range(14):
        caja(f"sendero_{i}", 9.0 + (0.12 if i % 2 else -0.12), 0.0, 14.1 + 1.1 * i, 0.9, 0.05, 0.55, "piso_piedra", b, 1.5 + 0.1 * i, solido=False)
    # farolitos del sendero
    for i in range(10):
        x = 7.8 if i % 2 == 0 else 10.2
        z = 14.5 + 3.1 * (i // 2)
        cil(f"farol_poste_{i}", x, 0.0, z, 0.03, 0.75, "marco", b, 3.4 + 0.12 * i)
        cil(f"farol_cap_{i}", x, 0.72, z, 0.09, 0.14, "luz_jardin", b, 3.4 + 0.12 * i)
        luces.append({"nombre": f"Luz_jardin_{i + 1}", "pos": [x, 0.8, z], "color": [1.0, 0.72, 0.4], "tipo": "puntual"})
    # entrada cubierta: techito, columnas, puerta, felpudo, maceteros, farolas de pared, número y buzón
    caja("porche_techo", 9.0, ALTO, 12.7, 5.4, 0.22, 1.9, "hormigon", "b03", crece=False, solido=False)
    mueble("streetlight_porch_column", 6.5, 13.45, "S", "b03", 1.2, solido=True)
    mueble("streetlight_porch_column_2", 11.5, 13.45, "S", "b03", 1.3, solido=True)
    caja("puerta_entrada", 9.0, 0.0, 11.0, 1.04, 2.12, 0.06, "madera_oscura", "b03", 1.6, solido=False)
    caja("puerta_manija", 9.38, 1.0, 11.06, 0.04, 0.3, 0.04, "marco", "b03", 1.8, solido=False)
    caja("felpudo", 9.0, 0.0, 11.7, 0.9, 0.025, 0.55, "felpudo", "b03", 2.2, solido=False)
    mueble("bush_plant_box", 8.0, 11.55, "S", "b03", 2.3, solido=False)
    mueble("bush_plant_box", 10.0, 11.55, "S", "b03", 2.4, solido=False)
    mueble("bush_decorative_plant", 7.65, 11.8, "S", "b03", 2.5, solido=False)
    mueble("bush_decorative_plant", 10.35, 11.8, "S", "b03", 2.6, solido=False)
    mueble("bench_painted_bench", 11.0, 12.3, "S", "b03", 2.8, solido=False)
    caja("numero_casa", 10.2, 1.9, 11.13, 0.2, 0.12, 0.02, "marco", "b03", 2.9, solido=False)
    mueble("trash_mailbox", 5.6, z1m(), "S", b, 2.0, solido=False)
    for i, x in enumerate((8.3, 9.7)):
        caja(f"farola_pared_{i}", x, 2.0, 11.14, 0.09, 0.3, 0.07, "luz_calida", "b03", 3.0, solido=False)
    luces.append({"nombre": "Luz_entrada", "pos": [9.0, 2.5, 12.2], "color": [1.0, 0.78, 0.5], "tipo": "puntual"})
    luces.append({"nombre": "Luz_fachada_1", "pos": [3.5, 0.2, 12.6], "color": [1.0, 0.8, 0.6], "tipo": "puntual"})
    luces.append({"nombre": "Luz_fachada_2", "pos": [14.5, 0.2, 12.6], "color": [1.0, 0.8, 0.6], "tipo": "puntual"})
    mueble("rock_stone_lantern", 12.3, 14.6, "S", b, 2.4, solido=False)
    mueble("rock_rock_2", 4.6, 21.0, "S", b, 2.6, solido=False)
    mueble("rock_rock_3", 14.2, 24.0, "S", b, 2.7, solido=False)
    mueble("sc_dog_house", 2.0, 14.5, "S", b, 3.0, solido=True)
    mueble("prop_fountain_2", 13.8, 18.8, "S", b, 3.1, esc=1.2, solido=True)


def z1m():
    return 28.2


def cochera():
    b = "b12"
    # pickup PAMPERO Yaguareté de Dream Racing, con las ruedas del juego; sedán deportivo al lado; escarabajo en la entrada
    auto_dr("pickup_dr", "pickup", 19.9, 8.1, "S", b, 0.6)
    auto_dr("hatch_r2", "hatch", 22.95, 8.2, "S", b, 1.0)
    auto_dr("auto_entrada", "gt", 21.5, 19.0, "N", b, 1.4)
    caja("led_cochera", 21.5, 2.62, 4.7, 5.6, 0.04, 0.05, "luz_calida", b, 1.6, solido=False)
    mueble("prop_barbecue", 24.0, 5.2, "S", b, 2.0, solido=False)
    mueble("crate_crate_2", 18.9, 5.0, "S", b, 2.1, solido=False)
    luces.append({"nombre": "Luz_cochera_1", "pos": [20.2, 2.65, 7.6], "color": [1.0, 0.9, 0.78], "tipo": "puntual"})
    luces.append({"nombre": "Luz_cochera_2", "pos": [22.7, 2.65, 7.6], "color": [1.0, 0.9, 0.78], "tipo": "puntual"})


def decorar():
    """Detalles: cuadros, libros, cortinas, plantas, objetos de uso. Ningún ambiente queda vacío."""
    # ── sala (b04 / b05)
    b = "b04"
    mueble("prop_fireplace_2", 1.75, 5.5, "S", b, 4.0)
    marcadores.append({"nombre": "FX_fuego_chimenea", "pos": [1.75, 0.35, 5.7]})
    luces.append({"nombre": "Luz_chimenea", "pos": [1.75, 0.6, 5.9], "color": [1.0, 0.5, 0.2], "tipo": "puntual"})
    cuadro("cuadro_chimenea", 1.75, 1.75, 5.3, 1.3, 0.75, "z", "cuadro2", b, 4.4)
    mueble("armchair_armchair_7", 1.9, 10.0, hacia(1.9, 10.0, 3.2, 8.3), b, 3.6)
    cortinas("cortina_sala", 0.7, 6.4, 10.85, b, 3.8)
    mueble("bush_indoor_plant", 6.1, 6.0, "S", b, 4.2)
    caja("florero_sala", 2.25, 0.38, 8.0, 0.11, 0.3, 0.11, "ceramica", b, 4.8, solido=False)
    esfera("flores_sala", 2.25, 0.74, 8.0, 0.14, "flor_rosa", b, 4.9, esc=(1, 0.8, 1))
    libros(1.95, 0.38, 8.45, 0.3, b, 5.0, eje="z", n=5, alto=0.07, prof=0.18, nombre="libros_ratona")
    cil("vela_1", 2.2, 0.38, 7.7, 0.04, 0.1, "cera", b, 5.2)
    caja("manta_sofa", 4.4, 0.62, 8.9, 0.5, 0.05, 0.6, "tela_naranja", b, 5.0, solido=False)
    # ── comedor (b06)
    b = "b06"
    mueble("cabinet_dresser_2", 9.0, 5.5, "S", b, 3.2)
    cuadro("cuadro_comedor", 9.0, 1.55, 5.3, 1.5, 0.95, "z", "cuadro3", b, 3.5)
    mueble("bush_decorative_plant_2", 8.2, 5.5, "S", b, 3.8, y=0.9, solido=False)
    mueble("bush_spider_plant", 9.8, 5.5, "S", b, 3.9, y=0.9, solido=False)
    caja("alfombra_comedor", 8.9, 0.0, 8.9, 3.6, 0.02, 2.6, "alfombra2", b, 0.2, solido=False)
    cortinas("cortina_comedor", 7.1, 11.3, 10.85, b, 3.6)
    mueble("cabinet_shoe_cabinet", 10.45, 10.66, "N", b, 4.2)
    cuadro("espejo_recibidor", 10.45, 1.5, 10.86, 0.9, 0.9, "z", "espejo", b, 4.4)
    # ── cocina (b07)
    b = "b07"
    off = DUR[BI[b]] * 0.44
    caja("azulejos_cocina", 15.6, 0.92, 5.27, 4.7, 0.62, 0.03, "azulejo", b, off + 1.2, solido=False)
    mueble("stove_microwave", 16.3, 5.55, "S", b, off + 1.6, y=0.93, solido=False)
    for i, (dx, col) in enumerate(((-0.35, "fruta_naranja"), (0.0, "fruta_verde"), (0.35, "fruta_roja"))):
        esfera(f"fruta_{i}", 14.9 + dx, 0.97, 8.35 + 0.05 * i, 0.06, col, b, off + 2.2 + 0.08 * i)
    cil("fuente_frutas", 14.9, 0.93, 8.35, 0.2, 0.06, "ceramica", b, off + 2.1)
    caja("tabla_cortar", 14.1, 0.935, 5.5, 0.5, 0.03, 0.32, "madera_clara", b, off + 2.0, solido=False)
    cil("pava", 15.4, 0.93, 5.55, 0.08, 0.2, "acero", b, off + 2.2)
    mueble("bush_decorative_plant_2", 17.5, 5.5, "S", b, off + 2.4, y=0.93, solido=False)
    cortinas("cortina_cocina", 11.7, 17.6, 10.85, b, off + 2.0)
    # ── principal (b08)
    b = "b08"
    cortinas("cortina_principal", 1.6, 4.6, 0.2, b, 3.4)
    mueble("cabinet_dresser", 5.6, 2.3, "O", b, 3.0)
    mueble("table_desk_lamp_2", 5.6, 2.3, "O", b, 3.3, y=0.62, solido=False)
    cuadro("cuadro_principal", 5.88, 1.55, 2.3, 0.9, 0.7, "x", "cuadro2", b, 3.6)
    libros(1.3, 0.45, 0.5, 0.2, b, 3.8, n=4, alto=0.05, prof=0.14, nombre="libros_velador")
    caja("manta_cama", 3.0, 0.62, 2.1, 1.9, 0.05, 0.8, "tela_violeta", b, 3.2, solido=False)
    for k, dx in enumerate((-0.55, 0.0, 0.55)):
        caja(f"almohada_{k}", 3.0 + dx, 0.66, 0.65, 0.5, 0.14, 0.32, "tela_blanca", b, 3.0 + 0.1 * k, solido=False)
    # ── visitas (b09) y estudio (b09b)
    b = "b09"
    cortinas("cortina_visitas", 10.3, 12.4, 0.2, b, 1.6)
    cuadro("cuadro_visitas", 11.2, 1.6, 0.17, 1.0, 0.7, "z", "cuadro3", b, 1.9)
    mueble("bush_indoor_plant", 12.9, 4.6, "S", b, 2.0)
    caja("manta_visitas", 11.2, 0.5, 2.3, 1.45, 0.05, 0.7, "tela_celeste", b, 1.4, solido=False)
    b = "b09b"
    mueble("prop_monitor_lcd", 15.7, 0.45, "S", b, 1.0, y=0.72, solido=False)
    mueble("table_desk_lamp_3", 16.5, 0.5, "S", b, 1.2, y=0.72, solido=False)
    mueble("shelf_bookcase_5", 17.55, 2.9, "O", b, 1.6)
    libros(16.95, 0.5, 2.9, 1.9, b, 2.2, eje="z", n=26, alto=0.3, prof=0.2, nombre="libros_estudio")
    libros(16.95, 1.05, 2.9, 1.9, b, 2.6, eje="z", n=26, alto=0.28, prof=0.2, nombre="libros_estudio_b")
    cortinas("cortina_estudio", 14.5, 17.1, 0.2, b, 2.4)
    caja("alfombra_estudio", 15.7, 0.0, 1.8, 2.2, 0.02, 1.8, "alfombra2", b, 0.3, solido=False)
    # ── baño (b10)
    b = "b10"
    caja("toallas", 8.55, 1.3, 2.6, 0.06, 0.45, 0.3, "tela_blanca", b, 2.6, solido=False)
    caja("alfombra_bano", 7.6, 0.012, 3.2, 1.0, 0.015, 0.6, "tela_celeste", b, 2.4, solido=False)
    mueble("shelf_shelves_4", 8.7, 4.0, "O", b, 3.0, y=1.0, solido=False)
    mueble("bush_spider_plant", 8.7, 4.0, "O", b, 3.4, y=1.8, solido=False)
    # ── pasillo
    b = "b09"
    mueble("cabinet_chest", 9.5, 5.5, "S", b, 2.6)
    cuadro("cuadro_pasillo", 9.5, 1.55, 5.3, 0.8, 0.6, "z", "cuadro2", b, 2.9)


def placa(nombre, x, y, z, eje, beat, off, n=1, sep=0.09, tipo="toma"):
    """Interruptor o tomacorriente pegado a un muro. eje 'z' = muro que corre en x (placa de frente a z); 'x' = muro que corre en z."""
    for k in range(n):
        d = k * sep
        if eje == "z":
            caja(f"{nombre}_placa_{k}", x + d, y, z, 0.08, 0.12, 0.02, "ceramica", beat, off, solido=False)
            if tipo == "toma":
                caja(f"{nombre}_ranura_{k}", x + d, y + 0.045, z, 0.035, 0.012, 0.024, "marco", beat, off, solido=False)
                caja(f"{nombre}_ranura_b_{k}", x + d, y + 0.065, z, 0.035, 0.012, 0.024, "marco", beat, off, solido=False)
            else:
                caja(f"{nombre}_tecla_{k}", x + d, y + 0.035, z, 0.028, 0.055, 0.03, "marco", beat, off, solido=False)
        else:
            caja(f"{nombre}_placa_{k}", x, y, z + d, 0.02, 0.12, 0.08, "ceramica", beat, off, solido=False)
            if tipo == "toma":
                caja(f"{nombre}_ranura_{k}", x, y + 0.045, z + d, 0.024, 0.012, 0.035, "marco", beat, off, solido=False)
                caja(f"{nombre}_ranura_b_{k}", x, y + 0.065, z + d, 0.024, 0.012, 0.035, "marco", beat, off, solido=False)
            else:
                caja(f"{nombre}_tecla_{k}", x, y + 0.035, z + d, 0.03, 0.055, 0.028, "marco", beat, off, solido=False)


def accesorios():
    """Los detalles pequeños que hacen creíble una casa: interruptores, tomacorrientes, cortineros (en cortinas()), ventilador
    de techo con su botón, accesorios de baño y de cocina. La biblioteca no trae piezas así: se arman con formas simples."""
    # ── sala (b04): ventilador de techo + sus botones junto a la puerta, tomas junto al sillón y a la tele
    b = "b04"
    caja("ventilador_varilla", 4.0, 2.66, 8.6, 0.03, 0.14, 0.03, "acero", b, 5.4, solido=False)
    caja("ventilador_cubo", 4.0, 2.55, 8.6, 0.22, 0.1, 0.22, "madera_oscura", b, 5.4, solido=False)
    caja("ventilador_aspa_x", 4.0, 2.58, 8.6, 1.25, 0.012, 0.17, "madera_clara", b, 5.5, solido=False)
    caja("ventilador_aspa_z", 4.0, 2.58, 8.6, 0.17, 0.012, 1.25, "madera_clara", b, 5.5, solido=False)
    placa("sw_sala", 10.0, 1.2, 10.93, "z", b, 5.6, n=3, tipo="tecla")          # luz, luz indirecta, ventilador
    placa("toma_sala_a", 0.13, 0.32, 8.0, "x", b, 5.8, n=2)
    placa("toma_sala_b", 3.0, 0.32, 5.29, "z", b, 5.8, n=1)
    placa("toma_sala_c", 7.0, 0.32, 10.93, "z", b, 5.9, n=1)
    # ── cocina (b07)
    b = "b07"
    placa("toma_cocina", 14.3, 1.05, 5.29, "z", b, 6.4, n=2, sep=1.9)
    placa("toma_cocina_b", 17.1, 1.05, 5.29, "z", b, 6.5, n=1)
    placa("sw_cocina", 12.7, 1.2, 5.29, "z", b, 6.5, n=2, tipo="tecla")
    mueble("stove_rice_cooker", 17.15, 5.6, "S", b, 6.6, y=0.93, solido=False)
    cil("porta_utensilios", 13.55, 0.93, 5.7, 0.06, 0.16, "acero", b, 6.7)
    for k, dx in enumerate((-0.025, 0.0, 0.025)):
        cil(f"cuchara_{k}", 13.55 + dx, 1.09, 5.7 + dx, 0.008, 0.14 + 0.03 * k, "madera_clara", b, 6.8)
    caja("tabla_cortar", 16.2, 0.93, 5.72, 0.5, 0.025, 0.32, "madera_clara", b, 6.9, solido=False)
    caja("riel_cocina", 17.05, 1.28, 5.3, 0.9, 0.02, 0.02, "acero", b, 7.0, solido=False)
    for k in range(4):
        caja(f"riel_gancho_{k}", 16.75 + 0.2 * k, 1.12, 5.3, 0.015, 0.18, 0.015, "acero", b, 7.1 + 0.05 * k, solido=False)
    caja("especiero", 17.0, 0.98, 5.3, 0.6, 0.03, 0.12, "madera_oscura", b, 7.3, solido=False)
    for k in range(5):
        cil(f"especia_{k}", 16.78 + 0.11 * k, 1.01, 5.3, 0.028, 0.09, ("tela_naranja", "flor_rosa", "follaje", "tela_celeste", "flor_blanca")[k], b, 7.4 + 0.05 * k)
    # ── dormitorio principal (b08): tomas junto a las mesitas, interruptor, ventilador de mesa
    b = "b08"
    placa("toma_cama_a", 0.9, 0.45, 0.13, "z", b, 4.4)
    placa("toma_cama_b", 5.1, 0.45, 0.13, "z", b, 4.5)
    placa("sw_principal", 5.55, 1.2, 5.13, "z", b, 4.6, n=2, tipo="tecla")
    mueble("table_table_fan", 5.0, 3.0, "S", b, 4.8, y=0.0, esc=1.6, solido=False)
    # ── visitas (b09) y estudio (b09b)
    b = "b09"
    placa("toma_visitas", 12.9, 0.45, 0.13, "z", b, 2.5)
    placa("sw_visitas", 11.95, 1.2, 5.13, "z", b, 2.6, n=2, tipo="tecla")
    b = "b09b"
    placa("toma_estudio", 16.3, 0.3, 0.13, "z", b, 2.6, n=2)
    placa("sw_estudio", 16.1, 1.2, 5.13, "z", b, 2.8, tipo="tecla")
    mueble("table_table_fan", 15.1, 0.6, "S", b, 3.0, y=0.72, solido=False)
    # ── baño (b10): portarrollo con papel, toallero, jabonero doble, escobilla, tomacorriente junto al espejo
    b = "b10"
    caja("portarrollo_brazo", 6.1, 0.72, 1.62, 0.06, 0.02, 0.02, "acero", b, 4.0, solido=False)
    caja("portarrollo_base", 6.075, 0.7, 1.62, 0.02, 0.07, 0.07, "acero", b, 4.0, solido=False)
    caja("papel_higienico", 6.12, 0.67, 1.62, 0.11, 0.11, 0.11, "tela_blanca", b, 4.1, solido=False)
    caja("toallero_barra", 8.9, 1.2, 3.4, 0.025, 0.025, 0.7, "acero", b, 4.2, solido=False)
    for k, zk in enumerate((3.08, 3.72)):
        caja(f"toallero_soporte_{k}", 8.93, 1.18, zk, 0.06, 0.04, 0.03, "acero", b, 4.2, solido=False)
    caja("toalla_colgada", 8.88, 0.72, 3.4, 0.035, 0.48, 0.5, "tela_celeste", b, 4.3, solido=False)
    cil("dispenser_jabon", 6.55, 0.93, 3.05, 0.03, 0.13, "tela_celeste", b, 4.4)
    cil("dispenser_cabeza", 6.55, 1.06, 3.05, 0.012, 0.035, "acero", b, 4.4)
    cil("vaso_cepillos", 6.55, 0.93, 3.75, 0.035, 0.1, "vidrio", b, 4.5)
    mueble("toilet_toilet_brush", 6.45, 1.55, "E", b, 4.5, solido=False)
    placa("toma_bano", 6.1, 1.25, 4.0, "x", b, 4.6)
    placa("sw_bano", 6.1, 1.2, 4.65, "x", b, 4.7, n=2, tipo="tecla")
    caja("grifo_ducha", 8.9, 1.05, 0.75, 0.03, 0.04, 0.12, "acero", b, 4.4, solido=False)
    # ── pasillo (b09): termostato y tomas
    b = "b09"
    placa("termostato", 6.5, 1.5, 5.29, "z", b, 2.9, tipo="tecla")
    placa("toma_pasillo", 8.2, 0.3, 5.29, "z", b, 3.0, n=1)


# ───────────────────────────────────────────────────────── cámara (retrato 9:16)
# por beat: [(u, (x, y, z), (mira_x, mira_y, mira_z)), …]; entre beats hay corte seco
CAM: dict[str, list] = {
    "b01": [(0.0, (-7.0, 1.7, 25.0), (9.0, 1.5, 11.0)), (1.0, (4.0, 1.7, 21.0), (9.0, 1.5, 11.0))],
    "b02": [(0.0, (32.0, 11.0, 33.0), (9.0, 1.0, 9.0)), (1.0, (19.0, 4.5, 26.0), (9.0, 1.2, 9.0))],
    "b03": [(0.0, (2.0, 1.7, 21.0), (9.0, 1.7, 11.0)), (1.0, (9.0, 1.6, 15.2), (9.0, 1.5, 11.0))],
    "b04": [(0.0, (9.0, 1.55, 10.4), (3.5, 1.2, 8.0)), (0.5, (7.0, 1.55, 10.4), (2.0, 1.2, 8.0)), (1.0, (5.2, 1.5, 10.2), (0.6, 1.3, 7.6))],
    "b05": [(0.0, (5.9, 1.55, 8.6), (4.4, 1.5, 5.3)), (1.0, (5.4, 1.5, 7.4), (4.4, 1.5, 5.3))],
    "b06": [(0.0, (10.8, 1.5, 10.5), (8.9, 0.9, 8.1)), (0.55, (10.3, 1.5, 10.2), (8.9, 0.9, 8.6)), (1.0, (7.4, 1.5, 10.3), (8.9, 0.9, 8.9))],
    "b07": [(0.0, (11.6, 1.55, 10.4), (14.8, 0.9, 8.3)), (0.45, (12.2, 1.55, 10.5), (14.9, 0.9, 8.3)), (1.0, (14.9, 1.55, 10.4), (15.2, 1.0, 6.0))],
    "b08": [(0.0, (4.7, 1.55, 6.0), (3.0, 1.0, 1.5)), (0.5, (4.7, 1.5, 4.5), (2.6, 0.9, 1.0)), (1.0, (3.9, 1.5, 3.6), (1.0, 1.0, 2.8))],
    "b09": [(0.0, (11.2, 1.55, 6.0), (11.2, 1.0, 1.8)), (1.0, (11.2, 1.5, 4.5), (11.4, 0.9, 1.4))],
    "b09b": [(0.0, (15.4, 1.55, 6.0), (15.7, 1.0, 1.0)), (1.0, (15.4, 1.5, 4.4), (15.9, 0.9, 0.8))],
    "b10": [(0.0, (7.5, 1.55, 6.0), (7.2, 1.1, 1.5)), (1.0, (7.5, 1.5, 4.4), (7.0, 1.1, 1.0))],
    "b11": [(0.0, (9.0, 1.6, 13.0), (9.0, 1.0, 22.0)), (1.0, (9.0, 1.7, 17.5), (7.0, 1.0, 25.0))],
    "b12": [(0.0, (14.0, 1.6, 17.0), (21.5, 0.9, 8.5)), (1.0, (19.2, 1.5, 14.2), (21.5, 0.9, 8.2))],
    "b13": [(0.0, (-12.0, 4.5, 31.0), (9.0, 1.6, 9.0)), (0.5, (9.0, 5.5, 37.0), (9.0, 1.6, 9.0)), (1.0, (30.0, 4.5, 31.0), (9.0, 1.6, 9.0))],
    "b14": [(0.0, (9.0, 6.0, 42.0), (9.0, 1.5, 9.0)), (1.0, (9.0, 3.8, 33.0), (9.0, 1.6, 9.0))],
}


def pos_cam(t: float) -> tuple[tuple, tuple]:
    i = max(k for k in range(len(INI)) if INI[k] <= t + 1e-9)
    i = min(i, len(INI) - 1)
    u = min(1.0, max(0.0, (t - INI[i]) / DUR[i]))
    w = CAM[BEATS[i]["id"].split("_")[0]]
    n = len(w)
    j = 0
    while j < n - 2 and u > w[j + 1][0]:
        j += 1
    u0, p0, m0 = w[j]
    u1, p1, m1 = w[j + 1]
    s = 0 if u1 == u0 else min(1.0, max(0.0, (u - u0) / (u1 - u0)))
    s = s * s * (3 - 2 * s)          # arranque y frenada suaves
    pos = tuple(p0[k] + (p1[k] - p0[k]) * s for k in range(3))
    mira = list(m0[k] + (m1[k] - m0[k]) * s for k in range(3))
    if 0.0 < pos[0] < 18.0 and 0.0 < pos[2] < 11.0 and pos[1] < 2.0:      # dentro de la casa: más hacia el piso
        mira[1] -= 0.6 + 0.12 * max(0.0, (math.hypot(mira[0] - pos[0], mira[2] - pos[2]) - 3.0))
    return pos, tuple(mira)


def validar_camara(margen: float = 0.32) -> list[str]:
    """La cámara nunca entra en un muro ni en un mueble (en planta, a la altura del lente)."""
    err = []
    t = 0.0
    while t < TOTAL:
        (x, y, z), _ = pos_cam(t)
        # los saltos grandes entre beats son cortes: no cuenta el interpolado, sólo las poses reales
        for s in solidos:
            if s["y0"] - 0.1 <= y <= s["y1"] + 0.1 and s["x0"] - margen <= x <= s["x1"] + margen and s["z0"] - margen <= z <= s["z1"] + margen:
                if not (y > ALTO + 0.1):
                    err.append(f"t={t:5.1f}s cámara ({x:.2f},{y:.2f},{z:.2f}) dentro de «{s['n']}»")
        t += 0.25
    vistos, out = set(), []
    for e in err:
        k = e.split("«")[1]
        if k not in vistos:
            vistos.add(k)
            out.append(e)
    return out


def main():
    arquitectura(); sala(); comedor(); cocina(); principal(); cuartos(); bano(); exterior(); cochera(); decorar(); accesorios(); parcela()
    layout = {
        "formato": "estudio.layout_casa/1", "produccion": "p013_mi_hogar_ideal", "total_s": TOTAL, "fps": 30,
        "tiempos": FUENTE_TIEMPOS, "beats": [{"id": b["id"], "ini": INI[i], "dur": DUR[i]} for i, b in enumerate(BEATS)],
        "gancho_hasta_s": INI[BI["b02"]], "items": items, "luces": luces, "marcadores": marcadores,
        "camara_vertical_fov": 64.0, "medidas": {k: v for k, v in MED.items()},
    }
    # la cámara se muestrea acá (misma función que valida): 30 poses por segundo
    cuadros = []
    for f in range(int(TOTAL * 30) + 1):
        p, m = pos_cam(f / 30.0)
        cuadros.append([round(p[0], 4), round(p[1], 4), round(p[2], 4), round(m[0], 4), round(m[1], 4), round(m[2], 4)])
    layout["camara"] = cuadros
    (AQUI / "layout.json").write_text(json.dumps(layout, ensure_ascii=False))
    err = validar_camara()
    print(f"{len(items)} piezas, {len(luces)} luces, {TOTAL} s ({FUENTE_TIEMPOS})")
    print("beats:", ", ".join(f"{b['id'][:3]} {INI[i]:.0f}-{INI[i] + DUR[i]:.0f}" for i, b in enumerate(BEATS)))
    print("cámara:", "OK, no atraviesa nada" if not err else f"{len(err)} problemas")
    for e in err:
        print("  ", e)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
