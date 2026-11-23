extends SceneTree
func _initialize() -> void:
	await process_frame
	var a := Actor3.new(); a.cargar("g", "res://assets/aiden.glb", "res://assets/aiden_meta.json", root)
	await process_frame
	var base := 0.0
	for nm in ["idle", "exit_car", "inj_walk", "sad_walk", "look_around2", "nerv_look", "calling", "dizzy", "kneel_down", "fall_fwd", "look_down", "stunned", "pain", "walk_dying"]:
		if not a.clips.has(nm): print("CLIP falta ", nm); continue
		var peor := 0.0; var peor_k := 0
		for k in range(0, int(a.clips[nm]["n"]), 6):
			a.poner_pose(a.pose_clip(nm, k, false))
			var cad: Vector3 = a.sk.get_bone_global_pose(a.hueso_cadera).origin
			for h in a.sk.get_bone_count():
				var d := (a.sk.get_bone_global_pose(h).origin - cad).length() * a.sk.global_transform.basis.get_scale().x
				if d > peor: peor = d; peor_k = k
		print("CLIP ", nm, " n=", a.clips[nm]["n"], " alcance máx ", snappedf(peor, 0.01), " m en k=", peor_k)
	quit()
