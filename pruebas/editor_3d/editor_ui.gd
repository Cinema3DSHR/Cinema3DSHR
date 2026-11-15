extends SceneTree
## Prueba de la página EDITOR 3D con la previsualización real: abre, avanza el tiempo, elige un personaje, coloca una
## cámara (sin red) y guarda capturas de pantalla. Uso (con ventana, p. ej. xvfb-run):
##   godot --path app --rendering-driver opengl3 --script res://../pruebas/editor_3d/editor_ui.gd -- GLB JSON SALIDA_DIR
var _paso := 0
var _app
var _ed
var _out := ""
func _process(_d: float) -> bool:
	_paso += 1
	var a := OS.get_cmdline_user_args()
	if _paso == 1:
		_out = a[2]
		get_root().size = Vector2i(1600, 900)
		_app = load("res://../pruebas/editor_3d/app_falsa.gd").new()
		_app.set_anchors_preset(Control.PRESET_FULL_RECT)
		_app.theme = Tema.tema_global()
		get_root().add_child(_app)
		_ed = load("res://main/paginas/editor.gd").new()
		_ed.set_anchors_preset(Control.PRESET_FULL_RECT)
		_ed.set("app", _app)
		_app.add_child(_ed)
		_ed.abrir({"produccion": "p005_mansion_cqb_30s_720p_30fps", "escena": "e01", "version": 1, "glb_local": a[0], "json_local": a[1]})
	elif _paso == 30:
		_ed._ir_a(12.0)
		_ed._elegir({"tipo": "personaje", "id": "o3", "nodo": _ed._actores[2]["nodo"]})
	elif _paso == 40:
		_captura("editor_libre_t12.png")
		_ed._ver_toma(_ed._d["tomas"][6])
	elif _paso == 50:
		_captura("editor_toma_t07.png")
		_ed._modo_montaje()
		_ed._ir_a(19.6)
	elif _paso == 60:
		_captura("editor_montaje_t19.png")
		# cámara del director: se captura lo que se ve (vista libre movida)
		_ed._modo_libre()
		_ed._mirar(Vector2(-80, 20))
		var cam: Dictionary = _ed._capturar("prueba", "t08_estatica", 17.0, 20.0, "prueba automática")
		var f := FileAccess.open(_out + "/camara_capturada.json", FileAccess.WRITE)
		f.store_string(JSON.stringify(cam, " "))
		print("CAMARA ", cam["camera_id"], " pos ", cam["position"], " rot ", cam["rotation"], " lente ", cam["lens_mm"])
		var c: Dictionary = _ed.clip_en(_ed._actores[0], 12.3)
		print("CLIP o1 @12.3: ", c)
		print("PROPS: ", _ed._props.text.replace("\n", " | "))
	elif _paso == 70:
		_captura("editor_libre_colocada.png")
		_ed._vp.get_texture().get_image().save_png(_out + "/vista_colocada.png")   # el cuadro 16:9 exacto de la vista
		quit()
	return false
func _captura(n: String) -> void:
	var img := get_root().get_texture().get_image()
	img.save_png(_out + "/" + n)
	print("CAPTURA ", n)
