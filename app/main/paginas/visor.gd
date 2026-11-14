extends Pagina
## VISOR 3D: carga el GLB liviano de la escena/escenario (colores planos, luces, cámaras de rodaje y animación).
## Gestos: un dedo gira, dos dedos acercan/alejan y desplazan. Botones: cámaras de rodaje, animación, luces.

var _vp: SubViewport
var _raiz3d: Node3D
var _pivote: Node3D
var _cam: Camera3D
var _modelo: Node3D
var _anim: AnimationPlayer
var _camaras: Array[Camera3D] = []
var _info: Label
var _slider: HSlider
var _play: Button
var _lista_cam: VBoxContainer
var _luces_escena := true
var _luz_estudio: DirectionalLight3D
var _ambiente: WorldEnvironment
var _toques := {}
var _dist := 30.0
var _yaw := -0.6
var _pitch := -0.45
var _camara_rodaje: Camera3D = null
var _url := ""

func abrir(d: Dictionary) -> void:
	var cont := SubViewportContainer.new()
	cont.set_anchors_preset(Control.PRESET_FULL_RECT)
	cont.stretch = true
	cont.stretch_shrink = 1
	cont.gui_input.connect(_entrada)
	add_child(cont)
	_vp = SubViewport.new()
	_vp.msaa_3d = Viewport.MSAA_2X
	_vp.own_world_3d = true
	cont.add_child(_vp)
	_raiz3d = Node3D.new()
	_vp.add_child(_raiz3d)
	_ambiente = WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.025, 0.04)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.35, 0.38, 0.5)
	env.ambient_light_energy = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	_ambiente.environment = env
	_raiz3d.add_child(_ambiente)
	_luz_estudio = DirectionalLight3D.new()
	_luz_estudio.rotation_degrees = Vector3(-50, -35, 0)
	_luz_estudio.light_energy = 0.15
	_raiz3d.add_child(_luz_estudio)
	_pivote = Node3D.new()
	_raiz3d.add_child(_pivote)
	_cam = Camera3D.new()
	_cam.far = 3000
	_cam.fov = 55
	_pivote.add_child(_cam)
	_cam.current = true
	# interfaz superpuesta
	var arriba := HBoxContainer.new()
	arriba.set_anchors_preset(Control.PRESET_TOP_WIDE)
	arriba.offset_left = 12
	arriba.offset_top = 10
	arriba.offset_right = -12
	add_child(arriba)
	arriba.add_child(Tema.boton("◀  VOLVER", func(): app.atras()))
	_info = Tema.etiqueta("  " + str(d.get("titulo", "Visor 3D")), 20)
	_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	arriba.add_child(_info)
	arriba.add_child(Tema.boton("💡 LUCES", _alternar_luces))
	arriba.add_child(Tema.boton("⌖ VISTA LIBRE", _vista_libre))
	var abajo := HBoxContainer.new()
	abajo.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	abajo.offset_left = 12
	abajo.offset_right = -12
	abajo.offset_top = -66
	abajo.offset_bottom = -10
	add_child(abajo)
	_play = Tema.boton("▶ ANIMACIÓN", _alternar_anim, "acento")
	abajo.add_child(_play)
	_slider = HSlider.new()
	_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_slider.step = 0.01
	_slider.value_changed.connect(func(v):
		if _anim and not _anim.is_playing():
			_anim.seek(v, true))
	abajo.add_child(_slider)
	var der := ScrollContainer.new()
	der.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	der.offset_left = -260
	der.offset_top = 80
	der.offset_bottom = -80
	der.offset_right = -12
	add_child(der)
	_lista_cam = VBoxContainer.new()
	_lista_cam.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	der.add_child(_lista_cam)
	_url = str(d.get("archivo", {}).get("url", ""))
	_info.text = "  Descargando escena 3D…"
	api.obtener(d.get("archivo", {}), func(ruta: String):
		if not is_instance_valid(self):
			return
		if ruta == "":
			_info.text = "  No se pudo descargar la escena 3D."
			return
		_cargar_glb(ruta, str(d.get("titulo", ""))))

func _cargar_glb(ruta: String, titulo: String) -> void:
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var err := doc.append_from_file(ruta, st)
	if err != OK:
		_info.text = "  Error al abrir la escena 3D (%d)." % err
		return
	_modelo = doc.generate_scene(st)
	_raiz3d.add_child(_modelo)
	var aabb := AABB()
	var primero := true
	for n in _modelo.find_children("*", "", true, false):
		if n is MeshInstance3D:
			var b: AABB = n.global_transform * n.get_aabb()
			if b.size.length() > 400 or b.get_center().length() > 150:
				continue  # el suelo y el fondo lejanos no cuentan para encuadrar
			aabb = b if primero else aabb.merge(b)
			primero = false
		elif n is Camera3D:
			_camaras.append(n)
		elif n is Light3D:
			# Blender exporta potencias físicas (vatios → candelas) que en tiempo real queman la imagen:
			# en el visor se usan intensidades fijas por tipo (sirven para ver dónde está cada luz y su color).
			n.shadow_enabled = false
			if n is OmniLight3D:
				n.light_energy = 0.8
				n.omni_range = 6.0
			elif n is SpotLight3D:
				n.light_energy = 1.5
				n.spot_range = 18.0
			elif n is DirectionalLight3D:
				n.light_energy = 0.25
		elif n is AnimationPlayer and _anim == null:
			_anim = n
	_pivote.position = aabb.get_center()
	_dist = clampf(aabb.size.length() * 0.7, 3.0, 400.0)
	_aplicar_orbita()
	_info.text = "  %s  ·  %d cámaras de rodaje%s" % [titulo, _camaras.size(), "  ·  con animación" if _anim else ""]
	if _anim:
		# Blender exporta un clip por objeto (cámaras, auto, portón…): se unen en uno solo para verlos juntos
		var todo := Animation.new()
		for nombre in _anim.get_animation_list():
			var a := _anim.get_animation(nombre)
			todo.length = maxf(todo.length, a.length)
			for i in a.get_track_count():
				a.copy_track(i, todo)
		var lib := AnimationLibrary.new()
		lib.add_animation("escena", todo)
		_anim.add_animation_library("estudio", lib)
		_anim.current_animation = "estudio/escena"
		_anim.pause()
		_slider.max_value = todo.length
	else:
		_play.disabled = true
	_lista_cam.add_child(Tema.etiqueta("CÁMARAS DE RODAJE", 15, Tema.ACENTO))
	for c in _camaras:
		var b := Tema.boton(str(c.name).replace("CAM_", ""), _ver_desde.bind(c), "", 16)
		b.custom_minimum_size.y = 44
		_lista_cam.add_child(b)

func _ver_desde(c: Camera3D) -> void:
	_camara_rodaje = c
	c.current = true
	_info.text = "  Viendo desde: " + str(c.name)

func _vista_libre() -> void:
	_camara_rodaje = null
	_cam.current = true

func _alternar_luces() -> void:
	_luces_escena = not _luces_escena
	if _modelo:
		for n in _modelo.find_children("*", "Light3D", true, false):
			n.visible = _luces_escena
	_luz_estudio.light_energy = 0.15 if _luces_escena else 1.2
	_ambiente.environment.ambient_light_energy = 0.35 if _luces_escena else 0.9
	app.mostrar_aviso("Iluminación de la escena" if _luces_escena else "Iluminación de estudio (para revisar formas)", 1.5)

func _alternar_anim() -> void:
	if not _anim:
		return
	if _anim.is_playing():
		_anim.pause()
		_play.text = "▶ ANIMACIÓN"
	else:
		_anim.play()
		_play.text = "⏸ PAUSA"

func _process(_d: float) -> void:
	if _modelo == null and _url != "":
		var f := api.fraccion(_url)
		if f >= 0:
			_info.text = "  Descargando escena 3D… %d %%" % int(f * 100)
	if _anim and _anim.is_playing():
		_slider.set_value_no_signal(_anim.current_animation_position)

func _aplicar_orbita() -> void:
	_pitch = clampf(_pitch, -1.45, 0.3)
	_pivote.rotation = Vector3(_pitch, _yaw, 0)
	_cam.position = Vector3(0, 0, _dist)

func _entrada(e: InputEvent) -> void:
	if e is InputEventScreenTouch:
		if e.pressed:
			_toques[e.index] = e.position
		else:
			_toques.erase(e.index)
	elif e is InputEventScreenDrag:
		var antes: Vector2 = _toques.get(e.index, e.position)
		_toques[e.index] = e.position
		if _toques.size() == 1:
			_yaw -= e.relative.x * 0.006
			_pitch -= e.relative.y * 0.006
		elif _toques.size() == 2:
			var ks := _toques.keys()
			var otro: Vector2 = _toques[ks[0] if ks[1] == e.index else ks[1]]
			var d_antes: float = antes.distance_to(otro)
			var d_ahora: float = e.position.distance_to(otro)
			if d_antes > 1:
				_dist = clampf(_dist * d_antes / maxf(1.0, d_ahora), 1.0, 600.0)
			_pivote.translate_object_local(Vector3(-e.relative.x, e.relative.y, 0) * _dist * 0.0006)
		_vista_libre()
		_aplicar_orbita()
	elif e is InputEventMagnifyGesture:
		_dist = clampf(_dist / e.factor, 1.0, 600.0)
		_aplicar_orbita()
	elif e is InputEventMouseButton and e.pressed:
		if e.button_index == MOUSE_BUTTON_WHEEL_UP:
			_dist = maxf(1.0, _dist * 0.9)
		elif e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_dist = minf(600.0, _dist * 1.1)
		_aplicar_orbita()
	elif e is InputEventMouseMotion and (e.button_mask & MOUSE_BUTTON_MASK_LEFT) and DisplayServer.is_touchscreen_available() == false:
		_yaw -= e.relative.x * 0.006
		_pitch -= e.relative.y * 0.006
		_vista_libre()
		_aplicar_orbita()
