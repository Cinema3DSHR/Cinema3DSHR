"""Guion de «Dúo Cero — Episodio 01: Un minuto para saltar» como datos (lo leen las recetas e01…e06).

Cada escena es una lista ordenada de pasos:
  {"voz": rol, "texto": "...", "cara": expr mientras habla, "oye": expr de quien escucha, "pausa": s antes}
  {"pausa": s, "nota": "..."}                      silencio actuado (miradas, sonrisas)
  {"accion": nombre, "dur": s}                      momento sin diálogo que la receta resuelve (salto, tiroteo…)
Las etiquetas entre corchetes son instrucciones de actuación de ElevenLabs v3 (no se leen en voz alta).
Rol de voz = config/voces.json («nico», «luna», «guardia», «central_ar»).
"""

ESCENAS = {
    1: [
        {"accion": "aerea_tren", "dur": 4.6},
        {"voz": "luna", "texto": "[firm] Bien. Repasemos la misión una última vez.", "cara": "concentrada", "oye": "neutral", "pausa": 0.0},
        {"voz": "nico", "texto": "[sarcastic] ¿Otra vez? Creo que ya la escuché unas... [sighs] siete veces.", "cara": "picara",
         "oye": "seria", "pausa": 0.35},
        {"voz": "luna", "texto": "[deadpan] Ocho. Y parece que todavía no entendiste.", "cara": "ironica", "oye": "sorpresa", "pausa": 0.3},
        {"voz": "nico", "texto": "[confident] Entendí perfectamente. Entramos, recuperamos el dispositivo y salimos. [proud] ¿Ves? Soy un alumno excelente.",
         "cara": "confiado", "oye": "incredula", "pausa": 0.35},
        {"pausa": 0.9, "nota": "Luna lo mira con incredulidad"},
        {"voz": "luna", "texto": "[dry] Me preocupa muchísimo que estés hablando en serio.", "cara": "incredula", "oye": "sonrisa", "pausa": 0.0},
        {"voz": "nico", "texto": "[playful] A mí me preocupa que no confíes en mí.", "cara": "picara", "oye": "ironica", "pausa": 0.3},
        {"voz": "luna", "texto": "[flat] Tengo motivos.", "cara": "ironica", "oye": "sonrisa", "pausa": 0.35},
        {"pausa": 1.6, "nota": "Nico sonríe"},
    ],
    2: [
        {"voz": "luna", "texto": "[focused] La instalación está a unos kilómetros. El tren pasa junto a la zona de carga. Tenemos una ventana de entrada muy corta.",
         "cara": "concentrada", "oye": "neutral", "pausa": 0.6},
        {"voz": "nico", "texto": "[curious] ¿Cuánto?", "cara": "neutral", "oye": "seria", "pausa": 0.3},
        {"voz": "luna", "texto": "Un minuto.", "cara": "seria", "oye": "sorpresa", "pausa": 0.3},
        {"voz": "nico", "texto": "[grinning] Perfecto.", "cara": "picara", "oye": "incredula", "pausa": 0.4},
        {"voz": "luna", "texto": "[exasperated] No es perfecto. Tenemos que saltar, llegar al perímetro, evitar las patrullas y entrar por el sector norte.",
         "cara": "enojo", "oye": "confiado", "pausa": 0.2},
        {"voz": "nico", "texto": "[curious] ¿Y si entramos por el sur?", "cara": "picara", "oye": "incredula", "pausa": 0.4},
        {"voz": "luna", "texto": "El sur tiene tres puestos de vigilancia.", "cara": "seria", "oye": "confiado", "pausa": 0.3},
        {"voz": "nico", "texto": "[smug] Entonces van a estar muy entretenidos.", "cara": "picara", "oye": "incredula", "pausa": 0.3},
        {"pausa": 1.0, "nota": "Luna lo mira fijamente"},
        {"voz": "luna", "texto": "[sighs] Nico, por favor, esta vez sigamos el plan.", "cara": "preocupada", "oye": "neutral", "pausa": 0.0},
        {"voz": "nico", "texto": "Siempre sigo el plan.", "cara": "confiado", "oye": "incredula", "pausa": 0.3},
        {"voz": "luna", "texto": "[sarcastic] Tu concepto de seguir un plan es bastante particular.", "cara": "ironica", "oye": "picara", "pausa": 0.3},
        {"voz": "nico", "texto": "[chuckles] Pero funciona.", "cara": "sonrisa", "oye": "seria", "pausa": 0.3},
        {"pausa": 1.8, "nota": "Luna intenta seguir seria y termina sonriendo"},
    ],
    3: [
        {"voz": "nico", "texto": "[clears throat] Central, aquí Nico. Prueba de comunicaciones.", "cara": "concentrada", "oye": "neutral",
         "pausa": 0.5, "radio": "mano"},
        {"accion": "interferencia", "dur": 0.9},
        {"voz": "luna", "texto": "Todavía no estamos en la zona.", "cara": "ironica", "oye": "neutral", "pausa": 0.1},
        {"voz": "nico", "texto": "Estoy comprobando que funcione.", "cara": "confiado", "oye": "incredula", "pausa": 0.3},
        {"voz": "luna", "texto": "[dry] La comprobaste hace diez minutos.", "cara": "incredula", "oye": "picara", "pausa": 0.25},
        {"voz": "nico", "texto": "Y ahora quiero comprobar que siga funcionando.", "cara": "picara", "oye": "incredula", "pausa": 0.3},
        {"voz": "nico", "texto": "[whispers] ¿Luna? ¿Me recibís?", "cara": "picara", "oye": "incredula", "pausa": 0.5, "radio": "boca"},
        {"voz": "luna", "texto": "[annoyed] Estoy a veinte centímetros. Te escucho perfectamente.", "cara": "incredula", "oye": "sonrisa",
         "pausa": 0.3},
        {"voz": "nico", "texto": "Excelente. Comunicación impecable.", "cara": "sonrisa", "oye": "risa", "pausa": 0.25},
        {"voz": "luna", "texto": "[laughs] Ja... ja.", "cara": "risa", "oye": "sonrisa", "pausa": 0.1},
        {"pausa": 1.3, "nota": "silencio"},
        {"voz": "nico", "texto": "[softly] ¿Estás nerviosa?", "cara": "carinosa_nico", "oye": "neutral", "pausa": 0.0},
        {"voz": "luna", "texto": "No.", "cara": "seria", "oye": "picara", "pausa": 0.35},
        {"voz": "nico", "texto": "[teasing] Mentira.", "cara": "picara", "oye": "avergonzada", "pausa": 0.3},
        {"voz": "luna", "texto": "¿Y vos?", "cara": "neutral", "oye": "neutral", "pausa": 0.3},
        {"voz": "nico", "texto": "¿Yo? [excited] Estoy deseando llegar.", "cara": "confiado", "oye": "carinosa", "pausa": 0.3},
        {"pausa": 1.2, "nota": "Luna lo observa unos segundos"},
        {"voz": "luna", "texto": "[warmly] Algún día vas a conseguir que me dé un infarto.", "cara": "carinosa", "oye": "sonrisa_suave", "pausa": 0.0},
        {"voz": "nico", "texto": "[gently] Pero hoy no. Hoy tenemos trabajo.", "cara": "sonrisa_suave", "oye": "avergonzada", "pausa": 0.35},
        {"pausa": 1.4, "nota": "Luna baja la mirada y sonríe"},
    ],
    4: [
        {"accion": "acercamiento_base", "dur": 3.0},
        {"voz": "luna", "texto": "[focused] Dos minutos.", "cara": "concentrada", "oye": "decidido", "pausa": 0.0},
        {"accion": "preparar", "dur": 1.6},
        {"voz": "luna", "texto": "Esperá mi señal.", "cara": "seria", "oye": "picara", "pausa": 0.2},
        {"voz": "nico", "texto": "[innocent] Por supuesto.", "cara": "picara", "oye": "incredula", "pausa": 0.3},
        {"voz": "luna", "texto": "[stern] Lo digo en serio.", "cara": "enojo", "oye": "confiado", "pausa": 0.3},
        {"voz": "nico", "texto": "Yo también.", "cara": "confiado", "oye": "preocupada", "pausa": 0.3},
        {"accion": "se_acerca_la_zona", "dur": 2.4},
        {"voz": "luna", "texto": "[tense] Treinta segundos.", "cara": "concentrada", "oye": "decidido", "pausa": 0.0},
        {"accion": "preparados", "dur": 1.8},
        {"voz": "luna", "texto": "[counting, tense] Diez... nueve... ocho...", "cara": "concentrada", "oye": "picara", "pausa": 0.0},
        {"voz": "luna", "texto": "[alarmed] ¡Nico, esperá!", "cara": "sorpresa", "oye": "picara", "pausa": 0.05},
        {"voz": "nico", "texto": "[shouting, excited] ¡Vamos!", "cara": "grito", "oye": "sorpresa", "pausa": 0.0},
        {"accion": "salto", "dur": 5.5},
    ],
    5: [
        {"accion": "tren_se_aleja", "dur": 1.6},
        {"voz": "luna", "texto": "[breathless] ¿Estás bien?", "cara": "preocupada", "oye": "neutral", "pausa": 0.0},
        {"voz": "nico", "texto": "[cheerful] Como nuevo.", "cara": "sonrisa", "oye": "preocupada", "pausa": 0.3},
        {"voz": "luna", "texto": "[annoyed] ¿Podrías haber esperado mi señal?", "cara": "enojo", "oye": "picara", "pausa": 0.3},
        {"voz": "nico", "texto": "Técnicamente, la escuché.", "cara": "picara", "oye": "incredula", "pausa": 0.3},
        {"voz": "luna", "texto": "[exasperated] ¡Nico!", "cara": "enojo", "oye": "sonrisa", "pausa": 0.2},
        {"voz": "nico", "texto": "[innocent] ¿Qué? Dijiste que esperara tu señal. No dijiste cuánto.", "cara": "picara", "oye": "incredula",
         "pausa": 0.2},
        {"pausa": 1.0, "nota": "Luna niega con la cabeza, sonriendo"},
        {"voz": "guardia", "texto": "[shouting] ¡Eh! ¿Quién anda ahí?", "pausa": 0.2},
        {"accion": "tiroteo", "dur": 12.5},
    ],
    6: [
        {"voz": "luna", "texto": "Central, estamos en posición.", "cara": "concentrada", "oye": "neutral", "pausa": 0.6, "radio": "boca"},
        {"voz": "central_ar", "texto": "Recibido, Dúo Cero. Adelante.", "pausa": 0.3, "filtro_radio": True},
        {"voz": "nico", "texto": "[smug] ¿Ves? Todo salió perfecto.", "cara": "confiado", "oye": "incredula", "pausa": 0.3},
        {"voz": "luna", "texto": "[incredulous] Acabamos de saltar de un tren en movimiento y nos recibieron a tiros.", "cara": "incredula",
         "oye": "picara", "pausa": 0.2},
        {"voz": "nico", "texto": "Pero estamos acá.", "cara": "sonrisa", "oye": "sonrisa_suave", "pausa": 0.3},
        {"voz": "luna", "texto": "[laughs softly] Sos imposible.", "cara": "sonrisa", "oye": "picara", "pausa": 0.3},
        {"voz": "nico", "texto": "[playful] Y aun así me elegiste como compañero.", "cara": "picara", "oye": "avergonzada", "pausa": 0.3},
        {"pausa": 0.9, "nota": "Luna lo observa un instante"},
        {"voz": "luna", "texto": "[smiling] No te acostumbres.", "cara": "carinosa", "oye": "risa", "pausa": 0.0},
        {"accion": "caminan_y_titulo", "dur": 5.0},
    ],
}

# expresiones que no están en el catálogo base del Stickman
EXPR_EXTRA = {"carinosa_nico": "sonrisa_suave"}


def personaje_de_rol(rol: str) -> str | None:
    return {"nico": "nico", "luna": "luna"}.get(rol)


# ------------------------------------------------------------------------------------------------ tiempos reales
DURACION_TOTAL = 180.0
# cámara lenta del salto (escena 4): desde t (película), `pelicula` s de pantalla muestran `contenido` s de acción
CAMARA_LENTA = {4: {"t": 20.0, "pelicula": 2.6, "contenido": 1.1}}
MINIMOS = {"salto": 5.5, "tiroteo": 11.0, "caminan_y_titulo": 4.6, "aerea_tren": 3.4}
SOLAPE = 0.12                    # interrupciones naturales en los intercambios rápidos


def _voz_ev(p: dict) -> dict:
    return {"tipo": "voz", "rol": p["voz"], "texto": p["texto"]}


def recorte(p: dict) -> tuple[float, float, float]:
    """(inicio, fin, largo del archivo) del habla dentro del mp3 de ElevenLabs (sin el silencio de los bordes)."""
    import numpy as np
    from estudio.audio import elevenlabs as EL
    from estudio.audio.procedural import _decodificar
    clave = (p["voz"], p["texto"])
    if clave not in _RECORTES:
        x = _decodificar(EL.ruta_en_biblioteca(_voz_ev(p)))
        if x.ndim > 1:
            x = x.mean(1)
        hop = 480
        fr = x[: len(x) // hop * hop].reshape(-1, hop)
        e = np.sqrt((fr ** 2).mean(1))
        act = np.nonzero(e > max(e.max() * 0.04, 1e-4))[0]
        ini = max(0.0, act[0] * hop / 48000 - 0.05)
        fin = min(len(x) / 48000, (act[-1] + 1) * hop / 48000 + 0.08)
        _RECORTES[clave] = (ini, fin, len(x) / 48000)
    return _RECORTES[clave]


_RECORTES: dict = {}


def _natural(n: int, k_pausa: float = 1.0) -> tuple[list, float]:
    pasos = ESCENAS[n]
    t = 0.0
    out = []
    previo = None
    for p in pasos:
        pausa = p.get("pausa", 0.0) * k_pausa
        if p.get("voz"):
            ini, fin, _ = recorte(p)
            rapido = previo is not None and previo.get("voz") and previo["voz"] != p["voz"] and p.get("pausa", 0.0) <= 0.3
            t0 = t + pausa - (SOLAPE if rapido else 0.0)
            item = {**p, "t_ini": t0, "t_fin": t0 + (fin - ini), "inicio_s": t0 - ini, "recorte_s": [ini, fin]}
            t = item["t_fin"]
        elif p.get("accion"):
            dur = max(MINIMOS.get(p["accion"], 0.0), p["dur"] * k_pausa)
            item = {**p, "t_ini": t, "t_fin": t + dur}
            t += dur
        else:
            item = {**p, "t_ini": t, "t_fin": t + pausa}
            t += pausa
        out.append(item)
        previo = p
    return out, t


def plan() -> dict:
    """Tiempos de todas las escenas: {n: {"pasos": [...], "duracion_s": d, "T0": inicio en el episodio}} (suma 180 s)."""
    if "plan" in _RECORTES:
        return _RECORTES["plan"]
    lo, hi = 0.2, 2.0
    for _ in range(40):                     # bisección del factor de pausas para clavar los 180 s
        k = (lo + hi) / 2
        tot = sum(_natural(n, k)[1] for n in ESCENAS)
        if tot > DURACION_TOTAL:
            hi = k
        else:
            lo = k
    k = lo
    res, T0 = {}, 0.0
    durs = {n: _natural(n, k)[1] for n in ESCENAS}
    resto = DURACION_TOTAL - sum(round(d * 30) / 30 for d in durs.values())
    for i, n in enumerate(ESCENAS):
        pasos, d = _natural(n, k)
        d = round(d * 30) / 30
        if i == len(ESCENAS) - 1:
            d += resto
        cl = CAMARA_LENTA.get(n)
        contenido = d - (cl["pelicula"] - cl["contenido"]) if cl else d
        res[n] = {"pasos": pasos, "duracion_s": round(d, 4), "T0": round(T0, 4), "k_pausa": k,
                  "contenido_s": round(contenido, 4), "camara_lenta": cl}
        T0 += contenido
    _RECORTES["plan"] = res
    return res


def a_escena(n: int, t: float) -> float:
    """Tiempo de película → tiempo de la escena (el contenido), teniendo en cuenta la cámara lenta."""
    cl = CAMARA_LENTA.get(n)
    if not cl or t <= cl["t"]:
        return t
    if t <= cl["t"] + cl["pelicula"]:
        return cl["t"] + (t - cl["t"]) * cl["contenido"] / cl["pelicula"]
    return t - (cl["pelicula"] - cl["contenido"])


def mapa_tiempo(n: int, dur: float):
    cl = CAMARA_LENTA.get(n)
    if not cl:
        return None
    return [[0.0, 0.0], [cl["t"], cl["t"]], [cl["t"] + cl["pelicula"], cl["t"] + cl["contenido"]],
            [dur, a_escena(n, dur)]]


def a_pelicula(n: int, t: float) -> float:
    """Inversa de a_escena: tiempo de la escena → tiempo de película."""
    cl = CAMARA_LENTA.get(n)
    if not cl or t <= cl["t"]:
        return t
    if t <= cl["t"] + cl["contenido"]:
        return cl["t"] + (t - cl["t"]) * cl["pelicula"] / cl["contenido"]
    return t + (cl["pelicula"] - cl["contenido"])
