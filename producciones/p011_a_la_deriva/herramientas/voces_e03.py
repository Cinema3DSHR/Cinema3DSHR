"""Genera (o reutiliza de la biblioteca) las 33 voces del cap. 3 y escribe audio_e03/voces.json con archivo, duración y alineación por letra.
Uso: python voces_e03.py [--gastar]  (sin --gastar sólo estima)"""
import json, subprocess, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).parent))
from estudio.audio import elevenlabs as EL
import guion_e03 as G
evs = G.eventos_voz()
print("líneas", len(evs), "créditos estimados", sum(EL.costo_estimado(e) for e in evs))
if "--gastar" not in sys.argv: sys.exit(0)
out = []
for (bloque, quien, texto, ea, ek), e in zip(G.LINEAS, evs):
    r = EL.generar(e)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(r)], capture_output=True, text=True).stdout)
    al = EL.ruta_alineacion(e)
    out.append({"bloque": bloque, "quien": quien, "texto": texto, "mp3": str(Path(r).relative_to(RAIZ)), "alineacion": str(Path(al).relative_to(RAIZ)) if Path(al).exists() else None,
                "dur_s": round(d, 3), "exp_aiden": ea, "exp_kate": ek})
    print(bloque, quien, round(d, 2), flush=True)
json.dump(out, open(Path(__file__).parents[1] / "audio_e03" / "voces.json", "w"), indent=1, ensure_ascii=False)
