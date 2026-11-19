## Ayudas para construir piezas simples. Cada pieza lleva meta "mat" (nombre del material): la etapa 2 los aplica.
class_name Kit
extends RefCounted

static func _poner(padre: Node3D, n: Node3D, nombre: String, pos: Vector3, rot_deg: Vector3) -> void:
	n.name = nombre
	n.position = pos
	n.rotation_degrees = rot_deg
	padre.add_child(n)

static func grupo(padre: Node, nombre: String, pos := Vector3.ZERO, rot_deg := Vector3.ZERO) -> Node3D:
	var n := Node3D.new()
	n.name = nombre
	n.position = pos
	n.rotation_degrees = rot_deg
	padre.add_child(n)
	return n

static func caja(padre: Node3D, nombre: String, tam: Vector3, pos: Vector3, mat: String, rot_deg := Vector3.ZERO) -> MeshInstance3D:
	var m := BoxMesh.new()
	m.size = tam
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.set_meta("mat", mat)
	_poner(padre, mi, nombre, pos, rot_deg)
	return mi

static func cilindro(padre: Node3D, nombre: String, r_arriba: float, r_abajo: float, alto: float, pos: Vector3, mat: String, rot_deg := Vector3.ZERO, lados := 24) -> MeshInstance3D:
	var m := CylinderMesh.new()
	m.top_radius = r_arriba
	m.bottom_radius = r_abajo
	m.height = alto
	m.radial_segments = lados
	m.rings = 1
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.set_meta("mat", mat)
	_poner(padre, mi, nombre, pos, rot_deg)
	return mi

static func esfera(padre: Node3D, nombre: String, r: float, pos: Vector3, mat: String, escala := Vector3.ONE) -> MeshInstance3D:
	var m := SphereMesh.new()
	m.radius = r
	m.height = r * 2.0
	m.radial_segments = 20
	m.rings = 10
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.set_meta("mat", mat)
	_poner(padre, mi, nombre, pos, Vector3.ZERO)
	mi.scale = escala
	return mi

## Línea quebrada gruesa (para el rayo): cajas finas que unen los puntos.
static func polilinea(padre: Node3D, nombre: String, puntos: PackedVector3Array, grosor: float, mat: String) -> Node3D:
	var g := grupo(padre, nombre)
	for i in puntos.size() - 1:
		var a := puntos[i]
		var b := puntos[i + 1]
		var mi := caja(g, "%s_%02d" % [nombre, i], Vector3(grosor, a.distance_to(b), grosor), (a + b) * 0.5, mat)
		var d := (b - a).normalized()
		mi.basis = Basis(Quaternion(Vector3.UP, d))
	return g

## Asigna el dueño a todo lo construido (sin entrar en escenas instanciadas) para poder guardar el .tscn.
static func adueñar(raiz: Node, n: Node) -> void:
	for h in n.get_children():
		h.owner = raiz
		if h.scene_file_path.is_empty():
			adueñar(raiz, h)
