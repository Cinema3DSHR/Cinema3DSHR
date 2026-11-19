"""AutoMaterials (bpy): correcciones de materiales que el GLB no transfiere bien y el mundo (que no viaja).

- Vidrios (convenciones: nombre «vidrio*» o cine_tipo «vidrio»): Godot los manda como transparencia alfa; en Cycles se
  rehacen con transmisión 1 + IOR (reflejos y refracción). La receta ajusta cada vidrio por nombre (rugosidad, ior,
  color) o lo excluye con null; los no listados usan `vidrio_por_defecto`.
- Emisivos: la emisión llega con su intensidad (KHR_materials_emissive_strength); la receta puede escalarla por
  nombre o prefijo (`emisivos: {"neon": 1.5}`). Sin pedido, no se tocan.
- Mundo: el WorldEnvironment de Godot llega como vacío; se arma el mundo de Blender con el color de la receta.
"""
from __future__ import annotations

import bpy

from estudio.autofinisher import convenciones as CV

VIDRIO_POR_DEFECTO = {"rugosidad": 0.0, "ior": 1.45}


def _bsdf(m):
    if not m.use_nodes:
        return None
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def corregir(receta: dict) -> dict:
    cfg = receta.get("materiales", {})
    vidrios = cfg.get("vidrios", {})
    defecto = {**VIDRIO_POR_DEFECTO, **cfg.get("vidrio_por_defecto", {})}
    emisivos = cfg.get("emisivos", {})
    hecho = {"vidrios": [], "vidrios_excluidos": [], "emisivos": [], "emisivos_escalados": []}
    for m in bpy.data.materials:
        b = _bsdf(m)
        if b is None:
            continue
        if CV.es_vidrio(m.name, m.get("cine_tipo")):
            if m.name in vidrios and vidrios[m.name] is None:
                hecho["vidrios_excluidos"].append(m.name)
            else:
                v = {**defecto, **(vidrios.get(m.name) or {})}
                alfa = b.inputs["Alpha"].default_value
                b.inputs["Alpha"].default_value = 1.0
                b.inputs["Transmission Weight"].default_value = 1.0
                b.inputs["Roughness"].default_value = float(v["rugosidad"])
                b.inputs["IOR"].default_value = float(v["ior"])
                if v.get("color"):
                    b.inputs["Base Color"].default_value = (*v["color"][:3], 1.0)
                m.surface_render_method = "DITHERED"
                hecho["vidrios"].append(f"{m.name}: alfa {alfa:.2f} → transmisión 1, IOR {v['ior']}, rugosidad {v['rugosidad']}")
        em = b.inputs["Emission Strength"].default_value
        if em > 0 or CV.es_emisivo_por_nombre(m.name, m.get("cine_tipo")):
            factor = next((f for clave, f in emisivos.items() if m.name == clave or m.name.startswith(clave)), None)
            if factor is not None:
                b.inputs["Emission Strength"].default_value = em * float(factor)
                hecho["emisivos_escalados"].append(f"{m.name}: {em} × {factor}")
            hecho["emisivos"].append(f"{m.name}: {round(b.inputs['Emission Strength'].default_value, 3)}")
    mundo = receta.get("mundo")
    if mundo:
        w = bpy.data.worlds.new(mundo.get("nombre", "Mundo"))
        bpy.context.scene.world = w
        w.use_nodes = True
        bg = w.node_tree.nodes["Background"]
        bg.inputs["Color"].default_value = (*mundo.get("color", (0.05, 0.05, 0.05))[:3], 1.0)
        bg.inputs["Strength"].default_value = float(mundo.get("fuerza", 1.0))
        hecho["mundo"] = {"color": mundo.get("color"), "fuerza": mundo.get("fuerza", 1.0)}
    return hecho
