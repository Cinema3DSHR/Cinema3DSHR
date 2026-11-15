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
