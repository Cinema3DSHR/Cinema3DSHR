# Sistema de componentes y escena de trabajo (18/11/2026)

Objetivo: que un cambio chico (una cámara, un clip, un audio) no obligue a rearmar la escena entera. Nada de esto
renderiza. La receta `escena.json` sigue siendo la fuente; no cambió de formato.

## 1. Qué es cada cosa

| archivo | qué es | se edita | en Git |
|---|---|---|---|
| `producciones/<p>/escenas/<e>/v<k>/escena.json` | **receta** (original de producción) | sí, mientras no esté entregada/aprobada | sí |
| `…/v<k>/entregado.json` | huellas (sha256) de la receta y de lo que se le dio al dueño | no | sí |
| `$CINE_TRABAJO/<p>/<e>/v<k>/escena.blend` | **escena de trabajo** de Blender (editable, derivada de la receta) | sólo con `trabajo actualizar` | no |
| `$CINE_TRABAJO/<p>/<e>/v<k>/estado.json` | huellas de los componentes, qué objetos son de cada uno, contexto de las cámaras | no (lo escribe el sistema) | no |
| `<e>_v<k>_previa.glb` + `.json` | **previsualización liviana** del visor (materiales planos, mallas alivianadas) | no | no (Releases) |
| render final (mp4, fotogramas) | entregable | no | no (Releases) |

`CINE_TRABAJO` por defecto es `../trabajo_cine` (al lado del repo). `CINE_RAIZ` cambia la raíz contra la que se
resuelven las rutas de las recetas (por defecto, este repo).

## 2. Componentes (`estudio/componentes.py`, sin Blender)

La receta se divide en: `tiempo`, `escenario` (generador + parámetros + eventos), `vehiculo:<id>`,
`personaje:<id>`, `despues` (lo que el escenario arma con los personajes ya hechos: la utilería), `pelota`,
`camara:<toma>`, `render` y `sonido`. Cada uno tiene identificador, tipo, dependencias y **huella** = sha256 de su
porción de la receta + el código que lo arma + sus recursos (audios y marcas de tiempo por contenido; FBX/GLB
externos por ruta y tamaño).

Detección de cambios: se comparan las huellas con las guardadas en `estado.json`; lo que cambió y todo lo que depende
de eso se rehace. Ejemplos (probados):

| cambio | se rehace |
|---|---|
| lente, posición, objetivo, movimiento o tiempos de UNA toma | sólo esa cámara |
| un clip, una expresión, una mirada o un audio de un personaje | ese personaje + la utilería + las cámaras que lo siguen o miran |
| la utilería (`PARAMETROS_DESPUES` del generador) | la utilería + las cámaras que siguen a los personajes |
| calidad, muestras, vertical, exposición | sólo los ajustes de render |
| la mezcla de sonido | nada en Blender |
| duración, escenario (parámetros, eventos, código), vehículos, pelota | **todo** (es la base de la escena) |

Un generador declara en `PARAMETROS_DESPUES` los parámetros que usa sólo `despues_personajes`, y su
`DEPENDENCIAS` tiene que ser una **lista literal** (Actions la lee sin importar el módulo).

## 3. Escena de trabajo (`estudio/blender/trabajo.py`)

```bash
python -m estudio componentes <escena.json>                 # qué componentes hay y qué cambió (sin Blender)
$PY -m estudio trabajo construir <escena.json> [--previa DIR]   # una vez: arma todo y lo guarda
$PY -m estudio trabajo actualizar <escena.json> [--previa DIR]  # después: rehace sólo lo afectado
```

- `construir` usa las mismas fases del director (`fase_escenario`, `fase_personajes`, `fase_despues`,
  `fase_muestreo`, cámaras, `fase_cierre`) y etiqueta cada objeto con su componente (`cine_componente`).
- `actualizar` abre la escena guardada, borra los objetos de los componentes afectados y los vuelve a crear; las
  cámaras se rehacen con el contexto guardado (anclas y trayectorias muestreadas de los personajes), sin tocar
  personajes ni escenario. Si cambió la base, lo dice y rehace todo.
- Una **versión nueva** sin escena de trabajo hereda (copia) la de la versión anterior: una corrección de cámara en
  v2 rehace sólo esa cámara y la escena de v1 no se toca.
- `--previa` exporta GLB + JSON del visor desde la escena de trabajo; la exportación aliviana materiales y mallas en
  memoria y la escena de trabajo NO se vuelve a guardar después (comprobado por sha256). Se niega a escribir encima de
  un archivo registrado como entregado.

Tiempos medidos en la prueba (escenario mínimo + un personaje humano): armar todo 17 s · una cámara 0,1 s · un
personaje 19 s (con un escenario pesado como el de E02 el ahorro al rehacer un personaje es mucho mayor: el escenario
no se rehace).

## 4. Protección de lo entregado (`estudio/proteccion.py`)

`entregado.json` guarda las huellas de la receta y de los derivados entregados. `MF.escribir` y los armadores de
«A la deriva» se niegan a sobrescribir una receta entregada o aprobada (`bloqueada`). `proteccion.verificar(ruta)`
comprueba que la receta y los derivados que estén a mano sigan intactos (lo usa `pruebas/sistema/test_componentes.py`).

## 5. Recursos y rutas (`estudio/recursos.py`, `config.ruta_recurso`)

- Las rutas de las recetas son relativas a la raíz (`CINE_RAIZ`). Las recetas viejas de Dúo Cero tienen rutas
  absolutas («/home/user/Cinema3DSHR/audio/…»): no se editan (están publicadas); `config.ruta_recurso` las resuelve en
  la raíz y `validar --recursos` lo informa como aviso.
- `python -m estudio validar --recursos <escena.json>` comprueba audios (existen y ffprobe los abre), marcas de
  tiempo por letra (JSON con `characters`), audios de la mezcla (en la biblioteca) y recursos externos (clips,
  modelos, muebles). `previa`, `trabajo` y el director cortan la preparación si falta algo: **nunca** se reemplaza la
  voz real por sílabas inventadas (antes, si faltaba un audio, la boca se movía con el texto sin avisar).

## 6. Biblioteca de clips (`estudio/clips.py`, `estudio/blender/ficha_clip.py`)

- `python -m estudio clips buscar <texto> [--funcion caminar] [--neutros]`: busca en la DESCRIPCIÓN del catálogo
  (6.515 clips), no en el nombre del archivo. «Walking_2» se llama igual que una caminata normal y es «Male Drunk
  Walk».
- `validar --recursos` avisa cada clip con estilo marcado (borracho, herido, brutal, boxeo, «llevando a alguien»…);
  si es a propósito, la acción lleva `"estilo_confirmado": true`.
- `$PY -m estudio clips ficha <ref> …`: el esqueleto del clip de costado y de frente en 8 momentos, con su
  descripción, duración y velocidad (dibujado con Pillow, no es un render). Mirarla ANTES de usar un clip.

## 7. Pruebas

- `python pruebas/sistema/test_componentes.py` (sin Blender, segundos): las 23 recetas del repo se leen y se dividen
  en componentes; detección de cambios; rutas; recursos; protección; avisos de clips. **16/16**.
- `$PY pruebas/sistema/test_trabajo.py` (Blender, ~3 min, sin render): escena de trabajo con el escenario
  `prueba_minima`; cambiar una cámara y un clip rehace sólo lo afectado y el resultado (caderas y cámaras) es igual
  al de armar de cero; una versión nueva hereda; exportar no modifica la escena. **19/19**.
- El director partido en fases da exactamente lo mismo que antes: la previsualización de E01 v2 armada de nuevo
  coincide con la anterior (caderas, cámaras y tomas, diferencia 0).

## 8. Límites que quedan

- Cambiar el escenario (o sus eventos) rehace todo: no hay reconstrucción parcial de un escenario.
- Vehículos y pelota: sin actualización parcial (cuentan como base).
- La previsualización se vuelve a exportar entera (GLB + JSON, ~1–2 min en escenas grandes); el visor no puede
  recibir sólo una cámara nueva sin cambiar el visor HTML y la app.
- La escena de trabajo vive fuera de Git (contenedor efímero): si se pierde, se reconstruye desde la receta.
- Los flujos de Actions (render) siguen armando la escena completa desde la receta (no se tocaron).
