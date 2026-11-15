"""Inventario y procedencia de los recursos de «Operación Tren Fantasma».

Recorre los repositorios de recursos (sin modificarlos) y escribe `recursos/inventario.json` con, por cada recurso:
nombre, tipo, repositorio, propietario, ruta, archivo, formato, bytes, commit del archivo, SHA-256, licencia conocida,
adaptaciones, compatibilidad y secuencias donde se usa. También el inventario completo de animaciones por categoría.
Uso: python inventario.py   (con los repositorios clonados al lado de Cinema3DSHR)
"""
import hashlib
import json
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
BASE = RAIZ.parent
REPOS = {"mixamo-respaldo": BASE / "mixamo-respaldo", "Rally-Sim-movile": BASE / "Rally-Sim-movile",
         "Operaci-n-Nexus-1": BASE / "Operaci-n-Nexus-1", "Extraction-tactical": BASE / "Extraction-tactical"}
DUENO = "webmaletin-art"
LIC_SH3D = {"contrib": "Free Art License 1.3 (Space Mushrooms y colaboradores)", "luca": "Free Art License 1.3 (LucaPresidente)",
            "trees": "Free Art License 1.3 (árboles Arbaro)", "bscc0": "CC0 1.0 (Blend Swap)", "bsccby": "CC BY 3.0 (Blend Swap)",
            "kator": "CC BY 3.0 US (Andrew Kator & Jennifer Legaz)", "reall": "CC BY 3.0 US (Reallusion)",
            "scopia": "CC BY 3.0 (Space Mushrooms y Scopia)", "starship": "Ken Mayes, sin licencia explícita (confirmar antes de uso comercial)"}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def commit(repo: str, rel: str) -> str:
    r = subprocess.run(["git", "-C", str(REPOS[repo]), "log", "-1", "--format=%H", "--", rel], capture_output=True, text=True)
    return r.stdout.strip() or subprocess.run(["git", "-C", str(REPOS[repo]), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def item(nombre, tipo, repo, rel, licencia, adaptaciones, secuencias, compat="compatible", **extra):
    p = REPOS[repo] / rel
    d = {"nombre": nombre, "tipo": tipo, "repositorio": f"{DUENO}/{repo}", "propietario": DUENO, "ruta": rel,
         "archivo": p.name, "formato": p.suffix.lstrip(".").upper(), "existe": p.exists(),
         "bytes": p.stat().st_size if p.exists() else None, "commit": commit(repo, rel) if p.exists() else None,
         "sha256": sha(p) if p.exists() and p.is_file() else None, "licencia": licencia, "adaptaciones": adaptaciones,
         "compatibilidad": compat, "secuencias": secuencias}
    d.update(extra)
    return d


R = []
# ---------------------------------------------------------------- personajes
R += [item("Lucía Ferrán (protagonista femenina)", "personaje", "mixamo-respaldo",
           "personajes_pelicula/protagonista_femenina/tripo_convert_5669269a-5647-4c37-ad7b-71abe72fe517.fbx",
           "modelo generado por el dueño con Tripo3D", "escala a 1,68 m; clips Mixamo por retarget", ["s02", "s03", "s04", "s05", "s06", "s08"],
           "esqueleto mixamorig 65 huesos"),
      item("Mateo Ibarra (protagonista masculino)", "personaje", "mixamo-respaldo",
           "personajes_pelicula/protagonista_masculino/tripo_convert_83c2a1e7-3bcc-46c6-b430-400ef54f0b81.fbx",
           "modelo generado por el dueño con Tripo3D", "escala a 1,80 m; clips Mixamo por retarget", ["s02", "s03", "s04", "s05", "s06", "s07", "s08"],
           "esqueleto mixamorig 65 huesos"),
      item("Soldado Ch35 (SWAT)", "personaje", "Extraction-tactical", "public/characters/personajes/Ch35.glb", "Mixamo (Adobe), uso libre en producciones",
           "fusil M4A1 acoplado a las manos", ["s01", "s04"]),
      item("Soldado Ch15 (camuflaje)", "personaje", "Extraction-tactical", "public/characters/personajes/Ch15.glb", "Mixamo (Adobe)", "fusil acoplado", ["s01", "s04"]),
      item("Operador de Nexus", "personaje", "Operaci-n-Nexus-1", "fuente/personajes/operador_character.fbx", "del dueño (Operación Nexus)", "fusil acoplado", ["s01", "s04", "s07"]),
      item("Piloto con casco (motociclistas)", "personaje", "Rally-Sim-movile", "godot/game/models/pilot.glb", "Mixamo Ch20 (del juego Dream Rally)",
           "material negro mate; pose de manejo de moto", ["s01", "s06"], "esqueleto mixamorig 52 huesos (sin dedos)")]
# ---------------------------------------------------------------- vehículos y tren
for nombre, rel, sec, ad in (
        ("Locomotora diésel", "modelos_pelicula/locomotora_diesel.glb", ["s01", "s03", "s04", "s05", "s08"], "escala 18 m; bogies con ruedas de acero animadas"),
        ("Vagón plataforma", "modelos_pelicula/vagon_plano.glb", ["s01", "s03", "s04", "s05"], "escala 14 m; ruedas de acero; amarres; autos encima"),
        ("Vagón cerrado", "modelos_pelicula/vagon_cerrado.glb", ["s01", "s04", "s05"], "escala 13,7 m; ruedas de acero; puerta corrediza"),
        ("Pickup 4×4 blanca (camioneta robada)", "modelos_pelicula/pickup_arena.glb", ["s05", "s06", "s07", "s08"], "ruedas Dream Rally; torreta remota"),
        ("Blindado (escolta Halcón Negro)", "modelos_pelicula/vehiculo_blindado_policial.glb", ["s01", "s03", "s06"], "ruedas Dream Rally; ficción"),
        ("Semirremolque plano", "modelos_pelicula/trailer_plano_camion.glb", ["s02", "s03"], "ruedas Dream Rally en 3 ejes; rampas"),
        ("Helicóptero militar", "modelos_pelicula/helicoptero_militar.glb", ["s07"], "rotores construidos y animados; daño"),
        ("Auto clásico (tránsito)", "modelos_pelicula/auto_clasico_falcon.glb", ["s02", "s06"], "ruedas Dream Rally")):
    R.append(item(nombre, "vehiculo", "mixamo-respaldo", rel, "modelo generado por el dueño con Tripo3D", ad, sec))
for c in sorted((REPOS["Rally-Sim-movile"] / "godot/game/models/cars").glob("*.json")):
    if c.stem in ("decals",):
        continue
    glb = c.with_suffix(".glb")
    if glb.exists():
        R.append(item(f"Dream Rally · {c.stem}", "vehiculo", "Rally-Sim-movile", f"godot/game/models/cars/{glb.name}",
                      "del dueño (juego Dream Rally)", "ruedas generadas con las medidas de su .json (arcos, radio, trocha, lift)",
                      ["s01", "s03", "s04"], parametros=f"godot/game/models/cars/{c.name}"))
# ---------------------------------------------------------------- Sweet Home 3D (vía Nexus)
sh = json.loads((REPOS["Operaci-n-Nexus-1"] / "game/assets/sh3d/models.json").read_text())
usados = {"tree", "bush", "car", "truck", "motorcycle", "streetlight", "fence", "rock", "bus", "window", "door", "table", "chair",
          "cabinet", "shelf", "sofa", "armchair", "fridge", "stove", "bed", "crate", "trash", "bench"}
for m in sh:
    if m["kind"] in usados:
        R.append(item(f"Sweet Home · {m['id']}", f"decorado/{m['kind']}", "Operaci-n-Nexus-1", f"game/assets/sh3d/models/{Path(m['file']).name}",
                      LIC_SH3D.get(m["lib"], m["lib"]), "escala real en metros; instanciado", [], medidas_m=[m["w"], m["d"], m["h"]],
                      biblioteca=m["lib"], nota="idéntico al ZIP sweethome3d-models-master entregado por el dueño (723 GLB, mismos SHA-256)"))
# ---------------------------------------------------------------- vegetación de Dream Rally
for p in sorted((REPOS["Rally-Sim-movile"] / "godot/game/vegbench/models").glob("*.glb")):
    R.append(item(f"Dream Rally · vegetación {p.stem}", "decorado/vegetacion", "Rally-Sim-movile", f"godot/game/vegbench/models/{p.name}",
                  "del dueño (Dream Rally)", "instanciado", ["s01", "s06"]))
# ---------------------------------------------------------------- armas
for a in ("rifle_M4A1", "rifle_AK47"):
    R.append(item(f"Arma {a}", "arma", "Extraction-tactical", f"public/characters/armas/{a}.glb", "del dueño (Extraction Tactical)",
                  "acoplada a la mano derecha con puntos de agarre", ["s01", "s04"]))
# ---------------------------------------------------------------- animaciones (inventario completo por categoría)
anim = {}
for d in sorted((REPOS["mixamo-respaldo"] / "animaciones").iterdir()):
    if d.is_dir():
        anim[d.name] = sorted(p.name for p in d.glob("*.fbx") if "inplace" not in p.name.lower())
packs = {d.name: len(list(d.glob("*.fbx"))) for d in sorted((REPOS["mixamo-respaldo"] / "packs").iterdir()) if d.is_dir()}
salida = {"produccion": "p006_operacion_tren_fantasma", "generado_por": "herramientas/inventario.py",
          "repositorios": {k: subprocess.run(["git", "-C", str(v), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
                           for k, v in REPOS.items()},
          "recursos": R, "animaciones_por_categoria": anim,
          "animaciones_resumen": {"clips": sum(len(v) for v in anim.values()), "categorias": {k: len(v) for k, v in anim.items()}, "packs": packs},
          "licencia_mixamo": "Animaciones y personajes Mixamo (Adobe): uso libre en proyectos personales y comerciales, no se redistribuyen sueltos."}
(AQUI.parent / "recursos" / "inventario.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1))
print(len(R), "recursos ·", salida["animaciones_resumen"]["clips"], "clips de animación")
