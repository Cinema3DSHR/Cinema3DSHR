"""p018 · línea de tiempo (30 fps), con los tiempos reales de la narración (duraciones_voz.json)."""
import json
import os
FPS = 30
W, H = 540, 960
AQUI = os.path.dirname(os.path.abspath(__file__))
VOZ = json.load(open(os.path.join(AQUI, "..", "duraciones_voz.json")))
INICIO_S = {"b01_gancho": 0.0, "b02_gigantes": 3.3, "b03_presion": 11.55, "b04_metano": 21.55, "b05_cristales": 30.6, "b06_lluvia": 35.8,
            "b07_laboratorio": 44.2, "b08_cautela": 55.0, "b09_pregunta": 62.5}
FIN_S = 66.0
TOTAL = int(round(FIN_S * FPS))
ESCENAS = [
    ("s0", "Gancho: Neptuno", 0.0, 3.3),
    ("s1", "Gigantes helados", 3.3, 11.55),
    ("s2", "Descenso: presión y temperatura", 11.55, 21.55),
    ("s3", "El metano se rompe", 21.55, 30.6),
    ("s4", "Carbono → cristal", 30.6, 35.8),
    ("s5", "La lluvia de diamantes", 35.8, 44.2),
    ("s6", "Laboratorio", 44.2, 55.0),
    ("s7", "Hipótesis, no certeza", 55.0, 62.5),
    ("s8", "Pregunta final", 62.5, FIN_S),
]


def f(s):
    return int(round(s * FPS))


def rango(i):
    _, _, a, b = ESCENAS[i]
    return f(a), f(b)


def desplazamiento(i):
    return (0.0, 1000.0 * i, 0.0)
