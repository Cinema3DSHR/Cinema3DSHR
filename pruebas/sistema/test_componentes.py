"""Pruebas del sistema de componentes, protección y recursos (sin Blender, sin render).
Uso: python pruebas/sistema/test_componentes.py"""
import copy
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from estudio import componentes as CO, config, manifiesto as MF, proteccion as PR, recursos as R  # noqa: E402

ok = fallas = 0


def prueba(nombre, cond, detalle=""):
    global ok, fallas
    if cond:
        ok += 1
        print("OK   ", nombre)
    else:
        fallas += 1
        print("FALLA", nombre, detalle)


recetas = sorted(RAIZ.glob("producciones/*/escenas/*/v*/escena.json"))
# 1) todas las recetas: dependencias legibles (el planificador de Actions las lee sin importar módulos) y componentes
malas = []
for r in recetas:
    try:
        m = MF.leer(r)
        if m.get("tipo") != "escena" and "escenario" not in m:
            continue
        MF.dependencias(m)
        CO.componentes(m)
    except Exception as e:  # noqa: BLE001
        malas.append(f"{r.relative_to(RAIZ)}: {e}")
prueba(f"{len(recetas)} recetas: dependencias y componentes", not malas, "\n".join(malas[:5]))

E02 = RAIZ / "producciones/p011_a_la_deriva/escenas/e02/v1/escena.json"
m = MF.leer(E02)
base = {k: v["huella"] for k, v in CO.componentes(m).items()}
prueba("componentes estables (dos cálculos iguales)", base == {k: v["huella"] for k, v in CO.componentes(m).items()})
# 2) detección de cambios
m2 = copy.deepcopy(m); m2["tomas"][9]["lente_mm"] = 45
d = CO.afectados(base, CO.componentes(m2))
prueba("cambiar una lente → sólo esa cámara", d["afectados"] == ["camara:t10_flores"] and not d["completa"], d)
m3 = copy.deepcopy(m); m3["personajes"][0]["acciones"][6]["clip"] = "mixamo:animaciones/caminar_correr/Standard_Walk.fbx"
d = CO.afectados(base, CO.componentes(m3))
prueba("cambiar un clip de Aiden → Aiden + utilería + sus cámaras; Kate y escenario no",
       "personaje:aiden" in d["afectados"] and "personaje:kate" not in d["afectados"] and "escenario" not in d["afectados"]
       and not d["completa"], d)
m4 = copy.deepcopy(m); m4["escenario"]["parametros"]["semilla_flores"] = 99
prueba("cambiar el escenario → reconstrucción completa", CO.afectados(base, CO.componentes(m4))["completa"])
m5 = copy.deepcopy(m); m5["render"]["muestras"] = 8
prueba("cambiar el render → sólo render", CO.afectados(base, CO.componentes(m5))["afectados"] == ["render"])
m6 = copy.deepcopy(m); m6["duracion_s"] = 140
prueba("cambiar la duración → completa", CO.afectados(base, CO.componentes(m6))["completa"])
# 3) rutas: las absolutas viejas se resuelven en la raíz
p = config.ruta_recurso("/home/otra_maquina/Cinema3DSHR/audio/biblioteca/x.mp3")
prueba("ruta absoluta vieja → relativa a la raíz", p == config.RAIZ_RECETAS / "audio/biblioteca/x.mp3", p)
prueba("ruta relativa → raíz", config.ruta_recurso("audio/x.mp3") == config.RAIZ_RECETAS / "audio/x.mp3")
# 4) recursos: E02 completo; una receta rota se detiene (no se inventa nada)
er, _ = R.verificar(m)
prueba("E02 v1: recursos completos", not er, er[:3])
mr = copy.deepcopy(m); mr["personajes"][0]["cara"]["habla"][0]["audio"] = "audio/biblioteca/no_existe.mp3"
try:
    R.exigir(mr)
    prueba("audio faltante detiene la preparación", False)
except R.RecursoFaltante as e:
    prueba("audio faltante detiene la preparación", "no_existe.mp3" in str(e))
# 5) protección: la receta entregada no se sobrescribe; una copia sí
try:
    MF.escribir(E02, m)
    prueba("escribir sobre E02 v1 entregada → prohibido", False)
except PermissionError:
    prueba("escribir sobre E02 v1 entregada → prohibido", True)
prueba("E02 v1 intacta (huellas de la entrega)", not [x for x in PR.verificar(E02) if not x.startswith("no disponible")],
       PR.verificar(E02))
with tempfile.TemporaryDirectory() as td:
    copia = Path(td) / "escena.json"
    MF.escribir(copia, m)
    prueba("una copia de trabajo sí se escribe", copia.exists())
# 6) clips: la descripción manda (Walking_2 es un borracho)
from estudio import clips as CL  # noqa: E402
av = CL.avisos_receta(m)
prueba("E02 v1: avisa la caminata de borracho y el freno «llevando a alguien»",
       any("Walking_2" in x for x in av) and any("Walk_To_Stop" in x for x in av), av)
neutros = [c["ref"] for c in CL.buscar("standard walk", "caminar", sin_estilo=True)]
prueba("buscar caminatas neutras encuentra Standard_Walk y no a los borrachos",
       "mixamo:animaciones/caminar_correr/Standard_Walk.fbx" in neutros and not any("Walking_2.fbx" in r for r in neutros))
print(f"\n{ok}/{ok + fallas} comprobaciones OK")
sys.exit(1 if fallas else 0)
