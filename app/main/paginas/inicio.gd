extends Pagina
## INICIO: novedades, pendientes de revisión, renderizando, aprobadas, almacenamiento.

var _col: VBoxContainer

func abrir(_d: Dictionary) -> void:
	_col = columna_desplazable()
	al_actualizar_catalogo()

func al_actualizar_catalogo() -> void:
	limpiar(_col)
	var cat: Dictionary = api.catalogo
	_col.add_child(titulo("Inicio", "Última actualización del estudio: " + Tema.fecha(str(cat.get("generado", "—")))))
	if cat.is_empty():
		_col.add_child(Tema.etiqueta("Todavía no hay datos del estudio. Revisá la conexión y tocá ⟳.", 20, Tema.TEXTO2, true))
		return
	var r: Dictionary = cat.get("resumen", {})
	var fichas := GridContainer.new()
	fichas.columns = 2 if vertical else 5
	fichas.add_theme_constant_override("h_separation", 14)
	fichas.add_theme_constant_override("v_separation", 14)
	for f in [["PRODUCCIONES", str(int(r.get("producciones", 0))), Tema.TEXTO],
			["PARA REVISAR", str(int(r.get("pendientes_revision", 0))), Tema.ACENTO],
			["RENDERIZANDO", str(int(r.get("renderizando", 0))), Tema.AZUL],
			["EN EL SERVIDOR", Tema.bytes(int(r.get("bytes_publicados", 0))), Tema.TEXTO],
			["EN ESTE TELÉFONO", Tema.bytes(api.bytes_cache()), Tema.TEXTO]]:
		var p := Tema.panel(14)
		p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 0)
		v.add_child(Tema.etiqueta(f[0], 14, Tema.TEXTO2))
		v.add_child(Tema.etiqueta(f[1], 30, f[2]))
		p.add_child(v)
		fichas.add_child(p)
	_col.add_child(fichas)
	if api.pendientes() > 0:
		_col.add_child(Tema.etiqueta("⚠ %d decisión(es) sin enviar: se envían solas al volver la conexión." % api.pendientes(), 18, Tema.NARANJA))
	var rem: Dictionary = ProjectSettings.get_setting("estudio/version", {}).get("remoto", {})
	var local_apk := int(ProjectSettings.get_setting("estudio/version", {}).get("apk", 0))
	if int(rem.get("apk", 0)) > local_apk and str(rem.get("apk_url", "")) != "":
		var b := Tema.boton("⬆  Hay una APK nueva (v%d): instalar encima, sin desinstalar" % int(rem.get("apk", 0)),
			func(): OS.shell_open(str(rem["apk_url"])), "acento")
		_col.add_child(b)

	var prods: Array = cat.get("producciones", [])
	var nuevas := prods.filter(func(p):
		for e in p.get("escenas", []):
			if api.es_nuevo(api.clave_version(p["id"], e["id"], int(e["version_actual"]))):
				return true
		return false)
	_seccion("Novedades", nuevas, "No hay producciones nuevas desde la última vez.")
	_seccion("Últimas producciones", prods.slice(0, 8), "")
	var pend := []
	var rend := []
	var aprob := []
	for p in prods:
		for e in p.get("escenas", []):
			var est: String = e["versiones"].back().get("estado", "")
			var fila := {"p": p, "e": e}
			if est in ["en_revision", "correcciones"]:
				pend.append(fila)
			elif est == "renderizando":
				rend.append(fila)
			elif est == "aprobada":
				aprob.append(fila)
	_lista_escenas("Escenas pendientes de revisión", pend, "Nada pendiente. ✔")
	_lista_escenas("En renderizado", rend, "No hay renders en curso.")
	_lista_escenas("Escenas aprobadas", aprob, "Todavía no hay escenas aprobadas.")

func _seccion(nombre: String, prods: Array, vacio: String) -> void:
	if prods.is_empty() and vacio == "":
		return
	_col.add_child(Tema.separador(4))
	_col.add_child(Tema.etiqueta(nombre.to_upper(), 18, Tema.ACENTO))
	if prods.is_empty():
		_col.add_child(Tema.etiqueta(vacio, 17, Tema.TEXTO2))
		return
	var sc := ScrollContainer.new()
	sc.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.custom_minimum_size.y = 330
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 18)
	sc.add_child(h)
	for p in prods:
		h.add_child(tarjeta_produccion(p, 340))
	_col.add_child(sc)

func _lista_escenas(nombre: String, filas: Array, vacio: String) -> void:
	_col.add_child(Tema.separador(4))
	_col.add_child(Tema.etiqueta(nombre.to_upper(), 18, Tema.ACENTO))
	if filas.is_empty():
		_col.add_child(Tema.etiqueta(vacio, 17, Tema.TEXTO2))
		return
	for f in filas:
		var e: Dictionary = f["e"]
		var v: Dictionary = e["versiones"].back()
		var b := Tema.boton("", func(): app.ir("escena", {"produccion": f["p"]["id"], "escena": e["id"]}))
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.clip_text = true                     # un título largo no debe ensanchar la página (en vertical se sale)
		b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		b.custom_minimum_size.y = 64
		b.text = "  %s  ·  Escena %02d — %s  ·  v%d  ·  %s" % [f["p"].get("titulo", ""), int(e.get("numero", 0)),
			e.get("titulo", ""), int(v.get("version", 1)), Tema.ESTADOS.get(v.get("estado", ""), [""])[0]]
		_col.add_child(b)
