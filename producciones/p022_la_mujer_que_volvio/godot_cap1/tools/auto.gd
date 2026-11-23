## Auto «hustler» listo para la escena: frente hacia −Z (el GLB original mira a +Z), carrocería NEGRA brillante con barniz, cromados espejados,
## vidrios oscuros y piezas accesibles por nombre. `dano.gd` lo destruye para el accidente.
extends RefCounted
const RUTA := "res://assets/hustler.glb"
const PINTURA := ["remap_kuzov", "nodamage_lod0"]   # materiales de carrocería (el original viene claro)
const CROMO := ["Color_A3A3A3", "Color_C5C5C5", "Color_808080", "ssr_mk1"]

static func crear() -> Node3D:
	var raiz := Node3D.new(); raiz.name = "Auto"
	var g: Node3D = load(RUTA).instantiate()
	g.name = "Modelo"; g.rotation_degrees = Vector3(0, 180, 0)
	raiz.add_child(g)
	pintar(g)
	return raiz

static func _mat_pintura(m: Material) -> StandardMaterial3D:
	var nm := (m.duplicate() as StandardMaterial3D)
	nm.albedo_color = Color(0.008, 0.008, 0.010); nm.albedo_texture = null; nm.normal_enabled = false
	nm.metallic = 0.92; nm.metallic_specular = 0.9; nm.roughness = 0.10
	nm.clearcoat_enabled = true; nm.clearcoat = 1.0; nm.clearcoat_roughness = 0.03
	return nm

static func _mat_cromo(m: Material) -> StandardMaterial3D:
	var nm := (m.duplicate() as StandardMaterial3D)
	nm.albedo_color = Color(0.82, 0.84, 0.88); nm.albedo_texture = null
	nm.metallic = 1.0; nm.roughness = 0.07
	return nm

static func pintar(n: Node) -> void:
	for c in n.get_children():
		var mi := c as MeshInstance3D
		if mi and mi.mesh:
			for i in mi.mesh.get_surface_count():
				var m := mi.mesh.surface_get_material(i)
				if m == null: continue
				var nom := m.resource_name
				if PINTURA.has(nom):
					mi.set_surface_override_material(i, _mat_pintura(m))
				elif CROMO.has(nom) and m is StandardMaterial3D:
					mi.set_surface_override_material(i, _mat_cromo(m))
				elif nom == "mirror":
					var e := (m.duplicate() as StandardMaterial3D); e.albedo_color = Color(0.7, 0.72, 0.75); e.metallic = 1.0; e.roughness = 0.04
					mi.set_surface_override_material(i, e)
		pintar(c)
	for nm in ["glassF", "glassR", "glassLF", "glassRF", "glassLR", "glassRR"]:
		var gl := n.find_child(nm, true, false) as MeshInstance3D
		if gl:
			var vm := StandardMaterial3D.new(); vm.albedo_color = Color(0.03, 0.04, 0.05, 0.38); vm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			vm.metallic = 0.3; vm.roughness = 0.03; vm.metallic_specular = 1.0
			gl.material_override = vm

static func pieza(auto: Node3D, nombre: String) -> Node3D:
	return auto.find_child(nombre, true, false) as Node3D

## Entorno nocturno con cielo para que la pintura brillante tenga qué reflejar (sólo revisión en Godot; el acabado final es de Blender/Cycles).
static func entorno_noche() -> WorldEnvironment:
	var we := WorldEnvironment.new(); var e := Environment.new()
	var sky := Sky.new(); var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.03, 0.04, 0.08); sm.sky_horizon_color = Color(0.22, 0.26, 0.34); sm.ground_horizon_color = Color(0.12, 0.13, 0.16); sm.ground_bottom_color = Color(0.02, 0.02, 0.03)
	sm.sun_angle_max = 8.0; sm.sun_curve = 0.3
	sky.sky_material = sm; e.sky = sky; e.background_mode = Environment.BG_SKY
	e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; e.ambient_light_energy = 0.9
	e.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	we.environment = e
	return we

## Quita del modelo los limpiaparabrisas estacionados (triángulos finos de «chrome» en la base del parabrisas) y devuelve sus 2 brazos nuevos,
## que sí giran (barrido de 1,65 rad, ciclo de 1,4 s como en Dream Rally). Los pivotes quedan en el cuerpo del auto.
static func limpiaparabrisas(auto: Node3D) -> Array:
	var mi := auto.find_child("chrome", true, false) as MeshInstance3D
	if mi:
		var m := auto.global_transform.affine_inverse() * mi.global_transform
		var viejo := mi.mesh as ArrayMesh
		var nuevo := ArrayMesh.new()
		for si in viejo.get_surface_count():
			var arr := viejo.surface_get_arrays(si)
			if si == 1 and arr[Mesh.ARRAY_INDEX] != null:
				var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
				var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
				var keep := PackedInt32Array()
				for t in range(0, idx.size() - 2, 3):
					var dentro := 0
					for k in 3:
						var q: Vector3 = m * v[idx[t + k]]
						if q.z > -0.86 and q.z < -0.5 and q.y > 0.17 and q.y < 0.34 and absf(q.x) < 0.78:
							dentro += 1
					if dentro < 3:
						keep.append_array([idx[t], idx[t + 1], idx[t + 2]])
				arr[Mesh.ARRAY_INDEX] = keep
			nuevo.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
			nuevo.surface_set_material(si, viejo.surface_get_material(si))
		mi.mesh = nuevo
	var brazos := []
	var negro := StandardMaterial3D.new(); negro.albedo_color = Color(0.01, 0.01, 0.012); negro.roughness = 0.45; negro.metallic = 0.2
	for lado in [-1.0, 1.0]:                                   # dos escobillas en paralelo; pivotes bajo el parabrisas
		var piv := Node3D.new(); piv.name = "LimpiaPivote_" + ("L" if lado < 0 else "R")
		piv.position = Vector3(lado * 0.36 - 0.12, 0.215, -0.80)
		var norm := Vector3(0, 0.80, -0.60).normalized()          # normal del parabrisas (hacia afuera y arriba)
		auto.add_child(piv)
		var brazo := MeshInstance3D.new(); brazo.name = "Escobilla"
		var bm := BoxMesh.new(); bm.size = Vector3(0.012, 0.50, 0.010); brazo.mesh = bm; brazo.material_override = negro
		brazo.position = Vector3(0, 0.25, 0.01)                   # el brazo nace en el pivote y se extiende hacia +Y local
		piv.add_child(brazo)
		piv.basis = Basis(Quaternion(Vector3(0, 0, 1), norm))      # eje Z local = normal del parabrisas
		brazos.append(piv)
	return brazos

## Ángulo del barrido para un instante t (s): reposo → 1,65 rad → reposo cada 1,4 s (idéntico a Dream Rally).
static func angulo_limpia(t: float) -> float:
	var ph := fmod(maxf(t, 0.0), 1.4) / 1.4
	return (0.5 - 0.5 * cos(ph * TAU)) * 1.65
