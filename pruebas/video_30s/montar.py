"""Verifica la secuencia, la codifica a MP4 (H.264 + audio) y arma el informe de rendimiento. Sin bpy.
Uso: python montar.py FRAMES_DIR AUDIO.wav SALIDA_DIR --total 900 [--run-iniciado ISO] [--trabajos N]"""
import argparse, collections, datetime as dt, hashlib, json, re, statistics, subprocess
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("frames"); ap.add_argument("audio"); ap.add_argument("salida")
ap.add_argument("--total", type=int, required=True); ap.add_argument("--run-iniciado", default=""); ap.add_argument("--crf", type=int, default=22); ap.add_argument("--nombre", default="futbol_30s_cycles6")
ap.add_argument("--produccion", default=""); ap.add_argument("--escena-id", default="e01"); ap.add_argument("--version", type=int, default=1); ap.add_argument("--huella", default="")
ap.add_argument("--escena", default="", help="escena.json: aplica el fundido a negro de la última toma, como el montaje del estudio")
a = ap.parse_args(); F = Path(a.frames); S = Path(a.salida); S.mkdir(parents=True, exist_ok=True)
def sh(*c): return subprocess.run([str(x) for x in c], capture_output=True, text=True)
# 1) integridad: ni faltantes ni sobrantes ni números repetidos
nums = sorted(int(re.search(r"f_(\d+)\.png", p.name).group(1)) for p in F.glob("f_*.png"))
faltan = sorted(set(range(1, a.total + 1)) - set(nums)); sobran = sorted(set(nums) - set(range(1, a.total + 1)))
assert not faltan and not sobran and len(nums) == a.total, f"faltan {faltan[:10]} sobran {sobran[:10]} cantidad {len(nums)}"
# 2) duplicados de CONTENIDO (md5 de bytes): se informan (una escena puede tener cuadros iguales, pero no deberían ser muchos)
md5 = {n: hashlib.md5((F / f"f_{n:04d}.png").read_bytes()).hexdigest() for n in nums}
dup = collections.defaultdict(list)
for n, h in md5.items(): dup[h].append(n)
iguales = [v for v in dup.values() if len(v) > 1]
# 3) continuidad: SSIM entre fotogramas consecutivos; los límites entre trabajos NO deben salirse de lo normal
informes = [json.loads(p.read_text()) for p in sorted(F.glob("informe_*.json"))]
assert informes, "no hay informes de los trabajos de render"
limites = sorted({i["hasta"] for i in informes if i["hasta"] < a.total})
def ssim(n):
    r = sh("ffmpeg", "-hide_banner", "-i", F / f"f_{n:04d}.png", "-i", F / f"f_{n + 1:04d}.png", "-lavfi", "ssim", "-f", "null", "-")
    m = re.search(r"All:([0-9.]+)", r.stderr); return float(m.group(1)) if m else None
s_lim = {n: ssim(n) for n in limites}
dentro = [ssim(n) for n in range(2, a.total, 17) if n not in limites and n + 1 <= a.total]
if not [x for x in dentro if x is not None]:     # ensayos chicos: no hay puntos internos → se comparan todos los pares que no son límite
    dentro = [ssim(n) for n in range(1, a.total) if n not in limites]
dentro = [x for x in dentro if x is not None]
med, mn = (statistics.median(dentro), min(dentro)) if dentro else (None, None)   # None = no había ningún par que comparar
# 4) MP4: 30 fps constantes, 1280x720, audio original normalizado como en producción
mp4 = S / f"{a.nombre}.mp4"
cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "30", "-start_number", "1", "-i", str(F / "f_%04d.png")]
if Path(a.audio).exists(): cmd += ["-i", a.audio, "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest"]
if a.escena:                                     # «corte a negro» de la última toma (efecto de montaje fundido_negro)
    _m = json.loads(Path(a.escena).read_text()); _ult = max(_m["tomas"], key=lambda t: t["inicio_s"]); _ef = _ult.get("montaje") or {}
    if _ef.get("efecto") == "fundido_negro":
        cmd += ["-vf", f"fade=t=out:st={_ult['inicio_s'] + float(_ef.get('desde_s', 0)):.3f}:d={float(_ef.get('duracion_s', 1.2)):.3f}"]
cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr", "-movflags", "+faststart", str(mp4)]
subprocess.run(cmd, check=True)
pr = json.loads(sh("ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,avg_frame_rate,nb_read_frames,codec_name,pix_fmt:format=duration,size", "-of", "json", mp4).stdout)
v = pr["streams"][0]; fmt = pr["format"]
aud = sh("ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name,sample_rate,channels", "-of", "csv=p=0", mp4).stdout.strip()
# 5) informe de rendimiento
tt = sorted((f for i in informes for f in i["fotogramas"]), key=lambda x: x["fotograma"]); segs = [f["segundos"] for f in tt]
ahora = dt.datetime.now(dt.timezone.utc)
reloj = (ahora - dt.datetime.fromisoformat(a.run_iniciado.replace("Z", "+00:00"))).total_seconds() if a.run_iniciado else None
por_toma = collections.defaultdict(list)
for f in tt: por_toma[f["toma"]].append(f["segundos"])
inf = {"integridad": {"fotogramas": len(nums), "esperados": a.total, "faltantes": faltan, "sobrantes": sobran, "grupos_de_fotogramas_con_contenido_identico": iguales[:20], "n_grupos_identicos": len(iguales)},
       "continuidad": {"ssim_en_limites_entre_trabajos": {f"{n}->{n + 1}": (round(x, 4) if x is not None else None) for n, x in s_lim.items()}, "pares_comparados_dentro": len(dentro), "ssim_mediana_dentro": round(med, 4) if med is not None else None, "ssim_minimo_dentro": round(mn, 4) if mn is not None else None},
       "video": {"archivo": mp4.name, "bytes": int(fmt["size"]), "mb": round(int(fmt["size"]) / 1e6, 2), "duracion_s": float(fmt["duration"]), "ancho": v["width"], "alto": v["height"],
                 "fps_declarados": v["r_frame_rate"], "fps_promedio": v["avg_frame_rate"], "fotogramas_leidos": v["nb_read_frames"], "codec": v["codec_name"], "pix_fmt": v["pix_fmt"], "audio": aud},
       "rendimiento": {"trabajos_de_render": len(informes), "fotogramas": len(tt), "render_acumulado_s": round(sum(segs), 1), "cpu_proceso_acumulada_s": round(sum(i["cpu_proceso_s"] for i in informes), 1),
                       "construccion_escena_acumulada_s": round(sum(i["construccion_escena_s"] for i in informes), 1), "tiempo_total_de_procesos_s": round(sum(i["segundos_total_proceso"] for i in informes), 1),
                       "s_por_fotograma_media": round(statistics.mean(segs), 2), "s_por_fotograma_mediana": round(statistics.median(segs), 2), "s_por_fotograma_min": min(segs), "s_por_fotograma_max": max(segs),
                       "trabajo_mas_largo_s": max(i["segundos_total_proceso"] for i in informes), "trabajo_mas_corto_s": min(i["segundos_total_proceso"] for i in informes),
                       "ram_pico_mb": max(i["ram_pico_mb"] for i in informes), "reloj_hasta_mp4_s": round(reloj, 1) if reloj else None,
                       "s_por_fotograma_por_toma": {k: round(statistics.mean(x), 2) for k, x in por_toma.items()},
                       "cpus": dict(collections.Counter(i["cpu_modelo"] for i in informes)), "nucleos_por_maquina": sorted({i["nucleos"] for i in informes})},
       "config_cycles": informes[0]["config_cycles"], "huellas_de_receta": sorted({i["huella_receta"] for i in informes}),
       "trabajos": [{k: i[k] for k in ("desde", "hasta", "fotogramas_renderizados", "inicio_utc", "fin_utc", "segundos_total_proceso", "construccion_escena_s", "render_s", "cpu_proceso_s", "ram_pico_mb", "cpu_modelo")} for i in informes],
       "fotogramas_tiempos": tt}
(S / "informe_rendimiento.json").write_text(json.dumps(inf, indent=1, ensure_ascii=False))
print(json.dumps({k: inf[k] for k in ("integridad", "continuidad", "video")}, indent=1, ensure_ascii=False)); print(json.dumps(inf["rendimiento"], indent=1, ensure_ascii=False))

# 6) entregables para la app y para comparar con futuras pruebas (sólo si se indicó la producción)
if a.produccion:
    import shutil, datetime
    pid, eid, ver = a.produccion, a.escena_id, a.version
    cfg = inf["config_cycles"]
    res = f'{v["width"]}x{v["height"]}'
    (S / "audio.aac").unlink(missing_ok=True)
    if Path(a.audio).exists():
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.audio, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-f", "adts", str(S / "audio.aac")], check=True)
    shutil.copy(mp4, S / f"{eid}_v{ver}_revision.mp4")                        # el nombre que la app busca en el catálogo
    # la app reproduce OGV (Theora + Vorbis), como los videos de revisión del estudio
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp4), "-vf", "scale='min(1280,iw)':-2", "-c:v", "libtheora",
                    "-q:v", "7", "-c:a", "libvorbis", "-q:a", "4", str(S / f"{eid}_v{ver}_revision.ogv")], check=True)
    n_portada = max(1, min(a.total, int(round(a.total * 0.38))))                 # un cuadro del enfrentamiento
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(F / f"f_{n_portada:04d}.png"), "-q:v", "2", str(S / f"{eid}_v{ver}_portada.jpg")], check=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(F / f"f_{n_portada:04d}.png"), "-vf", "scale=320:-2", "-q:v", "4", str(S / f"{eid}_v{ver}_miniatura.jpg")], check=True)
    fecha = ahora.strftime("%Y-%m-%dT%H:%M:%SZ")
    info = {"produccion": pid, "escena": eid, "version": ver, "huella": a.huella or ",".join(inf["huellas_de_receta"]), "calidad": "revision", "resolucion": res,
            "fps": 30, "duracion_s": round(float(fmt["duration"]), 3), "fecha": fecha, "segundos_render": inf["rendimiento"]["render_acumulado_s"]}
    (S / f"{eid}_v{ver}_info.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))
    informe = {"produccion": a.nombre and pid, "nombre": "mansion_cqb_30s_720p_30fps", "fecha": fecha,
               "configuracion_acordada": {"motor": cfg["motor"], "dispositivo": cfg["dispositivo"], "resolucion": res, "fps": 30, "duracion_s": 30, "fotogramas": a.total,
                                          "muestras": cfg["muestras"], "muestreo_adaptativo": cfg["muestreo_adaptativo"], "umbral_adaptativo": cfg["umbral_adaptativo"],
                                          "denoiser": cfg["denoiser"], "rebotes_max": cfg["rebotes_max"], "arbol_de_luces": cfg["arbol_de_luces"], "semilla": cfg["semilla"],
                                          "semilla_animada": cfg["semilla_animada"]},
               "entregables": {"video": "video.mp4", "audio": "audio.aac", "informe": "informe.json", "catalogo": f"{eid}_v{ver}_revision.mp4"}, **inf}
    (S / "informe.json").write_text(json.dumps(informe, indent=1, ensure_ascii=False))
    print("ENTREGA", sorted(p.name for p in S.iterdir()))
