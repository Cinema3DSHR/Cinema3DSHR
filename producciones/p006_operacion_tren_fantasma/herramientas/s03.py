"""Genera escenas/s03/v1/escena.json — SECUENCIA 3: EL SALTO.

El auto rampa se baja del acoplado del camión en marcha y vuela hasta la plataforma 9 (su ÚNICO salto en la película).
Física real de Dream Rally en dos marcos móviles (estudio/blender/salto_tren.py) y la cabina del juego con Lucía y
Mateo. CÁMARA LENTA: la acción de la escena entre 17,0 y 19,2 s (despegue, vuelo y aterrizaje) se ve en 8,8 s de
película (×4); la escena se evalúa en sub-cuadros (`mapa_tiempo`).
"""
import json
from pathlib import Path

FPS = 30
ESCENA_S = 31.0                       # duración de la acción (tiempo real de la escena)
LENTA = (17.0, 19.2, 4.0)             # tramo de la escena en cámara lenta y cuánto se estira
fin_lenta = LENTA[0] + (LENTA[1] - LENTA[0]) * LENTA[2]
DUR = round(fin_lenta + (ESCENA_S - LENTA[1]), 3)          # duración en la película
MAPA = [[0.0, 0.0], [LENTA[0], LENTA[0]], [fin_lenta, LENTA[1]], [DUR, ESCENA_S]]


def toma(i, tipo, plano, t0, t1, **k):
    return {"id": f"t{i:02d}_{tipo}", "tipo": tipo, "plano": plano, "inicio_s": t0, "duracion_s": round(t1 - t0, 3),
            "luz_relleno": 0, **k}


M = lambda movil, punto="", desp=None: {"movil": movil, "punto": punto, **({"desp_local": desp} if desp else {})}
L0, L1 = LENTA[0], fin_lenta
MEDIO = round(L0 + (L1 - L0) * 0.5, 3)
tomas = [
    toma(1, "grua", "aérea: el tren alcanza al camión que corre pegado a las vías; sobre el acoplado, el auto rampa", 0, 7,
         desde=M("acoplado", desp=[32, -45, 26]), hasta=M("acoplado", desp=[20, 12, 13]), objetivo=M("acoplado"), lente_mm=30),
    toma(2, "seguimiento", "lateral del camión: el auto rampa amarrado, la plataforma 9 se pone a la par", 7, 11,
         movil="acoplado", punto_base="", desp_local=[8.5, 3.0, 0.2], objetivo=M("auto_rampa"), lente_mm=35, retardo=0.6),
    toma(3, "seguimiento", "INTERIOR: Lucía al volante, Mateo agarrado de la jaula («Agarrate.»)", 11, 14.5,
         movil="auto_rampa", punto_base="interior", desp_local=[0, 0, 0], objetivo=M("auto_rampa", "cabina"), rigido=True, lente_mm=14, luz_relleno=60,
         retardo=1.0),
    toma(4, "seguimiento", "cámara sobre el capó: acelera a fondo por la cama del acoplado hacia la rampa", 14.5, 16.2,
         movil="auto_rampa", punto_base="capo", desp_local=[0, 0.2, 0.18], objetivo=M("auto_rampa", desp=[0, 30, 0.6]), rigido=True,
         lente_mm=26, retardo=1.0),
    toma(5, "seguimiento", "baja junto a la rueda trasera: patina y empuja", 16.2, L0,
         movil="auto_rampa", punto_base="", desp_local=[-1.7, -2.4, -0.62], objetivo=M("auto_rampa", "rueda_tra_izq"), rigido=True,
         lente_mm=28, retardo=1.0),
    toma(6, "seguimiento", "CÁMARA LENTA, de perfil a la altura del vuelo: el auto deja la rampa — la suspensión se "
         "estira, las ruedas siguen girando en el aire — y cruza hacia el tren", L0, MEDIO,
         movil="acoplado", punto_base="", desp_local=[7.0, 11.0, 1.3], objetivo=M("auto_rampa"), lente_mm=30, retardo=1.0),
    toma(7, "seguimiento", "CÁMARA LENTA, INTERIOR: los cuerpos se despegan de las butacas contra los arneses y se "
         "hunden con el aterrizaje", MEDIO, L1,
         movil="auto_rampa", punto_base="interior", desp_local=[0, 0, 0], objetivo=M("auto_rampa", "cabina"), rigido=True, lente_mm=14, luz_relleno=60,
         retardo=1.0),
    toma(8, "seguimiento", "velocidad normal: desde la plataforma 10, el auto derrapa sobre la madera y frena a medio "
         "metro del deportivo", L1, round(L1 + 4.8, 3),
         movil="carro_10", punto_base="", desp_local=[1.0, -5.5, 1.6], objetivo=M("auto_rampa"), lente_mm=30, retardo=1.0),
    toma(9, "grua", "aérea: la cámara se aleja; el camión queda atrás, el tren sigue con el auto rampa en la plataforma 9",
         round(L1 + 4.8, 3), DUR,
         desde=M("carro_09", desp=[-18, -22, 7]), hasta=M("carro_09", desp=[-55, -95, 48]), objetivo=M("carro_09"), lente_mm=28),
]
COMPOSICION_TREN = ["loco", "plano", "plano", "cerrado", "plano", "plano", "plano", "cerrado", "plano", "plano", "plano",
                    "cerrado", "plano", "cerrado", "cerrado", "plano", "plano", "plano", "plano", "plano", "plano"]
MUSICA = (f"Cinematic action score, {DUR:.0f} seconds, no vocals. 0-17s: tense driving hybrid percussion and pulsing low "
          "strings, building anticipation as a car prepares to jump onto a moving train. 17-26s: time slows down: the "
          "rhythm drops out, a high sustained string chord and a soft choir float over slow deep heartbeat thuds and a "
          "reversed swell. 26s: a massive orchestral impact hit. 26-37s: triumphant heroic brass and taiko restate the "
          "theme, then settle.")
sonido = {"generador": "procedural", "ambiente": "tren_llanura", "eventos": [
    {"tipo": "musica", "prompt": MUSICA, "duracion_s": DUR, "inicio_s": 0.0, "volumen": 0.75},
    {"tipo": "efecto", "prompt": "powerful sports car engine roaring to full throttle, tires spinning on steel, rising revs",
     "duracion_s": 3, "inicio_s": 14.6, "volumen": 0.8, "movil": "auto_rampa"},
    {"tipo": "efecto", "prompt": "heavy car landing hard on a wooden train flatcar: deep suspension slam, metal crunch, "
     "wood thud", "duracion_s": 2, "inicio_s": round(L1 - 0.25, 3), "volumen": 0.9, "movil": "auto_rampa"},
    {"tipo": "efecto", "prompt": "car tires skidding and screeching on wooden planks, braking hard",
     "duracion_s": 3, "inicio_s": round(L1 + 0.2, 3), "volumen": 0.7, "movil": "auto_rampa"},
    {"tipo": "tren", "tipos": COMPOSICION_TREN, "s_inicial": 1040.0, "volumen": 0.9},
    {"tipo": "motor", "movil": "auto_rampa", "clase": "diesel", "volumen": 0.7},
    {"tipo": "motor", "movil": "camion", "clase": "diesel", "volumen": 0.8},
]}
escena = {
    "tipo": "escena", "id": "p006_operacion_tren_fantasma-s03", "produccion": "p006_operacion_tren_fantasma", "numero": 3,
    "version": 1, "titulo": "El salto",
    "guion": "EXT. RUTA PEGADA A LAS VÍAS — CONTINUO. El camión corre junto al tren. Lucía acelera sobre el acoplado en "
             "marcha y el auto rampa se baja de un salto —el único de toda la película— hasta la plataforma 9. "
             "Cámara lenta en el despegue, el vuelo y el aterrizaje.",
    "duracion_s": DUR, "mapa_tiempo": MAPA,
    "escenario": {"id": "llanura_tren", "generador": "tren_fantasma",
                  "parametros": {"secuencia": 3, "semilla": 3, "duracion_s": ESCENA_S, "s_cabeza_inicial": 1040.0,
                                 "t_acelera": 15.0}},
    "eventos": [], "vehiculos": [], "personajes": [], "tomas": tomas,
    "moviles_escenario": [f"carro_{i:02d}" for i in range(21)] + ["acoplado", "camion", "auto_rampa", "auto_camara"],
    "sonido": sonido,
    "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.0},
    "estado": "borrador", "bloqueada": False, "huella_v": 2,
}
salida = Path(__file__).resolve().parents[1] / "escenas/s03/v1/escena.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=1))
print("escrito", salida, len(tomas), "tomas", DUR, "s de película,", ESCENA_S, "s de acción")
