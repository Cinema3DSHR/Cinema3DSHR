extends RefCounted
## Núcleo de la cinemática «Rally Convoy»: la ruta (generador de la Aventura), los siete autos con la física original y la IA
## original de Dream Racing, y el pelotón que los mantiene juntos. Lo usan la simulación sin imagen (pruebas) y la escena que se graba.

const AdvTrack := preload("res://game/adventure/adv_track.gd")
const AdvRoute := preload("res://game/adventure/adv_route.gd")
const AIDriver := preload("res://game/ai/ai_driver.gd")
const Car := preload("res://game/car/car.gd")
const CarBuild := preload("res://game/data/car_build.gd")
const AiCars := preload("res://game/data/ai_cars.gd")
const Profile := preload("res://game/data/profile.gd")
const VehicleParams := preload("res://game/physics/vehicle_params.gd")
const Peloton := preload("res://cine/peloton.gd")

## Los siete: id interno · nombre de la tienda de Dream Racing
const FLEET := [
	["pickup", "Yaguareté 4x4"], ["kodiak", "Kodiak Raid"], ["suv", "G4 4x4"], ["genesis", "Bisonte XR"],
	["hyper", "Aerion"], ["veltor_s", "Max Sport"], ["gt3", "GT3 RS"],
]
const STEP := 1.0 / 120.0

var vehicles: Dictionary
var track
var cars: Array = [] # Car
var drivers: Array = [] # AIDriver
var names: Array = []
var ids: Array = []
var pel # Peloton
var sim_t := 0.0
var toll_i := 0
var toll_s := 0.0
var anchor := 0
var hi := true # modelos originales completos (nunca los _lo)
var states: Array = []
var toll_node
var toll_arms: Array = []

func build(with_visuals := true) -> void:
	vehicles = JSON.parse_string(FileAccess.get_file_as_string("res://game/data/vehicles.json"))
	track = AdvTrack.new(0)
	for e in track.events:
		if str(e["t"]) == "toll":
			toll_i = int(e["i"])
	toll_s = float(track.cum[toll_i])
	anchor = track.i_start
	hi = with_visuals
	for k in FLEET.size():
		var id := str(FLEET[k][0])
		var st: Dictionary = Profile.new_car_state(id)
		var d: Dictionary = CarBuild.build_params(vehicles[id], st, AiCars.ASSISTS)
		var pp: Dictionary = st["paint"]
		var view = track.make_view()
		var car := Car.new(view, VehicleParams.from_dict(d), false, not with_visuals, Color(str(pp["body"])), Color(str(pp.get("rim", "#2a2d33"))), str(pp.get("finish", "gloss")))
		var sp := grid_pose(k)
		car.place(sp[0], sp[1], sp[2])
		car.restart_history(0.0)
		car.wall = float(track.half_width + track.shoulder) - 0.3 - 1.0
		var drv := AIDriver.new(track.make_view(), car.phys, {"skill": 0.84, "lane": 0.0, "aggr": 0.2})
		# agarre que la IA se permite usar: los de carrocería alta (camionetas, SUV) se descuelgan antes de lo que dice su perfil
		var mu_k: float = [0.72, 0.80, 0.85, 1.0, 1.0, 1.0, 1.0][k]
		drv.mu *= mu_k
		drv.prof = AIDriver.speed_profile(drv.track, snappedf(drv.mu, 0.02))
		drv.enabled = false
		car.driver = drv
		cars.append(car)
		drivers.append(drv)
		states.append(st)
		names.append(str(FLEET[k][1]))
		ids.append(id)
	var all_phys: Array = []
	for c in cars:
		all_phys.append(c.phys)
	for dr in drivers:
		dr.others = all_phys
	pel = Peloton.new()
	pel.s_toll = toll_s
	pel.go_t = 4.0
	var sg := 0.0
	for dr in drivers:
		dr.line_free = true
		dr.smooth_pedals = true
		dr._locate()
		sg += float(track.cum[mini(dr.idx, track.n - 1)])
	pel.setup(track, cars, drivers, sg / float(drivers.size()))

## Parrilla: los autos del carril derecho en la explanada de la estación (pegados al camino) y los del izquierdo sobre el camino,
## de a dos por fila, mirando hacia la ruta. Cada auto sale por su propio carril: nadie cruza por delante de otro.
func grid_pose(k: int) -> Array:
	var row := k / 2
	var i := anchor + 12 + row * 6
	var hw := float(track.hwa[i])
	var lat := hw + 1.9 if k % 2 == 0 else -1.9
	return track.pose_at(i, lat)

func step_to(t_target: float) -> void:
	while sim_t < t_target:
		for c in cars:
			c.step_and_record(STEP, sim_t)
		sim_t += STEP
		pel.update(STEP, sim_t)
