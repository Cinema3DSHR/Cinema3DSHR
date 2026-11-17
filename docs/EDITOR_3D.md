# EDITOR 3D / PREVISUALIZACIÓN — dirigir, corregir y aprobar ANTES del render

Etapa obligatoria antes de cualquier render final. El dueño abre la escena en la app, la recorre en 3D, reproduce las
animaciones, coloca sus propias cámaras, marca momentos, escribe correcciones y aprueba. Recién con la aprobación de
**esa versión** se habilita el render final (Cycles CPU, 1280×720, 30 fps, 6 muestras, OIDN, GitHub Actions).

## 1. Flujo de trabajo

1. El dueño pide una escena. Claude la construye (`producciones/<produccion>/escenas/<escena>/v<k>/escena.json`).
2. Claude publica la previsualización: flujo **«Previsualización 3D»** (`previa.yml`, entrada = ruta del escena.json).
   Sale `<escena>_v<k>_previa.glb` + `_previa.json` en la release de la producción y se rearma el catálogo.
3. En la app: PELÍCULAS → producción → escena → **🎬 EDITOR 3D / PREVISUALIZACIÓN**.
4. El dueño recorre la escena (cámara libre), reproduce, cambia de cámara, elige personajes y objetos.
5. Encuentra un encuadre y toca **COLOCAR CÁMARA** → nombre, toma, desde/hasta, entrada (corte o suave), notas.
6. La app manda la cámara al estudio (Issue `[DIRECCIÓN] … CAMARA`). El flujo **«Dirección desde el editor 3D»**
   (`direccion.yml`) la guarda en `producciones/<produccion>/director/cameras/camera_NNN.json`.
7. Marcadores (📍) y mensajes (ENVIAR) llevan el instante exacto, el cuadro, el personaje elegido, el clip que estaba
   reproduciendo y la cámara de ese momento. **GUARDAR CORRECCIONES** manda todo junto.
8. Claude lee `python -m estudio direccion <produccion>`, aplica los cambios en una **versión nueva**
   (`python -m estudio aplicar-direccion <produccion> <escena> --camaras camera_001,camera_002` para las cámaras;
   el resto de las correcciones a mano en la receta), publica la previsualización nueva y cierra el pedido.
9. El dueño revisa otra vez. Cuando está bien: **✔ APROBAR ESCENA** (queda atada a la versión y a su huella).
10. Con la versión aprobada, el dueño toca **🎬 AUTORIZAR RENDER FINAL** (DIRECCIÓN). Recién entonces se puede lanzar el
    render; todos los flujos y comandos de render **se niegan** sin esa autorización para la MISMA huella y la misma
    configuración. Regla completa y los 8 estados de revisión: `docs/REVISION_Y_AUTORIZACION.md`.

## 2. La previsualización es la escena de producción

`estudio/blender/previa.py` exporta desde `director.construir(escena.json)`: el mismo código y la misma receta que
el render. Se conservan geometría, personajes con sus **esqueletos originales**, las acciones NLA **horneadas cuadro a
cuadro** (los clips reales, no sustitutos), cámaras de rodaje con su lente, luces, puertas y tiempos. Lo único que se
simplifica para un teléfono: los materiales procedurales pasan a su color base (las texturas reales de personajes y
armas se conservan) y el fondo marcado `visor_omitir` no se exporta. Los fogonazos e impactos se encienden sólo en sus
cuadros, igual que en el render (`visibilidad` del JSON).

El `_previa.json` trae la línea de tiempo legible: para cada personaje, cada clip con inicio, fin, ciclos y velocidad
(la app muestra qué animación está haciendo cada uno en cada instante y cuál sigue), las tomas con su cámara, lente y
FOV, los destellos, las anclas y la **huella** de la receta.

**Tiempo:** película `t = (cuadro − 1) / fps`; dentro del GLB, Blender pone el cuadro *f* en `f / fps`. El editor ya
hace esa cuenta (medido: con la otra convención las cámaras móviles se desfasaban un cuadro).

## 3. Archivos de dirección (legibles por la app y por Claude)

```
producciones/<produccion>/
├── produccion.json
├── escenas/<escena>/v1, v2, …/escena.json   ← versiones (nunca se pisan; las aprobadas no se editan)
└── director/
    ├── cameras/camera_001.json              ← COLOCAR CÁMARA (coordenadas de Blender)
    ├── markers.json                         ← marcadores de tiempo con su contexto
    └── director_notes.json                  ← mensajes del director con su contexto
Release <produccion>: <escena>_v<k>_previa.glb / _previa.json / _revision.mp4 / _revision.ogv / …
```

### camera_NNN.json (formato `estudio.camara/1`)

| campo | qué es |
|---|---|
| `camera_id`, `name`, `shot`, `notes` | identificación, toma asociada, notas del director |
| `time_capture`, `frame_capture` | instante en que se colocó |
| `time_start`, `time_end`, `transition` | tramo en que se usa; `corte` o `suave` (viaja desde la cámara anterior) |
| `position {x,y,z}` | metros, **coordenadas de Blender** (Z arriba) |
| `rotation {x,y,z}` | grados, `rotation_euler` XYZ de la cámara de Blender |
| `quaternion [w,x,y,z]` | la misma orientación, exacta (es la que usa `aplicar`) |
| `forward`, `up` | dirección de mirada y vertical de la cámara (Blender) |
| `fov` (= `fov_v_deg`), `fov_h_deg`, `lens_mm`, `sensor_mm` | óptica: lente equivalente con sensor de 36 mm de ancho |
| `aspect`, `resolution` | 16:9, 1280×720 (la vista del editor es 16:9, igual al cuadro del render) |
| `produccion`, `escena`, `version_escena`, `huella_escena`, `created` | a qué versión corresponde |
| `godot {origin, basis_columns}` | lo crudo de la app, para auditoría |

## 4. Conversión de coordenadas (probada ida y vuelta)

Godot usa los ejes de glTF (Y arriba); Blender, Z arriba. `(x, y, z)_blender = (x, −z, y)_godot`. Las cámaras miran
hacia −Z local con +Y arriba en los tres programas, así que la orientación se convierte con la misma matriz.
Óptica: Godot ajusta el FOV por altura; Blender usa 36 mm de ancho: `fov_h = 2·atan(tan(fov_v/2)·16/9)`,
`lente = 18 / tan(fov_h/2)`. App: `app/main/camara_director.gd`; estudio: `estudio/blender/camara_director.py`.

**Prueba de ida y vuelta** (`pruebas/editor_3d/`): Godot captura cámaras igual que COLOCAR CÁMARA y proyecta una grilla
de puntos a 1280×720; Blender aplica cada archivo a una cámara y proyecta los mismos puntos.

| medición (escena CQB, 15/11/2026) | resultado |
|---|---|
| 12 cámaras libres al azar + 11 de rodaje: diferencia de encuadre | **0,004 px** máx. |
| cámaras de rodaje GLB → captura → Blender vs. cámara original | 0 m, 0°, 0 mm de lente |
| caderas de los 5 personajes en 9 cuadros (45 muestras) vs. Blender | **0,07 mm** máx. |

```
godot --headless --path app --script res://../pruebas/editor_3d/ida_vuelta.gd -- PREVIA.glb PREVIA.json capturas.json
python ida_vuelta_blender.py capturas.json PREVIA.json informe.json     # (con el Python de Blender)
```

## 5. La app (EDITOR 3D)

- **Vista 16:9** con guía de tercios. Cámara libre: táctil (mitad izquierda = joystick para moverse; derecha = mirar;
  dos dedos = subir/bajar y avanzar; ▲▼ = subir/bajar; tocar = seleccionar) y escritorio (arrastrar = mirar, WASD,
  Q/E, rueda = velocidad, Mayús = rápido). Velocidad regulable en CÁMARAS.
- **Modos:** LIBRE · MONTAJE (las tomas de la escena según el tiempo) · ver por una toma (lista de tomas).
- **Línea de tiempo:** ⏹ ⏮ ▶/⏸ ⏭ (cuadro a cuadro), velocidades 0,25× · 0,50× · 0,75× · 1× · 1,25× · 1,50×,
  tiempo y cuadro, cortes de toma y marcadores dibujados sobre la barra.
- **ESCENA:** personajes con el clip que reproduce cada uno ahora, SÓLO EL ELEGIDO (aislar), ENCUADRAR, propiedades
  (posición en coordenadas de Blender, animación actual y la que sigue), objetos con buscador y casilla de visibilidad.
- **CÁMARAS:** COLOCAR CÁMARA, GUARDAR POSICIÓN (rápida, sin formulario), VOLVER A CÁMARA, lista de cámaras del director
  (VER, ✎ renombrar / toma / tramo / transición / notas, ⧉ duplicar, A/B + COMPARAR, 🗑), tomas de la escena.
- **DIRECCIÓN:** mensaje al estudio con contexto, 📍 marcadores, GUARDAR CORRECCIONES, ✔ APROBAR ESCENA, versiones de la
  escena (abrir otra), historial de pedidos con las respuestas del estudio.
- Todo queda también guardado en el teléfono (`user://director/<produccion>_<escena>.json`); sin conexión, los envíos
  esperan y salen solos.

## 6. Límites (dichos sin vueltas)

- El «chat» no es en vivo: los mensajes llegan como pedidos (Issues) y Claude los atiende en la siguiente sesión de
  trabajo; las respuestas se ven en el HISTORIAL. Para que se atiendan solos haría falta un flujo con la API de
  Anthropic (secreto `ANTHROPIC_API_KEY`), que no está configurado.
- La iluminación del visor es de referencia (tiempo real en el teléfono): la luz final es la de Cycles.
- La previsualización se genera en Actions (~5 min por versión): no es instantánea.
- La aprobación compara la **huella**, que incluye el código del estudio: si se cambia `director.py`, `camaras.py`,
  `kit.py` o el generador del escenario después de aprobar, hay que volver a aprobar (a propósito).
- Partir una toma móvil (dolly, grúa, órbita) para insertar una cámara del director comprime su movimiento en el tramo
  que queda: Claude revisa esos cortes en la previsualización nueva.
