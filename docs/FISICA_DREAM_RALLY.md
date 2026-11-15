# Física, cabinas y pilotos de Dream Rally en las películas

Pedido del dueño (15/11/2026): «las físicas de los autos tenés que sacarlas de Dream Rally: tienen interior,
suspensión, aceleración, drift, pilotos, físicas reales». No se reescribió nada: el estudio corre **el mismo código
del juego** (Rally-Sim-movile, `godot/game/`) con Godot sin cabeza y hornea el resultado en Blender.

## Cómo funciona

```
plan (Python) ──► estudio/fisica_dr/grabar.gd en Godot 4.7.2 (headless)
                    · physics/vehicle_physics.gd del juego, 120 Hz con 2 subpasos (gomas, suspensión, caja, diferenciales,
                      ABS / control de tracción / estabilidad, aerodinámica, saltos)
                    · data/car_build.gd + vehicles.json: los parámetros de fábrica de cada auto (pisables por plan)
                    · un conductor que sigue la trayectoria (pure pursuit) y un horario de posición (s objetivo por tiempo),
                      con eventos: freno de mano, gas, freno, volantazo (derrapes)
                    · opcional "cabina": car/cockpit.gd + rig_pilot.gd + crew_motion.gd del juego → habitáculo y los dos
                      pilotos con su cinemática inversa y fuerzas G, cuadro a cuadro, exportados a GLB animado
                ◄── por cuadro: carrocería (posición + orientación con cabeceo, rolido y derrape), altura de cada rueda
                    (suspensión), giro de cada rueda, dirección, velocidad, rpm, marcha, deslizamiento por goma, entradas
Blender: vehiculos_dr.aplicar_fisica(rig, registro, cuadros) · vehiculos_dr.cabina(rig, glb, col)
```

- Caché: `datos/fisica_dr/<huella>.json.gz` (texto comprimido, versionado: Actions reproduce la misma simulación sin
  Godot). La huella depende del plan y de `grabar.gd`; el archivo anota la huella de cada archivo de física del juego
  y el commit de Rally-Sim-movile (procedencia).
- Las cabinas (GLB) van a `salida/fisica_dr/` y **no** a Git: se regeneran (necesitan Godot y los modelos del juego:
  `pilot.glb`, `models/cabin`, el GLB del auto). Un flujo que use cabinas tiene que instalar Godot 4.7.2.
- Ejes: entrada y salida en coordenadas de Blender; adentro, las del juego ((x, y, z)_juego = (x, z, −y)_blender).
  El origen grabado es el del modelo del auto (el nodo «Body» del juego), así la cabina y las ruedas caen donde las
  pone el juego (p. ej. el Bisonte XR lleva la carrocería 0,34 m más alta que las ruedas: `rideOffset`).

## Vidrios

Los GLB de los autos del juego son una sola malla: los vidrios los dibuja el sombreador del juego con las medidas del
`.json` (`glass.ws`, `glass.rg`, `glass.poly`, `cab_hw`). `estudio/blender/vidrios_dr.py` arma la misma máscara con
nodos (mismas fórmulas) y pone vidrio translúcido para que se vean los pilotos (como la opción del juego «Ver los
pilotos desde las cámaras de afuera»), o polarizado (`claro=False`).

Desde afuera se esconde lo que en el juego sólo existe para la cámara de adentro (techo, paneles de puertas, parantes,
capó del habitáculo: son un poco más grandes que el auto real); quedan butacas, tablero, consola, piso, jaula,
pilotos, volante, palancas y pedales.

## Probado (15/11/2026)

- Recta + curva de 60 m + derrape con freno de mano a 79 km/h (Bisonte XR y Cóndor Kodiak): 1,5 s de simulación para
  2 autos × 20 s; seguimiento de velocidad objetivo; contravolanteo y recuperación.
- Cabina del Bisonte XR con los dos pilotos animados: 8 s (incluye importar los modelos); 85 mallas, 2 esqueletos,
  360 cuadros; en Blender se ven piloto y copiloto a través del parabrisas y las ventanillas.
- s01 (Tren Fantasma): los dos blindados de escolta con la física del Cóndor T6 (medidas y peso del blindado).

## Límites

- La física del juego es de auto apoyado en el piso: cabeceo y rolido topan en ±0,6 rad. Vuelcos y vuelos (el
  blindado que da vuelta la cuña del auto rampa) se hacen con trayectoria balística aparte.
- Las motos no usan esta física (es de 4 ruedas): siguen con la dinámica del estudio.
- Piso: plano o rejilla de alturas (bilineal); la superficie (asfalto, tierra…) es una sola por plan por ahora.
