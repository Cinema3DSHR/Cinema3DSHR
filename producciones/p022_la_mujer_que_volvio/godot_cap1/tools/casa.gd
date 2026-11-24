## LA CASA (cap. 1): el presente, unas horas antes de que Elena le dispare. Sala antigua, elegante y oscura, con ventanal y tormenta. Gabriel, herido, sentado en un sillón,
## mira hacia la ventana; sangre goteando de su brazo, el hombro herido; sobre la mesa: botellas, copa, botella tumbada con el líquido derramado, cenicero con un cigarro encendido, pistola.
## Todo lo visual (materiales, curtains, lluvia, humo, relámpagos, gotas) lo agrega Blender. Aquí: geometría con nombres que Blender reconoce, animación de Gabriel y cámaras (vertical 540×960).
## Uso: xvfb-run -a godot --path . --rendering-driver opengl3 --resolution 540x960 --script res://tools/casa.gd -- SALIDA [sin_glb]
extends SceneTree
const FPS := 30.0
const DUR := 78.0
var esc: Node3D
var anim: Animation
var ap: AnimationPlayer
var G: Actor3
var RG: RigSentado
var total := 0
const ALTO := 3.3
const SILLON := Vector3(-0.35, 0.0, -0.20)           # centro del asiento (suelo)
const MESA_C := Vector3(1.55, 0.0, -0.85)          # la tapa empieza en x=0.40: libre del brazo derecho del sillón (borde en x=0.25)
const MESA_Y := 0.76

# ───────── geometría ─────────
func _mat(c := Color(0.5, 0.5, 0.5)) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = c; m.roughness = 0.7; return m

func _caja(nom: String, pos: Vector3, tam: Vector3, col := Color(0.4, 0.4, 0.4), rot_deg := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var b := BoxMesh.new(); b.size = tam; mi.mesh = b; mi.material_override = _mat(col); mi.name = nom; mi.position = pos; mi.rotation_degrees = rot_deg; esc.add_child(mi); return mi

func _torneado(nom: String, pos: Vector3, perfil: Array, seg := 40, col := Color(0.2, 0.2, 0.2), rot_deg := Vector3.ZERO) -> MeshInstance3D:
	# superficie de revolución: perfil = [Vector2(radio, altura)], de abajo hacia arriba
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in seg:
		var a0 := TAU * i / seg; var a1 := TAU * (i + 1) / seg
		for j in perfil.size() - 1:
			var p0: Vector2 = perfil[j]; var p1: Vector2 = perfil[j + 1]
			var v00 := Vector3(p0.x * cos(a0), p0.y, p0.x * sin(a0)); var v01 := Vector3(p0.x * cos(a1), p0.y, p0.x * sin(a1))
			var v10 := Vector3(p1.x * cos(a0), p1.y, p1.x * sin(a0)); var v11 := Vector3(p1.x * cos(a1), p1.y, p1.x * sin(a1))
			for v in [v00, v10, v11, v00, v11, v01]:
				st.add_vertex(v)
	st.generate_normals()
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = _mat(col); mi.name = nom; mi.position = pos; mi.rotation_degrees = rot_deg; esc.add_child(mi); return mi

func _lamina(nom: String, pos: Vector3, ancho: float, alto: float, nx := 10, ny := 28, col := Color(0.3, 0.1, 0.1)) -> MeshInstance3D:
	# lámina vertical subdividida (cortinas): Blender la deforma con el viento
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in nx:
		for j in ny:
			var x0 := ancho * i / nx - ancho * 0.5; var x1 := ancho * (i + 1) / nx - ancho * 0.5; var y0 := alto * j / ny; var y1 := alto * (j + 1) / ny
			for v in [Vector3(x0, y0, 0), Vector3(x1, y0, 0), Vector3(x1, y1, 0), Vector3(x0, y0, 0), Vector3(x1, y1, 0), Vector3(x0, y1, 0)]:
				st.add_vertex(v)
	st.generate_normals()
	var mi := MeshInstance3D.new(); mi.mesh = st.commit(); mi.material_override = _mat(col); mi.name = nom; mi.position = pos; esc.add_child(mi); return mi

func _construir_sala() -> void:
	_caja("Piso_madera", Vector3(0, -0.05, 0), Vector3(7.4, 0.1, 9.4), Color(0.18, 0.11, 0.07))
	_caja("Techo", Vector3(0, ALTO + 0.05, 0), Vector3(7.4, 0.1, 9.4), Color(0.5, 0.5, 0.5))
	_caja("Pared_este", Vector3(3.7, ALTO * 0.5, 0), Vector3(0.2, ALTO, 9.4), Color(0.3, 0.25, 0.2))
	_caja("Pared_oeste", Vector3(-3.7, ALTO * 0.5, 0), Vector3(0.2, ALTO, 9.4), Color(0.3, 0.25, 0.2))
	_caja("Pared_sur", Vector3(0, ALTO * 0.5, 4.7), Vector3(7.4, ALTO, 0.2), Color(0.3, 0.25, 0.2))
	# pared del ventanal (norte): pilares entre 3 ventanas altas, dintel y antepecho
	for i in 4:
		_caja("Pared_norte_pilar_%d" % i, Vector3(-2.7 + i * 1.8, ALTO * 0.5, -4.7), Vector3(0.5 if i in [1, 2] else 1.3 if i == 0 or i == 3 else 0.5, ALTO, 0.25), Color(0.3, 0.25, 0.2))
	_caja("Pared_norte_dintel", Vector3(0, 2.95, -4.7), Vector3(7.4, 0.7, 0.25), Color(0.3, 0.25, 0.2))
	_caja("Pared_norte_antepecho", Vector3(0, 0.3, -4.7), Vector3(7.4, 0.6, 0.25), Color(0.3, 0.25, 0.2))
	for k in 3:                                                                   # tres ventanas con cruces de madera
		var cx := -1.8 + k * 1.8
		_caja("Marco_ventana_%d_v" % k, Vector3(cx, 1.6, -4.68), Vector3(0.05, 2.3, 0.07), Color(0.12, 0.08, 0.05))
		_caja("Marco_ventana_%d_h" % k, Vector3(cx, 1.9, -4.68), Vector3(1.4, 0.05, 0.07), Color(0.12, 0.08, 0.05))
		_caja("Marco_ventana_%d_l" % k, Vector3(cx - 0.7, 1.6, -4.68), Vector3(0.07, 2.4, 0.09), Color(0.12, 0.08, 0.05))
		_caja("Marco_ventana_%d_r" % k, Vector3(cx + 0.7, 1.6, -4.68), Vector3(0.07, 2.4, 0.09), Color(0.12, 0.08, 0.05))
		_caja("Vidrio_ventana_%d" % k, Vector3(cx, 1.6, -4.72), Vector3(1.38, 2.38, 0.01), Color(0.2, 0.25, 0.3))
	# cortinas: dos paños largos a los costados del ventanal central (Blender los mueve con el viento)
	for lado in [-1, 1]:
		_lamina("Cortina_%s" % ("L" if lado < 0 else "R"), Vector3(lado * 1.55, 0.05, -4.45), 1.15, 3.1, 12, 30, Color(0.35, 0.08, 0.1))
	_caja("Cortinero", Vector3(0, 3.18, -4.45), Vector3(4.6, 0.04, 0.04), Color(0.08, 0.06, 0.05))
	# sillón con almohadones y respaldo (Blender los redondea con bisel)
	var s := SILLON
	_caja("Tela_sillon_base", s + Vector3(0, 0.22, 0), Vector3(0.95, 0.30, 0.90), Color(0.15, 0.06, 0.05))
	_caja("Tela_sillon_asiento", s + Vector3(0, 0.40, -0.02), Vector3(0.66, 0.14, 0.62), Color(0.2, 0.08, 0.06))
	_caja("Tela_sillon_respaldo", s + Vector3(0, 0.75, 0.38), Vector3(0.92, 0.72, 0.22), Color(0.17, 0.07, 0.06), Vector3(-8, 0, 0))
	_caja("Tela_sillon_brazo_L", s + Vector3(-0.50, 0.50, 0.0), Vector3(0.20, 0.30, 0.86), Color(0.17, 0.07, 0.06))
	_caja("Tela_sillon_brazo_R", s + Vector3(0.50, 0.50, 0.0), Vector3(0.20, 0.30, 0.86), Color(0.17, 0.07, 0.06))
	for dx in [-0.42, 0.42]:
		for dz in [-0.38, 0.36]:
			_caja("Madera_sillon_pata", s + Vector3(dx, 0.04, dz), Vector3(0.07, 0.10, 0.07), Color(0.08, 0.05, 0.03))
	# mesa larga y vacía (madera oscura), con faldón y patas torneadas
	var m := MESA_C
	_caja("Madera_mesa_tapa", m + Vector3(0, MESA_Y - 0.03, 0), Vector3(2.3, 0.06, 0.95), Color(0.12, 0.07, 0.04))
	_caja("Madera_mesa_faldon", m + Vector3(0, MESA_Y - 0.11, 0), Vector3(2.1, 0.10, 0.80), Color(0.1, 0.06, 0.04))
	for dx in [-0.98, 0.98]:
		for dz in [-0.38, 0.38]:
			_torneado("Madera_mesa_pata", m + Vector3(dx, 0, dz), [Vector2(0.025, 0.0), Vector2(0.045, 0.1), Vector2(0.03, 0.3), Vector2(0.055, 0.45), Vector2(0.035, 0.6), Vector2(0.05, MESA_Y - 0.1)], 14, Color(0.1, 0.06, 0.04))
	# lámpara de pie (pantalla cálida; la luz real la pone Blender), aparador con botellas, biblioteca, alfombra
	_torneado("Lampara_pie", Vector3(-1.75, 0, -1.9), [Vector2(0.18, 0.0), Vector2(0.18, 0.03), Vector2(0.03, 0.06), Vector2(0.025, 1.45)], 20, Color(0.1, 0.08, 0.05))
	_torneado("Lampara_pantalla", Vector3(-1.75, 1.45, -1.9), [Vector2(0.17, 0.0), Vector2(0.24, 0.30), Vector2(0.22, 0.32)], 24, Color(0.9, 0.75, 0.5))
	_caja("Madera_aparador", Vector3(3.2, 0.45, 1.5), Vector3(0.5, 0.9, 2.2), Color(0.1, 0.06, 0.04))
	_caja("Madera_biblioteca", Vector3(-3.45, 1.2, 1.0), Vector3(0.3, 2.4, 3.0), Color(0.1, 0.06, 0.04))
	_caja("Tela_alfombra", Vector3(0, 0.012, -0.5), Vector3(4.2, 0.02, 3.2), Color(0.18, 0.07, 0.06))

func _construir_mesa() -> void:
	var m := MESA_C; var y := MESA_Y
	# botella de whisky de pie (cuello largo, hombros, base gruesa) + etiqueta
	var perf_b := [Vector2(0.0, 0.0), Vector2(0.036, 0.0), Vector2(0.040, 0.02), Vector2(0.040, 0.17), Vector2(0.036, 0.20), Vector2(0.018, 0.25), Vector2(0.016, 0.30), Vector2(0.019, 0.305), Vector2(0.018, 0.31)]
	_torneado("Botella_whisky_vidrio", m + Vector3(-0.55, y, -0.15), perf_b, 36, Color(0.1, 0.07, 0.03))
	_torneado("Botella_whisky_liquido", m + Vector3(-0.55, y + 0.01, -0.15), [Vector2(0.0, 0.0), Vector2(0.034, 0.0), Vector2(0.037, 0.02), Vector2(0.037, 0.12), Vector2(0.0, 0.12)], 30, Color(0.4, 0.2, 0.05))
	_caja("Botella_etiqueta", m + Vector3(-0.55, y + 0.10, -0.15 + 0.041), Vector3(0.05, 0.07, 0.002), Color(0.8, 0.75, 0.6))
	# copa con vino: pie, tallo y cáliz + vino adentro
	var perf_c := [Vector2(0.0, 0.0), Vector2(0.040, 0.0), Vector2(0.041, 0.004), Vector2(0.006, 0.012), Vector2(0.005, 0.07), Vector2(0.012, 0.085), Vector2(0.040, 0.11), Vector2(0.050, 0.145), Vector2(0.048, 0.185), Vector2(0.040, 0.20)]
	_torneado("Copa_vidrio", m + Vector3(-0.15, y, -0.28), perf_c, 36, Color(0.7, 0.8, 0.85))
	_torneado("Copa_vino", m + Vector3(-0.15, y + 0.002, -0.28), [Vector2(0.0, 0.10), Vector2(0.035, 0.115), Vector2(0.047, 0.15), Vector2(0.0, 0.151)], 28, Color(0.25, 0.01, 0.03))
	# botella tumbada (vacía casi): acostada sobre la mesa, el cuello cuelga del borde; charco de vino sobre la tapa que gotea
	_torneado("Botella_vino_vidrio", m + Vector3(0.62, y + 0.045, -0.12), perf_b, 36, Color(0.05, 0.08, 0.04), Vector3(0, 0, -90))
	_caja("Botella_vino_etiqueta", m + Vector3(0.50, y + 0.075, -0.12), Vector3(0.07, 0.003, 0.05), Color(0.8, 0.75, 0.6))
	_torneado("Liquido_derramado", m + Vector3(0.84, y + 0.002, -0.12), [Vector2(0.0, 0.0), Vector2(0.19, 0.0), Vector2(0.22, 0.003), Vector2(0.0, 0.004)], 36, Color(0.3, 0.01, 0.03))        # charco irregular lo deforma Blender
	_caja("Liquido_hilo", m + Vector3(1.00, y + 0.0015, -0.14), Vector3(0.30, 0.003, 0.03), Color(0.3, 0.01, 0.03))                                                                    # hilo que corre hacia el borde de la mesa
	# cenicero de cristal con cigarros consumidos y uno ENCENDIDO
	_torneado("Cenicero", m + Vector3(0.05, y, 0.17), [Vector2(0.0, 0.0), Vector2(0.055, 0.0), Vector2(0.065, 0.012), Vector2(0.075, 0.03), Vector2(0.07, 0.034), Vector2(0.045, 0.02), Vector2(0.0, 0.018)], 40, Color(0.6, 0.65, 0.7))
	for k in 5:
		_torneado("Colilla_%d" % k, m + Vector3(0.05 + (k - 2) * 0.016, y + 0.024, 0.17 + (k % 2) * 0.02 - 0.01), [Vector2(0.0, 0.0), Vector2(0.004, 0.0), Vector2(0.004, 0.032), Vector2(0.0, 0.032)], 10, Color(0.75, 0.7, 0.6), Vector3(78, 20 * k, 0))
	_torneado("Cigarro_encendido", m + Vector3(0.05, y + 0.052, 0.20), [Vector2(0.0, 0.0), Vector2(0.0042, 0.0), Vector2(0.0042, 0.085), Vector2(0.0, 0.085)], 12, Color(0.92, 0.9, 0.82), Vector3(0, 0, -22))
	_torneado("Cigarro_filtro", m + Vector3(0.05 - 0.008, y + 0.039, 0.20), [Vector2(0.0, 0.0), Vector2(0.0043, 0.0), Vector2(0.0043, 0.02), Vector2(0.0, 0.02)], 12, Color(0.7, 0.45, 0.2), Vector3(0, 0, -22))
	_torneado("Cigarro_brasa", m + Vector3(0.05 + 0.040, y + 0.0805, 0.20), [Vector2(0.0, 0.0), Vector2(0.0044, 0.0), Vector2(0.0044, 0.007), Vector2(0.0, 0.007)], 12, Color(1.0, 0.3, 0.05), Vector3(0, 0, -22))
	_torneado("Cigarro_ceniza", m + Vector3(0.05 + 0.047, y + 0.0855, 0.20), [Vector2(0.0, 0.0), Vector2(0.0042, 0.0), Vector2(0.0040, 0.012), Vector2(0.0, 0.012)], 12, Color(0.35, 0.35, 0.36), Vector3(0, 0, -31))   # ceniza real: columna que se curva
	_caja("Encendedor", m + Vector3(-0.08, y + 0.007, 0.33), Vector3(0.055, 0.014, 0.03), Color(0.7, 0.62, 0.3), Vector3(0, 25, 0))
	# pistola USP real (modelo detallado del catálogo, 2090 triángulos) apoyada de lado sobre la mesa y apuntando hacia el sillón
	var ps: PackedScene = load("res://assets/pistola_USP.glb")
	var pis: Node3D = ps.instantiate(); pis.name = "Usp"; esc.add_child(pis)
	var nme := 0
	for n in pis.find_children("*", "MeshInstance3D", true, false):
		n.name = "Pistola_%d" % nme; nme += 1
	pis.rotation_degrees = Vector3(0, -112, 90)                                  # de costado (rollo 90° sobre el eje del caño), caño hacia −x
	pis.position = m + Vector3(-0.55, 0.0, 0.18)
	await process_frame
	var mn := 1e9
	for n in pis.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D; var ab := mi.global_transform * mi.get_aabb(); mn = minf(mn, ab.position.y)
	pis.position.y += (y - mn) + 0.0004                                          # apoyada exactamente sobre la tapa
	# aparador: más botellas (se ven al fondo)
	for k in 4:
		_torneado("Botella_aparador_%d" % k, Vector3(3.2, 0.9, 0.9 + k * 0.25), perf_b, 24, Color(0.1, 0.08, 0.05))

# ───────── cámaras ─────────
func _tomas() -> Array:
	return [
		{"id": "h1", "camara": "H1_establecimiento", "t0": 0.0, "t1": 11.0, "pos": [3.3, 1.60, 3.9], "pos_fin": [2.6, 1.40, 2.7], "mira": [0.1, 1.0, -1.3], "mira_fin": [0.3, 0.95, -1.1], "fov": 54.0, "mano": 0.004},
		{"id": "h2", "camara": "H2_mesa_detalle", "t0": 11.0, "t1": 20.5, "pos": [3.0, 1.25, 0.6], "pos_fin": [2.0, 1.05, -0.05], "mira": [1.6, 0.80, -0.8], "mira_fin": [1.0, 0.79, -0.67], "fov": 30.0, "mano": 0.002},
		{"id": "h3", "camara": "H3_ventanal_tormenta", "t0": 20.5, "t1": 29.5, "pos": [-0.2, 1.45, 1.9], "pos_fin": [-0.1, 1.5, 0.6], "mira": [0.0, 1.55, -4.5], "mira_fin": [0.0, 1.65, -4.5], "fov": 48.0, "mano": 0.003},
		{"id": "h4", "camara": "H4_gabriel_medio", "t0": 29.5, "t1": 43.0, "pos": [0.95, 1.30, -2.5], "pos_fin": [0.55, 1.28, -1.9], "mira": [-0.35, 1.0, -0.2], "mira_fin": [-0.35, 1.05, -0.2], "fov": 38.0, "mano": 0.003},
		{"id": "h5", "camara": "H5_gotas_suelo", "t0": 43.0, "t1": 51.0, "pos": [-1.85, 0.55, -1.95], "pos_fin": [-1.60, 0.38, -1.75], "mira": [-0.80, 0.45, -0.72], "mira_fin": [-0.80, 0.36, -0.72], "fov": 46.0, "mano": 0.0},
		{"id": "h6", "camara": "H6_hombro_herido", "t0": 51.0, "t1": 59.0, "pos": [-1.35, 1.38, -1.25], "pos_fin": [-1.05, 1.32, -0.95], "mira": [-0.55, 1.12, -0.15], "mira_fin": [-0.55, 1.12, -0.15], "fov": 34.0, "mano": 0.002},
		{"id": "h7", "camara": "H7_rostro", "t0": 59.0, "t1": 69.0, "pos": [0.55, 1.22, -1.15], "pos_fin": [0.30, 1.20, -0.85], "mira": [-0.35, 1.15, -0.2], "mira_fin": [-0.35, 1.15, -0.2], "fov": 28.0, "mano": 0.002},
		{"id": "h8", "camara": "H8_alejamiento_final", "t0": 69.0, "t1": 78.0, "pos": [0.30, 1.20, -0.85], "pos_fin": [2.7, 1.55, 3.4], "mira": [-0.35, 1.15, -0.2], "mira_fin": [0.0, 1.0, -1.5], "fov": 40.0, "mano": 0.0}]

func _initialize() -> void:
	_montar(OS.get_cmdline_user_args())

func _suave(a: float, b: float, x: float) -> float:
	var u := clampf((x - a) / (b - a), 0.0, 1.0); return u * u * (3.0 - 2.0 * u)

func _pista(n: Node, pos := true, rot := true) -> Array:
	var p := esc.get_path_to(n); var r := [-1, -1]
	if pos: r[0] = anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(r[0], p)
	if rot: r[1] = anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(r[1], p)
	return r

func _montar(a: PackedStringArray) -> void:
	await process_frame
	esc = Node3D.new(); esc.name = "Escena"; root.add_child(esc)
	# luz SÓLO para las fotos de control de Godot (cuelga de root, no de la escena: no se exporta; la iluminación real es de Blender)
	var luz := OmniLight3D.new(); luz.position = Vector3(0.3, 2.8, 1.0); luz.omni_range = 14.0; luz.light_energy = 2.2; root.add_child(luz)
	var wenv := WorldEnvironment.new(); var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.03, 0.04, 0.07); env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.5, 0.5, 0.6); env.ambient_light_energy = 0.7; wenv.environment = env; root.add_child(wenv)
	total = int(ceil(DUR * FPS)) + 1
	anim = Animation.new(); anim.length = float(total - 1) / FPS; anim.step = 1.0 / FPS; anim.loop_mode = Animation.LOOP_NONE
	ap = AnimationPlayer.new(); ap.name = "Anim"; esc.add_child(ap)
	_construir_sala(); await _construir_mesa()
	G = Actor3.new(); G.cargar("gabriel", "res://assets/aiden_noir.glb", "res://assets/aiden_meta.json", esc)
	G.raiz.position = SILLON + Vector3(0, 0.0, 0.05); G.raiz.rotation.y = PI
	await process_frame
	RG = RigSentado.new(G.sk, G.raiz)
	var goteo := Node3D.new(); goteo.name = "Goteo_origen"; esc.add_child(goteo)
	var p_goteo := _pista(goteo, true, false)
	var p_sk := {}
	for h in G.sk.get_bone_count():
		var tq := anim.add_track(Animation.TYPE_ROTATION_3D); anim.track_set_path(tq, NodePath("%s:%s" % [esc.get_path_to(G.sk), G.sk.get_bone_name(h)])); p_sk[h] = tq
	var th := anim.add_track(Animation.TYPE_POSITION_3D); anim.track_set_path(th, NodePath("%s:%s" % [esc.get_path_to(G.sk), G.sk.get_bone_name(G.hueso_cadera)])); p_sk["pos"] = th
	var tomas := _tomas(); var cams := {}; var p_cam := {}
	for tm in tomas:
		var c := Camera3D.new(); c.name = tm["camara"]; c.fov = tm["fov"]; c.near = 0.04; c.far = 120.0; esc.add_child(c); cams[tm["id"]] = c; p_cam[tm["id"]] = _pista(c)
	var inv := G.raiz.global_transform.affine_inverse()
	for g in total:
		var t := float(g) / FPS
		var resp := sin(t * 2.0 * PI / 4.6) * 0.5 + 0.5                          # respiración lenta (≈ 13 por minuto)
		var dolor := 0.5 + 0.5 * sin(t * 0.7)
		var hip := Vector3(0, 0.45 + 0.002 * resp, 0.0)
		# mano izquierda del personaje (+x local → −x del mundo): cuelga al costado del sillón; la derecha reposa sobre el muslo
		var man_i: Vector3 = inv * Vector3(SILLON.x - 0.45, 0.74, SILLON.z - 0.42)
		var man_d: Vector3 = inv * Vector3(SILLON.x + 0.23, 0.55, SILLON.z - 0.16)
		var head := hip + Vector3(0.015, 0.575 + 0.003 * resp - 0.02 * dolor, 0.07 + 0.01 * dolor)
		RG.pose({"hips": hip, "head": head, "roll": 0.10 + 0.02 * sin(t * 0.4), "look": -0.12 + 0.05 * sin(t * 0.23), "look_y": -0.10 + 0.04 * sin(t * 0.31) + (0.10 if (t > 28.0 and t < 33.5) else 0.0), "grip": 0.4,
			"hands": [{"side": "Left", "wrist": man_i, "fdir": Vector3(0.0, -1, -0.35).normalized(), "back": Vector3(1, 0.2, 0), "pole": Vector3(0.7, -0.4, -0.6)},
					  {"side": "Right", "wrist": man_d, "fdir": Vector3(0, -0.15, 1).normalized(), "back": Vector3(0, 1, 0), "pole": Vector3(0.5, -0.5, -0.3)}],
			"feet": [{"side": "Left", "pos": Vector3(0.13, 0.04, 0.42)}, {"side": "Right", "pos": Vector3(-0.10, 0.04, 0.46)}], "lean0": -0.02, "lean1": 0.22})
		for h in G.sk.get_bone_count(): anim.rotation_track_insert_key(p_sk[h], t, G.sk.get_bone_pose_rotation(h))
		anim.position_track_insert_key(p_sk["pos"], t, G.sk.get_bone_pose_position(G.hueso_cadera))
		# origen del goteo: punta de los dedos de la mano que cuelga (posición real de la mano en el mundo)
		var mano_w: Vector3 = G.sk.global_transform * G.sk.get_bone_global_pose(G.mano["L"]).origin
		goteo.global_position = mano_w + Vector3(0, -0.19, -0.05); anim.position_track_insert_key(p_goteo[0], t, goteo.position)
		for tm in tomas:
			var c: Camera3D = cams[tm["id"]]
			var u := clampf((t - tm["t0"]) / maxf(tm["t1"] - tm["t0"], 0.001), 0.0, 1.0); var e := smoothstep(0.0, 1.0, u)
			var pa: Array = tm["pos"]; var pb: Array = tm["pos_fin"]; var ma: Array = tm["mira"]; var mb: Array = tm["mira_fin"]
			c.global_position = Vector3(pa[0], pa[1], pa[2]).lerp(Vector3(pb[0], pb[1], pb[2]), e)
			c.look_at(Vector3(ma[0], ma[1], ma[2]).lerp(Vector3(mb[0], mb[1], mb[2]), e), Vector3.UP)
			var amp: float = tm["mano"]
			if amp > 0.0: c.position += Vector3(sin(t * 0.6), sin(t * 0.8 + 1.0), 0) * amp
			anim.position_track_insert_key(p_cam[tm["id"]][0], t, c.global_position); anim.rotation_track_insert_key(p_cam[tm["id"]][1], t, c.global_transform.basis.get_rotation_quaternion())
	var lib := AnimationLibrary.new(); lib.add_animation("escena", anim); ap.add_animation_library("", lib); ap.assigned_animation = "escena"
	var pre: String = a[0]
	for tm in tomas:
		(cams[tm["id"]] as Camera3D).current = true; ap.seek((float(tm["t0"]) + float(tm["t1"])) * 0.5, true)
		for i in 4: await process_frame
		root.get_viewport().get_texture().get_image().save_png("%s_%s.png" % [pre, tm["id"]])
	if a.size() > 1 and a[1] == "sin_glb":
		print("SIN_GLB"); quit(); return
	ap.seek(0.0, true)
	var doc := GLTFDocument.new(); var st := GLTFState.new(); doc.append_from_scene(esc, st)
	print("GLB ", pre, ".glb err=", doc.write_to_filesystem(st, pre + ".glb"))
	var cj := []
	for tm in tomas:
		cj.append({"id": tm["id"], "camara": tm["camara"], "inicio_s": tm["t0"], "fin_s": tm["t1"], "frame_inicio": int(tm["t0"] * FPS) + 1, "frame_fin": int(minf(tm["t1"] * FPS, total - 1)) + 1, "lente_mm": 12.0 / tan(deg_to_rad(tm["fov"]) / 2.0)})
	var js := {"formato": "estudio.previa_godot/1", "produccion": "p022_la_mujer_que_volvio", "escena_id": "casa", "version": 1, "titulo": "La casa (el presente)", "fps": int(FPS), "frames": total, "duracion_s": float(total - 1) / FPS,
		"resolucion": [540, 960], "animacion": "escena", "actores": [{"id": "gabriel", "nodo": "gabriel", "modelo": "aiden"}], "tomas": cj,
		"eventos": {"relampagos_s": [3.5, 9.0, 16.5, 24.0, 31.5, 39.0, 47.5, 56.0, 63.5, 72.0], "gota_sangre_cada_s": 1.9, "gota_vino_cada_s": 1.35, "mesa_centro": [MESA_C.x, MESA_C.y, MESA_C.z], "mesa_altura": MESA_Y, "sillon": [SILLON.x, SILLON.y, SILLON.z]},
		"efectos_blender": ["lluvia en el ventanal", "cortinas movidas por el viento", "relámpagos", "luz baja cálida de la lámpara", "humo de cigarrillo", "brasa y ceniza", "vino derramado que gotea", "sangre que gotea del brazo", "mancha en el hombro", "polvo en el aire", "materiales reales"],
		"tiempo": {"pelicula": "t = (cuadro − 1) / fps"}}
	var fa := FileAccess.open(pre + ".json", FileAccess.WRITE); fa.store_string(JSON.stringify(js, "  ")); fa.close()
	quit()
