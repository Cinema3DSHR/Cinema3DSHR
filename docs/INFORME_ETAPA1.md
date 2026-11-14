# Informe de la Etapa 1 — investigación y decisiones técnicas

Fecha: 14/11/2026. Todo lo marcado **medido** se probó en esta sesión (servidor de 4 núcleos, 16 GB, sin GPU,
equivalente a una máquina estándar de GitHub Actions). Lo marcado **documentación** viene de fuentes oficiales y
conviene revisarlo si cambian los planes de GitHub.

## 1. Repositorios y recursos encontrados

| Repositorio | Qué se usa | Hallazgos |
|---|---|---|
| **Cinema3DSHR** (público) | Todo el estudio | Estaba vacío. Es público: los minutos de Actions son gratis e ilimitados en máquinas estándar, y los entregables en Releases se descargan sin cuenta. **Ojo:** los videos publicados son visibles para quien encuentre el repo (ver §6). |
| **mixamo-respaldo** (privado) | Animaciones | 3099 FBX de Mixamo (Y Bot, FBX 7.7, 30 fps, sin piel) + `ybot_tpose.fbx` con piel + 2 GLB extra (178 clips de personas con esqueleto mixamorig de 66 huesos, 14 de perro). Índice `indice.json` con duración, fotogramas, categoría y descripciones. 2,5 GB en Git. |
| **Operaci-n-Nexus-1** (privado) | Armas, personaje, vehículo, voces | `fuente/armas`: 4 paquetes originales (94 armas en un solo FBX/OBJ/.blend, `Weapons.fbx`, `WeaponsOBJ.obj`, …). `fuente/personajes/operador_character.fbx` (operador táctico, **ya riggeado con mixamorig de 65 huesos**: compatible directo). `fuente/vehiculos/sputnik_jfkennedy_car.glb` (auto real: falta revisar licencia). Voces de ElevenLabs ya generadas para ese juego. También la referencia del *cliente liviano* (lanzador + parche `.pck`). |
| **Extraction-tactical** (privado) | Armas listas | 5 armas GLB ya procesadas (USP, M4A1, AK47, Mossberg, AWP) con **puntos de agarre medidos** (`armas_puntos.json`) y sonidos de disparo OGG. |
| Rally-Sim-movile, Futbol-5, otros | — | Sólo se miraron los flujos de compilación de Godot 4.7.2 como referencia. No se auditaron. |

**Compatibilidad de esqueletos (medido):** muestra al azar de 40 FBX abiertos con Blender: **40/40** con el
esqueleto `mixamorig` de 65 huesos (raíz `mixamorig:Hips`). El operador de Nexus usa el mismo esqueleto. Los clips
GLB de personas tienen 66 huesos (65 + `root`) y se combinan con el resto (mismos nombres).

## 2. Herramientas evaluadas

| Tarea | Elegido | Por qué / medición |
|---|---|---|
| Construcción de escenas, cámaras, animación, render | **Blender 5.3 como módulo de Python (`pip install bpy==5.3.0`)** | Se instala desde PyPI (blender.org no es accesible desde este entorno; en Actions sí, pero PyPI alcanza). Mismo Blender en la sesión de Claude y en Actions. Licencia GPL (las imágenes producidas son del usuario). |
| Motor de render | **Cycles CPU + OpenImageDenoise** | **Medido** en una toma real de la mansión a 1280×720: EEVEE por software (Mesa llvmpipe) 31–67 s/fotograma y sin luces de faros visibles; Cycles 8–12 muestras + denoise **17–24 s/fotograma** con faros, reflejos del asfalto mojado y sombras correctas. EEVEE queda como opción para una futura máquina con GPU. |
| Montaje, audio, conversión | **FFmpeg 6.1** | libx264 (MP4 H.264), libtheora/libvorbis (OGV), loudnorm (-16 LUFS), drawtext (efecto cámara de vigilancia). Medido: montaje de 28 s en < 1 min. |
| Sonido de prueba | **Síntesis propia con numpy** | Ambiente nocturno, motor que sigue la velocidad real del auto, portones; volumen y paneo según la cámara de cada toma. Sin costo ni licencias de terceros. |
| Voces, música, efectos de calidad | **ElevenLabs** (pendiente de autorización) | Ver `docs/AUDIO.md`. No se conectó: falta la clave del dueño. |
| App Android | **Godot 4.7.2**, renderer *GL Compatibility* | El más liviano y compatible para un visor. **Medido:** Godot 4.7.2 sólo decodifica video **Ogg Theora** (no MP4): la app reproduce un OGV y el MP4 H.264 queda para exportar/compartir. `GLTFDocument` carga GLB en tiempo de ejecución (probado: 467 mallas, 7 cámaras, 39 luces, animación). |
| Servidor | **GitHub (Releases + Issues + Actions)** | Sin servidor propio ni costo: ver §3. |

## 3. Límites de GitHub (documentación) y cómo se respetan

- **Repositorio Git:** archivos > 100 MB bloqueados; se recomienda < 1 GB. → En Git sólo van código, recetas,
  manifiestos y catálogos (texto). Videos, GLB y .blend **nunca** van al historial (`.gitignore`).
- **Releases:** cada archivo < 2 GiB; GitHub no limita el tamaño total ni el ancho de banda de las releases.
  → Los entregables van a una release por producción; la app descarga de ahí sin cuenta.
- **Actions:** gratis en repos públicos con máquinas estándar; máximo 6 h por trabajo; 20 trabajos simultáneos
  en el plan Free. → El render se reparte **una máquina por toma** (una escena de 7 tomas a 720p tarda lo que
  tarda su toma más larga: ~1 h, no 5 h).
- **Artifacts:** retención corta (se usan sólo para pasar tomas entre trabajos, 2 días).
- **Git LFS:** no hace falta por ahora (los recursos pesados ya viven en los repos privados de origen y no se
  duplican). Si se usara: el plan Free incluye 10 GiB de almacenamiento y de transferencia según fuentes
  recientes; verificar en *Settings → Billing* antes de activarlo.

## 4. Arquitectura definitiva

Ver `docs/ARQUITECTURA.md`. Resumen:

```
ORDEN A CLAUDE ─► receta (escena.json) en Git ─► push ─► Actions: render por tomas (Blender/Cycles)
   ─► montaje + audio (FFmpeg) ─► Release de la producción (MP4, OGV, GLB visor, .blend, info.json)
   ─► catalogo.json (release "catalogo") ─► APP ANDROID (lee el catálogo, descarga con caché)
   ─► APROBAR / CORREGIR / RENDERIZAR / EXPORTAR = Issue del dueño ─► flujo "Revisiones" ─► Claude
```

## 5. Propuestas de tecnología (para decidir)

1. **Cycles en lugar de EEVEE** para los servidores sin GPU (ya aplicado, medido arriba).
2. **OGV para ver en la app + MP4 para exportar**, porque Godot no trae decodificador H.264. Alternativa futura:
   un plugin Android de ExoPlayer (más trabajo, más peso en la APK).
3. **GitHub Issues como canal de revisión** (en vez de un servidor propio o Supabase): no cuesta, queda historial
   y Claude lo lee con las herramientas de GitHub. La app usa un token personal del dueño guardado cifrado.
4. **Repo público vs. privado:** público = render gratis ilimitado y descargas sin cuenta, pero los videos se
   pueden ver si alguien encuentra el repo. Privado = 2000 min/mes de Actions en el plan Free (una escena de
   28 s a 720p consume ~5 h de CPU repartidas) y la app necesitaría el token también para leer. **Decisión del
   dueño.** Hoy está público.

## 6. Riesgos y pendientes conocidos

- Los recursos Mixamo y las armas están en repos **privados**: para que Actions los use hace falta un secreto
  `ASSETS_TOKEN` (token de sólo lectura de esos repos). Las escenas sin personajes (como la de prueba) no lo
  necesitan. No se publican archivos originales de Mixamo (su licencia no permite redistribuirlos sueltos).
- Firma de la APK: hace falta que el dueño cree el secreto `ANDROID_KEYSTORE_PASSWORD` (ver `docs/APP_ANDROID.md`).
- El auto de Nexus representa un vehículo real: no se usa hasta revisar licencia y derechos de diseño.
