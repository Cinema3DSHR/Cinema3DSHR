## ETAPA 2 — Materiales (PBR estándar, lo que el GLB sabe llevar) y luces: neones arquitectónicos, colgantes,
## ventilador, velador, hogar, farolas, luna y el relámpago (energía 0: la anima la etapa 3). Ambiente nocturno.
class_name E2Materiales
extends RefCounted

static func _m(color: Color, rugosidad := 0.6, metal := 0.0, emision := Color.BLACK, intensidad := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = rugosidad
	m.metallic = metal
	if intensidad > 0.0:
		m.emission_enabled = true
		m.emission = emision
		m.emission_energy_multiplier = intensidad
	return m

static func materiales() -> Dictionary:
	var d := {
		"piso_madera": _m(Color("6b4a32"), 0.45),
		"techo": _m(Color("e8e4dc"), 0.9),
		"pared": _m(Color("d9d3c7"), 0.85),
		"metal_negro": _m(Color("141414"), 0.4, 0.8),
		"mueble_blanco": _m(Color("eeeeea"), 0.35),
		"mueble_madera": _m(Color("8a5a36"), 0.5),
		"marmol": _m(Color("f2f0ec"), 0.15),
		"azulejo": _m(Color("2f5a63"), 0.2),
		"acero": _m(Color("b8bcc0"), 0.25, 1.0),
		"vidrio_negro": _m(Color("050505"), 0.05, 0.2),
		"cuero": _m(Color("5a3420"), 0.55),
		"luz_calida": _m(Color("ffd9a0"), 0.5, 0.0, Color("ffc46b"), 6.0),
		"ceramica": _m(Color("e6dccd"), 0.3),
		"fruta_naranja": _m(Color("e2701c"), 0.45),
		"fruta_verde": _m(Color("7aa53a"), 0.45),
		"madera_clara": _m(Color("c49a6c"), 0.55),
		"vidrio_verde": _m(Color(0.15, 0.4, 0.2, 0.6), 0.05),
		"vidrio_ambar": _m(Color(0.55, 0.3, 0.08, 0.6), 0.05),
		"hoja": _m(Color("2f6b2a"), 0.7),
		"madera_oscura": _m(Color("3b2618"), 0.45),
		"tela_gris": _m(Color("8b8b88"), 0.95),
		"flor": _m(Color("d23c6e"), 0.7),
		"alfombra": _m(Color("8c7a66"), 1.0),
		"tela_azul": _m(Color("2c4a6e"), 0.95),
		"tela_naranja": _m(Color("c4632a"), 0.95),
		"cera": _m(Color("f3ead8"), 0.6),
		"pantalla_tela": _m(Color("efe2c8"), 0.9, 0.0, Color("ffcf8a"), 1.5),
		"metal_bronce": _m(Color("8a6a3e"), 0.35, 1.0),
		"vidrio_opalino": _m(Color("fff4e0"), 0.4, 0.0, Color("ffe7bd"), 5.0),
		"vidrio": _m(Color(0.75, 0.85, 0.9, 0.12), 0.02),
		"piedra": _m(Color("6f6a63"), 0.9),
		"piedra_oscura": _m(Color("3c3a37"), 0.8),
		"hollin": _m(Color("0c0b0a"), 1.0),
		"leña": _m(Color("4a3020"), 0.9),
		"brasa": _m(Color("ff4a10"), 0.8, 0.0, Color("ff3c00"), 8.0),
		"cuadro": _m(Color("3d5560"), 0.6),
		"vereda_mojada": _m(Color("3a3a3c"), 0.12),
		"cordon": _m(Color("55555a"), 0.3),
		"asfalto_mojado": _m(Color("161618"), 0.06),
		"pintura_vial": _m(Color("d8d2b0"), 0.2),
		"metal_poste": _m(Color("1e2226"), 0.35, 0.9),
		"luz_farola": _m(Color("ffd08a"), 0.5, 0.0, Color("ffc070"), 12.0),
		"edificio": _m(Color("1a1d24"), 0.8),
		"ventana_lejana": _m(Color("ffcf7a"), 0.5, 0.0, Color("ffb85c"), 3.0),
		"cerros": _m(Color("0b0e14"), 1.0),
		"cielo_tormenta": _m(Color("1b2333"), 1.0, 0.0, Color("161d2b"), 1.0),
		"rayo": _m(Color("e8f0ff"), 0.5, 0.0, Color("cfe0ff"), 40.0),
		"goma": _m(Color("111111"), 0.8),
		"llanta": _m(Color("2a2a2c"), 0.3, 1.0),
		"neon_cian": _m(Color("40f0ff"), 0.5, 0.0, Color("30e8ff"), 10.0),
		"neon_magenta": _m(Color("ff3ad0"), 0.5, 0.0, Color("ff2ac8"), 10.0),
		"led_calido": _m(Color("ffd9a0"), 0.5, 0.0, Color("ffcf8a"), 6.0),
	}
	for k in ["vidrio", "vidrio_verde", "vidrio_ambar"]:
		d[k].transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	d["cielo_tormenta"].cull_mode = BaseMaterial3D.CULL_DISABLED
	for k in d:
		d[k].resource_name = k
	return d

static func aplicar(raiz: Node3D) -> void:
	_neones(raiz)
	var mats := materiales()
	var faltan := {}
	for n in raiz.find_children("*", "MeshInstance3D", true, false):
		if n.has_meta("mat"):
			var k: String = n.get_meta("mat")
			if mats.has(k):
				(n.mesh as PrimitiveMesh).material = mats[k]
			else:
				faltan[k] = true
	if faltan:
		push_error("materiales que faltan: %s" % [faltan.keys()])
	_luces(raiz)
	_ambiente(raiz)

static func _neones(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Neones")
	Kit.caja(g, "Neon_cocina", Vector3(5.6, 0.03, 0.03), Vector3(9.1, 2.93, -3.86), "neon_cian")
	Kit.caja(g, "Neon_isla", Vector3(2.3, 0.02, 0.02), Vector3(8.9, 0.06, -0.62), "neon_cian")
	Kit.caja(g, "Led_bajo_alacena", Vector3(3.1, 0.015, 0.03), Vector3(8.4, 1.68, -3.56), "led_calido")
	Kit.caja(g, "Neon_living", Vector3(6.0, 0.03, 0.03), Vector3(3.0, 2.93, -3.86), "neon_magenta")
	Kit.caja(g, "Neon_techo_frente", Vector3(22.0, 0.03, 0.03), Vector3(0.5, 2.93, 3.96), "neon_cian")
	Kit.caja(g, "Neon_hogar_izq", Vector3(0.03, 2.6, 0.03), Vector3(-10.2, 1.4, -3.86), "neon_magenta")
	Kit.caja(g, "Neon_hogar_der", Vector3(0.03, 2.6, 0.03), Vector3(-7.0, 1.4, -3.86), "neon_magenta")

static func _omni(padre: Node3D, nombre: String, pos: Vector3, color: Color, energia: float, rango: float, sombra := false) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.name = nombre
	l.position = pos
	l.light_color = color
	l.light_energy = energia
	l.omni_range = rango
	l.shadow_enabled = sombra
	padre.add_child(l)
	return l

static func _luces(raiz: Node3D) -> void:
	var g := Kit.grupo(raiz, "Luces")
	_omni(g, "Luz_neon_cocina", Vector3(9.1, 2.6, -3.3), Color("40e8ff"), 0.7, 4.5)
	_omni(g, "Luz_neon_living", Vector3(3.0, 2.6, -3.3), Color("ff40d0"), 0.55, 4.5)
	_omni(g, "Luz_neon_hogar", Vector3(-8.6, 2.2, -3.2), Color("ff40d0"), 0.35, 3.5)
	_omni(g, "Luz_neon_frente", Vector3(0.5, 2.7, 3.5), Color("40e8ff"), 0.3, 8.0)
	for i in 3:
		_omni(g, "Luz_colgante_%d" % i, Vector3(8.1 + i * 0.8, 1.75, -1.1), Color("ffc87a"), 0.9, 3.0)
	_omni(g, "Luz_ventilador", Vector3(1.6, 2.25, -1.0), Color("ffe2b0"), 1.3, 6.0, true)
	_omni(g, "Luz_velador", Vector3(4.4, 0.95, -3.4), Color("ffc27a"), 0.8, 3.0)
	_omni(g, "Luz_fuego", Vector3(-8.6, 0.55, -3.3), Color("ff7a2a"), 2.0, 6.0, true)
	for i in 4:
		var f: Node3D = raiz.get_node("Exterior/Farola_%d" % i)
		var s := SpotLight3D.new()
		s.name = "Luz_farola_%d" % i
		s.position = f.position + Vector3(0, 4.38, -1.1)
		s.rotation_degrees = Vector3(-90, 0, 0)
		s.light_color = Color("ffbf6a")
		s.light_energy = 9.0
		s.spot_range = 9.0
		s.spot_angle = 55.0
		s.shadow_enabled = true
		g.add_child(s)
	var luna := DirectionalLight3D.new()
	luna.name = "Luz_luna"
	luna.rotation_degrees = Vector3(-35, 160, 0)
	luna.light_color = Color("5a6e9a")
	luna.light_energy = 0.12
	g.add_child(luna)
	var rel := DirectionalLight3D.new()
	rel.name = "Relampago_luz"
	rel.rotation_degrees = Vector3(-50, 170, 0)     # viene de atrás de los edificios hacia la casa
	rel.light_color = Color("cfdcff")
	rel.light_energy = 0.0
	rel.shadow_enabled = true
	g.add_child(rel)
	# destello del cielo: plano luminoso detrás de los edificios (escala 0 fuera de los destellos)
	var cielo := Kit.caja(g, "Relampago_cielo", Vector3(220, 60, 0.2), Vector3(0, 25, -95), "rayo")
	cielo.mesh.material = _m(Color("7f94c6"), 1.0, 0.0, Color("6f86c0"), 1.2)
	cielo.mesh.material.resource_name = "relampago_cielo"
	cielo.scale = Vector3(1, 1, 1) * 0.001
	raiz.get_node("Exterior/Relampago_rayo").scale = Vector3.ONE * 0.001

static func _ambiente(raiz: Node3D) -> void:
	var we := WorldEnvironment.new()
	we.name = "Ambiente"
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("0a0d14")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color("2a3346")
	e.ambient_light_energy = 0.35
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	e.glow_enabled = true
	e.glow_intensity = 0.8
	e.glow_bloom = 0.1
	we.environment = e
	raiz.add_child(we)
