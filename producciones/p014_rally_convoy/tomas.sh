#!/bin/bash
# uso: tomas.sh <seek> <cam:car> ...   → guarda /home/user/rally_cine/tomas/<cam>_<car>_<seek>.png
cd /home/user/rally_cine/godot
mkdir -p /home/user/rally_cine/tomas
SEEK=$1; shift
for spec in "$@"; do
  cam=${spec%%:*}; car=${spec##*:}
  out=/home/user/rally_cine/tomas/${cam}_${car}_${SEEK}.png
  timeout 300 xvfb-run -a -s "-screen 0 1280x1024x24" godot --rendering-driver opengl3 --path . --resolution 480x854 cine/cine.tscn -- --seek=$SEEK --shot=$out --cam=$cam --car=$car > /home/user/rally_cine/tomas/log_${cam}_${car}_${SEEK}.txt 2>&1
  echo "listo $out"
done
