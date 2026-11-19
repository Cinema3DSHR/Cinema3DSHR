"""Pruebas del AutoFinisher que NO necesitan Blender ni renderizan: receta, manifiesto (identidad, hashes,
inmutabilidad), reparto de cuadros, verificación de cuadros (sin rellenar), verificación de video con un MP4
sintético de ffmpeg, informe del render y los flujos nuevos (no se disparan solos, separan construcción y render).

    python3 pruebas/autofinisher/test_autofinisher.py
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from estudio.autofinisher import informe_render as IR  # noqa: E402
from estudio.autofinisher import manifiesto as MF  # noqa: E402
from estudio.autofinisher import receta as RC  # noqa: E402
from estudio.autofinisher import reparto as RP  # noqa: E402
from estudio.autofinisher import video as VI  # noqa: E402
from estudio.autofinisher import convenciones as CV  # noqa: E402

resultados = []


def caso(nombre, cond, detalle=""):
    resultados.append((nombre, bool(cond)))
    print(("OK    " if cond else "FALLA ") + nombre + (f" — {detalle}" if detalle else ""))


tmp = Path(tempfile.mkdtemp(prefix="af_test_"))

# ---- receta
r = RC.leer(RAIZ / "pruebas/autofinisher/casa_tormenta.receta.json")
caso("receta de la casa válida y completa", r["render"]["muestras"] == 6 and RC.cuadros(r) == 900 and r["render"]["arbol_de_luces"])
mala = dict(r, produccion="Casa Tormenta!")
caso("receta con id inválido → error", any("produccion" in e for e in RC.errores(mala)))
sin_final = json.loads(json.dumps(r)); sin_final["escena"]["cuadro_final"] = None
caso("receta sin cuadro_final → error", any("cuadro_final" in e for e in RC.errores(sin_final)))

# ---- convenciones (nombres de la prueba y estándar)
caso("luces: perfiles por nombre", [CV.perfil_luz(n, t) for n, t in (("Luz_colgante_0", "POINT"), ("Luz_farola_2", "SPOT"),
     ("Luz_neon_cocina", "POINT"), ("Luz_luna", "SUN"), ("Luz_fuego", "POINT"), ("Lampara", "SPOT"))]
     == ["puntual", "farola", "neon", "ambiente", "fuego", "foco"])
caso("luces: cine_tipo manda sobre el nombre", CV.perfil_luz("Luz_x", "POINT", "neon") == "neon")
caso("vacíos FX y vidrios", CV.receta_fx("FX_fuego_hogar") == "fuego" and CV.receta_fx("Mesa") is None
     and CV.es_vidrio("vidrio_verde") and not CV.es_vidrio("madera"))

# ---- manifiesto: identidad, hash, inmutabilidad
blend = tmp / "x.blend"; blend.write_bytes(b"BLENDER-prueba" * 1000)
glb = tmp / "x.glb"; glb.write_bytes(b"glTF" * 500)
m = MF.construir(r, 3, blend, glb, None, {"empaquetados": ["imagen:a"], "externos": []}, {"blender": "5.3.0"}, "0" * 64)
caso("manifiesto: id y release de la versión", m["id"] == "casa_tormenta_v003" and m["release"] == "blend-casa_tormenta-v003")
caso("manifiesto válido", MF.errores(m) == [], MF.errores(m))
ok, mot = MF.verificar_blend(m, blend)
caso("hash del .blend coincide", ok, mot)
blend.write_bytes(b"BLENDER-prueba" * 999 + b"BLENDER-pruebX")
ok, mot = MF.verificar_blend(m, blend)
caso("un byte distinto en el .blend → rechazado", not ok and "SHA-256" in mot, mot)
m2 = dict(m, dependencias={"empaquetadas": [], "externas": ["imagen:textura.png"]})
caso("manifiesto con recursos externos → inválido", any("externos" in e for e in MF.errores(m2)))
m3 = dict(m, id="casa_tormenta_v004")
caso("id que no corresponde a la versión → inválido", any("id o release" in e for e in MF.errores(m3)))

# ---- reparto (el de la prueba: 900 en 60 → 15 por trabajo)
t = RP.repartir(900, 60)
caso("900 cuadros en 60 trabajos: 60 tramos de 15, sin huecos", len(t) == 60 and all(x["cantidad"] == 15 for x in t)
     and t[0]["desde"] == 1 and t[-1]["hasta"] == 900)
t = RP.repartir(901, 60)
caso("901 cuadros: cubre todo sin repetir", sum(x["cantidad"] for x in t) == 901 and len({c for x in t for c in range(x["desde"], x["hasta"] + 1)}) == 901, f"{len(t)} tramos")
t = RP.repartir(10, 60)
caso("más trabajos que cuadros: uno por cuadro", len(t) == 10)
caso("tope de 60 trabajos", len(RP.repartir(5000, 200)) == 60)
lst = RP.parse_lista("12, 40-45,900", 900)
caso("lista de recuperación «12,40-45,900»", lst == [12, 40, 41, 42, 43, 44, 45, 900])
t = RP.repartir_lista(lst, 3)
caso("la lista se reparte entera", sorted(int(c) for x in t for c in x["cuadros"].split(",")) == lst)
try:
    RP.parse_lista("0,901", 900); caso("cuadros fuera de rango → error", False)
except ValueError:
    caso("cuadros fuera de rango → error", True)
caso("comprimir lista", RP.comprimir([1, 2, 3, 7, 9, 10]) == "1-3,7,9-10")

# ---- verificación de cuadros (no rellena)
cdir = tmp / "cuadros"; cdir.mkdir()
for n in range(1, 31):
    if n not in (7, 8, 20):
        (cdir / f"f_{n:04d}.png").write_bytes(b"x")
(cdir / "f_0020.png").write_bytes(b"")             # vacío
v = RP.verificar(cdir, 30)
caso("detecta faltantes y vacíos", v["faltan"] == [7, 8, 20] and v["vacios"] == ["f_0020.png"] and not v["completo"], v["faltan_texto"])
caso("no crea archivos al verificar", not (cdir / "f_0007.png").exists())

# ---- video (MP4 sintético de ffmpeg: no es un render)
if shutil.which("ffmpeg"):
    mp4 = tmp / "prueba.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=540x960:rate=30", "-frames:v", "45",
                    "-pix_fmt", "yuv420p", "-c:v", "libx264", str(mp4)], check=True)
    vv = VI.verificar(mp4, 540, 960, 30, 45)
    caso("video: 45 cuadros, 540x960, 30 fps, 1,5 s", vv["ok"], vv["problemas"])
    vv = VI.verificar(mp4, 540, 960, 30, 46)
    caso("video con un cuadro menos que lo esperado → error", not vv["ok"] and any("cuadros" in p for p in vv["problemas"]))
else:
    caso("ffmpeg disponible para probar el video", False)

# ---- informe del render con datos simulados de la API de GitHub
idir = tmp / "informes"; idir.mkdir()
for i in range(3):
    (idir / f"informe_{i:04d}.json").write_text(json.dumps({"renderizados": 5, "fallos": [], "reintentos": i,
        "por_cuadro": {str(n): {"s": 20.0 + i} for n in range(5)}, "verificar_hash_s": 0.5, "abrir_blend_s": 1.2, "ram_max_mb": 1500 + i}))
jobs = {"jobs": [{"name": f"render ({i})", "conclusion": "success", "created_at": "2026-11-19T10:00:00Z",
                  "started_at": f"2026-11-19T10:00:{10 * i:02d}Z", "completed_at": f"2026-11-19T10:0{2 + i}:00Z"} for i in range(3)]}
(tmp / "jobs.json").write_text(json.dumps(jobs))
inf = IR.armar(idir, 3, 15, {"completo": True}, tmp / "jobs.json")
caso("informe: cuadros, reintentos, RAM y trabajos", inf["cuadros_renderizados"] == 15 and inf["reintentos"] == 3
     and inf["ram_max_mb"] == 1502 and inf["github"]["trabajos_ejecutados"] == 3 and inf["github"]["simultaneos_max"] == 3,
     json.dumps(inf["github"]))

# ---- flujos nuevos (análisis del YAML; no se ejecutan)
wf = RAIZ / ".github" / "workflows"
c = (wf / "construir_produccion.yml").read_text()
rd = (wf / "render_desde_blend.yml").read_text()
trig = lambda t: t.split("\npermissions:")[0]
caso("construir: sólo a mano", not re.search(r"^\s{2}(push|schedule|issues|pull_request|workflow_run):", trig(c), re.M))
caso("render: sólo a mano", not re.search(r"^\s{2}(push|schedule|issues|pull_request|workflow_run):", trig(rd), re.M))
caso("construir: no sobrescribe una Release existente", "ya existe" in c and "gh release view" in c)
cuerpo = rd.split("jobs:")[1]
caso("render: no instala Godot ni ejecuta el armado", "godotengine" not in cuerpo and "godot --" not in cuerpo
     and "armar.py" not in cuerpo and "autofinisher construir" not in cuerpo and "autofinisher.recursos" not in cuerpo)
caso("render: verifica el SHA-256 antes de renderizar", "verificar-blend" in rd)
caso("render: falta un cuadro → se detiene (no rellena)", "verificar-cuadros" in rd and "rellen" not in rd.split("jobs:")[1].replace("NO se rellena", ""))
caso("render: el .blend se baja una vez por trabajo (descarga en el paso del trabajo)", rd.count("gh release download") >= 2)

malos = [n for n, ok in resultados if not ok]
print(f"\n{len(resultados) - len(malos)}/{len(resultados)} comprobaciones OK" + (f" — FALLAN: {malos}" if malos else ""))
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if malos else 0)
