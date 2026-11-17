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
             "vestuario": {"estilo": "tactico", "pelo": "puntas", "color_pelo": [0.20, 0.09, 0.03]},
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
        tramos.append((t, clip, (turno * 7.3) % 20.0 if "Talking" in clip else 0.0))
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
    "dos": ((1.25, 0.0, PISO + 1.15), (-0.95, 0.0, PISO + 1.25), 22),
    "cu_nico": ((0.25, 0.30, PISO + 1.38), (-0.93, -0.48, PISO + 1.42), 50),
    "cu_luna": ((0.25, -0.30, PISO + 1.35), (-0.93, 0.48, PISO + 1.36), 50),
    "os_nico": ((-0.30, 1.30, PISO + 1.46), (-0.93, -0.48, PISO + 1.40), 32),
    "os_luna": ((-0.30, -1.30, PISO + 1.50), (-0.93, 0.48, PISO + 1.34), 32),
    "ecu_nico": ((0.55, -0.42, PISO + 1.43), (-0.93, -0.48, PISO + 1.46), 95),
    "ecu_luna": ((0.55, 0.42, PISO + 1.38), (-0.93, 0.48, PISO + 1.40), 95),
    "exterior": ((6.5, -3.4, PISO + 0.55), (-0.9, 0.0, PISO + 1.2), 30),
    "exterior_cerca": ((3.4, 1.6, PISO + 1.0), (-0.9, -0.1, PISO + 1.25), 24),
    "farol": ((0.25, -1.05, PISO + 1.45), (-1.0, -1.9, PISO + 1.15), 42),
    "radio": ((0.05, 1.05, PISO + 0.95), (-0.55, 1.75, PISO + 0.62), 55),
    "tableta": ((-0.38, 0.30, PISO + 1.30), (-0.70, 0.48, PISO + 0.80), 45),
    "techo": ((0.55, 0.05, PISO + 2.55), (-0.95, 0.0, PISO + 1.0), 16),
    "puerta_afuera": ((-0.5, -0.9, PISO + 1.3), (3.0, 0.4, PISO + 1.0), 24),
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
    base = [{"tipo": "tren", "movil": "vagon", "volumen": 0.55}]
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
        extras = [(0.0, "tableta", "la tableta: el mapa de la instalación"), (14.5, "tableta", "el mapa: sector norte y patrullas")]
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
                      "parametros": {"escena": n, "T0": e["T0"], "duracion_escena_s": dur, "T_salto": t_salto()}},
        "eventos": [], "vehiculos": [], "personajes": pjs, "tomas": tomas,
        "moviles_escenario": ["vagon", "loco", "cola"],
        "sonido": sonido_dialogo(n, dur, musica=MUSICA[n].format(d=int(round(dur)))),
        "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.6, "muestras": 6},
        "estado": "borrador", "bloqueada": False, "huella_v": 2,
    }


def t_salto():
    e4 = PLAN[4]
    salto = next(p for p in e4["pasos"] if p.get("accion") == "salto")
    return round(e4["T0"] + salto["t_ini"], 3)


def escribir(m):
    n = m["numero"]
    salida = RAIZ / f"producciones/p009_duo_cero/escenas/e{n:02d}/v1/escena.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(m, ensure_ascii=False, indent=1))
    print("escrito", salida.relative_to(RAIZ), len(m["tomas"]), "tomas,", m["duracion_s"], "s")


if __name__ == "__main__":
    pedidas = [int(a) for a in sys.argv[1:]] or [1, 2, 3]
    for n in pedidas:
        if n in (1, 2, 3):
            escribir(escena_dialogo(n))
