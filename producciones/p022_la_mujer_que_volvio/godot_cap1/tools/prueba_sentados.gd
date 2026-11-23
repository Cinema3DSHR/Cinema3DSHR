## Gabriel (al volante) y Elena (acompañante) sentados con el RigSentado de Dream Rally. Capturas de revisión (no es render).
extends SceneTree
const PISO := -0.50                 # altura del piso de la cabina (mundo)
const ASIENTO_Z := 0.20             # z de la cadera (mundo)

func cabina(a: Actor3, x: float) -> void:
	a.raiz.position = Vector3(x, PISO, ASIENTO_Z)
	a.raiz.rotation.y = PI          # el personaje mira a +Z local = −Z del mundo (hacia el frente del auto)

func _initialize() -> void:
	var pre := OS.get_cmdline_user_args()[0]
	var auto: Node3D = load("res://tools/auto.gd").crear()
	root.add_child(auto)
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-55, 30, 0); luz.light_energy = 1.2; root.add_child(luz)
	var env := WorldEnvironment.new(); var e := Environment.new(); e.background_mode = Environment.BG_COLOR; e.background_color = Color(0.08, 0.1, 0.14)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color = Color(0.7, 0.72, 0.8); e.ambient_light_energy = 0.7; env.environment = e; root.add_child(env)
	var g := Actor3.new(); g.cargar("gabriel", "res://assets/aiden.glb", "res://assets/aiden_meta.json", root)
	var el := Actor3.new(); el.cargar("elena", "res://assets/kate.glb", "res://assets/kate_meta.json", root)
	cabina(g, 0.36); cabina(el, -0.36)
	await process_frame
	var rg := RigSentado.new(g.sk, g.raiz)
	var re := RigSentado.new(el.sk, el.raiz)
	print("rig ok ", rg.ok, " ", re.ok)
	var hip := Vector3(0, 0.30, 0)
	# volante en el espacio local de Gabriel (el mundo → local de su raíz)
	var inv := g.raiz.global_transform.affine_inverse()
	var wc := inv * Vector3(0.36, 0.18, -0.20)                       # centro del aro
	var n := (inv.basis * Vector3(0, 0.25, 1)).normalized()          # normal del volante hacia el conductor
	var wX := Vector3.UP.cross(n).normalized()
	var wY := n.cross(wX)
	var manos := []
	for par in [["Left", 2.5], ["Right", 0.64]]:                      # 10 y 2 horas
		var ph: float = par[1]
		var gp := wc + wX * cos(ph) * 0.19 + wY * sin(ph) * 0.19
		var rr := (gp - wc).normalized()
		manos.append({"side": par[0], "wrist": gp + n * 0.075 + rr * 0.05, "fdir": (rr * -0.15 + n * -0.85).normalized(), "back": (rr * 0.9 + n * 0.25).normalized(), "pole": Vector3(0.55, -0.55, -0.30)})
	rg.pose({"hips": hip, "head": hip + Vector3(0, 0.60, 0.03), "roll": 0.0, "look": 0.0, "look_y": -0.1, "hands": manos, "grip": 1.2,
		"feet": [{"side": "Left", "pos": Vector3(0.13, 0.13, 0.58)}, {"side": "Right", "pos": Vector3(-0.13, 0.13, 0.55)}]})
	re.pose({"hips": hip, "head": hip + Vector3(0, 0.60, 0.0), "roll": 0.0, "look": -0.05, "look_y": -0.1, "grip": 0.8,
		"hands": [{"side": "Left", "wrist": Vector3(0.20, 0.42, 0.26), "fdir": Vector3(0, -0.25, 1).normalized(), "back": Vector3(0, 1, 0), "pole": Vector3(0.5, -0.6, -0.3)},
				  {"side": "Right", "wrist": Vector3(-0.18, 0.42, 0.28), "fdir": Vector3(0, -0.25, 1).normalized(), "back": Vector3(0, 1, 0), "pole": Vector3(0.5, -0.6, -0.3)}],
		"feet": [{"side": "Left", "pos": Vector3(0.13, 0.12, 0.55)}, {"side": "Right", "pos": Vector3(-0.13, 0.12, 0.55)}]})
	for a in [g, el]:
		var sk: Skeleton3D = a.sk
		for nm in ["Hip", "Head", "L_Foot", "L_Hand", "R_Hand"]:
			var bi := sk.find_bone("EM3D_Base_" + nm)
			print(a.id, " ", nm, " mundo ", (sk.global_transform * sk.get_bone_global_pose(bi).origin).snapped(Vector3(0.01, 0.01, 0.01)))
		print(a.id, " sk escala ", sk.global_transform.basis.get_scale(), " rest hip ", sk.get_bone_rest(sk.find_bone("EM3D_Base_Hip")).origin, " raiz bone0 ", sk.get_bone_global_rest(0).origin)
	for nm in ["body", "salon", "Dver R", "dver L", "glassLF", "glassRF", "glassF", "glassR", "glassLR", "glassRR"]:
		var h = auto.find_child(nm, true, false)
		if h: h.visible = false
	var cam := Camera3D.new(); root.add_child(cam)
	var tomas := {"lado": [Vector3(3.6, 0.5, 0.2), Vector3(0, 0.1, 0), 35], "arriba": [Vector3(0, 3.2, 0.3), Vector3(0, 0, 0), 45], "volante": [Vector3(0.1, 0.55, 0.9), Vector3(0.36, 0.15, -0.2), 55]}
	for k in tomas:
		cam.look_at_from_position(tomas[k][0], tomas[k][1], Vector3.UP); cam.fov = tomas[k][2]; cam.current = true
		await process_frame; await process_frame; await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [pre, k])
	quit()
