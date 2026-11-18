"""«A la deriva» — Episodio 02 «Una flor en el vacío» (Documento Maestro v2 del dueño, 18/11/2026) como datos.

Vertical 9:16, objetivo 2:00 pero manda el largo REAL de los diálogos (el dueño: «si los diálogos hacen que se alargue,
no hay drama»). Cada línea: (bloque, quién, texto para la voz con etiquetas de actuación de ElevenLabs v3, expresión de
Aiden, expresión de Kate). «Kate» se escribe «Keit» en el texto que se manda a la voz (así lo pronuncian).
"""
from __future__ import annotations

LINEAS = [
    # 00:00 · LA VE EN EL MONITOR (Aiden sentado en el centro de operaciones, EVA en los altavoces)
    ("monitor", "eva", "[calm] Keit está en el comedor.", "cansado", "triste_sutil"),
    ("monitor", "aiden", "[tired, dry] ¿Y?", "cansado", "triste_sutil"),
    ("monitor", "eva", "[calm] Lleva un rato ahí. Está sola.", "triste_sutil", "triste_sutil"),
    ("monitor", "aiden", "[tired, quietly] No sé qué querés que haga.", "triste_sutil", "triste_sutil"),
    ("monitor", "eva", "[gentle, precise] Podrías sentarte con ella. No tenés que solucionar nada. "
                       "Solo compartir un momento.", "preocupado", "triste_sutil"),
    # 00:16 · EL TRAYECTO (se levanta y camina por el pasillo)
    ("trayecto", "aiden", "[quiet, unsure] No creo que quiera verme.", "triste_sutil", "triste_sutil"),
    ("trayecto", "eva", "[calm] No podés saberlo si nunca lo intentás.", "triste_sutil", "triste_sutil"),
    ("trayecto", "aiden", "[dry, ironic] Tu insistencia empieza a parecer humana.", "seria", "triste_sutil"),
    ("trayecto", "eva", "[slightly amused] Lo tomaré como un cumplido.", "seria", "triste_sutil"),
    ("trayecto", "aiden", "[dry] Era una crítica.", "seria", "triste_sutil"),
    ("trayecto", "eva", "[calm, bold] Lo sé.", "sonrisa_suave", "triste_sutil"),
    # 00:39 · EL PASILLO DE LAS FLORES
    ("flores", "aiden", "[softly, surprised] No recordaba que hubiera tantas flores.", "sorpresa", "triste_sutil"),
    ("flores", "eva", "[calm, warm] El módulo botánico sigue funcionando. Algunas cosas todavía crecen aquí.",
     "sonrisa_suave", "triste_sutil"),
    ("flores", "aiden", "[quiet, moved] No pensé que quedara algo tan... vivo.", "sonrisa_suave", "triste_sutil"),
    ("flores", "eva", "[gentle] Hay más cosas vivas de las que mirás, Aiden.", "triste_sutil", "triste_sutil"),
    # 01:10 · LA FLOR SOBRE LA MESA (comedor)
    ("mesa", "aiden", "[awkward, soft] Hola.", "triste_sutil", "seria"),
    ("mesa", "kate", "[quiet, guarded] Hola.", "triste_sutil", "seria"),
    ("mesa", "aiden", "[awkward, soft] Te traje esto.", "triste_sutil", "seria"),
    ("mesa", "aiden", "[hesitant, sincere, quiet] Perdón por todo esto. No sé cómo arreglar lo que nos pasó... "
                      "pero voy a intentar que las cosas no sigan así.", "triste", "seria"),
    ("mesa", "aiden", "[soft] No hace falta que digas nada. Te dejo tranquila.", "triste_sutil", "seria"),
    ("mesa", "aiden", "[quiet] Que estés bien.", "triste_sutil", "seria"),
    # 01:38 · EVA NO LO DEJA ESCAPAR (pasillo, alejándose del comedor)
    ("pasillo", "eva", "[calm, teasing] ¿Vas a seguir fingiendo que no te importa?", "seria", "seria"),
    ("pasillo", "aiden", "[tired, annoyed] No empieces.", "enojado", "seria"),
    ("pasillo", "eva", "[precise, bold] No es realista. Te gusta Keit. ¿Por qué no aceptás lo que sentís y se lo decís?",
     "preocupado", "seria"),
    ("pasillo", "aiden", "[quiet] Porque no sé si ella quiere escuchar eso.", "triste", "seria"),
    ("pasillo", "eva", "[calm] Podrías averiguarlo.", "triste_sutil", "seria"),
    ("pasillo", "aiden", "[dry, tired] No todo se resuelve con un cálculo.", "seria", "seria"),
    ("pasillo", "eva", "[warm] Disculpame. Solo intento ayudarte. [soft brief laugh]", "sonrisa_suave", "seria"),
]

ROLES = {"eva": "eva", "aiden": "aiden_es_ar", "kate": "kate_es_ar"}


def eventos_voz() -> list[dict]:
    return [{"tipo": "voz", "rol": ROLES[q], "texto": t, "modelo": "eleven_v3", "alineacion": True,
             "etiquetas": ["p011", "e02", q]} for _, q, t, _, _ in LINEAS]
