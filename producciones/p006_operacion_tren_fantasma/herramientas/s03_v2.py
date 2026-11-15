"""Genera escenas/s03/v2/escena.json — SECUENCIA 3: EL AUTO RAMPA (coreografía del dueño, 15/11/2026).

Correr con el Python que trae bpy (usa la física de Dream Rally ya calculada o la calcula):
    /opt/tools/blendenv/bin/python -I producciones/p006_operacion_tren_fantasma/herramientas/s03_v2.py

Los tiempos (cuándo cae a la ruta, cuándo vuelan los enemigos, cuándo salta el Bisonte…) salen de la física, así
que las tomas y las cámaras lentas se ubican con esos números.
"""
import json
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import bpy  # noqa: F401  (mathutils)
from estudio.blender import tren as TR, auto_rampa_s03 as ARS
from estudio.escenarios import tren_fantasma as TF

FPS = 30
PARAM = {"secuencia": 3, "semilla": 3, "duracion_s": 43.0, "angulo_salto_deg": 5.6, "v_bisonte": 23.0}
via = TR.Via([(x, y, 0) for x, y in TF.VIA])
pl = ARS.planificar(via, {**TF.PARAMETROS, **PARAM}, FPS)
t_aire, t_v, t_ret, t_q = pl["t_aire"], pl["t_vuelta"], pl["t_vuelta"] + 4.6, pl["t_quieto"]
t_c = t_v - 2.2                                  # la cuña alcanza al blindado (la moto 1,3 s antes)
t_sale, t_land = pl["sale"], pl["t_land"]
t_baja = round(t_land + 3.2, 2)
ESCENA_S = PARAM["duracion_s"]

from estudio.blender import batalla_s03 as BT
TC1, TC2, TC3 = BT.TC1, BT.TC2, BT.TC3

# cámaras lentas: (desde, hasta, ×)
LENTAS = [(t_aire - 0.7, t_aire + 0.6, 3.0), (TC1 - 0.4, TC1 + 1.6, 2.5), (t_c - 1.6, t_c + 1.6, 2.5),
          (TC2 - 0.2, TC2 + 0.8, 2.0), (t_sale - 0.35, t_land + 0.55, 4.0)]
MAPA = [[0.0, 0.0]]
tp = te = 0.0
for a, b, k in LENTAS:
    tp += a - te
    MAPA.append([round(tp, 3), round(a, 3)])
    tp += (b - a) * k
    MAPA.append([round(tp, 3), round(b, 3)])
    te = b
DUR = round(tp + (ESCENA_S - te), 2)
DUR = round(round(DUR * FPS) / FPS, 4)
MAPA.append([DUR, ESCENA_S])


def peli(t_escena):
    """Tiempo de película de un instante de la escena (inverso del mapa)."""
    for (p0, e0), (p1, e1) in zip(MAPA, MAPA[1:]):
        if e0 <= t_escena <= e1:
            return round(p0 + (p1 - p0) * (t_escena - e0) / max(1e-9, e1 - e0), 3)
    return DUR


def toma(i, tipo, plano, e0, e1, **k):
    t0, t1 = peli(e0), peli(e1)
    return {"id": f"t{i:02d}_{tipo}", "tipo": tipo, "plano": plano, "inicio_s": t0, "duracion_s": round(t1 - t0, 3),
            "luz_relleno": 0, **k}


M = lambda movil, punto="", desp=None: {"movil": movil, "punto": punto, **({"desp_local": desp} if desp else {})}
S = lambda i, plano, e0, e1, movil, desp, obj, lente, **k: toma(i, "seguimiento", plano, e0, e1, movil=movil, punto_base="",
                                                                 desp_local=desp, objetivo=obj, lente_mm=lente, retardo=1.0, **k)
cortes = [0.0, 3.0, t_aire - 0.7, t_aire + 0.6, 7.4, TC1 - 0.4, TC1 + 1.6, t_c - 1.6, t_c + 1.6, 17.6, TC2 - 0.2,
          TC2 + 0.8, 23.8, 25.4, t_q, t_sale - 1.6, t_sale - 0.35, (t_sale + t_land) / 2, t_land + 0.55, t_baja + 0.2,
          ESCENA_S]
c = [round(x, 3) for x in cortes]
assert all(b > a for a, b in zip(c, c[1:])), c
tomas = [
    toma(1, "grua", "aérea: el Titán gris con el auto rampa en el acoplado corre junto al tren; adelante, la escolta", c[0], c[1],
         desde=M("acoplado", desp=[28, -40, 22]), hasta=M("acoplado", desp=[16, 6, 12]), objetivo=M("acoplado"), lente_mm=30),
    S(2, "lateral del acoplado: el doble mete reversa y el auto rampa retrocede por la cama", c[1], c[2],
      "acoplado", [7.5, -6.0, 0.3], M("auto_rampa"), 32),
    S(3, "CÁMARA LENTA: desde atrás del acoplado, el auto rampa se baja marcha atrás y cae a la ruta (la suspensión se "
      "estira y golpea, el doble sacudido en la cabina)", c[2], c[3], "acoplado", [-2.4, -17.0, -1.1], M("auto_rampa"), 28),
    S(4, "acelera y pasa al camión por el carril de la izquierda", c[3], c[4], "auto_rampa", [4.5, -10.0, 1.0],
      M("auto_rampa"), 30),
    S(5, "400 m atrás, pegado a la cola del tren: el Bisonte de Lucía y Mateo con su escolta (Vortex, Veltor, Kodiak); "
      "el Cóndor T6 de Halcón Negro frena para ponérsele a la par", c[4], c[5], "bisonte", [7.0, -16.0, 5.0],
      M("bisonte", desp=[1.5, 6, 0]), 26),
    S(6, "CÁMARA LENTA: el T6 se le tira encima al Bisonte; el Vortex de El Zorro le mete la trompa en la cola (PIT) y "
      "el T6 sale dando vueltas al campo", c[5], c[6], "bisonte", [-4.0, 7.0, 3.2], M("condor_t6"), 24),
    S(7, "sobre el capó del auto rampa: la cuña apunta a la escolta de Halcón Negro", c[6], c[7], "auto_rampa",
      [0, 0.2, 0.18], M("auto_rampa", desp=[0, 30, 0.4]), 24, punto_base_="capo"),
    S(8, "CÁMARA LENTA: la cuña levanta la moto y después al blindado, que salen volando dando vueltas", c[7], c[8],
      "auto_rampa", [7.0, 6.0, 1.6], M("escolta_1"), 26),
    S(9, "aérea: trompo de 180° con freno de mano", c[8], c[9], "auto_rampa", [0, -12.0, 10.0], M("auto_rampa"), 28),
    S(10, "pegada al Veltor: pasa al Bisonte por la banquina, a centímetros, con el terraplén de las vías del otro lado",
      c[9], c[10], "veltor", [-1.7, 2.4, 0.85], M("bisonte"), 20),
    S(11, "CÁMARA LENTA: el Veltor se le pone adelante y le pega de costado al Pampero, que vuelca hacia el campo",
      c[10], c[11], "veltor", [2.5, 13.0, 5.0], M("pampero"), 26),
    S(12, "el auto rampa vuelve a contramano por el carril pegado a las vías", c[11], c[12], "auto_rampa",
      [-5.0, 9.0, 1.2], M("auto_rampa"), 30),
    S(13, "el KL5 de Halcón Negro viene a fondo por la banquina; el Kodiak lo encierra y el KL5 se va en trompo al campo",
      c[12], c[13], "kodiak", [-1.6, -7.0, 2.4], M("kl5"), 26),
    S(14, "el auto rampa se planta de frente, con la cuña mirando al Bisonte", c[13], c[14], "auto_rampa",
      [-5.0, 9.0, 1.2], M("auto_rampa", "cuna"), 30),
    toma(15, "seguimiento", "INTERIOR del Bisonte: Lucía a fondo, Mateo se agarra; adelante, la cuña", c[14], c[15],
         movil="bisonte", punto_base="interior", desp_local=[0, 0, 0], objetivo=M("bisonte", "cabina"), rigido=True,
         lente_mm=17, luz_relleno=60, retardo=1.0),
    S(16, "baja junto a la rueda delantera: el Bisonte sube por la cuña", c[15], c[16], "bisonte", [-1.9, 2.6, -0.5],
      M("bisonte", "rueda_del_izq"), 24, rigido=True),
    S(17, "CÁMARA LENTA de perfil: despega del techo del auto rampa y vuela hacia el último vagón; abajo, el Vortex pasa "
      "a fondo por la banquina", c[16], c[17], "bisonte", [-11.0, 1.5, 0.5], M("bisonte"), 30),
    toma(18, "seguimiento", "CÁMARA LENTA, INTERIOR: Lucía y Mateo flotan contra los arneses y se hunden con el golpe",
         c[17], c[18], movil="bisonte", punto_base="interior", desp_local=[0, 0, 0], objetivo=M("bisonte", "cabina"),
         rigido=True, lente_mm=17, luz_relleno=60, retardo=1.0),
    S(19, "velocidad normal: desde el vagón 19, el Bisonte derrapa sobre la madera del último vagón y frena delante de "
      "los autos amarrados", c[18], c[19], "carro_19", [1.0, -5.5, 1.5], M("bisonte"), 30),
    S(20, "Mateo se baja sobre el tren y camina hacia los autos para robarse uno; Lucía se queda en el Bisonte",
      c[19], c[20], "carro_20", [3.6, 6.5, 1.0], M("bisonte"), 28),
]
for tm in tomas:                         # S() no deja pasar «punto_base» como argumento con nombre repetido
    if tm.pop("punto_base_", None):
        tm["punto_base"] = "capo"
        tm["rigido"] = True
COMPOSICION_TREN = TF.COMPOSICION
MUSICA = (f"Epic cinematic action score, {DUR:.0f} seconds, no vocals, hybrid orchestral with heavy taiko drums, "
          "distorted low brass and driving string ostinatos: a high-speed highway battle between cars. It builds "
          "relentlessly, with five dramatic slow-motion moments where the rhythm drops away into sustained strings and a "
          "deep heartbeat: around {a:.0f}s, {b:.0f}s, {c:.0f}s, {d:.0f}s and the longest one from {e0:.0f}s to {e1:.0f}s, each "
          "ending in a massive impact hit. Triumphant heroic brass to finish.").format(
    a=peli(t_aire), b=peli(TC1), c=peli(t_c), d=peli(TC2), e0=peli(t_sale), e1=peli(t_land))
CHOQUE = ("violent car crash: metal crunch, side impact, then the car rolling over several times on asphalt and gravel, "
          "glass shattering, debris")
sonido = {"generador": "procedural", "ambiente": "tren_llanura", "eventos": [
    {"tipo": "musica", "prompt": MUSICA, "duracion_s": DUR, "inicio_s": 0.0, "volumen": 0.7},
    {"tipo": "efecto", "prompt": "heavy car dropping off the back of a moving flatbed trailer in reverse, suspension "
     "slamming onto asphalt, metal clank", "duracion_s": 2, "inicio_s": peli(t_aire + 0.2), "volumen": 0.9,
     "movil": "auto_rampa"},
    {"tipo": "efecto", "prompt": CHOQUE, "duracion_s": 4, "inicio_s": peli(TC1 - 0.05), "volumen": 1.0, "movil": "condor_t6"},
    {"tipo": "efecto", "prompt": "armored truck being launched by a steel ramp, violent metal crunch, then tumbling and "
     "crashing on the ground, debris", "duracion_s": 4, "inicio_s": peli(t_c - 0.1), "volumen": 1.0, "movil": "escolta_1"},
    {"tipo": "efecto", "prompt": "car handbrake 180 degree spin, long tire screech on asphalt", "duracion_s": 3,
     "inicio_s": peli(t_v), "volumen": 0.8, "movil": "auto_rampa"},
    {"tipo": "efecto", "prompt": CHOQUE, "duracion_s": 4, "inicio_s": peli(TC2 - 0.05), "volumen": 1.0, "movil": "pampero"},
    {"tipo": "efecto", "prompt": "sports car side impact at high speed, then spinning out with long tire screech onto "
     "gravel and grass", "duracion_s": 3, "inicio_s": peli(TC3 - 0.05), "volumen": 0.95, "movil": "kl5"},
    {"tipo": "efecto", "prompt": "SUV engine roaring at full throttle, then hitting a steel ramp and launching into the air",
     "duracion_s": 3, "inicio_s": peli(t_sale - 1.6), "volumen": 0.85, "movil": "bisonte"},
    {"tipo": "efecto", "prompt": "heavy SUV landing hard on a wooden train flatcar, suspension slam, wood crack, then tires "
     "skidding to a stop", "duracion_s": 3, "inicio_s": peli(t_land - 0.1), "volumen": 0.95, "movil": "bisonte"},
    {"tipo": "tren", "tipos": COMPOSICION_TREN, "s_inicial": 1000.0, "volumen": 0.85},
    {"tipo": "motor", "movil": "auto_rampa", "clase": "diesel", "volumen": 0.7},
    {"tipo": "motor", "movil": "bisonte", "clase": "diesel", "volumen": 0.7},
    {"tipo": "motor", "movil": "camion", "clase": "diesel", "volumen": 0.8},
    {"tipo": "motor", "movil": "vortex", "clase": "deportivo", "volumen": 0.75},
    {"tipo": "motor", "movil": "veltor", "clase": "deportivo", "volumen": 0.7},
    {"tipo": "motor", "movil": "kl5", "clase": "deportivo", "volumen": 0.65},
    {"tipo": "motor", "movil": "kodiak", "clase": "diesel", "volumen": 0.55},
    {"tipo": "motor", "movil": "condor_t6", "clase": "diesel", "volumen": 0.55},
    {"tipo": "motor", "movil": "pampero", "clase": "diesel", "volumen": 0.55},
]}
escena = {
    "tipo": "escena", "id": "p006_operacion_tren_fantasma-s03", "produccion": "p006_operacion_tren_fantasma", "numero": 3,
    "version": 2, "titulo": "El auto rampa",
    "guion": "EXT. RUTA PEGADA A LAS VÍAS — CONTINUO. El doble baja el auto rampa marcha atrás del acoplado del Titán en "
             "marcha (su único salto), pasa al camión, hace volar a la escolta con la cuña, da un trompo y vuelve a "
             "plantarse de frente. Atrás, pegada a la cola del tren, la escolta del Bisonte (Vortex de El Zorro, Veltor "
             "y Kodiak) pelea contra la retaguardia de Halcón Negro (Cóndor T6, Pampero y KL5) y los saca de la ruta. "
             "Lucía sube con el Bisonte por la cuña y vuela al último vagón, libre. Mateo se baja para robarse un auto.",
    "duracion_s": DUR, "mapa_tiempo": MAPA,
    "escenario": {"id": "llanura_tren", "generador": "tren_fantasma", "parametros": PARAM},
    "eventos": [], "vehiculos": [], "personajes": [], "tomas": tomas,
    "moviles_escenario": [f"carro_{i:02d}" for i in range(21)] + ["acoplado", "camion", "auto_rampa", "bisonte", "escolta_1",
                                                                   "moto_1", "auto_camara"] + list(BT.REPARTO),
    "sonido": sonido,
    "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.0},
    "estado": "borrador", "bloqueada": False, "huella_v": 2,
    "historial": [{"desde_version": 1, "motivo": "pedido del dueño: el auto rampa se baja marcha atrás, voltea a la escolta "
                   "y sirve de rampa al Bisonte de Lucía y Mateo, que cae en el último vagón libre; batalla de escoltas "
                   "(todoterrenos y superdeportivos) detrás del tren"}],
    "fisica": {"t_cae_ruta": t_aire, "t_choque": t_c, "t_vuelta": t_v, "t_plantado": t_q, "t_despega_bisonte": t_sale,
               "t_aterriza": t_land, "altura_max_bisonte": pl["altura_max"], "mateo_baja": t_baja,
               "golpes_batalla": [TC1, TC2, TC3]},
}
salida = RAIZ / "producciones/p006_operacion_tren_fantasma/escenas/s03/v2/escena.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=1))
print("escrito", salida, len(tomas), "tomas,", DUR, "s de película,", ESCENA_S, "s de acción; mapa", MAPA)
