extends SceneTree
func _initialize() -> void:
	var m: Node = load("res://assets/aiden.glb").instantiate(); root.add_child(m)
	var sk: Skeleton3D = m.find_children("*", "Skeleton3D", true, false)[0]
	for i in sk.get_bone_count():
		var nm := sk.get_bone_name(i)
		if "Arm" in nm or "Hand" in nm or "Clav" in nm or "Shoulder" in nm or "Hip" in nm or "Spine" in nm or "Head" in nm:
			print("B ", i, " ", nm, " padre ", sk.get_bone_parent(i))
	print("escala sk ", sk.global_transform.basis.get_scale())
	quit()
