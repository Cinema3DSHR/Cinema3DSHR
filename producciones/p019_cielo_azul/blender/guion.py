"""p019 · línea de tiempo (30 fps) con los tiempos reales de la narración (duraciones_voz.json)."""
import json
import os
FPS = 30
W, H = 540, 960
AQUI = os.path.dirname(os.path.abspath(__file__))
VOZ = json.load(open(os.path.join(AQUI, "..", "duraciones_voz.json")))
INICIO_S = {"b01_gancho": 0.0, "b02_luz": 3.0, "b03_atmosfera": 8.4, "b04_ondas": 17.03, "b05_cielo": 24.9, "b06_violeta": 29.95,
            "b07_atardecer": 39.3, "b08_espacio": 46.9, "b09_cierre": 51.8}
FIN_S = 60.0
TOTAL = int(round(FIN_S * FPS))
ESCENAS = [
    ("s0", "Gancho: pradera y cielo", 0.0, 3.0),
    ("s1", "Luz blanca y prisma", 3.0, 8.4),
    ("s2", "Luz y moléculas del aire", 8.4, 17.03),
    ("s3", "Azul vs rojo", 17.03, 24.9),
    ("s4", "Azul desde todo el cielo", 24.9, 29.95),
    ("s5", "¿Y el violeta?", 29.95, 39.3),
    ("s6", "Atardecer", 39.3, 46.9),
    ("s7", "Espacio", 46.9, 51.8),
    ("s8", "Cierre", 51.8, 60.0),
]


def f(s):
    return int(round(s * FPS))


def rango(i):
    _, _, a, b = ESCENAS[i]
    return f(a), f(b)


def desplazamiento(i):
    return (0.0, 1000.0 * i, 0.0)
