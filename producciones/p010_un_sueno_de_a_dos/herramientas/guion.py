"""Guion de «Un sueño de a dos — Episodio 01» como datos (del texto del dueño, 18/11/2026).

60 s, vertical 9:16, 30 fps. Cinco momentos; cada línea con quién la dice, cómo (dirección de actuación) y la
emoción de la cara (expresiones de estudio/blender/stickman.py, usadas por los rostros de cara_anime.py).
Las voces se eligen entre las muestras (config/voces.json, roles *_es_ar) y se generan recién con el OK del dueño.
"""
DURACION_S = 60.0
TEXTO_FINAL = "Los sueños se disfrutan más cuando alguien camina a tu lado"

ESCENAS = [
    {"id": "s1", "titulo": "El sueño", "inicio_s": 0.0, "fin_s": 10.0,
     "accion": "Exterior de la concesionaria al atardecer. Él frente a la vidriera mira el auto con admiración, "
               "recorre los detalles y baja un poco la mirada: lo desea, pero está lejos.",
     "sonido": "calle, autos que pasan, música instrumental muy suave", "lineas": [],
     "caras": {"el": [(0.0, "neutral"), (2.5, "carinosa"), (7.5, "preocupada", 0.45)]}},
    {"id": "s2", "titulo": "Su llegada", "inicio_s": 10.0, "fin_s": 19.0,
     "accion": "Ella llega caminando por detrás con dos helados. Él apenas sonríe sin dejar de mirar el auto. Ella "
               "mira su cara y después la vidriera.",
     "lineas": [("ella", "Amor, mirá lo que te traje... ¡tu sabor favorito!", "alegre, voz cálida", "sonrisa"),
                ("ella", "Amor... ¿estás bien?", "suave, atenta", "preocupada")],
     "caras": {"el": [(0.0, "sonrisa_suave", 0.4)]}},
    {"id": "s3", "titulo": "Una ilusión pendiente", "inicio_s": 19.0, "fin_s": 29.0,
     "accion": "Primer plano de él. Pausa. Ella lo mira con ternura.",
     "lineas": [("el", "Sí... Es que me encantaría tener uno así algún día.", "sereno, un poquito triste",
                 "preocupada"),
                ("el", "Pero todavía falta mucho.", "más bajo, sin dramatizar", "preocupada")],
     "caras": {"ella": [(0.0, "carinosa")]}},
    {"id": "s4", "titulo": "Ella cree en él", "inicio_s": 29.0, "fin_s": 47.0,
     "accion": "Ella se acerca y le toma la mano. Él la mira.",
     "lineas": [("ella", "Ay, amor... si yo sé cuánto lo soñás. Por eso estamos ahorrando juntos, ¿te acordás?",
                 "dulce, sincera", "carinosa"),
                ("ella", "No te preocupes. Vamos de a poquito. No tenemos que conseguirlo todo hoy. Yo creo en vos y "
                         "voy a estar a tu lado para apoyarte.", "segura y tierna", "sonrisa_suave")],
     "caras": {"el": [(0.0, "preocupada", 0.4), (12.0, "sonrisa_suave")]}},
    {"id": "s5", "titulo": "Un sueño compartido", "inicio_s": 47.0, "fin_s": 60.0,
     "accion": "Él sonríe. Ella se ríe un poquito. Ríen los dos. Ella lo toma del brazo y caminan; él mira el auto "
               "una última vez, sonriendo. Plano final: sus reflejos juntos en la vidriera. Fundido a negro y texto.",
     "lineas": [("el", "Gracias, amor. No sé qué haría sin vos.", "sonrisa pequeña y auténtica", "carinosa"),
                ("ella", "Bueno, entonces empezá por comerte el helado antes de que se derrita.", "risueña",
                 "sonrisa")],
     "caras": {"el": [(6.0, "risa", 0.6)], "ella": [(6.0, "risa", 0.7)]}},
]

DIRECCION = {
    "el": "Voz masculina serena y natural; tristeza muy sutil al comienzo; sonrisa chica y auténtica al final. "
          "Sin llanto ni dramatización.",
    "ella": "Voz femenina cálida, dulce y cercana; conversación espontánea, como una pareja real; ternura sin "
            "exagerar.",
    "musica": "Guitarra acústica y piano, instrumental, original, volumen bajo debajo de los diálogos.",
    "ambiente": "Tránsito lejano, calle, ambiente discreto de la concesionaria.",
    "visual": "Atardecer cálido, reflejos en la vidriera, planos medios, primeros planos y detalles; gestos chicos.",
}
