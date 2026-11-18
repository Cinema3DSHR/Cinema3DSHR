"""Prueba de integración de la escena de trabajo (Blender, SIN render) con el escenario mínimo de prueba.
Uso: /opt/tools/blendenv/bin/python pruebas/sistema/test_trabajo.py

1. arma la escena de trabajo A y marca un «testigo» en el escenario y en el personaje;
2. cambia UNA cámara → actualizar rehace sólo esa cámara (los testigos siguen: escenario y personaje intactos) y
   sus claves son iguales a las de una escena B armada de cero;
3. cambia un clip del personaje → se rehacen el personaje, lo de «después» y las cámaras que lo siguen; el
   escenario sigue intacto; caderas y cámaras iguales a una escena C armada de cero;
4. exporta la previsualización desde la escena de trabajo y comprueba que el .blend no cambió.
"""
import copy
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
TMP = Path(tempfile.mkdtemp(prefix="cine_trabajo_"))
os.environ["CINE_TRABAJO"] = str(TMP / "trabajo")

import bpy  # noqa: E402
from estudio import componentes as CO  # noqa: E402
from estudio import manifiesto as MF  # noqa: E402
from estudio.blender import director as D  # noqa: E402
from estudio.blender import trabajo as T  # noqa: E402

ok = fallas = 0


def prueba(nombre, cond, detalle=""):
    global ok, fallas
    ok, fallas = (ok + 1, fallas) if cond else (ok, fallas + 1)
    print(("OK   " if cond else "FALLA"), nombre, "" if cond else detalle, flush=True)


SENT = "mixamo:animaciones/sentado_manejar/"
CAM = "mixamo:animaciones/caminar_correr/"
A = {
    "tipo": "escena", "id": "prueba_sistema-e01", "produccion": "prueba_sistema", "numero": 1, "version": 1,
    "titulo": "prueba", "duracion_s": 6.0, "huella_v": 2,
    "escenario": {"id": "prueba_minima", "generador": "prueba_minima",
                  "parametros": {"objeto_mano": {"personaje": "chico"}}},
    "eventos": [{"accion": "titilar", "inicio_s": 1.0}],
    "personajes": [{"id": "chico", "modelo": "humano:chico", "alto_m": 1.8, "acciones": [
        {"clip": CAM + "Standard_Walk.fbx", "inicio_s": 0.0, "pos": [0, 0, 0], "mirando_deg": 90, "repetir": 2},
        {"clip": CAM + "Walk_To_Stop.fbx", "inicio_s": 2.3, "encadenar": True, "mirando_deg": 90}]}],
    "tomas": [
        {"id": "t01", "tipo": "estatica", "inicio_s": 0, "duracion_s": 2.0, "desde": [3, -3, 1.6],
         "objetivo": {"ancla": "centro"}, "lente_mm": 30},
        {"id": "t02", "tipo": "seguimiento", "inicio_s": 2.0, "duracion_s": 2.0, "movil": "chico",
         "desp_local": [0.3, 2.0, 0.6], "objetivo": {"movil": "chico", "punto": "cabeza"}, "lente_mm": 35},
        {"id": "t03", "tipo": "dolly", "inicio_s": 4.0, "duracion_s": 2.0, "desde": [-2, 4, 1.5], "hasta": [-1.5, 3.5, 1.5],
         "objetivo": {"ancla": "caja"}, "lente_mm": 28}],
    "render": {"calidad": "hd540", "fps": 30, "vertical": True},
}


def claves_camaras(tomas, frames=(1, 15, 31, 45, 61, 75, 91, 105, 120)):
    sc = bpy.context.scene
    out = {}
    for t in tomas:
        cam = t["camara"]
        out[t["spec"]["id"]] = []
        for f in frames:
            if t["frame_inicio"] <= f <= t["frame_fin"]:
                sc.frame_set(f)
                out[t["spec"]["id"]].append([round(x, 4) for row in cam.matrix_world for x in row] + [round(cam.data.lens, 3)])
    return out


def caderas(pjs, frames=(1, 30, 60, 90, 120, 150, 180)):
    sc = bpy.context.scene
    out = {}
    for pid, pj in pjs.items():
        arm = pj["armadura"]
        out[pid] = []
        for f in frames:
            sc.frame_set(f)
            h = arm.matrix_world @ arm.pose.bones[pj["info"]["cadera"]].head
            out[pid].append([round(v, 4) for v in h])
    return out


def iguales(a, b, tol=2e-3):
    if a.keys() != b.keys():
        return False
    for k in a:
        if len(a[k]) != len(b[k]):
            return False
        for x, y in zip(a[k], b[k]):
            if any(abs(p - q) > tol for p, q in zip(x, y)):
                return False
    return True


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def desde_cero(m):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    res = D.construir(m, "hd540")
    return claves_camaras(res["tomas"]), caderas(res["personajes"])


# 1) escena de trabajo A
bpy.ops.wm.read_factory_settings(use_empty=True)
t0 = time.time()
res = T.construir(A, "pruebas/sistema/receta_A.json")
t_completa = time.time() - t0
d = T.carpeta(A)
prueba("escena de trabajo guardada", (d / "escena.blend").exists() and (d / "estado.json").exists())
est = json.loads((d / "estado.json").read_text())
prueba("objetos etiquetados por componente", {"escenario", "personaje:chico", "despues", "camara:t01"} <= set(est["objetos"]),
       list(est["objetos"]))
bpy.data.objects["caja"]["testigo"] = "intacto"
res["personajes"]["chico"]["armadura"]["testigo"] = "intacto"
bpy.ops.wm.save_mainfile(filepath=str(d / "escena.blend"))

# 2) cambia una cámara
B = copy.deepcopy(A)
B["tomas"][0]["desde"] = [2.5, -3.5, 1.8]
B["tomas"][0]["lente_mm"] = 40
prueba("plan: sólo camara:t01", T.plan(B)["afectados"] == ["camara:t01"], T.plan(B))
t0 = time.time()
r = T.actualizar(B)
t_cam = time.time() - t0
prueba("actualizar rehizo sólo camara:t01", r["rehecho"] == ["camara:t01"] and not r["completa"], r.get("rehecho"))
prueba("escenario intacto (testigo)", bpy.data.objects["caja"].get("testigo") == "intacto")
arm = r["res"]["personajes"]["chico"]["armadura"]
prueba("personaje intacto (testigo)", arm.get("testigo") == "intacto")
cams_inc = claves_camaras(r["res"]["tomas"])
cams_b, _ = desde_cero(B)
prueba("cámaras iguales a la escena B armada de cero", iguales(cams_inc, cams_b))
prueba(f"más rápido que armar todo ({t_cam:.1f} s contra {t_completa:.1f} s)", t_cam < t_completa)

# 3) cambia un clip del personaje
Cr = copy.deepcopy(B)
Cr["personajes"][0]["acciones"][0]["clip"] = CAM + "Walking.fbx"
Cr["personajes"][0]["acciones"][0]["repetir"] = 1
pl = T.plan(Cr)
prueba("plan: personaje + después + cámara que lo sigue; no el escenario",
       set(pl["afectados"]) == {"personaje:chico", "despues", "camara:t02"} and not pl["completa"], pl)
t0 = time.time()
r = T.actualizar(Cr)
t_pj = time.time() - t0
prueba("escenario intacto tras rehacer el personaje (testigo)", bpy.data.objects["caja"].get("testigo") == "intacto")
prueba("el personaje sí se rehízo", r["res"]["personajes"]["chico"]["armadura"].get("testigo") is None)
prueba("el objeto de la mano se volvió a poner", bpy.data.objects.get("objeto_mano") is not None
       and bpy.data.objects["objeto_mano"].parent is not None)
cams_inc, cad_inc = claves_camaras(r["res"]["tomas"]), caderas(r["res"]["personajes"])
cams_c, cad_c = desde_cero(Cr)
prueba("caderas iguales a la escena C armada de cero", iguales(cad_inc, cad_c), (cad_inc, cad_c))
prueba("cámaras iguales a la escena C armada de cero", iguales(cams_inc, cams_c))
print(f"tiempos: completa {t_completa:.1f} s · una cámara {t_cam:.1f} s · un personaje {t_pj:.1f} s", flush=True)

# 3b) versión nueva (como una corrección del visor): hereda la escena de trabajo de v1 y rehace sólo la cámara
sha_v1 = sha(d / "escena.blend")
V2 = copy.deepcopy(Cr)
V2["version"] = 2
V2["tomas"][2]["lente_mm"] = 50
prueba("v2 sin escena propia: hereda la de v1 y el plan es sólo camara:t03", T.plan(V2)["afectados"] == ["camara:t03"],
       T.plan(V2))
r2 = T.actualizar(V2)
prueba("v2 actualizada rehaciendo sólo camara:t03", r2["rehecho"] == ["camara:t03"], r2.get("rehecho"))
prueba("la escena de trabajo de v1 no cambió", sha(d / "escena.blend") == sha_v1)
Cr = V2
d = T.carpeta(V2)

# 4) previsualización desde la escena de trabajo: el .blend no cambia
antes = sha(d / "escena.blend")
tam = T.exportar_previa(Cr, TMP / "previa")
prueba("previsualización exportada", (TMP / "previa" / f"e01_v{Cr['version']}_previa.glb").exists(), tam)
prueba("la escena de trabajo no cambió al exportar", sha(d / "escena.blend") == antes)
print(f"\n{ok}/{ok + fallas} comprobaciones OK   (carpeta temporal {TMP})")
sys.exit(1 if fallas else 0)
