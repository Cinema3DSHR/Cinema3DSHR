## Cinemática inversa de dos huesos para llevar una mano a un punto del mundo (volante, tablero, etc.). Se aplica DESPUÉS de poner la pose del clip.
class_name IkBrazo
extends RefCounted

static func _gp(sk: Skeleton3D, i: int) -> Transform3D:
	return sk.global_transform * sk.get_bone_global_pose(i)

static func _entre(a: Vector3, b: Vector3) -> Quaternion:
	var eje := a.cross(b)
	if eje.length() < 1e-6:
		return Quaternion.IDENTITY
	return Quaternion(eje.normalized(), acos(clampf(a.dot(b), -1.0, 1.0)))

static func _girar_hueso(sk: Skeleton3D, hueso: int, hacia_desde: Vector3, hacia_a: Vector3) -> void:
	var t := _gp(sk, hueso)
	var q := _entre(hacia_desde.normalized(), hacia_a.normalized())
	var nt := Transform3D(Basis(q) * t.basis, t.origin)
	sk.set_bone_global_pose(hueso, sk.global_transform.affine_inverse() * nt)

## mano: índice del hueso de la mano; objetivo y polo (hacia dónde apunta el codo) en coordenadas del mundo.
static func llevar_mano(sk: Skeleton3D, mano: int, objetivo: Vector3, polo: Vector3) -> float:
	var ante := sk.get_bone_parent(mano)
	var arriba := sk.get_bone_parent(ante)
	var A := _gp(sk, arriba).origin
	var B := _gp(sk, ante).origin
	var C := _gp(sk, mano).origin
	var l1 := A.distance_to(B)
	var l2 := B.distance_to(C)
	var d := clampf(A.distance_to(objetivo), 0.05, l1 + l2 - 0.002)
	var dir := (objetivo - A).normalized()
	var x := (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
	var h := sqrt(maxf(l1 * l1 - x * x, 0.0))
	var pv := polo - A
	var perp := (pv - dir * dir.dot(pv)).normalized()
	var codo := A + dir * x + perp * h
	_girar_hueso(sk, arriba, B - A, codo - A)
	var B2 := _gp(sk, ante).origin
	var C2 := _gp(sk, mano).origin
	_girar_hueso(sk, ante, C2 - B2, objetivo - B2)
	return _gp(sk, mano).origin.distance_to(objetivo)       # error residual (m); 0 = llegó
