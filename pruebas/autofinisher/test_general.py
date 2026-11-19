"""El AutoFinisher con una escena que NO es la casa (bpy, sin render): arma en Blender una escena mínima con los
nombres del estándar (cámara «Cam_A» entre dos cámaras, «Luz_farola_1», «Luz_neon_bar» animada, material
«vidrio_bar», material emisivo «neon_letrero», vacíos «FX_fuego_tacho» y «FX_humo_chimenea»), la exporta a GLB como lo
haría Godot y la pasa por el AutoFinisher con una receta que pide SÓLO el fuego. Comprueba lo general (perfiles,
vidrios por prefijo, efectos sólo pedidos, informe de vacíos sin receta, empaquetado, manifiesto, validación,
inmutabilidad) y los rechazos (cámara ambigua, vacío pedido que no llegó).

    /opt/tools/blendenv/bin/python pruebas/autofinisher/test_general.py
"""
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import bpy  # noqa: E402

from estudio.autofinisher import construir as CO, manifiesto as MF  # noqa: E402
from estudio.autofinisher.validar import validar  # noqa: E402

resultados = []


def caso(nombre, cond, detalle=""):
    resultados.append((nombre, bool(cond)))
    print(("OK    " if cond else "FALLA ") + nombre + (f" — {detalle}" if detalle else ""), flush=True)


tmp = Path(tempfile.mkdtemp(prefix="af_general_"))
# ---- escena de origen (lo que exportaría Godot)
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.fps = 24
for nombre, pos in (("Cam_A", (0, -8, 2)), ("Cam_B", (5, -5, 3))):
    cd = bpy.data.cameras.new(nombre)
    o = bpy.data.objects.new(nombre, cd)
    s.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (math.radians(80), 0, 0)
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.context.active_object.name = "Piso"
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
vaso = bpy.context.active_object
vaso.name = "Ventana"
mv = bpy.data.materials.new("vidrio_bar")
mv.use_nodes = True
b = mv.node_tree.nodes["Principled BSDF"]
b.inputs["Alpha"].default_value = 0.2
vaso.data.materials.append(mv)
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(2, 0, 1))
letrero = bpy.context.active_object
letrero.name = "Letrero"
me = bpy.data.materials.new("neon_letrero")
me.use_nodes = True
b = me.node_tree.nodes["Principled BSDF"]
b.inputs["Emission Color"].default_value = (1, 0.1, 0.5, 1)
b.inputs["Emission Strength"].default_value = 5.0
letrero.data.materials.append(me)
for nombre, tipo, e, pos in (("Luz_farola_1", "SPOT", 50.0, (3, 3, 4)), ("Luz_neon_bar", "POINT", 10.0, (2, 0, 2))):
    ld = bpy.data.lights.new(nombre, tipo)
    ld.energy = e
    o = bpy.data.objects.new(nombre, ld)
    s.collection.objects.link(o)
    o.location = pos
neon = bpy.data.objects["Luz_neon_bar"].data
for f, e in ((1, 5.0), (12, 20.0), (24, 5.0)):
    neon.energy = e
    neon.keyframe_insert("energy", frame=f)
for nombre, pos in (("FX_fuego_tacho", (-2, 1, 0.2)), ("FX_humo_chimenea", (-2, 1, 1.5))):
    o = bpy.data.objects.new(nombre, None)
    s.collection.objects.link(o)
    o.location = pos
glb = tmp / "escena_general.glb"
bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_lights=True, export_cameras=True,
                          export_animations=True, export_extras=True,
                          export_pointer_animation=True)   # energía animada por KHR_animation_pointer, como Godot
caso("GLB de origen exportado", glb.exists() and glb.stat().st_size > 1000, f"{glb.stat().st_size} bytes")

receta = {
    "formato": "estudio.receta_autofinisher/1", "produccion": "prueba_general", "titulo": "escena mínima de prueba",
    "escena": {"fps": 30, "cuadro_inicial": 1, "cuadro_final": 48, "camara": "Cam_A"},
    "render": {"resolucion": [320, 568], "muestras": 4},
    "luces": {"perfiles": {"farola": {"escala": 100.0}}},
    "mundo": {"color": [0.02, 0.02, 0.03], "fuerza": 0.5},
    "efectos": [{"receta": "fuego", "ancla": "FX_fuego_tacho", "parametros": {"emision": 70.0}}],
}
rp = tmp / "receta.json"
rp.write_text(json.dumps(receta))
r = CO.construir(str(rp), str(glb), 1, str(tmp / "v001"), godot="(sintético)")
m = r["manifiesto"]
inf = json.loads((tmp / "v001" / "informe_preparacion.json").read_text())
res = inf["resultados"]
caso("versión construida con su manifiesto", m["id"] == "prueba_general_v001" and MF.errores(m) == [], m["release"])
luces = res["auto_lights"]["luces"]
caso("perfiles por nombre: farola (escala de la receta) y neón", luces["Luz_farola_1"]["perfil"] == "farola"
     and luces["Luz_farola_1"]["escala"] == 100.0 and luces["Luz_neon_bar"]["perfil"] == "neon", json.dumps(luces)[:200])
caso("claves animadas del neón reescaladas", luces["Luz_neon_bar"]["claves"] >= 3, f"{luces['Luz_neon_bar']['claves']} claves")
caso("vidrio por prefijo con transmisión", any(v.startswith("vidrio_bar") for v in res["auto_materials"]["vidrios"]))
caso("emisivo informado (sin escalar: no se pidió)", any(e.startswith("neon_letrero") for e in res["auto_materials"]["emisivos"])
     and not res["auto_materials"]["emisivos_escalados"])
ef = res["auto_effects"]
caso("sólo el efecto pedido (fuego); el humo queda informado sin receta",
     [a["receta"] for a in ef["aplicados"]] == ["fuego"] and ef["vacios_fx_sin_receta"] == ["FX_humo_chimenea"])
caso("rango, fps y cámara de la receta", res["auto_import"]["rango"] == [1, 48] and res["auto_import"]["fps"] == 30
     and res["auto_import"]["camara"] == "Cam_A")
caso("autónomo, con tiempos y RAM por etapa", res["auto_pack"]["autonomo"] and all("segundos" in e and "ram_max_mb" in e
     for e in inf["etapas"].values()), f"{len(inf['etapas'])} etapas, RAM máx {inf['ram_max_mb']} MB")
v = validar(str(tmp / "v001" / "prueba_general_v001.blend"), str(tmp / "v001" / "manifest.json"))
caso("validación del .blend contra su manifiesto", v["ok"], v["problemas"])
try:
    CO.construir(str(rp), str(glb), 1, str(tmp / "v001"))
    caso("la misma versión no se sobrescribe", False)
except FileExistsError:
    caso("la misma versión no se sobrescribe", True)
mala = dict(receta, escena={**receta["escena"], "camara": None})
rp.write_text(json.dumps(mala))
try:
    CO.construir(str(rp), str(glb), 2, str(tmp / "v002"))
    caso("dos cámaras sin decir cuál → se detiene", False)
except ValueError as e:
    caso("dos cámaras sin decir cuál → se detiene", "cámaras" in str(e) and not (tmp / "v002").exists(), str(e)[:90])
mala = dict(receta, efectos=[{"receta": "fuego", "ancla": "FX_fuego_que_no_existe"}])
rp.write_text(json.dumps(mala))
try:
    CO.construir(str(rp), str(glb), 3, str(tmp / "v003"))
    caso("vacío pedido que no llegó → se detiene sin dejar la versión", False)
except KeyError as e:
    caso("vacío pedido que no llegó → se detiene sin dejar la versión", not (tmp / "v003").exists()
         and (tmp / "v003_ERROR.json").exists(), str(e)[:90])

malos = [n for n, ok in resultados if not ok]
print(f"\n{len(resultados) - len(malos)}/{len(resultados)} comprobaciones OK" + (f" — FALLAN: {malos}" if malos else ""))
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if malos else 0)
