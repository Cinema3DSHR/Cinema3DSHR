# 3D Film Studio — instrucciones para Claude Code

Hablar con el dueño en español rioplatense. Un chat nuevo empieza por `docs/GUIA_PARA_OTRO_CHAT.md` (todo lo necesario sin auditar). Leer primero `docs/REGISTRO.md` (estado) y `docs/FLUJO_DE_PRODUCCION.md` (cómo producir).

## METODOLOGÍA ÚNICA Y PERMANENTE (dueño, 19/11/2026) — `docs/METODOLOGIA.md`
**Godot → Blender → GLB de revisión → aprobación → render final.** Es la única metodología autorizada para todas las
producciones: no proponer otros flujos ni volver a preguntar qué modalidad usar, hasta que el dueño diga lo contrario.
- **Godot:** estructura, animaciones, conexiones y cámaras. Se exporta a GLB.
- **Blender:** luces, materiales, humo, niebla, efectos y Cycles. Lo visual se corrige en Blender; a Godot se vuelve
  sólo por problemas de construcción o de animación, y eso es una versión nueva.
- **Revisión:** al dueño se le manda el GLB exportado desde Blender, el JSON con la línea de tiempo y las cámaras, y
  fotos fijas sólo de lo que el GLB no muestra. NUNCA el BLEND, NUNCA videos de muestra ni renders intermedios.
- **«aprobada» / «está bien» / «renderizá»:** autoriza la producción de ESA versión.
  1. SHA-256 del BLEND exacto del GLB revisado. Si cambió, detenerse y avisar.
  2. `aprobar-blend`.
  3. Git LFS (`producciones/<p>/blend/`).
  4. `incorporar_blend.yml`: verifica, publica la Release y dispara `render_desde_blend.yml`.
  No hay otra aprobación en GitHub y nunca se reconstruye.
- **Render obligatorio:** 1280×720 a 30 fps, Cycles en CPU, 6 muestras, adaptativo 0,05, OpenImageDenoise, 6 rebotes,
  Light Tree, semilla fija y hasta 60 trabajos. Nunca 1920×1080.
- **Al dueño no se le piden operaciones técnicas:** ni subir archivos, ni crear Releases, ni transferencias.
- **AUTORIZACIÓN:** «APROBADA» = autorización completa de producción de esa versión: registro, LFS, verificación,
  Release, Actions, reparto, render a 720p/30, montaje y entrega, sin volver a preguntar nada
  (`docs/METODOLOGIA.md` §6 bis). Si el entorno bloquea un permiso técnico: no esquivarlo, no pedir otra aprobación,
  decir exactamente qué permiso falta y detenerse ahí.

## Repositorios
- **«A la deriva» quedó GUARDADA el 23/11/2026 (`docs/A_LA_DERIVA_ESTADO.md`: qué existe, qué no está en el repo, cómo rehacerlo, trampas). Formato por defecto de las series: VERTICAL 9:16, 540×960 — confirmarlo antes de renderizar (el cap. 3 salió horizontal por error).**
- **Desde el 19/11/2026 este repositorio está dedicado a «A la deriva» (`producciones/p011_a_la_deriva`)** más las
  herramientas comunes y la prueba Godot → Blender (`pruebas/godot_blender`). Las demás producciones se borraron
  (detalle y cómo recuperar: `docs/REGISTRO.md` → «Limpieza general»; estado previo en el commit `150fcea`).
- **Cinema3DSHR** (este, público): todo el trabajo. Rama de la sesión indicada por el sistema.
- **mixamo-respaldo** (privado): animaciones originales. **Sólo lectura** — nunca borrar, mover ni sobrescribir.
- Operaci-n-Nexus-1 / Extraction-tactical: sólo para tomar recursos (armas, operador, audio). No auditarlos.

## Reglas
1. No borrar ni modificar originales; índices y metadatos van aparte (`catalogo/`).
2. Reutilizar antes de crear (catálogos, escenarios). Tripo3D sólo con autorización y comprobando el costo antes.
3. Nada de servicios pagos sin avisar. ElevenLabs ya está conectado (credencial en el entorno, nunca por chat): primero `python -m estudio voces <escena>` (estima), recién después `--gastar`; respetar `config/presupuesto_audio.json`. Tripo3D sigue pidiendo autorización.
4. Ningún secreto en el repo, la APK, registros ni el chat.
5. Videos, .blend, GLB y fotogramas **nunca** al historial de Git (van a Releases por los flujos de Actions). Excepción: el audio generado, chico (mp3 de KB), vive en `audio/biblioteca/`.
6. Versiones: una versión publicada no se edita; correcciones = `python -m estudio nueva-version`. Las aprobadas
   llevan `"bloqueada": true`.
7. Antes de subir una escena: `validar` y revisar su previsualización 3D (`previa` + la prueba de la app
   `pruebas/revision/revision_ui.gd`, sin render). `fijas` es un render: sólo si el dueño lo pide. No decir que algo
   funciona sin haberlo probado.
8. Registrar cada avance en `docs/REGISTRO.md`.
9. **Cámaras de seguimiento (regla del dueño, 20/11/2026, p016):** una cámara que sigue a un auto o personaje tiene que moverse en forma CONTINUA, sin saltos ni vibraciones. Prohibido sumarle ruido al azar distinto en cada cuadro (en p016 `micro()` movía la cámara lateral a saltos) y dejar claves cada 2 cuadros en tomas de seguimiento: se animan con curvas suaves (ruido de baja frecuencia o seno) y una clave por cuadro. La vibración sólo se permite como golpe breve con decaimiento (onda de choque). **Antes de renderizar:** para cada toma de seguimiento calcular la posición de la cámara cuadro a cuadro y verificar que la aceleración no tenga picos, y mirar una tira de cuadros consecutivos; si hay salto, corregir antes de lanzar. Además, ninguna toma debe quedar tapada por una puerta o un objeto que ocupe todo el plano.
10. **Vehículos siempre apoyados en el suelo (regla del dueño, 20/11/2026, p016):** las ruedas tocan el piso: ni flotando ni hundidas. Antes de renderizar, para cada auto calcular el punto más bajo de CADA rueda en coordenadas de mundo (cuadro inicial y alguno en movimiento, también sobre rampas o cuestas) y comprobar que coincide con la altura del suelo (tolerancia 5 mm). No alcanza con alinear la carrocería: las ruedas de un mismo modelo pueden tener radios o alturas distintos (en p016 las traseras del McLaren quedaron ~3 cm arriba porque se calzó sólo la delantera). Si difieren, ajustar cada eje (altura por eje y cabeceo) y mirar una toma baja del contacto rueda-asfalto.

11. **Voces (regla del dueño, 21/11/2026, Temporada piloto):** no usar una sola voz para todo. Elegir la voz según el tipo de video y de contenido (documental/científico sereno, gancho enérgico, humor, emotivo, personajes distintos con voces distintas) y variar entre videos; para escenas con personajes, una voz por personaje. Reparto disponible: `config/voces.json` y `python -m estudio voces-lista`. Cada beat del guion puede llevar su propio `rol` o `voice_id` (`temporada_01/narrar.py`). Estimar antes de gastar y respetar `config/presupuesto_audio.json`.

## FLUJO DEFINITIVO (19/11/2026, `docs/FLUJO_DEFINITIVO.md`): creo → previa → correcciones → aprobada → la nube entrega
- Crear la escena → `python -m estudio previa <escena.json> --salida <scratchpad>/previa --audio` → mandar GLB + JSON +
  M4A por el chat y registrar la entrega. Correcciones = versión nueva + previa nueva. Nada de render en la revisión.
- Cuando el dueño dice que está **aprobada**: `python -m estudio aprobar <escena.json> --nota "<su frase>"`, commit +
  push y lanzar `publicar_escena.yml` (entrada `escena`). Esa frase es la autorización: el flujo publica BLEND + WAV
  (`audio_escena.py`) + voces/alineaciones + manifiesto y dispara solo `render_escena.yml` hasta el MP4 final. No pedir
  otra aprobación ni usar entornos protegidos de GitHub. Si una verificación falla: contarle al dueño cuál.
- Nunca: publicar sin aprobación, reconstruir una versión aprobada, tocar el sistema de voces/labios, normalizar o
  correr el audio final.

## Render: lo ordena el dueño en el chat (candado QUITADO el 18/11/2026)
- El dueño pidió sacar el candado de la app: `config/candado_render.json` → `"activo": false`. Con eso, cuando el dueño
  dice en el chat «renderizá …», Claude lanza el render (`render.yml`, `video30.yml`, `episodio.yml` o los comandos) sin
  pedir APROBAR ni AUTORIZAR en la app; `estudio/autorizacion.py` responde «candado QUITADO» y deja pasar.
- Claude sigue SIN renderizar por iniciativa propia: nada de renders de prueba, para mostrar ni automáticos. La revisión
  es en el visor HTML (`docs/VISOR_Y_ORDENES_DE_CAMARA.md`) o en el EDITOR 3D de la app, sin render.
- Para volver a poner el candado (render sólo con APROBAR + AUTORIZAR en la app, misma huella y configuración):
  `"activo": true` (detalle en docs/REVISION_Y_AUTORIZACION.md). Claude nunca crea pedidos `[AUTORIZACIÓN]` ni
  `[REVISIÓN] … APROBAR`.

## Previsualización y aprobación ANTES del render (docs/EDITOR_3D.md)
- Toda escena nueva o corregida: pasarle el GLB del visor por el chat (`python -m estudio previa`, ver
  docs/VISOR_Y_ORDENES_DE_CAMARA.md) o publicarlo con `previa.yml` para la app. **Nada de render final durante la revisión.**
- Pedidos `[DIRECCIÓN]` (etiqueta `direccion`): leer `python -m estudio direccion <produccion>` y los archivos de
  `producciones/<produccion>/director/` (cámaras en coordenadas de Blender: usar los números, nunca adivinar desde una
  captura). Aplicar en una versión NUEVA (`aplicar-direccion` para cámaras), publicar la previsualización nueva,
  comentar y cerrar el pedido. No tocar lo que la corrección no menciona.
- Render final: lo pide el dueño por el chat mientras el candado esté quitado (ver arriba).

## Construcción por componentes (docs/SISTEMA_COMPONENTES.md)
- Elegir clips por su DESCRIPCIÓN: `python -m estudio clips buscar …` y mirar `clips ficha` antes de usarlos;
  `validar --recursos` avisa los de estilo marcado (borracho, herido, «llevando a alguien»…). Nunca elegir sólo por
  velocidad o nombre de archivo.
- Correcciones chicas: `trabajo actualizar` (rehace sólo lo afectado: una cámara, un personaje) y `--previa` para el
  visor. Lo entregado tiene `entregado.json` y no se sobrescribe; si falta un recurso, la preparación se detiene.

## Pipeline Godot → GLB → AutoFinisher → .blend → Cycles (docs/AUTOFINISHER.md, docs/CONSTRUIR_Y_RENDERIZAR.md)
- Construir una versión = `construir_produccion.yml` (Godot → GLB → AutoFinisher → `.blend` autónomo + manifiesto con
  SHA-256 → Release `blend-<prod>-v<NNN>`). Una versión publicada es inmutable: cualquier cambio es una versión nueva.
- Renderizar = `render_desde_blend.yml` sobre una versión publicada: nunca instala Godot ni reconstruye la escena;
  verifica el hash, no rellena cuadros faltantes (recuperación explícita con `cuadros` + `corrida_previa`).
- Efectos: sólo los que pide la receta, deterministas por cuadro (`estudio/autofinisher/recetas_efectos/`). La prueba
  original `pruebas/godot_blender/` no se toca.
- **Modalidad 2 — BLEND externo aprobado** (docs/CONSTRUIR_Y_RENDERIZAR.md §5 bis): lo que el dueño aprueba en Blender
  es exactamente lo que se renderiza. `python -m estudio.autofinisher aprobar-blend` registra el SHA-256 en
  `producciones/<p>/versiones/v<NNN>.aprobacion.json` (sin tocar el `.blend`) → el BLEND viaja por Git LFS a
  `producciones/<p>/blend/<p>_v<NNN>.blend` (en el historial queda sólo el puntero; regla 5 respetada) →
  `incorporar_blend.yml` lo baja de LFS, verifica el hash, lo publica byte a byte y llama al render con ajustes
  bloqueados. Nunca reconstruir ni
  «arreglar» un BLEND aprobado: si no cumple el perfil 720p, se rechaza y se avisa.

## Revisión rápida en el navegador (visor HTML)
El dueño revisa con `visor/visor_escena.html` y manda por el chat un texto `VISOR DE ESCENA …` con un JSON
`estudio.visor_ordenes/2`: aplicarlo como dice `docs/VISOR_Y_ORDENES_DE_CAMARA.md` (versión nueva, sin render).

## Pedidos del dueño desde la app
Issues abiertos con etiqueta `correccion` (bloque JSON con producción, escena, versión y nota). Atenderlos con una
versión nueva sólo de esa escena; comentar el resultado en el issue y cerrarlo.
