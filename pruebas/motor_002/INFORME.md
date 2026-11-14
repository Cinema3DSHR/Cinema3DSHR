# Prueba de motor 002 — ¿se puede renderizar radicalmente más rápido?

14/11/2026 · Estado: **investigación + prueba de 5 fotogramas; no se cambió nada del estudio** (código, recetas, `config.py` intactos). Todo vive en `pruebas/motor_002/`; los PNG están en `salida/pruebas/motor_002/` (fuera de Git).

## 0. Conclusión corta

1. **El problema real es más chico de lo que parece, y la solución no es un solo cambio.** Los «274 min» son **CPU sumada de 7 máquinas en paralelo** (840 fotogramas × 19,6 s), no tiempo de reloj: el reloj fue ~26 min la toma más larga + montaje. Una película de 10 min a este ritmo son ~85 h de CPU = ~4,3 h de reloj con los 20 trabajos simultáneos de GitHub Actions.
2. **Un motor de rasterización (Godot/EEVEE) es entre ~100× (Godot) y ~1× (EEVEE en CPU) más rápido según el caso, pero hoy NO reproduce la imagen:** la misma escena sin adaptar sale oscura, sin los reflejos del asfalto mojado, y en EEVEE el agua de la piscina sale negra (SSIM 0,87 y 0,63 contra Cycles). Cambiar de motor es un proyecto de adaptación de escena, no un interruptor.
3. **Lo que se puede hacer ya, sin perder el «look»:** ajustes de Cycles (−25 % de tiempo con un costo de calidad pequeño y medido) y mejor reparto del trabajo. Lo que da el salto grande (10–100×) es una **GPU**, y **este equipo no tiene**: esas cifras no las pude medir y las marco como tales.
4. **Recomendación:** pipeline de dos niveles (borrador raster instantáneo para encuadrar + Cycles para revisión/final) y, para el salto real, repetir esta misma prueba en una GPU alquilada (costo estimado < US$ 1; **necesito tu autorización**, ver §7).

## 1. Auditoría del pipeline actual (sólo lectura)

| Etapa | Qué hace hoy | Costo medido | ¿Es el cuello? |
|---|---|---|---|
| Armado de escena (`director.construir`) | Genera la mansión con Python | 0,4 s | No |
| Render (`render_tomas`) | Cycles **CPU**, 10 muestras, OIDN, adaptativo, 6 rebotes, `persistent_data`; un fotograma a la vez a JPEG q92 | **17,1 s/fotograma** a 720p | **Sí (99,9 %)** |
| Codificación | `montaje.py`: x264 `slow` CRF 22 | 20 ms/fotograma (medido: 840 fotogramas en 16,9 s) | No |
| Guardado de imagen | JPEG/PNG | 0,12–0,27 s con ffmpeg; en Blender es parte del render | No |
| Reparto | 1 máquina por **toma** en Actions (20 simultáneas en plan gratis) | wall ≈ la toma más larga | Mejorable (§6) |

**Dónde se va un fotograma de 17,5 s** (medido en `auditar.py`): ~1,6 s de preparar la escena, **~1,4 s por muestra** × 10 = 14 s, ~3 s de denoise. La escena es **geométricamente trivial** (3.520 polígonos, 128 instancias): lo caro es la **iluminación** (47 luces, 25 con sombra: 16 spots, 6 áreas, 1 sol), 16 texturas de ruido procedural, 8 bump, 1 material con transmisión (agua) y 2 con alfa. **Ningún fotograma es idéntico al anterior** (cámaras en movimiento o con temblor): no hay reutilización trivial.
Hallazgo: el **árbol de luces de Cycles (`use_light_tree`) con 47 luces sale más lento** (17,5 s con árbol, 13,7 s sin él).

## 2. Prueba reproducible de 5 fotogramas

- **Escena:** `p000_prueba_mansion` v1 (la publicada), armada con `director.construir(…, "revision")`. **Cámaras, fotogramas, resolución (1280×720) y receta idénticos**; sólo cambia la variante en memoria.
- **Fotogramas:** los mismos cinco de la prueba 001 (`momentos.json`): #61, #421, #523, #730, #829 (general, fachada, garaje, piscina, jardín).
- **Método:** un proceso por variante (el pico de RAM es de esa variante), un render de calentamiento descartado, equipo sin otra carga, mismos PNG sin pérdida. Referencia de calidad: **Cycles 64 muestras sin adaptativo** (casi convergida).
- **Reproducir:** `python pruebas/motor_002/correr.py` (6 variantes, ~25 min) y `python pruebas/motor_002/analizar.py`. Equipo: 4 núcleos, 16 GB, **sin GPU**, Blender 5.3.0.
- **Métricas de calidad:** SSIM y PSNR contra la referencia de 64 muestras y contra la producción actual; «detalle» = energía de alta frecuencia relativa a producción; brillo medio.

## 3. Resultados (5 fotogramas, 1280×720, media)

| Variante | s/fotograma | RAM pico | SSIM vs ref64 | PSNR vs ref64 | Detalle | Brillo vs ref | **10 min: CPU** | **10 min: reloj con 20 máq.** |
|---|---|---|---|---|---|---|---|---|
| **Cycles producción** (10 muestras) | **17,06** | 1253 MB | 0,983 | 37,3 dB | 100 % | +0,07 | 85 h | 4,3 h |
| Cycles sin árbol de luces | 12,85 | 1252 MB | 0,969 | 35,7 dB | 95 % | +0,42 | 64 h | 3,2 h |
| Cycles «rápido» (6 muestras, sin árbol, denoise FAST) | 6,42 | 1093 MB | 0,950 | 33,3 dB | 80 % | +0,79 | 32 h | 1,6 h |
| EEVEE por **software**, 16 TAA, sin raytracing | 51,13 | 2100 MB | 0,870 | 22,8 dB | 104 % | **−6,7** | 256 h | 12,8 h |
| EEVEE por software, 16 TAA, con raytracing | 55,95 | 2175 MB | 0,876 | 23,1 dB | 103 % | −6,3 | 280 h | 14,0 h |
| Cycles 64 muestras (referencia) | 88,97 | 1235 MB | 1,000 | — | 105 % | 0 | 445 h | 22 h |
| **Godot Movie Maker** (GLB del visor, software)¹ | **0,16** | n/m | 0,63² | — | — | — | **0,8 h** | **2 min** |

¹ 90 fotogramas de la toma de grúa por Movie Maker (127 ms de render por fotograma). **No son los mismos 5 fotogramas**, usa el GLB liviano del visor (materiales planos, 39 luces sin sombras) y **memoria no medida**. ² SSIM contra Cycles producción, un solo fotograma (fachada).
**Los tiempos de EEVEE y Godot son de OpenGL emulado por CPU (Mesa llvmpipe): sobre una GPU real serían mucho menores, y no sé cuánto.** Los de Cycles sí son representativos del plan gratis de Actions.

## 4. Lo que se ve (imágenes en `comparaciones/`)

- **EEVEE con la escena sin adaptar:** más oscuro, **falta el resplandor rojo de la luz trasera** y los reflejos del asfalto mojado son más pobres; en la toma de la piscina **el agua se ve negra con un reflejo recortado** (el material con transmisión no se traduce). Brillo −6 a −7 niveles. No es «lo mismo, más rápido»: hay que rehacer materiales y luces.
- **Godot sin adaptar:** se parece en composición pero pierde el asfalto mojado, las sombras y la ciudad de fondo; SSIM 0,63. Es un borrador, no una película final, hasta portar materiales y luces.
- **Cycles «rápido»:** casi igual de lejos a simple vista pero **plástico**: el denoise FAST con 6 muestras borra las ondas del agua (detalle 80 %).
- **Cycles sin árbol de luces:** ahorra 25 % con una pérdida pequeña (SSIM 0,983 → 0,969, algo más de ruido residual). No es gratis, pero es la mejor relación calidad/tiempo medida **sin cambiar de motor**.

## 5. Las 10 ideas, una por una

| # | Idea | Veredicto |
|---|---|---|
| 1 | Rasterización en tiempo real | **Prometedora para borradores; no para la calidad actual sin portar la escena.** Godot: 0,16 s/fotograma aun por software. |
| 2 | Capturar el framebuffer de la GPU | Es lo que hacen EEVEE/Godot al renderizar; no hay un atajo aparte. La ganancia depende de **tener GPU**. |
| 3 | EEVEE y Godot Movie Maker | Ambos funcionan en servidor (`xvfb`). **EEVEE:** mismo pipeline Python, pero hay que adaptar materiales/luces (agua, resplandores). **Godot:** necesita un exportador de escena propio (hoy el GLB del visor pierde materiales); Movie Maker escribe AVI/PNG a tiempo fijo. |
| 4 | Lightmaps / iluminación precalculada | **No probado.** Encaja con esta escena (casi todo estático salvo auto y portón), pero el asfalto mojado, el vidrio y el agua dependen del ángulo de cámara y **no se pueden hornear**: sería un híbrido (luz horneada + reflejos en vivo). |
| 5 | PNG/JPEG vs. codificar directo con FFmpeg | **Irrelevante hoy:** guardar y codificar cuesta 0,1 % del render (20 ms contra 17.000 ms). Importaría sólo si el render bajara de ~0,5 s. |
| 6 | GPU alquilada y codificación por hardware | **La palanca más grande, no medida.** Acá `h264_nvenc` y similares figuran en FFmpeg pero no hay hardware. Precios de RTX 4090 entre US$ 0,2 y 0,9 la hora según el proveedor, con valores que no coinciden entre fuentes ([ejemplo](https://neurohive.io/en/guides/cloud-gpu-pricing/)). La codificación por hardware sería útil recién con render sub-segundo. |
| 7 | Reutilizar cálculos entre fotogramas | **Poco en este material:** 0 de 840 fotogramas idénticos. Lo realista: caché de luz horneada para lo estático (#4), o renderizar a 24 fps o con interpolación (no probado). |
| 8 | Paralelo por escenas | Ya existe (por toma). **Mejora segura:** repartir por **rangos de fotogramas** (p. ej. 20 trozos iguales) en lugar de por toma: el reloj pasa de «la toma más larga» a `CPU/20` (≈4,3 h para 10 min a producción). |
| 9 | Comparación vs. sistema actual | §3 y §4. |
| 10 | Motor de exportación cinematográfica | **Viable por etapas**, ver §7. |

## 6. Qué haría, en orden

1. **Ahora, sin riesgo (no toca el look):** repartir por rangos de fotogramas en Actions; y decidir si querés el ahorro de 25 % de «sin árbol de luces» (calidad algo menor, medida).
2. **Borrador instantáneo:** exportador de escena a Godot (materiales y luces reales) para encuadrar y revisar movimientos en segundos; Cycles sólo para la versión de revisión/final. Es trabajo de desarrollo, no una prueba.
3. **El salto real:** repetir **esta misma prueba de 5 fotogramas** en una GPU alquilada con Cycles GPU y EEVEE; recién ahí se sabrá si EEVEE (adaptando materiales) o Cycles en GPU es el camino, y cuánto cuesta una película.

## 7. Qué necesito de vos

- **Autorización y presupuesto** para alquilar una GPU unas horas (estimo menos de US$ 1 para la prueba de 5 fotogramas; no gasto nada ni abro cuentas sin tu OK). Tendrías que elegir proveedor o darme acceso.
- Decidir si seguimos por **(a)** ajustar Cycles + mejor reparto, **(b)** portar la escena a EEVEE/Godot para borradores, o ambas.

## 8. Límites de esta prueba

- **Sin GPU:** EEVEE y Godot se midieron emulados por CPU; no representan una GPU real. Cycles-GPU **no se midió**.
- Una sola escena (nocturna, con agua y asfalto mojado, que es difícil para los motores de rasterización).
- Godot: 90 fotogramas de otra toma, GLB de menor fidelidad, memoria no medida, un solo SSIM.
- Lightmaps, interpolación de fotogramas y render a menos FPS **no se probaron**.
- Calidad: métricas objetivas más mi vistazo a las imágenes; la decisión visual es tuya.
