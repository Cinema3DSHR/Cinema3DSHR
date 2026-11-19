## Revisión sin render: lleva la animación a los segundos pedidos y guarda la imagen del visor de Godot.
## Uso: xvfb-run … godot --path . -s herramientas/captura.gd -- salida/c 5 20.5 …
extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var esc: Node = (load("res://escena/principal.tscn") as PackedScene).instantiate()
	root.add_child(esc)
	await process_frame
	var ap: AnimationPlayer = esc.get_node("Animacion")
	ap.play("toma")
	for i in range(1, args.size()):
		var t := float(args[i])
		ap.seek(t, true)
		ap.pause()
		for f in 4:
			await process_frame
		root.get_texture().get_image().save_png("%s_%06.2f.png" % [args[0], t])
	quit()
