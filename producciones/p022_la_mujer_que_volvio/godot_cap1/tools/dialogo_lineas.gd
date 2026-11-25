## DIÁLOGO DE PRUEBA PARA EL ESTILO «E»: Aiden y Kate de frente a la cámara, uno al lado del otro, 10 s. Hablan (labios por las letras del texto, SIN audio), mueven las manos con clips de
## «hablar» de Mixamo, parpadean, miran a la cámara y al otro con micro-movimientos de ojos, cejas y cabeza. Sólo geometría + animación con nombres que reconoce Blender; el estilo lo pone Blender.
## Uso: xvfb-run -a godot --path . --rendering-driver opengl3 --resolution 720x1280 --script res://tools/dialogo_lineas.gd -- SALIDA
extends SceneTree
const FPS := 30.0
const DUR := 10.0
const Cara := preload("res://tools/cara.gd")
var esc: Node3D
var anim: Animation
func _caja(nom: String, pos: Vector3, tam: Vector3, col: Color) -> void:
	var mi := MeshInstance3D.new(); var b := BoxMesh.new(); b.size = tam; mi.mesh = b; var m := StandardMaterial3D.new(); m.albedo_color = col; mi.material_override = m; mi.name = nom; mi.position = pos; esc.add_child(mi)
func _ruta(n: Node) -> NodePath: return esc.get_path_to(n)
func _initialize() -> void: _montar(OS.get_cmdline_user_args())

func _montar(a: PackedStringArray) -> void:
	await process_frame
	esc = Node3D.new(); esc.name = "Escena"; root.add_child(esc)
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-30, 25, 0); luz.light_energy = 1.2; root.add_child(luz)
	var wenv := WorldEnvironment.new(); var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.6, 0.62, 0.66); env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.75, 0.75, 0.8); wenv.environment = env; root.add_child(wenv)
	_caja("Arq_pared", Vector3(0, 1.6, -1.2), Vector3(8, 3.4, 0.1), Color(0.8, 0.78, 0.74)); _caja("Arq_piso", Vector3(0, -0.05, 0.4), Vector3(8, 0.1, 6), Color(0.62, 0.58, 0.52))
	_caja("Arq_zocalo", Vector3(0, 0.12, -1.12), Vector3(8, 0.24, 0.06), Color(0.9, 0.9, 0.88))
	var total := int(DUR * FPS) + 1
	anim = Animation.new(); anim.length = float(total - 1) / FPS; anim.step = 1.0 / FPS; anim.loop_mode = Animation.LOOP_NONE
	var ap := AnimationPlayer.new(); ap.name = "Anim"; esc.add_child(ap)
	var A := Actor3.new(); A.cargar("aiden", "res://assets/aiden_noir.glb", "res://assets/aiden_meta.json", esc)
	var K := Actor3.new(); K.cargar("kate", "res://assets/kate_noir.glb", "res://assets/kate_meta.json", esc)
	A.raiz.position = Vector3(-0.25, 0, 0.0); A.raiz.rotation.y = deg_to_rad(8); K.raiz.position = Vector3(0.25, 0, 0.0); K.raiz.rotation.y = deg_to_rad(-8)
	for ac0 in [A, K]:                                                                              # aros sueltos (cuello y cinturón): no van en este plano
		for nm in ["COLLAR", "CINTURON", "CINTURON_hebilla"]:
			var n0: Node = ac0.raiz.find_child(nm, true, false)
			if n0 != null: n0.queue_free()
	await process_frame
	var actores := {"aiden": A, "kate": K}
	# texto, miradas y expresiones (Cara las toma de este diccionario)
	var lin: Array = JSON.parse_string(FileAccess.get_file_as_string("res://assets/dialogo_lineas.json"))
	var voces := []
	var exp := [{"aiden": "preocupado", "kate": "sorpresa"}, {"kate": "triste_sutil", "aiden": "preocupado_seria"}, {"aiden": "preocupado", "kate": "seria"}, {"kate": "seria", "aiden": "sorpresa"}]
	for i in lin.size():
		voces.append({"quien": lin[i]["quien"], "t": lin[i]["t"], "alineacion_res": "assets/dialogo_%d.json" % i, "exp": exp[i]})
	var miradas := [
		{"actor": "aiden", "t0": 0.2, "t1": 1.6, "a": [0.0, 1.35, 2.0], "peso_cabeza": 0.3}, {"actor": "aiden", "t0": 1.6, "t1": 2.6, "a": "kate", "peso_cabeza": 0.4}, {"actor": "aiden", "t0": 2.6, "t1": 3.7, "a": [0.0, 1.35, 2.0], "peso_cabeza": 0.3},
		{"actor": "kate", "t0": 0.2, "t1": 3.9, "a": "aiden", "peso_cabeza": 0.45}, {"actor": "aiden", "t0": 4.0, "t1": 7.2, "a": "kate", "peso_cabeza": 0.5},
		{"actor": "kate", "t0": 4.1, "t1": 5.4, "a": [0.0, 1.35, 2.0], "peso_cabeza": 0.3}, {"actor": "kate", "t0": 5.4, "t1": 6.3, "a": "aiden", "peso_cabeza": 0.4}, {"actor": "kate", "t0": 6.3, "t1": 7.2, "a": [0.0, 1.35, 2.0], "peso_cabeza": 0.3},
		{"actor": "aiden", "t0": 7.3, "t1": 8.7, "a": [0.0, 1.35, 2.0], "peso_cabeza": 0.3}, {"actor": "kate", "t0": 7.3, "t1": 8.7, "a": "aiden", "peso_cabeza": 0.5},
		{"actor": "kate", "t0": 8.8, "t1": 9.9, "a": [0.0, 1.35, 2.0], "peso_cabeza": 0.35}, {"actor": "aiden", "t0": 8.8, "t1": 9.9, "a": "kate", "peso_cabeza": 0.5}]
	var sb := {"dur": DUR, "titulo": "dialogo_lineas", "voces": voces, "miradas": miradas}
	var cf := Cara.new(); cf.preparar(sb, actores)
	# plan de clips (manos que hablan): [t0, clip] por actor
	var plan := {"aiden": [[0.0, "talk1"], [4.0, "idle"], [7.2, "talk3"], [8.7, "idle"]], "kate": [[0.0, "idle"], [4.0, "talk3"], [7.2, "thinking"], [8.7, "talk1"]]}
	var tr_hueso := {}; var tr_raiz := {}
	for id in actores:
		var ac = actores[id]; var hs := {}
		var tq := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tq, _ruta(ac.raiz)); tr_raiz[id] = tq
		for h in ac.clips["idle"]["rot"]:
			var tt := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tt, NodePath("%s:%s" % [_ruta(ac.sk), ac.sk.get_bone_name(h)])); hs[h] = tt
		var th := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(th, NodePath("%s:%s" % [_ruta(ac.sk), ac.sk.get_bone_name(ac.hueso_cadera)])); hs["pos"] = th
		tr_hueso[id] = hs
	cf.crear_pistas(anim, esc)
	# micro-movimientos: sacadas de los ojos, cabeceos con el ritmo del habla, ceja que sube en los énfasis
	var rng := RandomNumberGenerator.new(); rng.seed = 77
	var sacada := {"aiden": Vector2.ZERO, "kate": Vector2.ZERO}; var prox := {"aiden": 0.6, "kate": 1.0}
	var cam := Camera3D.new(); cam.name = "Cam_principal"; cam.fov = 55.0; cam.near = 0.05; cam.far = 80.0; esc.add_child(cam)
	var p_cam := [anim.add_track(Animation.TYPE_POSITION_3D), anim.add_track(Animation.TYPE_ROTATION_3D)]
	anim.track_set_path(p_cam[0], _ruta(cam)); anim.track_set_path(p_cam[1], _ruta(cam))
	for g in total:
		var t := float(g) / FPS
		for id in actores:
			var ac = actores[id]
			var pl: Array = plan[id]; var idx := 0
			for i in pl.size():
				if t >= float(pl[i][0]): idx = i
			var k := g - int(float(pl[idx][0]) * FPS)
			var pose: Dictionary = ac.pose_clip(pl[idx][1], k, true)
			if idx > 0 and float(t) - float(pl[idx][0]) < 0.45:                                   # fundido con el clip anterior
				var kp := g - int(float(pl[idx - 1][0]) * FPS)
				var w := clampf((t - float(pl[idx][0])) / 0.45, 0.0, 1.0); w = w * w * (3.0 - 2.0 * w)
				pose = Actor3.mezcla(ac.pose_clip(pl[idx - 1][1], kp, true), pose, w)
			ac.poner_pose(pose)
			cf.aplicar(id, ac, t, g)
			# sacadas de ojos: salto chico cada 0,5–1,6 s y deriva lenta
			prox[id] -= 1.0 / FPS
			if prox[id] <= 0.0:
				sacada[id] = Vector2(rng.randf_range(-1.0, 1.0), rng.randf_range(-0.6, 0.6)) * 2.2; prox[id] = rng.randf_range(0.5, 1.6)
			var fase: float = 0.0 if id == "aiden" else 1.7
			var sac: Vector2 = sacada[id] + Vector2(sin(t * 1.3 + fase), cos(t * 1.7 + fase)) * 0.5
			for l in ["L", "R"]:
				var h: int = ac.ojo[l]
				if h >= 0:
					var q0: Quaternion = ac.sk.get_bone_pose_rotation(h)
					ac.sk.set_bone_pose_rotation(h, q0 * Quaternion(Vector3.UP, deg_to_rad(sac.x)) * Quaternion(Vector3.RIGHT, deg_to_rad(sac.y)))
			# cabeza: cabeceo suave con el ritmo de la voz y pequeñas inclinaciones
			var habla := 0.0
			for v in voces:
				if v["quien"] == id and t >= float(v["t"]) and t <= float(v["t"]) + float(lin[voces.find(v)]["dur"]): habla = 1.0
			var hb: int = ac.cabeza
			var qh: Quaternion = ac.sk.get_bone_pose_rotation(hb)
			var ca: float = sin(t * 5.2 + fase) * 1.1 * habla + sin(t * 0.9 + fase) * 0.8
			var cb: float = sin(t * 3.1 + fase * 2.0) * 0.9 * habla + sin(t * 0.6 + fase) * 0.7
			ac.sk.set_bone_pose_rotation(hb, qh * Quaternion(Vector3.RIGHT, deg_to_rad(ca)) * Quaternion(Vector3.FORWARD, deg_to_rad(cb)))
		for id in actores:
			var ac2 = actores[id]
			anim.rotation_track_insert_key(tr_raiz[id], t, Quaternion(Vector3.UP, ac2.raiz.rotation.y))
			var hs2: Dictionary = tr_hueso[id]
			for h in hs2:
				if h is String: continue
				anim.rotation_track_insert_key(hs2[h], t, ac2.sk.get_bone_pose_rotation(h))
			anim.position_track_insert_key(hs2["pos"], t, ac2.sk.get_bone_pose_position(ac2.hueso_cadera))
			cf.claves(id, anim, t)
		# cámara: empuje lento hacia los dos
		var u := smoothstep(0.0, 1.0, t / DUR)
		cam.position = Vector3(0.0, 1.06 - 0.02 * u, 1.85 - 0.18 * u); cam.look_at(Vector3(0.0, 1.06, 0.0), Vector3.UP)
		anim.position_track_insert_key(p_cam[0], t, cam.position); anim.rotation_track_insert_key(p_cam[1], t, cam.basis.get_rotation_quaternion())
	var lib := AnimationLibrary.new(); lib.add_animation("escena", anim); ap.add_animation_library("", lib); ap.assigned_animation = "escena"
	var pre: String = a[0]
	cam.current = true
	for fr in [1.0, 3.0, 5.5, 8.0, 9.5]:
		ap.seek(fr, true)
		for i in 3: await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_g%d.png" % [pre, int(fr * 10)])
	ap.seek(0.0, true)
	var doc := GLTFDocument.new(); var st := GLTFState.new(); doc.append_from_scene(esc, st)
	print("GLB ", pre, ".glb err=", doc.write_to_filesystem(st, pre + ".glb"))
	quit()
