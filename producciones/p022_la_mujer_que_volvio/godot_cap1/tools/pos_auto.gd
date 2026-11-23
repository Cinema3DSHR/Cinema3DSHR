extends SceneTree
func _initialize() -> void:
	var auto: Node3D = load("res://tools/auto.gd").crear()
	root.add_child(auto)
	await process_frame
	for n in auto.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi == null: continue
		var bb := mi.global_transform * mi.get_aabb()
		var mats := []
		for i in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(i)
			mats.append(m.resource_name if m else "-")
		print("N ", n.name, " c", bb.get_center().snapped(Vector3(0.01, 0.01, 0.01)), " t", bb.size.snapped(Vector3(0.01, 0.01, 0.01)), " ", mats)
	quit()
