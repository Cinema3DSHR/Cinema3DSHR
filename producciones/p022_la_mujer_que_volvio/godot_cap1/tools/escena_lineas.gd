## EXPERIMENTO DE ESTILO «LÍNEAS TÉCNICAS»: escena de prueba con muchos objetos de todas las clases (auto, casa, puerta, cajas, barriles, árboles, flores, farol, tubos) y los dos personajes
## (Aiden apuntando con la pistola USP, Kate de pie). Aquí sólo geometría + animación + cámaras con nombres que Blender reconoce; el tratamiento artístico (4 versiones) lo hace Blender.
## Uso: xvfb-run -a godot --path . --rendering-driver opengl3 --resolution 720x1280 --script res://tools/escena_lineas.gd -- SALIDA
extends SceneTree
const FPS := 30.0
const N := 91
const APUNTA := "point"
var esc: Node3D
var anim: Animation
func _mat(c: Color, rough := 0.8) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = c; m.roughness = rough; return m
func _add(nom: String, mesh: Mesh, pos: Vector3, col: Color, rot_deg := Vector3.ZERO, padre: Node = null) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); mi.mesh = mesh; mi.material_override = _mat(col); mi.name = nom; mi.position = pos; mi.rotation_degrees = rot_deg
	(padre if padre else esc).add_child(mi); return mi
func _caja(nom: String, pos: Vector3, tam: Vector3, col: Color, rot_deg := Vector3.ZERO, padre: Node = null) -> MeshInstance3D:
	var b := BoxMesh.new(); b.size = tam; return _add(nom, b, pos, col, rot_deg, padre)
func _cil(nom: String, pos: Vector3, r_sup: float, r_inf: float, alto: float, col: Color, rot_deg := Vector3.ZERO, seg := 24) -> MeshInstance3D:
	var c := CylinderMesh.new(); c.top_radius = r_sup; c.bottom_radius = r_inf; c.height = alto; c.radial_segments = seg; c.rings = 1; return _add(nom, c, pos, col, rot_deg)
func _esf(nom: String, pos: Vector3, r: float, col: Color, esc_v := Vector3.ONE) -> MeshInstance3D:
	var s := SphereMesh.new(); s.radius = r; s.height = r * 2.0; s.radial_segments = 20; s.rings = 10; var mi := _add(nom, s, pos, col); mi.scale = esc_v; return mi

func _arbol_pino(i: int, p: Vector3, alto: float) -> void:
	_cil("Veg_tronco_%d" % i, p + Vector3(0, alto * 0.18, 0), 0.10, 0.16, alto * 0.36, Color(0.35, 0.22, 0.12), Vector3.ZERO, 12)
	for k in 4:
		var u := float(k) / 4.0
		_cil("Veg_copa_%d_%d" % [i, k], p + Vector3(0, alto * (0.30 + 0.17 * k), 0), 0.02, alto * (0.30 - 0.06 * k), alto * 0.30, Color(0.12, 0.38, 0.18), Vector3.ZERO, 18)
func _arbol_hoja(i: int, p: Vector3, alto: float) -> void:
	_cil("Veg_tronco_%d" % i, p + Vector3(0, alto * 0.28, 0), 0.12, 0.19, alto * 0.56, Color(0.4, 0.27, 0.15), Vector3.ZERO, 12)
	_esf("Veg_copa_%d_0" % i, p + Vector3(0, alto * 0.72, 0), alto * 0.30, Color(0.2, 0.5, 0.2), Vector3(1.0, 0.85, 1.0))
	_esf("Veg_copa_%d_1" % i, p + Vector3(alto * 0.18, alto * 0.62, 0.05), alto * 0.20, Color(0.22, 0.55, 0.22))
	_esf("Veg_copa_%d_2" % i, p + Vector3(-alto * 0.17, alto * 0.64, -0.08), alto * 0.21, Color(0.18, 0.48, 0.2))
func _flor(i: int, p: Vector3, alto: float, col: Color) -> void:
	_cil("Veg_tallo_%d" % i, p + Vector3(0, alto * 0.5, 0), 0.008, 0.010, alto, Color(0.2, 0.5, 0.2), Vector3.ZERO, 6)
	_esf("Veg_centro_%d" % i, p + Vector3(0, alto, 0), 0.03, Color(0.95, 0.8, 0.2))
	for k in 7:
		var a := TAU * k / 7.0
		_esf("Veg_petalo_%d_%d" % [i, k], p + Vector3(cos(a) * 0.055, alto + 0.005, sin(a) * 0.055), 0.04, col, Vector3(1.0, 0.45, 1.0))
	_cil("Veg_hoja_%d" % i, p + Vector3(0.05, alto * 0.35, 0), 0.0, 0.02, 0.12, Color(0.2, 0.55, 0.22), Vector3(0, 0, -60), 6)

func _construir() -> void:
	_caja("Arq_suelo", Vector3(0, -0.05, 0), Vector3(40, 0.1, 40), Color(0.55, 0.52, 0.48))
	_caja("Arq_camino", Vector3(0, 0.004, 1.2), Vector3(5.0, 0.01, 12), Color(0.68, 0.65, 0.60))
	# casa: cuerpo, techo a dos aguas, puerta, ventanas, chimenea, escalón, tubo con franja roja
	var hc := Vector3(3.1, 0, -5.0)
	_caja("Arq_casa_cuerpo", hc + Vector3(0, 1.4, 0), Vector3(4.4, 2.8, 3.6), Color(0.78, 0.72, 0.62))
	_caja("Arq_casa_techo_L", hc + Vector3(-1.05, 3.25, 0), Vector3(2.7, 0.14, 4.0), Color(0.45, 0.22, 0.16), Vector3(0, 0, 30))
	_caja("Arq_casa_techo_R", hc + Vector3(1.05, 3.25, 0), Vector3(2.7, 0.14, 4.0), Color(0.45, 0.22, 0.16), Vector3(0, 0, -30))
	_caja("Arq_casa_chimenea", hc + Vector3(1.2, 3.7, -0.8), Vector3(0.5, 1.2, 0.5), Color(0.55, 0.3, 0.25))
	_caja("Arq_puerta_casa", hc + Vector3(-0.9, 1.0, 1.82), Vector3(1.0, 2.0, 0.08), Color(0.35, 0.2, 0.12))
	_caja("Arq_puerta_marco", hc + Vector3(-0.9, 1.05, 1.80), Vector3(1.2, 2.1, 0.05), Color(0.9, 0.9, 0.9))
	_caja("Arq_escalon", hc + Vector3(-0.9, 0.08, 2.15), Vector3(1.6, 0.16, 0.6), Color(0.6, 0.6, 0.6))
	for k in 2:
		_caja("Arq_ventana_%d" % k, hc + Vector3(0.8 + 1.0 * k, 1.5, 1.82), Vector3(0.8, 1.0, 0.06), Color(0.25, 0.32, 0.4), Vector3.ZERO)
		_caja("Arq_ventana_marco_%d" % k, hc + Vector3(0.8 + 1.0 * k, 1.5, 1.80), Vector3(0.95, 1.15, 0.05), Color(0.92, 0.92, 0.92))
	_cil("Rojo_tubo", hc + Vector3(-2.25, 1.4, 1.0), 0.07, 0.07, 2.8, Color(0.85, 0.1, 0.1))
	# puerta suelta con marco (la hoja abierta a 55°)
	var pm := Vector3(-0.4, 0, -0.6)
	_caja("Arq_marco_L", pm + Vector3(-0.55, 1.05, 0), Vector3(0.1, 2.1, 0.12), Color(0.5, 0.5, 0.5))
	_caja("Arq_marco_R", pm + Vector3(0.55, 1.05, 0), Vector3(0.1, 2.1, 0.12), Color(0.5, 0.5, 0.5))
	_caja("Arq_marco_arriba", pm + Vector3(0, 2.1, 0), Vector3(1.2, 0.1, 0.12), Color(0.5, 0.5, 0.5))
	var hoja := _caja("Arq_hoja_puerta", pm + Vector3(0.55 - cos(deg_to_rad(55)) * 0.5, 1.0, sin(deg_to_rad(55)) * 0.5), Vector3(1.0, 2.0, 0.06), Color(0.4, 0.3, 0.2), Vector3(0, -55, 0))
	_caja("Obj_manija", hoja.position + Vector3(0.0, 0.0, 0.0), Vector3(0.001, 0.001, 0.001), Color(0.8, 0.7, 0.2))
	# cajas apiladas y barriles
	_caja("Obj_caja_1", Vector3(-2.7, 0.4, -0.3), Vector3(0.8, 0.8, 0.8), Color(0.7, 0.55, 0.3), Vector3(0, 12, 0))
	_caja("Obj_caja_2", Vector3(-1.95, 0.35, 0.0), Vector3(0.7, 0.7, 0.7), Color(0.66, 0.5, 0.28), Vector3(0, -8, 0))
	_caja("Obj_caja_3", Vector3(-2.6, 1.2, -0.25), Vector3(0.65, 0.65, 0.65), Color(0.72, 0.58, 0.32), Vector3(0, 28, 0))
	_caja("Obj_caja_4", Vector3(-3.2, 0.25, 0.5), Vector3(0.5, 0.5, 0.5), Color(0.6, 0.46, 0.26), Vector3(0, 40, 0))
	for k in 2:
		var bp := Vector3(2.2 + 0.7 * k, 0.45, 0.2 + 0.4 * k)
		_cil("Obj_barril_%d" % k, bp, 0.30, 0.30, 0.9, Color(0.25, 0.35, 0.55), Vector3.ZERO, 28)
		_cil("Obj_barril_aro_a_%d" % k, bp + Vector3(0, 0.25, 0), 0.31, 0.31, 0.04, Color(0.7, 0.7, 0.72), Vector3.ZERO, 28)
		_cil("Obj_barril_aro_b_%d" % k, bp + Vector3(0, -0.25, 0), 0.31, 0.31, 0.04, Color(0.7, 0.7, 0.72), Vector3.ZERO, 28)
	_cil("Rojo_extintor", Vector3(2.9, 0.3, -1.4), 0.09, 0.09, 0.6, Color(0.85, 0.1, 0.1), Vector3.ZERO, 16)
	_cil("Obj_extintor_cuello", Vector3(2.9, 0.65, -1.4), 0.03, 0.03, 0.1, Color(0.2, 0.2, 0.2), Vector3.ZERO, 10)
	# farol y valla baja
	_cil("Obj_farol_poste", Vector3(1.7, 1.3, -1.6), 0.04, 0.06, 2.6, Color(0.3, 0.3, 0.32), Vector3.ZERO, 12)
	_caja("Obj_farol_cabeza", Vector3(1.7, 2.65, -1.6), Vector3(0.35, 0.18, 0.35), Color(0.9, 0.85, 0.6))
	for k in 8:
		_caja("Arq_valla_poste_%d" % k, Vector3(-5.5 + 0.9 * k, 0.4, -3.2), Vector3(0.08, 0.8, 0.08), Color(0.9, 0.88, 0.82))
	_caja("Arq_valla_riel_a", Vector3(-2.2, 0.62, -3.2), Vector3(6.4, 0.06, 0.04), Color(0.9, 0.88, 0.82))
	_caja("Arq_valla_riel_b", Vector3(-2.2, 0.28, -3.2), Vector3(6.4, 0.06, 0.04), Color(0.9, 0.88, 0.82))
	# árboles
	_arbol_pino(0, Vector3(-3.4, 0, -5.8), 4.4); _arbol_pino(1, Vector3(0.6, 0, -9.0), 5.2)
	_arbol_hoja(2, Vector3(4.3, 0, -0.4), 3.6); _arbol_hoja(3, Vector3(-4.8, 0, -1.0), 3.2)
	# flores en el primer plano
	var rng := RandomNumberGenerator.new(); rng.seed = 11
	var cols := [Color(0.95, 0.35, 0.45), Color(0.98, 0.85, 0.3), Color(0.55, 0.45, 0.9), Color(1.0, 1.0, 1.0), Color(0.95, 0.55, 0.2)]
	for i in 22:
		_flor(i, Vector3(rng.randf_range(-1.7, 1.7), 0, rng.randf_range(3.4, 5.0)), rng.randf_range(0.28, 0.5), cols[i % cols.size()])
	# auto (modelo original del proyecto) a la izquierda, detrás
	var carro := Node3D.new(); carro.name = "AutoRaiz"; esc.add_child(carro)
	var ps: PackedScene = load("res://assets/hustler.glb")
	var modelo: Node3D = ps.instantiate(); carro.add_child(modelo); modelo.rotation.y = PI
	carro.position = Vector3(-1.7, 0.0, -1.5); carro.rotation.y = deg_to_rad(38)

func _pista(n: Node, pos := true, rot := true) -> Array:
	var p := esc.get_path_to(n); var r := [-1, -1]
	if pos: r[0] = anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(r[0], p)
	if rot: r[1] = anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(r[1], p)
	return r

func _initialize() -> void:
	_montar(OS.get_cmdline_user_args())

func _montar(a: PackedStringArray) -> void:
	await process_frame
	esc = Node3D.new(); esc.name = "Escena"; root.add_child(esc)
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-50, 35, 0); luz.light_energy = 1.2; root.add_child(luz)
	var wenv := WorldEnvironment.new(); var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.8, 0.82, 0.85); env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.8, 0.8, 0.85); env.ambient_light_energy = 0.7; wenv.environment = env; root.add_child(wenv)
	anim = Animation.new(); anim.length = float(N - 1) / FPS; anim.step = 1.0 / FPS; anim.loop_mode = Animation.LOOP_NONE
	var ap := AnimationPlayer.new(); ap.name = "Anim"; esc.add_child(ap)
	_construir()
	var G := Actor3.new(); G.cargar("aiden", "res://assets/aiden_noir.glb", "res://assets/aiden_meta.json", esc)
	var K := Actor3.new(); K.cargar("kate", "res://assets/kate_noir.glb", "res://assets/kate_meta.json", esc)
	G.raiz.position = Vector3(-0.35, 0, 1.9); G.raiz.rotation.y = deg_to_rad(125)      # mira hacia la casa, a la derecha del cuadro
	K.raiz.position = Vector3(1.05, 0, 3.0); K.raiz.rotation.y = deg_to_rad(-20)        # de pie, mirando hacia la cámara y un poco a la izquierda
	var pis: Node3D = (load("res://assets/pistola_USP.glb") as PackedScene).instantiate(); pis.name = "Arma_USP"; esc.add_child(pis)
	var laser := _cil("Rojo_laser", Vector3.ZERO, 0.004, 0.004, 9.0, Color(1.0, 0.05, 0.05), Vector3(90, 0, 0), 6); esc.remove_child(laser); pis.add_child(laser); laser.position = Vector3(0, 0.045, 4.6)
	await process_frame
	var ps := {}
	for ac in [G, K]:
		var d := {}
		for h in ac.sk.get_bone_count():
			var tq := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tq, NodePath("%s:%s" % [esc.get_path_to(ac.sk), ac.sk.get_bone_name(h)])); d[h] = tq
		var th := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(th, NodePath("%s:%s" % [esc.get_path_to(ac.sk), ac.sk.get_bone_name(ac.hueso_cadera)])); d["pos"] = th
		ps[ac] = d
	var p_pis := _pista(pis); var p_gr := _pista(G.raiz)
	# cámaras: principal (fija, vertical) y de movimiento (acercándose y lateral)
	var cam := Camera3D.new(); cam.name = "Cam_principal"; cam.fov = 46.0; cam.near = 0.05; cam.far = 120.0; esc.add_child(cam); cam.position = Vector3(2.5, 2.0, 8.6); cam.look_at(Vector3(0.1, 1.2, 0.6), Vector3.UP)
	var cm := Camera3D.new(); cm.name = "Cam_movimiento"; cm.fov = 50.0; cm.near = 0.05; cm.far = 120.0; esc.add_child(cm); var p_cm := _pista(cm)
	var g0 := G.raiz.position; var gdir := Vector3(sin(G.raiz.rotation.y), 0, cos(G.raiz.rotation.y))
	for g in N:
		var t := float(g) / FPS
		# Aiden camina 1,5 s hacia la casa y se detiene apuntando; Kate respira de pie
		var kc := 45
		if g < kc:
			G.poner_pose(G.pose_clip("walk", g, true)); var rc := G.raiz_clip("walk", g)
			G.raiz.position = g0 - gdir * (kc - g) * 0.04 + gdir * 0.0
		else:
			G.poner_pose(G.pose_clip(APUNTA, g - kc, false)); G.raiz.position = g0
		K.poner_pose(K.pose_clip("idle", g, true))
		for ac in [G, K]:
			for h in ac.sk.get_bone_count(): anim.rotation_track_insert_key(ps[ac][h], t, ac.sk.get_bone_pose_rotation(h))
			anim.position_track_insert_key(ps[ac]["pos"], t, ac.sk.get_bone_pose_position(ac.hueso_cadera))
		anim.position_track_insert_key(p_gr[0], t, G.raiz.position); anim.rotation_track_insert_key(p_gr[1], t, G.raiz.basis.get_rotation_quaternion())
		# pistola en la mano derecha, cañón a lo largo del antebrazo
		var hm: int = G.mano["R"]; var antebrazo := G.sk.get_bone_parent(hm)
		var ph: Vector3 = G.sk.global_transform * G.sk.get_bone_global_pose(hm).origin; var pa: Vector3 = G.sk.global_transform * G.sk.get_bone_global_pose(antebrazo).origin
		var dir := (ph - pa).normalized(); var arriba := Vector3.UP; var x := arriba.cross(dir).normalized(); var yv := dir.cross(x).normalized()
		pis.global_transform = Transform3D(Basis(x, yv, dir), ph + dir * 0.04 - yv * 0.02)
		anim.position_track_insert_key(p_pis[0], t, pis.position); anim.rotation_track_insert_key(p_pis[1], t, pis.basis.get_rotation_quaternion())
		var u := smoothstep(0.0, 1.0, float(g) / float(N - 1))
		cm.global_position = Vector3(3.2 - 1.8 * u, 2.2 - 0.5 * u, 10.5 - 3.8 * u) + Vector3(-1.6 * u, 0, 0)
		cm.look_at(Vector3(0.2 - 0.7 * u, 1.2, 0.6), Vector3.UP)
		anim.position_track_insert_key(p_cm[0], t, cm.position); anim.rotation_track_insert_key(p_cm[1], t, cm.basis.get_rotation_quaternion())
	var lib := AnimationLibrary.new(); lib.add_animation("escena", anim); ap.add_animation_library("", lib); ap.assigned_animation = "escena"
	var pre: String = a[0]
	cam.current = true; ap.seek(56.0 / FPS, true)
	for i in 4: await process_frame
	root.get_viewport().get_texture().get_image().save_png(pre + "_godot.png")
	ap.seek(0.0, true)
	var doc := GLTFDocument.new(); var st := GLTFState.new(); doc.append_from_scene(esc, st)
	print("GLB ", pre, ".glb err=", doc.write_to_filesystem(st, pre + ".glb"))
	var js := {"formato": "estudio.previa_godot/1", "escena_id": "escena_lineas", "fps": int(FPS), "frames": N, "resolucion": [720, 1280], "animacion": "escena", "camaras": ["Cam_principal", "Cam_movimiento"], "cuadro_pose": 57}
	var fa := FileAccess.open(pre + ".json", FileAccess.WRITE); fa.store_string(JSON.stringify(js, "  ")); fa.close()
	quit()
