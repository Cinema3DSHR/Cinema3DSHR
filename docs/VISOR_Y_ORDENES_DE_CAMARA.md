# Visor de escenas y órdenes de cámara (flujo rápido de revisión)

Para el chat de Claude que trabaje en el estudio. Desde el 18/11/2026 el dueño revisa las escenas en un **HTML en el
navegador del celular**, no en Godot ni en la app. Así funciona el ida y vuelta y así se aplica lo que manda.

## 1. Qué es

- **Visor**: `visor/visor_escena.html`, un solo archivo; el detalle de los botones está en `visor/LEEME.md`. El dueño
  lo abre desde **https://claude.ai/artifact/SEW8AN7eTVhb1t3vaRAvJq**, una página privada. Para actualizarla, desde otro
  chat: herramienta Artifact con `url` = ese enlace. Primero hay que leerla (`action: read`) y después publicar el
  contenido entre `<!--ARTIFACT-START-->` y `<!--ARTIFACT-END-->` del archivo del repo.
- Abre el **GLB** de la escena y, si viene, el **JSON** de la línea de tiempo (tomas, cámaras, personajes). Muestra:
  - MONTAJE, TOMA y LIBRE (recorrer la escena);
  - cuadro a cuadro;
  - el cuadro del render con su proporción;
  - una luz pareja, sin las luces del archivo ni sombras.
- El dueño coloca o modifica cámaras y escribe notas. **📋 COPIAR PARA CLAUDE** le arma un texto que pega en el chat.

## 2. El ida y vuelta

1. Claude arma o corrige la escena: receta `producciones/<p>/escenas/<e>/v<k>/escena.json` (una corrección es una
   **versión nueva**: `python -m estudio nueva-version`) y `python -m estudio validar <escena.json>`.
2. **GLB liviano para el visor, en la sesión, sin Actions** (no renderiza; ver «Instalación» en `docs/FLUJO_DE_PRODUCCION.md`):
   `$PY -m estudio previa producciones/<p>/escenas/<e>/v<k>/escena.json --salida <scratchpad>/previa`
   Salen `<e>_v<k>_previa.glb` y `.json`. Con `previa.yml` (Actions) se publican también en la release, para la app.
3. Mandarle **los dos archivos** con `SendUserFile` (`display: "attach"`) y recordarle que en el visor elija los dos
   juntos. El de e01 de Dúo Cero pesa 28 MB; con escenas más grandes, bajar `presupuesto` y `max_poligonos` en
   `estudio/blender/previa.exportar`.
4. El dueño revisa y pega el texto (punto 3). Claude lo aplica en una **versión nueva** (punto 4), vuelve al paso 2 y
   le avisa qué cambió.

## 3. El texto que llega

Empieza con `VISOR DE ESCENA · <produccion> · <escena> v<k> (huella …)`. Sigue con un bloque legible por cámara o nota
y termina con un bloque ```json``` con formato **`estudio.visor_ordenes/2`**. **El que manda es el JSON**; el texto es
para leerlo.

```
{ formato, produccion, escena, version, huella, fps,
  camaras: [ { n, accion: "nueva" | "modificar",
               toma,                 // modificar: la toma cuya cámara cambia · nueva: la toma que reemplaza en el tramo o "nueva"
               camara_toma, desde_s, hasta_s, cuadro_desde, cuadro_hasta,   // tramo en tiempo de PELÍCULA
               medida_en_cuadro,     // cuadro en que se midió la pose (importa si la cámara está quieta en el mundo)
               movimiento,           // "fija" | "como estaba" | "con paneo suave…" | "acercándose… (dolly in)" | "alejándose… (dolly out)" | "cámara en mano"
               nota,                 // texto libre del dueño
               cambio,               // sólo modificar: el cambio en palabras («0,30 m más alta · lente 32 → 45 mm»)
               original,             // sólo modificar: {pegada_a, relativa, mundo, lens_mm} de la cámara de la toma
               pegada_a,             // nombre del objeto al que va pegada (p. ej. "tren_06_cerrado") o null = quieta
               relativa,             // pose respecto de ese objeto: objeto.matrix_world⁻¹ · cámara.matrix_world (Blender)
               mundo,                // pose en el mundo en medida_en_cuadro (Blender)
               lens_mm, fov_v_deg, sensor_mm: 36, sensor_fit: "AUTO", aspecto, resolucion } ],
  notas: [ { cuadro, t, toma, nota } ] }
```

Cada pose (`relativa`, `mundo`) trae `position {x,y,z}` en metros, `rotation {x,y,z}` en grados (Euler **XYZ de
Blender**, el `rotation_euler` de la cámara), `quaternion [w,x,y,z]` (exacto, preferirlo) y `forward {x,y,z}` (hacia
dónde mira). Todo está ya en **coordenadas de Blender** (X, Y en el piso, Z arriba): el visor convierte desde glTF con
(x, y, z)_b = (x, −z, y)_g. **Usar los números tal cual, nunca adivinar desde una captura.**

Comprobado con Dúo Cero e01 v1:
- la pose `mundo` coincide con la cámara de Blender (rotación igual, ≤ 4 mm de diferencia);
- la pose `relativa` de la toma t05 coincide con su `desp_local` (x −0,30, y −1,35);
- la z sale 2,8 m más alta, porque es respecto del ORIGEN del vagón y no del ancla del piso;
- la pose `relativa` no cambia al avanzar el tiempo.

## 4. Cómo aplicar cada orden (en una versión nueva)

Lo primero es mirar `pegada_a`.

**a) `pegada_a: null`: cámara quieta en el mundo.** Es una toma `tipo: "director"`. El camino directo es armar un dict
de cámara del director y usar `estudio.direccion.aplicar_camaras(m, [cam])`, que corta las tomas del tramo y crea
`d_<camera_id>`:
`{"camera_id": "visor_<n>", "name": "visor <n>", "time_start": desde_s, "time_end": hasta_s,
  "position": mundo.position, "quaternion": mundo.quaternion, "rotation": mundo.rotation, "lens_mm": lens_mm,
  "sensor_mm": 36, "aspect": aspecto, "notes": nota}`

**b) `pegada_a` = un objeto que se mueve (vagón, auto): toma RÍGIDA.** Una toma `director` quedaría quieta mientras el
vagón se va. En `estudio/blender/camaras.py` (`rigido: true`) la cámara se cuelga del objeto del móvil con:
`location = ancla(punto_base) + desp_local` y mira a `ancla(objetivo.punto) + objetivo.desp_local`.

Los pasos:
1. Encontrar el `movil` cuyo objeto es `pegada_a`. En Blender, después de `director.construir(m)`:
   `ctx = res["contexto"]; [k for k, v in ctx.moviles.items() if v.get("objeto") and v["objeto"].name == pegada_a]`.
   Las anclas están en `ctx.moviles[k]["anclas"]`.
2. `desp_local = relativa.position − ancla(punto_base)`.
   - En un **modificar** de una toma que ya era rígida, el ancla sale sin Blender:
     `ancla = original.relativa.position − desp_local_viejo`.
   - En el caso más simple, `desp_local_nuevo = desp_local_viejo + (relativa − original.relativa)`.
3. `objetivo = {"movil": k, "punto": <el mismo>, "desp_local": relativa.position + 5·relativa.forward − ancla(punto)}`
   (5 m adelante, en el marco del objeto).
4. `lente_mm = lens_mm`. Mantener `rigido: true` y el resto de la toma.

**c) Pegada a un personaje.** No hay toma rígida para personajes. Usar una toma `seguimiento` o `estatica` que mire
al personaje, con la posición del mundo en `medida_en_cuadro`, y avisarle al dueño de la aproximación.

**d) `modificar` sobre una toma que se mueve** (seguimiento, dolly, órbita, grúa): aplicar el `cambio` a sus
parámetros (`desp_local`, `desp_local_final`, `lente_mm`, `lente_final_mm`, altura) para que todo el movimiento quede
corrido igual. El texto lo indica con «La toma es de tipo … (se mueve)».

**Movimiento** cuando no es «fija» ni «como estaba»:

| texto | qué usar |
|---|---|
| paneo suave | `tipo: "paneo"` con `objetivo_final` sobre el personaje |
| dolly in / dolly out | `desp_local_final` o `lente_final_mm` |
| en mano | `temblor` (≈ 0,02–0,04) |

**Tramos:**
- `desde_s` y `hasta_s` están en tiempo de película. Las tomas de la receta usan `inicio_s` y `duracion_s`, que deben
  quedar contiguas y sumar la duración: `validar` lo controla.
- Si la escena tiene `mapa_tiempo` (cámara lenta), los segundos del visor son los de la película, igual que los de las
  tomas.

**Notas** (`notas[]`): cambios que no son de cámara (miradas, cortes, animaciones). Aplicarlos con criterio y, si no
se entienden, preguntar.

## 5. Comprobar antes de mandar (sin render)

- `python -m estudio validar` sobre la versión nueva.
- En Blender (bpy, sin render): `director.construir(m)` y, en `medida_en_cuadro`, comparar la cámara nueva con la orden:
  - pegada: `obj.matrix_world.inverted() @ cam.matrix_world` contra `relativa`;
  - quieta: `cam.matrix_world` contra `mundo`;
  - tolerancia ≤ 1 cm y ≤ 0,5°, y el lente igual.
- Exportar el GLB nuevo (punto 2), mandarlo y decir en una línea qué se cambió de cada cámara.
- Anotar en `docs/REGISTRO.md`.

## 6. Render

Desde el 18/11/2026 el candado está **quitado** (`config/candado_render.json`): cuando el dueño dice en el chat
«renderizá …», se lanza el flujo que corresponda con la configuración de la producción, sin APROBAR ni AUTORIZAR en
la app. Sin su orden, no se renderiza (ni pruebas ni «para mostrar»).
