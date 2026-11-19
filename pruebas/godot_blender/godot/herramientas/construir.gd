## Arma la escena «casa en tormenta» etapa por etapa, la guarda como .tscn (editable) y exporta el GLB.
## Uso: godot --headless --path . -s herramientas/construir.gd -- [--hasta 1..4] [--glb salida/x.glb] [--liviano]
extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var hasta := 4
	var glb := "salida/casa_tormenta.glb"
	var liviano := false
	for i in args.size():
		if args[i] == "--hasta": hasta = int(args[i + 1])
		if args[i] == "--glb": glb = args[i + 1]
		if args[i] == "--liviano": liviano = true
	var raiz := Node3D.new()
	raiz.name = "CasaTormenta"
	root.add_child(raiz)
	var t0 := Time.get_ticks_msec()
	var tiempos := {}
	E1Geometria.construir(raiz)
	if liviano:
		var car := raiz.get_node("Camioneta_Kodiak/Kodiak_carroceria")
		var lo: Node3D = load("res://modelos/kodiak_lo.glb").instantiate()
		var padre := car.get_parent()
		padre.remove_child(car)
		car.free()                     # replace_by movería los hijos (la malla pesada) al nuevo nodo
		lo.name = "Kodiak_carroceria"
		padre.add_child(lo)
		padre.move_child(lo, 0)
	tiempos["1_geometria_ms"] = Time.get_ticks_msec() - t0
	if hasta >= 2:
		t0 = Time.get_ticks_msec()
		E2Materiales.aplicar(raiz)
		tiempos["2_materiales_luces_ms"] = Time.get_ticks_msec() - t0
	if hasta >= 3:
		t0 = Time.get_ticks_msec()
		E3Animacion.crear(raiz)
		tiempos["3_animacion_ms"] = Time.get_ticks_msec() - t0
	if hasta >= 4:
		t0 = Time.get_ticks_msec()
		E4Efectos.crear(raiz)
		tiempos["4_efectos_ms"] = Time.get_ticks_msec() - t0
	await process_frame
	Kit.adueñar(raiz, raiz)
	if not liviano:
		t0 = Time.get_ticks_msec()
		var ps := PackedScene.new()
		ps.pack(raiz)
		var err := ResourceSaver.save(ps, "res://escena/casa_tormenta.tscn")
		tiempos["tscn_ms"] = Time.get_ticks_msec() - t0
		print("tscn: ", error_string(err))
	t0 = Time.get_ticks_msec()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://" + glb.get_base_dir()))
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var e1 := doc.append_from_scene(raiz, st)
	var e2 := doc.write_to_filesystem(st, ProjectSettings.globalize_path("res://" + glb))
	tiempos["5_export_glb_ms"] = Time.get_ticks_msec() - t0
	print("glb: ", error_string(e1), " ", error_string(e2), " → ", glb)
	print("TIEMPOS ", JSON.stringify(tiempos))
	quit()
