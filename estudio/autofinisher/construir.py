"""Punto de entrada del AutoFinisher (bpy): GLB de Godot + receta → versión autónoma en una carpeta.

    <python de Blender> -m estudio.autofinisher construir --receta R.json --glb escena.glb --version 1 --salida DIR
                        [--godot 4.7.2]

Deja en DIR (que no puede existir: una versión no se sobrescribe):
    <produccion>_v<NNN>.blend   proyecto autónomo        <produccion>_v<NNN>.glb   copia del GLB de entrada
    manifest.json               identidad y hashes       informe_preparacion.json  tiempos, RAM, inspección
No renderiza. Si algo no se puede empaquetar o falta un vacío que la receta pide, falla sin dejar la versión.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import bpy

from estudio.autofinisher import (auto_cinema, auto_effects, auto_import, auto_lights, auto_materials, auto_pack,
                                  auto_report, manifiesto as MF, medicion as MD, receta as RC)


def construir(ruta_receta: str, glb: str, version: int, salida: str, godot: str | None = None) -> dict:
    cron = MD.Cronometro()
    receta = RC.leer(ruta_receta)
    out = Path(salida)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"{out} ya existe y tiene archivos: una versión no se sobrescribe (usá una versión nueva)")
    out.mkdir(parents=True, exist_ok=True)
    nom = MF.nombres(receta["produccion"], version)
    blend, glb_copia, informe_p, man_p = out / nom["blend"], out / nom["glb"], out / nom["informe"], out / nom["manifiesto"]
    res = {}
    try:
        with cron.etapa("copiar_glb") as e:
            shutil.copy2(glb, glb_copia)
            e["glb_mb"] = round(glb_copia.stat().st_size / 1e6, 2)
        with cron.etapa("1_auto_import"):
            res["auto_import"] = auto_import.importar(str(glb_copia), receta)
        with cron.etapa("2_auto_lights"):
            res["auto_lights"] = auto_lights.corregir(receta)
        with cron.etapa("3_auto_materials"):
            res["auto_materials"] = auto_materials.corregir(receta)
        with cron.etapa("4_auto_effects"):
            res["auto_effects"] = auto_effects.aplicar(receta)
        with cron.etapa("5_auto_cinema"):
            res["auto_cinema"] = auto_cinema.preparar(receta)
        with cron.etapa("6_auto_pack"):
            res["auto_pack"] = auto_pack.empaquetar()
        if not res["auto_pack"]["autonomo"]:
            raise RuntimeError(f"el .blend no quedaría autónomo, recursos externos: {res['auto_pack']['externos']}")
        with cron.etapa("7_guardar_blend") as e:
            bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()), compress=True)
            e["blend_mb"] = round(blend.stat().st_size / 1e6, 2)
        with cron.etapa("8_manifiesto_y_hashes"):
            vers = auto_report.versiones(godot or receta.get("godot", {}).get("version"))
            inf = auto_report.informe(cron, res, {"produccion": receta["produccion"], "version": version,
                                                  "receta": str(ruta_receta), "glb_entrada": str(glb)})
            informe_p.write_text(json.dumps(inf, ensure_ascii=False, indent=1))
            m = MF.construir(receta, version, blend, glb_copia, informe_p, res["auto_pack"], vers, MD.sha256(ruta_receta))
            err = MF.errores(m)
            if err:
                raise ValueError("manifiesto inválido: " + "; ".join(err))
        # el informe definitivo incluye la etapa de manifiesto ya cerrada
        inf = auto_report.informe(cron, res, {"produccion": receta["produccion"], "version": version,
                                              "receta": str(ruta_receta), "glb_entrada": str(glb)})
        informe_p.write_text(json.dumps(inf, ensure_ascii=False, indent=1))
        m = MF.construir(receta, version, blend, glb_copia, informe_p, res["auto_pack"], vers, MD.sha256(ruta_receta))
        man_p.write_text(json.dumps(m, ensure_ascii=False, indent=1))
        return {"salida": str(out), "manifiesto": m, "segundos": cron.total(), "ram_max_mb": MD.ram_max_mb()}
    except BaseException:
        # una versión fallida no queda a medias: se borra la carpeta y se guarda el informe del error al lado
        err_p = out.with_name(out.name + "_ERROR.json")
        err_p.write_text(json.dumps({"etapas": cron.etapas, "resultados": res}, ensure_ascii=False, indent=1, default=str))
        shutil.rmtree(out, ignore_errors=True)
        raise
