## Exporta la nave a GLB para el visor HTML. Uso: godot --headless --path . --script res://tools/exportar_glb.gd -- SALIDA.glb
extends SceneTree
func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	var nave: Node = load("res://nave.tscn").instantiate()
	root.add_child(nave)
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var e := doc.append_from_scene(nave, st)
	if e != OK:
		print("ERROR append ", e)
		quit(1)
		return
	e = doc.write_to_filesystem(st, a[0])
	print("GLB ", a[0], " ", e)
	quit()
