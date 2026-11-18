extends SceneTree
func _initialize() -> void:
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	doc.append_from_file(OS.get_cmdline_user_args()[0], st)
	var esc := doc.generate_scene(st)
	root.add_child(esc)
	_rec(esc)
	quit()
func _rec(n: Node) -> void:
	if n is MeshInstance3D and String(n.name).begins_with("CUERO"):
		var arr = n.mesh.surface_get_arrays(0)
		var pos: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		var t := [0, 0]
		for i in range(0, idx.size(), 3):
			var c: Vector3 = (pos[idx[i]] + pos[idx[i + 1]] + pos[idx[i + 2]]) / 3.0
			t[0 if c.x > 0.0019 else 1] += 1
		var mat: Material = n.mesh.surface_get_material(0)
		print("CUERO tris x>0=", t[0], " x<0=", t[1], " cull=", (mat as BaseMaterial3D).cull_mode if mat is BaseMaterial3D else -1, " xform=", n.transform, " global=", n.global_transform)
	for c in n.get_children(): _rec(c)
