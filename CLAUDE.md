# 3D Film Studio — instrucciones para Claude Code

Hablar con el dueño en español rioplatense. Leer primero `docs/REGISTRO.md` (estado) y `docs/FLUJO_DE_PRODUCCION.md` (cómo producir).

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
7. Antes de subir una escena: `validar` y `fijas` (mirar las imágenes). No decir que algo funciona sin haberlo probado.
8. Registrar cada avance en `docs/REGISTRO.md`.

## Previsualización y aprobación ANTES del render (docs/EDITOR_3D.md)
- Toda escena nueva o corregida: publicar su previsualización con el flujo «Previsualización 3D» (`previa.yml`) y avisar
  al dueño para que la revise en EDITOR 3D. **Nada de render final durante la revisión.**
- Pedidos `[DIRECCIÓN]` (etiqueta `direccion`): leer `python -m estudio direccion <produccion>` y los archivos de
  `producciones/<produccion>/director/` (cámaras en coordenadas de Blender: usar los números, nunca adivinar desde una
  captura). Aplicar en una versión NUEVA (`aplicar-direccion` para cámaras), publicar la previsualización nueva,
  comentar y cerrar el pedido. No tocar lo que la corrección no menciona.
- Render final sólo con la frase del dueño «LA ESCENA ESTÁ BIEN. EMPEZÁ CON EL VIDEO» y sobre la versión aprobada:
  `video30.yml` se niega si la versión no está aprobada con la misma huella.

## Pedidos del dueño desde la app
Issues abiertos con etiqueta `correccion` (bloque JSON con producción, escena, versión y nota). Atenderlos con una
versión nueva sólo de esa escena; comentar el resultado en el issue y cerrarlo.
