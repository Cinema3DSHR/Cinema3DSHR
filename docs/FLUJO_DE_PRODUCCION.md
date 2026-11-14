# Flujo de producción (para Claude)

## 0. Instalación del entorno (sesión de Claude o máquina nueva)

```bash
python3 -m venv /opt/tools/blendenv && /opt/tools/blendenv/bin/pip install -r requirements-produccion.txt
# FFmpeg: apt-get install ffmpeg   ·   Godot 4.7.2 (sólo para probar la app): ver .github/workflows/apk.yml
export PY=/opt/tools/blendenv/bin/python      # python con bpy
```
Los repos de recursos se buscan al lado de este (`../mixamo-respaldo`, `../Operaci-n-Nexus-1/fuente`,
`../Extraction-tactical/public`) o en `CINE_MIXAMO_DIR`, `CINE_NEXUS_DIR`, `CINE_EXTRACTION_DIR`.

## 1. Qué pidió el dueño

| Pedido | Qué se crea | Dónde aparece en la app |
|---|---|---|
| «Creá una mansión…» (sólo escenario) | `escenarios/<id>/escenario.json` (+ generador nuevo si no existe) | ESCENARIOS (visor 3D) |
| «Creá una escena de…» | Producción `clase: escena` con 1 escena | PELÍCULAS |
| «Creá una secuencia…» | Producción `clase: secuencia` con varias escenas | PELÍCULAS |
| «Creá una película de N minutos…» | Producción `clase: pelicula`: guion → escenas (20–60 s c/u) | PELÍCULAS |

Antes de crear nada: **reutilizar** (`catalogo/*.json`, `escenarios/`). Tripo3D sólo si no hay alternativa y con
autorización de créditos.

## 2. Pasos

1. Guion: sinopsis, personajes, escenas (título, lugar, hora, acción, duración).
2. `producciones/<pNNN_nombre>/produccion.json` y por escena `escenas/eNN/v1/escena.json` (formato abajo).
3. Revisar encuadres sin gastar render: `$PY -m estudio validar …/escena.json` y
   `$PY -m estudio fijas …/escena.json --salida /tmp/fijas` (un fotograma por toma, ~10 s c/u) y MIRAR las imágenes.
4. Opcional, animática rápida: `$PY -m estudio render … --calidad humo` (320×180, ~0,4 s/fotograma) + `cerrar`.
5. `git add producciones/… && git commit && git push` → `render.yml` renderiza en paralelo y publica.
6. Verificar en Actions que terminó y que el catálogo lo muestra (`catalogo.json` de la release `catalogo`).

## 3. Correcciones (el dueño escribe en la app)

- Llegan como Issues abiertos con la etiqueta `correccion` y un bloque JSON (`produccion`, `escena`, `version`, `nota`).
- `$PY -m estudio nueva-version <produccion> <escena> --motivo "issue #N: <nota>"` → crea `v<k+1>` (la anterior
  no se toca). Editar SÓLO la versión nueva, subirla, y comentar/cerrar el issue con el resultado.
- Al aprobar: poner `"bloqueada": true` y `"estado": "aprobada"` en esa versión (el render la rechaza desde ahí).

## 4. Formato de `escena.json`

```jsonc
{
  "tipo": "escena", "id": "<produccion>-eNN", "produccion": "<produccion>", "numero": 1, "version": 1,
  "titulo": "…", "guion": "…", "duracion_s": 28,
  "escenario": {"id": "mansion_moderna_noche", "generador": "mansion_moderna", "parametros": {…}},
  "eventos": [{"accion": "abrir_porton", "inicio_s": 4.0, "duracion_f": 75}],      // acciones del escenario
  "vehiculos": [{"id": "auto", "modelo": "procedural:sedan", "color": [r,g,b],
                 "recorrido": [[x,y,z], {"ancla": "porton", "desp": [0,-0.5,0]}, …],
                 "tiempos": [[indice_punto, segundo], …]}],                         // repetir índice = parada
  "personajes": [],                                                                 // Etapa 5
  "tomas": [ {"id": "t01_general", "tipo": "dolly", "plano": "texto para la app", "inicio_s": 0, "duracion_s": 5,
              "desde": […], "hasta": […], "objetivo": {"ancla": "centro_casa"}, "lente_mm": 24,
              "apertura": 2.8, "temblor": 0.01, "luz_relleno": 150, "montaje": {"efecto": "vigilancia", "texto": "CAM 03"}} ],
  "sonido": {"generador": "procedural", "ambiente": "noche_suburbio",
             "eventos": [{"tipo": "motor", "movil": "auto"}, {"tipo": "porton_motor", "inicio_s": 4, "duracion_s": 2.5, "ancla": "porton"}]},
  "render": {"calidad": "revision", "fps": 30, "exposicion": 1.1},
  "estado": "borrador", "bloqueada": false
}
```
Reglas que valida `validar`: tomas contiguas que suman la duración, tipos conocidos, móviles definidos, generador existente.
Puntos: `[x,y,z]`, `{"ancla": …, "desp": […]}` o `{"movil": "auto", "punto": "rueda_del_izq", "desp_local": […]}`.

## 5. Tipos de toma (ver `estudio/blender/camaras.py`)

`estatica`, `general`, `dolly` (travelling), `paneo` (`objetivo` → `objetivo_final`), `grua` (revelación),
`orbita` (aérea; `centro`, `radio`, `altura`, ángulos inicial/final), `seguimiento` (persecución: `movil`,
`desp_local` en el marco del móvil, `retardo`), `detalle` (primer plano de un punto del móvil), `vigilancia`
(fija, angular, barrido; con `montaje.efecto = vigilancia` agrega REC, hora y grano), `subjetiva` (POV).
Primeros planos de personajes, sobre el hombro y plano/contraplano llegan con la Etapa 5 (anclas de huesos).
Criterio: nunca una sola cámara fija; variar escala de plano (general → medio → detalle), cortar en movimiento,
mantener el eje de acción, usar profundidad de campo en detalles.

## 6. Niveles de calidad (`estudio/config.py`)

| Nivel | Resolución | Motor | Uso | Costo medido (4 núcleos) |
|---|---|---|---|---|
| humo | 320×180 | Cycles 2 mp | animática / pruebas | ~0,4 s/fotograma |
| previa | 854×480 | Cycles 4 mp | revisión de movimiento | ~5 s/fotograma (estimado) |
| revision | 1280×720 | Cycles 10 mp + denoise | **por defecto** | 17–24 s/fotograma |
| final | 1920×1080 | Cycles 48 mp | película aprobada | ~2–3 min/fotograma (estimado) |
| final4k | 3840×2160 | Cycles 64 mp | si el servidor lo permite | no viable en Actions estándar |

No se vuelve a renderizar una versión publicada (salvo `forzar`) ni una aprobada. Para cambiar algo, versión nueva.
