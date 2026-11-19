# Construir, publicar y renderizar una producción (pipeline Godot → Blender → Cycles)

Tres pasos separados: **construir** la versión (una vez), **publicarla** (su Release, inmutable) y **renderizarla**
(las veces que haga falta, siempre desde el `.blend` publicado). El render nunca instala Godot ni reconstruye la escena.
Herramienta: `docs/AUTOFINISHER.md`.

## 1. Preparar una producción nueva

1. **Escena en Godot** (proyecto en el repo, p. ej. `producciones/<p>/godot/`), con un script que la arme y exporte
   el GLB (modelo: `pruebas/godot_blender/godot/herramientas/construir.gd`). Usá los nombres del estándar
   (`docs/AUTOFINISHER.md` §2): `Luz_<perfil>_…`, materiales `vidrio*`, vacíos `FX_<efecto>` donde va un efecto que el
   GLB no transfiere, una cámara clara.
2. **Receta de terminación** (`estudio.receta_autofinisher/1`, §3 de AUTOFINISHER.md): fps y cuadros, cámara, calidad,
   vidrios, mundo y **sólo los efectos pedidos**.
3. **Probar sin render en la sesión**:
   ```bash
   cd <proyecto godot> && godot --headless --import && godot --headless --path . -s herramientas/construir.gd
   $PY -m estudio.autofinisher construir --receta R.json --glb <proyecto>/salida/x.glb --version 1 --salida /tmp/x_v001
   $PY -m estudio.autofinisher validar --blend /tmp/x_v001/<prod>_v001.blend --manifiesto /tmp/x_v001/manifest.json
   $PY -m estudio.autofinisher render-trozo … --sin-render     # recorre los cuadros sin renderizar
   ```
   Para revisar la escena antes de construir la versión: el GLB en el visor HTML (`docs/VISOR_Y_ORDENES_DE_CAMARA.md`).

## 2. Construir y publicar una versión — flujo «Construir producción» (`construir_produccion.yml`)

A mano, con:

| Entrada | Qué es |
|---|---|
| `receta` | ruta de la receta en el repo |
| `version` | entero NUEVO: si existe la Release `blend-<produccion>-v<NNN>`, el flujo se detiene |
| `publicar` | `true` publica la Release; `false` deja sólo un artefacto de 14 días para revisar |

Lo que hace, en un solo trabajo:
1. Lee la receta.
2. Comprueba que la versión sea nueva.
3. Instala Godot y Blender.
4. Baja los recursos externos.
5. Godot → GLB.
6. AutoFinisher → `.blend` autónomo, manifiesto y SHA-256.
7. Valida el `.blend` contra su manifiesto.
8. Mide tiempos.
9. Publica en **`blend-<produccion>-v<NNN>`**:
   - `<prod>_v<NNN>.blend`
   - `<prod>_v<NNN>.glb`
   - `manifest.json`
   - `informe_preparacion.json`
   - `tiempos_construccion.json`

**Inmutabilidad:**
- Una versión publicada no se toca.
- Cualquier cambio (receta, escena de Godot, scripts, calidad) es una versión nueva.
- El manifiesto guarda:
  - los SHA-256 del `.blend`, del GLB, de la receta y del código del AutoFinisher;
  - las versiones de Godot y Blender;
  - el commit;
  - el estado de revisión («sin revisar» al construir).

## 3. Renderizar una versión existente — flujo «Renderizar desde BLEND» (`render_desde_blend.yml`)

A mano, por orden del dueño (respeta el candado del render). Entradas:

| Entrada | Qué es |
|---|---|
| `produccion`, `version` | la versión exacta (su Release tiene que existir) |
| `ancho`, `alto`, `muestras` | vacíos = los del manifiesto (si se cambian, el informe lo dice) |
| `fps` | tiene que ser el del manifiesto (la animación está hecha a ese fps): otro valor se rechaza |
| `trabajos` | trabajos pedidos (máx. 60); GitHub corre a la vez los que permite la cuenta |
| `nombre_mp4`, `release_destino` | dónde publicar; si ese MP4 ya existe en la Release, el flujo se detiene |
| `cuadros`, `corrida_previa` | sólo para la recuperación explícita (§4) |

Trabajos:
1. **planificar** (sin Blender):
   - comprueba el candado;
   - baja **sólo `manifest.json`** de la versión y lo valida;
   - comprueba los fps;
   - comprueba que no se vaya a pisar el MP4;
   - reparte los cuadros: tramos contiguos de ceil(N / trabajos), los mismos que en la prueba. Con 900 cuadros y 60
     trabajos salen 15 cuadros por trabajo.
2. **render** (uno por tramo, en paralelo):
   - instala sólo Blender;
   - baja **una vez** el `.blend` y el manifiesto;
   - **verifica el SHA-256**, porque sólo se renderiza la versión pedida;
   - renderiza sus cuadros con `render-trozo`: cada cuadro se reintenta una vez si falla o sale vacío;
   - sube los PNG y su informe.
3. **montar**:
   - junta los cuadros;
   - **verifica que estén todos**. Si falta alguno, **se detiene sin publicar**, informa cuáles y cómo recuperarlos.
     **No se rellena nada**;
   - codifica el MP4;
   - **lo verifica**: cuadros exactos, resolución, fps y duración;
   - publica `<nombre>.mp4` y `<nombre>_informe.json` en la Release de destino.

## 4. Si faltan cuadros: recuperación explícita y documentada

El montaje dice, por ejemplo, «FALTAN CUADROS: 120-125,431». Se vuelve a lanzar el mismo flujo con la misma versión,
cambiando sólo esto:
- `cuadros` = `120-125,431`;
- `corrida_previa` = el número de la corrida que falló.

Se renderizan sólo esos cuadros y el montaje suma los de la corrida previa (los artefactos duran 14 días). El
informe registra la recuperación.

## 5. Qué se mide (informe del render, `<nombre>_informe.json`)

| Medida | De dónde sale |
|---|---|
| Trabajos solicitados, con informe, ejecutados y fallidos | planificar + API de GitHub |
| **Simultáneos máximos reales** y espera en cola (media y máxima) | tiempos de cada trabajo en la API |
| Instalación, descarga del `.blend` (s, MB, MB/s), verificación del hash y apertura del `.blend` | cada trabajo |
| Segundos por cuadro (media, mínimo y máximo) y horas de CPU totales | cada trabajo |
| RAM máxima del proceso de Blender | cada trabajo |
| Reintentos y cuadros fallidos | cada trabajo |
| Cuadros faltantes, vacíos y sobrantes | montaje |
| Video: cuadros, resolución, fps, duración y tamaño | ffprobe |
| SHA-256 del `.blend` usado y versión | manifiesto |
| Reloj total de punta a punta | planificar → montar |

La construcción mide: instalación, recursos (MB y s), Godot → GLB, cada etapa del AutoFinisher con su RAM máxima,
tamaños del GLB y del `.blend`, y el total hasta publicar.

## 6. Estado

Los dos flujos están **preparados y no se ejecutaron nunca**: todavía no hay ninguna versión publicada, ningún
render, ninguna Release nueva. La primera corrida real la decide el dueño.
