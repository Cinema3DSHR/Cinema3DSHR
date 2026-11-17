extends Pagina
## EDITOR 3D / PREVISUALIZACIÓN — dirección, revisión y aprobación de una escena ANTES del render.
##
## Carga la previsualización exportada de LA MISMA escena de producción (<escena>_v<k>_previa.glb + .json):
## mismos modelos, esqueletos, animaciones (horneadas cuadro a cuadro), cámaras de rodaje, luces y tiempos.
## · Cámara libre (táctil: izquierda = moverse, derecha = mirar, dos dedos = subir/bajar y avanzar;
##   escritorio: arrastrar = mirar, WASD = moverse, Q/E = bajar/subir, rueda = velocidad, Mayús = rápido).
## · Línea de tiempo con velocidades 0,25×…1,5×, cuadro a cuadro y marcadores con notas.
## · COLOCAR CÁMARA captura el punto de vista EXACTO (en coordenadas de Blender) y lo manda al estudio.
## · Panel de escena (personajes, qué clip hace cada uno, objetos, propiedades), cámaras y dirección.
## La vista 3D es 16:9 como el render: lo que se encuadra acá es lo que sale en el video.
## REGLA PERMANENTE (docs/REVISION_Y_AUTORIZACION.md): el render final sólo se habilita con ✔ APROBAR (versión cargada
## completa y con la huella de la versión actual) y después AUTORIZAR RENDER FINAL. El estado de la versión (8 estados)
## se ve arriba; sin la escena cargada, o con una previsualización vieja, no se puede aprobar ni autorizar.

const VELOCIDADES := [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]

var _d: Dictionary = {}           # datos de la previa (.json)
var _pid := ""
var _eid := ""
var _version := 1
var _huella := ""
var _fps := 30.0
var _dur := 30.0
var _t := 0.0
var _jugando := false
var _vel := 1.0

var _vp: SubViewport
var _cont: SubViewportContainer
var _mundo: Node3D
var _escena: Node3D
var _ap: AnimationPlayer
var _cam_libre: Camera3D
var _cam_activa: Camera3D
var _modo := "libre"              # libre | toma | montaje
var _toma_fija := ""
var _yaw := 0.0
var _pitch := -0.15
var _vel_mov := 2.0
var _subir := 0.0
var _toques := {}
var _joy_id := -1
var _joy_origen := Vector2.ZERO
var _joy_vec := Vector2.ZERO
var _toque_ini := {}

var _camaras_rodaje := {}         # nombre -> Camera3D
var _vis := {}                    # Node3D -> [[f0, f1), …]
var _actores: Array = []          # {id, d, nodo, esq, cadera}
var _sel := {}                    # {tipo, id, nodo}
var _solo := false
var _estado := {"camaras": [], "marcadores": [], "notas": []}
var _ab: Array = []
var _ab_idx := 0

var _info: Label
var _hora: Label
var _slider: HSlider
var _marcas: Control
var _play: Button
var _lista_pj: VBoxContainer
var _lista_obj: VBoxContainer
var _filtro: LineEdit
var _props: Label
var _lista_tomas: VBoxContainer
var _lista_cam: VBoxContainer
var _lista_marc: VBoxContainer
var _historial: VBoxContainer
var _chat: TextEdit
var _velmov_lbl: Label
var _modo_lbl: Label
var _dialogo: Control
var _cargando := ""
var _medio: BoxContainer
var _marco: Control
var _tabs: TabContainer
var _btn_colocar: Button
var _acc_t := 0.0
var _cargado := false             # true sólo si GLB + línea de tiempo cargaron completos y la huella es la actual
var _aviso_carga := ""
var _estado_lbl: Label
var _btn_aprobar: Button
var _btn_autorizar: Button

# ================================================================================================= construcción

func abrir(datos: Dictionary) -> void:
	_pid = str(datos.get("produccion", ""))
	_eid = str(datos.get("escena", "e01"))
	_version = int(datos.get("version", 1))
	app.pantalla_completa(true)
	var raiz := VBoxContainer.new()
	raiz.set_anchors_preset(Control.PRESET_FULL_RECT)
	raiz.add_theme_constant_override("separation", 4)
	add_child(raiz)
	raiz.add_child(_barra_superior())
	var medio := BoxContainer.new()
	_medio = medio
	medio.size_flags_vertical = Control.SIZE_EXPAND_FILL
	medio.add_theme_constant_override("separation", 6)
	raiz.add_child(medio)
	medio.add_child(_vista())
	medio.add_child(_panel_lateral())
	raiz.add_child(_linea_de_tiempo())
	_acomodar()
	_cargar_estado()
	api.catalogo_listo.connect(func(_c, _r): if is_instance_valid(self): _actualizar_estado_revision())
	_actualizar_estado_revision()
	# archivos: desde el catálogo (archivos.previa / archivos.previa_datos) o rutas locales (pruebas)
	if datos.has("glb_local"):
		_cargar(str(datos["glb_local"]), str(datos["json_local"]))
		return
	var arch: Dictionary = datos.get("archivos", {})
	if not arch.has("previa") or not arch.has("previa_datos"):
		_info.text = "  Esta versión todavía no tiene previsualización 3D (el estudio la genera con el flujo «Previsualización 3D»)."
		return
	_info.text = "  Descargando previsualización…"
	_cargando = str(arch["previa"].get("url", ""))
	api.obtener(arch["previa_datos"], func(ruta_json: String):
		if ruta_json == "":
			_info.text = "  No se pudo descargar la línea de tiempo."
			return
		api.obtener(arch["previa"], func(ruta_glb: String):
			if not is_instance_valid(self):
				return
			if ruta_glb == "":
				_info.text = "  No se pudo descargar la escena 3D."
				return
			_cargar(ruta_glb, ruta_json)))

## Vertical: la vista 3D (16:9) arriba a lo ancho, los paneles debajo y la línea de tiempo al pie.
func _acomodar() -> void:
	_medio.vertical = vertical
	_marco.size_flags_vertical = Control.SIZE_FILL if vertical else Control.SIZE_EXPAND_FILL
	_marco.custom_minimum_size.y = 400 if vertical else 0
	_tabs.custom_minimum_size.x = 0 if vertical else 330
	_tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_modo_lbl.visible = not vertical
	_btn_colocar.text = "🎥 COLOCAR" if vertical else "🎥 COLOCAR CÁMARA"
	_hora.custom_minimum_size.x = 112 if vertical else 150

func al_orientar(v: bool) -> void:
	vertical = v
	_acomodar()

func _exit_tree() -> void:
	if app:
		app.pantalla_completa(false)

func _barra_superior() -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	var v := Tema.boton("◀", func(): app.atras(), "", 20)
	v.custom_minimum_size = Vector2(56, 46)
	h.add_child(v)
	_info = Tema.etiqueta("  EDITOR 3D", 18, Tema.TEXTO)
	_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_info.clip_text = true
	h.add_child(_info)
	_estado_lbl = Tema.etiqueta("…", 15, Tema.ACENTO)
	h.add_child(_estado_lbl)
	_modo_lbl = Tema.etiqueta("CÁMARA LIBRE", 16, Tema.ACENTO)
	h.add_child(_modo_lbl)
	for par in [["LIBRE", _modo_libre], ["MONTAJE", _modo_montaje], ["💡", _alternar_luces]]:
		var b := Tema.boton(par[0], par[1], "", 16)
		b.custom_minimum_size = Vector2(0, 46)
		h.add_child(b)
	var colocar := Tema.boton("🎥 COLOCAR CÁMARA", _colocar_camara, "acento", 17)
	_btn_colocar = colocar
	colocar.custom_minimum_size = Vector2(0, 46)
	h.add_child(colocar)
	return h

func _vista() -> Control:
	var marco := Tema.panel(0, Color.BLACK, 6)
	_marco = marco
	marco.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	marco.size_flags_stretch_ratio = 2.6
	var asp := AspectRatioContainer.new()
	asp.ratio = 16.0 / 9.0
	marco.add_child(asp)
	_cont = SubViewportContainer.new()
	_cont.stretch = true
	_cont.gui_input.connect(_entrada)
	_cont.mouse_filter = Control.MOUSE_FILTER_STOP
	asp.add_child(_cont)
	_vp = SubViewport.new()
	_vp.own_world_3d = true
	_vp.msaa_3d = Viewport.MSAA_2X
	_vp.size = Vector2i(1280, 720)
	_cont.add_child(_vp)
	_mundo = Node3D.new()
	_vp.add_child(_mundo)
	var amb := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.55, 0.66, 0.82)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.8, 0.8, 0.85)
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	amb.environment = env
	amb.name = "ambiente"
	_mundo.add_child(amb)
	var sol := DirectionalLight3D.new()
	sol.name = "luz_estudio"
	sol.rotation_degrees = Vector3(-55, 25, 0)
	sol.light_energy = 0.6
	_mundo.add_child(sol)
	_cam_libre = Camera3D.new()
	_cam_libre.fov = 45.0
	_cam_libre.near = 0.03
	_cam_libre.far = 800
	_mundo.add_child(_cam_libre)
	_cam_libre.current = true
	_cam_activa = _cam_libre
	# guía de cuadro (tercios) y ayuda de controles
	var guia := _Guia.new()
	guia.set_anchors_preset(Control.PRESET_FULL_RECT)
	guia.mouse_filter = Control.MOUSE_FILTER_IGNORE
	guia.editor = self
	_cont.add_child(guia)
	var ayuda := Tema.etiqueta("Izquierda: moverse · Derecha: mirar · 2 dedos: subir/bajar y avanzar · Tocar: seleccionar", 13, Color(1, 1, 1, 0.55))
	ayuda.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	ayuda.offset_top = -22
	ayuda.offset_left = 10
	ayuda.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cont.add_child(ayuda)
	# subir / bajar (mantener apretado)
	var sb := VBoxContainer.new()
	sb.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	sb.offset_left = -64
	sb.offset_top = -60
	_cont.add_child(sb)
	for par in [["▲", 1.0], ["▼", -1.0]]:
		var b := Tema.boton(par[0], Callable(), "", 20)
		b.custom_minimum_size = Vector2(54, 54)
		b.button_down.connect(func(): _subir = par[1])
		b.button_up.connect(func(): _subir = 0.0)
		sb.add_child(b)
	return marco

func _panel_lateral() -> Control:
	var tabs := TabContainer.new()
	_tabs = tabs
	tabs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tabs.custom_minimum_size.x = 330
	tabs.add_theme_font_size_override("font_size", 16)
	# ---- ESCENA
	var esc := _pestana(tabs, "ESCENA")
	esc.add_child(Tema.etiqueta("PERSONAJES", 15, Tema.ACENTO))
	_lista_pj = VBoxContainer.new()
	esc.add_child(_lista_pj)
	var hs := HBoxContainer.new()
	hs.add_child(Tema.boton("SÓLO EL ELEGIDO", _alternar_solo, "", 15))
	hs.add_child(Tema.boton("ENCUADRAR", _encuadrar, "", 15))
	esc.add_child(hs)
	esc.add_child(Tema.etiqueta("PROPIEDADES", 15, Tema.ACENTO))
	_props = Tema.etiqueta("Tocá un personaje u objeto.", 14, Tema.TEXTO2, true)
	esc.add_child(_props)
	esc.add_child(Tema.etiqueta("OBJETOS", 15, Tema.ACENTO))
	_filtro = LineEdit.new()
	_filtro.placeholder_text = "Buscar objeto…"
	_filtro.text_changed.connect(func(_x): _llenar_objetos())
	esc.add_child(_filtro)
	_lista_obj = VBoxContainer.new()
	esc.add_child(_lista_obj)
	# ---- CÁMARAS
	var cams := _pestana(tabs, "CÁMARAS")
	var vh := HBoxContainer.new()
	_velmov_lbl = Tema.etiqueta("Velocidad 2.0 m/s", 14, Tema.TEXTO2)
	_velmov_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vh.add_child(_velmov_lbl)
	var vs := HSlider.new()
	vs.min_value = 0.2
	vs.max_value = 10.0
	vs.step = 0.1
	vs.value = _vel_mov
	vs.custom_minimum_size.x = 140
	vs.value_changed.connect(func(x): _vel_mov = x; _velmov_lbl.text = "Velocidad %.1f m/s" % x)
	vh.add_child(vs)
	cams.add_child(vh)
	var fila := HBoxContainer.new()
	fila.add_child(Tema.boton("💾 GUARDAR POSICIÓN", _guardar_posicion, "", 15))
	fila.add_child(Tema.boton("↩ VOLVER A CÁMARA", _volver_a_camara, "", 15))
	cams.add_child(fila)
	cams.add_child(Tema.etiqueta("CÁMARAS DEL DIRECTOR", 15, Tema.ACENTO))
	_lista_cam = VBoxContainer.new()
	cams.add_child(_lista_cam)
	cams.add_child(Tema.boton("⇄ COMPARAR A/B", _comparar, "", 15))
	cams.add_child(Tema.etiqueta("TOMAS DE LA ESCENA", 15, Tema.ACENTO))
	_lista_tomas = VBoxContainer.new()
	cams.add_child(_lista_tomas)
	# ---- DIRECCIÓN
	var dir := _pestana(tabs, "DIRECCIÓN")
	dir.add_child(Tema.etiqueta("Escribile al estudio (va con el tiempo, el personaje elegido y la cámara):", 14, Tema.TEXTO2, true))
	_chat = TextEdit.new()
	_chat.custom_minimum_size.y = 110
	_chat.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	_chat.placeholder_text = "Ej.: en este momento el operador gira demasiado rápido; hacelo más lento."
	dir.add_child(_chat)
	var fd := HBoxContainer.new()
	fd.add_child(Tema.boton("ENVIAR", _enviar_nota, "azul", 15))
	fd.add_child(Tema.boton("📍 MARCAR ESTE MOMENTO", _marcar, "", 15))
	dir.add_child(fd)
	dir.add_child(Tema.etiqueta("MARCADORES", 15, Tema.ACENTO))
	_lista_marc = VBoxContainer.new()
	dir.add_child(_lista_marc)
	var fa := HBoxContainer.new()
	fa.add_child(Tema.boton("GUARDAR CORRECCIONES", _guardar_correcciones, "acento", 15))
	_btn_aprobar = Tema.boton("✔ APROBAR ESCENA", _aprobar, "verde", 15)
	fa.add_child(_btn_aprobar)
	dir.add_child(fa)
	dir.add_child(Tema.etiqueta("RENDER FINAL (sólo con esta versión aprobada)", 15, Tema.ACENTO))
	var fr := HBoxContainer.new()
	_btn_autorizar = Tema.boton("🎬 AUTORIZAR RENDER FINAL", _autorizar, "acento", 15)
	fr.add_child(_btn_autorizar)
	fr.add_child(Tema.boton("⟳ ESTADO", func(): api.cargar_catalogo(), "", 15))
	dir.add_child(fr)
	dir.add_child(Tema.etiqueta("VERSIONES", 15, Tema.ACENTO))
	dir.add_child(_versiones())
	var fh := HBoxContainer.new()
	fh.add_child(Tema.etiqueta("HISTORIAL CON EL ESTUDIO", 15, Tema.ACENTO))
	fh.add_child(Tema.boton("⟳", _cargar_historial, "", 15))
	dir.add_child(fh)
	_historial = VBoxContainer.new()
	dir.add_child(_historial)
	return tabs

func _pestana(tabs: TabContainer, nombre: String) -> VBoxContainer:
	var sc := ScrollContainer.new()
	sc.name = nombre
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	tabs.add_child(sc)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 8)
	sc.add_child(v)
	return v

func _linea_de_tiempo() -> Control:
	var p := Tema.panel(8, Tema.PANEL, 8)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	p.add_child(h)
	for par in [["⏹", _detener], ["⏮", func(): _cuadro(-1)]]:
		h.add_child(_chico(par[0], par[1]))
	_play = _chico("▶", _alternar_reproduccion)
	_play.custom_minimum_size.x = 64
	h.add_child(_play)
	h.add_child(_chico("⏭", func(): _cuadro(1)))
	var ob := OptionButton.new()
	ob.add_theme_font_size_override("font_size", 16)
	for v in VELOCIDADES:
		ob.add_item(("%.2f×" % v).replace(".", ","))
	ob.selected = 3
	ob.item_selected.connect(func(i): _vel = VELOCIDADES[i])
	ob.custom_minimum_size = Vector2(96, 48)
	h.add_child(ob)
	var zona := Control.new()
	zona.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	zona.custom_minimum_size.y = 48
	h.add_child(zona)
	_slider = HSlider.new()
	_slider.set_anchors_preset(Control.PRESET_FULL_RECT)
	_slider.step = 0.001
	_slider.value_changed.connect(func(x):
		_jugando = false
		_play.text = "▶"
		_ir_a(x))
	zona.add_child(_slider)
	_marcas = _Marcas.new()
	_marcas.set_anchors_preset(Control.PRESET_FULL_RECT)
	_marcas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_marcas.editor = self
	zona.add_child(_marcas)
	_hora = Tema.etiqueta("0,00 s · f 1", 16, Tema.TEXTO)
	_hora.custom_minimum_size.x = 150
	h.add_child(_hora)
	h.add_child(_chico("📍", _marcar))
	return p

func _chico(t: String, f: Callable) -> Button:
	var b := Tema.boton(t, f, "", 20)
	b.custom_minimum_size = Vector2(52, 48)
	return b

# ================================================================================================= carga

func _cargar(ruta_glb: String, ruta_json: String) -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(ruta_json))
	if not (d is Dictionary):
		_info.text = "  La línea de tiempo está dañada."
		return
	_d = d
	_fps = float(_d.get("fps", 30))
	_dur = float(_d.get("duracion_s", 30))
	_huella = str(_d.get("huella", ""))
	_version = int(_d.get("version", _version))
	if _pid == "":
		_pid = str(_d.get("produccion", ""))
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var err := doc.append_from_file(ruta_glb, st)
	if err != OK:
		_info.text = "  Error al abrir la escena 3D (%d)." % err
		return
	_escena = doc.generate_scene(st)
	_mundo.add_child(_escena)
	for n in _escena.find_children("*", "", true, false):
		if n is Camera3D:
			_camaras_rodaje[str(n.name)] = n
		elif n is Light3D:
			# Blender exporta potencias físicas que en tiempo real queman la imagen: intensidades de referencia
			n.shadow_enabled = false
			if n is OmniLight3D:
				n.light_energy = 0.6
				n.omni_range = 5.0
			elif n is SpotLight3D:
				n.light_energy = 1.0
				n.spot_range = 12.0
			elif n is DirectionalLight3D:
				n.light_energy = 0.8
		elif n is AnimationPlayer and _ap == null:
			_ap = n
	if _ap:
		var todo := Animation.new()
		for nombre in _ap.get_animation_list():
			var a := _ap.get_animation(nombre)
			todo.length = maxf(todo.length, a.length)
			for i in a.get_track_count():
				a.copy_track(i, todo)
		var lib := AnimationLibrary.new()
		lib.add_animation("escena", todo)
		_ap.add_animation_library("estudio", lib)
		_ap.current_animation = "estudio/escena"
		_ap.pause()
	# destellos (fogonazos, impactos): visibles sólo en sus cuadros, como en el render
	for nombre in _d.get("visibilidad", {}):
		var n := _escena.find_child(str(nombre), true, false)
		if n is Node3D:
			_vis[n] = _d["visibilidad"][nombre]
			if n is OmniLight3D:
				n.light_energy = 3.0
				n.omni_range = 4.0
	# personajes
	for a in _d.get("actores", []):
		var nodo := _escena.find_child(str(a["nodo"]), true, false)
		var esq: Skeleton3D = null
		var cad := -1
		if nodo:
			var ss := nodo.find_children("*", "Skeleton3D", true, false)
			if ss.size():
				esq = ss[0]
				for nombre_h in ["mixamorig:Hips", "mixamorig_Hips", "Hips"]:
					cad = esq.find_bone(nombre_h)
					if cad >= 0:
						break
		_actores.append({"id": a["id"], "d": a, "nodo": nodo, "esq": esq, "cadera": cad})
	_slider.max_value = _dur
	# cámara libre: arranca desde la primera toma
	var tomas: Array = _d.get("tomas", [])
	if tomas.size() and _camaras_rodaje.has(str(tomas[0]["camara"])):
		_ir_a(0.0)
		var c0: Camera3D = _camaras_rodaje[str(tomas[0]["camara"])]
		_poner_libre(c0.global_transform, c0.fov)
	_info.text = "  %s · %s v%d · %d personajes · %d tomas" % [str(_d.get("titulo", "")), _eid, _version, _actores.size(), tomas.size()]
	_llenar_personajes()
	_llenar_objetos()
	_llenar_tomas()
	_llenar_camaras()
	_llenar_marcadores()
	_ir_a(0.0)
	var vc := api.version_catalogo(_pid, _eid, _version)
	var h_actual := str(vc.get("huella_actual", ""))
	if h_actual != "" and _huella != "" and h_actual != _huella:
		_cargado = false
		_aviso_carga = "La previsualización es de otra huella (%s, actual %s): el estudio tiene que publicar la nueva antes de revisar." % [_huella, h_actual]
		app.mostrar_aviso(_aviso_carga, 8.0)
	elif _escena == null or (_d.get("tomas", []) as Array).is_empty():
		_cargado = false
		_aviso_carga = "La escena no cargó completa: no se puede aprobar."
	else:
		_cargado = true
		_aviso_carga = ""
	_actualizar_estado_revision()

## Estado de revisión de ESTA versión (catálogo) y qué acciones se habilitan.
func _actualizar_estado_revision() -> void:
	if _estado_lbl == null:
		return
	var vc := api.version_catalogo(_pid, _eid, _version)
	var est := str(vc.get("estado_revision", "SIN DATOS DEL ESTUDIO"))
	_estado_lbl.text = "● " + est
	var aprobable := _cargado and not est in ["APROBADA POR EL USUARIO", "RENDER AUTORIZADO", "RENDER EN EJECUCIÓN", "FINALIZADA"]
	if _btn_aprobar:
		_btn_aprobar.disabled = not aprobable
	if _btn_autorizar:
		_btn_autorizar.disabled = not (_cargado and est == "APROBADA POR EL USUARIO")
		_btn_autorizar.tooltip_text = "" if not _btn_autorizar.disabled else \
			("Primero cargá y revisá la escena." if not _cargado else "Se habilita cuando ESTA versión está APROBADA (tocá ⟳ ESTADO después de aprobar).")

# ================================================================================================= tiempo

## cámara lenta: la animación del GLB está en tiempo de la escena; la línea de tiempo es la de la película
func _t_escena(t: float) -> float:
	var m = _d.get("mapa_tiempo")
	if not (m is Array) or (m as Array).size() < 2:
		return t
	var a: Array = m
	if t <= float(a[0][0]):
		return float(a[0][1]) + (t - float(a[0][0]))
	for i in range(1, a.size()):
		if t <= float(a[i][0]):
			var t0 := float(a[i - 1][0])
			var t1 := float(a[i][0])
			var k := (t - t0) / maxf(1e-9, t1 - t0)
			return lerpf(float(a[i - 1][1]), float(a[i][1]), k)
	var n := a.size()
	return float(a[n - 1][1]) + (t - float(a[n - 1][0]))

func _ir_a(t: float) -> void:
	_t = clampf(t, 0.0, _dur)
	if _ap:
		# el GLB de Blender pone el cuadro f en el tiempo f/fps (cuadro 1 = 1/fps); la película empieza en el cuadro 1
		_ap.seek(minf(_t_escena(_t) + 1.0 / _fps, _ap.current_animation_length), true)
	var f := _frame()
	for n in _vis:
		var on := false
		for r in _vis[n]:
			if f >= int(r[0]) and f < int(r[1]):
				on = true
				break
		n.visible = on
	if _modo == "montaje":
		var c := _camara_de_toma(_toma_en(_t))
		if c:
			_activar(c)
	elif _modo == "toma" and _camaras_rodaje.has(_toma_fija):
		_activar(_camaras_rodaje[_toma_fija])
	_slider.set_value_no_signal(_t)
	_hora.text = ("%.2f s · f %d" % [_t, f]).replace(".", ",")
	_marcas.queue_redraw()

func _frame() -> int:
	return mini(int(floor(_t * _fps + 1e-6)) + 1, int(_d.get("frames", int(_dur * _fps))))

func _cuadro(paso: int) -> void:
	_jugando = false
	_play.text = "▶"
	_ir_a((_frame() - 1 + paso) / _fps)

func _detener() -> void:
	_jugando = false
	_play.text = "▶"
	_ir_a(0.0)

func _alternar_reproduccion() -> void:
	_jugando = not _jugando
	if _jugando and _t >= _dur - 1e-3:
		_t = 0.0
	_play.text = "⏸" if _jugando else "▶"

func _toma_en(t: float) -> Dictionary:
	for tm in _d.get("tomas", []):
		if t >= float(tm["inicio_s"]) and t < float(tm["fin_s"]):
			return tm
	var ts: Array = _d.get("tomas", [])
	return ts.back() if ts.size() else {}

func _camara_de_toma(tm: Dictionary) -> Camera3D:
	return _camaras_rodaje.get(str(tm.get("camara", "")))

## Clip que reproduce un personaje en el instante t: {clip, inicio_s, fin_s, indice}
func clip_en(a: Dictionary, t: float) -> Dictionary:
	var acc: Array = a["d"].get("acciones", [])
	for i in acc.size():
		var ac: Dictionary = acc[i]
		var fin := float(acc[i + 1]["inicio_s"]) if i + 1 < acc.size() else float(ac["fin_s"])
		if t >= float(ac["inicio_s"]) and (t < fin or i == acc.size() - 1):
			return {"clip": ac["clip"], "inicio_s": float(ac["inicio_s"]), "fin_s": fin, "indice": i,
				"velocidad": ac.get("velocidad", 1.0), "ciclos": ac.get("ciclos", 1)}
	return {"clip": "—", "inicio_s": 0.0, "fin_s": 0.0, "indice": -1}

func _process(delta: float) -> void:
	if _escena == null:
		if _cargando != "":
			var fr := api.fraccion(_cargando)
			if fr >= 0:
				_info.text = "  Descargando previsualización… %d %%" % int(fr * 100)
		return
	if _jugando:
		var t := _t + delta * _vel
		if t >= _dur:
			t = _dur
			_jugando = false
			_play.text = "▶"
		_ir_a(t)
	_mover_camara(delta)
	_acc_t += delta
	if _acc_t > 0.25:
		_acc_t = 0.0
		_actualizar_personajes()
		_actualizar_props()

# ================================================================================================= cámara libre

func _poner_libre(tr: Transform3D, fov: float) -> void:
	_cam_libre.global_transform = tr
	_cam_libre.fov = fov
	var e := tr.basis.get_euler()
	_yaw = e.y
	_pitch = e.x

func _modo_libre() -> void:
	if _cam_activa and _cam_activa != _cam_libre:
		_poner_libre(_cam_activa.global_transform, _cam_activa.fov)
	_modo = "libre"
	_activar(_cam_libre)

func _modo_montaje() -> void:
	_modo = "montaje"
	_ir_a(_t)

func _activar(c: Camera3D) -> void:
	_cam_activa = c
	c.current = true
	_modo_lbl.text = {"libre": "CÁMARA LIBRE", "montaje": "MONTAJE · " + str(_toma_en(_t).get("id", "")),
		"toma": "TOMA · " + _toma_fija}.get(_modo, "")

func _mover_camara(delta: float) -> void:
	var mover := Vector3.ZERO
	if Input.is_physical_key_pressed(KEY_W):
		mover.z -= 1
	if Input.is_physical_key_pressed(KEY_S):
		mover.z += 1
	if Input.is_physical_key_pressed(KEY_A):
		mover.x -= 1
	if Input.is_physical_key_pressed(KEY_D):
		mover.x += 1
	var sube := _subir
	if Input.is_physical_key_pressed(KEY_E):
		sube += 1
	if Input.is_physical_key_pressed(KEY_Q):
		sube -= 1
	mover.x += _joy_vec.x
	mover.z += _joy_vec.y
	if mover == Vector3.ZERO and sube == 0.0:
		return
	if _modo != "libre":
		_modo_libre()
	var v := _vel_mov * (3.0 if Input.is_physical_key_pressed(KEY_SHIFT) else 1.0) * delta
	var b := _cam_libre.global_transform.basis
	var plano_z := Vector3(b.z.x, 0, b.z.z).normalized()
	var plano_x := Vector3(b.x.x, 0, b.x.z).normalized()
	_cam_libre.global_position += (plano_x * mover.x + plano_z * mover.z) * v + Vector3.UP * sube * v

func _mirar(rel: Vector2) -> void:
	if _modo != "libre":
		_modo_libre()
	_yaw -= rel.x * 0.005
	_pitch = clampf(_pitch - rel.y * 0.005, -1.55, 1.55)
	_cam_libre.global_basis = Basis.from_euler(Vector3(_pitch, _yaw, 0))

func _entrada(e: InputEvent) -> void:
	var tam := _cont.size
	if e is InputEventScreenTouch:
		if e.pressed:
			_toques[e.index] = e.position
			_toque_ini[e.index] = [e.position, Time.get_ticks_msec()]
			if e.position.x < tam.x * 0.35 and _joy_id < 0:
				_joy_id = e.index
				_joy_origen = e.position
		else:
			var ini = _toque_ini.get(e.index)
			if ini and e.position.distance_to(ini[0]) < 12 and Time.get_ticks_msec() - int(ini[1]) < 350 and _toques.size() == 1:
				_elegir_en(e.position)
			_toques.erase(e.index)
			_toque_ini.erase(e.index)
			if e.index == _joy_id:
				_joy_id = -1
				_joy_vec = Vector2.ZERO
	elif e is InputEventScreenDrag:
		var antes: Vector2 = _toques.get(e.index, e.position)
		_toques[e.index] = e.position
		if e.index == _joy_id:
			var d: Vector2 = (e.position - _joy_origen) / 80.0
			_joy_vec = d.limit_length(1.0)
		elif _toques.size() >= 2 and _joy_id < 0:
			# dos dedos: arrastre vertical = subir/bajar, pellizco = avanzar/retroceder
			var ks := _toques.keys()
			var otro: Vector2 = _toques[ks[0] if ks[1] == e.index else ks[1]]
			var avance: float = e.position.distance_to(otro) - antes.distance_to(otro)
			if _modo != "libre":
				_modo_libre()
			var b := _cam_libre.global_transform.basis
			_cam_libre.global_position += -b.z * avance * 0.01 * _vel_mov + Vector3.UP * (-e.relative.y) * 0.005 * _vel_mov
		else:
			_mirar(e.relative)
	elif e is InputEventMouseMotion and not DisplayServer.is_touchscreen_available():
		if e.button_mask & (MOUSE_BUTTON_MASK_LEFT | MOUSE_BUTTON_MASK_RIGHT):
			_mirar(e.relative)
	elif e is InputEventMouseButton and not DisplayServer.is_touchscreen_available():
		if e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_UP:
			_vel_mov = minf(10.0, _vel_mov * 1.15)
		elif e.pressed and e.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_vel_mov = maxf(0.2, _vel_mov / 1.15)
		elif e.button_index == MOUSE_BUTTON_LEFT:
			if e.pressed:
				_toque_ini[-1] = [e.position, Time.get_ticks_msec()]
			else:
				var ini = _toque_ini.get(-1)
				if ini and e.position.distance_to(ini[0]) < 6:
					_elegir_en(e.position)
		_velmov_lbl.text = "Velocidad %.1f m/s" % _vel_mov

# ================================================================================================= selección

func _elegir_en(p: Vector2) -> void:
	if _escena == null:
		return
	var esc := Vector2(_vp.size) / _cont.size
	var pv := p * esc
	var o := _cam_activa.project_ray_origin(pv)
	var dir := _cam_activa.project_ray_normal(pv)
	var mejor := {}
	var dist := 1e9
	for a in _actores:
		var c := _cadera(a)
		if c == Vector3.INF:
			continue
		var t := (c - o).dot(dir)
		if t > 0 and (o + dir * t).distance_to(c) < 0.55 and t < dist:
			dist = t
			mejor = {"tipo": "personaje", "id": a["id"], "nodo": a["nodo"]}
	if mejor.is_empty():
		for n in _escena.get_children():
			if n is MeshInstance3D and n.visible:
				var bb: AABB = n.global_transform * n.get_aabb()
				if bb.size.length() > 30:
					continue
				var hit = bb.intersects_ray(o, dir)
				if hit != null and o.distance_to(hit) < dist:
					dist = o.distance_to(hit)
					mejor = {"tipo": "objeto", "id": str(n.name), "nodo": n}
	if not mejor.is_empty():
		_elegir(mejor)

func _elegir(s: Dictionary) -> void:
	_sel = s
	if _solo:
		_aplicar_solo()
	_actualizar_props()
	_actualizar_personajes()

func _cadera(a: Dictionary) -> Vector3:
	var esq: Skeleton3D = a["esq"]
	if esq == null or a["cadera"] < 0:
		return a["nodo"].global_position if a["nodo"] else Vector3.INF
	return esq.global_transform * esq.get_bone_global_pose(a["cadera"]).origin

func _alternar_solo() -> void:
	_solo = not _solo
	_aplicar_solo()

func _aplicar_solo() -> void:
	for a in _actores:
		if a["nodo"]:
			a["nodo"].visible = (not _solo) or _sel.get("id", "") == a["id"] or _sel.get("tipo", "") != "personaje"

func _encuadrar() -> void:
	if _sel.is_empty() or _sel.get("nodo") == null:
		app.mostrar_aviso("Elegí primero un personaje u objeto.")
		return
	var c: Vector3
	if _sel["tipo"] == "personaje":
		c = _cadera(_actores.filter(func(x): return x["id"] == _sel["id"])[0])
	else:
		var n: MeshInstance3D = _sel["nodo"]
		c = (n.global_transform * n.get_aabb()).get_center()
	var desde := c + Vector3(2.2, 0.8, 2.2)
	_modo = "libre"
	_poner_libre(Transform3D(Basis(), desde).looking_at(c, Vector3.UP), _cam_libre.fov)
	_activar(_cam_libre)

func _actualizar_props() -> void:
	if _props == null:
		return
	if _sel.is_empty():
		_props.text = "Tocá un personaje u objeto en la vista o en las listas."
		return
	var nodo: Node3D = _sel.get("nodo")
	var txt := "%s  (%s)\n" % [_sel["id"], _sel["tipo"]]
	if _sel["tipo"] == "personaje":
		var a: Dictionary = _actores.filter(func(x): return x["id"] == _sel["id"])[0]
		var p := CamaraDirector.a_blender(_cadera(a))
		var c := clip_en(a, _t)
		txt += "Modelo: %s · arma: %s\nCadera (Blender): x %.2f  y %.2f  z %.2f\nAnimación: %s  (%.2f → %.2f s, ×%s)\n" % [
			a["d"].get("modelo", ""), str(a["d"].get("arma", "—")), p.x, p.y, p.z, c["clip"], c["inicio_s"], c["fin_s"], str(c.get("velocidad", 1.0))]
		var acc: Array = a["d"].get("acciones", [])
		var i: int = c["indice"]
		if i + 1 < acc.size():
			txt += "Sigue: %s a los %.2f s" % [acc[i + 1]["clip"], float(acc[i + 1]["inicio_s"])]
	elif nodo:
		var p := CamaraDirector.a_blender(nodo.global_position)
		var r := CamaraDirector.euler_blender(Basis(CamaraDirector.a_blender(nodo.global_basis.x), CamaraDirector.a_blender(nodo.global_basis.y), CamaraDirector.a_blender(nodo.global_basis.z)).orthonormalized())
		txt += "Posición (Blender): x %.2f  y %.2f  z %.2f\nRotación: x %.1f°  y %.1f°  z %.1f°\nVisible: %s" % [p.x, p.y, p.z, r.x, r.y, r.z, "sí" if nodo.visible else "no"]
	_props.text = txt

func _llenar_personajes() -> void:
	limpiar(_lista_pj)
	for a in _actores:
		var b := Tema.boton(a["id"], func(): _elegir({"tipo": "personaje", "id": a["id"], "nodo": a["nodo"]}), "", 15)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.clip_text = true
		b.set_meta("actor", a["id"])
		_lista_pj.add_child(b)
	_actualizar_personajes()

func _actualizar_personajes() -> void:
	if _lista_pj == null:
		return
	for b in _lista_pj.get_children():
		var aid := str(b.get_meta("actor", ""))
		var a: Dictionary = {}
		for x in _actores:
			if x["id"] == aid:
				a = x
		if a.is_empty():
			continue
		var c := clip_en(a, _t)
		b.text = "%s %s · %s" % ["●" if _sel.get("id", "") == aid else "○", aid, c["clip"]]

func _llenar_objetos() -> void:
	limpiar(_lista_obj)
	if _escena == null:
		return
	var f := _filtro.text.strip_edges().to_lower()
	var n := 0
	for o in _escena.get_children():
		if not (o is Node3D) or o is Camera3D:
			continue
		if f != "" and not str(o.name).to_lower().contains(f):
			continue
		n += 1
		if n > 80:
			_lista_obj.add_child(Tema.etiqueta("… (usá el buscador)", 13, Tema.TEXTO2))
			break
		var h := HBoxContainer.new()
		var cb := CheckBox.new()
		cb.button_pressed = o.visible
		cb.toggled.connect(func(v): o.visible = v)
		h.add_child(cb)
		var b := Tema.boton(str(o.name), func(): _elegir({"tipo": "objeto", "id": str(o.name), "nodo": o}), "", 14)
		b.custom_minimum_size.y = 40
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.clip_text = true
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(b)
		_lista_obj.add_child(h)

func _llenar_tomas() -> void:
	limpiar(_lista_tomas)
	for tm in _d.get("tomas", []):
		var b := Tema.boton("%s · %s–%s s · %s mm" % [tm["id"], _s(tm["inicio_s"]), _s(tm["fin_s"]), str(snappedf(float(tm["lente_mm"]), 0.1))],
			func(): _ver_toma(tm), "", 14)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size.y = 42
		b.tooltip_text = str(tm.get("plano", ""))
		_lista_tomas.add_child(b)

func _ver_toma(tm: Dictionary) -> void:
	_modo = "toma"
	_toma_fija = str(tm["camara"])
	if _t < float(tm["inicio_s"]) or _t >= float(tm["fin_s"]):
		_ir_a(float(tm["inicio_s"]))
	else:
		_ir_a(_t)

func _s(x) -> String:
	return ("%.1f" % float(x)).replace(".", ",")

func _alternar_luces() -> void:
	if _escena == null:
		return
	var luces := _escena.find_children("*", "Light3D", true, false)
	var on: bool = not (luces.size() > 0 and luces[0].visible)
	for l in luces:
		if not _vis.has(l):
			l.visible = on
	app.mostrar_aviso("Luces de la escena" if on else "Luz de estudio (para revisar formas)", 1.5)

# ================================================================================================= cámaras del director

func _ruta_estado() -> String:
	return "user://director/%s_%s.json" % [_pid, _eid]

func _cargar_estado() -> void:
	DirAccess.make_dir_recursive_absolute("user://director")
	if FileAccess.file_exists(_ruta_estado()):
		var d = JSON.parse_string(FileAccess.get_file_as_string(_ruta_estado()))
		if d is Dictionary:
			_estado.merge(d, true)

func _guardar_estado() -> void:
	var f := FileAccess.open(_ruta_estado(), FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_estado, " "))

func _proximo_id() -> String:
	var n := 0
	for c in _estado["camaras"]:
		n = maxi(n, int(str(c.get("camera_id", "camera_000")).get_slice("_", 1)))
	return "camera_%03d" % (n + 1)

func _capturar(nombre: String, toma: String, t0: float, t1: float, notas: String, transicion := "corte") -> Dictionary:
	var cid := _proximo_id()
	return CamaraDirector.capturar(_cam_activa, {
		"camera_id": cid, "name": nombre if nombre != "" else cid, "produccion": _pid, "escena": _eid,
		"version_escena": _version, "huella_escena": _huella, "shot": toma,
		"time_capture": snappedf(_t, 0.0001), "frame_capture": _frame(),
		"time_start": snappedf(t0, 0.0001), "time_end": snappedf(t1, 0.0001), "transition": transicion,
		"notes": notas, "source_view": _modo if _modo != "toma" else "toma " + _toma_fija})

func _colocar_camara() -> void:
	if _escena == null:
		return
	var tomas: Array = ["(toma nueva)"]
	for tm in _d.get("tomas", []):
		tomas.append(str(tm["id"]))
	var actual := str(_toma_en(_t).get("id", ""))
	_formulario("COLOCAR CÁMARA — se guarda este punto de vista exacto", [
		["nombre", "Nombre", "texto", ""],
		["toma", "Toma", "opciones", tomas, maxi(0, tomas.find(actual))],
		["inicio", "Desde (s)", "numero", snappedf(_t, 0.01)],
		["fin", "Hasta (s)", "numero", snappedf(minf(_dur, _t + 3.0), 0.01)],
		["transicion", "Entrada", "opciones", ["corte", "suave desde la cámara anterior"], 0],
		["notas", "Notas para el estudio", "parrafo", "Encuadre elegido por el director"]],
		func(v: Dictionary):
			var toma: String = v["toma"] if v["toma"] != "(toma nueva)" else ""
			var cam := _capturar(v["nombre"], toma, float(v["inicio"]), float(v["fin"]), v["notas"],
				"suave" if str(v["transicion"]).begins_with("suave") else "corte")
			_estado["camaras"].append(cam)
			_guardar_estado()
			_llenar_camaras()
			api.enviar_direccion({"tipo": "camara", "produccion": _pid, "escena": _eid, "version": _version,
				"huella": _huella, "camara": cam, "texto": "Me gusta esta toma: usá esta cámara (%s) entre %s y %s s%s." % [
				cam["name"], _s(cam["time_start"]), _s(cam["time_end"]), (" en la toma " + toma) if toma != "" else ""]},
				func(_ok, texto): app.mostrar_aviso("Cámara %s guardada. %s" % [cam["camera_id"], texto], 5.0)))

func _guardar_posicion() -> void:
	if _escena == null:
		return
	var cam := _capturar("", str(_toma_en(_t).get("id", "")), _t, minf(_dur, _t + 3.0), "Posición guardada")
	_estado["camaras"].append(cam)
	_guardar_estado()
	_llenar_camaras()
	app.mostrar_aviso("Posición %s guardada en el teléfono (se envía con GUARDAR CORRECCIONES)." % cam["camera_id"], 3.5)

func _volver_a_camara() -> void:
	if _estado["camaras"].is_empty():
		_modo_montaje()
		return
	_ver_camara(_estado["camaras"].back())

func _ver_camara(c: Dictionary) -> void:
	_modo = "libre"
	CamaraDirector.aplicar(_cam_libre, c)
	var e := _cam_libre.global_basis.get_euler()
	_yaw = e.y
	_pitch = e.x
	_activar(_cam_libre)
	if c.has("time_start") and (_t < float(c["time_start"]) or _t > float(c["time_end"])):
		_ir_a(float(c["time_start"]))
	_modo_lbl.text = "CÁMARA · " + str(c.get("name", ""))

func _llenar_camaras() -> void:
	limpiar(_lista_cam)
	if _estado["camaras"].is_empty():
		_lista_cam.add_child(Tema.etiqueta("Todavía no hay. Recorré la escena y tocá COLOCAR CÁMARA.", 14, Tema.TEXTO2, true))
	for i in _estado["camaras"].size():
		var c: Dictionary = _estado["camaras"][i]
		var p := Tema.panel(6, Tema.PANEL2, 8)
		var v := VBoxContainer.new()
		p.add_child(v)
		v.add_child(Tema.etiqueta("%s · %s" % [c.get("camera_id", ""), c.get("name", "")], 15, Tema.TEXTO))
		v.add_child(Tema.etiqueta("%s · %s–%s s · %.1f mm%s" % [c.get("shot", "") if str(c.get("shot", "")) != "" else "sin toma",
			_s(c.get("time_start", 0)), _s(c.get("time_end", 0)), float(c.get("lens_mm", 0)),
			"  ⇄" if _ab.has(i) else ""], 13, Tema.TEXTO2))
		var h := HBoxContainer.new()
		for par in [["VER", func(): _ver_camara(c)], ["✎", func(): _editar_camara(i)], ["⧉", func(): _duplicar_camara(i)],
				["A/B", func(): _marcar_ab(i)], ["🗑", func(): _borrar_camara(i)]]:
			var b := Tema.boton(par[0], par[1], "", 14)
			b.custom_minimum_size = Vector2(44, 40)
			h.add_child(b)
		v.add_child(h)
		_lista_cam.add_child(p)

func _editar_camara(i: int) -> void:
	var c: Dictionary = _estado["camaras"][i]
	var tomas: Array = [""]
	for tm in _d.get("tomas", []):
		tomas.append(str(tm["id"]))
	_formulario("EDITAR " + str(c["camera_id"]), [
		["nombre", "Nombre", "texto", str(c.get("name", ""))],
		["toma", "Toma", "opciones", tomas, maxi(0, tomas.find(str(c.get("shot", ""))))],
		["inicio", "Desde (s)", "numero", float(c.get("time_start", 0))],
		["fin", "Hasta (s)", "numero", float(c.get("time_end", 0))],
		["transicion", "Entrada", "opciones", ["corte", "suave"], 1 if str(c.get("transition", "")) == "suave" else 0],
		["notas", "Notas", "parrafo", str(c.get("notes", ""))]],
		func(v: Dictionary):
			c["name"] = v["nombre"]
			c["shot"] = v["toma"]
			c["time_start"] = float(v["inicio"])
			c["time_end"] = float(v["fin"])
			c["transition"] = v["transicion"]
			c["notes"] = v["notas"]
			_guardar_estado()
			_llenar_camaras())

func _duplicar_camara(i: int) -> void:
	var c: Dictionary = _estado["camaras"][i].duplicate(true)
	c["camera_id"] = _proximo_id()
	c["name"] = str(c.get("name", "")) + " (copia)"
	_estado["camaras"].append(c)
	_guardar_estado()
	_llenar_camaras()

func _borrar_camara(i: int) -> void:
	_estado["camaras"].remove_at(i)
	_ab.clear()
	_guardar_estado()
	_llenar_camaras()

func _marcar_ab(i: int) -> void:
	if _ab.has(i):
		_ab.erase(i)
	else:
		_ab.append(i)
		if _ab.size() > 2:
			_ab.pop_front()
	_llenar_camaras()

func _comparar() -> void:
	if _ab.size() < 2:
		app.mostrar_aviso("Marcá dos cámaras con A/B y tocá COMPARAR para alternar entre ellas.")
		return
	_ab_idx = (_ab_idx + 1) % 2
	var c: Dictionary = _estado["camaras"][_ab[_ab_idx]]
	_ver_camara(c)
	app.mostrar_aviso("%s: %s" % ["A" if _ab_idx == 0 else "B", c.get("name", "")], 1.5)

# ================================================================================================= dirección

func _contexto() -> Dictionary:
	var ctx := {"tiempo_s": snappedf(_t, 0.0001), "frame": _frame(), "toma": str(_toma_en(_t).get("id", "")),
		"vista": _modo_lbl.text}
	if _sel.get("tipo", "") == "personaje":
		var a: Dictionary = _actores.filter(func(x): return x["id"] == _sel["id"])[0]
		var c := clip_en(a, _t)
		ctx["personaje"] = a["id"]
		ctx["animacion"] = c
		ctx["posicion_blender"] = CamaraDirector._v(CamaraDirector.a_blender(_cadera(a)), 3)
	elif not _sel.is_empty():
		ctx["objeto"] = _sel["id"]
	ctx["camara_actual"] = CamaraDirector.capturar(_cam_activa, {})
	return ctx

func _enviar_nota() -> void:
	var texto := _chat.text.strip_edges()
	if texto == "":
		app.mostrar_aviso("Escribí qué querés cambiar.")
		return
	var nota := {"texto": texto, "contexto": _contexto(), "fecha": Time.get_datetime_string_from_system(true) + "Z"}
	_estado["notas"].append(nota)
	_guardar_estado()
	api.enviar_direccion({"tipo": "nota", "produccion": _pid, "escena": _eid, "version": _version, "huella": _huella,
		"titulo": texto.left(50), "texto": texto, "nota": nota}, func(ok, t):
			app.mostrar_aviso(t, 4.0)
			if ok:
				_chat.text = "")

func _marcar() -> void:
	_jugando = false
	_play.text = "▶"
	_formulario("MARCADOR en %s s (cuadro %d)" % [_s(_t), _frame()], [["nota", "¿Qué pasa en este momento?", "parrafo", ""]],
		func(v: Dictionary):
			var m := {"id": "m%03d" % (_estado["marcadores"].size() + 1), "tiempo_s": snappedf(_t, 0.0001), "frame": _frame(),
				"nota": v["nota"], "contexto": _contexto()}
			_estado["marcadores"].append(m)
			_guardar_estado()
			_llenar_marcadores()
			_marcas.queue_redraw())

func _llenar_marcadores() -> void:
	limpiar(_lista_marc)
	for i in _estado["marcadores"].size():
		var m: Dictionary = _estado["marcadores"][i]
		var h := HBoxContainer.new()
		var b := Tema.boton("%s s · %s" % [_s(m["tiempo_s"]), str(m.get("nota", ""))], func(): _cuadro_a(float(m["tiempo_s"])), "", 14)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.clip_text = true
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size.y = 40
		h.add_child(b)
		h.add_child(Tema.boton("🗑", func():
			_estado["marcadores"].remove_at(i)
			_guardar_estado()
			_llenar_marcadores()
			_marcas.queue_redraw(), "", 14))
		_lista_marc.add_child(h)

func _cuadro_a(t: float) -> void:
	_jugando = false
	_play.text = "▶"
	_ir_a(t)

func _guardar_correcciones() -> void:
	api.enviar_direccion({"tipo": "guardar", "produccion": _pid, "escena": _eid, "version": _version, "huella": _huella,
		"titulo": "%d cámaras · %d marcadores · %d notas" % [_estado["camaras"].size(), _estado["marcadores"].size(), _estado["notas"].size()],
		"texto": "GUARDAR CORRECCIONES de %s v%d." % [_eid, _version],
		"camaras": _estado["camaras"], "marcadores": _estado["marcadores"], "notas": _estado["notas"]},
		func(_ok, t): app.mostrar_aviso(t, 5.0))

func _aprobar() -> void:
	if not _cargado:
		app.mostrar_aviso(_aviso_carga if _aviso_carga != "" else "La escena todavía no cargó: no se puede aprobar sin revisarla.", 6.0)
		return
	_formulario("APROBAR %s v%d PARA PRODUCCIÓN" % [_eid, _version], [["nota", "La aprobación queda atada a ESTA versión (huella %s). Comentario:" % _huella, "parrafo", "La escena está bien."]],
		func(v: Dictionary):
			api.enviar_revision({"produccion": _pid, "escena": _eid, "version": _version, "decision": "APROBAR",
				"nota": v["nota"], "huella": _huella}, func(_ok, t): app.mostrar_aviso(t, 5.0)))

## AUTORIZAR RENDER FINAL: sólo con esta versión cargada y APROBADA (misma huella). Queda registrada con la versión,
## la huella, la configuración de render, la fecha y la cuenta; los flujos de render la exigen y la verifican.
func _autorizar() -> void:
	var vc := api.version_catalogo(_pid, _eid, _version)
	if not _cargado or str(vc.get("estado_revision", "")) != "APROBADA POR EL USUARIO":
		app.mostrar_aviso("Se autoriza sólo una versión revisada y APROBADA (estado actual: %s)." % str(vc.get("estado_revision", "?")), 6.0)
		return
	var cfg := api.config_render(_pid)
	_formulario("AUTORIZAR RENDER FINAL · %s v%d" % [_eid, _version], [["nota",
		"Versión %d · huella %s · %s · %d fps · %d muestras · %s %s. Si la escena cambia después, esta autorización deja de valer. Comentario:" % [
			_version, _huella, cfg["resolucion"], cfg["fps"], cfg["muestras"], cfg["motor"], cfg["dispositivo"]],
		"parrafo", "Autorizo el render final de esta versión."]],
		func(v: Dictionary):
			api.enviar_autorizacion({"produccion": _pid, "escena": _eid, "version": _version, "huella": _huella,
				"config": cfg, "nota": v["nota"]}, func(_ok, t): app.mostrar_aviso(t, 6.0)))

func _versiones() -> Control:
	var v := VBoxContainer.new()
	var p := api.produccion(_pid)
	for e in p.get("escenas", []):
		if str(e.get("id", "")) != _eid:
			continue
		for ver in e.get("versiones", []):
			var arch: Dictionary = ver.get("archivos", {})
			var texto := "v%d · %s%s" % [int(ver["version"]), str(ver.get("estado_revision", ver.get("estado", ""))), "" if arch.has("previa") else " · sin previa"]
			var b := Tema.boton(texto, func():
				if int(ver["version"]) != _version and arch.has("previa"):
					app.atras()
					app.ir("editor", {"produccion": _pid, "escena": _eid, "version": int(ver["version"]), "archivos": arch}), "", 14)
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.custom_minimum_size.y = 40
			if int(ver["version"]) == _version:
				b.text = "▶ " + texto
			v.add_child(b)
	return v

func _cargar_historial() -> void:
	limpiar(_historial)
	_historial.add_child(Tema.etiqueta("Consultando…", 14, Tema.TEXTO2))
	api.historial_direccion(_pid, func(lista: Array):
		if not is_instance_valid(self):
			return
		limpiar(_historial)
		if lista.is_empty():
			_historial.add_child(Tema.etiqueta("Sin pedidos todavía (o sin conexión).", 14, Tema.TEXTO2))
		for it in lista:
			var b := Tema.boton("#%d %s %s%s" % [it["numero"], "●" if it["estado"] == "open" else "✔",
				str(it["titulo"]).replace("[DIRECCIÓN] " + _pid + " · ", "").replace("[REVISIÓN] " + _pid + " · ", ""),
				"  💬%d" % it["comentarios"] if it["comentarios"] > 0 else ""], func(): _ver_respuestas(it), "", 13)
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.clip_text = true
			b.custom_minimum_size.y = 38
			_historial.add_child(b))

func _ver_respuestas(it: Dictionary) -> void:
	api.comentarios(int(it["numero"]), func(lista: Array):
		var txt := str(it.get("cuerpo", "")) + "\n"
		for c in lista:
			txt += "\n— %s (%s):\n%s\n" % [c["autor"], Tema.fecha(c["fecha"]), str(c["texto"]).left(600)]
		_formulario("#%d" % int(it["numero"]), [["info", txt if txt.strip_edges() != "" else "Sin respuestas todavía.", "info", ""]], Callable()))

# ================================================================================================= formulario simple

## campos: [clave, etiqueta, tipo(texto|parrafo|numero|opciones|info), valor, (índice para opciones)]
func _formulario(titulo: String, campos: Array, al_aceptar: Callable) -> void:
	if _dialogo:
		_dialogo.queue_free()
	var fondo := ColorRect.new()
	fondo.color = Color(0, 0, 0, 0.6)
	fondo.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(fondo)
	_dialogo = fondo
	var p := Tema.panel(18, Tema.PANEL, 12)
	p.set_anchors_preset(Control.PRESET_CENTER)
	var ancho := 660.0 if vertical else 620.0
	p.custom_minimum_size = Vector2(ancho, 0)
	p.position = Vector2(-ancho / 2, -260)
	fondo.add_child(p)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(ancho - 20, 440)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	p.add_child(sc)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 8)
	sc.add_child(v)
	v.add_child(Tema.etiqueta(titulo, 18, Tema.ACENTO, true))
	var ctrls := {}
	for c in campos:
		if c[2] != "info":
			v.add_child(Tema.etiqueta(c[1], 15, Tema.TEXTO2))
		match c[2]:
			"texto":
				var le := LineEdit.new()
				le.text = str(c[3])
				ctrls[c[0]] = le
				v.add_child(le)
			"parrafo":
				var te := TextEdit.new()
				te.text = str(c[3])
				te.custom_minimum_size.y = 90
				te.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
				ctrls[c[0]] = te
				v.add_child(te)
			"numero":
				var sb := SpinBox.new()
				sb.min_value = 0
				sb.max_value = _dur
				sb.step = 0.01
				sb.value = float(c[3])
				ctrls[c[0]] = sb
				v.add_child(sb)
			"opciones":
				var ob := OptionButton.new()
				for o in c[3]:
					ob.add_item(str(o) if str(o) != "" else "(sin toma)")
				ob.selected = int(c[4]) if c.size() > 4 else 0
				ob.set_meta("valores", c[3])
				ctrls[c[0]] = ob
				v.add_child(ob)
			"info":
				v.add_child(Tema.etiqueta(c[1], 14, Tema.TEXTO, true))
	var h := HBoxContainer.new()
	h.add_child(Tema.boton("CANCELAR" if al_aceptar.is_valid() else "CERRAR", func(): fondo.queue_free(), "", 16))
	if al_aceptar.is_valid():
		h.add_child(Tema.boton("ACEPTAR", func():
			var r := {}
			for k in ctrls:
				var n = ctrls[k]
				if n is LineEdit or n is TextEdit:
					r[k] = n.text
				elif n is SpinBox:
					r[k] = n.value
				elif n is OptionButton:
					r[k] = str(n.get_meta("valores")[n.selected])
			fondo.queue_free()
			al_aceptar.call(r), "acento", 16))
	v.add_child(h)

# ================================================================================================= dibujos

class _Guia extends Control:
	var editor
	func _draw() -> void:
		var s := size
		var c := Color(1, 1, 1, 0.18)
		for i in [1, 2]:
			draw_line(Vector2(s.x * i / 3.0, 0), Vector2(s.x * i / 3.0, s.y), c, 1.0)
			draw_line(Vector2(0, s.y * i / 3.0), Vector2(s.x, s.y * i / 3.0), c, 1.0)
		if editor and editor._joy_id >= 0:
			draw_arc(editor._joy_origen, 80, 0, TAU, 40, Color(1, 1, 1, 0.35), 2.0)
			draw_circle(editor._joy_origen + editor._joy_vec * 80, 22, Color(0.91, 0.69, 0.29, 0.6))
	func _process(_d: float) -> void:
		queue_redraw()

class _Marcas extends Control:
	var editor
	func _draw() -> void:
		if editor == null or editor._dur <= 0:
			return
		var w := size.x
		for tm in editor._d.get("tomas", []):
			var x: float = float(tm["inicio_s"]) / editor._dur * w
			draw_line(Vector2(x, 2), Vector2(x, 12), Color(1, 1, 1, 0.35), 1.0)
		for m in editor._estado["marcadores"]:
			var x: float = float(m["tiempo_s"]) / editor._dur * w
			draw_line(Vector2(x, 0), Vector2(x, size.y), Color(0.91, 0.69, 0.29, 0.9), 2.0)
