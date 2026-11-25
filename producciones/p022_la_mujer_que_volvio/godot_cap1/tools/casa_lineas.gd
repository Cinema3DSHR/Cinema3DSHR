## ESCENA PARA EL ESTILO «MUNDO BLANCO CON LÍNEAS»: casita con ventanas de vidrio, puerta, canteros, mesa servida y lámparas, garaje con auto, jardín con césped y flores, valla,
## pinos y colinas al fondo. Sólo geometría con nombres que Blender reconoce (Arq_, Veg_, Obj_, Vidrio_, Auto) y una cámara vertical. Sin personajes, sin sangre, sin disparos.
## Uso: xvfb-run -a godot --path . --rendering-driver opengl3 --resolution 720x1280 --script res://tools/casa_lineas.gd -- SALIDA
extends SceneTree
var esc: Node3D
var rng := RandomNumberGenerator.new()
func _mat(c: Color, a := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = Color(c.r, c.g, c.b, a); m.roughness = 0.8
	if a < 1.0: m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return m
func _add(nom: String, mesh: Mesh, pos: Vector3, col: Color, rot := Vector3.ZERO, a := 1.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); mi.mesh = mesh; mi.material_override = _mat(col, a); mi.name = nom; mi.position = pos; mi.rotation_degrees = rot; esc.add_child(mi); return mi
func caja(nom: String, pos: Vector3, tam: Vector3, col: Color, rot := Vector3.ZERO, a := 1.0) -> MeshInstance3D:
	var b := BoxMesh.new(); b.size = tam; return _add(nom, b, pos, col, rot, a)
func cil(nom: String, pos: Vector3, r_sup: float, r_inf: float, alto: float, col: Color, rot := Vector3.ZERO, seg := 20) -> MeshInstance3D:
	var c := CylinderMesh.new(); c.top_radius = r_sup; c.bottom_radius = r_inf; c.height = alto; c.radial_segments = seg; c.rings = 1; return _add(nom, c, pos, col, rot)
func esf(nom: String, pos: Vector3, r: float, col: Color, esc_v := Vector3.ONE, seg := 16) -> MeshInstance3D:
	var s := SphereMesh.new(); s.radius = r; s.height = r * 2.0; s.radial_segments = seg; s.rings = seg / 2; var mi := _add(nom, s, pos, col); mi.scale = esc_v; return mi
func prisma(nom: String, pos: Vector3, tam: Vector3, col: Color, rot := Vector3.ZERO) -> MeshInstance3D:
	var p := PrismMesh.new(); p.size = tam; return _add(nom, p, pos, col, rot)

func _casa() -> void:
	var YESO := Color(0.80, 0.75, 0.64); var BLANCO := Color(0.93, 0.93, 0.90); var TEJA := Color(0.50, 0.22, 0.16); var MAD := Color(0.30, 0.18, 0.09); var MADC := Color(0.62, 0.45, 0.26)
	var AN := 4.8; var PR := 4.0; var AL := 2.6; var E := 0.16
	# frente con vanos de puerta y ventanas (x, z de planta → Godot: Z hacia la cámara; la casa mira a +Z)
	var frente := [[-2.4, -1.9, 0.0, 2.6], [-1.9, -1.0, 0.0, 0.9], [-1.9, -1.0, 2.0, 2.6], [-1.0, -0.475, 0.0, 2.6], [-0.475, 0.475, 2.0, 2.6], [0.475, 1.0, 0.0, 2.6], [1.0, 1.9, 0.0, 0.9], [1.0, 1.9, 2.0, 2.6], [1.9, 2.4, 0.0, 2.6]]
	for i in frente.size():
		var f: Array = frente[i]; caja("Arq_casa_frente_%d" % i, Vector3((f[0] + f[1]) / 2, (f[2] + f[3]) / 2, PR / 2), Vector3(f[1] - f[0], f[3] - f[2], E), YESO)
	caja("Arq_casa_fondo", Vector3(0, AL / 2, -PR / 2), Vector3(AN, AL, E), YESO)
	caja("Arq_casa_lado_izq", Vector3(-AN / 2, AL / 2, 0), Vector3(E, AL, PR), YESO); caja("Arq_casa_lado_der", Vector3(AN / 2, AL / 2, 0), Vector3(E, AL, PR), YESO)
	caja("Arq_zocalo", Vector3(0, 0.18, PR / 2 + 0.03), Vector3(AN + 0.1, 0.36, 0.06), Color(0.62, 0.6, 0.56))
	caja("Arq_piso_interior", Vector3(0, 0.04, 0), Vector3(AN - 0.1, 0.08, PR - 0.1), MADC); caja("Arq_techo_interior", Vector3(0, AL + 0.05, 0), Vector3(AN, 0.1, PR), Color(0.9, 0.86, 0.78))
	for s in [-1, 1]:
		caja("Arq_techo_agua_%d" % s, Vector3(s * 1.35, AL + 0.72, 0), Vector3(3.0, 0.12, PR + 0.9), TEJA, Vector3(0, 0, -s * 28))
	prisma("Arq_fronton_frente", Vector3(0, AL + 0.72, PR / 2 - 0.05), Vector3(AN, 1.35, 0.1), YESO); prisma("Arq_fronton_fondo", Vector3(0, AL + 0.72, -PR / 2 + 0.05), Vector3(AN, 1.35, 0.1), YESO)
	caja("Arq_chimenea", Vector3(1.5, AL + 1.5, -0.6), Vector3(0.5, 1.1, 0.5), TEJA); caja("Arq_chimenea_tapa", Vector3(1.5, AL + 2.08, -0.6), Vector3(0.62, 0.08, 0.62), Color(0.6, 0.58, 0.55))
	# puerta
	caja("Arq_puerta", Vector3(0, 1.0, PR / 2 - 0.01), Vector3(0.92, 2.0, 0.07), MAD); caja("Vidrio_puerta", Vector3(0, 1.45, PR / 2 + 0.03), Vector3(0.5, 0.6, 0.02), Color(0.8, 0.92, 1.0), Vector3.ZERO, 0.35)
	caja("Arq_puerta_dintel", Vector3(0, 2.04, PR / 2 + 0.02), Vector3(1.1, 0.1, 0.12), BLANCO); esf("Obj_picaporte", Vector3(0.34, 1.0, PR / 2 + 0.06), 0.035, Color(0.7, 0.7, 0.72))
	caja("Arq_escalon_1", Vector3(0, 0.08, PR / 2 + 0.45), Vector3(1.5, 0.16, 0.7), Color(0.62, 0.6, 0.56)); caja("Arq_escalon_2", Vector3(0, 0.04, PR / 2 + 0.9), Vector3(1.7, 0.08, 0.4), Color(0.66, 0.64, 0.6))
	# ventanas con marco, cruz, postigos y cantero con flores
	for s in [-1, 1]:
		var cx: float = s * 1.45
		caja("Vidrio_ventana_%d" % s, Vector3(cx, 1.45, PR / 2), Vector3(0.9, 1.1, 0.02), Color(0.8, 0.92, 1.0), Vector3.ZERO, 0.35)
		caja("Arq_ventana_dintel_%d" % s, Vector3(cx, 2.0, PR / 2 + 0.04), Vector3(1.06, 0.08, 0.1), BLANCO); caja("Arq_ventana_alfeizar_%d" % s, Vector3(cx, 0.9, PR / 2 + 0.06), Vector3(1.06, 0.07, 0.14), BLANCO)
		caja("Arq_ventana_marco_izq_%d" % s, Vector3(cx - 0.49, 1.45, PR / 2 + 0.04), Vector3(0.07, 1.16, 0.1), BLANCO); caja("Arq_ventana_marco_der_%d" % s, Vector3(cx + 0.49, 1.45, PR / 2 + 0.04), Vector3(0.07, 1.16, 0.1), BLANCO)
		caja("Arq_ventana_cruz_v_%d" % s, Vector3(cx, 1.45, PR / 2 + 0.03), Vector3(0.04, 1.1, 0.06), BLANCO); caja("Arq_ventana_cruz_h_%d" % s, Vector3(cx, 1.45, PR / 2 + 0.03), Vector3(0.9, 0.04, 0.06), BLANCO)
		caja("Arq_postigo_a_%d" % s, Vector3(cx - 0.68, 1.45, PR / 2 + 0.05), Vector3(0.42, 1.14, 0.04), Color(0.2, 0.45, 0.42)); caja("Arq_postigo_b_%d" % s, Vector3(cx + 0.68, 1.45, PR / 2 + 0.05), Vector3(0.42, 1.14, 0.04), Color(0.2, 0.45, 0.42))
		caja("Obj_cantero_%d" % s, Vector3(cx, 0.72, PR / 2 + 0.28), Vector3(1.1, 0.2, 0.26), MADC)
		for k in 9:
			var fx: float = cx - 0.45 + 0.11 * k
			cil("Veg_cantero_tallo_%d_%d" % [s, k], Vector3(fx, 0.96, PR / 2 + 0.28), 0.006, 0.006, 0.22, Color(0.2, 0.5, 0.2), Vector3.ZERO, 6)
			esf("Veg_cantero_flor_%d_%d" % [s, k], Vector3(fx, 1.08, PR / 2 + 0.28), 0.055, [Color(0.9, 0.3, 0.45), Color(0.95, 0.8, 0.2), Color(0.6, 0.45, 0.85), Color(0.97, 0.97, 0.95)][(k + s) % 4], Vector3(1, 0.6, 1), 10)
	# interior: alfombra, mesa servida, sillas, estante, lámparas
	caja("Obj_alfombra", Vector3(-0.1, 0.09, 0.2), Vector3(2.2, 0.02, 1.6), Color(0.6, 0.2, 0.18))
	caja("Obj_mesa_tapa", Vector3(-0.1, 0.76, 0.2), Vector3(1.3, 0.05, 0.8), MADC)
	for dx in [-0.58, 0.58]:
		for dz in [-0.33, 0.33]: caja("Obj_mesa_pata", Vector3(-0.1 + dx, 0.37, 0.2 + dz), Vector3(0.06, 0.74, 0.06), MAD)
	for k in 2:
		var cz: float = -0.5 if k == 0 else 0.9
		caja("Obj_silla_asiento_%d" % k, Vector3(-0.1, 0.46, cz + 0.2), Vector3(0.42, 0.05, 0.42), MAD); caja("Obj_silla_respaldo_%d" % k, Vector3(-0.1, 0.8, cz + 0.2 + (0.2 if k == 0 else -0.2)), Vector3(0.42, 0.5, 0.04), MAD)
		for dx in [-0.18, 0.18]:
			for dz in [-0.18, 0.18]: caja("Obj_silla_pata_%d" % k, Vector3(-0.1 + dx, 0.22, cz + 0.2 + dz), Vector3(0.04, 0.44, 0.04), MAD)
	cil("Obj_florero", Vector3(-0.1, 0.9, 0.2), 0.06, 0.07, 0.24, Color(0.95, 0.95, 0.92))
	for k in 7:
		var a := TAU * k / 7.0; esf("Veg_florero_flor_%d" % k, Vector3(-0.1 + 0.07 * cos(a), 1.08 + 0.03 * (k % 2), 0.2 + 0.07 * sin(a)), 0.05, [Color(0.9, 0.3, 0.45), Color(0.95, 0.8, 0.2), Color(0.6, 0.45, 0.85)][k % 3], Vector3(1, 0.6, 1), 10)
	cil("Obj_tetera", Vector3(0.22, 0.84, 0.05), 0.07, 0.07, 0.12, Color(0.95, 0.95, 0.92)); cil("Obj_taza_1", Vector3(-0.4, 0.81, 0.0), 0.04, 0.04, 0.07, Color(0.95, 0.95, 0.92)); cil("Obj_taza_2", Vector3(-0.4, 0.81, 0.42), 0.04, 0.04, 0.07, Color(0.95, 0.95, 0.92))
	cil("Obj_plato_1", Vector3(-0.1, 0.79, -0.1), 0.12, 0.12, 0.015, Color(0.95, 0.95, 0.92)); cil("Obj_plato_2", Vector3(-0.1, 0.79, 0.5), 0.12, 0.12, 0.015, Color(0.95, 0.95, 0.92))
	cil("Obj_vela", Vector3(0.35, 0.84, 0.4), 0.02, 0.02, 0.1, Color(0.96, 0.95, 0.9))
	caja("Obj_estante_1", Vector3(-1.8, 1.5, -1.7), Vector3(0.7, 0.05, 0.28), MAD); caja("Obj_estante_2", Vector3(-1.8, 1.05, -1.7), Vector3(0.7, 0.05, 0.28), MAD)
	for k in 4: caja("Obj_libro_%d" % k, Vector3(-2.0 + 0.1 * k, 1.55 + 0.05, -1.7), Vector3(0.07, 0.1, 0.2), [Color(0.6, 0.2, 0.2), Color(0.2, 0.3, 0.5), Color(0.7, 0.6, 0.2), Color(0.2, 0.45, 0.3)][k])
	cil("Obj_lampara_colgante", Vector3(-0.1, 2.05, 0.2), 0.22, 0.22, 0.2, Color(0.95, 0.85, 0.6)); cil("Obj_lampara_cable", Vector3(-0.1, 2.35, 0.2), 0.008, 0.008, 0.5, Color(0.3, 0.3, 0.3), Vector3.ZERO, 6)
	cil("Obj_lampara_pie_poste", Vector3(1.9, 0.7, -1.3), 0.02, 0.02, 1.4, Color(0.3, 0.3, 0.3), Vector3.ZERO, 8); cil("Obj_lampara_pie_pantalla", Vector3(1.9, 1.5, -1.3), 0.12, 0.17, 0.26, Color(0.95, 0.85, 0.6))
	caja("Obj_cuadro", Vector3(0.6, 1.6, -PR / 2 + 0.1), Vector3(0.8, 0.6, 0.03), BLANCO); caja("Obj_cuadro_tela", Vector3(0.6, 1.6, -PR / 2 + 0.12), Vector3(0.68, 0.48, 0.02), Color(0.3, 0.5, 0.65))
	# fuera: farol del porche y guirnalda
	cil("Obj_farol_porche", Vector3(0.8, 1.75, PR / 2 + 0.12), 0.06, 0.06, 0.18, Color(0.95, 0.85, 0.6))
	for k in 13: esf("Obj_guirnalda_%d" % k, Vector3(-2.3 + 4.6 * k / 12.0, 2.36 - 0.14 * sin(PI * (k % 6) / 6.0), PR / 2 + 0.5), 0.035, Color(0.95, 0.9, 0.7), Vector3.ONE, 8)

func _exterior() -> void:
	caja("Arq_suelo", Vector3(0, -0.05, 20), Vector3(120, 0.1, 120), Color(0.30, 0.52, 0.2))
	caja("Arq_camino", Vector3(0, 0.012, 7.2), Vector3(1.3, 0.02, 7.2), Color(0.7, 0.66, 0.58)); caja("Arq_camino_entrada", Vector3(0, 0.014, 3.1), Vector3(1.8, 0.02, 1.0), Color(0.7, 0.66, 0.58))
	# colinas
	for i in 4:
		var s := esf("Arq_colina_%d" % i, Vector3(-20 + i * 14, -1.0, -34 - i * 6), 1.0, Color(0.34, 0.55, 0.24), Vector3(24, 9 + i * 2, 14), 24)
	# pinos (conos apilados) y árboles de hoja ancha
	for i in 26:
		var p := Vector3(rng.randf_range(-32, 32), 0, rng.randf_range(-40, -8)); var h := rng.randf_range(5.5, 9.5)
		cil("Veg_pino_tronco_%d" % i, p + Vector3(0, h * 0.15, 0), 0.12, 0.18, h * 0.3, Color(0.35, 0.22, 0.12), Vector3.ZERO, 8)
		for k in 4: cil("Veg_pino_copa_%d_%d" % [i, k], p + Vector3(0, h * (0.3 + 0.16 * k), 0), 0.02, h * (0.2 - 0.035 * k), h * 0.28, Color(0.14, 0.40, 0.2), Vector3.ZERO, 14)
	for k in 4:
		var q: Vector3 = [Vector3(-4.6, 0, 0.5), Vector3(4.2, 0, 3.2), Vector3(-5.4, 0, -4.0), Vector3(1.8, 0, -7.0)][k]; var h2: float = [3.8, 3.2, 4.4, 4.6][k]
		cil("Veg_arbol_tronco_%d" % k, q + Vector3(0, h2 * 0.3, 0), 0.12, 0.17, h2 * 0.6, Color(0.4, 0.27, 0.15), Vector3.ZERO, 10)
		esf("Veg_arbol_copa_%d_0" % k, q + Vector3(0, h2 * 0.78, 0), h2 * 0.32, Color(0.25, 0.55, 0.2), Vector3(1, 0.85, 1), 14)
		esf("Veg_arbol_copa_%d_1" % k, q + Vector3(h2 * 0.18, h2 * 0.64, 0.1), h2 * 0.22, Color(0.28, 0.58, 0.22), Vector3.ONE, 12); esf("Veg_arbol_copa_%d_2" % k, q + Vector3(-h2 * 0.18, h2 * 0.66, -0.1), h2 * 0.23, Color(0.22, 0.5, 0.18), Vector3.ONE, 12)
	for k in 22:
		var x := rng.randf_range(-9, 9); var z := rng.randf_range(-6, 6)
		if absf(x) < 3.0 and z > 2.0: continue
		if x > 3.4 and z < 4.0: continue
		esf("Veg_arbusto_%d" % k, Vector3(x, 0.28, z), rng.randf_range(0.35, 0.7), Color(0.2, 0.5, 0.18), Vector3(1, 0.7, 1), 12)
	# flores del primer plano y valla
	var cols := [Color(0.9, 0.3, 0.45), Color(0.95, 0.8, 0.2), Color(0.6, 0.45, 0.85), Color(0.97, 0.97, 0.95), Color(0.95, 0.55, 0.15)]
	for k in 90:
		var x := (1.0 if rng.randf() < 0.5 else -1.0) * rng.randf_range(1.0, 3.6); var z := rng.randf_range(5.0, 9.0); var h := rng.randf_range(0.25, 0.5)
		cil("Veg_flor_tallo_%d" % k, Vector3(x, h / 2, z), 0.006, 0.006, h, Color(0.2, 0.5, 0.2), Vector3.ZERO, 6); esf("Veg_flor_%d" % k, Vector3(x, h, z), rng.randf_range(0.04, 0.065), cols[k % 5], Vector3(1, 0.55, 1), 10)
	for k in 30:
		var x := -6.2 + 0.4 * k
		if absf(x) > 0.9: caja("Obj_valla_poste_%d" % k, Vector3(x, 0.3, 10.6), Vector3(0.07, 0.6, 0.07), Color(0.93, 0.93, 0.9))
	caja("Obj_valla_riel_a", Vector3(-3.8, 0.45, 10.6), Vector3(5.0, 0.06, 0.04), Color(0.93, 0.93, 0.9)); caja("Obj_valla_riel_b", Vector3(3.8, 0.45, 10.6), Vector3(5.0, 0.06, 0.04), Color(0.93, 0.93, 0.9))
	for k in 4:
		var p := Vector3([-1.3, 1.3, -1.3, 1.3][k], 0, [5.4, 5.4, 8.0, 8.0][k]); cil("Obj_farol_%d" % k, p + Vector3(0, 0.25, 0), 0.02, 0.02, 0.5, Color(0.3, 0.3, 0.32), Vector3.ZERO, 8); esf("Obj_farol_luz_%d" % k, p + Vector3(0, 0.55, 0), 0.06, Color(0.95, 0.9, 0.7), Vector3.ONE, 10)
	# garaje y auto
	var GX := 4.7; var GZ := -0.4
	caja("Arq_garaje", Vector3(GX, 1.2, GZ), Vector3(3.4, 2.4, 4.2), Color(0.66, 0.68, 0.7)); caja("Arq_garaje_techo", Vector3(GX, 2.5, GZ), Vector3(3.7, 0.15, 4.5), Color(0.5, 0.22, 0.16))
	caja("Arq_garaje_porton", Vector3(GX - 0.1, 1.05, GZ + 2.12), Vector3(2.5, 2.1, 0.06), Color(0.8, 0.82, 0.84))
	for k in 7: caja("Arq_garaje_nervio_%d" % k, Vector3(GX - 0.1, 0.15 + 0.3 * k, GZ + 2.17), Vector3(2.5, 0.04, 0.03), Color(0.6, 0.62, 0.64))
	caja("Arq_garaje_marco", Vector3(GX - 0.1, 2.15, GZ + 2.14), Vector3(2.7, 0.1, 0.1), Color(0.93, 0.93, 0.9)); caja("Vidrio_garaje", Vector3(GX + 1.72, 1.4, GZ + 0.8), Vector3(0.04, 0.6, 0.8), Color(0.8, 0.92, 1.0), Vector3.ZERO, 0.35)
	var carro := Node3D.new(); carro.name = "Auto"; esc.add_child(carro); var modelo: Node3D = (load("res://assets/hustler.glb") as PackedScene).instantiate(); carro.add_child(modelo); modelo.rotation.y = PI
	carro.position = Vector3(-2.3, 0.0, 3.2); carro.rotation.y = deg_to_rad(-22)

func _initialize() -> void:
	_montar(OS.get_cmdline_user_args())
func _montar(a: PackedStringArray) -> void:
	await process_frame
	esc = Node3D.new(); esc.name = "Escena"; root.add_child(esc); rng.seed = 5
	var luz := DirectionalLight3D.new(); luz.rotation_degrees = Vector3(-35, 30, 0); luz.light_energy = 1.1; root.add_child(luz)
	var wenv := WorldEnvironment.new(); var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.8, 0.85, 0.92); env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.8, 0.8, 0.85); wenv.environment = env; root.add_child(wenv)
	_casa(); _exterior()
	var cam := Camera3D.new(); cam.name = "Cam_principal"; cam.fov = 46.0; cam.near = 0.05; cam.far = 300.0; esc.add_child(cam); cam.position = Vector3(2.7, 2.3, 15.2); cam.look_at(Vector3(0.0, 1.9, 0.0), Vector3.UP); cam.current = true
	for i in 4: await process_frame
	root.get_viewport().get_texture().get_image().save_png(a[0] + "_godot.png")
	var doc := GLTFDocument.new(); var st := GLTFState.new(); doc.append_from_scene(esc, st)
	print("GLB ", a[0], ".glb err=", doc.write_to_filesystem(st, a[0] + ".glb"))
	quit()
