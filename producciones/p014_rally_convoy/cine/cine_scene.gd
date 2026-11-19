extends Node3D
## Escena de la cinemática «Rally Convoy»: el mundo de la Aventura de Dream Racing (ruta armada con su generador), los siete autos
## ORIGINALES completos (carrocería, ruedas, cabina 3D y pilotos animados) conducidos por la física y la IA reales, el pelotón,
## el auto fantasma de cámara, la dirección de cámaras y el sonido. Corre sola de principio a fin; `--write-movie` la graba.
## Argumentos (después de `--`):  --fps=12  --t_end=300  --seek=T (avanza la simulación sin dibujar hasta T)  --shot=archivo.png
##   --cam=<tipo>  --car=<n>  --quality=1.0

const Core := preload("res://cine/cine_core.gd")
const Director := preload("res://cine/director.gd")
const AdvWorld := preload("res://game/adventure/adv_world.gd")
const Cockpit := preload("res://game/car/cockpit.gd")
const CarAudio := preload("res://game/audio/car_audio.gd")
const CameraRig := preload("res://game/car/camera_rig.gd")

var core
var world3d: Node3D
var adv_world
var cam: Camera3D
var env: Environment
var sun: DirectionalLight3D
var cockpits: Array = []
var audio
var dir # Director
var fps := 12
var t_end := 330.0
var t_now := 0.0
var frame := 0
var seek_to := -1.0
var shot_path := ""
var args := {}
var quality := 1.0
var _fog_col := Color(0.72, 0.82, 0.93)
var _last_inside := -1
var export_mode := false # exportación a Blender: la cabina y las ruedas se dejan siempre completas (el plano decide qué se ve)

func _arg(k: String, d: String = "") -> String:
	return str(args.get(k, d))

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and a.contains("="):
			var kv := a.substr(2).split("=", true, 1)
			args[kv[0]] = kv[1]
		elif a.begins_with("--"):
			args[a.substr(2)] = "1"
	var rw := int(_arg("w", "480"))
	var rh := int(_arg("h", "854"))
	get_window().size = Vector2i(rw, rh)
	get_window().content_scale_size = Vector2i(rw, rh)
	fps = int(_arg("fps", "12"))
	t_end = float(_arg("t_end", "330"))
	seek_to = float(_arg("seek", "-1"))
	shot_path = _arg("shot", "")
	quality = float(_arg("quality", "1.0"))
	Car_hook()
	core = Core.new()
	core.build(true)
	_build_world()
	_build_cars()
	dir = Director.new()
	dir.setup(self)
	print("[cine] escena lista · ruta %d m · %d autos · %d cuadros/s" % [int(core.track.length), core.cars.size(), fps])
	if seek_to >= 0.0:
		_advance(seek_to)
		_step_visuals(0.0, true)
	if shot_path != "":
		await get_tree().process_frame
		await get_tree().process_frame

func Car_hook() -> void:
	const Car := preload("res://game/car/car.gd")
	Car.set_sync_hook(func() -> void: pass)

func _build_world() -> void:
	world3d = Node3D.new()
	add_child(world3d)
	env = Environment.new()
	var sky := Sky.new()
	var psm := ProceduralSkyMaterial.new()
	psm.sky_top_color = Color(0.30, 0.52, 0.86)
	psm.sky_horizon_color = Color(0.74, 0.83, 0.93)
	psm.ground_horizon_color = Color(0.62, 0.70, 0.74)
	psm.ground_bottom_color = Color(0.30, 0.36, 0.34)
	psm.sun_angle_max = 22.0
	sky.sky_material = psm
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.75
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_light_color = _fog_col
	env.fog_density = 0.0011
	var we := WorldEnvironment.new()
	we.environment = env
	world3d.add_child(we)
	sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38, 52, 0)
	sun.light_energy = 1.15
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 140.0
	sun.shadow_blur = 1.4
	world3d.add_child(sun)
	cam = Camera3D.new()
	cam.keep_aspect = Camera3D.KEEP_WIDTH
	cam.fov = 70.0
	cam.near = 0.08
	cam.far = 1400.0
	world3d.add_child(cam)
	cam.make_current()
	adv_world = AdvWorld.new()
	adv_world.setup(core.track, quality)
	world3d.add_child(adv_world)
	# toda la ruta armada de antemano (la grabación no tiene apuro: nada de tramos que aparecen)
	adv_world.build_now(0.0, core.track.length)
	core.toll_node = _build_toll()
	world3d.add_child(core.toll_node)

func _build_cars() -> void:
	for k in core.cars.size():
		var car = core.cars[k]
		world3d.add_child(car.visual)
		var Vp = car.phys.V
		var id: String = core.ids[k]
		var st: Dictionary = core.states[k]
		var pp: Dictionary = st["paint"]
		var cp := Cockpit.new(str(core.vehicles[id].get("visualType", id)), Color(str(pp["body"])), Color(str(pp.get("rim", "#2a2d33"))), {})
		cp.crew_out = true # los pilotos se ven desde afuera (vidrios translúcidos); la cabina 3D sólo con la cámara interior
		car.visual.set_clear_glass(true)
		cp.position = Vector3(0, -Vp.comHeight + Vp.rideOffset, 0)
		car.visual.add_child(cp)
		cp.set_engine(Vp.maxRpm, Vp.shiftUpRpm)
		cp.set_inside(false, false)
		cockpits.append(cp)
	audio = CarAudio.new()
	add_child(audio)

## Peaje: pórtico con cabinas y barreras que se levantan al pasar el grupo
func _build_toll() -> Node3D:
	var root := Node3D.new()
	root.name = "Peaje"
	var tr = core.track
	var i: int = core.toll_i + 14
	var p: Vector3 = tr.samples[i]
	var tg: Vector3 = tr.tangents[i]
	var lt: Vector3 = tr.laterals[i]
	root.position = Vector3(p.x, p.y, p.z)
	root.basis = Basis.looking_at(-tg, Vector3.UP) # +z local = hacia adelante de la ruta
	var white := _mat(Color(0.93, 0.93, 0.9), 0.6)
	var blue := _mat(Color(0.10, 0.17, 0.45), 0.5)
	var orange := _mat(Color(1.0, 0.48, 0.1), 0.5)
	var hw: float = float(tr.hwa[i])
	# techo (pórtico) a lo ancho del camino
	_box(root, Vector3(0, 5.3, 0), Vector3(hw * 2.0 + 5.0, 0.7, 11.0), white)
	_box(root, Vector3(0, 5.62, 0), Vector3(hw * 2.0 + 5.06, 0.3, 11.06), blue)
	_box(root, Vector3(0, 4.9, 0), Vector3(hw * 2.0 + 5.04, 0.1, 11.04), orange)
	# islas con cabinas entre los carriles y columnas
	var lanes := 4
	var cw := hw * 2.0 / float(lanes)
	for k in lanes + 1:
		var x := -hw + float(k) * cw
		_box(root, Vector3(x, 0.15, 0), Vector3(0.9, 0.3, 9.0), _mat(Color(0.75, 0.75, 0.72), 0.9))
		_box(root, Vector3(x, 2.6, 0), Vector3(0.7, 5.2, 0.7), white)
		if k > 0 and k < lanes:
			_box(root, Vector3(x, 1.2, -0.5), Vector3(1.5, 2.4, 3.0), white)
			_box(root, Vector3(x, 1.7, 1.05), Vector3(1.52, 1.0, 0.1), _mat(Color(0.1, 0.16, 0.22), 0.2))
	# barreras: una por carril, giran al paso del grupo
	core.toll_arms.clear()
	for k in lanes:
		var x := -hw + (float(k) + 0.5) * cw
		var piv := Node3D.new()
		piv.position = Vector3(x - cw * 0.45, 1.0, 3.3)
		root.add_child(piv)
		var bar := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(cw * 0.86, 0.14, 0.12)
		bar.mesh = bm
		bar.position = Vector3(cw * 0.43, 0, 0)
		bar.material_override = _mat(Color(0.9, 0.1, 0.1), 0.5)
		piv.add_child(bar)
		core.toll_arms.append(piv)
	var lb := Label3D.new()
	lb.text = "PEAJE"
	lb.font_size = 220
	lb.pixel_size = 0.012
	lb.position = Vector3(0, 5.62, 5.62)
	lb.modulate = Color(1, 1, 1)
	root.add_child(lb)
	var lb2 := lb.duplicate()
	lb2.position = Vector3(0, 5.62, -5.62)
	lb2.rotation = Vector3(0, PI, 0)
	root.add_child(lb2)
	return root

func _mat(c: Color, rough := 0.8) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	return m

func _box(parent: Node3D, pos: Vector3, size: Vector3, m: Material) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.position = pos
	mi.material_override = m
	parent.add_child(mi)

## Avanza la simulación (física + IA reales) hasta t
func _advance(t: float) -> void:
	core.step_to(t)
	t_now = t
	# barreras del peaje: se levantan cuando se acerca el primero y bajan cuando pasa el último
	var lead := 0.0
	var rear := 1e18
	for i in core.cars.size():
		lead = maxf(lead, core.pel.s[i])
		rear = minf(rear, core.pel.s[i])
	var tgt := 0.0 if (rear > core.toll_s + 20.0 or lead < core.toll_s - 90.0) else 1.0
	for a in core.toll_arms:
		var cur: float = a.rotation.z
		a.rotation.z = move_toward(cur, deg_to_rad(80.0) * tgt, deg_to_rad(120.0) / float(maxi(fps, 1)))

func _step_visuals(dt: float, force := false) -> void:
	for c in core.cars:
		c.snap.sample(core.sim_t)
		c.update_visual(dt)
	var cpos := cam.global_position
	for k in core.cars.size():
		var snp = core.cars[k].snap
		var near := cpos.distance_to(Vector3(snp.px, snp.py, snp.pz)) < 90.0
		if near or force:
			cockpits[k].update_crew(dt, snp, false, t_now, 0.0)
	dir.update(dt)
	cam.fov = dir.fov
	adv_world.follow(cam.global_position, _fog_col)
	var inside_k: int = dir.inside_car
	if inside_k != _last_inside and not export_mode:
		for k in core.cars.size():
			var on: bool = (k == inside_k)
			core.cars[k].visual.set_inside(on)
			cockpits[k].set_inside(on, false) # false: con la cámara del piloto no se dibuja su cabeza ni el casco (no quedan retazos)
		_last_inside = inside_k
	if inside_k >= 0:
		cockpits[inside_k].update_cabin(dt, core.cars[inside_k].snap, false, t_now)
	_audio(dt)

func _audio(dt: float) -> void:
	var f: int = dir.focus_car
	var snp = core.cars[f].snap
	audio.update(snp, core.cars[f].phys.V, dt, snp.take_events(), snp.take_impact())
	# el rival más cercano al foco también suena
	var nd := -1.0
	var nrpm := 0.0
	for i in core.cars.size():
		if i == f:
			continue
		var d2 := Vector2(core.cars[i].snap.px - snp.px, core.cars[i].snap.pz - snp.pz).length()
		if d2 < 70.0 and (nd < 0.0 or d2 < nd):
			nd = d2
			nrpm = core.cars[i].snap.rpm
	audio.rival(nd, nrpm, core.cars[f].phys.V.firingOrder)

func _process(delta: float) -> void:
	if seek_to >= 0.0 or shot_path != "":
		if shot_path != "" and frame >= 3:
			get_viewport().get_texture().get_image().save_png(shot_path)
			print("[cine] captura ", shot_path, " t=%.1f" % t_now)
			get_tree().quit()
		frame += 1
		_step_visuals(1.0 / float(fps))
		return
	var dt := 1.0 / float(fps)
	_advance(t_now + dt)
	_step_visuals(dt)
	frame += 1
	if t_now >= t_end:
		print("[cine] fin: %d cuadros · %.1f s" % [frame, t_now])
		get_tree().quit()
