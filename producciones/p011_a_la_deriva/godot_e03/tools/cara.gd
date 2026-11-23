## Cara de los personajes del capítulo 3: expresiones, parpadeo, labios por las letras de la voz real (alineación de ElevenLabs), mandíbula,
## cabeza y ojos que miran a un objetivo. Se evalúa cuadro a cuadro desde montaje.gd.
extends RefCounted

const FPS := 30.0

# expresión → {forma: valor}
const EXPRESIONES := {
	"-": {},
	"neutra": {},
	"seria": {"Brow_Drop_Left": 0.30, "Brow_Drop_Right": 0.30, "Mouth_Lips_Tight": 0.15},
	"preocupado": {"Brow_Raise_Inner_Left": 0.65, "Brow_Raise_Inner_Right": 0.65, "Mouth_Frown": 0.25, "Eye_Wide_L": 0.12, "Eye_Wide_R": 0.12},
	"sorpresa": {"Brow_Raise_Left": 0.75, "Brow_Raise_Right": 0.75, "Eye_Wide_L": 0.5, "Eye_Wide_R": 0.5, "Mouth_Lips_Part": 0.35},
	"triste_sutil": {"Brow_Raise_Inner_Left": 0.45, "Brow_Raise_Inner_Right": 0.45, "Mouth_Frown": 0.35, "Eye_Squint_L": 0.1, "Eye_Squint_R": 0.1},
	"sonrisa_suave": {"Mouth_Smile": 0.5, "Cheek_Raise_L": 0.3, "Cheek_Raise_R": 0.3, "Eye_Squint_L": 0.12, "Eye_Squint_R": 0.12},
	"cansado": {"Eye_Blink_L": 0.28, "Eye_Blink_R": 0.28, "Brow_Drop_Left": 0.12, "Brow_Drop_Right": 0.12, "Mouth_Frown": 0.12},
	"preocupado_seria": {"Brow_Raise_Inner_Left": 0.45, "Brow_Drop_Left": 0.15, "Brow_Raise_Inner_Right": 0.45, "Brow_Drop_Right": 0.15, "Mouth_Lips_Tight": 0.2},
	"dormida": {"Eye_Blink_L": 0.8, "Eye_Blink_R": 0.8},
}

# letra → [{forma: valor}, mandíbula 0..1]
const VISEMAS := {
	"a": [{"V_Open": 0.75}, 0.55], "á": [{"V_Open": 0.75}, 0.6],
	"e": [{"V_Wide": 0.45, "V_Open": 0.3}, 0.35], "é": [{"V_Wide": 0.45, "V_Open": 0.3}, 0.4],
	"i": [{"V_Wide": 0.7, "V_Open": 0.1}, 0.2], "í": [{"V_Wide": 0.7, "V_Open": 0.1}, 0.22],
	"o": [{"V_Tight_O": 0.7, "V_Open": 0.25}, 0.4], "ó": [{"V_Tight_O": 0.7, "V_Open": 0.25}, 0.42],
	"u": [{"V_Tight_O": 0.9}, 0.18], "ú": [{"V_Tight_O": 0.9}, 0.2], "ü": [{"V_Tight_O": 0.9}, 0.18],
	"m": [{"V_Explosive": 0.9}, 0.0], "b": [{"V_Explosive": 0.9}, 0.0], "p": [{"V_Explosive": 0.9}, 0.0],
	"f": [{"V_Dental_Lip": 0.85}, 0.1], "v": [{"V_Dental_Lip": 0.6}, 0.1],
	"s": [{"V_Affricate": 0.4}, 0.12], "z": [{"V_Affricate": 0.4}, 0.12], "c": [{"V_Affricate": 0.3}, 0.15], "x": [{"V_Affricate": 0.4}, 0.12],
	"j": [{"V_Tight": 0.35}, 0.15], "y": [{"V_Tight": 0.3}, 0.15], "ñ": [{"V_Tight": 0.3}, 0.15], "r": [{"V_Open": 0.18}, 0.15],
	"l": [{"V_Open": 0.22}, 0.2], "t": [{"V_Open": 0.2}, 0.15], "d": [{"V_Open": 0.2}, 0.15], "n": [{"V_Open": 0.18}, 0.12],
	"k": [{"V_Open": 0.2}, 0.18], "g": [{"V_Open": 0.2}, 0.18], "q": [{"V_Tight_O": 0.3}, 0.15], "h": [{"V_Open": 0.12}, 0.1], "w": [{"V_Tight_O": 0.6}, 0.15],
}

var SB: Dictionary
var estado := {}                 # id → {actual:{forma:valor}, mandibula, visemas:[{t0,t1,letra}], parpadeos:[t…], eje_mand, signo_mand, miradas, ...}
var pistas := {}                 # id → {"path": track}
var ultimo := {}                 # id → {track: [valor, t_ultimo_insertado, t_pendiente, hay_pendiente]}

func preparar(sb: Dictionary, actores: Dictionary) -> void:
	SB = sb
	SB["_actores_ref"] = actores
	for id in actores:
		var st := {"actual": {}, "mandibula": 0.0, "visemas": [], "expresiones": [], "parpadeos": [], "mirada_cabeza": Quaternion.IDENTITY, "mir_ojos": Vector2.ZERO}
		var rng := RandomNumberGenerator.new()
		rng.seed = hash("e03_" + id + str(sb.get("titulo", "")))
		var t := 1.2 + rng.randf() * 1.5
		while t < float(sb["dur"]):
			st["parpadeos"].append(t)
			t += 2.4 + rng.randf() * 3.2
		st["eje_mand"] = Vector3.RIGHT
		st["signo_mand"] = 1.0
		estado[id] = st
	# voces de la escena: visemas (sólo quien habla) y expresión de cada personaje durante la línea
	for v in sb.get("voces", []):
		var js = JSON.parse_string(FileAccess.get_file_as_string("res://" + String(v["alineacion_res"]))) if v.has("alineacion_res") else null
		var quien: String = v["quien"]
		if js != null and estado.has(quien):
			var ch: Array = js["characters"]; var ini: Array = js["character_start_times_seconds"]; var fin: Array = js["character_end_times_seconds"]
			var dentro := false
			for i in ch.size():
				var c: String = ch[i]
				if c == "[":
					dentro = true
				if not dentro:
					var l := c.to_lower()
					if VISEMAS.has(l):
						estado[quien]["visemas"].append([float(v["t"]) + float(ini[i]), float(v["t"]) + float(fin[i]), l])
				if c == "]":
					dentro = false
		for id in v.get("exp", {}):
			if estado.has(id):
				estado[id]["expresiones"].append([float(v["t"]), String(v["exp"][id])])
	for id in estado:
		estado[id]["expresiones"].sort_custom(func(a, b): return a[0] < b[0])
	# parpadeos coincidentes con una pausa de la voz no importan: son parte de la vida normal

func crear_pistas(anim: Animation, esc: Node3D) -> void:
	for id in estado:
		pistas[id] = {}
		ultimo[id] = {}
		_asegurar_pistas(id, SB["_actores_ref"][id], anim, esc)

func _nombres_usados() -> Array:
	var s := {}
	for k in EXPRESIONES:
		for f in EXPRESIONES[k]:
			s[f] = true
	for k in VISEMAS:
		for f in VISEMAS[k][0]:
			s[f] = true
	s["Eyes_Blink"] = true; s["Eye_Blink_L"] = true; s["Eye_Blink_R"] = true
	return s.keys()

func _asegurar_pistas(id: String, ac, anim: Animation, esc: Node3D) -> void:
	if not pistas[id].is_empty():
		return
	for par in ac.mallas_con_forma:
		var mi: MeshInstance3D = par[0]
		var d: Dictionary = par[1]
		for nm in _nombres_usados():
			if d.has(nm):
				var tp := anim.add_track(Animation.TYPE_VALUE)
				anim.track_set_path(tp, NodePath("%s:blend_shapes/%s" % [esc.get_path_to(mi), nm]))
				anim.track_set_interpolation_type(tp, Animation.INTERPOLATION_LINEAR)
				pistas[id][tp] = [mi, nm]
				ultimo[id][tp] = [0.0, -1.0, -1.0, false]
	# jaula: mandíbula como hueso (rotación)
	var tj := anim.add_track(Animation.TYPE_ROTATION_3D)
	anim.track_set_path(tj, NodePath("%s:%s" % [esc.get_path_to(ac.sk), ac.sk.get_bone_name(ac.mand)]))
	pistas[id]["mand"] = tj
	for l in ["L", "R"]:
		var to := anim.add_track(Animation.TYPE_ROTATION_3D)
		anim.track_set_path(to, NodePath("%s:%s" % [esc.get_path_to(ac.sk), ac.sk.get_bone_name(ac.ojo[l])]))
		pistas[id]["ojo" + l] = to

func _viseme_en(st: Dictionary, t: float) -> Array:
	# suma de envolventes de las letras activas cerca de t
	var vals := {}
	var jaw := 0.0
	var vis: Array = st["visemas"]
	for v in vis:
		if t < v[0] - 0.08 or t > v[1] + 0.09:
			continue
		var env := minf(clampf((t - (v[0] - 0.05)) / 0.07, 0.0, 1.0), clampf(((v[1] + 0.06) - t) / 0.08, 0.0, 1.0))
		env = smoothstep(0.0, 1.0, env)
		var def: Array = VISEMAS[v[2]]
		for f in def[0]:
			vals[f] = maxf(float(vals.get(f, 0.0)), float(def[0][f]) * env)
		jaw = maxf(jaw, float(def[1]) * env)
	return [vals, jaw]

func aplicar(id: String, ac, t: float, g: int) -> void:
	var st: Dictionary = estado[id]
	# expresión objetivo
	var nombre := "neutra"
	for e in st["expresiones"]:
		if e[0] <= t:
			nombre = e[1]
	var objetivo: Dictionary = EXPRESIONES.get(nombre, {})
	var act: Dictionary = st["actual"]
	var k := 1.0 - exp(-(1.0 / FPS) / 0.22)
	for f in objetivo:
		act[f] = lerpf(float(act.get(f, 0.0)), float(objetivo[f]), k)
	for f in act.keys():
		if not objetivo.has(f):
			act[f] = lerpf(float(act[f]), 0.0, k)
	# labios
	var vv := _viseme_en(st, t)
	var finales := act.duplicate()
	for f in vv[0]:
		finales[f] = clampf(float(finales.get(f, 0.0)) + float(vv[0][f]), 0.0, 1.0)
	# parpadeo (envolvente de 7 cuadros)
	var parp := 0.0
	for pt in st["parpadeos"]:
		var d: float = t - float(pt)
		if d >= 0.0 and d <= 0.23:
			parp = maxf(parp, 1.0 - absf(d / 0.115 - 1.0))
	if parp > 0.0:
		finales["Eye_Blink_L"] = maxf(float(finales.get("Eye_Blink_L", 0.0)), parp)
		finales["Eye_Blink_R"] = maxf(float(finales.get("Eye_Blink_R", 0.0)), parp)
	st["finales"] = finales
	# mandíbula
	var jaw_open := clampf(float(vv[1]) + float(act.get("Mouth_Lips_Part", 0.0)) * 0.3, 0.0, 1.0)
	st["mand_valor"] = lerpf(float(st["mand_valor"]) if st.has("mand_valor") else 0.0, jaw_open, 0.6)
	_mandibula(ac, st)
	_mirada(id, ac, t, st)

func _mandibula(ac, st: Dictionary) -> void:
	if ac.mand < 0:
		return
	if not st.has("eje_ok"):
		# eje de apertura: la derecha del personaje en el espacio del hueso; signo: el mentón baja
		var sk: Skeleton3D = ac.sk
		var reposo: Transform3D = sk.get_bone_global_rest(ac.mand)
		var der_sk: Vector3 = (sk.global_transform.basis.inverse() * ac.raiz.global_transform.basis.x).normalized()
		st["eje_mand"] = (reposo.basis.inverse() * der_sk).normalized()
		st["eje_ok"] = true
		st["signo_mand"] = 1.0
		# prueba del signo: se abre 20° y se mira si la punta del hueso hijo (lengua) baja en el mundo
		var q0: Quaternion = sk.get_bone_rest(ac.mand).basis.get_rotation_quaternion()
		var hijo := -1
		for i in sk.get_bone_count():
			if sk.get_bone_parent(i) == ac.mand:
				hijo = i
				break
		if hijo >= 0:
			var y0: float = (sk.global_transform * sk.get_bone_global_pose(hijo)).origin.y
			sk.set_bone_pose_rotation(ac.mand, q0 * Quaternion(st["eje_mand"], deg_to_rad(20)))
			var y1: float = (sk.global_transform * sk.get_bone_global_pose(hijo)).origin.y
			st["signo_mand"] = 1.0 if y1 < y0 else -1.0
			sk.set_bone_pose_rotation(ac.mand, q0)
	var q: Quaternion = ac.sk.get_bone_rest(ac.mand).basis.get_rotation_quaternion()
	ac.sk.set_bone_pose_rotation(ac.mand, q * Quaternion(st["eje_mand"], deg_to_rad(11.0) * float(st["mand_valor"]) * float(st["signo_mand"])))

func _mirada(id: String, ac, t: float, st: Dictionary) -> void:
	# cabeza y ojos hacia un objetivo con pesos suaves; sin objetivo = lo que dice el clip
	var m = null
	for mm in SB.get("miradas", []):
		if mm["actor"] == id and t >= float(mm["t0"]) - 0.4 and t <= float(mm["t1"]) + 0.4:
			m = mm
	var w := 0.0
	var objetivo := Vector3.ZERO
	if m != null:
		var a := (t - (float(m["t0"]) - 0.4)) / 0.4
		var b := ((float(m["t1"]) + 0.4) - t) / 0.4
		w = smoothstep(0.0, 1.0, clampf(minf(a, b), 0.0, 1.0))
		var o = m["a"]
		if o is String:
			var oa = SB["_actores_ref"][o]
			objetivo = oa.raiz.global_position + Vector3(0, float(m.get("alto", oa.altura * 0.9)), 0)
		else:
			objetivo = Vector3(o[0], o[1], o[2])
	var peso_cab := w * float(m.get("peso_cabeza", 0.55)) if m != null else 0.0
	var peso_oj := w * float(m.get("peso_ojos", 1.0)) if m != null else 0.0
	var sk: Skeleton3D = ac.sk
	# cabeza
	if peso_cab > 0.001:
		if not st.has("cab_fwd"):
			var rest: Transform3D = sk.get_bone_global_rest(ac.cabeza)
			var fwd_sk: Vector3 = (sk.global_transform.basis.inverse() * ac.raiz.global_transform.basis.z).normalized()
			st["cab_fwd"] = (rest.basis.inverse() * fwd_sk).normalized()
		var gp: Transform3D = sk.get_bone_global_pose(ac.cabeza)
		var origen_mundo: Vector3 = (sk.global_transform * gp).origin
		var hacia_mundo := (objetivo - origen_mundo).normalized()
		var hacia_sk: Vector3 = (sk.global_transform.basis.inverse() * hacia_mundo).normalized()
		var actual_sk: Vector3 = (gp.basis * (st["cab_fwd"] as Vector3)).normalized()
		var ang := actual_sk.angle_to(hacia_sk)
		var eje := actual_sk.cross(hacia_sk)
		if eje.length() > 1e-5 and ang > 1e-4:
			var lim := deg_to_rad(38.0)
			var q := Quaternion(eje.normalized(), minf(ang, lim) * peso_cab)
			var nuevo_basis := Basis(q) * gp.basis
			var par := sk.get_bone_parent(ac.cabeza)
			var pb := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
			var local := (pb.inverse() * nuevo_basis).get_rotation_quaternion()
			sk.set_bone_pose_rotation(ac.cabeza, local)
	# ojos
	for l in ["L", "R"]:
		var h: int = ac.ojo[l]
		if h < 0:
			continue
		sk.set_bone_pose_rotation(h, sk.get_bone_rest(h).basis.get_rotation_quaternion())
		if peso_oj > 0.001:
			if not st.has("ojo_fwd" + l):
				var rest2: Transform3D = sk.get_bone_global_rest(h)
				var fwd2: Vector3 = (sk.global_transform.basis.inverse() * ac.raiz.global_transform.basis.z).normalized()
				st["ojo_fwd" + l] = (rest2.basis.inverse() * fwd2).normalized()
			var gp2: Transform3D = sk.get_bone_global_pose(h)
			var o2: Vector3 = (sk.global_transform * gp2).origin
			var hacia2: Vector3 = (sk.global_transform.basis.inverse() * (objetivo - o2).normalized()).normalized()
			var act2: Vector3 = (gp2.basis * (st["ojo_fwd" + l] as Vector3)).normalized()
			var ang2 := act2.angle_to(hacia2)
			var eje2 := act2.cross(hacia2)
			if eje2.length() > 1e-5 and ang2 > 1e-4:
				var q2 := Quaternion(eje2.normalized(), minf(ang2, deg_to_rad(28.0)) * peso_oj)
				var nb := Basis(q2) * gp2.basis
				var par2 := sk.get_bone_parent(h)
				var pb2 := sk.get_bone_global_pose(par2).basis
				sk.set_bone_pose_rotation(h, (pb2.inverse() * nb).get_rotation_quaternion())

# ───────────────────────────────────────────────────────────── claves en la Animation
func claves(id: String, anim: Animation, t: float) -> void:
	var st: Dictionary = estado[id]
	var fin: Dictionary = st["finales"] if st.has("finales") else {}
	for tp in pistas[id]:
		if tp is String:
			continue
		var par: Array = pistas[id][tp]
		var v := float(fin.get(par[1], 0.0))
		(par[0] as MeshInstance3D).set_blend_shape_value(int(par[0].find_blend_shape_by_name(par[1])), v)
		var u: Array = ultimo[id][tp]
		if absf(v - float(u[0])) > 0.003 or u[1] < 0.0:
			if u[3] and float(u[2]) > float(u[1]):
				anim.track_insert_key(tp, float(u[2]), float(u[0]))
			anim.track_insert_key(tp, t, v)
			u[0] = v; u[1] = t; u[3] = false
		else:
			u[2] = t; u[3] = true
	var sk: Skeleton3D = null
	# huesos de cara/cabeza (la pose ya quedó puesta en el esqueleto)
	for nom in ["mand", "ojoL", "ojoR"]:
		if not pistas[id].has(nom):
			continue
		var hueso: int = -1
		var ac = SB["_actores_ref"][id]
		match nom:
			"mand": hueso = ac.mand
			"ojoL": hueso = ac.ojo["L"]
			"ojoR": hueso = ac.ojo["R"]
		if hueso >= 0:
			anim.rotation_track_insert_key(pistas[id][nom], t, ac.sk.get_bone_pose_rotation(hueso))
