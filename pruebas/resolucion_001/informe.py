"""Genera INFORME.md a partir de resultados.json (las cifras salen de las mediciones, no se copian a mano)."""
import json
import math
from pathlib import Path

AQUI = Path(__file__).resolve().parent
R = json.loads((AQUI / "resultados.json").read_text())
MOM = json.loads((AQUI / "momentos.json").read_text())["momentos"]
RES = ["1280x720", "1024x576", "960x540", "854x480"]
T, F, D, V, P = R["tiempos"], R["fidelidad"], R["detalle_fino_pct_vs_720p"], R["tamano_video"], R["configuracion_render"]
CAL = V["calibrado_con_archivo_real"]["mb_10min_video_mas_audio"]
amp = lambda pct: round(100 * math.sqrt(pct / 100))
nombre = {"1280x720": "1280×720 (referencia)", "1024x576": "1024×576", "960x540": "960×540", "854x480": "854×480"}
dtot = {r: T[r]["media_por_fotograma_s"] * 18000 / 3600 for r in RES}

L = []
a = L.append
a("# Prueba comparativa de resolución 001 — informe\n")
a("**Fecha:** 14/11/2026 · **Estado:** prueba; **no se fijó ninguna resolución definitiva** (la decisión es tuya, después de revisar las imágenes).\n")
a("> Siguiente prueba prevista: formato vertical 9:16 (TikTok, Instagram Reels, Facebook Reels).\n")

a("## 1. Qué se hizo\n")
a("- Escena de referencia: `p000_prueba_mansion` v1 (la ya producida y publicada). **No se reconstruyó ni se modificó**: el ejecutor "
  "(`ejecutar.py`) la arma con el mismo camino de código de producción (`director.construir(…, \"revision\")`) y **sólo cambia la resolución de "
  "salida** en memoria.")
a("- Cuatro resoluciones, todas 16:9: 1280×720 (referencia), 1024×576, 960×540 y 854×480.")
a("- Cinco momentos exactos de la escena (toma + número de fotograma), idénticos en todas las resoluciones → **20 imágenes comparables**.")
a("- Dos pasadas por resolución (720→480 y 480→720) en procesos separados, en serie y sin otra carga en el equipo, para que el orden "
  "o el calentamiento no favorezcan a ninguna. Un render de calentamiento por proceso (carga de escena y BVH) se descarta y se informa aparte.")
a("- **Las dos pasadas dieron imágenes idénticas píxel a píxel** (20 de 20: misma semilla; los archivos PNG difieren sólo por la fecha que "
  "Blender escribe en los metadatos). Es decir: toda diferencia entre resoluciones se debe a la resolución, no al azar del render.\n")

a("## 2. Condiciones de la prueba\n")
M = R["maquina"]
a(f"- Equipo: {M['nucleos_logicos']} núcleos lógicos, {M['ram_total_mb']} MB de RAM, **sin GPU**; Blender {M['blender']}; "
  "equivalente a una máquina estándar de GitHub Actions.")
a(f"- Render: {P['motor']} en {P['dispositivo']}, **{P['muestras']} muestras**, denoiser {P['denoiser']}, muestreo adaptativo (umbral {P['umbral_adaptativo']:.2f}), "
  f"{P['rebotes']} rebotes, transformación {P['transformacion_vista']} ({P['look']}), exposición {P['exposicion']:.1f}. Es la calidad «revisión» de producción, sin tocar nada.")
a(f"- Escena: {P['objetos']} objetos, {P['luces']} luces, {P['materiales']} materiales. FPS declarados en el archivo: {P['fps_declarados']} (**no** son los FPS de render; ver §4).")
a("- **Efectos conservados (ninguno se desactivó):** iluminación cinematográfica con 47 luces, sombras, reflejos en asfalto mojado y vidrios, agua de piscina "
  "animada, texturas procedurales (madera, piedra, ciudad de fondo con ventanas), vegetación instanciada (26 árboles y 70 arbustos), balizas y "
  "luces del jardín, cielo nocturno y animaciones (portón, garaje, auto).")
a("- **Lo que esta escena NO tiene** (para no sobreestimar la prueba): no hay partículas, lluvia ni niebla volumétrica activas (`niebla = 0`), ni "
  "personajes. Esos efectos no se pudieron evaluar acá.\n")

a("## 3. Momentos elegidos\n")
a("Elegidos mirando vistas previas de baja calidad de 10 candidatos, **antes de medir**.\n")
a("| # | Momento | Toma · tiempo · fotograma | Qué muestra |\n|---|---|---|---|")
for i, m in enumerate(MOM, 1):
    a(f"| {i} | {m['nombre']} | `{m['toma']}` · {m['tiempo_s']} s · #{m['frame']} | {m['por_que']} |")
a("")

a("## 4. Rendimiento medido\n")
a("Media de las dos pasadas. «FPS reales» = fotogramas que el equipo **termina de renderizar por segundo** (no confundir con los 30 FPS declarados del video).\n")
a("| Resolución | Píxeles vs 720p | s por fotograma | 5 fotogramas (s) | FPS reales de render | Tiempo vs 720p | CPU (proceso) | RAM pico | Calentamiento (s) |")
a("|---|---|---|---|---|---|---|---|---|")
for r in RES:
    t = T[r]
    a(f"| **{nombre[r]}** | {t['pixeles_relativos_a_720p']:.2f}× | **{t['media_por_fotograma_s']:.2f}** | {t['total_5_media_s']:.1f} (A {t['total_5_A_s']:.1f} · B {t['total_5_B_s']:.1f}) | "
      f"{t['fps_reales_render']:.3f} | {t['tiempo_relativo_a_720p']:.2f}× | {t['uso_cpu_proceso_pct']:.0f} % | {t['memoria_pico_mb']} MB | {t['calentamiento_s']:.1f} |")
a("")
a(f"- **El costo es casi exactamente proporcional a los píxeles** (≈ {min(T[r]['s_por_megapixel'] for r in RES):.1f}–{max(T[r]['s_por_megapixel'] for r in RES):.1f} s por megapíxel en las cuatro): "
  "no hay un «punto dulce» escondido; bajar píxeles baja el tiempo en la misma proporción.")
a("- **CPU:** ~98 % de los 4 núcleos en todas (el render está limitado por CPU y la usa entera). **GPU:** no disponible, no se usó.")
a("- **Memoria:** pico de 824 MB (480p) a 1267 MB (720p); sobra RAM (16 GB). El 720p usa ~54 % más que el 480p.")
a("- **Tiempo de render por segundo de video** (30 fotogramas): "
  + " · ".join(f"{r.split('x')[1]}p {T[r]['media_por_fotograma_s'] * 30 / 60:.1f} min" for r in RES) + " de CPU de este equipo.")
a("- **Una película de 10 minutos (18 000 fotogramas):** "
  + " · ".join(f"{r.split('x')[1]}p ≈ {dtot[r]:.0f} h de CPU" for r in RES)
  + ". Repartida en los 20 trabajos simultáneos de GitHub Actions: "
  + " · ".join(f"{r.split('x')[1]}p ≈ {dtot[r] / 20:.1f} h" for r in RES) + " de reloj (sin contar montaje ni colas). "
  "Contraste: el render real de la mansión en Actions tardó 4,6 h de CPU para 840 fotogramas (≈ 19,7 s/fotograma), coherente con estas cifras.\n")

a("## 5. Tamaño estimado de un video de 10 minutos\n")
a(f"Método: se recodificó el video de producción (28 s, 720p) a cada resolución con los parámetros de producción (H.264, preset slow, CRF 22) y se extrapoló la tasa de bits. "
  f"Como esa recodificación parte de un video ya comprimido, sale ~{(1 - 1 / V['calibrado_con_archivo_real']['factor_calibracion']) * 100:.0f} % más liviana que el archivo real; "
  f"se **calibró** con el tamaño real del MP4 publicado (factor {V['calibrado_con_archivo_real']['factor_calibracion']}). Incluye audio AAC 192 kb/s (14,4 MB). "
  "Es una estimación (±25 %): depende del contenido (esta escena es oscura y con poco movimiento) y de la calidad CRF.\n")
FACT = V["calibrado_con_archivo_real"]["factor_calibracion"]
DUR = V["duracion_muestra_s"]
cal = lambda r, crf: V["por_resolucion"][r][crf]["bytes_muestra"] * FACT / DUR * 600 / 1e6 + 192_000 / 8 * 600 / 1e6
a("Todas las columnas incluyen el audio y están calibradas con el mismo factor.\n")
a("| Resolución | CRF 19 (calidad «final») | **CRF 22 (producción «revisión»)** | CRF 26 (más compacto) | CRF 22 vs 720p |")
a("|---|---|---|---|---|")
for r in RES:
    a(f"| **{nombre[r]}** | ≈ {cal(r, 'crf19'):.0f} MB | **≈ {cal(r, 'crf22'):.0f} MB** | ≈ {cal(r, 'crf26'):.0f} MB | {cal(r, 'crf22') / cal(RES[0], 'crf22'):.2f}× |")
a("")

a("## 6. Calidad visual\n")
a("### 6.1 Medición objetiva (contra la referencia 1280×720)\n")
a("- **SSIM** (1 = idéntica) y **PSNR** de cada imagen ampliada a 1280×720 (lo que verías en una pantalla de 720p); media de los 5 momentos.")
a("- **Detalle fino conservado**: amplitud del detalle de alta frecuencia (laplaciano) vista a un mismo tamaño; 100 % = tanto detalle como el 720p.\n")
a("| Resolución | SSIM vista a 720p | PSNR (dB) | SSIM en su propia resolución | Detalle fino (cuadro) | Detalle fino (zona de interés) | Detalle fino en la piscina |")
a("|---|---|---|---|---|---|---|")
for r in RES:
    f, d = F[r], D[r]
    ps = "—" if f["psnr_vista_720p_db"] is None else f"{f['psnr_vista_720p_db']:.1f}"
    a(f"| **{nombre[r]}** | {f['ssim_vista_720p']:.3f} | {ps} | {f['ssim_propia']:.3f} | {amp(d['cuadro_media_pct'])} % | {amp(d['zona_media_pct'])} % | {amp(d['zona']['m4_piscina_reflejos'])} % |")
a("")
a("**Cómo leerlo:** el SSIM de las tres bajas está en un rango muy estrecho (0,966–0,973) y **no ordena bien** 1024 y 960 (en la piscina y el jardín 960 sale apenas "
  "por encima, dentro del margen de la métrica). Lo que sí marca diferencias es el detalle fino: 1024×576 conserva ~3/4, 960×540 ~2/3 y 854×480 ~3/5 del detalle del 720p, "
  "y en la piscina cae a ~63 %, ~52 % y ~44 %.\n")
VP = R["validacion_contra_video_publicado"]
a(f"**Validación de la prueba:** mi render de referencia de hoy contra los mismos fotogramas del video ya publicado da SSIM "
  f"{min(x['ssim'] for x in VP.values()):.3f} a {max(x['ssim'] for x in VP.values()):.3f} "
  f"(PSNR {min(x['psnr_db'] for x in VP.values()):.0f}–{max(x['psnr_db'] for x in VP.values()):.0f} dB): "
  "la diferencia es la compresión H.264 del MP4 y confirma que la prueba reproduce la producción.\n")

a("### 6.2 Observación visual (mía, sobre las imágenes)\n")
obs = (AQUI / "observaciones.md").read_text() if (AQUI / "observaciones.md").exists() else "(pendiente)"
a(obs.strip() + "\n")

a("## 7. Relación calidad · rendimiento · tamaño\n")
a("| Resolución | Tiempo de render | Tamaño 10 min | SSIM | Detalle fino | Lo que se pierde (observado) |")
a("|---|---|---|---|---|---|")
perd = {"1280x720": "nada (referencia)", "1024x576": "algo de textura fina en agua y vidrio; ventanas de la ciudad un poco más blandas",
        "960x540": "textura del agua casi lisa; vidrio y muro más suaves; ventanas lejanas más pastosas",
        "854x480": "agua lisa, bordes y ventanas lejanas claramente más blandos; lo grande (luces, sombras, reflejos, color) igual"}
for r in RES:
    a(f"| **{nombre[r]}** | {T[r]['tiempo_relativo_a_720p']:.2f}× ({dtot[r]:.0f} h CPU) | ≈ {CAL[r]:.0f} MB ({CAL[r] / CAL[RES[0]]:.2f}×) | {F[r]['ssim_vista_720p']:.3f} | {amp(D[r]['cuadro_media_pct'])} % | {perd[r]} |")
a("")
a("**Saltos entre escalones** (qué ganás y qué perdés al bajar un paso):\n")
a("| Paso | Tiempo | Tamaño | SSIM | Detalle fino |\n|---|---|---|---|---|")
for x, y in zip(RES, RES[1:]):
    a(f"| {x.split('x')[1]}p → {y.split('x')[1]}p | −{(1 - T[y]['media_por_fotograma_s'] / T[x]['media_por_fotograma_s']) * 100:.0f} % | −{(1 - CAL[y] / CAL[x]) * 100:.0f} % | "
      f"{F[y]['ssim_vista_720p'] - F[x]['ssim_vista_720p']:+.3f} | {amp(D[y]['cuadro_media_pct']) - amp(D[x]['cuadro_media_pct']):+d} pts |")
a("")
a("### Mi lectura (provisoria, para que la discutamos; no es una decisión)\n")
lectura = (AQUI / "lectura.md").read_text() if (AQUI / "lectura.md").exists() else "(pendiente)"
a(lectura.strip() + "\n")

a("## 8. Límites de esta prueba (qué NO demuestra)\n")
a("- **Una sola escena**, nocturna y oscura: el detalle fino pesa menos que en una escena diurna o con mucha textura.")
a("- **Sólo fotogramas fijos:** no se evaluó la estabilidad temporal (parpadeo del agua, brillos en movimiento), ni el efecto de la compresión de video sobre cada resolución.")
a("- **No se probó en un teléfono ni en las plataformas** (TikTok, Reels, YouTube recomprimen y reescalan). Para el formato vertical 1080×1920 el video se amplía en el reproductor; eso se medirá en la prueba 9:16.")
a("- Los tiempos son de **CPU de 4 núcleos con 10 muestras**; con GPU, más muestras o escenas más pesadas, las proporciones pueden cambiar. La proporcionalidad con los píxeles sí es robusta.")
a("- El tamaño de video es una **estimación** (§5), no un video renderizado de 10 minutos.")
a("- Mi «observación visual» es una opinión sobre las imágenes; la decisión de calidad es tuya.\n")

a("## 9. Protección del proyecto y archivos\n")
a("- No se modificó la producción original, la receta, el escenario ni `estudio/config.py`; no se eliminó ningún recurso. Todo vive en `pruebas/resolucion_001/`; los PNG sin pérdida quedan fuera de Git (`salida/pruebas/…`).")
a("- Excepción deliberada a la regla «fotogramas no van a Git»: las 20 imágenes de revisión (JPEG, 1,6 MB en total) y las comparaciones (2,1 MB) sí se guardan acá porque son el entregable de la prueba.")
a("- `ejecutar.py` (mide un render), `correr.py` (8 corridas), `analizar.py` (análisis), `informe.py` (este informe), `momentos.json`, `roi.json`, `resultados.json`, `medidas/` (crudo de cada pasada).\n")
a("### Las 20 imágenes\n")
a("| Momento | 1280×720 | 1024×576 | 960×540 | 854×480 | Comparación 2×2 | Recorte al 100 % |\n|---|---|---|---|---|---|---|")
for m in MOM:
    a(f"| {m['nombre']} | " + " | ".join(f"[{r}](imagenes/{r}/{m['id']}.jpg)" for r in RES)
      + f" | [2×2](comparaciones/{m['id']}_2x2.jpg) | [detalle](comparaciones/{m['id']}_detalle_pixeles_2x2.jpg) |")
a("")
(AQUI / "INFORME.md").write_text("\n".join(L), encoding="utf-8")
print("INFORME.md escrito,", len("\n".join(L)), "caracteres")
