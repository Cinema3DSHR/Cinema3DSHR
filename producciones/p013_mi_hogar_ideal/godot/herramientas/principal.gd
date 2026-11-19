## «Mi hogar ideal» (p013): arma la casa desde layout.json (generado por ../disenio.py) y la anima.
## Godot construye la estructura, los muebles, las cámaras y las animaciones de aparición. La iluminación final, los
## materiales y los efectos son de Blender. Las piezas «crecen» o aparecen con un golpe de escala; la cámara hace un
## recorrido continuo con cortes secos entre planos. Retrato 9:16 (la altura manda el campo visual).
extends Node3D

const FPS := 30
const TINY := Vector3(0.001, 0.001, 0.001)

const WheelGen := preload("res://herramientas/wheel_gen.gd")
var L: Dictionary
var mats := {}
var anim: Animation
var ap: AnimationPlayer
var camara: Camera3D
var _n := 0


func _ready() -> void:
	L = JSON.parse_string(FileAccess.get_file_as_string("res://layout.json"))
	_materiales()
	_entorno()
	anim = Animation.new()
	anim.length = float(L["total_s"])
	anim.step = 1.0 / FPS
	var raiz := Node3D.new()
	raiz.name = "Casa"
	add_child(raiz)
	for it in L["items"]:
		_item(raiz, it)
	_luces(raiz)
	for mk in L.get("marcadores", []):
		var n := Node3D.new()
		n.name = mk["nombre"]
		n.position = Vector3(mk["pos"][0], mk["pos"][1], mk["pos"][2])
		raiz.add_child(n)
	_camara()
	ap = AnimationPlayer.new()
	ap.name = "Animacion"
	add_child(ap)
	var lib := AnimationLibrary.new()
	lib.add_animation("toma", anim)
	ap.add_animation_library("", lib)
	ap.play("toma")


func _m(nombre: String, color: Color, rug := 0.8, metal := 0.0, emision := 0.0, alfa := 1.0) -> void:
	var m := StandardMaterial3D.new()
	m.resource_name = nombre
	m.albedo_color = Color(color, alfa)
	m.roughness = rug
	m.metallic = metal
	if emision > 0.0:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = emision
	if alfa < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mats[nombre] = m


func _materiales() -> void:
	_m("estuco", Color(0.93, 0.91, 0.87), 0.92)
	_m("estuco_int", Color(0.95, 0.94, 0.92), 0.95)
	_m("piedra", Color(0.46, 0.41, 0.36), 0.95)
	_m("hormigon", Color(0.55, 0.55, 0.56), 0.9)
	_m("hormigon_piso", Color(0.42, 0.42, 0.44), 0.85)
	_m("piso_madera", Color(0.62, 0.45, 0.30), 0.45)
	_m("piso_piedra", Color(0.72, 0.70, 0.66), 0.6)
	_m("madera_clara", Color(0.76, 0.59, 0.41), 0.5)
	_m("madera_oscura", Color(0.24, 0.15, 0.10), 0.45)
	_m("marco", Color(0.05, 0.05, 0.06), 0.4, 0.7)
	_m("vidrio", Color(0.72, 0.86, 0.92), 0.03, 0.0, 0.0, 0.16)
	_m("alfombra", Color(0.84, 0.80, 0.72), 1.0)
	_m("marmol", Color(0.94, 0.94, 0.93), 0.12)
	_m("ceramica", Color(0.9, 0.87, 0.82), 0.3)
	_m("pantalla", Color(0.96, 0.88, 0.70), 0.9, 0.0, 1.6)
	_m("pantalla_negra", Color(0.05, 0.05, 0.05), 0.5, 0.4)
	_m("luz_calida", Color(1.0, 0.80, 0.50), 0.5, 0.0, 6.0)
	_m("neon_magenta", Color(1.0, 0.20, 0.90), 0.5, 0.0, 9.0)
	_m("neon_violeta", Color(0.62, 0.26, 1.0), 0.5, 0.0, 9.0)
	_m("luz_jardin", Color(1.0, 0.76, 0.45), 0.5, 0.0, 9.0)
	_m("espejo", Color(0.82, 0.88, 0.93), 0.04, 1.0)
	_m("cuadro", Color(0.16, 0.36, 0.46), 0.6)
	_m("tierra", Color(0.18, 0.10, 0.06), 1.0)
	_m("flor_violeta", Color(0.52, 0.36, 0.78), 0.8)
	_m("flor_rosa", Color(0.92, 0.46, 0.62), 0.8)
	_m("flor_blanca", Color(0.96, 0.96, 0.92), 0.8)
	_m("follaje", Color(0.12, 0.36, 0.12), 0.9)
	_m("follaje_2", Color(0.18, 0.46, 0.16), 0.9)
	_m("tronco", Color(0.30, 0.20, 0.12), 0.95)
	_m("cesped", Color(0.20, 0.46, 0.15), 1.0)
	_m("azulejo", Color(0.88, 0.9, 0.9), 0.15)
	_m("cortina", Color(0.95, 0.93, 0.9), 1.0, 0.0, 0.0, 0.88)
	_m("asfalto", Color(0.14, 0.14, 0.15), 0.85)
	_m("vereda", Color(0.62, 0.61, 0.58), 0.9)
	_m("pintura_vial", Color(0.88, 0.82, 0.55), 0.7)
	_m("colina", Color(0.15, 0.32, 0.13), 1.0)
	_m("felpudo", Color(0.2, 0.17, 0.14), 1.0)
	_m("cuadro2", Color(0.82, 0.55, 0.32), 0.7)
	_m("cuadro3", Color(0.30, 0.42, 0.40), 0.7)
	_m("alfombra2", Color(0.42, 0.44, 0.46), 1.0)
	_m("libro_a", Color(0.65, 0.18, 0.15), 0.8)
	_m("libro_b", Color(0.16, 0.30, 0.50), 0.8)
	_m("libro_c", Color(0.82, 0.68, 0.30), 0.8)
	_m("libro_d", Color(0.20, 0.40, 0.25), 0.8)
	_m("libro_e", Color(0.88, 0.86, 0.80), 0.8)
	_m("tela_naranja", Color(0.78, 0.42, 0.20), 1.0)
	_m("tela_violeta", Color(0.42, 0.32, 0.58), 1.0)
	_m("tela_blanca", Color(0.96, 0.96, 0.95), 1.0)
	_m("tela_celeste", Color(0.55, 0.72, 0.82), 1.0)
	_m("cera", Color(0.96, 0.92, 0.82), 0.6)
	_m("acero", Color(0.72, 0.74, 0.76), 0.25, 1.0)
	_m("fruta_naranja", Color(0.92, 0.50, 0.12), 0.5)
	_m("fruta_verde", Color(0.48, 0.70, 0.18), 0.5)
	_m("fruta_roja", Color(0.82, 0.15, 0.12), 0.5)
	_m("cielorraso", Color(0.96, 0.95, 0.93), 0.95)


func _entorno() -> void:
	# sólo para revisar en Godot; la atmósfera final (cielo, sol, niebla) es de Blender
	var we := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.55, 0.72, 0.9)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.75, 0.78, 0.85)
	e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	we.environment = e
	add_child(we)
	var sol := DirectionalLight3D.new()
	sol.name = "Luz_sol"
	sol.rotation_degrees = Vector3(-48, 35, 0)
	sol.light_energy = 1.1
	sol.shadow_enabled = true
	add_child(sol)
	var suelo := MeshInstance3D.new()
	suelo.name = "Terreno"
	var pm := PlaneMesh.new()
	pm.size = Vector2(600, 520)
	suelo.mesh = pm
	suelo.material_override = mats["cesped"]
	suelo.position = Vector3(10, -0.16, 20)
	add_child(suelo)


func _nodo(tipo: String, it: Dictionary) -> Node3D:
	var w := Node3D.new()
	_n += 1
	w.name = "%s_%03d" % [String(it["nombre"]).left(28), _n]
	var p: Array = it["pos"]
	w.position = Vector3(p[0], p[1], p[2])
	var mi: MeshInstance3D
	match tipo:
		"caja":
			var bm := BoxMesh.new()
			bm.size = Vector3(it["tam"][0], it["tam"][1], it["tam"][2])
			mi = MeshInstance3D.new()
			mi.mesh = bm
			mi.position = Vector3(0, it["tam"][1] * 0.5, 0)
		"cil":
			var cm := CylinderMesh.new()
			cm.top_radius = it["tam"][0]
			cm.bottom_radius = it["tam"][0]
			cm.height = it["tam"][1]
			cm.radial_segments = 16
			cm.rings = 1
			mi = MeshInstance3D.new()
			mi.mesh = cm
			mi.position = Vector3(0, it["tam"][1] * 0.5, 0)
		"esfera":
			var sm := SphereMesh.new()
			sm.radius = 1.0
			sm.height = 2.0
			sm.radial_segments = 16
			sm.rings = 8
			mi = MeshInstance3D.new()
			mi.mesh = sm
			mi.scale = Vector3(it["tam"][0], it["tam"][1], it["tam"][2])
		"auto_dr":
			var psa: PackedScene = load("res://modelos/%s.glb" % it["modelo"])
			var car: Node3D = psa.instantiate()
			car.name = "carroceria"
			w.add_child(car)
			w.rotation_degrees.y = it["yaw"]
			_ruedas_dr(w, JSON.parse_string(FileAccess.get_file_as_string("res://modelos/%s.json" % it["modelo"])))
		"modelo":
			var ps: PackedScene = load("res://modelos/%s.glb" % it["modelo"])
			var inst: Node3D = ps.instantiate()
			inst.name = "m"
			w.add_child(inst)
			w.rotation_degrees.y = it["yaw"]
			var esc: float = it["esc"]
			inst.scale = Vector3(esc, esc, esc)
			_pintar_sin_material(inst)
	if mi != null:
		mi.name = "malla"
		mi.material_override = mats[it["mat"]]
		w.add_child(mi)
	return w


## Ruedas del juego (wheel_gen.gd de Dream Racing, sin cambios): goma y llanta con el estilo, el dibujo y las medidas del auto.
## Eje de la rueda = X; las del lado izquierdo se espejan, como en el juego.
func _ruedas_dr(auto: Node3D, meta: Dictionary) -> void:
	var W: Dictionary = meta["wheel"]
	var R := float(meta["R"])
	var rr := float(W["rim"])
	var tw := float(W["tw"])
	var tire := StandardMaterial3D.new()
	tire.resource_name = "goma"
	tire.albedo_color = Color(0.08, 0.085, 0.09)
	tire.roughness = 0.93
	var wall := StandardMaterial3D.new()
	wall.resource_name = "flanco"
	wall.albedo_color = Color(0.5, 0.5, 0.52)
	wall.roughness = 0.9
	var rim := StandardMaterial3D.new()
	rim.resource_name = "llanta"
	rim.albedo_color = Color(0.72, 0.74, 0.78)
	rim.metallic = 0.85
	rim.roughness = 0.28
	var dark := StandardMaterial3D.new()
	dark.resource_name = "llanta_oscura"
	dark.albedo_color = Color(0.03, 0.03, 0.035)
	dark.roughness = 0.9
	var steel := StandardMaterial3D.new()
	steel.resource_name = "acero_rueda"
	steel.albedo_color = Color(0.7, 0.72, 0.75)
	steel.metallic = 1.0
	steel.roughness = 0.25
	var por_nombre := {"tire": tire, "wall": wall, "rim": rim, "dark": dark, "steel": steel}
	var cont := 0
	for ar in meta["arches"]:
		for lado in [1.0, -1.0]:
			var steer := Node3D.new()
			cont += 1
			steer.name = "Rueda_%d" % cont
			steer.position = Vector3(lado * (float(ar["x_out"]) - tw * 0.5 + 0.03), R, float(ar["z"]))
			auto.add_child(steer)
			var asm := Node3D.new()
			asm.name = "asm"
			asm.scale = Vector3(lado, 1.0, 1.0)
			steer.add_child(asm)
			var mt := MeshInstance3D.new()
			mt.mesh = WheelGen.tire_mesh(R, rr, tw, str(W["tread"]), false)
			asm.add_child(mt)
			var mr := MeshInstance3D.new()
			mr.mesh = WheelGen.rim_mesh(str(W["style"]), rr, tw * 0.78, false)
			asm.add_child(mr)
			for mi in [mt, mr]:
				var nombres: Array = mi.mesh.get_meta("names", [])
				for i in nombres.size():
					mi.set_surface_override_material(i, por_nombre.get(str(nombres[i]), dark))


## Los árboles de la biblioteca (pino, acacia, ciprés…) vienen sin material: hoja y tronco según el nombre de la pieza.
func _pintar_sin_material(raiz: Node) -> void:
	for mi in raiz.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.mesh == null or m.get_active_material(0) != null:
			continue
		var nombre := String(m.name).to_lower()
		if "leaf" in nombre or "leaves" in nombre or "foil" in nombre:
			m.material_override = mats["follaje_2"]
		elif "trunk" in nombre or "branch" in nombre or "stem" in nombre:
			m.material_override = mats["tronco"]
		else:
			m.material_override = mats["follaje"]


func _t(a: float, b: float) -> float:
	return snappedf(maxf(a, 0.0), 1.0 / FPS)


func _item(raiz: Node3D, it: Dictionary) -> void:
	var w := _nodo(it["tipo"], it)
	raiz.add_child(w)
	var vis: Dictionary = it["vis"]
	var t_on: float = vis["t_on"]
	var t_off = vis["t_off"]
	var gancho: float = L["gancho_hasta_s"]
	var base_p := w.position
	var mueve = it.get("mueve")
	if mueve != null:                         # se muestra donde estaba y se corre después; el estado final es el de la apertura
		w.position = base_p + Vector3(0, 0, float(mueve["dz"]))
	var tp := anim.add_track(Animation.TYPE_SCALE_3D)
	anim.track_set_path(tp, NodePath(str(get_path_to(w))))
	var crece: bool = it["crece"]
	var uno := Vector3.ONE
	var dt := 1.0 / FPS
	# estado inicial y la apertura (estado final de la casa durante el gancho)
	if it["hook"]:
		anim.scale_track_insert_key(tp, 0.0, uno)
		anim.scale_track_insert_key(tp, _t(gancho - dt, 0), uno)
		anim.scale_track_insert_key(tp, _t(gancho, 0), TINY)
	else:
		anim.scale_track_insert_key(tp, 0.0, TINY)
	var tt := _t(t_on, 0)
	anim.scale_track_insert_key(tp, maxf(tt - dt, _t(gancho, 0) + dt), TINY)
	if crece:
		anim.scale_track_insert_key(tp, tt, Vector3(1, 0.001, 1))
		anim.scale_track_insert_key(tp, tt + 1.0, uno)
	else:
		anim.scale_track_insert_key(tp, tt, TINY)
		anim.scale_track_insert_key(tp, tt + 0.26, uno * 1.1)
		anim.scale_track_insert_key(tp, tt + 0.42, uno)
	if t_off != null:
		var to := _t(float(t_off), 0)
		anim.scale_track_insert_key(tp, to - dt, uno)
		anim.scale_track_insert_key(tp, to, TINY)
	# movimiento (la mesa del comedor se corre hacia la ventana)
	if mueve != null:
		var tpos := anim.add_track(Animation.TYPE_POSITION_3D)
		anim.track_set_path(tpos, NodePath(str(get_path_to(w))))
		var final_p := base_p
		var ini_p := base_p + Vector3(0, 0, float(mueve["dz"]))      # (ver abajo: ini = z original)
		ini_p = Vector3(base_p.x, base_p.y, base_p.z)
		var t0 := _t(t_on + float(mueve["off"]), 0)
		var t1 := t0 + float(mueve["dur"])
		anim.position_track_insert_key(tpos, 0.0, final_p + Vector3(0, 0, float(mueve["dz"])))
		anim.position_track_insert_key(tpos, _t(t_on, 0), ini_p)
		anim.position_track_insert_key(tpos, t0, ini_p)
		anim.position_track_insert_key(tpos, t1, final_p + Vector3(0, 0, float(mueve["dz"])))
		anim.track_set_interpolation_type(tpos, Animation.INTERPOLATION_CUBIC)


func _luces(raiz: Node3D) -> void:
	for l in L["luces"]:
		var luz: Light3D
		if l["tipo"] == "foco":
			var s := SpotLight3D.new()
			s.spot_angle = 55.0
			s.spot_range = 7.0
			luz = s
		else:
			var o := OmniLight3D.new()
			o.omni_range = 7.0
			luz = o
		luz.name = l["nombre"]
		var p: Array = l["pos"]
		luz.position = Vector3(p[0], p[1], p[2])
		var c: Array = l["color"]
		luz.light_color = Color(c[0], c[1], c[2])
		luz.light_energy = 0.9
		raiz.add_child(luz)


func _camara() -> void:
	camara = Camera3D.new()
	camara.name = "Camara"
	camara.fov = float(L["camara_vertical_fov"])
	camara.near = 0.05
	camara.far = 800.0
	camara.keep_aspect = Camera3D.KEEP_HEIGHT
	add_child(camara)
	camara.current = true
	var tpos := anim.add_track(Animation.TYPE_POSITION_3D)
	var trot := anim.add_track(Animation.TYPE_ROTATION_3D)
	anim.track_set_path(tpos, NodePath(str(get_path_to(camara))))
	anim.track_set_path(trot, NodePath(str(get_path_to(camara))))
	var cu: Array = L["camara"]
	for f in cu.size():
		var c: Array = cu[f]
		var t := float(f) / FPS
		var p := Vector3(c[0], c[1], c[2])
		var m := Vector3(c[3], c[4], c[5])
		anim.position_track_insert_key(tpos, t, p)
		anim.rotation_track_insert_key(trot, t, Basis.looking_at(m - p, Vector3.UP).get_rotation_quaternion())
	# cortes secos: sin interpolar entre cuadros (cada cuadro es una pose)
	anim.track_set_interpolation_type(tpos, Animation.INTERPOLATION_LINEAR)
	var c0: Array = cu[0]
	camara.position = Vector3(c0[0], c0[1], c0[2])
	camara.basis = Basis.looking_at(Vector3(c0[3], c0[4], c0[5]) - camara.position, Vector3.UP)
