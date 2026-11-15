"""PRUEBA DE IDA Y VUELTA (parte Blender): aplica cada captura del editor a una cámara de Blender con
`camara_director.aplicar` y compara el encuadre con el de Godot proyectando los mismos puntos a 1280×720.
Para las cámaras de rodaje, compara además contra la cámara ORIGINAL de la escena (matriz de control).
Uso: python ida_vuelta_blender.py CAPTURAS.json PREVIA.json INFORME.json"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
from estudio.blender import camara_director as CD

cap = json.loads(Path(sys.argv[1]).read_text())
prev = json.loads(Path(sys.argv[2]).read_text())
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 720, 100
cd = bpy.data.cameras.new("dir")
cam = bpy.data.objects.new("dir", cd)
s.collection.objects.link(cam)
s.camera = cam
lentes = {t["camara"]: t["lente_mm"] for t in prev["tomas"]}
pts = [Vector(p) for p in cap["puntos_blender"]]
filas, peor_px, peor_ang, peor_pos, peor_lente = [], 0.0, 0.0, 0.0, 0.0
for c in cap["casos"]:
    CD.aplicar(cam, c["captura"])
    bpy.context.view_layer.update()
    errs = []
    for p, g in zip(pts, c["px_godot"]):
        v = world_to_camera_view(s, cam, p)
        if g is None or v.z <= 0:
            continue
        bx, by = v.x * 1280, (1 - v.y) * 720
        if -200 < bx < 1480 and -200 < by < 920:       # sólo puntos cerca del cuadro
            errs.append(math.hypot(bx - g[0], by - g[1]))
    # Euler de la captura == cuaternión (los dos campos describen la misma orientación)
    ro = c["captura"]["rotation"]
    from mathutils import Euler, Quaternion
    me = Euler([math.radians(ro[k]) for k in "xyz"], "XYZ").to_matrix()
    mq = Quaternion(c["captura"]["quaternion"]).to_matrix()
    d_euler = math.degrees((me.to_quaternion().rotation_difference(mq.to_quaternion())).angle)
    fila = {"caso": c["nombre"], "tipo": c["tipo"], "puntos": len(errs), "error_px_max": round(max(errs), 4) if errs else None,
            "error_px_medio": round(sum(errs) / len(errs), 4) if errs else None, "euler_vs_cuaternion_deg": round(d_euler, 6),
            "lente_mm": c["captura"]["lens_mm"]}
    if c["tipo"] == "toma":
        orig = Matrix(prev["control"]["camaras"][c["nombre"]]["matriz"])
        mw = cam.matrix_world
        fila["error_pos_m"] = round((orig.translation - mw.translation).length, 6)
        fila["error_ang_deg"] = round(math.degrees(orig.to_quaternion().rotation_difference(mw.to_quaternion()).angle), 5)
        fila["lente_original_mm"] = lentes[c["nombre"]]
        fila["error_lente_mm"] = round(abs(lentes[c["nombre"]] - c["captura"]["lens_mm"]), 5)
        peor_pos, peor_ang = max(peor_pos, fila["error_pos_m"]), max(peor_ang, fila["error_ang_deg"])
        peor_lente = max(peor_lente, fila["error_lente_mm"])
    if errs:
        peor_px = max(peor_px, max(errs))
    filas.append(fila)
cad = cap.get("caderas", {})
inf = {"casos": len(filas), "error_px_max": round(peor_px, 4), "caderas_muestras": cad.get("muestras"),
       "caderas_error_max_m": round(cad.get("error_max_m", 9), 5), "tomas_error_pos_max_m": peor_pos,
       "tomas_error_ang_max_deg": peor_ang, "tomas_error_lente_max_mm": peor_lente,
       "aprobada": peor_px < 1.0 and peor_ang < 0.05 and peor_pos < 0.005 and peor_lente < 0.05 and cad.get("error_max_m", 9) < 0.01, "detalle": filas}
Path(sys.argv[3]).write_text(json.dumps(inf, indent=1, ensure_ascii=False))
print("RESULTADO", json.dumps({k: v for k, v in inf.items() if k != "detalle"}))
