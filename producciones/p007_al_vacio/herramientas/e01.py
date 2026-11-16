"""Genera la escena de AL VACÍO: Messi contra Cristiano Ronaldo, 60 s verticales, sin HUD.

    /opt/tools/blendenv/bin/python -I producciones/p007_al_vacio/herramientas/e01.py            # e01: gana Cristiano
    /opt/tools/blendenv/bin/python -I producciones/p007_al_vacio/herramientas/e01.py messi      # e02: gana Messi

El duelo (primero a 3, se alternan; patea primero el que gana al final): el primero voltea al otro en el segundo 2 (gancho);
el rival pega en el tablero; el primero la tira afuera; el rival empata; el primero pasa adelante; el rival empata 2-2; el
primero la clava y el otro cae al vacío en cámara lenta. Festejo: Cristiano el «Siu» (salto, media vuelta en el aire,
cae con los brazos abiertos); Messi los dos índices al cielo. Remates: Cristiano de empeine y muy fuerte; Messi con
rosca, colocado (interior del zurdo). Caídas al vacío de Mixamo («Losing Balance» + «Falling In The Air»).
"""
import json
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import bpy  # noqa: F401
from mathutils import Vector
from estudio.escenarios import al_vacio as AV

GANA = (sys.argv[1] if len(sys.argv) > 1 else "cristiano").lower()
from estudio import config as CF
RAICES = json.loads(CF.resolver("mixamo:futbol_free_kick_swipe/raices_clips.json").read_text())
ESCENA_ID, NUM = ("e01", 1) if GANA == "cristiano" else ("e02", 2)
FPS = 30
MESSI, CR7 = 0, 1                          # Messi en la plataforma celeste (x < 0), Cristiano en la roja (x > 0)
PJ = {MESSI: "messi", CR7: "cristiano"}
MODELO = {MESSI: "pelicula:messi", CR7: "pelicula:cristiano"}
MIRA = {MESSI: 0, CR7: 180}
ADELANTE = {MESSI: 1.0, CR7: -1.0}         # hacia el rival, en X
PIE = {MESSI: -1, CR7: 1}                  # Messi zurdo, Cristiano diestro (el juego: toque_pie izq / der)
AV.PIE.update(PIE)
FESTEJOS = ["f_jn_celebrate_scorer_0874", "f_jn_celebrate_scorer_1950", "f_jn_celebrate_1954", "f_jn_celebrate_0092"]


def raiz(clip, t):
    """Raíz del clip del juego a t s (root_path a 30 fps: adelante, derecha)."""
    rp = RAICES[clip.split(":")[-1]]["root_path"]
    f = min(max(t * 30.0, 0.0), len(rp) - 1.001)
    i = int(f)
    a = f - i
    return Vector((rp[i][0] + (rp[i + 1][0] - rp[i][0]) * a, rp[i][1] + (rp[i + 1][1] - rp[i][1]) * a, 0))


def encuadre(s, rem):
    """Como ShotCatalog.frame_for_shot + start_time_near del juego: el clip mira al botón rival y se ubica para que su
    raíz en el contacto deje el pie en la pelota; entra en el punto de la carrera más cercano a donde espera."""
    a = Vector((ADELANTE[s], 0, 0))
    der = Vector((a.y, -a.x, 0))
    mundo = lambda tt: O + a * raiz(rem["clip"], tt).x + der * raiz(rem["clip"], tt).y
    rc = raiz(rem["clip"], rem["tc"])
    O = AV.lugar_pelota(s) - a * rc.x - der * rc.y
    O.z = 0
    espera = AV.trampilla(s)
    t0 = min((k / 30.0 for k in range(int((rem["tc"] - 0.7) * 30))), key=lambda tt: (mundo(tt) - espera).length)
    local = O - espera
    return [round(local.x, 3), round(local.y, 3)], round(t0, 3), round((mundo(t0) - espera).length, 2)
F = "futbol:"
MX = "mixamo:animaciones/"
# remates del juego (tc = contacto, carrera = metros de carrera hasta el contacto, dur = largo del clip)
REMATE = {
    CR7: [{"clip": F + "f_jn_setpiece_shot_0704", "tc": 2.383, "carrera": 5.03, "dur": 3.35, "vel": 29.0, "efecto": (0, 0, 0)},
          {"clip": F + "f_jn_setpiece_shot_3352", "tc": 1.783, "carrera": 4.92, "dur": 2.667, "vel": 28.0, "efecto": (0, 0, 0)},
          {"clip": F + "f_jn_setpiece_shot_3354", "tc": 1.85, "carrera": 4.79, "dur": 2.883, "vel": 28.0, "efecto": (0, 0, 0)}],
    MESSI: [{"clip": F + "f_jn_setpiece_shot_2258", "tc": 2.092, "carrera": 5.53, "dur": 3.133, "vel": 23.0, "efecto": (0, 0, 28)},
            {"clip": F + "f_jn_setpiece_shot_2260", "tc": 1.592, "carrera": 5.08, "dur": 2.35, "vel": 23.5, "efecto": (0, 0, -24)}],
}
# reacciones del juego (catálogo: nombres originales del dueño, animaciones_futbol5_nombres_originales)
TAUNTS = ["s_jn_nis_misc_2864", "s_jn_nis_misc_2860", "s_jn_nis_misc_2866", "s_jn_nis_misc_2858", "s_jn_nis_misc_2862"]
ENOJOS = ["f_jn_angry_0366", "s_jn_angry_0372", "f_jn_angry_0368", "f_jn_angry_0356"]
# tropezón del juego (pierde el piso) y la caída en el aire de Mixamo («Falling In The Air»); el «Losing Balance» de
# Mixamo arranca 0,8 m más alto (está parado en una cornisa) y el jugador flotaba sobre el hueco
CAIDA = [{"clip": F + "f_jn_stumble_1262", "dt": 0.02},
         {"clip": MX + "caidas_muertes/Falling.fbx", "dt": 0.4, "repetir": 3}]
ganador = CR7 if GANA == "cristiano" else MESSI
perdedor = 1 - ganador
# (tirador, resultado, destino) — se alternan empezando por el ganador; 7 turnos, 3-2
PLAN = [(ganador, "boton", {"dy": 0.0, "dz": 0.0}),
        (perdedor, "tablero", {"dy": 0.1, "dz": 0.85}),
        (ganador, "afuera", {"dy": -2.2, "dz": 0.4}),
        (perdedor, "boton", {"dy": 0.05, "dz": -0.05}),
        (ganador, "boton", {"dy": -0.08, "dz": 0.08}),
        (perdedor, "boton", {"dy": 0.0, "dz": 0.05}),
        (ganador, "boton", {"dy": 0.0, "dz": 0.0})]


def t_apreta(s, de, vel, efecto, t_contacto):
    p0 = AV.lugar_pelota(s)
    destino = AV.centro_boton(1 - s) + Vector((0, de["dy"], de["dz"]))
    v0 = AV.resolver(p0, destino, vel, efecto)
    _tray, ev = AV.simular_pelota(p0, v0, efecto, duracion=4.0)
    for e in ev:
        if e["tipo"] == "boton" and e["lado"] == 1 - s:
            return t_contacto + e["t"], ev
    return None, ev


# ---------------------------------------------------------------- el banco de animaciones del juego (SpClips / SpReactions)
CAT = json.loads((RAIZ / "catalogo" / "futbol.json").read_text())["clips"]


def _meta(c):
    return RAICES.get(c, {}).get("meta", {})


def _recorrido(c, hasta=None):
    rp = RAICES.get(c, {}).get("root_path") or [[0, 0]]
    n = len(rp) if hasta is None else min(len(rp), int(hasta * 30) + 1)
    return max((rp[i][0] ** 2 + rp[i][1] ** 2) ** 0.5 for i in range(n))


def pool(acciones_, max_root=9.0, min_len=0.0, max_len=99.0, sin_giro=True):
    """Como SpReactions.pick / SpShooter.IDLE_ROLES: clips del rol, sin bucles largos, con poco recorrido."""
    out = []
    for x in CAT:
        if x["accion"] in acciones_ and not x["espejo"] and min_len <= x["duracion_s"] <= max_len \
                and _recorrido(x["clip"]) <= max_root and not (sin_giro and _meta(x["clip"]).get("heading_mode") == "turn"):
            out.append(x["clip"])
    return out


ESPERAS = pool(("idle_ready", "idle"), max_root=0.3, min_len=1.5)                      # SpShooter.stance
FESTEJOS = pool(("celebrate_scorer", "celebrate"), max_root=0.9, min_len=1.5, max_len=5.0)  # GOAL_SCORER (con borde cerca)
LAMENTOS = pool(("angry", "dejected"), max_root=0.9, min_len=1.2, max_len=5.0)         # MISS_SHOOTER
CAIDAS = [c for c in pool(("fall",), min_len=0.5) if _recorrido(c, 0.9) <= 0.15]     # BotonCaida.fall_clips
TROTES = [(x["clip"], _meta(x["clip"]).get("natural_speed_json", 0)) for x in CAT
          if x["accion"] in ("walk", "jog", "loco_jog") and not x["espejo"] and _meta(x["clip"]).get("natural_speed_json", 0) > 0.2]
print(f"banco del juego: {len(ESPERAS)} esperas, {len(FESTEJOS)} festejos, {len(LAMENTOS)} lamentos/enojos, {len(CAIDAS)} caídas, {len(TROTES)} trotes")


def trote_para(v):
    """SpShooter._loop_for: el bucle de caminar/trotar con la velocidad natural más cercana."""
    return min(TROTES, key=lambda x: abs(x[1] - v))


def velocidad_raiz(clip, t):
    a, b = raiz(clip, t), raiz(clip, t + 0.1)
    return (b - a).length / 0.1


def elegir(lista, n):
    return lista[(n * 7 + 3) % len(lista)]


# ---------------------------------------------------------------- tiempos del juego (Minigame: AIM → RUNUP → FLIGHT → RESOLVE)
RESOLVE_T = 2.2                            # el cartel del resultado
ESPERA_T = 2.0                             # lo que tarda en patear (una persona: 2–3 s; la CPU piensa 0,9 s)
acciones = {MESSI: [], CR7: []}
turnos, caidas, llamaradas = [], [], []
inicio_turno = 0.0
cayo_antes = None                           # quién cayó en el turno anterior: reaparece al empezar este
uso = {MESSI: 0, CR7: 0}
for n, (s, res, de) in enumerate(PLAN):
    r = 1 - s
    ultimo = n == len(PLAN) - 1
    rem = REMATE[s][uso[s] % len(REMATE[s])] if not ultimo else REMATE[s][0]
    uso[s] += 1
    origen, desde, salto = encuadre(s, rem)
    espera = 1.2 if n == 0 else (ESPERA_T + (0.6 if ultimo else 0.0))
    # SpShooter.execute: trota al punto de la carrera más cercano (a la velocidad de la raíz ahí) y entra al clip
    a_ = Vector((ADELANTE[s], 0, 0))
    der = Vector((a_.y, -a_.x, 0))
    rc = raiz(rem["clip"], desde)
    entrada = Vector(origen + [0]) + a_ * rc.x + der * rc.y
    v_tr = min(max(velocidad_raiz(rem["clip"], desde), 1.6), 5.0)
    clip_tr, v_nat = trote_para(v_tr)
    t_trote = salto / v_tr if salto > 0.35 else 0.0
    t_aim = inicio_turno + espera
    t_kick = t_aim + t_trote
    t_c = t_kick + rem["tc"] - desde
    t_p, ev = t_apreta(s, de, rem["vel"], rem["efecto"], t_c)
    ok = (t_p is not None) == (res == "boton")
    t_res = t_p if t_p is not None else t_c + (1.0 if res == "tablero" else 1.3)
    print(f"turno {n}: {PJ[s]:9s} {res:8s} espera {espera:.1f} s, trote {t_trote:.2f} s ({clip_tr}, {v_tr:.1f} m/s), "
          f"contacto {t_c:5.2f}, resultado {t_res:5.2f}  {'OK' if ok else '¡NO COINCIDE!'}")
    tu = {"tirador": s, "personaje": PJ[s], "clip": rem["clip"], "patea_s": round(t_kick, 3), "resultado": res,
          "destino": de, "velocidad": rem["vel"], "efecto": list(rem["efecto"]), "aparece_s": round(inicio_turno, 2),
          "desde_s": desde, "inicio_turno_s": round(inicio_turno, 3), "contacto_s": round(t_c, 3), "resultado_s": round(t_res, 3)}
    if cayo_antes is not None:              # como el juego (_restore_mechanisms): reaparece en su lugar al empezar el turno
        tu["sube_s"], tu["sube_lado"], tu["sube_dur"] = round(inicio_turno, 3), cayo_antes, 0.0
        cayo_antes = None
    turnos.append(tu)
    # los dos en su lugar al empezar el turno (SpShooter.stance): esperas del banco
    for k in (s, r):
        clip_e = ("s_jn_warmup_2878" if (k == CR7 and k == s) else elegir(ESPERAS, n + 3 * k))
        ac = {"clip": F + clip_e, "inicio_s": round(inicio_turno, 3), "pos": [0.0, 0.0], "mirando_deg": MIRA[k], "repetir": 4}
        if k == CR7 and k == s:
            ac["pose"], ac["pose_dur_s"] = "pose_a", round(espera + 0.2, 2)     # la parada «A» de Cristiano
        acciones[k].append(ac)
    # trote hasta la carrera y el remate
    if t_trote > 0:
        rumbo_tr = __import__("math").degrees(__import__("math").atan2(entrada.y, entrada.x))
        acciones[s].append({"clip": F + clip_tr, "inicio_s": round(t_aim, 3), "pos": [0.0, 0.0], "mirando_deg": round(rumbo_tr, 1),
                            "mover_a": [round(entrada.x, 3), round(entrada.y, 3)], "mover_s": round(t_trote, 3),
                            "repetir": 6, "velocidad": round(v_tr / max(v_nat, 0.5), 3)})
    acciones[s].append({"clip": rem["clip"], "inicio_s": round(t_kick, 3), "pos": origen, "mirando_deg": MIRA[s], "desde_s": desde})
    # reacción del que pateó (SpShooter.react): al saberse el resultado, con el seguimiento de la pierna hecho
    t_reac = max(t_res + 0.1, t_c + 0.45)
    if not ultimo:
        lista = FESTEJOS if res == "boton" else LAMENTOS
        acciones[s].append({"clip": F + elegir(lista, n), "inicio_s": round(t_reac, 3), "encadenar": True})
    if res == "boton":
        # el rival pierde el piso (caída del juego sin desplazamiento) y se va al vacío agitándose (Mixamo)
        acciones[r].append({"clip": F + elegir(CAIDAS, n), "inicio_s": round(t_p + 0.02, 3), "encadenar": True})
        acciones[r].append({"clip": MX + "caidas_muertes/Falling.fbx", "inicio_s": round(t_p + 0.55, 3), "encadenar": True,
                            "repetir": 3})
        caidas.append((r, t_p))
        llamaradas.append([round(t_p + 0.05, 3), r])
        cayo_antes = r
    elif n + 1 < len(PLAN):
        # se salvó: provoca al que falló
        acciones[r].append({"clip": F + TAUNTS[n % len(TAUNTS)], "inicio_s": round(t_res + 0.5, 3), "pos": [0.0, 0.0],
                            "mirando_deg": MIRA[r]})
    inicio_turno = round(t_res + RESOLVE_T, 3)
t_final = caidas[-1][1]
# festejo final del ganador
if ganador == CR7:
    t_siu = round(t_final + 1.0, 2)
    acciones[CR7].append({"clip": MX + "saltos_parkour/Joyful_Jump.fbx", "inicio_s": t_siu, "pos": [ADELANTE[CR7] * 1.2, 0.0],
                          "mirando_deg": (MIRA[CR7] + 180) % 360, "giro_deg": 180, "giro_desde_s": 0.42, "giro_dur_s": 0.55})
    acciones[CR7].append({"clip": F + "f_jn_celebrate_scorer_0942", "inicio_s": round(t_siu + 1.45, 2), "encadenar": True,
                          "pose": "siu", "pose_dur_s": 5.0})
    t_festejo = t_siu
else:
    t_festejo = round(t_final + 0.9, 2)
    acciones[MESSI].append({"clip": F + "f_jn_celebrate_scorer_0942", "inicio_s": t_festejo, "pos": [ADELANTE[MESSI] * 1.2, 0.0],
                            "mirando_deg": MIRA[MESSI], "pose": "dedos_al_cielo", "pose_dur_s": 5.2})
ESCENA_S = round(t_festejo + 6.5, 2)
for k in (MESSI, CR7):
    acciones[k].sort(key=lambda a: a["inicio_s"])

# cámara lenta sólo en el final (el último remate y la caída)
tc_fin = turnos[-1]["contacto_s"]
LENTAS = [(tc_fin - 0.3, t_final + 1.4, 1.8)]
MAPA = [[0.0, 0.0]]
tp = te = 0.0
for a, b, k in LENTAS:
    tp += a - te
    MAPA.append([round(tp, 3), round(a, 3)])
    tp += (b - a) * k
    MAPA.append([round(tp, 3), round(b, 3)])
    te = b
DUR = round(tp + (ESCENA_S - te), 3)
ESCENA_S = round(ESCENA_S + (60.0 - DUR), 3)       # la película dura 60 s: el festejo final se ajusta
DUR = 60.0
MAPA.append([DUR, ESCENA_S])
print(f"escena {ESCENA_S:.1f} s; festejo final desde {t_festejo:.1f} s")


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
    if t1_ - t0 < 0.2:
        return
    tomas.append({"id": f"t{len(tomas) + 1:02d}_{tipo}", "tipo": tipo, "plano": plano, "inicio_s": t0,
                  "duracion_s": round(t1_ - t0, 3), "luz_relleno": 0, **k})


def lado(s):
    return 1.0 if AV.trampilla(s).y > 0 else -1.0


def juego(s, e0, e1, plano):
    """La cámara del juego (Boton de caída: detrás y arriba del que patea, mirando adelante), vertical."""
    toma("estatica", plano, e0, e1, desde=A(f"pelota_{s}", [-ADELANTE[s] * 6.0, lado(s) * 2.6, 3.6]),
         objetivo=A(f"pelota_{s}", [ADELANTE[s] * 6.0, lado(s) * 0.4, 0.4]), lente_mm=22)


def lateral(s, e0, e1, plano):
    toma("estatica", plano, e0, e1, desde=A(f"pelota_{s}", [ADELANTE[s] * 0.8, -lado(s) * 3.4, 0.45]),
         objetivo=A(f"pelota_{s}", [-ADELANTE[s] * 0.6, lado(s) * 0.6, 0.7]), lente_mm=24)


def victima(r, e0, e1, plano):
    toma("estatica", plano, e0, e1, desde=A(f"trampa_{r}", [ADELANTE[r] * 2.4, -lado(r) * 2.0, 0.55]),
         objetivo=A(f"trampa_{r}", [0, 0, 1.3]), lente_mm=22)


def abajo(r, e0, e1, plano):
    toma("estatica", plano, e0, e1, desde=A(f"trampa_{r}", [-ADELANTE[r] * 0.5, -lado(r) * 0.6, 4.6]),
         objetivo=A(f"trampa_{r}", [0, 0, -8.0]), lente_mm=22)


def pelota(n, e0, e1, plano):
    toma("seguimiento", plano, e0, e1, movil=f"pelota_{n}", punto_base="", desp_local=[0.6, -2.4, 0.5],
         objetivo=Mv(f"pelota_{n}", [0, 6, 0]), lente_mm=26, retardo=0.6)


def reaccion(s, e0, e1, plano):
    toma("orbita", plano, e0, e1, centro=A(f"pelota_{s}", [-ADELANTE[s] * 0.3, 0, 1.0]), radio=4.5, altura=1.4,
         angulo_inicial=30, angulo_final=60, lente_mm=28)


Nm = {MESSI: "MESSI", CR7: "CRISTIANO"}
for n, tu in enumerate(turnos):
    s, r = tu["tirador"], 1 - tu["tirador"]
    ini, t_c, t_res = tu["inicio_turno_s"], tu["contacto_s"], tu["resultado_s"]
    fin = turnos[n + 1]["inicio_turno_s"] if n + 1 < len(turnos) else None
    if n == 0:
        toma("grua", "el estadio de noche, las dos plataformas sobre el vacío; CRISTIANO / MESSI se prepara", 0.0, t_c - 0.7,
             desde=A("centro", [-3, -26, 15]), hasta=A(f"pelota_{s}", [-ADELANTE[s] * 6.0, lado(s) * 2.6, 3.6]),
             objetivo=A(f"boton_{r}"), lente_mm=22)
    else:
        juego(s, ini, t_c - 0.7, f"turno de {Nm[s]}: espera, toma carrera")
    lateral(s, t_c - 0.7, t_c + 0.25, f"{Nm[s]}: " + ("empeine, a matar" if s == CR7 else "zurda con rosca"))
    if tu["resultado"] == "boton":
        pelota(n, t_c + 0.25, t_res - 0.3, "la pelota cruza el vacío hacia el botón")
        victima(r, t_res - 0.3, t_res + 0.3, "el botón se pone ROJO: alarma, se abre el piso")
        abajo(r, t_res + 0.3, t_res + 1.7, f"{Nm[r]} cae al vacío")
        if fin is not None:
            reaccion(s, t_res + 1.7, fin, f"{Nm[s]} festeja; el público estalla")
        cierre = t_res + 1.7
    else:
        pelota(n, t_c + 0.25, t_res + 0.2, "pega en el tablero" if tu["resultado"] == "tablero" else "se le abre al vacío")
        victima(r, t_res + 0.2, t_res + 1.3, f"{Nm[r]} se salvó y lo provoca")
        reaccion(s, t_res + 1.3, fin, f"{Nm[s]} se lamenta")
        cierre = fin
festejo_txt = ("CRISTIANO: salto, media vuelta en el aire… ¡SIUUU!" if ganador == CR7 else "MESSI: los dos índices al cielo")
cursor = turnos[-1]["resultado_s"] + 1.7
toma("orbita", festejo_txt, cursor, ESCENA_S - 2.4, centro=A(f"trampa_{ganador}", [ADELANTE[ganador] * 0.6, 0, 1.1]),
     radio=4.2, altura=1.4, angulo_inicial=-40 if ganador == CR7 else 140, angulo_final=40 if ganador == CR7 else 220,
     lente_mm=26)
toma("grua", "final: la cámara sube sobre el estadio; papelitos",
     ESCENA_S - 2.4, ESCENA_S, desde=A("centro", [0, -9, 3]), hasta=A("centro", [0, -20, 18]), objetivo=A("centro"), lente_mm=22)

personajes = [{"id": PJ[k], "modelo": MODELO[k], "sobre": f"soporte_{k}", "acciones": acciones[k]} for k in (MESSI, CR7)]
animo = [[0, "aplauso"]]
for tu in turnos:
    animo.append([tu["patea_s"] - 0.2, "tension"])
for lado, t_p in caidas:
    animo.append([t_p, "festejo"])
    animo.append([t_p + 2.2, "aplauso"])
animo.append([t_final + 2.2, "salta"])
animo.sort(key=lambda a: a[0])
MUSICA = (f"High energy sports arena track, {DUR:.0f} seconds, no vocals: hard-hitting trap drums, deep 808 bass and an "
          "epic stadium brass hook, built for a viral football duel video; constant forward drive with short breaks, "
          "a dramatic tension build in the last third and a huge drop at the winning moment around "
          f"{peli(t_final):.0f}s, then a triumphant outro.")
sonido = {"generador": "procedural", "ambiente": "arcade_duelo", "publico": 0.45, "eventos": [
    {"tipo": "musica", "prompt": MUSICA, "duracion_s": DUR, "inicio_s": 0.0, "volumen": 0.5},
] + [{"tipo": "efecto", "prompt": "massive football stadium crowd erupting in wild cheers and screams, tens of thousands of fans",
      "duracion_s": 4, "inicio_s": peli(t_p + 0.1), "volumen": 1.0} for _l, t_p in caidas]
  + [{"tipo": "efecto", "prompt": "man screaming as he falls down into a deep abyss, voice fading away with echo",
      "duracion_s": 3, "inicio_s": peli(t_p + 0.15), "volumen": 0.75, "movil": PJ[l]} for l, t_p in caidas]
  + ([{"tipo": "efecto", "prompt": "a whole football stadium shouting SIUUU together, huge crowd chant", "duracion_s": 3,
       "inicio_s": peli(t_festejo + 1.4), "volumen": 1.0}] if ganador == CR7 else
     [{"tipo": "efecto", "prompt": "football stadium crowd chanting Messi Messi Messi rhythmically", "duracion_s": 5,
       "inicio_s": peli(t_festejo + 0.3), "volumen": 0.9}])}
escena = {
    "tipo": "escena", "id": f"p007_al_vacio-{ESCENA_ID}", "produccion": "p007_al_vacio", "numero": NUM, "version": 1,
    "titulo": f"Al vacío — Messi vs. Cristiano (gana {'Cristiano' if ganador == CR7 else 'Messi'})",
    "guion": "Estadio de noche. Dos plataformas sobre el vacío. MESSI contra CRISTIANO, primero a tres: quien le pega fuerte "
             "al botón verde del rival lo pone rojo, suena la alarma y se le abre el piso. Cristiano le pega de empeine y "
             "muy fuerte; Messi con rosca, colocado. 2-2 y el último remate decide: el otro cae al vacío en cámara lenta. "
             + ("Cristiano festeja con el «Siu»." if ganador == CR7 else "Messi señala el cielo con los dos índices."),
    "duracion_s": DUR, "mapa_tiempo": MAPA,
    "escenario": {"id": "al_vacio", "generador": "al_vacio",
                  "parametros": {"semilla": 7, "duracion_s": ESCENA_S, "animo": animo, "llamaradas": llamaradas,
                                 "pie": {"0": PIE[MESSI], "1": PIE[CR7]},
                                 "papelitos_s": round(t_final + 1.0, 2)}},
    "duelo": {"turnos": turnos, "primero_a": 3, "gana": PJ[ganador]},
    "eventos": [], "vehiculos": [], "personajes": personajes, "tomas": tomas,
    "moviles_escenario": [f"pelota_{n}" for n in range(len(turnos))],
    "sonido": sonido,
    "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.0, "vertical": True},
    "estado": "borrador", "bloqueada": False, "huella_v": 2,
}
salida = RAIZ / f"producciones/p007_al_vacio/escenas/{ESCENA_ID}/v1/escena.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=1))
print("escrito", salida, len(tomas), "tomas,", DUR, "s de película,", ESCENA_S, "s de escena; caídas",
      [(PJ[l], round(t, 2)) for l, t in caidas])
