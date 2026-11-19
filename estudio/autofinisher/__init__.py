"""AutoFinisher — prepara un proyecto Blender AUTÓNOMO a partir del GLB que exporta Godot (docs/AUTOFINISHER.md).

Pipeline del estudio:  GODOT → GLB → AUTOFINISHER → .BLEND AUTÓNOMO → GITHUB RELEASES → DESCARGA → RENDER → MP4

La escena se construye UNA vez por versión. El .blend queda guardado (inmutable, identificado por su manifiesto y sus
hashes) y se renderiza las veces que haga falta sin reconstruirla.

Módulos (los que dicen «bpy» sólo corren dentro del Python de Blender; el resto es Python común, para los
planificadores de Actions y las pruebas):
  receta.py         lee y completa la receta de terminación (entrada)                         — sin bpy
  manifiesto.py     manifiesto de la versión, hashes SHA-256, nombres de versión y Release    — sin bpy
  reparto.py        reparto de cuadros entre trabajos y verificación de cuadros renderizados  — sin bpy
  video.py          verificación del MP4 final con ffprobe                                    — sin bpy
  medicion.py       tiempos, RAM máxima y tamaños                                             — sin bpy
  convenciones.py   estándar de nombres Godot → Blender (luces, vidrios, emisivos, vacíos FX) — sin bpy
  auto_import.py    AutoImport: fps antes de importar, GLB, cámara, rango, inspección          — bpy
  auto_lights.py    AutoLights: energía de las luces por perfil (y sus claves animadas)       — bpy
  auto_materials.py AutoMaterials: vidrios con transmisión, emisivos, mundo                   — bpy
  auto_effects.py   AutoEffects: aplica las recetas de efectos pedidas sobre sus vacíos FX_*  — bpy
  recetas_efectos/  biblioteca de efectos deterministas por cuadro (lluvia, fuego, humo, …)    — bpy
  auto_cinema.py    AutoCinema: Cycles según la calidad de la receta                          — bpy
  auto_pack.py      AutoPack: empaqueta todo y falla si queda un recurso externo              — bpy
  auto_report.py    AutoReport: informe JSON de la preparación                                — bpy (lee versiones)
  construir.py      punto de entrada: GLB + receta → .blend + manifiesto + informe            — bpy
  validar.py        valida un .blend contra su manifiesto (sin render)                         — bpy
  render_trozo.py   renderiza los cuadros asignados a un trabajo, con mediciones y reintentos — bpy
"""
VERSION = "1.0.0"
