"""Arma la receta de la escena e02 de «A la deriva» («Una flor en el vacío») desde guion_e02.py y las voces YA
generadas. El largo lo manda el diálogo real (el dueño: «si los diálogos hacen que se alargue no hay drama»).

Uso:  python producciones/p011_a_la_deriva/herramientas/escenas_e02.py [version]  → escenas/e02/v<k>/escena.json

Puesta (todo sobre el eje x = 0, Aiden camina hacia −Y; escenario nave_deriva_ampliada):
  silla del puesto (0, 0,5) → puerta (y −3,2) → pasillo → botánico (−10,2 … −20,2, bandeja de poda en y −15)
  → comedor (−20,2 … −32,2), mesa de Kate en (0, −30): Kate sentada del lado de la pared, mirando a la puerta;
  Aiden se para del otro lado de la mesa.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).parent))
import guion_e02 as G                                   # noqa: E402
from estudio.audio import elevenlabs as E               # noqa: E402

FPS = 30
A = "mixamo:animaciones/"
SENT, CAM, INT, IDLE, GES, EMO, TRAB = (A + "sentado_manejar/", A + "caminar_correr/", A + "interaccion/",
                                        A + "idle_parado/", A + "gestos/", A + "emociones/", A + "trabajo_acciones/")
CAMINAR = CAM + "Walking_2.fbx"          # un ciclo: 2,94 m en 2,10 s (medido en el retarget de Aiden)
D_CICLO, T_CICLO = 2.94, 63 / 30
V_CAMINAR = D_CICLO / T_CICLO
V_LENTO = 0.8
FRENAR = CAM + "Walk_To_Stop.fbx"        # 1,62 m en 4,90 s
D_FRENAR, T_FRENAR = 1.62, 147 / 30
TOMAR = INT + "Taking_Item.fbx"          # 4,70 s; la mano llega abajo a los 1,33 s
T_MANO_ABAJO = 1.0                       # medido: la mano llega abajo al segundo (0,65 m de alto)
PARADO = IDLE + "Bored.fbx"              # parado, quieto (10,7 s)
MIRAR = GES + "Looking_Around.fbx"
NIEGA = GES + "Shake_Gesture.fbx"


def _rel(p: Path) -> str:
    return str(p.relative_to(RAIZ))


def armar(version: int = 1) -> dict:
    evs = G.eventos_voz()
    rutas = [E.BIBLIOTECA / f"{E.id_biblioteca(e)}.mp3" for e in evs]
    durs = [E.duracion_s(r) for r in rutas]
    L = []
    for (bloque, quien, texto, ea, ek), ev, r, d in zip(G.LINEAS, evs, rutas, durs):
        alin = E.ruta_alineacion(ev)
        L.append({"bloque": bloque, "quien": quien, "texto": texto, "ea": ea, "ek": ek, "dur": d, "ev": ev,
                  "audio": _rel(r), "alineacion": _rel(alin) if alin.exists() else None})

    # ------------------------------------------------------------------ tiempos del diálogo y de la acción
    def en(i, t):
        L[i]["inicio_s"] = round(t, 3)
        return t + L[i]["dur"]

    # MONITOR (Aiden sentado; ve a Kate en la cámara del comedor)
    t = en(0, 1.2)
    t = en(1, t + 0.6)
    t = en(2, t + 0.5)
    t = en(3, t + 0.55)
    t = en(4, t + 0.6)
    t_levanta = t + 0.8                                   # suspira y se levanta
    t_camina = t_levanta + 2.27                            # Sit_To_Stand
    # TRAYECTO: sale caminando por el pasillo (el diálogo va mientras camina)
    t = en(5, t_camina + 0.6)
    t = en(6, t + 0.5)
    t = en(7, t + 0.5)
    t = en(8, t + 0.45)
    t = en(9, t + 0.45)
    t = en(10, t + 0.4)
    # caminata en CICLOS ENTEROS (si un tramo se corta, el siguiente arrancaría desde donde habría terminado el
    # tramo completo): A diagonal hasta pasar la puerta, B derecho por el pasillo, C despacio en el botánico, frena
    import math
    def avanza(p, rumbo_deg, dist):
        r = math.radians(rumbo_deg)
        return (p[0] + math.cos(r) * dist, p[1] + math.sin(r) * dist)
    p0 = (-0.72, 0.35)                                     # al costado de la silla (no la atraviesa)
    pA = avanza(p0, -82, 2 * D_CICLO)
    pB = avanza(pA, -90, 2 * D_CICLO)
    pC = avanza(pB, -95, D_CICLO)
    pP = avanza(pC, -95, D_FRENAR)                         # parado frente a la bandeja
    t_A = t_camina
    t_B = t_A + 2 * T_CICLO
    t_C = t_B + 2 * T_CICLO
    t_puerta = t_A + (p0[1] - (-3.2)) / (pA[1] - p0[1]) * (t_B - t_A) * -1
    t_ini_frena = t_C + T_CICLO / V_LENTO
    t_parado = t_ini_frena + T_FRENAR
    # FLORES
    t = en(11, max(t, t_ini_frena - 1.0))
    t = en(12, t + 0.6)
    t = en(13, t + 0.7)
    t = en(14, t + 0.6)
    t_toma = t + 0.4                                       # toma la flor de la bandeja
    t_flor_mano = t_toma + T_MANO_ABAJO
    t_sale_bot = t_toma + 4.7
    # al comedor: un ciclo hacia la salida del botánico; en el corte al plano general entra al comedor y camina dos
    # ciclos + frena del otro lado de la mesa de Kate (0, −29,32)
    t_corte_comedor = t_sale_bot + T_CICLO
    pD = (-0.26, -29.32 + 2 * D_CICLO + D_FRENAR)
    rumbo_D = math.degrees(math.atan2(-29.32 - pD[1], 0.0 - pD[0]))
    y_corte = pD[1]
    t_ini_frena2 = t_corte_comedor + 2 * T_CICLO
    t_llega = t_ini_frena2 + T_FRENAR
    # MESA
    t = en(15, t_llega - 0.3)
    t = en(16, t + 0.75)
    t = en(17, t + 0.55)
    t_deja = L[17]["inicio_s"] + 0.3                       # deja la flor y la botella
    t_flor_mesa = t_deja + 0.7                             # el gesto se corta cuando la mano llega a la mesa
    t = max(t, t_deja + 1.8) + 1.2                         # sostiene el silencio
    t = en(18, t)
    t = en(19, t + 0.9)
    t = en(20, t + 0.7)
    t_se_va = t + 0.25
    # EVA NO LO DEJA ESCAPAR: camina hacia la puerta y se detiene en el botánico
    t_ini_frena3 = t_se_va + 0.5 + 4 * T_CICLO             # 4 ciclos hacia +Y y frena: queda en y ≈ −15,6
    t = en(21, t_se_va + 2.6)
    t = en(22, t + 0.6)
    t = en(23, t + 0.55)
    t = en(24, t + 0.6)
    t = en(25, t + 0.55)
    t = en(26, t + 0.6)
    t = en(27, t + 0.6)
    t_niega = L[27]["inicio_s"] + L[27]["dur"] - 1.2
    # LO QUE AIDEN NO VIO: Kate a solas con la flor
    t_final = t + 1.2
    t_k_mira = t_final + 0.4
    t_k_toma = t_final + 3.6
    t_k_flor_mano = t_k_toma + 1.5                         # = corte al primer plano (no se ve el alcance)
    t_k_deja = t_k_toma + 6.0
    t_k_escribe = t_k_deja + 1.3
    t_k_listo = t_k_escribe + 4.2
    t_k_duda = t_k_listo + 0.4
    dur = round(t_k_listo + 4.6, 2)
    nf = int(round(dur * FPS))

    # ------------------------------------------------------------------ Aiden
    ac = [{"clip": SENT + "Sitting_Idle.fbx", "inicio_s": 0.0, "pos": [0.0, 0.5, 0.0], "mirando_deg": 90}]
    for i in (1, 3):
        ac.append({"clip": SENT + "Sitting_Talking.fbx", "inicio_s": L[i]["inicio_s"] - 0.2, "pos": [0.0, 0.5, 0.0],
                   "mirando_deg": 90, "mezcla_s": 0.5})
        ac.append({"clip": SENT + "Sitting_Idle.fbx", "inicio_s": L[i]["inicio_s"] + L[i]["dur"] + 0.3,
                   "pos": [0.0, 0.5, 0.0], "mirando_deg": 90, "mezcla_s": 0.6})
    ac.append({"clip": SENT + "Sit_To_Stand.fbx", "inicio_s": t_levanta, "pos": [0.0, 0.5, 0.0], "mirando_deg": 90,
               "mezcla_s": 0.6})
    # corte: ya parado al costado de la silla, camina hacia la puerta (en diagonal) y sigue derecho
    ac.append({"clip": CAMINAR, "inicio_s": t_A, "pos": [p0[0], p0[1], 0.0], "mirando_deg": -82, "repetir": 2,
               "mezcla_s": 0.3})
    ac.append({"clip": CAMINAR, "inicio_s": t_B, "encadenar": True, "mirando_deg": -90, "giro_s": 0.6, "repetir": 2})
    ac.append({"clip": CAMINAR, "inicio_s": t_C, "encadenar": True, "mirando_deg": -95, "velocidad": V_LENTO,
               "giro_s": 0.8, "mezcla_s": 0.6})
    ac.append({"clip": FRENAR, "inicio_s": t_ini_frena, "encadenar": True, "mirando_deg": -95, "mezcla_s": 0.4})
    ac.append({"clip": PARADO, "inicio_s": t_parado, "encadenar": True, "mirando_deg": -95, "mezcla_s": 0.6})
    ac.append({"clip": PARADO, "inicio_s": L[13]["inicio_s"] - 0.5, "encadenar": True, "mirando_deg": 180,
               "giro_s": 1.2, "mezcla_s": 0.8})
    ac.append({"clip": TOMAR, "inicio_s": t_toma, "encadenar": True, "mirando_deg": 180, "mezcla_s": 0.4})
    ac.append({"clip": CAMINAR, "inicio_s": t_sale_bot, "encadenar": True, "mirando_deg": -90, "giro_s": 0.7,
               "mezcla_s": 0.5})
    ac.append({"clip": CAMINAR, "inicio_s": t_corte_comedor, "pos": [pD[0], pD[1], 0.0], "mirando_deg": rumbo_D,
               "repetir": 2, "mezcla_s": 0.1})
    ac.append({"clip": FRENAR, "inicio_s": t_ini_frena2, "encadenar": True, "mirando_deg": rumbo_D, "mezcla_s": 0.4})
    ac.append({"clip": PARADO, "inicio_s": t_llega, "encadenar": True, "mirando_deg": -90, "giro_s": 0.5,
               "mezcla_s": 0.8})
    ac.append({"clip": TOMAR, "inicio_s": t_deja, "encadenar": True, "mirando_deg": -90, "mezcla_s": 0.4})
    ac.append({"clip": PARADO, "inicio_s": t_deja + 0.8, "encadenar": True, "mirando_deg": -90, "mezcla_s": 0.7})
    # se da vuelta (corte a Kate) y vuelve hacia la puerta; frena en el botánico para discutir con EVA
    ac.append({"clip": CAMINAR, "inicio_s": t_se_va + 0.5, "pos": [0.05, -29.0, 0.0], "mirando_deg": 90,
               "repetir": 4, "mezcla_s": 0.2})
    ac.append({"clip": FRENAR, "inicio_s": t_ini_frena3, "encadenar": True, "mirando_deg": 90, "mezcla_s": 0.4})
    ac.append({"clip": PARADO, "inicio_s": t_ini_frena3 + T_FRENAR, "encadenar": True, "mirando_deg": 90,
               "mezcla_s": 0.8})
    ac.append({"clip": NIEGA, "inicio_s": t_niega, "encadenar": True, "mirando_deg": 90, "mezcla_s": 0.4})
    ac.append({"clip": PARADO, "inicio_s": t_niega + 1.75, "encadenar": True, "mirando_deg": 90, "mezcla_s": 0.5})

    exprA = [{"t": 0.0, "expr": "cansado"}]
    for ln in L:
        exprA.append({"t": ln["inicio_s"], "expr": ln["ea"], "transicion": 0.6})
    hablaA = [{"inicio_s": ln["inicio_s"], "audio": ln["audio"], "texto": ln["texto"],
               **({"alineacion": ln["alineacion"]} if ln["alineacion"] else {})} for ln in L if ln["quien"] == "aiden"]
    miradasA = [
        {"t": L[0]["inicio_s"], "hasta": L[4]["inicio_s"] + 2, "u": 0.0, "v": 0.2},              # mira el monitor
        {"t": L[11]["inicio_s"] - 1.0, "hasta": L[11]["inicio_s"] + 2.5, "u": -0.7, "v": 0.1},   # las flores
        {"t": L[11]["inicio_s"] + 2.5, "hasta": L[13]["inicio_s"], "u": 0.6, "v": 0.2},
        {"t": t_flor_mano + 0.3, "hasta": t_flor_mano + 2.6, "u": 0.0, "v": -0.7},               # la flor en su mano
        {"t": L[15]["inicio_s"] - 0.2, "hasta": t_deja, "u": 0.0, "v": -0.35},                   # a Kate
        {"t": t_deja, "hasta": t_flor_mesa + 1.2, "u": 0.0, "v": -0.8},                          # la mesa
        {"t": L[18]["inicio_s"] + 2.5, "hasta": L[18]["inicio_s"] + 5.0, "u": -0.3, "v": -0.6},  # no la mira
        {"t": L[22]["inicio_s"], "hasta": L[22]["inicio_s"] + 1.6, "u": 0.5, "v": -0.2},         # «No empieces»
        {"t": L[24]["inicio_s"], "hasta": L[24]["inicio_s"] + 2.5, "u": 0.0, "v": -0.5},
    ]
    aiden = {"id": "aiden", "modelo": "humano:chico", "alto_m": 1.80, "acciones": ac,
             "cara": {"expresiones": exprA, "habla": hablaA, "miradas": miradasA}}

    # ------------------------------------------------------------------ Kate: sentada a la mesa todo el capítulo
    kp = [0.0, -30.62, 0.0]
    acK = [{"clip": SENT + "Sitting_Idle_3.fbx", "inicio_s": 0.0, "pos": kp, "mirando_deg": 90, "repetir": 40}]
    acK.append({"clip": SENT + "Sit_To_Type.fbx", "inicio_s": t_k_toma, "pos": kp, "mirando_deg": 90, "mezcla_s": 0.5})
    acK.append({"clip": SENT + "Sitting_Rubbing_Arm.fbx", "inicio_s": t_k_toma + 1.1, "pos": kp, "mirando_deg": 90,
                "mezcla_s": 0.7})
    acK.append({"clip": SENT + "Sit_To_Type.fbx", "inicio_s": t_k_deja - 0.9, "pos": kp, "mirando_deg": 90,
                "mezcla_s": 0.6})
    acK.append({"clip": TRAB + "Typing.fbx", "inicio_s": t_k_deja + 0.3, "pos": kp, "mirando_deg": 90, "mezcla_s": 0.5})
    acK.append({"clip": SENT + "Type_To_Sit.fbx", "inicio_s": t_k_duda, "pos": kp, "mirando_deg": 90, "mezcla_s": 0.4})
    acK.append({"clip": SENT + "Sitting_Idle_3.fbx", "inicio_s": t_k_duda + 0.9, "pos": kp, "mirando_deg": 90,
                "mezcla_s": 0.6})
    exprK = [{"t": 0.0, "expr": "triste_sutil"}, {"t": t_llega - 1.0, "expr": "seria", "transicion": 0.8},
             {"t": t_flor_mesa + 0.5, "expr": "seria", "transicion": 0.5},
             {"t": t_final, "expr": "triste_sutil", "transicion": 0.5},
             {"t": t_k_mira + 0.6, "expr": "conmovida", "transicion": 2.2},
             {"t": t_k_flor_mano + 0.8, "expr": "ruborizada", "transicion": 3.0},
             {"t": t_k_flor_mano + 3.6, "expr": "sonrisa_contenida", "transicion": 1.6},
             {"t": t_k_deja - 0.2, "expr": "ruborizada", "transicion": 1.0},
             {"t": t_k_duda, "expr": "conmovida", "transicion": 1.2}]
    hablaK = [{"inicio_s": ln["inicio_s"], "audio": ln["audio"], "texto": ln["texto"],
               **({"alineacion": ln["alineacion"]} if ln["alineacion"] else {})} for ln in L if ln["quien"] == "kate"]
    miradasK = [
        {"t": 0.0, "hasta": t_llega - 2.5, "u": 0.0, "v": -0.6},                                 # baja la mirada
        {"t": t_llega - 2.5, "hasta": t_deja, "u": 0.0, "v": 0.35},                              # levanta la mirada
        {"t": t_deja, "hasta": t_flor_mesa + 2.0, "u": 0.0, "v": -0.75},                         # mira la flor
        {"t": t_flor_mesa + 2.0, "hasta": t_se_va, "u": 0.1, "v": 0.2},
        {"t": t_se_va, "hasta": t_final, "u": 0.0, "v": -0.5},
        {"t": t_final, "hasta": t_k_flor_mano + 3.0, "u": 0.0, "v": -0.75},                      # la flor
        {"t": t_k_flor_mano + 3.0, "hasta": t_k_flor_mano + 5.0, "u": 0.0, "v": 0.3},           # la puerta
        {"t": t_k_deja, "hasta": dur, "u": 0.15, "v": -0.6},                                     # la pantalla
    ]
    kate = {"id": "kate", "modelo": "humano:chica", "alto_m": 1.66, "acciones": acK,
            "cara": {"expresiones": exprK, "habla": hablaK, "miradas": miradasK}}

    # ------------------------------------------------------------------ utilería (la flor y la botella)
    utileria = [
        {"objeto": "flor", "tramos": [{"desde_s": 0.0, "en": "bandeja"},
                                      {"desde_s": t_flor_mano, "en": "mano", "personaje": "aiden", "mano": "R"},
                                      {"desde_s": t_flor_mesa, "en": "mesa"},
                                      {"desde_s": t_k_flor_mano, "en": "mano", "personaje": "kate", "mano": "R"},
                                      {"desde_s": t_k_deja, "en": "mesa2", "rumbo_deg": -15}]},
        {"objeto": "botella", "tramos": [{"desde_s": 0.0, "en": "consola"},
                                         {"desde_s": t_camina, "en": "mano", "personaje": "aiden", "mano": "L"},
                                         {"desde_s": t_flor_mesa, "en": "mesa"}]},
    ]

    # ------------------------------------------------------------------ tomas (9:16)
    def toma(tipo, nombre, t0, t1, **kw):
        return {"id": nombre, "tipo": tipo, "plano": kw.pop("plano", nombre), "inicio_s": round(t0, 3),
                "duracion_s": round(t1 - t0, 3), **kw}
    cab = {"movil": "aiden", "punto": "cabeza"}
    pecho = {"movil": "aiden", "punto": "pecho"}
    c = {}
    c["vig"] = L[1]["inicio_s"] - 0.1
    c["monitor"] = L[3]["inicio_s"] - 0.15
    c["frente"] = L[4]["inicio_s"] - 0.1
    c["vig2"] = L[4]["inicio_s"] + 3.2
    c["levanta"] = t_levanta - 0.5
    c["sale"] = t_camina
    c["pasillo"] = t_camina + 3.0
    c["botanico"] = t_puerta + 7.0 / V_CAMINAR - 0.6
    c["detalle"] = L[11]["inicio_s"] - 0.3
    c["aiden_flores"] = L[12]["inicio_s"] + 1.6
    c["cara_vivo"] = L[13]["inicio_s"] - 0.2
    c["toma"] = t_toma - 0.3
    c["flor_mano"] = t_flor_mano + 0.9
    c["sale_bot"] = t_sale_bot
    c["general"] = t_corte_comedor
    c["kate_ve"] = t_ini_frena2 + 0.8
    c["hola"] = L[15]["inicio_s"] - 0.4
    c["te_traje"] = L[17]["inicio_s"] - 0.2
    c["flor_mesa"] = t_flor_mesa + 0.7
    c["perdon"] = L[18]["inicio_s"] - 0.3
    c["kate_seria"] = L[19]["inicio_s"] - 0.2
    c["dos"] = L[20]["inicio_s"] - 0.3
    c["se_va"] = t_se_va
    c["pasillo2"] = L[21]["inicio_s"] - 0.6
    c["eva_medio"] = L[23]["inicio_s"] - 0.3
    c["calculo"] = L[26]["inicio_s"] - 0.3
    c["final"] = t_final
    c["rubor"] = t_k_flor_mano
    c["mensaje"] = t_k_escribe - 0.4
    c["duda"] = t_k_listo - 0.3
    orden = list(c.keys())
    cortes = [0.0] + [c[k] for k in orden] + [dur]
    T = {k: (cortes[i], cortes[i + 1]) for i, k in enumerate(["vig1"] + orden)}
    tomas = [
        toma("vigilancia", "t01_vigilancia", *T["vig1"], plano="CAM 04 · COMEDOR: Kate sola al fondo del comedor "
             "enorme", desde={"ancla": "vigilancia_comedor"}, objetivo={"ancla": "kate", "desp": [0, 0, -0.3]},
             lente_mm=20, barrido_m=0.6, barridos=0.3,
             montaje={"efecto": "vigilancia", "texto": "CAM 04 · COMEDOR"}),
        toma("dolly", "t02_hombro_monitor", *T["vig"], plano="sobre el hombro de Aiden: el monitor con la cámara del "
             "comedor", desde=[0.42, -0.42, 1.5], hasta=[0.36, -0.12, 1.47], objetivo={"ancla": "pantalla_trayectoria"},
             lente_mm=32),
        toma("dolly", "t03_monitor_detalle", *T["monitor"], plano="el monitor: Kate, un punto solo en el comedor",
             desde=[0.12, 0.95, 1.28], hasta=[0.08, 1.12, 1.3], objetivo={"ancla": "pantalla_trayectoria"}, lente_mm=40),
        toma("estatica", "t04_aiden_frente", *T["frente"], plano="Aiden de frente, la luz de las pantallas en la cara",
             desde=[0.42, 1.6, 1.28], objetivo={"ancla": "puesto", "desp": [0, 0.0, 0.08]}, lente_mm=45, apertura=2.8),
        toma("vigilancia", "t05_vigilancia_cerca", *T["vig2"], plano="CAM 04 más cerca: Kate sola",
             desde=[-3.4, -24.0, 2.6], objetivo={"ancla": "kate", "desp": [0, 0, -0.2]}, lente_mm=38, barrido_m=0.2,
             barridos=0.2, montaje={"efecto": "vigilancia", "texto": "CAM 04 · COMEDOR"}),
        toma("estatica", "t06_se_levanta", *T["levanta"], plano="Aiden se levanta del puesto", desde=[-1.6, 1.3, 1.35],
             objetivo={"ancla": "silla", "desp": [0, 0.25, 0.55]}, lente_mm=28),
        toma("dolly", "t07_sale", *T["sale"], plano="sale del centro de operaciones hacia la cámara (desde el pasillo)",
             desde=[0.15, -4.3, 1.55], hasta=[0.15, -5.4, 1.55], objetivo=cab, lente_mm=30),
        toma("seguimiento", "t08_pasillo", *T["pasillo"], plano="travelling por el pasillo, delante de él",
             movil="aiden", desp_local=[0.25, 1.9, 0.62], objetivo=cab, lente_mm=30, retardo=0.15),
        toma("dolly", "t09_botanico", *T["botanico"], plano="el pasillo botánico se revela: incubadoras y flores a los "
             "dos lados; Aiden entra", desde=[0.25, -19.3, 1.75], hasta=[0.25, -18.4, 1.68],
             objetivo={"ancla": "botanico_entrada", "desp": [0, 0, -0.2]}, lente_mm=24),
        toma("dolly", "t10_flores", *T["detalle"], plano="detalle: flores vivas tras el vidrio con gotas",
             desde=[-0.92, -10.95, 1.66], hasta=[-0.95, -11.7, 1.62], objetivo=[-1.5, -11.45, 1.55], lente_mm=40,
             apertura=2.0),
        toma("estatica", "t11_aiden_flores", *T["aiden_flores"], plano="Aiden entre las flores, de frente",
             desde=[0.2, -17.6, 1.55], objetivo=cab, lente_mm=38, apertura=3.2),
        toma("estatica", "t12_cara_vivo", *T["cara_vivo"], plano="primer plano: «algo tan… vivo»",
             desde=[-0.98, -16.45, 1.58], objetivo=cab, lente_mm=50, apertura=2.4),
        toma("estatica", "t13_toma_flor", *T["toma"], plano="la bandeja de poda: toma la flor con cuidado",
             desde=[-0.62, -14.7, 1.28], objetivo={"ancla": "bandeja"}, lente_mm=40, apertura=2.8),
        toma("estatica", "t14_flor_mano", *T["flor_mano"], plano="la flor en su mano, delicada", movil="aiden",
             desde=[-0.98, -15.15, 1.55], objetivo=[round(pP[0] - 0.17, 3), round(pP[1] + 0.06, 3), 1.4], lente_mm=50,
             apertura=2.0),
        toma("seguimiento", "t15_sale_botanico", *T["sale_bot"], plano="se va hacia el comedor con la flor",
             movil="aiden", desp_local=[-0.3, -1.8, 0.7], objetivo=cab, lente_mm=28, retardo=0.12),
        toma("dolly", "t16_comedor_general", *T["general"], plano="plano general del comedor: mesas vacías, comida "
             "sellada; Kate sola al fondo", desde=[4.9, -20.9, 2.7], hasta=[4.4, -21.6, 2.5],
             objetivo={"ancla": "mesa_kate", "desp": [-0.4, 3.0, 0.2]}, lente_mm=20),
        toma("estatica", "t17_kate_lo_ve", *T["kate_ve"], plano="Kate levanta la mirada", desde=[0.75, -29.2, 1.25],
             objetivo={"ancla": "kate", "desp": [0, 0, 0.12]}, lente_mm=55, apertura=2.4),
        toma("estatica", "t18_hola", *T["hola"], plano="los dos: «Hola.» «Hola.»", desde=[2.35, -29.95, 1.35],
             objetivo={"ancla": "mesa_kate", "desp": [0, 0.05, 0.55]}, lente_mm=26),
        toma("estatica", "t19_te_traje", *T["te_traje"], plano="sobre el hombro de Aiden: deja la flor y la botella",
             desde=[-0.42, -28.75, 1.62], objetivo={"ancla": "mesa_kate", "desp": [0, -0.25, 0.2]}, lente_mm=35),
        toma("estatica", "t20_flor_mesa", *T["flor_mesa"], plano="la flor y la botella sobre la mesa",
             desde=[-0.85, -29.15, 1.08], objetivo={"ancla": "flor_mesa", "desp": [0.05, -0.05, 0.03]}, lente_mm=45,
             apertura=2.0),
        toma("estatica", "t21_perdon", *T["perdon"], plano="sobre el hombro de Kate: Aiden pide perdón",
             desde=[0.32, -30.95, 1.33], objetivo=cab, lente_mm=45, apertura=2.8),
        toma("estatica", "t22_kate_seria", *T["kate_seria"], plano="Kate seria, no contesta",
             desde=[-0.22, -29.55, 1.25], objetivo={"ancla": "kate", "desp": [0, 0, 0.12]}, lente_mm=60, apertura=2.4),
        toma("estatica", "t23_que_estes_bien", *T["dos"], plano="«Que estés bien.»", desde=[2.35, -29.95, 1.35],
             objetivo={"ancla": "mesa_kate", "desp": [0, 0.05, 0.55]}, lente_mm=26),
        toma("estatica", "t24_kate_queda", *T["se_va"], plano="Kate no cambia la expresión mientras él se va",
             desde=[0.6, -29.45, 1.25], objetivo={"ancla": "kate", "desp": [0, 0, 0.1]}, lente_mm=50, apertura=2.4),
        toma("seguimiento", "t25_eva_pasillo", *T["pasillo2"], plano="se aleja del comedor; EVA en los altavoces",
             movil="aiden", desp_local=[0.3, 2.0, 0.62], objetivo=cab, lente_mm=32, retardo=0.12),
        toma("estatica", "t26_eva_medio", *T["eva_medio"], plano="plano medio entre las flores: la mandíbula, la mirada",
             desde=[0.55, -13.6, 1.6], objetivo=cab, lente_mm=40, apertura=2.8),
        toma("dolly", "t27_calculo", *T["calculo"], plano="más cerca: «no todo se resuelve con un cálculo»; EVA ríe",
             desde=[-0.45, -13.75, 1.62], hasta=[-0.38, -14.05, 1.62], objetivo=cab, lente_mm=55, apertura=2.4),
        toma("estatica", "t28_lo_que_no_vio", *T["final"], plano="el comedor: Aiden ya se fue; Kate mira la flor",
             desde=[1.25, -28.4, 1.4], objetivo={"ancla": "mesa_kate", "desp": [0, -0.35, 0.3]}, lente_mm=40),
        toma("dolly", "t29_rubor", *T["rubor"], plano="primer plano: el rubor, la sonrisa que intenta disimular, "
             "mira la puerta", desde=[0.24, -30.12, 0.93], hasta=[0.2, -30.2, 0.93],
             objetivo={"ancla": "kate", "desp": [0, 0, 0.0]}, lente_mm=35, apertura=2.2),
        toma("estatica", "t30_mensaje", *T["mensaje"], plano="sobre el hombro de Kate: «Gracias por la flor»",
             desde=[-0.12, -30.95, 1.32], objetivo={"ancla": "pantalla_kate"}, lente_mm=45, apertura=2.8),
        toma("dolly", "t31_duda", *T["duda"], plano="el cursor sobre ENVIAR; Kate duda. Corte a negro",
             desde=[0.05, -30.55, 1.05], hasta=[0.1, -30.45, 1.0], objetivo={"ancla": "pantalla_kate"}, lente_mm=55,
             apertura=2.4, montaje={"efecto": "fundido_negro", "desde_s": round(dur - T["duda"][0] - 1.4, 2),
                                    "duracion_s": 1.2}),
    ]

    # ------------------------------------------------------------------ sonido
    voces = []
    for ln in L:
        v = {**ln["ev"], "inicio_s": ln["inicio_s"], "volumen": 1.0}
        v.pop("etiquetas", None)
        if ln["quien"] in ("aiden", "kate"):
            v["movil"] = ln["quien"]
        voces.append(v)
    t_bot = c["botanico"]
    sonido = {"generador": "procedural", "ambiente": "nave_interior", "eventos": voces + [
        {"tipo": "musica", "prompt": "Very subtle, warm and fragile ambient score for a quiet sci-fi love story in an "
                                     "isolated spaceship, 60 seconds, no vocals, no drums: soft felt piano and a warm "
                                     "string pad, slowly blooming with wonder in the middle (a hidden garden of "
                                     "flowers), tender and hopeful but sad, lots of space and silence, never competing "
                                     "with dialogue", "duracion_s": 60.0, "inicio_s": round(t_bot - 2.0, 2),
         "volumen": 0.2},
        {"tipo": "musica", "prompt": "Short tender solo felt piano motif, 18 seconds, intimate and warm, a shy blush, "
                                     "a small hopeful melody that ends unresolved on a suspended chord, no other "
                                     "instruments, quiet", "duracion_s": 18.0, "inicio_s": round(t_final + 0.2, 2),
         "volumen": 0.24},
        {"tipo": "efecto", "prompt": "very quiet hydroponic greenhouse ambience inside a spaceship: gentle water "
                                     "circulation, soft air flow, faint drip, no birds", "duracion_s": 20.0,
         "inicio_s": round(t_bot, 2), "volumen": 0.35},
        {"tipo": "efecto", "prompt": "very quiet hydroponic greenhouse ambience inside a spaceship: gentle water "
                                     "circulation, soft air flow, faint drip, no birds", "duracion_s": 20.0,
         "inicio_s": round(c["pasillo2"] + 3.0, 2), "volumen": 0.3},
        {"tipo": "efecto", "prompt": "single soft futuristic message notification ping, subtle, clean", "duracion_s": 1.0,
         "inicio_s": round(t_k_escribe - 0.3, 2), "volumen": 0.25}]}

    escena = {
        "tipo": "escena", "id": "p011_a_la_deriva-e02", "produccion": "p011_a_la_deriva", "numero": 2,
        "version": version, "titulo": "A la deriva · E02 · Una flor en el vacío", "duracion_s": dur,
        "guion": "Documento Maestro v2 (18/11/2026), episodio 2. EVA le muestra a Aiden que Kate está sola en el "
                 "comedor; en el pasillo botánico él toma una flor de la bandeja de poda y se la deja en la mesa. Kate "
                 "no reacciona mientras él está; cuando se va, se ruboriza y escribe «Gracias por la flor», sin "
                 "enviarlo todavía.",
        "escenario": {"id": "nave_deriva_ampliada", "generador": "nave_deriva_ampliada",
                      "parametros": {"semilla": 11, "semilla_flores": 23, "utileria": utileria,
                                     # medidos con la mano de Aiden (Taking_Item): ahí cae la mano
                                     "bandeja": [round(pP[0] - 0.74, 3), round(pP[1] + 0.42, 3), 0.655],
                                     "flor_mesa": [-0.36, -29.8, 0.75], "botella_mesa": [-0.08, -29.72, 0.75],
                                     "flor_mesa2": [-0.2, -30.18, 0.75]}},
        "eventos": [
            {"accion": "eva_habla", "inicio_s": 0.0, "nf": nf, "fps": FPS,
             "lineas": [{"inicio_s": ln["inicio_s"], "audio": ln["audio"]} for ln in L if ln["quien"] == "eva"]},
            {"accion": "plantas_vivas", "inicio_s": 0.0, "nf": nf, "fps": FPS},
            {"accion": "mensaje_kate", "inicio_s": 0.0, "escribir_s": round(t_k_escribe, 3),
             "fin_s": round(t_k_listo, 3), "fps": FPS},
        ],
        "vehiculos": [], "personajes": [aiden, kate], "tomas": tomas, "sonido": sonido,
        "render": {"calidad": "hd540", "fps": FPS, "vertical": True, "exposicion": 0.0},
        "estado": "borrador", "bloqueada": False, "huella_v": 2,
        "posiciones": {"bandeja_parado": [round(pP[0], 2), round(pP[1], 2)], "comedor_desde": [round(pD[0], 2), round(pD[1], 2)]},
        "notas_puesta": {k: round(v, 2) for k, v in {
            "levanta": t_levanta, "camina": t_camina, "puerta": t_puerta, "fin_A": t_B, "fin_B": t_C,
            "frena": t_ini_frena, "parado_bandeja": t_parado, "toma": t_toma,
            "flor_mano": t_flor_mano, "llega_mesa": t_llega, "flor_mesa": t_flor_mesa, "se_va": t_se_va,
            "final": t_final, "kate_flor": t_k_flor_mano, "escribe": t_k_escribe, "listo": t_k_listo}.items()},
    }
    return escena


if __name__ == "__main__":
    v = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    e = armar(v)
    out = RAIZ / "producciones/p011_a_la_deriva/escenas/e02" / f"v{v}" / "escena.json"
    from estudio import proteccion as PR
    PR.exigir_escritura(out)                       # una versión entregada no se sobrescribe: usar otra versión
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(e, ensure_ascii=False, indent=1) + "\n")
    print(out, "duración", e["duracion_s"], "s", "tomas", len(e["tomas"]))
    print(json.dumps(e["notas_puesta"], ensure_ascii=False))
    print("parado frente a la bandeja en", e["posiciones"])
