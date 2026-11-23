## Gabriel (der., al volante) y Elena (izq.) sentados en el auto. Capturas de revisión (no es render).
extends SceneTree
func _initialize() -> void:
	var pre := OS.get_cmdline_user_args()[0]
	var auto: Node3D = load("res://tools/auto.gd").crear()
	root.add_child(auto)
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-55, 30, 0); luz.light_energy = 1.2; root.add_child(luz)
	var env := WorldEnvironment.new(); var e := Environment.new(); e.background_mode = Environment.BG_COLOR; e.background_color = Color(0.08, 0.1, 0.14)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(0.7, 0.72, 0.8); e.ambient_light_energy = 0.7; env.environment = e; root.add_child(env)
	var g := Actor3.new(); g.cargar("gabriel", "res://assets/aiden.glb", "res://assets/aiden_meta.json", root)
	var el := Actor3.new(); el.cargar("elena", "res://assets/kate.glb", "res://assets/kate_meta.json", root)
	for a in [g, el]:
		a.poner_pose(a.pose_clip("sit_idle", 1, true))
		a.raiz.rotation.y = PI
	await process_frame
	for par in [[g, Vector3(0.36, -0.22, 0.2)], [el, Vector3(-0.36, -0.22, 0.2)]]:
		var a: Actor3 = par[0]
		var cad := a.sk.global_transform * a.sk.get_bone_global_pose(a.hueso_cadera).origin
		print(a.id, " cadera en ", cad.snapped(Vector3(0.01, 0.01, 0.01)), " raiz ", a.raiz.position)
		a.raiz.position += par[1] - cad
	await process_frame
	var reg := {"R": Vector3(-0.50, -0.12, -0.12), "L": Vector3(-0.22, -0.12, -0.12)}   # Elena: manos sobre las piernas
	for lado in reg:
		IkBrazo.llevar_mano(el.sk, el.mano[lado], reg[lado], reg[lado] + Vector3(-0.6 if lado == "R" else 0.6, -0.4, 0.2))
	var manos := {"R": Vector3(0.56, 0.24, -0.24), "L": Vector3(0.17, 0.24, -0.24)}
	for lado in manos:
		var hand: int = g.mano[lado]
		var fuera := 1.0 if lado == "R" else -1.0
		var err := IkBrazo.llevar_mano(g.sk, hand, manos[lado], manos[lado] + Vector3(0.5 * fuera, -0.8, 0.3))
		print("mano ", lado, " error ", snappedf(err, 0.001))
	for nm in ["body", "salon", "Dver R", "dver L", "glassLF", "glassRF", "glassF", "glassR", "glassLR", "glassRR"]:
		var h = auto.find_child(nm, true, false)
		if h: h.visible = false
	var cam := Camera3D.new(); root.add_child(cam)
	var tomas := {"lado": [Vector3(3.6, 0.5, 0.2), Vector3(0, 0.1, 0), 35], "arriba": [Vector3(0, 3.2, 0.3), Vector3(0, 0, 0), 45], "volante": [Vector3(0.1, 0.55, 0.9), Vector3(0.36, 0.15, -0.2), 55]}
	for k in tomas:
		cam.look_at_from_position(tomas[k][0], tomas[k][1], Vector3.UP); cam.fov = tomas[k][2]; cam.current = true
		await process_frame; await process_frame; await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [pre, k])
	quit()
