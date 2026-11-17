"""Genera (o estima) las voces de todo el guion de Dúo Cero, escena por escena, respetando el presupuesto.

    /opt/tools/blendenv/bin/python producciones/p009_duo_cero/herramientas/voces.py          # sólo estima
    /opt/tools/blendenv/bin/python producciones/p009_duo_cero/herramientas/voces.py --gastar # genera lo que falta
"""
import json
import sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from estudio.audio import elevenlabs as EL
import guion as G

gastar = "--gastar" in sys.argv
total = {"faltan": 0, "creditos": 0.0}
for n, pasos in G.ESCENAS.items():
    evs = [{"tipo": "voz", "rol": p["voz"], "texto": p["texto"], "inicio_s": 0.0} for p in pasos if p.get("voz")]
    m = {"id": f"p009_duo_cero-e{n:02d}", "sonido": {"generador": "procedural", "eventos": evs}}
    r = EL.asegurar_escena(m, gastar=gastar)
    print(f"e{n:02d}", json.dumps(r, ensure_ascii=False))
