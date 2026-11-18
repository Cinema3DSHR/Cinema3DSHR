extends SceneTree
## Radio medio por lado (x>0 / x<0) de cabeza y cuero cabelludo tal como los ve Godot (reposo y con piel).
func _initialize() -> void:
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	doc.append_from_file(OS.get_cmdline_user_args()[0], st)
	var esc := doc.generate_scene(st)
	root.add_child(esc)
	var datos := {}
	_rec(esc, datos)
	var c := Vector3(0.0019, 1.68, 0.02)
	var cab: PackedVector3Array = datos["CABEZA_chico"]
	var cue: PackedVector3Array = datos["CUERO_chico"]
	var res := {0: [0, 0], 1: [0, 0]}
	for p in cue:
		var mejor := 1e9
		var q := Vector3()
		for h in cab:
			var dd := p.distance_squared_to(h)
			if dd < mejor:
				mejor = dd
				q = h
		var k := 0 if p.x > 0.0019 else 1
		res[k][0] += 1
		if (p - c).length() < (q - c).length(): res[k][1] += 1
	print("cuero dentro de la cabeza: x>0 ", res[0], "  x<0 ", res[1])
	for nombre in datos:
		var pos: PackedVector3Array = datos[nombre]
		var r := [0.0, 0.0]
		var n := [0, 0]
		for p in pos:
			if p.y < 1.70: continue
			var k := 0 if p.x > 0.0019 else 1
			r[k] += (p - c).length()
			n[k] += 1
		print(nombre, " radio x>0=", r[0] / max(1, n[0]), " (", n[0], ")  x<0=", r[1] / max(1, n[1]), " (", n[1], ")")
	quit()
func _rec(n: Node, d: Dictionary) -> void:
	if n is MeshInstance3D and (String(n.name).begins_with("CABEZA") or String(n.name).begins_with("CUERO")):
		d[String(n.name)] = n.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	for c in n.get_children(): _rec(c, d)
