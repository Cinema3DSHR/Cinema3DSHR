"""Genera escenas/e01/v1/escena.json — DRIFT SUNSET: persecución de drift al atardecer, 60 s exactos.

    /opt/tools/blendenv/bin/python -I producciones/p008_drift_sunset/herramientas/e01.py

Usa la física real (estudio.escenarios.drift_sunset.planificar) para ubicar las cámaras y el sonido en los mismos
tiempos en que pasan las cosas: cuándo el Bisonte XR entra a cada curva derrapando, cuándo alcanza y pasa al Titán,
cuándo aparece el helicóptero. `construir()` (en la escena) hace exactamente lo mismo al renderizar.
"""
import json
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import bpy  # noqa: F401
from mathutils import Vector
from estudio.escenarios import drift_sunset as DS

FPS = 30
DUR = 60.0
PARAM = {**DS.PARAMETROS, "duracion_s": DUR}
pl = DS.planificar(PARAM, FPS)
via = pl["via"]
t_titan = pl["t_pasa_titan"]
t_heli = t_titan + 10.0
# los 4 derrapes del Bisonte (mismos tiempos que los "eventos" de la física en drift_sunset.planificar)
DERRAPES = [(8.6, 1.3), (22.6, 1.5), (43.6, 1.7), (54.0, 1.4)]
print(f"t_pasa_titan={t_titan:.2f} t_heli={t_heli:.2f} s_cruce={pl['s_cruce']:.1f}")


def s_b(t):
    return pl["hor_b_eval"](min(int(DUR * FPS) - 1, max(0, int(round(t * FPS)))))


A = lambda ancla, desp=None: {"ancla": ancla, **({"desp": desp} if desp else {})}
Mv = lambda movil, punto="", desp=None: {"movil": movil, "punto": punto, **({"desp_local": desp} if desp else {})}
tomas = []


def toma(tipo, plano, t0, t1, **k):
    tomas.append({"id": f"t{len(tomas) + 1:02d}_{tipo}", "tipo": tipo, "plano": plano, "inicio_s": round(t0, 3),
                  "duracion_s": round(t1 - t0, 3), "luz_relleno": 0, **k})


def rigida(plano, t0, t1, movil, punto_base, desp, obj_movil, obj_punto="", obj_desp=(0, 0, 0), lente=28):
    toma("estatica", plano, t0, t1, rigido=True, movil=movil, punto_base=punto_base, desp_local=list(desp),
         objetivo=Mv(obj_movil, obj_punto, list(obj_desp)), lente_mm=lente)


def seguir(plano, t0, t1, movil, desp, obj_desp=(0, 2, 0.6), lente=28, retardo=0.5):
    toma("seguimiento", plano, t0, t1, movil=movil, punto_base="", desp_local=list(desp),
         objetivo=Mv(movil, "", list(obj_desp)), lente_mm=lente, retardo=retardo)


# =================================================================================================== 0:00–0:05 presentación
toma("estatica", "el Bisonte XR en la ruta, motor en marcha; el sol bajo detrás", 0.0, 3.2,
     desde=A("inicio", [-9.5, -5.0, 1.4]), objetivo=Mv("bisonte"), lente_mm=32)
rigida("detalle de la rueda delantera: arranca", 3.2, 5.0, "bisonte", "rueda_del_izq", (-0.3, 0.1, 0.05),
       "bisonte", "", (0, 4, 0), lente=50)

# =================================================================================================== 0:05–0:12 entrada al drift
toma("seguimiento", "primeras curvas, baja y afuera (se ven las ruedas)", 5.0, 8.4,
     movil="bisonte", punto_base="rueda_tra_izq", desp_local=[-2.0, -3.0, 0.1], objetivo=Mv("bisonte"), lente_mm=30,
     retardo=0.4)
rigida("CORTE A INTERIOR: Lucía… no, el doble de riesgo, a fondo hacia la primera curva", 8.4, 12.0, "bisonte",
       "interior", (0, 0.3, 0), "bisonte", "cabina", (0, 10, 0.3), lente=16)

# =================================================================================================== 0:12–0:20 persecución
toma("seguimiento", "detrás del Bisonte: aparece la camioneta policial con la baliza encendida", 12.0, 16.0,
     movil="policia", punto_base="", desp_local=[0, -11.0, 2.4], objetivo=Mv("bisonte"), lente_mm=26, retardo=0.5)
toma("grua", "aérea: los dos autos tomando la curva 1, la policía cerrando distancia", 16.0, 20.0,
     desde=A("curva_1", [-24, -14, 14]), hasta=A("curva_1", [10, 16, 20]), objetivo=A("curva_1"), lente_mm=24)

# =================================================================================================== 0:20–0:28 drift intenso
cursor = 20.0
toma("estatica", "CÁMARA FIJA en la curva: el Bisonte entra derrapando, humo de los neumáticos", cursor, cursor + 4.5,
     desde=A("curva_1", [12, -7, 1.3]), objetivo=Mv("bisonte"), lente_mm=35)
cursor += 4.5
seguir("sale del derrape levantando polvo de la banquina; la policía detrás", cursor, 28.0, "bisonte", (0, -8.5, 1.8),
       lente=30)
cursor = 28.0

# =================================================================================================== 0:28–0:40 el Titán en la ruta
toma("estatica", "frente del Titán con el acoplado; el Súper GT amarrado arriba", cursor, cursor + 4.0,
     desde=A("cruce_titan", [-14, 8, 2.0]), objetivo=Mv("titan"), lente_mm=28)
cursor += 4.0
rigida("las ruedas del acoplado pasando", cursor, cursor + 3.0, "acoplado", "", (-2.1, 1.0, -0.6),
       "acoplado", "", (0, 4, 0.3), lente=38)
cursor += 3.0
seguir("el Bisonte adelanta por el carril contrario; la policía, atrás, esquiva al Titán", cursor, cursor + 2.5,
       "bisonte", (3.2, -9.0, 2.0), lente=26)
cursor += 2.5
toma("grua", "aérea general: Bisonte adelante, Titán en el medio, policía atrás", cursor, 40.0,
     desde=A("cruce_titan", [20, -30, 22]), hasta=A("cruce_titan", [60, -5, 16]), objetivo=A("cruce_titan"),
     lente_mm=22)
cursor = 40.0

# =================================================================================================== 0:40–0:50 llega el helicóptero
toma("grua", "el helicóptero policial se acerca sobre los árboles", cursor, cursor + 4.0,
     desde=A("inicio", [0, 260, 150]), hasta=Mv("helicoptero", "", (0, -18, -6)), objetivo=Mv("helicoptero"),
     lente_mm=30)
cursor += 4.0
rigida("desde abajo: el helicóptero pasa sobre la cámara, los rotores girando", cursor, cursor + 3.0,
       "helicoptero", "", (0, 0, -3.0), "helicoptero", "", (0, 0, 0), lente=20)
cursor += 3.0
seguir("plano desde el helicóptero: el Bisonte visto desde arriba, en seguimiento", cursor, cursor + 2.0,
       "helicoptero", (0, -22, -3), lente=24, retardo=0.25)
cursor += 2.0
toma("grua", "la ruta entera con los tres vehículos y el helicóptero arriba", cursor, 50.0,
     desde=A("climax", [-30, 20, 22]), hasta=A("climax", [18, -14, 30]), objetivo=A("climax"), lente_mm=22)
cursor = 50.0

# =================================================================================================== 0:50–0:56 clímax: última curva
toma("estatica", "CÁMARA FIJA, última curva: el derrape más largo, humo y polvo; la policía muy cerca", cursor,
     cursor + 4.5, desde=A("climax", [-13, 9, 1.4]), objetivo=Mv("bisonte"), lente_mm=32)
t_final_curva = cursor
cursor += 4.5
seguir("sale controlado del derrape; el helicóptero sigue desde arriba", cursor, 56.0, "bisonte", (0, -9.5, 2.1),
       lente=28)
cursor = 56.0

# =================================================================================================== 0:56–1:00 cierre
toma("grua", "aérea alejándose: el Bisonte entre los árboles al atardecer, el helicóptero en seguimiento",
     cursor, 60.0, desde=A("final", [-8, -22, 10]), hasta=A("final", [-40, -70, 55]), objetivo=Mv("bisonte"),
     lente_mm=26)

# =================================================================================================== sonido
# =================================================================================================== sonido
dialogo_central = "radio"            # Central: Daniel — locutor de radio/comunicaciones
dialogo_agente = "hombre_joven"       # Unidad/agente: Liam, enérgico
dialogo_piloto = "hombre_grave"       # piloto del helicóptero: Brian, grave

voces = [
    {"rol": dialogo_central, "texto": "Central a todas las unidades, tenemos un vehículo deportivo circulando a "
     "alta velocidad por la ruta rural. Mantengan posición.", "inicio_s": 0.3},
    {"rol": dialogo_agente, "texto": "Unidad en camino. Visual del objetivo.", "inicio_s": 3.6},
    {"rol": dialogo_agente, "texto": "¡Central, lo tenemos a la vista! Está entrando a las curvas a una velocidad "
     "increíble.", "inicio_s": 10.0},
    {"rol": dialogo_central, "texto": "Unidad, mantenga distancia. No se acerque demasiado.", "inicio_s": 14.2},
    {"rol": dialogo_agente, "texto": "¡Este está loco! ¡Está cruzando toda la ruta!", "inicio_s": 17.8},
    {"rol": dialogo_central, "texto": "Solicite apoyo. Repito, solicite apoyo.", "inicio_s": 19.6},
    {"rol": dialogo_agente, "texto": "¡Necesitamos refuerzos inmediatamente!", "inicio_s": 21.6},
    {"rol": dialogo_central, "texto": "Central... el vehículo perdió adherencia... ¡pero recuperó el control!",
     "inicio_s": 24.9},
    {"rol": dialogo_agente, "texto": "¿Cómo demonios sigue controlándolo?", "inicio_s": 27.4},
    {"rol": dialogo_central, "texto": "Central, tenemos tráfico pesado en la ruta. Un camión de gran porte con un "
     "vehículo transportado.", "inicio_s": t_titan - 4.0},
    {"rol": dialogo_agente, "texto": "Copiado. Atención a todas las unidades, refuercen el operativo.",
     "inicio_s": t_titan + 1.0},
    {"rol": dialogo_piloto, "texto": "Central, unidad aérea en posición. Tenemos visual del vehículo desde arriba.",
     "inicio_s": t_heli + 0.5},
    {"rol": dialogo_central, "texto": "Unidad aérea, mantenga seguimiento y comunique sus movimientos.",
     "inicio_s": t_heli + 3.4},
    {"rol": dialogo_piloto, "texto": "Copiado. Este tipo está haciendo drift en plena persecución. ¡No puedo "
     "creerlo!", "inicio_s": t_heli + 6.0},
    {"rol": dialogo_agente, "texto": "¡Está perdiendo tracción! ¡Está perdiendo tracción!", "inicio_s": t_final_curva + 0.6},
    {"rol": dialogo_agente, "texto": "¡No, volvió a controlarlo! ¡Este tipo está completamente loco!",
     "inicio_s": t_final_curva + 2.6},
    {"rol": dialogo_central, "texto": "Todas las unidades, continúen el seguimiento. No perdemos ese vehículo.",
     "inicio_s": 56.6},
]
eventos_sonido = [{"tipo": "voz", "radio": True, "rol": v["rol"], "texto": v["texto"],
                   "inicio_s": round(v["inicio_s"], 2), "volumen": 0.85} for v in voces]

MUSICA = (f"Epic cinematic chase score, {DUR:.0f} seconds, no vocals: a slow tense opening with low strings and a "
          "distant pulse, building through heavy orchestral percussion, driving synth bass and brass stabs as the "
          "chase intensifies, a dramatic drop around {t_titan:.0f}s when the big truck appears, rising tension "
          "through the helicopter's arrival around {t_heli:.0f}s, and an all-out percussive climax at the final "
          "drift around {t_cl:.0f}s with soaring brass, resolving into a triumphant but driving outro that ends on "
          "a hard cinematic hit at the very last second.").format(DUR=DUR, t_titan=t_titan, t_heli=t_heli,
                                                                  t_cl=t_final_curva)
sonido = {"generador": "procedural", "ambiente": None, "eventos": [
    {"tipo": "musica", "prompt": MUSICA, "duracion_s": DUR, "inicio_s": 0.0, "volumen": 0.42},
    {"tipo": "motor", "movil": "bisonte", "clase": "deportivo", "volumen": 0.85},
    {"tipo": "motor", "movil": "policia", "clase": "diesel", "volumen": 0.6},
    {"tipo": "motor", "movil": "titan", "clase": "diesel", "volumen": 0.7},
    {"tipo": "viento_conduccion", "movil": "bisonte", "volumen": 0.14},
    {"tipo": "derrape", "ventanas": [[t0, t0 + d] for t0, d in DERRAPES], "volumen": 0.9},
    {"tipo": "sirena", "movil": "policia", "inicio_s": 11.5, "fin_s": 56.5, "volumen": 0.7},
    {"tipo": "rotor_helicoptero", "movil": "helicoptero", "inicio_s": t_heli, "volumen": 0.55},
] + eventos_sonido}

escena = {
    "tipo": "escena", "id": "p008_drift_sunset-e01", "produccion": "p008_drift_sunset", "numero": 1, "version": 1,
    "titulo": "Drift Sunset",
    "guion": "Ruta rural al atardecer. El Bisonte XR derrapa curva tras curva perseguido por una camioneta policial; "
             "se cruzan con el camión Titán y su acoplado, que lleva un Súper GT amarrado, y lo pasan. Un helicóptero "
             "policial se suma al seguimiento desde el aire. El derrape final, el más largo, y el Bisonte se pierde "
             "entre los árboles con la policía y el helicóptero detrás. Radio policial todo el tiempo, con "
             "interferencias.",
    "duracion_s": DUR,
    "escenario": {"id": "drift_sunset", "generador": "drift_sunset", "parametros": PARAM},
    "eventos": [], "vehiculos": [], "personajes": [], "tomas": tomas,
    "moviles_escenario": ["bisonte", "policia", "titan", "acoplado", "super_gt", "helicoptero"],
    "sonido": sonido,
    "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.1, "muestras": 6},
    "estado": "borrador", "bloqueada": False, "huella_v": 2,
}
salida = RAIZ / "producciones/p008_drift_sunset/escenas/e01/v1/escena.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=1))
print("escrito", salida, len(tomas), "tomas,", len(voces), "líneas de radio,", DUR, "s")
