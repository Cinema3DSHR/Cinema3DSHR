## Una captura vertical 9:16 de cada toma de una previsualización (cámara de rodaje del GLB, a mitad de la toma),
## con las luces normalizadas como el EDITOR 3D. No es un render.
## xvfb-run -a godot --path pruebas/nave --rendering-driver opengl3 --script res://tomas.gd -- PREVIA.glb PREVIA.json PREFIJO
extends SceneTree

var tomas := []
var ap: AnimationPlayer
var cams := {}
var i := 0
var espera := 0
var salida := ""
var esc: Node

func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	salida = a[2]
	DisplayServer.window_set_size(Vector2i(540, 960))
	root.size = Vector2i(540, 960)
	root.mesh_lod_threshold = 0.0
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	doc.append_from_file(a[0], st)
	esc = doc.generate_scene(st)
	root.add_child(esc)
	var d = JSON.parse_string(FileAccess.get_file_as_string(a[1]))
	tomas = d["tomas"]
	for n in esc.find_children("*", "", true, false):
		if n is Camera3D:
			cams[str(n.name)] = n
		elif n is Light3D:
			n.shadow_enabled = false
			if n is OmniLight3D:
				n.light_energy = 0.6
				n.omni_range = 5.0
			elif n is DirectionalLight3D:
				n.light_energy = 0.8
		elif n is AnimationPlayer and ap == null:
			ap = n
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.55, 0.66, 0.82)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.8, 0.8, 0.85)
	e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	root.add_child(env)
	var sol := DirectionalLight3D.new()
	sol.rotation_degrees = Vector3(-55, 25, 0)
	sol.light_energy = 0.6
	root.add_child(sol)
	_poner()

func _poner() -> void:
	var t = tomas[i]
	var mitad: float = (float(t.get("inicio_s", 0)) + float(t.get("fin_s", 1))) * 0.5
	if ap:
		for nombre in ap.get_animation_list():
			ap.play(nombre)
			ap.seek(mitad, true)
	for k in cams:
		if k.find(str(t["id"])) >= 0:
			cams[k].current = true

func _process(_d: float) -> bool:
	espera += 1
	if espera < 6: return false
	espera = 0
	root.get_texture().get_image().save_png("%s_%02d.png" % [salida, i + 1])
	i += 1
	if i >= tomas.size(): return true
	_poner()
	return false
