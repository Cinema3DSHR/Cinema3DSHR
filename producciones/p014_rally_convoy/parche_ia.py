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
# 2) pedales suaves (cinemática): ley de control continua + filtro de subida/bajada. Con `smooth_pedals = false` (lo normal en el juego) no cambia nada.
s = s.replace("var line_free := false", "var smooth_pedals := false # cinemática: pedales continuos, sin pisar y soltar\nvar _ft := 0.0\nvar _tff := 0.3\nvar _fb := 0.0\nvar line_free := false", 1)
orig = """	var err := vt - spd
	if err > 0.0:
		throttle = minf(1.0, 0.35 + err * 0.25)
		brake = 0.0
	else:
		throttle = 0.25 if err > -1.2 else 0.0
		brake = minf(1.0, -err * 0.22) if err < -1.2 else 0.0
"""
assert orig in s
s = s.replace(orig, """	var err := vt - spd
	if smooth_pedals:
		# ley continua: sin saltos al cruzar la velocidad buscada (el original saltaba de 0,35 a 0,25 y de 0,25 a freno)
		throttle = clampf(0.30 + 0.30 * err, 0.0, 1.0)
		brake = clampf(-(err + 0.8) * 0.30, 0.0, 1.0)
	elif err > 0.0:
		throttle = minf(1.0, 0.35 + err * 0.25)
		brake = 0.0
	else:
		throttle = 0.25 if err > -1.2 else 0.0
		brake = minf(1.0, -err * 0.22) if err < -1.2 else 0.0
""", 1)
# envoltorio: update() filtra la salida de _update_raw()
s = s.replace("func update(ph: VehiclePhysics, h: float) -> Vector3:", "func update(ph: VehiclePhysics, h: float) -> Vector3:\n\tvar c := _update_raw(ph, h)\n\tif not smooth_pedals or not enabled:\n\t\treturn c\n\t# filtro: el gas sube y baja de a poco; el freno entra rápido pero sale de a poco; nunca los dos a la vez\n\tvar up := 2.2 if c.y < 0.05 else 0.0\n\t_ft = move_toward(_ft, c.x, (2.2 if c.x > _ft else 3.5) * h)\n\t_fb = move_toward(_fb, c.y, (9.0 if c.y > _fb else 3.0) * h)\n\tif _fb > 0.03:\n\t\t_ft = minf(_ft, maxf(0.0, 0.25 - _fb))\n\tthrottle = _ft\n\tbrake = _fb\n\treturn Vector3(_ft, _fb, c.z)\n\nfunc _update_raw(ph: VehiclePhysics, h: float) -> Vector3:", 1)
p.write_text(s, encoding="utf-8")
print("ai_driver.gd parcheado")
