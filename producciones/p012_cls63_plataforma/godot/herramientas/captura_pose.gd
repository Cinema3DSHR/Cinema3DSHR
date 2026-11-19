## Capturas de revisión con cámara fija: args «t» (segundo de la animación) o «px:py:pz:tx:ty:tz» (cámara y punto que mira).
extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var base := args[0]
	var esc: Node = (load("res://escena/principal.tscn") as PackedScene).instantiate()
	root.add_child(esc)
	await process_frame
	var ap: AnimationPlayer = esc.get_node("Animacion")
	var cam: Camera3D = esc.get_node("Camara")
	ap.play("toma")
	for i in range(1, args.size()):
		var a: String = args[i]
		if a.contains(":"):
			var v := a.split(":")
			ap.seek(float(v[6]) if v.size() > 6 else 0.0, true)
			ap.pause()
			cam.position = Vector3(float(v[0]), float(v[1]), float(v[2]))
			cam.look_at(Vector3(float(v[3]), float(v[4]), float(v[5])), Vector3.UP)
			for f in 4:
				await process_frame
			root.get_texture().get_image().save_png("%s_pose%d.png" % [base, i])
		else:
			ap.seek(float(a), true)
			ap.pause()
			for f in 4:
				await process_frame
			root.get_texture().get_image().save_png("%s_%05.2f.png" % [base, float(a)])
	quit()
