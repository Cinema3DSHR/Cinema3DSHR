# Metodología de trabajo de Cinema3DSHR (definitiva, 19/11/2026)

**Godot → Blender → GLB de revisión → aprobación → render final.** Es la ÚNICA metodología autorizada para todas las
producciones, por orden del dueño. Es permanente: no se cambia, no se proponen otros flujos ni se vuelve a preguntar
qué modalidad usar hasta que el dueño diga expresamente otra cosa.

> Una escena, una preparación artística, una revisión y un render final. Sin reconstrucciones innecesarias ni
> circuitos paralelos.

## 1. Godot: construcción de la escena

Godot es donde se construye la escena original:

- escenarios y espacios;
- personajes, vehículos y objetos, y cómo se conectan;
- animaciones, movimientos, interacciones y secuencias;
- cámaras, recorridos y cambios de plano;
- duración y línea de tiempo.

Hay que comprobar que todo funcione. La iluminación cinematográfica y los efectos no hace falta terminarlos acá: son
de Blender. Con la estructura, las animaciones y las cámaras andando, se exporta a GLB para llevarla a Blender.

## 2. Blender: terminación artística y cinematográfica

Una vez importada, Blender es el entorno principal. Ahí se hacen:

- luces principales, secundarias y ambientales;
- materiales, texturas, reflejos y superficies;
- humo, niebla, volúmenes, partículas, fuego, atmósfera y haces de luz;
- ajustes de cámara y composición;
- la configuración de Cycles.

Cualquier problema artístico o visual se corrige en Blender.

**No volver a Godot por cosas de Blender.** Humo chico, niebla densa, luces débiles, materiales o reflejos mal, texturas
que faltan: todo eso se corrige en Blender, sin reconstruir desde Godot.

Sólo se vuelve a Godot cuando el problema es de la construcción:

- una animación mal hecha (camina en vez de correr, una puerta con la trayectoria mal);
- un objeto mal conectado;
- una interacción que no funciona;
- el escenario que hay que cambiar.

En ese caso se corrige en Godot, se exporta una versión nueva y se sigue en Blender.

## 3. Conservar el trabajo de Blender

Las correcciones normales se hacen sobre el proyecto Blender existente. Si el BLEND se regenera con scripts, los
scripts tienen que conservar TODOS los ajustes artísticos y dar un resultado reproducible. No se reimporta el GLB ni
se rehace el proyecto por un ajuste de humo, luces, materiales o niebla.

El BLEND es autónomo, con las texturas y dependencias empaquetadas.

## 4. Previsualización para el dueño (desde Android)

Se entrega:

- **el GLB exportado desde Blender**, que es el entregable principal y lleva todo lo que el formato puede llevar;
- **el JSON** con la línea de tiempo, las cámaras, los cortes, los eventos y la duración;
- **imágenes fijas de referencia**, sólo para lo que el GLB no muestra (volúmenes, haces de luz).

Nunca se entrega:

- el BLEND, que es interno;
- videos de muestra;
- renders intermedios;
- secuencias de cuadros.

El único video es el MP4 final.

## 5. Correcciones

- **Estructura o animación:** se corrige en Godot (sólo eso).
- **Algo visual:** se corrige en Blender.

Después va un GLB nuevo y se conserva el resto. No se reinicia la producción por una corrección puntual. Se repite
hasta que el dueño esté conforme.

## 6. Aprobación y render final

Cuando el dueño dice «aprobada», «está bien» o «renderizá», esa frase autoriza la producción final de la versión
revisada. No hay una segunda aprobación en GitHub. Pasos:

1. Identificar el BLEND exacto del GLB aprobado.
2. Calcular su SHA-256 y comprobar que no cambió desde la revisión. Si cambió, detenerse y avisar qué cambió: nunca
   se reemplaza la versión aprobada en silencio.
3. Registrar la aprobación y el hash:
   `python -m estudio.autofinisher aprobar-blend` → `producciones/<p>/versiones/v<NNN>.aprobacion.json`.
4. Transferir el BLEND a GitHub con **Git LFS**: se copia a `producciones/<p>/blend/<p>_v<NNN>.blend` (en el
   historial queda sólo el puntero, por `.gitattributes`), y se hace commit y push.
5. `incorporar_blend.yml`: baja el archivo de LFS y verifica que sea idéntico (SHA-256 del registro). Lo inspecciona en
   sólo lectura, arma el manifiesto y publica la Release `blend-<p>-v<NNN>`.
6. El mismo flujo dispara `render_desde_blend.yml`, que renderiza directamente desde el BLEND aprobado. Cada trabajo
   verifica el hash y no se permite cambiar resolución ni muestras.
7. El montaje conserva el audio original y su sincronización cuando hay sonido. El MP4 queda en la misma Release.

Después de la aprobación nunca se reconstruye la escena ni se corre el AutoFinisher para producir algo distinto.

## 7. Configuración obligatoria del render

| | |
|---|---|
| Resolución | 1280 × 720 (16:9). Nunca 1920 × 1080. |
| Frecuencia | 30 fps |
| Motor | Cycles, en CPU |
| Muestras | 6 |
| Muestreo adaptativo | umbral 0,05 |
| Denoiser | OpenImageDenoise |
| Rebotes | 6 |
| Light Tree | activado |
| Semilla | fija |

El render usa hasta 60 trabajos en paralelo. Esta configuración está en código como `PERFIL_720P`
(`estudio/autofinisher/blend_externo.py`), y un BLEND que no la cumple se rechaza al aprobarlo.

## 8. Entrega final

El dueño recibe:

- el MP4 final, que se puede descargar directo desde Android;
- un informe breve de validación.

Al dueño nunca se le pide que suba archivos, cree Releases ni haga transferencias técnicas. Lo único que hace el dueño
es revisar el GLB, pedir correcciones, aprobar y recibir el MP4.

## 9. Reglas que no se incumplen

- No cambiar esta metodología sin autorización expresa del dueño.
- No crear pipelines alternativos por iniciativa propia.
- No reconstruir una escena entera por una corrección visual.
- No volver a Godot por efectos que corresponden a Blender.
- No enviar el BLEND al dueño.
- No generar videos de muestra.
- No hacer renders finales antes de la aprobación.
- No publicar Releases ni ejecutar GitHub Actions antes de la aprobación.
- No regenerar voces, animaciones o recursos que ya existen.
- No reemplazar una versión aprobada por otra.
- No pedirle al dueño operaciones técnicas que corresponden al sistema.
