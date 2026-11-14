# Películas de fútbol

Todo lo necesario para producir escenas de fútbol con jugadores animados, arquero, barrera, público y pelota con
física real. Recursos originales (sin modificar) en **mixamo-respaldo/futbol_free_kick_swipe/**.

## Recursos

| Recurso | Dónde | Notas |
|---|---|---|
| Jugador con 3 223 animaciones | `mixamo:futbol_free_kick_swipe/exportados/jugador_con_animaciones.glb` | Modelo Tripo3D, esqueleto mixamorig de 23 huesos, 1,75 m, mira a +X. Clips `f_jn_…` (campo, 2 125), `k_jn_…` (arquero, 476), `s_jn_…` (escenas: festejos, barrera, 622). |
| Catálogo de clips | `catalogo/futbol.json` | Por clip: biblioteca, acción, espejo, duración, **rol** (34), **categorías** (25), etiqueta, toma original y, en los remates (560), **golpeo**: cuadro de contacto `tc`, pie, potencia, elevación, superficie, carrera. También entran al buscador general (`catalogo/animaciones.json`, esqueleto `futbol_tripo_23`). |
| Estadio de fútbol 11 | escenario `estadio_futbol11_noche` (generador `estudio/escenarios/estadio_futbol.py`) | Cancha 105 × 68 m, arcos en x = ±52,5. Se rematerializa en Blender (los shaders de Godot no viajan en el GLB). |
| Física del balón | `estudio/blender/pelota.py` | Valores reales del juego (`FISICA_E_IA.md`): arrastre Cd 0,25, Magnus k 0,0018, rebote 0,54, rodadura, red que absorbe. |

## El estadio (`parametros`)

- `hora`: `noche` (4 torres de iluminación) o `dia` (sol y cielo).
- `animo`: `calma`, `aplauso`, `festejo`, `tension`, o una línea de tiempo `[[0, "tension"], [6.9, "festejo"]]`.
- `colores_local`, `colores_visitante`: butacas por sectores y carteles LED (degradés **sin marcas**).
- `publico`: 0..1 (fracción de butacas ocupadas). Los 13 074 hinchas son sprites 2D del juego (6 poses × 12
  personas); el GLB los traía todos en el origen, así que el estudio los sienta butaca por butaca mirando a la cancha.
- Anclas: `centro`, `arco_este/oeste`, `penal_este/oeste`, `medialuna_*`, `corner_ne/se/no/so`, `banco_local/visitante`,
  `camara_tv`, `detras_arco_*`, `tribuna_este`, `angulo_superior_der_este`, `angulo_superior_izq_este`.

## Personajes en `escena.json`

```jsonc
"personajes": [{
  "id": "tirador", "modelo": "futbol:jugador",
  "uniforme": {"camiseta": [r,g,b], "short": [..], "medias": [..], "botines": [..], "piel": [..], "pelo": [..]},
  "acciones": [
    {"clip": "f_jn_idle_0520", "inicio_s": 0, "pos": [24.5, -9.0], "mirando_deg": 15},
    {"clip": "f_jn_setpiece_shot_2594", "inicio_s": 3.4, "pos": [24.5, -9.0], "mirando_deg": 15},
    {"clip": "f_jn_celebrate_scorer_0942", "inicio_s": 6.3, "encadenar": true, "mirando_deg": -60, "repetir": 1, "velocidad": 1.0}
  ]}]
```
- `mirando_deg`: 0 = hacia el arco de x = +52,5; 180 = hacia el otro arco.
- `encadenar`: el clip empieza donde terminó la cadera del anterior (las carreras no "vuelven" al origen).
- Si un clip con `repetir` se superpone con el siguiente, se corta solo.

## Pelota

```jsonc
"pelota": {"patada": {"personaje": "tirador", "clip": "f_jn_setpiece_shot_2594",
           "destino": {"ancla": "angulo_superior_der_este"}, "velocidad": 26, "efecto": [0, 0, -35], "arco": "este"}}
```
La pelota espera donde va a pegar el pie (punta del botín en el **cuadro de contacto** del clip, `golpeo.tc`) y sale
con la velocidad pedida; el estudio busca la dirección para que, con aire y efecto, pase por el `destino`.
`efecto` es el giro (rad/s): Z negativo curva hacia la derecha del tirador. La patada y el gol quedan como eventos
para el sonido (golpe, red, ovación). Las cámaras pueden seguirla: `{"movil": "pelota"}`.

## Cámaras útiles

`seguimiento`/`detalle` con `"movil": "<personaje>"` y `punto_base`/`punto`: `cadera`, `pecho`, `cabeza`, `pies`.
Ejemplo de festejo al hombro: `{"tipo": "seguimiento", "movil": "tirador", "punto_base": "cadera", "desp_local": [0, 4.5, 0.6], "objetivo": {"movil": "tirador", "punto": "cabeza"}, "lente_mm": 50, "apertura": 2.8, "temblor": 0.02}`.

## Elegir clips

`python3 -c "import json; c=json.load(open('catalogo/futbol.json'))['clips']; print([x['clip'] for x in c if x['rol']=='gk_dive'][:20])"`
Roles más usados: `gk_dive` 216, `header` 190, `kick_shot` 140, `kick_pass` 128, `receive` 114, `volley` 108,
`celebrate*`, `dejected`, `wall`, `setpiece_shot`, `run`, `sprint`, `idle`. Los `_mirror` son la versión espejada.

## Escena de prueba

`producciones/p001_futbol_tiro_libre` (14 s, 6 tomas): plano de TV, detrás del tirador, detalle del remate, desde
atrás del arco, festejo al hombro y grúa. Verificada en la sesión con fotogramas fijos y un render completo en
calidad previa.

## Render en Actions

Los recursos de fútbol están en un repo **privado**: el flujo de render necesita el secreto `ASSETS_TOKEN`
(token fine-grained de sólo lectura: *Contents: Read* sobre **mixamo-respaldo**) y baja sólo los archivos que usa
la escena. Mientras el paquete esté en la rama `ccr-6d21fe8a-76t9c3` de mixamo-respaldo, el flujo lee esa rama
(cambiable con la variable `MIXAMO_REF`).

## Pendiente
- Conducción de pelota en juego corrido (pases encadenados entre jugadores, recepciones con `receive`).
- Número y nombre en la espalda (el juego los proyecta con datos de reposo que el GLB no trae).
- Sonido con ElevenLabs (relato, cánticos) cuando se autorice.
