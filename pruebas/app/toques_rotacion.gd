extends SceneTree
## La app arranca en horizontal, el teléfono gira a vertical (cambia el tamaño de la ventana, como hace Android al
## rotar solo) y se tocan botones con eventos táctiles en coordenadas de ventana; después vuelve a horizontal.
## Uso: xvfb-run -a -s "-screen 0 2400x2400x24" godot --path app --resolution 2340x1080 --script res://../pruebas/app/toques_rotacion.gd -- SALIDA
var _p := 0
var _m
var _out := ""
var _ok := 0
var _mal: Array = []
func _chk(n: String, c: bool, d := "") -> void:
	if c: _ok += 1
	else: _mal.append(n)
	print(("OK    " if c else "FALLA ") + n + ("" if d == "" else " — " + d))
func _tocar(ctrl: Control) -> void:
	var w: Vector2 = get_root().get_final_transform() * ctrl.get_global_rect().get_center()
	for pr in [true, false]:
		var t := InputEventScreenTouch.new()
		t.position = w
		t.pressed = pr
		Input.parse_input_event(t)
func _process(_d: float) -> bool:
	_p += 1
	match _p:
		1:
			_out = OS.get_cmdline_user_args()[0]
			_m = load("res://main/main.tscn").instantiate()
			get_root().add_child(_m)
		30:
			_chk("arranca en horizontal", not _m.vertical, str(DisplayServer.window_get_size()))
			_tocar(_m._nav["peliculas"])
		45:
			_chk("horizontal: tocar PELÍCULAS funciona", _m._pila[0]["nombre"] == "peliculas")
			DisplayServer.window_set_size(Vector2i(1080, 2340))     # el teléfono gira a vertical
		75:
			_chk("al girar el teléfono la app pasa a vertical", _m.vertical, "%s · escala %s" % [DisplayServer.window_get_size(), get_root().content_scale_size])
			_cap("rot_vertical")
			_tocar(_m._nav["ajustes"])
		90:
			_chk("vertical: tocar AJUSTES funciona", _m._pila[0]["nombre"] == "ajustes")
			_tocar(_m._nav["inicio"])
		105:
			_chk("vertical: tocar INICIO funciona", _m._pila[0]["nombre"] == "inicio")
			DisplayServer.window_set_size(Vector2i(2340, 1080))     # vuelve a horizontal
		135:
			_chk("al volver a horizontal la app se reacomoda", not _m.vertical)
			_tocar(_m._nav["escenarios"])
		150:
			_chk("horizontal otra vez: tocar ESCENARIOS funciona", _m._pila[0]["nombre"] == "escenarios")
			print("\n%d/%d OK%s" % [_ok, _ok + _mal.size(), "" if _mal.is_empty() else " — FALLAN: " + str(_mal)])
			quit(0 if _mal.is_empty() else 1)
	return false
func _cap(n: String) -> void:
	get_root().get_texture().get_image().save_png("%s/%s.png" % [_out, n])
