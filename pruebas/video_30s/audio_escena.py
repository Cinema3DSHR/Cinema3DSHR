"""Genera el audio ORIGINAL de la escena (procedural, sincronizado con cámaras, pelota y gol). Usa el estudio sin modificarlo."""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
import bpy
from estudio.blender import director as D
from estudio.audio import procedural
from estudio import manifiesto as MF
escena, salida = Path(sys.argv[1]), Path(sys.argv[2]); salida.mkdir(parents=True, exist_ok=True)
m = MF.leer(escena)
res = D.construir(m, "revision")
pistas = D.exportar_pistas(res, salida / "pistas.json")
w = procedural.generar(m, pistas, salida / "audio.wav")
print("AUDIO", w, "eventos:", pistas.get("eventos"))
