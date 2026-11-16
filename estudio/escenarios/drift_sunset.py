"""DRIFT SUNSET — persecución policial de drift en una ruta rural al atardecer (producción p008).

Vehículos de Dream Rally tal cual (física real, estudio.fisica_dr): el Bisonte XR (dr="genesis") derrapando por una
ruta rural sinuosa, la camioneta policial (dr="police") persiguiéndolo con baliza, y el camión Colossus Titán T4
(dr="titan") con su acoplado y un Súper GT (dr="gt3") amarrado, cruzándose en el camino. Un helicóptero (modelo
entregado) se suma después, siguiendo desde el aire.

`planificar()` corre las físicas y arma los horarios (sin tocar Blender aparte de lo que hace fisica_dr): lo usa tanto
`construir()` como la receta de la escena (producciones/p008_drift_sunset/herramientas/e01.py) para ubicar cámaras y
sonido en los mismos tiempos que la física.
"""
from __future__ import annotations
import math
import random
import bpy
import bmesh
from mathutils import Vector, Euler
from estudio import fisica_dr as FD
from estudio.blender import kit as K, importar as I, tren as TR, via_ferrea as VF, vehiculos_dr as VD, paisaje as PA, \
    animar as AN

DEPENDENCIAS = [
    "mixamo:modelos_pelicula/helicoptero_militar.glb", "mixamo:modelos_pelicula/trailer_plano_camion.glb",
    "rally:godot/game/models/cars/genesis.json", "rally:godot/game/models/cars/genesis.glb", "rally:godot/game/models/cars/genesis_lo.glb",
    "rally:godot/game/models/cars/police.json", "rally:godot/game/models/cars/police.glb", "rally:godot/game/models/cars/police_lo.glb",
    "rally:godot/game/models/cars/titan.json", "rally:godot/game/models/cars/titan.glb", "rally:godot/game/models/cars/titan_lo.glb",
    "rally:godot/game/models/cars/gt3.json", "rally:godot/game/models/cars/gt3.glb", "rally:godot/game/models/cars/gt3_lo.glb",
    "rally:godot/game/physics/", "rally:godot/game/data/", "rally:godot/game/car/", "rally:godot/game/models/pilot.glb",
    "rally:godot/game/models/pilot_lo.glb", "rally:godot/game/models/pilot_Ch20_1001_Diffuse.jpg",
    "rally:godot/game/models/pilot_Ch20_1001_Normal.jpg", "rally:godot/game/models/pilot_ao_met_rough_Ch20_1001_Glossiness.jpg",
    "rally:godot/game/models/cabin/", "rally:godot/game/models/paint/", "rally:godot/game/models/cars/*.json",
    "rally:godot/game/models/cars/*.png",
    "sh3d:models/tree_tree.glb", "sh3d:models/tree_birch.glb", "sh3d:models/tree_black_tupelo.glb",
    "sh3d:models/tree_quaking_aspen.glb", "sh3d:models/tree_sassafras.glb", "sh3d:models/tree_lombardy_poplar.glb",
    "sh3d:models/tree_weeping_willow.glb",
]

PARAMETROS = {"semilla": 11, "duracion_s": 60.0, "arboles": 260}

# ------------------------------------------------------------------------------------------------ la ruta
# control points (m) de la ruta rural: S-curvas en una ladera boscosa. Las curvas quedan donde hacen falta
# para que, con el horario de abajo, el Bisonte llegue a cada una en el instante de la historia.
PUNTOS = [(-60, 10), (40, 55), (160, 60), (260, 10), (300, -90), (260, -200), (150, -260), (40, -230),
          (-40, -140), (-30, -10), (60, 90), (220, 150), (420, 140), (620, 60), (760, -60), (780, -200),
          (680, -320), (520, -360), (380, -300), (320, -180), (380, -60), (540, 20), (740, 40), (920, -10),
          (1040, -110), (1040, -250), (940, -340), (800, -360), (700, -300), (680, -180), (760, -70),
          (920, -20), (1100, -40), (1260, -140), (1320, -280), (1260, -400), (1120, -440), (1000, -400)]


def _via():
    return TR.Via([(x, y, 0.0) for x, y in PUNTOS])


# ------------------------------------------------------------------------------------------------ física

def planificar(p: dict, fps: int) -> dict:
    via = _via()
    dur = p["duracion_s"]
    nf = int(round(dur * fps))
    L = min(via.largo, 1480.0)     # el Bisonte no pasa de ahí en los 60 s; via.largo trae margen de sobra
    # el Bisonte: acelera, entra a la primera curva derrapando (gancho), sigue a fondo, dos derrapes más (persecución,
    # drift intenso) y el derrape largo del clímax antes de la última curva.
    s0_b = 40.0
    hor_b = FD.horario_por_velocidades(s0_b, [(0.0, 14.0), (4.0, 24.0), (9.0, 21.0), (12.0, 17.0), (16.0, 27.0),
                                              (20.0, 20.0), (24.0, 16.0), (28.0, 30.0), (34.0, 29.0), (40.0, 22.0),
                                              (45.0, 16.0), (49.0, 29.0), (53.0, 23.0), (56.0, 15.0), (60.0, 24.0)],
                                       previo=4.0)
    # ventanas de derrape: freno de mano + un poco de contra-volante en la entrada de cada curva marcada arriba
    eventos_b = []
    for t0, dur_ev, extra in ((8.6, 1.3, -0.22), (22.6, 1.5, 0.25), (43.6, 1.7, -0.28), (54.0, 1.4, 0.22)):
        eventos_b.append({"t0": t0, "t1": t0 + dur_ev, "freno_mano": True, "volante_extra": extra, "gas": 0.55})
    plan_b = {"fps": fps, "hz": 120, "cuadros": nf, "suelo": {"tipo": "plano", "altura": 0.06, "superficie": 0},
              "vehiculos": [{"id": "bisonte", "dr": "genesis", "ruta": [list(via.en(s)[0])[:2] for s in
                             [x * 2.0 for x in range(int(L / 2) + 1)]], "horario": hor_b, "previo_s": 4.0,
                             "eventos": eventos_b, "params": {"tractionControl": False, "tcSlip": 0.22},
                             "cabina": {"tipo": "genesis", "pintura": [0.04, 0.05, 0.08], "acento": [0.85, 0.45, 0.05]}}]}
    fis_b = FD.simular(plan_b)
    rb = fis_b["vehiculos"]["bisonte"]

    def s_de_t_bisonte(t):
        f = min(nf - 1, max(0, int(round(t * fps))))
        return hor_b_eval(f)

    # s(t) real del Bisonte (para ubicar al resto de los móviles y las cámaras): integrado del horario pedido
    def hor_b_eval(f):
        t = f / fps
        H = hor_b
        for (ta, sa), (tb, sb) in zip(H, H[1:]):
            if t <= tb:
                k = (t - ta) / max(1e-6, tb - ta)
                return sa + (sb - sa) * k
        return H[-1][1]

    # la camioneta policial: la misma ruta, 16-24 m detrás (según el momento)
    gap = [(0.0, 26.0), (10.0, 20.0), (20.0, 16.0), (35.0, 15.0), (50.0, 18.0), (60.0, 20.0)]
    def gap_en(t):
        for (ta, ga), (tb, gb) in zip(gap, gap[1:]):
            if t <= tb:
                k = (t - ta) / max(1e-6, tb - ta)
                return ga + (gb - ga) * k
        return gap[-1][1]
    hor_p = [[round(t, 3), round(hor_b_eval(min(nf - 1, int(round(t * fps)))) - gap_en(t), 3)]
             for t in [x * 0.1 for x in range(-50, int((dur + 2) * 10))]]
    plan_p = {"fps": fps, "hz": 120, "cuadros": nf, "suelo": {"tipo": "plano", "altura": 0.06, "superficie": 0},
              "vehiculos": [{"id": "policia", "dr": "police", "ruta": plan_b["vehiculos"][0]["ruta"],
                             "horario": hor_p, "previo_s": 4.0, "params": {"tractionControl": True}}]}
    fis_p = FD.simular(plan_p)

    # el Titán con el acoplado: cruza la zona media de la ruta a velocidad constante, de forma que el Bisonte lo
    # alcance y lo pase alrededor de t=30s (según el horario de arriba, ahí el Bisonte está por s≈560 m)
    s_cruce = hor_b_eval(int(30.0 * fps))
    v_titan = 17.0
    s0_t = s_cruce - v_titan * 30.0
    hor_t = FD.horario_constante(s0_t, v_titan, dur, previo=4.0)
    plan_t = {"fps": fps, "hz": 120, "cuadros": nf, "suelo": {"tipo": "plano", "altura": 0.06, "superficie": 0},
              "vehiculos": [{"id": "titan", "dr": "titan", "ruta": plan_b["vehiculos"][0]["ruta"], "horario": hor_t,
                             "previo_s": 4.0}]}
    fis_t = FD.simular(plan_t)

    t_pasa_titan = next((f / fps for f in range(nf) if hor_b_eval(f) - 6.0 > _s_en_t(hor_t, f / fps)), 30.0)
    return {"via": via, "fis_b": rb, "fis_p": fis_p["vehiculos"]["policia"], "fis_t": fis_t["vehiculos"]["titan"],
            "hor_b_eval": hor_b_eval, "hor_t": hor_t, "s_cruce": s_cruce, "t_pasa_titan": t_pasa_titan,
            "v_titan": v_titan, "s0_t": s0_t}


def _s_en_t(hor, t):
    for (ta, sa), (tb, sb) in zip(hor, hor[1:]):
        if t <= tb:
            k = (t - ta) / max(1e-6, tb - ta)
            return sa + (sb - sa) * k
    return hor[-1][1]


# ------------------------------------------------------------------------------------------------ escenario (terreno, ruta, árboles, cielo)

def _tira(nombre, via, s0, s1, paso, perfil, mat, col, desp=0.0, z0=0.0):
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
            l[uv].uv = (l.vert.co.x * 0.2, l.vert.co.y * 0.2)
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nombre, me)
    me.materials.append(mat)
    col.objects.link(ob)
    return ob


_PROTOS: dict = {}


def _arbol(nombre):
    if nombre in _PROTOS:
        return _PROTOS[nombre]
    c = K.prototipo(f"PROTO_{nombre}")
    I.importar(f"sh3d:models/{nombre}.glb", c)
    for o in c.objects:
        o["visor_lod"] = "bajo"
    PA.vestir(c, semilla=len(_PROTOS) + 3)
    _PROTOS[nombre] = c
    return c


def construir(parametros: dict | None = None) -> dict:
    p = {**PARAMETROS, **(parametros or {})}
    rnd = random.Random(p["semilla"])
    s = bpy.context.scene
    fps = s.render.fps
    col = K.coleccion("ESCENARIO_drift_sunset")
    c_terr, c_ruta, c_bosque, c_veh = (K.coleccion(n, col) for n in ("terreno", "ruta", "bosque", "vehiculos"))
    pl = planificar(p, fps)
    via = pl["via"]
    frames = list(range(1, int(round(p["duracion_s"] * fps)) + 1))
    nf = len(frames)
    L = min(via.largo, 1480.0)     # sólo se construye lo que el Bisonte llega a recorrer (via.largo trae margen de sobra)

    # ---------------------------------------------------------------- cielo y sol del atardecer
    K.cielo_dia(s, cenit=(0.22, 0.30, 0.52), horizonte=(0.96, 0.55, 0.22), fuerza=1.0)
    sol = K.luz("sol_atardecer", "SUN", (0, 0, 40), 3.0, (1.0, 0.62, 0.32), col, tam=0.9)
    sol.rotation_euler = (math.radians(100), 0, math.radians(35))      # bajo sobre el horizonte, sombras largas

    # ---------------------------------------------------------------- terreno (loma suave con pasto seco)
    pasto = K.material("pasto_seco", (0.42, 0.33, 0.14), 0.95, ruido=0.3, escala_ruido=6)
    tierra = K.material("banquina_tierra", (0.33, 0.24, 0.14), 0.95, ruido=0.45, escala_ruido=5)
    mn_x = min(x for x, y in PUNTOS) - 140
    mx_x = max(x for x, y in PUNTOS) + 140
    mn_y = min(y for x, y in PUNTOS) - 140
    mx_y = max(y for x, y in PUNTOS) + 140
    K.plano("terreno", ((mn_x + mx_x) / 2, (mn_y + mx_y) / 2, -0.03), (mx_x - mn_x, mx_y - mn_y), pasto, c_terr)

    # ---------------------------------------------------------------- la ruta: asfalto + banquina de tierra + guardarraíl
    asfalto = K.material("asfalto_drift", (0.065, 0.065, 0.07), 0.55, ruido=0.2, escala_ruido=3, relieve=0.08)
    blanco = K.material("linea_ruta", (0.82, 0.8, 0.75), 0.5)
    _tira("ruta_asfalto", via, 0, L, 3.0, [(-3.6, 0.05), (3.6, 0.05)], asfalto, c_ruta)
    _tira("ruta_banquina", via, 0, L, 4.0, [(-6.0, 0.0), (6.0, 0.0)], tierra, c_ruta, z0=-0.01)
    for bd in (-3.5, 3.5):
        _tira(f"linea_{bd}", via, 0, L, 5.0, [(-0.08, 0.07), (0.08, 0.07)], blanco, c_ruta, desp=bd)
    # guardarraíl sólo en las curvas cerradas (cada ~60 m de curvatura fuerte): postes + viga
    m_rail = K.material("guardarrail", (0.72, 0.73, 0.75), 0.3, 0.7)
    lote = VF.Lote()
    s_g = 10.0
    while s_g <= L - 10.0:
        p0, t0 = via.en(s_g - 2.0)
        p1, t1 = via.en(s_g + 2.0)
        curv = (t1 - t0).length
        if curv > 0.18:
            pp, tt, nn, ang = VF.marco(via, s_g)
            for lado in (-1, 1):
                lote.caja(pp + nn * lado * 4.3 + Vector((0, 0, 0.55)), ang, (0.08, 1.2, 0.06))
                lote.caja(pp + nn * lado * 4.3 + Vector((0, 0, 0.25)), ang, (0.1, 0.1, 0.5))
        s_g += 4.0
    lote.objeto("guardarrail", m_rail, c_ruta)

    # ---------------------------------------------------------------- bosque a los costados (Sweet Home, follaje real)
    especies = ["tree_tree", "tree_birch", "tree_black_tupelo", "tree_quaking_aspen", "tree_sassafras",
                "tree_lombardy_poplar", "tree_weeping_willow"]
    n_arb = 0
    intentos = 0
    while n_arb < p["arboles"] and intentos < p["arboles"] * 6:
        intentos += 1
        sc = rnd.uniform(5.0, L - 5.0)
        pp, tt = via.en(sc)
        nn = Vector((tt.y, -tt.x, 0)).normalized()
        d = rnd.choice((-1, 1)) * rnd.uniform(9.0, 55.0)
        q = pp + nn * d
        K.instancia(f"arbol_{n_arb}", _arbol(rnd.choice(especies)), (q.x, q.y, 0), rnd.uniform(0, 6.3),
                    rnd.uniform(0.85, 1.5), c_bosque)
        n_arb += 1

    # ---------------------------------------------------------------- vehículos
    rb, fp, ft = pl["fis_b"], pl["fis_p"], pl["fis_t"]
    rig_b = VD.vehiculo("bisonte", c_veh, dr="genesis")
    tray_b = VD.aplicar_fisica(rig_b, rb, frames)
    VD.cabina(rig_b, rb["cabina"], c_veh, exterior=True)
    moviles = {"bisonte": {"tray": tray_b, "objeto": rig_b["raiz"], "rpm": rb["rpm"][:nf],
                           "anclas": {**VD.ANCLAS_VEHICULO, "interior": (0.0, 0.5, 1.35), "cabina": (0.0, -0.4, 1.3)},
                           "telemetria": rig_b.get("telemetria", {})}}

    rig_p = VD.vehiculo("policia", c_veh, dr="police")
    tray_p = VD.aplicar_fisica(rig_p, fp, frames)
    moviles["policia"] = {"tray": tray_p, "objeto": rig_p["raiz"], "rpm": fp["rpm"][:nf], "anclas": VD.ANCLAS_VEHICULO}
    # baliza policial: dos luces (roja/azul) que alternan cada 0,1 s
    barra = K.vacio("baliza_policia", (0, 0, 1.55), c_veh)
    barra.parent = rig_p["raiz"]
    # cada luz usa SU PROPIO material (no compartido, para poder animar su emisión sin afectar a la otra), alternando
    # entre encendida y apagada cada 0,09 s
    for k, (x, color) in enumerate(((-0.22, (1.0, 0.07, 0.05)), (0.22, (0.1, 0.3, 1.0)))):
        mat = K.material(f"luz_baliza_{k}_ds", color, 0.3, emision=color, fuerza=0.0)
        l = K.caja(f"luz_baliza_{k}", (x, 0, 1.55), (0.22, 0.32, 0.1), mat, c_veh)
        l.parent = rig_p["raiz"]
        emi = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        for f in frames:
            on = (int(round((f - 1) / fps / 0.09)) + k) % 2 == 0
            emi.inputs["Emission Strength"].default_value = 26.0 if on else 0.0
            emi.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
        if mat.node_tree.animation_data and mat.node_tree.animation_data.action:
            for fc in K._fcurves(mat.node_tree.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"

    rig_t = VD.vehiculo("titan_tractor", c_veh, dr="titan")
    tray_t = VD.aplicar_fisica(rig_t, ft, frames)
    moviles["titan"] = {"tray": tray_t, "objeto": rig_t["raiz"], "rpm": ft["rpm"][:nf], "anclas": VD.ANCLAS_VEHICULO}
    # el acoplado sigue al tractor por la misma vía, 7,7 m atrás (como en Tren Fantasma); el horario ya da s(t) exacto
    LAG_ACOP = 7.7
    pos_ac, rot_ac = [], []
    for i in range(nf):
        s_tr = max(0.0, _s_en_t(pl["hor_t"], i / fps) - LAG_ACOP)
        q, t = via.en(s_tr)
        pos_ac.append((q.x, q.y, 0.0))
        rot_ac.append((0, 0, math.atan2(t.y, t.x) - math.pi / 2))
    ACOPLADO = "mixamo:modelos_pelicula/trailer_plano_camion.glb"
    # mismas medidas que salto_tren.py (tomadas sobre el modelo): gemelas bajo los guardabarros, no una sola por lado
    RUEDAS_ACOP = [{"x": sx * x, "y": yy, "z": 0.52, "radio": 0.52, "ancho": 0.34, "lado": sx, "delantera": False}
                   for yy in (-4.9, -3.0, -1.25) for sx in (-1, 1) for x in (1.36, 0.98)]
    rig_ac = VD.vehiculo("acoplado_titan", c_veh, ref=ACOPLADO, largo=13.0, ruedas=RUEDAS_ACOP)
    yaws_ac = AN.desenrollar([r[2] for r in rot_ac])
    AN.transformacion(rig_ac["raiz"], frames, pos_ac, [(0, 0, a) for a in yaws_ac])
    # giro de las ruedas del acoplado (no tiene física propia: eje no motriz, siempre a la velocidad del Titán)
    giro_ac = [-(pl["v_titan"] * (f - 1) / fps) / RUEDAS_ACOP[0]["radio"] for f in frames]
    for w in rig_ac["ruedas"]:
        AN.curva(w["giro"], "rotation_euler", 0, frames, giro_ac)
    CAMA = 1.59
    moviles["acoplado"] = {"tray": {f: (Vector(pos_ac[i]), rot_ac[i][2], pl["v_titan"]) for i, f in enumerate(frames)},
                          "objeto": rig_ac["raiz"], "anclas": {"": (0, 0, 2.0), "cama": (0, 0, CAMA)}}
    # el Súper GT amarrado arriba del acoplado
    rig_gt = VD.vehiculo("super_gt", c_veh, dr="gt3")
    alto_gt = float(VD.params_dr("gt3").get("rideOffset", 0.0))
    pos_gt, rot_gt = [], []
    for i in range(nf):
        p_ac = Vector(pos_ac[i]) + Vector((0, 0, CAMA + alto_gt))
        pos_gt.append(tuple(p_ac))
        rot_gt.append((0, 0, rot_ac[i][2]))
    rig_gt["carroceria"].location.z = 0.0
    AN.transformacion(rig_gt["raiz"], frames, pos_gt, rot_gt)           # las ruedas quedan quietas: viaja amarrado
    m_correa = K.material("correa_amarre", (0.08, 0.08, 0.08), 0.6)
    for dx, dy in ((-0.9, 1.7), (0.9, 1.7), (-0.9, -1.7), (0.9, -1.7)):
        correa = K.caja(f"correa_{dx}_{dy}", (dx, dy, CAMA + alto_gt * 0.4), (0.06, 0.06, alto_gt * 0.8 + 0.1), m_correa, c_veh)
        correa.rotation_euler = (math.radians(20), math.radians(15), 0)
        correa.parent = rig_ac["raiz"]
        correa.location = (dx, dy, CAMA + alto_gt * 0.4)
    moviles["super_gt"] = {"tray": {f: (Vector(pos_gt[i]), rot_gt[i][1], pl["v_titan"]) for i, f in enumerate(frames)},
                          "anclas": {"": (0, 0, 0.8)}}

    # ---------------------------------------------------------------- helicóptero (modelo entregado; sin físicas: ruta
    # armada a mano, siguiendo al Bisonte desde el aire a partir de que entra en escena)
    heli_objs = I.importar("mixamo:modelos_pelicula/helicoptero_militar.glb", c_veh)
    heli = K.vacio("helicoptero", (0, 0, 60), c_veh)
    for o in heli_objs:
        if o.parent is None:
            o.parent = heli
    ESCALA_HELI = 12.0
    heli.scale = (ESCALA_HELI,) * 3
    m_rotor = K.material("disco_rotor", (0.05, 0.05, 0.05), 0.3, alfa=0.28)
    rotor_p = K.cilindro("rotor_principal", (0.08, 0, 0.33), 0.44, 0.01, m_rotor, c_veh, lados=24)
    rotor_p.parent = heli
    rotor_p.location = (0.08, 0.0, 0.335)
    rotor_t = K.cilindro("rotor_cola", (-0.48, 0.0, 0.0), 0.09, 0.01, m_rotor, c_veh, lados=16)
    rotor_t.parent = heli
    rotor_t.location = (-0.48, 0.13, 0.11)
    rotor_t.rotation_euler = (0, math.radians(90), 0)
    for ob, vel in ((rotor_p, 32.0), (rotor_t, 70.0)):
        d = ob.driver_add("rotation_euler", 2)
        d.driver.expression = f"frame * {vel}"
    t_heli0 = pl["t_pasa_titan"] + 10.0        # entra en escena después del Titán, como pide el guion
    heli_pos, heli_rot, yaws = [], [], []
    for i, f in enumerate(frames):
        t = (f - 1) / fps
        if t < t_heli0:
            q = Vector((PUNTOS[0][0], PUNTOS[0][1] + 200, 120.0))
            yaw = 0.0
        else:
            s_b = pl["hor_b_eval"](f - 1)
            pb, tb = via.en(s_b + 26.0)          # un poco adelante del Bisonte
            q = Vector((pb.x - tb.y * 6.0, pb.y + tb.x * 6.0, 34.0 + 2.0 * math.sin(t * 0.7)))
            yaw = math.atan2(tb.y, tb.x) - math.pi / 2
        heli_pos.append(tuple(q))
        heli_rot.append((math.radians(-4.0), math.radians(3.0 * math.sin(t * 0.5))))
        yaws.append(yaw)
    yaws = AN.desenrollar(yaws)
    AN.transformacion(heli, frames, heli_pos, [(heli_rot[i][0], heli_rot[i][1], yaws[i]) for i in range(nf)])
    moviles["helicoptero"] = {"tray": {f: (Vector(heli_pos[i]), yaws[i], 0.0) for i, f in enumerate(frames)},
                             "objeto": heli, "anclas": {"": (0, 0, 0)}}

    anclas = {"inicio": tuple(via.en(0)[0]), "curva_1": tuple(via.en(_curva_cercana(via, 230))[0]),
              "curva_2": tuple(via.en(_curva_cercana(via, 460))[0]), "cruce_titan": tuple(via.en(pl["s_cruce"])[0]),
              "climax": tuple(via.en(_curva_cercana(via, 980))[0]), "final": tuple(via.en(L - 30)[0])}
    return {"anclas": anclas, "animables": {"via": via}, "moviles": moviles, "parametros": p,
            "info": {"t_pasa_titan": pl["t_pasa_titan"], "t_heli": t_heli0, "s_cruce": pl["s_cruce"]}}


def _curva_cercana(via, s_aprox):
    return max(0.0, min(via.largo, s_aprox))
