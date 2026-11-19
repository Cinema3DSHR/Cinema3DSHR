# AutoFinisher — de Godot a un .blend autónomo listo para Cycles

Herramienta general del estudio (`estudio/autofinisher/`). Toma el **GLB que exporta Godot** y una **receta de
terminación**, y deja una **versión inmutable**: un `.blend` autónomo (texturas empaquetadas) con su manifiesto,
hashes e informe. No renderiza. Sirve para cualquier escena, no sólo para la prueba de la casa.

```
GODOT ──► GLB ──► AUTOFINISHER ──► .BLEND AUTÓNOMO + manifest.json ──► RELEASE ──► render distribuido ──► MP4
          (construir_produccion.yml: una vez por versión)          (render_desde_blend.yml: las veces que haga falta)
```

Cómo construir, publicar y renderizar paso a paso: `docs/CONSTRUIR_Y_RENDERIZAR.md`.

## 1. Etapas (cada una es un módulo)

| # | Módulo | Qué hace |
|---|---|---|
| 1 | `auto_import.py` (AutoImport) | Escena vacía con los **fps de la receta ANTES de importar** (si no, 30 s quedan en 720 cuadros); importa el GLB; elige la cámara (la de la receta o la única); fija el rango; inspecciona qué llegó (objetos, triángulos, luces, vacíos FX, colisiones, materiales, acciones, imágenes). |
| 2 | `auto_lights.py` (AutoLights) | Recupera la energía de cada luz por **perfil** (puntual, foco, farola, neón, fuego, ambiente, relámpago, área): deshace la conversión fotométrica del importador y aplica la escala del perfil. Reescala las **claves animadas** (KHR_animation_pointer), con el factor 4π extra que llega en puntuales y focos. |
| 3 | `auto_materials.py` (AutoMaterials) | **Vidrios** (transmisión + IOR, por nombre `vidrio*` o `cine_tipo`), **emisivos** (se informan; se escalan sólo si la receta lo pide), **mundo** (el ambiente de Godot no viaja). |
| 4 | `auto_effects.py` (AutoEffects) | Aplica **sólo los efectos que pide la receta**, cada uno sobre su vacío `FX_*`. Los vacíos FX sin receta se informan. Si falta un vacío pedido, se detiene. |
| 5 | `auto_cinema.py` (AutoCinema) | Cycles con la calidad de la receta (por defecto la del estudio, ver §4). |
| 6 | `auto_pack.py` (AutoPack) | Empaqueta todo y **falla si queda algo externo** (biblioteca, caché, imagen faltante). |
| 7 | guardar | `.blend` comprimido. |
| 8 | `manifiesto.py` + `auto_report.py` (AutoReport) | Manifiesto `estudio.version_blend/1` con SHA-256 del `.blend` y del GLB, versiones de Blender, Godot y los scripts (SHA-256 del código del AutoFinisher), receta (SHA-256) y estado de revisión. Informe con tiempo y RAM máxima de cada etapa, máquina y resultados. |

Punto de entrada: `construir.py` (`python -m estudio.autofinisher construir …`). Si cualquier etapa falla, la carpeta
de la versión se borra y queda `<carpeta>_ERROR.json` con lo que pasó: nunca queda una versión a medias.

## 2. Estándar de nombres Godot → Blender

El GLB transfiere mallas, materiales PBR, luces, cámaras y animaciones de transformación. Lo demás se marca en Godot
con **nombres** (o con la metadata `cine_tipo`, que llega como extra del glTF y tiene prioridad sobre el nombre).

| En Godot | Nombre | En Blender |
|---|---|---|
| Luz | `Luz_<perfil>_<nombre>` (`Luz_farola_0`, `Luz_neon_cocina`, `Luz_luna`) | energía por perfil (tabla de `convenciones.py`); sin perfil en el nombre, el del tipo (OmniLight → puntual, SpotLight → foco, DirectionalLight → ambiente) |
| Material de vidrio | `vidrio*` | transmisión 1 + IOR (ajustable o excluible por material en la receta) |
| Material emisivo | `emisivo*`, `neon*` (o cualquiera con emisión) | se informa; se escala si la receta lo pide |
| Partículas / volumen | vacío `FX_<receta>[_<nombre>]` (`FX_lluvia`, `FX_fuego_hogar`) | la receta de efecto se reconstruye en esa posición |
| Colisión de partículas | `Colision_*` | llega sin tamaño: la receta de lluvia usa cajas explícitas u objetos reales |
| Ambiente | WorldEnvironment | `mundo` de la receta |

Perfiles de luz y escala por defecto (unidad de Godot → vatios de Blender; W/m² en el sol): puntual 60, foco 120,
farola 120, neón 60, fuego 60, ambiente 0,6, relámpago 0,6, área 60. Son las correcciones medidas en la prueba; cada
producción puede ajustar un perfil (`luces.perfiles.farola.escala`) o una luz puntual (`luces.objetos.<nombre>`).

## 3. Receta de terminación (`estudio.receta_autofinisher/1`)

Un JSON en el repositorio por producción o escena. Ejemplo completo: `pruebas/autofinisher/casa_tormenta.receta.json`.

```json
{
 "formato": "estudio.receta_autofinisher/1",
 "produccion": "a_la_deriva_e03",
 "godot": {"proyecto": "producciones/p011_a_la_deriva/godot", "script": "herramientas/construir.gd", "args": [],
           "glb": "salida/e03.glb", "version": "4.7.2", "recursos": []},
 "escena": {"fps": 30, "cuadro_inicial": 0, "cuadro_final": 1799, "camara": "Camara"},
 "render": {"resolucion": [540, 960], "muestras": 6},
 "luces": {"perfiles": {}, "objetos": {}},
 "materiales": {"vidrios": {"vidrio_visor": {"rugosidad": 0.02, "ior": 1.5}}, "emisivos": {}},
 "mundo": {"color": [0.0, 0.0, 0.0], "fuerza": 1.0},
 "efectos": [{"receta": "humo", "ancla": "FX_humo_consola", "parametros": {"densidad": 1.2}}]
}
```

- `escena.cuadro_inicial/final` son cuadros de **Blender**; los archivos renderizados salen numerados 1..N.
- `godot.recursos`: archivos de otros repositorios que el proyecto de Godot necesita (`{repo, ref, archivos, destino}`;
  los privados usan el secreto `ASSETS_TOKEN`).
- `efectos`: **sólo los pedidos**. Los parámetros que no se den usan los de la biblioteca.

## 4. Calidad por defecto (`receta.RENDER_POR_DEFECTO`)

Cycles CPU · 540×960 · 30 fps · 6 muestras · adaptativo 0,05 · OpenImageDenoise (albedo + normal) · rebotes
6/2/3/4/8 (volumen 0) · sin cáusticas · clamp indirecto 8 · árbol de luces · AgX Medium High Contrast · pasos de
volumen 2 / 256 · datos persistentes. Es la misma de la prueba y de «A la deriva» E02 a 540p. No se cambia por
iniciativa propia: una calidad distinta va en la receta y es una versión nueva.

## 5. Biblioteca de efectos (`recetas_efectos/`)

Todos son **deterministas por número de cuadro**: no simulan ni hornean nada, así que cualquier trabajo de render
puede empezar en cualquier cuadro y da lo mismo. Hoy están los que ya se usaron en una escena real:

| Receta | Vacío | Qué arma | Parámetros principales |
|---|---|---|---|
| `lluvia` | `FX_lluvia` | gotas en bucle con viento (nodos de geometría) que se cortan contra superficies elegidas | cantidad, mitad_x/y, alto, velocidad, viento, semillas, piso_z, choque_objetos, cajas_choque, gota |
| `fuego` | `FX_fuego` | volumen emisivo con ruido 4D que sube y se angosta | desplazamiento, tamano, umbral, ganancia, emision, colores |
| `humo` | `FX_humo` | volumen gris que sube | tamano, z_centro, umbral, ganancia, densidad, color |
| `brasas` | `FX_brasas` | chispas emisivas que suben con vaivén | cantidad, vida, ancho, fondo, subida, emision |
| `relampago` | — | refuerza el rayo animado que ya viaja en el GLB | material, emision, objetos_sin_sombra |

**Fuego corregido** respecto de la prueba (las llamas salían más tenues que las brasas): umbral 0,08 → 0,05,
ganancia 9 → 12, emisión 22 → 90. **No se verificó con un render** (esta implementación no renderiza); si hace falta,
se ajusta en la receta sin tocar el código.

Niebla, gotas en el vidrio y otras partículas **no están**: se agregan a la biblioteca cuando el dueño las pida en una
escena (un módulo nuevo en `recetas_efectos/` con `PARAMETROS_POR_DEFECTO` y `aplicar(ancla, parametros, ctx)`).

## 6. Comandos

```bash
PY=/opt/tools/blendenv/bin/python                         # Python con bpy 5.3
$PY -m estudio.autofinisher construir --receta R.json --glb escena.glb --version 1 --salida dist/<prod>_v001
$PY -m estudio.autofinisher validar --blend dist/<prod>_v001/<prod>_v001.blend --manifiesto dist/<prod>_v001/manifest.json
$PY -m estudio.autofinisher render-trozo --blend X.blend --manifiesto manifest.json --desde 1 --hasta 15 \
    --ancho 540 --alto 960 --muestras 6 --salida out [--sin-render]
python3 -m estudio.autofinisher receta --receta R.json             # valida y completa (sin bpy)
python3 -m estudio.autofinisher verificar-blend --manifiesto M --blend X.blend
python3 -m estudio.autofinisher reparto --total 900 --trabajos 60 [--cuadros 12,40-45]
python3 -m estudio.autofinisher verificar-cuadros --carpeta frames --total 900
python3 -m estudio.autofinisher verificar-video --mp4 X.mp4 --ancho 540 --alto 960 --fps 30 --cuadros 900
python3 -m estudio.autofinisher descargar --url URL --destino ARCHIVO --sha256 H
python3 -m estudio.autofinisher.recursos --receta R.json
```

## 7. Pruebas (ninguna renderiza)

```bash
python3 pruebas/autofinisher/test_autofinisher.py            # receta, manifiesto, reparto, cuadros, video, informe, flujos
$PY pruebas/autofinisher/test_general.py                      # el AutoFinisher con una escena que no es la casa
$PY pruebas/autofinisher/resumen_blend.py A.blend a.json      # + comparar.py: comparar dos .blend campo por campo
```

La reconstrucción de «Casa moderna en tormenta» y su comparación con la prueba original: `pruebas/autofinisher/COMPARACION.md`.

## 8. Relación con lo existente

- La prueba original (`pruebas/godot_blender/`: b6–b9, `armar.py`, `render_trozo.py`,
  `render_prueba_godot_blender.yml`) **no se modificó**. El AutoFinisher copió y generalizó su código, porque la
  condición fue no tocarla. Los números fijos pasaron a la receta.
- Los flujos de «A la deriva» que arman desde una receta del estudio (`video30.yml`, `render.yml`, `episodio.yml`) siguen
  igual. El pipeline nuevo es independiente: `construir_produccion.yml` + `render_desde_blend.yml`.
- El render respeta el candado (`config/candado_render.json`), igual que los demás flujos.
