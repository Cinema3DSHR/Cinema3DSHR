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

# cámaras lentas: (desde, hasta, ×)
LENTAS = [(t_aire - 0.7, t_aire + 0.6, 3.0), (t_c - 1.6, t_c + 1.6, 2.5), (t_sale - 0.35, t_land + 0.55, 4.0)]
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
cortes = [0.0, 3.0, t_aire - 0.7, t_aire + 0.6, t_c - 3.0, t_c - 1.6, t_c + 1.6, t_ret, t_q, t_sale - 1.6, t_sale - 0.35,
          (t_sale + t_land) / 2, t_land + 0.55, t_baja + 0.2, ESCENA_S]
c = [round(x, 3) for x in cortes]
tomas = [
    toma(1, "grua", "aérea: el Titán gris con el auto rampa en el acoplado corre junto al tren; adelante, la escolta", c[0], c[1],
         desde=M("acoplado", desp=[28, -40, 22]), hasta=M("acoplado", desp=[16, 6, 12]), objetivo=M("acoplado"), lente_mm=30),
    toma(2, "seguimiento", "lateral del acoplado: el doble mete reversa y el auto rampa retrocede por la cama", c[1], c[2],
         movil="acoplado", punto_base="", desp_local=[7.5, -6.0, 0.3], objetivo=M("auto_rampa"), lente_mm=32, retardo=1.0),
    toma(3, "seguimiento", "CÁMARA LENTA: desde atrás del acoplado, el auto rampa se baja marcha atrás y cae a la ruta "
         "(la suspensión se estira y golpea, el doble sacudido en la cabina)", c[2], c[3],
         movil="acoplado", punto_base="", desp_local=[-2.4, -17.0, -1.1], objetivo=M("auto_rampa"), lente_mm=28, retardo=1.0),
    toma(4, "seguimiento", "acelera y pasa al camión por el carril de la izquierda", c[3], c[4],
         movil="auto_rampa", punto_base="", desp_local=[4.5, -10.0, 1.0], objetivo=M("auto_rampa"), lente_mm=30, retardo=1.0),
    toma(5, "seguimiento", "sobre el capó: la cuña apunta a la escolta de Halcón Negro", c[4], c[5],
         movil="auto_rampa", punto_base="capo", desp_local=[0, 0.2, 0.18], objetivo=M("auto_rampa", desp=[0, 30, 0.4]),
         rigido=True, lente_mm=24, retardo=1.0),
    toma(6, "seguimiento", "CÁMARA LENTA: la cuña levanta la moto y después al blindado, que salen volando dando vueltas",
         c[5], c[6], movil="auto_rampa", punto_base="", desp_local=[7.0, 6.0, 1.6], objetivo=M("escolta_1"), lente_mm=26,
         retardo=1.0),
    toma(7, "seguimiento", "aérea: trompo de 180° con freno de mano", c[6], c[7],
         movil="auto_rampa", punto_base="", desp_local=[0, -12.0, 10.0], objetivo=M("auto_rampa"), lente_mm=28, retardo=1.0),
    toma(8, "seguimiento", "vuelve a contramano por el carril pegado a las vías y se planta con la cuña hacia atrás",
         c[7], c[8], movil="auto_rampa", punto_base="", desp_local=[-5.0, 9.0, 1.2], objetivo=M("auto_rampa", "cuna"),
         lente_mm=30, retardo=1.0),
    toma(9, "seguimiento", "INTERIOR del Bisonte: Lucía a fondo, Mateo se agarra; adelante, la cuña", c[8], c[9],
         movil="bisonte", punto_base="interior", desp_local=[0, 0, 0], objetivo=M("bisonte", "cabina"), rigido=True,
         lente_mm=15, luz_relleno=60, retardo=1.0),
    toma(10, "seguimiento", "baja junto a la rueda delantera: el Bisonte sube por la cuña", c[9], c[10],
         movil="bisonte", punto_base="", desp_local=[-1.9, 2.6, -0.5], objetivo=M("bisonte", "rueda_del_izq"), rigido=True,
         lente_mm=24, retardo=1.0),
    toma(11, "seguimiento", "CÁMARA LENTA de perfil: despega del techo del auto rampa, vuela por encima de la ruta y del "
         "terraplén hacia el último vagón", c[10], c[11], movil="bisonte", punto_base="", desp_local=[-11.0, 1.5, 0.5],
         objetivo=M("bisonte"), lente_mm=30, retardo=1.0),
    toma(12, "seguimiento", "CÁMARA LENTA, INTERIOR: Lucía y Mateo flotan contra los arneses y se hunden con el golpe",
         c[11], c[12], movil="bisonte", punto_base="interior", desp_local=[0, 0, 0], objetivo=M("bisonte", "cabina"),
         rigido=True, lente_mm=15, luz_relleno=60, retardo=1.0),
    toma(13, "seguimiento", "velocidad normal: desde el vagón 19, el Bisonte derrapa sobre la madera del último vagón y "
         "frena delante de los autos amarrados", c[12], c[13], movil="carro_19", punto_base="", desp_local=[1.0, -5.5, 1.5],
         objetivo=M("bisonte"), lente_mm=30, retardo=1.0),
    toma(14, "seguimiento", "Mateo se baja sobre el tren y camina hacia los autos para robarse uno; Lucía se queda en el "
         "Bisonte", c[13], c[14], movil="carro_20", punto_base="", desp_local=[3.6, 6.5, 1.0], objetivo=M("bisonte"),
         lente_mm=28, retardo=1.0),
]
COMPOSICION_TREN = TF.COMPOSICION
MUSICA = (f"Cinematic action score, {DUR:.0f} seconds, no vocals, hybrid orchestral with heavy drums. Builds from a "
          "tense pulse into a high-speed chase, with three dramatic slow-motion moments where the rhythm drops away into "
          "sustained strings and a deep heartbeat: around {a:.0f}s, around {b:.0f}s and the longest one from {c0:.0f}s to "
          "{c1:.0f}s, each ending in a massive impact hit. Triumphant brass to finish.").format(
    a=peli(t_aire), b=peli(t_c), c0=peli(t_sale), c1=peli(t_land))
sonido = {"generador": "procedural", "ambiente": "tren_llanura", "eventos": [
    {"tipo": "musica", "prompt": MUSICA, "duracion_s": DUR, "inicio_s": 0.0, "volumen": 0.7},
    {"tipo": "efecto", "prompt": "heavy car dropping off the back of a moving flatbed trailer in reverse, suspension "
     "slamming onto asphalt, metal clank", "duracion_s": 2, "inicio_s": peli(t_aire + 0.2), "volumen": 0.9,
     "movil": "auto_rampa"},
    {"tipo": "efecto", "prompt": "armored truck being launched by a steel ramp, violent metal crunch, then tumbling and "
     "crashing on the ground, debris", "duracion_s": 4, "inicio_s": peli(t_c - 0.1), "volumen": 1.0, "movil": "escolta_1"},
    {"tipo": "efecto", "prompt": "car handbrake 180 degree spin, long tire screech on asphalt", "duracion_s": 3,
     "inicio_s": peli(t_v), "volumen": 0.8, "movil": "auto_rampa"},
    {"tipo": "efecto", "prompt": "SUV engine roaring at full throttle, then hitting a steel ramp and launching into the air",
     "duracion_s": 3, "inicio_s": peli(t_sale - 1.6), "volumen": 0.85, "movil": "bisonte"},
    {"tipo": "efecto", "prompt": "heavy SUV landing hard on a wooden train flatcar, suspension slam, wood crack, then tires "
     "skidding to a stop", "duracion_s": 3, "inicio_s": peli(t_land - 0.1), "volumen": 0.95, "movil": "bisonte"},
    {"tipo": "tren", "tipos": COMPOSICION_TREN, "s_inicial": 1000.0, "volumen": 0.85},
    {"tipo": "motor", "movil": "auto_rampa", "clase": "diesel", "volumen": 0.7},
    {"tipo": "motor", "movil": "bisonte", "clase": "diesel", "volumen": 0.7},
    {"tipo": "motor", "movil": "camion", "clase": "diesel", "volumen": 0.8},
]}
escena = {
    "tipo": "escena", "id": "p006_operacion_tren_fantasma-s03", "produccion": "p006_operacion_tren_fantasma", "numero": 3,
    "version": 2, "titulo": "El auto rampa",
    "guion": "EXT. RUTA PEGADA A LAS VÍAS — CONTINUO. El doble baja el auto rampa marcha atrás del acoplado del Titán en "
             "marcha (su único salto), pasa al camión, hace volar a la escolta con la cuña, da un trompo y vuelve a "
             "plantarse de frente: Lucía sube con el Bisonte por la cuña y vuela al último vagón, libre. Mateo se baja "
             "para robarse un auto del tren.",
    "duracion_s": DUR, "mapa_tiempo": MAPA,
    "escenario": {"id": "llanura_tren", "generador": "tren_fantasma", "parametros": PARAM},
    "eventos": [], "vehiculos": [], "personajes": [], "tomas": tomas,
    "moviles_escenario": [f"carro_{i:02d}" for i in range(21)] + ["acoplado", "camion", "auto_rampa", "bisonte", "escolta_1",
                                                                   "moto_1", "auto_camara"],
    "sonido": sonido,
    "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.0},
    "estado": "borrador", "bloqueada": False, "huella_v": 2,
    "historial": [{"desde_version": 1, "motivo": "pedido del dueño: el auto rampa se baja marcha atrás, voltea a la escolta "
                   "y sirve de rampa al Bisonte de Lucía y Mateo, que cae en el último vagón libre"}],
    "fisica": {"t_cae_ruta": t_aire, "t_choque": t_c, "t_vuelta": t_v, "t_plantado": t_q, "t_despega_bisonte": t_sale,
               "t_aterriza": t_land, "altura_max_bisonte": pl["altura_max"], "mateo_baja": t_baja},
}
salida = RAIZ / "producciones/p006_operacion_tren_fantasma/escenas/s03/v2/escena.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=1))
print("escrito", salida, len(tomas), "tomas,", DUR, "s de película,", ESCENA_S, "s de acción; mapa", MAPA)
