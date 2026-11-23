## Auto «hustler» listo para la escena: frente hacia −Z (el GLB original mira a +Z), carrocería NEGRA brillante, piezas accesibles por nombre.
extends RefCounted
const RUTA := "res://assets/hustler.glb"
const PINTURA := ["remap_kuzov", "nodamage_lod0"]   # materiales de carrocería (el original viene claro)

static func crear() -> Node3D:
	var raiz := Node3D.new(); raiz.name = "Auto"
	var g: Node3D = load(RUTA).instantiate()
	g.name = "Modelo"; g.rotation_degrees = Vector3(0, 180, 0)
	raiz.add_child(g)
	pintar(g)
	return raiz

static func pintar(n: Node) -> void:
	for c in n.get_children():
		var mi := c as MeshInstance3D
		if mi and mi.mesh:
			for i in mi.mesh.get_surface_count():
				var m := mi.mesh.surface_get_material(i)
				if m and PINTURA.has(m.resource_name):
					var nm := (m.duplicate() as StandardMaterial3D)
					nm.albedo_color = Color(0.015, 0.015, 0.018); nm.albedo_texture = null
					nm.metallic = 0.85; nm.roughness = 0.18
					nm.clearcoat_enabled = true; nm.clearcoat = 1.0; nm.clearcoat_roughness = 0.05
					mi.set_surface_override_material(i, nm)
		pintar(c)

static func pieza(auto: Node3D, nombre: String) -> Node3D:
	return auto.find_child(nombre, true, false) as Node3D
