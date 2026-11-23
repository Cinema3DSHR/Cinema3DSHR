## Escena del VIAJE bajo la lluvia (cap. 1): Gabriel (volante) y Elena en el cupé negro, ruta mojada que pasa, faros, limpiaparabrisas, ruedas.
## Hornea cuadro a cuadro (30 fps) y exporta GLB + JSON para el visor/Blender.  Vertical 540×960.
## Uso: xvfb-run -a godot --path . --rendering-driver opengl3 --resolution 540x960 --script res://tools/viaje.gd -- SALIDA [segundos] [sin_glb]
extends SceneTree
const FPS := 30.0
const V := 22.0                        # m/s (≈ 80 km/h)
const PISO := -0.50                    # piso de la cabina
const SUELO := -0.75                   # base de las ruedas = asfalto
var DUR := 25.0
var esc: Node3D
var anim: Animation
var ap: AnimationPlayer
var mundo: Node3D
var auto: Node3D
var limp: Array
var G: Actor3
var E: Actor3
var RG: RigSentado
var RE: RigSentado
var pistas := {}
var total := 0
var ruedas := {}
var vol_rul: Node3D
var cams := {}
const TOMAS := [
	{"id": "t1", "camara": "C1_exterior_frente", "t0": 0.0, "t1": 6.0, "pos": [-2.6, -0.35, -7.0], "pos_fin": [-2.1, -0.25, -4.4], "mira": [0.0, -0.1, -1.8], "mira_fin": [0.15, 0.05, -0.6], "fov": 42.0, "mano": 0.0},
	{"id": "t2", "camara": "C2_sobre_hombro", "t0": 6.0, "t1": 12.0, "pos": [0.52, 0.52, 1.15], "pos_fin": [0.46, 0.50, 0.95], "mira": [0.25, 0.22, -0.7], "mira_fin": [0.20, 0.25, -0.7], "fov": 58.0, "mano": 0.004},
	{"id": "t3", "camara": "C3_perfil_ambos", "t0": 12.0, "t1": 18.0, "pos": [3.0, 0.30, 1.0], "pos_fin": [2.7, 0.28, 0.45], "mira": [0.0, 0.18, 0.05], "mira_fin": [0.0, 0.2, 0.0], "fov": 36.0, "mano": 0.0},
	{"id": "t4", "camara": "C4_rostro_gabriel", "t0": 18.0, "t1": 22.5, "pos": [0.02, 0.33, -0.32], "pos_fin": [0.08, 0.34, -0.27], "mira": [0.36, 0.44, 0.2], "mira_fin": [0.36, 0.45, 0.2], "fov": 32.0, "mano": 0.003},
	{"id": "t5", "camara": "C5_faros", "t0": 22.5, "t1": 25.0, "pos": [0.5, -0.62, -9.5], "pos_fin": [0.3, -0.56, -5.8], "mira": [0.0, 0.0, -1.8], "mira_fin": [0.0, 0.0, -1.8], "fov": 36.0, "mano": 0.0}]
const RELAMPAGOS := [5.1, 12.4, 19.7]       # s (los truenos del sonido caen ~0,8 s después)
const BOTELLA := 0

func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	if a.size() > 1 and a[1].is_valid_float():
		DUR = float(a[1])
	_montar(a[0], a.size() > 2 and a[2] == "sin_glb")

func _pista(n: Node, pos := true, rot := true, sc := false) -> Array:
	var p := esc.get_path_to(n)
	var r := [-1, -1, -1]
	if pos: r[0] = anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(r[0], p)
	if rot: r[1] = anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(r[1], p)
	if sc: r[2] = anim.add_track(Animation.TYPE_SCALE_3D); anim.track_set_path(r[2], p)
	return r

func _clave(pt: Array, n: Node3D, t: float, local := true) -> void:
	if pt[0] >= 0: anim.position_track_insert_key(pt[0], t, n.position if local else n.global_position)
	if pt[1] >= 0: anim.rotation_track_insert_key(pt[1], t, n.transform.basis.get_rotation_quaternion() if local else n.global_transform.basis.get_rotation_quaternion())
	if pt[2] >= 0: anim.scale_track_insert_key(pt[2], t, n.scale)

func _mat(c: Color, r := 0.5, m := 0.0) -> StandardMaterial3D:
	var s := StandardMaterial3D.new(); s.albedo_color = c; s.roughness = r; s.metallic = m; return s

func _caja(p: Node, nom: String, pos: Vector3, tam: Vector3, m: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var b := BoxMesh.new(); b.size = tam; mi.mesh = b; mi.material_override = m; mi.name = nom; mi.position = pos; p.add_child(mi); return mi

func _construir_mundo() -> void:
	mundo = Node3D.new(); mundo.name = "Mundo"; esc.add_child(mundo)
	var asf := _mat(Color(0.018, 0.018, 0.022), 0.08, 0.25)
	_caja(mundo, "Asfalto", Vector3(0, SUELO - 0.05, -300), Vector3(8.0, 0.1, 800), asf)
	var blanco := _mat(Color(0.8, 0.8, 0.75), 0.4)
	var rng := RandomNumberGenerator.new(); rng.seed = 4242
	for i in 90:                                                     # rayas del centro cada 9 m
		_caja(mundo, "Raya_%d" % i, Vector3(0, SUELO + 0.003, 80 - i * 9.0), Vector3(0.14, 0.006, 3.2), blanco)
	_caja(mundo, "BordeIzq", Vector3(-3.7, SUELO + 0.003, -300), Vector3(0.12, 0.006, 800), blanco)
	_caja(mundo, "BordeDer", Vector3(3.7, SUELO + 0.003, -300), Vector3(0.12, 0.006, 800), blanco)
	var roca := _mat(Color(0.05, 0.05, 0.055), 0.9)
	_caja(mundo, "ParedRoca", Vector3(-8.0, 3.0, -300), Vector3(6.0, 9.0, 800), roca)                  # lado montaña
	_caja(mundo, "Barranco", Vector3(11.5, -6.0, -300), Vector3(14.0, 0.5, 800), _mat(Color(0.02, 0.02, 0.025), 0.9))   # fondo del precipicio
	var metal := _mat(Color(0.2, 0.2, 0.22), 0.35, 0.8)
	_caja(mundo, "Baranda", Vector3(4.4, SUELO + 0.65, -300), Vector3(0.08, 0.28, 800), metal)
	for i in 200:                                                    # postes de la baranda cada 4 m
		_caja(mundo, "Poste_%d" % i, Vector3(4.4, SUELO + 0.35, 90 - i * 4.0), Vector3(0.1, 0.7, 0.1), metal)
	var tronco := _mat(Color(0.04, 0.03, 0.025), 0.9); var hoja := _mat(Color(0.02, 0.05, 0.035), 0.9)
	for i in 70:                                                     # árboles de la montaña y del borde del barranco
		var z := 90.0 - i * 11.0 + rng.randf_range(-3, 3)
		for lado in [-1, 1]:
			var x: float = lado * rng.randf_range(5.3, 6.4) if lado < 0 else rng.randf_range(5.0, 9.0)
			var h := rng.randf_range(4.0, 8.0)
			var tr := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 0.12; cm.bottom_radius = 0.2; cm.height = h * 0.45; tr.mesh = cm; tr.material_override = tronco
			tr.position = Vector3(x, SUELO + h * 0.22, z); tr.name = "Tronco_%d_%d" % [i, lado]; mundo.add_child(tr)
			var co := MeshInstance3D.new(); var cn := CylinderMesh.new(); cn.top_radius = 0.0; cn.bottom_radius = rng.randf_range(1.1, 1.8); cn.height = h; co.mesh = cn; co.material_override = hoja
			co.position = Vector3(x, SUELO + h * 0.45 + h * 0.5, z); co.name = "Copa_%d_%d" % [i, lado]; mundo.add_child(co)
	# montañas lejanas (fuera de «Mundo»: no se mueven)
	for k in 7:
		var mt := MeshInstance3D.new(); var cn2 := CylinderMesh.new(); cn2.top_radius = 0.0; cn2.bottom_radius = rng.randf_range(35, 70); cn2.height = rng.randf_range(60, 140); mt.mesh = cn2
		mt.material_override = _mat(Color(0.03, 0.035, 0.05), 1.0); mt.position = Vector3(-120 + k * 45 + rng.randf_range(-12, 12), cn2.height * 0.5 - 20, -420 + rng.randf_range(-40, 20)); mt.name = "Montana_%d" % k; esc.add_child(mt)

func _luces() -> void:
	for lado in [-1.0, 1.0]:
		var sp := SpotLight3D.new(); sp.name = "Faro_" + ("L" if lado < 0 else "R"); sp.position = Vector3(lado * 0.52, -0.02, -1.95)
		sp.rotation_degrees = Vector3(-5.0, 0, 0); sp.spot_range = 55.0; sp.spot_angle = 24.0; sp.spot_attenuation = 0.6; sp.light_energy = 9.0; sp.light_color = Color(1.0, 0.94, 0.8); auto.add_child(sp)
	var cola := OmniLight3D.new(); cola.name = "Luz_Trasera"; cola.position = Vector3(0, -0.05, 2.35); cola.light_color = Color(1, 0.05, 0.03); cola.light_energy = 0.12; cola.omni_range = 2.5; auto.add_child(cola)
	var tablero := OmniLight3D.new(); tablero.name = "Luz_Tablero"; tablero.position = Vector3(0.3, 0.05, -0.35); tablero.light_color = Color(0.3, 1.0, 0.6); tablero.light_energy = 0.03; tablero.omni_range = 0.6; auto.add_child(tablero)
	var rayo := DirectionalLight3D.new(); rayo.name = "Luz_Rayo"; rayo.rotation_degrees = Vector3(-50, 40, 0); rayo.light_color = Color(0.7, 0.8, 1.0); rayo.light_energy = 0.0; esc.add_child(rayo)
	var luna := DirectionalLight3D.new(); luna.name = "Luz_Luna"; luna.rotation_degrees = Vector3(-60, -30, 0); luna.light_color = Color(0.4, 0.5, 0.8); luna.light_energy = 0.25; esc.add_child(luna)

func _montar(prefijo: String, sin_glb: bool) -> void:
	esc = Node3D.new(); esc.name = "Escena"; root.add_child(esc)
	var Au = load("res://tools/auto.gd")
	var we: WorldEnvironment = Au.entorno_noche(); we.name = "Entorno"; esc.add_child(we)
	total = int(ceil(DUR * FPS)) + 1
	anim = Animation.new(); anim.length = float(total - 1) / FPS; anim.step = 1.0 / FPS; anim.loop_mode = Animation.LOOP_NONE
	ap = AnimationPlayer.new(); ap.name = "Anim"; esc.add_child(ap)
	_construir_mundo()
	auto = Au.crear(); esc.add_child(auto)
	limp = Au.limpiaparabrisas(auto)
	_luces()
	for nm in ["Wheel FL", "Wheel FR", "Wheel RL", "Wheel RR"]:
		var w := auto.find_child(nm, true, false) as MeshInstance3D
		var P := (auto.global_transform.affine_inverse() * (w.get_parent() as Node3D).global_transform).basis      # padre del nodo → espacio del auto
		ruedas[nm] = [w, w.transform, w.get_aabb().get_center(), P]
	vol_rul = auto.find_child("rul", true, false) as Node3D
	# personajes
	G = Actor3.new(); G.cargar("gabriel", "res://assets/aiden.glb", "res://assets/aiden_meta.json", esc)
	E = Actor3.new(); E.cargar("elena", "res://assets/kate.glb", "res://assets/kate_meta.json", esc)
	for par in [[G, 0.36], [E, -0.36]]:
		par[0].raiz.position = Vector3(par[1], PISO, 0.20); par[0].raiz.rotation.y = PI
	await process_frame
	RG = RigSentado.new(G.sk, G.raiz); RE = RigSentado.new(E.sk, E.raiz)
	print("rigs ", RG.ok, " ", RE.ok)
	# pistas
	var p_mundo := _pista(mundo, true, false); var p_auto := _pista(auto)
	var p_rued := {}; for k in ruedas: p_rued[k] = _pista(ruedas[k][0], true, true)
	var p_limp := []; for pv in limp: p_limp.append(_pista(pv, false, true))
	var p_rul := _pista(vol_rul, true, true)
	var p_sk := {}
	for ac in [G, E]:
		var d := {}
		for h in ac.sk.get_bone_count():
			var tq := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tq, NodePath("%s:%s" % [esc.get_path_to(ac.sk), ac.sk.get_bone_name(h)])); d[h] = tq
		var th := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(th, NodePath("%s:%s" % [esc.get_path_to(ac.sk), ac.sk.get_bone_name(ac.hueso_cadera)])); d["pos"] = th
		p_sk[ac.id] = d
	var p_raiz := {}; for ac in [G, E]: p_raiz[ac.id] = _pista(ac.raiz)
	var p_cam := {}; var rul_base := vol_rul.transform; var wc_loc := Vector3.ZERO
	for tm in TOMAS:
		var c := Camera3D.new(); c.name = tm["camara"]; c.fov = tm["fov"]; c.near = 0.05; c.far = 600.0; esc.add_child(c); cams[tm["id"]] = c; p_cam[tm["id"]] = _pista(c)
	var inv_g := G.raiz.global_transform.affine_inverse()
	var wc: Vector3 = inv_g * Vector3(0.36, 0.18, -0.20)
	var nrm: Vector3 = (inv_g.basis * Vector3(0, 0.25, 1)).normalized()
	var wX := Vector3.UP.cross(nrm).normalized(); var wY := nrm.cross(wX)
	var ang := {"Wheel FL": 0.0, "Wheel FR": 0.0, "Wheel RL": 0.0, "Wheel RR": 0.0}
	var mira_sua := {}
	for g in total:
		var t := float(g) / FPS
		# mundo, coche
		mundo.position = Vector3(0, 0, V * t); _clave(p_mundo, mundo, t)
		auto.position = Vector3(0, 0.010 * sin(t * 1.3) + 0.006 * sin(t * 3.1 + 1.0), 0); auto.rotation = Vector3(0.0035 * sin(t * 0.9), 0.0, 0.006 * sin(t * 1.1 + 0.5)); _clave(p_auto, auto, t)
		for k in ruedas:
			ang[k] += V / 0.33 / FPS
			var w: Node3D = ruedas[k][0]; var c: Vector3 = ruedas[k][2]; var Pb: Basis = ruedas[k][3]
			var rl := Pb.inverse() * Basis(Vector3.RIGHT, -ang[k]) * Pb                                    # giro en el eje del auto (el techo de la rueda va hacia el frente)
			w.transform = Transform3D(Basis.IDENTITY, (ruedas[k][1] as Transform3D) * c) * Transform3D(rl, Vector3.ZERO) * Transform3D(Basis.IDENTITY, -((ruedas[k][1] as Transform3D) * c)) * (ruedas[k][1] as Transform3D)
			_clave(p_rued[k], w, t)
		var ia := 0
		for pv in limp:
			var base := Basis(Quaternion(Vector3(0, 0, 1), Vector3(0, 0.80, -0.60).normalized()))
			pv.basis = base * Basis(Vector3(0, 0, 1), Au.angulo_limpia(t) - 0.0); _clave(p_limp[ia], pv, t); ia += 1
		# volante y manos
		var steer := 0.07 * sin(t * 0.45) + 0.03 * sin(t * 1.2 + 0.7)
		vol_rul.transform = rul_base; _clave(p_rul, vol_rul, t)
		var manos := []
		for par in [["Left", 2.5 + steer], ["Right", 0.64 + steer]]:
			var ph: float = par[1]
			var gp := wc + wX * cos(ph) * 0.19 + wY * sin(ph) * 0.19
			var rr := (gp - wc).normalized()
			manos.append({"side": par[0], "wrist": gp + nrm * 0.075 + rr * 0.05, "fdir": (rr * -0.15 + nrm * -0.85).normalized(), "back": (rr * 0.9 + nrm * 0.25).normalized(), "pole": Vector3(0.55, -0.55, -0.30)})
		var glance_g := _mira(t, [[9.0, 10.4], [15.5, 17.0], [21.0, 22.2]])
		var sw := Vector3(0.006 * sin(t * 1.7), 0.004 * sin(t * 2.3 + 1.0), 0.005 * sin(t * 1.3 + 0.4))
		var hip := Vector3(0, 0.30, 0) + sw * 0.5
		RG.pose({"hips": hip, "head": hip + Vector3(0.0, 0.60, 0.03) + sw, "roll": 0.02 * sin(t * 1.1), "look": 0.55 * glance_g + 0.03 * sin(t * 0.6), "look_y": -0.08 + 0.03 * sin(t * 0.8), "hands": manos, "grip": 1.2,
			"feet": [{"side": "Left", "pos": Vector3(0.13, 0.13, 0.58)}, {"side": "Right", "pos": Vector3(-0.13, 0.13, 0.55 + 0.01 * sin(t * 2.0))}]})
		var glance_e := _mira(t, [[9.5, 11.0], [15.2, 16.6], [20.5, 22.0]])
		var pelo := _mira(t, [[12.0, 14.2]])                          # Elena se acomoda el pelo
		var wr_l := Vector3(0.20, 0.42, 0.26).lerp(Vector3(0.10, 0.86, 0.12), pelo)
		var fd_l := Vector3(0, -0.25, 1).normalized().lerp(Vector3(0, 0.5, 0.2).normalized(), pelo)
		var sw2 := Vector3(0.005 * sin(t * 1.4 + 2.0), 0.004 * sin(t * 2.1), 0.004 * sin(t * 1.0))
		var hip2 := Vector3(0, 0.30, 0) + sw2 * 0.5
		RE.pose({"hips": hip2, "head": hip2 + Vector3(0.0, 0.60, 0.0) + sw2, "roll": 0.02 * sin(t * 0.9 + 1.0), "look": -0.5 * glance_e + 0.25 * _mira(t, [[1.5, 4.5], [25.0, 30.0]]) + 0.02, "look_y": -0.10, "grip": 0.8,
			"hands": [{"side": "Left", "wrist": wr_l, "fdir": fd_l, "back": Vector3(0, 1, 0), "pole": Vector3(0.5, -0.6, -0.3)},
					  {"side": "Right", "wrist": Vector3(-0.18, 0.42, 0.28), "fdir": Vector3(0, -0.25, 1).normalized(), "back": Vector3(0, 1, 0), "pole": Vector3(0.5, -0.6, -0.3)}],
			"feet": [{"side": "Left", "pos": Vector3(0.13, 0.12, 0.55)}, {"side": "Right", "pos": Vector3(-0.13, 0.12, 0.55)}]})
		for ac in [G, E]:
			var d: Dictionary = p_sk[ac.id]
			for h in ac.sk.get_bone_count():
				anim.rotation_track_insert_key(d[h], t, ac.sk.get_bone_pose_rotation(h))
			anim.position_track_insert_key(d["pos"], t, ac.sk.get_bone_pose_position(ac.hueso_cadera))
			_clave(p_raiz[ac.id], ac.raiz, t)
		# cámaras
		for tm in TOMAS:
			var c: Camera3D = cams[tm["id"]]
			var u := clampf((t - tm["t0"]) / maxf(tm["t1"] - tm["t0"], 0.001), 0.0, 1.0); var e := smoothstep(0.0, 1.0, u)
			var pa: Array = tm["pos"]; var pb: Array = tm["pos_fin"]; var ma: Array = tm["mira"]; var mb: Array = tm["mira_fin"]
			c.global_position = Vector3(pa[0], pa[1], pa[2]).lerp(Vector3(pb[0], pb[1], pb[2]), e)
			c.look_at(Vector3(ma[0], ma[1], ma[2]).lerp(Vector3(mb[0], mb[1], mb[2]), e), Vector3.UP)
			var amp: float = tm["mano"]
			if amp > 0.0: c.position += Vector3(sin(t * 0.7), sin(t * 0.9 + 1.0), 0) * amp
			_clave(p_cam[tm["id"]], c, t, false)
	var lib := AnimationLibrary.new(); lib.add_animation("escena", anim); ap.add_animation_library("", lib); ap.assigned_animation = "escena"
	# capturas de revisión (no son render)
	for tm in TOMAS:
		var tc: float = (float(tm["t0"]) + float(tm["t1"])) * 0.5
		(cams[tm["id"]] as Camera3D).current = true
		ap.seek(tc, true)
		for i in 4: await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [prefijo, tm["id"]])
	if sin_glb:
		print("SIN_GLB"); quit(); return
	ap.seek(0.0, true)
	var doc := GLTFDocument.new(); var st := GLTFState.new()
	doc.append_from_scene(esc, st)
	var err := doc.write_to_filesystem(st, prefijo + ".glb")
	print("GLB ", prefijo, ".glb err=", err)
	var cj := []
	for tm in TOMAS:
		cj.append({"id": tm["id"], "camara": tm["camara"], "inicio_s": tm["t0"], "fin_s": tm["t1"], "frame_inicio": int(tm["t0"] * FPS) + 1, "frame_fin": int(minf(tm["t1"] * FPS, total - 1)) + 1, "lente_mm": 12.0 / tan(deg_to_rad(tm["fov"]) / 2.0)})
	var js := {"formato": "estudio.previa_godot/1", "produccion": "p022_la_mujer_que_volvio", "escena_id": "viaje", "version": 1, "titulo": "El viaje bajo la lluvia", "fps": int(FPS), "frames": total, "duracion_s": float(total - 1) / FPS,
		"resolucion": [540, 960], "animacion": "escena", "actores": [{"id": "gabriel", "nodo": "gabriel", "modelo": "aiden"}, {"id": "elena", "nodo": "elena", "modelo": "kate"}], "tomas": cj,
		"relampagos_s": RELAMPAGOS, "limpiaparabrisas": {"periodo_s": 1.4, "barrido_rad": 1.65}, "velocidad_ms": V, "efectos_blender": ["lluvia", "gotas en el parabrisas", "niebla", "relámpagos", "brillo del barniz", "faros con cono volumétrico"],
		"tiempo": {"pelicula": "t = (cuadro − 1) / fps"}}
	var fa := FileAccess.open(prefijo + ".json", FileAccess.WRITE); fa.store_string(JSON.stringify(js, "  ")); fa.close()
	quit()

func _mira(t: float, ventanas: Array) -> float:
	var r := 0.0
	for v in ventanas:
		var a: float = v[0]; var b: float = v[1]
		r = maxf(r, smoothstep(a - 0.4, a + 0.2, t) * (1.0 - smoothstep(b - 0.2, b + 0.4, t)))
	return r
