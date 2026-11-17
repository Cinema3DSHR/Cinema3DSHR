# Dúo Cero — Episodio 01: informe de tiempos y rendimiento (17/11/2026)

Fuente: corrida de prueba n.º 1 de «Episodio · render distribuido» (`episodio.yml`, run 44069629391): 19 trabajos × 6
fotogramas = 114 fotogramas repartidos en los 5 400 de la película. Configuración verificada en los 24 tramos: Cycles CPU,
960×540, 30 fps, 6 muestras, adaptativo 0,05, OpenImageDenoise, 6 rebotes, árbol de luces, semilla 0 fija, Blender 5.3.0.
Máquinas de GitHub: AMD EPYC 9V45, 4 núcleos. **No se lanzó el render completo.**

Marcas: **[M]** medido en GitHub · **[C]** cálculo con lo medido · **[E]** estimación sin medición (falta el dato).

## 1. Resultados de la prueba [M]

- 19 de 19 trabajos de render ejecutados, 19 sin error, sin reintentos. Los 19 arrancaron a las 10:58:04 (0 s entre el
  primero y el último): 19 simultáneos.
- Planificación 5 s (10:57:56–10:58:01). Recopilación + informe 12 s (11:06:29–11:06:41).
- Reloj total: 10:57:56 → 11:06:41 = **8 min 45 s**. Suma de los 21 trabajos: **96,1 min de máquina** (108 min con el
  redondeo por minuto que usa GitHub).

| trabajo | bloque | escenas | inicio–fin | total (s) | preparación (s) | armado escenas (s) | render 6 fotog. (s) | s/fotograma |
|---|---|---|---|---|---|---|---|---|
| 00 | 1–285 | e01 | 10:58:04–11:01:03 | 179 | 31 | 95 | 46 | 7,6 |
| 01 | 286–570 | e01 | –11:03:59 | 355 | 29 | 232 | 87 | 14,5 |
| 02 | 571–855 | e01 | –11:03:07 | 303 | 30 | 168 | 98 | 16,4 |
| 03 | 856–1140 | e01+e02 | –11:02:31 | 267 | 31 | 175 | 53 | 8,9 |
| 04 | 1141–1424 | e02 | –11:02:10 | 246 | 45 | 144 | 49 | 8,2 |
| 05 | 1425–1708 | e02 | –11:02:17 | 253 | 36 | 126 | 82 | 13,7 |
| 06 | 1709–1992 | e02 | –11:02:07 | 243 | 41 | 143 | 48 | 8,0 |
| 07 | 1993–2276 | e02+e03 | –11:05:09 | 425 | 29 | 302 | 85 | 14,1 |
| 08 | 2277–2560 | e03 | –11:03:30 | 326 | 41 | 191 | 83 | 13,8 |
| 09 | 2561–2844 | e03 | –11:04:37 | 393 | 30 | 253 | 104 | 17,3 |
| 10 | 2845–3128 | e03 | –11:04:50 | 406 | 40 | 252 | 105 | 17,5 |
| 11 | 3129–3412 | e03+e04 | –11:06:26 | 502 | 30 | 359 | 104 | 17,2 |
| 12 | 3413–3696 | e04 | –11:01:29 | 205 | 33 | 119 | 46 | 7,7 |
| 13 | 3697–3980 | e04 | –11:00:44 | 160 | 29 | 76 | 46 | 7,6 |
| 14 | 3981–4264 | e04+e05 | –11:05:13 | 429 | 37 | 289 | 93 | 15,5 |
| 15 | 4265–4548 | e05 | –11:03:00 | 296 | 31 | 179 | 78 | 13,0 |
| 16 | 4549–4832 | e05+e06 | –11:04:22 | 378 | 38 | 251 | 79 | 13,1 |
| 17 | 4833–5116 | e06 | –11:01:44 | 220 | 30 | 102 | 82 | 13,6 |
| 18 | 5117–5400 | e06 | –11:00:48 | 164 | 46 | 83 | 28 | 4,6 |

- Segundos por fotograma: promedio **12,2**, mediana 13,3, mínimo 3,4, máximo 20,7; primer fotograma de cada escena
  14,7 s (prepara la escena en memoria), los siguientes 11,6 s. RAM pico 2,8 GB de 16 GB.
- Preparación del trabajo (máquina + Blender + recursos de mixamo-respaldo): 29–46 s (promedio 35). Dentro de eso, la
  descarga de modelos y animaciones (checkout parcial) tarda ~4 s y la instalación de Blender ~17 s.
- Empaquetado: < 1 s. Subida: 1–2 s por trabajo (3,0–3,4 MB cada uno).
- Avisos sin efecto: la caché de texturas del vestuario la guardó un solo trabajo (los demás avisan «otro trabajo la está
  creando»); aviso de GitHub por Node 20. Ningún trabajo tardó más de lo previsto (el más largo, 8 min 22 s, armó 2
  escenas).

## 2. Por escena [M] y proyección [C]

| escena | fotogramas | s/fotograma (media; mín–máx entre trabajos) | armado (s, media; mín–máx) | minutos de máquina: optimista / realista / pesimista |
|---|---|---|---|---|
| e01 | 979 | 12,8 (7,6–16,4) | 165 (95–232) | 124 / 209 / 268 |
| e02 | 1 133 | 10,0 (8,0–13,7) | 138 (126–144) | 151 / 188 / 259 |
| e03 | 1 117 | **16,2** (13,8–17,5) | 232 (191–253) | 257 / 302 / 326 |
| e04 | 769 | **7,7** (7,6–7,7) | 98 (76–119) | 97 / 98 / 99 |
| e05 | 721 | 13,0 (un solo trabajo) | 179 | 156 / 156 / 156 |
| e06 | 681 | 9,1 (4,6–13,6) | 92 (83–102) | 52 / 103 / 154 |

La e03 (vagón con radio, primeros planos) es la más cara por fotograma y la e04 (salto, exteriores) la más barata.
Dentro de una misma escena el costo varía hasta 2× según la toma (en e01, la toma aérea 7,6 s y el interior 16,4 s).
Con sólo 6 muestras por trabajo, el margen de error por bloque es de ±15 % [E].

## 3. Proyección del render de 5 400 fotogramas [C]

Cada trabajo = preparación + armado de sus escenas + sus fotogramas × s/fotograma de esa escena + empaquetar y subir.
Manda el trabajo más lento (todos corren a la vez).

| escenario | criterio | trabajo más lento | promedio por trabajo | minutos de máquina |
|---|---|---|---|---|
| optimista | s/fotograma mínimo observado por escena | ~70 min | ~48 min | ~910 |
| realista | media por escena | **~82 min** | ~60 min | ~1 145 |
| pesimista | máximo por escena + 10 %, armado más lento, +90 s de transferencia | ~98 min | ~79 min | ~1 500 |
| control | s/fotograma propio de cada trabajo | ~89 min (trabajo 11) | ~62 min | ~1 185 |

Los trabajos más lentos son los de la e03 (08, 09, 10 y 11).

## 4. Tiempo total de producción (desde la autorización)

| # | etapa | tiempo | paralelo / secuencial | usa Actions | manual | estado |
|---|---|---|---|---|---|---|
| 1 | validación de recursos | 5 s [M] | secuencial | sí | no | hecho |
| 2 | descarga de modelos/animaciones/texturas | ~4 s + 17 s Blender [M] | paralelo (19) | sí | no | hecho |
| 3 | armado de las 6 escenas | 1,5–6 min por trabajo [M] | paralelo | sí | no | hecho |
| 4 | reparto de los 5 400 fotogramas | incluido en 1 [M] | — | sí | no | hecho |
| 5 | arranque de los 19 trabajos | ~3 s, 0 s de diferencia [M] | paralelo | sí | no | hecho |
| 6 | render | 70 / 82 / 98 min [C] | paralelo | sí | no | hecho (probado con 114) |
| 7 | empaquetado y subida (~150 MB por trabajo) | 0,5–1,5 min [E] | paralelo | sí | no | hecho |
| 8 | recopilación de los 19 bloques (~2,8 GB) | 1–3 min [E] | secuencial | sí | no | hecho (probado con 59 MB: 7 s) |
| 9 | verificación (5 400, sin faltantes ni repetidos) | < 30 s [E] | secuencial | sí | no | parcial: cuenta y repetidos sí; falta cortar si falta alguno |
| 10–11 | orden, ensamblado y MP4 30 fps 960×540 | 3–8 min [E] | secuencial | sí | no | **falta** (existe `pruebas/video_30s/montar.py` para una escena) |
| 12 | audio (voces, música, efectos ya generados) | 15–20 min [E] | paralelo con el render (puesto 20) | sí | no | **falta** para el episodio (existe por escena) |
| 13 | verificación del MP4 (duración, resolución, fps, audio) | < 1 min [E] | secuencial | sí | no | **falta** |
| 14 | publicación en una release | ~1 min [E] | secuencial | sí | no | **falta** |
| — | autorización (tu frase) | — | — | no | **sí** | hecho (el flujo la exige) |

## 5. Cronograma (reloj, contando el paralelismo)

| etapa | optimista | realista | pesimista |
|---|---|---|---|
| preparación (validación, arranque, máquinas, armado) | 3 min | 5 min | 8 min |
| renderizado (ya incluye armado y preparación de cada trabajo) | 70 min | 82 min | 98 min |
| transferencia (subida + recopilación) | 2 min | 3 min | 5 min |
| ensamblado y MP4 | 3 min | 5 min | 8 min |
| audio | 0 (en paralelo) | 0 (en paralelo) | 5 min (si se atrasa) |
| verificación | 1 min | 1 min | 2 min |
| publicación | 1 min | 1 min | 2 min |
| **TOTAL de reloj** | **~1 h 20 min** | **~1 h 35 min** | **~2 h 05 min** |

La preparación de cada trabajo ocurre dentro del renderizado (los 19 a la vez); la fila «preparación» es sólo el
arranque común. Con el reparto por costo (sección 7) el realista baja a ~1 h 15 min [C].

## 6. Consumo de GitHub

- Prueba [M]: 8 min 45 s de reloj; 96 min de máquina (108 min con redondeo).
- Render completo [C]: 910 / 1 145 / 1 500 min de máquina (+ ~30 min de planificación, audio y montaje [E]). En reloj son
  70–98 min, porque 19 máquinas corren a la vez y cada una cuenta sus propios minutos.
- **Costo: 0.** Cinema3DSHR es público y GitHub no cobra los minutos de las máquinas estándar ni el almacenamiento de
  artefactos en repositorios públicos. Si fuera privado, el plan Free trae 2 000 min/mes y 500 MB de artefactos: un
  episodio consumiría ~60–75 % de los minutos del mes y excedería el almacenamiento.
- Imágenes [C]: ~0,52 MB por PNG → ~2,8 GB los 5 400 (19 artefactos de ~150 MB, se borran solos a los 7 días).
- Transferencia: ~2,8 GB dentro de GitHub (subida y recopilación); a vos sólo te llega el MP4 (~60–120 MB [E]).
- Espacio para ensamblar: ~6 GB en la máquina de montaje (zips + PNG + MP4) de los ~14 GB libres que trae [E].
- Límites: 20 trabajos simultáneos del plan (19 de render + 1 de audio); 6 h por trabajo (el más lento, ~1,6 h); no hay
  riesgo de límites con esta configuración.

## 7. Cuellos de botella y optimizaciones (sin tocar la calidad)

- Domina el **render: ~85–90 % del reloj**; el armado de escenas es 2–6 min por trabajo, la transferencia y el montaje
  son minutos sueltos.
- Los bloques iguales en fotogramas no son iguales en trabajo: los de la e03 tardan ~82 min y los de la e04 ~40 min.
  1. **Reparto por costo medido** (bloques más chicos en e03 y e01, más grandes en e04 y e06): el reloj baja de ~82 a
     ~60 min en el escenario realista [C]. Es la mejora principal.
  2. Cortar los bloques en el borde de cada escena cuando se pueda: 4 trabajos se ahorran armar una segunda escena
     (1,5–4 min cada uno).
  3. Audio en el puesto 20, en paralelo al render.
  4. Caché de texturas del vestuario: ya guardada para las próximas corridas.
- No conviene: bajar muestras, resolución, rebotes o el denoiser (está fuera de lo acordado).

## 8. Qué puede fallar

- Una máquina más lenta que el resto (en la prueba, el armado de la misma escena varió de 95 a 232 s): el pesimista lo
  contempla.
- Que otro flujo ocupe puestos mientras corre (por ejemplo `render.yml`, que se dispara al subir un escena.json): no
  hacer push de escenas durante el render.
- Ensamblado, audio y publicación del episodio: todavía no están hechos ni probados.
- Falla de un trabajo: se reintenta sólo ese bloque (la corrida es reanudable por fotograma).
