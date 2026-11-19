#!/bin/bash
cd /home/user/rally_cine/godot
mkdir -p /home/user/rally_cine/plan
for T in "$@"; do
  out=/home/user/rally_cine/plan/t_${T}.png
  timeout 400 xvfb-run -a -s "-screen 0 1280x1024x24" godot --rendering-driver opengl3 --path . cine/cine.tscn -- --seek=$T --shot=$out > /home/user/rally_cine/plan/log_${T}.txt 2>&1
  echo "listo $out"
done
