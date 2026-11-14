extends Pagina
## Escena: reproductor de video (OGV/Theora) + control de producción (aprobar, rechazar, correcciones,
## volver a renderizar, versiones anteriores) + exportación del MP4.

var _pid := ""
var _eid := ""
var _es_pelicula := false
var _version_idx := -1
var _player: VideoStreamPlayer
var _cartel: Label
var _slider: HSlider
var _tiempo: Label
var _play: Button
var _arrastrando := false
var _lado: Control
var _controles: Control
var _info: VBoxContainer
var _nota: TextEdit
var _url_cargando := ""
var _pantalla_completa := false

func abrir(d: Dictionary) -> void:
	_pid = str(d.get("produccion", ""))
	_eid = str(d.get("escena", ""))
	_es_pelicula = bool(d.get("pelicula", false))
	var h := HBoxContainer.new()
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 16
	h.offset_right = -16
	h.offset_top = 12
	h.offset_bottom = -12
	h.add_theme_constant_override("separation", 16)
	add_child(h)
	# --- reproductor
	var izq := VBoxContainer.new()
	izq.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(izq)
	var marco := Tema.panel(0, Color.BLACK, 12)
	marco.size_flags_vertical = Control.SIZE_EXPAND_FILL
	marco.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	izq.add_child(marco)
	var asp := AspectRatioContainer.new()
	asp.ratio = 16.0 / 9.0
	marco.add_child(asp)
	_player = VideoStreamPlayer.new()
	_player.expand = true
	_player.finished.connect(func(): _play.text = "▶")
	asp.add_child(_player)
	_cartel = Tema.etiqueta("", 20, Tema.TEXTO2, true)
	_cartel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_cartel.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	marco.add_child(_cartel)
	var ctrl := HBoxContainer.new()
	_controles = ctrl
	izq.add_child(ctrl)
	ctrl.add_child(Tema.boton("⏪ 10", func(): _saltar(-10.0)))
	_play = Tema.boton("▶", _alternar, "acento", 24)
	_play.custom_minimum_size.x = 80
	ctrl.add_child(_play)
	ctrl.add_child(Tema.boton("10 ⏩", func(): _saltar(10.0)))
	_slider = HSlider.new()
	_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_slider.step = 0.01
	_slider.drag_started.connect(func(): _arrastrando = true)
	_slider.drag_ended.connect(func(_c): _arrastrando = false; _player.stream_position = _slider.value)
	ctrl.add_child(_slider)
	_tiempo = Tema.etiqueta("0:00 / 0:00", 17, Tema.TEXTO2)
	ctrl.add_child(_tiempo)
	ctrl.add_child(Tema.boton("⛶", _alternar_completa))
	# --- panel lateral
	var sc := ScrollContainer.new()
	sc.custom_minimum_size.x = 430
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_lado = sc
	h.add_child(sc)
	_info = VBoxContainer.new()
	_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(_info)
	al_actualizar_catalogo()

func _escena() -> Dictionary:
	for e in api.produccion(_pid).get("escenas", []):
		if e.get("id") == _eid:
			return e
	return {}

func al_actualizar_catalogo() -> void:
	limpiar(_info)
	var p := api.produccion(_pid)
	if _es_pelicula:
		_info.add_child(Tema.etiqueta(str(p.get("titulo", "")), 26))
		_info.add_child(Tema.etiqueta("Película completa (montaje final)", 18, Tema.TEXTO2))
		var f: Dictionary = p.get("final", {})
		_info.add_child(Tema.boton("⬇  DESCARGAR / COMPARTIR MP4", func(): OS.shell_open(str(f.get("url", ""))), "acento"))
		_cargar_video(p.get("final_ogv", {}))
		return
	var e := _escena()
	if e.is_empty():
		_info.add_child(Tema.etiqueta("La escena ya no está en el catálogo.", 20, Tema.TEXTO2))
		return
	var vers: Array = e["versiones"]
	if _version_idx < 0 or _version_idx >= vers.size():
		_version_idx = vers.size() - 1
	var v: Dictionary = vers[_version_idx]
	api.marcar_visto(api.clave_version(_pid, _eid, int(v["version"])))
	_info.add_child(Tema.etiqueta("Escena %02d — %s" % [int(e.get("numero", 0)), e.get("titulo", "")], 26, Tema.TEXTO, true))
	_info.add_child(Tema.etiqueta(str(p.get("titulo", "")), 16, Tema.TEXTO2))
	var fila := HBoxContainer.new()
	fila.add_child(Tema.chip(str(v.get("estado", ""))))
	var sel := OptionButton.new()
	sel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for i in vers.size():
		var vi: Dictionary = vers[i]
		sel.add_item("Versión %d — %s%s" % [int(vi["version"]), Tema.ESTADOS.get(vi.get("estado", ""), ["?"])[0],
			"  (actual)" if i == vers.size() - 1 else ""], i)
	sel.selected = _version_idx
	sel.item_selected.connect(func(i): _version_idx = i; al_actualizar_catalogo())
	fila.add_child(sel)
	_info.add_child(fila)
	_info.add_child(Tema.etiqueta("Duración %s · %s · %s FPS · %s\nRender: %s · %s" % [
		Tema.duracion(float(v.get("duracion_s", 0))), str(v.get("resolucion", "—")), str(v.get("fps", 30)),
		str(v.get("calidad", "")), Tema.fecha(str(v.get("fecha", ""))),
		("%d min de CPU" % int(float(v.get("segundos_render", 0)) / 60.0)) if v.get("segundos_render") else "—"], 16, Tema.TEXTO2, true))
	var arch: Dictionary = v.get("archivos", {})
	_cargar_video(arch.get("ogv", {}))
	# visor 3D
	if arch.has("visor"):
		_info.add_child(Tema.boton("🧊  VER EN 3D (escenario, cámaras, animación)", func():
			app.ir("visor", {"archivo": arch["visor"], "titulo": e.get("titulo", "")}), "azul"))
	# control de producción
	_info.add_child(Tema.separador(4))
	_info.add_child(Tema.etiqueta("CONTROL DE PRODUCCIÓN", 17, Tema.ACENTO))
	_nota = TextEdit.new()
	_nota.placeholder_text = "Observaciones para Claude (ej.: «La cámara está demasiado lejos. Acercala al personaje, mantené la iluminación y repetí la escena»)"
	_nota.custom_minimum_size.y = 120
	_nota.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	_info.add_child(_nota)
	var g := VBoxContainer.new()
	var bloqueada := str(v.get("estado", "")) == "aprobada"
	for par in [["✔  APROBAR", "APROBAR", "verde"], ["✖  RECHAZAR", "RECHAZAR", "rojo"],
			["✎  SOLICITAR CORRECCIONES", "CORREGIR", "naranja"], ["⟳  VOLVER A RENDERIZAR", "RENDERIZAR", "azul"]]:
		var b := Tema.boton(par[0], _decidir.bind(par[1], v), par[2], 17)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.disabled = bloqueada and par[1] != "CORREGIR"
		g.add_child(b)
	_info.add_child(g)
	if _version_idx > 0:
		_info.add_child(Tema.boton("◀  VER VERSIÓN ANTERIOR", func(): _version_idx -= 1; al_actualizar_catalogo()))
	if not api.tiene_token():
		_info.add_child(Tema.etiqueta("Para enviar decisiones vinculá la cuenta en AJUSTES.", 15, Tema.NARANJA, true))
	var notas: Array = v.get("notas", [])
	if not notas.is_empty():
		_info.add_child(Tema.etiqueta("HISTORIAL DE ESTA VERSIÓN", 15, Tema.TEXTO2))
		for n in notas:
			_info.add_child(Tema.etiqueta("• %s — %s: %s" % [Tema.fecha(str(n.get("fecha", ""))), n.get("decision", ""), n.get("nota", "")], 15, Tema.TEXTO, true))
	# tomas
	_info.add_child(Tema.separador(4))
	_info.add_child(Tema.etiqueta("TOMAS", 17, Tema.ACENTO))
	for t in v.get("tomas", []):
		var b := Tema.boton("%s  ·  %s" % [Tema.duracion(float(t.get("inicio_s", 0))), t.get("plano", t.get("id", ""))],
			func(): _player.stream_position = float(t.get("inicio_s", 0)), "", 16)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size.y = 44
		_info.add_child(b)
	# guion
	if str(e.get("guion", "")) != "":
		_info.add_child(Tema.separador(4))
		_info.add_child(Tema.etiqueta("GUION", 17, Tema.ACENTO))
		_info.add_child(Tema.etiqueta(str(e["guion"]), 16, Tema.TEXTO, true))
	# exportación
	_info.add_child(Tema.separador(4))
	_info.add_child(Tema.etiqueta("EXPORTAR", 17, Tema.ACENTO))
	if arch.has("mp4"):
		var mp4: Dictionary = arch["mp4"]
		_info.add_child(Tema.boton("⬇  DESCARGAR / COMPARTIR MP4  (%s)" % Tema.bytes(int(mp4.get("bytes", 0))),
			func(): OS.shell_open(str(mp4["url"])), "acento"))
		_info.add_child(Tema.boton("🔗  COPIAR ENLACE", func():
			DisplayServer.clipboard_set(str(mp4["url"]))
			app.mostrar_aviso("Enlace copiado.")))
		_info.add_child(Tema.boton("💾  GUARDAR PARA VER SIN CONEXIÓN", func():
			api.obtener(arch.get("ogv", {}), func(r): app.mostrar_aviso("Guardado en el teléfono." if r != "" else "No se pudo guardar."))))

func _decidir(decision: String, v: Dictionary) -> void:
	var nota := _nota.text.strip_edges()
	if decision == "CORREGIR" and nota == "":
		app.mostrar_aviso("Escribí qué hay que corregir.")
		return
	api.enviar_revision({"produccion": _pid, "escena": _eid, "version": int(v.get("version", 1)),
		"decision": decision, "nota": nota, "huella": str(v.get("huella", ""))},
		func(ok, texto):
			app.mostrar_aviso(texto, 5.0)
			if ok:
				_nota.text = "")

func _cargar_video(archivo) -> void:
	_player.stop()
	_player.stream = null
	_play.text = "▶"
	if not (archivo is Dictionary) or archivo.is_empty():
		_cartel.text = "Esta versión todavía no tiene video de revisión."
		_cartel.visible = true
		return
	_url_cargando = str(archivo.get("url", ""))
	_cartel.text = "Descargando video…"
	_cartel.visible = true
	var url := _url_cargando
	api.obtener(archivo, func(ruta: String):
		if not is_instance_valid(self) or url != _url_cargando:
			return
		if ruta == "":
			_cartel.text = "No se pudo descargar el video."
			return
		var st := VideoStreamTheora.new()
		st.file = ruta
		_player.stream = st
		_cartel.visible = false
		_player.play()
		_play.text = "⏸")

func _alternar() -> void:
	if _player.stream == null:
		return
	if not _player.is_playing():
		_player.play()
		_player.paused = false
	else:
		_player.paused = not _player.paused
	_play.text = "▶" if (_player.paused or not _player.is_playing()) else "⏸"

func _saltar(s: float) -> void:
	if _player.stream == null:
		return
	var largo := _player.get_stream_length()
	_player.stream_position = clampf(_player.stream_position + s, 0.0, maxf(0.0, largo - 0.1))

func _alternar_completa() -> void:
	_pantalla_completa = not _pantalla_completa
	_lado.visible = not _pantalla_completa
	app.pantalla_completa(_pantalla_completa)

func _process(_d: float) -> void:
	if _cartel.visible and _url_cargando != "":
		var f := api.fraccion(_url_cargando)
		if f >= 0.0:
			_cartel.text = "Descargando video… %d %%" % int(f * 100)
	if _player.stream == null:
		return
	var largo := _player.get_stream_length()
	if largo > 0:
		_slider.max_value = largo
		if not _arrastrando:
			_slider.value = _player.stream_position
		_tiempo.text = "%s / %s" % [Tema.duracion(_player.stream_position), Tema.duracion(largo)]

func _exit_tree() -> void:
	if _pantalla_completa and app:
		app.pantalla_completa(false)
