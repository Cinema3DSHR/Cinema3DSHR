## Revisión sin render: cámara libre. Uso: … -s herramientas/captura_libre.gd -- salida/l t x y z mx my mz [x y z mx my mz …]
extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var esc: Node = (load("res://escena/principal.tscn") as PackedScene).instantiate()
	root.add_child(esc)
	await process_frame
	var ap: AnimationPlayer = esc.get_node("Animacion")
	ap.play("toma")
	ap.seek(float(args[1]), true)
	ap.pause()
	var cam := Camera3D.new()
	cam.fov = 64.0
	cam.far = 800.0
	root.add_child(cam)
	cam.current = true
	var k := 0
	var i := 2
	while i + 5 < args.size():
		cam.position = Vector3(float(args[i]), float(args[i + 1]), float(args[i + 2]))
		cam.look_at(Vector3(float(args[i + 3]), float(args[i + 4]), float(args[i + 5])))
		for f in 4:
			await process_frame
		root.get_texture().get_image().save_png("%s_%d.png" % [args[0], k])
		k += 1
		i += 6
	quit()
