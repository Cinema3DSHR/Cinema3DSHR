"""p018 · banda sonora original (síntesis numpy): pad espacial, subgrave de descenso, barrido de presión, estallido del metano, campanillas de cristal,
zap y estruendo del láser; mezcla con la narración (la música baja 9 dB mientras se habla). Uso: python3 audio.py salida.wav"""
import json, math, os, subprocess, sys, wave
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
BIB = os.path.join(AQUI, "..", "..", "audio", "biblioteca")
SR = 48000
DUR = 66.0
N = int(SR * DUR)
RNG = np.random.default_rng(18)
V = json.load(open(os.path.join(AQUI, "duraciones_voz.json")))
INI = {"b01_gancho": 0.0, "b02_gigantes": 3.3, "b03_presion": 11.55, "b04_metano": 21.55, "b05_cristales": 30.6, "b06_lluvia": 35.8, "b07_laboratorio": 44.2, "b08_cautela": 55.0, "b09_pregunta": 62.5}
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
ACORDES = [(50, 57, 62, 65), (46, 53, 58, 62), (53, 57, 60, 65), (48, 55, 60, 64)]
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
for i, tb in enumerate(np.arange(30.6, 65.0, 0.5)):
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


whoosh(3.0, 0.9)
whoosh(11.2, 1.0)
# descenso (11,55–21,55): subgrave que sube + barrido de presión (seno que sube de 60 a 900 Hz)
d = tt(10.0)
barrido = np.sin(2 * np.pi * np.cumsum(60 + 840 * (d / 10.0) ** 2) / SR) * np.minimum(1, d / 1.0) * 0.06
suma(sfx, 11.55, barrido.astype(np.float32), 1.0)
sub = np.sin(2 * np.pi * (35 + 25 * d / 10.0) * d) * 0.18 * np.minimum(1, d / 2.0)
suma(sfx, 11.55, sub.astype(np.float32), 1.0)
# el metano se rompe (≈ 21,55 + 38 % de 9 s ≈ 25,0 s): estallido y siseo
golpe(25.0, 0.9, 40)
for i in range(18):
    campana(25.05 + 0.05 * i, 900 + 140 * i, 0.12, math.sin(i) * 0.8)
whoosh(26.3, 1.4, 0.35, False)
# cristal (30,6 s…): acorde de campanas al formarse el diamante (≈ 33,2 s)
for j, m in enumerate((74, 78, 81, 86)):
    campana(33.2 + 0.07 * j, hz(m), 0.5, -0.5 + 0.33 * j)
# lluvia (35,8–44,2 s): campanillas aleatorias
for tb in np.sort(RNG.uniform(36.0, 44.0, 40)):
    campana(tb, hz(int(RNG.choice([81, 86, 88, 93]))), 0.2, float(RNG.uniform(-0.8, 0.8)))
# laboratorio (44,2–55 s): disparo del láser a los 44,2 + 3,33 s ≈ 47,5 s
d = tt(0.35)
zap = np.sin(2 * np.pi * np.cumsum(2600 * np.exp(-d * 9) + 300) / SR) * np.exp(-d * 8) * 0.35
suma(sfx, 47.5, zap.astype(np.float32), 1.0)
golpe(47.55, 1.0, 55)
whoosh(47.6, 1.1, 0.3, False)
for tb in np.sort(RNG.uniform(48.8, 52.5, 14)):
    campana(tb, hz(int(RNG.choice([88, 93, 96]))), 0.22, float(RNG.uniform(-0.8, 0.8)))
whoosh(54.6, 0.9)
golpe(62.5, 0.6, 44)
for j, m in enumerate((74, 81, 86, 93)):
    campana(63.0 + 0.2 * j, hz(m), 0.35, -0.4 + 0.27 * j)


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
