"""p014 · parche mínimo a ai_driver.gd de la COPIA del proyecto: permite que el pelotón le dé una trazada de carrera (afuera → vértice →
afuera) en vez de cerrarse siempre al centro en las curvas. Con `line_free = false` (lo normal en el juego) todo queda como estaba.
Uso: python3 parche_ia.py <carpeta godot/game de la copia>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "ai" / "ai_driver.gd"
s = p.read_text(encoding="utf-8")
if "line_free" in s:
    print("ya parcheado"); sys.exit(0)
s = s.replace("var respawns := 0\n", "var respawns := 0\nvar line_free := false # cinemática: la trazada (lane_t) NO se cierra al centro en las curvas\n", 1)
a = "var ln := clampf(lane_t, -lane_max, lane_max) * (1.0 - minf(1.0, kap * 40.0))"
assert a in s
s = s.replace(a, "var ln := clampf(lane_t, -lane_max, lane_max) * (1.0 if line_free else (1.0 - minf(1.0, kap * 40.0)))", 1)
p.write_text(s, encoding="utf-8")
print("ai_driver.gd parcheado")
