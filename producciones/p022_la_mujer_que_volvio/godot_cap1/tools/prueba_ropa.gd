extends SceneTree
func _initialize() -> void:
	var pre := OS.get_cmdline_user_args()[0]
	await process_frame
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-35, 30, 0); luz.light_energy = 1.4; root.add_child(luz)
	var env := WorldEnvironment.new(); var e := Environment.new(); e.background_mode = Environment.BG_COLOR; e.background_color = Color(0.12, 0.14, 0.18); e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(0.8, 0.82, 0.9); env.environment = e; root.add_child(env)
	var a := Actor3.new(); a.cargar("g", "res://assets/aiden_noir.glb", "res://assets/aiden_meta.json", root)
	await process_frame
	a.poner_pose(a.pose_clip("idle", 10, true)); a.raiz.rotation.y = PI * 0.0
	var cam := Camera3D.new(); root.add_child(cam)
	for v in [["frente", Vector3(0, 1.0, 3.6), Vector3(0, 0.95, 0), 32], ["tres", Vector3(2.4, 1.1, 2.6), Vector3(0, 0.95, 0), 32], ["pecho", Vector3(0.9, 1.35, 1.6), Vector3(0, 1.3, 0), 28], ["pies", Vector3(1.4, 0.35, 1.8), Vector3(0, 0.2, 0), 30]]:
		cam.look_at_from_position(v[1], v[2]); cam.fov = v[3]; cam.current = true
		for i in 3: await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [pre, v[0]])
	quit()
