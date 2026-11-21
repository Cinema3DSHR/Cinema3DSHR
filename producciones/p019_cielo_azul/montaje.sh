#!/bin/bash
# p018 · montaje: video renderizado + subtítulos ASS + audio → mp4 final. Uso: montaje.sh main.mp4 salida.mp4 audio.wav subtitulos.ass
set -e
ffmpeg -y -v error -i "$1" -vf "subtitles=$4:fontsdir=/usr/share/fonts/truetype/dejavu,format=yuv420p" -r 30 -c:v libx264 -crf 16 -preset medium -an v_sub2.mp4
ffmpeg -y -v error -i v_sub2.mp4 -i "$3" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$2"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration,nb_frames -of default=nw=1 "$2"
