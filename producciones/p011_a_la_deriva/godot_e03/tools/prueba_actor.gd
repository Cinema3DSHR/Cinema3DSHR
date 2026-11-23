extends SceneTree
func _initialize() -> void:
	root.size = Vector2i(960, 540)
	DisplayServer.window_set_size(Vector2i(960, 540))
	var nave: Node = load("res://nave.tscn").instantiate()
	root.add_child(nave)
	var a := Actor3.new()
	var quien := OS.get_cmdline_user_args()[0]
	a.cargar(quien, "res://assets/personajes/%s.glb" % quien, "res://assets/personajes/%s_meta.json" % quien, root)
	a.raiz.rotation.y = atan2(1, 0)
	print("clips ", a.clips.keys().size(), " curl R ", a.curl["R"].size())
	var cam := Camera3D.new(); cam.current = true; root.add_child(cam)
	var ocultar := OS.get_cmdline_user_args()
	for nm in ocultar.slice(1):
		var mm = a.modelo.find_child(nm, true, false) if nm != "" else null
		if mm: mm.visible = false
	var tomas := [["idle", 10, Vector3(1.1, 0.25, 0.9), Vector3(0, 0.07, 0), 30], ["walk", 6, Vector3(1.0, 0.18, 0.5), Vector3(0.1, 0.1, 0), 40],
		["idle", 10, Vector3(1.2, 1.62, 0.35), Vector3(0, 1.58, 0), 30], ["idle", 10, Vector3(1.4, 1.0, 0.7), Vector3(0, 0.95, 0), 40], ["idle", 10, Vector3(3.2, 1.1, 1.2), Vector3(0, 0.9, 0), 50]]
	var i := 0
	for t in tomas:
		a.poner_pose(a.pose_clip(t[0], t[1], true))
		cam.global_position = t[2]; cam.look_at(t[3]); cam.fov = t[4]
		await process_frame; await process_frame; await process_frame
		root.get_texture().get_image().save_png("/tmp/pa_%d.png" % i); i += 1
	quit()
