extends Control
## Interfaz principal: barra superior (INICIO · PELÍCULAS · ESCENARIOS · AJUSTES) y pila de páginas.
## El botón ATRÁS de Android vuelve a la página anterior.

const PAGINAS := {
	"inicio": preload("res://main/paginas/inicio.gd"),
	"peliculas": preload("res://main/paginas/peliculas.gd"),
	"pelicula": preload("res://main/paginas/pelicula.gd"),
	"escena": preload("res://main/paginas/escena.gd"),
	"visor": preload("res://main/paginas/visor.gd"),
	"editor": preload("res://main/paginas/editor.gd"),
	"escenarios": preload("res://main/paginas/escenarios.gd"),
	"ajustes": preload("res://main/paginas/ajustes.gd"),
}

var api: EstudioApi
var _contenido: Control
var _pila: Array = []           # [{"nombre", "datos", "nodo"}]
var _nav: Dictionary = {}
var _barra: Control
var _aviso: Label
var _aviso_t := 0.0
var _logo: Label
var vertical := false
var orientacion := "horizontal"     # horizontal | vertical | automatica (AJUSTES)
const ARCH_AJUSTES := "user://ajustes.json"

func _ready() -> void:
	theme = Tema.tema_global()
	var fondo := ColorRect.new()
	fondo.color = Tema.FONDO
	fondo.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(fondo)
	api = EstudioApi.new()
	add_child(api)
	api.aviso.connect(mostrar_aviso)
	api.catalogo_listo.connect(_on_catalogo)

	var raiz := VBoxContainer.new()
	raiz.set_anchors_preset(Control.PRESET_FULL_RECT)
	raiz.add_theme_constant_override("separation", 0)
	add_child(raiz)
	_barra = _construir_barra()
	raiz.add_child(_barra)
	_contenido = Control.new()
	_contenido.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_contenido.clip_contents = true
	raiz.add_child(_contenido)

	_aviso = Tema.etiqueta("", 18, Tema.TEXTO, true)
	_aviso.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.1, 0.1, 0.13, 0.95)
	sb.border_color = Tema.ACENTO
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 18
	sb.content_margin_right = 18
	sb.content_margin_top = 10
	sb.content_margin_bottom = 10
	_aviso.add_theme_stylebox_override("normal", sb)
	_aviso.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_ubicar_aviso(700.0)
	_aviso.visible = false
	add_child(_aviso)

	var aj = JSON.parse_string(FileAccess.get_file_as_string(ARCH_AJUSTES)) if FileAccess.file_exists(ARCH_AJUSTES) else null
	if aj is Dictionary:
		orientacion = str(aj.get("orientacion", "horizontal"))
	get_window().size_changed.connect(_revisar_orientacion)
	aplicar_orientacion(orientacion, false)
	_revisar_orientacion(true)
	ir("inicio", {}, true)
	api.cargar_catalogo()

## Orientación elegida en AJUSTES: el teléfono gira y la interfaz se reacomoda (720×1280 en vertical).
func aplicar_orientacion(modo: String, guardar := true) -> void:
	orientacion = modo
	var o: int = {"vertical": DisplayServer.SCREEN_SENSOR_PORTRAIT, "automatica": DisplayServer.SCREEN_SENSOR}.get(modo, DisplayServer.SCREEN_SENSOR_LANDSCAPE)
	DisplayServer.screen_set_orientation(o)
	if guardar:
		var f := FileAccess.open(ARCH_AJUSTES, FileAccess.WRITE)
		if f:
			f.store_string(JSON.stringify({"orientacion": modo}))
	_revisar_orientacion.call_deferred()

## El aviso queda centrado abajo (con márgenes relativos al ancla, no con una posición absoluta).
func _ubicar_aviso(ancho: float) -> void:
	_aviso.custom_minimum_size = Vector2(ancho, 0)
	_aviso.offset_left = -ancho / 2
	_aviso.offset_right = ancho / 2
	_aviso.offset_top = -110
	_aviso.offset_bottom = -40
	_aviso.grow_vertical = Control.GROW_DIRECTION_BEGIN

func _revisar_orientacion(forzar := false) -> void:
	var s := DisplayServer.window_get_size()
	var v := s.y > s.x
	if v == vertical and not forzar:
		return
	vertical = v
	get_window().content_scale_size = Vector2i(720, 1280) if v else Vector2i(1280, 720)
	_logo.text = "  3D FS" if v else "  3D FILM STUDIO"
	_logo.custom_minimum_size.x = 90 if v else 250
	for k in _nav:
		_nav[k].custom_minimum_size.x = 0 if v else 150
		_nav[k].add_theme_font_size_override("font_size", 15 if v else 18)
		_nav[k].size_flags_horizontal = Control.SIZE_EXPAND_FILL if v else Control.SIZE_FILL
	_ubicar_aviso(640.0 if v else 700.0)
	for e in _pila:
		if e["nodo"].has_method("al_orientar"):
			e["nodo"].call("al_orientar", v)

func _construir_barra() -> Control:
	var p := Tema.panel(10, Color("0f0f14"), 0)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	p.add_child(h)
	var logo := Tema.etiqueta("  3D FILM STUDIO", 24, Tema.ACENTO)
	logo.custom_minimum_size.x = 250
	_logo = logo
	h.add_child(logo)
	for par in [["inicio", "INICIO"], ["peliculas", "PELÍCULAS"], ["escenarios", "ESCENARIOS"], ["ajustes", "AJUSTES"]]:
		var b := Tema.boton(par[1], ir.bind(par[0], {}, true), "", 18)
		b.custom_minimum_size = Vector2(150, 48)
		b.toggle_mode = true
		h.add_child(b)
		_nav[par[0]] = b
	var esp := Control.new()
	esp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(esp)
	var r := Tema.boton("⟳", func(): api.cargar_catalogo(); mostrar_aviso("Consultando novedades…"), "", 22)
	r.custom_minimum_size = Vector2(56, 48)
	h.add_child(r)
	return p

## Abre una página. raiz=true limpia la pila (navegación por la barra superior).
func ir(nombre: String, datos := {}, raiz := false) -> void:
	if raiz:
		for e in _pila:
			e["nodo"].queue_free()
		_pila.clear()
	elif not _pila.is_empty():
		_pila.back()["nodo"].visible = false
	var n: Control = PAGINAS[nombre].new()
	n.set_anchors_preset(Control.PRESET_FULL_RECT)
	n.set("app", self)
	n.set("vertical", vertical)
	_contenido.add_child(n)
	_pila.append({"nombre": nombre, "datos": datos, "nodo": n})
	n.call("abrir", datos)
	for k in _nav:
		_nav[k].button_pressed = (k == _pila[0]["nombre"])
	_barra.visible = not (nombre in ["visor", "editor"])

func atras() -> bool:
	if _pila.size() <= 1:
		return false
	var e = _pila.pop_back()
	e["nodo"].queue_free()
	var arriba: Control = _pila.back()["nodo"]
	arriba.visible = true
	if arriba.has_method("al_volver"):
		arriba.call("al_volver")
	_barra.visible = not (_pila.back()["nombre"] in ["visor", "editor"])
	return true

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		if not atras():
			get_tree().quit()

func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and ev.keycode == KEY_ESCAPE:
		atras()

func _on_catalogo(_c: Dictionary, desde_red: bool) -> void:
	for e in _pila:
		if e["nodo"].has_method("al_actualizar_catalogo"):
			e["nodo"].call("al_actualizar_catalogo")
	if desde_red:
		mostrar_aviso("Catálogo al día.", 1.5)

func mostrar_aviso(t: String, segundos := 3.5) -> void:
	_aviso.text = t
	_aviso.visible = true
	_aviso_t = segundos

func _process(d: float) -> void:
	if _aviso_t > 0:
		_aviso_t -= d
		if _aviso_t <= 0:
			_aviso.visible = false

func pantalla_completa(activa: bool) -> void:
	_barra.visible = not activa
