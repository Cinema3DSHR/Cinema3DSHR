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
CAIDA = [{"clip": MX + "caidas_muertes/Falling_From_Losing_Balance.fbx", "dt": 0.02},
         {"clip": MX + "caidas_muertes/Falling.fbx", "dt": 0.85, "repetir": 3}]
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


acciones = {MESSI: [], CR7: []}
turnos, caidas, llamaradas = [], [], []
pendiente_subir = None
patea = 0.0                                # (el primero se ajusta para pegarle en el segundo 1,25)
uso = {MESSI: 0, CR7: 0}
for n, (s, res, de) in enumerate(PLAN):
    r = 1 - s
    rem = REMATE[s][uso[s] % 2] if n != len(PLAN) - 1 else REMATE[s][0]    # el último: el remate «firma»
    uso[s] += 1
    origen, desde, salto = encuadre(s, rem)
    if n == 0:                              # el primer remate pega en el segundo 1,25 (gancho)
        patea = round(1.25 - (rem["tc"] - desde), 3)
    t_c = patea + rem["tc"] - desde
    t_p, ev = t_apreta(s, de, rem["vel"], rem["efecto"], t_c)
    ok = (t_p is not None) == (res == "boton")
    print(f"turno {n}: {PJ[s]:9s} {res:8s} remate {rem['clip'][-4:]} contacto {t_c:5.2f} aprieta {t_p}  "
          f"{'OK' if ok else '¡NO COINCIDE!'}  {[(e['tipo'], e['lado'], e['impacto']) for e in ev[:2]]}")
    inicio = patea - 1.0
    tu = {"tirador": s, "personaje": PJ[s], "clip": rem["clip"], "patea_s": round(patea, 3), "resultado": res,
          "destino": de, "velocidad": rem["vel"], "efecto": list(rem["efecto"]), "aparece_s": round(inicio, 2), "sube_dur": 1.6,
          "desde_s": desde}
    if pendiente_subir is not None:
        tu["sube_s"], tu["sube_lado"] = pendiente_subir[1], pendiente_subir[0]
        pendiente_subir = None
    turnos.append(tu)
    # el que patea espera al costado de la pelota (sobre su trampilla) y entra a la carrera del clip desde ahí;
    # Cristiano en su parada de tiro libre (piernas abiertas, brazos en «A»)
    if s == CR7:
        acciones[s].append({"clip": F + "s_jn_warmup_2878", "inicio_s": round(inicio, 3), "pos": [0.0, 0.0],
                            "mirando_deg": MIRA[s], "pose": "pose_a", "pose_dur_s": round(patea - inicio + 0.2, 2)})
    else:
        acciones[s].append({"clip": F + "s_jn_idle_ready_0150", "inicio_s": round(inicio, 3), "pos": [0.0, 0.0], "mirando_deg": MIRA[s]})
    acciones[s].append({"clip": rem["clip"], "inicio_s": round(patea, 3), "pos": origen, "mirando_deg": MIRA[s],
                        "desde_s": desde, "desde_pos": [0.0, 0.0], "empalme_s": round(min(1.3, 0.35 + salto / 2.6), 2)})
    print(f"   {PJ[s]}: entra al clip en {desde:.2f} s (a {salto} m de donde espera)")
    reac = patea + rem["dur"] - desde - 0.1
    ultimo = n == len(PLAN) - 1
    if res == "boton" and not ultimo:
        acciones[s].append({"clip": F + FESTEJOS[n % len(FESTEJOS)], "inicio_s": round(reac, 3), "encadenar": True})
        acciones[s].append({"clip": F + TAUNTS[n % len(TAUNTS)], "inicio_s": round(reac + 2.6, 3), "encadenar": True})
    elif res == "tablero":
        acciones[s].append({"clip": F + "s_jn_gesture_0944", "inicio_s": round(reac - 0.4, 3), "encadenar": True})
        acciones[s].append({"clip": F + "f_jn_angry_0356", "inicio_s": round(reac + 1.0, 3), "encadenar": True})
    elif res == "afuera":
        acciones[s].append({"clip": F + "f_jn_dejected_0102", "inicio_s": round(reac - 0.3, 3), "encadenar": True})
        acciones[s].append({"clip": F + "s_jn_dejected_0948", "inicio_s": round(reac + 1.8, 3), "encadenar": True})
    # el rival espera parado sobre su trampilla (salvo que esté subiendo en el ascensor)
    if tu.get("sube_lado") != r:
        acciones[r].append({"clip": F + ("s_jn_idle_fidget_0148" if n % 2 else "f_jn_idle_0520"), "inicio_s": round(inicio, 3),
                            "pos": [0.0, 0.0], "mirando_deg": MIRA[r], "repetir": 3})
    if res == "boton":
        for k, c in enumerate(CAIDA):
            a = {"clip": c["clip"], "inicio_s": round(t_p + c["dt"], 3), "encadenar": True}
            if c.get("repetir"):
                a["repetir"] = c["repetir"]
            acciones[r].append(a)
        caidas.append((r, t_p))
        llamaradas.append([round(t_p + 0.05, 3), r])
        if not ultimo:
            t_s = round(t_p + 1.25, 2)
            pendiente_subir = (r, t_s)
            acciones[r].append({"clip": F + ENOJOS[n % len(ENOJOS)], "inicio_s": t_s, "pos": [0.0, 0.0], "mirando_deg": MIRA[r]})
            # el que cayó vuelve en el ascensor (1,6 s); si es el próximo en patear, recién arriba se va atrás a tomar carrera
            patea = round(t_s + 1.6 + 1.05, 3) if r == PLAN[n + 1][0] else round(t_p + 1.8, 3)
        else:
            patea = None
    else:                                   # el rival se salvó: lo provoca
        acciones[r].append({"clip": F + TAUNTS[(n + 2) % len(TAUNTS)], "inicio_s": round(t_c + 1.15, 3), "pos": [0.0, 0.0],
                            "mirando_deg": MIRA[r]})
    if res == "tablero":
        patea = round(t_c + 2.9, 3)
    elif res == "afuera":
        patea = round(t_c + 2.7, 3)
t_final = caidas[-1][1]
# festejo final del ganador (cámara lenta en el salto del «Siu»)
if ganador == CR7:
    t_siu = round(t_final + 1.4, 2)
    acciones[CR7].append({"clip": MX + "saltos_parkour/Joyful_Jump.fbx", "inicio_s": t_siu, "pos": [ADELANTE[CR7] * 0.6, 0.0],
                          "mirando_deg": (MIRA[CR7] + 180) % 360, "giro_deg": 180, "giro_desde_s": 0.42, "giro_dur_s": 0.55})
    acciones[CR7].append({"clip": F + "f_jn_celebrate_scorer_0942", "inicio_s": round(t_siu + 1.45, 2), "encadenar": True,
                          "pose": "siu", "pose_dur_s": 5.0})
    t_festejo = t_siu
else:
    t_festejo = round(t_final + 1.3, 2)
    acciones[MESSI].append({"clip": F + "f_jn_celebrate_scorer_0942", "inicio_s": t_festejo, "pos": [ADELANTE[MESSI] * 0.6, 0.0],
                            "mirando_deg": MIRA[MESSI], "pose": "dedos_al_cielo", "pose_dur_s": 5.2})
ESCENA_S = round(t_festejo + 7.2, 2)
# el perdedor vuelve derrotado en el ascensor al final
t_vuelve = round(t_final + 4.4, 2)
turnos[-1]["sube_s"], turnos[-1]["sube_lado"] = t_vuelve, perdedor
acciones[perdedor].append({"clip": F + "s_jn_angry_0372", "inicio_s": t_vuelve, "pos": [0.0, 0.0], "mirando_deg": MIRA[perdedor]})
acciones[perdedor].append({"clip": F + "f_jn_dejected_0104", "inicio_s": round(t_vuelve + 2.4, 2), "encadenar": True})   # de rodillas
for k in (MESSI, CR7):
    acciones[k].sort(key=lambda a: a["inicio_s"])

# cámara lenta: la primera caída (gancho), el último remate y su caída, y el salto del festejo
t1 = caidas[0][1]
tc_fin = turnos[-1]["patea_s"] + REMATE[ganador][0]["tc"] - turnos[-1]["desde_s"]
LENTAS = [(t1 - 0.2, t1 + 1.3, 2.5), (tc_fin - 0.35, t_final + 1.6, 2.2), (max(t_festejo + 0.2, t_final + 1.7), t_festejo + 1.5, 2.0)]
MAPA = [[0.0, 0.0]]
tp = te = 0.0
for a, b, k in LENTAS:
    tp += a - te
    MAPA.append([round(tp, 3), round(a, 3)])
    tp += (b - a) * k
    MAPA.append([round(tp, 3), round(b, 3)])
    te = b
DUR = round(tp + (ESCENA_S - te), 3)
# la película dura 60 s: el festejo se estira o se corta para llegar justo
ESCENA_S = round(ESCENA_S + (60.0 - DUR), 3)
DUR = 60.0
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
    if t1_ - t0 < 0.2:
        return
    tomas.append({"id": f"t{len(tomas) + 1:02d}_{tipo}", "tipo": tipo, "plano": plano, "inicio_s": t0,
                  "duracion_s": round(t1_ - t0, 3), "luz_relleno": 0, **k})


def lado(s):
    """+1 si espera a la izquierda de la plataforma (en Y del mundo), −1 a la derecha."""
    return 1.0 if AV.trampilla(s).y > 0 else -1.0


def espalda(s, e0, e1, plano):
    """Detrás y afuera de donde espera el que patea, alta: el jugador, la pelota, el vacío y el rival con su botón."""
    toma("estatica", plano, e0, e1, desde=A(f"trampa_{s}", [-ADELANTE[s] * 2.6, lado(s) * 1.3, 2.2]),
         objetivo=A(f"pelota_{s}", [ADELANTE[s] * 7.0, 0, 0.2]), lente_mm=22)


def lateral(s, e0, e1, plano):
    """Del otro costado de la pelota y bajo: la carrera llega y le pega."""
    toma("estatica", plano, e0, e1, desde=A(f"pelota_{s}", [ADELANTE[s] * 0.8, -lado(s) * 3.4, 0.45]),
         objetivo=A(f"pelota_{s}", [-ADELANTE[s] * 0.6, lado(s) * 0.6, 0.7]), lente_mm=24)


def victima(r, e0, e1, plano):
    """Delante y hacia el centro del que espera, bajo: él arriba de su trampilla y el botón detrás."""
    toma("estatica", plano, e0, e1, desde=A(f"trampa_{r}", [ADELANTE[r] * 2.4, -lado(r) * 2.0, 0.55]),
         objetivo=A(f"trampa_{r}", [0, 0, 1.3]), lente_mm=22)


def abajo(r, e0, e1, plano):
    """Desde abajo y afuera de la plataforma: se abre la trampilla y el jugador cae de perfil hacia la niebla."""
    toma("estatica", plano, e0, e1, desde=A(f"trampa_{r}", [ADELANTE[r] * 1.5, lado(r) * 7.5, -6.5]),
         objetivo=A(f"trampa_{r}", [0, 0, -3.0]), lente_mm=20)


def pelota(n, e0, e1, plano):
    toma("seguimiento", plano, e0, e1, movil=f"pelota_{n}", punto_base="", desp_local=[0.6, -2.4, 0.5],
         objetivo=Mv(f"pelota_{n}", [0, 6, 0]), lente_mm=26, retardo=0.6)


Nm = {MESSI: "MESSI", CR7: "CRISTIANO"}
cursor = 0.0
for n, tu in enumerate(turnos):
    s, r = tu["tirador"], 1 - tu["tirador"]
    rem = next(x for x in REMATE[s] if x["clip"] == tu["clip"])
    t_c = tu["patea_s"] + rem["tc"] - tu["desde_s"]
    t_p = next((tp_ for lado, tp_ in caidas if lado == r and tp_ > t_c and tp_ < t_c + 2.0), None)
    if n == 0:
        toma("grua", "aérea sobre el vacío: el estadio lleno, las plataformas; CRISTIANO / MESSI ya corre hacia la pelota",
             0.0, t_c - 0.15, desde=A("centro", [-3, -26, 15]), hasta=A(f"trampa_{s}", [-ADELANTE[s] * 3, -7, 3.5]),
             objetivo=A(f"boton_{r}"), lente_mm=22)
    else:
        espalda(s, cursor, t_c - 0.6, f"{Nm[s]} toma carrera")
        lateral(s, t_c - 0.6, t_c + 0.12, f"{Nm[s]}: " + ("empeine, a matar" if s == CR7 else "zurda con rosca"))
    if t_p is not None:
        pelota(n, t_c + 0.12 if n else t_c - 0.15, t_p - 0.25, "la pelota cruza el vacío hacia el botón")
        victima(r, t_p - 0.25, t_p + 0.3, "el botón se pone ROJO: alarma, se abre el piso")
        abajo(r, t_p + 0.3, t_p + 1.6, f"{Nm[r]} cae al vacío")
        cursor = t_p + 1.6
        if n != len(turnos) - 1:
            toma("orbita", f"{Nm[s]} festeja; el público estalla", cursor, cursor + 1.0,
                 centro=A(f"pelota_{s}", [-ADELANTE[s] * 0.3, 0, 1.0]), radio=4.5, altura=1.4, angulo_inicial=30, angulo_final=70,
                 lente_mm=28)
            cursor += 1.0
            if tu.get("sube_s") is None:
                pass
    else:
        fin = t_c + (1.6 if tu["resultado"] == "tablero" else 1.4)
        if tu["resultado"] == "tablero":
            victima(r, t_c + 0.12, fin, "pega arriba del botón: el tablero tiembla")
        else:
            pelota(n, t_c + 0.12, fin, "se le abre y se pierde en el vacío")
        cursor = fin
# subidas en el ascensor (si quedó tiempo entre tomas, se ven en las de espalda del siguiente)
festejo_txt = ("CRISTIANO: carrera, salto, media vuelta en el aire… ¡SIUUU!" if ganador == CR7
               else "MESSI: los dos índices al cielo")
toma("orbita", festejo_txt, cursor, ESCENA_S - 2.4, centro=A(f"trampa_{ganador}", [ADELANTE[ganador] * 0.6, 0, 1.1]),
     radio=4.2, altura=1.4, angulo_inicial=-40 if ganador == CR7 else 140, angulo_final=40 if ganador == CR7 else 220,
     lente_mm=26)
toma("grua", "final: la cámara sube sobre el estadio; papelitos; el perdedor vuelve derrotado en el ascensor",
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
