"""Storyboard del capítulo 3 → godot_e03/data/storyboard_e03.json (lo lee tools/montaje.gd).
Las duraciones salen de audio_e03/voces.json (voces reales). Uso: python storyboard_e03.py"""
from __future__ import annotations
import json
import shutil
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROD = AQUI.parent
RAIZ = PROD.parents[1]
GODOT = PROD / "godot_e03"
VOCES = json.load(open(PROD / "audio_e03" / "voces.json", encoding="utf-8"))
(GODOT / "data" / "alin").mkdir(parents=True, exist_ok=True)
(GODOT / "data" / "voz").mkdir(parents=True, exist_ok=True)
GAP = 0.45                       # silencio entre líneas


def lineas(bloque: str, t0: float, pausas: dict[int, float] | None = None) -> list[dict]:
    """Voces de un bloque colocadas desde t0 con GAP entre ellas (pausas = {índice: segundos extra ANTES de esa línea})."""
    out, t = [], t0
    for i, v in enumerate([x for x in VOCES if x["bloque"] == bloque]):
        t += (pausas or {}).get(i, 0.0)
        alin = None
        if v["alineacion"]:
            alin = "data/alin/" + Path(v["alineacion"]).name
            shutil.copy(RAIZ / v["alineacion"], GODOT / alin)
        mp3 = "data/voz/" + Path(v["mp3"]).name
        shutil.copy(RAIZ / v["mp3"], GODOT / mp3)
        out.append({"t": round(t, 3), "dur": v["dur_s"], "quien": v["quien"], "texto": v["texto"], "mp3": mp3, "alineacion_res": alin,
                    "exp": {"aiden": v["exp_aiden"], "kate": v["exp_kate"]}})
        t += v["dur_s"] + GAP
    return out


def fin(vs: list[dict]) -> float:
    return vs[-1]["t"] + vs[-1]["dur"]


# ───────────────────────────────────────────────────────────── ESCENA 1 · LA MAÑANA SIGUIENTE (cuarto de Kate)
def escena_1() -> dict:
    vs = lineas("manana", 3.0)
    t = [v["t"] for v in vs]                 # inicio de cada línea: 0 EVA · 1 Kate · 2 EVA · 3 Kate · 4 EVA · 5 Kate · 6 EVA
    dur = round(fin(vs) + 3.0, 2)
    EVA_P = [9.72, 0.775, -5.6]
    return {
        "titulo": "Cap. 3 · Escena 1 · La mañana siguiente",
        "dur": dur,
        "voces": vs,
        "actores": {
            "kate": {"modelo": "kate", "cuero": [0.27, 0.10, 0.045], "inicio": {"pos": [15.55, -4.62], "yaw": 0.0, "y": 0.0, "postura": "sentado", "clip": "sit_idle"},
                     "eventos": [
                         {"t": t[3] - 0.2, "clip": "sit_talk", "dur": vs[3]["dur"] + 0.4},
                         {"t": t[4] + 0.2, "clip": "sit_to_stand", "una_vez": True, "postura": "de_pie"},
                         {"walk": [[16.0, -3.5]], "yaw_final": 90.0, "rapidez": 0.8},
                         {"clip": "taking_item", "una_vez": True, "agarra": {"prop": "rosa", "mano": "R", "en": 1.0,
                                                                          "off": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}},
                         {"gira": -90.0, "dur": 1.0, "clip": "idle"},
                         {"clip": "idle"},
                     ],
                     "clip_final": "idle"},
            "eva": {"modelo": "eva", "escala": 0.2, "holograma": True, "inicio": {"pos": [EVA_P[0], EVA_P[2]], "y": EVA_P[1], "yaw": 90.0, "clip": "idle"},
                    "visible": [[t[0] - 0.6, fin(vs) + 1.4]],
                    "eventos": [
                        {"t": t[0], "clip": "talk1", "dur": vs[0]["dur"] + 0.3},
                        {"t": t[2], "clip": "talk2", "dur": vs[2]["dur"] + 0.3},
                        {"t": t[4], "clip": "talk3", "dur": vs[4]["dur"] + 0.3},
                        {"t": t[6], "clip": "talk1", "dur": vs[6]["dur"] + 0.3},
                        {"clip": "idle"},
                    ]},
        },
        "props": {
            "rosa": {"tipo": "glb", "glb": "res://assets/plantas/rosa_unica.glb", "pos": [16.65, 0.5, -3.8], "esc": 1.0},
        },
        "miradas": [
            {"actor": "kate", "t0": t[0] + 0.5, "t1": t[2] - 0.2, "a": [EVA_P[0], EVA_P[1] + 0.25, EVA_P[2]]},
            {"actor": "kate", "t0": t[2] + 2.0, "t1": t[3] + 0.4, "a": [16.65, 0.95, -3.8]},
            {"actor": "kate", "t0": t[3] + 0.6, "t1": t[4] + 3.0, "a": [EVA_P[0], EVA_P[1] + 0.25, EVA_P[2]]},
            {"actor": "eva", "t0": t[0], "t1": fin(vs), "a": "kate", "alto": 1.45, "peso_cabeza": 0.7},
        ],
        "diag": [
            {"n": "kate_habla", "t": t[3] + 1.35, "sigue": "kate", "hueso": "Head", "off": [0.0, 0.04, 0.55], "fov": 26},
            {"n": "kate_habla2", "t": t[3] + 2.4, "sigue": "kate", "hueso": "Head", "off": [0.15, 0.04, 0.55], "fov": 26},
            {"n": "kate_manos", "t": t[5] + 0.5, "sigue": "kate", "hueso": "R_Hand", "off": [0.0, 0.1, 0.45], "fov": 34},
            {"n": "kate_pies", "t": t[4] + 4.6, "sigue": "kate", "alto": 0.08, "off": [0.0, 0.05, 0.8], "fov": 32},
            {"n": "kate_pies2", "t": t[4] + 4.6, "sigue": "kate", "alto": 0.08, "off": [0.9, 0.05, 0.3], "fov": 32},
        ],
        "tomas": [
            {"id": "t01", "camara": "cam_s1_general", "plano": "general", "t0": 0.0, "t1": t[0] + 1.5, "pos": [12.8, 1.9, -2.0], "pos_fin": [12.8, 1.9, -2.0], "mira": [13.5, 0.9, -5.2], "fov": 72},
            {"id": "t02", "camara": "cam_s1_eva", "plano": "primer plano EVA", "t0": t[0] + 1.5, "t1": t[1] - 0.2, "pos": [11.0, 1.15, -5.1], "pos_fin": [10.8, 1.1, -5.15],
             "mira": [EVA_P[0], 1.0, EVA_P[2]], "fov": 32},
            {"id": "t03", "camara": "cam_s1_kate", "plano": "medio Kate", "t0": t[1] - 0.2, "t1": t[3] - 0.2, "pos": [14.3, 1.3, -2.7], "pos_fin": [14.5, 1.3, -2.8],
             "mira": [15.55, 1.05, -4.5], "fov": 42},
            {"id": "t04", "camara": "cam_s1_rosa", "plano": "detalle de la rosa", "t0": t[3] - 0.2, "t1": t[4] + 2.2, "pos": [15.7, 1.0, -3.0], "pos_fin": [15.9, 1.02, -3.1],
             "mira": [16.65, 0.85, -3.8], "fov": 34},
            {"id": "t05", "camara": "cam_s1_sigue", "plano": "sigue a Kate", "t0": t[4] + 2.2, "t1": t[5] - 0.2, "pos": [13.6, 1.5, -2.6], "pos_fin": [14.4, 1.5, -2.6],
             "sigue": "kate", "sigue_alto": 1.2, "mira": [15, 1, -4], "fov": 48},
            {"id": "t06", "camara": "cam_s1_primer", "plano": "primer plano Kate con la rosa", "t0": t[5] - 0.2, "t1": dur, "pos": [14.5, 1.5, -3.9], "pos_fin": [14.7, 1.5, -3.7],
             "sigue": "kate", "sigue_alto": 1.5, "mira": [16, 1.4, -3.5], "fov": 32},
        ],
    }


ESCENAS = {"s1": escena_1}

if __name__ == "__main__":
    out = {"global": {"fundido_cuadros": 8}, "escenas": {k: f() for k, f in ESCENAS.items()}}
    json.dump(out, open(GODOT / "data" / "storyboard_e03.json", "w"), indent=1, ensure_ascii=False)
    for k, e in out["escenas"].items():
        print(k, "dur", e["dur"], "tomas", len(e["tomas"]), "voces", len(e["voces"]))
