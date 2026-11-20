"""p016 · audio original del McLaren F1 SHOCKWAVE (síntesis con numpy; sin muestras ni grabaciones ajenas).
Un V12 de 6,1 L (6 explosiones por vuelta, caja de 6 marchas) con efecto Doppler real calculado desde las posiciones de la cámara activa y el coche,
atenuación por distancia, ruido de rodadura y de aire, la onda de choque, y los vidrios que se rompen en el instante exacto en que estalla cada vidriera.
En cámara lenta el motor baja de tono (estilizado) y los vidrios se estiran. Uso: python audio.py audio_datos.json salida.wav"""
import json
import math
import sys
import wave
import numpy as np

SR = 48000
DUR = 60.0
N = int(SR * DUR)
C = 343.0
rng = np.random.default_rng(1618)

D = json.load(open(sys.argv[1]))
FPS = D["fps"]
NF = D["total"]
Tsim = np.array(D["T"])
ycar = np.array(D["coche_y"])
oy = np.array(D["oyente"])
XC = D["x_carril"]
tf = np.arange(NF) / FPS


def v_coche(t):
    t = np.asarray(t)
    return np.where(t <= 10, 12 + 2.6 * t, np.where(t <= 17.667, 38 + 3.52 * (t - 10), np.where(t <= 22.6, 65.0, 65.0 + (t - 22.6) * (10 / 2.2))))


vsim = v_coche(Tsim)
rate = np.gradient(Tsim) * FPS                          # segundos de simulación por segundo real
pcar = np.stack([np.full(NF, XC), ycar, np.full(NF, 0.5)], axis=1)
dist = np.linalg.norm(oy - pcar, axis=1)
vr = np.gradient(dist) * FPS                            # velocidad radial real (+ se aleja)
vr = np.convolve(vr, np.ones(3) / 3, mode="same")
dop = C / (C + np.clip(vr, -250, 250))

# RPM con caja de 6 marchas (rpm = v · k); se cambia a 7000 rpm
K = [560, 360, 260, 200, 150, 112]
rpm = np.zeros(NF)
marcha = np.zeros(NF, dtype=int)
g = 0
for i in range(NF):
    while g < 5 and vsim[i] * K[g] > 7000:
        g += 1
    rpm[i] = max(900, vsim[i] * K[g])
    marcha[i] = g
# en los cambios de marcha el régimen cae unos 80 ms: lo suavizamos a nivel de cuadro
rpm = np.convolve(rpm, np.ones(2) / 2, mode="same")
pitch_slow = np.clip(0.40 + 0.60 * rate, 0.40, 1.0)     # estilización de la cámara lenta
carga = np.clip(0.55 + 0.45 * (np.gradient(vsim) > 0.001), 0.55, 1.0)


def porcuadro_a_muestras(a):
    return np.interp(np.arange(N) / SR, tf, a)


Dop = porcuadro_a_muestras(dop)
Pit = porcuadro_a_muestras(pitch_slow)
Rpm = porcuadro_a_muestras(rpm)
Dist = porcuadro_a_muestras(dist)
Car = porcuadro_a_muestras(carga)
Vs = porcuadro_a_muestras(vsim)
Rate = porcuadro_a_muestras(rate)

# amplitud por distancia (ley 1/r suavizada) y filtro de aire (más grave cuando está lejos)
Amp = np.maximum(1.0 / (1.0 + (Dist / 8.0) ** 0.7), 0.045)      # ley de distancia «de película»: el coche lejano se oye, aunque suave


def panoramica():
    """−1 izquierda … +1 derecha: dirección del coche respecto de adonde mira la cámara (hacia el coche)."""
    # la cámara siempre mira al coche: el paneo lo da el movimiento lateral relativo (componente x del vector, con signo)
    rel = (pcar - oy)
    # eje derecho de la cámara = (fwd_y, −fwd_x); como mira al coche, el coche está al centro; usamos la velocidad angular para repartir el sonido
    ang = np.arctan2(rel[:, 0], -rel[:, 1] + 1e-6)
    ang = np.unwrap(ang)
    return np.clip(np.gradient(ang) * FPS * 0.35, -0.8, 0.8)


Pan = porcuadro_a_muestras(panoramica())


def lp(x, fc):
    fcs = np.broadcast_to(np.asarray(fc, dtype=np.float64), x.shape) if np.ndim(fc) else np.full(x.shape, fc, dtype=np.float64)
    a = 1.0 - np.exp(-2 * np.pi * fcs / SR)
    y = np.empty(len(x), dtype=np.float64)
    s = 0.0
    xs = x.astype(np.float64)
    for i in range(len(xs)):
        s += a[i] * (xs[i] - s)
        y[i] = s
    return y.astype(np.float32)


def reverb(x, rt=2.4, mezcla=0.22):
    ir_n = int(rt * SR)
    t = np.arange(ir_n) / SR
    ir = rng.standard_normal(ir_n) * np.exp(-t / (rt / 5.0))
    ir[:int(0.015 * SR)] *= np.linspace(0, 1, int(0.015 * SR))
    n = len(x) + ir_n
    nfft = 1 << (n - 1).bit_length()
    r = np.fft.irfft(np.fft.rfft(x.astype(np.float64), nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return (r * mezcla * 0.02).astype(np.float32)


# ───────────────────────────────────────────── motor V12
ff = Rpm / 60.0 * 6.0 * Pit * Dop                       # frecuencia de encendido observada
ph = np.cumsum(ff) / SR
motor = np.zeros(N, dtype=np.float32)
for h in range(1, 15):
    a = h ** -0.85 * (1.0 + 0.35 * np.sin(2 * np.pi * (0.7 * h) * np.arange(N) / SR / 3.0))
    motor += (np.sin(2 * np.pi * h * ph + h * 0.7) * a).astype(np.float32)
# sub-orden (irregularidad entre bancadas) y brillo mecánico a alta
motor += (0.7 * np.sin(2 * np.pi * 0.5 * ph)).astype(np.float32)
motor += (0.22 * np.sin(2 * np.pi * 7.0 * ph) * (Rpm / 7500.0) ** 2).astype(np.float32)
# escape: ruido modulado por cada explosión
ruido = rng.standard_normal(N).astype(np.float32)
mod = 0.5 + 0.5 * np.cos(2 * np.pi * ph)
motor += (lp(ruido, 2200) * mod * 1.2 * Car).astype(np.float32)
motor *= Amp * (0.35 + 0.65 * Car) * 0.55
# aire/distancia: filtro más oscuro con la distancia
fc_aire = np.clip(9000.0 / (1.0 + Dist / 60.0), 900, 9000)
motor = lp(motor, fc_aire)

# ───────────────────────────────────────────── rodadura, aire y onda
rod = lp(rng.standard_normal(N).astype(np.float32), 1400) - lp(rng.standard_normal(N).astype(np.float32), 180)
rod *= (Vs / 65.0) ** 1.4 * Amp * 0.35 * np.clip(Rate * 2.5, 0.25, 1.0)
viento = lp(rng.standard_normal(N).astype(np.float32), 900) * ((Vs / 65.0) ** 2) * (1.0 / (1.0 + (Dist / 4.0) ** 2)) * 3.2 * np.clip(Rate, 0.0, 1.0)
base_ciudad = (lp(rng.standard_normal(N).astype(np.float32), 160) * 0.02 + np.sin(2 * np.pi * 55 * np.arange(N) / SR) * 0.006).astype(np.float32)

eventos = np.zeros(N, dtype=np.float32)
eventos_wet = np.zeros(N, dtype=np.float32)


def poner(buf, t0, x, g=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 < 0 or i0 >= N:
        return
    n = min(len(x), N - i0)
    buf[i0:i0 + n] += (x[:n] * g).astype(np.float32)


# onda expansiva: el golpe llega a la cámara en el cuadro 534
t_onda = 534 / FPS
d1 = 1.6
tt = np.arange(int(d1 * SR)) / SR
boom = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-tt / 0.28) + 22) / SR) * np.exp(-tt / 0.45) * 1.5
boom += lp(rng.standard_normal(len(tt)).astype(np.float32), np.clip(9000 * np.exp(-tt / 0.12), 200, 9000)) * np.exp(-tt / 0.18) * 1.2
poner(eventos, t_onda, boom, 1.0)
poner(eventos_wet, t_onda, boom, 0.9)
# pasada: ráfaga de aire cuando el coche cruza (cuadros 515–545)
tw = np.arange(int(0.9 * SR)) / SR
whoosh = lp(rng.standard_normal(len(tw)).astype(np.float32), 3500) * np.sin(np.pi * tw / 0.9) ** 2 * 2.2
poner(eventos, 516 / FPS, whoosh, 0.9)

# vidrios: cada vidriera estalla en su cuadro, con la distancia/paneo de la cámara activa en ese momento
tiempo_amp = np.arange(int(3.6 * SR)) / SR


def vidrio(rate_local):
    p = float(np.clip(0.55 + 0.45 * rate_local, 0.5, 1.0))
    s = np.zeros(len(tiempo_amp), dtype=np.float32)
    n0 = lp(rng.standard_normal(int(0.4 * SR)).astype(np.float32), 8000)
    n0 = n0 - lp(n0, 2500)
    s[:len(n0)] += n0 * np.exp(-np.arange(len(n0)) / SR / (0.07 / p)) * 1.4
    thud = np.sin(2 * np.pi * 170 * p * tiempo_amp[:int(0.4 * SR)]) * np.exp(-tiempo_amp[:int(0.4 * SR)] / (0.12 / p))
    s[:len(thud)] += thud * 0.7
    for _ in range(22):
        f0 = rng.uniform(2200, 9500) * p
        dd = rng.uniform(0.35, 1.5) / p
        inicio = int(rng.uniform(0.0, 0.7 / p) * SR)
        m = min(int(dd * SR * 2), len(s) - inicio)
        if m <= 0:
            continue
        tt_ = np.arange(m) / SR
        s[inicio:inicio + m] += (np.sin(2 * np.pi * f0 * tt_) * np.exp(-tt_ / (dd * 0.4)) * rng.uniform(0.05, 0.22)).astype(np.float32)
    return s


for fb, x, y in D["roturas"]:
    fb = int(min(NF - 1, max(0, fb)))
    if fb >= NF - 2:
        continue
    pos_o = oy[fb]
    dd = math.hypot(x - pos_o[0], y - pos_o[1])
    if dd > 160:
        continue
    g = 1.1 / (1.0 + dd / 9.0)
    s = vidrio(float(rate[fb]))
    poner(eventos, fb / FPS, s, g)
    poner(eventos_wet, fb / FPS, s, g * 0.8)

# crujidos finos: hojas, piedras y polvo mientras todo cae
for _ in range(900):
    tt0 = rng.uniform(560 / FPS, 1560 / FPS)
    k = rng.uniform(0.02, 0.09)
    hp_ = rng.standard_normal(int(0.05 * SR)).astype(np.float32)
    c = hp_ * np.exp(-np.arange(len(hp_)) / SR / 0.01)
    poner(eventos, tt0, c, k * (1.0 / (1.0 + dist[int(tt0 * FPS) % NF] / 12.0)))

# ───────────────────────────────────────────── mezcla
seco = motor + rod + viento + base_ciudad + eventos
hum = reverb(motor * 0.5 + eventos_wet, rt=2.6, mezcla=0.25)
mono = seco + hum
# paneo suave por la posición lateral relativa
izq = mono * (1.0 - np.clip(Pan, 0, 1) * 0.55)
der = mono * (1.0 + np.clip(Pan, 0, 1) * 0.0 - np.clip(-Pan, 0, 1) * 0.55)
st = np.stack([izq, der])
# fundidos de entrada/salida y limitación suave
st[:, :int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
st[:, -int(1.5 * SR):] *= np.linspace(1, 0, int(1.5 * SR))
pico = float(np.max(np.abs(st)))
st = np.tanh(st / pico * 1.7) / np.tanh(1.7) * 0.92
pcm = (st.T * 32767).astype(np.int16)
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("audio listo", sys.argv[2], "pico previo", round(pico, 3), "dist min", round(float(dist.min()), 2))
