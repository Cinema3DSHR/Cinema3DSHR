"""p014 · «Rally Convoy»: adapta una COPIA del proyecto de Dream Racing (nunca el original) para armar la ruta de la cinemática
con el MISMO generador de rutas de la Aventura (adv_route.gd): salida urbana con estación y peaje → campo → puente →
montaña estilo Hill Climb, todo asfalto. Uso: python3 parche_ruta.py <carpeta godot/game de la copia>"""
import re
import sys
from pathlib import Path

game = Path(sys.argv[1])
ruta = game / "adventure" / "adv_route.gd"
s = ruta.read_text(encoding="utf-8")
if "CINE_RALLY_CONVOY" in s:
    print("ya parcheado"); sys.exit(0)

# 1) estilo de curvas «hill»: horquillas y eses cerradas de montaña (rectas cortas, radios chicos, giros grandes)
s = s.replace('\t"fast": {', '\t"hill": {"s": [14.0, 60.0], "r": [20.0, 62.0], "a": [45.0, 150.0], "bound": 120.0},\n\t"fast": {', 1)

# 2) pieza «toll»: tramo recto donde va el peaje (la cinemática dibuja la plaza en ese punto)
s = s.replace('\t\t"town": events.append({"i": count, "t": "town", "name": str(a[1])})',
              '\t\t"town": events.append({"i": count, "t": "town", "name": str(a[1])})\n'
              '\t\t"toll":\n\t\t\tevents.append({"i": count + 12, "t": "toll"})\n\t\t\t_straight(float(a[1]))', 1)

# 3) la ruta: un solo tramo (el de la cinemática)
ini = s.index("## Antes de la primera etapa")
fin = s.index("# ───────────────────────── ruta generada")
nuevo = '''## CINE_RALLY_CONVOY — la ruta de la cinemática (única etapa). Todo asfalto.
const PRELUDE := [
	{"biome": CITY, "surf": S_ASPHALT, "hw": 5.4, "town": 2, "grade": 0.0},
	["S", 40.0],
]

const STAGES := [
	{"name": "Rally Convoy", "sub": "Peaje, ciudad, campo, puente y montaña", "sky": "dia",
		"rival": {"name": "-", "car": "pickup", "paint": "#ffffff", "skill": 0.9, "power": 1.0, "grip": 1.0, "bio": ""},
		"tip": "", "setup": "",
		"pieces": [
			# SECTOR 1 · estación de servicio, peaje y salida urbana por una avenida ancha
			["S", 30.0], ["station", "Estación Aurora"], ["S", 20.0], ["sign", "PEAJE · 100 m"], ["S", 25.0], ["toll", 70.0], ["S", 150.0],
			["S", 180.0], ["R", 160.0, 20.0], ["S", 220.0], ["L", 180.0, 24.0], ["S", 220.0],
			["town", "AV. COSTANERA"], ["R", 170.0, 26.0], ["S", 160.0],
			# SECTOR 2 · el pueblo queda atrás, campo abierto
			{"biome": RURAL, "town": 0, "crop": 1, "hw": 4.4}, ["S", 120.0], ["sign", "LOS GIRASOLES 9 km"],
			["auto", 1300.0, "fast"], {"crop": 2}, ["farm"], ["auto", 700.0, "rural"], {"crop": 4}, ["auto", 400.0, "rural"],
			# SECTOR 3 · el puente
			["overpass", "rail"], ["auto", 260.0, "rural"], ["sign", "PUENTE RÍO MANSO"], ["S", 140.0], ["bridge", 340.0], ["S", 110.0],
			# SECTOR 4 · montaña estilo Hill Climb, asfalto angosto, subida pronunciada y bosque denso
			{"biome": FOREST, "grade": 0.025, "hw": 3.9}, ["auto", 500.0, "forest"],
			{"biome": MOUNTAIN, "mside": 1, "grade": 0.06, "hw": 3.6}, ["auto", 600.0, "hill"],
			{"mside": -1, "grade": 0.07}, ["auto", 500.0, "hill"], {"mside": 1, "grade": 0.045}, ["auto", 350.0, "hill"],
			{"grade": 0.0}, ["S", 140.0], ["sign", "REFUGIO DE LA CUMBRE 1 km"], ["S", 200.0],
			["station", "Refugio de la Cumbre"],
		]},
]

'''
s = s[:ini] + nuevo + s[fin:]
ruta.write_text(s, encoding="utf-8")
print("adv_route.gd parcheado")
