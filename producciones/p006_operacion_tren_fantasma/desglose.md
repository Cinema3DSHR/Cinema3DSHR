# OPERACIÓN TREN FANTASMA — desglose de producción

Cada secuencia es una **escena** de la producción (`escenas/s01…s08`), con su versión, su previsualización en el
EDITOR 3D y su aprobación. La película completa se arma con las 8 escenas aprobadas y una previsualización de la
película entera antes del render final (que sólo arranca con «APROBADO. INICIÁ EL RENDER FINAL DE LOS 10 MINUTOS»).

| # | secuencia | tiempo | duración | escenario | fotogramas |
|---|---|---|---|---|---|
| s01 | El transporte | 00:00–01:15 | 75 s | llanura + vías + ruta paralela | 2.250 |
| s02 | La preparación | 01:15–02:20 | 65 s | ruta abierta, cabina, túnel | 1.950 |
| s03 | El salto | 02:20–03:40 | 80 s | ruta paralela + tren | 2.400 |
| s04 | Asalto e infiltración | 03:40–05:35 | 115 s | techos y plataformas del tren | 3.450 |
| s05 | El robo | 05:35–06:35 | 60 s | vagón 14, salida del tren | 1.800 |
| s06 | Persecución en la montaña | 06:35–08:15 | 100 s | ruta de montaña + pueblo | 3.000 |
| s07 | El helicóptero | 08:15–09:20 | 65 s | cornisa + torre de oficinas | 1.950 |
| s08 | Final | 09:20–10:00 | 40 s | valle al atardecer | 1.200 |
| | **total** | | **600 s** | | **18.000** |

## Personajes

| personaje | recurso | origen | adaptación |
|---|---|---|---|
| Lucía Ferrán | `personajes_pelicula/protagonista_femenina` (FBX) | entregado por el dueño (mixamo-respaldo) | escala a 1,68 m; retarget Mixamo |
| Mateo Ibarra | `personajes_pelicula/protagonista_masculino` (FBX) | entregado por el dueño (mixamo-respaldo) | escala a 1,80 m; retarget Mixamo |
| Soldados de Halcón Negro | Ch35, Ch15 (Extraction-tactical), operador (Nexus) | repos del dueño | fusil M4A1/AK47 acoplado (estudio/blender/armas.py) |
| Motociclistas | `pilot.glb` (Ch20 con casco) | Rally-Sim-movile | material negro mate; pose de manejo |
| Piloto del helicóptero | operador (Nexus) | repo del dueño | sentado en cabina |

## Vehículos

| vehículo | recurso | origen | adaptación |
|---|---|---|---|
| Locomotora | `modelos_pelicula/locomotora_diesel.glb` | entregado (mixamo-respaldo) | escala 18 m; bogies y ruedas de acero animadas (estudio) |
| Vagón plataforma | `modelos_pelicula/vagon_plano.glb` | entregado | escala 14 m; ruedas de acero; amarres; autos encima |
| Vagón cerrado | `modelos_pelicula/vagon_cerrado.glb` | entregado | escala 13,7 m; ruedas de acero; puerta corrediza (s04–s05) |
| Autos transportados | los 28 autos de Dream Rally (todos menos el camión Mamut) (`godot/game/models/cars/*.glb` + `.json`) | Rally-Sim-movile | ruedas generadas con las medidas de cada `.json` (arcos, radio, trocha) |
| Auto rampa (Lucía) | `vehiculos_pelicula/auto_rampa` (FBX entregado; cuña delantera, jaula, alerón) | entregado (mixamo-respaldo) | escala 5 m; ruedas y física de Dream Rally; cabina del juego con Lucía y Mateo. **Salta una sola vez**: en s03, al bajarse del acoplado del camión hasta el tren (cámara lenta). Después son los otros los que saltan sobre su cuña (la camioneta en s05, una moto en s06) o los que salen volando (el blindado en s06) |
| Camioneta robada | `modelos_pelicula/pickup_arena.glb` | entregado | ruedas Dream Rally (radio de la pickup del juego); torreta remota construida |
| Blindados de escolta | `modelos_pelicula/vehiculo_blindado_policial.glb` | entregado | ruedas Dream Rally; rotulado de ficción (Halcón Negro); torreta |
| Camión + remolque | Dream Rally `truck` (tractor) + `modelos_pelicula/trailer_plano_camion.glb` | Rally-Sim-movile + entregado | ruedas Dream Rally en los 3 ejes del remolque; rampas hidráulicas |
| Motos | Sweet Home `sc_yamaha_yzr_r6` | Nexus `game/assets/sh3d` | material negro; ruedas con giro |
| Helicóptero | `modelos_pelicula/helicoptero_militar.glb` | entregado | rotor principal y de cola construidos y animados; daño progresivo |
| Tránsito y decorado | Sweet Home: autos, camiones, colectivo | Nexus | estáticos o con recorrido simple |

## Escenarios y decorado

- **Llanura y sierra** (s01, s03, s05): terreno procedural con montañas al fondo, vías (rieles, durmientes, balasto),
  ruta paralela con banquina, alambrados, casas de campo (paredes procedurales + puertas y ventanas Sweet Home),
  árboles Sweet Home (álamos, sauces, abedules, pinos, acacias) y vegetación de Dream Rally, postes, cielo con nubes.
- **Túnel** (s02): boca de hormigón en la ladera, luces de sodio.
- **Ruta de montaña y pueblo** (s06): horquillas con guardarraíl, rocas, casas con interiores Sweet Home (mesas, sillas,
  heladeras, sillones) preparadas para romperse.
- **Cornisa y torre de oficinas** (s07): torre de 10 pisos con escritorios, sillas, mesas y ventanas Sweet Home.
- **Valle al atardecer** (s08).

## Animaciones seleccionadas (mixamo-respaldo/animaciones, retarget del estudio)

- **Parkour de Mateo (s04)**: Running_Jump, Jump_Over, Vault_Over_Box, Running_Slide, Sprint_To_Wall_Climb,
  Climbing_To_Top, Braced_Hang, Braced_Hang_Shimmy, Freehang_Climb, Jump_Down, Landing, Dive_Roll, Sprinting_Forward_Roll,
  Crouched_Run, Crouch_Cover_To_Cover, Cover_Idle, Emerge_From_Cover.
- **Interacción con vehículos (s02, s05)**: Entering_Car, Exiting_Car, Driving, Opening (puerta corrediza), Kneeling_Inspecting.
- **Soldados (s01, s04)**: Pro_Rifle_Pack (idle_aiming, walk/run, crouch), firing_rifle, hit_reaction, Rifle_Death,
  Standing_Death_* (4 direcciones), Falling_Back_Death, Flying_Back_Death, Shoulder_Hit_And_Fall, Falling_From_Losing_Balance.
- **Ambiente (s01)**: Talking_On_Phone / Looking_Around / Rifle idle variants.

## Cámaras planificadas (resumen; detalle por toma en cada escena.json)

s01 aérea de revelación, lateral de seguimiento, baja junto a los bogies, desde un vagón hacia la locomotora, recorrido
sobre los autos, seguimiento de blindados y motos, plano de soldados, grúa final con título · s02 exterior del convoy,
interior de cabina, contraplano de Lucía, túnel, salida marcha atrás en plano general y detalle de ruedas · s03 interior,
capó, baja en ruedas, lateral del salto, aérea, cámara lenta de despegue y aterrizaje · s04 abiertos que ubican la
acción + cercanos de parkour y combate, subjetiva de Mateo, cámara colgada del costado del vagón · s05 interior del
vagón, tablero, salida en rampa · s06 diez tipos de cámara de persecución (interior, trasera, ruedas, lateral, capó,
suelo, aérea, derrape, fija en curva, desde otro auto) · s07 helicóptero desde la ruta, desde la cabina, desde arriba,
torreta, impacto en cámara lenta · s08 alejamiento aéreo y título.

## Explosiones y destrucción (técnica)

Sin simulaciones costosas: geometría fragmentada de antemano (muros y vidrios partidos en piezas con trayectorias
balísticas calculadas), objetos del interior (Sweet Home) lanzados por la onda expansiva, partículas como mallas
instanciadas, humo y fuego con volúmenes de baja resolución + emisión, luz de la explosión animada. Cada impacto tiene
causa visible (choque, disparos, caída del helicóptero). Cámara lenta = tomas re-muestreadas en el tiempo (la escena se
evalúa en sub-cuadros).

## Diseño sonoro

Procedural del estudio (motores con régimen según velocidad, ruedas de tren con golpes de junta por distancia recorrida,
disparos con reverberación según el lugar, impactos, vidrios, escombros, viento) + ElevenLabs para música y efectos
especiales (helicóptero, explosión mayor), **con estimación de costo antes de gastar** y dentro de
`config/presupuesto_audio.json`. Voces de los protagonistas: ElevenLabs, sólo con autorización.

## Plan de producción y render

1. s01 construida → previsualización → revisión del dueño (estamos acá).
2. s02…s08 en orden, cada una con su previsualización y correcciones.
3. Previsualización de la película completa (las 8 escenas en una línea de tiempo) + animática de baja calidad.
4. Aprobación con huella de las 8 versiones.
5. Render final: 18.000 fotogramas, Cycles CPU 1280×720, 6 muestras, adaptativo 0,05, OIDN, 6 rebotes, árbol de luces,
   semilla 0. Bloques por escena en Actions (19 trabajos simultáneos; ~18–25 s por fotograma medidos en CQB →
   ~90–125 h de CPU, ~5–7 h de reloj repartidas en varias tandas). Montaje H.264 + audio final, release, catálogo.
6. Limpieza: fotogramas sólo como artefactos temporales; nada pesado en Git.
