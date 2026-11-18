extends Control
## Lanzador del cliente liviano (lo único que no se actualiza sin instalar una APK nueva).
## 1) Lee la versión de la APK (res://boot/version.json) y la del código descargado (user://app/instalado.json).
## 2) Consulta app.json en la release "app" del repositorio. Si hay código más nuevo para esta APK,
##    baja app.pck (unos cientos de KB), verifica su SHA-256 y lo monta encima del código de la APK.
## 3) Abre la interfaz principal. Sin internet sigue con lo último que tenga.
## Si la release trae una APK más nueva (cambió el motor o el lanzador), la interfaz ofrece instalarla:
## está firmada con la misma clave, así que se instala ENCIMA sin desinstalar ni perder datos.

const REPO := "Cinema3DSHR/Cinema3DSHR"
const URL_APP_JSON := "https://github.com/%s/releases/download/app/app.json"
const DIR_APP := "user://app"

var _estado: Label
var _barra: ProgressBar
var _http: HTTPRequest
var _local := {}
var _remoto := {}

func _ready() -> void:
	var fondo := ColorRect.new()
	fondo.color = Color(0.035, 0.035, 0.045)
	fondo.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(fondo)
	var caja := VBoxContainer.new()
	caja.set_anchors_preset(Control.PRESET_CENTER)
	caja.custom_minimum_size = Vector2(620, 180)
	caja.position = Vector2(-310, -90)
	caja.alignment = BoxContainer.ALIGNMENT_CENTER
	add_child(caja)
	var t := Label.new()
	t.text = "3D  FILM  STUDIO"
	t.add_theme_font_size_override("font_size", 46)
	t.add_theme_color_override("font_color", Color(0.91, 0.69, 0.29))
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	caja.add_child(t)
	_estado = Label.new()
	_estado.add_theme_font_size_override("font_size", 20)
	_estado.add_theme_color_override("font_color", Color(0.7, 0.7, 0.75))
	_estado.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	caja.add_child(_estado)
	_barra = ProgressBar.new()
	_barra.custom_minimum_size = Vector2(620, 8)
	_barra.show_percentage = false
	_barra.visible = false
	caja.add_child(_barra)
	_local = _leer_json("res://boot/version.json")
	_montar_instalado()
	_buscar_actualizacion()

func _leer_json(ruta: String) -> Dictionary:
	if not FileAccess.file_exists(ruta):
		return {}
	var d = JSON.parse_string(FileAccess.get_file_as_string(ruta))
	return d if d is Dictionary else {}

func _version_codigo() -> int:
	return int(_leer_json(DIR_APP + "/instalado.json").get("app", 0))

## Monta el código descargado antes si es más nuevo que el que trae la APK.
func _montar_instalado() -> void:
	var inst := _leer_json(DIR_APP + "/instalado.json")
	if inst.is_empty():
		return
	if int(inst.get("apk", 0)) != int(_local.get("apk", 0)) or int(inst.get("app", 0)) <= int(_local.get("app", 0)):
		return  # se instaló otra APK (o una más nueva que el parche): el parche viejo no corresponde
	var pck := DIR_APP + "/" + str(inst.get("archivo", ""))
	if FileAccess.file_exists(pck) and ProjectSettings.load_resource_pack(pck, true):
		_local["app_montado"] = int(inst.get("app", 0))

func _buscar_actualizacion() -> void:
	_estado.text = "Buscando novedades…"
	_http = HTTPRequest.new()
	_http.timeout = 8.0
	add_child(_http)
	_http.request_completed.connect(_on_app_json)
	if _http.request(URL_APP_JSON % REPO + "?t=%d" % Time.get_unix_time_from_system()) != OK:
		_abrir()

func _on_app_json(res: int, codigo: int, _h: PackedStringArray, cuerpo: PackedByteArray) -> void:
	if res != HTTPRequest.RESULT_SUCCESS or codigo != 200:
		_abrir()
		return
	var d = JSON.parse_string(cuerpo.get_string_from_utf8())
	if not (d is Dictionary):
		_abrir()
		return
	_remoto = d
	var actual: int = max(int(_local.get("app", 0)), int(_local.get("app_montado", 0)))
	var mismo_apk := int(d.get("apk", -1)) == int(_local.get("apk", 0))
	if mismo_apk and int(d.get("app", 0)) > actual and str(d.get("pck_url", "")) != "":
		_descargar_pck()
	else:
		_abrir()

func _descargar_pck() -> void:
	DirAccess.make_dir_recursive_absolute(DIR_APP)
	var nombre := "app_%d.pck" % int(_remoto["app"])
	_estado.text = "Actualizando la app (v%d)…" % int(_remoto["app"])
	_barra.visible = true
	_http.request_completed.disconnect(_on_app_json)
	_http.download_file = DIR_APP + "/" + nombre + ".tmp"
	_http.timeout = 120.0
	_http.request_completed.connect(_on_pck.bind(nombre))
	_http.request(str(_remoto["pck_url"]))
	set_process(true)

func _process(_d: float) -> void:
	if _http and _http.get_body_size() > 0:
		_barra.value = 100.0 * _http.get_downloaded_bytes() / _http.get_body_size()

func _on_pck(res: int, codigo: int, _h: PackedStringArray, _b: PackedByteArray, nombre: String) -> void:
	set_process(false)
	var tmp := DIR_APP + "/" + nombre + ".tmp"
	if res == HTTPRequest.RESULT_SUCCESS and codigo == 200 and FileAccess.get_sha256(tmp) == str(_remoto.get("pck_sha256", "")):
		DirAccess.rename_absolute(tmp, DIR_APP + "/" + nombre)
		# borrar parches anteriores
		for f in DirAccess.get_files_at(DIR_APP):
			if f.ends_with(".pck") and f != nombre:
				DirAccess.remove_absolute(DIR_APP + "/" + f)
		var inst := {"app": int(_remoto["app"]), "apk": int(_local.get("apk", 0)), "archivo": nombre}
		var fa := FileAccess.open(DIR_APP + "/instalado.json", FileAccess.WRITE)
		fa.store_string(JSON.stringify(inst))
		fa.close()
		if ProjectSettings.load_resource_pack(DIR_APP + "/" + nombre, true):
			_local["app_montado"] = int(_remoto["app"])
	else:
		DirAccess.remove_absolute(tmp)
	_abrir()

func _abrir() -> void:
	var info := _local.duplicate()
	info["remoto"] = _remoto
	ProjectSettings.set_setting("estudio/version", info)
	get_tree().change_scene_to_file.call_deferred("res://main/main.tscn")
