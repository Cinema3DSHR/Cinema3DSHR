"""Exporta la línea de tiempo del guion (escenas, transiciones y eventos sonoros) a godot/data/linea_de_tiempo.json."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guion

TRANSICIONES = [
    {"id": "B", "tipo": "pupila del ojo", "desde": "s0", "hasta": "s1", "cuadros": [150, 179]},
    {"id": "F", "tipo": "onda de choque contra la lente", "desde": "s1", "hasta": "s2", "cuadros": [628, 659]},
    {"id": "E", "tipo": "partícula luminosa que crece", "desde": "s2", "hasta": "s3", "cuadros": [1000, 1199]},
    {"id": "A", "tipo": "zoom al interior de la explosión", "desde": "s3", "hasta": "s4", "cuadros": [1740, 1919]},
    {"id": "C", "tipo": "espejo que estalla", "desde": "s4", "hasta": "s4", "cuadros": [2262, 2330]},
    {"id": "D", "tipo": "esquirla de cristal gigante", "desde": "s4", "hasta": "s5", "cuadros": [2330, 2399]},
    {"id": "G1", "tipo": "ventana de luz que estalla", "desde": "s5", "hasta": "s6", "cuadros": [2900, 2999]},
    {"id": "H", "tipo": "anillo de luz hasta la lente", "desde": "s6", "hasta": "s7", "cuadros": [3640, 3749]},
    {"id": "I", "tipo": "ascenso al cielo en blanco", "desde": "s7", "hasta": "s8", "cuadros": [4400, 4499]},
    {"id": "G", "tipo": "esfera de espejos que se rompe en 320 fragmentos", "desde": "s8", "hasta": "s8", "cuadros": [4800, 4999]},
]
d = {
    "formato": "fractura.linea_de_tiempo/1",
    "fps": guion.FPS,
    "cuadros": guion.TOTAL,
    "escenas": [{"id": i, "nombre": n, "desde": a, "hasta": b, "desplazamiento": guion.desplazamiento(k)} for k, (i, n, a, b) in enumerate(guion.ESCENAS)],
    "transiciones": TRANSICIONES,
    "eventos": [{"cuadro": c, "tipo": t, "intensidad": x} for c, t, x in guion.EVENTOS],
}
ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "godot", "data", "linea_de_tiempo.json")
json.dump(d, open(ruta, "w"), indent=1, ensure_ascii=False)
print("escrito", os.path.normpath(ruta))
