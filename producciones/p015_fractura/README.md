# p015 · A la deriva: FRACTURA (experimento, 20/11/2026)

Cortometraje experimental de 3 min (180 s · 720×1280 vertical · 30 fps · 5400 cuadros) con Aiden, sin parkour como hilo: un montaje no lineal de escenas
épicas unidas por transiciones imposibles hechas con geometría y cámara. El dueño pidió el video **renderizado y con música, sin aprobar nada**
(«es un experimento con vos»), así que la producción recorre `aprobar-blend` → LFS → `incorporar_blend.yml` → `render_desde_blend.yml` sin pasos de aprobación.

## Cómo está hecho
| Pieza | Dónde | Qué es |
|---|---|---|
| Línea de tiempo | `blender/guion.py` | escenas, cuadros y eventos sonoros (los usan Blender y la música) |
| Biblioteca de Aiden | `blender/aiden_clips.py`, `blender/retarget_dir.py` | el Aiden original de E02 con 18 clips de Mixamo retargeteados (variante que conserva la dirección de los huesos: brazos T → A) |
| Marco Blender | `blender/marco.py`, `lib.py`, `aiden.py`, `construir.py` | Cycles, compositor (glare, dispersión, balance, viñeta), cortes por marcadores, velos de transición, tiempo animado por NLA, física balística por fragmento, volúmenes de fuego |
| Escenas | `blender/esc_s0.py` … `esc_s8.py` | Ojo · Corredor · Cero g · Detonación · Espejos · Colapso · Oscuro · Reconstrucción · Final |
| Música | `blender/musica.py` | síntesis original con numpy, 48 kHz estéreo, sincronizada con `guion.EVENTOS` |
| Godot | `godot/` | previsualización de la línea de tiempo, cortes y transiciones (`prueba.gd` la valida sin ventana) |

Cada escena vive a 1 km de las demás (offset en Y), así no hace falta ocultar nada por colección (no es animable). Los cortes son marcadores con cámara;
las transiciones son geometría + cámara + un velo pegado a la lente para el cuadro de relleno.

Reconstrucción: `/opt/tools/blendenv/bin/python blender/aiden_clips.py -- aiden_clips.blend` y
`/opt/tools/blendenv/bin/python blender/construir.py -- salida.blend todas 1.0`; música: `python3 blender/musica.py musica.wav`.

## Transiciones (A–G y propias)
B pupila · F onda de choque contra la lente · E partícula que crece · A zoom al interior de la explosión · C espejo que estalla · D esquirla de cristal gigante ·
G esfera de 320 espejos que se agrieta y estalla · más el anillo de luz, la ventana que estalla y el ascenso al cielo.

## Límites honestos
- El audio se midió (envolvente y picos) pero no se escuchó.
- La geometría y las simulaciones están hechas en Python dentro de Blender; Godot sólo contiene la previsualización de la línea de tiempo.
