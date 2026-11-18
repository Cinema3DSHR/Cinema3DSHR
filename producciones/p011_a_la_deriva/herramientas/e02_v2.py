"""E02 v2 = la v1 con SÓLO las animaciones de Aiden corregidas (pedido del dueño, 18/11/2026):

  caminar   Walking_2 («Male Drunk Walk»)                  → Standard_Walk («Standard Walk»)
  frenar    Walk_To_Stop («… While Carrying Someone»)      → Stop_Walking («Walking To Standing Idle»)
  parado    Bored («Standing Around Bored Idle», brazos en péndulo, manos 0,87 m) → Breathing_Idle (manos 0,12 m)
  negar     Shake_Gesture («Big Vegas Shaking Gesturing»)  → annoyed_head_shake («Shaking Head No Annoyed»)

Todo lo demás es la v1 tal cual (diálogos, tiempos, duración, Kate, utilería, escenario, cámaras): así el sistema de
componentes rehace sólo a Aiden, la utilería y las cámaras que lo siguen. Aiden llega a los MISMOS lugares en los
MISMOS segundos que en la v1 (la bandeja de poda, la mesa de Kate, el lugar donde discute con EVA): las caminatas se
calculan con lo que avanza cada clip ya adaptado al esqueleto de Aiden (medido):
  Standard_Walk  1,7896 m por ciclo de 35 cuadros · Stop_Walking 1,1827 m (+0,0593 m al costado) en 90 cuadros
  (v1) Walking_2 2,94 m / 63 cuadros · Walk_To_Stop 1,62 m (+0,01) / 147 cuadros
Uso: python producciones/p011_a_la_deriva/herramientas/e02_v2.py   → escenas/e02/v2/escena.json (la v1 no se toca)
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from estudio import manifiesto as MF  # noqa: E402

A = "mixamo:animaciones/"
CAMINAR = A + "caminar_correr/Standard_Walk.fbx"
FRENAR = A + "caminar_correr/Stop_Walking.fbx"
PARADO = A + "trabajo_acciones/Breathing_Idle.fbx"
NIEGA = "mixamo:packs/Gestures_Pack_Basic/annoyed_head_shake.fbx"
D_W, T_W = (0.0, -1.7896), 35 / 30          # avance local (x al costado, y = −adelante) y duración de un ciclo
D_S, T_S = (0.0593, -1.1827), 90 / 30
T_I = 298 / 30                               # Breathing_Idle
T_H = 77 / 30                                # annoyed_head_shake
D_W1, D_S1 = (0.0, -2.94), (0.01, -1.62)     # v1 (para saber dónde terminaba exactamente)


def mundo(d, rumbo_deg):
    """Avance local del clip → mundo con el personaje mirando a rumbo_deg (convención de personajes.py)."""
    t = math.radians(rumbo_deg + 90)
    return (d[0] * math.cos(t) - d[1] * math.sin(t), d[0] * math.sin(t) + d[1] * math.cos(t))


def suma(p, *vs):
    return (p[0] + sum(v[0] for v in vs), p[1] + sum(v[1] for v in vs))


def menos(p, *vs):
    return (p[0] - sum(v[0] for v in vs), p[1] - sum(v[1] for v in vs))


def k(v, n):
    return (v[0] * n, v[1] * n)


def armar() -> dict:
    v1 = MF.leer(MF.ruta_escena("p011_a_la_deriva", "e02", 1))
    ac1 = v1["personajes"][0]["acciones"]
    assert v1["personajes"][0]["id"] == "aiden"
    t = {i: a["inicio_s"] for i, a in enumerate(ac1)}
    # dónde terminaba Aiden en la v1 (exacto, con el desvío de cada clip)
    p0_1 = tuple(ac1[6]["pos"][:2])
    bandeja_1 = suma(p0_1, k(mundo(D_W1, -82), 2), k(mundo(D_W1, -90), 2), mundo(D_W1, -95), mundo(D_S1, -95))
    mesa_1 = suma(tuple(ac1[14]["pos"][:2]), k(mundo(D_W1, ac1[14]["mirando_deg"]), 2), mundo(D_S1, ac1[14]["mirando_deg"]))
    eva_1 = suma(tuple(ac1[19]["pos"][:2]), k(mundo(D_W1, 90), 4), mundo(D_S1, 90))
    # 1) del puesto a la bandeja: 2 ciclos en diagonal, 4 derecho por el pasillo, 2 despacio entre las flores y frena;
    #    termina en el mismo lugar y en el mismo segundo (36,515 s) que la v1
    fin_1 = t[10]
    ini_s1 = fin_1 - T_S
    n_a, n_b, n_c = 2, 4, 2
    v_ab = v_c = round((n_a + n_b + n_c) * T_W / (ini_s1 - t[6]), 4)   # paso parejo, lento y cansado (~1,1 m/s)
    t_ab = (n_a + n_b) * T_W / v_ab
    p0 = menos(bandeja_1, k(mundo(D_W, -82), n_a), k(mundo(D_W, -90), n_b), k(mundo(D_W, -95), n_c), mundo(D_S, -95))
    # 2) del corte al comedor: entra desde el botánico y frena del otro lado de la mesa, en el segundo de la v1 (65,08)
    llega = t[16]
    n_d = 5
    v_d = n_d * T_W / (llega - T_S - t[14])
    rumbo_d = -90.0
    pD = menos(mesa_1, k(mundo(D_W, rumbo_d), n_d), mundo(D_S, rumbo_d))
    # 3) se va: desde donde estaba parado hacia la puerta; frena entre las flores donde discute con EVA (99,93 s)
    para_eva = t[21]
    n_e = 7
    v_e = n_e * T_W / (para_eva - T_S - t[19])
    pE = menos(eva_1, k(mundo(D_W, 90), n_e), mundo(D_S, 90))
    ac = copy.deepcopy(ac1[:6])                                        # sentado y levantarse: igual que la v1
    ac += [
        {"clip": CAMINAR, "inicio_s": t[6], "pos": [round(p0[0], 4), round(p0[1], 4), 0.0], "mirando_deg": -82,
         "repetir": n_a, "velocidad": v_ab, "mezcla_s": 0.3},
        {"clip": CAMINAR, "inicio_s": round(t[6] + n_a * T_W / v_ab, 4), "encadenar": True, "mirando_deg": -90,
         "giro_s": 0.6, "repetir": n_b, "velocidad": v_ab},
        {"clip": CAMINAR, "inicio_s": round(t[6] + t_ab, 4), "encadenar": True, "mirando_deg": -95, "giro_s": 0.8,
         "repetir": n_c, "velocidad": round(v_c, 4), "mezcla_s": 0.3},
        {"clip": FRENAR, "inicio_s": round(ini_s1, 4), "encadenar": True, "mirando_deg": -95, "mezcla_s": 0.4},
        {"clip": PARADO, "inicio_s": t[10], "encadenar": True, "mirando_deg": -95, "mezcla_s": 0.6},
        {"clip": PARADO, "inicio_s": t[11], "encadenar": True, "mirando_deg": 180, "giro_s": 1.2, "mezcla_s": 0.8},
        copy.deepcopy(ac1[12]),                                        # toma la flor (igual)
        {"clip": CAMINAR, "inicio_s": t[13], "encadenar": True, "mirando_deg": -90, "giro_s": 0.7,
         "repetir": 2, "velocidad": round(2 * T_W / (t[14] - t[13]), 4), "mezcla_s": 0.5},
        {"clip": CAMINAR, "inicio_s": t[14], "pos": [round(pD[0], 4), round(pD[1], 4), 0.0], "mirando_deg": rumbo_d,
         "repetir": n_d, "velocidad": round(v_d, 4), "mezcla_s": 0.1},
        {"clip": FRENAR, "inicio_s": round(llega - T_S, 4), "encadenar": True, "mirando_deg": rumbo_d, "mezcla_s": 0.4},
        {"clip": PARADO, "inicio_s": t[16], "encadenar": True, "mirando_deg": -90, "giro_s": 0.5, "mezcla_s": 0.8},
        copy.deepcopy(ac1[17]),                                        # deja la flor (igual)
        {"clip": PARADO, "inicio_s": t[18], "encadenar": True, "mirando_deg": -90, "repetir": 2, "mezcla_s": 0.7},
        {"clip": CAMINAR, "inicio_s": t[19], "pos": [round(pE[0], 4), round(pE[1], 4), 0.0], "mirando_deg": 90,
         "repetir": n_e, "velocidad": round(v_e, 4), "mezcla_s": 0.2},
        {"clip": FRENAR, "inicio_s": round(para_eva - T_S, 4), "encadenar": True, "mirando_deg": 90, "mezcla_s": 0.4},
        {"clip": PARADO, "inicio_s": t[21], "encadenar": True, "mirando_deg": 90, "repetir": 2, "mezcla_s": 0.8},
        {"clip": NIEGA, "inicio_s": t[22], "encadenar": True, "mirando_deg": 90, "mezcla_s": 0.4},
        {"clip": PARADO, "inicio_s": round(t[22] + T_H - 0.15, 4), "encadenar": True, "mirando_deg": 90, "mezcla_s": 0.5},
    ]
    v2 = copy.deepcopy(v1)
    v2["version"] = 2
    v2["estado"] = "borrador"
    v2["bloqueada"] = False
    v2.pop("salidas", None)
    v2["personajes"][0]["acciones"] = ac
    v2.setdefault("historial", []).append({
        "desde_version": 1, "motivo": "dueño: caminata de borracho (Walking_2) → Standard_Walk; Walk_To_Stop («llevando a "
        "alguien») → Stop_Walking; Bored (brazos en péndulo) → Breathing_Idle; Shake_Gesture («Big Vegas») → "
        "annoyed_head_shake. Mismos lugares y tiempos que la v1; el resto de la escena, igual."})
    v2["notas_puesta"] = {**v1.get("notas_puesta", {}), "v2": {
        "inicio_caminata": [round(p0[0], 3), round(p0[1], 3)], "bandeja": [round(bandeja_1[0], 3), round(bandeja_1[1], 3)],
        "entra_comedor": [round(pD[0], 3), round(pD[1], 3)], "mesa": [round(mesa_1[0], 3), round(mesa_1[1], 3)],
        "sale_comedor": [round(pE[0], 3), round(pE[1], 3)], "discute_con_eva": [round(eva_1[0], 3), round(eva_1[1], 3)],
        "velocidades": {"pasillo": v_ab, "flores": round(v_c, 3), "al_comedor": round(v_d, 3), "vuelta": round(v_e, 3)}}}
    return v2


if __name__ == "__main__":
    e = armar()
    out = MF.ruta_escena("p011_a_la_deriva", "e02", 2)
    MF.escribir(out, e)                       # se niega si v2 ya estuviera entregada
    print(out, json.dumps(e["notas_puesta"]["v2"], ensure_ascii=False))
