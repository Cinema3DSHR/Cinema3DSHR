"""Rutas y fuentes de recursos. Todo se puede cambiar con variables de entorno (nunca secretos aquí)."""
from __future__ import annotations
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "catalogo"
ESCENARIOS = RAIZ / "escenarios"
PRODUCCIONES = RAIZ / "producciones"
SALIDA = Path(os.environ.get("CINE_SALIDA", RAIZ / "salida"))  # renders y temporales (fuera de Git)

# Repositorio público donde se publican entregables (GitHub Releases) y el catálogo que lee la app.
REPO = os.environ.get("CINE_REPO", "Cinema3DSHR/Cinema3DSHR")

# Fuentes de recursos pesados reutilizables. Se referencian como "<fuente>:<ruta relativa>".
# Los originales NUNCA se modifican: el sistema sólo lee de estas carpetas.
FUENTES = {
    # 3099 animaciones Mixamo (Y Bot, FBX 30 fps) + packs GLB. Repo privado.
    "mixamo": Path(os.environ.get("CINE_MIXAMO_DIR", RAIZ.parent / "mixamo-respaldo")),
    # Material original de Operación Nexus (armas, operador, vehículo, audio). Repo privado.
    "nexus": Path(os.environ.get("CINE_NEXUS_DIR", RAIZ.parent / "Operaci-n-Nexus-1" / "fuente")),
    # Armas ya procesadas con puntos de agarre (Extraction-tactical). Repo privado.
    "extraction": Path(os.environ.get("CINE_EXTRACTION_DIR", RAIZ.parent / "Extraction-tactical" / "public")),
    # Dream Rally (repo público): autos con sus medidas (.json), piloto, vegetación, rutas.
    "rally": Path(os.environ.get("CINE_RALLY_DIR", RAIZ.parent / "Rally-Sim-movile")),
    # Biblioteca Sweet Home 3D de Nexus (724 GLB a escala real; mismo contenido que sweethome3d-models-master).
    "sh3d": Path(os.environ.get("CINE_SH3D_DIR", RAIZ.parent / "Operaci-n-Nexus-1" / "game" / "assets" / "sh3d")),
    # Modelos que manda el dueño por el chat (Tripo3D: Messi, Cristiano…): fuera de Git; en Actions los baja el flujo.
    "subidas": Path(os.environ.get("CINE_SUBIDAS_DIR", RAIZ.parent / "modelos_subidos")),
    # Recursos propios del estudio (generados por el propio sistema; viven en este repo o en Releases).
    "estudio": RAIZ / "recursos",
}


def resolver(ref: str) -> Path:
    """Convierte "mixamo:packs/x.fbx" en una ruta local. Lanza FileNotFoundError si falta."""
    if ":" not in ref:
        raise ValueError(f"Referencia sin fuente: {ref!r} (formato <fuente>:<ruta>)")
    fuente, rel = ref.split(":", 1)
    if fuente not in FUENTES:
        raise ValueError(f"Fuente desconocida {fuente!r}; conocidas: {sorted(FUENTES)}")
    p = FUENTES[fuente] / rel
    if not p.exists():
        raise FileNotFoundError(f"No está el recurso {ref} (buscado en {p})")
    return p


# Niveles de calidad (sección 17). Medido en un servidor de 4 núcleos SIN GPU (igual a los de GitHub Actions):
# Cycles CPU + OIDN rinde mejor que EEVEE por software (Mesa llvmpipe): 17–24 s por fotograma a 720p contra 35–65 s,
# y con luces de faros/reflejos correctos. EEVEE queda disponible para máquinas con GPU ("motor": "BLENDER_EEVEE").
CALIDADES = {
    "humo":     {"ancho": 320,  "alto": 180,  "fps": 30, "muestras": 2,  "motor": "CYCLES", "crf": 30},  # pruebas
    "previa":   {"ancho": 854,  "alto": 480,  "fps": 30, "muestras": 4,  "motor": "CYCLES", "crf": 28},
    "revision": {"ancho": 1280, "alto": 720,  "fps": 30, "muestras": 10, "motor": "CYCLES", "crf": 22},
    "final":    {"ancho": 1920, "alto": 1080, "fps": 30, "muestras": 48, "motor": "CYCLES", "crf": 19},
    "final4k":  {"ancho": 3840, "alto": 2160, "fps": 30, "muestras": 64, "motor": "CYCLES", "crf": 18},
}
