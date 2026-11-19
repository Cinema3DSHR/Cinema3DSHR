## Capturas de revisión (visor de Godot, no es el render): abre la escena, lleva la animación al segundo pedido y
## guarda la imagen del viewport. Uso: xvfb-run godot --path . -s herramientas/captura.gd -- salida/cap 2 8.5 15 …
extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var base := args[0]
	var ps: PackedScene = load("res://escena/casa_tormenta.tscn")
	var esc := ps.instantiate()
	root.add_child(esc)
	root.size = Vector2i(270, 480)
	var ap: AnimationPlayer = esc.get_node_or_null("Animacion")
	var cam: Camera3D = esc.get_node_or_null("Camara")
	if cam == null:
		cam = Camera3D.new()
		esc.add_child(cam)
		cam.position = Vector3(1.0, 1.6, 3.5)
		cam.fov = 75
	cam.make_current()
	for i in range(1, args.size()):
		if ":" in args[i]:          # pose fija x:y:z:yaw:pitch (para revisar antes de que exista la animación)
			var v := args[i].split(":")
			cam.position = Vector3(float(v[0]), float(v[1]), float(v[2]))
			cam.rotation_degrees = Vector3(float(v[4]), float(v[3]), 0)
			for f in 30:
				await process_frame
			root.get_texture().get_image().save_png("%s_pose%d.png" % [base, i])
			continue
		var t := float(args[i])
		if ap:
			ap.play("toma")
			ap.seek(t, true)
			ap.pause()
		for f in 30:
			await process_frame
		var img := root.get_texture().get_image()
		img.save_png("%s_%05.1f.png" % [base, t])
	quit()
