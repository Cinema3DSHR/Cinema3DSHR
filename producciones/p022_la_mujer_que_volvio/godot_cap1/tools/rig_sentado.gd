## Piloto/pasajero SENTADO con cinemática inversa completa (cadera, columna, cabeza, brazos con dedos, piernas con pies en pedales).
## Port de `Rally-Sim-movile/godot/game/car/rig_pilot.gd` (Dream Rally) a los personajes de Character Creator (huesos EM3D_Base_*).
## Se trabaja en el espacio de la cabina = espacio local del personaje: +z adelante (hacia donde mira), +x a SU izquierda, y arriba.
class_name RigSentado
extends RefCounted

const FINGERS := ["Index", "Middle", "Ring", "Pinky"]
const NEED := ["Hips", "Spine", "Head", "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot"]
const DEDO_CC := {"Index": "Index", "Middle": "Mid", "Ring": "Ring", "Pinky": "Pinky", "Thumb": "Thumb"}

var ok := false
var skel: Skeleton3D
var B := {}                 # nombre estilo Mixamo → índice de hueso
var s := 1.0
var T := Transform3D.IDENTITY   # espacio del esqueleto (cm, Z arriba) → espacio de la cabina (m, Y arriba, +Z adelante)
var TB := Basis.IDENTITY
var _rest := {}
var _ax := {}
var _side := {}
var _spine: Array = []
var _fing: Array = []

func _init(sk: Skeleton3D, marco: Node3D) -> void:
	skel = sk
	skel.reset_bone_poses()
	T = marco.global_transform.affine_inverse() * skel.global_transform
	TB = T.basis.orthonormalized()
	var pre := "EM3D_Base_"
	var mapa := {"Hips": "Hip", "Spine": "Waist", "Spine1": "Spine01", "Spine2": "Spine02", "Head": "Head"}
	for k in mapa:
		B[k] = skel.find_bone(pre + mapa[k])
	var neck := skel.get_bone_parent(B["Head"])
	if neck >= 0 and neck != B["Spine2"]:
		B["Neck"] = neck
	for pair in [["Left", "L"], ["Right", "R"]]:
		var S: String = pair[0]
		var X: String = pair[1]
		B[S + "Shoulder"] = skel.find_bone(pre + X + "_Clavicle")
		B[S + "Arm"] = skel.find_bone(pre + X + "_Upperarm")
		B[S + "ForeArm"] = skel.find_bone(pre + X + "_Forearm")
		B[S + "Hand"] = skel.find_bone(pre + X + "_Hand")
		B[S + "UpLeg"] = skel.find_bone(pre + X + "_Thigh")
		B[S + "Leg"] = skel.find_bone(pre + X + "_Calf")
		B[S + "Foot"] = skel.find_bone(pre + X + "_Foot")
		B[S + "ToeBase"] = skel.find_bone(pre + X + "_ToeBase")
		for F in DEDO_CC:
			for n in [1, 2, 3]:
				var bi := skel.find_bone(pre + X + "_" + DEDO_CC[F] + str(n))
				if bi >= 0:
					B[S + "Hand" + F + str(n)] = bi
	for k in NEED:
		if not B.has(k) or int(B[k]) < 0:
			push_warning("RigSentado: falta el hueso " + k)
			return
	for i in skel.get_bone_count():
		var gr := skel.get_bone_global_rest(i)
		_rest[i] = {"lq": skel.get_bone_rest(i).basis.get_rotation_quaternion(), "wq": TB * gr.basis.orthonormalized(), "p": T * gr.origin}
	var up := Vector3.UP
	var fw := Vector3.BACK
	_spine = []
	for k in ["Spine", "Spine1", "Spine2", "Neck"]:
		if B.has(k):
			_spine.append(B[k])
	for b in _spine:
		_def(b, -1, fw, up)
	_def(B["Hips"], -1, fw, up)
	_def(B["Head"], -1, fw, up)
	for pair in [["Left", 1.0], ["Right", -1.0]]:
		var S: String = pair[0]
		var sg: float = pair[1]
		var arm: int = B[S + "Arm"]
		var fore: int = B[S + "ForeArm"]
		var hand: int = B[S + "Hand"]
		var mid: int = B.get(S + "HandMiddle1", B.get(S + "HandIndex1", -1))
		var shb: int = B.get(S + "Shoulder", -1)
		if shb >= 0:
			_def(shb, arm, up)
		_def(arm, fore, fw)
		_def(fore, hand, up)
		_def(hand, mid, up, Vector3.ZERO if mid >= 0 else Vector3(sg, 0, 0))
		var ul: int = B[S + "UpLeg"]
		var lg: int = B[S + "Leg"]
		var ft: int = B[S + "Foot"]
		var toe: int = B.get(S + "ToeBase", -1)
		_def(ul, lg, fw)
		_def(lg, ft, fw)
		_def(ft, toe, up, Vector3.ZERO if toe >= 0 else Vector3(0, -0.5, 1).normalized())
		var rp: Vector3 = _rest[arm]["p"]
		var rf: Vector3 = _rest[fore]["p"]
		var rh: Vector3 = _rest[hand]["p"]
		var lu: Vector3 = _rest[ul]["p"]
		var ll: Vector3 = _rest[lg]["p"]
		var lf: Vector3 = _rest[ft]["p"]
		# dedos: eje de nudillos en reposo (T-pose: Z); se curvan hacia la palma
		var fing := []
		for F in FINGERS + ["Thumb"]:
			for n in [1, 2, 3]:
				var nm: String = S + "Hand" + str(F) + str(n)
				if B.has(nm):
					var bi: int = B[nm]
					var axv: Vector3 = (_rest[bi]["wq"] as Basis).inverse() * Vector3(0, 0, 1)
					fing.append({"b": bi, "ax": axv, "k": 0.35 if F == "Thumb" else 1.0, "sg": sg})
		_side[S] = {"sh": shb, "arm": arm, "fore": fore, "hand": hand, "ul": ul, "lg": lg, "ft": ft, "fing": fing, "sg": sg,
			"L1": rp.distance_to(rf) * s, "L2": rf.distance_to(rh) * s, "T1": lu.distance_to(ll) * s, "T2": ll.distance_to(lf) * s}
	ok = true

## eje primario (hacia el hijo, o el dado en prim) y secundario (dado en el espacio del personaje) en coordenadas del hueso
func _def(b: int, child: int, sec: Vector3, prim := Vector3.ZERO) -> void:
	var r: Dictionary = _rest[b]
	var p: Vector3 = prim if prim != Vector3.ZERO else ((_rest[child]["p"] as Vector3) - (r["p"] as Vector3)).normalized()
	var iq: Basis = (r["wq"] as Basis).inverse()
	_ax[b] = {"p": (iq * p).normalized(), "s": (iq * sec).normalized()}

## posición del hueso en el espacio de la cabina
func _fpos(b: int) -> Vector3:
	return T * skel.get_bone_global_pose(b).origin

## orienta el hueso para que su eje primario apunte a P y el secundario hacia S (vectores de la cabina)
func _orient(b: int, P: Vector3, S: Vector3) -> void:
	if not _ax.has(b):
		return
	var a: Dictionary = _ax[b]
	var p1 := P.normalized()
	var s1 := S - p1 * S.dot(p1)
	if s1.length_squared() < 1e-9:
		return
	s1 = s1.normalized()
	var t1 := p1.cross(s1)
	var m1 := Basis(p1, s1, t1)
	var ap: Vector3 = a["p"]
	var s0: Vector3 = (a["s"] as Vector3)
	s0 = (s0 - ap * s0.dot(ap)).normalized()
	var t0 := ap.cross(s0)
	var m2 := Basis(ap, s0, t0).transposed()
	var Q := m1 * m2
	var par := skel.get_bone_parent(b)
	var pq := skel.get_bone_global_pose(par).basis.orthonormalized() if par >= 0 else Basis.IDENTITY
	skel.set_bone_pose_rotation(b, (pq.inverse() * (TB.inverse() * Q)).get_rotation_quaternion())

## IK de dos huesos: A (raíz) → codo/rodilla → objetivo T, con vector polo
func _two_bone(A: int, B2: int, L1: float, L2: float, T: Vector3, pole: Vector3, secA: Variant, secB: Variant) -> void:
	var S := _fpos(A)
	var d := T - S
	var ln := d.length()
	var mx := (L1 + L2) * 0.999
	if ln > mx:
		d *= mx / ln
		ln = mx
	ln = maxf(ln, absf(L1 - L2) + 1e-3)
	var dir := d.normalized()
	var a := (L1 * L1 - L2 * L2 + ln * ln) / (2.0 * ln)
	var h := sqrt(maxf(0.0, L1 * L1 - a * a))
	var pd := (pole - dir * pole.dot(dir)).normalized()
	var E := S + dir * a + pd * h
	var tgt := S + d
	var sa: Vector3
	if secA is String:
		sa = tgt - E + pd * -0.3
	elif secA == null:
		sa = pd
	else:
		sa = secA
	_orient(A, E - S, sa)
	_orient(B2, tgt - _fpos(B2), pd if secB == null else (secB as Vector3))

## Pose completa. o = {hips, head, roll, look, hands:[{side, wrist, fdir, back, pole?}], feet:[{side, pos}], grip}
func pose(o: Dictionary) -> void:
	if not ok:
		return
	var hips: int = B["Hips"]
	var par_h := skel.get_bone_parent(hips)
	var en_sk: Vector3 = T.affine_inverse() * (o["hips"] as Vector3)
	skel.set_bone_pose_position(hips, (skel.get_bone_global_pose(par_h).affine_inverse() * en_sk) if par_h >= 0 else en_sk)
	var fwd := Vector3(0, 0, 1)
	_orient(hips, Vector3(0, 1, o.get("hip_tilt", -0.18)).normalized(), fwd)
	# columna hacia la cabeza (reclinada, cuello adelante)
	var hp := _fpos(hips)
	var dir: Vector3 = ((o["head"] as Vector3) - hp).normalized()
	var n := _spine.size()
	for i in n:
		var tt := float(i) / float(n - 1) if n > 1 else 1.0
		var l0: float = o.get("lean0", -0.10)
		var l1: float = o.get("lean1", 0.18)
		var d := (dir + Vector3(0, 0, l0 + (l1 - l0) * tt)).normalized()
		_orient(_spine[i], d, fwd)
	# cabeza: inclinación lateral por G y mirada hacia adelante
	var roll: float = o.get("roll", 0.0)
	var hd := Vector3(sin(roll), cos(roll), 0.05).normalized()
	_orient(B["Head"], hd, Vector3(o.get("look", 0.0), o.get("look_y", -0.1), 1))
	# brazos
	var grip: float = o.get("grip", 1.1)
	for h in o["hands"]:
		var S: Dictionary = _side.get(h["side"], {})
		if S.is_empty():
			continue
		var sg: float = S["sg"]
		var pole := Vector3(sg * 0.6, -1, -0.25)
		if h.has("pole"):
			var hp2: Vector3 = h["pole"]
			pole = Vector3(sg * hp2.x, hp2.y, hp2.z)
		var wrist: Vector3 = h["wrist"]
		# clavícula: acompaña un poco al brazo (sin esto el hombro se estira y deforma)
		if S["sh"] >= 0:
			var sp := _fpos(S["sh"])
			var tw := (wrist - sp).normalized()
			_orient(S["sh"], Vector3(sg, 0, 0) * 0.72 + tw * 0.28 + Vector3(0, -0.04, 0), Vector3.UP)
		_two_bone(S["arm"], S["fore"], S["L1"], S["L2"], wrist, pole, "fold", h["back"])
		_orient(S["hand"], h["fdir"], h["back"])
		for f in S["fing"]:
			var r: Quaternion = _rest[f["b"]]["lq"]
			skel.set_bone_pose_rotation(f["b"], r * Quaternion(f["ax"], -f["sg"] * grip * 0.55 * f["k"]))
	# piernas
	for f in o["feet"]:
		var S2: Dictionary = _side.get(f["side"], {})
		if S2.is_empty():
			continue
		_two_bone(S2["ul"], S2["lg"], S2["T1"], S2["T2"], f["pos"], f.get("pole", Vector3(0, 1, 0.3)), Vector3(0, 1, 0), Vector3(0, 0.3, 1))
		_orient(S2["ft"], Vector3(0, o.get("foot_up", 0.25), 1), Vector3(0, 1, -0.2))

