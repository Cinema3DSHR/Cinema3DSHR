#!/bin/bash
# p017 · montaje final: main.mp4 (cuadros 0–1661 renderizados) + cierre en tres paneles (s10) + subtítulos ASS + audio → video1.mp4
# Uso: montaje.sh main.mp4 salida.mp4 audio.wav subtitulos.ass
set -e
MAIN="$1"; SAL="$2"; WAV="$3"; ASS="$4"
FPS=30
# tres tomas del propio video para el cierre (cada una se repite hasta cubrir 338 cuadros = 11,27 s)
# A prudente: cuadros 300–399 (casa y camino) · B impulsivo: 1215–1314 (fiesta) · C generoso: 1445–1544 (familia)
panel() {  # $1 inicio, $2 alto-recorte-y, $3 etiqueta
  echo "[0:v]trim=start_frame=$1:end_frame=$(( $1 + 100 )),setpts=PTS-STARTPTS,crop=540:320:0:$2,loop=loop=3:size=100:start=0,trim=end_frame=338,setpts=PTS-STARTPTS[$3]"
}
ffmpeg -y -v error -i "$MAIN" -filter_complex "$(panel 300 330 pa);$(panel 1215 400 pb);$(panel 1445 330 pc);[pa][pb][pc]vstack=inputs=3,format=yuv420p[fin]" -map "[fin]" -r $FPS -c:v libx264 -crf 14 -preset fast fin.mp4
ffmpeg -y -v error -i "$MAIN" -i fin.mp4 -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v];[v]subtitles=$ASS:fontsdir=/usr/share/fonts/truetype/dejavu,format=yuv420p[o]" -map "[o]" -r $FPS -c:v libx264 -crf 16 -preset medium -an v_sub.mp4
ffmpeg -y -v error -i v_sub.mp4 -i "$WAV" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$SAL"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration,nb_frames -of default=nw=1 "$SAL"
