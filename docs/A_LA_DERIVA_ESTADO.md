# «A la deriva» — todo lo hecho y cómo retomarlo (guardado el 23/11/2026)

Serie espacial de Aiden, Kate y EVA (p011). Este documento junta lo que hay que saber para retomar la serie o reutilizar sus piezas
en otra. **Formato de publicación: VERTICAL 9:16, 540×960, 30 fps** (Shorts/Reels/TikTok). El 23/11 se renderizó el cap. 3 en horizontal
por error y hubo que rehacerlo: **antes de renderizar cualquier video, confirmar el formato en `produccion.json` y con el dueño.**

## 1. Qué existe
| Pieza | Dónde | Estado |
|---|---|---|
| Cap. 1 y 2 | `producciones/p011_a_la_deriva/escenas/e01`, `e02` (sistema anterior, recetas `escena.json`) | entregados |
| Cap. 3 «Protocolo de cierre» (5 escenas, 177 s) | guion `herramientas/guion_e03.py`, voces `audio_e03/voces.json`, storyboard `herramientas/storyboard_e03.py`, Godot `godot_e03/` | **entregado en vertical** (p021 v001) |
| Render vertical (correcto) | Release `blend-p021_a_la_deriva_cap3-v001` (BLEND + MP4 sin audio); producción `producciones/p021_a_la_deriva_cap3/` | publicado |
| Render horizontal (error) | Release `blend-p020_a_la_deriva_cap3-v001` | **descartar** (no sirve para publicar) |
| Video final CON sonido | se arma con `herramientas/audio_cap3.py` sobre el MP4 de la Release; el dueño lo recibió por el chat | no está en ninguna Release |
| Personajes para cambiar ropa | zip que recibió el dueño; se regenera con `herramientas/personajes_c3/entrega_personaje.py` | no está en el repo |

## 2. Lo que NO está en el repo (y por qué)
- **Modelos originales de los personajes** (FBX/BLEND de Character Creator 4, ~540 MB): los subió el dueño. Aiden = «Man03/fbx_a», Kate = «chica nueva»
  (`m/fbx/fbx.fbx`), tercera mujer = «fbx_b» (era EVA, ahora «Mujer adulta»). **No traen licencia**; el repo es público y los Releases también:
  hay que confirmar los términos antes de publicar archivos con esos modelos (los BLEND de las Releases p020/p021 ya los contienen).
  Si la sesión se reinicia, el dueño tiene que volver a subirlos. Rutas de trabajo usadas: `/home/user/personajes_c3/modelos/{fbx_a,fbx_b}`, `/home/user/chica_nueva/m/fbx`.
- GLB, .blend intermedios, cuadros y MP4 (regla 5). Se regeneran con los scripts de abajo.
- Animaciones de Mixamo: repo privado `mixamo-respaldo` (sólo lectura).

## 3. Cómo se rehace todo (orden)
1. **Voces** (ElevenLabs, `config/voces.json`: EVA = Alma, Aiden = `aiden_es_ar`, Kate = `kate_es_ar`): `herramientas/voces_e03.py [--gastar]`. Cap. 3 costó 2.240 créditos. Los mp3 y alineaciones por letra viven en `audio/biblioteca/`.
2. **Personajes** (Blender: `/opt/tools/blendenv/bin/python`): `herramientas/personajes_c3/ensamblar.py -- fbx nombre piel pelo clips_e03.json` (colores reales, 35 clips de Mixamo retargeteados **con el movimiento de raíz extraído**, `raiz_xy` en el meta) → `traje2.py -- nombre` (traje «primera piel» + botas + collar, corte limpio por altura y planos, formas de cara reducidas) → `agregar_clips.py` para clips nuevos.
3. **Nave única** (Godot 4.7.2): `godot_e03/tools/construir_nave.gd` → `verificar.gd` (0 problemas) ; plantas reales desde `herramientas/plantas/plantas.py` (PNG, no JPEG: Godot no lee el JPEG de Blender 5.3).
4. **Storyboard → escenas**: `python storyboard_e03.py` (escribe `godot_e03/data/storyboard_e03.json`; `REENCUADRE` = cámaras verticales) → `godot --path . --script res://tools/montaje.gd -- sN prefijo [segundos|tomas|plan] [sin_glb]` (hornea clips, cara/labios por letra, manos que agarran, cámaras suaves; sale GLB + JSON).
5. **Blender del capítulo**: `herramientas/etapa_blender/construir_cap3.py -- salida.blend` (+ `efectos_cap3.py`: luces por sala, piel, holograma de EVA, normales del piso) → un solo BLEND de 5.324 cuadros. Muestras: `muestra.py`.
6. **Aprobación y render**: `python -m estudio.autofinisher aprobar-blend …` → BLEND por Git LFS en `producciones/<p>/blend/` → `incorporar_blend.yml` (60 trabajos). Perfil de render obligatorio + `PERFIL_540V` (540×960) y `PERFIL_540H` (960×540, no usar).
7. **Sonido**: `herramientas/audio_cap3.py video_mudo.mp4 salida.mp4` (voces + ambiente `nave_interior` ×0,35 + música y efectos de la biblioteca de los cap. 1 y 2 + pasos + alerta). Necesita `/tmp/e3/sN_plan.json` (`montaje.gd -- sN prefijo plan`).

## 4. Trampas que ya nos mordieron
- El importador glTF de Blender 5.3 deja las pistas NLA **silenciadas** (`mute=True`) y con nombres `escena`, `escena.001`…: desilenciar y desplazar con `frame_start_ui`.
- Godot exporta la malla de un esqueleto ×0,01: hay que poner `custom_aabb` o el recorte la oculta.
- Piezas de la nave con las caras al revés → piso negro en Cycles; `efectos_cap3.py` las orienta. El tinte >1 de Godot se pierde en glTF.
- Z-fighting entre traje y piel: el traje va 12 mm afuera; cámaras con `near` 0,1.
- Los materiales procedurales de Blender no viajan en el GLB (agua, estrellas, holograma): se rehacen en la etapa Blender.
- ElevenLabs: estimar antes de gastar; `config/presupuesto_audio.json` (reserva 5.000, tope 4.000 por escena); en noviembre se llevan ~7.400 de 40.000.
- `rm` con comodines lo bloquea el sistema de seguridad: no insistir, sobrescribir archivos.

## 5. Pendientes conocidos del cap. 3
Parche claro en la nuca de Aiden (cuero cabelludo), aro de cuello provisorio y borde irregular en el cuello de Aiden, botas con forma de aleta, EVA como silueta azul plana
(falta la construcción por capas del holograma), pelo sin física, 33 voces sin variantes. Además: borrar o no el render horizontal p020, y la **licencia de los modelos**.
El dueño no revisó en su visor HTML la versión con luces/efectos de Blender antes del render (sólo la de Godot).

## 6. Cómo trabaja el dueño (aprendido en esta tanda)
Godot arma el escenario único y los personajes; Blender sólo corrige modelos y agrega luces/efectos. Revisa con GLB + JSON en su visor. Quiere vertical, el mismo
sonido de los capítulos anteriores, personajes «normales» (no la EVA IA) para los paquetes de ropa, y que se le avise antes si algo obliga a rehacer.

## 7. Limpieza del 23/11/2026 (pedido del dueño: los videos ya están en YouTube)
- Se borraron del árbol de trabajo 269 audios viejos (`audio/biblioteca/` salvo 6 archivos que reutiliza `audio_cap3.py`, más `producciones/*/audio`) y sus entradas de `catalogo/audio.json` (178 → 10). `audio/ledger.jsonl` se conserva.
- **Para recuperar cualquier audio:** `git show 2e07f26:<ruta>` (último commit con todo). Las voces se pueden regenerar con ElevenLabs (cuesta créditos).
- Se conservan escenas, recetas, fuentes de Godot/Blender, BLEND por LFS y herramientas para capítulos futuros.
- Videos/audios de las Releases: se borran con el flujo `borrar_medios.yml` (primero simulacro); los BLEND, GLB y manifiestos no se tocan.
