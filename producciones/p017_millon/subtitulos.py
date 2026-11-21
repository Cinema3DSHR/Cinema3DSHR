"""p017 · subtítulos y textos en pantalla (ASS, se queman con ffmpeg/libass). Los tiempos salen de la narración real; las frases se parten en renglones cortos
(≤ 26 caracteres) y dentro de la zona segura (abajo, con margen para teléfonos). Uso: python3 subtitulos.py salida.ass"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(AQUI, "guion.json")))
V = json.load(open(os.path.join(AQUI, "duraciones_voz.json")))
INICIO = {"b01_gancho": 0.0, "b02_saldo": 4.16, "b03_prudente": 9.5, "b04_impulsivo": 18.3, "b05_auto": 27.0, "b06_casa": 30.3, "b07_piscina": 33.2,
          "b08_tele": 35.9, "b09_resto": 39.7, "b10_cero": 43.9, "b11_generoso": 48.0, "b12_cierre": 55.4, "b13_pregunta": 60.4}


def t_ass(s):
    h = int(s // 3600)
    m = int(s % 3600 // 60)
    x = s % 60
    return f"{h}:{m:02d}:{x:05.2f}"


def partir(texto, maxc=26):
    """Parte en bloques de 1–2 renglones sin cortar palabras; cada bloque es un subtítulo."""
    pal = texto.split()
    bloques, linea, bloque = [], "", []
    for p in pal:
        if len(linea) + len(p) + (1 if linea else 0) > maxc:
            bloque.append(linea)
            linea = p
            if len(bloque) == 2:
                bloques.append(bloque)
                bloque = []
        else:
            linea = (linea + " " + p).strip()
    if linea:
        bloque.append(linea)
    if bloque:
        bloques.append(bloque)
    return ["\\N".join(b) for b in bloques]


def main(salida):
    cab = """[Script Info]
ScriptType: v4.00+
PlayResX: 540
PlayResY: 960
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,40,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,1,2,40,40,170,1
Style: Titulo,DejaVu Sans,36,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,5,40,40,40,1
Style: Gran,DejaVu Sans,50,&H0000E5FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,5,40,40,40,1
Style: Panel,DejaVu Sans,30,&H0000E5FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,1,7,20,20,20,1
Style: Aviso,DejaVu Sans,19,&H00D8D8D8,&H000000FF,&H00000000,&H80000000,0,1,0,0,100,100,0,0,1,2,0,2,30,30,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for b in G["beats"]:
        bid = b["id"]
        t0 = INICIO[bid]
        dur = V[bid]["dur_s"]
        blq = partir(b["texto"])
        tot = sum(len(x) for x in blq)
        t = t0
        for x in blq:
            d = dur * len(x) / tot
            if bid == "b01_gancho":
                continue       # el gancho va como título grande
            if bid in ("b12_cierre", "b13_pregunta"):
                continue       # el cierre va como título grande
            ev.append(f"Dialogue: 0,{t_ass(t)},{t_ass(t + d + 0.05)},Sub,,0,0,0,,{x}")
            t += d
    # títulos grandes
    ev.append(f"Dialogue: 1,{t_ass(0.2)},{t_ass(4.0)},Titulo,,0,0,0,,¿QUÉ HARÍAS SI MAÑANA\\NDESPERTARAS CON\\NUN MILLÓN DE DÓLARES\\NEN TU CUENTA?")
    ev.append(f"Dialogue: 1,{t_ass(55.4)},{t_ass(60.3)},Titulo,,0,0,0,,UN MILLÓN DE DÓLARES\\NPUEDE CAMBIAR TU VIDA.\\NPERO TODO DEPENDE\\NDE LO QUE HAGAS CON ÉL.")
    ev.append(f"Dialogue: 1,{t_ass(60.4)},{t_ass(66.6)},Gran,,0,0,0,,¿VOS QUÉ\\NHARÍAS?")
    for yy, nom in ((10, "EL PRUDENTE"), (330, "EL IMPULSIVO"), (650, "EL GENEROSO")):
        ev.append(f"Dialogue: 2,{t_ass(55.4)},{t_ass(66.6)},Panel,,0,0,0,,{{\\pos(20,{yy})}}{nom}")
    ev.append(f"Dialogue: 0,{t_ass(27.0)},{t_ass(44.0)},Aviso,,0,0,0,,Valores ficticios: escenario hipotético,\\Nno precios de mercado.")
    ev.append(f"Dialogue: 0,{t_ass(9.6)},{t_ass(13.0)},Gran,,0,0,0,,EL PRUDENTE")
    ev.append(f"Dialogue: 0,{t_ass(18.4)},{t_ass(22.5)},Gran,,0,0,0,,EL IMPULSIVO")
    ev.append(f"Dialogue: 0,{t_ass(48.1)},{t_ass(52.0)},Gran,,0,0,0,,EL GENEROSO")
    open(salida, "w", encoding="utf-8").write(cab + "\n".join(ev) + "\n")
    print("escrito", salida, len(ev), "eventos")


if __name__ == "__main__":
    main(sys.argv[1])
