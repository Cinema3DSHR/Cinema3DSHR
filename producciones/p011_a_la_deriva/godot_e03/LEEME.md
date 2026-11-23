# Nave única de «A la deriva» (capítulo 3) — proyecto Godot

**Una sola nave** (`nave.tscn`) para todo el capítulo: arreglar una pieza o su lugar aquí se arregla en TODAS las tomas.
Cada objeto es una pieza propia en `piezas/*.tscn` (frente hacia −Z, origen en el piso); la nave las instancia (`tools/construir_nave.gd`).

## Reconstruir
```
python tools/pantallas.py assets/pantallas      # pantallas, muros, suelos, rótulos
python tools/fondo.py assets/fondo              # nebulosa y Tierra
# plantas: Blender (pruebas/personajes_cap3 → ver docs) → assets/plantas/*.glb
godot --headless --path . --import
godot --headless --path . --script res://tools/construir_nave.gd
godot --headless --path . --script res://tools/verificar.gd     # orientación, flotando, atravesadas (debe dar 0 problemas)
godot --headless --path . --script res://tools/exportar_glb.gd -- SALIDA.glb   # GLB para el visor HTML
xvfb-run -a godot --path . --rendering-driver opengl3 --script res://tools/captura.gd -- PREFIJO   # capturas de revisión (no es render)
```
Los GLB, las texturas generadas y los modelos de Sweet Home/plantas no van al historial de Git (regla 5): se regeneran con estos scripts.
