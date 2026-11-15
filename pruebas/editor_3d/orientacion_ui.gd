extends SceneTree
## Prueba de orientación: abre la app completa en la ventana que se pida (vertical u horizontal) y saca capturas de
## INICIO, AJUSTES, PELÍCULAS y EDITOR 3D. Uso: godot --path app --resolution 720x1440 --script … -- GLB JSON SALIDA PREFIJO
var _p := 0
var _m
var _out := ""
var _pre := ""
func _process(_d: float) -> bool:
	_p += 1
	var a := OS.get_cmdline_user_args()
	match _p:
		1:
			_out = a[2]
			_pre = a[3]
			_m = load("res://main/main.tscn").instantiate()
			get_root().add_child(_m)
		40:
			print("VERTICAL=", _m.vertical, " escala=", get_root().content_scale_size)
			_cap("1_inicio")
			_m.ir("ajustes", {}, true)
		55:
			_cap("2_ajustes")
			_m.ir("peliculas", {}, true)
		70:
			_cap("3_peliculas")
			_m.ir("editor", {"produccion": "p005_mansion_cqb_30s_720p_30fps", "escena": "e01", "version": 1, "glb_local": a[0], "json_local": a[1]})
		110:
			var ed = _m._pila.back()["nodo"]
			ed._ir_a(15.0)
			ed._modo_montaje()
		125:
			_cap("4_editor")
			quit()
	return false
func _cap(n: String) -> void:
	get_root().get_texture().get_image().save_png("%s/%s_%s.png" % [_out, _pre, n])
