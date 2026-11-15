extends SceneTree
## PRUEBA DE IDA Y VUELTA (parte Godot): carga la previsualización, captura cámaras con CamaraDirector (lo mismo que
## hace el botón COLOCAR CÁMARA) y proyecta puntos de control a píxeles de 1280×720 desde Godot.
## Uso: godot --headless --path app --script res://../pruebas/editor_3d/ida_vuelta.gd -- PREVIA.glb PREVIA.json SALIDA.json

var _hecho := false

func _process(_d: float) -> bool:
	if _hecho:
		return true
	_hecho = true
	_correr()
	quit()
	return false

func _correr() -> void:
	var a := OS.get_cmdline_user_args()
	var datos: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(a[1]))
	var vp := SubViewport.new()
	vp.size = Vector2i(1280, 720)
	vp.own_world_3d = true
	get_root().add_child(vp)
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(a[0], st) != OK:
		push_error("no se pudo abrir el GLB")
		return
	var escena := doc.generate_scene(st)
	vp.add_child(escena)
	var ap: AnimationPlayer = escena.find_children("*", "AnimationPlayer", true, false)[0]
	var todo := Animation.new()
	for n in ap.get_animation_list():
		var an := ap.get_animation(n)
		todo.length = maxf(todo.length, an.length)
		for i in an.get_track_count():
			an.copy_track(i, todo)
	var lib := AnimationLibrary.new()
	lib.add_animation("escena", todo)
	ap.add_animation_library("estudio", lib)
	ap.current_animation = "estudio/escena"
	ap.pause()
	# puntos de control en coordenadas de Blender: una grilla que cubre la habitación y el pasillo
	var puntos: Array = []
	for x in [-4.0, -2.0, 0.0, 2.0, 4.0]:
		for y in [-6.0, -2.0, 1.0, 3.0, 5.0, 7.5]:
			for z in [0.1, 1.2, 2.5]:
				puntos.append(Vector3(x, y, z))
	var fps: float = datos["fps"]
	var salida := {"puntos_blender": puntos.map(func(p): return [p.x, p.y, p.z]), "casos": []}
	var cams := {}
	for c in escena.find_children("*", "Camera3D", true, false):
		cams[str(c.name)] = c
	# 1) cámaras de rodaje exportadas desde Blender, en el fotograma de control
	for nombre in datos["control"]["camaras"]:
		var info: Dictionary = datos["control"]["camaras"][nombre]
		ap.seek(float(info["frame"]) / fps, true)   # GLB: cuadro f en f/fps
		var c: Camera3D = cams.get(nombre)
		if c == null:
			push_error("falta la cámara " + nombre)
			continue
		salida["casos"].append(_caso(vp, c, "toma", nombre, int(info["frame"]), puntos))
	# 1 bis) animaciones: caderas de cada personaje en los cuadros de control vs. Blender (cm)
	var err_cad := 0.0
	var n_cad := 0
	var frames: Array = datos["control"]["frames"]
	for i in frames.size():
		ap.seek(float(frames[i]) / fps, true)
		for act in datos["actores"]:
			var nodo := escena.find_child(str(act["nodo"]), true, false)
			var esq: Skeleton3D = nodo.find_children("*", "Skeleton3D", true, false)[0]
			var hb := esq.find_bone("mixamorig:Hips")
			if hb < 0:
				hb = esq.find_bone("mixamorig_Hips")
			var g := esq.global_transform * esq.get_bone_global_pose(hb).origin
			var b := CamaraDirector.a_blender(g)
			var ref: Array = datos["control"]["caderas"][act["id"]][i]
			err_cad = maxf(err_cad, b.distance_to(Vector3(ref[0], ref[1], ref[2])))
			n_cad += 1
	salida["caderas"] = {"muestras": n_cad, "error_max_m": err_cad}
	print("CADERAS muestras=", n_cad, " error_max_m=", err_cad)
	# 2) cámaras libres al azar (como si el director navegara y pulsara COLOCAR CÁMARA)
	var libre := Camera3D.new()
	vp.add_child(libre)
	var rng := RandomNumberGenerator.new()
	rng.seed = 20261115
	for i in 12:
		var pos_b := Vector3(rng.randf_range(-4.0, 4.0), rng.randf_range(-6.0, 7.0), rng.randf_range(0.4, 2.9))
		libre.global_transform = Transform3D(Basis(), CamaraDirector.a_godot(pos_b))
		libre.rotation = Vector3(deg_to_rad(rng.randf_range(-35, 25)), deg_to_rad(rng.randf_range(-180, 180)),
			deg_to_rad(rng.randf_range(-8, 8)))
		libre.fov = rng.randf_range(25.0, 80.0)
		salida["casos"].append(_caso(vp, libre, "libre", "libre_%02d" % i, 0, puntos))
	var f := FileAccess.open(a[2], FileAccess.WRITE)
	f.store_string(JSON.stringify(salida, " "))
	print("IDA_VUELTA casos=", salida["casos"].size())

func _caso(vp: SubViewport, c: Camera3D, tipo: String, nombre: String, frame: int, puntos: Array) -> Dictionary:
	c.current = true
	var px: Array = []
	for p in puntos:
		var g := CamaraDirector.a_godot(p)
		if c.is_position_behind(g):
			px.append(null)
		else:
			var s := c.unproject_position(g)
			px.append([s.x, s.y])
	return {"tipo": tipo, "nombre": nombre, "frame": frame, "viewport": [vp.size.x, vp.size.y],
		"captura": CamaraDirector.capturar(c, {"camera_id": nombre}), "px_godot": px}
