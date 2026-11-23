"""Sonido de la escena del viaje bajo la lluvia (cap. 1, interior del auto): lluvia en el techo, ruta mojada, motor, limpiaparabrisas, truenos,
música original (piano + cuerdas graves) y la voz de Gabriel (líneas 1–5 del accidente). Todo procedural: no gasta créditos.
Uso: python audio_viaje.py SALIDA.wav [DURACION_S]"""
import json, sys, wave
from pathlib import Path
import numpy as np
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from estudio.audio import procedural as P  # noqa: E402
SR = P.SR
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 36.0
n = int(DUR * SR)
rng = np.random.default_rng(1101)
t = np.arange(n) / SR
mez = np.zeros((n, 2))
PERIODO_LIMPIA = 1.4                                  # s por barrido de ida y vuelta (la animación de Godot usa el mismo)


def lp(x, fc):                                        # pasabajos por FFT
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))


def estereo(x, ancho=0.6):                            # decorrelaciona dos canales de ruido
    return np.stack([x, np.roll(x, int(0.0007 * SR)) * 0.9], axis=1)


# 1) LLUVIA en el techo y los vidrios: ruido de banda media-alta + gotas gordas
llu = lp(P._ruido_banda(n, rng, 1500, 9000), 7000) * 0.35 + lp(P._ruido_banda(n, rng, 300, 1500), 900) * 0.25
gotas = np.zeros(n)
for i in rng.integers(0, n - 800, int(DUR * 55)):
    k = np.arange(800); gotas[i:i + 800] += np.exp(-k / 90) * np.sin(2 * np.pi * rng.uniform(900, 2600) * k / SR) * rng.uniform(0.2, 0.9)
llu_amp = 0.75 + 0.25 * np.sin(2 * np.pi * t / 17.0)  # la lluvia respira
mez += estereo(llu * llu_amp * 0.55 + gotas * 0.22)

# 2) RUTA MOJADA: siseo de neumáticos sobre agua, grave y constante
ruta = lp(P._ruido_banda(n, rng, 120, 1800), 700)
mez += estereo(ruta * (0.30 + 0.05 * np.sin(2 * np.pi * t / 5.3)))

# 3) MOTOR amortiguado de cabina: fundamental ~48 Hz con armónicos y leve oscilación
rpm = 48 + 3 * np.sin(2 * np.pi * t / 9.0) + 1.2 * np.sin(2 * np.pi * t / 2.3)
fase = 2 * np.pi * np.cumsum(rpm) / SR
mot = np.sin(fase) * 0.5 + np.sin(2 * fase) * 0.28 + np.sin(3 * fase) * 0.12 + np.sin(5 * fase) * 0.05
mot *= 0.8 + 0.2 * np.sin(2 * np.pi * 24 * t)       # pulso de cilindros
mez += estereo(lp(mot, 260) * 0.33)

# 4) LIMPIAPARABRISAS: roce de goma + golpecito en cada extremo, a intervalos regulares
def limpia():
    m = int(0.62 * SR); k = np.arange(m) / SR
    roce = lp(P._ruido_banda(m, rng, 400, 3500), 2600) * np.sin(np.pi * k / 0.62) ** 1.5 * 0.55
    ch = np.sin(2 * np.pi * (1500 + 600 * np.sin(2 * np.pi * 7 * k)) * k) * 0.04 * np.sin(np.pi * k / 0.62) ** 4   # chirrido leve de la goma
    def tope(x, a): x[a:a + 1500] += np.sin(2 * np.pi * 95 * np.arange(1500) / SR) * np.exp(-np.arange(1500) / 220) * 0.9
    s = roce + ch; tope(s, 0); tope(s, m - 1500 - 10); return s
w = limpia()
tt = 0.8
while tt < DUR - 1:
    P._poner(mez, w, tt, 0.55, -0.15); P._poner(mez, w[::-1] * 0.9, tt + PERIODO_LIMPIA / 2, 0.5, -0.15); tt += PERIODO_LIMPIA

# 5) TRUENOS lejanos (graves, con cola larga)
for t0, g in ((13.2, 0.55), (29.5, 0.8)):
    m = int(5.5 * SR); k = np.arange(m) / SR
    tr = lp(P._ruido_banda(m, rng, 25, 220), 180) * np.exp(-k / 1.7) * (1 + 0.6 * np.sin(2 * np.pi * 3.1 * k)) * g
    P._poner(mez, tr, t0, 1.0, 0.0)

# 6) MÚSICA original: cuerdas graves (pad) + piano melancólico lento (La menor), crece hasta el final
def cuerda(f, dur, g):
    m = int(dur * SR); k = np.arange(m) / SR
    s = sum(np.sin(2 * np.pi * f * h * k + rng.uniform(0, 6.28)) / h ** 1.3 for h in range(1, 7))
    s *= np.minimum(k / 2.5, 1) * np.minimum((dur - k) / 3.0, 1) * g
    return s * (1 + 0.04 * np.sin(2 * np.pi * 5.2 * k))
def piano(f, g):
    m = int(4.0 * SR); k = np.arange(m) / SR
    s = (np.sin(2 * np.pi * f * k) + 0.5 * np.sin(4 * np.pi * f * k) * np.exp(-k / 0.8) + 0.25 * np.sin(6 * np.pi * f * k) * np.exp(-k / 0.4) + 0.1 * np.sin(8 * np.pi * f * k) * np.exp(-k / 0.2))
    return s * np.exp(-k / 1.4) * np.minimum(k / 0.006, 1) * g
mus = np.zeros((n, 2))
acordes = [(110.0, 220.0, 261.63), (87.31, 174.61, 220.0), (130.81, 261.63, 329.63), (98.0, 196.0, 246.94)]   # Am, F, C, G (inversiones graves)
for i, (b, m1, m2) in enumerate(acordes * 4):
    t0 = i * 8.0
    if t0 >= DUR: break
    for f, g in ((b, 0.22), (m1, 0.12), (m2, 0.08)):
        P._poner(mus, cuerda(f, 9.5, g), t0, 1.0, 0.0)
melodia = [440, 523.25, 493.88, 392, 440, 349.23, 392, 329.63]
for i, f in enumerate(melodia * 3):
    t0 = 4.0 + i * 1.6
    if t0 < DUR - 2: P._poner(mus, piano(f, 0.20 + 0.15 * min(t0 / DUR, 1)), t0, 1.0, 0.2)
mus_amp = np.minimum(t / 5, 1) * (0.55 + 0.45 * (t / DUR)) * np.minimum((DUR - t) / 2.5, 1)
mez += mus * mus_amp[:, None] * 0.75

# 7) VOZ de Gabriel (líneas 1–5 del accidente): se mezcla aparte, se normaliza a −3 dBFS de pico y el resto (lluvia, ruta, motor, música) BAJA mientras habla
vo = json.load(open(Path(__file__).parents[1] / "audio_cap1" / "voces.json"))
voz = np.zeros((n, 2))
ta = 3.0
for l in [x for x in vo if x["bloque"] == "accidente"][:5]:
    x = P._decodificar(RAIZ / l["mp3"])
    P._poner(voz, x, ta, 1.0, 0.0)
    ta += l["dur_s"] + 0.9
voz *= 0.85 / (np.abs(voz).max() + 1e-9)
env = np.convolve(np.abs(voz[:, 0]), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
env = np.minimum(env / 0.06, 1.0)
env = np.convolve(env, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")        # ataque/relajo suaves del ducking
mez *= 0.55
mez *= (1.0 - 0.85 * env)[:, None]                                                   # el fondo baja ~7 dB con la voz
habla = env > 0.5
fondo = np.sqrt((mez[habla] ** 2).mean()); lavoz = np.sqrt((voz[habla] ** 2).mean())
print("voz sobre el fondo mientras habla: +%.1f dB" % (20 * np.log10(lavoz / fondo)))
mez += voz
pico = np.abs(mez).max()
mez *= min(1.0, 0.92 / pico) if pico > 0.92 else 1.0
print("PICO", round(float(np.abs(mez).max()), 3), "fin de la voz", round(ta, 1), "s")
pcm = (np.clip(mez, -1, 1) * 32767).astype("<i2")
with wave.open(sys.argv[1], "wb") as w_:
    w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes(pcm.tobytes())
