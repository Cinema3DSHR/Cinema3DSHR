"""Sonido completo del capítulo 3 de «A la deriva»: las 33 voces + EL MISMO ambiente, música y efectos de los capítulos 1 y 2
(ambiente procedural «nave_interior» a 0,35; música y efectos que ya están en la biblioteca de audio, sin generar ni gastar nada nuevo)
+ pasos, una alerta suave en la escena 2 y los pitidos del holograma. Mezcla a 48 kHz estéreo y se le pone al MP4 renderizado.
Uso: python audio_cap3.py VIDEO_MUDO.mp4 SALIDA.mp4   (necesita /tmp/e3/sN_plan.json: `montaje.gd -- sN prefijo plan`)"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
PROD = RAIZ / "producciones" / "p011_a_la_deriva"
sys.path.insert(0, str(RAIZ))
from estudio.audio import elevenlabs as EL, nave as NV, procedural as P  # noqa: E402

SR = P.SR
FPS = 30.0
INICIO_CUADRO = {"s1": 0, "s2": 1231, "s3": 2161, "s4": 3515, "s5": 4638}       # cuadro (0 = primero) donde empieza cada escena
OFF = {k: v / FPS for k, v in INICIO_CUADRO.items()}
TOTAL_S = 5324 / FPS
n = int(TOTAL_S * SR)
sb = json.load(open(PROD / "godot_e03" / "data" / "storyboard_e03.json"))["escenas"]
mezcla = np.zeros((n, 2))
rng = np.random.default_rng(sum(map(ord, "p020_a_la_deriva_cap3")) + 1)


def dec(ev: dict) -> np.ndarray:
    x = P._decodificar(EL.ruta_en_biblioteca(ev))
    return x / (np.abs(x).max() + 1e-9) * 0.5          # como en los capítulos 1 y 2: los efectos y la música se llevan a −6 dB de pico


def poner(x: np.ndarray, t0: float, vol: float, fade_in=0.0, fade_out=0.0, pan=0.0):
    x = x.copy() * vol
    if fade_in > 0:
        k = min(len(x), int(fade_in * SR)); x[:k] *= np.linspace(0, 1, k)
    if fade_out > 0:
        k = min(len(x), int(fade_out * SR)); x[-k:] *= np.linspace(1, 0, k)
    P._poner(mezcla, x, t0, 1.0, pan)


def cargar_ev(escena: str, i_tipo: str, inicio_s: float) -> dict:
    s = json.load(open(PROD / "escenas" / escena / "escena.json"))["sonido"]["eventos"]
    return next(e for e in s if e["tipo"] == i_tipo and abs(e["inicio_s"] - inicio_s) < 0.01)


# 1) AMBIENTE de la nave (el mismo de los capítulos 1 y 2) en todo el capítulo
mezcla += NV.ambiente_interior(n, rng) * 0.35

# 2) MÚSICA de los capítulos anteriores
musA = dec(cargar_ev("e01/v2", "musica", 0.0))                      # partitura sutil de espacio (cap. 1)
musB = dec(cargar_ev("e02/v3", "musica", 25.55))                    # partitura frágil del jardín (cap. 2)
motivo = dec(cargar_ev("e02/v3", "musica", 113.78))                 # motivo de piano tierno (cap. 2)
poner(musA[: int(23 * SR)], 0.0, 0.22, fade_in=2.0, fade_out=5.0)                                  # mañana de Kate
poner(motivo, 23.0, 0.24, fade_in=1.5, fade_out=3.0)                                               # la rosa
poner(musB, OFF["s4"], 0.20, fade_in=2.0, fade_out=4.0)                                            # el momento entre los dos (y el cierre)

# 3) EFECTOS de la biblioteca de los capítulos anteriores
inver = dec(cargar_ev("e02/v3", "efecto", 27.55))                   # invernadero hidropónico (20 s) → en bucle con cruces
chime = dec(cargar_ev("e01/v2", "efecto", 72.23))                   # chime suave de interfaz
ping = dec(cargar_ev("e02/v3", "efecto", 124.18))                   # ping de mensaje
t = OFF["s3"]
cruce = 2.0
while t < TOTAL_S - 0.5:
    poner(inver, t, 0.30, fade_in=cruce, fade_out=cruce)
    t += len(inver) / SR - cruce
poner(ping, 0.8, 0.25)                                              # el mensaje «Gracias por la flor» en la tablet de Kate
# el holograma de EVA aparece: el mismo chime de interfaz
for esc in ("s1", "s3", "s5"):
    vis = sb[esc]["actores"]["eva"]["visible"][0][0]
    poner(chime, OFF[esc] + max(vis, 0.0) + 0.4, 0.30)
# la pista del registro oculto (escena 5): chime al decir «Mostralo»
v5 = sb["s5"]["voces"][-1]
poner(chime, OFF["s5"] + v5["t"] + v5["dur"] + 0.15, 0.40)

# 4) ALERTA suave de la escena 2 (procedural): dos tonos bajos que laten mientras EVA avisa; se apaga cuando salen
a0, a1 = OFF["s2"] + 1.0, OFF["s2"] + 20.5
m = int((a1 - a0) * SR)
tt = np.arange(m) / SR
ciclo = np.mod(tt, 1.1)
tono = np.where(ciclo < 0.55, 740.0, 554.0)
fase = 2 * np.pi * np.cumsum(tono) / SR
sirena = np.sin(fase) * 0.7 + np.sin(2 * fase) * 0.15
sirena *= (0.55 + 0.45 * np.sin(np.pi * np.mod(ciclo, 0.55) / 0.55) ** 0.5)
sirena = np.convolve(sirena, np.ones(24) / 24, mode="same")                  # redondeo: suave, no de sirena de policía
poner(sirena, a0, 0.10, fade_in=1.0, fade_out=2.5)

# 5) PASOS (procedural) en cada caminata/corrida: dos por ciclo del clip
for esc in ("s1", "s2", "s3", "s4", "s5"):
    plan = json.load(open(f"/tmp/e3/{esc}_plan.json"))
    for actor, segs in plan.items():
        for sg in segs:
            if sg["modo"] != "ruta":
                continue
            paso_s = max(sg["ciclo_s"] / 2.0, 0.25)
            tp = sg["t0"] + paso_s * 0.5
            k = 0
            while tp < sg["t1"]:
                P._poner(mezcla, P.paso(rng), OFF[esc] + tp, rng.uniform(0.16, 0.26), (-0.12 if k % 2 else 0.12))
                tp += paso_s; k += 1

# 6) VOCES (como en los capítulos anteriores: mono centradas al 0,9)
for esc in ("s1", "s2", "s3", "s4", "s5"):
    for v in sb[esc]["voces"]:
        x = P._decodificar(RAIZ / "producciones" / "p011_a_la_deriva" / "godot_e03" / v["mp3"])
        P._poner(mezcla, x, OFF[esc] + v["t"], 0.9, 0.0)

# sin normalizar: sólo se baja el nivel si algo se pasa de 0 dBFS
pico = np.abs(mezcla).max()
if pico > 0.98:
    mezcla *= 0.98 / pico
print("PICO", round(float(np.abs(mezcla).max()), 3), "RMS", round(float(np.sqrt((mezcla ** 2).mean())), 4))
pcm = (np.clip(mezcla, -1, 1) * 32767).astype("<i2")
wav = Path(sys.argv[2]).with_suffix(".wav")
import wave  # noqa: E402
with wave.open(str(wav), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", sys.argv[1], "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-t", f"{TOTAL_S:.4f}", "-movflags", "+faststart", sys.argv[2]], check=True)
print("LISTO", sys.argv[2])
