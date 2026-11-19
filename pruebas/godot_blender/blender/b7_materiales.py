"""ETAPA 7 — Correcciones de materiales y luces después de importar.
- Vidrios: Godot los manda como transparencia (alfa); en Cycles se rehacen con transmisión (reflejos y refracción).
- Luces: el GLB convierte la energía de Godot a unidades fotométricas y Blender la lee casi en 0; se recupera la
  energía de Godot y se pasa a vatios con una escala por tipo (también en las claves animadas: relámpago y fuego).
- Ambiente: el WorldEnvironment de Godot no viaja; se arma el mundo de Blender con el mismo color."""
import math
import bpy
from bpy_extras import anim_utils

# lo que hace el importador: puntual/foco W = cd·4π/683 ; sol W/m² = lux/683 (Godot exporta su «energía» tal cual)
A_GODOT = {"POINT": 683 / (4 * math.pi), "SPOT": 683 / (4 * math.pi), "SUN": 683.0}
# escala elegida: Godot «energía» → vatios de Blender
A_BLENDER = {"POINT": 60.0, "SPOT": 120.0, "SUN": 0.6}
VIDRIOS = {"vidrio": (0.0, 1.45), "vidrio_verde": (0.05, 1.5), "vidrio_ambar": (0.05, 1.5), "vidrio_negro": None}


def _bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _curvas(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return list(cb.fcurves) if cb else []


def corregir() -> dict:
    hecho = {"vidrios": [], "luces": {}, "claves_luz_reescaladas": 0}
    for nombre, v in VIDRIOS.items():
        m = bpy.data.materials.get(nombre)
        if not m or v is None:
            continue
        b = _bsdf(m)
        alfa = b.inputs["Alpha"].default_value
        b.inputs["Alpha"].default_value = 1.0
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["Roughness"].default_value = v[0]
        b.inputs["IOR"].default_value = v[1]
        if nombre == "vidrio":                      # vidrio del ventanal: casi incoloro
            b.inputs["Base Color"].default_value = (0.92, 0.96, 1.0, 1.0)
        m.surface_render_method = "DITHERED"
        hecho["vidrios"].append(f"{nombre}: alfa {alfa:.2f} → transmisión 1, IOR {v[1]}")
    for o in bpy.data.objects:
        if o.type != "LIGHT":
            continue
        L = o.data
        k = A_GODOT[L.type] * A_BLENDER[L.type]
        antes = L.energy
        L.energy = antes * k
        L.shadow_soft_size = 0.05 if L.type != "SUN" else L.shadow_soft_size
        if L.type == "SUN":
            L.angle = math.radians(2.0)
        # las claves animadas (KHR_animation_pointer) llegan además divididas por 4π en luces puntuales y focos
        # (medido: el fuego de Godot 1,5–2,5 llegaba como 0,10–0,16 tras la escala de la luz fija)
        kc = k * (4 * math.pi if L.type in ("POINT", "SPOT") else 1.0)
        for fc in _curvas(L):
            if fc.data_path == "energy":
                for kp in fc.keyframe_points:
                    kp.co.y *= kc
                    kp.handle_left.y *= kc
                    kp.handle_right.y *= kc
                    hecho["claves_luz_reescaladas"] += 1
        hecho["luces"][o.name] = [round(antes, 4), round(L.energy, 2)]
    # mundo (el de Godot no viaja): fondo azul noche casi negro; el «cielo» real es la esfera emisiva del exterior
    w = bpy.data.worlds.new("Mundo_tormenta")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.004, 0.006, 0.011, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    return hecho
