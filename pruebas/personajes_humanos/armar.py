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
             "habla": [{"t": 0, "expr": "neutral"}], "carinosa": [{"t": 0, "expr": "carinosa"}],
             "miedo": [{"t": 0, "expr": "miedo"}], "parpadeo": [{"t": 0, "expr": "neutral"}],
             "triste_fuerte": [{"t": 0, "expr": "triste"}]}
    quienes = [x for x in a[1:] if x in ("chico", "chica")] or ["chico", "chica"]
    pelo = a[a.index("--pelo") + 1] if "--pelo" in a else None
    for q in quienes:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        PJ.reiniciar()
        sc = bpy.context.scene
        sc.frame_start, sc.frame_end = 1, 90
        alto = 1.80 if q == "chico" else 1.66
        cara = {"expresiones": caras[expr], "parpadeo": False}
        if expr == "habla":
            cara["habla"] = [{"inicio_s": 0, "texto": "Hola... ¿me escuchás?", "intensidad": 1.0}]
        spec = {"id": q, "modelo": f"humano:{q}", "alto_m": alto, "acciones": [], "cara": cara}
        if pelo:
            spec["perfil"] = {"pelo_modelo": pelo}
        pj = PJ.crear(spec, 30)
        bpy.context.scene.frame_set(5 if expr == "habla" else 1)
        if expr == "parpadeo":
            for o in bpy.data.objects:
                if o.type == "MESH" and o.data.shape_keys and "BlinkLeft" in o.data.shape_keys.key_blocks:
                    o.data.shape_keys.animation_data_clear()
                    for k in ("BlinkLeft", "BlinkRight"):
                        o.data.shape_keys.key_blocks[k].value = 1.0
        # la expresión de ese cuadro se hornea en la malla (el visor de prueba no aplica pesos por defecto del GLB)
        for o in list(bpy.data.objects):
            if o.type == "MESH" and o.data.shape_keys and o.name.startswith(("CABEZA_", "CEJAS_")):
                mezcla = o.shape_key_add(name="mezcla", from_mix=True)
                co = [0.0] * (len(o.data.vertices) * 3)
                mezcla.data.foreach_get("co", co)
                o.shape_key_clear()
                o.data.vertices.foreach_set("co", co)
        from estudio.blender import previa as PV
        PV._aplanar_materiales()                    # como la previsualización real (colores planos)
        bpy.ops.export_scene.gltf(filepath=str(salida / f"{q}_{expr}{'_' + pelo if pelo else ''}.glb"), export_format="GLB",
                                  export_apply=False, export_animations=False, export_image_format="WEBP")
        print("OK", q, expr)


main()
