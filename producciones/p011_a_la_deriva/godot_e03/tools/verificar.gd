## Verificador de la nave: (1) orientación: cada pieza mira hacia lo que declaró (mira_a); (2) nada flota: apoyada en el piso o sobre una superficie;
## (3) piezas atravesadas entre sí. Uso: godot --headless --path . --script res://tools/verificar.gd
extends SceneTree
const TOL_GRADOS := 8.0
const PARED := ["pantalla_pared", "ventanal", "luminaria_techo", "caja_electrica"]
const IGNORAR_CHOQUE := ["pantalla_pared", "ventanal", "luminaria_techo", "marco_puerta", "silla_comando", "silla_comedor", "mesa_comedor", "consola_mando", "consola_central", "escritorio", "cama", "mesita", "florero", "casco", "microscopio", "terrario", "barra_cocina", "camilla", "soporte_suero", "armario", "estante", "nucleo_eva", "holoproyector"]
var piezas := []
var mallas := []

func _initialize() -> void:
	var nave: Node = load("res://nave.tscn").instantiate()
	root.add_child(nave)
	await process_frame
	await process_frame
	_recolectar(nave)
	var errores := 0
	for p in piezas:
		var n: Node3D = p
		if n.has_meta("mira_a"):
			var d: Vector3 = n.get_meta("mira_a") - n.global_position
			d.y = 0
			var f: Vector3 = -n.global_transform.basis.z
			f.y = 0
			if d.length() > 0.01 and f.length() > 0.01:
				var ang := rad_to_deg(f.normalized().angle_to(d.normalized()))
				if ang > TOL_GRADOS:
					print("ORIENTACION ", n.name, " (", n.get_meta("pieza"), ") mira ", snappedf(ang, 0.1), "° fuera de su objetivo")
					errores += 1
		var pieza := String(n.get_meta("pieza", ""))
		if PARED.has(pieza) or n.has_meta("hundida"):
			continue
		var bb := _aabb_global(n)
		if bb.size == Vector3.ZERO:
			continue
		var base := bb.position.y
		if absf(base) <= 0.005:
			continue
		# sobre una superficie: existe una malla ajena, que contiene (x,z) y cuya cara superior está a ±1 cm de la base
		var apoyo := false
		for m in mallas:
			if n.is_ancestor_of(m):
				continue
			var mb := _aabb_global(m)
			var c := bb.get_center()
			if c.x >= mb.position.x - 0.02 and c.x <= mb.end.x + 0.02 and c.z >= mb.position.z - 0.02 and c.z <= mb.end.z + 0.02 and absf(mb.end.y - base) <= 0.015:
				apoyo = true
				break
		if not apoyo:
			print("FLOTA ", n.name, " (", pieza, ") base a ", snappedf(base, 0.001), " m sin nada debajo")
			errores += 1
	# piezas atravesadas
	for i in piezas.size():
		for j in range(i + 1, piezas.size()):
			var a: Node3D = piezas[i]
			var b: Node3D = piezas[j]
			var pa := String(a.get_meta("pieza", ""))
			var pb := String(b.get_meta("pieza", ""))
			if PARED.has(pa) or PARED.has(pb) or pa == "costilla" or pb == "costilla" or a.has_meta("hundida") or b.has_meta("hundida") or pa.begins_with("bush") or pb.begins_with("bush") or a.is_ancestor_of(b) or b.is_ancestor_of(a):
				continue
			var ba := _aabb_global(a)
			var bb2 := _aabb_global(b)
			var inter := ba.intersection(bb2)
			if inter.size.x > 0.12 and inter.size.y > 0.12 and inter.size.z > 0.12:
				var par := [pa, pb]
				if (par.has("silla_comando") or par.has("silla_comedor")) and (par.has("mesa_comedor") or par.has("escritorio") or par.has("consola_mando") or par.has("consola_central")):
					continue
				print("ATRAVIESA ", a.name, " con ", b.name, " (", snappedf(inter.size.x, 0.01), "×", snappedf(inter.size.y, 0.01), "×", snappedf(inter.size.z, 0.01), " m)")
				errores += 1
	print("VERIFICACION piezas=", piezas.size(), " problemas=", errores)
	quit(1 if errores > 0 else 0)

func _recolectar(n: Node) -> void:
	for c in n.get_children():
		if c is Node3D and c.has_meta("pieza"):
			piezas.append(c)
		if c is MeshInstance3D:
			mallas.append(c)
		_recolectar(c)

func _aabb_global(n: Node) -> AABB:
	var out := AABB()
	var primero := true
	var lista := []
	if n is MeshInstance3D:
		lista.append(n)
	_meshes(n, lista)
	for m in lista:
		var mi: MeshInstance3D = m
		if mi.mesh == null or mi.mesh is PlaneMesh:
			continue
		var ab: AABB = mi.global_transform * mi.mesh.get_aabb()
		if primero:
			out = ab
			primero = false
		else:
			out = out.merge(ab)
	return out

func _meshes(n: Node, lista: Array) -> void:
	for c in n.get_children():
		if c is MeshInstance3D:
			lista.append(c)
		_meshes(c, lista)
