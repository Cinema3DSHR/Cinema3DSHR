"""Director: arma una escena completa en Blender a partir de su manifiesto JSON y la renderiza por tomas.

El manifiesto es la "receta" editable de la escena (ver docs/MANIFIESTOS.md). Con él y los recursos referenciados
la escena se reconstruye siempre igual: el .blend que se guarda es una comodidad para editar a mano, no la fuente.
"""
from __future__ import annotations
import importlib
import json
import math
import time
from pathlib import Path

import bpy
from estudio import config
from estudio.blender import kit as K
from estudio.blender import camaras as C
from estudio.blender import vehiculos as V


def _modulo_escenario(gen: str):
    return importlib.import_module(f"estudio.escenarios.{gen}")


def construir(manifiesto: dict, calidad: str = "revision") -> dict:
    fps = manifiesto.get("render", {}).get("fps", 30)
    K.reiniciar_materiales()
    s = K.escena_vacia(manifiesto["id"])
    esc = manifiesto["escenario"]
    mod = _modulo_escenario(esc["generador"])
    info = mod.construir(esc.get("parametros", {}))
    ctx = C.Contexto(info["anclas"], fps)

    # eventos del escenario (abrir portón, encender luces…)
    for ev in manifiesto.get("eventos", []):
        fn = getattr(mod, ev["accion"], None)
        if fn is None:
            raise ValueError(f"El escenario {esc['generador']} no sabe hacer {ev['accion']!r}")
        fn(info["animables"], frame_inicio=int(ev["inicio_s"] * fps) + 1,
           **{k: v for k, v in ev.items() if k not in ("accion", "inicio_s")})

    # vehículos
    for vh in manifiesto.get("vehiculos", []):
        modelo = vh.get("modelo", "procedural:sedan")
        if modelo == "procedural:sedan":
            veh = V.sedan_procedural(vh["id"], tuple(vh.get("color", (0.02, 0.02, 0.025))))
        else:
            raise NotImplementedError(f"Modelo de vehículo {modelo} todavía no soportado (ver docs/VEHICULOS.md)")
        puntos = [ctx.punto(p, 0) for p in vh["recorrido"]]
        tray = V.animar_por_recorrido(veh, puntos, int(vh.get("inicio_s", 0) * fps) + 1,
                                      [tuple(x) for x in vh["tiempos"]], fps,
                                      duracion_s=manifiesto.get("duracion_s"))
        ctx.moviles[vh["id"]] = {"tray": tray, "anclas": veh["anclas"]}

    # personajes (Etapa 5): por ahora se validan y se ignoran con aviso
    for pj in manifiesto.get("personajes", []):
        print(f"[director] aviso: personaje {pj.get('id')} pendiente (Etapa 5)")

    # tomas
    tomas = [C.crear_toma(t, ctx) for t in manifiesto["tomas"]]
    duracion_f = max(t["frame_fin"] for t in tomas)
    s.frame_start, s.frame_end = 1, duracion_f
    s.render.fps = fps
    s.camera = tomas[0]["camara"]
    ajustes_render(s, calidad, manifiesto.get("render", {}))
    return {"escena": s, "tomas": tomas, "contexto": ctx, "info": info}


def ajustes_render(s, calidad: str, extra: dict):
    q = {**config.CALIDADES[calidad], **{k: v for k, v in extra.items() if k in ("muestras", "motor")}}
    s.render.engine = q["motor"]
    s.render.resolution_x, s.render.resolution_y = q["ancho"], q["alto"]
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "JPEG"
    s.render.image_settings.quality = 92
    s.render.use_motion_blur = extra.get("desenfoque_movimiento", False)
    try:
        s.view_settings.view_transform = "AgX"
        s.view_settings.look = extra.get("look", "AgX - Medium High Contrast")
    except TypeError:
        try:
            s.view_settings.look = "Medium High Contrast"
        except TypeError:
            pass
    s.view_settings.exposure = extra.get("exposicion", 0.0)
    if q["motor"] == "BLENDER_EEVEE":
        e = s.eevee
        e.taa_render_samples = q["muestras"]
        for attr, val in (("use_raytracing", extra.get("trazado_rayos", True)),
                          ("use_shadows", True),
                          ("use_volumetric_shadows", False),
                          ("volumetric_tile_size", "16"),
                          ("use_bloom", True)):
            try:
                setattr(e, attr, val)
            except (AttributeError, TypeError):
                pass
        try:
            e.ray_tracing_options.resolution_scale = "2"
            e.ray_tracing_options.use_denoise = True
            e.fast_gi_method = "GLOBAL_ILLUMINATION"
        except (AttributeError, TypeError):
            pass
    elif q["motor"] == "CYCLES":
        c = s.cycles
        c.device = "CPU"
        c.samples = q["muestras"]
        c.use_adaptive_sampling = True
        c.adaptive_threshold = 0.05
        c.use_denoising = True
        try:
            c.denoiser = "OPENIMAGEDENOISE"
            c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        except TypeError:
            pass
        c.max_bounces = 6
        c.diffuse_bounces = 2
        c.glossy_bounces = 3
        c.transmission_bounces = 4
        c.transparent_max_bounces = 8
        c.caustics_reflective = False
        c.caustics_refractive = False
        c.sample_clamp_indirect = 8.0
        s.render.use_persistent_data = True  # reutiliza la escena entre fotogramas (mucho más rápido)


def render_tomas(res: dict, carpeta: Path, solo: list[str] | None = None, cada: int = 1) -> dict:
    """Renderiza cada toma a JPG en carpeta/<toma>/f_0001.jpg. Reanuda si ya hay fotogramas.

    cada > 1 renderiza sólo 1 de cada N fotogramas (previsualización rápida tipo "animática").
    """
    s = res["escena"]
    informe = {}
    for t in res["tomas"]:
        tid = t["spec"]["id"]
        if solo and tid not in solo:
            continue
        d = carpeta / tid
        d.mkdir(parents=True, exist_ok=True)
        s.camera = t["camara"]
        t0 = time.time()
        hechos = 0
        for i, f in enumerate(range(t["frame_inicio"], t["frame_fin"] + 1)):
            if i % cada:
                continue
            out = d / f"f_{i + 1:04d}.jpg"
            if out.exists() and out.stat().st_size > 0:
                continue
            s.frame_set(f)
            s.render.filepath = str(out)
            bpy.ops.render.render(write_still=True)
            hechos += 1
        informe[tid] = {"fotogramas": t["frame_fin"] - t["frame_inicio"] + 1, "renderizados": hechos,
                        "segundos": round(time.time() - t0, 1)}
        print(f"[render] {tid}: {informe[tid]}", flush=True)
    return informe


def guardar_blend(ruta: Path):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ruta), compress=True)


def exportar_visor(ruta: Path, max_tex: int = 512):
    """GLB liviano para el visor Android: colores planos (sin texturas procedurales), luces, cámaras y animación.

    Se omiten fondo lejano de alto costo y la geometría oculta. Las instancias se realizan (el visor no las tiene).
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # en el visor los materiales procedurales se reemplazan por su color base equivalente
    for m in bpy.data.materials:
        meta = m.get("estudio")
        if not meta or not m.use_nodes:
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        if bsdf.inputs["Emission Strength"].is_linked:  # ventanas procedurales: en el visor, silueta oscura
            for l in list(bsdf.inputs["Emission Strength"].links):
                m.node_tree.links.remove(l)
            bsdf.inputs["Emission Strength"].default_value = 0.0
        for inp in ("Base Color", "Roughness", "Normal", "Emission Color"):
            for l in list(bsdf.inputs[inp].links):
                m.node_tree.links.remove(l)
        bsdf.inputs["Base Color"].default_value = (*meta["color"], 1)
        if meta.get("emision"):
            bsdf.inputs["Emission Color"].default_value = (*meta["emision"], 1)
        bsdf.inputs["Roughness"].default_value = meta["rugosidad"]
    bpy.ops.export_scene.gltf(filepath=str(ruta), export_format="GLB", export_apply=True,
                              export_lights=True, export_cameras=True, export_animations=True,
                              export_yup=True, export_image_format="WEBP" if max_tex else "AUTO",
                              export_extras=True, export_animation_mode="SCENE", export_bake_animation=False)
    return ruta.stat().st_size


def exportar_pistas(res: dict, ruta: Path) -> dict:
    """Datos de la escena por fotograma para el sonido y la app (no necesitan Blender para leerse).

    camara_activa: [x, y, z, derecha_x, derecha_y] de la cámara de la toma vigente en cada fotograma.
    moviles: {id: [[x, y, z, velocidad_m_s], …]} por fotograma.
    """
    s = res["escena"]
    ctx = res["contexto"]
    cortes = sorted((t["frame_inicio"], t["frame_fin"], t["camara"]) for t in res["tomas"])
    cam_activa = []
    for f in range(s.frame_start, s.frame_end + 1):
        cam = next((c for a, b, c in cortes if a <= f <= b), cortes[-1][2])
        s.frame_set(f)
        mw = cam.matrix_world
        der = mw.to_3x3() @ __import__("mathutils").Vector((1, 0, 0))
        cam_activa.append([round(v, 3) for v in (*mw.translation, der.x, der.y)])
    moviles = {}
    for mid, m in ctx.moviles.items():
        tray = m["tray"]
        f0, f1 = min(tray), max(tray)
        filas = []
        for f in range(s.frame_start, s.frame_end + 1):
            pos, rumbo, v = tray[min(max(f, f0), f1)]
            filas.append([round(pos.x, 3), round(pos.y, 3), round(pos.z, 3), round(v if f0 <= f <= f1 else 0.0, 3)])
        moviles[mid] = filas
    datos = {"fps": s.render.fps, "frames": s.frame_end, "camara_activa": cam_activa, "moviles": moviles,
             "anclas": {k: list(v) for k, v in ctx.anclas.items()},
             "tomas": [{"id": t["spec"]["id"], "frame_inicio": t["frame_inicio"], "frame_fin": t["frame_fin"]}
                       for t in res["tomas"]]}
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos))
    return datos
