## Destrucción del cupé para el accidente: deformación real de las mallas (aplastamiento + ondulado de chapa), capó levantado, paragolpes colgando,
## faro roto, parabrisas rajado, rueda delantera torcida y puerta abollada. Todo en el espacio del auto (frente = −Z). `nivel` 0 = intacto … 1 = destruido.
extends RefCounted

const PIEZAS_CHAPA := ["body", "chrome", "hood", "headlights_okidoko", "headlightRdetail", "headlightRglass", "coo_ok", "plate_F", "lf", "rf", "lb", "rb", "svet1", "svet2", "svet3", "dver L", "Dver R", "zerk", "zerk (2)", "wing", "bumperF"]

static func _suave(a: float, b: float, x: float) -> float:
	var t := clampf((x - a) / (b - a), 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)

## Deformación de un punto (espacio del auto). choque: golpe frontal sobre la esquina del conductor + roce lateral.
static func deformar(v: Vector3, nivel: float) -> Vector3:
	var P := Vector3(0.50, 0.05, -2.15)                      # punto principal de impacto (esquina delantera, lado del volante)
	var d := Vector3((v.x - P.x) / 0.95, (v.y - P.y) / 0.70, (v.z - P.z) / 1.15)
	var w := exp(-(d.x * d.x + d.y * d.y * 0.7 + d.z * d.z))
	var frente := _suave(-0.9, -2.3, v.z)                      # todo el frente se acorta un poco
	var rip := sin(v.x * 21.0 + v.y * 15.0) * sin(v.z * 17.0 + 2.0) * 0.045
	var rip2 := sin(v.x * 9.0 - v.y * 11.0 + v.z * 7.0) * 0.06
	var o := v
	o.z += (0.95 * w + 0.22 * frente) * nivel + (rip * w) * nivel * 2.2           # aplastamiento hacia atrás
	o.y += (0.22 * w * sin(v.z * 6.0 + 1.0) + rip2 * w) * nivel - 0.10 * w * nivel  # la chapa se arruga y se hunde
	o.x += ((v.x - P.x) * 0.16 * w + 0.10 * w) * nivel + rip * 0.8 * w * nivel      # abulta hacia afuera
	# roce lateral (lado derecho del auto, contra las rocas)
	var Q := Vector3(0.88, 0.0, -0.4)
	var dq := Vector3((v.x - Q.x) / 0.25, (v.y - Q.y) / 0.55, (v.z - Q.z) / 1.35)
	var wq := exp(-(dq.x * dq.x + dq.y * dq.y + dq.z * dq.z))
	o.x -= (0.09 * wq + 0.02 * wq * sin(v.z * 25.0)) * nivel
	return o

static func _normales(verts: PackedVector3Array, idx: PackedInt32Array) -> PackedVector3Array:
	var nor := PackedVector3Array(); nor.resize(verts.size())
	for i in range(0, idx.size() - 2, 3):
		var a := idx[i]; var b := idx[i + 1]; var c := idx[i + 2]
		var fn := (verts[b] - verts[a]).cross(verts[c] - verts[a])
		nor[a] += fn; nor[b] += fn; nor[c] += fn
	for i in nor.size():
		nor[i] = nor[i].normalized() if nor[i].length_squared() > 1e-12 else Vector3.UP
	return nor

static func deformar_malla(mi: MeshInstance3D, auto: Node3D, nivel: float) -> void:
	var m := auto.global_transform.affine_inverse() * mi.global_transform
	var mi_inv := m.affine_inverse()
	var viejo := mi.mesh as ArrayMesh
	if viejo == null:
		return
	var nuevo := ArrayMesh.new()
	for i in viejo.get_surface_count():
		var arr := viejo.surface_get_arrays(i)
		var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var out := PackedVector3Array(); out.resize(verts.size())
		for k in verts.size():
			out[k] = mi_inv * deformar(m * verts[k], nivel)
		arr[Mesh.ARRAY_VERTEX] = out
		if arr[Mesh.ARRAY_INDEX] != null and (arr[Mesh.ARRAY_INDEX] as PackedInt32Array).size() > 0:
			arr[Mesh.ARRAY_NORMAL] = _normales(out, arr[Mesh.ARRAY_INDEX])
		arr[Mesh.ARRAY_TANGENT] = null
		nuevo.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nuevo.surface_set_material(i, viejo.surface_get_material(i))
	mi.mesh = nuevo

static func _girar_en(auto: Node3D, mi: Node3D, pivote: Vector3, rot: Basis, mover := Vector3.ZERO) -> void:
	var ga := auto.global_transform
	var t := Transform3D(Basis.IDENTITY, pivote) * Transform3D(rot, Vector3.ZERO) * Transform3D(Basis.IDENTITY, -pivote)
	mi.global_transform = ga * Transform3D(Basis.IDENTITY, mover) * t * (ga.affine_inverse() * mi.global_transform)

## Destruye el auto. semilla: reproducible.
static func destruir(auto: Node3D, nivel := 1.0) -> void:
	for nm in PIEZAS_CHAPA:
		var mi := auto.find_child(nm, true, false) as MeshInstance3D
		if mi:
			deformar_malla(mi, auto, nivel)
	# capó: se levanta por la bisagra del parabrisas y queda torcido
	var capo := auto.find_child("hood", true, false) as Node3D
	if capo:
		_girar_en(auto, capo, Vector3(0.0, 0.18, -0.85), Basis.from_euler(Vector3(deg_to_rad(24.0 * nivel), deg_to_rad(-6.0 * nivel), deg_to_rad(5.0 * nivel))))
	# paragolpes delantero: se suelta de un lado y cuelga
	var pg := auto.find_child("bumperF", true, false) as Node3D
	if pg:
		_girar_en(auto, pg, Vector3(-0.75, -0.37, -1.9), Basis.from_euler(Vector3(deg_to_rad(8.0 * nivel), deg_to_rad(-16.0 * nivel), deg_to_rad(-22.0 * nivel))), Vector3(0.06, -0.14, 0.12) * nivel)
	var pl := auto.find_child("plate_F", true, false) as Node3D
	if pl:
		_girar_en(auto, pl, Vector3(0.0, -0.3, -1.95), Basis.from_euler(Vector3(deg_to_rad(15.0 * nivel), 0, deg_to_rad(-30.0 * nivel))), Vector3(0.08, -0.12, 0.1) * nivel)
	# rueda delantera del golpe (lado del conductor): torcida y levantada
	var rd := auto.find_child("Wheel FR", true, false) as Node3D
	var ri := auto.find_child("Wheel FL", true, false) as Node3D
	for r in [rd, ri]:
		if r == null: continue
		var lado: float = 1.0 if (r.global_position - auto.global_position).x > 0 else -1.0
		_girar_en(auto, r, auto.global_transform.affine_inverse() * r.global_position,
			Basis.from_euler(Vector3(0, deg_to_rad(-28.0 * nivel * lado), deg_to_rad(14.0 * nivel * lado))), Vector3(0.05 * lado, 0.05, 0.22) * nivel)
	# faro roto + cristales
	var fr := auto.find_child("headlightRglass", true, false) as Node3D
	if fr and nivel >= 0.5: fr.get_parent().remove_child(fr); fr.queue_free()
	for nm in ["glassLF", "glassLR", "glassRR"]:
		var g := auto.find_child(nm, true, false) as Node3D
		if g and nivel >= 0.5: g.get_parent().remove_child(g); g.queue_free()
	var pb := auto.find_child("glassF", true, false) as MeshInstance3D
	if pb and nivel > 0.5:
		pb.material_override = _vidrio_roto()

## Parabrisas rajado: textura de grietas radiales desde el impacto + telaraña, dibujada en código (no se versiona).
static func _vidrio_roto() -> StandardMaterial3D:
	var N := 1024
	var img := Image.create(N, N, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.03, 0.04, 0.05, 0.30))
	var rng := RandomNumberGenerator.new(); rng.seed = 7717
	var c := Vector2(N * 0.62, N * 0.42)
	for k in 26:
		var ang := rng.randf() * TAU
		var p := c; var a := ang
		var largo := rng.randf_range(260, 760)
		var paso := 0.0
		while paso < largo:
			a += rng.randf_range(-0.12, 0.12)
			p += Vector2(cos(a), sin(a)) * 3.0; paso += 3.0
			for dx in [0, 1]:
				var q := Vector2i(int(p.x) + dx, int(p.y))
				if q.x >= 0 and q.y >= 0 and q.x < N and q.y < N:
					img.set_pixelv(q, Color(0.92, 0.95, 1.0, 0.92 - 0.55 * paso / largo))
			if rng.randf() < 0.012 and paso > 40.0:       # ramifica
				a += rng.randf_range(-0.9, 0.9)
	for anillo in [40, 85, 150, 240]:                     # telaraña concéntrica
		var a2 := 0.0
		while a2 < TAU:
			var q2 := Vector2i(int(c.x + cos(a2) * anillo * (1.0 + 0.1 * sin(a2 * 5.0))), int(c.y + sin(a2) * anillo * 0.85))
			if q2.x >= 0 and q2.y >= 0 and q2.x < N and q2.y < N and rng.randf() < 0.6:
				img.set_pixelv(q2, Color(0.9, 0.94, 1.0, 0.75))
			a2 += 0.004
	var m := StandardMaterial3D.new()
	m.albedo_texture = ImageTexture.create_from_image(img)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; m.metallic = 0.3; m.roughness = 0.05; m.metallic_specular = 1.0
	return m
