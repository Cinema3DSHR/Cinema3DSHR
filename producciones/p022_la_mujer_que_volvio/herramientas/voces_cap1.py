"""Genera (o reutiliza de la biblioteca) la narración de Gabriel del cap. 1 y escribe audio_cap1/voces.json (archivo, duración, alineación por letra).
Uso: python voces_cap1.py [--gastar]   (sin --gastar sólo estima)"""
import json, subprocess, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).parent))
from estudio.audio import elevenlabs as EL
import guion_cap1 as G

TAG = {"accidente": "[tired, broken, low]", "despues": "[bitter, quiet, weary]", "casa": "[exhausted, hurt, low]"}
EXTRA = {"¿Qué te pasó, Elena?": "[voice cracking]", "Grité su nombre hasta quedarme sin voz.": "[hoarse, anguished]",
         "Estaba viva.": "[stunned, whisper]", "¿Por qué?": "[desperate]"}
lineas = []
for bloque, textos in G.BLOQUES.items():
    for t in textos:
        lineas.append((bloque, t, {"tipo": "voz", "rol": "gabriel_noir", "texto": f"{EXTRA.get(t, TAG[bloque])} {t}", "modelo": "eleven_v3",
                                    "alineacion": True, "etiquetas": ["p022", "cap1", bloque]}))
print("líneas", len(lineas), "créditos estimados", sum(EL.costo_estimado(e) for _, _, e in lineas))
if "--gastar" not in sys.argv:
    sys.exit(0)
out = []
for bloque, t, e in lineas:
    r = EL.generar(e)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(r)], capture_output=True, text=True).stdout)
    al = EL.ruta_alineacion(e)
    out.append({"bloque": bloque, "texto": t, "mp3": str(Path(r).relative_to(RAIZ)), "alineacion": str(Path(al).relative_to(RAIZ)) if Path(al).exists() else None, "dur_s": round(d, 3)})
    print(bloque, round(d, 2), t[:40], flush=True)
carpeta = Path(__file__).parents[1] / "audio_cap1"; carpeta.mkdir(exist_ok=True)
json.dump(out, open(carpeta / "voces.json", "w"), indent=1, ensure_ascii=False)
print("total s", round(sum(o["dur_s"] for o in out), 1))
