## Revisión del auto: carga hustler.glb, lista piezas y toma capturas. Uso: xvfb-run -a godot --path . --rendering-driver opengl3 --script res://tools/prueba_auto.gd -- PREFIJO
extends SceneTree
func _initialize() -> void:
	var pre := OS.get_cmdline_user_args()[0]
	var auto: Node3D = load("res://tools/auto.gd").crear()
	root.add_child(auto)
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-40, 35, 0); luz.light_energy = 1.4; root.add_child(luz)
	var env := WorldEnvironment.new(); var e := Environment.new(); e.background_mode = Environment.BG_COLOR; e.background_color = Color(0.1, 0.12, 0.16)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(0.6, 0.65, 0.75); env.environment = e; root.add_child(env)
	var cam := Camera3D.new(); root.add_child(cam)
	var vistas := {"lado": [Vector3(6, 1.6, 0), Vector3(0, 0.6, 0)], "tres_cuartos": [Vector3(4.5, 2.0, -5.0), Vector3(0, 0.6, 0)], "frente": [Vector3(0, 1.2, -7), Vector3(0, 0.6, 0)]}
	for k in vistas:
		cam.look_at_from_position(vistas[k][0], vistas[k][1]); cam.current = true
		await process_frame; await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [pre, k])
	for n in auto.get_node("Modelo").get_children():
		var mi := n as MeshInstance3D
		if mi: print(n.name, " ", mi.get_aabb().size.snapped(Vector3(0.01, 0.01, 0.01)), " pos ", n.position.snapped(Vector3(0.01, 0.01, 0.01)))
	quit()
