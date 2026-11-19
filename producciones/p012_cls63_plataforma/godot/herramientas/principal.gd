## Escena «CLS63 en plataforma», 30 s a 30 fps. Todo se arma en código al abrir la escena.
## Medidas tomadas del GLB (metros): base de las ruedas y = −0,766; eje delantero z = 1,671; rueda única del modelo
## en (±0,970; −0,359; 1,671), se copia a las 4 esquinas. Distancia entre ejes 2,94 m (típica del CLS 63; se verifica).
extends Node3D

const DUR := 30.0
const FPS := 30
const SUELO_Y := -0.766
const RUEDA_Z_TRA := -1.83      # centro del hueco del guardabarros trasero (medido en la carrocería)
const ALTO_VENTANA := 0.30

var auto: Node3D
var plataforma: Node3D
var camara: Camera3D
var ruedas: Array[Node3D] = []
var bisagras := {}
var ventanas: Array[Node3D] = []
var neones_luz: Array[OmniLight3D] = []

# Cámara: [segundo, posición, punto al que mira]. Movimiento continuo (Hermite), sin cortes.
const CAMARA := [
	[0.0, Vector3(-5.2, 1.3, 6.4), Vector3(0.0, 0.0, 0.0)],
	[4.0, Vector3(-6.6, 1.0, 1.8), Vector3(-0.9, 0.0, 0.2)],
	[9.0, Vector3(-4.6, 1.3, -5.2), Vector3(0.0, 0.2, -1.8)],
	[13.5, Vector3(-2.2, 1.8, -6.4), Vector3(0.0, 0.3, -2.4)],
	[17.0, Vector3(4.4, 1.6, 4.6), Vector3(0.0, 0.25, 1.7)],
	[21.0, Vector3(2.3, 0.85, 0.15), Vector3(-0.4, 0.15, -0.1)],
	[25.0, Vector3(-3.2, -0.25, 3.3), Vector3(-0.97, -0.35, 1.67)],
	[30.0, Vector3(-7.4, 2.6, -2.2), Vector3(0.0, 0.1, 0.0)],
]


func _ready() -> void:
	_ambiente()
	_plataforma()
	_auto()
	_ruedas()
	_piezas_moviles()
	_luces()
	_efectos()
	camara = Camera3D.new()
	camara.name = "Camara"
	camara.fov = 55.0
	camara.near = 0.05
	camara.far = 200.0
	add_child(camara)
	camara.current = true
	_animacion()


func _ambiente() -> void:
	var we := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.012, 0.012, 0.018)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.10, 0.11, 0.14)
	e.ambient_light_energy = 0.12
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	e.glow_enabled = true
	e.glow_intensity = 0.7
	e.glow_bloom = 0.05
	e.volumetric_fog_enabled = true
	e.volumetric_fog_density = 0.012
	e.volumetric_fog_albedo = Color(0.7, 0.72, 0.8)
	we.environment = e
	add_child(we)


func _mat(color: Color, rugosidad: float, metal: float, emision := Color.BLACK, energia := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = rugosidad
	m.metallic = metal
	if energia > 0.0:
		m.emission_enabled = true
		m.emission = emision
		m.emission_energy_multiplier = energia
	return m


func _plataforma() -> void:
	# piso oscuro y reflejante bajo el disco
	var piso := MeshInstance3D.new()
	var pl := PlaneMesh.new()
	pl.size = Vector2(60, 60)
	piso.mesh = pl
	piso.material_override = _mat(Color(0.02, 0.02, 0.025), 0.12, 0.2)
	piso.position = Vector3(0, SUELO_Y - 0.141, 0)
	add_child(piso)
	# disco giratorio
	plataforma = Node3D.new()
	plataforma.name = "Plataforma"
	add_child(plataforma)
	var disco := CylinderMesh.new()
	disco.top_radius = 3.6
	disco.bottom_radius = 3.6
	disco.height = 0.14
	disco.radial_segments = 96
	var d := MeshInstance3D.new()
	d.mesh = disco
	d.material_override = _mat(Color(0.03, 0.03, 0.035), 0.22, 0.6)
	d.position = Vector3(0, SUELO_Y - 0.07, 0)
	plataforma.add_child(d)
	# aro de neón en el borde
	var aro := TorusMesh.new()
	aro.inner_radius = 3.55
	aro.outer_radius = 3.63
	aro.rings = 64
	aro.ring_segments = 8
	var a := MeshInstance3D.new()
	a.mesh = aro
	a.material_override = _mat(Color(0.2, 0.7, 1.0), 0.5, 0.0, Color(0.2, 0.7, 1.0), 6.0)
	a.position = Vector3(0, SUELO_Y + 0.01, 0)
	plataforma.add_child(a)


func _auto() -> void:
	auto = (load("res://modelos/cls63.glb") as PackedScene).instantiate()
	auto.name = "Auto"
	auto.position = Vector3(0, 0, 0.2)       # centra la carrocería en el eje del disco
	plataforma.add_child(auto)


func _ruedas() -> void:
	# el modelo trae UNA sola rueda: se la quita de su lugar y se copia a las cuatro esquinas
	var m001 := auto.find_child("Mesh 001", true, false) as MeshInstance3D
	var malla: Mesh = m001.mesh
	var c_malla := malla.get_aabb().get_center()
	var c_auto: Vector3 = auto.global_transform.affine_inverse() * (m001.global_transform * c_malla)
	m001.get_parent().remove_child(m001)
	m001.queue_free()
	var ax := absf(c_auto.x)
	var posiciones := [
		Vector3(-ax, c_auto.y, c_auto.z), Vector3(ax, c_auto.y, c_auto.z),
		Vector3(-ax, c_auto.y, RUEDA_Z_TRA), Vector3(ax, c_auto.y, RUEDA_Z_TRA)]
	for i in 4:
		var p: Vector3 = posiciones[i]
		var piv := Node3D.new()
		piv.name = "Rueda_%d" % i
		piv.position = p
		if p.x > 0.0:
			piv.rotation.y = PI      # espejo: la rueda es simétrica
		auto.add_child(piv)
		var mi := MeshInstance3D.new()
		mi.mesh = malla
		mi.position = -c_malla
		piv.add_child(mi)
		ruedas.append(piv)
	print("ruedas en: ", posiciones)


func _puerta(id: String, partes: Array, x: float, z_bisagra: float, grados: float) -> void:
	var h := Node3D.new()
	h.name = "Bisagra_" + id
	h.position = Vector3(x, -0.03, z_bisagra)
	auto.add_child(h)
	for p in partes:
		var n := auto.find_child(p, true, false) as Node3D
		if n == null:
			push_warning("no está la pieza " + p)
			continue
		n.reparent(h, true)
		if p.begins_with("window"):
			ventanas.append(n)
	h.set_meta("eje", "y")
	h.set_meta("signo", -signf(x))       # la puerta se abre hacia afuera
	h.set_meta("grados", grados)
	bisagras[id] = h


func _piezas_moviles() -> void:
	_puerta("pf", ["door_pside_f", "window_rf", "window_rf (2)"], -1.10, 0.933, deg_to_rad(62.0))
	_puerta("df", ["door_dside_f", "door_dside_f_a", "window_lf", "window_lf (2)"], 1.10, 0.933, deg_to_rad(62.0))
	_puerta("pr", ["door_pside_r", "door_pside_r (2)", "window_rr", "window_rr (2)"], -1.10, -0.391, deg_to_rad(62.0))
	_puerta("dr", ["door_dside_r", "door_dside_r (2)", "window_lr", "window_lr (2)"], 1.10, -0.391, deg_to_rad(62.0))
	# capó: bisagra en el borde trasero, se levanta por delante
	var capo := Node3D.new()
	capo.name = "Bisagra_capo"
	capo.position = Vector3(0, 0.353, 0.830)
	auto.add_child(capo)
	for p in ["bonnet", "bonnet_badge"]:
		var n := auto.find_child(p, true, false) as Node3D
		if n:
			n.reparent(capo, true)
	capo.set_meta("eje", "x")
	capo.set_meta("signo", -1.0)
	capo.set_meta("grados", deg_to_rad(36.0))
	bisagras["capo"] = capo
	# baúl: bisagra en el borde superior delantero, se levanta por detrás
	var baul := Node3D.new()
	baul.name = "Bisagra_baul"
	baul.position = Vector3(0, 0.454, -2.170)
	auto.add_child(baul)
	var b := auto.find_child("boot", true, false) as Node3D
	if b:
		b.reparent(baul, true)
	baul.set_meta("eje", "x")
	baul.set_meta("signo", 1.0)
	baul.set_meta("grados", deg_to_rad(44.0))
	bisagras["baul"] = baul


func _luces() -> void:
	# focos tipo minero, altos y de frente, que bajan sobre el auto (haces visibles por niebla volumétrica)
	for x in [-3.6, 3.6]:
		var s := SpotLight3D.new()
		s.name = "Foco_minero_%d" % int(x)
		s.position = Vector3(x, 4.8, 4.2)
		s.light_color = Color(1.0, 0.93, 0.8)
		s.light_energy = 3.2
		s.spot_range = 16.0
		s.spot_angle = 24.0
		s.spot_attenuation = 0.8
		s.shadow_enabled = true
		s.light_volumetric_fog_energy = 4.0
		add_child(s)
		s.look_at(Vector3(0.0, 0.2, 0.0))
	# contraluz frío desde atrás
	var r := SpotLight3D.new()
	r.name = "Contraluz"
	r.position = Vector3(0, 3.4, -6.6)
	r.light_color = Color(0.6, 0.8, 1.0)
	r.light_energy = 2.0
	r.spot_range = 14.0
	r.spot_angle = 34.0
	r.light_volumetric_fog_energy = 2.0
	add_child(r)
	r.look_at(Vector3(0, 0.3, -1.0))
	# neón bajo el auto, sobre el disco, a cada lado
	for lado in [-1.0, 1.0]:
		var col := Color(0.1, 0.9, 1.0) if lado < 0.0 else Color(1.0, 0.2, 0.75)
		var tira := MeshInstance3D.new()
		var caja := BoxMesh.new()
		caja.size = Vector3(0.06, 0.03, 5.8)
		tira.mesh = caja
		tira.material_override = _mat(col, 0.5, 0.0, col, 8.0)
		tira.position = Vector3(lado * 2.0, SUELO_Y + 0.015, 0.0)
		plataforma.add_child(tira)
		var om := OmniLight3D.new()
		om.name = "Neon_luz_%d" % int(lado)
		om.position = Vector3(lado * 1.5, -0.5, 0.0)
		om.light_color = col
		om.light_energy = 0.6
		om.omni_range = 2.2
		add_child(om)
		neones_luz.append(om)


func _textura_suave() -> GradientTexture2D:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.45, 1.0])
	g.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.5), Color(1, 1, 1, 0)])
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 128
	t.height = 128
	return t


func _curva(puntos: Array) -> CurveTexture:
	var c := Curve.new()
	for p in puntos:
		c.add_point(Vector2(p[0], p[1]))
	var t := CurveTexture.new()
	t.curve = c
	return t


func _rampa(colores: Array) -> GradientTexture1D:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array(colores.map(func(c): return c[0]))
	g.colors = PackedColorArray(colores.map(func(c): return c[1]))
	var t := GradientTexture1D.new()
	t.gradient = g
	return t


func _particulas(padre: Node3D, nombre: String, pos: Vector3, cantidad: int, vida: float, extents: Vector3, tipo: String) -> void:
	var p := GPUParticles3D.new()
	p.name = nombre
	p.position = pos
	p.amount = cantidad
	p.lifetime = vida
	p.preprocess = vida
	p.visibility_aabb = AABB(Vector3(-6, -2, -6), Vector3(12, 8, 12))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = extents
	var malla := QuadMesh.new()
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = _textura_suave()
	if tipo == "neblina":
		# neblina baja que se extiende despacio a lo ancho, sin subir mucho
		pm.direction = Vector3(0, 0.2, 0)
		pm.spread = 180.0
		pm.initial_velocity_min = 0.05
		pm.initial_velocity_max = 0.14
		pm.gravity = Vector3.ZERO
		pm.damping_min = 0.2
		pm.damping_max = 0.4
		pm.scale_min = 1.2
		pm.scale_max = 2.0
		pm.scale_curve = _curva([[0.0, 0.6], [1.0, 2.6]])
		pm.color_ramp = _rampa([[0.0, Color(0.6, 0.63, 0.7, 0.0)], [0.3, Color(0.6, 0.63, 0.7, 0.10)], [1.0, Color(0.5, 0.52, 0.58, 0.0)]])
		malla.size = Vector2(1.6, 1.6)
	elif tipo == "humo":
		pm.direction = Vector3.UP
		pm.spread = 35.0
		pm.initial_velocity_min = 0.15
		pm.initial_velocity_max = 0.45
		pm.gravity = Vector3(0, 0.05, 0)
		pm.damping_min = 0.4
		pm.damping_max = 0.8
		pm.scale_min = 0.5
		pm.scale_max = 1.2
		pm.scale_curve = _curva([[0.0, 0.5], [1.0, 2.2]])
		pm.color_ramp = _rampa([[0.0, Color(0.5, 0.52, 0.56, 0.0)], [0.25, Color(0.5, 0.52, 0.56, 0.22)], [1.0, Color(0.4, 0.42, 0.46, 0.0)]])
		malla.size = Vector2(1.2, 1.2)
	else:
		# polvo y aire: motas que flotan en todas direcciones dentro de los haces
		pm.direction = Vector3.UP
		pm.spread = 180.0
		pm.initial_velocity_min = 0.03
		pm.initial_velocity_max = 0.12
		pm.scale_min = 0.6
		pm.scale_max = 1.3
		pm.color_ramp = _rampa([[0.0, Color(1, 1, 1, 0.0)], [0.3, Color(1, 0.97, 0.9, 0.55)], [1.0, Color(1, 1, 1, 0.0)]])
		malla.size = Vector2(0.035, 0.035)
	malla.material = mat
	p.process_material = pm
	p.draw_pass_1 = malla
	padre.add_child(p)


func _efectos() -> void:
	# humo que sale por debajo del auto y de las ruedas (gira con el disco)
	# neblina baja a los costados del auto (nada sale de debajo del auto)
	for lado in [-1.0, 1.0]:
		_particulas(self, "Neblina_%d" % int(lado), Vector3(lado * 2.7, SUELO_Y + 0.12, 0.0), 40, 7.0, Vector3(0.5, 0.08, 2.4), "neblina")
	# polvo y aire en el volumen de los focos
	_particulas(self, "Polvo", Vector3(0, 1.6, 0), 700, 8.0, Vector3(3.2, 1.6, 3.2), "polvo")


func _herm(comp: int, t: float) -> Vector3:
	var n := CAMARA.size()
	var i := 0
	while i < n - 2 and t > CAMARA[i + 1][0]:
		i += 1
	var t0: float = CAMARA[i][0]
	var t1: float = CAMARA[i + 1][0]
	var h := t1 - t0
	var u := clampf((t - t0) / h, 0.0, 1.0)
	var p0: Vector3 = CAMARA[i][comp]
	var p1: Vector3 = CAMARA[i + 1][comp]
	var d0: Vector3
	var d1: Vector3
	if i == 0:
		d0 = (p1 - p0) / h
	else:
		d0 = (CAMARA[i + 1][comp] - CAMARA[i - 1][comp]) / (CAMARA[i + 1][0] - CAMARA[i - 1][0])
	if i + 2 >= n:
		d1 = (p1 - p0) / h
	else:
		d1 = (CAMARA[i + 2][comp] - CAMARA[i][comp]) / (CAMARA[i + 2][0] - CAMARA[i][0])
	var u2 := u * u
	var u3 := u2 * u
	return (2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * h * d0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * h * d1


func _pista(a: Animation, nodo: Node, prop: String) -> int:
	var t := a.add_track(Animation.TYPE_VALUE)
	a.track_set_path(t, NodePath(str(get_path_to(nodo)) + ":" + prop))
	return t


func _pista_rot(a: Animation, nodo: Node) -> int:
	# pistas de rotación por cuaternión: así el GLB las exporta bien
	var t := a.add_track(Animation.TYPE_ROTATION_3D)
	a.track_set_path(t, NodePath(str(get_path_to(nodo))))
	return t


func _eje(nodo: Node3D) -> Vector3:
	return Vector3.UP if nodo.get_meta("eje") == "y" else Vector3.RIGHT


func _girar(a: Animation, h: Node3D, t0: float, t1: float) -> void:
	var t := _pista_rot(a, h)
	var eje := _eje(h)
	var fin := float(h.get_meta("signo")) * float(h.get_meta("grados"))
	a.rotation_track_insert_key(t, 0.0, Quaternion.IDENTITY)
	a.rotation_track_insert_key(t, t0, Quaternion.IDENTITY)
	a.rotation_track_insert_key(t, t1, Quaternion(eje, fin))
	a.track_set_interpolation_type(t, Animation.INTERPOLATION_CUBIC)


func _animacion() -> void:
	var a := Animation.new()
	a.length = DUR
	a.step = 1.0 / FPS
	# disco: una vuelta en 30 s
	var tp := _pista_rot(a, plataforma)
	a.rotation_track_insert_key(tp, 0.0, Quaternion.IDENTITY)
	a.rotation_track_insert_key(tp, DUR, Quaternion(Vector3.UP, TAU))
	# ruedas: giran a media vuelta por segundo (el aliasing a 30 fps se ve feo con más)
	for r in ruedas:
		var tr := _pista_rot(a, r)
		for f in int(DUR * FPS) + 1:
			var tt := float(f) / FPS
			a.rotation_track_insert_key(tr, tt, Quaternion(Vector3.RIGHT, -tt * TAU * 0.5))
	# puertas, en orden: copiloto, conductor, traseras
	var orden := [["pf", 2.5, 4.5], ["df", 5.0, 7.0], ["pr", 7.5, 9.5], ["dr", 8.0, 10.0]]
	for o in orden:
		_girar(a, bisagras[o[0]], o[1], o[2])
	# vidrios: bajan todos a la vez
	for v in ventanas:
		var tv := a.add_track(Animation.TYPE_POSITION_3D)
		a.track_set_path(tv, NodePath(str(get_path_to(v))))
		var p0: Vector3 = v.position
		a.position_track_insert_key(tv, 0.0, p0)
		a.position_track_insert_key(tv, 10.5, p0)
		a.position_track_insert_key(tv, 12.5, p0 + Vector3(0, -ALTO_VENTANA, 0))
		a.track_set_interpolation_type(tv, Animation.INTERPOLATION_CUBIC)
	# baúl y capó
	_girar(a, bisagras["baul"], 13.0, 15.0)
	_girar(a, bisagras["capo"], 15.5, 17.5)
	# neón: respira despacio
	for om in neones_luz:
		var tn := _pista(a, om, "light_energy")
		for k in int(DUR * 2) + 1:
			var tt := k * 0.5
			a.track_insert_key(tn, tt, 0.6 + 0.15 * sin(tt * 1.7))
	# cámara: posición y mirada, un cuadro cada vez
	var tc_pos := a.add_track(Animation.TYPE_POSITION_3D)
	a.track_set_path(tc_pos, NodePath(str(get_path_to(camara))))
	var tc_rot := a.add_track(Animation.TYPE_ROTATION_3D)
	a.track_set_path(tc_rot, NodePath(str(get_path_to(camara))))
	for f in int(DUR * FPS) + 1:
		var tt := float(f) / FPS
		var pos := _herm(1, tt)
		var mira := _herm(2, tt)
		var base := Basis.looking_at(mira - pos, Vector3.UP)
		a.position_track_insert_key(tc_pos, tt, pos)
		a.rotation_track_insert_key(tc_rot, tt, base.get_rotation_quaternion())
	camara.position = _herm(1, 0.0)
	camara.basis = Basis.looking_at(_herm(2, 0.0) - _herm(1, 0.0), Vector3.UP)
	var ap := AnimationPlayer.new()
	ap.name = "Animacion"
	add_child(ap)
	var lib := AnimationLibrary.new()
	lib.add_animation("toma", a)
	ap.add_animation_library("", lib)
	ap.autoplay = "toma"
	ap.play("toma")
