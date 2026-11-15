"""Genera escenas/s01/v1/escena.json — SECUENCIA 1: EL TRANSPORTE (75 s, 2.250 fotogramas).

Soldados de Halcón Negro viajando sobre los vagones (sus posiciones están en el marco del vagón: +Y adelante, z = altura
sobre la vía), motociclistas de negro sobre las motos de escolta y 9 tomas que presentan el tren.
"""
import json
from pathlib import Path

FPS, DUR = 30, 75.0
RP = "mixamo:packs/Pro_Rifle_Pack/"
CUBIERTA = 0.45 + 0.55 + 0.101 * 14 * 0.82        # altura de la cubierta de una plataforma (tren.py)
TECHO = 0.45 + 0.55 + 0.287 * 13.7                 # techo de un vagón cerrado


def rep(seg, ciclo):
    return max(1, round(seg / ciclo))


def soldado_quieto(pid, modelo, arma, carro, pos, mirando, clip="idle.fbx"):
    ciclo = 63 / FPS
    return {"id": pid, "modelo": modelo, "arma": arma, "sobre": f"tren_{carro:02d}_{'cerrado' if pos[2] > 3 else 'plano'}",
            "acciones": [{"clip": RP + clip, "inicio_s": 0, "pos": list(pos), "mirando_deg": mirando, "repetir": rep(DUR, ciclo) + 1}]}


def soldado_patrulla(pid, modelo, arma, carro, x, y0, y1, z):
    """Camina de y0 a y1 por la cubierta, se da vuelta mirando, vuelve. Ciclos enteros de walk_forward (1,81 m)."""
    acc, t = [], 0.0
    ida = True
    tramo = abs(y1 - y0)
    n = max(1, round(tramo / 1.81))
    while t < DUR:
        acc.append({"clip": RP + "walk_forward.fbx", "inicio_s": round(t, 3), "repetir": n, "mirando_deg": 90 if ida else -90,
                    "giro_s": 0.5, **({"pos": [x, y0, z]} if not acc else {"encadenar": True})})
        t += n * 1.0
        acc.append({"clip": RP + "idle_aiming.fbx", "inicio_s": round(t, 3), "repetir": 2, "mirando_deg": 0 if ida else 180,
                    "giro_s": 0.6, "encadenar": True})
        t += 2 * 63 / FPS
        ida = not ida
    return {"id": pid, "modelo": modelo, "arma": arma, "sobre": f"tren_{carro:02d}_plano", "acciones": acc}


def motociclista(k):
    return {"id": f"motero_{k}", "modelo": "rally:piloto", "sobre": f"moto_{k}_asiento",
            "material": {"color": [0.02, 0.02, 0.022], "rugosidad": 0.45},
            "acciones": [{"clip": "mixamo:animaciones/sentado_manejar/Driving.fbx", "inicio_s": 0, "pos": [0, 0.05, -0.5],
                          "mirando_deg": 90, "repetir": 40}]}


personajes = [
    soldado_quieto("guardia_1", "soldado:ch35", "M4A1", 2, (1.1, -3.5, CUBIERTA), 0),
    soldado_patrulla("guardia_2", "soldado:ch15", "M4A1", 5, -1.0, -5.5, 4.0, CUBIERTA),
    soldado_quieto("guardia_3", "soldado:operador", "M4A1", 3, (0.4, 2.0, TECHO), 0, "idle_crouching_aiming.fbx"),
    soldado_quieto("guardia_4", "soldado:ch35", "AK47", 9, (-1.2, 1.0, CUBIERTA), 180),
    soldado_patrulla("guardia_5", "soldado:ch15", "M4A1", 16, 1.0, -5.0, 3.5, CUBIERTA),
    soldado_quieto("guardia_6", "soldado:operador", "M4A1", 11, (-0.5, -3.0, TECHO), 0, "idle_aiming.fbx"),
] + [motociclista(k) for k in (1, 2, 3, 4)]


def toma(i, tipo, plano, t0, t1, **k):
    return {"id": f"t{i:02d}_{tipo}", "tipo": tipo, "plano": plano, "inicio_s": t0, "duracion_s": round(t1 - t0, 3),
            "luz_relleno": 0, **k}


M = lambda movil, punto="", desp=None: {"movil": movil, "punto": punto, **({"desp_local": desp} if desp else {})}
tomas = [
    toma(1, "grua", "aérea de revelación: la cámara sube y descubre el tren entero entre lomas y cortinas de álamos", 0, 10,
         desde=M("carro_08", desp=[-70, -40, 6]), hasta=M("carro_08", desp=[-150, 60, 120]), objetivo=M("carro_04"), lente_mm=26),
    toma(2, "seguimiento", "desde la ruta, más lenta que el tren: los vagones con autos pasan uno tras otro", 10, 18,
         movil="auto_camara", punto_base="", desp_local=[-5, 0, 1.3], objetivo=M("auto_camara", desp=[-38, 22, 2.6]),
         lente_mm=35, retardo=1.0),
    toma(3, "seguimiento", "cámara baja junto a los bogies: ruedas de acero, durmientes que pasan", 18, 24,
         movil="carro_04", punto_base="", desp_local=[-2.7, -3.6, -1.6], objetivo=M("carro_04", "bogie"), lente_mm=24, retardo=1.0),
    toma(4, "seguimiento", "recorrido sobre la plataforma: los autos de lujo amarrados", 24, 32,
         movil="carro_02", punto_base="", desp_local=[-4.2, 7.5, 1.6], desp_local_final=[-4.2, -6.5, 1.4],
         objetivo=M("carro_02", "cubierta"), lente_mm=32, retardo=1.0),
    toma(5, "seguimiento", "blindado de escolta de Halcón Negro por la ruta, el tren detrás", 32, 40,
         movil="escolta_1", punto_base="", desp_local=[4.5, 10, 0.6], objetivo=M("escolta_1"), lente_mm=35, retardo=1.0),
    toma(6, "seguimiento", "motos de escolta en fila, pilotos de negro", 40, 46,
         movil="moto_1", punto_base="", desp_local=[4.5, 7.0, 0.9], objetivo=M("moto_1", "piloto"), lente_mm=50, retardo=1.0),
    toma(7, "seguimiento", "guardia patrullando entre los autos", 46, 55,
         movil="carro_05", punto_base="", desp_local=[-5.8, 5.5, 1.5], objetivo=M("carro_05", "cubierta"), lente_mm=35, retardo=1.0),
    toma(8, "seguimiento", "desde un vagón hacia la locomotora que entra en la curva; al fondo, la sierra", 55, 64,
         movil="carro_09", punto_base="", desp_local=[2.3, -1.5, 3.6], objetivo=M("carro_00", "frente"), lente_mm=28, retardo=1.0),
    toma(9, "grua", "la cámara se eleva: el tren se aleja hacia las montañas (título)", 64, 75,
         desde=M("carro_10", desp=[-25, -40, 4]), hasta=M("carro_10", desp=[-110, -240, 130]), objetivo=M("carro_05"), lente_mm=24),
]
escena = {
    "tipo": "escena", "id": "p006_operacion_tren_fantasma-s01", "produccion": "p006_operacion_tren_fantasma", "numero": 1,
    "version": 1, "titulo": "El transporte",
    "guion": "EXT. LLANURA AL PIE DE LA SIERRA — MEDIA TARDE. El tren de Halcón Negro cruza la llanura con veinte vagones "
             "cargados de autos de lujo, custodiado por blindados, motos y soldados sobre los vagones.",
    "duracion_s": DUR,
    "escenario": {"id": "llanura_tren", "generador": "tren_fantasma", "parametros": {"secuencia": 1, "semilla": 3, "duracion_s": DUR}},
    "eventos": [], "vehiculos": [], "personajes": personajes, "tomas": tomas,
    "moviles_escenario": [f"carro_{i:02d}" for i in range(21)] + ["escolta_1", "escolta_2", "moto_1", "moto_2", "moto_3", "moto_4", "auto_camara"],
    "sonido": {"generador": "procedural", "ambiente": "tren_llanura", "eventos": []},
    "render": {"calidad": "revision", "fps": FPS, "exposicion": 0.0},
    "estado": "borrador", "bloqueada": False, "huella_v": 2,
}
salida = Path(__file__).resolve().parents[1] / "escenas/s01/v1/escena.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(escena, ensure_ascii=False, indent=1))
print("escrito", salida, len(personajes), "personajes", len(tomas), "tomas")
