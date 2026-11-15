extends Pagina
## Ficha de una producción: portada, datos, escenas ordenadas y exportación de la película completa.

var _id := ""
var _col: VBoxContainer

func abrir(d: Dictionary) -> void:
	_id = str(d.get("id", ""))
	_col = columna_desplazable()
	al_actualizar_catalogo()

func al_volver() -> void:
	al_actualizar_catalogo()

func al_actualizar_catalogo() -> void:
	limpiar(_col)
	var p := api.produccion(_id)
	if p.is_empty():
		_col.add_child(Tema.etiqueta("La producción ya no está en el catálogo.", 20, Tema.TEXTO2))
		return
	var cab := BoxContainer.new()
	cab.vertical = vertical
	cab.add_theme_constant_override("separation", 24)
	var marco := Tema.panel(0, Tema.PANEL2, 14)
	marco.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	marco.add_child(Tema.imagen(api, p.get("portada"), Vector2(480, 270)))
	cab.add_child(marco)
	var info := VBoxContainer.new()
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.add_child(Tema.etiqueta(str(p.get("titulo", "")), 34))
	var fila := HBoxContainer.new()
	fila.add_child(Tema.chip(str(p.get("estado", ""))))
	fila.add_child(Tema.etiqueta("  %s" % p.get("genero", ""), 18, Tema.TEXTO2))
	info.add_child(fila)
	info.add_child(Tema.etiqueta(str(p.get("sinopsis", "")), 18, Tema.TEXTO, true))
	var escenas: Array = p.get("escenas", [])
	var n_vers := 0
	for e in escenas:
		n_vers += e.get("versiones", []).size()
	info.add_child(Tema.etiqueta("Duración: %s   ·   Escenas: %d   ·   Versiones: %d   ·   Creada: %s" % [
		Tema.duracion(float(p.get("duracion_s", 0))), escenas.size(), n_vers, str(p.get("creada", ""))], 17, Tema.TEXTO2, true))
	var acc := HFlowContainer.new()
	var final_ = p.get("final")
	if final_ is Dictionary and not final_.is_empty():
		acc.add_child(Tema.boton("▶  VER PELÍCULA COMPLETA", func(): app.ir("escena", {"produccion": _id, "pelicula": true}), "acento"))
		acc.add_child(Tema.boton("⬇  DESCARGAR MP4", func(): OS.shell_open(str(final_["url"])), ""))
	acc.add_child(Tema.boton("🎬  EXPORTAR PELÍCULA", _dialogo_exportar.bind(p), ""))
	info.add_child(acc)
	cab.add_child(info)
	_col.add_child(cab)
	_col.add_child(Tema.separador(6))
	_col.add_child(Tema.etiqueta("ESCENAS", 18, Tema.ACENTO))
	for e in escenas:
		_col.add_child(_fila_escena(p, e))

func _fila_escena(p: Dictionary, e: Dictionary) -> Control:
	var v: Dictionary = e["versiones"].back()
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size.y = 128
	b.pressed.connect(func(): app.ir("escena", {"produccion": p["id"], "escena": e["id"]}))
	var h := HBoxContainer.new()
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 10
	h.offset_top = 8
	h.offset_bottom = -8
	h.add_theme_constant_override("separation", 18)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var img := Tema.imagen(api, v.get("archivos", {}).get("miniatura"), Vector2(200, 112))
	img.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(img)
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var nuevo := api.es_nuevo(api.clave_version(p["id"], e["id"], int(v.get("version", 1))))
	col.add_child(Tema.etiqueta("Escena %02d — %s%s" % [int(e.get("numero", 0)), e.get("titulo", ""), "   ● NUEVA" if nuevo else ""], 22))
	var f2 := HBoxContainer.new()
	f2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	f2.add_child(Tema.chip(str(v.get("estado", ""))))
	f2.add_child(Tema.etiqueta("  versión %d de %d  ·  %s  ·  %s" % [int(v.get("version", 1)), e["versiones"].size(),
		Tema.duracion(float(v.get("duracion_s", 0))), str(v.get("resolucion", ""))], 16, Tema.TEXTO2))
	col.add_child(f2)
	col.add_child(Tema.etiqueta("%d tomas" % v.get("tomas", []).size(), 15, Tema.TEXTO2))
	h.add_child(col)
	for c in col.get_children():
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(h)
	return b

func _dialogo_exportar(p: Dictionary) -> void:
	var d := AcceptDialog.new()
	d.title = "Exportar película completa"
	d.ok_button_text = "PEDIR AL ESTUDIO"
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(620, 0)
	v.add_child(Tema.etiqueta("El montaje final se arma en el servidor con las escenas APROBADAS y queda para descargar y compartir.", 18, Tema.TEXTO, true))
	var res := OptionButton.new()
	for r in ["1080p", "720p", "4K (si el servidor lo permite)"]:
		res.add_item(r)
	var fps := OptionButton.new()
	for f in ["30 FPS", "24 FPS", "60 FPS"]:
		fps.add_item(f)
	var fmt := OptionButton.new()
	fmt.add_item("MP4 H.264")
	for par in [["Resolución", res], ["Cuadros por segundo", fps], ["Formato", fmt]]:
		var h := HBoxContainer.new()
		var l := Tema.etiqueta(par[0], 18, Tema.TEXTO2)
		l.custom_minimum_size.x = 220
		h.add_child(l)
		par[1].size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(par[1])
		v.add_child(h)
	d.add_child(v)
	d.confirmed.connect(func():
		api.enviar_revision({"produccion": p["id"], "escena": "", "version": 0, "decision": "EXPORTAR",
			"resolucion": ["1080p", "720p", "4k"][res.selected], "fps": [30, 24, 60][fps.selected], "formato": "mp4"},
			func(ok, t): app.mostrar_aviso(t))
		d.queue_free())
	d.canceled.connect(d.queue_free)
	add_child(d)
	d.popup_centered()
