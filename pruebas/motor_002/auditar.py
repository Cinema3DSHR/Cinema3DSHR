"""AUDITORÍA de sólo lectura de la escena de la mansión y del costo de un fotograma (no modifica nada del estudio)."""
import json, sys, time, collections
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
import bpy
from estudio.blender import director as D
from estudio import manifiesto as MF
m = MF.leer(RAIZ / "producciones/p000_prueba_mansion/escenas/e01/v1/escena.json")
res = D.construir(m, "revision"); s = res["escena"]
dg = bpy.context.evaluated_depsgraph_get()
tris = sum(len(o.evaluated_get(dg).data.polygons) for o in bpy.data.objects if o.type == "MESH" and not o.hide_render)
inst = sum(1 for o in bpy.data.objects if o.instance_type == "COLLECTION")
luces = collections.Counter((o.data.type, o.data.use_shadow) for o in bpy.data.objects if o.type == "LIGHT")
mats = collections.Counter()
for mt in bpy.data.materials:
    if not mt.use_nodes: continue
    for n in mt.node_tree.nodes:
        if n.type in ("TEX_NOISE", "TEX_BRICK", "TEX_VORONOI", "BUMP", "TEX_WHITE_NOISE"): mats[n.type] += 1
        if n.type == "BSDF_PRINCIPLED" and n.inputs["Transmission Weight"].default_value > 0: mats["TRANSMISION"] += 1
        if n.type == "BSDF_PRINCIPLED" and n.inputs["Alpha"].default_value < 1: mats["ALFA"] += 1
dof = [t["spec"]["id"] for t in res["tomas"] if t["camara"].data.dof.use_dof]
# fotogramas con TODO estático (cámara fija y sin objetos animados) -> reutilizables
def firma(f):
    s.frame_set(f); out = []
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action or o.type == "CAMERA":
            out.append((o.name, tuple(round(v, 5) for v in o.matrix_world.translation), tuple(round(v, 4) for v in o.matrix_world.to_euler())))
    return tuple(out)
rep = 0; prev = None
for t in res["tomas"]:
    ult = None
    for f in range(t["frame_inicio"], t["frame_fin"] + 1):
        cam = t["camara"]; s.camera = cam; s.frame_set(f)
        sig = tuple(sorted((o.name, tuple(round(v, 5) for v in o.matrix_world.translation), tuple(round(v, 4) for v in o.matrix_world.to_euler()))
                           for o in bpy.data.objects if (o.animation_data and (o.animation_data.action or True) and o.type != "LIGHT" and o.name.startswith(("CAM_" + t["spec"]["id"], "porton", "auto", "puerta")))))
        rep += (sig == ult); ult = sig
info = {"poligonos_evaluados": tris, "instancias_colecciones": inst, "luces_por_tipo_y_sombra": {f"{k[0]}/sombra={k[1]}": v for k, v in luces.items()},
        "materiales_nodos_costosos": dict(mats), "tomas_con_profundidad_de_campo": dof, "fotogramas": s.frame_end, "fotogramas_identicos_al_anterior": rep,
        "cycles": {"luz_arbol": s.cycles.use_light_tree, "muestras": s.cycles.samples, "min_muestras_adaptativo": s.cycles.adaptive_min_samples,
                   "denoiser": s.cycles.denoiser, "denoise_prefiltro": getattr(s.cycles, "denoising_prefilter", None), "tile": getattr(s.cycles, "tile_size", None) if hasattr(s.cycles, "tile_size") else None,
                   "bvh": getattr(s.cycles, "debug_bvh_type", None), "hilos": s.render.threads},
        "eevee": {k: getattr(s.eevee, k) for k in ("taa_render_samples", "use_raytracing", "fast_gi_method") if hasattr(s.eevee, k)}}
print("AUDIT", json.dumps(info, ensure_ascii=False))
# ---- desglose de un fotograma (toma 4, grúa, el más caro de producción)
t = [x for x in res["tomas"] if x["spec"]["id"] == "t04_grua"][0]; s.camera = t["camara"]; s.frame_set(523)
s.render.resolution_x, s.render.resolution_y = 1280, 720; s.render.image_settings.file_format = "PNG"
def rend(tag, **kw):
    for k, v in kw.items():
        obj, attr = k.split("__"); setattr(s.cycles if obj == "c" else s.render, attr, v)
    s.render.filepath = f"/tmp/claude-0/audit_{tag}.png"; t0 = time.perf_counter(); bpy.ops.render.render(write_still=True)
    return round(time.perf_counter() - t0, 2)
rend("calent", c__samples=1)
out = {"1_muestra_con_denoise": rend("s1", c__samples=1), "10_muestras_con_denoise": rend("s10", c__samples=10)}
out["10_muestras_SIN_denoise"] = rend("s10nd", c__use_denoising=False)
out["1_muestra_SIN_denoise (sólo preparar escena)"] = rend("s1nd", c__samples=1)
s.cycles.use_denoising = True; s.cycles.samples = 10
out["10_muestras_sin_luz_arbol"] = rend("lt", c__use_light_tree=False)
print("DESGLOSE", json.dumps(out, ensure_ascii=False))
