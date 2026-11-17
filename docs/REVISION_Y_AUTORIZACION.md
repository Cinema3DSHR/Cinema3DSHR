# REGLA PERMANENTE — Revisión 3D en la app antes de cualquier render

**Nunca se renderiza nada sin que el dueño haya revisado esa versión de la escena en 3D dentro de la app Android, la
haya APROBADO y haya tocado AUTORIZAR RENDER FINAL.** Esta regla está por encima de cualquier automatización, flujo o
decisión de Claude. No hay renders «de prueba», «para ver cómo quedó», automáticos al terminar una escena ni porque otro
flujo terminó bien. La vista previa es el EDITOR 3D interactivo, no un video.

## 1. Proceso

1. Claude prepara o corrige la escena (`producciones/<p>/escenas/<e>/v<k>/escena.json`; una corrección es SIEMPRE una
   versión nueva, la anterior se conserva para comparar).
2. Claude publica la previsualización 3D con el flujo **«Previsualización 3D»** (`previa.yml`): exporta la MISMA escena
   de producción a GLB + línea de tiempo (sin fotogramas, sin Cycles) y rearma el catálogo.
3. En la app: PELÍCULAS → producción → escena → **🎬 EDITOR 3D**. Arriba se ve el estado de la versión.
4. El dueño revisa: cámara libre (no toca las cámaras de rodaje), MONTAJE, ver por TOMA (cámara, lente, encuadre,
   movimiento, duración), ▶/⏸, ⏮ ⏭ cuadro a cuadro, línea de tiempo con cortes de toma, personajes con la animación que
   hace cada uno, objetos, luces de referencia.
5. Si algo está mal: 📍 MARCAR ESTE MOMENTO, mensaje (ENVIAR), 🎥 COLOCAR CÁMARA, **GUARDAR CORRECCIONES**. Llegan al
   estudio como pedidos `[DIRECCIÓN]`; la versión pasa a CORRECCIONES SOLICITADAS.
6. Claude aplica las correcciones en una **versión nueva** y vuelve al paso 2.
7. Cuando está bien: **✔ APROBAR ESCENA** (atada a esa versión y a su huella).
8. Con la versión aprobada (tocar ⟳ ESTADO): **🎬 AUTORIZAR RENDER FINAL**. Queda registrada la escena, la versión, la
   huella, la configuración de render, la fecha y la cuenta. Recién ahí un flujo de render puede arrancar.

## 2. Estados (por versión de escena; los calcula `estudio/autorizacion.py` y los muestra la app)

| estado | cuándo |
|---|---|
| EN PREPARACIÓN | la versión existe pero no tiene previsualización 3D publicada |
| LISTA PARA REVISIÓN | hay previsualización y todavía no hay notas ni decisiones del dueño |
| EN REVISIÓN | el dueño mandó notas o marcadores |
| CORRECCIONES SOLICITADAS | GUARDAR CORRECCIONES, una cámara del director o CORREGIR/RECHAZAR |
| APROBADA POR EL USUARIO | ✔ APROBAR con la huella actual y sin correcciones después |
| RENDER AUTORIZADO | además, AUTORIZAR RENDER FINAL posterior a la aprobación, con la huella actual |
| RENDER EN EJECUCIÓN | autorizada y con el render en marcha |
| FINALIZADA | el render de esa huella está publicado |

**Invalidación automática:** la aprobación y la autorización valen sólo para la **huella** (la receta + el código del
estudio que la construye). Si Claude cambia cualquier cosa relevante, la huella cambia y la versión vuelve a revisión;
una corrección pedida después de aprobar también anula la aprobación. Los registros de otra huella no cuentan.

## 3. Bloqueo del render (backend, no sólo la app)

- `estudio/autorizacion.py` es la fuente única: `verificar(escena, registros, configuración)` exige aprobación vigente +
  autorización posterior de la misma versión y huella + la misma configuración (resolución, fps, muestras).
- Cuentan sólo los registros de las cuentas de `config/autorizados.json` (variable `AUTORIZADOS` de GitHub para los
  disparadores): cualquiera puede abrir Issues en un repo público y no cuentan.
- **Flujos que renderizan** (`render.yml`, `video30.yml`, `episodio.yml`): sólo a mano; el planificador verifica la
  autorización de cada escena ANTES de pedir máquinas y cada trabajo de render la vuelve a verificar (CINE_ISSUES).
  `render.yml` ya no se dispara al subir un escena.json; `video30.yml` ya no tiene el interruptor para saltear la
  aprobación ni su modo ensayo la saltea; `episodio.yml` la exige también para una escena sola y para los ensayos.
- **Comandos y scripts que renderizan** (`python -m estudio render | fijas`, `render_tomas` —animática incluida—,
  `pruebas/video_30s/render_rango.py`, `pruebas/episodio/render_bloque.py`): se niegan sin registros
  («RENDER BLOQUEADO»), antes de cargar Blender. Los scripts históricos de medición quedaron deshabilitados.
- «Revisiones desde la app» (`revisiones.yml`): RENDERIZAR ya no renderiza; un `[AUTORIZACIÓN]` se verifica y se
  responde en el pedido, pero NO lanza el render.
- Previsualización (`previa.yml`), catálogo, dirección, montaje de escenas ya aprobadas (`pelicula.yml`) y la portada
  de un escenario suelto no son renders de escena y no la necesitan.

**Claude** nunca crea pedidos `[AUTORIZACIÓN]` ni `[REVISIÓN] … APROBAR`, nunca renderiza por iniciativa propia y nunca
usa un render para comprobar algo. Límite honesto: los registros son Issues de la cuenta del dueño; si alguien con ese
token los creara a mano, el sistema no lo distinguiría de la app. Para una segunda llave humana se puede crear en
GitHub un entorno «render-final» con revisor obligatorio (Settings → Environments) y asignarlo a los trabajos de render.

## 4. Si la app no carga bien

La versión sólo se considera revisable si el GLB y la línea de tiempo cargaron completos y la huella de la
previsualización es la de la versión actual del catálogo. Si no: ✔ APROBAR y AUTORIZAR quedan deshabilitados. Una
aprobación o una autorización sin conexión NO queda en espera: no se registra y hay que repetirla.

## 5. Comandos

```
python -m estudio autorizacion estado <produccion> --issues issues.json [--con-previa]
python -m estudio autorizacion verificar <escena.json…> --issues issues.json --resolucion 960x540 --fps 30 --muestras 6
python3 pruebas/autorizacion/test_autorizacion.py                       # lógica, comandos y flujos (sin render)
xvfb-run -a godot --path app --rendering-driver opengl3 --script res://../pruebas/revision/revision_ui.gd -- \
    PREVIA.glb PREVIA.json <produccion> <escena> <version> SALIDA_DIR   # la app con una previsualización real
```
