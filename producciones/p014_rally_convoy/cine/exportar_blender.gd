extends SceneTree
## «Rally Convoy» → Blender: corre la cinemática (física e IA reales) a 30 cuadros por segundo y deja en un GLB TODO lo que Blender necesita:
## el mundo, los siete autos originales completos (con sus ruedas, suspensión y la textura original), la cabina 3D y los pilotos con sus huesos
## animados, las barreras del peaje y la cámara de la dirección de cámaras. Más un JSON con los cortes, el zoom de lente por cuadro y las pinturas.
## Uso: godot --rendering-driver opengl3 --path . -s cine/exportar_blender.gd -- --t_end=312 --out=/ruta/rally_convoy_godot.glb [--detect]
##  --detect: sólo detecta qué nodos se mueven (los guarda en res://cine/animados.json); el export real los lee.

const FPS := 30
const NEED := ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "RightShoulder", "RightArm", "RightForeArm", "RightHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot"]

var sc: Node
var w3: Node3D
var args := {}
var tracks := {} # NodePath(str) → {"idx_p": int, "idx_r": int, "node": Node3D}
var bone_tracks := []
var head_tracks := {} # auto → pista de escala de la cabeza del piloto (se oculta con la cámara interior: sin retazos del casco) # {"skel": Skeleton3D, "bone": int, "name": String, "ir": int, "ip": int}
var anim: Animation
var fov_log := PackedFloat32Array()
var cuts: Array = []
var inside_log: Array = []
var tele: Array = [] # por auto: {slip: [], frenada: [], v: []} por cuadro (para el humo de las gomas en Blender)
var _last_shot := -1
var diag := {} # tipo de plano → [cuadros, cuadros con la cámara pegada al terreno, cuadros con terreno delante]

func _arg(k: String, d := "") -> String:
	return str(args.get(k, d))

func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and a.contains("="):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1]
		elif a.begins_with("--"):
			args[a.substr(2)] = "1"
	_run.call_deferred()

func _run() -> void:
	sc = (load("res://cine/cine.tscn") as PackedScene).instantiate()
	root.add_child(sc)
	await process_frame
	await process_frame
	sc.set_process(false) # el cuadro lo manejo yo (no el reloj)
	sc.export_mode = true
	w3 = sc.world3d
	var t_end := float(_arg("t_end", "312"))
	if args.has("detect"):
		_detect()
		quit()
		return
	if args.has("solo_camara"):
		await _solo_camara(t_end)
		return
	var solo := args.has("solo_json")
	_prepare_nodes()
	anim = Animation.new()
	anim.length = t_end
	anim.step = 1.0 / float(FPS)
	var ap := AnimationPlayer.new()
	ap.name = "Animacion"
	w3.add_child(ap)
	var lib := AnimationLibrary.new()
	lib.add_animation("toma", anim)
	ap.add_animation_library("", lib)
	if not solo:
		_make_tracks()
	var n_frames := int(round(t_end * FPS))
	var t0 := Time.get_ticks_msec()
	sc.fps = FPS
	for f in n_frames:
		var t := float(f) / float(FPS)
		sc._advance(t)
		sc._step_visuals(1.0 / float(FPS))
		_record(f, t)
		if f % 300 == 0:
			print("[export] cuadro %d/%d · %.0f s de reloj" % [f, n_frames, (Time.get_ticks_msec() - t0) / 1000.0])
	print("[export] animación lista: %d pistas de nodos + %d de huesos" % [tracks.size(), bone_tracks.size()])
	if solo:
		_write_json(t_end, n_frames)
		print("[export] solo JSON escrito")
		print("[diag] ", diag)
		quit()
		return
	_strip_invisible()
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var e := doc.append_from_scene(w3, st)
	print("[export] append_from_scene = ", e)
	var out := _arg("out", "/home/user/rally_cine/salida/rally_convoy_godot.glb")
	var e2 := doc.write_to_filesystem(st, out)
	print("[export] escrito ", out, " = ", e2, " · %.0f s" % ((Time.get_ticks_msec() - t0) / 1000.0))
	_write_json(t_end, n_frames)
	quit()

# ───────────────────────────── preparar nodos para el GLB
func _prepare_nodes() -> void:
	for k in sc.core.cars.size():
		var car = sc.core.cars[k]
		car.visual.name = "Auto_%d_%s" % [k, str(sc.core.ids[k])]
		sc.cockpits[k].name = "Cabina_%d" % k
		sc.cockpits[k].set_inside(true, true) # se construye y se exporta la cabina completa (se muestra sólo en los planos interiores)
		# materiales originales (con su textura) en vez del sombreador de pintura del juego, que el GLB no puede llevar
		for n in car.visual.find_children("*", "MeshInstance3D", true, false):
			var mi := n as MeshInstance3D
			if mi.mesh == null:
				continue
			for s in mi.mesh.get_surface_count():
				var ov := mi.get_surface_override_material(s)
				if ov is ShaderMaterial:
					var orig := mi.mesh.surface_get_material(s)
					var nm := orig.resource_name if orig != null else ""
					if nm == "glass":
						var gm := StandardMaterial3D.new()
						gm.resource_name = "vidrio_auto"
						gm.albedo_color = Color(0.04, 0.05, 0.07, 0.35)
						gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
						mi.set_surface_override_material(s, gm)
					else:
						mi.set_surface_override_material(s, null)
	if sc.core.toll_node != null:
		sc.core.toll_node.name = "Peaje"
	# nombres de los materiales del mundo (Blender los reconoce por nombre)
	for mk in sc.adv_world.mats.keys():
		(sc.adv_world.mats[mk] as Material).resource_name = "mundo_" + str(mk)
	for k in sc.core.cars.size():
		tele.append({"slip": [], "frenada": [], "v": []})
	sc.cam.name = "Camara"

func _strip_invisible() -> void:
	var dead: Array = []
	for n in w3.find_children("*", "Node3D", true, false):
		if not (n as Node3D).visible:
			dead.append(n)
	for n in dead:
		if is_instance_valid(n) and n.get_parent() != null:
			n.get_parent().remove_child(n)
			n.free()
	print("[export] nodos invisibles quitados: ", dead.size())

# ───────────────────────────── detección y pistas
func _animated_roots() -> Array:
	var r: Array = []
	for car in sc.core.cars:
		r.append(car.visual)
	return r

## Ubicación estable de un nodo: la lista de posiciones de hijo desde la raíz (los nombres automáticos «@Node3D@1062» cambian de una corrida a otra)
func _idx_path(n: Node) -> String:
	var parts: Array = []
	var cur: Node = n
	while cur != w3 and cur != null:
		parts.append(str(cur.get_index()))
		cur = cur.get_parent()
	parts.reverse()
	return ",".join(parts)

func _by_idx(path: String) -> Node3D:
	var cur: Node = w3
	for p in path.split(","):
		if p == "" or int(p) >= cur.get_child_count():
			return null
		cur = cur.get_child(int(p))
	return cur as Node3D

func _snapshot(rootn: Node) -> Dictionary:
	var d := {}
	for n in rootn.find_children("*", "Node3D", true, false):
		var n3 := n as Node3D
		d[_idx_path(n3)] = n3.transform
	return d

func _detect() -> void:
	var rootn: Node = w3
	sc._advance(12.0)
	sc._step_visuals(1.0 / 30.0)
	var a: Dictionary = {}
	for r in _animated_roots():
		a.merge(_snapshot(r))
	if sc.core.toll_node != null:
		a.merge(_snapshot(sc.core.toll_node))
	sc._advance(12.4)
	sc._step_visuals(1.0 / 30.0)
	var b: Dictionary = {}
	for r in _animated_roots():
		b.merge(_snapshot(r))
	if sc.core.toll_node != null:
		b.merge(_snapshot(sc.core.toll_node))
	var moving: Array = []
	for k in a.keys():
		if b.has(k):
			var ta: Transform3D = a[k]
			var tb: Transform3D = b[k]
			if not ta.is_equal_approx(tb):
				moving.append(k)
	var skel_moving := {}
	for k in sc.core.cars.size():
		for sk in sc.cockpits[k].find_children("*", "Skeleton3D", true, false):
			skel_moving[str(w3.get_path_to(sk))] = (sk as Skeleton3D).get_bone_count()
	var f := FileAccess.open("res://cine/animados.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"nodos": moving, "esqueletos": skel_moving}))
	f.close()
	print("[detect] nodos que se mueven: %d · esqueletos: %d" % [moving.size(), skel_moving.size()])

func _make_tracks() -> void:
	var info: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://cine/animados.json"))
	var nodes: Array = []
	for ip_str in info["nodos"]:
		var nd := _by_idx(str(ip_str))
		if nd != null:
			nodes.append(nd)
	for r in _animated_roots():
		nodes.append(r)
	nodes.append(sc.cam)
	for node in nodes:
		var p := str(w3.get_path_to(node))
		if tracks.has(p):
			continue
		var ip := anim.add_track(Animation.TYPE_POSITION_3D)
		anim.track_set_path(ip, NodePath(p))
		var ir := anim.add_track(Animation.TYPE_ROTATION_3D)
		anim.track_set_path(ir, NodePath(p))
		tracks[p] = {"ip": ip, "ir": ir, "node": node}
	# interior de cada cabina: escala 1 (se ve) o 0 (oculto) según la cámara
	for k in sc.core.cars.size():
		var inter: Node3D = sc.cockpits[k].interior
		inter.name = "Interior_%d" % k
		var p2 := str(w3.get_path_to(inter))
		var isc := anim.add_track(Animation.TYPE_SCALE_3D)
		anim.track_set_path(isc, NodePath(p2))
		tracks["__int%d" % k] = {"is": isc, "node": inter}
	# barreras del peaje
	for i in sc.core.toll_arms.size():
		var arm: Node3D = sc.core.toll_arms[i]
		arm.name = "Barrera_%d" % i
		var p3 := str(w3.get_path_to(arm))
		var ir2 := anim.add_track(Animation.TYPE_ROTATION_3D)
		anim.track_set_path(ir2, NodePath(p3))
		tracks["__arm%d" % i] = {"ir": ir2, "node": arm}
	# huesos de los pilotos (sólo los que mueve el juego)
	for k in sc.core.cars.size():
		for sk in sc.cockpits[k].find_children("*", "Skeleton3D", true, false):
			var skel := sk as Skeleton3D
			var sp := str(w3.get_path_to(skel))
			for b in skel.get_bone_count():
				var bn := skel.get_bone_name(b)
				var short := bn.get_slice(":", bn.get_slice_count(":") - 1).replace("mixamorig", "").replace("mixamorig_", "")
				var is_need := false
				for nd in NEED:
					if short.ends_with(nd) or short == nd:
						is_need = true
				if not is_need:
					continue
				var ir3 := anim.add_track(Animation.TYPE_ROTATION_3D)
				anim.track_set_path(ir3, NodePath(sp + ":" + bn))
				var ip3 := -1
				if short.ends_with("Hips"):
					ip3 = anim.add_track(Animation.TYPE_POSITION_3D)
					anim.track_set_path(ip3, NodePath(sp + ":" + bn))
				bone_tracks.append({"skel": skel, "bone": b, "ir": ir3, "ip": ip3})
				if short.ends_with("Head") and head_tracks.get(k, null) == null:
					var is3 := anim.add_track(Animation.TYPE_SCALE_3D)
					anim.track_set_path(is3, NodePath(sp + ":" + bn))
					head_tracks[k] = is3

func _record(f: int, t: float) -> void:
	for key in tracks.keys():
		var tr: Dictionary = tracks[key]
		var node: Node3D = tr["node"]
		if tr.has("ip"):
			anim.position_track_insert_key(int(tr["ip"]), t, node.position)
			anim.rotation_track_insert_key(int(tr["ir"]), t, node.basis.get_rotation_quaternion().normalized())
		elif tr.has("is"):
			var k := int(str(key).substr(5))
			anim.scale_track_insert_key(int(tr["is"]), t, Vector3.ONE if sc.dir.inside_car == k else Vector3.ONE * 0.0001)
		elif tr.has("ir"):
			anim.rotation_track_insert_key(int(tr["ir"]), t, node.basis.get_rotation_quaternion().normalized())
	# huesos: a 15 cuadros por segundo (Blender interpola)
	if f % 2 == 0:
		for bt in bone_tracks:
			var sk: Skeleton3D = bt["skel"]
			var b: int = bt["bone"]
			anim.rotation_track_insert_key(int(bt["ir"]), t, sk.get_bone_pose_rotation(b))
			if int(bt["ip"]) >= 0:
				anim.position_track_insert_key(int(bt["ip"]), t, sk.get_bone_pose_position(b))
	for kk in head_tracks.keys():
		anim.scale_track_insert_key(int(head_tracks[kk]), t, Vector3.ONE * (0.001 if sc.dir.inside_car == int(kk) else 1.0))
	for kq in sc.core.cars.size():
		var ph = sc.core.cars[kq].phys
		tele[kq]["slip"].append(snappedf(rad_to_deg(atan2(ph.vLat, maxf(1.0, absf(ph.vLong)))), 0.1))
		tele[kq]["frenada"].append(snappedf(sc.core.drivers[kq].brake, 0.01))
		tele[kq]["v"].append(snappedf(sqrt(ph.vx * ph.vx + ph.vz * ph.vz), 0.1))
	if args.has("diag"):
		var cp: Vector3 = sc.cam.global_position
		var fwd: Vector3 = -sc.cam.global_transform.basis.z
		var gy: float = sc.dir.ground_y(cp.x, cp.z)
		var blocked := false
		for dd in [1.5, 3.0, 5.0, 8.0]:
			var q: Vector3 = cp + fwd * dd
			if sc.dir.ground_y(q.x, q.z) > q.y + 0.15:
				blocked = true
		var ty := str(sc.dir.plan[sc.dir.cur]["type"])
		var rec: Array = diag.get(ty, [0, 0, 0])
		rec[0] += 1
		if cp.y < gy + 0.2:
			rec[1] += 1
		if blocked:
			rec[2] += 1
		diag[ty] = rec
	fov_log.append(sc.cam.fov)
	var shot: int = sc.dir.cur
	if shot != _last_shot:
		_last_shot = shot
		var sh: Dictionary = sc.dir.plan[shot]
		cuts.append({"cuadro": f, "t": snappedf(t, 0.01), "tipo": str(sh["type"]), "auto": int(sh.get("car", 0))})
	inside_log.append(sc.dir.inside_car)

func _write_json(t_end: float, n_frames: int) -> void:
	var cars_info: Array = []
	for k in sc.core.cars.size():
		var st: Dictionary = sc.core.states[k]
		cars_info.append({"indice": k, "id": sc.core.ids[k], "nombre": sc.core.names[k], "nodo": "Auto_%d_%s" % [k, sc.core.ids[k]], "pintura": st["paint"]})
	var d := {
		"formato": "estudio.rally_convoy_export/1", "fps": FPS, "cuadros": n_frames, "duracion_s": t_end,
		"fov_horizontal_por_cuadro": Array(fov_log), "cortes": cuts, "autos": cars_info,
		"auto_con_cabina_por_cuadro": inside_log, "telemetria": tele, "peaje_s": sc.core.toll_s, "ruta_m": sc.core.track.length,
		"nota": "fov_horizontal_por_cuadro: grados (Camera3D keep_aspect = ancho). Los cortes son saltos de cámara: interpolación en escalón en esos cuadros."
	}
	var f := FileAccess.open(_arg("out", "/home/user/rally_cine/salida/rally_convoy_godot.glb").get_basename() + ".json", FileAccess.WRITE)
	f.store_string(JSON.stringify(d, "\t"))
	f.close()

## Sólo la cámara: un GLB chico con la cámara animada (posición y rotación por cuadro) que se importa al BLEND en lugar de la anterior,
## y el JSON con cortes, zoom y telemetría. Sirve para corregir la dirección de cámaras sin repetir el export de 260 MB.
func _solo_camara(t_end: float) -> void:
	var croot := Node3D.new()
	croot.name = "CamRoot"
	var c2 := Camera3D.new()
	c2.name = "Camara"
	croot.add_child(c2)
	var ap := AnimationPlayer.new()
	ap.name = "Animacion"
	croot.add_child(ap)
	anim = Animation.new()
	anim.length = t_end
	anim.step = 1.0 / float(FPS)
	var lib := AnimationLibrary.new()
	lib.add_animation("toma", anim)
	ap.add_animation_library("", lib)
	var ip := anim.add_track(Animation.TYPE_POSITION_3D)
	anim.track_set_path(ip, NodePath("Camara"))
	var ir := anim.add_track(Animation.TYPE_ROTATION_3D)
	anim.track_set_path(ir, NodePath("Camara"))
	for k in sc.core.cars.size():
		tele.append({"slip": [], "frenada": [], "v": []})
	var n_frames := int(round(t_end * FPS))
	sc.fps = FPS
	for f in n_frames:
		var t := float(f) / float(FPS)
		sc._advance(t)
		sc._step_visuals(1.0 / float(FPS))
		anim.position_track_insert_key(ip, t, sc.cam.global_position)
		anim.rotation_track_insert_key(ir, t, sc.cam.global_transform.basis.get_rotation_quaternion().normalized())
		_record_datos(f, t)
		if f % 1500 == 0:
			print("[camara] cuadro %d/%d" % [f, n_frames])
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var e := doc.append_from_scene(croot, st)
	var out := _arg("out", "/home/user/rally_cine/salida/camara.glb")
	var e2 := doc.write_to_filesystem(st, out)
	print("[camara] escrito ", out, " ", e, " ", e2)
	_write_json(t_end, n_frames)
	quit()

func _record_datos(f: int, t: float) -> void:
	for kq in sc.core.cars.size():
		var ph = sc.core.cars[kq].phys
		tele[kq]["slip"].append(snappedf(rad_to_deg(atan2(ph.vLat, maxf(1.0, absf(ph.vLong)))), 0.1))
		tele[kq]["frenada"].append(snappedf(sc.core.drivers[kq].brake, 0.01))
		tele[kq]["v"].append(snappedf(sqrt(ph.vx * ph.vx + ph.vz * ph.vz), 0.1))
	fov_log.append(sc.cam.fov)
	var shot: int = sc.dir.cur
	if shot != _last_shot:
		_last_shot = shot
		var sh: Dictionary = sc.dir.plan[shot]
		cuts.append({"cuadro": f, "t": snappedf(t, 0.01), "tipo": str(sh["type"]), "auto": int(sh.get("car", 0))})
	inside_log.append(sc.dir.inside_car)
