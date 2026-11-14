# App Android — 3D Film Studio (Godot 4.7.2)

## Qué es

Cliente **liviano** (sólo interfaz; nada se renderiza en el teléfono). Pantalla horizontal, estética oscura.

| Sección | Qué hace |
|---|---|
| INICIO | Fichas (producciones, para revisar, renderizando, espacio en el servidor y en el teléfono), novedades, últimas producciones, escenas pendientes, en render, aprobadas, aviso de APK nueva. |
| PELÍCULAS | Biblioteca con portada, título, género, estado, escenas, duración. Ficha de cada producción con sinopsis, versiones, escenas ordenadas y EXPORTAR PELÍCULA (resolución, FPS, formato). |
| Escena | Reproductor (⏪10 · ▶/⏸ · 10⏩ · barra · tiempo · pantalla completa), versión y resolución, selector de versiones, APROBAR / RECHAZAR / SOLICITAR CORRECCIONES / VOLVER A RENDERIZAR / VER VERSIÓN ANTERIOR, observaciones en texto libre, historial, tomas (tocar = saltar), guion, DESCARGAR/COMPARTIR MP4, COPIAR ENLACE, GUARDAR SIN CONEXIÓN. |
| VISOR 3D | Escena 3D liviana: girar (1 dedo), acercar/alejar y desplazar (2 dedos), cámaras de rodaje (ver desde cada una), animación con barra de tiempo, luces de la escena / luz de estudio. |
| ESCENARIOS | Escenarios reutilizables con su portada y visor 3D. |
| AJUSTES | Vincular cuenta (token), almacenamiento, versión, descargar la última APK. |

## Instalar

1. GitHub → *Releases* → **app** → `3DFilmStudio.apk` → instalar (permitir «orígenes desconocidos» la primera vez).
2. Las mejoras de la interfaz llegan **solas** al abrir (paquete `app.pck`, cientos de KB).
3. Si cambia el motor o el lanzador, la app ofrece una APK nueva: se instala **encima**, sin desinstalar ni
   perder datos, porque siempre se firma con la misma clave.

## Firma (una sola vez, la hace el dueño)

GitHub → repo **Cinema3DSHR** → *Settings* → *Secrets and variables* → *Actions* → *New repository secret*:

- Nombre: `ANDROID_KEYSTORE_PASSWORD`
- Valor: una contraseña larga inventada por vos (24+ caracteres al azar; guardala en tu gestor de contraseñas).

La primera compilación con ese secreto crea la clave, la guarda **cifrada** en la release `firma` y anota la
huella pública en `app.json`. **No borrar la release `firma`**: sin ella, la próxima APK obligaría a desinstalar.
Sin el secreto, el flujo arma una APK de PRUEBA con firma temporal (sólo como artefacto, no se publica).

## Vincular la cuenta (para aprobar y pedir cambios)

1. GitHub → *Settings* → *Developer settings* → *Fine-grained tokens* → *Generate new token*.
2. *Repository access*: sólo **Cinema3DSHR**. *Permissions*: **Issues: Read and write** (nada más).
3. En la app: AJUSTES → pegar → GUARDAR → PROBAR CONEXIÓN.
El token queda cifrado en el teléfono (clave derivada del dispositivo). Sin token la app funciona en modo lectura.
Si no hay conexión al decidir, la decisión queda en cola y se envía sola al volver.

## Sincronización

La app sólo consulta `catalogo.json` (release `catalogo`). Cada archivo del catálogo trae URL, tamaño y SHA-256:
lo descargado se guarda en `user://cache` y no se vuelve a bajar si no cambió; se puede ver sin conexión.
Las «novedades» se calculan contra lo ya visto en el teléfono. (Las notificaciones del sistema Android necesitan
un plugin nativo: quedan para más adelante; hoy las novedades se ven al abrir la app.)

## Compilar (lo hace `.github/workflows/apk.yml`)

Cada push a `app/**`: exporta la APK (arm64, firmada) y `app.pck`, y publica `app.json` → `app.pck` → APK en la
release `app`. Época de APK: `app/apk_epoca.txt` (subirla sólo si cambia el motor o `app/boot/`).

## Probado en esta sesión (sin teléfono)

- Todos los scripts compilan en Godot 4.7.2 (headless).
- Recorrido automático de todas las páginas con un catálogo real: el OGV se reproduce, el salto de 10 s funciona,
  el visor carga 7 cámaras, 39 luces y la animación; capturas reales con Xvfb.
- **No probado en un teléfono** todavía: tacto real, gestos de dos dedos, rendimiento del visor en GPU móvil.
