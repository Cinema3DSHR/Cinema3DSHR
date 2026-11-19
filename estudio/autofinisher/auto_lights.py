"""AutoLights (bpy): recupera la intensidad de las luces que vienen de Godot, por PERFIL (convenciones.py).

Lo que pasa en el camino (medido en la prueba «Casa moderna en tormenta», Godot 4.7.2 → Blender 5.3):
- Godot exporta su «energía» tal cual como candelas (puntual/foco) o lux (sol); el importador de Blender la pasa a
  vatios con W = cd·4π/683 (puntual/foco) y W/m² = lux/683 (sol): quedan en ~0,01 W. Se deshace esa conversión y se
  aplica la escala del perfil (unidad de Godot → vatios de Blender).
- Las claves de energía ANIMADAS (KHR_animation_pointer) de luces puntuales y focos llegan además divididas por 4π
  (fuego 1,5–2,5 → 0,10–0,16); las del sol llegan bien. Se reescalan con el factor 4π extra.
- Radio de las luces 5 cm (sombras definidas, como en Godot); el sol con 2° de diámetro angular.
"""
from __future__ import annotations

import math

import bpy
from bpy_extras import anim_utils

from estudio.autofinisher import convenciones as CV

A_GODOT = {"POINT": 683 / (4 * math.pi), "SPOT": 683 / (4 * math.pi), "SUN": 683.0, "AREA": 683 / (4 * math.pi)}
FACTOR_CLAVES = {"POINT": 4 * math.pi, "SPOT": 4 * math.pi, "SUN": 1.0, "AREA": 1.0}
RADIO = 0.05
ANGULO_SOL = 2.0


def _curvas(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return list(cb.fcurves) if cb else []


def corregir(receta: dict) -> dict:
    cfg = receta.get("luces", {})
    perfiles = {k: {**v} for k, v in CV.PERFILES_LUZ.items()}
    for k, v in cfg.get("perfiles", {}).items():
        perfiles.setdefault(k, {"tipos": (), "escala": 60.0}).update(v)
    por_objeto = cfg.get("objetos", {})
    hecho = {"luces": {}, "claves_reescaladas": 0, "avisos": []}
    for o in bpy.data.objects:
        if o.type != "LIGHT":
            continue
        L = o.data
        ajuste = por_objeto.get(o.name, {})
        perfil = ajuste.get("perfil") or CV.perfil_luz(o.name, L.type, o.get("cine_tipo"))
        p = perfiles.get(perfil, perfiles[CV.PERFIL_POR_TIPO.get(L.type, "puntual")])
        if p.get("tipos") and L.type not in p["tipos"]:
            hecho["avisos"].append(f"{o.name}: perfil «{perfil}» con una luz {L.type} (se usa igual su escala)")
        escala = float(ajuste.get("escala", p["escala"]))
        k = A_GODOT.get(L.type, A_GODOT["POINT"]) * escala
        antes = L.energy
        L.energy = antes * k
        if L.type == "SUN":
            L.angle = math.radians(float(p.get("angulo_sol_grados", ANGULO_SOL)))
        else:
            L.shadow_soft_size = float(p.get("radio", RADIO))
        kc = k * FACTOR_CLAVES.get(L.type, 1.0)
        n = 0
        for fc in _curvas(L):
            if fc.data_path == "energy":
                for kp in fc.keyframe_points:
                    kp.co.y *= kc
                    kp.handle_left.y *= kc
                    kp.handle_right.y *= kc
                    n += 1
        hecho["claves_reescaladas"] += n
        hecho["luces"][o.name] = {"tipo": L.type, "perfil": perfil, "escala": escala,
                                  "energia": [round(antes, 4), round(L.energy, 2)], "claves": n}
    return hecho
