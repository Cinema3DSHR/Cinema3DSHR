# 3D Film Studio — instrucciones para Claude Code

Hablar con el dueño en español rioplatense. Leer primero `docs/REGISTRO.md` (estado) y `docs/FLUJO_DE_PRODUCCION.md` (cómo producir).

## Repositorios
- **Cinema3DSHR** (este, público): todo el trabajo. Rama de la sesión indicada por el sistema.
- **mixamo-respaldo** (privado): animaciones originales. **Sólo lectura** — nunca borrar, mover ni sobrescribir.
- Operaci-n-Nexus-1 / Extraction-tactical: sólo para tomar recursos (armas, operador, audio). No auditarlos.

## Reglas
1. No borrar ni modificar originales; índices y metadatos van aparte (`catalogo/`).
2. Reutilizar antes de crear (catálogos, escenarios). Tripo3D sólo con autorización y comprobando el costo antes.
3. Nada de servicios pagos sin avisar. ElevenLabs: pedir la clave como credencial del entorno, nunca por chat.
4. Ningún secreto en el repo, la APK, registros ni el chat.
5. Videos, .blend, GLB y fotogramas **nunca** al historial de Git (van a Releases por los flujos de Actions).
6. Versiones: una versión publicada no se edita; correcciones = `python -m estudio nueva-version`. Las aprobadas
   llevan `"bloqueada": true`.
7. Antes de subir una escena: `validar` y `fijas` (mirar las imágenes). No decir que algo funciona sin haberlo probado.
8. Registrar cada avance en `docs/REGISTRO.md`.

## Pedidos del dueño desde la app
Issues abiertos con etiqueta `correccion` (bloque JSON con producción, escena, versión y nota). Atenderlos con una
versión nueva sólo de esa escena; comentar el resultado en el issue y cerrarlo.
