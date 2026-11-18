"""Arma los dos personajes de «Un sueño de a dos» SIN escena y exporta un GLB por personaje para el visor
(xvfb-run godot … vista.gd). No renderiza nada.
Uso: python pruebas/personajes_humanos/armar.py SALIDA_DIR [chico|chica …] [--expresion nombre]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import bpy
from estudio.blender import personajes as PJ, humanos as HU

def main():
    a = sys.argv[1:]
    salida = Path(a[0]); salida.mkdir(parents=True, exist_ok=True)
    expr = a[a.index("--expresion") + 1] if "--expresion" in a else "neutral"
    caras = {"neutral": [{"t": 0, "expr": "neutral"}], "sonrisa": [{"t": 0, "expr": "sonrisa"}],
             "triste": [{"t": 0, "expr": "preocupada"}], "sorpresa": [{"t": 0, "expr": "sorpresa"}],
             "habla": [{"t": 0, "expr": "neutral"}], "carinosa": [{"t": 0, "expr": "carinosa"}]}
    quienes = [x for x in a[1:] if x in ("chico", "chica")] or ["chico", "chica"]
    for q in quienes:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        PJ.reiniciar()
        sc = bpy.context.scene
        sc.frame_start, sc.frame_end = 1, 90
        alto = 1.78 if q == "chico" else 1.65
        cara = {"expresiones": caras[expr], "parpadeo": False}
        if expr == "habla":
            cara["habla"] = [{"inicio_s": 0, "texto": "Amor, mirá lo que te traje", "intensidad": 1.0}]
        pj = PJ.crear({"id": q, "modelo": f"humano:{q}", "alto_m": alto, "acciones": [], "cara": cara}, 30)
        bpy.context.scene.frame_set(4 if expr == "habla" else 1)
        for o in bpy.data.objects:                  # el GLB lleva el valor del cuadro como peso por defecto
            if o.type == "MESH" and o.data.shape_keys and o.data.shape_keys.animation_data:
                for kb in o.data.shape_keys.key_blocks[1:]:
                    v = kb.value
                    o.data.shape_keys.animation_data_clear()
                    break
        from estudio.blender import previa as PV
        PV._aplanar_materiales()                    # como la previsualización real (colores planos)
        bpy.ops.export_scene.gltf(filepath=str(salida / f"{q}_{expr}.glb"), export_format="GLB",
                                  export_apply=False, export_animations=False, export_image_format="WEBP")
        print("OK", q, expr)


main()
