"""Escenario de «Operación Tren Fantasma»: llanura al pie de la sierra con la vía, la ruta paralela y el tren.

Construye (todo parametrizado por `secuencia` y `semilla`):
- Terreno: llanura con lomas suaves que sube a montañas lejanas; el corredor de la vía y la ruta queda plano.
- Vía: terraplén de balasto, durmientes y dos rieles a lo largo de toda la curva; postes de telégrafo.
- Ruta paralela (asfalto, banquinas, líneas), camino secundario de tierra hacia las casas.
- Decorado: cortinas de álamos y montes de árboles (Sweet Home 3D de Nexus), casas de campo con puertas y ventanas
  Sweet Home, galpón, tanque australiano y molino; cielo físico con sol de tarde y nubes.
- Tren (estudio/blender/tren.py): locomotora + 20 vagones con autos de Dream Rally, animado sobre la vía.
- Escolta: blindados con ruedas de Dream Rally y motos con pilotos de casco negro, animados por la ruta.
Los vagones, blindados y motos se devuelven como «móviles» para las cámaras de seguimiento.
"""
from __future__ import annotations
import math
import random
import bpy
from mathutils import Vector, noise
from mathutils.kdtree import KDTree
from estudio.blender import kit as K, importar as I, tren as TR, vehiculos_dr as VD, via_ferrea as VF, paisaje as PA, salto_tren as ST
from estudio import fisica_dr as FD

PARAMETROS = {"secuencia": 1, "semilla": 3, "velocidad_tren": 21.0, "s_cabeza_inicial": 620.0, "duracion_s": 75.0,
              "lado_ruta": 34.0, "arboles": 900, "nubes": 26}

# Recursos externos que usa (para bajar sólo esto en Actions)
DEPENDENCIAS = [
    "mixamo:modelos_pelicula/locomotora_diesel.glb", "mixamo:modelos_pelicula/vagon_plano.glb",
    "mixamo:modelos_pelicula/vagon_cerrado.glb", "mixamo:modelos_pelicula/vehiculo_blindado_policial.glb",
    "rally:godot/game/models/cars/buggy.json", "rally:godot/game/models/cars/buggy.glb", "rally:godot/game/models/cars/buggy_lo.glb",
    "rally:godot/game/models/cars/camo.json", "rally:godot/game/models/cars/camo.glb", "rally:godot/game/models/cars/camo_lo.glb",
    "rally:godot/game/models/cars/clasico60.json", "rally:godot/game/models/cars/clasico60.glb", "rally:godot/game/models/cars/clasico60_lo.glb",
    "rally:godot/game/models/cars/f1.json", "rally:godot/game/models/cars/f1.glb", "rally:godot/game/models/cars/f1_lo.glb",
    "rally:godot/game/models/cars/genesis.json", "rally:godot/game/models/cars/genesis.glb", "rally:godot/game/models/cars/genesis_lo.glb",
    "rally:godot/game/models/cars/gt.json", "rally:godot/game/models/cars/gt.glb", "rally:godot/game/models/cars/gt_lo.glb",
    "rally:godot/game/models/cars/gt3.json", "rally:godot/game/models/cars/gt3.glb", "rally:godot/game/models/cars/gt3_lo.glb",
    "rally:godot/game/models/cars/hatch.json", "rally:godot/game/models/cars/hatch.glb", "rally:godot/game/models/cars/hatch_lo.glb",
    "rally:godot/game/models/cars/hatch2.json", "rally:godot/game/models/cars/hatch2.glb", "rally:godot/game/models/cars/hatch2_lo.glb",
    "rally:godot/game/models/cars/hyper.json", "rally:godot/game/models/cars/hyper.glb", "rally:godot/game/models/cars/hyper_lo.glb",
    "rally:godot/game/models/cars/kl5.json", "rally:godot/game/models/cars/kl5.glb", "rally:godot/game/models/cars/kl5_lo.glb",
    "rally:godot/game/models/cars/kodiak.json", "rally:godot/game/models/cars/kodiak.glb", "rally:godot/game/models/cars/kodiak_lo.glb",
    "rally:godot/game/models/cars/moust.json", "rally:godot/game/models/cars/moust.glb", "rally:godot/game/models/cars/moust_lo.glb",
    "rally:godot/game/models/cars/muscle.json", "rally:godot/game/models/cars/muscle.glb", "rally:godot/game/models/cars/muscle_lo.glb",
    "rally:godot/game/models/cars/pickup.json", "rally:godot/game/models/cars/pickup.glb", "rally:godot/game/models/cars/pickup_lo.glb",
    "rally:godot/game/models/cars/police.json", "rally:godot/game/models/cars/police.glb", "rally:godot/game/models/cars/police_lo.glb",
    "rally:godot/game/models/cars/pro_gt.json", "rally:godot/game/models/cars/pro_gt.glb", "rally:godot/game/models/cars/pro_gt_lo.glb",
    "rally:godot/game/models/cars/rally80.json", "rally:godot/game/models/cars/rally80.glb", "rally:godot/game/models/cars/rally80_lo.glb",
    "rally:godot/game/models/cars/strix.json", "rally:godot/game/models/cars/strix.glb", "rally:godot/game/models/cars/strix_lo.glb",
    "rally:godot/game/models/cars/suv.json", "rally:godot/game/models/cars/suv.glb", "rally:godot/game/models/cars/suv_lo.glb",
    "rally:godot/game/models/cars/titan.json", "rally:godot/game/models/cars/titan.glb", "rally:godot/game/models/cars/titan_lo.glb",
    "rally:godot/game/models/cars/torito.json", "rally:godot/game/models/cars/torito.glb", "rally:godot/game/models/cars/torito_lo.glb",
    "rally:godot/game/models/cars/trilux.json", "rally:godot/game/models/cars/trilux.glb", "rally:godot/game/models/cars/trilux_lo.glb",
    "rally:godot/game/models/cars/trilux_gt.json", "rally:godot/game/models/cars/trilux_gt.glb", "rally:godot/game/models/cars/trilux_gt_lo.glb",
    "rally:godot/game/models/cars/trilux_s.json", "rally:godot/game/models/cars/trilux_s.glb", "rally:godot/game/models/cars/trilux_s_lo.glb",
    "rally:godot/game/models/cars/veltor.json", "rally:godot/game/models/cars/veltor.glb", "rally:godot/game/models/cars/veltor_lo.glb",
    "rally:godot/game/models/cars/veltor_gtr.json", "rally:godot/game/models/cars/veltor_gtr.glb", "rally:godot/game/models/cars/veltor_gtr_lo.glb",
    "rally:godot/game/models/cars/veltor_s.json", "rally:godot/game/models/cars/veltor_s.glb", "rally:godot/game/models/cars/veltor_s_lo.glb",
    # física, cabina y pilotos de Dream Rally (estudio/fisica_dr) y lo del salto (secuencia 3)
    "rally:godot/game/physics/", "rally:godot/game/data/", "rally:godot/game/car/", "rally:godot/game/models/pilot.glb",
    "rally:godot/game/models/pilot_lo.glb", "rally:godot/game/models/pilot_Ch20_1001_Diffuse.jpg",
    "rally:godot/game/models/pilot_Ch20_1001_Normal.jpg", "rally:godot/game/models/pilot_ao_met_rough_Ch20_1001_Glossiness.jpg",
    "rally:godot/game/models/cabin/", "rally:godot/game/models/paint/", "rally:godot/game/models/cars/*.json",
    "rally:godot/game/models/cars/*.png", "rally:godot/game/models/cars/truck.glb", "rally:godot/game/models/cars/truck_lo.glb",
    "mixamo:vehiculos_pelicula/auto_rampa/", "mixamo:modelos_pelicula/trailer_plano_camion.glb",
    "mixamo:personajes_pelicula/protagonista_femenina/", "mixamo:personajes_pelicula/protagonista_masculino/",
    "sh3d:models/tree_lombardy_poplar.glb", "sh3d:models/tree_tree.glb", "sh3d:models/tree_birch.glb",
    "sh3d:models/tree_weeping_willow.glb", "sh3d:models/tree_black_tupelo.glb", "sh3d:models/tree_quaking_aspen.glb",
    "sh3d:models/tree_sassafras.glb", "sh3d:models/sc_pine.glb", "sh3d:models/sc_cypress.glb", "sh3d:models/sc_acacia.glb",
    "sh3d:models/sc_lavender_bush.glb", "sh3d:models/door_front_door.glb",
    "sh3d:models/window_five_panes_window.glb", "sh3d:models/window_double_small_window_with_sill.glb",
    "sh3d:models/door_garage_door.glb", "sh3d:models/sc_yamaha_yzr_r6.glb", "sh3d:models/fence_fence_post.glb",
]

# Composición: 0 = locomotora. Viajan los 28 autos de Dream Rally (todos menos el camión Mamut, que es el camión de la
# secuencia 2): dos por plataforma; la 9 lleva un solo deportivo adelante (atrás aterriza el auto rampa en la secuencia 3)
COMPOSICION = ["loco", "plano", "plano", "cerrado", "plano", "plano", "plano", "cerrado", "plano", "plano", "plano",
               "cerrado", "plano", "cerrado", "cerrado", "plano", "plano", "plano", "plano", "plano", "plano"]
CARGA = {1: ["gt3", "kodiak"], 2: ["hyper", "suv"], 4: ["veltor_s", "muscle"], 5: ["titan", "strix"],
         6: ["kl5", "trilux_gt"], 8: ["rally80", "pro_gt"], 9: ["veltor_gtr"], 10: ["gt", "genesis"],
         12: ["torito", "clasico60"], 15: ["police", "camo"], 16: ["veltor", "hatch2"], 17: ["pickup", "hatch"],
         18: ["buggy", "trilux"], 19: ["f1", "trilux_s"], 20: ["moust"]}
VIA = [(-1600, -260), (-1000, -210), (-500, -90), (0, 0), (420, 110), (820, 170), (1220, 300), (1620, 500),
       (2000, 790), (2350, 1150)]


# blindado de la película con la física de Dream Rally del Cóndor T6 («camo»), con sus medidas y su peso
PARAMS_BLINDADO = {"wheelBase": 3.27, "weightFront": 0.474, "trackF": 1.72, "trackR": 1.72, "wheelRadius": 0.46,
                   "mass": 4300.0, "comHeight": 0.95, "rideOffset": 0.0, "Ixx": 2200.0, "Iyy": 7800.0, "Izz": 8600.0}


def _sh3d(nombre: str, col_proto: dict):
    """Colección prototipo con un modelo Sweet Home (se instancia sin copiar mallas)."""
    if nombre in col_proto:
        return col_proto[nombre]
    c = K.prototipo(f"PROTO_{nombre}")
    I.importar(f"sh3d:models/{nombre}.glb", c)
    for o in c.objects:          # Sweet Home viene en Y arriba → el importador ya lo pone en Z arriba
        o["visor_lod"] = "bajo"
    if nombre.startswith(("tree_", "sc_pine", "sc_acacia", "sc_cypress", "bush_", "sc_lavender")):
        PA.arbolar(c, semilla=len(col_proto) + 1)      # copa sólida (las hojas de Sweet Home son triángulos sueltos)
    col_proto[nombre] = c
    return c


def _tira(nombre, via, s0, s1, paso, perfil, mat, col, desp=0.0, z0=0.0):
    """Malla extruida a lo largo de la vía: perfil [(x_lateral, z)…] (x positivo = derecha)."""
    import bmesh
    bm = bmesh.new()
    anillos = []
    s = s0
    while s <= s1:
        p, t = via.en(s)
        n = Vector((t.y, -t.x, 0)).normalized()
        anillos.append([bm.verts.new(p + n * (desp + x) + Vector((0, 0, z0 + z))) for x, z in perfil])
        s += paso
    for a, b in zip(anillos, anillos[1:]):
        for j in range(len(perfil) - 1):
            bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (l.vert.co.x * 0.25, l.vert.co.y * 0.25)
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nombre, me)
    me.materials.append(mat)
    col.objects.link(ob)
    return ob


def _cajas_por_via(nombre, via, s0, s1, paso, tam, mat, col, desp=0.0, z=0.0, alternar=0.0):
    """Muchas cajas (líneas, postes) en una sola malla. tam = (lateral, a lo largo, alto)."""
    lote = VF.Lote()
    s, k = s0, 0
    while s <= s1:
        p, t, n, ang = VF.marco(via, s)
        lote.caja(p + n * (desp + (alternar if k % 2 else 0)) + Vector((0, 0, z)), ang, tam)
        s += paso
        k += 1
    return lote.objeto(nombre, mat, col)


def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    rnd = random.Random(p["semilla"])
    s = K.bpy.context.scene
    fps = s.render.fps
    col = K.coleccion("ESCENARIO_tren_fantasma")
    c_terr, c_via, c_deco, c_veh = (K.coleccion(n, col) for n in ("terreno", "via_y_ruta", "decorado", "vehiculos"))
    protos = {}
    via = TR.Via([(x, y, 0) for x, y in VIA])
    if p["secuencia"] == 3:
        # el camión va por el carril de la izquierda a la distancia que pide el salto (ruta pegada a las vías)
        pv = ST.prevuelo(fps, p.get("t_acelera", 15.0))
        p["lado_ruta"] = (-pv["x"] + 0.45) + 1.875
    M = K.material

    # ------------------------------------------------------------------ cielo físico + sol de tarde
    w = bpy.data.worlds.new("cielo_tarde")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    sky = nt.nodes.new("ShaderNodeTexSky")
    for tipo in ("MULTIPLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try:
            sky.sky_type = tipo
            break
        except TypeError:
            continue
    elev, azim = math.radians(24), math.radians(215)
    for attr, val in (("sun_elevation", elev), ("sun_rotation", azim), ("altitude", 300.0), ("air_density", 1.0),
                      ("dust_density", 0.9), ("sun_intensity", 0.6)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.12          # el cielo de dispersión múltiple ya es físico: con más se lava todo
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    sol = K.luz("sol", "SUN", (0, 0, 100), 2.8, (1.0, 0.88, 0.72), col,
                rot=(math.pi / 2 - elev, 0, azim + math.pi / 2))
    sol.data.angle = math.radians(0.8)

    # ------------------------------------------------------------------ terreno (llanura → lomas → sierra)
    pts_via = [via.en(si)[0] for si in range(0, int(via.largo), 20)]
    kd = KDTree(len(pts_via))
    for i, q in enumerate(pts_via):
        kd.insert((q.x, q.y, 0), i)
    kd.balance()
    import bmesh
    bm = bmesh.new()
    X0, X1, Y0, Y1, paso = -2600, 3400, -2200, 3200, 30
    nx, ny = int((X1 - X0) / paso) + 1, int((Y1 - Y0) / paso) + 1
    grid, campo = [], []
    for j in range(ny):
        fila = []
        for i in range(nx):
            x, y = X0 + i * paso, Y0 + j * paso
            _, _, d = kd.find((x, y, 0))
            plano = min(1.0, max(0.0, (d - 70.0) / 260.0)) ** 1.6       # corredor plano de 70 m
            lomas = 9.0 * noise.noise(Vector((x / 420, y / 420, 0.3))) + 4.0 * noise.noise(Vector((x / 160, y / 160, 1.7)))
            # sierra: crece con la distancia al corredor, más del lado izquierdo (norte)
            lejos = max(0.0, d - 700.0) / 900.0
            sierra = (lejos ** 1.5) * (260 + 180 * noise.noise(Vector((x / 900, y / 900, 4.0)))) * (1.3 if y > 0 else 0.8)
            cresta = abs(noise.noise(Vector((x / 340, y / 340, 7.0)))) * 90 * min(1.0, lejos)
            fila.append(bm.verts.new((x, y, plano * (lomas + sierra + cresta) - 0.05)))
            campo.append(min(1.0, max(0.0, (d - 45.0) / 60.0)) * (0.0 if lejos > 0.35 else 1.0))
        grid.append(fila)
    for j in range(ny - 1):
        for i in range(nx - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    me = bpy.data.meshes.new("terreno")
    bm.to_mesh(me)
    bm.free()
    for f in me.polygons:
        f.use_smooth = True
    terreno = bpy.data.objects.new("terreno", me)
    c_terr.objects.link(terreno)
    at = me.attributes.new("campo", "FLOAT", "POINT")         # 1 = parcelas cultivadas · 0 = pastura (corredor, sierra)
    at.data.foreach_set("value", campo)
    me.materials.append(PA.material_campos())
    terreno["visor_lod"] = "bajo"

    # ------------------------------------------------------------------ vía férrea con detalle real (estudio/blender/via_ferrea.py)
    s_det0 = p["s_cabeza_inicial"] - 420.0
    s_det1 = p["s_cabeza_inicial"] + p["velocidad_tren"] * p["duracion_s"] + 120.0
    vf = VF.construir(via, c_via, s_detalle0=s_det0, s_detalle1=s_det1, lado_ruta=p["lado_ruta"], semilla=p["semilla"],
                 pasos_a_nivel=(p["s_cabeza_inicial"] + 760.0,), senales=(p["s_cabeza_inicial"] + 420.0, p["s_cabeza_inicial"] + 1380.0))

    # ------------------------------------------------------------------ ruta paralela
    lado = p["lado_ruta"]
    asfalto = M("asfalto_ruta", (0.07, 0.07, 0.075), 0.62, ruido=0.25, escala_ruido=3, relieve=0.08)
    ripio = M("banquina", (0.36, 0.32, 0.26), 0.95, ruido=0.4, escala_ruido=4)
    blanco = M("pintura_ruta", (0.85, 0.85, 0.82), 0.5)
    _tira("banquinas", via, 0, via.largo, 4.0, [(-6.5, 0.02), (6.5, 0.02)], ripio, c_via, desp=lado)
    _tira("ruta", via, 0, via.largo, 4.0, [(-3.75, 0.06), (3.75, 0.06)], asfalto, c_via, desp=lado)
    for b in (-3.55, 3.55):
        _tira(f"linea_borde_{b}", via, 0, via.largo, 4.0, [(-0.08, 0.075), (0.08, 0.075)], blanco, c_via, desp=lado + b)
    _cajas_por_via("linea_central", via, 0, via.largo, 9.0, (0.12, 4.5, 0.02), blanco, c_via, desp=lado, z=0.075)

    # ------------------------------------------------------------------ casas de campo, galpón, tanque y molino
    revoque = M("revoque", (0.82, 0.76, 0.66), 0.9, ruido=0.15, escala_ruido=3, relieve=0.1)
    teja = M("teja", (0.48, 0.18, 0.1), 0.7, ladrillo=((0.4, 0.14, 0.08), 6.0), relieve=0.2)
    chapa = M("chapa", (0.55, 0.57, 0.6), 0.4, 0.8, ruido=0.2)
    casas = []
    for k, sc in enumerate((380, 760, 1010, 1330, 1720, 2050)):
        pp, t = via.en(sc)
        n = Vector((t.y, -t.x, 0)).normalized()
        dist = lado + 40 + rnd.uniform(0, 60) if k % 2 == 0 else -(55 + rnd.uniform(0, 70))
        c = pp + n * dist
        ang = math.atan2(t.y, t.x) + rnd.uniform(-0.3, 0.3)
        ancho, prof, alto = rnd.uniform(10, 14), rnd.uniform(7, 9), 3.0
        casa = K.vacio(f"casa_{k}", (c.x, c.y, 0), c_deco)
        casa.rotation_euler.z = ang
        partes = [K.caja(f"casa_{k}_muros", (0, 0, alto / 2), (ancho, prof, alto), revoque, c_deco, bisel=0.03)]
        # techo a dos aguas
        bmr = bmesh.new()
        h = 2.2
        v = [bmr.verts.new(q) for q in ((-ancho / 2 - 0.5, -prof / 2 - 0.6, alto), (ancho / 2 + 0.5, -prof / 2 - 0.6, alto),
                                       (ancho / 2 + 0.5, prof / 2 + 0.6, alto), (-ancho / 2 - 0.5, prof / 2 + 0.6, alto),
                                       (-ancho / 2 - 0.5, 0, alto + h), (ancho / 2 + 0.5, 0, alto + h))]
        for f in ((0, 1, 5, 4), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5)):
            bmr.faces.new([v[i] for i in f])
        mr = bpy.data.meshes.new(f"techo_{k}")
        bmr.to_mesh(mr)
        bmr.free()
        techo = bpy.data.objects.new(f"casa_{k}_techo", mr)
        mr.materials.append(teja)
        c_deco.objects.link(techo)
        partes.append(techo)
        for o in partes:
            K.padre(o, casa) if False else None
            o.parent = casa
        # puerta y ventanas Sweet Home sobre la fachada que mira a la vía
        cara = -prof / 2 - 0.02 if dist > 0 else prof / 2 + 0.02
        rot = 0 if dist > 0 else math.pi
        for nombre_m, x, z in (("door_front_door", -ancho * 0.15, 0), ("window_five_panes_window", ancho * 0.22, 0.9),
                               ("window_double_small_window_with_sill", -ancho * 0.38, 1.0)):
            e = K.instancia(f"casa_{k}_{nombre_m}", _sh3d(nombre_m, protos), (x, cara, z), rot, 1.0, c_deco)
            e.parent = casa
        casas.append(casa)
        if k in (1, 4):          # galpón de chapa, tanque australiano y molino junto a la casa
            g = K.caja(f"galpon_{k}", (c.x + n.x * 22, c.y + n.y * 22, 3.0), (16, 10, 6), chapa, c_deco, rot_z=ang)
            K.instancia(f"galpon_{k}_porton", _sh3d("door_garage_door", protos), (c.x + n.x * 17, c.y + n.y * 17, 0), ang, 1.6, c_deco)
            K.cilindro(f"tanque_{k}", (c.x - t.x * 18, c.y - t.y * 18, 0.9), 4.0, 1.8, chapa, c_deco, lados=40)
            torre = K.cilindro(f"molino_torre_{k}", (c.x - t.x * 26, c.y - t.y * 26, 6), 0.15, 12, chapa, c_deco, lados=8)
            for a in range(12):
                aspa = K.caja(f"molino_aspa_{k}_{a}", (c.x - t.x * 26, c.y - t.y * 26 - 0.3, 12 + 1.2 * math.sin(a * math.pi / 6)),
                              (0.08, 0.05, 1.3), chapa, c_deco)
                aspa.rotation_euler = (0, a * math.pi / 6, 0)

    # ------------------------------------------------------------------ árboles: cortinas de álamos + montes + sueltos
    arboles = ["tree_tree", "tree_birch", "tree_black_tupelo", "tree_quaking_aspen", "tree_sassafras", "sc_acacia", "sc_pine", "tree_weeping_willow"]
    n_arb = 0
    def libre(q):
        _, _, d = kd.find((q.x, q.y, 0))
        return d > 14 and abs(d - lado) > 11
    # cortinas de álamos (rompevientos) perpendiculares y paralelas a la vía
    for k in range(16):
        sc = 200 + k * 140 + rnd.uniform(-30, 30)
        pp, t = via.en(sc)
        n = Vector((t.y, -t.x, 0)).normalized()
        signo = 1 if k % 2 else -1
        d0 = (lado + 25) if signo > 0 else 30
        for j in range(rnd.randint(14, 26)):
            q = pp + n * signo * (d0 + j * 6.5) + t * rnd.uniform(-1, 1)
            if libre(q):
                K.instancia(f"alamo_{k}_{j}", _sh3d("tree_lombardy_poplar", protos), (q.x, q.y, 0), rnd.uniform(0, 6.3),
                            rnd.uniform(1.6, 2.4), c_deco)
                n_arb += 1
    # montes alrededor de las casas y sueltos en el campo
    for casa in casas:
        for j in range(26):
            q = casa.location + Vector((rnd.uniform(-35, 35), rnd.uniform(-35, 35), 0))
            if (q - casa.location).length > 11 and libre(q):
                K.instancia(f"monte_{casa.name}_{j}", _sh3d(rnd.choice(arboles), protos), (q.x, q.y, 0), rnd.uniform(0, 6.3),
                            rnd.uniform(1.0, 1.7), c_deco)
                n_arb += 1
    while n_arb < p["arboles"]:
        sc = rnd.uniform(100, via.largo - 100)
        pp, t = via.en(sc)
        n = Vector((t.y, -t.x, 0)).normalized()
        q = pp + n * rnd.choice((-1, 1)) * rnd.uniform(25, 650)
        if libre(q):
            K.instancia(f"arbol_{n_arb}", _sh3d(rnd.choice(arboles), protos), (q.x, q.y, 0), rnd.uniform(0, 6.3),
                        rnd.uniform(0.9, 1.6), c_deco)
            n_arb += 1
    for j in range(260):        # arbustos y pastizales junto al alambrado
        sc = rnd.uniform(100, via.largo - 100)
        pp, t = via.en(sc)
        n = Vector((t.y, -t.x, 0)).normalized()
        q = pp + n * rnd.choice((-1, 1)) * rnd.uniform(9, 60)
        if libre(q):
            K.instancia(f"arbusto_{j}", _sh3d("sc_lavender_bush", protos), (q.x, q.y, 0),
                        rnd.uniform(0, 6.3), rnd.uniform(1.2, 2.6), c_deco)

    # ------------------------------------------------------------------ nubes (planos altos con ruido)
    nube = bpy.data.materials.new("nube")
    nube.use_nodes = True
    ntm = nube.node_tree
    for n_ in list(ntm.nodes):
        ntm.nodes.remove(n_)
    o_ = ntm.nodes.new("ShaderNodeOutputMaterial")
    mix = ntm.nodes.new("ShaderNodeMixShader")
    tr = ntm.nodes.new("ShaderNodeBsdfTransparent")
    em = ntm.nodes.new("ShaderNodeBsdfDiffuse")
    em.inputs["Color"].default_value = (1.0, 0.97, 0.94, 1)
    tex = ntm.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 3.0
    tex.inputs["Detail"].default_value = 8.0
    grad = ntm.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    mapg = ntm.nodes.new("ShaderNodeMapRange")
    mapg.inputs["From Min"].default_value = 0.45
    mapg.inputs["From Max"].default_value = 0.75
    mul = ntm.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    tc = ntm.nodes.new("ShaderNodeTexCoord")
    ntm.links.new(tc.outputs["Object"], grad.inputs["Vector"])
    ntm.links.new(tex.outputs["Fac"], mapg.inputs["Value"])
    ntm.links.new(mapg.outputs["Result"], mul.inputs[0])
    ntm.links.new(grad.outputs["Fac"], mul.inputs[1])
    ntm.links.new(mul.outputs["Value"], mix.inputs["Fac"])
    ntm.links.new(tr.outputs[0], mix.inputs[1])
    ntm.links.new(em.outputs[0], mix.inputs[2])
    ntm.links.new(mix.outputs[0], o_.inputs["Surface"])
    nube.blend_method = "BLEND" if hasattr(nube, "blend_method") else None
    for k in range(p["nubes"]):
        cx, cy = rnd.uniform(-2500, 3500), rnd.uniform(-1500, 3500)
        r = rnd.uniform(180, 420)
        ob = K.plano(f"nube_{k}", (cx, cy, rnd.uniform(900, 1400)), (r * 2, r * 1.3), nube, c_terr)
        ob.rotation_euler.z = rnd.uniform(0, 3.1)
        ob.visible_shadow = False
        ob["visor_omitir"] = True

    # ------------------------------------------------------------------ tren
    tren = TR.construir("tren", c_veh, COMPOSICION, CARGA)
    nf = int(round(p["duracion_s"] * fps))
    frames = list(range(1, nf + 1))
    v = p["velocidad_tren"]
    s_cab = [p["s_cabeza_inicial"] + v * (f - 1) / fps for f in frames]
    trays = TR.animar(tren, via, frames, s_cab)
    moviles = {}
    anclas_carro = {"": (0, 0, 2.2), "techo": (0, 0, 4.4), "cubierta": (0, 0, 2.2), "bogie": (1.6, -5.0, 0.9),
                    "frente": (0, 9, 3.0), "cola": (0, -7, 3.0)}
    for c in tren["carros"]:
        moviles[f"carro_{c['indice']:02d}"] = {"tray": trays[c["raiz"].name], "anclas": anclas_carro}

    # ------------------------------------------------------------------ escolta por la ruta: 2 blindados + 4 motos
    def por_ruta(desfase, lateral=0.0, vel=v, oscila=0.0, fase=0.0):
        out = []
        for f in frames:
            t = (f - 1) / fps
            si = p["s_cabeza_inicial"] + vel * t - desfase
            pp, tt = via.en(si)
            n = Vector((tt.y, -tt.x, 0)).normalized()
            out.append(tuple(pp + n * (lado + lateral + oscila * math.sin(t * 0.35 + fase))))
        return out
    ruedas_blindado = [{"x": sx * 0.86, "y": yy, "z": 0.46, "radio": 0.46, "ancho": 0.32, "lado": sx, "delantera": yy > 0}
                       for yy in (1.72, -1.55) for sx in (-1, 1)]
    negro = M("negro_halcon", (0.015, 0.015, 0.017), 0.35, 0.3)
    # los blindados se manejan con la física REAL de Dream Rally (estudio/fisica_dr): suspensión, transferencia de peso,
    # gomas y caja de cambios del juego; el conductor sigue su carril a la par del tren.
    if p["secuencia"] != 3:          # en el salto la escolta se arma aparte (la ruta va pegada a las vías)
        s0c, dur, previo = p["s_cabeza_inicial"], p["duracion_s"], 3.0
        plan = {"fps": fps, "hz": 120, "cuadros": nf, "suelo": {"tipo": "plano", "altura": 0.06, "superficie": 0}, "vehiculos": []}
        escoltas = []
        for k, (desfase, lat) in enumerate(((10.0, -1.8), (150.0, -1.8))):
            lat_fn = (lambda s_, d_=desfase, l_=lat, k_=k: lado + l_ + 0.4 * math.sin((s_ - s0c + d_) / v * 0.35 + k_))
            pts, sv = VD.ruta_paralela(via, max(1.0, s0c - desfase - v * (previo + 3) - 30),
                                       min(via.largo - 1.0, s0c - desfase + v * (dur + 3) + 30), lat_fn)
            hor = VD.horario_siguiendo(pts, sv, (lambda t, d_=desfase: s0c + v * t - d_), -previo - 1.0, dur + 1.0)
            plan["vehiculos"].append({"id": f"escolta_{k + 1}", "dr": "camo", "ruta": pts, "horario": hor, "previo_s": previo,
                                      "params": PARAMS_BLINDADO})
            escoltas.append(VD.vehiculo(f"escolta_{k + 1}", c_veh, ref="mixamo:modelos_pelicula/vehiculo_blindado_policial.glb",
                                        largo=5.6, ruedas=ruedas_blindado, alto_caja=0.18,
                                        giro_modelo=math.pi / 2))     # el GLB del blindado tiene el largo en X
        fis = FD.simular(plan)
        for k, rig in enumerate(escoltas):
            tray = VD.aplicar_fisica(rig, fis["vehiculos"][f"escolta_{k + 1}"], frames)
            moviles[f"escolta_{k + 1}"] = {"tray": tray, "anclas": VD.ANCLAS_VEHICULO,
                                           "rpm": fis["vehiculos"][f"escolta_{k + 1}"]["rpm"][:nf]}
        motos = []
        for k in range(4):
            raiz = K.vacio(f"VEH_moto_{k + 1}", (0, 0, 0), c_veh)
            caja = K.vacio(f"VEH_moto_{k + 1}_caja", (0, 0, 0), c_veh)
            caja.parent = raiz
            proto_moto = _sh3d("sc_yamaha_yzr_r6", protos)
            if k == 0:                                   # motos de Halcón Negro: carenado negro brillante, mecánica grafito
                pintura = {"white": M("moto_negro", (0.012, 0.012, 0.014), 0.22, 0.4), "yellow": M("moto_negro", (0, 0, 0)),
                           "red": M("moto_negro", (0, 0, 0)), "tires": M("goma_moto", (0.02, 0.02, 0.022), 0.85),
                           "metal": M("moto_grafito", (0.06, 0.06, 0.065), 0.45, 0.8), "grey": M("moto_grafito", (0, 0, 0)),
                           "tap": M("moto_grafito", (0, 0, 0)), "black": M("moto_grafito", (0, 0, 0))}
                for o in proto_moto.objects:              # en el modelo de Sweet Home cada pieza se llama como su material
                    if o.type != "MESH":
                        continue
                    clave = next((c for c in pintura if o.name.lower().startswith(c) or c in o.name.lower().split("-")), None)
                    if clave:
                        o.data.materials.clear()
                        o.data.materials.append(pintura[clave])
            m = K.instancia(f"moto_{k + 1}_modelo", proto_moto, (0, 0, 0), 0.0, 1.0, c_veh)
            m.parent = caja
            asiento = K.vacio(f"moto_{k + 1}_asiento", (0, -0.15, 0.55), c_veh)
            asiento.parent = caja
            asiento.rotation_euler = (math.radians(-18), 0, 0)
            rig = {"nombre": f"moto_{k + 1}", "raiz": raiz, "caja": caja, "ruedas": [], "entre_ejes": 1.4}
            desfase = 175.0 + (k // 2) * 9.0
            tray = VD.animar(rig, frames, por_ruta(desfase, -1.6 if k % 2 == 0 else 1.6, v, 0.3, k * 1.3), rolido_por_g=0.35)
            moviles[f"moto_{k + 1}"] = {"tray": tray, "anclas": {"": (0, 0, 1.0), "piloto": (0, 0, 1.4)}}
            motos.append(rig)

    # cámara-auto invisible por la ruta (más lenta que el tren: los vagones la pasan)
    moviles["auto_camara"] = {"tray": {f: (Vector(q), math.atan2(-(tt := via.en(p['s_cabeza_inicial'] + 15.5 * (f - 1) / fps - 120)[1]).x, tt.y), 15.5)
                                       for f, q in zip(frames, por_ruta(120.0, 4.0, 15.5))}, "anclas": {"": (0, 0, 1.4)}}

    s_des = p["s_cabeza_inicial"] + p["velocidad_tren"] * 10.5 - 2.0
    tray_des = {}
    for f in frames:
        t_ = (f - 1) / fps
        si = s_des + 4.0 * (t_ - 10.0)
        pp_, tt_ = via.en(si)
        nn_ = Vector((tt_.y, -tt_.x, 0)).normalized()
        tray_des[f] = (pp_ + nn_ * 8.0, math.atan2(-tt_.x, tt_.y), 4.0)
    moviles["camara_desfile"] = {"tray": tray_des, "anclas": {"": (0, 0, 3.1)}}

    if p["secuencia"] == 3:
        info_salto = ST.construir(via, tren, trays, frames, fps, c_veh, p, moviles)
    else:
        info_salto = None
    anclas = {"via_centro": tuple(via.en(1200)[0]), "casa_1": tuple(casas[1].location), "casa_3": tuple(casas[3].location)}
    for k, (sp_, pp_, nn_) in enumerate(vf["pasos_a_nivel"]):
        anclas[f"paso_nivel_{k + 1}"] = tuple(pp_)
        anclas[f"paso_nivel_{k + 1}_camino"] = tuple(pp_ + nn_ * -14.0 + Vector((0, 0, 1.6)))
    return {"anclas": anclas, "animables": {"tren": tren, "via": via, "salto": info_salto}, "parametros": p, "moviles": moviles}
