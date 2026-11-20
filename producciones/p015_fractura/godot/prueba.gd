extends SceneTree
## Prueba sin ventana: godot --headless --path . -s prueba.gd
func _init() -> void:
	var f := FileAccess.open("res://data/linea_de_tiempo.json", FileAccess.READ)
	var d: Dictionary = JSON.parse_string(f.get_as_text())
	var previo := 0
	var ok := true
	for e in d["escenas"]:
		if e["desde"] != previo:
			ok = false
			print("HUECO antes de ", e["id"])
		previo = e["hasta"]
	ok = ok and previo == int(d["cuadros"]) and int(d["cuadros"]) == 5400 and int(d["fps"]) == 30
	print("LINEA_DE_TIEMPO ", "OK" if ok else "FALLA", " escenas=", d["escenas"].size(), " transiciones=", d["transiciones"].size(), " eventos=", d["eventos"].size(), " cuadros=", d["cuadros"])
	quit(0 if ok else 1)
