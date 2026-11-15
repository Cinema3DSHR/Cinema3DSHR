"""Genera escenas/e01/v1/escena.json de p004 desde un recorrido por puntos (los ciclos de cada clip son enteros:
el script simula dónde termina cada tramo y orienta el siguiente desde la posición real)."""
import json
import math
from pathlib import Path

FPS = 30
DUR = 30.0
CL = "mixamo:packs/Pro_Rifle_Pack/"
# (archivo, metros por ciclo, segundos por ciclo) medidos con el retarget
CORRER = ("run_forward.fbx", 2.26, 0.5)
AGACHADO = ("walk_crouching_forward.fbx", 1.92, 1.0)
APUNTA = ("idle_crouching_aiming.fbx", 2.1)

POLI = [(14.0, -6.0), (9.0, -1.9), (-0.8, -1.9)]   # tras el punto de partida; el último es el de la puerta
SOLDADOS = [("s1", "soldado:ch49", "M4A1"), ("s2", "soldado:ch15", "AK47"), ("s3", "soldado:ch35", "M4A1"),
            ("s4", "soldado:operador", "M4A1")]
SEPARACION = 2.3      # metros entre soldados en la fila


def simular(k, deltas):
    """Recorre el itinerario del soldado k con ciclos = redondeo + delta por tramo (deltas ∈ {-1,0,1})."""
    x, y = 14.0 + (0.25 if k % 2 else -0.25), -37.0 - SEPARACION * k
    t = 0.0
    acc = []
    destinos = POLI[:-1] + [(POLI[-1][0] + 1.15 * k, POLI[-1][1])]
    for i, (dx, dy) in enumerate(destinos):
        clip, d, dur = CORRER if i < len(destinos) - 1 else AGACHADO
        dist = math.hypot(dx - x, dy - y)
        ciclos = max(1, round(dist / d) + deltas[i])
        rumbo = math.degrees(math.atan2(dy - y, dx - x))
        a = {"clip": CL + clip, "inicio_s": round(t, 3), "repetir": ciclos, "mirando_deg": round(rumbo, 2)}
        if i == 0:
            a["pos"] = [round(x, 2), round(y, 2)]
        else:
            a["encadenar"] = True
        acc.append(a)
        x += math.cos(math.radians(rumbo)) * d * ciclos
        y += math.sin(math.radians(rumbo)) * d * ciclos
        t += ciclos * dur
    return acc, x, y, t, destinos[-1]


def tramos(k):
    mejor = None
    for d0 in (-1, 0, 1):
        for d1 in (-1, 0, 1):
            for d2 in (-1, 0, 1):
                acc, x, y, t, meta = simular(k, (d0, d1, d2))
                err = math.hypot(x - meta[0], y - meta[1])
                if mejor is None or err < mejor[0]:
                    mejor = (err, acc, x, y, t)
    _, acc, x, y, t = mejor
    ciclos = math.ceil((DUR - t) / APUNTA[1]) + 1
    acc.append({"clip": CL + APUNTA[0], "inicio_s": round(t, 3), "encadenar": True, "repetir": ciclos, "mirando_deg": 180})
    return acc, (x, y, t)


personajes = []
for k, (pid, modelo, arma) in enumerate(SOLDADOS):
    acc, fin = tramos(k)
    print(pid, "se detiene en", tuple(round(v, 2) for v in fin))
    personajes.append({"id": pid, "modelo": modelo, "arma": arma, "acciones": acc})

L = lambda **k: k
tomas = [
    L(id="t01_calle", tipo="estatica", plano="cruzan la calle hacia el portón que se abre", inicio_s=0, duracion_s=3.0,
      desde=[19, -29, 0.9], objetivo={"movil": "s1", "punto": "cadera"}, lente_mm=35, apertura=4.0, luz_relleno=0),
    L(id="t02_camino", tipo="dolly", plano="travelling lateral por el camino de entrada", inicio_s=3.0, duracion_s=3.5,
      desde=[8.5, -22, 1.3], hasta=[8.5, -8, 1.3], objetivo={"movil": "s1", "punto": "cadera"}, lente_mm=40,
      apertura=4.0, luz_relleno=0),
    L(id="t03_seguimiento", tipo="seguimiento", plano="seguimiento por detrás del jefe de la patrulla", inicio_s=6.5,
      duracion_s=3.5, movil="s1", punto_base="cadera", desp_local=[0, -3.6, 1.0],
      objetivo={"movil": "s1", "punto": "cabeza"}, lente_mm=35, luz_relleno=0, retardo=0.2, temblor=0.012),
    L(id="t04_fachada", tipo="estatica", plano="avanzan agachados junto a la fachada", inicio_s=10.0, duracion_s=4.0,
      desde=[-5.5, -5.5, 1.0], objetivo={"movil": "s1", "punto": "cabeza"}, lente_mm=50, apertura=2.8, luz_relleno=0),
    L(id="t05_primer_plano", tipo="estatica", plano="primer plano del jefe apuntando", inicio_s=14.0, duracion_s=4.0,
      desde=[2.6, -5.2, 1.45], objetivo={"movil": "s1", "punto": "cabeza"}, lente_mm=70, apertura=2.0, luz_relleno=0),
    L(id="t06_fila", tipo="estatica", plano="la fila apilada frente a la puerta", inicio_s=18.0, duracion_s=4.0,
      desde=[8.5, -3.6, 1.5], objetivo=[-0.5, -1.9, 1.2], lente_mm=32, apertura=4.0, luz_relleno=0),
    L(id="t07_puerta", tipo="estatica", plano="la puerta se abre", inicio_s=22.0, duracion_s=4.0,
      desde={"ancla": "entrada", "desp": [5.5, -5.0, 1.6]}, objetivo={"ancla": "entrada", "desp": [-0.2, 0, 1.4]},
      lente_mm=40, apertura=4.0, luz_relleno=0),
    L(id="t08_grua", tipo="grua", plano="grúa que se eleva sobre el jardín", inicio_s=26.0, duracion_s=4.0,
      desde=[-5, -11.5, 2.5], hasta=[-4, -10, 10.0], objetivo={"ancla": "entrada", "desp": [1.0, 0, 0.5]}, lente_mm=28,
      luz_relleno=0),
]
escena = {
    "tipo": "escena", "id": "p004_mansion_dia_soldados-e01", "produccion": "p004_mansion_dia_soldados", "numero": 1,
    "version": 1, "titulo": "Infiltración de día",
    "guion": "EXT. MANSIÓN — DÍA. Cuatro soldados cruzan la calle, entran por el portón y corren por el camino; al llegar a la casa avanzan agachados junto a la fachada y se apilan frente a la puerta principal, que se abre.",
    "duracion_s": DUR,
    "escenario": {"id": "mansion_moderna_dia", "generador": "mansion_moderna",
                  "parametros": {"hora": "dia", "suelo_mojado": False, "semilla": 7}},
    "eventos": [{"accion": "abrir_porton", "inicio_s": 0.0, "duracion_f": 60},
                {"accion": "abrir_puerta", "inicio_s": 23.0, "duracion_f": 45}],
    "vehiculos": [],
    "personajes": personajes,
    "tomas": tomas,
    "sonido": {"generador": "procedural", "ambiente": "dia_suburbio",
               "eventos": [{"tipo": "porton_motor", "inicio_s": 0.0, "duracion_s": 2.0, "ancla": "porton"}]},
    "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.0},
    "estado": "borrador", "bloqueada": False,
}
salida = Path(__file__).resolve().parents[1] / "escenas/e01/v1/escena.json"
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=2))
print("escrito", salida)
