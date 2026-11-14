Medición de Godot Movie Maker con el GLB liviano del visor de la mansión (no incluido: `curl -L https://github.com/webmaletin-art/Cinema3DSHR/releases/download/p000_prueba_mansion/e01_v1_visor.glb -o visor.glb`).
Ejecutar: `xvfb-run -a -s "-screen 0 1400x900x24" godot --path . --rendering-driver opengl3 --resolution 1280x720 --write-movie out.avi --fixed-fps 30 --quit-after 90`
Sin GPU (Mesa llvmpipe, software). Luces con las intensidades fijas que usa la app del visor, sin sombras, materiales planos.
