class_name Tema
extends RefCounted
## Estética de estudio cinematográfico: oscura, sobria, acento ámbar. Ayudas para construir la interfaz por código.

const FONDO := Color("0a0a0e")
const PANEL := Color("15151c")
const PANEL2 := Color("1f1f29")
const BORDE := Color("2b2b38")
const ACENTO := Color("e8b04a")
const TEXTO := Color("ededf2")
const TEXTO2 := Color("9a9aa8")
const VERDE := Color("4cc38a")
const ROJO := Color("e5484d")
const AZUL := Color("5b9bf0")
const NARANJA := Color("f0a35b")

const ESTADOS := {
	"borrador": ["BORRADOR", TEXTO2],
	"renderizando": ["RENDERIZANDO", AZUL],
	"en_revision": ["PARA REVISAR", ACENTO],
	"aprobada": ["APROBADA", VERDE],
	"rechazada": ["RECHAZADA", ROJO],
	"correcciones": ["CORRECCIONES", NARANJA],
	"en_produccion": ["EN PRODUCCIÓN", AZUL],
	"reemplazada": ["VERSIÓN ANTERIOR", TEXTO2],
}

static func tema_global() -> Theme:
	var t := Theme.new()
	t.default_font_size = 20
	var sb := func(c: Color, radio := 10, borde := Color(0, 0, 0, 0), ancho := 0, margen := 14) -> StyleBoxFlat:
		var s := StyleBoxFlat.new()
		s.bg_color = c
		s.set_corner_radius_all(radio)
		s.border_color = borde
		s.set_border_width_all(ancho)
		s.content_margin_left = margen
		s.content_margin_right = margen
		s.content_margin_top = margen * 0.6
		s.content_margin_bottom = margen * 0.6
		return s
	t.set_stylebox("normal", "Button", sb.call(PANEL2, 10, BORDE, 1))
	t.set_stylebox("hover", "Button", sb.call(PANEL2.lightened(0.08), 10, ACENTO.darkened(0.3), 1))
	t.set_stylebox("pressed", "Button", sb.call(ACENTO.darkened(0.55), 10, ACENTO, 1))
	t.set_stylebox("focus", "Button", sb.call(Color(0, 0, 0, 0), 10, ACENTO.darkened(0.2), 1))
	t.set_stylebox("disabled", "Button", sb.call(PANEL, 10, BORDE, 1))
	t.set_color("font_color", "Button", TEXTO)
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", ACENTO.lightened(0.3))
	t.set_color("font_disabled_color", "Button", TEXTO2.darkened(0.3))
	t.set_color("font_color", "Label", TEXTO)
	t.set_stylebox("normal", "LineEdit", sb.call(PANEL, 8, BORDE, 1))
	t.set_stylebox("focus", "LineEdit", sb.call(PANEL, 8, ACENTO, 1))
	t.set_stylebox("normal", "TextEdit", sb.call(PANEL, 8, BORDE, 1))
	t.set_stylebox("focus", "TextEdit", sb.call(PANEL, 8, ACENTO, 1))
	t.set_color("font_color", "LineEdit", TEXTO)
	t.set_color("font_color", "TextEdit", TEXTO)
	t.set_color("font_placeholder_color", "TextEdit", TEXTO2)
	t.set_color("font_placeholder_color", "LineEdit", TEXTO2)
	t.set_stylebox("panel", "PanelContainer", sb.call(PANEL, 14, BORDE, 1, 16))
	var barra := StyleBoxFlat.new()
	barra.bg_color = BORDE
	barra.set_corner_radius_all(4)
	var lleno := StyleBoxFlat.new()
	lleno.bg_color = ACENTO
	lleno.set_corner_radius_all(4)
	t.set_stylebox("background", "ProgressBar", barra)
	t.set_stylebox("fill", "ProgressBar", lleno)
	var pista := StyleBoxFlat.new()
	pista.bg_color = BORDE
	pista.set_corner_radius_all(3)
	pista.content_margin_top = 3
	pista.content_margin_bottom = 3
	var pista_llena := pista.duplicate()
	pista_llena.bg_color = ACENTO
	t.set_stylebox("slider", "HSlider", pista)
	t.set_stylebox("grabber_area", "HSlider", pista_llena)
	t.set_stylebox("grabber_area_highlight", "HSlider", pista_llena)
	t.set_constant("separation", "VBoxContainer", 10)
	t.set_constant("separation", "HBoxContainer", 10)
	t.set_constant("h_separation", "GridContainer", 16)
	t.set_constant("v_separation", "GridContainer", 16)
	var scroll := StyleBoxFlat.new()
	scroll.bg_color = Color(1, 1, 1, 0.15)
	scroll.set_corner_radius_all(3)
	t.set_stylebox("grabber", "VScrollBar", scroll)
	t.set_stylebox("grabber_highlight", "VScrollBar", scroll)
	t.set_stylebox("scroll", "VScrollBar", StyleBoxEmpty.new())
	t.set_stylebox("grabber", "HScrollBar", scroll)
	t.set_stylebox("scroll", "HScrollBar", StyleBoxEmpty.new())
	return t

static func etiqueta(texto: String, tam := 20, color := TEXTO, envolver := false) -> Label:
	var l := Label.new()
	l.text = texto
	l.add_theme_font_size_override("font_size", tam)
	l.add_theme_color_override("font_color", color)
	if envolver:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l

static func boton(texto: String, al_tocar: Callable = Callable(), estilo := "", tam := 20) -> Button:
	var b := Button.new()
	b.text = texto
	b.add_theme_font_size_override("font_size", tam)
	b.custom_minimum_size.y = 52
	b.focus_mode = Control.FOCUS_NONE
	if estilo != "":
		var c: Color = {"acento": ACENTO, "verde": VERDE, "rojo": ROJO, "naranja": NARANJA, "azul": AZUL}.get(estilo, PANEL2)
		var s := StyleBoxFlat.new()
		s.bg_color = c.darkened(0.62)
		s.border_color = c
		s.set_border_width_all(1)
		s.set_corner_radius_all(10)
		s.content_margin_left = 16
		s.content_margin_right = 16
		b.add_theme_stylebox_override("normal", s)
		var s2 := s.duplicate()
		s2.bg_color = c.darkened(0.35)
		b.add_theme_stylebox_override("pressed", s2)
		b.add_theme_stylebox_override("hover", s2)
		b.add_theme_color_override("font_color", c.lightened(0.25))
	if al_tocar.is_valid():
		b.pressed.connect(al_tocar)
	return b

static func panel(margen := 16, color := PANEL, radio := 14) -> PanelContainer:
	var p := PanelContainer.new()
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.border_color = BORDE
	s.set_border_width_all(1)
	s.set_corner_radius_all(radio)
	s.content_margin_left = margen
	s.content_margin_right = margen
	s.content_margin_top = margen
	s.content_margin_bottom = margen
	p.add_theme_stylebox_override("panel", s)
	return p

static func chip(estado: String) -> PanelContainer:
	var e: Array = ESTADOS.get(estado, [estado.to_upper(), TEXTO2])
	var p := PanelContainer.new()
	var s := StyleBoxFlat.new()
	s.bg_color = (e[1] as Color).darkened(0.7)
	s.border_color = e[1]
	s.set_border_width_all(1)
	s.set_corner_radius_all(20)
	s.content_margin_left = 12
	s.content_margin_right = 12
	s.content_margin_top = 3
	s.content_margin_bottom = 3
	p.add_theme_stylebox_override("panel", s)
	p.add_child(etiqueta(e[0], 15, e[1]))
	p.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return p

static func separador(alto := 8) -> Control:
	var c := Control.new()
	c.custom_minimum_size.y = alto
	return c

static func duracion(seg: float) -> String:
	var s := int(round(seg))
	return "%d:%02d" % [s / 60, s % 60]

static func bytes(n: int) -> String:
	if n >= 1 << 30:
		return "%.1f GB" % (n / float(1 << 30))
	if n >= 1 << 20:
		return "%.1f MB" % (n / float(1 << 20))
	if n >= 1 << 10:
		return "%d KB" % (n / 1024)
	return "%d B" % n

static func fecha(iso: String) -> String:
	if iso.length() < 10:
		return iso
	var p := iso.substr(0, 10).split("-")
	var h := iso.substr(11, 5) if iso.length() >= 16 else ""
	return "%s/%s/%s %s" % [p[2], p[1], p[0], h]

## Imagen remota con caché: muestra un marco oscuro hasta que llega.
static func imagen(api: EstudioApi, archivo, tam: Vector2) -> TextureRect:
	var tr := TextureRect.new()
	tr.custom_minimum_size = tam
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	if archivo is Dictionary and not archivo.is_empty():
		api.obtener(archivo, func(ruta: String):
			if ruta == "" or not is_instance_valid(tr):
				return
			var img := Image.load_from_file(ruta)
			if img:
				tr.texture = ImageTexture.create_from_image(img))
	return tr
