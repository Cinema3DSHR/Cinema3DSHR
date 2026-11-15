# Registro

## 14/11/2026 — Etapas 1 a 4 (primera entrega)

**Etapa 1 — investigación:** `docs/INFORME_ETAPA1.md`. Blender 5.3 (bpy desde PyPI), Cycles CPU + denoise medido
más rápido y mejor que EEVEE sin GPU, FFmpeg, Godot 4.7.2 (sólo Theora: OGV en la app, MP4 para exportar),
GitHub Releases/Issues/Actions como servidor. Esqueletos: 40/40 FBX de la muestra con mixamorig de 65 huesos.

**Etapa 2 — infraestructura:** paquete `estudio/` (kit procedural, cámaras, vehículos, director, audio procedural,
montaje, manifiestos con versiones/huella/bloqueo, publicación y catálogo, limpieza), catálogos
(3292 animaciones con funciones/arma/postura/similares y buscador; 5 armas con puntos de agarre; vehículos; audio),
flujos de Actions (render paralelo por toma, catálogo, revisiones, película final, limpieza, APK).

**Etapa 3 — escena de prueba:** `producciones/p000_prueba_mansion` (28 s, 7 tomas: general, portón en contrapicado,
detalle de rueda, grúa, cámara de vigilancia con REC, sala de seguridad, aérea) sobre el escenario procedural
`mansion_moderna_noche`. Probado de punta a punta en la sesión en calidad «humo» (320×180): 840 fotogramas en
6,3 min de CPU, audio sincronizado, MP4 + OGV + portada + GLB del visor (0,7 MB) + .blend (0,35 MB).
La versión de revisión (720p) la renderiza el flujo `render.yml` en Actions al subir.

**Etapa 4 — app:** cliente Godot 4.7.2 con INICIO, PELÍCULAS, escena (reproductor + control de producción +
exportación), VISOR 3D, ESCENARIOS y AJUSTES; lanzador con actualización por `app.pck`; firma estable cifrada.
Probado headless + capturas con Xvfb. **No probado en un teléfono.**

## 14/11/2026 — Módulo de fútbol (pedido del dueño)

- Paquete Free Kick Swipe guardado completo en **mixamo-respaldo/futbol_free_kick_swipe/** (rama de la sesión),
  con `README.md` e `indice_futbol.json` (3 223 clips con rol, categoría, toma y golpeo). Originales intactos.
- `catalogo/futbol.json`, `catalogo/personajes.json`; los clips de fútbol también entran al buscador general
  (6 515 clips en total).
- Estudio: importador GLB que tolera extensiones de Godot (copia saneada en caché), personajes animados por NLA con
  encadenado por desplazamiento de cadera, uniformes por máscaras (recrea el shader del juego), pelota con la física
  del juego y solucionador de tiro al destino, estadio rematerializado con 13 074 hinchas sentados, línea de tiempo
  del ánimo del público, sonido de estadio (murmullo, patada, red, ovación).
- Escena de prueba `p001_futbol_tiro_libre` (14 s, 6 tomas) verificada con fotogramas fijos; render completo local en
  calidad previa enviado al dueño. En Actions necesita el secreto `ASSETS_TOKEN`.
- Render de la mansión (p000) en Actions (calidad revisión 1280×720, Cycles): **publicado** en la release
  `p000_prueba_mansion` (MP4, OGV, GLB del visor, .blend, audio) y listado en `catalogo.json` como «para revisar».
  4,6 h de CPU repartidas en 7 máquinas (≈1 h de reloj, ~10–20 s por fotograma según la toma).
- Escenario `mansion_moderna_noche` publicado (release `escenarios`).
- Fútbol en Actions: el flujo se frena (como corresponde) en «Recursos privados» hasta que exista `ASSETS_TOKEN`.
- Los clips de fútbol son en el lugar: se exportaron las curvas de raíz de las bibliotecas `.res` con Godot
  (`raices_clips.json` en mixamo-respaldo) y el director las aplica; la carrera del tiro libre recorre 6,6 m.

## 14/11/2026 — ElevenLabs y 13 modelos 3D

- **ElevenLabs conectado y probado:** plan Starter (40 000 créditos), 27 voces; módulo `estudio/audio/elevenlabs.py` con
  caché permanente, estimación previa, tope de gasto y registro (`audio/ledger.jsonl`). Voz en español de la Jefa y
  un efecto generados (~83 créditos estimados, más ~40 por regenerar el efecto); mezcla verificada midiendo niveles.
  Música no probada. No pude escuchar los audios.
- **13 modelos 3D** guardados sin modificar en mixamo-respaldo/modelos_pelicula (con índice y vistas previas) y
  catalogados (`catalogo/modelos.json`). Vehículos sin ruedas, helicóptero sin rotores, 3 packs de decorado fusionados.
- **Jefa/novia:** esqueleto idéntico al Y Bot → nuevo `retarget.py` (probado: tres errores propios corregidos: slot de
  acción, cm→m y escala mundo) + modelo `mixamo:jefa` en el director + escena de prueba `p002_la_jefa_llega`
  (14 s, 3 tomas, voz y efecto). Verificada con fotogramas fijos y la mezcla de audio; **no se renderizó el video completo**.

## 14/11/2026 — Prueba comparativa de resolución 001 (`pruebas/resolucion_001/`)

- Escena de referencia: mansión p000 v1, sin tocarla; sólo se cambió la resolución de salida en memoria. 4 resoluciones
  (1280×720, 1024×576, 960×540, 854×480) × 5 momentos = 20 imágenes; dos pasadas en orden inverso (idénticas píxel a píxel).
- Resultado principal: el tiempo de render es proporcional a los píxeles (≈ 18,4–19,1 s/MP; 16,96 s por fotograma en 720p a 7,55 s en 480p;
  CPU al 98 %, sin GPU). Lo que se pierde primero al bajar es el detalle fino (textura del agua, vidrio, ventanas lejanas).
- **No se fijó resolución definitiva**: informe en `pruebas/resolucion_001/INFORME.md`; falta que el dueño revise las imágenes. Siguiente: prueba 9:16.
- Error propio corregido en el camino: creí que Cycles no era determinista (comparé bytes de PNG con fecha en los metadatos); comparando píxeles son idénticos.

## 14/11/2026 — Prueba de motor 002 (`pruebas/motor_002/`)

- Auditoría + prueba de 5 fotogramas: Cycles producción 17,1 s/fot.; sin árbol de luces 12,9 s; «rápido» 6,4 s (pierde detalle del agua);
  EEVEE en CPU por software ~51–56 s y **no reproduce la imagen** (agua negra, más oscuro); Godot Movie Maker 0,16 s/fot. (software, GLB del visor).
- Corrección de premisa: los «274 min» son CPU sumada de 7 máquinas, no reloj. La codificación (20 ms/fot.) no es cuello.
- **Sin GPU en el entorno: las cifras de GPU no se midieron.** Pendiente autorización del dueño para alquilar GPU. No se cambió nada del estudio.

## 15/11/2026 — Video de 30 s (Cycles 6 muestras, 720p) — preparado, **bloqueado por ASSETS_TOKEN**

- Copia de producción `p003_futbol_30s` (900 fotogramas; p001 intacta): jugada original + festejo, arquero, barrera, tribuna y aérea final. Tomas nuevas verificadas con fijas.
- `pruebas/video_30s/` (render por rangos, audio, montaje con verificación de integridad/continuidad/CFR) + flujo `video30.yml` (19 trabajos de render + audio en paralelo → MP4 → release). No se modificó el estudio ni los flujos existentes.
- Medido localmente: 11,5 s/fotograma a 6 muestras; 132 s de armado de escena por trabajo; 3,3 GB de RAM. Estimación en Actions: ~13–15 min de reloj.
- El ensayo (4 fotogramas) falló en `planificar`: **falta el secreto `ASSETS_TOKEN`** (lectura de mixamo-respaldo). Creación del secreto: sólo el dueño.

### Pendiente / próximo
- Dueño: crear `ASSETS_TOKEN` (lectura de mixamo-respaldo) para renderizar fútbol en Actions; autorizar fusionar
  la rama de mixamo-respaldo a `main`.
- Dueño: crear `ANDROID_KEYSTORE_PASSWORD` (firma) — sin eso la APK es de prueba.
- Dueño: decidir si el repo sigue público (videos visibles) — ver informe §5.
- Etapa 5: secreto `ASSETS_TOKEN` (lectura de mixamo-respaldo y Nexus en Actions), personajes en escena,
  armas en la mano, análisis completo de animaciones, retargeting.
- Etapa 6: probar música de ElevenLabs y los modelos v3/v4; reparto final de voces.
- Integrar al director los vehículos del dueño (ruedas, frente) y separar los packs de decorado.
- Calidad visual: modelo de auto más detallado, árboles con más forma, pantallas de vigilancia con imagen real.
