## Actor del capítulo 3: modelo CC4 (GLB de Blender) + clips de Mixamo ya retargeteados (c_<nombre>), con movimiento de raíz extraído.
## Se «hornea» cuadro a cuadro: cada cuadro se compone la pose (mezcla de clips con fundido), se pone en el esqueleto, se leen manos/cabeza
## (para objetos agarrados y mirada) y se guardan claves en la Animation de la escena. Todo en 30 cuadros/s.
class_name Actor3
extends RefCounted

const FPS := 30.0

var id := ""
var raiz: Node3D                # nodo con la posición/giro del personaje en el piso (frente = +Z)
var modelo: Node3D
var sk: Skeleton3D
var meta := {}                  # clips: nombre → {frames, desp, raiz_xy}
var altura := 1.8
var escala := 1.0
var clips := {}                 # nombre → {rot: {hueso_idx: Array[Quaternion]}, pos: {hueso_idx: Array[Vector3]}, n: cuadros, raiz: Array[Vector2] (x local, z local, m)}
var hueso_cadera := -1
var base_pose := {}             # hueso → Quaternion de reposo/pos
var mallas_con_forma := []      # [MeshInstance3D, {nombre_forma: índice}]
var ruta_sk := ""               # ruta del esqueleto relativa a la raíz de la escena
var anim: Animation
var mano := {"R": -1, "L": -1}
var cabeza := -1
var mand := -1
var ojo := {"L": -1, "R": -1}

func cargar(id_: String, glb: String, meta_json: String, padre: Node) -> void:
	id = id_
	raiz = Node3D.new()
	raiz.name = id
	padre.add_child(raiz)
	modelo = (load(glb) as PackedScene).instantiate()
	modelo.name = "Modelo"
	raiz.add_child(modelo)
	var ap: AnimationPlayer = modelo.find_children("*", "AnimationPlayer", true, false)[0]
	sk = modelo.find_children("*", "Skeleton3D", true, false)[0]
	var js = JSON.parse_string(FileAccess.get_file_as_string(meta_json))
	altura = float(js["altura"])
	meta = js["clips"]
	hueso_cadera = sk.find_bone("EM3D_Base_Hip")
	cabeza = sk.find_bone("EM3D_Base_Head")
	mand = sk.find_bone("EM3D_Base_JawRoot")
	mano["R"] = sk.find_bone("EM3D_Base_R_Hand")
	mano["L"] = sk.find_bone("EM3D_Base_L_Hand")
	ojo["L"] = sk.find_bone("EM3D_Base_L_Eye")
	ojo["R"] = sk.find_bone("EM3D_Base_R_Eye")
	for i in sk.get_bone_count():
		base_pose[i] = sk.get_bone_rest(i)
	for nm in ap.get_animation_list():
		clips[String(nm).trim_prefix("c_")] = _muestrear(ap.get_animation(nm), String(nm).trim_prefix("c_"))
	ap.get_parent().remove_child(ap)
	ap.free()
	detectar_dedos()
	for m in modelo.find_children("*", "MeshInstance3D", true, false):
		var mi: MeshInstance3D = m
		if mi.skin != null:
			mi.custom_aabb = AABB(Vector3(-120, -120, -120), Vector3(240, 240, 240))      # malla en cm dentro de un esqueleto ×0,01: evita que el recorte la oculte
		if mi.mesh and mi.mesh.get_blend_shape_count() > 0:
			var d := {}
			for i in mi.mesh.get_blend_shape_count():
				d[String(mi.mesh.get_blend_shape_name(i))] = i
			mallas_con_forma.append([mi, d])

func _muestrear(a: Animation, nombre: String) -> Dictionary:
	var n := int(round(a.length * FPS)) + 1
	var r := {"n": n, "rot": {}, "pos": {}, "raiz": []}
	for t in a.get_track_count():
		var ruta := String(a.track_get_path(t))
		var hueso := sk.find_bone(ruta.get_slice(":", 1))
		if hueso < 0:
			continue
		var tipo := a.track_get_type(t)
		if tipo == Animation.TYPE_ROTATION_3D:
			var arr: Array = []
			for k in n:
				arr.append(a.rotation_track_interpolate(t, minf(k / FPS, a.length)))
			r["rot"][hueso] = arr
		elif tipo == Animation.TYPE_POSITION_3D:
			var arr2: Array = []
			for k in n:
				arr2.append(a.position_track_interpolate(t, minf(k / FPS, a.length)))
			r["pos"][hueso] = arr2
	# movimiento de raíz: Blender (dx, dy) en el marco del personaje de reposo (frente −Y) → local Godot (x = dx, z = −dy)
	var rx: Array = meta[nombre].get("raiz_xy", [])
	var cuadros: int = rx.size() / 2
	for k in n:
		var kk := mini(k, cuadros - 1)
		if cuadros == 0:
			r["raiz"].append(Vector2.ZERO)
		else:
			r["raiz"].append(Vector2(float(rx[kk * 2]), -float(rx[kk * 2 + 1])))
	return r

## Pose de un clip en el cuadro k (con repetición opcional). Devuelve {rot: {hueso: Quaternion}, pos: {hueso: Vector3}}
func pose_clip(nombre: String, k: int, repetir: bool) -> Dictionary:
	var c: Dictionary = clips[nombre]
	var n: int = c["n"]
	var kk := k
	if repetir:
		kk = k % maxi(n - 1, 1)
	else:
		kk = mini(k, n - 1)
	var rot := {}
	for h in c["rot"]:
		rot[h] = c["rot"][h][kk]
	var pos := {}
	for h in c["pos"]:
		pos[h] = c["pos"][h][kk]
	return {"rot": rot, "pos": pos}

func raiz_clip(nombre: String, k: int) -> Vector2:
	var c: Dictionary = clips[nombre]
	return c["raiz"][mini(k, int(c["n"]) - 1)]

func duracion_cuadros(nombre: String) -> int:
	return int(clips[nombre]["n"])

static func mezcla(p0: Dictionary, p1: Dictionary, w: float) -> Dictionary:
	var rot := {}
	for h in p1["rot"]:
		rot[h] = (p0["rot"][h] as Quaternion).slerp(p1["rot"][h], w) if p0["rot"].has(h) else p1["rot"][h]
	var pos := {}
	for h in p1["pos"]:
		pos[h] = (p0["pos"][h] as Vector3).lerp(p1["pos"][h], w) if p0["pos"].has(h) else p1["pos"][h]
	return {"rot": rot, "pos": pos}

func poner_pose(p: Dictionary) -> void:
	for h in p["rot"]:
		sk.set_bone_pose_rotation(h, p["rot"][h])
	for h in p["pos"]:
		sk.set_bone_pose_position(h, p["pos"][h])

# ───────────────────────────────────────────────────────────── agarre: dedos que se cierran sobre un objeto
var curl := {"R": [], "L": []}      # [{hueso, eje (local), signo, grados}]

func detectar_dedos() -> void:
	## Para cada falange se prueba girar ±X/±Y/±Z y se elige el eje que acerca la punta del dedo a la palma.
	for lado in ["R", "L"]:
		var mano_i: int = mano[lado]
		if mano_i < 0:
			continue
		var palma_a: Vector3 = _g(mano_i).origin
		var mid1 := sk.find_bone("EM3D_Base_%s_Mid1" % lado)
		var palma: Vector3 = (palma_a + _g(mid1).origin) * 0.5
		for dedo in ["Thumb", "Index", "Mid", "Ring", "Pinky"]:
			var grados := [40.0, 55.0, 40.0] if dedo != "Thumb" else [20.0, 28.0, 25.0]
			for fi in 3:
				var b := sk.find_bone("EM3D_Base_%s_%s%d" % [lado, dedo, fi + 1])
				if b < 0:
					continue
				var punta_b := sk.find_bone("EM3D_Base_%s_%s%d" % [lado, dedo, 3])
				var q0 := sk.get_bone_pose_rotation(b)
				var base_d: float = _g(punta_b).origin.distance_to(palma)
				var mejor := 1e9
				var mejor_eje := Vector3.RIGHT
				var mejor_signo := 1.0
				for eje in [Vector3.RIGHT, Vector3.UP, Vector3.BACK]:
					for sg in [1.0, -1.0]:
						sk.set_bone_pose_rotation(b, q0 * Quaternion(eje, deg_to_rad(35.0) * sg))
						var d: float = _g(punta_b).origin.distance_to(palma)
						if d < mejor:
							mejor = d
							mejor_eje = eje
							mejor_signo = sg
				sk.set_bone_pose_rotation(b, q0)
				curl[lado].append({"hueso": b, "eje": mejor_eje, "signo": mejor_signo, "grados": grados[fi]})

func _g(i: int) -> Transform3D:
	return sk.get_bone_global_pose(i)

func aplicar_agarre(lado: String, w: float) -> void:
	for c in curl[lado]:
		var q: Quaternion = sk.get_bone_pose_rotation(c["hueso"])
		sk.set_bone_pose_rotation(c["hueso"], q * Quaternion(c["eje"], deg_to_rad(float(c["grados"])) * float(c["signo"]) * w))
