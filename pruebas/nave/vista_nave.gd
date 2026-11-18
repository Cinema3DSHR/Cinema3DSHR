## Mira un GLB desde cámaras dadas en coordenadas de BLENDER (x, y, z; z arriba) y guarda capturas.
## CAMS='[["nombre", [px,py,pz], [ox,oy,oz], lente_mm], ...]'  (lente en mm, sensor de 36 mm)
## xvfb-run -a godot --path pruebas/nave --rendering-driver opengl3 --script res://vista_nave.gd -- ESC.glb PREFIJO ancho alto
extends SceneTree

var cams := []
var cam: Camera3D
var salida := ""
var paso := 0
var esperar := 0

func _b2g(v) -> Vector3:
	return Vector3(v[0], v[2], -v[1])

func _initialize() -> void:
	var a := OS.get_cmdline_user_args()
	salida = a[1]
	var w := int(a[2]); var h := int(a[3])
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	root.mesh_lod_threshold = 0.0
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	doc.append_from_file(a[0], st)
	var esc := doc.generate_scene(st)
	root.add_child(esc)
	# igual que el EDITOR 3D de la app (editor.gd): intensidades de referencia para las luces de Blender
	for n in esc.find_children("*", "Light3D", true, false):
		n.shadow_enabled = false
		if n is OmniLight3D:
			n.light_energy = 0.6
			n.omni_range = 5.0
		elif n is SpotLight3D:
			n.light_energy = 1.0
			n.spot_range = 12.0
		elif n is DirectionalLight3D:
			n.light_energy = 0.8
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.55, 0.66, 0.82)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.8, 0.8, 0.85)
	e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	root.add_child(env)
	var sol := DirectionalLight3D.new()
	sol.rotation_degrees = Vector3(-55, 25, 0)
	sol.light_energy = 0.6
	root.add_child(sol)
	cam = Camera3D.new()
	cam.far = 2000.0
	cam.near = 0.03
	root.add_child(cam)
	cams = JSON.parse_string(OS.get_environment("CAMS"))
	_poner(0)

func _poner(i: int) -> void:
	var c = cams[i]
	cam.position = _b2g(c[1])
	cam.look_at(_b2g(c[2]), Vector3.UP)
	var lente: float = c[3]
	# vertical: FOV vertical de un sensor de 36 mm de ancho en cuadro 9:16 (el lado largo es el alto)
	var alto_sensor := 36.0 * (float(root.size.y) / float(root.size.x)) if root.size.y > root.size.x else 36.0 * float(root.size.y) / float(root.size.x)
	cam.fov = rad_to_deg(2.0 * atan(alto_sensor / (2.0 * lente)))

func _process(_d: float) -> bool:
	esperar += 1
	if esperar < 8: return false
	esperar = 0
	root.get_texture().get_image().save_png("%s_%s.png" % [salida, cams[paso][0]])
	paso += 1
	if paso >= cams.size(): return true
	_poner(paso)
	return false
