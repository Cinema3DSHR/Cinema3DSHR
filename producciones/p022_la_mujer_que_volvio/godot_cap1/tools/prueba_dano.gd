extends SceneTree
func _initialize() -> void:
	var pre := OS.get_cmdline_user_args()[0]
	var A = load("res://tools/auto.gd")
	var auto: Node3D = A.crear(); root.add_child(auto)
	root.add_child(A.entorno_noche())
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-35, 150, 0); luz.light_energy = 1.3; root.add_child(luz)
	var l2 := DirectionalLight3D.new(); l2.rotation_degrees = Vector3(-20, -60, 0); l2.light_energy = 0.9; l2.light_color = Color(0.7, 0.8, 1.0); root.add_child(l2)
	await process_frame
	var limp: Array = A.limpiaparabrisas(auto)
	var t0 := Time.get_ticks_msec()
	load("res://tools/dano.gd").destruir(auto, float(OS.get_cmdline_user_args()[1]))
	for pv in limp: pv.rotate_object_local(Vector3(0, 0, 1), 0.9)
	print("destrucción en ", Time.get_ticks_msec() - t0, " ms")
	var hd := auto.find_child("hood", true, false) as Node3D
	if hd: print("capó en ", ((auto.global_transform.affine_inverse() * hd.global_transform) * Vector3.ZERO).snapped(Vector3(0.01, 0.01, 0.01)), " visible ", hd.visible)
	var cam := Camera3D.new(); root.add_child(cam)
	var vistas := {"capot": [Vector3(0, 2.6, -0.6), Vector3(0, 0.2, -0.7), 38], "tres_cuartos": [Vector3(-5.5, 1.6, -6.5), Vector3(0, 0.0, -0.8), 38], "frente": [Vector3(0, 1.3, -8.5), Vector3(0, 0.1, -1.0), 32], "lado": [Vector3(8.5, 1.1, -1.0), Vector3(0, 0.0, -1.0), 32]}
	for k in vistas:
		cam.look_at_from_position(vistas[k][0], vistas[k][1]); cam.fov = vistas[k][2]; cam.current = true
		await process_frame; await process_frame; await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [pre, k])
	quit()
