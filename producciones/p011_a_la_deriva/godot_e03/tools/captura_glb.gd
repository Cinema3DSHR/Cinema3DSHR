## Capturas de revisión de la nave (no es un render): xvfb-run -a godot --path . --rendering-driver opengl3 --script res://tools/captura.gd -- SALIDA_PREFIJO [lista.json]
extends SceneTree
var tomas := []
var i := 0
var espera := 0
var salida := ""
var nave: Node

func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	salida = a[0]
	root.size = Vector2i(960, 540)
	DisplayServer.window_set_size(Vector2i(960, 540))
	var doc := GLTFDocument.new(); var st := GLTFState.new(); doc.append_from_file(a[2], st); nave = doc.generate_scene(st)
	root.add_child(nave)
	var f := "res://tools/tomas_revision.json"
	tomas = JSON.parse_string(FileAccess.get_file_as_string(f))
	var cam := Camera3D.new()
	cam.name = "CamRev"
	cam.current = true
	cam.near = 0.05
	cam.far = 2000.0
	root.add_child(cam)

func _process(_d: float) -> bool:
	if i >= tomas.size():
		quit()
		return true
	var t = tomas[i]
	var cam: Camera3D = root.get_node("CamRev")
	if espera == 0:
		cam.fov = float(t.get("fov", 70))
		cam.global_position = Vector3(t["pos"][0], t["pos"][1], t["pos"][2])
		cam.look_at(Vector3(t["mira"][0], t["mira"][1], t["mira"][2]), Vector3.UP)
		espera = 4
		return false
	espera -= 1
	if espera == 0:
		var img := root.get_texture().get_image()
		img.save_png("%s_%s.png" % [salida, t["n"]])
		print("CAP ", t["n"])
		i += 1
	return false
