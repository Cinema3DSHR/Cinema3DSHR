"""La caminata no salta: la cadera nunca va a más de 3 m/s (Blender, sin render).
Casos que fallaban: ciclos de duración fraccionaria (velocidad ≠ 1) y tramos con fundido (mezcla_s).
Uso: /opt/tools/blendenv/bin/python pruebas/sistema/test_caminata.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import bpy  # noqa: E402
from estudio.blender import director as D  # noqa: E402

A = "mixamo:animaciones/"
ac = [{"clip": A + "trabajo_acciones/Breathing_Idle.fbx", "inicio_s": 0.0, "pos": [0, 0, 0], "mirando_deg": -90},
      {"clip": A + "caminar_correr/Standard_Walk.fbx", "inicio_s": 1.0, "pos": [0, 0, 0], "mirando_deg": -82, "repetir": 2,
       "velocidad": 0.72, "mezcla_s": 0.3},
      {"clip": A + "caminar_correr/Standard_Walk.fbx", "inicio_s": 1.0 + 2 * 35 / 30 / 0.72, "encadenar": True,
       "mirando_deg": -90, "giro_s": 0.6, "repetir": 3, "velocidad": 0.72},
      {"clip": A + "caminar_correr/Stop_Walking.fbx", "inicio_s": 1.0 + 5 * 35 / 30 / 0.72, "encadenar": True,
       "mirando_deg": -90, "mezcla_s": 0.4}]
m = {"tipo": "escena", "id": "caminata-e01", "produccion": "caminata", "numero": 1, "version": 1, "titulo": "c",
     "duracion_s": 13.0, "escenario": {"id": "prueba_minima", "generador": "prueba_minima", "parametros": {}},
     "personajes": [{"id": "chico", "modelo": "humano:chico", "alto_m": 1.8, "acciones": ac}],
     "tomas": [{"id": "t", "tipo": "estatica", "inicio_s": 0, "duracion_s": 13.0, "desde": [3, 3, 2],
                "objetivo": {"ancla": "centro"}}], "render": {"calidad": "hd540", "fps": 30}}
res = D.construir(m, "hd540")
arm = res["personajes"]["chico"]["armadura"]
cad = arm.pose.bones[res["personajes"]["chico"]["info"]["cadera"]]
sc = bpy.context.scene
prev, peor = None, (0, 0)
for f in range(1, 390):
    sc.frame_set(f)
    p = (arm.matrix_world @ cad.head).copy()
    if prev is not None:
        v = (p - prev).length * 30
        peor = max(peor, (v, f))
    prev = p
resultados = [(peor[0] < 3.0, f"velocidad máxima de la cadera {peor[0]:.2f} m/s (cuadro {peor[1]})")]
# el pie apoyado no patina: en cada medio ciclo de la caminata, el pie más lento va a menos de 0,35 m/s
pies = [arm.pose.bones[n] for n in arm.pose.bones.keys() if n.endswith(("LeftToeBase", "RightToeBase"))]
alturas, lentos = [], []
prevp = None
for f in range(45, 255):
    sc.frame_set(f)
    alturas.append((arm.matrix_world @ cad.head).z)
    pp = [(arm.matrix_world @ b.head).copy() for b in pies]
    if prevp is not None:
        lentos.append(min((a - b).length * 30 for a, b in zip(pp, prevp)))
    prevp = pp
peor_apoyo = max(min(lentos[i:i + 20]) for i in range(0, len(lentos) - 20, 20))
resultados.append((peor_apoyo < 0.35, f"pie apoyado: el más lento de cada tramo va a {peor_apoyo:.2f} m/s como mucho"))
vaiven = max(alturas) - min(alturas)
resultados.append((0.02 < vaiven < 0.15, f"la cadera sube y baja al caminar {vaiven * 100:.1f} cm"))
for ok_, txt in resultados:
    print(("OK   " if ok_ else "FALLA"), txt)
n = sum(1 for o, _ in resultados if o)
print(f"\n{n}/{len(resultados)} comprobaciones OK")
sys.exit(0 if n == len(resultados) else 1)
