"""p019 · banda sonora original (síntesis numpy): pad luminoso, campanillas del prisma y de la dispersión, golpe de la onda azul, cascada de barras,
calidez del atardecer y silencio del espacio; mezcla con la narración (la música baja 9 dB mientras se habla). Uso: python3 audio.py salida.wav"""
import json, math, os, subprocess, sys, wave
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
BIB = os.path.join(AQUI, "..", "..", "audio", "biblioteca")
SR = 48000
DUR = 60.0
N = int(SR * DUR)
RNG = np.random.default_rng(19)
V = json.load(open(os.path.join(AQUI, "duraciones_voz.json")))
INI = {"b01_gancho": 0.0, "b02_luz": 3.0, "b03_atmosfera": 8.4, "b04_ondas": 17.03, "b05_cielo": 24.9, "b06_violeta": 29.95, "b07_atardecer": 39.3, "b08_espacio": 46.9, "b09_cierre": 51.8}
mus = np.zeros((2, N), np.float32)
sfx = np.zeros((2, N), np.float32)


def tt(d):
    return np.arange(int(d * SR)) / SR


def suma(buf, t0, x, g=1.0, pan=0.0):
    i0 = int(t0 * SR)
    n = min(len(x), N - i0)
    if n <= 0:
        return
    buf[0, i0:i0 + n] += x[:n] * g * math.cos((pan + 1) * math.pi / 4)
    buf[1, i0:i0 + n] += x[:n] * g * math.sin((pan + 1) * math.pi / 4)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pad(f, d, ataque=1.5, rel=2.0):
    t = tt(d + rel)
    env = np.minimum(1, t / ataque) * np.where(t < d, 1.0, np.exp(-(t - d) / (rel / 4)))
    x = sum(a * np.sin(2 * np.pi * f * k * t + ph) for k, a, ph in ((1, 1, 0), (2, 0.4, 1), (3, 0.2, 2), (5, 0.07, 4)))
    x += 0.5 * np.sin(2 * np.pi * f * 1.005 * t) + 0.5 * np.sin(2 * np.pi * f * 0.995 * t)
    return (x * env * 0.07).astype(np.float32)


# pad en Dm – Bb – F – C (cada acorde 8 s): tono misterioso que se abre al final
ACORDES = [(48, 55, 60, 64), (43, 50, 55, 59), (45, 52, 57, 60), (41, 48, 53, 57)]
t = 0.0
k = 0
while t < DUR - 1:
    ac = ACORDES[k % 4]
    amp = 0.8 + 0.4 * min(1.0, t / 40.0)
    for j, m in enumerate(ac):
        suma(mus, t, pad(hz(m), 8.0), amp, -0.4 + 0.27 * j)
        suma(mus, t, pad(hz(m + 12), 8.0, 2.0), amp * 0.5, 0.4 - 0.27 * j)
    suma(mus, t, pad(hz(ac[0] - 12), 8.0, 1.0), amp * 1.4, 0)
    t += 8.0
    k += 1
# arpegio de campanillas desde la formación del cristal (30,6 s) hasta el final
for i, tb in enumerate(np.arange(24.9, 58.0, 0.5)):
    m = ACORDES[int(tb // 8) % 4][i % 4] + 24
    d = tt(1.2)
    x = (np.sin(2 * np.pi * hz(m) * d) + 0.35 * np.sin(2 * np.pi * hz(m) * 2.76 * d)) * np.exp(-d * 4.5)
    suma(mus, tb, (x * 0.05).astype(np.float32), 1.0, math.sin(i) * 0.6)


def whoosh(t0, dur=1.0, g=0.5, sube=True):
    d = tt(dur)
    r = RNG.standard_normal(len(d))
    env = np.sin(np.pi * d / dur) ** 2
    fc = (300 + 3500 * (d / dur)) if sube else (3800 - 3300 * (d / dur))
    a = 1 - np.exp(-2 * np.pi * np.clip(fc, 100, 9000) / SR)
    y = np.empty_like(r); s_ = 0.0
    for i in range(len(r)):
        s_ += a[i] * (r[i] - s_); y[i] = s_
    suma(sfx, t0, (y * env * g * 1.6).astype(np.float32), 1.0)


def golpe(t0, g=0.8, f0=48):
    d = tt(0.9)
    x = np.sin(2 * np.pi * (f0 + 90 * np.exp(-d * 25)) * d) * np.exp(-d * 6)
    suma(sfx, t0, (x * g).astype(np.float32), 1.0)


def campana(t0, f, g=0.4, pan=0.0):
    d = tt(1.6)
    x = (np.sin(2 * np.pi * f * d) + 0.4 * np.sin(2 * np.pi * f * 2.76 * d) + 0.2 * np.sin(2 * np.pi * f * 5.4 * d)) * np.exp(-d * 3.2)
    suma(sfx, t0, (x * g * 0.3).astype(np.float32), 1.0, pan)


whoosh(2.7, 0.8)
# prisma (3,0–8,4 s): rayo blanco y siete campanas ascendentes al abrirse el arcoíris (≈ 4,2 s)
for j in range(7):
    campana(4.2 + 0.13 * j, hz(72 + 2 * j), 0.4, -0.7 + 0.23 * j)
whoosh(8.1, 0.8)
# moléculas (8,4–17 s): chispitas azules al azar
for tb in np.sort(RNG.uniform(10.0, 16.5, 30)):
    campana(tb, hz(int(RNG.choice([84, 88, 91, 96]))), 0.18, float(RNG.uniform(-0.8, 0.8)))
whoosh(16.7, 0.8)
# ondas (17–24,9 s): la onda azul choca a ≈ 19,4 s → golpe y abanico de destellos
golpe(19.35, 0.7, 60)
for i in range(16):
    campana(19.4 + 0.045 * i, 1000 + 160 * i, 0.12, math.sin(i) * 0.8)
whoosh(24.5, 0.7)
# cielo azul (24,9–30 s): acorde amplio
for j, m in enumerate((72, 76, 79, 84)):
    campana(25.2 + 0.09 * j, hz(m), 0.4, -0.5 + 0.33 * j)
# violeta (30–39,3 s): una marca por barra al crecer (≈ cada 1,6 s)
for k, tb in enumerate(np.arange(31.2, 38.0, 0.8)):
    campana(tb, hz(79 + (k % 4) * 2), 0.22, -0.6 + 0.2 * (k % 7))
whoosh(39.0, 0.8)
# atardecer (39,3–46,9 s): barrido cálido y grave que baja
d = tt(7.0)
cal = np.sin(2 * np.pi * np.cumsum(220 - 120 * (d / 7.0)) / SR) * np.minimum(1, d / 1.5) * np.exp(-((d - 3.5) / 3.5) ** 2) * 0.06
suma(sfx, 39.3, cal.astype(np.float32), 1.0)
whoosh(46.4, 0.9, 0.4, False)
# espacio (46,9–51,8 s): zumbido grave casi silencioso
d = tt(5.0)
suma(sfx, 46.9, (np.sin(2 * np.pi * 42 * d) * 0.1 * np.minimum(1, d / 1.0)).astype(np.float32), 1.0)
# cierre (51,8 s): acorde luminoso
golpe(51.8, 0.4, 55)
for j, m in enumerate((72, 79, 84, 88)):
    campana(52.1 + 0.18 * j, hz(m), 0.4, -0.4 + 0.27 * j)


def narr():
    out = np.zeros((2, N), np.float32)
    env = np.ones(N, np.float32)
    for bid, i in INI.items():
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(BIB, V[bid]["archivo"]), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.float32)
        suma(out, i, x, 1.0)
        a, b = int((i - 0.15) * SR), int((i + len(x) / SR + 0.25) * SR)
        env[max(0, a):min(N, b)] = 0.35
    k = int(0.12 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same").astype(np.float32)
    return out, env


voz, duck = narr()
mix = voz + mus * 0.6 * duck + sfx * 0.9 * (0.5 + 0.5 * duck)
fade = np.ones(N, np.float32)
nf = int(1.5 * SR)
fade[-nf:] = np.linspace(1, 0, nf)
mix *= fade
mix = mix / np.abs(mix).max() * 0.89
pcm = (np.clip(mix.T, -1, 1) * 32767).astype("<i2")
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("audio listo", sys.argv[1])
