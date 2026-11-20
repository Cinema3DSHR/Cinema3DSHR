extends Node3D
## Previsualización de FRACTURA: recorre la línea de tiempo (data/linea_de_tiempo.json) y muestra, cuadro a cuadro,
## la escena activa, las transiciones y los eventos sonoros; una cámara de volúmenes simples se coloca en el desplazamiento de cada escena.

var datos: Dictionary = {}
var cuadro := 0
var etiqueta: Label
var cam: Camera3D
var cubos := {}

func _ready() -> void:
	var f := FileAccess.open("res://data/linea_de_tiempo.json", FileAccess.READ)
	datos = JSON.parse_string(f.get_as_text())
	cam = Camera3D.new()
	add_child(cam)
	for e in datos["escenas"]:
		var m := MeshInstance3D.new()
		m.mesh = BoxMesh.new()
		m.position = Vector3(e["desplazamiento"][0], e["desplazamiento"][1] * 0.01, e["desplazamiento"][2])
		add_child(m)
		cubos[e["id"]] = m
	var cl := CanvasLayer.new()
	etiqueta = Label.new()
	cl.add_child(etiqueta)
	add_child(cl)

func escena_en(c: int) -> Dictionary:
	for e in datos["escenas"]:
		if c >= e["desde"] and c < e["hasta"]:
			return e
	return {}

func transicion_en(c: int) -> String:
	for t in datos["transiciones"]:
		if c >= t["cuadros"][0] and c <= t["cuadros"][1]:
			return "%s: %s" % [t["id"], t["tipo"]]
	return ""

func _process(_d: float) -> void:
	cuadro = (cuadro + 4) % int(datos["cuadros"])
	var e := escena_en(cuadro)
	if e.is_empty():
		return
	var m: MeshInstance3D = cubos[e["id"]]
	cam.position = m.position + Vector3(3, 2, 6)
	cam.look_at(m.position)
	etiqueta.text = "%d  %.1fs  %s\n%s" % [cuadro, cuadro / float(datos["fps"]), e["nombre"], transicion_en(cuadro)]
