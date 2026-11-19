#!/bin/bash
# «Rally Convoy» — arma desde cero el set de la cinemática a partir del juego Dream Racing (repositorio Rally-Sim-movile), sin tocar el original.
# Uso: ./preparar_set.sh [carpeta_destino=/home/user/rally_cine]
# Deja en <destino>/godot una COPIA del proyecto del juego con: ruta nueva (parche_ruta.py), IA con trazada libre (parche_ia.py), resolución
# vertical 480×854 y la carpeta cine/ (núcleo, pelotón, dirección de cámaras, escena). Luego importa los recursos y corre la simulación
# (genera cine/telemetria.json). Grabar: ./grabar.sh
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-/home/user/rally_cine}"
JUEGO="${DR_JUEGO:-/home/user/Rally-Sim-movile/godot}"
mkdir -p "$DEST"
[ -d "$DEST/godot" ] || cp -a "$JUEGO" "$DEST/godot"
python3 "$AQUI/parche_ruta.py" "$DEST/godot/game"
python3 "$AQUI/parche_ia.py" "$DEST/godot/game"
sed -i 's/window\/size\/viewport_width=[0-9]*/window\/size\/viewport_width=480/; s/window\/size\/viewport_height=[0-9]*/window\/size\/viewport_height=854/' "$DEST/godot/project.godot"
mkdir -p "$DEST/godot/cine"
cp "$AQUI"/cine/*.gd "$AQUI"/cine/cine.tscn "$DEST/godot/cine/"
[ -f "$DEST/godot/cine/telemetria.json" ] || cp "$AQUI/cine/telemetria.json" "$DEST/godot/cine/" 2>/dev/null || true
( cd "$DEST/godot" && godot --headless --path . --import )
echo "Set listo en $DEST/godot. Simulación sin imagen (genera la telemetría):  cd $DEST/godot && godot --headless --path . -s cine/sim_headless.gd"
