extends SceneTree
func _init():
	var ps: PackedScene = load("res://hombre_prueba.glb")
	if ps == null:
		print("RESULTADO no se pudo cargar"); quit(); return
	var raiz = ps.instantiate()
	root.add_child(raiz)
	var sk: Skeleton3D = null
	var mallas := []
	var ap: AnimationPlayer = null
	var pila := [raiz]
	while pila.size() > 0:
		var n = pila.pop_back()
		if n is Skeleton3D: sk = n
		if n is MeshInstance3D: mallas.append(n)
		if n is AnimationPlayer: ap = n
		for c in n.get_children(): pila.append(c)
	print("RESULTADO huesos=", sk.get_bone_count() if sk else -1)
	var total_bs := 0
	for m in mallas:
		var nbs: int = m.mesh.get_blend_shape_count() if m.mesh else 0
		total_bs += nbs
		print("MALLA ", m.name, " tris~", (m.mesh.get_faces().size()/3) if m.mesh else 0, " blendshapes=", nbs, " superficies=", m.mesh.get_surface_count() if m.mesh else 0)
	print("RESULTADO blendshapes_total=", total_bs)
	if ap:
		for a in ap.get_animation_list():
			var an: Animation = ap.get_animation(a)
			var bs_tracks := 0
			var bone_tracks := 0
			var otros := 0
			var nombres := []
			for i in an.get_track_count():
				var p := str(an.track_get_path(i))
				var t := an.track_get_type(i)
				if t == Animation.TYPE_BLEND_SHAPE:
					bs_tracks += 1
					if nombres.size() < 4: nombres.append(p)
				elif t == Animation.TYPE_POSITION_3D or t == Animation.TYPE_ROTATION_3D or t == Animation.TYPE_SCALE_3D:
					bone_tracks += 1
				else:
					otros += 1
			print("ANIM ", a, " dur=", an.length, " pistas_hueso=", bone_tracks, " pistas_blendshape=", bs_tracks, " otras=", otros, " ej=", nombres)
		# reproducir y leer valores
		var lista := ap.get_animation_list()
		if lista.size() > 0:
			ap.play("Mesh_001Action")
			ap.seek(0.27, true)
			var hips_i = sk.find_bone("EM3D_Base_Hip") if sk else -1
			print("HUESO Hip pos t=0.3 ", sk.get_bone_pose_position(hips_i) if hips_i >= 0 else "?")
			for m in mallas:
				if m.mesh and m.mesh.get_blend_shape_count() > 0 and String(m.name).contains("Body"):
					for i in m.mesh.get_blend_shape_count():
						var bn: String = String(m.mesh.get_blend_shape_name(i))
						if bn == "V_Open" or bn == "Mouth_Smile" or bn == "Eyes_Blink":
							print("BS ", bn, " valor=", m.get_blend_shape_value(i))
	quit()
