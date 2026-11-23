## Piezas nuevas (v2): alimentos, jardín y estructura de nave. Frente hacia −Z, origen en el piso.
extends RefCounted
const L = preload("res://tools/lib.gd")
const P := "res://assets/pantallas/"

static func heladera_vidrio() -> Node3D:
	var r := Node3D.new()
	r.name = "heladera_vidrio"
	var acero := L.mat(Color(0.62, 0.66, 0.72), 0.85, 0.28)
	var oscuro := L.mat(Color(0.07, 0.08, 0.10), 0.6, 0.35)
	var vidrio := L.mat(Color(0.75, 0.9, 1.0), 0.0, 0.04, Color(0, 0, 0), 0.0, 0.14)
	var luz := L.mat(Color(0.8, 0.95, 1.0), 0, 0.3, Color(0.75, 0.92, 1.0), 2.6)
	var rng := RandomNumberGenerator.new()
	rng.seed = 31
	L.caja(r, "Zocalo", Vector3(0, 0.11, 0.0), Vector3(1.5, 0.22, 0.9), oscuro)
	L.caja(r, "Fondo", Vector3(0, 1.4, 0.4), Vector3(1.5, 2.4, 0.08), luz)
	L.caja(r, "Techo", Vector3(0, 2.6, 0), Vector3(1.5, 0.12, 0.9), acero)
	for s in [-1, 1]:
		L.caja(r, "Lateral", Vector3(s * 0.72, 1.4, 0), Vector3(0.06, 2.4, 0.9), acero)
	L.caja(r, "VidrioFrente", Vector3(0, 1.4, -0.43), Vector3(1.4, 2.35, 0.03), vidrio)
	L.caja(r, "MarcoCentro", Vector3(0, 1.4, -0.445), Vector3(0.04, 2.35, 0.05), acero)
	L.caja(r, "LuzSuperior", Vector3(0, 2.5, -0.3), Vector3(1.3, 0.03, 0.06), luz)
	for i in 5:
		var y := 0.45 + i * 0.5
		L.caja(r, "Estante%d" % i, Vector3(0, y, 0.02), Vector3(1.38, 0.025, 0.74), L.mat(Color(0.8, 0.85, 0.9), 0.7, 0.2, Color(0.5, 0.7, 0.9), 0.3, 0.8))
		for j in 6:
			var tipo := rng.randi() % 3
			var c := Color.from_hsv(rng.randf(), rng.randf_range(0.4, 0.85), rng.randf_range(0.6, 0.95))
			var x := -0.58 + j * 0.23
			if tipo == 0:
				L.cil(r, "Lata%d_%d" % [i, j], Vector3(x, y + 0.1, rng.randf_range(-0.2, 0.15)), 0.045, 0.2, L.mat(c, 0.6, 0.3), Vector3.ZERO, 14)
			elif tipo == 1:
				L.caja(r, "Caja%d_%d" % [i, j], Vector3(x, y + 0.11, rng.randf_range(-0.2, 0.15)), Vector3(0.17, 0.2, 0.2), L.mat(c, 0.0, 0.7))
			else:
				L.caja(r, "Bandeja%d_%d" % [i, j], Vector3(x, y + 0.04, rng.randf_range(-0.2, 0.15)), Vector3(0.2, 0.05, 0.28), L.mat(Color(0.95, 0.95, 0.97), 0.0, 0.5))
	L.caja(r, "Tirador", Vector3(0.06, 1.4, -0.47), Vector3(0.02, 0.7, 0.03), acero)
	L.caja(r, "Tirador2", Vector3(-0.06, 1.4, -0.47), Vector3(0.02, 0.7, 0.03), acero)
	L.caja(r, "Indicador", Vector3(0.55, 2.52, -0.45), Vector3(0.12, 0.05, 0.01), L.mat(Color(0.1, 1.0, 0.6), 0, 0.3, Color(0.1, 1.0, 0.6), 3.0))
	return r

static func expendedora() -> Node3D:
	var r := Node3D.new()
	r.name = "expendedora"
	var cuerpo := L.mat(Color(0.12, 0.15, 0.20), 0.7, 0.3)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.6)
	L.caja(r, "Cuerpo", Vector3(0, 0.95, 0), Vector3(0.95, 1.9, 0.78), cuerpo)
	L.pantalla(r, "Frente", Vector3(0, 1.06, -0.392), 0.84, 1.26, L.mat_tex(P + "expendedora.png", 1.25))
	L.caja(r, "Bandeja", Vector3(-0.2, 0.28, -0.40), Vector3(0.4, 0.14, 0.04), L.mat(Color(0.02, 0.02, 0.03), 0.3, 0.4))
	L.caja(r, "LuzSuperior", Vector3(0, 1.88, -0.395), Vector3(0.9, 0.03, 0.01), luz)
	L.caja(r, "LuzBase", Vector3(0, 0.04, -0.395), Vector3(0.9, 0.02, 0.01), luz)
	return r

static func estanteria_alimentos() -> Node3D:
	## Depósito de alimentos NO perecederos: estantería de acero con cajas, latas, bolsas y contenedores etiquetados.
	var r := Node3D.new()
	r.name = "estanteria_alimentos"
	var acero := L.mat(Color(0.35, 0.38, 0.44), 0.8, 0.35)
	var rng := RandomNumberGenerator.new()
	rng.seed = 77
	for x in [-0.8, 0.8]:
		L.caja(r, "Montante", Vector3(x, 1.1, 0), Vector3(0.05, 2.2, 0.5), acero)
	for i in 5:
		var y := 0.1 + i * 0.5
		L.caja(r, "Estante%d" % i, Vector3(0, y, 0), Vector3(1.64, 0.04, 0.52), acero)
		for j in 4:
			var tipo := rng.randi() % 4
			var c := Color.from_hsv(rng.randf_range(0.0, 1.0), rng.randf_range(0.35, 0.75), rng.randf_range(0.55, 0.9))
			var x := -0.6 + j * 0.4
			if tipo == 0:
				for k in 3:
					L.cil(r, "Lata%d_%d_%d" % [i, j, k], Vector3(x - 0.09 + k * 0.09, y + 0.09, rng.randf_range(-0.1, 0.1)), 0.04, 0.16, L.mat(c, 0.6, 0.3), Vector3.ZERO, 12)
			elif tipo == 1:
				L.caja(r, "Caja%d_%d" % [i, j], Vector3(x, y + 0.17, 0), Vector3(0.34, 0.3, 0.4), L.mat(Color(0.65, 0.5, 0.32), 0.0, 0.85))
				L.caja(r, "Etiqueta%d_%d" % [i, j], Vector3(x, y + 0.17, -0.205), Vector3(0.22, 0.12, 0.005), L.mat(Color(0.95, 0.95, 0.95), 0, 0.5, Color(0.9, 0.95, 1.0), 0.4))
			elif tipo == 2:
				L.esf(r, "Bolsa%d_%d" % [i, j], Vector3(x, y + 0.14, 0), 0.16, L.mat(Color(0.85, 0.82, 0.7), 0, 0.9), Vector3(1.2, 0.9, 1.1))
			else:
				L.caja(r, "Contenedor%d_%d" % [i, j], Vector3(x, y + 0.14, 0), Vector3(0.34, 0.24, 0.4), L.mat(Color(0.2, 0.45, 0.6), 0.1, 0.5, Color(0.1, 0.3, 0.5), 0.3))
	return r

static func jardinera(largo := 2.4) -> Node3D:
	var r := Node3D.new()
	r.name = "jardinera"
	var acero := L.mat(Color(0.20, 0.23, 0.28), 0.75, 0.3)
	var luz := L.mat(Color(0.5, 1.0, 0.8), 0, 0.3, Color(0.5, 1.0, 0.8), 2.4)
	L.caja(r, "Cuerpo", Vector3(0, 0.3, 0), Vector3(largo, 0.6, 0.8), acero)
	L.caja(r, "Sustrato", Vector3(0, 0.61, 0), Vector3(largo - 0.1, 0.04, 0.7), L.mat(Color(0.16, 0.10, 0.06), 0, 0.95))
	L.caja(r, "LuzBorde", Vector3(0, 0.55, -0.405), Vector3(largo - 0.2, 0.015, 0.01), luz)
	for s in [-1, 1]:
		L.caja(r, "Pata", Vector3(s * (largo / 2 - 0.1), 0.04, 0), Vector3(0.1, 0.08, 0.7), L.mat(Color(0.1, 0.11, 0.14), 0.6, 0.4))
	return r

const SHADER_AGUA := """
shader_type spatial;
render_mode cull_disabled;
uniform vec4 color : source_color = vec4(0.05, 0.45, 0.6, 0.78);
uniform float velocidad = 1.0;
float ola(vec2 p, float t) {
	return sin(p.x * 5.0 + t * 1.6) * 0.5 + sin(p.y * 7.0 - t * 1.2) * 0.35 + sin((p.x + p.y) * 9.0 + t * 2.1) * 0.25;
}
void vertex() {
	VERTEX.y += ola(VERTEX.xz, TIME * velocidad) * 0.012;
}
void fragment() {
	vec2 p = UV * 24.0;
	float h = ola(p, TIME * velocidad);
	float e = 0.02;
	vec3 n = normalize(vec3(-(ola(p + vec2(e, 0.0), TIME * velocidad) - h) / e * 0.08, 1.0, -(ola(p + vec2(0.0, e), TIME * velocidad) - h) / e * 0.08));
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	ALBEDO = color.rgb + vec3(0.04) * h;
	ALPHA = color.a;
	ROUGHNESS = 0.04;
	SPECULAR = 0.9;
	METALLIC = 0.1;
	EMISSION = color.rgb * 0.35 + vec3(0.05, 0.15, 0.2) * (h * 0.5 + 0.5);
}
"""

static func canal_agua(largo := 16.0) -> Node3D:
	var r := Node3D.new()
	r.name = "canal_agua"
	var acero := L.mat(Color(0.16, 0.18, 0.22), 0.7, 0.35)
	var luz := L.mat(Color(0.3, 0.9, 1.0), 0, 0.3, Color(0.3, 0.9, 1.0), 2.4)
	L.caja(r, "Fondo", Vector3(0, 0.04, 0), Vector3(largo, 0.08, 1.0), acero)
	for s in [-1, 1]:
		L.caja(r, "Borde", Vector3(0, 0.22, s * 0.53), Vector3(largo, 0.44, 0.1), acero)
		L.caja(r, "BordeLuz", Vector3(0, 0.45, s * 0.53), Vector3(largo, 0.01, 0.03), luz)
	var piedras := RandomNumberGenerator.new()
	piedras.seed = 3
	for i in 40:
		L.esf(r, "Piedra%d" % i, Vector3(piedras.randf_range(-largo / 2, largo / 2), 0.1, piedras.randf_range(-0.4, 0.4)), piedras.randf_range(0.04, 0.09), L.mat(Color(0.35, 0.36, 0.38), 0.1, 0.9), Vector3(1.2, 0.6, 1.0))
	var agua := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(largo, 0.9)
	pm.subdivide_width = int(largo * 6)
	pm.subdivide_depth = 6
	agua.mesh = pm
	var sh := Shader.new()
	sh.code = SHADER_AGUA
	var sm := ShaderMaterial.new()
	sm.shader = sh
	agua.material_override = sm
	agua.position = Vector3(0, 0.3, 0)
	agua.name = "Agua"
	r.add_child(agua)
	L.caja(r, "LuzSumergida", Vector3(0, 0.1, 0), Vector3(largo - 1.0, 0.01, 0.04), luz)
	return r

static func rack_servidores() -> Node3D:
	var r := Node3D.new()
	r.name = "rack_servidores"
	var cuerpo := L.mat(Color(0.09, 0.11, 0.14), 0.75, 0.3)
	L.caja(r, "Cuerpo", Vector3(0, 1.05, 0), Vector3(0.75, 2.1, 0.65), cuerpo)
	L.pantalla(r, "Frente", Vector3(0, 1.1, -0.331), 0.66, 1.7, L.mat_tex(P + "botonera.png", 1.6))
	L.caja(r, "Rejilla", Vector3(0, 0.12, -0.331), Vector3(0.66, 0.16, 0.005), L.mat(Color(0.03, 0.04, 0.05), 0.5, 0.5))
	L.caja(r, "LuzTope", Vector3(0, 2.07, -0.33), Vector3(0.6, 0.02, 0.01), L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.6))
	return r

static func costilla() -> Node3D:
	## Cuaderna estructural adosada al muro (nave, no casa): columna biselada con vena de luz y bulones.
	var r := Node3D.new()
	r.name = "costilla"
	var acero := L.mat(Color(0.12, 0.14, 0.18), 0.8, 0.3)
	var luz := L.mat(Color(0.1, 0.8, 1.0), 0, 0.3, Color(0.1, 0.8, 1.0), 2.4)
	L.caja(r, "Columna", Vector3(0, 1.6, -0.12), Vector3(0.22, 3.2, 0.24), acero)
	L.caja(r, "Vena", Vector3(0, 1.6, -0.245), Vector3(0.03, 2.8, 0.01), luz)
	for y in [0.4, 1.2, 2.0, 2.8]:
		L.cil(r, "Bulon", Vector3(0.07, y, -0.25), 0.015, 0.02, L.mat(Color(0.5, 0.52, 0.58), 0.9, 0.3), Vector3(90, 0, 0), 10)
		L.cil(r, "Bulon2", Vector3(-0.07, y, -0.25), 0.015, 0.02, L.mat(Color(0.5, 0.52, 0.58), 0.9, 0.3), Vector3(90, 0, 0), 10)
	return r

static func caja_electrica() -> Node3D:
	var r := Node3D.new()
	r.name = "caja_electrica"
	L.caja(r, "Cuerpo", Vector3(0, 0, 0), Vector3(0.5, 0.7, 0.1), L.mat(Color(0.14, 0.16, 0.2), 0.7, 0.35))
	L.caja(r, "Panel", Vector3(0, 0.06, -0.052), Vector3(0.42, 0.4, 0.005), L.mat(Color(0.05, 0.06, 0.08), 0.5, 0.4))
	for i in 5:
		var c: Color = [Color(0.1, 1, 0.5), Color(1, 0.7, 0.1), Color(0.1, 0.8, 1), Color(1, 0.2, 0.2), Color(0.1, 1, 0.5)][i]
		L.caja(r, "Led%d" % i, Vector3(-0.15 + i * 0.075, 0.2, -0.056), Vector3(0.03, 0.03, 0.01), L.mat(c, 0, 0.3, c, 3.0))
	L.caja(r, "Manija", Vector3(0, -0.24, -0.06), Vector3(0.2, 0.04, 0.03), L.mat(Color(0.6, 0.62, 0.68), 0.9, 0.3))
	return r

static func umbral() -> Node3D:
	var r := Node3D.new()
	r.name = "umbral"
	var m := StandardMaterial3D.new()
	m.albedo_texture = load(P + "franja_peligro.png")
	m.roughness = 0.6
	m.uv1_scale = Vector3(5, 1, 1)
	L.caja(r, "Franja", Vector3(0, 0.012, 0), Vector3(1.5, 0.024, 0.4), m)
	return r
