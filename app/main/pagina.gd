class_name Pagina
extends Control
## Base de las páginas: acceso a la app y al API, contenedor con desplazamiento y márgenes.

var app  # main.gd
var api: EstudioApi:
	get:
		return app.api

func abrir(_datos: Dictionary) -> void:
	pass

## Crea un ScrollContainer con una columna con márgenes y la devuelve.
func columna_desplazable(margen := 24) -> VBoxContainer:
	var sc := ScrollContainer.new()
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(sc)
	var m := MarginContainer.new()
	m.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for lado in ["left", "right", "top", "bottom"]:
		m.add_theme_constant_override("margin_" + lado, margen)
	sc.add_child(m)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 14)
	m.add_child(v)
	return v

func limpiar(nodo: Node) -> void:
	for c in nodo.get_children():
		c.queue_free()

func titulo(texto: String, sub := "") -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.add_child(Tema.etiqueta(texto, 32, Tema.TEXTO))
	if sub != "":
		v.add_child(Tema.etiqueta(sub, 17, Tema.TEXTO2, true))
	return v

## Tarjeta de producción (portada grande + datos). Al tocarla abre la película.
func tarjeta_produccion(p: Dictionary, ancho := 360) -> Control:
	var b := Button.new()
	b.custom_minimum_size = Vector2(ancho, ancho * 0.5625 + 118)
	b.focus_mode = Control.FOCUS_NONE
	b.flat = true
	b.pressed.connect(func(): app.ir("pelicula", {"id": p.get("id")}))
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_theme_constant_override("separation", 6)
	b.add_child(v)
	var marco := Tema.panel(0, Tema.PANEL2, 12)
	marco.mouse_filter = Control.MOUSE_FILTER_IGNORE
	marco.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	var img := Tema.imagen(api, p.get("portada"), Vector2(ancho, ancho * 0.5625))
	img.mouse_filter = Control.MOUSE_FILTER_IGNORE
	marco.add_child(img)
	v.add_child(marco)
	var h := HBoxContainer.new()
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var t := Tema.etiqueta(str(p.get("titulo", "")), 20, Tema.TEXTO)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	t.clip_text = true
	t.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	h.add_child(t)
	h.add_child(Tema.chip(str(p.get("estado", ""))))
	v.add_child(h)
	var n_esc: int = p.get("escenas", []).size()
	v.add_child(Tema.etiqueta("%s · %d escena%s · %s" % [p.get("genero", ""), n_esc, "" if n_esc == 1 else "s",
		Tema.duracion(float(p.get("duracion_s", 0)))], 16, Tema.TEXTO2))
	for c in v.get_children():
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b
