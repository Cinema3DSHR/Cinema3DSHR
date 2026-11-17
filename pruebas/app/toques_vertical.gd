extends SceneTree
## Toques reales en la app (vertical u horizontal): abre la app completa, toca botones de la barra y de las páginas
## con eventos de pantalla táctil EN COORDENADAS DE VENTANA (como Android) y comprueba que respondan.
## Uso: xvfb-run -a godot --path app --resolution 1080x2340 --script res://../pruebas/app/toques_vertical.gd -- SALIDA
var _p := 0
var _m
var _out := ""
var _ok := 0
var _mal: Array = []
var _ed_t0 := 0.0
var _tab_previa := 0
func _fin() -> void:
	print("\n%d/%d OK%s" % [_ok, _ok + _mal.size(), "" if _mal.is_empty() else " — FALLAN: " + str(_mal)])
	quit()
func _tocar_en(c: Vector2) -> void:
	var w: Vector2 = get_root().get_final_transform() * c
	for presionado in [true, false]:
		var t := InputEventScreenTouch.new()
		t.index = 0
		t.position = w
		t.pressed = presionado
		Input.parse_input_event(t)
	print("toque en ", c)
func _chk(n: String, c: bool, d := "") -> void:
	if c: _ok += 1
	else: _mal.append(n)
	print(("OK    " if c else "FALLA ") + n + ("" if d == "" else " — " + d))
func _tocar(ctrl: Control) -> void:
	# centro del control en coordenadas de ventana (lo que manda Android)
	var c := ctrl.get_global_rect().get_center()
	var w: Vector2 = get_root().get_final_transform() * c
	for presionado in [true, false]:
		var t := InputEventScreenTouch.new()
		t.index = 0
		t.position = w
		t.pressed = presionado
		Input.parse_input_event(t)
	print("toque en ", c, " (ventana ", w, ") sobre ", ctrl.name, " «", ctrl.get("text"), "»")
func _boton(raiz: Node, texto: String) -> Button:
	for b in raiz.find_children("*", "Button", true, false):
		if str(b.text).strip_edges().contains(texto) and b.is_visible_in_tree():
			return b
	return null
func _process(_d: float) -> bool:
	_p += 1
	match _p:
		1:
			_out = OS.get_cmdline_user_args()[0]
			_m = load("res://main/main.tscn").instantiate()
			get_root().add_child(_m)
		40:
			print("ventana=", DisplayServer.window_get_size(), " vertical=", _m.vertical, " escala=", get_root().content_scale_size,
				" transform=", get_root().get_final_transform())
			_cap("a_inicio")
			_tocar(_m._nav["ajustes"])
		60:
			_chk("tocar AJUSTES en la barra abre AJUSTES", _m._pila.size() > 0 and _m._pila[0]["nombre"] == "ajustes", str(_m._pila[0]["nombre"]))
			_cap("b_tras_tocar_ajustes")
			_tocar(_m._nav["peliculas"])
		80:
			_chk("tocar PELÍCULAS en la barra abre PELÍCULAS", _m._pila[0]["nombre"] == "peliculas", str(_m._pila[0]["nombre"]))
			_cap("c_peliculas")
			var a := OS.get_cmdline_user_args()
			if a.size() < 3:
				_fin()
				return true
			_m.ir("editor", {"produccion": "p009_duo_cero", "escena": "e01", "version": 1, "glb_local": a[1], "json_local": a[2]})
		130:
			var ed = _m._pila.back()["nodo"]
			_cap("d_editor")
			_ed_t0 = ed._t
			_tocar(ed._play)
		150:
			var ed = _m._pila.back()["nodo"]
			_chk("editor: tocar ▶ reproduce", ed._jugando, "t=%.2f" % ed._t)
			_tocar(ed._play)
			var tabs: TabContainer = ed._tabs
			_tab_previa = tabs.current_tab
			var barra: TabBar = tabs.get_tab_bar()
			var r := barra.get_tab_rect(2)
			_tocar_en(barra.get_global_transform() * r.get_center())
		170:
			var ed = _m._pila.back()["nodo"]
			_chk("editor: tocar la pestaña DIRECCIÓN la abre", ed._tabs.current_tab == 2, "pestaña %d" % ed._tabs.current_tab)
			_cap("e_direccion")
			_tocar(_boton(ed, "MONTAJE"))
		190:
			var ed = _m._pila.back()["nodo"]
			_chk("editor: tocar MONTAJE cambia el modo", ed._modo == "montaje", ed._modo)
			_tocar(_boton(ed, "◀"))
		210:
			_chk("editor: tocar ◀ vuelve atrás", _m._pila.back()["nombre"] != "editor", _m._pila.back()["nombre"])
			_fin()
	return false
func _cap(n: String) -> void:
	get_root().get_texture().get_image().save_png("%s/%s.png" % [_out, n])
