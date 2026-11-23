extends SceneTree
func _initialize() -> void:
	var auto: Node3D = load("res://tools/auto.gd").crear()
	root.add_child(auto)
	await process_frame
	var tot := 0
	for n in auto.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var v := 0
		for i in mi.mesh.get_surface_count():
			v += mi.mesh.surface_get_array_len(i)
		tot += v
		var mats := []
		for i in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(i)
			mats.append((m.resource_name if m else "-") + ("" if not (m is StandardMaterial3D) else (":a" if (m as StandardMaterial3D).transparency != 0 else "")))
		print("N ", n.name, " v=", v, " ", mats)
	print("TOTAL vértices ", tot)
	quit()
