"""Estándar de nombres Godot → Blender (docs/AUTOFINISHER.md §2), sin bpy.

Godot exporta por GLB mallas, materiales PBR, luces, cámaras y animaciones de transformación. Lo demás (partículas,
colisiones de partículas, ambiente, niebla) NO viaja: se marca con un vacío (Node3D) cuyo NOMBRE dice qué rehacer en
Blender. El AutoFinisher reconoce cada elemento así, en este orden:
  1. la propiedad «cine_tipo» del objeto o del material (metadatos de Godot que llegan como extras del glTF);
  2. el prefijo del nombre (lo que usó la prueba «Casa moderna en tormenta», que sigue funcionando).

LUCES  «Luz_<perfil>_<nombre>»  (p. ej. Luz_farola_0, Luz_neon_cocina, Luz_luna)
  perfil          tipo Blender     escala por defecto (unidad de Godot → vatios / W·m⁻² en el sol)
  puntual         POINT            60     (sinónimo en la prueba: «colgante»)
  foco            SPOT             120
  farola          SPOT             120
  neon            POINT/AREA       60
  fuego           POINT            60     (suele estar animada: sus claves se reescalan igual)
  ambiente        SUN              0,6    (sinónimos: luna, sol)
  relampago       SUN              0,6
  Si el nombre no dice el perfil, se usa el del tipo de luz (POINT → puntual, SPOT → foco, SUN → ambiente,
  AREA → area). Cada perfil se puede ajustar en la receta (luces.perfiles.<perfil>.escala) y cada luz por su nombre.

MATERIALES
  vidrio*         transmisión 1 + IOR (los vidrios de Godot llegan como transparencia alfa)
  emisivo* neon*  se informan; la receta puede escalar su emisión
VACÍOS DE EFECTOS «FX_<receta>[_<nombre>]» (p. ej. FX_lluvia, FX_fuego, FX_humo, FX_brasas)
  Sólo se aplica la receta que la receta de terminación PIDE para ese vacío; los vacíos FX sin receta se informan.
  Colision_* (cajas de colisión de partículas de Godot): llegan sin tamaño; las recetas usan cajas explícitas.
"""
from __future__ import annotations

import re

PERFILES_LUZ = {
    "puntual": {"tipos": ("POINT",), "escala": 60.0},
    "foco": {"tipos": ("SPOT",), "escala": 120.0},
    "farola": {"tipos": ("SPOT",), "escala": 120.0},
    "neon": {"tipos": ("POINT", "AREA", "SPOT"), "escala": 60.0},
    "fuego": {"tipos": ("POINT",), "escala": 60.0},
    "ambiente": {"tipos": ("SUN",), "escala": 0.6},
    "relampago": {"tipos": ("SUN", "POINT"), "escala": 0.6},
    "area": {"tipos": ("AREA",), "escala": 60.0},
}
SINONIMOS_LUZ = {"colgante": "puntual", "punto": "puntual", "luna": "ambiente", "sol": "ambiente", "spot": "foco"}
PERFIL_POR_TIPO = {"POINT": "puntual", "SPOT": "foco", "SUN": "ambiente", "AREA": "area"}
PREFIJO_LUZ = "Luz_"
PREFIJO_FX = "FX_"
PREFIJO_COLISION = "Colision_"
PREFIJOS_VIDRIO = ("vidrio",)
PREFIJOS_EMISIVO = ("emisivo", "neon")


def perfil_luz(nombre: str, tipo_blender: str, cine_tipo: str | None = None) -> str:
    """Perfil de una luz: por su propiedad cine_tipo, por su nombre o por su tipo."""
    for cand in (cine_tipo, _token(nombre, PREFIJO_LUZ)):
        if cand:
            c = SINONIMOS_LUZ.get(cand.lower(), cand.lower())
            if c in PERFILES_LUZ:
                return c
    return PERFIL_POR_TIPO.get(tipo_blender, "puntual")


def receta_fx(nombre: str, cine_tipo: str | None = None) -> str | None:
    """«FX_lluvia» → «lluvia»; «FX_fuego_hogar» → «fuego». None si no es un vacío de efecto."""
    if cine_tipo and cine_tipo.lower().startswith("fx_"):
        return cine_tipo[3:].lower()
    return _token(nombre, PREFIJO_FX)


def es_vidrio(nombre_material: str, cine_tipo: str | None = None) -> bool:
    return (cine_tipo or "").lower() == "vidrio" or nombre_material.lower().startswith(PREFIJOS_VIDRIO)


def es_emisivo_por_nombre(nombre_material: str, cine_tipo: str | None = None) -> bool:
    return (cine_tipo or "").lower() in ("emisivo", "neon") or nombre_material.lower().startswith(PREFIJOS_EMISIVO)


def _token(nombre: str, prefijo: str) -> str | None:
    base = re.sub(r"\.\d{3}$", "", nombre)          # Blender agrega .001 a los nombres repetidos
    if not base.startswith(prefijo):
        return None
    resto = base[len(prefijo):]
    return resto.split("_", 1)[0].lower() or None
