# Prueba comparativa de resolución 001 — informe

**Fecha:** 14/11/2026 · **Estado:** prueba; **no se fijó ninguna resolución definitiva** (la decisión es tuya, después de revisar las imágenes).

> Siguiente prueba prevista: formato vertical 9:16 (TikTok, Instagram Reels, Facebook Reels).

## 1. Qué se hizo

- Escena de referencia: `p000_prueba_mansion` v1 (la ya producida y publicada). **No se reconstruyó ni se modificó**: el ejecutor (`ejecutar.py`) la arma con el mismo camino de código de producción (`director.construir(…, "revision")`) y **sólo cambia la resolución de salida** en memoria.
- Cuatro resoluciones, todas 16:9: 1280×720 (referencia), 1024×576, 960×540 y 854×480.
- Cinco momentos exactos de la escena (toma + número de fotograma), idénticos en todas las resoluciones → **20 imágenes comparables**.
- Dos pasadas por resolución (720→480 y 480→720) en procesos separados, en serie y sin otra carga en el equipo, para que el orden o el calentamiento no favorezcan a ninguna. Un render de calentamiento por proceso (carga de escena y BVH) se descarta y se informa aparte.
- **Las dos pasadas dieron imágenes idénticas píxel a píxel** (20 de 20: misma semilla; los archivos PNG difieren sólo por la fecha que Blender escribe en los metadatos). Es decir: toda diferencia entre resoluciones se debe a la resolución, no al azar del render.

## 2. Condiciones de la prueba

- Equipo: 4 núcleos lógicos, 16088 MB de RAM, **sin GPU**; Blender 5.3.0; equivalente a una máquina estándar de GitHub Actions.
- Render: CYCLES en CPU, **10 muestras**, denoiser OPENIMAGEDENOISE, muestreo adaptativo (umbral 0.05), 6 rebotes, transformación AgX (AgX - Medium High Contrast), exposición 1.1. Es la calidad «revisión» de producción, sin tocar nada.
- Escena: 417 objetos, 47 luces, 34 materiales. FPS declarados en el archivo: 30 (**no** son los FPS de render; ver §4).
- **Efectos conservados (ninguno se desactivó):** iluminación cinematográfica con 47 luces, sombras, reflejos en asfalto mojado y vidrios, agua de piscina animada, texturas procedurales (madera, piedra, ciudad de fondo con ventanas), vegetación instanciada (26 árboles y 70 arbustos), balizas y luces del jardín, cielo nocturno y animaciones (portón, garaje, auto).
- **Lo que esta escena NO tiene** (para no sobreestimar la prueba): no hay partículas, lluvia ni niebla volumétrica activas (`niebla = 0`), ni personajes. Esos efectos no se pudieron evaluar acá.

## 3. Momentos elegidos

Elegidos mirando vistas previas de baja calidad de 10 candidatos, **antes de medir**.

| # | Momento | Toma · tiempo · fotograma | Qué muestra |
|---|---|---|---|
| 1 | Plano general de la mansión | `t01_general` · 2.0 s · #61 | Toma 1 de la producción: casa, piscina, jardín, muro y ciudad de fondo. |
| 2 | Fachada e iluminación exterior | `t04_grua` · 14.0 s · #421 | Grúa baja: fachada de madera y vidrio, apliques, balizas y asfalto mojado. |
| 3 | Entrada del garaje | `t04_grua` · 17.4 s · #523 | Misma grúa, más alta: portón del garaje abierto, el auto frente a la entrada. |
| 4 | Piscina y reflejos | `t07_aerea` · 24.3 s · #730 | Toma aérea: piscina iluminada con su agua animada y reflejos sobre el deck. |
| 5 | Jardín, vegetación y luces | `t07_aerea` · 27.6 s · #829 | Aérea abierta: árboles, arbustos, camino de balizas y luces del jardín. |

## 4. Rendimiento medido

Media de las dos pasadas. «FPS reales» = fotogramas que el equipo **termina de renderizar por segundo** (no confundir con los 30 FPS declarados del video).

| Resolución | Píxeles vs 720p | s por fotograma | 5 fotogramas (s) | FPS reales de render | Tiempo vs 720p | CPU (proceso) | RAM pico | Calentamiento (s) |
|---|---|---|---|---|---|---|---|---|
| **1280×720 (referencia)** | 1.00× | **16.96** | 84.8 (A 85.2 · B 84.3) | 0.059 | 1.00× | 98 % | 1267 MB | 16.6 |
| **1024×576** | 0.64× | **11.29** | 56.5 (A 54.9 · B 58.0) | 0.089 | 0.67× | 98 % | 972 MB | 12.0 |
| **960×540** | 0.56× | **9.92** | 49.6 (A 48.5 · B 50.7) | 0.101 | 0.58× | 98 % | 914 MB | 10.1 |
| **854×480** | 0.45× | **7.55** | 37.7 (A 38.0 · B 37.5) | 0.133 | 0.45× | 98 % | 824 MB | 8.4 |

- **El costo es casi exactamente proporcional a los píxeles** (≈ 18.4–19.1 s por megapíxel en las cuatro): no hay un «punto dulce» escondido; bajar píxeles baja el tiempo en la misma proporción.
- **CPU:** ~98 % de los 4 núcleos en todas (el render está limitado por CPU y la usa entera). **GPU:** no disponible, no se usó.
- **Memoria:** pico de 824 MB (480p) a 1267 MB (720p); sobra RAM (16 GB). El 720p usa ~54 % más que el 480p.
- **Tiempo de render por segundo de video** (30 fotogramas): 720p 8.5 min · 576p 5.6 min · 540p 5.0 min · 480p 3.8 min de CPU de este equipo.
- **Una película de 10 minutos (18 000 fotogramas):** 720p ≈ 85 h de CPU · 576p ≈ 56 h de CPU · 540p ≈ 50 h de CPU · 480p ≈ 38 h de CPU. Repartida en los 20 trabajos simultáneos de GitHub Actions: 720p ≈ 4.2 h · 576p ≈ 2.8 h · 540p ≈ 2.5 h · 480p ≈ 1.9 h de reloj (sin contar montaje ni colas). Contraste: el render real de la mansión en Actions tardó 4,6 h de CPU para 840 fotogramas (≈ 19,7 s/fotograma), coherente con estas cifras.

## 5. Tamaño estimado de un video de 10 minutos

Método: se recodificó el video de producción (28 s, 720p) a cada resolución con los parámetros de producción (H.264, preset slow, CRF 22) y se extrapoló la tasa de bits. Como esa recodificación parte de un video ya comprimido, sale ~19 % más liviana que el archivo real; se **calibró** con el tamaño real del MP4 publicado (factor 1.233). Incluye audio AAC 192 kb/s (14,4 MB). Es una estimación (±25 %): depende del contenido (esta escena es oscura y con poco movimiento) y de la calidad CRF.

Todas las columnas incluyen el audio y están calibradas con el mismo factor.

| Resolución | CRF 19 (calidad «final») | **CRF 22 (producción «revisión»)** | CRF 26 (más compacto) | CRF 22 vs 720p |
|---|---|---|---|---|
| **1280×720 (referencia)** | ≈ 309 MB | **≈ 231 MB** | ≈ 110 MB | 1.00× |
| **1024×576** | ≈ 201 MB | **≈ 122 MB** | ≈ 70 MB | 0.53× |
| **960×540** | ≈ 180 MB | **≈ 110 MB** | ≈ 65 MB | 0.48× |
| **854×480** | ≈ 143 MB | **≈ 91 MB** | ≈ 56 MB | 0.39× |

## 6. Calidad visual

### 6.1 Medición objetiva (contra la referencia 1280×720)

- **SSIM** (1 = idéntica) y **PSNR** de cada imagen ampliada a 1280×720 (lo que verías en una pantalla de 720p); media de los 5 momentos.
- **Detalle fino conservado**: amplitud del detalle de alta frecuencia (laplaciano) vista a un mismo tamaño; 100 % = tanto detalle como el 720p.

| Resolución | SSIM vista a 720p | PSNR (dB) | SSIM en su propia resolución | Detalle fino (cuadro) | Detalle fino (zona de interés) | Detalle fino en la piscina |
|---|---|---|---|---|---|---|
| **1280×720 (referencia)** | 1.000 | — | 1.000 | 100 % | 100 % | 100 % |
| **1024×576** | 0.973 | 34.6 | 0.977 | 73 % | 73 % | 63 % |
| **960×540** | 0.972 | 34.1 | 0.976 | 68 % | 68 % | 52 % |
| **854×480** | 0.966 | 32.8 | 0.973 | 60 % | 59 % | 44 % |

**Cómo leerlo:** el SSIM de las tres bajas está en un rango muy estrecho (0,966–0,973) y **no ordena bien** 1024 y 960 (en la piscina y el jardín 960 sale apenas por encima, dentro del margen de la métrica). Lo que sí marca diferencias es el detalle fino: 1024×576 conserva ~3/4, 960×540 ~2/3 y 854×480 ~3/5 del detalle del 720p, y en la piscina cae a ~63 %, ~52 % y ~44 %.

**Validación de la prueba:** mi render de referencia de hoy contra los mismos fotogramas del video ya publicado da SSIM 0.955 a 0.977 (PSNR 37–41 dB): la diferencia es la compresión H.264 del MP4 y confirma que la prueba reproduce la producción.

### 6.2 Observación visual (mía, sobre las imágenes)

Mirando las 20 imágenes, los recortes al 100 % y las rejillas 2×2:

- **Lo que NO cambia con la resolución:** color, exposición, balance de luces, posición y dureza de las sombras, reflejos grandes sobre el asfalto
  mojado, brillo de las balizas y del portón, el resplandor de la piscina y la composición. A tamaño de pantalla completo, las cuatro versiones se ven
  muy parecidas; las diferencias son sutiles. No vi bandas de color, ruido nuevo ni artefactos distintos en los fotogramas fijos.
- **Lo que sí cambia es la nitidez del detalle fino**, en este orden de aparición:
  1. **Textura del agua de la piscina (momento 4):** es lo más sensible. En 720p se ven las ondas finas con destellos; en 1024×576 siguen visibles pero más
     tenues; en 960×540 el agua queda casi lisa; en 854×480 es lisa. (El brillo, el color y el reflejo de las luces siguen iguales.)
  2. **Ventanas de la ciudad de fondo (momento 1):** cada ventana encendida se distingue en 720p; en 960 y 854 se «pastan» y se funden entre sí.
  3. **Vidrio de la baranda del garaje (momento 3):** el moteado fino se pierde en 960 y 854; los bordes y la iluminación quedan igual.
  4. **Bordes y muro/madera de la fachada (momentos 1 y 2):** un poco más blandos al bajar; legibles en todas.
  5. **Jardín y vegetación (momento 5):** casi sin diferencia: la escena es oscura y tiene poco detalle de alta frecuencia que perder.
- Mis observaciones son sobre imágenes en una pantalla de computadora; no las miré en un teléfono.

## 7. Relación calidad · rendimiento · tamaño

| Resolución | Tiempo de render | Tamaño 10 min | SSIM | Detalle fino | Lo que se pierde (observado) |
|---|---|---|---|---|---|
| **1280×720 (referencia)** | 1.00× (85 h CPU) | ≈ 231 MB (1.00×) | 1.000 | 100 % | nada (referencia) |
| **1024×576** | 0.67× (56 h CPU) | ≈ 122 MB (0.53×) | 0.973 | 73 % | algo de textura fina en agua y vidrio; ventanas de la ciudad un poco más blandas |
| **960×540** | 0.58× (50 h CPU) | ≈ 110 MB (0.48×) | 0.972 | 68 % | textura del agua casi lisa; vidrio y muro más suaves; ventanas lejanas más pastosas |
| **854×480** | 0.45× (38 h CPU) | ≈ 91 MB (0.39×) | 0.966 | 60 % | agua lisa, bordes y ventanas lejanas claramente más blandos; lo grande (luces, sombras, reflejos, color) igual |

**Saltos entre escalones** (qué ganás y qué perdés al bajar un paso):

| Paso | Tiempo | Tamaño | SSIM | Detalle fino |
|---|---|---|---|---|
| 720p → 576p | −33 % | −47 % | -0.027 | -27 pts |
| 576p → 540p | −12 % | −10 % | -0.002 | -5 pts |
| 540p → 480p | −24 % | −17 % | -0.006 | -8 pts |

### Mi lectura (provisoria, para que la discutamos; no es una decisión)

- **Lo que pagás por cada paso hacia abajo:** de 720p a 1024×576 ahorrás un tercio del tiempo y casi la mitad del peso; de ahí a 960×540 otro ~12 % de
  tiempo y ~10 % de peso; y de 960×540 a 854×480 otro ~24 % de tiempo y ~17 % de peso. Cada escalón pierde más detalle fino, pero ninguno cambia el
  «look» cinematográfico (luces, color, sombras, reflejos).
- **960×540 es mi candidata provisoria a «mejor relación»:** ahorra ~42 % de tiempo de render y ~52 % de peso, conserva el aspecto completo de la imagen
  y es **exactamente la mitad de 1080p** (se amplía con un factor entero, 2×, sin remuestreo raro; en vertical sería 540×960 → 1080×1920). 1024×576 es el piso
  si querés conservar un poco más la textura del agua y el vidrio, a cambio de ~12 % más de render y de peso.
- **854×480 es la más rápida (−55 % de tiempo, −61 % de peso)**, pero ya se nota más blanda en el detalle fino (ventanas lejanas, agua, vidrio). Hoy la veo mejor
  como resolución de **borradores y revisión rápida** que como estándar de entrega, salvo que la prueba vertical muestre que en un teléfono no se aprecia.
- **Lo que pesa en la decisión y todavía no sé:** cómo se ven en un teléfono y después de la recompresión de TikTok/Reels/YouTube (pueden esconder o empeorar
  estas diferencias), y cuánto importa el agua/vidrio en tus películas. Por eso no fijo nada: **mirá los recortes de la piscina y de las ventanas de la ciudad** y decidí si
  esa pérdida te molesta.

## 8. Límites de esta prueba (qué NO demuestra)

- **Una sola escena**, nocturna y oscura: el detalle fino pesa menos que en una escena diurna o con mucha textura.
- **Sólo fotogramas fijos:** no se evaluó la estabilidad temporal (parpadeo del agua, brillos en movimiento), ni el efecto de la compresión de video sobre cada resolución.
- **No se probó en un teléfono ni en las plataformas** (TikTok, Reels, YouTube recomprimen y reescalan). Para el formato vertical 1080×1920 el video se amplía en el reproductor; eso se medirá en la prueba 9:16.
- Los tiempos son de **CPU de 4 núcleos con 10 muestras**; con GPU, más muestras o escenas más pesadas, las proporciones pueden cambiar. La proporcionalidad con los píxeles sí es robusta.
- El tamaño de video es una **estimación** (§5), no un video renderizado de 10 minutos.
- Mi «observación visual» es una opinión sobre las imágenes; la decisión de calidad es tuya.

## 9. Protección del proyecto y archivos

- No se modificó la producción original, la receta, el escenario ni `estudio/config.py`; no se eliminó ningún recurso. Todo vive en `pruebas/resolucion_001/`; los PNG sin pérdida quedan fuera de Git (`salida/pruebas/…`).
- Excepción deliberada a la regla «fotogramas no van a Git»: las 20 imágenes de revisión (JPEG, 1,6 MB en total) y las comparaciones (2,1 MB) sí se guardan acá porque son el entregable de la prueba.
- `ejecutar.py` (mide un render), `correr.py` (8 corridas), `analizar.py` (análisis), `informe.py` (este informe), `momentos.json`, `roi.json`, `resultados.json`, `medidas/` (crudo de cada pasada).

### Las 20 imágenes

| Momento | 1280×720 | 1024×576 | 960×540 | 854×480 | Comparación 2×2 | Recorte al 100 % |
|---|---|---|---|---|---|---|
| Plano general de la mansión | [1280x720](imagenes/1280x720/m1_plano_general.jpg) | [1024x576](imagenes/1024x576/m1_plano_general.jpg) | [960x540](imagenes/960x540/m1_plano_general.jpg) | [854x480](imagenes/854x480/m1_plano_general.jpg) | [2×2](comparaciones/m1_plano_general_2x2.jpg) | [detalle](comparaciones/m1_plano_general_detalle_pixeles_2x2.jpg) |
| Fachada e iluminación exterior | [1280x720](imagenes/1280x720/m2_fachada_exterior.jpg) | [1024x576](imagenes/1024x576/m2_fachada_exterior.jpg) | [960x540](imagenes/960x540/m2_fachada_exterior.jpg) | [854x480](imagenes/854x480/m2_fachada_exterior.jpg) | [2×2](comparaciones/m2_fachada_exterior_2x2.jpg) | [detalle](comparaciones/m2_fachada_exterior_detalle_pixeles_2x2.jpg) |
| Entrada del garaje | [1280x720](imagenes/1280x720/m3_entrada_garaje.jpg) | [1024x576](imagenes/1024x576/m3_entrada_garaje.jpg) | [960x540](imagenes/960x540/m3_entrada_garaje.jpg) | [854x480](imagenes/854x480/m3_entrada_garaje.jpg) | [2×2](comparaciones/m3_entrada_garaje_2x2.jpg) | [detalle](comparaciones/m3_entrada_garaje_detalle_pixeles_2x2.jpg) |
| Piscina y reflejos | [1280x720](imagenes/1280x720/m4_piscina_reflejos.jpg) | [1024x576](imagenes/1024x576/m4_piscina_reflejos.jpg) | [960x540](imagenes/960x540/m4_piscina_reflejos.jpg) | [854x480](imagenes/854x480/m4_piscina_reflejos.jpg) | [2×2](comparaciones/m4_piscina_reflejos_2x2.jpg) | [detalle](comparaciones/m4_piscina_reflejos_detalle_pixeles_2x2.jpg) |
| Jardín, vegetación y luces | [1280x720](imagenes/1280x720/m5_jardin_vegetacion.jpg) | [1024x576](imagenes/1024x576/m5_jardin_vegetacion.jpg) | [960x540](imagenes/960x540/m5_jardin_vegetacion.jpg) | [854x480](imagenes/854x480/m5_jardin_vegetacion.jpg) | [2×2](comparaciones/m5_jardin_vegetacion_2x2.jpg) | [detalle](comparaciones/m5_jardin_vegetacion_detalle_pixeles_2x2.jpg) |
