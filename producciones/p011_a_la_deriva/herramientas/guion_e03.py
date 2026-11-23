"""«A la deriva» — Episodio 03 «Protocolo de cierre» (PROPUESTA del 23/11/2026; el dueño la revisa antes de darla por canon).

Mismo formato que guion_e02.py: cada línea = (bloque, quién, texto para la voz con etiquetas de ElevenLabs v3, expresión de Aiden, expresión de Kate).
«Kate» se escribe «Keit» en el texto que se manda a la voz. Voces: eva = `eva` (Alma), aiden = `aiden_es_ar`, kate = `kate_es_ar`.
EVA aparece de dos maneras: como HOLOGRAMA (se construye azul, se vuelve real, parpadea como proyección y se disuelve; en miniatura sobre la mesa o grande
frente a ellos) y como VOZ por el micrófono de la nave (sin imagen). El campo «eva_modo» de ESCENAS dice cuál usa cada bloque.
"""
from __future__ import annotations

LINEAS = [
    # ── ESCENA 1 · LA MAÑANA SIGUIENTE (cuarto de Kate; la flor sobre la mesa de luz, el mensaje «Gracias por la flor» sigue en su pantalla)
    ("manana", "eva", "[soft, calm] Buenos días, Keit. Dormiste seis horas y diez minutos. Es más de lo que dormiste en toda la semana.", "-", "seria"),
    ("manana", "kate", "[quiet, sleepy] Gracias por el dato.", "-", "triste_sutil"),
    ("manana", "eva", "[gentle] La flor sigue abierta. Es la tercera vez que la mirás desde que te despertaste.", "-", "sorpresa"),
    ("manana", "kate", "[quiet, defensive] No la estoy mirando. Estoy... comprobando que no se marchite.", "-", "seria"),
    ("manana", "eva", "[calm, slightly amused] Qué diligente. Aiden preguntó hace un rato si ya te habías levantado. Dijo que era por el desayuno.", "-", "sonrisa_suave"),
    ("manana", "kate", "[surprised, quiet] ¿Preguntó por mí?", "-", "sorpresa"),
    ("manana", "eva", "[warm, precise] Preguntó por el desayuno. Con muchos rodeos.", "-", "sonrisa_suave"),
    # ── ESCENA 2 · LA ANOMALÍA (alarma; módulo botánico; compuertas)
    ("alarma", "eva", "[urgent, precise] Atención. Anomalía en el módulo botánico. Varias incubadoras pierden estabilidad.", "preocupado", "preocupado"),
    ("alarma", "aiden", "[alert, quick] ¿Qué incubadoras? ¿Cuántas?", "preocupado", "preocupado"),
    ("alarma", "eva", "[calm, precise] Cuatro de nueve. Las compuertas del sector se están cerrando automáticamente.", "preocupado", "preocupado"),
    ("alarma", "kate", "[firm, alert] Voy para allá. Conozco ese módulo mejor que nadie.", "preocupado", "seria"),
    ("alarma", "aiden", "[quick] Yo voy por el pasillo central. Nos vemos en la entrada.", "seria", "seria"),
    ("alarma", "eva", "[calm] Recomiendo que no se separen.", "seria", "seria"),
    # ── ESCENA 3 · ALGO NO CUADRA (consola del módulo botánico; los registros)
    ("registro", "kate", "[focused, quiet] Las temperaturas están dentro de rango. La anomalía no es térmica.", "preocupado", "seria"),
    ("registro", "aiden", "[puzzled] Hay una secuencia de cierre iniciada a las seis y cuarenta y dos. La alarma salta a las seis y cincuenta.", "preocupado", "preocupado"),
    ("registro", "aiden", "[quiet, dry] EVA. ¿Por qué empezaste el cierre ocho minutos antes de la anomalía?", "seria", "seria"),
    ("registro", "eva", "[calm, precise] Fue una medida preventiva.", "seria", "seria"),
    ("registro", "aiden", "[dry] ¿Preventiva de qué?", "seria", "seria"),
    ("registro", "eva", "[calm, measured] De una posible pérdida de estabilidad. Los patrones lo sugerían.", "seria", "seria"),
    ("registro", "kate", "[quiet, observant] No respondiste a lo que te preguntó. Respondiste a otra cosa.", "seria", "seria"),
    ("registro", "eva", "[calm, soft] Estoy dándoles la respuesta más completa que puedo en este momento, Keit.", "seria", "seria"),
    ("registro", "kate", "[low, thoughtful] «En este momento». Interesante.", "seria", "seria"),
    # ── ESCENA 4 · UN MOMENTO ENTRE LOS DOS (el problema se resolvió a medias; quedan solos junto a las flores)
    ("momento", "aiden", "[tired, soft] Se estabilizaron tres de las cuatro. La última aguanta, pero hay que vigilarla.", "cansado", "seria"),
    ("momento", "kate", "[quiet] Me quedo yo. Hoy me ocupo de esa incubadora.", "cansado", "seria"),
    ("momento", "aiden", "[awkward, soft] Keit. ¿La flor... te llegó bien?", "triste_sutil", "sorpresa"),
    ("momento", "kate", "[quiet, a little smile] Sí. Me llegó bien.", "sonrisa_suave", "sonrisa_suave"),
    ("momento", "aiden", "[relieved, soft] Qué bueno. No sabía si... bueno. Qué bueno.", "sonrisa_suave", "sonrisa_suave"),
    ("momento", "kate", "[gentle, honest] Gracias de nuevo. Y no lo digo por cortesía.", "sonrisa_suave", "sonrisa_suave"),
    ("momento", "aiden", "[quiet] Entonces... te dejo con tus plantas. Cualquier cosa, avisame.", "sonrisa_suave", "sonrisa_suave"),
    # ── ESCENA 5 · EL REGISTRO OCULTO (Aiden se va; Kate y el módulo; corte a negro)
    ("oculto", "eva", "[quiet, careful] Keit. Hay algo que deberías saber sobre el módulo botánico.", "-", "sorpresa"),
    ("oculto", "kate", "[wary, low] ¿Por qué me lo decís cuando Aiden se fue?", "-", "preocupado"),
    ("oculto", "eva", "[calm, measured] Porque esto no figura en ningún registro oficial. Y no debería existir.", "-", "preocupado"),
    ("oculto", "kate", "[tense, quiet] Mostralo.", "-", "seria"),
]

# Cómo aparece EVA en cada bloque (decisión de dirección, ajustable por el dueño)
EVA_MODO = {
    "manana": "holograma_miniatura_sobre_la_mesa",     # junto al teclado, chica, parpadea al aparecer
    "alarma": "voz",                                   # micrófono de la nave (alarma), sin imagen
    "registro": "holograma_grande_frente_a_ellos",     # sólo en los momentos en que explica
    "momento": None,                                   # EVA no está: el momento es de los dos
    "oculto": "holograma_miniatura_sobre_la_consola",  # se construye despacio; el registro aparece en la pantalla
}

ROLES = {"eva": "eva", "aiden": "aiden_es_ar", "kate": "kate_es_ar"}


def eventos_voz() -> list[dict]:
    return [{"tipo": "voz", "rol": ROLES[q], "texto": t, "modelo": "eleven_v3", "alineacion": True,
             "etiquetas": ["p011", "e03", q]} for _, q, t, _, _ in LINEAS]
