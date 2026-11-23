extends SceneTree
func _initialize() -> void:
	var pre := OS.get_cmdline_user_args()[0]
	var auto: Node3D = load("res://tools/auto.gd").crear()
	root.add_child(auto)
	root.add_child(load("res://tools/auto.gd").entorno_noche())
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-35, 150, 0); luz.light_energy = 1.1; root.add_child(luz)
	var l2 := DirectionalLight3D.new(); l2.rotation_degrees = Vector3(-20, -60, 0); l2.light_energy = 0.7; l2.light_color = Color(0.7, 0.8, 1.0); root.add_child(l2)
	var suelo := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(30, 30); suelo.mesh = pm; suelo.position.y = -0.75
	var sm := StandardMaterial3D.new(); sm.albedo_color = Color(0.03, 0.03, 0.035); sm.roughness = 0.12; sm.metallic = 0.4; suelo.material_override = sm; root.add_child(suelo)
	for sp in [[Vector3(-3, 3.2, -2), Vector3(5, 0.1, 1.2), Color(1, 1, 1), 6.0], [Vector3(4, 2.6, 3), Vector3(0.1, 4, 1.0), Color(0.6, 0.75, 1.0), 4.0]]:   # cajas de luz para que el barniz tenga qué reflejar
		var q := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = sp[1]; q.mesh = bm; q.position = sp[0]
		var em := StandardMaterial3D.new(); em.albedo_color = sp[2]; em.emission_enabled = true; em.emission = sp[2]; em.emission_energy_multiplier = sp[3]; q.material_override = em; root.add_child(q)
	var cam := Camera3D.new(); root.add_child(cam)
	var vistas := {"tres_cuartos": [Vector3(-6.5, 1.4, -8.0), Vector3(0, 0.0, 0), 34], "lado": [Vector3(10, 1.2, 0), Vector3(0, 0.0, 0), 30], "frente": [Vector3(0, 1.0, -10), Vector3(0, 0.1, 0), 30]}
	for k in vistas:
		cam.look_at_from_position(vistas[k][0], vistas[k][1]); cam.fov = vistas[k][2]; cam.current = true
		await process_frame; await process_frame; await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [pre, k])
	quit()
