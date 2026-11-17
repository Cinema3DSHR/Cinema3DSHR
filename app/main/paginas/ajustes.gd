extends Pagina
## AJUSTES: vincular la cuenta (token personal de GitHub, guardado cifrado en el teléfono), almacenamiento,
## versión de la app y actualizaciones.

var _col: VBoxContainer
var _estado: Label

func abrir(_d: Dictionary) -> void:
	_col = columna_desplazable()
	_construir()

func _construir() -> void:
	limpiar(_col)
	_col.add_child(titulo("Ajustes"))
	# ---- pantalla
	var pp := Tema.panel()
	var vp := VBoxContainer.new()
	pp.add_child(vp)
	vp.add_child(Tema.etiqueta("PANTALLA", 17, Tema.ACENTO))
	vp.add_child(Tema.etiqueta("La app gira sola con el teléfono: ponelo vertical u horizontal y la pantalla se reacomoda (también el EDITOR 3D).", 16, Tema.TEXTO2, true))
	_col.add_child(pp)
	# ---- cuenta
	var p := Tema.panel()
	var v := VBoxContainer.new()
	p.add_child(v)
	v.add_child(Tema.etiqueta("CUENTA DEL ESTUDIO", 17, Tema.ACENTO))
	v.add_child(Tema.etiqueta("Ver producciones no necesita cuenta. Para APROBAR, RECHAZAR, pedir CORRECCIONES, VOLVER A RENDERIZAR o EXPORTAR hace falta un token personal de GitHub del dueño del repositorio (fine-grained, sólo para Cinema3DSHR, permiso Issues: lectura y escritura). Se guarda cifrado en este teléfono; nunca viaja dentro de la app ni del repositorio.", 16, Tema.TEXTO2, true))
	var h := HBoxContainer.new()
	var campo := LineEdit.new()
	campo.secret = true
	campo.placeholder_text = "github_pat_…" if not api.tiene_token() else "•••• token guardado ••••"
	campo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(campo)
	h.add_child(Tema.boton("GUARDAR", func():
		if campo.text.strip_edges().length() < 20:
			app.mostrar_aviso("Ese token parece incompleto.")
			return
		api.guardar_token(campo.text)
		campo.text = ""
		_probar(), "acento"))
	v.add_child(h)
	var h2 := HFlowContainer.new()
	h2.add_child(Tema.boton("PROBAR CONEXIÓN", _probar))
	h2.add_child(Tema.boton("DESVINCULAR", func(): api.borrar_token(); _construir(); app.mostrar_aviso("Cuenta desvinculada."), "rojo"))
	h2.add_child(Tema.boton("CREAR TOKEN (abre GitHub)", func():
		OS.shell_open("https://github.com/settings/personal-access-tokens/new")))
	v.add_child(h2)
	_estado = Tema.etiqueta("Cuenta vinculada." if api.tiene_token() else "Sin cuenta: modo sólo lectura.", 16,
		Tema.VERDE if api.tiene_token() else Tema.TEXTO2)
	v.add_child(_estado)
	_col.add_child(p)
	# ---- almacenamiento
	var p2 := Tema.panel()
	var v2 := VBoxContainer.new()
	p2.add_child(v2)
	v2.add_child(Tema.etiqueta("ALMACENAMIENTO EN ESTE TELÉFONO", 17, Tema.ACENTO))
	v2.add_child(Tema.etiqueta("Videos, portadas y escenas 3D descargados: %s. Se pueden borrar sin perder nada: se vuelven a bajar cuando haga falta." % Tema.bytes(api.bytes_cache()), 16, Tema.TEXTO2, true))
	v2.add_child(Tema.boton("BORRAR DESCARGAS", func(): api.limpiar_cache(); _construir(); app.mostrar_aviso("Descargas borradas.")))
	_col.add_child(p2)
	# ---- versión
	var ver: Dictionary = ProjectSettings.get_setting("estudio/version", {})
	var rem: Dictionary = ver.get("remoto", {})
	var p3 := Tema.panel()
	var v3 := VBoxContainer.new()
	p3.add_child(v3)
	v3.add_child(Tema.etiqueta("APLICACIÓN", 17, Tema.ACENTO))
	v3.add_child(Tema.etiqueta("APK v%d · código v%d (%s)%s" % [int(ver.get("apk", 0)), max(int(ver.get("app", 0)), int(ver.get("app_montado", 0))),
		str(ver.get("commit", "")), ("\nÚltima publicada: APK v%d · código v%d" % [int(rem.get("apk", 0)), int(rem.get("app", 0))]) if not rem.is_empty() else ""], 16, Tema.TEXTO2, true))
	v3.add_child(Tema.etiqueta("Las mejoras de la interfaz llegan solas al abrir la app (sin reinstalar). Si cambia el motor, se ofrece una APK nueva firmada con la misma clave: se instala encima sin perder datos.", 15, Tema.TEXTO2, true))
	if str(rem.get("apk_url", "")) != "":
		v3.add_child(Tema.boton("DESCARGAR LA ÚLTIMA APK", func(): OS.shell_open(str(rem["apk_url"]))))
	_col.add_child(p3)

func _probar() -> void:
	_estado.text = "Probando…"
	api.probar_token(func(ok, t):
		_estado.text = t
		_estado.add_theme_color_override("font_color", Tema.VERDE if ok else Tema.ROJO))
