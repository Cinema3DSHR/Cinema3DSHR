"""Prueba comparativa de resolución — ANÁLISIS (se corre DESPUÉS de medir, nunca durante).

Entradas : salida/pruebas/resolucion_001/pasada_{A,B}/<resolución>/{m1..m5.png, medidas.json}
Salidas  : pruebas/resolucion_001/{imagenes/, comparaciones/, medidas/, resultados.json}
Qué calcula
  1. Tiempos, CPU, memoria y FPS reales de render (media de las dos pasadas y cada pasada).
  2. Fidelidad objetiva contra la referencia 1280×720 (SSIM y PSNR con ffmpeg), de dos maneras:
       "vista a 720p": la imagen de baja resolución ampliada a 1280×720 (lo que verías en una pantalla de 720p);
       "propia resolución": la referencia reducida a esa resolución contra la render nativa (aísla ruido/denoiser).
  3. Validación de la referencia: el render de 720p de hoy contra los mismos fotogramas del video YA PUBLICADO.
  4. Tamaño estimado de un video de 10 minutos: se recodifica el video de producción (28 s, 720p) a cada resolución
     con los mismos parámetros de producción (H.264, preset slow, CRF 22) y se extrapola la tasa de bits.
  5. Imágenes JPEG de revisión, comparaciones de 4 resoluciones y recortes al 100 %.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SAL = RAIZ / "salida/pruebas/resolucion_001"
RES = ["1280x720", "1024x576", "960x540", "854x480"]
REF = "1280x720"
VIDEO_PROD = Path(next((a for a in sys.argv[1:] if not a.startswith("--")), "/tmp/claude-0/pub/mansion.mp4"))
MOM = json.loads((AQUI / "momentos.json").read_text())["momentos"]
# zona de recorte al 100 % por momento (fracciones x0, y0, ancho, alto de la imagen): se ajustan mirando las imágenes
ROI = {"m1_plano_general": (0.30, 0.22, 0.30, 0.30), "m2_fachada_exterior": (0.40, 0.45, 0.30, 0.30),
       "m3_entrada_garaje": (0.45, 0.30, 0.30, 0.30), "m4_piscina_reflejos": (0.55, 0.55, 0.30, 0.30),
       "m5_jardin_vegetacion": (0.55, 0.50, 0.30, 0.30)}
if (AQUI / "roi.json").exists():
    ROI.update({k: tuple(v) for k, v in json.loads((AQUI / "roi.json").read_text()).items()})


def sh(*args, captura=True):
    r = subprocess.run([str(a) for a in args], capture_output=captura, text=True)
    return r


def ff(*args):
    return sh("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args)


def metrica(a: Path, b: Path, escalar_a_b: bool) -> dict:
    """SSIM y PSNR de a contra b (a se amplía/reduce a b si hace falta)."""
    fa = "[0:v]scale=iw:ih:flags=lanczos[x]" if not escalar_a_b else "[0:v][1:v]scale2ref=flags=lanczos[x][y]"
    # con scale2ref a se lleva al tamaño de b
    if escalar_a_b:
        grafo_ssim = "[0:v][1:v]scale2ref=flags=lanczos[x][y];[x][y]ssim"
        grafo_psnr = "[0:v][1:v]scale2ref=flags=lanczos[x][y];[x][y]psnr"
    else:
        grafo_ssim, grafo_psnr = "[0:v][1:v]ssim", "[0:v][1:v]psnr"
    out = {}
    r = sh("ffmpeg", "-hide_banner", "-i", a, "-i", b, "-lavfi", grafo_ssim, "-f", "null", "-")
    m = re.search(r"All:([0-9.]+)", r.stderr)
    out["ssim"] = float(m.group(1)) if m else None
    r = sh("ffmpeg", "-hide_banner", "-i", a, "-i", b, "-lavfi", grafo_psnr, "-f", "null", "-")
    m = re.search(r"average:([0-9.inf]+)", r.stderr)
    out["psnr_db"] = float(m.group(1)) if m and m.group(1) not in ("inf",) else None
    return out


def cargar_medidas():
    datos = {}
    for pas in ("A", "B"):
        for r in RES:
            p = SAL / f"pasada_{pas}" / r / "medidas.json"
            datos.setdefault(r, {})[pas] = json.loads(p.read_text())
    return datos


def resumen_tiempos(datos):
    out = {}
    for r in RES:
        A, B = datos[r]["A"], datos[r]["B"]
        mom = {}
        for m in MOM:
            ta = next(x for x in A["momentos"] if x["id"] == m["id"])
            tb = next(x for x in B["momentos"] if x["id"] == m["id"])
            mom[m["id"]] = {"A_s": ta["segundos"], "B_s": tb["segundos"], "media_s": round((ta["segundos"] + tb["segundos"]) / 2, 2),
                            "rss_pico_mb": max(ta["rss_pico_mb"], tb["rss_pico_mb"])}
        tot_a, tot_b = A["total_5_s"], B["total_5_s"]
        media = (tot_a + tot_b) / 2
        todos = A["momentos"] + B["momentos"]
        out[r] = {
            "pixeles": A["pixeles"], "momentos": mom,
            "total_5_A_s": tot_a, "total_5_B_s": tot_b, "total_5_media_s": round(media, 2),
            "media_por_fotograma_s": round(media / 5, 2),
            "fps_reales_render": round(5 / media, 4),
            "horas_cpu_10min_video": round(media / 5 * 18000 / 3600, 1),
            "uso_cpu_proceso_pct": round(sum(x["uso_cpu_proceso_pct"] for x in todos) / len(todos), 1),
            "uso_cpu_sistema_pct": round(sum(x["uso_cpu_sistema_pct"] for x in todos) / len(todos), 1),
            "cpu_s_por_fotograma": round(sum(x["cpu_s"] for x in todos) / len(todos), 1),
            "memoria_pico_mb": max(A["rss_pico_mb"], B["rss_pico_mb"]),
            "memoria_pico_A_mb": A["rss_pico_mb"], "memoria_pico_B_mb": B["rss_pico_mb"],
            "construccion_escena_s": round((A["construccion_escena_s"] + B["construccion_escena_s"]) / 2, 1),
            "calentamiento_s": round((A["calentamiento"]["segundos"] + B["calentamiento"]["segundos"]) / 2, 1),
        }
    ref = out[REF]["media_por_fotograma_s"]
    for r in RES:
        out[r]["tiempo_relativo_a_720p"] = round(out[r]["media_por_fotograma_s"] / ref, 3)
        out[r]["pixeles_relativos_a_720p"] = round(out[r]["pixeles"] / out[REF]["pixeles"], 3)
        out[r]["s_por_megapixel"] = round(out[r]["media_por_fotograma_s"] / (out[r]["pixeles"] / 1e6), 1)
    return out


def jpegs_y_comparaciones():
    """JPEG de revisión (misma calidad para todas), comparación 2×2 por momento y recortes al 100 %."""
    for r in RES:
        (AQUI / "imagenes" / r).mkdir(parents=True, exist_ok=True)
        for m in MOM:
            ff("-i", SAL / "pasada_A" / r / f"{m['id']}.png", "-q:v", "2", AQUI / "imagenes" / r / f"{m['id']}.jpg")
    (AQUI / "comparaciones").mkdir(exist_ok=True)
    for m in MOM:
        # rejilla 2×2 a tamaño de pantalla común (1280×720 por celda → 2560×1440), con el nombre de cada resolución
        ins, flt = [], []
        for i, r in enumerate(RES):
            ins += ["-i", SAL / "pasada_A" / r / f"{m['id']}.png"]
            flt.append(f"[{i}:v]scale=1280:720:flags=lanczos,drawtext=text='{r}':x=16:y=12:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8[v{i}]")
        ff(*ins, "-filter_complex", ";".join(flt) + ";[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[o]",
           "-map", "[o]", "-q:v", "3", AQUI / "comparaciones" / f"{m['id']}_2x2.jpg")
        # recorte al 100 % de la zona de interés, ampliado al mismo tamaño para verlas juntas
        x0, y0, w, h = ROI[m["id"]]
        ins, flt = [], []
        for i, r in enumerate(RES):
            ins += ["-i", SAL / "pasada_A" / r / f"{m['id']}.png"]
            flt.append(f"[{i}:v]crop=iw*{w}:ih*{h}:iw*{x0}:ih*{y0},scale=640:360:flags=neighbor,drawtext=text='{r}':x=8:y=6:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=6[c{i}]")
        ff(*ins, "-filter_complex", ";".join(flt) + ";[c0][c1][c2][c3]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[o]",
           "-map", "[o]", "-q:v", "3", AQUI / "comparaciones" / f"{m['id']}_detalle_pixeles_2x2.jpg")


def fidelidad():
    out = {}
    for r in RES:
        filas = {}
        for m in MOM:
            n = SAL / "pasada_A" / r / f"{m['id']}.png"
            ref = SAL / "pasada_A" / REF / f"{m['id']}.png"
            # vista a 720p: la render nativa ampliada al tamaño de la referencia
            v720 = metrica(n, ref, escalar_a_b=True) if r != REF else {"ssim": 1.0, "psnr_db": None}
            # propia resolución: la referencia reducida a esa resolución contra la render nativa
            if r != REF:
                red = AQUI.parent.parent / "salida/pruebas/resolucion_001/_tmp_ref_reducida.png"
                red.parent.mkdir(parents=True, exist_ok=True)
                ancho, alto = (int(v) for v in r.split("x"))
                ff("-i", ref, "-vf", f"scale={ancho}:{alto}:flags=lanczos", red)
                propia = metrica(n, red, escalar_a_b=False)
            else:
                propia = {"ssim": 1.0, "psnr_db": None}
            filas[m["id"]] = {"vista_720p": v720, "propia_resolucion": propia}
        def media(clave, sub):
            vals = [f[clave][sub] for f in filas.values() if f[clave][sub] is not None]
            return round(sum(vals) / len(vals), 4) if vals else None
        out[r] = {"momentos": filas, "ssim_vista_720p": media("vista_720p", "ssim"), "psnr_vista_720p_db": media("vista_720p", "psnr_db"),
                  "ssim_propia": media("propia_resolucion", "ssim"), "psnr_propia_db": media("propia_resolucion", "psnr_db")}
    return out


def validar_contra_video_publicado():
    """Referencia (hoy) contra los mismos fotogramas del MP4 publicado: prueba que la prueba reproduce la producción."""
    out = {}
    for m in MOM:
        t = (m["frame"] - 1) / 30.0
        tmp = SAL / f"_pub_{m['id']}.png"
        ff("-ss", f"{t:.4f}", "-i", VIDEO_PROD, "-frames:v", "1", tmp)
        out[m["id"]] = metrica(SAL / "pasada_A" / REF / f"{m['id']}.png", tmp, escalar_a_b=False)
    return out


def tamano_video_10min():
    """Recodifica el video de producción a cada resolución con los parámetros de producción y extrapola a 10 min."""
    info = json.loads(sh("ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,bit_rate", "-of", "json", VIDEO_PROD).stdout)
    dur = float(info["format"]["duration"])
    out = {"duracion_muestra_s": round(dur, 2), "audio_aac_192k_mb_10min": round(192_000 * 600 / 8 / 1e6, 1), "por_resolucion": {}}
    tmp = SAL / "_tamano"
    tmp.mkdir(parents=True, exist_ok=True)
    for r in RES:
        ancho, alto = (int(v) for v in r.split("x"))
        filas = {}
        for crf in (19, 22, 26):
            dest = tmp / f"{r}_crf{crf}.mp4"
            ff("-i", VIDEO_PROD, "-an", "-vf", f"scale={ancho}:{alto}:flags=lanczos", "-c:v", "libx264", "-preset", "slow",
               "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", dest)
            b = dest.stat().st_size
            filas[f"crf{crf}"] = {"bytes_muestra": b, "kbps": round(b * 8 / dur / 1000), "mb_10min_solo_video": round(b / dur * 600 / 1e6, 1)}
        out["por_resolucion"][r] = filas
    return out


def md5_pixeles(ruta: Path) -> str:
    """MD5 de los PÍXELES decodificados (los PNG de Blender llevan fecha y tiempo de render en los metadatos y por eso
    sus bytes nunca coinciden aunque la imagen sea idéntica)."""
    r = sh("ffmpeg", "-v", "error", "-i", ruta, "-f", "md5", "-")
    return r.stdout.strip()


def piso_de_ruido():
    """Pasada A contra pasada B en la MISMA resolución: mide la repetibilidad del método. Resultado medido: las dos
    pasadas son idénticas píxel a píxel (misma semilla), así que toda diferencia entre resoluciones es de la resolución."""
    out = {}
    for r in RES:
        ident = {m["id"]: md5_pixeles(SAL / "pasada_A" / r / f"{m['id']}.png") == md5_pixeles(SAL / "pasada_B" / r / f"{m['id']}.png")
                 for m in MOM}
        out[r] = {"momentos_identicos_por_pixel": sum(ident.values()), "de": len(ident), "detalle": ident}
    return out


def calibrar_tamano(res):
    """La recodificación parte de un video YA comprimido (sale ~20 % más liviana que el original). Se calibra con el
    tamaño real del archivo publicado: factor = (video del MP4 real) / (recodificación 720p, CRF 22)."""
    real = VIDEO_PROD.stat().st_size
    audio = 192_000 / 8 * res["tamano_video"]["duracion_muestra_s"]
    video_real = real - audio
    base = res["tamano_video"]["por_resolucion"][REF]["crf22"]["bytes_muestra"]
    f = video_real / base
    dur = res["tamano_video"]["duracion_muestra_s"]
    cal = {"archivo_real_bytes": real, "video_real_estimado_bytes": round(video_real), "factor_calibracion": round(f, 3),
           "mb_10min_video_mas_audio": {}}
    for r in RES:
        b = res["tamano_video"]["por_resolucion"][r]["crf22"]["bytes_muestra"] * f
        cal["mb_10min_video_mas_audio"][r] = round(b / dur * 600 / 1e6 + 192_000 / 8 * 600 / 1e6, 0)
    return cal


def detalle_fino():
    """Energía de detalle fino (varianza del laplaciano) de cada imagen vista a 1280×720 (todas ampliadas con lanczos al
    mismo tamaño, como se verían en una misma pantalla), relativa a la referencia 720p. 100 % = tanto detalle fino como
    el 720p; menos = más suave. Se calcula en el cuadro completo y en la zona de interés de cada momento."""
    import numpy as np

    def gris(ruta):
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-vf", "scale=1280:720:flags=lanczos,format=gray", "-f", "rawvideo", "-"],
                           capture_output=True, check=True)
        return np.frombuffer(r.stdout, dtype=np.uint8).reshape(720, 1280).astype(np.float64)

    def lap_var(g):
        c = g[1:-1, 1:-1]
        l = 4 * c - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
        return float(l.var())

    out = {r: {"cuadro": {}, "zona": {}} for r in RES}
    for m in MOM:
        x0, y0, w, h = ROI[m["id"]]
        base = {}
        for r in RES:
            g = gris(SAL / "pasada_A" / r / f"{m['id']}.png")
            zona = g[int(720 * y0):int(720 * (y0 + h)), int(1280 * x0):int(1280 * (x0 + w))]
            out[r]["cuadro"][m["id"]] = lap_var(g)
            out[r]["zona"][m["id"]] = lap_var(zona)
    res = {}
    for r in RES:
        res[r] = {k: {m: round(100 * out[r][k][m] / out[REF][k][m], 1) for m in out[r][k]} for k in ("cuadro", "zona")}
        res[r]["cuadro_media_pct"] = round(sum(res[r]["cuadro"].values()) / 5, 1)
        res[r]["zona_media_pct"] = round(sum(res[r]["zona"].values()) / 5, 1)
    return res


if __name__ == "__main__" and "--solo-detalle" in sys.argv:
    res = json.loads((AQUI / "resultados.json").read_text())
    res["detalle_fino_pct_vs_720p"] = detalle_fino()
    (AQUI / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("DETALLE LISTO")
    sys.exit(0)

if __name__ == "__main__" and "--solo-piso" in sys.argv:
    res = json.loads((AQUI / "resultados.json").read_text())
    res["piso_de_ruido"] = piso_de_ruido()
    res["tamano_video"]["calibrado_con_archivo_real"] = calibrar_tamano(res)
    (AQUI / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("PISO LISTO")
    sys.exit(0)

if __name__ == "__main__":
    datos = cargar_medidas()
    (AQUI / "medidas").mkdir(exist_ok=True)
    for r in RES:
        for pas in ("A", "B"):
            (AQUI / "medidas" / f"{r}_pasada_{pas}.json").write_text(json.dumps(datos[r][pas], ensure_ascii=False, indent=1))
    res = {"tiempos": resumen_tiempos(datos)}
    print("tiempos listos", flush=True)
    jpegs_y_comparaciones()
    print("imágenes listas", flush=True)
    res["fidelidad"] = fidelidad()
    print("fidelidad lista", flush=True)
    res["validacion_contra_video_publicado"] = validar_contra_video_publicado()
    res["tamano_video"] = tamano_video_10min()
    res["maquina"] = datos[REF]["A"]["maquina"]
    res["configuracion_render"] = datos[REF]["A"]["configuracion"]
    res["huella_receta"] = datos[REF]["A"]["huella_receta"]
    res["piso_de_ruido"] = piso_de_ruido()
    res["tamano_video"]["calibrado_con_archivo_real"] = calibrar_tamano(res)
    (AQUI / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("LISTO")
