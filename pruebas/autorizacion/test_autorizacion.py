"""Pruebas de aceptación de la REGLA de revisión 3D y autorización de render (docs/REVISION_Y_AUTORIZACION.md).

NO renderiza nada. Usa registros (Issues) simulados con el mismo formato que crea la app y comprueba:
estados de revisión, invalidación por correcciones y por cambios de la escena, rechazo sin autorización, aceptación
con autorización válida y la misma configuración, que nadie fuera de las cuentas autorizadas cuente, que los comandos
y scripts que renderizan se niegan sin registros, y que ningún flujo de GitHub renderiza sin verificar.

    python3 pruebas/autorizacion/test_autorizacion.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.chdir(RAIZ)
from estudio import autorizacion as AUT  # noqa: E402
from estudio import manifiesto as MF  # noqa: E402

ESCENA = "producciones/p009_duo_cero/escenas/e01/v1/escena.json"
M = MF.leer(ESCENA)
H = MF.huella(M)
P, E, V = "p009_duo_cero", "e01", 1
CFG = {"resolucion": "960x540", "fps": 30, "muestras": 6, "motor": "CYCLES", "dispositivo": "CPU"}
DUENO = "webmaletin-art"
_n = [0]


def issue(clase, datos, autor=DUENO, minuto=0):
    _n[0] += 1
    pref = {"revision": "[REVISIÓN]", "direccion": "[DIRECCIÓN]", "autorizacion": "[AUTORIZACIÓN]"}[clase]
    d = {"produccion": P, "escena": E, "version": V, **datos}
    return {"number": _n[0], "title": f"{pref} {P} · {E} v{V} · {datos.get('decision', datos.get('tipo', 'RENDER FINAL'))}",
            "body": "x\n\n```json\n" + json.dumps(d) + "\n```", "user": {"login": autor},
            "created_at": f"2026-11-17T13:{minuto:02d}:00Z", "state": "closed"}


def estado(issues, previa=True):
    return AUT.estado(P, E, V, H, AUT.eventos(issues), previa=previa)


resultados = []


def caso(nombre, cond, detalle=""):
    resultados.append((nombre, bool(cond)))
    print(("OK    " if cond else "FALLA ") + nombre + (f" — {detalle}" if detalle else ""))


aprobar = issue("revision", {"decision": "APROBAR", "huella": H}, minuto=10)
autorizar = issue("autorizacion", {"huella": H, "config": CFG}, minuto=20)

# ---- 1. estados de revisión
caso("1a sin previsualización publicada → EN PREPARACIÓN", estado([], previa=False) == "EN PREPARACIÓN")
caso("1b previsualización publicada, sin revisar → LISTA PARA REVISIÓN", estado([]) == "LISTA PARA REVISIÓN")
nota = issue("direccion", {"tipo": "nota", "huella": H, "texto": "ver el cuadro 120"}, minuto=5)
caso("1c el dueño la está revisando (notas/marcadores) → EN REVISIÓN", estado([nota]) == "EN REVISIÓN")
corr = issue("revision", {"decision": "CORREGIR", "huella": H, "nota": "bajar la cámara"}, minuto=6)
caso("5  enviar correcciones → CORRECCIONES SOLICITADAS", estado([nota, corr]) == "CORRECCIONES SOLICITADAS")
caso("1d aprobada con la huella actual → APROBADA POR EL USUARIO", estado([nota, aprobar]) == "APROBADA POR EL USUARIO")
caso("1e aprobada + autorizada → RENDER AUTORIZADO", estado([aprobar, autorizar]) == "RENDER AUTORIZADO")
ev = AUT.eventos([aprobar, autorizar])
caso("1f render corriendo → RENDER EN EJECUCIÓN",
     AUT.estado(P, E, V, H, ev, previa=True, render="ejecutando") == "RENDER EN EJECUCIÓN")
caso("1g render final publicado → FINALIZADA", AUT.estado(P, E, V, H, ev, previa=True, render="finalizado") == "FINALIZADA")

# ---- 6. una corrección o un cambio invalidan la aprobación
corr_despues = issue("revision", {"decision": "CORREGIR", "huella": H, "nota": "otra cosa"}, minuto=30)
caso("6a corrección después de aprobar → la aprobación deja de valer",
     estado([aprobar, autorizar, corr_despues]) == "CORRECCIONES SOLICITADAS")
ok, motivo, _ = AUT.verificar(M, [aprobar, autorizar, corr_despues], CFG)
caso("6b …y el render queda BLOQUEADO", not ok and "correcciones" in motivo, motivo)
aprob_vieja = issue("revision", {"decision": "APROBAR", "huella": "huella_de_otra_version"}, minuto=10)
aut_vieja = issue("autorizacion", {"huella": "huella_de_otra_version", "config": CFG}, minuto=20)
ok, motivo, _ = AUT.verificar(M, [aprob_vieja, aut_vieja], CFG)
caso("6c escena modificada (otra huella) → la aprobación anterior no sirve", not ok and "otra huella" in motivo, motivo)
caso("6d con otra huella el estado vuelve a LISTA PARA REVISIÓN", estado([aprob_vieja, aut_vieja]) == "LISTA PARA REVISIÓN")

# ---- 7. render sin autorización
ok, motivo, _ = AUT.verificar(M, [], CFG)
caso("7a sin aprobación ni autorización → BLOQUEADO", not ok, motivo)
ok, motivo, _ = AUT.verificar(M, [aprobar], CFG)
caso("7b aprobada pero sin AUTORIZAR RENDER FINAL → BLOQUEADO", not ok and "AUTORIZAR" in motivo, motivo)
aut_antes = issue("autorizacion", {"huella": H, "config": CFG}, minuto=1)
ok, motivo, _ = AUT.verificar(M, [aut_antes, aprobar], CFG)
caso("7c autorización anterior a la aprobación → BLOQUEADO", not ok, motivo)
ok, motivo, _ = AUT.verificar(M, [aprobar, autorizar], {**CFG, "resolucion": "1280x720"})
caso("7d otra configuración que la autorizada → BLOQUEADO", not ok and "configuración" in motivo, motivo)
intruso_ap = issue("revision", {"decision": "APROBAR", "huella": H}, autor="otra-persona", minuto=10)
intruso_aut = issue("autorizacion", {"huella": H, "config": CFG}, autor="otra-persona", minuto=20)
ok, motivo, _ = AUT.verificar(M, [intruso_ap, intruso_aut], CFG)
caso("10a registros de una cuenta no autorizada no cuentan → BLOQUEADO", not ok, motivo)

# ---- 8/9. autorización válida
ok, motivo, aut = AUT.verificar(M, [nota, aprobar, autorizar], CFG)
caso("8  aprobada + autorizada con la misma configuración → se puede iniciar", ok, motivo)
caso("9  la autorización queda vinculada a la versión exacta (n.º, fecha, cuenta, huella, configuración)",
     ok and aut["issue"] == autorizar["number"] and aut["huella"] == H and aut["version"] == V
     and aut["autor"] == DUENO and aut["config"] == CFG and aut["fecha"].startswith("2026-11-17"))

# ---- 10. los comandos y scripts que renderizan se niegan sin registros (sin llegar a Blender)
env = {k: v for k, v in os.environ.items() if k != "CINE_ISSUES"}
for nombre, cmd in [
        ("python -m estudio render", [sys.executable, "-m", "estudio", "render", ESCENA, "--toma", "t01_aerea"]),
        ("python -m estudio fijas", [sys.executable, "-m", "estudio", "fijas", ESCENA])]:
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
    caso(f"10b {nombre} sin autorización → rechazado", r.returncode != 0 and "RENDER BLOQUEADO" in (r.stderr + r.stdout),
         (r.stderr + r.stdout).strip().splitlines()[-1][:140] if (r.stderr + r.stdout).strip() else "")
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump([aprobar], f)
r = subprocess.run([sys.executable, "-m", "estudio", "fijas", ESCENA, "--calidad", "previa"], capture_output=True, text=True,
                   env={**env, "CINE_ISSUES": f.name}, timeout=120)
caso("10c fijas con aprobación pero sin autorización → rechazado", r.returncode != 0 and "RENDER BLOQUEADO" in (r.stderr + r.stdout))
r = subprocess.run([sys.executable, "-m", "estudio", "autorizacion", "verificar", ESCENA, "--issues", f.name,
                    "--resolucion", "960x540", "--muestras", "6"], capture_output=True, text=True, timeout=60)
caso("10d verificación de los flujos: código de salida ≠ 0 si no hay autorización", r.returncode == 1, r.stdout.strip()[:140])

# ---- 10. ningún flujo de GitHub renderiza sin verificar (análisis de los YAML)
RENDER = re.compile(r"render_rango\.py|render_bloque\.py|python3? -m estudio (render|fijas)\b|animatica\.py")
for wf in sorted((RAIZ / ".github" / "workflows").glob("*.yml")):
    txt = wf.read_text()
    if not RENDER.search(txt):
        continue
    trig = txt.split("\npermissions:")[0]
    caso(f"10e {wf.name}: no se dispara solo (push/schedule/issues)",
         not re.search(r"^\s{2}(push|schedule|issues|pull_request|workflow_run):", trig, re.M))
    caso(f"10f {wf.name}: verifica la autorización antes de pedir máquinas",
         "autorizacion verificar" in txt or "AUT.verificar" in txt)
    for bloque in re.split(r"\n  [a-z_]+:\n", txt):
        codigo = "\n".join(l for l in bloque.splitlines() if not l.lstrip().startswith("#"))
        if RENDER.search(codigo):
            caso(f"10g {wf.name}: el trabajo que renderiza baja los registros (CINE_ISSUES) y vuelve a verificar",
                 "CINE_ISSUES" in bloque)
    caso(f"10h {wf.name}: lee los Issues (permiso issues: read)", re.search(r"issues:\s*(read|write)", txt) is not None)

malos = [n for n, ok in resultados if not ok]
print(f"\n{len(resultados) - len(malos)}/{len(resultados)} comprobaciones OK" + (f" — FALLAN: {malos}" if malos else ""))
sys.exit(1 if malos else 0)
