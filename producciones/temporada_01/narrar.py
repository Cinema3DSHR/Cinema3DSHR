"""Genera (o reutiliza de la biblioteca) la narración de un guion de la Temporada 01: un mp3 por beat y duraciones_voz.json.
Uso: python temporada_01/narrar.py producciones/<p>/guion.json [--gastar]   (sin --gastar sólo estima los caracteres)"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from estudio.audio import elevenlabs as EL  # noqa: E402

g = Path(sys.argv[1])
guion = json.load(open(g))
nar = guion["narradora"]
def _ev(b):
    """Cada beat puede traer su propia voz: «rol» (config/voces.json) o «voice_id» (+ «ajustes»); si no, la narradora del guion."""
    e = {"tipo": "voz", "texto": b["texto"], "modelo": b.get("modelo", nar["modelo"]), "ajustes": b.get("ajustes", nar["ajustes"])}
    if b.get("rol"):
        e["rol"] = b["rol"]
        e.pop("ajustes", None) if "ajustes" not in b else None
    else:
        e["voice_id"] = b.get("voice_id", nar["voice_id"])
    return e


evs = [_ev(b) for b in guion["beats"]]
print("caracteres:", sum(len(e["texto"]) for e in evs))
if "--gastar" not in sys.argv:
    sys.exit(0)
out = {}
for b, e in zip(guion["beats"], evs):
    r = EL.generar(e)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(r)], capture_output=True, text=True).stdout)
    out[b["id"]] = {"archivo": r.name, "dur_s": round(d, 2)}
    print(b["id"], r.name, round(d, 2))
json.dump(out, open(g.parent / "duraciones_voz.json", "w"), indent=1)
