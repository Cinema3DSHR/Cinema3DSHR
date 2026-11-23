extends SceneTree
func _initialize() -> void:
	var auto: Node3D = load("res://tools/auto.gd").crear(); root.add_child(auto)
	await process_frame
	var mi := auto.find_child("chrome", true, false) as MeshInstance3D
	var m := auto.global_transform.affine_inverse() * mi.global_transform
	for si in mi.mesh.get_surface_count():
		var v: PackedVector3Array = mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]
		var mn := Vector3(9, 9, 9); var mx := Vector3(-9, -9, -9)
		for p in v:
			var q := m * p; mn = mn.min(q); mx = mx.max(q)
		print("W sup", si, " verts ", v.size(), " min ", mn.snapped(Vector3(0.01, 0.01, 0.01)), " max ", mx.snapped(Vector3(0.01, 0.01, 0.01)))
	# conectividad: ¿los vértices de la sup1 dentro de la franja forman 2 racimos?
	var v1: PackedVector3Array = mi.mesh.surface_get_arrays(1)[Mesh.ARRAY_VERTEX]
	var izq := 0; var der := 0
	for p in v1:
		var q := m * p
		if q.z > -0.95 and q.z < -0.4 and q.y > 0.12 and q.y < 0.35:
			if q.x < 0: izq += 1
			else: der += 1
	print("W franja izq ", izq, " der ", der)
	quit()
