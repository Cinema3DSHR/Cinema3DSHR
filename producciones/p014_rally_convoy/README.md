# p014 · Rally Convoy (cinemática de Dream Racing, etapa Godot)

Set reutilizable: ruta de 8,1 km generada con el generador de la Aventura (estación → peaje → ciudad → campo → puente → montaña Hill Climb, todo asfalto),
siete autos ORIGINALES completos (pickup Yaguareté, Kodiak, G4, Bisonte XR, Aerion, Max Sport, GT3 RS) con cabina 3D y pilotos animados, física e IA
originales del juego, pelotón con trazada de carrera, auto fantasma con cámara y dirección de cámaras. Se graba con el modo de grabación de Godot.
- `preparar_set.sh` arma una COPIA del juego con los parches (`parche_ruta.py`, `parche_ia.py`), resolución 480×854 y la carpeta `cine/`.
- `cine/sim_headless.gd` corre la simulación sin imagen y mide el pelotón (choques, fuera de ruta, derrapes); genera `telemetria.json`.
- `grabar.sh` graba AVI con audio (≈12 min de reloj para 296 s). `tomas.sh` / `planshots.sh`: fotogramas de control.
Nada de esto sube videos ni modelos al repositorio (los modelos viven en el juego, Rally-Sim-movile).
