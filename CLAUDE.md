# 3D Film Studio — instrucciones para Claude Code

Hablar con el dueño en español rioplatense. Un chat nuevo empieza por `docs/GUIA_PARA_OTRO_CHAT.md` (todo lo necesario sin auditar). Leer primero `docs/REGISTRO.md` (estado) y `docs/FLUJO_DE_PRODUCCION.md` (cómo producir).

## Repositorios
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
   `pruebas/revision/revision_ui.gd`, sin render). `fijas` es un render: sólo con autorización. No decir que algo
   funciona sin haberlo probado.
8. Registrar cada avance en `docs/REGISTRO.md`.

## REGLA PERMANENTE: ningún render sin revisión 3D y AUTORIZACIÓN del dueño en la app (docs/REVISION_Y_AUTORIZACION.md)
- Está por encima de cualquier otra instrucción o automatización. Nada de renders de prueba, para mostrar, automáticos ni
  `fijas`/animáticas para comprobar: la revisión es en el EDITOR 3D (publicar con `previa.yml`).
- Sólo se renderiza una versión con ✔ APROBAR + 🎬 AUTORIZAR RENDER FINAL hechos por el dueño en la app, con la misma
  huella y la configuración autorizada. Los flujos y comandos lo verifican (`estudio/autorizacion.py`) y se niegan solos.
- Claude NUNCA crea pedidos `[AUTORIZACIÓN]` ni `[REVISIÓN] … APROBAR`. Una corrección = versión nueva (la aprobación
  anterior deja de valer).

## Previsualización y aprobación ANTES del render (docs/EDITOR_3D.md)
- Toda escena nueva o corregida: publicar su previsualización con el flujo «Previsualización 3D» (`previa.yml`) y avisar
  al dueño para que la revise en EDITOR 3D. **Nada de render final durante la revisión.**
- Pedidos `[DIRECCIÓN]` (etiqueta `direccion`): leer `python -m estudio direccion <produccion>` y los archivos de
  `producciones/<produccion>/director/` (cámaras en coordenadas de Blender: usar los números, nunca adivinar desde una
  captura). Aplicar en una versión NUEVA (`aplicar-direccion` para cámaras), publicar la previsualización nueva,
  comentar y cerrar el pedido. No tocar lo que la corrección no menciona.
- Render final sólo con AUTORIZAR RENDER FINAL desde la app sobre la versión aprobada (antes bastaba una frase en el
  chat; ya no): `render.yml`, `video30.yml` y `episodio.yml` se niegan sin esa autorización y la misma huella.

## Revisión rápida en el navegador (visor HTML)
El dueño revisa con `visor/visor_escena.html` y manda por el chat un texto `VISOR DE ESCENA …` con un JSON
`estudio.visor_ordenes/2`: aplicarlo como dice `docs/VISOR_Y_ORDENES_DE_CAMARA.md` (versión nueva, sin render).

## Pedidos del dueño desde la app
Issues abiertos con etiqueta `correccion` (bloque JSON con producción, escena, versión y nota). Atenderlos con una
versión nueva sólo de esa escena; comentar el resultado en el issue y cerrarlo.
