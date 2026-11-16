"""Genera escenas/e01/v1/escena.json — AL VACÍO: duelo de 60 s (video vertical para redes).

Correr con el Python que trae bpy (usa la física de la pelota del escenario para saber cuándo cae cada uno):
    /opt/tools/blendenv/bin/python -I producciones/p007_al_vacio/herramientas/e01.py

El duelo (primero a 3 caídas): ROJO tira primero y lo tira a AZUL (gancho de los primeros 2 s); AZUL falla arriba del
botón; ROJO la tira afuera; AZUL empata; ROJO pega abajo del tablero; AZUL pasa adelante; ROJO empata 2-2; AZUL roza
el aro en cámara lenta; ROJO la clava con efecto y AZUL cae al vacío en cámara lenta; festejo con fuego y papelitos.
"""
import json
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import bpy  # noqa: F401
from mathutils import Vector
from estudio.escenarios import al_vacio as AV

FPS = 30
AZUL, ROJO = 0, 1
PJ = {AZUL: "azul", ROJO: "rojo"}
MIRA = {AZUL: 0, ROJO: 180}
KICK = {"f_jn_kick_shot_hard_2550": 0.317, "f_jn_kick_shot_hard_2548": 0.342, "f_jn_kick_shot_hard_2552": 0.283,
        "f_jn_kick_shot_hard_2544": 0.292}
DUR_CLIP = {"f_jn_kick_shot_hard_2550": 1.05, "f_jn_kick_shot_hard_2548": 1.167, "f_jn_kick_shot_hard_2552": 1.15,
            "f_jn_kick_shot_hard_2544": 1.067}
# (tirador, patea_s, clip, resultado, destino {dy, dz}, velocidad, efecto)
TURNOS = [
    (ROJO, 0.9, "f_jn_kick_shot_hard_2548", "boton", {"dy": 0.0, "dz": 0.0}, 24.0, (0, 0, 0)),
    (AZUL, 8.0, "f_jn_kick_shot_hard_2550", "tablero", {"dy": 0.15, "dz": 0.82}, 25.0, (0, 0, 0)),
    (ROJO, 11.4, "f_jn_kick_shot_hard_2552", "afuera", {"dy": -2.1, "dz": 0.3}, 26.0, (0, 0, 20)),
    (AZUL, 14.6, "f_jn_kick_shot_hard_2544", "boton", {"dy": 0.05, "dz": -0.05}, 25.0, (0, 0, 0)),
    (ROJO, 21.6, "f_jn_kick_shot_hard_2548", "tablero", {"dy": -0.1, "dz": -0.85}, 24.0, (0, 0, 0)),
    (AZUL, 25.0, "f_jn_kick_shot_hard_2552", "boton", {"dy": -0.1, "dz": 0.1}, 26.0, (0, 0, 0)),
    (ROJO, 31.8, "f_jn_kick_shot_hard_2544", "boton", {"dy": 0.0, "dz": 0.05}, 25.0, (0, 0, 0)),
    (AZUL, 39.0, "f_jn_kick_shot_hard_2550", "tablero", {"dy": 0.8, "dz": 0.05}, 25.5, (0, 0, 0)),
    (ROJO, 42.6, "f_jn_kick_shot_hard_2552", "boton", {"dy": 0.0, "dz": 0.0}, 23.0, (0, 0, -25)),
]
ESCENA_S = 53.0


def t_apreta(s, de, vel, efecto, t_contacto):
    """Cuándo se aprieta el botón rival (física del escenario, pelota en su lugar nominal)."""
    p0 = AV.local(s, AV.HOLE_BACK - 1.15, 0.0, 0.11)
    destino = AV.centro_boton(1 - s) + Vector((0, de["dy"], de["dz"]))
    v0 = AV.resolver(p0, destino, vel, efecto)
    _tray, ev = AV.simular_pelota(p0, v0, efecto, duracion=4.0)
    for e in ev:
        if e["tipo"] == "boton" and e["lado"] == 1 - s:
            return t_contacto + e["t"], ev
    return None, ev


acciones = {AZUL: [], ROJO: []}
turnos_json, caidas, llamaradas = [], [], []
pendiente_subir = None
for n, (s, patea, clip, res, de, vel, ef) in enumerate(TURNOS):
    r = 1 - s
    t_c = patea + KICK[clip]
    t_p, ev = t_apreta(s, de, vel, ef, t_c)
    ok = (t_p is not None) == (res == "boton")
    print(f"turno {n}: {PJ[s]} {res:8s} contacto {t_c:5.2f}  aprieta {t_p}  {'OK' if ok else '¡NO COINCIDE!'}  "
          f"{[(e['tipo'], e['lado'], e['impacto']) for e in ev[:3]]}")
    inicio = patea - 1.7
    tu = {"tirador": s, "personaje": PJ[s], "clip": clip, "patea_s": patea, "resultado": res, "destino": de,
          "velocidad": vel, "efecto": list(ef), "aparece_s": round(inicio, 2),
          "desaparece_s": round(TURNOS[n + 1][1] - 1.7, 2) if n + 1 < len(TURNOS) else ESCENA_S + 1}
    if pendiente_subir is not None:
        lado, t_s = pendiente_subir
        tu["sube_s"], tu["sube_lado"] = t_s, lado
        pendiente_subir = None
    turnos_json.append(tu)
    # el que patea: espera preparado sobre su trampilla y patea
    acciones[s].append({"clip": "s_jn_idle_ready_0150", "inicio_s": round(inicio, 3), "pos": [-0.15, 0.0],
                        "mirando_deg": MIRA[s], "repetir": 2})
    acciones[s].append({"clip": clip, "inicio_s": patea, "pos": [-0.15, 0.0], "mirando_deg": MIRA[s]})
    reac = patea + DUR_CLIP[clip] - 0.12
    if res == "boton":
        acciones[s].append({"clip": "f_jn_celebrate_scorer_0874" if n < len(TURNOS) - 1 else "f_jn_celebrate_scorer_0942",
                            "inicio_s": round(reac, 3), "encadenar": True})
    elif res == "tablero":
        acciones[s].append({"clip": "f_jn_angry_0356", "inicio_s": round(reac, 3), "encadenar": True})
    else:
        acciones[s].append({"clip": "f_jn_dejected_0102", "inicio_s": round(reac, 3), "encadenar": True})
    # el rival espera sobre su trampilla (si no está subiendo en el ascensor)
    sube_r = tu.get("sube_s") if tu.get("sube_lado") == r else None
    if sube_r is None:
        acciones[r].append({"clip": "s_jn_idle_fidget_0148" if n % 2 else "f_jn_idle_0520", "inicio_s": round(inicio, 3),
                            "pos": [0.0, 0.0], "mirando_deg": MIRA[r], "repetir": 3})
    if res == "boton":
        acciones[r].append({"clip": "f_jn_stumble_1262", "inicio_s": round(t_p + 0.02, 3), "encadenar": True})
        acciones[r].append({"clip": "f_jn_fall_0964", "inicio_s": round(t_p + 0.3, 3), "encadenar": True})
        caidas.append((r, t_p))
        llamaradas.append([round(t_p + 0.05, 3), r])
        if n < len(TURNOS) - 1:
            # vuelve en el ascensor 2,7 s después de caer, enojado
            t_s = round(t_p + 2.7, 2)
            pendiente_subir = (r, t_s)
            acciones[r].append({"clip": "f_jn_angry_0366", "inicio_s": t_s, "pos": [0.0, 0.0], "mirando_deg": MIRA[r]})
    elif res == "tablero":
        acciones[r].append({"clip": "s_jn_gesture_0140", "inicio_s": round(t_c + 1.2, 3), "pos": [0.0, 0.0],
                            "mirando_deg": MIRA[r]})
# final: ROJO festeja, AZUL vuelve derrotado en el ascensor
t_final = caidas[-1][1]
acciones[ROJO].append({"clip": "f_jn_celebrate_scorer_1952", "inicio_s": round(t_final + 5.4, 2), "encadenar": True})
t_vuelve = round(t_final + 4.8, 2)
turnos_json[-1]["sube_s"], turnos_json[-1]["sube_lado"] = t_vuelve, AZUL
acciones[AZUL].append({"clip": "f_jn_dejected_0104", "inicio_s": t_vuelve, "pos": [0.0, 0.0], "mirando_deg": MIRA[AZUL]})
for k in (AZUL, ROJO):
    acciones[k].sort(key=lambda a: a["inicio_s"])

# cámara lenta: la primera caída (gancho) y el final
t1 = caidas[0][1]
LENTAS = [(t1 - 0.25, t1 + 1.35, 2.5), (39.0 + 0.32 + 0.6, 39.0 + 0.32 + 1.3, 2.0), (t_final - 0.9, t_final + 1.7, 2.5)]
MAPA = [[0.0, 0.0]]
tp = te = 0.0
for a, b, k in LENTAS:
    tp += a - te
    MAPA.append([round(tp, 3), round(a, 3)])
    tp += (b - a) * k
    MAPA.append([round(tp, 3), round(b, 3)])
    te = b
DUR = round(tp + (ESCENA_S - te), 3)
DUR = round(round(DUR * FPS) / FPS, 4)
MAPA.append([DUR, ESCENA_S])


def peli(t):
    for (p0, e0), (p1, e1) in zip(MAPA, MAPA[1:]):
        if e0 <= t <= e1:
            return round(p0 + (p1 - p0) * (t - e0) / max(1e-9, e1 - e0), 3)
    return DUR


A = lambda ancla, desp=None: {"ancla": ancla, **({"desp": desp} if desp else {})}
Mv = lambda movil, desp=None: {"movil": movil, "punto": "", **({"desp_local": desp} if desp else {})}
tomas = []


def toma(tipo, plano, e0, e1, **k):
    t0, t1_ = peli(e0), peli(e1)
    tomas.append({"id": f"t{len(tomas) + 1:02d}_{tipo}", "tipo": tipo, "plano": plano, "inicio_s": t0,
                  "duracion_s": round(t1_ - t0, 3), "luz_relleno": 0, **k})


def espalda(s, e0, e1, plano, lente=24):
    """Detrás del que patea, por encima del hombro: se ve todo el carril, el vacío y al rival sobre su trampilla."""
    sg = -1 if s == AZUL else 1
    toma("estatica", plano, e0, e1, desde=A(f"trampa_{s}", [sg * 3.6, 1.1, 2.3]),
         objetivo=A(f"boton_{1 - s}", [0, 0, -0.6]), lente_mm=lente)


def victima(r, e0, e1, plano):
    """Contrapicado al rival con su botón detrás (se ve venir la pelota)."""
    sg = -1 if r == AZUL else 1
    toma("estatica", plano, e0, e1, desde=A(f"trampa_{r}", [-sg * 2.6, -1.9, 0.55]),
         objetivo=A(f"trampa_{r}", [0, 0, 1.3]), lente_mm=22)


def abajo(r, e0, e1, plano):
    """Desde el vacío mirando arriba: se abre la trampilla y el jugador cae hacia la cámara."""
    toma("estatica", plano, e0, e1, desde=A(f"trampa_{r}", [0.4, 0.3, -16.0]), objetivo=A(f"trampa_{r}", [0, 0, 1.0]),
         lente_mm=20)


def pelota(n, e0, e1, plano):
    toma("seguimiento", plano, e0, e1, movil=f"pelota_{n}", punto_base="", desp_local=[0.6, -2.4, 0.5],
         objetivo=Mv(f"pelota_{n}", [0, 6, 0]), lente_mm=26, retardo=0.6)


tc = [t[1] + KICK[t[2]] for t in TURNOS]
# turno 0 (gancho): aérea que cae sobre el duelo, patada, la pelota, el botón, la caída desde abajo
toma("grua", "aérea sobre el vacío: el estadio lleno, las dos plataformas y las torres que se pierden en la niebla",
     0.0, tc[0] - 0.25, desde=A("centro", [-2, -24, 16]), hasta=A("trampa_1", [6, -6, 4]), objetivo=A("boton_0"), lente_mm=22)
pelota(0, tc[0] - 0.25, t1 - 0.25, "la pelota de ROJO cruza el vacío hacia el botón de AZUL")
abajo(AZUL, t1 - 0.25, t1 + 1.35, "CÁMARA LENTA desde el vacío: se abre la trampilla y AZUL cae hacia la cámara")
toma("orbita", "el público estalla; las llamaradas en las esquinas de la plataforma azul", t1 + 1.35, 5.6,
     centro=A("plataforma_0", [0, 0, 1]), radio=11, altura=4, angulo_inicial=200, angulo_final=250, lente_mm=20)
victima(AZUL, 5.6, 7.9, "AZUL vuelve en el ascensor por la trampilla, furioso")
# turno 1: AZUL pega arriba del botón
espalda(AZUL, 7.9, tc[1] + 0.25, "AZUL patea")
victima(ROJO, tc[1] + 0.25, 11.0, "la pelota da en el tablero arriba del botón: ROJO respira")
# turno 2: ROJO la tira afuera
espalda(ROJO, 11.0, tc[2] + 0.4, "ROJO patea con efecto")
pelota(2, tc[2] + 0.4, 14.3, "se le abre y se pierde en el vacío")
# turno 3: AZUL empata
espalda(AZUL, 14.3, tc[3] + 0.3, "AZUL, revancha")
victima(ROJO, tc[3] + 0.3, caidas[1][1] + 0.1, "ROJO ve venir la pelota")
abajo(ROJO, caidas[1][1] + 0.1, caidas[1][1] + 2.0, "ROJO cae al vacío")
toma("orbita", "AZUL festeja; el estadio de pie", caidas[1][1] + 2.0, 21.4, centro=A("trampa_0", [0, 0, 1.2]), radio=4.5,
     altura=1.6, angulo_inicial=40, angulo_final=95, lente_mm=28)
# turno 4: ROJO pega abajo
espalda(ROJO, 21.4, tc[4] + 0.3, "ROJO, de nuevo arriba")
victima(AZUL, tc[4] + 0.3, 24.8, "da abajo del tablero")
# turno 5: AZUL pasa adelante
pelota(5, 24.8, caidas[2][1] - 0.05, "AZUL le pega fuerte")
abajo(ROJO, caidas[2][1] - 0.05, caidas[2][1] + 1.6, "ROJO otra vez al vacío")
toma("general", "plano general: 2-1, el público de pie, las balizas rojas", caidas[2][1] + 1.6, 31.6,
     desde=A("centro", [0, -30, 6]), objetivo=A("centro", [0, 0, 0]), lente_mm=18)
# turno 6: ROJO empata 2-2
espalda(ROJO, 31.6, tc[6] + 0.3, "ROJO no se rinde")
victima(AZUL, tc[6] + 0.3, caidas[3][1] + 0.1, "AZUL mira el botón")
abajo(AZUL, caidas[3][1] + 0.1, caidas[3][1] + 1.8, "2-2: AZUL cae")
toma("estatica", "el público, tenso: la próxima define", caidas[3][1] + 1.8, 38.8, desde=A("centro", [0, 6, 1.2]),
     objetivo=A("centro", [0, 30, 3]), lente_mm=35)
# turno 7: AZUL roza el aro (cámara lenta)
espalda(AZUL, 38.8, tc[7] + 0.55, "AZUL, punto de partido")
victima(ROJO, tc[7] + 0.55, 41.0, "CÁMARA LENTA: pega al lado del aro, por centímetros")
# turno 8: ROJO la clava con efecto; AZUL cae en cámara lenta
espalda(ROJO, 41.0, tc[8] + 0.06, "ROJO, punto de partido")
pelota(8, tc[8] + 0.06, t_final - 0.35, "CÁMARA LENTA: la pelota se curva hacia el botón")
victima(AZUL, t_final - 0.35, t_final + 0.35, "CÁMARA LENTA: el botón se pone verde")
abajo(AZUL, t_final + 0.35, t_final + 1.7, "CÁMARA LENTA: AZUL cae al vacío, el fuego sube por las esquinas")
toma("orbita", "ROJO campeón: festejo, fuego y papelitos", t_final + 1.7, ESCENA_S - 2.6,
     centro=A("trampa_1", [0, 0, 1.2]), radio=5.0, altura=1.8, angulo_inicial=-30, angulo_final=60, lente_mm=26)
toma("grua", "final: la cámara sube sobre el estadio; abajo, AZUL vuelve derrotado en el ascensor", ESCENA_S - 2.6,
     ESCENA_S, desde=A("centro", [0, -9, 3]), hasta=A("centro", [0, -20, 18]), objetivo=A("centro"), lente_mm=22)

UNIF = {
    "azul": {"camiseta": [0.03, 0.22, 0.95], "short": [0.95, 0.95, 0.97], "medias": [0.03, 0.22, 0.95],
             "botines": [1.0, 0.45, 0.02], "piel": [0.86, 0.63, 0.5], "pelo": [0.78, 0.6, 0.28]},
    "rojo": {"camiseta": [0.9, 0.05, 0.05], "short": [0.03, 0.03, 0.035], "medias": [0.9, 0.05, 0.05],
             "botines": [1.0, 0.9, 0.05], "piel": [0.34, 0.2, 0.12], "pelo": [0.02, 0.02, 0.02]},
}
personajes = [{"id": PJ[k], "modelo": "futbol:jugador", "uniforme": UNIF[PJ[k]], "sobre": f"soporte_{k}",
               "acciones": acciones[k]} for k in (AZUL, ROJO)]
animo = [[0, "aplauso"], [tc[0] - 0.5, "tension"]]
for lado, t_p in caidas:
    animo += [[t_p, "festejo"], [t_p + 2.4, "aplauso"]]
animo[-1] = [t_final + 2.4, "salta"]
for k, (s, patea, *_r) in enumerate(TURNOS[1:], 1):
    animo.append([patea - 0.3, "tension"])
animo.sort(key=lambda a: a[0])
MUSICA = (f"High energy sports arena track, {DUR:.0f} seconds, no vocals: hard-hitting trap drums, deep 808 bass and an "
          "epic stadium brass hook, built for a viral sports duel video; constant forward drive with short breaks, "
          "a dramatic tension build in the last third and a huge drop at the winning moment around "
          f"{peli(t_final):.0f}s, then a triumphant outro.")
sonido = {"generador": "procedural", "ambiente": "arcade_duelo", "publico": 0.32, "eventos": [
    {"tipo": "musica", "prompt": MUSICA, "duracion_s": DUR, "inicio_s": 0.0, "volumen": 0.55},
    {"tipo": "efecto", "prompt": "whistle blow then a huge stadium crowd roaring", "duracion_s": 3, "inicio_s": 0.0,
     "volumen": 0.7},
] + [{"tipo": "efecto", "prompt": "massive arena crowd erupting in wild cheers and screams, thousands of fans",
      "duracion_s": 4, "inicio_s": peli(t_p + 0.1), "volumen": 0.9} for _l, t_p in caidas]
  + [{"tipo": "efecto", "prompt": "man screaming as he falls down into a deep abyss, voice fading away with echo",
      "duracion_s": 3, "inicio_s": peli(t_p + 0.15), "volumen": 0.8, "movil": PJ[l]} for l, t_p in caidas]}
escena = {
    "tipo": "escena", "id": "p007_al_vacio-e01", "produccion": "p007_al_vacio", "numero": 1, "version": 1,
    "titulo": "Al vacío — el duelo",
    "guion": "Estadio de noche. Dos plataformas sobre el vacío. AZUL contra ROJO, primero a tres: quien le pega fuerte "
             "al botón del rival le abre el piso. ROJO golpea primero; AZUL empata; se pasan; 2-2; AZUL roza el aro y "
             "ROJO la clava con efecto: AZUL cae al vacío en cámara lenta. Fuego, papelitos y el estadio de pie.",
    "duracion_s": DUR, "mapa_tiempo": MAPA,
    "escenario": {"id": "al_vacio", "generador": "al_vacio",
                  "parametros": {"semilla": 7, "duracion_s": ESCENA_S, "animo": animo, "llamaradas": llamaradas,
                                 "papelitos_s": round(t_final + 1.0, 2)}},
    "duelo": {"turnos": turnos_json, "primero_a": 3},
    "eventos": [], "vehiculos": [], "personajes": personajes, "tomas": tomas,
    "moviles_escenario": [f"pelota_{n}" for n in range(len(TURNOS))],
    "sonido": sonido,
    "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.0, "vertical": True},
    "estado": "borrador", "bloqueada": False, "huella_v": 2,
}
salida = RAIZ / "producciones/p007_al_vacio/escenas/e01/v1/escena.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=1))
print("escrito", salida, len(tomas), "tomas,", DUR, "s de película,", ESCENA_S, "s de escena; caídas", caidas)
