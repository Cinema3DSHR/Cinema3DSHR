# Guía para otro chat de Claude: cómo trabajar en la organización Cinema3DSHR

Leé esto primero, antes de abrir otros archivos. Sirve para trabajar sin auditar los repositorios. Si algo de acá no
coincide con el código, **manda el código**: corregí esta guía en el mismo cambio. Estado al 18/11/2026.

> **18/11/2026: revisión rápida con el visor HTML.** El dueño revisa las escenas en el navegador con
> `visor/visor_escena.html` (https://claude.ai/artifact/SEW8AN7eTVhb1t3vaRAvJq): Claude le pasa el GLB + JSON de
> `python -m estudio previa` por el chat y el dueño devuelve un texto con cámaras nuevas o modificadas y notas.
> **Cómo recibirlo y aplicarlo: `docs/VISOR_Y_ORDENES_DE_CAMARA.md`.**

---

## 1. Quién es el dueño y cómo hablarle

- El dueño es la cuenta de GitHub **`webmaletin-art`**. Es la única cuenta autorizada (`config/autorizados.json`).
- Hablale en **español rioplatense** (vos, tenés, probá), con frases cortas y sin jerga. Trabaja desde un teléfono
  Android: prueba todo con la **app del estudio** y con GitHub en el celular.
- No inventes resultados. No digas que algo funciona sin haberlo probado, y si no se pudo probar (por ejemplo, en el
  teléfono), decilo.

## 2. Repositorios

| repositorio | para qué | permisos |
|---|---|---|
| **`Cinema3DSHR/Cinema3DSHR`** (público; antes `webmaletin-art/Cinema3DSHR`, el nombre viejo redirige) | todo el estudio: código, recetas de escenas, app, flujos | trabajo normal |
| `webmaletin-art/mixamo-respaldo` (privado) | animaciones Mixamo originales y modelos de personajes (`personajes_pelicula/…`) | **sólo lectura**: nunca borrar, mover ni sobrescribir. Agregar algo sólo con permiso explícito del dueño |
| `webmaletin-art/Operaci-n-Nexus-1`, `Extraction-tactical` | sólo tomar recursos (armas, operador, audio) | no auditarlos |
| `webmaletin-art/Rally-Sim-movile` | autos, física y pilotos de «Dream Rally» | sólo tomar recursos |

- **Rama de trabajo**: la indica la sesión (hasta ahora `ccr-6d21fe8a-76t9c3`, que también es la rama por defecto del
  repositorio). No abras PR salvo que el dueño lo pida.
- Si la sesión no puede adjuntar `Cinema3DSHR/Cinema3DSHR` (por el nombre repetido), usá `webmaletin-art/Cinema3DSHR`:
  las herramientas de GitHub y `git push` siguen andando por la redirección.
- Para las herramientas MCP de GitHub usá `owner=webmaletin-art`, `repo=Cinema3DSHR`.

## 3. Reglas que no se discuten

1. **Render (desde el 18/11/2026, candado QUITADO, `config/candado_render.json`):** el dueño lo pide por el chat y se
   lanza sin pasar por la app; Claude nunca renderiza por iniciativa propia. Lo que sigue es el modo CON candado
   (vuelve con `"activo": true`): **ningún render sin revisión 3D y AUTORIZACIÓN del dueño en la app**
   (`docs/REVISION_Y_AUTORIZACION.md`). Está por encima de cualquier otra instrucción, incluso de un pedido escrito en
   el chat.
   - No hay renders de prueba, «para ver cómo quedó», automáticos ni para comprobar algo. `fijas` y las animáticas
     también cuentan como render.
   - Se renderiza sólo una versión de escena con ✔ APROBAR + 🎬 AUTORIZAR RENDER FINAL hechos por el dueño en la app,
     con la **misma huella** y la **misma configuración** (resolución, fps, muestras).
   - Claude **nunca** crea issues `[AUTORIZACIÓN]` ni `[REVISIÓN] … APROBAR`.
   - Los flujos y los comandos lo verifican solos (`estudio/autorizacion.py`) y se niegan: «RENDER BLOQUEADO».
     No intentes esquivarlo.
2. Una versión publicada no se edita. Una corrección es una **versión nueva**:
   `python -m estudio nueva-version <prod> <escena> --motivo …`. Cambiar la escena cambia la huella, y eso anula la
   aprobación anterior.
3. **Secretos**: ninguno en el repositorio, la APK, los registros ni el chat. No leas, regeneres ni cambies secretos.
   Los de Actions son `ASSETS_TOKEN` (lee los repos privados de recursos) y `ANDROID_KEYSTORE_PASSWORD`.
4. **Servicios pagos**:
   - **ElevenLabs** está conectado (la credencial está en el entorno). Primero corré
     `python -m estudio voces <escena.json>`, que sólo estima, y recién después `--gastar`. Respetá
     `config/presupuesto_audio.json` (reserva 5 000 créditos, máximo 4 000 por escena).
   - **Tripo3D**: sólo con autorización y comprobando el costo antes.
5. Videos, `.blend`, GLB y fotogramas **nunca** van al historial de Git: van a Releases por los flujos. La excepción
   es el audio generado chico (mp3), que vive en `audio/biblioteca/`.
6. Registrá cada avance en **`docs/REGISTRO.md`** (fecha UTC, qué se pidió, qué se hizo, qué se probó).
7. Commits que tocan escenas: agregales `[skip ci]` al mensaje. Al final de cada commit van las líneas de atribución
   que indique la sesión.
8. No inicies nada que el dueño pidió no iniciar. Si dice «no lances X sin mi autorización», esperá su frase.

## 4. Cómo está armado el estudio (mapa mental)

```
Claude escribe una RECETA  producciones/<prod>/escenas/<eNN>/v<k>/escena.json
        │   (las de Dúo Cero se generan con producciones/p009_duo_cero/herramientas/escenas.py)
        ▼
python -m estudio validar <escena.json>
        ▼
previa.yml  (Actions, a mano) ── Blender sin render ──► Release <prod>: <e>_v<k>_previa.glb + .json (línea de tiempo)
        ▼                                                └─► catalogo.yml rearma catalogo.json (release «catalogo»)
App Android → PELÍCULAS → producción → escena → 🎬 EDITOR 3D
   el dueño revisa en 3D ── correcciones ──► Issues [DIRECCIÓN] / [REVISIÓN] CORREGIR ──► Claude hace una versión nueva
                         ── ✔ APROBAR + 🎬 AUTORIZAR RENDER FINAL ──► Issues [REVISIÓN] APROBAR / [AUTORIZACIÓN]
        ▼
render.yml / episodio.yml / video30.yml (a mano; verifican la autorización antes de pedir máquinas y en cada trabajo)
        ▼
Release <prod>: MP4, portada, etc. → catálogo → la app lo muestra
```

- **`estudio/`** (Python + `bpy` de Blender): todo el sistema. Entrada: `python -m estudio <comando>` (lista completa
  con `--help`). Lo principal:
  - `manifiesto.py`: recetas, versiones y huella.
  - `autorizacion.py`: los 8 estados y la verificación de render.
  - `publicacion.py`: el catálogo.
  - `blender/director.py`: arma la escena.
  - `blender/camaras.py`: tipos de toma.
  - `blender/personajes.py` + `retarget.py`: personajes Mixamo y clips en pistas NLA con fundidos.
  - `blender/stickman.py`: personajes Stickman con vestuario pintado y rostro 2D.
  - `blender/previa.py`: exportación del EDITOR 3D.
  - `montaje.py`: FFmpeg.
  - `audio/`: sonido procedural y ElevenLabs.
- **`escenarios/<id>/escenario.json`**: escenarios reutilizables con **anclas**. Reutilizá antes de crear (lo mismo
  vale para `catalogo/*.json`: animaciones, armas, vehículos, audio, personajes).
- **`producciones/<prod>/produccion.json`**: datos de la producción, incluida la configuración de render acordada.
- **`app/`**: app Godot 4.7.2 (cliente liviano). Lee `catalogo.json` de la release `catalogo`, muestra los videos y el
  EDITOR 3D, y manda los pedidos como Issues con el token del dueño (`app/main/api.gd`). `apk.yml` la compila en cada
  push a `app/**`. El resto de la app se actualiza sola; la APK sólo cambia de «época» (`app/apk_epoca.txt`) cuando cambian el motor, el lanzador (`app/boot`) o el manifiesto de Android (por ejemplo, la orientación). En ese caso el dueño tiene que reinstalarla.
- **Entorno local** (`docs/FLUJO_DE_PRODUCCION.md` §0): `python3 -m venv /opt/tools/blendenv &&
  /opt/tools/blendenv/bin/pip install -r requirements-produccion.txt`, y `export PY=/opt/tools/blendenv/bin/python`.
  Los repos de recursos se clonan al lado (`../mixamo-respaldo`, …) o se indican con `CINE_MIXAMO_DIR`, etc.

### Flujos de GitHub Actions

| flujo | disparo | qué hace | ¿render? |
|---|---|---|---|
| `previa.yml` | a mano (`escena`) | GLB + línea de tiempo para el EDITOR 3D y catálogo | no |
| `catalogo.yml` | a mano / programado / llamado | rearma `catalogo.json` con manifiestos, releases e issues | no |
| `revisiones.yml` | issue nuevo | registra APROBAR/CORREGIR/RECHAZAR; un `[AUTORIZACIÓN]` se verifica y se contesta (**no** lanza el render) | no |
| `direccion.yml` | issue nuevo | guarda cámaras y notas del director en `producciones/<p>/director/` | no |
| `render.yml` | a mano (`escena`) | render por tomas | **sí, con autorización** |
| `episodio.yml` | a mano (`produccion`, `trabajos` ≤ 60, `escenas`, `prueba`) | render distribuido del episodio por bloques de fotogramas | **sí, con autorización** (también los ensayos) |
| `video30.yml` | a mano | render en paralelo de una escena corta | **sí, con autorización** |
| `pelicula.yml` | a mano | montaje final de escenas ya renderizadas y aprobadas | no renderiza escenas |
| `apk.yml` | push a `app/**` / a mano | APK firmada y su actualización | no |
| `concurrencia.yml` | a mano (`trabajos`, `espera_s`) | sonda: N trabajos que sólo esperan; el trabajo `medir` calcula el máximo simultáneo | no |
| `limpieza.yml`, `verificar-acceso.yml` | programado / a mano | temporales viejos; comprobar que se leen los repos privados | no |

Para lanzar un flujo usá `mcp__github__actions_run_trigger` (`run_workflow`, `ref` = rama de trabajo). Para seguirlo,
`actions_list` / `actions_get` y los registros con `get_job_logs`. La API sin autenticar de este repo está bloqueada
desde la sesión: usá las herramientas MCP.

## 4 bis. Inventario de recursos (qué hay y dónde, sin auditar)

En las recetas y en el código los recursos se nombran `<fuente>:<ruta>` (`estudio/config.py` → `FUENTES`).
`mixamo:` es `webmaletin-art/mixamo-respaldo`, `nexus:` es `Operaci-n-Nexus-1/fuente`, `extraction:` es
`Extraction-tactical/public`, `rally:` es `Rally-Sim-movile`, `sh3d:` son los muebles de Sweet Home de Nexus y
`estudio:` es este repo. Cada carpeta de mixamo-respaldo tiene su índice JSON con medidas, polígonos y sha256.
**Lo que el dueño manda por el chat se pierde con el contenedor**: guardalo en mixamo-respaldo (sólo agregar, con su
permiso) y anotalo en el índice que corresponda y acá.

**Personajes** (`mixamo:personajes_pelicula/`, índice `indice_personajes.json`). Todos son FBX de Tripo3D con
esqueleto `mixamorig` de 65 huesos, así que usan los clips Mixamo con `retarget.py`.

| id | qué es | uso |
|---|---|---|
| `stickman_masculino`, `stickman_femenino` | **Stickman definitivos**, proporcionados a Mixamo (0,979 m al importar) | **todos** los personajes de Dúo Cero (Nico, Luna, guardias); vestuario pintado y rostro 2D con `estudio/blender/stickman.py` |
| `armas_stickman` | pack de armas y linterna estilo Stickman | Dúo Cero (`estudio/blender/armas_stickman.py`) |
| `protagonista_masculino`, `protagonista_femenina` | protagonistas realistas | Operación Tren Fantasma (p006) |
| `messi`, `cristiano` | jugadores (Cristiano con la textura del nombre corregida) | Al vacío (p007) |
| `versiones_anteriores/stickman_*_v1` | primera tanda de Stickman | **no usar**: sólo respaldo |

Además: `mixamo:personajes/ybot_tpose.fbx` (Y Bot, el esqueleto de las 3 099 animaciones de `animaciones/` y
`packs/`, buscables en `indice.json` y en `catalogo/animaciones.json`), `packs_extra_glb/` (personas y perro) y
`modelos_pelicula/jefa_o_novia.glb` (mujer de traje negro, GLB con rig Mixamo).

**Vehículos y decorados** (`mixamo:modelos_pelicula/*.glb`, índice `indice_modelos.json`, vistas previas en
`previews/`). Vienen normalizados a 1 m en su lado más largo, así que hay que escalarlos a su tamaño real:

| id | qué es | tamaño real aprox. |
|---|---|---|
| `helicoptero_militar` | **helicóptero militar** negro de transporte. Es sólo el fuselaje, **sin rotores**: el rotor principal y el de cola se agregan como discos semitransparentes que giran (ver `estudio/escenarios/drift_sunset.py`, función del helicóptero) | 15 m |
| `vehiculo_blindado_policial` | blindado «POLICIA» | — |
| `pickup_arena` | pickup 4×4 blanca | — |
| `auto_clasico_falcon` | auto clásico azul | — |
| `locomotora_diesel`, `vagon_cerrado`, `vagon_plano` | tren | — |
| `trailer_plano_camion` | semirremolque plano | — |
| `moto_enduro_decoracion_taller`, `decoracion_taller_segmentada` | taller mecánico (69 piezas) | — |
| `cocina_sin_segmentos`, `muebles_casa_sin_segmentar` | interiores | — |

Las medidas exactas de cada uno están en el índice. También hay `mixamo:vehiculos_pelicula/auto_rampa/` (auto negro
con jaula y rampa adelante, FBX; mira a +Y y no trae ruedas: se le ponen las de Dream Rally) y
`mixamo:futbol_free_kick_swipe/` (jugador con 3 223 animaciones de fútbol, estadio y los 2 023 clips JSON originales
en `01_animaciones/json_originales/`).

**De los otros repos**:
- Dream Rally (`rally:`): los 28 autos con física real (`estudio/fisica_dr`), pilotos, motos, vegetación y rutas.
- Nexus (`nexus:`): armas, operador, vehículo y audio.
- Extraction (`extraction:`): armas con puntos de agarre.
- Sweet Home (`sh3d:`): 723 muebles, árboles, plantas, puertas y ventanas a escala real. El estudio los lee de
  `Operaci-n-Nexus-1/game/assets/sh3d`. El **pack original completo** (GLB + 723 miniaturas + `models.json` +
  `CREDITS.txt`) está respaldado en `mixamo:sweethome3d/sweethome3d-models-master.zip`. Si Nexus cambiara,
  descomprimilo y apuntá `CINE_SH3D_DIR` a su carpeta `models/`. Respetá las licencias de `CREDITS.txt`.

**Del estudio** (este repo): `escenarios/` (mansión moderna de noche, estadio de fútbol 11 de noche, más los
generadores de `estudio/escenarios/`: tren, ruta del atardecer, etc.), `catalogo/*.json` (animaciones, armas,
vehículos, audio, personajes, modelos) y `audio/biblioteca/` (voces y efectos ya generados: reutilizalos antes de
gastar créditos).

## 5. Recetas de escena (`escena.json`)

Claves: `tipo, id, produccion, numero, version, titulo, guion, duracion_s, escenario, eventos, vehiculos, personajes,
tomas, moviles_escenario, sonido, render, estado, bloqueada, huella_v`. Las tomas tienen que ser contiguas y sumar la
duración (`validar` lo revisa). El formato completo está en `docs/FLUJO_DE_PRODUCCION.md` §4, y los tipos de toma en
§5 y en `estudio/blender/camaras.py`.

Convenciones aprendidas a los golpes (detalle en `docs/ERRORES.md`):
- Los clips de Mixamo se aplican con `retarget.py`. Blender 5 liga cada acción a un «slot»; la cadera se escala por el
  cociente de alturas.
- Los fundidos entre clips van en pistas NLA nuevas. Sólo la de abajo sostiene hacia atrás; las de arriba usan
  `HOLD_FORWARD`.
- Las coordenadas de las cámaras del director están en Blender: usá esos números, nunca adivines desde una captura.

## 6. Estado actual de los trabajos (18/11/2026)

**Dúo Cero (`p009_duo_cero`), Episodio 01**: estilo Stickman, 6 escenas, 180 s, 5 400 fotogramas.
- **Personajes**: modelos definitivos del dueño (Stickman masculino y femenino proporcionados a Mixamo), en
  `mixamo-respaldo/personajes_pelicula/stickman_{masculino,femenino}` y `armas_stickman`. Nico, con corte Kingsman, y
  Luna son los protagonistas. Los guardias tienen cresta o mohicano.
- **Voces**: ElevenLabs v3 rioplatenses, ya generadas (57 líneas y 6 músicas). Nico «Tomas», Luna «Malena», guardia
  «Uriel», Central «Carlos» (`config/voces.json`).
- **Configuración de render fijada por el dueño** (no se cambia): Cycles CPU, **960×540, 30 fps, 6 muestras**,
  adaptativo 0,05, OIDN, 6 rebotes, Light Tree, semilla 0.
- **Revisión**: e01 v1 tiene previsualización publicada y está **LISTA PARA REVISIÓN** (huella `d4d2e3909563bce1`).
  e02–e06 están **EN PREPARACIÓN**: falta publicar su previsualización con `previa.yml`. Nada está aprobado ni
  autorizado todavía, y **no se renderizó el episodio**.
- **Tiempos medidos**: unos 12,2 s por fotograma, unas 18 h de máquina en total, más ~4,5 min fijos por trabajo
  (`docs/informes/duo_cero_ep01_tiempos.md`). Conviene repartirlo en 60 trabajos chicos (~23 min cada uno).

**Concurrencia de GitHub Actions** (`docs/informes/ticket_github_concurrencia.md`):
- El repositorio pasó a la organización Cinema3DSHR (plan Team, 60 trabajos simultáneos en teoría).
- En la práctica dio 7, después 11 y después 13. GitHub Support explicó que una organización nueva tiene un
  **período de arranque de 7 días**: el límite sube solo a medida que terminan trabajos, como mucho cada 10 minutos.
- La forma de medirlo es `concurrencia.yml` con 60 trabajos. El dueño pidió **cancelarla si no supera 20**.
- Episodio completo estimado según el límite: con 13, ~2 h 05 min; con 20, ~1 h 20 min; con 60, ~35 min.

**App**: la APK época 2 (orientación «sensor») arregló que en vertical no respondía ningún botón. El dueño tiene que
instalarla y confirmarlo: no se probó en un teléfono real, sólo con pruebas de toques en Godot.

Otras producciones (p000–p008: mansión, fútbol, tren fantasma, Al vacío, Drift Sunset…): su historia está en
`docs/REGISTRO.md`. No las toques si no te lo piden.

## 7. Cómo atender pedidos típicos

| el dueño pide | qué hacer |
|---|---|
| una escena nueva o corregida | receta → `validar` → `previa.yml` → avisarle que la revise en EDITOR 3D. **No renderizar** |
| issue `correccion` / `[DIRECCIÓN]` | `python -m estudio direccion <prod>` + `producciones/<p>/director/` → versión nueva sólo de esa escena (`aplicar-direccion` para las cámaras) → `previa.yml` → comentar el issue y cerrarlo. No toques lo que no se menciona |
| «renderizá» | con el candado quitado: lanzar `episodio.yml` / `render.yml` / `video30.yml` con la configuración de la producción. Con el candado puesto: revisar `python -m estudio autorizacion estado <prod> --issues …`. Si falta la aprobación o la autorización, explicale que tiene que hacerla en la app (botones ✔ APROBAR y 🎬 AUTORIZAR RENDER FINAL). Con la autorización vigente, lanzar `episodio.yml` / `render.yml` con la configuración autorizada |
| «¿cuánto falta / cuántos corren?» | `actions_list list_workflow_jobs` sobre la corrida y contar `in_progress` y `queued` |
| probar la concurrencia | `concurrencia.yml` (`trabajos=60`, `espera_s=120`). Contar a los ~30 s y aplicar el criterio que haya dado el dueño (hoy: cancelar si ≤ 20) |
| cambiar la app | editar `app/`, probar con Godot headless (`pruebas/app/*.gd`, `pruebas/revision/revision_ui.gd` con `xvfb-run`), push → `apk.yml` |
| audio | `voces` sin `--gastar` (estima) → mostrar el costo → recién después `--gastar` |

## 8. Pruebas que existen (ninguna renderiza)

```
python3 pruebas/autorizacion/test_autorizacion.py        # regla de render: lógica, comandos y flujos (35/35)
xvfb-run -a godot --path app --rendering-driver opengl3 --script res://../pruebas/revision/revision_ui.gd -- \
    PREVIA.glb PREVIA.json <prod> <escena> <version> SALIDA_DIR    # app + EDITOR 3D con una previa real (18/18)
pruebas/app/toques_vertical.gd (6/6), pruebas/app/toques_rotacion.gd (7/7)   # toques en vertical / al girar
```

## 9. Documentos para ampliar (sólo si hace falta)

`docs/REGISTRO.md` (historia y estado) · `docs/FLUJO_DE_PRODUCCION.md` (cómo producir) ·
`docs/REVISION_Y_AUTORIZACION.md` (la regla) · `docs/EDITOR_3D.md` · `docs/APP_ANDROID.md` · `docs/ARQUITECTURA.md` ·
`docs/ANIMACIONES_Y_PERSONAJES.md` · `docs/AUDIO.md` · `docs/ERRORES.md` · `docs/MIGRACION_ORGANIZACION.md` ·
`docs/informes/` (tiempos y el ticket de GitHub).
