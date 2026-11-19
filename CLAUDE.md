# 3D Film Studio — instrucciones para Claude Code

Hablar con el dueño en español rioplatense. Un chat nuevo empieza por `docs/GUIA_PARA_OTRO_CHAT.md` (todo lo necesario sin auditar). Leer primero `docs/REGISTRO.md` (estado) y `docs/FLUJO_DE_PRODUCCION.md` (cómo producir).

## Repositorios
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

## Revisión rápida en el navegador (visor HTML)
El dueño revisa con `visor/visor_escena.html` y manda por el chat un texto `VISOR DE ESCENA …` con un JSON
`estudio.visor_ordenes/2`: aplicarlo como dice `docs/VISOR_Y_ORDENES_DE_CAMARA.md` (versión nueva, sin render).

## Pedidos del dueño desde la app
Issues abiertos con etiqueta `correccion` (bloque JSON con producción, escena, versión y nota). Atenderlos con una
versión nueva sólo de esa escena; comentar el resultado en el issue y cerrarlo.
