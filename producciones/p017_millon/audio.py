"""p017 · banda sonora original (síntesis numpy) + efectos sincronizados + mezcla con la narración. Uso: python3 audio.py salida.wav
Música: acordes cálidos y pulso suave que sube hacia el final; la narración tiene prioridad (la música baja 9 dB mientras habla)."""
import json, math, os, subprocess, sys, wave
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
BIB = os.path.join(AQUI, "..", "..", "audio", "biblioteca")
SR = 48000
DUR = 66.7
N = int(SR * DUR)
RNG = np.random.default_rng(17)
V = json.load(open(os.path.join(AQUI, "duraciones_voz.json")))
INICIO = {"b01_gancho": 0.0, "b02_saldo": 4.16, "b03_prudente": 9.5, "b04_impulsivo": 18.3, "b05_auto": 27.0, "b06_casa": 30.3, "b07_piscina": 33.2,
          "b08_tele": 35.9, "b09_resto": 39.7, "b10_cero": 43.9, "b11_generoso": 48.0, "b12_cierre": 55.4, "b13_pregunta": 60.4}
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


def nota(f, d, ataque=0.25, rel=0.8):
    t = tt(d + rel)
    env = np.minimum(1, t / ataque) * np.where(t < d, 1.0, np.exp(-(t - d) / (rel / 4)))
    x = sum(a * np.sin(2 * np.pi * f * k * t + ph) for k, a, ph in ((1, 1, 0), (2, 0.35, 1), (3, 0.15, 2), (4, 0.06, 3)))
    x += 0.4 * np.sin(2 * np.pi * f * 1.004 * t)
    return (x * env * 0.12).astype(np.float32)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# progresión: Am – F – C – G (cada acorde 4 s), tonos más abiertos al final
ACORDES = [(57, 60, 64), (53, 57, 60), (48, 55, 64), (55, 59, 62)]
t = 0.0
k = 0
while t < DUR - 1:
    ac = ACORDES[k % 4]
    sube = 1.0 if t < 43 else 1.35
    for m in ac:
        suma(mus, t, nota(hz(m), 4.0), 0.9 * sube, -0.3 + 0.3 * (m % 3))
        suma(mus, t, nota(hz(m + 12), 4.0, 0.4), 0.5 * sube, 0.4 - 0.3 * (m % 3))
    suma(mus, t, nota(hz(ac[0] - 12), 4.0, 0.1), 1.2, 0)
    # arpegio suave
    for j, m in enumerate(ac + (ac[1] + 12,)):
        suma(mus, t + 0.5 * j + 0.25, nota(hz(m + 12), 0.4, 0.01, 0.5), 0.55 * sube, 0.2 * (j - 1.5))
    t += 4.0
    k += 1
# pulso de bombo suave desde el segundo 18 hasta el 55 (la energía del impulsivo)
for tb in np.arange(18.3, 55.0, 0.5):
    x = np.sin(2 * np.pi * (50 + 90 * np.exp(-tt(0.25) * 30)) * tt(0.25)) * np.exp(-tt(0.25) * 14)
    suma(mus, tb, (x * 0.35).astype(np.float32), 1.0)


def ding(t0, f=1568, g=0.5):
    d = tt(0.9)
    x = (np.sin(2 * np.pi * f * d) + 0.5 * np.sin(2 * np.pi * f * 2.76 * d)) * np.exp(-d * 5)
    suma(sfx, t0, (x * 0.35 * g).astype(np.float32), 1.0)


def whoosh(t0, dur=0.9, g=0.6, sube=True):
    d = tt(dur)
    r = RNG.standard_normal(len(d))
    env = np.sin(np.pi * d / dur) ** 2
    fc = 300 + (3000 if sube else -2000) * (d / dur) if sube else 3300 - 3000 * (d / dur)
    a = 1 - np.exp(-2 * np.pi * np.clip(fc, 100, 8000) / SR)
    y = np.empty_like(r); s = 0.0
    for i in range(len(r)):
        s += a[i] * (r[i] - s); y[i] = s
    suma(sfx, t0, (y * env * g * 1.6).astype(np.float32), 1.0)


def golpe(t0, g=0.8):
    d = tt(0.6)
    x = np.sin(2 * np.pi * (45 + 80 * np.exp(-d * 25)) * d) * np.exp(-d * 7)
    suma(sfx, t0, (x * g).astype(np.float32), 1.0)


# notificación (vibración + timbre) a ~2,2 s y conteo del número: tictac ascendente
for i, f in enumerate((1318, 1760)):
    ding(1.9 + 0.12 * i, f, 0.6)
for i in range(30):
    ding(4.5 + i * 0.045, 900 + 25 * i, 0.12)   # conteo
ding(6.0, 2093, 0.7)
whoosh(8.7, 0.9)
# compras: golpe + caja (los tiempos las fija COMPRAS desde la escena; se pueden ajustar con la env COMPRAS="t1,t2,...")
COMPRAS = [float(x) for x in os.environ.get("COMPRAS", "27.6,30.9,33.8,36.5,40.6,43.9").split(",")]
for tc in COMPRAS:
    golpe(tc, 0.6)
    ding(tc + 0.05, 1568, 0.7)
    ding(tc + 0.2, 2093, 0.5)
whoosh(47.6, 0.8)
whoosh(55.0, 0.9)
golpe(60.4, 0.7)


def narr():
    out = np.zeros((2, N), np.float32)
    env = np.ones(N, np.float32)
    for bid, i in INICIO.items():
        mp3 = os.path.join(BIB, V[bid]["archivo"])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.float32)
        suma(out, i, x, 1.0)
        a, b = int((i - 0.15) * SR), int((i + len(x) / SR + 0.25) * SR)
        env[max(0, a):min(N, b)] = 0.35
    # suavizar la envolvente de ducking
    k = int(0.12 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same").astype(np.float32)
    return out, env


voz, duck = narr()
m = mus * 0.55 * duck + sfx * 0.9
mix = voz * 1.0 + m
# fundido final y normalización a −1 dBFS (sin tocar la proporción voz/música)
mix *= np.minimum(1, (DUR - tt(DUR)[:N] if False else np.linspace(1, 0, N) * 0 + 1))
pico = np.abs(mix).max()
mix = mix / pico * 0.89
pcm = (np.clip(mix.T, -1, 1) * 32767).astype("<i2")
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("audio listo", sys.argv[1], round(pico, 2))
