extends SceneTree
func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	doc.append_from_file(args[0], st)
	var esc := doc.generate_scene(st)
	root.add_child(esc)
	_rec(esc)
	quit()
func _rec(n: Node) -> void:
	if n is MeshInstance3D and String(n.name).begins_with(OS.get_environment("SONDA")):
		var m: Mesh = n.mesh
		var aabb := m.get_aabb()
		print(n.name, " superficies=", m.get_surface_count(), " aabb=", aabb, " skin=", n.skin != null)
		for i in m.get_surface_count():
			var arr = m.surface_get_arrays(i)
			var pos: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var izq := 0
			var der := 0
			for p in pos:
				if p.x > 0.0019: der += 1
				else: izq += 1
			var idx = arr[Mesh.ARRAY_INDEX]
			print("  sup ", i, " verts=", pos.size(), " x>0=", der, " x<0=", izq, " idx=", (idx.size() if idx != null else 0))
	for c in n.get_children():
		_rec(c)
