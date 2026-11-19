"""ETAPA 9 — Preparación para Cycles (SIN renderizar): los mismos parámetros del estudio para 540p
(config.CALIDADES["hd540"] + director.ajustes_render): 540x960 vertical, 30 fps, 900 cuadros, 6 muestras,
adaptativo 0,05, OIDN, rebotes 6/2/3/4/8, sin cáusticas, AgX Medium High Contrast. Se suman sólo los ajustes de
volumen (fuego y humo) y la imagen de la camioneta empaquetada para que el .blend sea autónomo."""
import bpy


def preparar() -> dict:
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 540, 960, 100
    s.render.fps = 30
    s.frame_start, s.frame_end = 0, 899
    s.render.image_settings.file_format = "JPEG"
    s.render.image_settings.quality = 92
    s.render.use_motion_blur = False
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    c = s.cycles
    c.device = "CPU"
    c.samples = 6
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 6, 2, 3
    c.transmission_bounces, c.transparent_max_bounces = 4, 8
    c.volume_bounces = 0
    c.caustics_reflective = c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    c.volume_step_rate = 2.0          # fuego y humo: pasos más largos (son volúmenes chicos)
    c.volume_max_steps = 256
    s.render.use_persistent_data = True
    s.render.filepath = "//render/f_"
    bpy.ops.file.pack_all()
    return {"motor": "CYCLES", "resolucion": "540x960", "fps": 30, "cuadros": 900, "muestras": 6}
