"""Genera escenas/eNN/v1/escena.json de «Dúo Cero — Episodio 01» a partir del guion y de las voces ya generadas.

    /opt/tools/blendenv/bin/python producciones/p009_duo_cero/herramientas/escenas.py [1 2 3 …]

Los tiempos salen de guion.plan() (duración real de cada línea sin el silencio de los bordes; las seis escenas
suman 180 s). Caras: expresión de quien habla y reacción de quien escucha, miradas entre ellos, boca sincronizada
con el audio. Cuerpos: clips de Mixamo sentados (hablar / escuchar / gestos) con fundidos. Cámaras: cobertura que
corta con el diálogo (primeros planos, sobre el hombro, planos detalle, exteriores del vagón).
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import guion as G
from estudio.audio import elevenlabs as EL

FPS = 30
VAGON = "tren_06_cerrado"
PISO = 1.60
PLAN = G.plan()
SENT = "mixamo:animaciones/sentado_manejar/"

PERSONAJES = {
    "nico": {"modelo": "stickman:masculino", "alto_m": 1.78,
             "vestuario": {"estilo": "tactico", "pelo": "kingsman", "color_pelo": [0.20, 0.09, 0.03]},
             "sentado": (-1.02, -0.48), "otro": "luna", "mirar_al_otro": 0.55},
    "luna": {"modelo": "stickman:femenino", "alto_m": 1.68,
             "vestuario": {"estilo": "tactico", "pelo": "luna", "color_pelo": [0.06, 0.025, 0.012]},
             "sentado": (-1.02, 0.48), "otro": "nico", "mirar_al_otro": -0.55},
}
CLIPS_HABLA = {"nico": ["Sitting_Talking.fbx", "Sitting_Talking_2.fbx"], "luna": ["Sitting_Talking_2.fbx", "Sitting_Talking.fbx"]}
CLIPS_OYE = {"nico": ["Sitting_Idle_2.fbx", "Sitting_Idle_3.fbx"], "luna": ["Sitting_Idle_3.fbx", "Sitting_Idle_2.fbx"]}
# gestos puntuales: (escena, quien, texto que contiene, clip, segundos desde el comienzo de la línea)
GESTOS = [
    (1, "nico", "¿Otra vez?", "Sitting_Disbelief.fbx", 0.2),
    (1, "nico", "alumno excelente", "Sitting_Thumbs_Up.fbx", 5.2),
    (1, "luna", "Me preocupa", "Sitting_Disbelief.fbx", 0.0),
    (2, "luna", "No es perfecto", "Sitting_Angry_3.fbx", 0.1),
    (2, "luna", "Tu concepto", "Sitting_Disapproval.fbx", 0.0),
    (3, "luna", "Ja... ja", "Sitting_Laughing.fbx", -0.3),
    (3, "nico", "Estoy deseando llegar", "Cheering_While_Sitting.fbx", 0.6),
]
# silencios actuados (nota del guion → expresión)
NOTAS = {
    "Luna lo mira con incredulidad": {"luna": "incredula"},
    "Nico sonríe": {"nico": "sonrisa", "luna": "ironica"},
    "Luna lo mira fijamente": {"luna": "seria", "nico": "confiado"},
    "Luna intenta seguir seria y termina sonriendo": {"luna": "sonrisa", "nico": "picara"},
    "silencio": {"luna": "sonrisa_suave", "nico": "neutral"},
    "Luna lo observa unos segundos": {"luna": "carinosa", "nico": "sonrisa_suave"},
    "Luna baja la mirada y sonríe": {"luna": "avergonzada", "nico": "sonrisa_suave"},
    "Luna niega con la cabeza, sonriendo": {"luna": "sonrisa", "nico": "picara"},
    "Luna lo observa un instante": {"luna": "carinosa", "nico": "picara"},
}


def voz_ev(p):
    return {"tipo": "voz", "rol": p["voz"], "texto": p["texto"]}


def expr(nombre):
    return G.EXPR_EXTRA.get(nombre, nombre)


# ------------------------------------------------------------------------------------------------ caras
def cara(n, quien):
    pasos = PLAN[n]["pasos"]
    otro = PERSONAJES[quien]["otro"]
    exprs, habla, miradas = [{"t": 0.0, "expr": "neutral"}], [], []
    for p in pasos:
        if p.get("voz") == quien:
            exprs.append({"t": max(0.0, p["t_ini"] - 0.15), "expr": expr(p.get("cara", "neutral"))})
            habla.append({"inicio_s": p["t_ini"], "audio": str(EL.ruta_en_biblioteca(voz_ev(p))), "recorte_s": p["recorte_s"],
                          "texto": p["texto"]})
            if p.get("voz") in ("nico", "luna"):
                miradas.append({"t": p["t_ini"], "hasta": p["t_fin"], "u": PERSONAJES[quien]["mirar_al_otro"] * 0.8})
        elif p.get("voz") == otro:
            exprs.append({"t": p["t_ini"] + 0.3, "expr": expr(p.get("oye", "neutral"))})
            miradas.append({"t": p["t_ini"] + 0.1, "hasta": p["t_fin"] + 0.3, "u": PERSONAJES[quien]["mirar_al_otro"]})
        elif p.get("nota") and NOTAS.get(p["nota"], {}).get(quien):
            exprs.append({"t": p["t_ini"] + 0.1, "expr": NOTAS[p["nota"]][quien]})
            if quien == "luna" and "baja la mirada" in p["nota"]:
                miradas.append({"t": p["t_ini"] + 0.2, "hasta": p["t_fin"] + 2.0, "v": -0.7, "u": -0.2})
            else:
                miradas.append({"t": p["t_ini"], "hasta": p["t_fin"], "u": PERSONAJES[quien]["mirar_al_otro"]})
    return {"expresiones": exprs, "habla": habla, "miradas": miradas}


# ------------------------------------------------------------------------------------------------ cuerpos sentados
def acciones_sentado(n, quien, dur):
    pasos = PLAN[n]["pasos"]
    x, y = PERSONAJES[quien]["sentado"]
    tramos = []                                         # (t, clip, desde_clip)
    turno = 0
    for p in pasos:
        if not p.get("voz") or p["voz"] not in ("nico", "luna"):
            continue
        habla = p["voz"] == quien
        lista = CLIPS_HABLA[quien] if habla else CLIPS_OYE[quien]
        clip = lista[turno % len(lista)]
        turno += 1
        t = max(0.0, p["t_ini"] - (0.25 if habla else -0.2))
        tramos.append((t, clip, (turno * 3.7) % 8.0 if "Talking" in clip else 0.0))
        for (e, q, frag, gclip, dt) in GESTOS:
            if e == n and q == quien and frag in p["texto"]:
                tramos.append((max(0.0, p["t_ini"] + dt), gclip, 0.0))
    tramos.sort(key=lambda a: a[0])
    limpio = []
    for t, c, d in tramos:                              # no dos cambios a menos de 0,9 s
        if limpio and t - limpio[-1][0] < 0.9:
            limpio[-1] = (limpio[-1][0], c, d) if "Talking" not in c and "Idle" not in c else limpio[-1]
            continue
        limpio.append((t, c, d))
    if not limpio or limpio[0][0] > 0.0:
        limpio.insert(0, (0.0, CLIPS_OYE[quien][0], 0.0))
    acc = []
    for i, (t, c, d) in enumerate(limpio):
        a = {"clip": SENT + c, "inicio_s": round(t, 3), "pos": [x, y, PISO], "mirando_deg": 0, "mezcla_s": 0.45}
        if "Talking" in c:
            a["clip_hasta_s"] = 18.0             # sólo lo que se usa (desde ≤ 8 s + la línea más larga ≤ 9 s)
        if d:
            a["desde_clip_s"] = round(d, 2)
        if i == 0:
            a.pop("mezcla_s")
        acc.append(a)
    return acc


# ------------------------------------------------------------------------------------------------ cámaras
ANC = (0.0, 0.0, PISO + 1.2)                        # ancla "" del vagón


def _loc(p):
    return [round(p[0] - ANC[0], 3), round(p[1] - ANC[1], 3), round(p[2] - ANC[2], 3)]


TIROS = {
    # sentados: la cabeza queda a ~1,15 m del piso del vagón (medido en las fijas)
    "dos": ((1.25, 0.0, PISO + 1.0), (-0.95, 0.0, PISO + 0.98), 22),
    "cu_nico": ((0.35, 0.32, PISO + 1.10), (-0.95, -0.48, PISO + 1.09), 42),
    "cu_luna": ((0.35, -0.32, PISO + 1.07), (-0.95, 0.48, PISO + 1.05), 42),
    "os_nico": ((-0.30, 1.35, PISO + 1.22), (-0.95, -0.48, PISO + 1.12), 32),
    "os_luna": ((-0.30, -1.35, PISO + 1.24), (-0.95, 0.48, PISO + 1.09), 32),
    "ecu_nico": ((0.45, -0.42, PISO + 1.13), (-0.95, -0.48, PISO + 1.12), 60),
    "ecu_luna": ((0.45, 0.42, PISO + 1.09), (-0.95, 0.48, PISO + 1.08), 60),
    "exterior": ((6.5, -3.4, PISO + 0.55), (-0.9, 0.0, PISO + 1.0), 30),
    "exterior_cerca": ((3.4, 1.6, PISO + 0.95), (-0.9, -0.1, PISO + 0.95), 24),
    "farol": ((0.25, -1.05, PISO + 1.45), (-1.0, -1.9, PISO + 1.15), 42),
    "radio": ((0.05, 1.05, PISO + 0.95), (-0.55, 1.75, PISO + 0.62), 55),
    "tableta": ((-0.55, 0.40, PISO + 1.25), (-0.72, 0.48, PISO + 0.82), 32),
    "techo": ((0.55, 0.05, PISO + 2.55), (-0.95, 0.0, PISO + 0.9), 16),
    "puerta_afuera": ((-0.5, -0.9, PISO + 1.3), (3.0, 0.4, PISO + 1.0), 24),
    # de pie (escena 4)
    # (medido: cabeza de Nico de pie ~1,47 m sobre el piso; de Luna en la puerta ~1,35; Nico agachado ~1,0)
    "cu_nico_pie": ((0.85, 0.2, PISO + 1.55), (-0.45, -0.47, PISO + 1.47), 38),
    "dos_pie": ((1.3, 0.05, PISO + 1.45), (-0.8, 0.0, PISO + 1.30), 24),
    "cu_luna_puerta": ((3.0, 1.2, PISO + 1.45), (1.3, 0.42, PISO + 1.44), 45),
    "ecu_luna_puerta": ((2.7, 0.75, PISO + 1.40), (1.3, 0.38, PISO + 1.36), 50),
    "cu_nico_puerta": ((2.9, -1.2, PISO + 1.15), (1.4, -0.38, PISO + 1.0), 42),
    "siluetas": ((-1.0, 0.05, PISO + 1.45), (3.0, 0.05, PISO + 1.15), 24),
    "puerta_exterior": ((4.2, -1.6, PISO + 1.0), (1.3, 0.05, PISO + 1.25), 28),
    "puerta_exterior_ancho": ((6.0, -4.5, PISO + 0.4), (1.2, 0.0, PISO + 1.0), 22),
}


def toma_vagon(tid, nombre, t0, t1, plano, desp_extra=(0, 0, 0)):
    desde, mira, lente = TIROS[nombre]
    d = [desde[i] + desp_extra[i] for i in range(3)]
    return {"id": tid, "tipo": "estatica", "plano": plano, "inicio_s": round(t0, 3), "duracion_s": round(t1 - t0, 3),
            "rigido": True, "movil": "vagon", "punto_base": "", "desp_local": _loc(d),
            "objetivo": {"movil": "vagon", "punto": "", "desp_local": _loc(mira)}, "lente_mm": lente, "luz_relleno": 0}


def cobertura(n, dur, inicio_dialogo=0.0, extras=None):
    """Plan de cortes para una conversación: cada línea con su plano, reacciones en los silencios y respiros."""
    pasos = [p for p in PLAN[n]["pasos"] if p["t_fin"] > inicio_dialogo]
    cortes = []                                          # (t, tiro, plano)
    alterna = {"nico": 0, "luna": 0}
    for p in pasos:
        if p.get("voz") in ("nico", "luna"):
            q = p["voz"]
            d = p["t_fin"] - p["t_ini"]
            opciones = [f"cu_{q}", f"os_{q}", f"cu_{q}"]
            tiro = opciones[alterna[q] % len(opciones)]
            alterna[q] += 1
            if p.get("radio") == "boca" or "Ja... ja" in p["texto"]:
                tiro = f"ecu_{q}" if q == "luna" else f"cu_{q}"
            cortes.append((p["t_ini"] - 0.12, tiro, f"{q.capitalize()}: «{_limpio(p['texto'])[:60]}»"))
            if d > 4.6:
                otro = PERSONAJES[q]["otro"]
                cortes.append((p["t_ini"] + d * 0.58, f"cu_{otro}", f"reacción de {otro.capitalize()}"))
        elif p.get("nota"):
            quien = next(iter(NOTAS.get(p["nota"], {"luna": 1})))
            cortes.append((p["t_ini"] + 0.05, f"ecu_{quien}" if "mira" in p["nota"] or "observa" in p["nota"] else f"cu_{quien}",
                           p["nota"]))
    for (t, tiro, plano) in (extras or []):
        cortes.append((t, tiro, plano))
    cortes.sort(key=lambda c: c[0])
    # unir cortes muy seguidos (menos de 1,1 s) y evitar el mismo tiro dos veces seguidas
    limpio = []
    for c in cortes:
        if limpio and (c[0] - limpio[-1][0] < 1.1 or c[1] == limpio[-1][1]):
            continue
        limpio.append(c)
    return limpio


def _limpio(texto):
    import re
    return re.sub(r"\[[^\]]*\]\s*", "", texto).strip()


def tomas_desde_cortes(cortes, dur, previas=None):
    tomas = list(previas or [])
    t_ini = tomas[-1]["inicio_s"] + tomas[-1]["duracion_s"] if tomas else 0.0
    cortes = [c for c in cortes if c[0] > t_ini + 0.6]
    pts = [t_ini] + [c[0] for c in cortes] + [dur]
    tiros = ([cortes[0][1]] if cortes else ["dos"])
    if cortes:
        tiros = ["dos"] + [c[1] for c in cortes]
        planos = ["Nico y Luna en el vagón"] + [c[2] for c in cortes]
    else:
        planos = ["Nico y Luna en el vagón"]
    for i in range(len(pts) - 1):
        t0, t1 = pts[i], pts[i + 1]
        if t1 - t0 < 0.05:
            continue
        tomas.append(toma_vagon(f"t{len(tomas) + 1:02d}_{tiros[i]}", tiros[i], t0, t1, planos[i]))
    return tomas


def encadenar(tomas, dur):
    """Cortes en cuadros enteros y encadenados exacto (cada toma empieza donde termina la anterior)."""
    bordes = [round(t["inicio_s"] * FPS) for t in tomas] + [round(dur * FPS)]
    limpio = []
    for t, b0, b1 in zip(tomas, bordes, bordes[1:]):
        if b1 - b0 >= 1:
            limpio.append((t, b0, b1))
    tomas[:] = []
    ini = 0.0
    for i, (t, b0, b1) in enumerate(limpio):
        t["inicio_s"] = ini
        t["duracion_s"] = round((b1 - b0) / FPS, 4) if i < len(limpio) - 1 else dur - ini
        t["id"] = f"t{i + 1:02d}_{t['id'].split('_', 1)[1]}"
        ini = ini + t["duracion_s"]
        tomas.append(t)


# ------------------------------------------------------------------------------------------------ sonido
def sonido_dialogo(n, dur, extra=None, musica=None):
    evs = []
    for p in PLAN[n]["pasos"]:
        if p.get("voz"):
            ev = {"tipo": "voz", "rol": p["voz"], "texto": p["texto"], "inicio_s": round(p["inicio_s"], 3),
                  "recorte_s": [round(x, 3) for x in p["recorte_s"]], "volumen": 1.0}
            if p.get("filtro_radio"):
                ev["radio"] = True
            elif p["voz"] in ("nico", "luna"):
                ev["movil"] = p["voz"]
            evs.append(ev)
    from estudio.escenarios import duo_cero as DC
    DC._CACHE["T_salto"] = t_salto()
    base = [{"tipo": "tren", "tipos": DC.COMPOSICION, "s_inicial": round(DC.s_cabeza(PLAN[n]["T0"]), 2), "volumen": 0.7}]
    if musica:
        base.append({"tipo": "musica", "prompt": musica, "duracion_s": round(dur, 2), "inicio_s": 0.0, "volumen": 0.32})
    return {"generador": "procedural", "ambiente": None, "eventos": base + (extra or []) + evs}


# ------------------------------------------------------------------------------------------------ escenas 1-3
MUSICA = {
    1: "Cinematic night train opening, {d} seconds, no vocals: low ambient synth pad, distant metallic percussion "
       "like train wheels, a playful pizzicato motif enters as two characters banter, warm and slightly mysterious, "
       "light action-comedy tone",
    2: "Cinematic spy-mission briefing underscore, {d} seconds, no vocals: tense pulsing synth bass, soft ticking "
       "percussion, light comedic staccato strings answering, building curiosity, modern action series",
    3: "Tender cinematic underscore inside a night train, {d} seconds, no vocals: warm felt piano and soft strings, "
       "a light comedic beat at the start, then intimate and romantic, gentle and understated, ends hopeful",
}


def escena_dialogo(n):
    e = PLAN[n]
    dur = e["duracion_s"]
    pjs = []
    for q, d in PERSONAJES.items():
        pjs.append({"id": q, "modelo": d["modelo"], "alto_m": d["alto_m"], "vestuario": d["vestuario"], "sobre": VAGON,
                    "acciones": acciones_sentado(n, q, dur), "cara": cara(n, q)})
    params_extra = {}
    if n in (1, 2):
        # Luna con la tableta: el mapa de la instalación (sólo mientras la sostiene con las dos manos)
        if n == 1:
            ventanas = [(0.0, 7.2)]
        else:
            sur = next(p for p in e["pasos"] if p.get("voz") == "luna" and "sur tiene" in p["texto"])
            ventanas = [(0.0, e["pasos"][0]["t_fin"] + 0.6), (sur["t_ini"] - 0.6, sur["t_fin"] + 0.5)]
        luna = pjs[1]
        luna["en_mano"] = {"objeto": "tableta", "visible": [[a, b] for a, b in ventanas]}
        luna["poses"] = [{"pose": "tableta", "inicio_s": a, "dur_s": b - a} for a, b in ventanas]
        luna["cara"]["miradas"] += [{"t": a + 0.2, "hasta": min(b, a + 3.5), "v": -0.7, "u": 0.1} for a, b in ventanas]
    if n == 3:
        # Nico con la radio: en la mano, a la boca para «¿Luna? ¿Me recibís?», y la deja después de «impecable»
        boca = next(p for p in e["pasos"] if p.get("radio") == "boca")
        impecable = next(p for p in e["pasos"] if p.get("voz") == "nico" and "impecable" in p["texto"])
        r1 = impecable["t_fin"] + 0.4
        nico = pjs[0]
        nico["en_mano"] = {"visible": [[0.0, r1]]}
        nico["poses"] = [{"pose": "radio_mano", "inicio_s": 0.0, "dur_s": boca["t_ini"] - 0.3},
                         {"pose": "radio_boca", "inicio_s": boca["t_ini"] - 0.3, "dur_s": boca["t_fin"] - boca["t_ini"] + 0.6},
                         {"pose": "radio_mano", "inicio_s": boca["t_fin"] + 0.3, "dur_s": r1 - boca["t_fin"] - 0.3}]
        params_extra["radio_en_mano"] = [0.0, r1]
    tomas = []
    extras = []
    if n == 1:
        a = PLAN[1]["pasos"][0]["t_fin"]
        tomas.append({"id": "t01_aerea", "tipo": "grua", "plano": "aérea: el tren de carga cruza la sierra de noche",
                      "inicio_s": 0.0, "duracion_s": round(a, 3),
                      "desde": {"movil": "vagon", "punto": "", "desp_local": [-95, -150, 62]},
                      "hasta": {"movil": "vagon", "punto": "", "desp_local": [-30, -46, 16]},
                      "objetivo": {"movil": "vagon", "punto": "", "desp_local": [0, 10, 0]}, "lente_mm": 30})
        tomas.append(toma_vagon("t02_exterior", "exterior", a, a + 3.1,
                                "el vagón con la puerta abierta: adentro, la luz del farol"))
        extras = [(17.0, "exterior_cerca", "exterior: el paisaje pasa por la puerta")]
    elif n == 2:
        sur = next(p for p in PLAN[2]["pasos"] if p.get("voz") == "luna" and "sur tiene" in p["texto"])
        extras = [(0.0, "tableta", "la tableta: el mapa de la instalación"),
                  (sur["t_ini"] - 0.1, "tableta", "el mapa: los tres puestos de vigilancia del sur")]
    elif n == 3:
        extras = [(0.0, "radio", "Nico toma la radio"), (26.0, "exterior", "exterior: el tren en la noche, la puerta encendida")]
    cortes = cobertura(n, dur, extras=extras)
    tomas = tomas_desde_cortes(cortes, dur, tomas)
    encadenar(tomas, dur)
    return {
        "tipo": "escena", "id": f"p009_duo_cero-e{n:02d}", "produccion": "p009_duo_cero", "numero": n, "version": 1,
        "titulo": {1: "El tren de carga", 2: "Repaso de la misión", 3: "Prueba de comunicaciones"}[n],
        "guion": " ".join(_limpio(p["texto"]) for p in e["pasos"] if p.get("voz")),
        "duracion_s": dur,
        "escenario": {"id": "duo_cero_noche", "generador": "duo_cero",
                      "parametros": {"escena": n, "T0": e["T0"], "duracion_escena_s": dur, "T_salto": t_salto(),
                                     **params_extra}},
        "eventos": [], "vehiculos": [], "personajes": pjs, "tomas": tomas,
        "moviles_escenario": ["vagon", "loco", "cola"],
        "sonido": sonido_dialogo(n, dur, musica=MUSICA[n].format(d=int(round(dur))),
                                 extra=[{"tipo": "voz", "radio": True, "rol": "central_ar", "texto": "Recibido, Dúo Cero. Adelante.",
                                         "inicio_s": round(next(p for p in e["pasos"] if p.get("accion") == "interferencia")["t_ini"], 2),
                                         "recorte_s": [0.0, 0.35], "volumen": 0.5}] if n == 3 else None),
        "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.6, "muestras": 6},
        "estado": "borrador", "bloqueada": False, "huella_v": 2,
    }


def t_salto():
    """Instante del episodio (reloj del tren) en que Nico sale por la puerta frente al montículo de arena."""
    return round(PLAN[4]["T0"] + 19.55, 3)


def escribir(m):
    n = m["numero"]
    salida = RAIZ / f"producciones/p009_duo_cero/escenas/e{n:02d}/v1/escena.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(m, ensure_ascii=False, indent=1))
    print("escrito", salida.relative_to(RAIZ), len(m["tomas"]), "tomas,", m["duracion_s"], "s")


# ------------------------------------------------------------------------------------------------ escena 4: el salto
RIFLE = "mixamo:packs/Pro_Rifle_Pack/"
AVENT = "mixamo:packs/Action_Adventure_Pack/"
SHOOT = "mixamo:animaciones/armas_shooter/"
PUERTA_NICO = (1.30, -0.32, PISO)
PUERTA_LUNA = (1.30, 0.42, PISO)
SALTO = {"nico": 19.55, "luna": 20.02}           # tiempo de la escena (contenido) en que cada uno sale por la puerta
FRENO_RAIZ = 45.0                                # la raíz frena enseguida: la rodada del clip pone el resto


def _ts(n, t):
    return round(G.a_escena(n, t), 3)


def cara_escena(n, quien, extra=()):
    c = cara(n, quien)
    for e in c["expresiones"]:
        e["t"] = _ts(n, e["t"])
    for h in c["habla"]:
        h["inicio_s"] = _ts(n, h["inicio_s"])
    for m in c["miradas"]:
        m["t"], m["hasta"] = _ts(n, m["t"]), _ts(n, m["hasta"])
    for t, ex in extra:
        c["expresiones"].append({"t": t, "expr": ex})
    c["expresiones"].sort(key=lambda e: e["t"])
    return c


def _acc(clip, t, pos=None, mirando=0, **k):
    a = {"clip": clip, "inicio_s": round(t, 3), "mirando_deg": mirando, **k}
    if pos is not None:
        a["pos"] = [round(v, 3) for v in pos]
    return a


def t_rodada(quien, T0):
    """Cuándo toca la arena (tiempo de la escena) según la trayectoria del salto."""
    from estudio.escenarios import duo_cero as DC
    DC._CACHE["T_salto"] = t_salto()
    loc = PUERTA_NICO if quien == "nico" else PUERTA_LUNA
    tray = DC.salto(loc, T0 + SALTO[quien], freno=FRENO_RAIZ)
    aire = [x for x in tray if x[3]]
    return SALTO[quien] + aire[-1][0], tray


def escena_4():
    n = 4
    e = PLAN[n]
    dur = e["duracion_s"]
    T0 = e["T0"]
    tl_n, _ = t_rodada("nico", T0)
    tl_l, _ = t_rodada("luna", T0)
    nico = [
        _acc(SENT + "Sitting_Idle_2.fbx", 0.0, (-1.02, -0.48, PISO)),
        _acc(SENT + "Sit_To_Stand.fbx", 3.2, (-1.02, -0.48, PISO), mezcla_s=0.3),
        _acc(SHOOT + "Grab_Rifle_From_The_Side.fbx", 5.0, encadenar=True, mezcla_s=0.35),
        _acc(RIFLE + "idle.fbx", 7.2, encadenar=True, mezcla_s=0.4),
        _acc(RIFLE + "idle.fbx", 9.17, PUERTA_NICO),
        _acc(RIFLE + "idle_crouching.fbx", 12.3, PUERTA_NICO, mezcla_s=0.5),
        _acc(RIFLE + "idle.fbx", 17.3, PUERTA_NICO, mezcla_s=0.4),
        _acc(RIFLE + "jump_up.fbx", SALTO["nico"] - 0.12, PUERTA_NICO, mezcla_s=0.12),
        _acc(AVENT + "falling_idle.fbx", SALTO["nico"] + 0.22, PUERTA_NICO, mezcla_s=0.15),
        _acc(AVENT + "falling_to_roll.fbx", tl_n - 0.1, PUERTA_NICO, mezcla_s=0.1),
        _acc(SHOOT + "Rifle_Kneel_Idle.fbx", tl_n + 1.45, PUERTA_NICO, mezcla_s=0.4),
    ]
    luna = [
        _acc(SENT + "Sitting_Idle_3.fbx", 0.0, (-1.02, 0.48, PISO)),
        _acc(SENT + "Sitting_Talking_2.fbx", 2.1, (-1.02, 0.48, PISO), mezcla_s=0.35, desde_clip_s=6.0, clip_hasta_s=12.0),
        _acc(SENT + "Sit_To_Stand.fbx", 6.75, (-1.02, 0.48, PISO), mezcla_s=0.3),
        _acc(SHOOT + "Grab_Rifle_From_The_Side.fbx", 8.4, encadenar=True, mezcla_s=0.3),
        _acc(RIFLE + "idle.fbx", 9.17, PUERTA_LUNA),
        _acc(RIFLE + "idle_aiming.fbx", 13.3, PUERTA_LUNA, mezcla_s=0.5),
        _acc("mixamo:animaciones/hablar_conversacion/Yelling_Out.fbx", 17.5, PUERTA_LUNA, mezcla_s=0.3),
        _acc(RIFLE + "jump_up.fbx", SALTO["luna"] - 0.12, PUERTA_LUNA, mezcla_s=0.12),
        _acc(AVENT + "falling_idle.fbx", SALTO["luna"] + 0.22, PUERTA_LUNA, mezcla_s=0.15),
        _acc(AVENT + "falling_to_roll.fbx", tl_l - 0.1, PUERTA_LUNA, mezcla_s=0.1),
        _acc(SHOOT + "Rifle_Kneel_Idle.fbx", tl_l + 1.45, PUERTA_LUNA, mezcla_s=0.4),
    ]
    t_fusil, t_sub = 5.75, 9.17
    pjs = [
        {"id": "nico", **{k: PERSONAJES["nico"][k] for k in ("modelo", "alto_m", "vestuario")}, "sobre": VAGON,
         "acciones": nico, "cara": cara_escena(n, "nico", [(SALTO["nico"] - 0.05, "grito"), (tl_n + 0.2, "risa"),
                                                          (tl_n + 1.6, "confiado")]),
         "arma_stickman": {"tipo": "fusil", "visible": [[t_fusil, dur]]}, "mochila": {"desde_s": 9.17}},
        {"id": "luna", **{k: PERSONAJES["luna"][k] for k in ("modelo", "alto_m", "vestuario")}, "sobre": VAGON,
         "acciones": luna, "cara": cara_escena(n, "luna", [(SALTO["luna"] - 0.3, "sorpresa"), (tl_l + 0.25, "dolor"),
                                                          (tl_l + 1.2, "enojo")]),
         "arma_stickman": {"tipo": "subfusil", "visible": [[t_sub, dur]]}, "mochila": {"desde_s": 9.17}},
    ]
    # ---- cámaras (tiempos de película)
    def T(tid, nombre, t0, t1, plano, **k):
        return toma_vagon(tid, nombre, t0, t1, plano, **k)
    tomas = [
        T("t_base", "puerta_afuera", 0.0, 2.28, "desde adentro, por la puerta abierta: la base iluminada a lo lejos"),
        T("t_cu_luna", "cu_luna", 2.28, 3.2, "Luna: «Dos minutos»"),
        T("t_dos", "dos", 3.2, 4.57, "Nico se pone de pie"),
        T("t_cu_luna2", "dos", 4.57, 5.62, "Luna: «Esperá mi señal»; Nico ya de pie"),
        T("t_nico_pie", "cu_nico_pie", 5.62, 6.99, "Nico, ya con el fusil: «Por supuesto»"),
        T("t_dos_pie", "dos_pie", 6.99, 8.53, "Luna se levanta: «Lo digo en serio»"),
        T("t_nico_pie2", "cu_nico_pie", 8.53, 9.17, "Nico: «Yo también»"),
        {"id": "t_zona", "tipo": "estatica", "plano": "desde la zona de carga: el tren llega, la puerta encendida",
         "inicio_s": 9.17, "duracion_s": 1.83, "desde": [12.0, 14.0, 1.3],
         "objetivo": {"movil": "vagon", "punto": "", "desp_local": [0, 0, 0]}, "lente_mm": 38},
        T("t_luna_puerta", "cu_luna_puerta", 11.0, 12.05, "Luna en la puerta: «Treinta segundos»"),
        T("t_siluetas", "siluetas", 12.05, 13.42, "los dos en la puerta, a contraluz de la zona de carga"),
        T("t_ecu_luna", "ecu_luna_puerta", 13.42, 15.3, "Luna cuenta: «Diez… nueve…»"),
        T("t_nico_sonrie", "cu_nico_puerta", 15.3, 16.5, "Nico sonríe"),
        T("t_puerta_ext", "puerta_exterior", 16.5, 17.58, "los dos listos en la puerta"),
        T("t_luna_grita", "cu_luna_puerta", 17.58, 18.79, "Luna: «¡Nico, esperá!»"),
        T("t_vamos", "puerta_exterior_ancho", 18.79, 20.0, "Nico: «¡Vamos!» y salta"),
        {"id": "t_vuelo", "tipo": "seguimiento", "plano": "CÁMARA LENTA: Nico en el aire, el tren detrás; Luna salta",
         "inicio_s": 20.0, "duracion_s": 2.6, "movil": "nico", "punto_base": "", "desp_local": [5.2, 1.2, 0.6],
         "objetivo": {"movil": "nico", "punto": "", "desp_local": [0, 0, 0.3]}, "lente_mm": 30, "retardo": 0.35},
        {"id": "t_aterrizaje", "tipo": "estatica", "plano": "aterrizan en la arena y ruedan; el tren sigue de largo",
         "inicio_s": 22.6, "duracion_s": 0.0, "desde": [12.2, 25.0, 0.55],
         "objetivo": [6.3, 15.0, 0.9], "lente_mm": 26},
    ]
    encadenar(tomas, dur)
    son = sonido_dialogo(n, dur, musica="Rising cinematic action cue, {d} seconds, no vocals: tense ticking pulse and low "
                         "strings building under a countdown, heavy drums and brass swell, a huge hit and a brief "
                         "slow-motion suspended swell at second 20, then driving percussion as the heroes land. "
                         "Modern action series".format(d=int(round(dur))),
                         extra=[{"tipo": "viento_conduccion", "movil": "vagon", "volumen": 0.35},
                                {"tipo": "caida", "t": [round(G.a_pelicula(n, tl_n), 2), round(G.a_pelicula(n, tl_l), 2)]},
                                {"tipo": "pasos", "t": [round(G.a_pelicula(n, SALTO["nico"] - 0.1), 2),
                                                        round(G.a_pelicula(n, SALTO["luna"] - 0.1), 2)]}])
    m = {
        "tipo": "escena", "id": "p009_duo_cero-e04", "produccion": "p009_duo_cero", "numero": 4, "version": 1,
        "titulo": "El momento del salto",
        "guion": " ".join(_limpio(p["texto"]) for p in e["pasos"] if p.get("voz")) + " Saltan del tren.",
        "duracion_s": dur, "mapa_tiempo": G.mapa_tiempo(n, dur),
        "escenario": {"id": "duo_cero_noche", "generador": "duo_cero",
                      "parametros": {"escena": n, "T0": T0, "duracion_escena_s": e["contenido_s"], "T_salto": t_salto(),
                                     "fusil_hasta_s": t_fusil, "subfusil_hasta_s": t_sub, "mochilas_hasta_s": 9.17}},
        "eventos": [], "vehiculos": [], "personajes": pjs, "tomas": tomas,
        "saltos": [{"pj": q, "t": SALTO[q], "local": list(PUERTA_NICO if q == "nico" else PUERTA_LUNA),
                    "freno": FRENO_RAIZ, "avance_desde_s": round((tl_n if q == "nico" else tl_l) + 1.45, 3),
                    "avance_m": 2.9} for q in ("nico", "luna")],
        "moviles_escenario": ["vagon", "loco", "cola"],
        "sonido": son,
        "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.6, "muestras": 6},
        "estado": "borrador", "bloqueada": False, "huella_v": 2,
    }
    return m


# ------------------------------------------------------------------------------------------------ escena 5: primer contacto
GUARDIAS = {
    "guardia_a": {"modelo": "stickman:masculino", "alto_m": 1.82,
                  "vestuario": {"estilo": "urbano", "pelo": "cresta", "color_pelo": [0.015, 0.015, 0.016]}},
    "guardia_b": {"modelo": "stickman:masculino", "alto_m": 1.76,
                  "vestuario": {"estilo": "urbano", "pelo": "mohicano", "color_pelo": [0.02, 0.018, 0.016]}},
}
P1_LUNA = (10.55, 24.85)            # detrás de la pila de cajas P1 (12, 26,5), del lado opuesto a los guardias
P2_NICO = (15.35, 17.55)            # detrás de la pila P2 (17,2, 19)
A_ALTO = (23.5, 38.5)               # dónde se planta el guardia A
B_ALTO = (28.6, 36.4)


def _ang(a, b):
    import math
    return round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), 1)


def _dist(a, b):
    return ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5


def escena_5():
    import math
    from estudio.escenarios import duo_cero as DC
    n = 5
    e = PLAN[n]
    dur = e["duracion_s"]
    DC._CACHE["T_salto"] = t_salto()
    T4 = PLAN[4]["T0"]
    (pn, rn) = DC.fin_del_salto(PUERTA_NICO, T4 + SALTO["nico"], FRENO_RAIZ)
    (pl, rl) = DC.fin_del_salto(PUERTA_LUNA, T4 + SALTO["luna"], FRENO_RAIZ)
    z = lambda p: DC.altura_suelo(p[0], p[1])
    # Luna camina hasta Nico mientras le pregunta si está bien
    junto = (pn[0] + 0.55, pn[1] + 1.55)
    a_junto = _ang(pl, junto)
    n_walk = max(1, round(_dist(pl, junto) / 1.86))
    t_shout = next(p for p in e["pasos"] if p.get("voz") == "guardia")["t_ini"]
    t_fuego = next(p for p in e["pasos"] if p.get("accion") == "tiroteo")["t_ini"]       # 13,03
    # ---- tiros (tiempo de la escena = película en esta escena)
    tiros, sn, sl, sa, sb = [], [], [], [], []

    def tiro(quien, t, a, imp, normal=None, lista=None):
        tiros.append({"tirador": quien, "t": round(t, 3), "a": [round(v, 3) for v in a], "impacto": imp,
                      **({"normal": normal} if normal else {})})
        lista.append(round(t, 3))
    for k, t in enumerate((14.05, 14.35, 14.7)):
        tiro("guardia_a", t, (12.0 + 0.3 * k, 26.0, 2.2 - 0.25 * k), "chispas", [-0.6, -0.8, 0.2], sa)
    for k, t in enumerate((15.1, 15.55)):
        tiro("guardia_b", t, (17.0 + 0.4 * k, 18.45, 2.0 - 0.4 * k), "chispas", [-0.7, -0.7, 0.2], sb)
    for k, t in enumerate((15.95, 16.2)):
        tiro("luna", t, (A_ALTO[0] + 1.5, A_ALTO[1] + 3.5, 1.7), "nada", lista=sl)
    for k, t in enumerate((16.95, 17.08, 17.21)):
        tiro("nico", t, (A_ALTO[0], A_ALTO[1], 1.25 + 0.05 * k), "sangre" if k else "nada", lista=sn)
    tiro("guardia_b", 18.45, (16.6, 18.4, 2.35), "chispas", [-0.7, -0.7, 0.3], sb)
    for k, t in enumerate((19.75, 19.87, 19.99)):
        tiro("luna", t, (B_ALTO[0], B_ALTO[1], 1.3), "sangre" if k == 2 else "nada", lista=sl)
    t_hit_a, t_hit_b = 17.08, 19.99
    # ---- coreografías
    nico = [
        _acc(SHOOT + "Rifle_Kneel_Idle.fbx", 0.0, pn, rn),
        _acc(SHOOT + "Rifle_Kneel_To_Stand.fbx", 1.7, pn, rn, mezcla_s=0.3),
        _acc(RIFLE + "idle.fbx", 2.95, pn, _ang(pn, junto), mezcla_s=0.4, giro_s=0.5),
        _acc("mixamo:animaciones/gestos/Shrugging.fbx", 8.4, pn, _ang(pn, junto), mezcla_s=0.35),
        _acc(RIFLE + "idle.fbx", 10.3, pn, _ang(pn, junto), mezcla_s=0.4),
        _acc(RIFLE + "idle_aiming.fbx", t_shout + 0.35, pn, _ang(pn, A_ALTO), mezcla_s=0.25, giro_s=0.3),
        _acc(RIFLE + "sprint_forward.fbx", t_fuego + 0.05, pn, _ang(pn, P2_NICO), mezcla_s=0.2,
             repetir=max(1, round(_dist(pn, P2_NICO) / 3.25))),
        _acc(RIFLE + "idle_crouching_aiming.fbx", t_fuego + 1.55, (P2_NICO[0], P2_NICO[1], 0.0), _ang(P2_NICO, A_ALTO),
             mezcla_s=0.2),
        _acc(SHOOT + "Firing_Rifle.fbx", 16.7, (P2_NICO[0] + 0.9, P2_NICO[1] - 0.5, 0.0), _ang(P2_NICO, A_ALTO),
             mezcla_s=0.15),
        _acc(RIFLE + "idle_crouching_aiming.fbx", 18.2, (P2_NICO[0], P2_NICO[1], 0.0), _ang(P2_NICO, B_ALTO), mezcla_s=0.2),
        _acc(RIFLE + "idle_aiming.fbx", 20.9, (P2_NICO[0] + 0.4, P2_NICO[1], 0.0), _ang(P2_NICO, B_ALTO), mezcla_s=0.4),
        _acc(RIFLE + "idle.fbx", 22.4, (P2_NICO[0] + 0.4, P2_NICO[1], 0.0), _ang(P2_NICO, P1_LUNA), mezcla_s=0.5,
             giro_s=0.6),
    ]
    luna = [
        _acc(SHOOT + "Rifle_Kneel_Idle.fbx", 0.0, pl, rl),
        _acc(SHOOT + "Rifle_Kneel_To_Stand.fbx", 0.6, pl, rl, mezcla_s=0.3),
        _acc(RIFLE + "walk_forward.fbx", 1.75, pl, a_junto, mezcla_s=0.3, repetir=n_walk, giro_s=0.4),
        _acc(RIFLE + "idle.fbx", 1.75 + n_walk * 1.0, (junto[0], junto[1], 0.0), _ang(junto, pn), mezcla_s=0.35, giro_s=0.4),
        _acc("mixamo:animaciones/hablar_conversacion/Talking_5.fbx", 3.4, (junto[0], junto[1], 0.0), _ang(junto, pn),
             mezcla_s=0.35),
        _acc("mixamo:packs/Gestures_Pack_Basic/annoyed_head_shake.fbx", 6.7, (junto[0], junto[1], 0.0), _ang(junto, pn),
             mezcla_s=0.3),
        _acc("mixamo:packs/Gestures_Pack_Basic/shaking_head_no.fbx", 10.95, (junto[0], junto[1], 0.0), _ang(junto, pn),
             mezcla_s=0.3),
        _acc(RIFLE + "idle_aiming.fbx", t_shout + 0.3, (junto[0], junto[1], 0.0), _ang(junto, A_ALTO), mezcla_s=0.25,
             giro_s=0.3),
        _acc(RIFLE + "sprint_forward.fbx", t_fuego, (junto[0], junto[1], 0.0), _ang(junto, P1_LUNA), mezcla_s=0.2,
             repetir=max(1, round(_dist(junto, P1_LUNA) / 3.25))),
        _acc(RIFLE + "idle_crouching_aiming.fbx", t_fuego + 1.45, (P1_LUNA[0], P1_LUNA[1], 0.0), _ang(P1_LUNA, A_ALTO),
             mezcla_s=0.2),
        _acc(SHOOT + "Female_Peek_And_Aim.fbx", 15.6, (P1_LUNA[0], P1_LUNA[1], 0.0), _ang(P1_LUNA, A_ALTO), mezcla_s=0.2),
        _acc(RIFLE + "idle_crouching_aiming.fbx", 16.6, (P1_LUNA[0], P1_LUNA[1], 0.0), _ang(P1_LUNA, B_ALTO), mezcla_s=0.2),
        _acc(SHOOT + "Firing_Rifle.fbx", 19.5, (P1_LUNA[0] + 0.5, P1_LUNA[1] + 0.9, 0.0), _ang(P1_LUNA, B_ALTO),
             mezcla_s=0.15),
        _acc(RIFLE + "idle_aiming.fbx", 21.0, (P1_LUNA[0] + 0.5, P1_LUNA[1] + 0.9, 0.0), _ang(P1_LUNA, B_ALTO), mezcla_s=0.4),
        _acc(RIFLE + "idle.fbx", 22.4, (P1_LUNA[0] + 0.5, P1_LUNA[1] + 0.9, 0.0), _ang(P1_LUNA, P2_NICO), mezcla_s=0.5,
             giro_s=0.6),
    ]
    a_ini, b_ini = (25.8, 44.0), (31.6, 43.5)
    guardia_a = [
        _acc(RIFLE + "walk_forward.fbx", 9.6, (*a_ini, 0.0), _ang(a_ini, A_ALTO), repetir=max(1, round(_dist(a_ini, A_ALTO) / 1.86))),
        _acc("mixamo:animaciones/hablar_conversacion/Standing_Yell.fbx", t_shout - 0.15, (*A_ALTO, 0.0), _ang(A_ALTO, pn),
             mezcla_s=0.25),
        _acc(RIFLE + "idle_aiming.fbx", t_shout + 1.2, (*A_ALTO, 0.0), _ang(A_ALTO, P1_LUNA), mezcla_s=0.25),
        _acc(SHOOT + "Firing_Rifle.fbx", 13.95, (*A_ALTO, 0.0), _ang(A_ALTO, P1_LUNA), mezcla_s=0.15),
        _acc(RIFLE + "idle_aiming.fbx", 15.2, (*A_ALTO, 0.0), _ang(A_ALTO, P2_NICO), mezcla_s=0.3),
        _acc(SHOOT + "Rifle_Hit_To_Back.fbx", t_hit_a, (*A_ALTO, 0.0), _ang(A_ALTO, P2_NICO), mezcla_s=0.06),
    ]
    guardia_b = [
        _acc(RIFLE + "walk_forward.fbx", 11.0, (*b_ini, 0.0), _ang(b_ini, B_ALTO), repetir=max(1, round(_dist(b_ini, B_ALTO) / 1.86))),
        _acc(RIFLE + "idle_aiming.fbx", 14.2, (*B_ALTO, 0.0), _ang(B_ALTO, P2_NICO), mezcla_s=0.3),
        _acc(SHOOT + "Firing_Rifle.fbx", 15.0, (*B_ALTO, 0.0), _ang(B_ALTO, P2_NICO), mezcla_s=0.15),
        _acc(RIFLE + "idle_aiming.fbx", 16.2, (*B_ALTO, 0.0), _ang(B_ALTO, P2_NICO), mezcla_s=0.3),
        _acc(SHOOT + "Firing_Rifle.fbx", 18.35, (*B_ALTO, 0.0), _ang(B_ALTO, P2_NICO), mezcla_s=0.15),
        _acc(RIFLE + "death_from_front_headshot.fbx", t_hit_b, (*B_ALTO, 0.0), _ang(B_ALTO, P1_LUNA), mezcla_s=0.06),
    ]
    for lst in (nico, luna):                    # la altura de los pies sobre el montículo
        for a in lst:
            if "pos" in a and len(a["pos"]) == 3 and a["pos"][2] == 0.0:
                a["pos"][2] = round(z(a["pos"]), 3)
    pjs = [
        {"id": "nico", **{k: PERSONAJES["nico"][k] for k in ("modelo", "alto_m", "vestuario")}, "acciones": nico,
         "cara": cara_escena(n, "nico", [(t_fuego - 0.1, "decidido"), (16.6, "grito"), (17.5, "confiado"), (22.2, "sonrisa")]),
         "arma_stickman": {"tipo": "fusil", "disparos": sn}, "mochila": {"desde_s": 0.0}},
        {"id": "luna", **{k: PERSONAJES["luna"][k] for k in ("modelo", "alto_m", "vestuario")}, "acciones": luna,
         "cara": cara_escena(n, "luna", [(t_fuego - 0.1, "concentrada"), (14.05, "preocupada"), (15.6, "enojo"),
                                         (19.5, "decidido"), (21.2, "concentrada"), (22.5, "sonrisa_suave")]),
         "arma_stickman": {"tipo": "subfusil", "disparos": sl}, "mochila": {"desde_s": 0.0}},
        {"id": "guardia_a", **GUARDIAS["guardia_a"], "acciones": guardia_a,
         "cara": {"expresiones": [{"t": 0, "expr": "seria"}, {"t": t_shout - 0.2, "expr": "grito"}, {"t": 13.5, "expr": "enojo"},
                                  {"t": t_hit_a, "expr": "dolor"}],
                  "habla": [{"inicio_s": p["t_ini"], "audio": str(EL.ruta_en_biblioteca(voz_ev(p))), "recorte_s": p["recorte_s"],
                             "texto": p["texto"]} for p in e["pasos"] if p.get("voz") == "guardia"]},
         "arma_stickman": {"tipo": "ak", "disparos": sa}},
        {"id": "guardia_b", **GUARDIAS["guardia_b"], "acciones": guardia_b,
         "cara": {"expresiones": [{"t": 0, "expr": "seria"}, {"t": 14.2, "expr": "enojo"}, {"t": t_hit_b, "expr": "dolor"}]},
         "arma_stickman": {"tipo": "escopeta", "disparos": sb}},
    ]
    # ---- cámaras
    def sig(tid, movil, t0, t1, desp, obj_movil, obj_punto, plano, lente=40, retardo=0.25):
        return {"id": tid, "tipo": "seguimiento", "plano": plano, "inicio_s": t0, "duracion_s": t1 - t0, "movil": movil,
                "punto_base": "", "desp_local": desp, "objetivo": {"movil": obj_movil, "punto": obj_punto},
                "lente_mm": lente, "retardo": retardo, "luz_relleno": 25}

    def fija(tid, t0, t1, desde, objetivo, plano, lente=30):
        return {"id": tid, "tipo": "estatica", "plano": plano, "inicio_s": t0, "duracion_s": t1 - t0, "desde": desde,
                "objetivo": objetivo, "lente_mm": lente, "luz_relleno": 0}
    L = {p["voz"] + str(i): p for i, p in enumerate(e["pasos"]) if p.get("voz")}
    tomas = [
        fija("t_tren_se_va", 0.0, 1.22, [12.5, 6.0, 0.9], [3.5, 30.0, 2.0], "en la arena; el tren sigue de largo en la noche", 26),
        sig("t_luna_bien", "luna", 1.22, 2.13, [0.25, 1.9, 0.62], "luna", "cabeza", "Luna: «¿Estás bien?»", 45),
        sig("t_nico_nuevo", "nico", 2.13, 3.44, [-0.25, 1.9, 0.62], "nico", "cabeza", "Nico: «Como nuevo»", 45),
        sig("t_os_luna", "nico", 3.44, 5.44, [0.45, -0.85, 0.72], "luna", "cabeza", "Luna: «¿Podrías haber esperado mi señal?»", 40),
        sig("t_nico_tecnica", "nico", 5.44, 6.73, [-0.25, 1.8, 0.62], "nico", "cabeza", "Nico: «Técnicamente, la escuché»", 45),
        sig("t_luna_nico", "luna", 6.73, 7.82, [0.2, 1.4, 0.64], "luna", "cabeza", "Luna: «¡Nico!»", 60),
        fija("t_dos_arena", 7.82, 10.91, {"movil": "nico", "punto": "", "desp": [3.6, -2.4, 0.4]},
             {"movil": "luna", "punto": "pecho"}, "Nico: «No dijiste cuánto» — los dos en la arena", 32),
        sig("t_luna_niega", "luna", 10.91, 11.82, [0.25, 1.7, 0.62], "luna", "cabeza", "Luna niega con la cabeza, sonriendo", 50),
        sig("t_guardia", "guardia_a", 11.82, 13.03, [0.6, 2.4, 0.55], "guardia_a", "cabeza", "un guardia: «¡Eh! ¿Quién anda ahí?»", 38),
        fija("t_corren", 13.03, 14.0, [4.0, 33.0, 6.0], [16.0, 26.0, 1.0], "corren a cubrirse; los guardias levantan las armas", 24),
        sig("t_luna_cubierta", "luna", 14.0, 15.0, [-1.6, -1.2, 0.35], "luna", "pecho", "Luna detrás de las cajas: los tiros pegan arriba", 30),
        sig("t_guardia_b", "guardia_b", 15.0, 15.95, [0.9, 2.6, 0.5], "guardia_b", "pecho", "el segundo guardia dispara la escopeta", 35),
        sig("t_nico_sale", "nico", 15.95, 17.6, [-1.7, 1.6, 0.15], "nico", "pecho", "Nico sale de la cobertura y dispara", 26),
        sig("t_cae_a", "guardia_a", 17.6, 18.7, [2.6, 3.0, 0.3], "guardia_a", "pecho", "el guardia recibe el impacto y cae", 30),
        sig("t_nico_cubre", "nico", 18.7, 19.55, [1.4, -1.4, 0.4], "nico", "cabeza", "la escopeta pega en las cajas de Nico", 30),
        sig("t_luna_dispara", "luna", 19.55, 20.9, [1.5, 1.3, 0.45], "luna", "cabeza", "Luna asoma y dispara", 35),
        sig("t_cae_b", "guardia_b", 20.9, 22.2, [-2.6, 2.8, 0.4], "guardia_b", "pecho", "el segundo guardia cae", 30),
        fija("t_despejado", 22.2, dur, [3.0, 12.0, 2.6], [17.0, 27.0, 1.0], "la zona queda despejada", 24),
    ]
    encadenar(tomas, dur)
    son = sonido_dialogo(n, dur, musica="Action-comedy cue, {d} seconds, no vocals: starts light and playful with plucked "
                         "strings and a cheeky bass line, then at second 12 a sharp hit and a switch to tense, driving "
                         "percussion and staccato strings for a short gunfight, resolving with a confident brass "
                         "sting at the end".format(d=int(round(dur))),
                         extra=[{"tipo": "disparos", "t": sn, "arma": "M4A1"}, {"tipo": "disparos", "t": sl, "arma": "M4A1"},
                                {"tipo": "disparos", "t": sa, "arma": "AK47", "lado": "enemigo"},
                                {"tipo": "disparos", "t": sb, "arma": "AK47", "lado": "enemigo"},
                                {"tipo": "impactos", "t": [t + 0.04 for t in sa + sb]},
                                {"tipo": "caida", "t": [t_hit_a + 1.1, t_hit_b + 1.0]},
                                {"tipo": "pasos", "t": [round(t_fuego + 0.15 + 0.23 * k, 2) for k in range(8)]}])
    son["eventos"] = [ev for ev in son["eventos"] if ev["tipo"] != "tren"] + [
        {"tipo": "tren", "tipos": __import__("estudio.escenarios.duo_cero", fromlist=["x"]).COMPOSICION,
         "s_inicial": round(DC.s_cabeza(e["T0"]), 2), "volumen": 0.4}]
    return {
        "tipo": "escena", "id": "p009_duo_cero-e05", "produccion": "p009_duo_cero", "numero": 5, "version": 1,
        "titulo": "Primer contacto",
        "guion": " ".join(_limpio(p["texto"]) for p in e["pasos"] if p.get("voz")) + " Tiroteo con dos guardias.",
        "duracion_s": dur,
        "escenario": {"id": "duo_cero_noche", "generador": "duo_cero",
                      "parametros": {"escena": n, "T0": e["T0"], "duracion_escena_s": dur, "T_salto": t_salto()}},
        "eventos": [], "vehiculos": [], "personajes": pjs, "tomas": tomas, "tiros": tiros,
        "moviles_escenario": ["vagon", "loco", "cola"],
        "sonido": son,
        "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.6, "muestras": 6},
        "estado": "borrador", "bloqueada": False, "huella_v": 2,
    }


# ------------------------------------------------------------------------------------------------ escena 6: cierre
def escena_6():
    import math
    from estudio.escenarios import duo_cero as DC
    n = 6
    e = PLAN[n]
    dur = e["duracion_s"]
    DC._CACHE["T_salto"] = t_salto()
    z = lambda p: round(DC.altura_suelo(p[0], p[1]), 3)
    Lp = (P1_LUNA[0] + 0.5, P1_LUNA[1] + 0.9)
    N0 = (P2_NICO[0] + 0.4, P2_NICO[1])
    d = ((N0[0] - Lp[0]), (N0[1] - Lp[1]))
    k = (d[0] ** 2 + d[1] ** 2) ** 0.5
    N1 = (round(Lp[0] + d[0] / k * 1.5, 3), round(Lp[1] + d[1] / k * 1.5, 3))
    pasos = {(p.get("voz"), i): p for i, p in enumerate(e["pasos"])}
    t_fin_dialogo = next(p for p in e["pasos"] if p.get("accion") == "caminan_y_titulo")["t_ini"]
    porton = (150.0, 40.0)
    a_base = _ang(N1, porton)
    nico = [
        _acc(RIFLE + "walk_forward.fbx", 0.0, (*N0, z(N0)), _ang(N0, N1), repetir=4),
        _acc(RIFLE + "idle.fbx", 3.85, (*N1, z(N1)), _ang(N1, Lp), mezcla_s=0.4),
        _acc("mixamo:animaciones/hablar_conversacion/Talking_3.fbx", 3.95, (*N1, z(N1)), _ang(N1, Lp), mezcla_s=0.35),
        _acc(RIFLE + "idle.fbx", 6.2, (*N1, z(N1)), _ang(N1, Lp), mezcla_s=0.4),
        _acc("mixamo:animaciones/hablar_conversacion/Talking_6.fbx", 13.0, (*N1, z(N1)), _ang(N1, Lp), mezcla_s=0.35),
        _acc(RIFLE + "idle.fbx", 16.0, (*N1, z(N1)), _ang(N1, Lp), mezcla_s=0.4),
        _acc(RIFLE + "walk_forward.fbx", t_fin_dialogo + 0.1, (*N1, z(N1)), a_base, mezcla_s=0.4, repetir=4),
    ]
    L1 = (Lp[0] + 0.0, Lp[1] + 0.0)
    luna = [
        _acc(RIFLE + "idle.fbx", 0.0, (*Lp, z(Lp)), _ang(Lp, N0)),
        _acc("mixamo:animaciones/hablar_conversacion/Talking_5.fbx", 6.0, (*Lp, z(Lp)), _ang(Lp, N1), mezcla_s=0.35),
        _acc(RIFLE + "idle.fbx", 9.9, (*Lp, z(Lp)), _ang(Lp, N1), mezcla_s=0.4),
        _acc("mixamo:animaciones/emociones/Laughing.fbx", 10.7, (*Lp, z(Lp)), _ang(Lp, N1), mezcla_s=0.35),
        _acc(RIFLE + "idle.fbx", 12.9, (*Lp, z(Lp)), _ang(Lp, N1), mezcla_s=0.4),
        _acc(RIFLE + "walk_forward.fbx", t_fin_dialogo + 0.75, (*L1, z(L1)), _ang(L1, porton), mezcla_s=0.4, repetir=4),
    ]
    radio_boca = next(p for p in e["pasos"] if p.get("radio") == "boca")
    central = next(p for p in e["pasos"] if p.get("voz") == "central_ar")
    pjs = [
        {"id": "nico", **{k_: PERSONAJES["nico"][k_] for k_ in ("modelo", "alto_m", "vestuario")}, "acciones": nico,
         "cara": cara_escena(n, "nico", [(0.0, "confiado"), (t_fin_dialogo + 0.2, "picara")]),
         "arma_stickman": {"tipo": "fusil"}, "mochila": {"desde_s": 0.0}},
        {"id": "luna", **{k_: PERSONAJES["luna"][k_] for k_ in ("modelo", "alto_m", "vestuario")}, "acciones": luna,
         "cara": cara_escena(n, "luna", [(central["t_ini"] + 0.2, "concentrada"), (central["t_fin"], "sonrisa_suave"),
                                         (t_fin_dialogo + 0.4, "carinosa")]),
         "arma_stickman": {"tipo": "subfusil", "visible": [[central["t_fin"] + 0.3, dur]]},
         "en_mano": {"visible": [[0.0, central["t_fin"] + 0.3]]},
         "poses": [{"pose": "radio_boca", "inicio_s": max(0.0, radio_boca["t_ini"] - 0.35),
                    "dur_s": radio_boca["t_fin"] - radio_boca["t_ini"] + 0.5},
                   {"pose": "radio_mano", "inicio_s": radio_boca["t_fin"] + 0.15, "dur_s": central["t_fin"] - radio_boca["t_fin"]}],
         "mochila": {"desde_s": 0.0}},
    ]

    def sig(tid, movil, t0, t1, desp, obj_movil, obj_punto, plano, lente=45, retardo=0.25):
        return {"id": tid, "tipo": "seguimiento", "plano": plano, "inicio_s": t0, "duracion_s": t1 - t0, "movil": movil,
                "punto_base": "", "desp_local": desp, "objetivo": {"movil": obj_movil, "punto": obj_punto},
                "lente_mm": lente, "retardo": retardo, "luz_relleno": 25}
    tomas = [
        sig("t_luna_radio", "luna", 0.0, 2.24, [0.3, 1.8, 0.6], "luna", "cabeza", "Luna por radio: «Central, estamos en posición»"),
        {"id": "t_central", "tipo": "estatica", "plano": "la radio contesta con interferencia; Nico se acerca",
         "inicio_s": 2.24, "duracion_s": 1.65, "desde": [6.0, 16.5, 1.6], "objetivo": {"movil": "luna", "punto": "pecho"},
         "lente_mm": 28, "luz_relleno": 0},
        sig("t_nico_perfecto", "nico", 3.89, 6.08, [-0.3, 1.9, 0.6], "nico", "cabeza", "Nico: «¿Ves? Todo salió perfecto»"),
        sig("t_os_luna_tiros", "nico", 6.08, 10.0, [0.45, -0.85, 0.72], "luna", "cabeza",
            "Luna: «Acabamos de saltar de un tren en movimiento y nos recibieron a tiros»", 40),
        sig("t_nico_aca", "nico", 10.0, 10.82, [-0.3, 1.9, 0.6], "nico", "cabeza", "Nico: «Pero estamos acá»"),
        sig("t_luna_imposible", "luna", 10.82, 13.1, [0.3, 1.8, 0.6], "luna", "cabeza", "Luna se ríe: «Sos imposible»", 50),
        sig("t_nico_elegiste", "nico", 13.1, 15.86, [-0.35, 1.9, 0.62], "nico", "cabeza", "Nico: «Y aun así me elegiste como compañero»"),
        sig("t_luna_mira", "luna", 15.86, 16.54, [0.2, 1.45, 0.62], "luna", "cabeza", "Luna lo observa un instante", 85),
        sig("t_luna_acostumbres", "luna", 16.54, t_fin_dialogo, [0.3, 1.8, 0.6], "luna", "cabeza", "Luna: «No te acostumbres»", 50),
        {"id": "t_final", "tipo": "grua", "plano": "se van hacia la base; la cámara sube y aparece el título",
         "inicio_s": t_fin_dialogo, "duracion_s": 0.0,
         "desde": {"movil": "nico", "punto": "", "desp": [-5.5, -2.0, 0.6]},
         "hasta": [N1[0] - 30.0, N1[1] - 8.0, 26.0],
         "objetivo": [210.0, 60.0, 4.0], "lente_mm": 24,
         "montaje": {"efecto": "titulo", "lineas": ["DÚO CERO", "EPISODIO 01 — UN MINUTO PARA SALTAR"], "desde_s": 1.5}},
    ]
    encadenar(tomas, dur)
    son = sonido_dialogo(n, dur, musica="Warm, confident end-title theme, {d} seconds, no vocals: starts soft with a "
                         "hopeful guitar and strings under light banter, then at second 18 the full heroic action-series "
                         "theme with drums and brass rising as the camera lifts, ending on a strong final hit".format(
                             d=int(round(dur))),
                         extra=[{"tipo": "pasos", "t": [round(0.2 + 0.5 * k, 2) for k in range(8)] +
                                 [round(t_fin_dialogo + 0.2 + 0.5 * k, 2) for k in range(9)]}])
    son["eventos"] = [ev for ev in son["eventos"] if ev["tipo"] != "tren"]
    return {
        "tipo": "escena", "id": "p009_duo_cero-e06", "produccion": "p009_duo_cero", "numero": 6, "version": 1,
        "titulo": "Cierre y presentación de la misión",
        "guion": " ".join(_limpio(p["texto"]) for p in e["pasos"] if p.get("voz")) + " Título: DÚO CERO.",
        "duracion_s": dur,
        "escenario": {"id": "duo_cero_noche", "generador": "duo_cero",
                      "parametros": {"escena": n, "T0": e["T0"], "duracion_escena_s": dur, "T_salto": t_salto()}},
        "eventos": [], "vehiculos": [], "personajes": pjs, "tomas": tomas,
        "moviles_escenario": ["vagon", "loco", "cola"],
        "sonido": son,
        "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.6, "muestras": 6},
        "estado": "borrador", "bloqueada": False, "huella_v": 2,
    }


if __name__ == "__main__":
    pedidas = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5, 6]
    for n in pedidas:
        if n in (1, 2, 3):
            escribir(escena_dialogo(n))
        elif n == 4:
            escribir(escena_4())
        elif n == 5:
            escribir(escena_5())
        elif n == 6:
            escribir(escena_6())
