"""AutoCinema (bpy): configura Cycles con la calidad de la receta (por defecto, la del estudio: 6 muestras, adaptativo
0,05, OIDN, rebotes 6/2/3/4/8, árbol de luces, AgX). No renderiza."""
from __future__ import annotations

import bpy


def preparar(receta: dict) -> dict:
    s = bpy.context.scene
    es, rd = receta["escena"], receta["render"]
    s.render.engine = rd["motor"]
    s.render.resolution_x, s.render.resolution_y = rd["resolucion"]
    s.render.resolution_percentage = 100
    s.render.fps, s.render.fps_base = es["fps"], 1.0
    s.frame_start, s.frame_end = es["cuadro_inicial"], es["cuadro_final"]
    s.render.image_settings.file_format = rd["formato_cuadros"]
    if rd["formato_cuadros"] == "PNG":
        s.render.image_settings.color_mode = "RGB"
    s.render.use_motion_blur = bool(rd["desenfoque_movimiento"])
    s.view_settings.view_transform = rd["color"]["transformacion"]
    s.view_settings.look = rd["color"]["aspecto"]
    c = s.cycles
    c.device = rd["dispositivo"]
    c.samples = rd["muestras"]
    c.use_adaptive_sampling = rd["muestreo_adaptativo"] is not None
    if rd["muestreo_adaptativo"] is not None:
        c.adaptive_threshold = rd["muestreo_adaptativo"]
    c.use_denoising = bool(rd["denoiser"])
    if rd["denoiser"]:
        c.denoiser = rd["denoiser"]
        c.denoising_input_passes = rd["pases_denoiser"]
    rb = rd["rebotes"]
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces = rb["total"], rb["difusos"], rb["brillantes"]
    c.transmission_bounces, c.transparent_max_bounces, c.volume_bounces = rb["transmision"], rb["transparencia"], rb["volumen"]
    c.caustics_reflective = c.caustics_refractive = bool(rd["causticas"])
    c.sample_clamp_indirect = rd["limite_indirecto"]
    if hasattr(c, "use_light_tree"):
        c.use_light_tree = bool(rd["arbol_de_luces"])
    c.volume_step_rate = rd["volumen"]["paso"]
    c.volume_max_steps = rd["volumen"]["pasos_max"]
    s.render.use_persistent_data = bool(rd["datos_persistentes"])
    s.render.filepath = "//render/f_"
    return {"motor": s.render.engine, "dispositivo": c.device, "resolucion": [s.render.resolution_x, s.render.resolution_y],
            "fps": s.render.fps, "cuadros": [s.frame_start, s.frame_end], "muestras": c.samples,
            "adaptativo": c.adaptive_threshold if c.use_adaptive_sampling else None, "denoiser": c.denoiser if c.use_denoising else None,
            "rebotes": [c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces, c.volume_bounces],
            "arbol_de_luces": getattr(c, "use_light_tree", None), "color": [s.view_settings.view_transform, s.view_settings.look]}
