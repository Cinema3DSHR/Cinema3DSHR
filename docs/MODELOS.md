# Modelos 3D del dueño (vehículos, personaje, decorados)

13 GLB generados con Tripo3D, entregados el 14/11/2026. Originales **sin modificar** en
`mixamo-respaldo/modelos_pelicula/` (privado) con vistas previas y `indice_modelos.json`; acá el catálogo de uso
(`catalogo/modelos.json`, `catalogo/vehiculos.json`, `catalogo/personajes.json`).

| Modelo | Qué es | Estado |
|---|---|---|
| `jefa_o_novia` | Mujer de traje negro, 18 mil polígonos, **65 huesos idénticos a Mixamo** | **Listo y probado en escena** (escena `p002_la_jefa_llega`) |
| `auto_clasico_falcon`, `pickup_arena`, `vehiculo_blindado_policial` | Carrocerías (≈500 mil polígonos) | Sin ruedas; falta integrarlos al director |
| `helicoptero_militar` | Fuselaje | Sin rotores; falta integrarlo |
| `locomotora_diesel`, `vagon_cerrado`, `vagon_plano`, `trailer_plano_camion` | Tren y semirremolque | Una malla cada uno |
| `cocina_sin_segmentos`, `muebles_casa_sin_segmentar`, `moto_enduro_decoracion_taller` | Packs de decorado fusionados | Sirven completos; separar por objeto queda pendiente (~2 000 islas cada uno) |
| `decoracion_taller_segmentada` | 69 piezas de taller sueltas | Usable por pieza |

**Escala:** todos vienen con su lado más largo = 1 m. `escala_real_estimada_m` del catálogo es una estimación (la
Jefa 1,70 m; el auto 5 m; la locomotora 18 m…): hay que ajustarla mirando la toma.
**Peso:** ~500 mil polígonos cada uno: sirven para render, no para el visor del teléfono (hace falta una versión
liviana, como la del escenario).
**Derechos:** el «Falcon» evoca un modelo real de fabricante y el blindado lleva «POLICIA» pintado: sólo para ficción,
sin logos ni marcas.

## La Jefa en una escena

```jsonc
"personajes": [{"id": "jefa", "modelo": "mixamo:jefa", "acciones": [
  {"clip": "mixamo:packs/Female_Locomotion_Pack/walking.fbx", "inicio_s": 0, "pos": [3.1, -17.3], "mirando_deg": 108.7, "repetir": 10},
  {"clip": "mixamo:packs/Female_Locomotion_Pack/idle.fbx", "inicio_s": 10, "encadenar": true, "repetir": 6}]}]
```
- `clip` es cualquier FBX del catálogo de Mixamo (`catalogo/animaciones.json`, campo `ref`).
- Se **retargetea** al esqueleto de la Jefa (`estudio/blender/retarget.py`): sin eso, el clip la deja en T-pose y, al
  forzarlo, la cadera viaja a −77 m (el FBX está en centímetros).
- Al repetir un ciclo, el personaje avanza lo que avanzó el ciclo (si no, se «desliza» y vuelve al punto de partida).
- `mirando_deg`: 0 = hacia +X, 90 = hacia +Y. El modelo mira a −Y y el estudio ya lo compensa.
- Las cámaras la siguen con `{"movil": "jefa", "punto": "cabeza"}` (puntos: cadera, pecho, cabeza, pies).
- Sirven también los 3 223 clips de fútbol? **No**: ésos son para el jugador de fútbol (otro esqueleto de 23 huesos).

## Pendiente
Ruedas y rotores; definir el frente de cada vehículo; separar los packs; versiones livianas para el visor.
