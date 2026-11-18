extends SceneTree
## Prueba de aceptación de la REVISIÓN 3D en la app (docs/REVISION_Y_AUTORIZACION.md) con la previsualización REAL de
## una escena: carga en 3D, tomas y cámaras de rodaje, cámara libre que no toca las de rodaje, cuadro a cuadro, estados
## del catálogo, habilitación de ✔ APROBAR y 🎬 AUTORIZAR RENDER FINAL y bloqueo con una previsualización vieja.
## No renderiza con Blender ni manda nada a GitHub (sin token). Uso (con pantalla virtual para las capturas):
##   xvfb-run -a godot --path app --rendering-driver opengl3 --script res://../pruebas/revision/revision_ui.gd -- \
##       GLB JSON PRODUCCION ESCENA VERSION SALIDA_DIR
var _paso := 0
var _app
var _ed
var _a: PackedStringArray
var _ok := 0
var _mal: Array = []
var _cam_ref: Transform3D
var _cam_nombre := ""

func _chequear(nombre: String, cond: bool, detalle := "") -> void:
	if cond:
		_ok += 1
	else:
		_mal.append(nombre)
	print(("OK    " if cond else "FALLA ") + nombre + ("" if detalle == "" else " — " + detalle))

func _catalogo(estado: String, huella: String) -> void:
	_app.api.catalogo = {"producciones": [{"id": _a[2], "render": {"resolucion": "960x540", "fps": 30, "muestras": 6},
		"escenas": [{"id": _a[3], "versiones": [{"version": int(_a[4]), "estado_revision": estado, "huella_actual": huella}]}]}]}

func _abrir() -> void:
	_ed = load("res://main/paginas/editor.gd").new()
	_ed.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ed.set("app", _app)
	_app.add_child(_ed)
	_ed.abrir({"produccion": _a[2], "escena": _a[3], "version": int(_a[4]), "glb_local": _a[0], "json_local": _a[1]})

func _process(_d: float) -> bool:
	_paso += 1
	if _paso == 1:
		_a = OS.get_cmdline_user_args()
		get_root().size = Vector2i(1600, 900)
		_app = load("res://../pruebas/editor_3d/app_falsa.gd").new()
		_app.set_anchors_preset(Control.PRESET_FULL_RECT)
		_app.theme = Tema.tema_global()
		get_root().add_child(_app)
		var h := str(JSON.parse_string(FileAccess.get_file_as_string(_a[1])).get("huella", ""))
		_catalogo("LISTA PARA REVISIÓN", h)
		_abrir()
	elif _paso == 20:
		# 2. la APK carga y muestra la escena en 3D
		_chequear("2  la escena 3D cargó completa", _ed._cargado and _ed._escena != null, _ed._info.text.strip_edges())
		_chequear("2  tiene personajes animados", _ed._actores.size() >= 1 and _ed._ap != null, "%d personajes" % _ed._actores.size())
		var tomas: Array = _ed._d.get("tomas", [])
		_chequear("3  tomas y cámaras de rodaje disponibles", tomas.size() > 0 and _ed._camaras_rodaje.size() >= tomas.size(),
			"%d tomas, %d cámaras" % [tomas.size(), _ed._camaras_rodaje.size()])
		_chequear("4  estado visible: LISTA PARA REVISIÓN", _ed._estado_lbl.text.contains("LISTA PARA REVISIÓN"), _ed._estado_lbl.text)
		_chequear("4  ✔ APROBAR habilitado (escena cargada y revisable)", not _ed._btn_aprobar.disabled)
		_chequear("4  🎬 AUTORIZAR RENDER FINAL deshabilitado (todavía no aprobada)", _ed._btn_autorizar.disabled)
		# 3. elegir una toma: la vista pasa a la cámara de rodaje
		var tm: Dictionary = tomas[min(2, tomas.size() - 1)]
		_cam_nombre = str(tm["camara"])
		_ed._ver_toma(tm)
		_ed._ir_a(float(tm["inicio_s"]) + 0.5)
		_cam_ref = _ed._camaras_rodaje[_cam_nombre].global_transform
		_chequear("3  ver por toma usa la cámara de rodaje de esa toma", _ed._cam_activa == _ed._camaras_rodaje[_cam_nombre], _cam_nombre)
	elif _paso == 30:
		_captura("revision_toma.png")
		# 4. cuadro a cuadro: adelante y atrás
		_ed._ir_a(5.0)
		var f0: int = _ed._frame()
		_ed._cuadro(1)
		var f1: int = _ed._frame()
		_ed._cuadro(1)
		var f2: int = _ed._frame()
		_ed._cuadro(-1)
		var f3: int = _ed._frame()
		_chequear("4  avanzar y retroceder cuadro a cuadro", f1 == f0 + 1 and f2 == f0 + 2 and f3 == f0 + 1, "%d → %d → %d → %d" % [f0, f1, f2, f3])
		# cámara libre: moverla no toca las cámaras de rodaje
		_ed._modo_libre()
		_ed._mirar(Vector2(-120, 40))
		_ed._cam_libre.global_position += Vector3(2, 1, -3)
		var tm2: Dictionary = _ed._d["tomas"][min(2, _ed._d["tomas"].size() - 1)]
		_ed._ver_toma(tm2)
		_ed._ir_a(float(tm2["inicio_s"]) + 0.5)
		var t_now: Transform3D = _ed._camaras_rodaje[_cam_nombre].global_transform
		_chequear("3  la cámara libre no modifica las cámaras de rodaje", t_now.origin.distance_to(_cam_ref.origin) < 1e-4,
			"diferencia %.6f m" % t_now.origin.distance_to(_cam_ref.origin))
		# personajes: qué clip hace cada uno en este momento
		var c: Dictionary = _ed.clip_en(_ed._actores[0], 5.0)
		_chequear("4  se ve qué animación hace cada personaje", not c.is_empty(), str(c.get("clip", "")))
		_ed._modo_libre()
	elif _paso == 40:
		_captura("revision_libre.png")
		# estados que vienen del estudio: aprobada → se habilita AUTORIZAR
		_catalogo("APROBADA POR EL USUARIO", _ed._huella)
		_ed._actualizar_estado_revision()
		_chequear("8  aprobada: 🎬 AUTORIZAR RENDER FINAL habilitado", not _ed._btn_autorizar.disabled)
		_chequear("6  aprobada: ✔ APROBAR deshabilitado (ya aprobada)", _ed._btn_aprobar.disabled)
		_catalogo("CORRECCIONES SOLICITADAS", _ed._huella)
		_ed._actualizar_estado_revision()
		_chequear("6  con correcciones: AUTORIZAR deshabilitado otra vez", _ed._btn_autorizar.disabled, _ed._estado_lbl.text)
		_catalogo("RENDER AUTORIZADO", _ed._huella)
		_ed._actualizar_estado_revision()
		_chequear("9  autorizado: el estado se ve en la app", _ed._estado_lbl.text.contains("RENDER AUTORIZADO"))
		# sin cuenta vinculada no se envía nada (y una aprobación sin conexión nunca queda en espera)
		var res := []
		_app.api.enviar_autorizacion({"produccion": _a[2], "escena": _a[3], "version": 1, "huella": _ed._huella, "config": {}},
			func(ok, t): res.append([ok, t]))
		_chequear("5  sin cuenta vinculada no se manda la autorización", res.size() == 1 and not res[0][0], str(res))
		# previsualización vieja: el catálogo dice otra huella → no se puede aprobar ni autorizar
		_ed.queue_free()
		_catalogo("APROBADA POR EL USUARIO", "huella_de_la_version_nueva")
		_abrir()
	elif _paso == 60:
		_chequear("6  previsualización de otra huella: NO se considera revisable", not _ed._cargado)
		_chequear("6  …✔ APROBAR deshabilitado", _ed._btn_aprobar.disabled)
		_chequear("6  …🎬 AUTORIZAR RENDER FINAL deshabilitado", _ed._btn_autorizar.disabled)
		_captura("revision_estado.png")
		print("\n%d/%d comprobaciones OK%s" % [_ok, _ok + _mal.size(), "" if _mal.is_empty() else " — FALLAN: " + str(_mal)])
		quit(0 if _mal.is_empty() else 1)
	return false

func _captura(n: String) -> void:
	get_root().get_texture().get_image().save_png(_a[5] + "/" + n)
	print("CAPTURA ", n)
