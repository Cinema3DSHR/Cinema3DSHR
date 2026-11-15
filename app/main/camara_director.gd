class_name CamaraDirector
## Captura del punto de vista (botón COLOCAR CÁMARA) en coordenadas de BLENDER, que son las de la escena de producción.
## Godot usa los ejes de glTF (Y arriba). Blender: Z arriba. Conversión: (x, y, z)_blender = (x, −z, y)_godot.
## Las cámaras miran hacia −Z local con +Y local arriba en Godot, glTF y Blender: la orientación se convierte
## aplicando la misma matriz C a los ejes de la cámara. Óptica: la vista del editor es 16:9 (igual que el render) y
## Godot ajusta el FOV por altura; Blender usa un sensor de 36 mm de ANCHO.
## Ver estudio/blender/camara_director.py (la contraparte que aplica estos datos a la cámara de Blender).

const ASPECTO := 16.0 / 9.0
const SENSOR_MM := 36.0
const FORMATO := "estudio.camara/1"

static func a_blender(v: Vector3) -> Vector3:
	return Vector3(v.x, -v.z, v.y)

static func a_godot(v: Vector3) -> Vector3:
	return Vector3(v.x, v.z, -v.y)

static func _r(x: float, d := 6) -> float:
	return snappedf(x, pow(10.0, -d))

static func _v(v: Vector3, d := 6) -> Dictionary:
	return {"x": _r(v.x, d), "y": _r(v.y, d), "z": _r(v.z, d)}

## Euler XYZ como lo usa Blender (R = Rz · Ry · Rx), en grados.
static func euler_blender(b: Basis) -> Vector3:
	var r20 := clampf(b.x.z, -1.0, 1.0)
	var ry := asin(-r20)
	var rx: float
	var rz: float
	if absf(r20) < 0.999999:
		rx = atan2(b.y.z, b.z.z)
		rz = atan2(b.x.y, b.x.x)
	else:  # bloqueo de cardán: se fija Z = 0
		rx = atan2(-b.z.y, b.y.y)
		rz = 0.0
	return Vector3(rad_to_deg(rx), rad_to_deg(ry), rad_to_deg(rz))

static func lente_mm(fov_v_deg: float, aspecto := ASPECTO) -> float:
	var fov_h := 2.0 * atan(tan(deg_to_rad(fov_v_deg) / 2.0) * aspecto)
	return SENSOR_MM / 2.0 / tan(fov_h / 2.0)

static func fov_h_deg(fov_v_deg: float, aspecto := ASPECTO) -> float:
	return rad_to_deg(2.0 * atan(tan(deg_to_rad(fov_v_deg) / 2.0) * aspecto))

## Devuelve el diccionario del archivo director/cameras/camera_NNN.json (coordenadas de Blender).
static func capturar(cam: Camera3D, extra: Dictionary = {}) -> Dictionary:
	var t := cam.global_transform
	var g := t.basis.orthonormalized()
	var b := Basis(a_blender(g.x), a_blender(g.y), a_blender(g.z))
	var q := b.get_rotation_quaternion()
	var p := a_blender(t.origin)
	var fov_v := cam.fov
	var d := {
		"formato": FORMATO,
		"position": _v(p),
		"rotation": _v(euler_blender(b), 4),
		"rotation_mode": "XYZ",
		"quaternion": [_r(q.w, 8), _r(q.x, 8), _r(q.y, 8), _r(q.z, 8)],
		"forward": _v(-b.z),
		"up": _v(b.y),
		"fov": _r(fov_v, 4),
		"fov_v_deg": _r(fov_v, 4),
		"fov_h_deg": _r(fov_h_deg(fov_v), 4),
		"lens_mm": _r(lente_mm(fov_v), 4),
		"sensor_mm": SENSOR_MM,
		"sensor_fit": "HORIZONTAL (AUTO, imagen apaisada)",
		"aspect": _r(ASPECTO, 6),
		"resolution": [1280, 720],
		"coordinates": "Blender: metros, Z arriba; rotation = rotation_euler XYZ de la cámara de Blender",
		"created": Time.get_datetime_string_from_system(true) + "Z",
		"godot": {"origin": [_r(t.origin.x), _r(t.origin.y), _r(t.origin.z)],
			"basis_columns": [[_r(g.x.x), _r(g.x.y), _r(g.x.z)], [_r(g.y.x), _r(g.y.y), _r(g.y.z)], [_r(g.z.x), _r(g.z.y), _r(g.z.z)]]},
	}
	d.merge(extra, true)
	return d

## Lleva una cámara de Godot al punto de vista guardado (para RECUPERAR una cámara del director).
static func aplicar(cam: Camera3D, d: Dictionary) -> void:
	var q: Array = d.get("quaternion", [])
	var b: Basis
	if q.size() == 4:
		b = Basis(Quaternion(q[1], q[2], q[3], q[0]))
	else:
		var r: Dictionary = d.get("rotation", {})
		b = _euler_xyz(Vector3(r.get("x", 0.0), r.get("y", 0.0), r.get("z", 0.0)))   # en ejes de Blender
	var gb := Basis(a_godot(b.x), a_godot(b.y), a_godot(b.z))
	var p: Dictionary = d.get("position", {})
	cam.global_transform = Transform3D(gb, a_godot(Vector3(p.get("x", 0.0), p.get("y", 0.0), p.get("z", 0.0))))
	cam.fov = float(d.get("fov_v_deg", d.get("fov", cam.fov)))

static func _euler_xyz(gr: Vector3) -> Basis:
	var x := deg_to_rad(gr.x)
	var y := deg_to_rad(gr.y)
	var z := deg_to_rad(gr.z)
	var rx := Basis(Vector3(1, 0, 0), Vector3(0, cos(x), sin(x)), Vector3(0, -sin(x), cos(x)))
	var ry := Basis(Vector3(cos(y), 0, -sin(y)), Vector3(0, 1, 0), Vector3(sin(y), 0, cos(y)))
	var rz := Basis(Vector3(cos(z), sin(z), 0), Vector3(-sin(z), cos(z), 0), Vector3(0, 0, 1))
	return rz * ry * rx
