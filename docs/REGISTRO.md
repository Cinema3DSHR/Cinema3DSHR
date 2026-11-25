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

## 15–16/11/2026 — Tren Fantasma SUSPENDIDA (pedido del dueño); recursos conservados

- Última tanda antes de suspender: s03 v2 (auto rampa marcha atrás, escolta volteada, rampa para el Bisonte al
  vagón 20 libre) y **batalla de escoltas** (`estudio/blender/batalla_s03.py`: Vortex, Veltor y Kodiak contra
  Cóndor T6, Pampero y KL5 con la física de Dream Rally; los embestidos siguen como cuerpo rígido). Fijas revisadas
  de la base v2; la batalla quedó sin fijas ni previsualización.
- Arreglos que quedan para la próxima película (Drift): la **cabina de Dream Rally sólo se ve en las tomas
  «interior»** de su auto (`director._cabinas_por_toma`; desde afuera asomaba por el techo, y el visor del teléfono
  ya no la lleva); **pilotos de las motos al derecho** (el piloto del juego mira a +Y en Blender); **árboles de
  Sweet Home con follaje real** (`paisaje.vestir`: racimos densos de hojas con forma y transparencia sobre las ramas
  del modelo); arranque andando en el grabador (`v_inicial`); motor «deportivo» en el sonido procedural.
- Ideas anotadas del dueño para Drift: sonidos de motor, aceleración y frenada **del propio Dream Rally**
  (`godot/tests/audio_render.gd` graba `car_audio.gd`; falta alimentarlo con la telemetría de la física).
- `producciones/p006_operacion_tren_fantasma/produccion.json` → `"estado": "suspendida"`. No se borró nada.

## 16/11/2026 — p007 «Al vacío»: Messi vs. Cristiano (previsualización publicada)

- El minijuego «Botón de caída» de Free Kick Swipe (s4muy3ni-lang/Free-Kick-Swipe) recreado y mejorado: 60 s
  verticales (9:16) sin HUD. Escenario `estudio/escenarios/al_vacio.py` (plataformas sobre el vacío, botón verde que
  se pone rojo con alarma, trampilla, torres de hierro, niebla, estadio con el público del juego, llamaradas, ascensor,
  papelitos). Física de la pelota contra tablero y botón (impacto ≥ 2,5 m/s, como el juego).
- Messi y Cristiano: modelos Tripo3D del dueño en `mixamo-respaldo/personajes_pelicula/` (autorizado a escribir);
  nombre «RONALDO 7» corregido proyectando la foto de referencia (`estudio/blender/proyectar_textura.py`, textura
  nueva). Animaciones del juego retargeteadas a Mixamo (`futbol:<clip>` con su root_path): remates (Cristiano diestro
  de empeine 0704/3352/3354; Messi zurdo con rosca 2258/2260), espera al costado de la pelota (STANCE 2,4 × 2,3 del
  juego; la trampilla ahí, el botón libre), entrada a la carrera como ShotCatalog, reacciones (enojos, provocaciones,
  lamentos), festejos de autor de gol; «Siu» y dedos al cielo armados con poses (el juego no los tiene).
- Dos finales: e01 gana Cristiano, e02 gana Messi. Audio: sonidos del juego + ElevenLabs (estimado 860 créditos).
- Previsualización publicada (previa.yml, corridas 9 y 10): las 7 pelotas, los dos jugadores, botones. **Sin render
  final**: espera la revisión del dueño en EDITOR 3D.

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

## 17/11/2026 — p009 «Dúo Cero — Episodio 01: Un minuto para saltar» (en construcción, sin render)

- Modelos del dueño (stickman.part1-3.rar): Stickman masculino (2 versiones de textura), femenino y pack de 19
  armas estilizadas. Esqueleto mixamorig de 65 huesos. Guardados en `modelos_subidos/stickman/` (fuente `subidas:`):
  escribir en mixamo-respaldo quedó bloqueado (sólo lectura) → **falta autorización del dueño** para agregarlos
  ahí y que Actions (previa/render) los vea.
- `estudio/blender/stickman.py`: vestuario pintado como las láminas (urbano, deportivo, táctico, elegante) en una
  textura nueva desde la posición de reposo de cada punto; pelo (casco + mechones; Luna con cola y pestañas); cara
  2D animada (ojos, brillo, párpados, cejas, boca, rubor) apoyada sobre la cabeza real con shape keys: 18
  expresiones, miradas, parpadeo y boca sincronizada con el audio de cada línea. Arma en mano, mochila, radio.
- `estudio/blender/armas_stickman.py`: armas del pack a su largo real, empuñadura y apoyo medidos, acople a la mano.
- `estudio/escenarios/duo_cero.py`: noche, sierra, zona industrial, tren de carga (frena junto a la zona de
  carga), vagón de los héroes armado a mano con la puerta abierta, base con torres y reflectores, zona de carga con
  coberturas y montículo de arena; el salto (Child Of + trayectoria balística + rodada); tiroteo
  (`estudio/blender/tiroteo.py`: trazadoras, chispas, sangre estilizada, casquillos).
- Voces ElevenLabs v3 con etiquetas de actuación, acento rioplatense (biblioteca compartida, agregadas a la
  cuenta): Nico «Tomas», Luna «Malena», guardia «Uriel», Central «Carlos». 57 líneas (~2 150 créditos) + 6 músicas.
- `producciones/p009_duo_cero/herramientas/`: `guion.py` (guion como datos; `plan()` ubica cada línea con su
  duración real y clava 180 s exactos con cámara lenta en el salto), `escenas.py` (e01–e06), `animatica.py`.
- Los push con escenas de Dúo Cero llevan `[skip ci]`: `render.yml` se dispara con cualquier escena.json nueva y
  renderizaría borradores (una corrida, la 23, se canceló a los 15 s sin renderizar).
- Peinados modernos a pedido: Nico con corte Kingsman (al costado, degradé y línea rapada), guardias con cresta y
  mohicano. Los Stickman del pack de armas no se usan (sólo las armas y la linterna).
- **Modelos definitivos (dueño, mismo día):** Stickman masculino y femenino proporcionados a Mixamo (0,98 m al
  importar), en `modelos_subidos/stickman/stickman_{masculino,femenino}_v2/`. El vestuario se lleva a las
  proporciones de los primeros por hitos de los huesos (`stickman.normalizar`); cara y pelo se apoyan en la cabeza real.
- Arreglos: fundido entre clips en pistas NLA (las de arriba sólo sostienen hacia adelante: antes Nico y Luna
  quedaban «sentados en el aire»); el retarget dejaba una posición sin clave en los huesos que no son la cadera y se
  acumulaba (el cuerpo de Nico terminaba a kilómetros del esqueleto y no salía en cámara); cámaras de la escena 4
  medidas sobre las cabezas reales.
- Render distribuido del episodio (`episodio.yml`, `pruebas/episodio/`): 5 400 fotogramas en 19 bloques parejos,
  configuración verificada (960×540, Cycles 6 muestras, adaptativo 0,05, OIDN, 6 rebotes, árbol de luces, semilla 0).
  Prueba de 114 fotogramas (run 44069629391): 19/19 simultáneos y sin error, 8 min 45 s, 12,2 s/fotograma; proyección
  del episodio ~82 min de render (70–98). Informe: `docs/informes/duo_cero_ep01_tiempos.md`. La animática local quedó
  cancelada (sin GPU no es viable).
- **Sin render final**: espera «APROBADO. INICIÁ EL RENDER FINAL DE DÚO CERO — EPISODIO 01».

## 17/11/2026 — REGLA PERMANENTE: revisión 3D en la app y AUTORIZACIÓN antes de cualquier render

- Pedido del dueño: nunca un render sin revisar la versión en 3D en la app, aprobarla y autorizarla. Procedimiento y
  estados en `docs/REVISION_Y_AUTORIZACION.md`; regla agregada a `CLAUDE.md`.
- Ya existía: EDITOR 3D (previsualización real, cámara libre, montaje, tomas, cuadro a cuadro, marcadores, notas, cámaras
  del director, ✔ APROBAR atada a la huella) y el candado de `video30.yml`.
- Nuevo: `estudio/autorizacion.py` (8 estados, verificación única), comando `autorizacion`, botón 🎬 AUTORIZAR RENDER
  FINAL y estado de la versión en el editor, aprobación/autorización sólo con la escena cargada completa, con la huella
  actual y con conexión; catálogo con `estado_revision`, `autorizacion` y la configuración de render de la producción.
- Cerrado: `render.yml` ya no renderiza solo al subir un escena.json; `video30.yml` sin interruptor para saltear la
  aprobación ni ensayos sin autorización; `episodio.yml` la exige también para una escena y los ensayos; RENDERIZAR desde
  la app ya no renderiza; `render`/`fijas`/animática/render_rango/render_bloque se niegan sin registros; scripts viejos
  de medición deshabilitados.
- Arreglado por la transferencia: «Revisiones» y «Dirección» sólo aceptaban Issues del dueño del repo (ahora la
  organización), así que ignoraban los de la cuenta del director → lista `config/autorizados.json` / variable AUTORIZADOS.
- `p009` `produccion.json`: configuración de render = la acordada por el dueño (960×540, 30 fps, 6 muestras, …).
- Pruebas (sin render): `pruebas/autorizacion/test_autorizacion.py` 35/35; app con la previsualización real de e01
  (`pruebas/revision/revision_ui.gd`) 18/18.

## 17/11/2026 — App: en vertical no respondía ningún botón (arreglado, APK nueva época 2)

- Causa: la app arrancaba bloqueada en horizontal (orientación 4) y para pasar a vertical forzaba el giro en marcha
  (`DisplayServer.screen_set_orientation`); además el aviso de cambio de tamaño no siempre llegaba al rotar y la app
  seguía armada en horizontal dentro de una pantalla vertical. En la PC funcionaba; en el teléfono no.
- Arreglo: el proyecto pasa a orientación «sensor» (6, Android rota la app solo), sin forzar el giro en marcha; la app
  revisa el tamaño real en cada cuadro y se reacomoda; AJUSTES ya no tiene los botones HORIZONTAL/VERTICAL.
  `apk_epoca` 2: hace falta instalar la APK nueva (la orientación está en el manifiesto de Android).
- Pruebas con toques de pantalla táctil (sin teléfono): `pruebas/app/toques_rotacion.gd` 7/7 (horizontal → vertical →
  horizontal), `pruebas/app/toques_vertical.gd` 6/6 (barra y EDITOR 3D en vertical), revisión 18/18. No se pudo probar
  en un teléfono real desde acá.

### 17/11/2026 13:23 UTC — Sonda de 60 trabajos: sigue limitada, cancelada
- Pedido del dueño: «probá los 60 trabajos; si no funciona cancelá todo y esperamos la respuesta de GitHub».
- `concurrencia.yml` con 60 trabajos de `sleep 120` (sin render), corrida 44092060314: a los 13 s había **9 corriendo y
  51 en cola** (lejos de 60). Cancelada a las 13:23 UTC; no queda ninguna corrida activa. Agregada al ticket
  (`docs/informes/ticket_github_concurrencia.md`). Se espera la respuesta de GitHub Support antes de repetir nada.

### 17/11/2026 14:41 UTC — Sonda de 60 trabajos completa: máximo 11 simultáneos
- Pedido del dueño: «probá una vez más», y después «dejala terminar y agregá el resultado al ticket».
- `concurrencia.yml`, 60 trabajos de `sleep 120` (sin render), corrida 44103430911, 14:28–14:40 UTC: los 60 bien, en
  tandas de ~10; **máximo 11 a la vez** (trabajo `medir`), el último arrancó 627 s después del primero. Con 60 reales
  habría tardado ~2 min, no 12. Agregado al ticket (`docs/informes/ticket_github_concurrencia.md`). Sigue la espera de
  la respuesta de GitHub Support; no se lanza ningún render.

### 18/11/2026 01:05 UTC — Respuesta de GitHub Support y nueva sonda: 13 simultáneos, cancelada
- Support: período de arranque de 7 días para cuentas nuevas; el límite de concurrencia sube solo a medida que terminan
  trabajos (como mucho cada 10 min). Era 11 al responder.
- Sonda de 60 trabajos (corrida 44212957289): 13 corriendo a la vez y 47 en cola → cancelada (el dueño pidió cancelar si
  no superaba 20). No se renderizó nada.

## 18/11/2026 — p010 «Un sueño de a dos»: personajes humanos (en preparación, sin render)

- Accesos de la sesión: GitHub (rama `claude/inspiring-sagan-1ogr0n`) y ElevenLabs (credencial cargada por el dueño
  en el entorno; saldo 24.376 créditos de 40.000, renueva el 13/12/2026).
- Voces: 4 voces es-AR de la biblioteca compartida agregadas a la cuenta (gratis) y una muestra de cada una con una
  línea del guion (eleven_v3, ~418 créditos estimados): ÉL Aiden / Antonio, ELLA Kate / Hellen
  (`config/voces.json`, roles `*_es_ar`). **Falta que el dueño elija.**
- Personajes nuevos del dueño (Tripo, mixamorig, blancos y SIN rostro), guardados sin tocar en
  `../modelos_subidos/un_sueno_de_a_dos/` (fuente `subidas:`). Para que Actions los use hace falta copiarlos a
  mixamo-respaldo (**pedir autorización**: es sólo lectura).
- `estudio/blender/humanos.py` (modelos `humano:chico` y `humano:chica`): piel con dispersión subsuperficial,
  rostro dibujado, pelo esculpido, ropa y zapatos; se arma desde `personajes.crear` como los Stickman.
- `estudio/blender/cara_anime.py`: el sistema de caras de los Stickman con dibujo «anime realista» (pedido del
  dueño, en lugar de las expresiones 3D, que descartó): ojos en capas (blanco en almendra, iris con anillo y pupila
  recortados por los párpados, dos brillos, línea del párpado con cola, pestañas en ella, línea de abajo, pliegue),
  cejas afinadas, nariz sugerida, labios con interior y dientes, rubor. Mismas formas clave que los Stickman, así
  sirven sus 18 expresiones, la boca con la voz, las miradas y el parpadeo (`stickman.actuar`). Proporciones medidas
  sobre el perfil de cada maniquí (ojos a media cabeza, nariz y boca en los tercios de la cara).
- `estudio/blender/pelo_esculpido.py`: pelo «de arcilla» (pedido del dueño): casco con surcos + mechones gruesos
  modelados; él: jopo texturizado hacia adelante y costados cortos; ella: tirante a un rodete de tres mechones
  enroscados y mechones que enmarcan la cara. Vaivén con formas clave (se ve también en el EDITOR 3D).
- `estudio/blender/ropa_humana.py`: prendas como cáscaras alisadas sobre el cuerpo (no marcan músculos) que siguen
  al esqueleto, con la piel tapada borrada: buzo con capucha caída, bolsillo canguro, cordones con punteras y puños
  acanalados; campera de jean abierta con cuello, bolsillos con tapa, botones y costuras naranjas; remera; jeans con
  costuras, bolsillos traseros con remaches, presillas y botón; zapatillas armadas sobre la horma del pie (suela de
  goma, franja, cordones, lengüeta); cartera cruzada de cuero, aros y reloj.
- Descartado en el camino (el dueño no lo quiso): cabeza injertada de MakeHuman con 59 expresiones 3D y pelo de
  miles de hebras. Errores propios corregidos: el corte del cuello calculaba el mentón con los pies; el árbol de
  búsqueda del cuerpo no tenía normales y la ropa quedaba pegada a la piel; normales invertidas del maniquí.
- Prueba (sin render): `pruebas/personajes_humanos/armar.py` arma cada personaje y exporta un GLB como la
  previsualización; `vista.gd` lo mira en el visor OpenGL de Godot (el de la app). Capturas enviadas al dueño.
- Autos subidos por el dueño (Golf GTI, Golf R, Audi RS3): son mods de GTA V (.yft/.ytd/.rpf), formato que el
  estudio no puede abrir; hace falta exportarlos (OpenIV/CodeWalker → FBX/OBJ) o conseguirlos en GLB/FBX.
- Guion como datos: `producciones/p010_un_sueno_de_a_dos/herramientas/guion.py`. Falta: escenario de la
  concesionaria, escenas, voces elegidas y previsualización 3D. **Sin render.**

## 18/11/2026 (tarde) — Cambio de historia: serie espacial; personajes humanos con cabeza MakeHuman

- El dueño cambió la historia: serie espacial (un hombre a la deriva en el espacio, una IA que le habla desde las
  computadoras de la nave; él y ella quieren volver a la Tierra y se van enamorando). Voces: Aiden (él) y Kate (ella)
  (`config/voces.json`, roles `aiden_es_ar` y `kate_es_ar`). La concesionaria de «Un sueño de a dos» queda sin hacer.
- Descartado a pedido del dueño: la cara dibujada estilo anime y el pelo esculpido (quedan en el historial de Git).
- `estudio/makehuman.py` + `estudio/blender/cabeza_mh.py`: cabeza de MakeHuman (CC0) TAL CUAL (hombre o mujer por
  defecto, sin retoques), escalada entera para un cuerpo de la altura del maniquí y apoyada en la base de su cuello;
  el cuello se funde con el del cuerpo; el corte del maniquí respeta los trapecios. Ojos (córnea transparente, iris
  del color del personaje), dientes, lengua, boca por dentro, pestañas y cejas de pelitos, piel pintada por zonas.
- `estudio/blender/expresiones_3d.py`: 59 unidades de expresión de MakeHuman + parpadeo completo; expresiones con
  los nombres de los Stickman, microexpresiones, mirada con sacádicos, labios con la voz (ruta relativa al repo).
  Error de Blender 5 encontrado: una forma clave nueva arranca con peso 1 (la cara salía con todo aplicado) → 0.
- Pelo: `estudio/blender/pelo_modelo.py` pone los pelos que subió el dueño (escala, ubicación, nada adentro de la
  cabeza ni del cuerpo, textura teñida con transparencia, pesos cabeza → espalda). Él: «hair02» (el único corto).
  Ella: «SummerGirl» (largo, suelto, con flequillo; el más femenino: el Bob deja ver el cuero cabelludo y el Daisy
  es de nodos de pelo, no se ve en el teléfono). Los archivos están en `../modelos_subidos/un_sueno_de_a_dos/pelos/`.
  `estudio/blender/pelo_realista.py` (hebras guía + hijas, guía del dueño) queda como alternativa.
- Traje de primera piel (`ropa_humana.traje_primera_piel`): una pieza pegada al cuerpo con pie tipo media, vivos de
  color, cierre corto, rodilleras y coderas, parche en el pecho y cuello alto que tapa la unión con la cabeza y queda
  siempre por debajo de la mandíbula.
- Visor de prueba: `pruebas/personajes_humanos/vista.gd` (vistas de cara, 3/4 de los dos lados, nuca y cuello).
  Hallazgo: las capturas desde un solo lado engañaban (parecía que faltaba medio pelo).
- Sin render. Falta: autorización para copiar modelos y pelos a mixamo-respaldo (Actions), los trajes espaciales, la
  nave, el robot/IA y el guion del primer episodio.

## 18/11/2026 (noche) — Vuelta a la cabeza original del maniquí con caras Stickman realistas

- Decisión del dueño: cabeza ORIGINAL del maniquí + cara dibujada estilo Stickman realista (`cara_anime.py`,
  recuperado del historial) + los pelos modelados que ya quedaban bien (hair02 él, SummerGirl ella) + traje de
  primera piel. La cabeza MakeHuman con expresiones 3D queda guardada como alternativa (`cabeza_mh.py`,
  `expresiones_3d.py`), igual que el pelo de hebras (`pelo_realista.py`). Las cabezas «free_head» y «BustBaseMesh»
  que mandó el dueño no traen expresiones (sólo forma); no se usaron.
- `humanos._cabeza_propia`: malla auxiliar de la cabeza del maniquí para encajar el pelo y medir la mandíbula.
- Traje: no sube a la cabeza; cuello alto más bajo adelante y cierre que arranca en el cuello (antes en el mentón).

## 18/11/2026 (noche) — Caras más reales y expresiones «Stickman cinematográfico»

- Pedido del dueño: caras menos largas (mucho mentón) y las expresiones de sus láminas «Stickman cinematográfico –
  híbrido realista» (neutro, feliz, sorpresa, preocupado, enojado, triste), más reales.
- `humanos.esculpir_cara`: acorta la parte de abajo de la cara (de los ojos al mentón, 17 %) y lleva el mentón un
  poco atrás, sólo adelante y con transición al cuello (cambia la malla en reposo; esqueleto y animaciones igual).
- `cara_anime`: alturas de ojos, cejas, nariz y boca medidas en cada cabeza con proporciones humanas (`_alturas`;
  error propio corregido: el «mentón» se tomaba en el cuello y la boca quedaba fuera de la cara); ojos más redondos
  con iris oscuro grande y brillos; cejas gruesas redondeadas; formas nuevas: ojos «triste», cejas «feliz»/«triste»,
  boca en D con dientes y lengua, «o» de sorpresa, enojo y preocupada; tabla `EXPRESIONES` propia (las seis de las
  láminas + las de los Stickman) usada por `cara_anime.actuar`.
- Prueba: las capturas tomaban el cuadro 1, con la expresión a mitad de su transición (se veía floja); ahora el 20.
- Pendiente visto en las capturas: en la sonrisa abierta de ella los dientes se ven cortados de un lado.

## 18/11/2026 — «A la deriva» E01 (p011): set de la nave, voces y escena (previsualización local, sin render)

- Documento del dueño: `producciones/p011_a_la_deriva/E01_documento_produccion_v1_1.txt`. p010 queda «descartada».
- Set único y reutilizable `estudio/escenarios/nave_deriva.py`: cielo panorámico generado (estrellas, Vía Láctea,
  nebulosas), Tierra con nubes y atmósfera, planeta gigante con anillos, luna, Sol; la nave por fuera (módulo de
  mando con ventanal, cuerpo, módulo de Kate, alas solares, motores, antena, luces de navegación que titilan); el
  centro de operaciones (ventanal con vidrio y nervios, consola curva con teclados, monitores de trayectoria,
  telemetría y comunicaciones, energía/combustible, núcleo de EVA que late con su voz, pantalla del módulo de Kate
  que pasa a «COMUNICACIÓN SIN RESPUESTA», silla de oficina de Sweet Home retapizada, caños, cables, gabinetes, luces
  ámbar/rojas, puerta y pasillo). Pantallas dibujadas con Pillow (agregado a requirements). Todo dentro de 700 m.
  Error propio corregido: las esferas sin capa UV exportaban la textura con texCoord −1 (cielo negro en el visor).
- Voces: EVA = «Alma» (elegida por el dueño), Aiden = «Aiden»; 14 líneas con marcas de tiempo por letra
  (`/with-timestamps`, `elevenlabs.ruta_alineacion`) → `cara_anime._labios_por_letra`. Narradora guardada para otros
  capítulos: «Veronica» (`narradora_deriva`). Gasto: ~1.208 (voces) + ~880 (EVA con Alma) + ~357 (muestras de EVA)
  + música (85 s) y un efecto; saldo informado 22.558 (ElevenLabs descuenta con atraso).
- Escena `escenas/e01/v1` (`herramientas/escenas.py`): 11 tomas 9:16, Aiden sentado de espaldas (Mixamo sentado),
  eventos `eva_habla`, `estado_kate`, `luces_navegacion`, ambiente `nave_interior` (`estudio/audio/nave.py`),
  efecto de montaje `fundido_negro`. Validada. **Dura 88,5 s**: los diálogos del documento, a ritmo natural, ocupan
  ~67 s (el documento pide 60 s): decisión del dueño.
- Previsualización hecha en el contenedor y probada con `pruebas/revision/revision_ui.gd` (18/18; la prueba pedía 2
  personajes y este episodio tiene 1) y capturas por toma (`pruebas/nave/tomas.gd`). **No publicada**: `previa.yml`
  necesita los modelos y pelos en mixamo-respaldo (autorización del dueño pendiente). Sin render.
- Con autorización del dueño («copialos a mixamo-respaldo y publicala»): los maniquíes (chico, chica, con sus `.fbm`)
  y los pelos `hair02` y `summer_girl` quedaron respaldados sin modificar en mixamo-respaldo,
  `personajes_pelicula/a_la_deriva/` (rama `claude/inspiring-sagan-1ogr0n`, hecha sobre `ccr-6d21fe8a-76t9c3`;
  hashes en `indice_personajes.json`). `humanos.py` y `pelo_modelo.py` los leen de ahí (`mixamo:`), `blender_deps`
  los declara para Actions, `nave_deriva.DEPENDENCIAS` declara la silla de Sweet Home y `previa.yml` acepta la
  entrada `mixamo_ref` (rama del respaldo). Huella nueva de e01/v1: `f7e399b32f6f0463`.
- **Previsualización publicada** con «Previsualización 3D» (corrida n.º 17, `mixamo_ref=claude/inspiring-sagan-1ogr0n`,
  en verde: exportó, publicó en la release de la producción y rearmó el catálogo). Antes se armó igual en el
  contenedor sin la carpeta de subidas (todo desde mixamo-respaldo) y pasó `revision_ui.gd` 18/18. Espera la revisión
  del dueño en EDITOR 3D. Sin render.

## 18/11/2026 — La app rechazaba APROBAR con «código 307»

- Causa: el repositorio ya está en la organización (`Cinema3DSHR/Cinema3DSHR`) y la app seguía usando
  `webmaletin-art/Cinema3DSHR`. Las lecturas siguen por la redirección de GitHub, pero crear el pedido (POST) recibe
  307 y la app lo tomaba como rechazo. Corregido `REPO` en `app/main/api.gd`, `app/boot/boot.gd` y
  `estudio/config.py` (paso 13 de `docs/MIGRACION_ORGANIZACION.md`). La clave del token guardado sigue con el nombre
  viejo (`REPO_CLAVE`) para no pedirlo de nuevo. Prueba de la app 18/18. La APK salió como PRUEBA con firma
  temporal (artefacto `3DFilmStudio-PRUEBA-firma-temporal-v7`, corrida 44276199602): en el repositorio movido no está
  el secreto `ANDROID_KEYSTORE_PASSWORD` ni la release `app`, así que no hay actualización automática; hay que
  instalarla a mano. El dueño pidió «renderizalo» por chat: no se renderiza hasta que APROBAR + AUTORIZAR salgan desde la app.

## 18/11/2026 — A la deriva E01 v2: cámara del director (pedido #5)

- El dueño aprobó v1 desde la app (#6, ya funciona con la dirección nueva del repositorio) y pidió una cámara que
  muestre un poco la cara (#5, «01 ver cafa», t06_reflejo, 49,63–52,63 s). El flujo «direccion» falló porque corre
  en la rama por defecto, donde p011 todavía no está: la cámara se guardó igual que lo hace el flujo en
  `producciones/p011_a_la_deriva/director/cameras/camera_001.json` y se aplicó con `aplicar-direccion` → **v2**
  (huella `61228e9425de750c`). Único cambio fuera de los números: la cámara se estiró a 52,77 s para tapar un resto
  de 0,14 s (4 cuadros) de la toma vieja antes de t07. Comprobado en la captura: Aiden de tres cuartos, cara a la
  vista. La aprobación de v1 no vale para v2. Prueba de la app 18/18. Sin render.

### 18/11/2026 — Guía para otro chat de Claude
- Pedido del dueño: un documento para que otro chat aprenda a trabajar en la organización sin auditar los repositorios.
- `docs/GUIA_PARA_OTRO_CHAT.md`: dueño y trato, repositorios y permisos, reglas (sobre todo la de render), mapa del
  estudio y de los flujos, recetas, estado actual (Dúo Cero, concurrencia, app), cómo atender pedidos típicos y
  pruebas. `CLAUDE.md` la nombra como punto de partida.

### 18/11/2026 — Respaldo completo de lo enviado por el chat + inventario de recursos en la guía
- Pedido del dueño: «subí todo y actualizá el documento así tiene esos recursos nuevos (helicópteros, los nuevos
  personajes)».
- Revisado todo lo que mandó por el chat: helicóptero y los otros 12 GLB, auto rampa, protagonistas, Messi, Cristiano,
  Stickman definitivos y armas Stickman YA estaban en mixamo-respaldo; Sweet Home está en Nexus. Faltaban y se
  agregaron (mixamo-respaldo `2e62ee5`, sólo agregados): `personajes_pelicula/versiones_anteriores/stickman_*_v1`
  (primera tanda, no usar) y `futbol_free_kick_swipe/01_animaciones/json_originales/` (2 023 clips JSON de Fútbol 5).
- `docs/GUIA_PARA_OTRO_CHAT.md` § 4 bis: inventario de recursos (personajes, vehículos con el helicóptero y cómo se le
  ponen los rotores, decorados, otros repos y recursos del estudio).

### 18/11/2026 — Pack Sweet Home 3D respaldado en mixamo-respaldo
- Comparado archivo por archivo: los 723 GLB y `models.json` del pack que mandó el dueño están idénticos en Nexus
  (`game/assets/sh3d`), pero faltaban las 723 miniaturas y el README. Se guardó el zip original completo, sin
  modificar, en `mixamo-respaldo/sweethome3d/` (`9739149`, con LEEME y sha256). La guía lo explica (§ 4 bis).

## 18/11/2026 — Por qué no aparecía AUTORIZAR RENDER FINAL

- El APROBAR de la pantalla de inicio de la app manda la aprobación SIN huella (#7, #8), y el verificador sólo cuenta
  las que llevan la huella de la versión. La del EDITOR 3D sí la lleva (sale de la previsualización). Además, cada
  pedido desde la app rearma el catálogo desde la rama por defecto, donde p011 no estaba. El «RENDERIZAR» (#9) es el
  botón viejo y ya no renderiza.
- Con autorización del dueño: la rama de trabajo se fusionó en `ccr-6d21fe8a-76t9c3` (fusión normal; antes se trajeron
  sus 3 commits de guías) y en mixamo-respaldo `ccr-6d21fe8a-76t9c3` se avanzó con la carpeta `a_la_deriva` (sólo
  agrega archivos), que es la que leen los flujos de render. Catálogo rearmado: e01 v2 «EN REVISIÓN».

## 18/11/2026 — A la deriva E01 v2: render final autorizado (60 trabajos)

- El dueño aprobó (#12) y tocó AUTORIZAR RENDER FINAL (#13) en el EDITOR 3D: v2, huella `61228e9425de750c`,
  1280x720 (vertical → 720x1280), 30 fps, 6 muestras, Cycles CPU. `autorizacion.estado` = RENDER AUTORIZADO.
- `episodio.yml` no sirve (fijo en 960x540 y sin recursos de Nexus: la silla). Se usa `video30.yml`, ajustado:
  hasta 60 trabajos (la organización), `render_rango.py` acepta el 720p vertical, `montar.py --escena` aplica el
  fundido a negro de la última toma (antes se perdía) y los entregables salen con la versión real (`e01_v2_*`, antes
  fijo `e01_v1_*`). Configuración de Cycles sin tocar.
- **Render terminado** (corrida 44285010355, `video30.yml`, 59 trabajos): 2.655/2.655 fotogramas, sin faltantes,
  sobrantes ni repetidos; 720x1280, 88,5 s, audio AAC 48 kHz; fundido a negro final comprobado (luminancia 16 en el
  último segundo). 21,9 s por fotograma de media (13–15 min por trabajo de 45). Publicado en la release
  `p011_a_la_deriva` (`e01_v2_revision.mp4/.ogv`, portada, miniatura, info, informe) y catálogo rearmado.
- Incidentes: la organización sólo dio 19–20 trabajos simultáneos aunque la página de Runners muestra «19/60» (causa
  no confirmada; desde esta sesión no se ven los ajustes de la organización). 13 trabajos se cancelaron juntos a las
  10:43:55–10:44:06 sin error del render (GitHub los cortó; coincide con cambios del dueño en la organización) y el
  reparto quedó congelado hasta las 10:52. Con autorización del dueño se usó «Re-run failed jobs» (intento 2): los 13
  y el montaje salieron bien. Reloj total ~1 h 55 min.


### 18/11/2026 — Visor de escenas en HTML (revisión rápida en el navegador)
- Pedido del dueño: revisar las escenas en el navegador del celular con un GLB liviano, sin Godot ni esperar a la app, y
  pedir cambios de cámara por el chat.
- `visor/visor_escena.html` (+ `visor/LEEME.md`), publicado también para el teléfono en
  https://claude.ai/artifact/SEW8AN7eTVhb1t3vaRAvJq. Abre el GLB (+ JSON) de `previa`; MONTAJE / TOMA / LIBRE, cuadro a
  cuadro, cortes de toma, 📍 MARCAR y COPIAR PARA CLAUDE con la cámara en coordenadas de Blender.
- Probado con la previsualización real de e01 v1 en Chromium con pantalla de Pixel 7: carga (12 cámaras, 12 tomas,
  32,6 s), reproduce, el montaje cambia de cámara, cuadro a cuadro, y la cámara copiada coincide con la de Blender
  (≤ 4 mm). No probado en un teléfono real.
- No se tocó ningún flujo ni lo que corre en Actions (video30 de A la deriva en marcha).
- Segunda vuelta (pedido del dueño: «recorrer la escena y colocar cámara, y que el HTML me dé el texto con dónde, en qué
  minuto y en qué ubicación»): LIBRE para recorrer (1 dedo mira, 2 dedos acercan/corren, cruceta, rapidez), «Pegada a»
  (arranca pegada a lo que lleva la cámara de la toma: en e01, el vagón `tren_06_cerrado`, que se mueve) y
  🎥 COLOCAR CÁMARA, que copia al instante la orden (desde/hasta, qué toma reemplaza, fija o movimiento, pose respecto
  del vagón y en el mundo en Blender, lente). Probado con e01: la pose relativa coincide con el `desp_local` de t05 y no
  cambia entre 13,2 s y 14,5 s; la del mundo coincide con Blender.
- Tercera vuelta (pedido del dueño: moverse libre, un botón de cámara que la agregue al texto, poder modificar las
  cámaras ya puestas y agregar otras, y sólo COPIAR): ➕ CÁMARA NUEVA, ✏️ EDITAR CÁMARA DE LA TOMA, EDITAR en cada
  cámara de la lista (lo que se mueve mientras edita queda en la orden, con el cambio en palabras), conos rojos y un único
  📋 COPIAR PARA CLAUDE (JSON `estudio.visor_ordenes/2`). Probado con e01: editar t05 (subirla, lente 32 → 45 mm),
  moverse sin editar no la cambia, cámara nueva en t08; sin errores de la página.
- `docs/VISOR_Y_ORDENES_DE_CAMARA.md`: cómo funciona el visor, cómo pasarle el GLB al dueño por el chat y cómo recibir y
  aplicar el texto `estudio.visor_ordenes/2` (quieta → toma `director`; pegada al vagón → toma rígida con ancla y
  objetivo; modificar = aplicar el cambio). Enlazado desde `CLAUDE.md` y `docs/GUIA_PARA_OTRO_CHAT.md`.
- Candado del render: el dueño pidió sacarlo; queda para cuando termine el `video30` de A la deriva (en curso,
  corrida 44285010355), para no tocar nada mientras corre.

### 18/11/2026 12:3x UTC — Candado del render QUITADO (pedido del dueño)
- Terminado el video30 de A la deriva (corrida 44285010355, 12:19, éxito) y sin renders en curso.
- `config/candado_render.json` `"activo": false` + `estudio/autorizacion.candado_activo()`: `verificar` y `exigir` dejan
  pasar con «candado del render QUITADO por el dueño»; los flujos (`render.yml`, `video30.yml`, `episodio.yml`) y los
  comandos ya no piden APROBAR/AUTORIZAR en la app. La lógica queda: con `"activo": true` vuelve todo.
- Pruebas sin render: `pruebas/autorizacion/test_autorizacion.py` 40/40 (las de la regla corren con CINE_CANDADO=1 y
  hay 5 nuevas del modo sin candado).
- CLAUDE.md, REVISION_Y_AUTORIZACION.md, GUIA_PARA_OTRO_CHAT.md y VISOR_Y_ORDENES_DE_CAMARA.md actualizados. Claude
  sigue sin renderizar por iniciativa propia.

## 18/11/2026 — A la deriva: configuración de los próximos capítulos (pedido del dueño)

- E01 v2 le gustó al dueño. Desde E02: **540×960 vertical, 30 fps, MP4 H.264, Cycles 6 muestras** (mismos parámetros),
  hasta 60 trabajos; duración según los diálogos (2 min o más). Nueva calidad `hd540` en `estudio/config.CALIDADES`
  (960x540; con `"vertical": true` sale 540x960). `video30.yml` y `render_rango.py` ya no están fijos en 720p: usan la
  calidad de la escena (la verificación también). Audio AAC 320 kbps (antes 192). Anotado en
  `producciones/p011_a_la_deriva/produccion.json` → `render_capitulos`.
- Revisión de cada escena: GLB liviano + JSON para el visor HTML por el chat (`python -m estudio previa`), sin render.
  Candado del render quitado por el dueño (otro chat): se renderiza cuando él lo pide en el chat.

## 18/11/2026 — «A la deriva» E02 «Una flor en el vacío» v1 (previsualización para el visor, sin render)

- Documento Maestro v2 del dueño. Guion como datos: `herramientas/guion_e02.py` (28 líneas, voseo; «Keit» en la voz);
  voces con marcas por letra (Aiden, EVA = Alma, Kate = kate_es_ar). Música: dos piezas (botánico y final) + ambiente
  del invernadero + aviso del mensaje. Gasto: ~1.355 (voces) + 820 (música y efectos); quedan 21.664.
- Escenario nuevo `nave_deriva_ampliada` (el E01 no cambia): centro de operaciones → pasillo → **pasillo botánico**
  (12 incubadoras de vidrio con 16–22 flores procedurales cada una, `estudio/blender/flores.py`: 7 especies, todas
  distintas, se mecen con el aire; raíces en el agua, sustrato, gotas en el vidrio, luz de cultivo) → **comedor**
  (mesas largas, banquetas, estanterías con comida sellada, botellas, ventanal, plantas en maceta de Sweet Home). El
  monitor del puesto muestra la cámara del comedor; la tablet de Kate escribe «Gracias por la flor» letra por letra.
  Sin casco exterior (sus tapas atravesaban los pasillos).
- Utilería de mano en mano (`despues_personajes`): la flor bandeja → mano de Aiden → mesa → mano de Kate → mesa; la
  botella consola → mano izquierda → mesa. Posiciones medidas con la mano real del clip (Taking_Item).
- Traje: se borra la piel que queda debajo (con margen en cuello y muñecas): ya no asoma en pecho ni brazos.
  Kate: expresiones nuevas `conmovida`, `ruborizada`, `sonrisa_contenida` (rubor progresivo).
- Lección: un tramo de caminata que se corta antes de terminar sus repeticiones deja al siguiente donde habría
  terminado (personajes.py): las caminatas se planifican en ciclos enteros (`escenas_e02.py`).
- e02 v1: 133,3 s, 31 tomas, calidad `hd540` (540x960). `pruebas/nave/tomas.gd` ahora aplica la visibilidad del
  JSON. Prueba de la app 18/18. GLB (29 MB) + JSON enviados al dueño para el visor.

## 18/11/2026 — Mejora del sistema: componentes, escena de trabajo, recursos y biblioteca de clips (sin render)

- Pedido del dueño tras rechazar la caminata de E02 v1 (Walking_2 = «Male Drunk Walk»: el catálogo lo decía y no se
  consultó). Detalle completo en `docs/SISTEMA_COMPONENTES.md`.
- A · Protección: `estudio/proteccion.py` + `producciones/p011_a_la_deriva/escenas/e02/v1/entregado.json` (huellas de
  la receta y del GLB/JSON entregados); `MF.escribir` y los armadores de p011 se niegan a sobrescribir lo entregado.
  E02 v1 no se modificó: receta, GLB y JSON intactos (verificado por sha256). No existía un .blend de E02: el sistema
  armaba todo en memoria en cada previsualización.
- B · `estudio/componentes.py`: la receta dividida en tiempo, escenario, personaje:*, despues, camara:*, render,
  sonido (+ vehículos y pelota) con dependencias y huellas; `python -m estudio componentes`.
- C · `config.ruta_recurso` (rutas relativas a `CINE_RAIZ`; las absolutas viejas de Dúo Cero se resuelven sin editar
  sus recetas) y `estudio/recursos.py` (`validar --recursos`): si falta un audio, sus marcas de tiempo o un recurso
  externo, la preparación se detiene (antes la boca se movía con sílabas del texto sin avisar). Encontró un error
  real: `DEPENDENCIAS` de `nave_deriva_ampliada` no era una lista literal (Actions no la podía leer).
- D/E · `estudio/blender/trabajo.py` + `python -m estudio trabajo construir|actualizar [--previa]`: escena de trabajo
  guardada fuera de Git (`CINE_TRABAJO`); rehace sólo cámaras, personajes, utilería o render afectados; una versión
  nueva hereda la escena de la anterior. El director se partió en fases (mismo resultado: E01 v2 rearmada da caderas,
  cámaras y tomas idénticas). Las pruebas encontraron y se corrigieron: fps del FBX (24) si se partía el cierre;
  cachés de retargets y materiales con referencias borradas; la colección «personajes» excluida al rehacer.
- F · Previsualización desde la escena de trabajo sin modificarla (sha256 igual antes y después); biblioteca de clips:
  `clips buscar` por descripción, `clips ficha` (esqueleto en 8 momentos, Pillow, no es render), aviso de clips con
  estilo marcado en `validar --recursos` (E02 v1: Walking_2 borracho, Walk_To_Stop «llevando a alguien»,
  Shake_Gesture «Big Vegas»). Reemplazos neutros revisados con sus fichas: Standard_Walk, Stop_Walking,
  annoyed_head_shake.
- Pruebas: `pruebas/sistema/test_componentes.py` 16/16 (sin Blender); `pruebas/sistema/test_trabajo.py` 19/19
  (Blender, sin render); `pruebas/autorizacion/test_autorizacion.py` 40/40. Actions no se tocó.
- Migración de E02: no hay .blend que migrar; hace falta UN armado completo de una copia de trabajo (≈8 min, sin
  render) — pendiente de autorización del dueño. Desde ahí, la corrección de la caminata en una v2 rehace sólo a Aiden,
  la utilería y sus 10 cámaras (el escenario de flores y comedor no), si los nuevos clips frenan en los mismos lugares.

## 18/11/2026 — «A la deriva» E02 v2: Aiden con clips neutros, por componentes (sin render, sin Actions)

- Autorización del dueño: armar la copia de trabajo y entregar la previsualización de la v2 (no el render).
- v2 = la v1 con SÓLO las acciones de Aiden cambiadas (`herramientas/e02_v2.py`): Standard_Walk, Stop_Walking,
  annoyed_head_shake y, por pedido del dueño, Breathing_Idle en lugar de Bored (brazos en péndulo: las manos recorrían
  0,87 m; ahora 0,12 m). Mismos lugares y segundos que la v1 (la mano cae en la bandeja en el mismo punto, ±2 cm).
  Elegidos por su descripción y revisados con sus fichas (`clips ficha`, con el recorrido de manos medido).
- Tiempos: copia de trabajo de v1 482 s (escenario 28, personajes 376, utilería y muestreo 73, cámaras 0,3);
  actualización final de v2 459 s (personajes 377, utilería y muestreo 76, cámaras 0,2); exportar la previa 96 s.
  El escenario (flores y comedor) y las otras 21 cámaras NO se rehicieron. Kate se rehízo porque cambió el código
  común de personajes (arreglos de abajo); quedó idéntica a la v1 (diferencia 0,0000 m).
- Arreglos del motor de caminatas encontrados al verificar (afectaban también a la v1: la cadera saltaba ~1,7 m):
  (1) la clave de sostén de la raíz a 0,01 cuadros se fundía con ciclos fraccionarios; (2) los clips que avanzan ahora
  se usan «en el lugar» y la raíz avanza continua (los fundidos mezclaban caderas de raíces distintas); (3) el
  comienzo de cada tramo se sigue sosteniendo (si no, la raíz giraba durante la espera previa a un corte). Prueba
  `pruebas/sistema/test_caminata.py` 4/4; `test_trabajo.py` 19/19; `test_componentes.py` 16/16; revisión de la app 18/18.
- Huellas: los imports dentro de funciones ya no se siguen (el escenario «dependía» de personajes por stickman); la
  escena de trabajo guarda el sha de cada archivo de código y `trabajo.reestampar` recalcula huellas sólo si el código
  de esos componentes no cambió (usado una vez, con constancia en el estado).
- Entregado: `e02_v2_previa.glb` + `.json` (huellas en `escenas/e02/v2/entregado.json`). E02 v1 intacta (verificada).

## 18/11/2026 — «A la deriva» E02 v3: la tablet de Kate arriba de la mesa (reconstrucción completa)

- El dueño: el mensaje no se veía porque la tablet estaba metida en la mesa (borde 3–4 cm bajo la tapa). Ahora está
  sobre un soporte (pata trasera y tope), el borde de abajo 2,8 cm sobre la mesa; ancla `pantalla_kate` subida.
- Se evaluó y se ABANDONÓ, por pedido del dueño, la migración del escenario a «piezas» independientes (no quedó nada de
  ese intento en el repo). Lo anterior del sistema incremental sigue como estaba.
- v3 (copia de v2 con `nueva-version`) reconstruida entera: 439 s de escena + exportación (526 s en total). Capturas:
  la tablet se ve y el mensaje «Gracias por la flor» se lee (tomas 28–31). Revisión de la app 18/18. Entregado:
  `e02_v3_previa.glb` + `.json` (`escenas/e02/v3/entregado.json`). v2 intacta (verificada). Sin render ni Actions.

## 18/11/2026 — «A la deriva» E02 v3: render final (60 trabajos) y montaje

- Render autorizado por el dueño en el chat: `video30.yml`, corrida 44361974666, 540x960, 30 fps, Cycles 6 muestras,
  60 trabajos (hasta 31 a la vez; 16–24 min cada uno). 59/60 bien; el trabajo 30 se cortó en el fotograma 2063
  («sin toma»: hueco de un cuadro entre t18 y t19 por redondeo) y su paso terminó en verde igual. Arreglado
  `render_rango.py` (usa la cámara de la toma anterior, como Blender). Se relanzó el render completo y el dueño lo
  canceló: pidió armarlo «así nomás».
- Flujo nuevo «Montar una corrida ya renderizada» (`montar_corrida.yml`, autorizado por el dueño): corrida 44378165497
  armó el video con los fotogramas de 44361974666, rellenando 2063–2077 (15 cuadros, medio segundo) con el 2062.
  Informe: 3.998/3.998 fotogramas, 540x960, 133,27 s, audio AAC 48 kHz. Publicado en la release `p011_a_la_deriva`
  (`a_la_deriva_e02_v3.mp4`, `e02_v3_revision.mp4/.ogv`, portada, miniatura, info, `e02_v3_fotogramas_rellenados.json`).

## 19/11/2026 — Prueba técnica Godot → Blender: casa moderna en tormenta (sin render, sin Actions)

- Toma de 30 s, 540x960, 30 fps, un solo movimiento de cámara de derecha a izquierda: cocina → mesas → ventilador →
  ventanal con la calle, farolas y lluvia → relámpagos → hogar. A pedido del dueño, el jardín se cambió por la CÓNDOR
  Kodiak Raid de Dream Racing (`kodiak.glb`, la camioneta con el arco de hierro en la caja), estacionada de cola al
  ventanal entre dos farolas. El RAR del mod de GTA no se pudo usar (formato RPF y licencia).
- Godot 4.7.2: escena armada por scripts, una etapa por archivo (`pruebas/godot_blender/godot/herramientas/e1…e4`).
  Queda `escena/casa_tormenta.tscn` editable. GLB exportado con GLTFDocument.
- Blender 5.3: importación y correcciones generales (`pruebas/godot_blender/blender/b6…b9`, `armar.py`) →
  `casa_tormenta.blend` con Cycles preparado con los parámetros hd540.
- Resultados, tiempos reales por etapa (≈25 min en total), lo que pasó y lo que se rehízo, problemas de compatibilidad
  y costo estimado del render (5–10 h de CPU, 15–25 min de reloj con 60 trabajos): `pruebas/godot_blender/INFORME.md`.
- Previa liviana: captura en tiempo real del visor de Godot (no es Cycles), 8 MB, más un GLB liviano de 2 MB.
- GLB, .blend, previa y proyecto comprimido se mandaron por el chat (no van a Git). No se hizo ningún render ni se usó
  Actions.
- Render ordenado por el dueño en el chat («renderizala con 60 trabajos a 720p»): flujo nuevo
  `render_prueba_godot_blender.yml`. Arma todo desde cero en un trabajo (Kodiak de Rally-Sim-movile main → Godot → GLB
  → Blender), reparte los 900 cuadros en 60 trabajos a 720x1280, 6 muestras (`blender/render_trozo.py`), y monta y
  publica el MP4 en la release `prueba_godot_blender`.
- El dueño corrigió la orden a 540p (lo entregado). La corrida 44463973456 (720p) se canceló durante la preparación,
  antes de renderizar. **Render terminado**: corrida 44464073661, 540x960, 6 muestras, 60 trabajos, 900/900 cuadros
  sin faltantes. Preparación 1,5 min, 21,75 s por cuadro de media, 14 min de reloj de punta a punta (05:17 → 05:31 UTC).
  Publicado: release `prueba_godot_blender` (`casa_tormenta_540p.mp4`, `informe_render.json`). Visto: el fuego
  volumétrico sale tenue (se ven más las brasas que las llamas); para la próxima prueba hay que subirle la emisión.

## 19/11/2026 — Limpieza general: el repositorio queda dedicado a «A la deriva»

Pedido del dueño: dejar sólo «A la deriva» (p011), las herramientas comunes del pipeline, los flujos, la documentación y
los registros. Rama `claude/inspiring-sagan-1ogr0n`. Sin renders, sin Actions, sin Releases nuevas ni borradas.

**Copia de seguridad (estado previo completo):** el commit `150fcea` (padre del commit de esta limpieza; para recuperar
un archivo: `git show 150fcea:<ruta>` o `git checkout 150fcea -- <ruta>`) y la rama `ccr-6d21fe8a-76t9c3`, que no se
tocó. La etiqueta `respaldo-pre-limpieza-2026-11-19` no se pudo subir (la política de la sesión rechaza etiquetas con
403); hubo además un `git bundle --all` verificado en la carpeta temporal de la sesión (efímero).

**Borrado (172 archivos), con certeza de que era de otras producciones y que el código que queda no lo usa:**
- `producciones/`: p000 mansión, p001 fútbol tiro libre, p002 la jefa, p003 fútbol 30 s, p004 mansión de día, p005 CQB,
  p006 Tren Fantasma, p007 Al vacío, p008 Drift Sunset, p009 Dúo Cero, p010 Un sueño de a dos (descartada) y
  `producciones/pruebas/` (fichas del render de prueba de la CQB).
- `escenarios/` (mansion_moderna_noche, estadio_futbol11_noche).
- Generadores de escenario exclusivos: `estudio/escenarios/{al_vacio,drift_sunset,duo_cero,estadio_futbol,mansion_cqb,
  mansion_moderna,tren_fantasma}.py`.
- Módulos de Blender que sólo usaban esas producciones (comprobado con el grafo de importaciones, también las que están
  dentro de funciones): `estudio/blender/{auto_rampa_s03,batalla_s03,salto_tren,tren,via_ferrea,paisaje,vehiculos_dr,
  ruedas,vidrios_dr,tiroteo}.py`.
- Física de Dream Rally (`estudio/fisica_dr/`, `datos/fisica_dr/` con las simulaciones guardadas) y su documento
  `docs/FISICA_DREAM_RALLY.md`.
- 66 archivos de voces de `audio/biblioteca/` usados sólo por recetas de Dúo Cero, las muestras de voz de p010 y la voz
  de prueba de la jefa, más sus 66 entradas de `catalogo/audio.json` (el registro de gasto `audio/ledger.jsonl` se
  conserva entero).

**Conservado a propósito:**
- Todo `producciones/p011_a_la_deriva/` (recetas e01 v1–v2, e02 v1–v3, `entregado.json`, guiones, documento del dueño,
  cámaras del director): sin tocar.
- Herramientas comunes: `estudio/` (director, cámaras, personajes, humanos, stickman —lo usan los humanos de «A la
  deriva»—, previa, trabajo, componentes, recursos, clips, manifiesto, protección, autorización, montaje, publicación,
  audio procedural y ElevenLabs), `app/`, `visor/`, `catalogo/`, `config/`, `tools` locales.
- Módulos nacidos en otras producciones que el código común importa (borrarlos rompe el pipeline o exige cambiarlo):
  `blender/pelota.py` (lo importa `director`), `blender/armas.py` y `armas_stickman.py` (`personajes`/`stickman`),
  `blender/efectos.py`, `blender/vehiculos.py`, `audio/{arcade,dream_rally,tren,radio}.py` y sus sonidos
  `audio/biblioteca/{free_kick_swipe,dream_rally}/` (los llama `audio/procedural.py`), `catalogo/futbol.json` (lo leen
  `director`, `personajes` y el buscador de animaciones). Candidatos a una poda posterior con un cambio dedicado.
- Herramientas generales sin uso hoy: `blender/animar.py`, `blender/proyectar_textura.py`, `blender/pelo_realista.py`,
  `blender/expresiones_3d.py`.
- `pruebas/godot_blender/` («Casa moderna en tormenta»): es la base del pipeline Godot → Blender → Cycles.
- `pruebas/` del sistema, de la app, de la autorización, del render por rangos y por bloques, del editor, de la nave y
  de los personajes humanos; `pruebas/motor_002` y `pruebas/resolucion_001` como registro histórico (sus scripts ya
  estaban deshabilitados; de ahí salió la configuración de Cycles).
- Todos los flujos de `.github/workflows/`, los documentos históricos (`INFORME_ETAPA1`, `MIGRACION_ORGANIZACION`,
  `docs/informes/`) y este registro.

**Ambiguos, NO borrados (decidir):**
- 45 audios de `audio/biblioteca/` que no nombra ninguna receta y no tienen etiqueta de producción. Por el texto,
  parecen de fútbol, Drift Sunset, el tren y Al vacío, pero también hay ambientes y músicas que podrían ser de «A la
  deriva»: música espacial, invernadero, timbres de consola.
- Siete voces de Eva de «A la deriva» (etiqueta p011) que ninguna receta usa: versiones anteriores.
- Roles de voz de Dúo Cero en `config/voces.json` y modelos de otras producciones en `estudio/blender_deps.py` y en
  los catálogos: apuntan a recursos de mixamo-respaldo, que no se tocó (es de sólo lectura).
- Valores por defecto obsoletos que no se cambiaron, porque la tarea del pipeline pide no tocar esos flujos sin
  necesidad. Si se lanzan sin datos fallan solos, sin renderizar nada:
  - `video30.yml`: escena de fútbol p003;
  - `episodio.yml`: Dúo Cero;
  - `pruebas/episodio/informe.py`;
  - las pruebas de la app: etiquetas p005 y p009, que sólo son textos.

**Ajustes para no romper referencias:**
- `pruebas/autorizacion/test_autorizacion.py` ahora usa «A la deriva» e02 v3 (antes usaba Dúo Cero e01).
- Ejemplos de escenario en `README.md`, `docs/ARQUITECTURA.md` y `docs/FLUJO_DE_PRODUCCION.md`.
- `docs/GUIA_PARA_OTRO_CHAT.md` (§4, §4 bis y §6).

**Verificación (sin render):**
- Ningún archivo que queda importa un módulo borrado: lo comprobé con `git grep` y con el grafo de importaciones.
- Importan los 53 módulos de `estudio` con el Python de Blender.
- La línea de comandos `estudio` funciona.
- Las 5 recetas de «A la deriva» validan, y sus huellas son **idénticas antes y después** de la limpieza.
- `test_autorizacion`: 40/40.
- `test_componentes`: 16/16, con mixamo-respaldo local actualizado (sólo descarga). Antes de actualizarlo daba 15/16
  por falta de los recursos de «A la deriva»; con el estado previo, 14/16.
- Los JSON de `catalogo/` y `config/` son válidos.
- `test_trabajo` 19/19 y `test_caminata` 4/4: arman escenas en Blender sin renderizar.

## 19/11/2026 — Pipeline Godot → GLB → AutoFinisher → .blend → Cycles (implementado, sin ejecutar)

Pedido del dueño (plan aprobado con 10 condiciones). Rama `claude/inspiring-sagan-1ogr0n`. **Sin renders, sin Actions,
sin Releases, sin publicar nada.** La prueba original (`pruebas/godot_blender/`: b6–b9, `armar.py`, su flujo) no se
tocó, ni los flujos existentes ni «A la deriva».

- **AutoFinisher** (`estudio/autofinisher/`), herramienta general. Módulos:
  - AutoImport, AutoLights (perfiles de luz), AutoMaterials, AutoEffects, AutoCinema, AutoPack, AutoReport;
  - receta de terminación, manifiesto (`estudio.version_blend/1`, SHA-256, inmutable), reparto de cuadros,
    verificación de cuadros y de video, mediciones (tiempo y RAM por etapa), bajada de recursos;
  - `render_trozo` (hash antes de abrir, reintentos por cuadro, `--sin-render`) e informe del render.
- **Estándar de nombres Godot → Blender**: `Luz_<perfil>_…`, `vidrio*`, `emisivo*`/`neon*`, `FX_<efecto>`, `Colision_*`,
  y la metadata `cine_tipo` con prioridad sobre el nombre.
- **Biblioteca de efectos** deterministas por cuadro: lluvia, fuego, humo, brasas y relámpago. Son los de la prueba,
  ahora con parámetros. El **fuego quedó corregido** (umbral 0,08→0,05, ganancia 9→12, emisión 22→90), sin
  verificar con render. No se agregó ningún efecto que no estuviera pedido.
- **Flujos nuevos e independientes** (preparados, nunca ejecutados):
  - `construir_produccion.yml`: Godot → GLB → AutoFinisher → validación → manifiesto → Release
    `blend-<prod>-v<NNN>`. Se niega si la Release existe.
  - `render_desde_blend.yml`:
    - sólo el `.blend` publicado, que verifica por SHA-256, y sin Godot;
    - reparto de la prueba, reintento por cuadro;
    - si falta un cuadro, se detiene sin rellenar; la recuperación es explícita (`cuadros` + `corrida_previa`);
    - MP4 verificado;
    - mide trabajos pedidos y ejecutados, simultaneidad real, cola, descarga, preparación, tiempo por cuadro, RAM,
      fallos y reintentos.
- **Reconstrucción local de «Casa moderna en tormenta»** (`pruebas/autofinisher/COMPARACION.md`): mismo GLB.
  - Comparación campo por campo: 721 iguales y 6 distintos. Las diferencias son el fuego corregido y el nombre de la
    colección de auxiliares ocultos.
  - Se encontró que `vidrio_opalino` se convertía por el prefijo; quedó excluido en la receta.
  - 3,06 s de máquina, RAM máxima 877 MB, `.blend` de 37,1 MB autónomo.
- **Pruebas** (sin render):
  - `test_autofinisher.py` 32/32;
  - `test_general.py` 13/13, con una escena que no es la casa;
  - validación y hash, `render-trozo --sin-render`;
  - descarga real de un archivo de Release con SHA-256 igual al de GitHub;
  - bajada de la Kodiak;
  - montaje simulado con un cuadro faltante (se detiene) y completo (MP4 verificado).
- **Docs**: `docs/AUTOFINISHER.md`, `docs/CONSTRUIR_Y_RENDERIZAR.md`, `FLUJO_DE_PRODUCCION.md` §7, `CLAUDE.md`, la guía.
- **Pendiente:**
  - la primera construcción y el primer render reales, que decide el dueño;
  - verificar el fuego con un render;
  - el MP4 sale sin audio;
  - «descargar un .blend publicado» se probó con otro archivo de Release, porque todavía no hay ninguno.

## 19/11/2026 — Flujo definitivo: creo → previa → correcciones → aprobada → la nube entrega el MP4

Pedido del dueño: una sola aprobación (la del chat), sin formularios ni entornos protegidos de GitHub; al aprobar, la
publicación y el render son automáticos. Detalle: `docs/FLUJO_DEFINITIVO.md`.

- **Nuevo:** `python -m estudio aprobar` (exige la previsualización entregada con la misma huella),
  `python -m estudio publicar-escena preparar|validar|cerrar`, `estudio/version_escena.py` (manifiesto
  `estudio.version_escena/1`), `estudio/blender/publicar_escena.py`, flujos `publicar_escena.yml` (publica y llama
  solo a) `render_escena.yml`; `previa --audio` (mezcla en .m4a para el visor) y `previa.yml` la sube; visor con
  audio sincronizado (el reloj es el del audio) y botón 💡 LUCES DE LA ESCENA.
- **Cambiado (mínimo):** `montar.py --audio-intacto` y `--fps` (sin la opción hace lo mismo que antes);
  `render_trozo.py` escribe también los campos de los informes de `render_rango.py`; `autofinisher/manifiesto.leer`
  acepta las dos clases de manifiesto; `proteccion.verificar` reconoce la receta aprobada.
- **Sin tocar:** `elevenlabs.py`, `cara_anime.py`, `expresiones_3d.py`, `stickman.py`, `procedural.py`,
  `audio_escena.py`, `director.py`, `video30.yml`, A la deriva y sus recursos.
- **Encontrado con la prueba real:** `director.guardar_blend` borraba las acciones de las formas de la cara
  (expresiones y labios cuelgan de las shape keys, no de los objetos): el `.blend` reabierto tenía las caras quietas
  (568 valores distintos). `publicar_escena` guarda por su cuenta. Además: un cuadro de corte (3408) donde el
  marcador daba la toma siguiente y `render_rango.py` la anterior (los marcadores se rehacen desde esa tabla), y
  materiales sueltos del FBX de un pelo con una textura inexistente (se borran los datos sin uso antes de empaquetar).
- **Prueba local con E02 v3 (modo ensayo, sin publicar, sin render, sin Actions):** preparar 539 s (RAM máx.
  1,72 GB; BLEND 45,6 MB autónomo, 44 voces y alineaciones en el zip); validar: 3998/3998 cuadros con la cámara
  correcta y 2790 valores de cara iguales en 31 cuadros de control; `audio_escena.py` 524 s: WAV idéntico byte a byte
  al de control (133,28 s, 48 kHz, estéreo); `render-trozo --sin-render` abre el BLEND en 0,84 s; `montar.py
  --audio-intacto` con el WAV real y 3998 cuadros de prueba de ffmpeg (no es un render): desfase 0 muestras, volumen
  −18,78 dB = −18,78 dB, MP4 3998 cuadros 30 fps 133,28 s. Un WAV con un byte cambiado se rechaza.
- **Previsualización con audio de E02 v3:** `previa --audio` → GLB 29,5 MB (14 mallas de cara con formas animadas:
  los labios se ven), JSON y M4A 2,2 MB (AAC 48 kHz, 133,28 s). Visor probado en Chromium como Pixel 7 con los tres
  archivos: carga sin errores, ▶ avanza con el reloj del audio, 💡 LUCES DE LA ESCENA con exposición tipo cámara (sin
  ella el sol de 2732 lux quemaba la imagen). Visor publicado en el artifact (versión 4).
- **No probado:** los flujos en Actions (no se ejecutaron), un render real desde el BLEND, la publicación de la Release
  y el visor en un teléfono real.

## 19/11/2026 — Pipeline: modalidad 2, incorporar un BLEND aprobado (sin render, sin Release, sin Actions)

- Pedido del dueño: el `p012_v1.blend` que revisó es el que se renderiza; el pipeline no admitía un BLEND externo.
- Nuevo `estudio/autofinisher/blend_externo.py` y comandos `aprobar-blend` / `incorporar`:
  - inspección del `.blend` en sólo lectura (nunca guarda ni empaqueta);
  - perfil obligatorio `PERFIL_720P`: 1280×720, 30 fps, Cycles CPU, 6 muestras, adaptativo 0,05, OIDN, 6 rebotes,
    Light Tree y semilla fija;
  - registro de aprobación con el SHA-256;
  - versión publicable = copia byte a byte + manifiesto `estudio.version_blend/1` con `origen: blend_externo` y
    `ajustes_bloqueados`.
- Flujo nuevo `incorporar_blend.yml`: baja el archivo (Release de entrada o URL), verifica el hash contra el registro,
  lo incorpora, lo valida, lo publica en `blend-<p>-v<NNN>` y llama a `render_desde_blend.yml`.
- Cambios en `render_desde_blend.yml`:
  - acepta `workflow_call`, con las mismas entradas;
  - con `ajustes_bloqueados`, rechaza resolución o muestras distintas.
- Documentación: `docs/CONSTRUIR_Y_RENDERIZAR.md` §5 bis y `CLAUDE.md`.
- Verificado sin render:
  - `test_blend_externo.py` 19/19;
  - las pruebas anteriores siguen bien (`test_general.py` 13/13, `test_autofinisher.py` 32/32);
  - con el archivo real `p012_v1.blend` (SHA-256 `3b36dda3…6b00`, 12 851 935 bytes), en una carpeta temporal:
    - aprobación, incorporación (copia idéntica) y `validar` OK (34 texturas empaquetadas);
    - `render-trozo --sin-render` del tramo 886–900;
    - reparto en 60 trabajos de 15 cuadros;
    - rechazo de 1920×1080 y de 12 muestras;
    - rechazo de un archivo con un byte cambiado.
- **No hecho (a pedido del dueño):** el registro de aprobación real de p012 en el repo, la Release, el flujo y el
  render.
- **Falta definir:** cómo llega el `.blend` a la nube (Release de entrada subida a mano o un enlace directo). Desde la
  sesión no hay una herramienta para subir archivos a una Release.

## 19/11/2026 — Metodología única y permanente (dueño) + transporte del BLEND aprobado por Git LFS

- El dueño fijó la metodología definitiva para todas las producciones: `docs/METODOLOGIA.md` (resumen al principio de
  `CLAUDE.md`).
  - Godot construye la estructura, las animaciones y las cámaras.
  - Blender hace la terminación artística: lo visual se corrige ahí, sin volver a Godot.
  - El dueño revisa sólo el GLB exportado desde Blender, más el JSON y fotos fijas de lo que el GLB no muestra.
    Nunca el BLEND, nunca videos de muestra.
  - Con «aprobada» se renderiza el BLEND exacto, verificado por SHA-256.
  - Render 1280×720 a 30 fps, Cycles CPU, 6 muestras, hasta 60 trabajos.
- Transporte del BLEND a la nube sin intervención del dueño: Git LFS en `producciones/<p>/blend/` (`.gitattributes`);
  `incorporar_blend.yml` lo toma de ahí por defecto.
- Red del entorno: el proxy bloqueaba `lfs.github.com`. Con aprobación del dueño se agregaron `lfs.github.com` y
  `github-cloud.s3.amazonaws.com` a los hosts permitidos del entorno Default.
- **Pendiente:** la primera subida real a LFS no se pudo probar. El control de permisos de la sesión bloqueó la prueba
  de subida con un objeto chico. Hace falta que el dueño permita `git lfs push` en esta sesión para que el paso 6
  funcione.
- p012: el BLEND original sigue intacto (SHA-256 `3b36dda3…6b00`). Sin aprobación explícita de producción todavía:
  nada publicado ni ejecutado.

## 19/11/2026 — Verificación del transporte por Git LFS (sin producción)

- Repo `Cinema3DSHR/Cinema3DSHR`, rama `claude/inspiring-sagan-1ogr0n`.
- `.claude/settings.json` (regla `Bash(git lfs *)`): lo creó el dueño en GitHub (commit `1e7b2b3`). Se llevó también a
  la rama por defecto `ccr-6d21fe8a-76t9c3` (avance directo) para que lo lean las sesiones nuevas.
- Git LFS 3.4.1, endpoint `https://github.com/Cinema3DSHR/Cinema3DSHR.git/info/lfs`. La autenticación la pone el
  proxy del entorno.
- Prueba segura:
  - un objeto de prueba de 58 bytes subido con `git lfs push --object-id` (sin commit, no queda en el historial);
  - bajado en un repo temporal con `git lfs smudge`: idéntico byte a byte.
  - Conectividad, autenticación y permisos OK.
- No se tocó la escena, no se subió el BLEND de p012, no se publicó nada ni se ejecutó ningún flujo.

## 19/11/2026 — p013 «Mi hogar ideal» (Reel vertical 9:16, narradora invisible) — versión 1 de revisión

- Fuentes en `producciones/p013_mi_hogar_ideal/`: `guion.json`, `disenio.py` (genera `layout.json`: casa, muebles, luces y
  cámara cuadro a cuadro, con validador «la cámara no atraviesa nada»), `godot/` (proyecto que lo arma y exporta el GLB),
  `blender/construir.py` (terminación artística) y `blender/exportar_previa.py`. Nada de esto sube BLEND, GLB ni videos.
- **Godot (cerrado, no se vuelve):** casa minimalista de una planta (sala, comedor, cocina, principal, 2 dormitorios, baño,
  pasillo), jardín, sendero, cerco con rejas y portones, calle, 99 árboles reales de la biblioteca, colinas en el horizonte.
  Autos SOLO de Dream Racing con las ruedas del juego: camioneta Yaguareté + R2 Turbo rojo (el auto inicial) en la cochera,
  GT en la calle. Accesorios armados con formas simples porque la biblioteca no trae piezas así (tomacorrientes,
  interruptores, cortineros, portarrollo, toallero, jabonero, riel de cocina, ventilador de techo) + ventilador de mesa,
  escobilla y olla arrocera de la biblioteca.
- **Blender (`construir.py`):** cielo y sol animados (día → atardecer → noche), vidrio con refracción, pasto, copas de árboles,
  autos aligerados (≈90 mil triángulos c/u), fuego de la chimenea con chispas, neblina baja en el jardín y bruma, luces
  exteriores que se encienden al anochecer, Cycles con el perfil del estudio.
- **Pendientes que dependen del dueño:** (1) la voz `9b3epFpN8VNQyCsbs3ER` no existe en la cuenta de ElevenLabs
  (`voice_not_found`): hay que agregarla a «Mis voces» o enviar el audio; no se generó ni inventó otra voz. (2) La
  resolución del Reel es 720×1280 (vertical, mismos píxeles que 1280×720): el perfil obligatorio del estudio dice 1280×720 y
  `aprobar-blend` lo rechazaría; hace falta que el dueño confirme la excepción vertical antes de aprobar.
- Sin audio todavía: los tiempos de las tomas son estimados. Nada publicado, ninguna Release, ningún Actions.

## 19/11/2026 — p013 «Mi hogar ideal» v001 APROBADA por el dueño → producción

- Frase del dueño: «la escena esta Aprobada.» + indicó la voz «Yuli - Warm, Natural» (`9b3epFpN8VNQyCsbs3ER`) y el formato vertical.
- Voz: estaba en la biblioteca compartida de ElevenLabs (no en «Mis voces»); se agregó a la cuenta (gratis) y se generaron 15
  clips, uno por toma (1290 caracteres de 20 479 disponibles; presupuesto respetado). Todos duran menos que su toma, así que
  el video aprobado NO cambia: cada clip entra 0,15 s después del inicio de su toma (`audio/narracion_v001.m4a`, sin música,
  sin acelerar ni normalizar).
- Formato: se agregó `PERFIL_VERTICAL` (720×1280, todo lo demás igual al perfil obligatorio) a `blend_externo.py`; sólo se
  elige si la producción declara `720x1280`. Prueba `test_blend_externo.py`: 20/20.
- BLEND aprobado: SHA-256 `dced75ce…c435`, 33 880 174 bytes (el mismo del que se exportó el GLB revisado; sin cambios).
  Registro: `producciones/p013_mi_hogar_ideal/versiones/v001.aprobacion.json`. Transporte por Git LFS.

## 19/11/2026 — p013 «Mi hogar ideal» v001: render final entregado

- Corrida `incorporar_blend.yml` 44530912559: hash del BLEND verificado, Release `blend-p013_mi_hogar_ideal-v001` publicada,
  60 trabajos de render (0 fallos, 0 reintentos), 2985/2985 cuadros, 720×1280 a 30 fps, 99,5 s.
  MP4 sin audio en la Release: `p013_mi_hogar_ideal_v001_final.mp4` (44 MB) + informe.
- Montaje con voz: `ffmpeg` copia el video (sin recodificar) y suma `audio/narracion_v001.m4a` (clips de la voz Yuli en el
  inicio de cada toma + 0,15 s; sin música, sin acelerar, sin normalizar). Se entregó al dueño por el chat. No se pudo subir
  a la Release: `gh release upload` usa GraphQL y el entorno lo bloquea (permiso técnico que falta; no se esquivó).

## 19/11/2026 — p014 «Rally Convoy» (cinemática de Dream Racing, solo etapa Godot)

- Pedido del dueño: cinemática de ~5 min, 480×854 vertical, siete autos originales conducidos por la física y la IA reales del juego, en pelotón;
  detenerse en Godot (sin Blender, sin efectos); mostrar un video grabado del motor de Godot (MP4 liviano). Además: auto fantasma invisible con
  cámara, zoom de lente que sigue y se aleja, dron no muy alto, trazadas reales; guardar el set.
- Hecho: ruta nueva con el generador de la Aventura, simulación (0 solapamientos de autos, 0 salidas de camino, deslizamiento máx. 31° en montaña,
  llegada a los 308 s), dirección de cámaras, grabación 3552 cuadros (296 s) con el sonido original. Set en `producciones/p014_rally_convoy/`.
- Entregado el video al dueño por el chat. No se hizo Blender ni render final; no se publicó nada.

## 19/11/2026 — p014 «Rally Convoy» v001: ajustes, Blender, render final y entrega

- Ajustes pedidos por el dueño: (1) pedales: se terminó el «pisar y soltar» (ley de gas/freno continua con gas de crucero que se aprende solo,
  filtro de pedales, topes de velocidad del pelotón graduales y zona muerta en la corrección de posición); frenadas por auto en 120 s de ruta
  abierta pasaron de 49–109 a 0–4 en los autos potentes. (2) cámara interior: sin pedazos del casco (cabeza del piloto oculta con la cámara interior
  y carrocería oculta a la cámara en esos planos, luz suave en la cabina). (3) más tomas con el auto fantasma por delante de un auto elegido (en
  especial en la montaña alta) y sin planos aéreos salvo el del puente. Autos de carrocería alta con menos agarre permitido (no se salían del camino
  con el perfil original). Simulación completa: 0 solapamientos de autos y 0 salidas de camino durante el video (el tramo final después de la
  estación de llegada no se usa).
- Exportación a Blender (`exportar_blender.gd`): mundo, siete autos originales completos con su textura, ruedas y suspensión, cabinas 3D, pilotos con
  huesos animados, peaje y cámara, a 30 cuadros por segundo; GLB de 261 MB + JSON (cortes, zoom, telemetría). Etapa de Blender (`blender/construir.py`
  + `retoque_camara.py`): materiales, cielo y sol, árboles redondeados, bruma, humo de gomas por telemetría, desenfoque de movimiento, Cycles.
- Producción: perfil de prueba 480×854 (`PERFIL_480V`, 21/21 pruebas). BLEND aprobado SHA-256 `d471350d…e30c` (363 803 158 bytes), Git LFS,
  Release `blend-p014_rally_convoy-v001`, corrida `incorporar_blend.yml` 44576933015: 60 trabajos, 9360/9360 cuadros, 0 fallos,
  13,1 s por cuadro de media (34,1 h de CPU). MP4 de 312,0 s en la Release. El sonido original del juego (grabado de la misma simulación) se montó
  aparte y el MP4 con audio se entregó por el chat; no se pudo subir a la Release (`gh release upload` usa GraphQL, bloqueado en el entorno).

## 20/11/2026 — p015 «A la deriva: FRACTURA» (experimento, sin aprobación previa por pedido del dueño)
- 180 s · 720×1280 · 30 fps · 5400 cuadros. 9 escenas (ojo, corredor, cero g, detonación, espejos, colapso, oscuro, reconstrucción, final) y transiciones por geometría y cámara.
- BLEND `p015_fractura_v001` (SHA-256 `44037c42…2557`) por Git LFS → `incorporar_blend.yml` (corrida 44709823893): 59 de 60 trabajos bien; el de los cuadros 1351–1440 (explosión) pasó las 2 h y se canceló.
- Recuperación con `render_desde_blend.yml` (corrida 44748847228, `cuadros=1351-1440`, 45 trabajos, `corrida_previa=44709823893`): montaje OK, MP4 de 5400 cuadros verificado.
- Música original (`blender/musica.py`, numpy) mezclada con ffmpeg sobre el video (`-c:v copy`); el audio se midió pero no se escuchó. Entregado por el chat (la subida del MP4 con música a la Release sigue bloqueada por GraphQL).
- Detalle técnico y límites: `producciones/p015_fractura/README.md`.

## 20/11/2026 — p016 «Dream Racing — McLaren F1: SHOCKWAVE»
- GLB del dueño sin deformar (versión F1; piezas [LM] y «(2)» ocultas). Ruedas izquierdas = las del derecho copiadas y GIRADAS 180° (opción A; el dueño no confirmó la B espejada). Matrículas «3D SHR»; parabrisas «Cinema3DSHR».
- Avenida con interiores de Sweet Home (restaurante, supermercado, muebles; orientación verificada midiendo el respaldo), árboles reales `tree_tree` densificados, física de vidrios/hojas/piedras por Python+numpy horneada a claves.
- BLEND `p016_mclaren_shockwave_v001` (SHA-256 `38e0d82e…727e`) por LFS → `incorporar_blend.yml` (corrida 44770581752, 63 trabajos OK) → MP4 de 1800 cuadros. Audio V12 sintetizado (`blender/audio.py`) mezclado con ffmpeg; no se escuchó, sólo se midió.
- Pendiente de revisar con el dueño: la toma lateral 0:05–0:11 tapa el plano con la puerta; al final un fragmento queda pegado a la lente (~0:57).
- Regla nueva (dueño, 20/11/2026): las cámaras de seguimiento deben ser continuas, sin saltos ni vibraciones (en p016 la lateral iba a saltos por el ruido por cuadro de `micro()` y las claves cada 2 cuadros). Quedó en `CLAUDE.md` regla 9; se revisa antes de cada render. El video p016 salió igual, el dueño lo publica así.
- Regla nueva (dueño, 20/11/2026): los vehículos siempre apoyados en el suelo (`CLAUDE.md` regla 10). En p016 el McLaren flotaba: el modelo se apoyó por la rueda delantera (z −0,64) y las traseras tienen su punto más bajo en z −0,61, o sea ~3 cm en el aire. Antes de renderizar hay que medir el punto más bajo de cada rueda en mundo.

## 21/11/2026 — Temporada piloto (p017, p018, p019): tres videos verticales 540×960, 30 fps
Orden del dueño: tres videos separados, uno tras otro. Todos con narración ElevenLabs (voz Yuli, `temporada_01/narrar.py`), música y efectos originales sintetizados (`audio.py`), subtítulos ASS integrados y el aviso en pantalla correspondiente. Metodología única: Godot/Blender → BLEND aprobado (SHA-256) → LFS → `incorporar_blend.yml` → render Cycles 6 muestras → montaje local (ffmpeg).
- **p017 «¿Qué harías si apareciera un millón de dólares?»** (66,7 s): 1662 cuadros en Blender + cierre en tres paneles armado en el montaje. Personas Aiden/Kate retargeteadas con `retarget_dir` (columna/cuello/cabeza por giro relativo al reposo; la raíz se retargetea mirando a −Y). Saldo con odómetro 3D, cuentas verificadas (`cuentas.json`). Arreglos de la sesión: velos de transición sólo visibles durante su rampa (ensuciaban el denoise de otras tomas), modelos Sweet Home con varias piezas sueltas (`sh3d.poner` agrupa bajo un vacío: el auto chico salía ×100), llegadas de personas sin deslizarse entre escenas, apoyo de ruedas/pies al milímetro (suelo = cara superior real de cada superficie).
- **p018 «¿Sabías que podría llover diamantes en otros planetas?»** (66 s): Urano/Neptuno, descenso con presión y temperatura, ruptura del metano, red cristalina de diamante, lluvia, experimento láser/rayos X (SLAC 2017, Nature Astronomy; XFEL 2024). Presentado como hipótesis respaldada por experimentos; «Representación científica, no filmación real».
- **p019 «¿Por qué el cielo es azul?»** (60 s): dispersión de Rayleigh con el cielo físico de Blender (Sky Texture), prisma, moléculas, onda azul vs roja, violeta (barras ilustrativas), atardecer con el Sol bajando de 38° a 0,8°, Tierra desde el espacio con cielo negro.
Verificaciones previas al render: cámaras sin picos de aceleración (2.ª diferencia por cuadro), ruedas de los autos tocando el suelo (APOYO impreso al construir), orientación de personas y objetos revisada en tiras de cuadros. Entrega: `VIDEO_0X_final.mp4` con QC (duración, resolución, fps, audio) en el informe final.

## 23/11/2026 · Cap. 3 — nave única en Godot (v2) con plantas reales
- Nave única en Godot (`producciones/p011_a_la_deriva/godot_e03`): 33 piezas, verificador 230 piezas / 0 problemas (nada flotando ni al revés).
- Plantas modeladas en Blender (`herramientas/plantas/plantas.py`: ficus, helecho, enredadera, hojas anchas, rosales) con viento por morph targets. Causa de las hojas blancas en Godot: Blender 5.3 exportaba el JPEG de la hoja en un formato que Godot no decodifica; se exporta ahora con `export_image_format='AUTO'` (PNG). Los GLB de plantas no van a Git (regla 5): se regeneran con `QUE=rosa_roja,rosa_blanca,rosa_amarilla,ficus,helecho,enredadera,anchas /opt/tools/blendenv/bin/python plantas.py -- <salida>`.
- Pendiente de revisión del dueño en su visor: GLB de la nave; luego personajes, manos con objetos, cámaras y audio.

## 23/11/2026 · Cap. 3 — motor de montaje en Godot (en curso)
- Personajes (`herramientas/personajes_c3/`): `ensamblar.py` (FBX CC4 → colores → clips de Mixamo retargeteados con movimiento de raíz extraído → GLB), `traje2.py` (traje «primera piel» + botas con pesos al esqueleto; pies con envolvente convexa). Los GLB no van al repo.
- Godot (`godot_e03/tools/`): `actor.gd`, `cara.gd` (labios por letra de la voz real, mandíbula, parpadeo, expresiones, mirada), `montaje.gd` (horneado a 30 cuadros/s, objetos en la mano con cierre de dedos, cámaras suaves, GLB + JSON para el visor), `data/storyboard_e03.json` generado por `herramientas/storyboard_e03.py`.
- Voces del cap. 3 generadas (33 líneas, 2.240 créditos, 137 s): `audio_e03/voces.json`.
- Rosa real de Blender (`plantas.py`: `rosa_unica`) y pétalos con degradado como imagen (antes salían blancos). Estado: escena 1 montada y en revisión; faltan escenas 2–5.

## 23/11/2026 · Cap. 3 «Protocolo de cierre» — BLEND único aprobado y render lanzado (540p)
- Orden del dueño: «renderiza a 540p. las escenas están aprobada… hazlo todo, el 60 trabajos». 540p = 960×540 (16:9, como se encuadraron y revisaron las cámaras: no hizo falta rehacer nada). Nuevo `PERFIL_540H` en `estudio/autofinisher/blend_externo.py` (todo lo demás igual al perfil obligatorio: Cycles CPU, 6 muestras, adaptativo 0,05, OIDN, 6 rebotes, Light Tree, semilla fija, 30 fps).
- Etapa Blender (`herramientas/etapa_blender/`): `construir_cap3.py` junta los 5 GLB de Godot en UN .blend (nave única, tiras NLA encadenadas, cámaras por marcadores, visibilidad por escena) y `efectos_cap3.py` agrega luces por sala, mundo, piel con subsurface, holograma de EVA con parpadeo y corrige la orientación de las caras de la nave. Total 5.324 cuadros = 177,47 s.
- Producción `producciones/p020_a_la_deriva_cap3` v001: BLEND 141.493.948 bytes, SHA-256 `e6c8615d64e07fb9ace2b2ab7605042a7db2c988e06f749b69ab935e304a3c96`, aprobación registrada (`versiones/v001.aprobacion.json`), BLEND por Git LFS (`blend/`).
- `incorporar_blend.yml` lanzado (run 45146139176, 60 trabajos). Pendiente: descargar el MP4, mezclar el audio de las voces (`audio_e03/voces.json`, M4A por escena) y entregar.
- Honestidad: la etapa Blender (luces, holograma, materiales) no pasó antes por el visor del dueño; el GLB revisado era el de Godot. Pendientes conocidos: parche claro en la nuca de Aiden, aro de cuello provisorio, pelo sin física, holograma de EVA sin «construcción por capas».

## 23/11/2026 · Cap. 3 — sonido de ambiente (mismo que los cap. 1 y 2)
- El primer montaje sólo llevaba voces. Ahora (`herramientas/audio_cap3.py`): ambiente procedural «nave_interior» a 0,35 en todo el capítulo + música y efectos YA generados en la biblioteca para los cap. 1 y 2 (partitura de espacio, partitura del jardín, motivo de piano, invernadero hidropónico en bucle, chime y ping), pasos en cada caminata/corrida y una alerta suave en la escena 2. Sin generar ni gastar créditos nuevos. El video no se volvió a renderizar: sólo se rehízo el audio del MP4.
- `montaje.gd` tiene un modo `plan` (`-- sN prefijo plan`) que vuelca qué hace cada actor y cuándo (lo usa el diseño de sonido).

## 23/11/2026 · Cap. 3 — rehecho en VERTICAL 540×960 (corrige un error de formato)
- Error mío: el primer render (p020, 960×540 horizontal) ignoró que la serie es 9:16 (540×960; `produccion.json` de p011 ya lo decía). El dueño publica en Shorts/Reels/TikTok.
- Se reutilizó todo menos las cámaras: reencuadre vertical (`REENCUADRE` en `storyboard_e03.py`: 8 tomas), GLB nuevos desde Godot a 540×960, BLEND nuevo, producción `p021_a_la_deriva_cap3` v001 (SHA-256 `6d1f18a861d249c075ead8230e33c5e38ffe6ae90e6f283258fb69bcd63f3838`), render 60 trabajos OK (5.324 cuadros) y el mismo audio (`audio_cap3.py`: ambiente nave_interior, música y efectos de los cap. 1 y 2, pasos, alerta, voces). Sin gasto de ElevenLabs.
- El render horizontal p020 queda en su Release pero no sirve para publicar.

## 23/11/2026 — Limpieza de audios viejos
A pedido del dueño (videos ya en YouTube): `git rm` de 269 audios (recuperables en `2e07f26`), catálogo de audio podado a 10 entradas, conservados 6 audios de ambiente/música/efectos del cap. 1–2 y el `ledger`. Siguiente: borrar medios de las Releases con `borrar_medios.yml`.

## 23/11/2026 — Serie nueva: «La mujer que volvió de la muerte» (cap. 1) — arranque
Pedido del dueño: neo-noir de 3–4 min (accidente en tormenta, recuerdos, casa con tormenta), Gabriel=Aiden y Elena=Kate con ropa nueva, narración con ElevenLabs voz `5egO01tkUjEzu7xSSE8M` (agregada a `config/voces.json` como `gabriel_noir`), escenas del accidente en 1.ª persona (respiración y latidos), Godot arma todo → Blender agrega efectos → render VERTICAL 540×960 («520p» = 540p). Narración total ≈ 1.475 caracteres (≈1.500 créditos, dentro del tope). **Falta el auto «proporcionado»**: el dueño lo sube. Sin gastar nada todavía.

**23/11/2026 (cont.)** Cap. 1 «La mujer que volvió de la muerte»: el dueño subió el auto (`hustler.glb`, negro, 58 piezas sueltas, sin daño); plan en `docs/CAP1_LA_MUJER_QUE_VOLVIO.md`, guion en `producciones/p022_la_mujer_que_volvio/herramientas/guion_cap1.py`. Formato 540×960 vertical confirmado.

**23/11/2026 (aclaración del dueño):** en el cap. 1 NO se muestra el disparo; Gabriel ya está herido en la casa y el disparo se cuenta en otro capítulo. La sangre real (suelo, rostro, manos) se mantiene en el accidente. Plan actualizado.

**23/11/2026:** voz de Gabriel del cap. 1 generada (42 líneas, 111,9 s, 2.354 créditos; ledger actualizado). Contexto: tras buscar a Elena se desmaya y pierde el rastro; pasa 1 año y luego el disparo (otros capítulos).

## 24/11/2026 · Cap. 1 «La mujer que volvió de la muerte» — escena de la CASA: BLEND aprobado y render lanzado (vertical 540×960)
- Orden del dueño: «corregí… termina con una toma desde lejos mostrando un poco la escena completa y podés hacer el renderizado ya». Correcciones: sangre de las manos en manchas (no «guante»), sillón más redondeado, herida del hombro más marcada, última toma (H8) que se aleja hasta mostrar toda la sala.
- Producción `p022_la_mujer_que_volvio` v001: BLEND 15.108.323 bytes, SHA-256 `da4dfcca2f96551e7e4c5e3eae46203f322898829fe45192bff402555343bb61` (= el BLEND de las fotos de control), 2.341 cuadros = 78,03 s, aprobación en `versiones/v001.aprobacion.json`, BLEND por Git LFS.
- `incorporar_blend.yml` lanzado (run 45369773353, 60 trabajos). Pendiente: bajar el MP4 y mezclar el audio (`herramientas/audio_casa.py` → `casa.wav`/`casa.m4a`, subtítulos `casa.srt`).
- Límites conocidos: accidente (el recuerdo) todavía sin ropa/chispas/vidrios/polvo cerrados y sin renderizar; licencias de modelos sin confirmar.
- **Render terminado (24/11/2026):** run 45369773353 OK, 2.341/2.341 cuadros, 540×960 a 30 fps, sin fallos (59 trabajos, 14,4 s/cuadro, 9,4 h de CPU). MP4 sin audio `p022_la_mujer_que_volvio_v001_final.mp4` en la Release `blend-p022_la_mujer_que_volvio-v001`; audio mezclado aparte (`audio_casa.py`, voz +10,6 dB sobre el fondo) → entrega `casa_final.mp4` (78 s). Subtítulos en `casa.srt` (no incrustados).

## 24/11/2026 · Cap. 1 «La mujer que volvió de la muerte» — capítulo completo armado
- Accidente: producción `p023_la_mujer_accidente` v001 (SHA-256 `67c50f2d56dc6b47556577149bc25f826e514548251470a8820c9e2e35e2e868`), orden del dueño «renderizá el accidente y armá el capítulo con la tarjeta»; run 45384746049 OK, 2.038/2.038 cuadros, 540×960, sin fallos.
- Puente de 50 s con la narración que había quedado sin usar (bloque «despues», 12 líneas) sobre negro con grano y subtítulos (`herramientas/audio_puente.py`) y tarjeta final de 7 s «CAPÍTULO 1 / LA MUJER QUE VOLVIÓ DE LA MUERTE».
- Montaje: accidente (67,9 s) → puente (50 s) → casa (78 s) → tarjeta (7 s), fundidos de 0,5 s, total 201,4 s, 540×960 a 30 fps. Entregado como `capitulo1_envio.mp4` (reducido para el chat).
- Pendiente: puente con imágenes (hoy negro), pulgar sin sangre, licencias de modelos.

## 25/11/2026 · Experimento de estilo «líneas técnicas» (pedido del dueño, prompt EXTRACCIÓN VERTICAL adaptado a nuestras producciones)
- Escena de prueba con todos los tipos de objeto (auto original, casa, puerta con marco, cajas, barriles, árboles, flores, farol, valla, extintor, tubo rojo) y los dos personajes (Aiden apuntando con la pistola USP y láser rojo, Kate de pie): `godot_cap1/tools/escena_lineas.gd` → GLB → Blender (`herramientas/estilo_lineas/render_estilo.py` + `componer.py`). 720×1280 vertical, Cycles (perfil del estudio: 6 muestras, OIDN, semilla fija).
- Cuatro tratamientos del mismo cuadro y la misma cámara: A ink filter, B technical materials, C hybrid line art, D plano dibujado (imágenes en el chat; no van al repo).
- Costos medidos (4 núcleos, por cuadro a 720×1280): sombreado Cycles ≈ 6,7 s; contornos con Freestyle ≈ 33 s (lo caro); contornos por pasadas (normales+profundidad+clases, bordes en espacio de imagen) ≈ 3,7 s; máscara de clases ≈ 1,5 s. Total: ≈ 41 s con Freestyle, ≈ 12 s por pasadas. Referencia noir actual ≈ 14 s/cuadro a 540×960 en GitHub.
- Prueba de movimiento (16 cuadros, caminata → apuntado, cámara acercándose, estilo B por pasadas): líneas estables, sin parpadeo visible en la tira; los contornos de cara y manos son más ruidosos que los de arquitectura.

## 25/11/2026 · Estilo «líneas técnicas»: el auto gris con giro de cámara de 5 s en 5 tratamientos (render distribuido en 60 máquinas)
- Producción `p024_auto_estilos` (BLEND por LFS). Escena: Hustler gris metalizado en playón, seto y árboles, cámara que rodea el auto en 150 cuadros (frente → costado → atrás), 720×1280 a 30 fps. Flujo `estilo_auto.yml` (60 trabajos de 2–3 cuadros) y `estilo_auto_medir.yml` (medición por estilo en 1 máquina). Videos en la Release `estilo-auto-2`.
- Render distribuido (corrida 2): 60 trabajos, 6,6 min de reloj, trabajo medio 223 s (121–326), 9,76 h de CPU para los 5 videos juntos (las pasadas se comparten), memoria pico 1,6 GB, máquina 4 vCPU x86_64. La corrida 1 perdió un trabajo (el 17) y GitHub dio 500 al reintentar sólo ese: se relanzó entera.
- Costo por estilo si se renderiza solo (medición, 1 máquina de 4 vCPU, por cuadro): original 58,1 s · C 3,9 s · D 25,2 s · E 25,1 s · híbrido 52,2 s (+ composición 0,1–0,6 s). C cuesta ~7 % del original; D y E ~44 %; el híbrido ~90 %.
- Aviso: los tiempos varían ±30 % entre máquinas (el color a 32 muestras tardó 42,7 s en el render y 58,1 s en la medición).

## 25/11/2026 · Escena «pistolas» del trailer de extracción en estilo E (p026)
- Origen: `escena_pistolas.part1-3.rar` del dueño (GLB de 98 MB con mapa, personajes, armas, cámara, sangre y anatomía de rayos X, 23,1 s). El GLB usa `KHR_node_visibility`, que este Blender no importa: `herramientas/parchear_glb.py` quita la extensión.
- `herramientas/construir_pistolas.py` arma el BLEND (116 MB, LFS) y agrega los efectos que no viajan en el GLB desde `datos/escena_pistolas_disparos.json` + `sonidos.csv`: sangre (chorros y charcos), fogonazos con luz, trazadoras, humo, chispas, polvo/esquirlas y rotura del cajón. Cuadro de salida a 30 fps ↔ animación a 24.
- `herramientas/estilo_pistolas_frame.py`: pasadas + compuesto estilo E (color directo sólo en sangre, anatomía y fuego) y original. Formato 1280×720 (la escena es horizontal).
- Flujo `pistolas_e.yml` (disparador `.github/disparadores/pistolas_e.txt`): 60 trabajos, 694 cuadros, audio `audio/mezcla_audio.m4a`. Corrida 1 OK → Release `pistolas-e-1` (E, original, informe).
- Costos: 32,9 CPU-h, trabajo medio 591 s (337–808), 2,9 GB pico, 18 s/cuadro color, 18 s arcilla, 3,4 s cada pasada de normales/profundidad/clases, composición 0,9 s.
