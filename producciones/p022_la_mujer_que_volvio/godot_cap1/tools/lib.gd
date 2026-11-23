## Ayudas para armar piezas y la nave. Convención de TODAS las piezas: origen en el piso, el FRENTE mira hacia −Z (como la cámara de Godot).
extends RefCounted

static func mat(col: Color, metal := 0.0, rough := 0.6, emi := Color(0, 0, 0), ee := 0.0, alfa := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(col.r, col.g, col.b, alfa)
	m.metallic = metal
	m.roughness = rough
	if ee > 0.0:
		m.emission_enabled = true
		m.emission = emi
		m.emission_energy_multiplier = ee
	if alfa < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return m

static func mat_tex(ruta: String, ee := 1.6, brillo := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	var t = load(ruta)
	m.albedo_color = Color(0.02, 0.02, 0.03)
	m.emission_enabled = true
	m.emission_texture = t
	m.emission_operator = BaseMaterial3D.EMISSION_OP_MULTIPLY
	m.emission = Color(brillo, brillo, brillo)
	m.emission_energy_multiplier = ee
	m.roughness = 0.3
	return m

static func mat_muro(ruta: String, col: Color, escala := Vector3(1, 1, 1)) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_texture = load(ruta)
	m.albedo_color = col
	m.uv1_scale = escala
	m.roughness = 0.55
	m.metallic = 0.35
	return m

static func nodo(p: Node, nom: String, pos := Vector3.ZERO, rot_deg := Vector3.ZERO) -> Node3D:
	var n := Node3D.new()
	n.name = nom
	n.position = pos
	n.rotation_degrees = rot_deg
	p.add_child(n)
	return n

static func caja(p: Node, nom: String, pos: Vector3, tam: Vector3, m: Material, rot_deg := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = tam
	mi.mesh = b
	mi.material_override = m
	mi.name = nom
	mi.position = pos
	mi.rotation_degrees = rot_deg
	p.add_child(mi)
	return mi

static func cil(p: Node, nom: String, pos: Vector3, radio: float, alto: float, m: Material, rot_deg := Vector3.ZERO, seg := 32) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = radio
	c.bottom_radius = radio
	c.height = alto
	c.radial_segments = seg
	mi.mesh = c
	mi.material_override = m
	mi.name = nom
	mi.position = pos
	mi.rotation_degrees = rot_deg
	p.add_child(mi)
	return mi

static func esf(p: Node, nom: String, pos: Vector3, radio: float, m: Material, esc := Vector3.ONE) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = radio
	s.height = radio * 2.0
	s.radial_segments = 32
	s.rings = 16
	mi.mesh = s
	mi.material_override = m
	mi.name = nom
	mi.position = pos
	mi.scale = esc
	p.add_child(mi)
	return mi

static func toro(p: Node, nom: String, pos: Vector3, r_int: float, r_ext: float, m: Material, rot_deg := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var t := TorusMesh.new()
	t.inner_radius = r_int
	t.outer_radius = r_ext
	t.rings = 48
	t.ring_segments = 12
	mi.mesh = t
	mi.material_override = m
	mi.name = nom
	mi.position = pos
	mi.rotation_degrees = rot_deg
	p.add_child(mi)
	return mi

## Pantalla plana que mira hacia −Z (frente de la pieza).
static func pantalla(p: Node, nom: String, pos: Vector3, w: float, h: float, m: Material, rot_deg := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(w, h)
	mi.mesh = q
	mi.material_override = m
	mi.name = nom
	mi.position = pos
	mi.rotation_degrees = Vector3(rot_deg.x, rot_deg.y + 180.0, rot_deg.z)
	p.add_child(mi)
	return mi

static func luz(p: Node, nom: String, pos: Vector3, col: Color, energia: float, rango: float, tipo := "omni") -> Light3D:
	var l: Light3D
	if tipo == "spot":
		l = SpotLight3D.new()
		l.spot_range = rango
		l.spot_angle = 60.0
	else:
		l = OmniLight3D.new()
		l.omni_range = rango
	l.light_color = col
	l.light_energy = energia
	l.name = nom
	l.position = pos
	p.add_child(l)
	return l

static func dueno(n: Node, o: Node) -> void:
	for c in n.get_children():
		c.owner = o
		dueno(c, o)

static func guardar_pieza(n: Node3D, ruta: String) -> void:
	dueno(n, n)
	var ps := PackedScene.new()
	ps.pack(n)
	var e := ResourceSaver.save(ps, ruta)
	if e != OK:
		push_error("no se pudo guardar " + ruta)

## Caja con UV en METROS DEL MUNDO (viajan en el GLB): u = coordenada horizontal / tile, v = 1 − altura / tile en las caras verticales (el zócalo queda abajo).
static func caja_uv(p: Node, nom: String, pos: Vector3, tam: Vector3, m: Material, tile := 3.2) -> MeshInstance3D:
	var h := tam / 2.0
	var caras := [
		[Vector3(0, 0, -1), Vector3(-1, 0, 0), Vector3(0, 1, 0)],   # normal, eje u (en mundo), eje v (arriba)
		[Vector3(0, 0, 1), Vector3(1, 0, 0), Vector3(0, 1, 0)],
		[Vector3(1, 0, 0), Vector3(0, 0, -1), Vector3(0, 1, 0)],
		[Vector3(-1, 0, 0), Vector3(0, 0, 1), Vector3(0, 1, 0)],
		[Vector3(0, 1, 0), Vector3(1, 0, 0), Vector3(0, 0, 1)],
		[Vector3(0, -1, 0), Vector3(1, 0, 0), Vector3(0, 0, -1)]]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for c in caras:
		var n: Vector3 = c[0]
		var eu: Vector3 = c[1]
		var ev: Vector3 = c[2]
		var cen := n * h
		var su := absf(eu.x * h.x + eu.y * h.y + eu.z * h.z)
		var sv := absf(ev.x * h.x + ev.y * h.y + ev.z * h.z)
		var esq := [[-1, -1], [1, -1], [1, 1], [-1, 1]]
		var vs := []
		for e in esq:
			var q: Vector3 = cen + eu * su * e[0] + ev * sv * e[1]
			var w := q + pos
			var uv: Vector2
			if absf(n.y) > 0.5:
				uv = Vector2(w.x / tile, w.z / tile)
			elif absf(n.x) > 0.5:
				uv = Vector2(w.z / tile, 1.0 - w.y / tile)
			else:
				uv = Vector2(w.x / tile, 1.0 - w.y / tile)
			vs.append([q, uv])
		for idx in [0, 2, 1, 0, 3, 2]:
			st.set_normal(n)
			st.set_uv(vs[idx][1])
			st.add_vertex(vs[idx][0])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = m
	mi.name = nom
	mi.position = pos
	p.add_child(mi)
	return mi
