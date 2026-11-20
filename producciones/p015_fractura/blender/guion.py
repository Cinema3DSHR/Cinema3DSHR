"""p015 «FRACTURA» · guion de tiempos (30 fps, 5400 cuadros = 180 s). Lo usan el Blender (construir.py) y la música (musica.py)."""
FPS = 30
TOTAL = 5400

# (id, nombre, inicio, fin) en cuadros
ESCENAS = [
    ("s0", "Ojo", 0, 180),
    ("s1", "Corredor", 180, 660),
    ("s2", "Cero_g", 660, 1200),
    ("s3", "Detonacion", 1200, 1920),
    ("s4", "Espejos", 1920, 2400),
    ("s5", "Colapso", 2400, 3000),
    ("s6", "Oscuro", 3000, 3750),
    ("s7", "Reconstruccion", 3750, 4500),
    ("s8", "Final", 4500, 5400),
]

# desplazamiento de cada escena en el mundo (m) para que no se pisen
def desplazamiento(i):
    return (0.0, 1000.0 * i, 0.0)

# eventos sonoros (cuadro global, tipo, intensidad 0-1): la música y los efectos se sincronizan con estos cuadros
EVENTOS = [
    (0, "latido", 0.6),
    (150, "subida", 0.8),
    (180, "impacto", 1.0),         # pupila → corredor
    (420, "estruendo", 0.7),       # explosión detrás de Aiden
    (640, "onda", 1.0),            # onda de choque → cero g
    (660, "silencio", 0.0),
    (900, "particula", 0.4),
    (1180, "subida", 0.9),
    (1200, "impacto", 1.0),        # partícula → detonación
    (1290, "explosion", 1.0),
    (1450, "camara_lenta", 0.8),
    (1560, "congelado", 0.6),
    (1680, "retroceso", 0.8),
    (1900, "subida", 1.0),
    (1920, "impacto", 0.9),        # explosión → espejos
    (2250, "espejo", 0.8),
    (2400, "cristal", 1.0),        # esquirla → colapso
    (2560, "colapso", 1.0),
    (2800, "camara_lenta", 0.7),
    (2990, "subida", 0.8),
    (3000, "silencio", 0.0),
    (3300, "polvo", 0.3),
    (3600, "latido", 0.5),
    (3740, "subida", 1.0),
    (3750, "impacto", 0.9),
    (4000, "reversa", 0.8),
    (4300, "reconstruye", 0.8),
    (4490, "subida", 1.0),
    (4500, "impacto", 1.0),
    (4650, "montaje", 0.9),
    (5000, "montaje", 1.0),
    (5200, "rotura", 1.0),
    (5300, "silencio", 0.0),
]
