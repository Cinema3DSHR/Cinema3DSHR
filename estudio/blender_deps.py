"""Dependencias de los modelos de personajes (sin importar bpy, para el planificador de Actions)."""
MODELOS_DEPS = {
    "futbol:jugador": ["mixamo:futbol_free_kick_swipe/exportados/jugador_con_animaciones.glb",
                       "mixamo:futbol_free_kick_swipe/02_jugador/assets/characters/player",
                       "mixamo:futbol_free_kick_swipe/raices_clips.json"],
    "mixamo:jefa": ["mixamo:modelos_pelicula/jefa_o_novia.glb"],
}

# Soldados (mixamo65 de Extraction-tactical y de Operación Nexus) y sus armas
_ARMAS = {"M4A1": "rifle_M4A1", "AK47": "rifle_AK47", "Mossberg": "escopeta_Mossberg", "AWP": "francotirador_AWP",
          "USP": "pistola_USP"}
for _id, _ref in (("ch49", "extraction:characters/personajes/Ch49.glb"), ("ch15", "extraction:characters/personajes/Ch15.glb"),
                  ("ch35", "extraction:characters/personajes/Ch35.glb"), ("operador", "nexus:personajes/operador_character.fbx")):
    MODELOS_DEPS[f"soldado:{_id}"] = [_ref, "mixamo:packs/Pro_Rifle_Pack/idle_aiming.fbx",
                                      "extraction:characters/armas/armas_puntos.json"]


def armas_deps(arma: str) -> list[str]:
    """Archivos de un arma («M4A1», «AK47»…): el modelo y la tabla de puntos de agarre."""
    return [f"extraction:characters/armas/{_ARMAS[arma]}.glb", "extraction:characters/armas/armas_puntos.json"]

MODELOS_DEPS["pelicula:lucia"] = ["mixamo:personajes_pelicula/protagonista_femenina"]
MODELOS_DEPS["pelicula:mateo"] = ["mixamo:personajes_pelicula/protagonista_masculino"]
MODELOS_DEPS["rally:piloto"] = ["rally:godot/game/models/pilot.glb", "rally:godot/game/models/pilot_Ch20_1001_Diffuse.jpg",
                               "rally:godot/game/models/pilot_Ch20_1001_Normal.jpg", "rally:godot/game/models/pilot_ao_met_rough_Ch20_1001_Glossiness.jpg"]
# «Al vacío» (p007): modelos Tripo3D del dueño; usan los clips del juego (futbol:<clip>): necesitan también al futbolista
for _id in ("messi", "cristiano"):
    MODELOS_DEPS[f"pelicula:{_id}"] = [f"mixamo:personajes_pelicula/{_id}"] + MODELOS_DEPS["futbol:jugador"]
# «Dúo Cero» (p009): Stickman definitivos del dueño + el pack de armas (arma en mano) y la pose de referencia del arma
for _id in ("masculino", "femenino"):
    MODELOS_DEPS[f"stickman:{_id}"] = [f"mixamo:personajes_pelicula/stickman_{_id}", "mixamo:personajes_pelicula/armas_stickman",
                                       "mixamo:packs/Pro_Rifle_Pack/idle_aiming.fbx"]
