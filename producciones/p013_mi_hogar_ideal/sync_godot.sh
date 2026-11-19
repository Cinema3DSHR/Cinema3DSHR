#!/bin/bash
# Lleva al directorio de trabajo de Godot (con los modelos, que no van a Git) el proyecto del repo y el layout.json.
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
DEST=/home/user/casa/godot
python3 "$AQUI/disenio.py" "$@"
mkdir -p "$DEST/escena" "$DEST/herramientas" "$DEST/salida"
cp "$AQUI/godot/project.godot" "$DEST/"
cp "$AQUI/godot/escena/"* "$DEST/escena/"
cp "$AQUI/godot/herramientas/"*.gd "$DEST/herramientas/"
cp "$AQUI/layout.json" "$DEST/layout.json"
touch "$DEST/salida/.gdignore"
