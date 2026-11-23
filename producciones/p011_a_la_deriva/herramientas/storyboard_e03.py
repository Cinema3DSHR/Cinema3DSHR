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
                        {"t": t[2], "clip": "talk1", "dur": vs[2]["dur"] + 0.3},
                        {"t": t[4], "clip": "talk1", "dur": vs[4]["dur"] + 0.3},
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
            {"n": "kate_habla", "t": t[3] + 0.55, "sigue": "kate", "hueso": "Head", "off": [0.0, 0.02, 0.5], "fov": 24},
            {"n": "kate_habla2", "t": t[3] + 0.85, "sigue": "kate", "hueso": "Head", "off": [0.0, 0.02, 0.5], "fov": 24},
            {"n": "kate_manos", "t": t[5] + 0.5, "sigue": "kate", "hueso": "R_Hand", "off": [0.0, 0.1, 0.45], "fov": 34},
            {"n": "kate_pies", "t": t[4] + 4.6, "sigue": "kate", "alto": 0.08, "off": [0.0, 0.05, 0.8], "fov": 32},
            {"n": "kate_pies3", "t": t[4] + 4.6, "sigue": "kate", "alto": 0.08, "off": [0.9, 0.05, 0.3], "fov": 32, "ocultar": ["EM3D_Base_Body"]},
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


# ───────────────────────────────────────────────────────────── ESCENA 2 · LA ANOMALÍA (comedor → pasillo; EVA sólo por el micrófono)
def escena_2() -> dict:
    vs = lineas("alarma", 2.0)
    t = [v["t"] for v in vs]                 # 0 EVA · 1 Aiden · 2 EVA · 3 Kate · 4 Aiden · 5 EVA
    dur = round(fin(vs) + 4.0, 2)
    return {
        "titulo": "Cap. 3 · Escena 2 · La anomalía",
        "dur": dur, "voces": vs,
        "actores": {
            "kate": {"modelo": "kate", "cuero": [0.27, 0.10, 0.045],
                     "inicio": {"pos": [-1.4, -6.7], "yaw": 0.0, "y": 0.0, "postura": "sentado", "clip": "sit_idle"},
                     "eventos": [
                         {"t": t[0] + 3.2, "clip": "look_around", "una_vez": True},
                         {"t": t[2] + 0.2, "clip": "sit_idle2", "dur": 2.0},
                         {"t": t[3] - 1.2, "clip": "sit_to_stand", "una_vez": True, "postura": "de_pie"},
                         {"walk": [[-0.55, -6.45], [-0.3, -3.6], [0.0, -1.9], [0.0, 0.0], [3.0, 0.0]], "clip": "run", "yaw_final": 90.0},
                     ], "clip_final": "idle"},
            "aiden": {"modelo": "aiden", "cuero": [0.085, 0.057, 0.04],
                      "inicio": {"pos": [-1.4, -4.5], "yaw": 180.0, "y": 0.0, "postura": "sentado", "clip": "sit_idle2"},
                      "eventos": [
                          {"t": t[1] - 1.0, "clip": "sit_to_stand", "una_vez": True, "postura": "de_pie"},
                          {"clip": "idle", "dur": 1.6},
                          {"t": t[4] - 0.3, "walk": [[-0.6, -4.8], [-0.2, -3.0], [0.0, -1.9], [0.0, -0.3], [-3.0, 0.0]], "clip": "run", "yaw_final": -90.0},
                      ], "clip_final": "idle"},
        },
        "props": {},
        "diag": [
            {"n": "aiden_cara", "t": t[1] + 0.5, "sigue": "aiden", "hueso": "Head", "off": [0.0, 0.02, 0.5], "fov": 24},
            {"n": "aiden_cara2", "t": t[4] + 1.5, "sigue": "aiden", "hueso": "Head", "off": [0.0, 0.02, 0.5], "fov": 24},
            {"n": "aiden_manos", "t": t[1] + 0.5, "sigue": "aiden", "hueso": "R_Hand", "off": [0.0, 0.15, 0.5], "fov": 34},
        ],
        "miradas": [
            {"actor": "aiden", "t0": t[0] + 3.5, "t1": t[1] + 2.0, "a": "kate", "alto": 1.45},
            {"actor": "kate", "t0": t[1], "t1": t[3] - 0.5, "a": "aiden", "alto": 1.5},
        ],
        "tomas": [
            {"id": "t01", "camara": "cam_s2_general", "plano": "general del comedor", "t0": 0.0, "t1": t[1] - 0.3, "pos": [-0.8, 2.1, -2.1], "mira": [-1.4, 1.0, -5.6], "fov": 62},
            {"id": "t02", "camara": "cam_s2_aiden", "plano": "medio Aiden", "t0": t[1] - 0.3, "t1": t[2] + 0.3, "pos": [-1.1, 1.35, -6.0], "mira": [-1.4, 1.2, -4.6], "fov": 38},
            {"id": "t03", "camara": "cam_s2_dos", "plano": "los dos en pie", "t0": t[2] + 0.3, "t1": t[4] - 0.6, "pos": [1.2, 1.6, -2.6], "pos_fin": [0.8, 1.6, -2.9], "mira": [-1.0, 1.1, -5.5], "fov": 55},
            {"id": "t04", "camara": "cam_s2_pasillo", "plano": "salen corriendo", "t0": t[4] - 0.6, "t1": dur, "pos": [-2.5, 1.7, 1.3], "mira": [0.0, 1.0, -0.5], "fov": 60},
        ],
    }


# ───────────────────────────────────────────────────────────── ESCENA 3 · ALGO NO CUADRA (consola del módulo botánico; EVA holograma grande)
def escena_3() -> dict:
    vs = lineas("registro", 2.0)
    t = [v["t"] for v in vs]      # 0 K · 1 A · 2 A · 3 EVA · 4 A · 5 EVA · 6 K · 7 EVA · 8 K
    dur = round(fin(vs) + 3.0, 2)
    CON = [-4.4, 5.1]
    return {
        "titulo": "Cap. 3 · Escena 3 · Algo no cuadra",
        "dur": dur, "voces": vs,
        "actores": {
            "kate": {"modelo": "kate", "cuero": [0.27, 0.10, 0.045], "inicio": {"pos": [-4.35, 4.9], "yaw": -90.0, "clip": "tablet"},
                     "eventos": [
                         {"t": t[5] - 1.0, "gira": 90.0, "dur": 1.1, "clip": "idle"},
                         {"t": t[6] - 0.3, "clip": "thoughtful", "una_vez": True},
                         {"t": t[8] - 0.5, "clip": "thinking", "dur": vs[8]["dur"] + 0.6},
                     ], "clip_final": "idle"},
            "aiden": {"modelo": "aiden", "cuero": [0.085, 0.057, 0.04], "inicio": {"pos": [-4.35, 6.1], "yaw": -90.0, "clip": "idle"},
                      "eventos": [
                          {"t": t[2] - 0.4, "gira": 90.0, "dur": 1.0, "clip": "idle"},
                          {"t": t[4] - 0.2, "clip": "shrug", "una_vez": True},
                      ], "clip_final": "idle"},
            "eva": {"modelo": "eva", "escala": 1.0, "holograma": True, "inicio": {"pos": [-2.4, 5.5], "y": 0.04, "yaw": -90.0, "clip": "idle"},
                    "visible": [[t[3] - 1.2, t[8] + 2.0]],
                    "eventos": [
                        {"t": t[3], "clip": "talk1", "dur": vs[3]["dur"] + 0.3},
                        {"t": t[5], "clip": "talk1", "dur": vs[5]["dur"] + 0.3},
                        {"t": t[7], "clip": "talk1", "dur": vs[7]["dur"] + 0.3},
                    ], "clip_final": "idle"},
        },
        "props": {"tablet": {"tipo": "tablet", "pos": [-4.0, 1.1, 4.7], "rot": [0, 0, 0], "manos": [{"actor": "kate", "mano": "L", "t0": 0.0, "t1": dur, "off": [0.0, 0.03, 0.06, 0, 0, 0]}]}},
        "miradas": [
            {"actor": "kate", "t0": t[0], "t1": t[5] - 1.0, "a": [-5.6, 1.35, 5.5]},
            {"actor": "aiden", "t0": t[0], "t1": t[2], "a": [-5.6, 1.35, 5.5]},
            {"actor": "aiden", "t0": t[2] + 1.0, "t1": t[8] + 1.0, "a": "eva", "alto": 1.6},
            {"actor": "kate", "t0": t[5] + 0.5, "t1": t[8] + 1.0, "a": "eva", "alto": 1.6},
            {"actor": "eva", "t0": t[3], "t1": t[8] + 1.0, "a": "aiden", "alto": 1.55, "peso_cabeza": 0.7},
        ],
        "diag": [],
        "tomas": [
            {"id": "t01", "camara": "cam_s3_general", "plano": "general del módulo", "t0": 0.0, "t1": t[1] - 0.2, "pos": [3.0, 2.4, 3.0], "mira": [-4.0, 1.1, 5.5], "fov": 58},
            {"id": "t02", "camara": "cam_s3_perfil", "plano": "perfil Kate y Aiden", "t0": t[1] - 0.2, "t1": t[3] - 0.5, "pos": [-3.0, 1.95, 2.8], "pos_fin": [-3.2, 1.95, 2.9], "mira": [-4.4, 1.3, 5.5], "fov": 46},
            {"id": "t03", "camara": "cam_s3_eva", "plano": "EVA frente a ellos", "t0": t[3] - 0.5, "t1": t[6] - 0.3, "pos": [-5.0, 1.5, 7.4], "mira": [-2.6, 1.4, 5.5], "fov": 46},
            {"id": "t04", "camara": "cam_s3_kate", "plano": "Kate", "t0": t[6] - 0.3, "t1": t[7] - 0.2, "pos": [-2.9, 1.9, 3.0], "mira": [-4.35, 1.45, 4.9], "fov": 34},
            {"id": "t05", "camara": "cam_s3_dos", "plano": "los tres", "t0": t[7] - 0.2, "t1": dur, "pos": [-3.0, 1.7, 8.2], "pos_fin": [-3.3, 1.7, 8.0], "mira": [-3.4, 1.2, 5.5], "fov": 52},
        ],
    }


# ───────────────────────────────────────────────────────────── ESCENA 4 · UN MOMENTO ENTRE LOS DOS
def escena_4() -> dict:
    vs = lineas("momento", 2.0)
    t = [v["t"] for v in vs]      # 0 A · 1 K · 2 A · 3 K · 4 A · 5 K · 6 A
    dur = round(fin(vs) + 3.5, 2)
    return {
        "titulo": "Cap. 3 · Escena 4 · Un momento entre los dos",
        "dur": dur, "voces": vs,
        "actores": {
            "kate": {"modelo": "kate", "cuero": [0.27, 0.10, 0.045], "inicio": {"pos": [2.3, 5.4], "yaw": 90.0, "clip": "idle"},
                     "eventos": [
                         {"t": t[1] - 0.3, "clip": "talk1", "dur": 2.0},
                         {"t": t[3] - 0.3, "clip": "nod_yes", "una_vez": True},
                         {"t": t[5] - 0.3, "clip": "acknowledge", "una_vez": True},
                     ], "clip_final": "idle"},
            "aiden": {"modelo": "aiden", "cuero": [0.085, 0.057, 0.04], "inicio": {"pos": [3.7, 5.4], "yaw": -90.0, "clip": "bashful"},
                      "eventos": [
                          {"t": t[0], "clip": "bashful", "dur": 10.0},
                          {"t": t[4] - 0.2, "clip": "sigh", "una_vez": True},
                          {"t": t[6] + vs[6]["dur"] - 2.4, "gira": 0.0, "dur": 0.7, "clip": "idle"},
                          {"walk": [[3.9, 3.8], [3.0, 2.4], [3.0, 0.6], [3.0, -0.2]], "clip": "walk"},
                      ], "clip_final": "idle"},
        },
        "props": {},
        "diag": [
            {"n": "kate_cara", "t": t[1] + 0.8, "sigue": "kate", "hueso": "Head", "off": [0.3, 0.02, 0.5], "fov": 24},
            {"n": "aiden_cara", "t": t[2] + 1.0, "sigue": "aiden", "hueso": "Head", "off": [0.0, 0.02, 0.5], "fov": 24},
            {"n": "kate_manos", "t": t[3] + 0.3, "sigue": "kate", "hueso": "L_Hand", "off": [0.0, 0.1, 0.5], "fov": 34},
        ],
        "miradas": [
            {"actor": "kate", "t0": 0.0, "t1": dur, "a": "aiden", "alto": 1.6},
            {"actor": "aiden", "t0": t[0] + 1.0, "t1": t[1] + 1.0, "a": [3.0, 0.4, 5.9]},
            {"actor": "aiden", "t0": t[1] + 1.0, "t1": t[6] + 1.0, "a": "kate", "alto": 1.55},
        ],
        "tomas": [
            {"id": "t01", "camara": "cam_s4_general", "plano": "los dos junto al canal", "t0": 0.0, "t1": t[1] - 0.2, "pos": [3.0, 1.7, 3.2], "pos_fin": [3.0, 1.7, 3.0], "mira": [3.0, 1.2, 5.4], "fov": 56},
            {"id": "t02", "camara": "cam_s4_aiden", "plano": "Aiden", "t0": t[1] - 0.2, "t1": t[2] - 0.2, "pos": [1.7, 1.55, 5.7], "mira": [3.7, 1.5, 5.4], "fov": 34},
            {"id": "t03", "camara": "cam_s4_kate", "plano": "Kate", "t0": t[2] - 0.2, "t1": t[4] - 0.2, "pos": [4.3, 1.55, 5.7], "mira": [2.3, 1.5, 5.4], "fov": 34},
            {"id": "t04", "camara": "cam_s4_dos", "plano": "los dos de perfil", "t0": t[4] - 0.2, "t1": t[6] + 0.5, "pos": [3.0, 1.55, 7.0], "pos_fin": [3.0, 1.55, 6.7], "mira": [3.0, 1.45, 5.4], "fov": 44},
            {"id": "t05", "camara": "cam_s4_sale", "plano": "Aiden se va", "t0": t[6] + 0.5, "t1": dur, "pos": [3.0, 1.7, 7.0], "sigue": "aiden", "sigue_alto": 1.1, "mira": [3, 1, 3], "fov": 50},
        ],
    }


# ───────────────────────────────────────────────────────────── ESCENA 5 · EL REGISTRO OCULTO (corte a negro)
def escena_5() -> dict:
    vs = lineas("oculto", 2.0)
    t = [v["t"] for v in vs]      # 0 EVA · 1 K · 2 EVA · 3 K
    dur = round(fin(vs) + 3.0, 2)
    MINI = [-5.15, 0.8, 6.1]
    return {
        "titulo": "Cap. 3 · Escena 5 · El registro oculto",
        "dur": dur, "voces": vs,
        "actores": {
            "kate": {"modelo": "kate", "cuero": [0.27, 0.10, 0.045], "inicio": {"pos": [-4.3, 4.9], "yaw": -90.0, "clip": "tablet"},
                     "eventos": [
                         {"t": t[1] - 0.3, "gira": -40.0, "dur": 0.9, "clip": "idle"},
                         {"t": t[2], "clip": "thinking", "dur": vs[2]["dur"] + 0.3},
                         {"t": t[3] - 0.3, "gira": -90.0, "dur": 0.9, "clip": "idle"},
                     ], "clip_final": "idle"},
            "eva": {"modelo": "eva", "escala": 0.2, "holograma": True, "inicio": {"pos": [MINI[0], MINI[2]], "y": MINI[1] + 0.07, "yaw": 50.0, "clip": "idle"},
                    "visible": [[t[0] - 1.2, fin(vs) + 0.5]],
                    "eventos": [
                        {"t": t[0], "clip": "talk1", "dur": vs[0]["dur"] + 0.3},
                        {"t": t[2], "clip": "talk1", "dur": vs[2]["dur"] + 0.3},
                    ], "clip_final": "idle"},
        },
        "props": {},
        "miradas": [
            {"actor": "kate", "t0": 0.0, "t1": t[0] + 0.3, "a": [-5.6, 1.35, 5.4]},
            {"actor": "kate", "t0": t[1] - 0.3, "t1": t[3] + 0.5, "a": "eva", "alto": 0.35},
            {"actor": "eva", "t0": t[0], "t1": fin(vs), "a": "kate", "alto": 1.6, "peso_cabeza": 0.8},
        ],
        "diag": [],
        "tomas": [
            {"id": "t01", "camara": "cam_s5_general", "plano": "Kate frente a la consola", "t0": 0.0, "t1": t[1] - 0.3, "pos": [-1.0, 1.9, 3.2], "pos_fin": [-1.4, 1.8, 3.6], "mira": [-4.8, 1.2, 5.4], "fov": 52},
            {"id": "t02", "camara": "cam_s5_eva", "plano": "EVA en la consola", "t0": t[1] - 0.3, "t1": t[2] - 0.2, "pos": [-4.0, 1.05, 5.6], "mira": [-5.15, 0.95, 6.1], "fov": 30},
            {"id": "t03", "camara": "cam_s5_kate", "plano": "Kate preocupada", "t0": t[2] - 0.2, "t1": dur, "pos": [-3.7, 1.55, 7.0], "pos_fin": [-3.6, 1.55, 6.8], "mira": [-4.3, 1.5, 4.9], "fov": 32},
        ],
    }


ESCENAS = {"s1": escena_1, "s2": escena_2, "s3": escena_3, "s4": escena_4, "s5": escena_5}

if __name__ == "__main__":
    out = {"global": {"fundido_cuadros": 8}, "escenas": {k: f() for k, f in ESCENAS.items()}}
    json.dump(out, open(GODOT / "data" / "storyboard_e03.json", "w"), indent=1, ensure_ascii=False)
    for k, e in out["escenas"].items():
        print(k, "dur", e["dur"], "tomas", len(e["tomas"]), "voces", len(e["voces"]))
