"""Animática de revisión de «Dúo Cero» (NO es el render final): cada escena construida con el director, render
rápido en Cycles (4 muestras + limpieza) a 640×360, uno de cada 2 cuadros (cada cuadro se repite: 15 imágenes por
segundo en un video de 30), montada con su mezcla de audio (voces, música, tren, disparos) y las 6 unidas en un solo
video de 3 minutos. Sin GPU, Workbench se dibuja por software y tardaba ~80 s por cuadro; Cycles así, ~3,5 s.

    /opt/tools/blendenv/bin/python producciones/p009_duo_cero/herramientas/animatica.py <escena> <carpeta>
    /opt/tools/blendenv/bin/python producciones/p009_duo_cero/herramientas/animatica.py unir <carpeta>
"""
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))


CADA = 2


def _rellenar(carpeta: Path, total: int):
    """Los cuadros que no se renderizaron repiten el anterior (la secuencia f_0001… tiene que quedar completa)."""
    import shutil
    previo = None
    for i in range(1, total + 1):
        f = carpeta / f"f_{i:04d}.jpg"
        if f.exists():
            previo = f
        elif previo is not None:
            shutil.copyfile(previo, f)


def escena(n: int, carpeta: Path):
    import bpy
    from estudio import manifiesto as MF, montaje
    from estudio.audio import procedural
    from estudio.blender import director as D
    m = MF.leer(RAIZ / f"producciones/p009_duo_cero/escenas/e{n:02d}/v1/escena.json")
    t0 = time.time()
    res = D.construir(m, "humo")
    s = res["escena"]
    s.render.engine = "CYCLES"
    s.cycles.samples = 4
    s.cycles.use_adaptive_sampling = False
    s.cycles.use_denoising = True
    s.render.resolution_x, s.render.resolution_y = 640, 360
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "JPEG"
    s.render.image_settings.quality = 88
    print(f"[animática] e{n:02d} construida en {time.time() - t0:.0f} s", flush=True)
    out = carpeta / f"e{n:02d}"
    out.mkdir(parents=True, exist_ok=True)
    D.render_tomas(res, out, cada=CADA)
    mp4s = []
    for t in res["tomas"]:
        tid = t["spec"]["id"]
        _rellenar(out / tid, t["frame_fin"] - t["frame_inicio"] + 1)
        mp4s.append(montaje.montar_toma(out / tid, out / f"{tid}.mp4", 30, t["spec"].get("montaje"), crf=20))
    pistas = D.exportar_pistas(res, out / "pistas.json")
    wav = procedural.generar(m, pistas, out / "audio.wav")
    r = montaje.unir_escena(mp4s, wav, out, f"e{n:02d}_animatica", crf=24)
    print(f"[animática] e{n:02d} lista en {time.time() - t0:.0f} s: {r}", flush=True)


def unir(carpeta: Path):
    from estudio import montaje
    partes = [carpeta / f"e{n:02d}" / f"e{n:02d}_animatica.mp4" for n in range(1, 7)]
    faltan = [str(p) for p in partes if not p.exists()]
    if faltan:
        sys.exit("faltan: " + ", ".join(faltan))
    lista = carpeta / "lista.txt"
    lista.write_text("".join(f"file '{p.resolve()}'\n" for p in partes))
    salida = carpeta / "duo_cero_ep01_animatica.mp4"
    montaje._ff("-f", "concat", "-safe", 0, "-i", lista, "-c:v", "libx264", "-preset", "medium", "-crf", 24,
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", salida)
    print("listo:", salida, round(montaje.duracion(salida), 2), "s")


if __name__ == "__main__":
    if sys.argv[1] == "unir":
        unir(Path(sys.argv[2]))
    else:
        escena(int(sys.argv[1]), Path(sys.argv[2]))
