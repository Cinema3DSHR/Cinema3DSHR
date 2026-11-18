## Vista de personajes en el visor 3D (OpenGL, el mismo motor de la app): NO es un render de Cycles.
## Uso: xvfb-run -a godot --path pruebas/personajes_humanos --script res://vista.gd -- MODELO.glb SALIDA_PREFIJO [ancho alto]
## Saca: cuerpo de frente, de 3/4, de espalda, de perfil y primer plano de la cara.
extends SceneTree

var tomas := []
var cam: Camera3D
var salida := ""
var paso := 0

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var glb: String = args[0]
	salida = args[1]
	var w := int(args[2]) if args.size() > 2 else 900
	var h := int(args[3]) if args.size() > 3 else 1600
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	root.mesh_lod_threshold = 0.0           # sin LOD automático (simplificaba el pelo de un solo lado)
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(glb, st) != OK:
		push_error("no pude leer " + glb); quit(1); return
	var escena := doc.generate_scene(st)
	root.add_child(escena)
	_aplicar_formas(escena, JSON.parse_string(OS.get_environment("FORMAS")) if OS.get_environment("FORMAS") != "" else {})
	var ap := _buscar_anim(escena)
	if ap and args.size() > 4:
		ap.play(args[4]); ap.seek(float(args[5]) if args.size() > 5 else 0.0, true); ap.pause()
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.13, 0.13, 0.15)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.55, 0.55, 0.6)
	e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	root.add_child(env)
	var sol := DirectionalLight3D.new()
	sol.rotation_degrees = Vector3(-35, 30, 0)
	sol.light_energy = 1.25
	sol.light_color = Color(1.0, 0.92, 0.82)
	root.add_child(sol)
	var rel := DirectionalLight3D.new()
	rel.rotation_degrees = Vector3(-15, -140, 0)
	rel.light_energy = 0.45
	rel.light_color = Color(0.75, 0.82, 1.0)
	root.add_child(rel)
	var piso := MeshInstance3D.new()
	var pm := PlaneMesh.new(); pm.size = Vector2(6, 6)
	piso.mesh = pm
	var mp := StandardMaterial3D.new(); mp.albedo_color = Color(0.2, 0.2, 0.22)
	piso.material_override = mp
	root.add_child(piso)
	cam = Camera3D.new()
	root.add_child(cam)
	var alto := float(OS.get_environment("ALTO")) if OS.get_environment("ALTO") != "" else 1.75
	var c := alto * 0.52
	var d := alto * 1.65
	var cabeza := alto * 0.93
	# glTF: +Y arriba, el personaje mira a +Z
	tomas = [
		["frente", Vector3(0, c, d), Vector3(0, c, 0), 40.0],
		["tres_cuartos", Vector3(d * 0.7, c, d * 0.7), Vector3(0, c, 0), 40.0],
		["espalda", Vector3(0, c, -d), Vector3(0, c, 0), 40.0],
		["perfil", Vector3(d, c, 0), Vector3(0, c, 0), 40.0],
		["cara", Vector3(0.12, cabeza, 0.62), Vector3(0, cabeza, 0), 30.0],
		["cara_34", Vector3(0.45, cabeza + 0.02, 0.45), Vector3(0, cabeza, 0), 30.0],
		["cara_34_der", Vector3(-0.45, cabeza + 0.02, 0.45), Vector3(0, cabeza, 0), 30.0],
		["atras", Vector3(0, cabeza + 0.05, -0.62), Vector3(0, cabeza, 0), 30.0],
		["pelo_atras", Vector3(-0.35, cabeza + 0.1, -0.5), Vector3(0, cabeza, 0), 32.0],
		["pies", Vector3(0.5, 0.25, 0.9), Vector3(0, 0.06, 0.05), 30.0],
		["cuello", Vector3(0.22, alto * 0.84, 0.5), Vector3(0, alto * 0.835, 0), 28.0],
		["cara_perfil", Vector3(0.68, cabeza, 0.02), Vector3(0, cabeza, 0.02), 30.0],
		["cuello_atras", Vector3(-0.25, alto * 0.86, -0.5), Vector3(0, alto * 0.835, 0), 28.0],
	]
	_poner(0)

## FORMAS='{"JawDrop": 0.5, …}': pesos de las formas clave (Godot no aplica los pesos por defecto del GLB)
func _aplicar_formas(n: Node, formas) -> void:
	if n is MeshInstance3D and OS.get_environment("OCULTAR") != "" and String(n.name).begins_with(OS.get_environment("OCULTAR")):
		n.visible = false
	if n is MeshInstance3D and OS.get_environment("SOLO") != "":
		var ok := false
		for pre in OS.get_environment("SOLO").split(","):
			if String(n.name).begins_with(pre):
				ok = true
		n.visible = ok
	if n is MeshInstance3D and n.mesh:
		for i in n.mesh.get_blend_shape_count():
			var nom: String = n.mesh.get_blend_shape_name(i)
			if formas is Dictionary and formas.has(nom):
				n.set_blend_shape_value(i, float(formas[nom]))
	for c in n.get_children():
		_aplicar_formas(c, formas)


func _buscar_anim(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer: return n
	for c in n.get_children():
		var r := _buscar_anim(c)
		if r: return r
	return null

func _poner(i: int) -> void:
	var t = tomas[i]
	cam.position = t[1]
	cam.fov = t[3]
	cam.look_at(t[2], Vector3.UP)

var esperar := 0
func _process(_d: float) -> bool:
	esperar += 1
	if esperar < 6: return false
	esperar = 0
	var img := root.get_texture().get_image()
	img.save_png("%s_%s.png" % [salida, tomas[paso][0]])
	paso += 1
	if paso >= tomas.size(): return true
	_poner(paso)
	return false
