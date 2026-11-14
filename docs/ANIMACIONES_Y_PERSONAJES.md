# Animaciones, personajes, armas y vehículos

## Inventario de animaciones (`catalogo/animaciones.json`)

`$PY -m estudio animaciones [--analizar]` lo regenera desde `mixamo-respaldo` (sólo lectura).
- **3292 clips**: 3100 FBX de Mixamo (esqueleto `mixamo_65`), 178 clips GLB de personas (`mixamo_66_root`),
  14 de perro (`perro_48`).
- Por clip: referencia (`mixamo:ruta`), nombre y descripciones (es/en), pack, duración, fotogramas, fps,
  **funciones derivadas** (idle, caminar, correr, sprint, agacharse, arrastrarse, saltar, caer, levantarse,
  girar, mirar, apuntar, disparar, recargar, cambiar_arma, pelear, golpear, esquivar, recibir_impacto, morir,
  conducir, subir/bajar_vehiculo, sentarse, interactuar, gesto, hablar, reaccion, nadar, trepar, bailar, lanzar,
  herido, sigilo, magia), **arma**, **postura**, en el lugar / con desplazamiento, bucle probable,
  **grupo de similares** y cantidad de variantes.
- `catalogo/analisis_animaciones.json`: muestra de 40 abierta con Blender → 40/40 esqueleto mixamorig de 65 huesos,
  rango de fotogramas y desplazamiento real de la cadera.
- Búsqueda por contexto: `estudio.catalogo.animaciones.buscar("recargar", arma="rifle")`.

Pendiente (Etapa 5): análisis completo de los 3292 (desplazamiento, velocidad, bucle real comparando primer y último
fotograma), miniaturas/previsualizaciones, marcas de eventos (pisada, disparo, recarga) para sincronizar sonido.

## Personajes ya integrados

- **Jefa** (`mixamo:jefa`): rig de Mixamo con retargeting; ver `docs/MODELOS.md`.
- **Futbolista** (`futbol:jugador`): animado con sus 3 223 clips, uniforme configurable. Ver `docs/FUTBOL.md`.

## Personajes y retargeting (Etapa 5)

- Compatibles directos (mismo esqueleto): Y Bot (`mixamo:personajes/ybot_tpose.fbx`), operador de Nexus
  (`nexus:personajes/operador_character.fbx`, 65 huesos mixamorig — verificado).
- Proceso previsto para modelos nuevos (Tripo3D, FBX, GLB): 1) importar; 2) validar rig (nombres, jerarquía,
  T/A-pose, escala); 3) si es mixamorig → directo; si no → tabla de correspondencia de huesos + retarget por
  rotaciones con compensación de pose de descanso; 4) prueba automática (render de 3 clips de control).
- Rig facial: si existe, se usa en diálogos; si no, la dirección usa planos generales, perfil o de espaldas
  (nunca se bloquea una producción por eso).
- Tripo3D: sólo con autorización y comprobando costo antes de generar/riggear.

## Armas (`catalogo/armas.json`)

5 armas listas (Extraction-tactical) con origen en la empuñadura, +Z boca del cañón y puntos de mano derecha,
mano izquierda, culata y boca medidos → se fijan al hueso `mixamorig:RightHand`. 4 paquetes originales de Nexus
listados para procesar (separar cada arma, escala, puntos). Pendiente: cuchillos, mochilas, cascos, chalecos.

## Vehículos (`catalogo/vehiculos.json`)

Sedán procedural (genérico, sin marca) con anclas (asiento, puerta, ruedas, capot, baúl, techo), ruedas que
giran según la distancia recorrida y faros reales. Esquema de anclas para modelos importados (ruedas, puertas con
bisagra, asientos, luces). El auto de Nexus representa un modelo real: no se usa sin revisar licencia y derechos.
