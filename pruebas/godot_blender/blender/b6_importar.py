"""ETAPA 6 — Importación del GLB de Godot (automática). Pone 30 fps ANTES de importar: el importador convierte los
segundos de la animación con los fps de la escena (con los 24 de fábrica la toma quedaba en 720 cuadros)."""
import bpy

FPS = 30
CUADROS = 900          # 30 s


def importar(glb: str) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = FPS
    s.render.fps_base = 1.0
    bpy.ops.import_scene.gltf(filepath=glb)
    s.frame_start, s.frame_end = 0, CUADROS - 1
    cam = bpy.data.objects["Camara"]
    s.camera = cam
    acc = bpy.data.actions["toma"]
    return {"fps": s.render.fps, "rango_accion": list(acc.frame_range), "objetos": len(bpy.data.objects)}
