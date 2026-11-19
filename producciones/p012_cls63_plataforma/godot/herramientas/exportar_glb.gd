## Exporta la escena base de Godot (auto, plataforma, puertas, ruedas, cámara y animación «toma») a GLB.
## Los efectos de partículas y la niebla volumétrica no viajan: Blender los rehace.
extends SceneTree

func _initialize() -> void:
	var esc: Node3D = (load("res://escena/principal.tscn") as PackedScene).instantiate()
	root.add_child(esc)
	await process_frame
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var e1 := doc.append_from_scene(esc, st)
	var e2 := doc.write_to_filesystem(st, ProjectSettings.globalize_path("res://salida/cls63_escena.glb"))
	print("GLB: ", error_string(e1), " ", error_string(e2))
	quit()
