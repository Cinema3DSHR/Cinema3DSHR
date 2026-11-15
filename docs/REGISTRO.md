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

## 15/11/2026 — Video de 30 s «Infiltración» (mansión de día, soldados) — preparado, **bloqueado por ASSETS_TOKEN**

- Pedido: «otro de día con soldados». Producción `p004_mansion_dia_soldados`: 4 soldados (Ch49, Ch15, Ch35 de Extraction-tactical y el operador de Nexus)
  con fusil (M4A1 ×3, AK47 ×1) cruzan la calle, entran por el portón, corren por el camino, avanzan agachados junto a la fachada y se apilan
  frente a la puerta, que se abre. 8 tomas, 900 fotogramas. La escena se genera con `producciones/p004_mansion_dia_soldados/herramientas/generar_escena.py`
  (los recorridos usan ciclos enteros de clip; el script elige los ciclos que mejor llegan al punto).
- Nuevo en el estudio (sin tocar versiones publicadas): `estudio/blender/armas.py` (acopla el arma a la mano derecha y apoya la izquierda en el guardamanos,
  calibrado con la pose de apuntar; verificado a ojo con los 4 modelos en apuntar/caminar/correr), modelos `soldado:*`, modo `hora: "dia"` de la mansión
  (cielo, sol, sin luces nocturnas, pasto/asfalto claros), evento `abrir_puerta`, ambiente `dia_suburbio`.
- Error propio corregido: el centro de la palma se calculaba con la «cola» del hueso de la mano (el importador la inventa y mide metros) → ahora se usa
  hasta la base del dedo medio.
- Verificado: `validar` OK, 8 fijas revisadas, audio generado, 2 fotogramas reales a 6 muestras (≈13 s/fot., ≈130 s de armado). **No se corrió en Actions.**
- `video30.yml` ahora baja también recursos de Nexus y Extraction (parámetros `nombre`, variables `NEXUS_REF`/`EXTRACTION_REF`); `ASSETS_TOKEN` debe leer los 3 repos.

## 15/11/2026 — Video «Mansión CQB» 30 s (p005) — **ENTREGADO**

- Producción `p005_mansion_cqb_30s_720p_30fps`: entrada táctica de 4 operadores a un estudio de lujo, enemigo armado, intercambio de disparos, caída y aseguramiento. Escenario nuevo `estudio/escenarios/mansion_cqb.py` (pasillo, puerta que se abre de patada, estudio con biblioteca/escritorio/sofá, jardín visible por los ventanales), efectos `estudio/blender/efectos.py` (fogonazos por fotograma), giro suave del rumbo en `personajes.py` y audio procedural CQB con reverberación (`procedural.py`). Coreografía generada por `herramientas/generar_escena.py` (11 tomas, 65 disparos sincronizados).
- Render en Actions (corrida 43696801076): 900 fotogramas, 19 trabajos en paralelo, Cycles CPU 1280×720 30 fps 6 muestras, adaptativo 0,05, OIDN, 6 rebotes, árbol de luces, semilla 0. Reloj real 1592 s (26,5 min); render acumulado 16 348 s (18,2 s/fotograma de media, 10–27 s); RAM pico 1758 MB. Integridad: 900/900 sin faltantes ni duplicados.
- Entregables en la release `p005_mansion_cqb_30s_720p_30fps` (video.mp4 6,4 MB, audio.aac, informe.json, portada, miniatura, info). Los fotogramas quedaron sólo como artefactos temporales de Actions. Informe y huellas en `producciones/pruebas/mansion_cqb_30s_720p_30fps/`.
- Límites conocidos: el enemigo usa el modelo Ch49 (uniforme de otra época, lo diferencia pero desentona); en la reacción al impacto la mano izquierda suelta el arma unos 0,4 s; árboles y jardín de baja poligonación; el catálogo de la app lo muestra recién cuando esta rama se fusione a la rama por defecto y corra `catalogo.yml`.

## 15/11/2026 — EDITOR 3D / PREVISUALIZACIÓN (dirigir y aprobar antes del render)

- Pedido del dueño: etapa obligatoria de previsualización 3D interactiva con cámara libre, COLOCAR CÁMARA con
  coordenadas exactas, línea de tiempo, marcadores, chat de correcciones, versiones y aprobación antes del render.
- Estudio: `estudio/blender/previa.py` (GLB + línea de tiempo desde la MISMA escena del render, esqueletos y clips
  reales horneados), `estudio/blender/camara_director.py` (conversión Godot↔Blender), toma tipo `director` en
  `camaras.py`, `estudio/direccion.py` + comandos `previa`, `direccion`, `aplicar-direccion`; catálogo con `previa`.
- App: página `editor.gd` (vista 16:9, cámara libre táctil y de escritorio, montaje/tomas, línea de tiempo con
  0,25×–1,50× y cuadro a cuadro, personajes con su clip actual, objetos, propiedades, cámaras del director con
  renombrar/duplicar/borrar/comparar A/B, marcadores, mensajes al estudio, historial, versiones, GUARDAR CORRECCIONES
  y APROBAR ESCENA); `camara_director.gd`; envío por Issues `[DIRECCIÓN]` (con cola sin conexión).
- Flujos: `previa.yml` (exporta y publica; completa el OGV si falta), `direccion.yml` (guarda en `director/`),
  `video30.yml` bloquea el render final si la versión no está aprobada con la misma huella, `catalogo.yml` acepta rama.
- **Verificado:** ida y vuelta Godot→JSON→Blender 0,004 px máx. (23 cámaras), cámaras de rodaje exactas, caderas de los
  5 personajes a 0,07 mm de Blender; prueba visual del editor con la escena CQB (capturas); lógica del flujo de
  dirección (incluye rechazo de rutas maliciosas) y del bloqueo de render (5 casos). Error propio encontrado y
  corregido en la prueba: el GLB pone el cuadro f en f/fps (las cámaras móviles se desfasaban un cuadro).
- **No probado en un teléfono.** Detalle y límites en `docs/EDITOR_3D.md`.

## 15/11/2026 — App en vertical y horizontal (AJUSTES → PANTALLA)

- Pedido del dueño: usar la app en vertical y horizontal, elegible en configuración. AJUSTES → PANTALLA: HORIZONTAL,
  VERTICAL o AUTOMÁTICA (gira con el teléfono; `DisplayServer.screen_set_orientation`), guardado en `user://ajustes.json`.
- La interfaz se reacomoda sola al girar: en vertical la base pasa a 720×1280, la barra se compacta, PELÍCULAS y
  ESCENARIOS van en una columna, INICIO en fichas de 2, la página de escena pone el video arriba y el panel debajo, el
  EDITOR 3D pone la vista 16:9 arriba, los paneles debajo y la línea de tiempo al pie.
- Arreglos encontrados en la prueba: títulos largos de INICIO ensanchaban la página (en vertical se salía) y el aviso
  inferior salía corrido a la izquierda (también en horizontal, venía de antes).
- Verificado con capturas en ventana 720×1440 y 1600×900 (INICIO, AJUSTES, PELÍCULAS, EDITOR con la escena CQB).
  **No probado en un teléfono** (el giro real lo hace Android).

## 15/11/2026 — OPERACIÓN TREN FANTASMA (p006): física, cabinas y pilotos de Dream Rally; vía real

- Guion, desglose de 8 secuencias (600 s, 18.000 fotogramas), inventario con procedencia (555 recursos) y secuencia 1
  en construcción: `producciones/p006_operacion_tren_fantasma/`. Render final bloqueado hasta «APROBADO. INICIÁ EL
  RENDER FINAL DE LOS 10 MINUTOS» con la huella de las 8 versiones.
- **Física de Dream Rally** (pedido del dueño): `estudio/fisica_dr/` corre `vehicle_physics.gd` del juego tal cual en
  Godot sin cabeza con un conductor que sigue la trayectoria y hornea por cuadro carrocería, suspensión, ruedas,
  dirección, rpm y deslizamiento; caché versionada en `datos/fisica_dr/`. **Cabina y pilotos del juego**
  (`cockpit.gd`, `rig_pilot.gd`, `crew_motion.gd`) exportados como GLB animado con el mismo estado; vidrios del juego
  portados a Cycles (`vidrios_dr.py`). Detalle: `docs/FISICA_DREAM_RALLY.md`. Los blindados de s01 ya la usan.
- **Vía férrea real** (`estudio/blender/via_ferrea.py`): balasto de piedra, durmientes de quebracho con variación,
  rieles de perfil Vignole con banda pulida, placas, clips y tirafondos, eclisas cada 18 m, tendido telegráfico con
  crucetas, aisladores y 8 cables con catenaria, alambrado de 5 hilos, mojones y carteles km, señales luminosas,
  paso a nivel con cruces de San Andrés, línea de media tensión y delineadores en la ruta.
- **Paisaje** (`estudio/blender/paisaje.py`): parcelas cultivadas con surcos (alfalfa, trigo, arada, soja, rastrojo)
  y pastura en el corredor; los árboles de Sweet Home ganan copa sólida (de lejos eran palos) y material los que no
  tenían (pino, acacia).
- Arreglos encontrados al probar: el GLB del blindado tiene el largo en X (iba cruzado 80°: `giro_modelo`); durmientes
  y líneas de la ruta iban girados 90°; armar miles de piezas con bmesh era cuadrático (el armado de s01 pasó de >20 min
  a menos de 1 min); colores del campo en lineal; cielo físico más bajo (se lavaba todo).
- Previsualización de s01 para el EDITOR 3D: el GLB pasó de 252 a 64 MB (mallas reducidas una vez y compartidas, autos
  del juego con su versión `_lo` sólo en el visor, ruedas y ejes quietos en el visor, muestreo cada 3 cuadros en
  escenas de más de 60 s). Godot lo abre en 3 s. **No probado en un teléfono** (memoria: ~0,8 GB).
- La huella de las escenas nuevas (`"huella_v": 2`) incluye los módulos que importa el generador (física, vía,
  paisaje…): un cambio de código invalida la aprobación. Las escenas viejas conservan su huella.

## 15/11/2026 — Tren Fantasma: el salto (s03), los 28 autos y la música (pedido del dueño)

- **Regla del auto rampa** (dueño): salta UNA sola vez, al bajarse del acoplado del camión hasta el tren; después
  son los otros los que saltan sobre su cuña o salen volando. Guion y desglose corregidos (s02, s03, s05, s06).
- **s03 v1 «El salto»** (37,6 s de película, 31 s de acción): `estudio/blender/salto_tren.py`. Física real de
  Dream Rally en dos marcos móviles (el acoplado que viaja → la plataforma 9 del tren, cambio en pleno vuelo):
  despega a los 17,77 s, sube a 3,4 m, vuela 0,67 s, cae en la plataforma y frena detrás del deportivo amarrado.
  La cabina del juego con **Lucía y Mateo** (sus modelos sentados con la cinemática inversa y las fuerzas G del
  juego). **Cámara lenta ×4** (despegue, vuelo y aterrizaje en 8,8 s) con el nuevo `mapa_tiempo` de la escena
  (cámaras, render, sonido, previsualización y el EDITOR 3D de la app lo respetan). Tomas rígidas a la carrocería
  (interior, capó, rueda) que siguen cabeceo y rolido.
- Para que el salto sea limpio: el grabador ahora simula en marcos móviles, maneja con un camino dentro del marco,
  tiene rampas giradas y un faldón bajo los bordes (la física del juego calcula la pendiente con las 4 ruedas, también
  las del aire: un borde a pique la disparaba).
- **s01 v2**: los **28 autos de Dream Rally** en el tren (todos menos el Mamut, que es el camión) y una toma de
  **desfile**; **música épica** (ElevenLabs, 75 s + golpe del título) y **ambiente profesional procedural**
  (`estudio/audio/tren.py`: diésel de la locomotora, el «ta-tac» de cada eje en las juntas cada 18 m, rodadura,
  viento, teros, motores con las rpm reales de la física).
- ElevenLabs: s01 (música 75 s, golpe 10 s, bocina) y s03 (música 37,6 s, motor, aterrizaje, derrape): saldo
  32.973 → 31.850 créditos (1.123 en total; la música no informa costo en la respuesta y se cobra con atraso).
- Arreglos: cámaras de seguimiento con `retardo` 0 quedaban quietas; los protagonistas (FBX en centímetros) se
  sentaban a escala casi cero en la cabina; el arranque detenido con freno a fondo ponía reversa (el juego lo hace:
  se sostiene con el de mano).
- s03 dura 37,6 s (el desglose decía 80 s): se reparte al armar las secuencias 2 y 4. **Nada probado en un teléfono.**

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
