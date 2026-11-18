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
