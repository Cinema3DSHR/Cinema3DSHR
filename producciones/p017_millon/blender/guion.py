"""p017 · línea de tiempo (30 fps). Los tiempos salen de la duración real de la narración (duraciones_voz.json)."""
import json
import os
FPS = 30
W, H = 540, 960
AQUI = os.path.dirname(os.path.abspath(__file__))
VOZ = json.load(open(os.path.join(AQUI, "..", "duraciones_voz.json")))
# inicio de cada frase (s): con una pausa de 0,4 s entre frases salvo donde la escena lo pide
INICIO_S = {"b01_gancho": 0.0, "b02_saldo": 4.16, "b03_prudente": 9.5, "b04_impulsivo": 18.3, "b05_auto": 27.0, "b06_casa": 30.3, "b07_piscina": 33.2,
            "b08_tele": 35.9, "b09_resto": 39.7, "b10_cero": 43.9, "b11_generoso": 48.0, "b12_cierre": 55.4, "b13_pregunta": 60.4}
FIN_S = 66.67
TOTAL = int(round(FIN_S * FPS))
# escenas: (id, nombre, inicio_s, fin_s)
ESCENAS = [
    ("s0", "Dormitorio y teléfono", 0.0, 9.5),
    ("s1", "El prudente", 9.5, 18.3),
    ("s2", "El impulsivo (montaje)", 18.3, 27.0),
    ("s3", "Superdeportivo", 27.0, 30.3),
    ("s4", "Casa de lujo", 30.3, 33.2),
    ("s5", "Piscina y jardín", 33.2, 35.9),
    ("s6", "Pantalla gigante", 35.9, 39.7),
    ("s7", "Fiestas y lujos", 39.7, 43.9),
    ("s8", "Saldo cero", 43.9, 48.0),
    ("s9", "El generoso", 48.0, 55.4),
    ("s10", "Los tres en paralelo", 55.4, FIN_S),
]
# saldo (USD) del impulsivo: se actualiza al empezar cada compra (cuentas.json, verificadas)
GASTOS = [("b05_auto", 250000), ("b06_casa", 400000), ("b07_piscina", 60000), ("b08_tele", 20000), ("b09_resto", 270000)]


def f(s):
    return int(round(s * FPS))


def rango(i):
    _, _, a, b = ESCENAS[i]
    return f(a), f(b)


def desplazamiento(i):
    return (0.0, 1000.0 * i, 0.0)
