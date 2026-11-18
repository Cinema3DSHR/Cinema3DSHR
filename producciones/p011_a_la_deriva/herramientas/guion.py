"""«A la deriva» — Episodio 01 (documento de producción v1.1 del dueño, 18/11/2026) como datos.

60 s exactos (1.800 cuadros a 30 fps), vertical 9:16. Las líneas llevan la etiqueta de actuación de ElevenLabs v3 y la
expresión de la cara de Aiden. «Kate» se escribe «Keit» en el texto que se manda a la voz (así lo pronuncian).
`plan()` ubica cada línea con su duración REAL (las voces ya generadas) respetando los bloques del documento.
"""
from __future__ import annotations

DURACION_S = 60.0

# (bloque, quién, texto para la voz, expresión de Aiden mientras dura la línea)
LINEAS = [
    ("eva", "eva", "[calm] Aiden. ¿Sigues despierto?", "cansado"),
    ("eva", "aiden", "[tired, dry] ¿Qué te parece?", "cansado"),
    ("eva", "eva", "[calm, precise] Tus constantes indican que llevas treinta y una horas sin dormir. "
                   "¿Quieres que vuelva a preguntarte si estás bien?", "cansado"),
    ("eva", "aiden", "[flat, tired] No hace falta.", "seria"),
    ("realidad", "eva", "[calm, precise] He recalculado la trayectoria otras cuatrocientas doce veces. "
                        "No existe una solución viable de retorno.", "preocupado"),
    ("realidad", "aiden", "[quiet] ¿Por el combustible?", "preocupado"),
    ("realidad", "eva", "[precise, matter-of-fact, fast] Combustible insuficiente, velocidad relativa incompatible y "
                        "ninguna ventana de transferencia que podamos alcanzar. Incluso con una maniobra de asistencia "
                        "gravitatoria, el delta-v requerido supera nuestra capacidad. La probabilidad de regresar es "
                        "inferior al margen de error de los sensores.", "preocupado"),
    ("realidad", "aiden", "[tired, dry] Entonces deja de calcularlo.", "seria"),
    ("kate", "eva", "[calm] Puedo dejar de mostrarte los resultados. No puedo cambiar las ecuaciones.", "triste_sutil"),
    ("kate", "aiden", "[pause] [tired, softly] ¿Por qué no hablas con Keit? A lo mejor ella todavía quiere escuchar a "
                      "alguien. [sighs] Es la única interacción humana que voy a tener hasta que me muera.", "triste"),
    ("kate", "eva", "[calm, precise] Keit lleva nueve días sin responder a tus mensajes.", "triste"),
    ("gancho", "eva", "[calm] Puedo abrir el canal.", "triste"),
    ("gancho", "aiden", "[quiet, firm] No. Déjala.", "triste"),
    ("gancho", "eva", "[calm, slightly bold] Entendido. Aunque, estadísticamente, el aislamiento no está mejorando tu "
                      "estado.", "triste"),
]

# bloques del documento (segundos)
BLOQUES = {"universo": (0.0, 8.0), "eva": (8.0, 18.0), "realidad": (18.0, 34.0), "kate": (34.0, 48.0),
           "gancho": (48.0, 60.0)}
ROLES = {"eva": "eva", "aiden": "aiden_es_ar"}


def eventos_voz() -> list[dict]:
    return [{"tipo": "voz", "rol": ROLES[q], "texto": t, "modelo": "eleven_v3", "alineacion": True,
             "etiquetas": ["p011", "e01", q]} for _, q, t, _ in LINEAS]


def plan(duraciones: list[float], pausa: float = 0.35, inicio: float = 8.4, fin_dialogo: float = 56.0) -> list[float]:
    """Inicio de cada línea: arranca en el bloque EVA y encadena con pausas cortas; si sobra tiempo se reparten
    pausas más largas (silencios, como pide el documento); si falta, se achican hasta 0,15 s."""
    n = len(duraciones)
    total = sum(duraciones)
    libre = fin_dialogo - inicio - total
    p = max(0.15, min(1.6, libre / max(1, n - 1))) if libre > 0 else 0.15
    t, out = inicio, []
    for d in duraciones:
        out.append(round(t, 3))
        t += d + p
    return out
