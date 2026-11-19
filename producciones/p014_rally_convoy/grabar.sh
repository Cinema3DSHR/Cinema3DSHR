#!/bin/bash
# Graba la cinemática con el modo de grabación de Godot (sin Blender): 480×854 vertical, 12 cuadros/s, con el audio original del juego.
# Uso: ./grabar.sh [salida.avi] [t_end=296] [fps=12]      (después: ffmpeg -i salida.avi -c:v libx264 -crf 23 -pix_fmt yuv420p -c:a aac salida.mp4)
DEST="${DR_DEST:-/home/user/rally_cine}"
OUT="${1:-$DEST/salida/rally_convoy.avi}"; TEND="${2:-296}"; FPS="${3:-12}"
mkdir -p "$(dirname "$OUT")"
cd "$DEST/godot" && xvfb-run -a -s "-screen 0 1280x1024x24" godot --rendering-driver opengl3 --path . --write-movie "$OUT" --fixed-fps "$FPS" cine/cine.tscn -- --fps="$FPS" --t_end="$TEND"
