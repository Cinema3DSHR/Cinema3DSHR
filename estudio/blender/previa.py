"""Previsualización 3D interactiva de una escena (EDITOR 3D de la app).

Se exporta desde LA MISMA escena que se renderiza (`director.construir` sobre el mismo escena.json): misma geometría,
mismos personajes con sus esqueletos originales, las mismas acciones NLA horneadas fotograma a fotograma, las mismas
cámaras de rodaje y las mismas luces. Lo único que cambia para que ande en un teléfono: los materiales procedurales
se reemplazan por su color base (las texturas reales de personajes y armas se conservan) y el fondo lejano marcado
`visor_omitir` no se exporta.

Salen dos archivos por versión de escena (van a la release de la producción):
  <escena>_v<k>_previa.glb    geometría + esqueletos + una animación "escena" con todo (personajes, puertas, cámaras)
  <escena>_v<k>_previa.json   línea de tiempo legible: qué clip hace cada personaje y cuándo, tomas y cámaras
                              (con FOV y focal), destellos (fogonazos, impactos), anclas, huella de la receta.

Coordenadas: el GLB está en ejes glTF (Y arriba). Blender → glTF: (x, y, z) → (x, z, −y). Los archivos de cámara del
director se guardan SIEMPRE en coordenadas de Blender (ver `camara_director.py`).
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import bpy
from estudio import manifiesto as MF


def _aplanar_materiales():
    for m in bpy.data.materials:
        meta = m.get("estudio")
        if not meta or not m.use_nodes:
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        if bsdf.inputs["Emission Strength"].is_linked:
            for l in list(bsdf.inputs["Emission Strength"].links):
                m.node_tree.links.remove(l)
            bsdf.inputs["Emission Strength"].default_value = 0.0
        for inp in ("Base Color", "Roughness", "Normal", "Emission Color", "Alpha"):
            for l in list(bsdf.inputs[inp].links):
                m.node_tree.links.remove(l)
        bsdf.inputs["Base Color"].default_value = (*meta["color"], 1)
        if meta.get("emision"):
            bsdf.inputs["Emission Color"].default_value = (*meta["emision"], 1)
        bsdf.inputs["Roughness"].default_value = meta["rugosidad"]


def _visibilidad() -> dict:
    """{objeto: [[frame_desde, frame_hasta), …]} de los objetos que aparecen y desaparecen (fogonazos, impactos)."""
    sc = bpy.context.scene
    out = {}
    for o in bpy.data.objects:
        ad = o.animation_data
        if not ad or not ad.action:
            continue
        fcs = [fc for fc in __import__("estudio.blender.kit", fromlist=["_fcurves"])._fcurves(ad.action)
               if fc.data_path == "hide_render"]
        if not fcs:
            continue
        tramos, ini = [], None
        for f in range(sc.frame_start, sc.frame_end + 2):
            oculto = fcs[0].evaluate(f) > 0.5 if f <= sc.frame_end else True
            if not oculto and ini is None:
                ini = f
            elif oculto and ini is not None:
                tramos.append([ini, f])
                ini = None
        if tramos:
            out[o.name] = tramos
    return out


def _lente(cam) -> dict:
    cd = cam.data
    sc = bpy.context.scene
    asp = sc.render.resolution_x / sc.render.resolution_y
    # sensor_fit AUTO con imagen apaisada: el sensor de 36 mm es el ancho
    fov_h = 2 * math.atan(cd.sensor_width / 2 / cd.lens)
    fov_v = 2 * math.atan(math.tan(fov_h / 2) / asp)
    return {"lente_mm": round(cd.lens, 4), "sensor_mm": cd.sensor_width, "ajuste_sensor": cd.sensor_fit,
            "fov_h_deg": round(math.degrees(fov_h), 4), "fov_v_deg": round(math.degrees(fov_v), 4)}


def exportar(res: dict, manifiesto: dict, ruta_glb: Path, ruta_json: Path, max_poligonos: int = 60000,
             presupuesto: int = 700000) -> dict:
    s = res["escena"]
    fps = s.render.fps
    ruta_glb.parent.mkdir(parents=True, exist_ok=True)
    vis = _visibilidad()
    _aplanar_materiales()
    for o in bpy.data.objects:
        if o.get("visor_omitir"):
            o.hide_set(True)
    # escenas grandes: las mallas pesadas que no son personajes se alivianan SÓLO en el GLB del teléfono (la escena del
    # render no se toca: es un modificador temporal); con más de 40 s, la animación se muestrea cada 2 cuadros
    # mallas livianas para el teléfono: cada malla se reduce UNA vez y se reasigna a todos los objetos que la usan (así el
    # GLB la sigue compartiendo: los 21 vagones son la misma malla); los autos de Dream Rally usan su versión «_lo» del
    # juego. La escena del render no cambia: las mallas originales se devuelven después de exportar.
    pesadas = [o for o in bpy.data.objects if o.type == "MESH" and o.visible_get()
               and not any(m.type == "ARMATURE" for m in o.modifiers)]
    total = sum(len(o.data.polygons) for o in pesadas)
    proporcion = min(1.0, presupuesto / total) if total else 1.0
    originales, reemplazo, lo_cache = [], {}, {}
    dg = bpy.context.evaluated_depsgraph_get()
    for o in pesadas:
        me = o.data
        if me.name not in reemplazo:
            nuevo = None
            ref_lo = o.get("visor_lo")
            if ref_lo:
                if ref_lo not in lo_cache:
                    from estudio.blender import importar as I
                    objs = I.importar(ref_lo)
                    m_lo = next((x.data for x in objs if x.type == "MESH"), None)
                    for x in objs:
                        bpy.data.objects.remove(x)
                    lo_cache[ref_lo] = m_lo
                nuevo = lo_cache[ref_lo]
            else:
                n = len(me.polygons)
                r = min(proporcion if n > 1500 else 1.0, max_poligonos / n if n > max_poligonos else 1.0)
                if r < 0.98:
                    tmp = bpy.data.objects.new("_previa_tmp", me)
                    s.collection.objects.link(tmp)
                    mod = tmp.modifiers.new("d", "DECIMATE")
                    mod.ratio = max(0.02, r)
                    dg.update()
                    nuevo = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
                    bpy.data.objects.remove(tmp)
            reemplazo[me.name] = nuevo
        if reemplazo[me.name] is not None:
            originales.append((o, me))
            o.data = reemplazo[me.name]
    print(f"previa: {total} polígonos en {len(pesadas)} mallas, proporción {proporcion:.3f}, {len(originales)} reemplazadas")
    # piezas que sólo giran (ruedas, ejes): en el visor quedan quietas (la animación muestreada pesaba decenas de MB)
    sin_anim = []
    for o in bpy.data.objects:
        if o.get("visor_sin_anim") and o.animation_data and o.animation_data.action:
            sin_anim.append((o, o.animation_data.action, o.animation_data.action_slot))
            o.animation_data.action = None
    dur = s.frame_end / fps
    paso = 1 if dur <= 40 else (2 if dur <= 60 else 3)
    bpy.ops.export_scene.gltf(
        filepath=str(ruta_glb), export_format="GLB", use_visible=True, export_apply=False,
        export_lights=True, export_cameras=True, export_extras=True, export_yup=True,
        export_animations=True, export_animation_mode="SCENE", export_force_sampling=True,
        export_frame_range=True, export_frame_step=paso, export_optimize_animation_size=True,
        export_image_format="WEBP")
    for o, a, slot in sin_anim:
        o.animation_data.action = a
        if slot is not None:
            o.animation_data.action_slot = slot
    for o, me in originales:
        o.data = me
    actores = []
    for spec in manifiesto.get("personajes", []):
        pj = res["personajes"][spec["id"]]
        acciones = []
        for ac, tr in zip(spec.get("acciones", []), pj["tramos"]):
            acciones.append({"clip": ac["clip"].split("/")[-1].rsplit(".", 1)[0], "archivo": ac["clip"],
                             "inicio_s": round((tr["f0"] - 1) / fps, 4), "fin_s": round((tr["fin"] - 1) / fps, 4),
                             "ciclos": ac.get("repetir", 1), "velocidad": ac.get("velocidad", 1.0),
                             "rumbo_deg": round(math.degrees(tr["rumbo"]), 2)})
        actores.append({"id": spec["id"], "modelo": spec.get("modelo"), "arma": spec.get("arma"),
                         "nodo": pj["raiz"].name, "armadura": pj["armadura"].name,
                         "nodo_arma": pj["arma"].name if pj.get("arma") else None,
                         "disparos_s": spec.get("disparos", []), "acciones": acciones})
    tomas = []
    for t in res["tomas"]:
        sp = t["spec"]
        tomas.append({"id": sp["id"], "tipo": sp["tipo"], "plano": sp.get("plano", ""),
                      "inicio_s": round((t["frame_inicio"] - 1) / fps, 4), "fin_s": round(t["frame_fin"] / fps, 4),
                      "frame_inicio": t["frame_inicio"], "frame_fin": t["frame_fin"], "camara": t["camara"].name,
                      **_lente(t["camara"])})
    # muestras de control (coordenadas de Blender) para comprobar que el visor reproduce lo mismo que el render
    control = {"frames": [], "caderas": {a["id"]: [] for a in actores}, "camaras": {}}
    for f in sorted({1, *range(60, s.frame_end + 1, 120), s.frame_end}):
        s.frame_set(f)
        control["frames"].append(f)
        for a in actores:
            pj = res["personajes"][a["id"]]
            arm = pj["armadura"]
            h = arm.matrix_world @ arm.pose.bones[pj["info"]["cadera"]].head
            control["caderas"][a["id"]].append([round(v, 4) for v in h])
    for t in res["tomas"]:
        f = (t["frame_inicio"] + t["frame_fin"]) // 2
        s.frame_set(f)
        mw = t["camara"].matrix_world
        control["camaras"][t["camara"].name] = {"frame": f, "matriz": [[round(v, 6) for v in fila] for fila in mw]}
    datos = {
        "formato": "estudio.previa/1", "produccion": manifiesto["produccion"], "escena_id": manifiesto["id"],
        "version": manifiesto.get("version", 1), "huella": MF.huella(manifiesto), "titulo": manifiesto.get("titulo", ""),
        "fps": fps, "frames": s.frame_end, "duracion_s": s.frame_end / fps,
        "resolucion": [s.render.resolution_x, s.render.resolution_y],
        "coordenadas": {"glb": "glTF Y arriba", "blender_desde_glb": "(x, y, z)_blender = (x, -z, y)_glb",
                        "camara": "mira hacia −Z local con +Y local arriba (igual en Blender, glTF y Godot)"},
        "tiempo": {"pelicula": "t = (cuadro − 1) / fps", "glb": "t_glb = cuadro / fps (Blender exporta el cuadro f en f/fps)"},
        "animacion": "escena", "actores": actores, "tomas": tomas, "visibilidad": vis,
        "eventos": manifiesto.get("eventos", []),
        "anclas": {k: list(v) for k, v in res["contexto"].anclas.items()},
        "control": control,
        "render": {"motor": "CYCLES", "dispositivo": "CPU", "resolucion": "1280x720", "fps": fps, "muestras": 6},
    }
    ruta_json.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
    return {"glb_bytes": ruta_glb.stat().st_size, "json_bytes": ruta_json.stat().st_size}
