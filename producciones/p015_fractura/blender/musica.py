"""p015 «FRACTURA» · banda sonora original (síntesis con numpy, sin muestras ni música ajena): ambiente espacial, graves, impactos, explosiones, metales,
distorsiones y silencios sincronizados con los cuadros de guion.py. Estéreo 48 kHz, 180 s. Uso: python musica.py <salida.wav>"""
import math
import sys
import wave
import numpy as np

import guion

SR = 48000
DUR = 180.0
N = int(SR * DUR)
RNG = np.random.default_rng(2026)
F = lambda frame: frame / 30.0          # cuadro → segundo

D = np.zeros((2, N), dtype=np.float32)   # señal seca
W = np.zeros((2, N), dtype=np.float32)   # envío a reverberación


# ───────────────────────────────────────────── utilidades
def sumar(buf, t0, x, g=1.0, pan=0.0):
    """Suma x (mono) en buf desde t0 (s) con ganancia y paneo −1..1."""
    i0 = int(t0 * SR)
    if i0 >= N or len(x) == 0:
        return
    if i0 < 0:
        x = x[-i0:]
        i0 = 0
    n = min(len(x), N - i0)
    gl = g * math.cos((pan + 1) * math.pi / 4)
    gr = g * math.sin((pan + 1) * math.pi / 4)
    buf[0, i0:i0 + n] += (x[:n] * gl).astype(np.float32)
    buf[1, i0:i0 + n] += (x[:n] * gr).astype(np.float32)


def emitir(t0, x, g=1.0, pan=0.0, rev=0.3):
    sumar(D, t0, x, g, pan)
    if rev > 0:
        sumar(W, t0, x, g * rev, pan)


def tt(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return RNG.standard_normal(int(d * SR)).astype(np.float32)


def lp(x, fc):
    """Filtro paso bajo de un polo; fc puede ser escalar o arreglo (barrido)."""
    x = np.asarray(x, dtype=np.float64)
    fcs = np.broadcast_to(np.asarray(fc, dtype=np.float64), x.shape)
    a = 1.0 - np.exp(-2.0 * np.pi * fcs / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s)
        y[i] = s
    return y.astype(np.float32)


def hp(x, fc):
    return x - lp(x, fc)


def bp(x, f0, f1):
    return lp(hp(x, f0), f1)


def sweep(d, f0, f1, curva="exp"):
    t = tt(d)
    u = t / max(d, 1e-9)
    if curva == "exp":
        return f0 * (f1 / f0) ** u
    return f0 + (f1 - f0) * u


def seno(freq, ph=0.0):
    fr = np.asarray(freq, dtype=np.float64)
    return np.sin(2 * np.pi * np.cumsum(fr) / SR + ph).astype(np.float32)


def env(d, a=0.01, r=0.3, curva=3.0):
    n = int(d * SR)
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.clip((d - t) / max(r, 1e-4), 0, 1) ** 1.0
    return e.astype(np.float32)


def caida(d, tau):
    return np.exp(-tt(d) / tau).astype(np.float32)


# ───────────────────────────────────────────── instrumentos
def bombo(t, g=1.0):
    d = 0.5
    f = 42 + 90 * np.exp(-tt(d) / 0.04)
    x = seno(f) * caida(d, 0.16)
    emitir(t, x, g, 0, 0.05)


def sub(t, d=3.0, f0=70, f1=28, g=1.0):
    x = seno(sweep(d, f0, f1)) * caida(d, d * 0.35)
    emitir(t, x, g, 0, 0.05)


def explosion(t, d=5.0, g=1.0):
    n = noise(d)
    fc = sweep(d, 7000, 90)
    x = lp(n, fc) * caida(d, d * 0.28) * 3.0
    x += seno(sweep(d, 62, 24)) * caida(d, d * 0.4) * 1.6
    # crepitar de escombros
    cr = np.zeros(int(d * SR), dtype=np.float32)
    for _ in range(int(60 * d)):
        i = int(abs(RNG.exponential(d * 0.25)) * SR)
        if i < len(cr) - 400:
            cr[i:i + 400] += RNG.standard_normal(400).astype(np.float32) * np.exp(-np.arange(400) / 80.0) * RNG.uniform(0.2, 1.0)
    x += hp(cr, 1500) * 0.6
    emitir(t, x, g * 0.8, 0, 0.35)


def impacto(t, g=1.0, d=2.2):
    x = seno(sweep(d, 95, 30)) * caida(d, 0.5) * 1.4
    c = lp(noise(0.5), 2500) * caida(0.5, 0.08) * 1.2
    x[:len(c)] += c
    emitir(t, x, g, 0, 0.5)


def subida(t0, t1, f0=200, f1=4000, g=0.6, tono=True):
    d = t1 - t0
    n = noise(d)
    fc = sweep(d, f0, f1)
    x = bp(n, f0 * 0.5, f1) * (tt(d) / d) ** 2.2 * 2.0
    if tono:
        x += seno(sweep(d, f0 * 0.5, f1 * 0.5)) * (tt(d) / d) ** 2 * 0.5
    emitir(t0, x, g, 0, 0.5)


def subida_inversa(t0, t1, g=0.6):
    """Cola de explosión invertida (reversa) que termina en t1."""
    d = t1 - t0
    n = noise(d)
    y = lp(n, sweep(d, 7000, 120)) * caida(d, d * 0.3) * 2.0 + seno(sweep(d, 70, 25)) * caida(d, d * 0.4)
    emitir(t0, y[::-1], g, 0, 0.5)


def vidrio(t, g=1.0, d=2.0):
    y = np.zeros(int(d * SR), dtype=np.float32)
    ruido = hp(noise(0.25), 3500) * caida(0.25, 0.04) * 2.0
    y[:len(ruido)] += ruido
    for _ in range(14):
        f = RNG.uniform(2200, 9500)
        dd = RNG.uniform(0.4, 1.6)
        p = seno(np.full(int(dd * SR), f)) * caida(dd, dd * 0.3) * RNG.uniform(0.08, 0.3)
        i = int(RNG.uniform(0, 0.4) * SR)
        n = min(len(p), len(y) - i)
        y[i:i + n] += p[:n]
    emitir(t, y, g * 0.7, RNG.uniform(-0.5, 0.5), 0.6)


def campana(t, f, d=3.0, g=0.3, pan=0.0, rev=0.7):
    m = f * 3.5
    ph = seno(np.full(int(d * SR), f)) + 0 * seno(np.full(int(d * SR), m))
    mod = seno(np.full(int(d * SR), m)) * 2.4 * caida(d, d * 0.2)
    x = np.sin(2 * np.pi * np.cumsum(np.full(int(d * SR), f)) / SR + mod).astype(np.float32) * caida(d, d * 0.28)
    emitir(t, x, g, pan, rev)


def pad(t0, t1, notas, g=0.2, brillo=1600, a=2.0, r=3.0, pan=0.0):
    d = t1 - t0
    x = np.zeros(int(d * SR), dtype=np.float32)
    tr = tt(d)
    for k, f in enumerate(notas):
        for det in (-0.07, 0.0, 0.08):
            fr = f * (1 + det * 0.01 * (k + 1))
            for h in range(1, 6):
                x += (np.sin(2 * np.pi * fr * h * tr + RNG.uniform(0, 6.28)) / h).astype(np.float32) * 0.25
    x = lp(x, brillo) * env(d, a, r) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.17 * tr))
    emitir(t0, x, g / max(1, len(notas)) * 2, pan, 0.8)


def latido(t, g=0.6):
    d = 0.4
    for off, k in ((0.0, 1.0), (0.2, 0.7)):
        x = seno(sweep(d, 70, 38)) * caida(d, 0.07) * k
        emitir(t + off, x, g, 0, 0.1)


def whoosh(t, d=0.8, g=0.5, f0=300, f1=5000, inv=False):
    x = bp(noise(d), f0, f1) * np.sin(np.pi * tt(d) / d) ** 2 * 3.0
    if inv:
        x = x[::-1]
    emitir(t, x, g, RNG.uniform(-0.6, 0.6), 0.4)


def metal(t, g=0.4, d=1.6, base=140):
    x = np.zeros(int(d * SR), dtype=np.float32)
    for r in (1.0, 1.52, 2.31, 2.97, 4.18, 5.41):
        x += seno(np.full(len(x), base * r * RNG.uniform(0.98, 1.02))) * caida(d, d * RNG.uniform(0.18, 0.4)) * (1.0 / r)
    emitir(t, x, g, RNG.uniform(-0.5, 0.5), 0.6)


def zumbido(t0, t1, f=6900, g=0.05):
    d = t1 - t0
    x = seno(np.full(int(d * SR), f)) * env(d, 0.3, 0.6)
    emitir(t0, x, g, 0, 0.2)


def tom(t, f=90, g=0.8, d=0.7):
    x = seno(f * (1 + 1.2 * np.exp(-tt(d) / 0.05))) * caida(d, 0.22)
    x += lp(noise(d), 700) * caida(d, 0.05) * 0.6
    emitir(t, x, g, RNG.uniform(-0.4, 0.4), 0.4)


def hit(t, g=0.6):
    x = hp(noise(0.5), 1500) * caida(0.5, 0.09) * 1.5 + seno(sweep(0.5, 180, 60)) * caida(0.5, 0.12)
    emitir(t, x, g, RNG.uniform(-0.3, 0.3), 0.5)


# ───────────────────────────────────────────── composición por escena
NOTA = {"D1": 36.71, "D2": 73.42, "A1": 55.0, "F2": 87.31, "G2": 98.0, "C2": 65.41, "Bb1": 58.27, "E2": 82.41,
        "D3": 146.83, "F3": 174.61, "A3": 220.0, "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0, "Bb4": 466.16, "C5": 523.25, "D5": 587.33, "E5": 659.26, "F5": 698.46, "A5": 880.0,
        "B3": 246.94, "G3": 196.0, "Fs4": 369.99, "Fs3": 185.0, "B4": 493.88, "A2": 110.0}

def s0():
    for k in range(5):
        latido(0.6 + k * 1.0, 0.35 + 0.1 * k)
    pad(0.0, 6.2, [NOTA["D2"], NOTA["A2"]], 0.3, 500, 3.0, 1.5)
    campana(2.0, NOTA["A5"], 4.0, 0.12, -0.4)
    subida(F(100), F(180), 300, 5000, 0.7)
    impacto(F(180), 1.0)


def s1():
    # carrera: pulso de bombo y bajo en corcheas hasta la explosión; después golpe del cuerpo
    bpm = 132.0
    paso = 60.0 / bpm
    t = F(186)
    k = 0
    while t < F(640):
        if k % 2 == 0:
            bombo(t, 0.9)
        nota = [NOTA["D1"], NOTA["D1"], NOTA["F2"] / 2, NOTA["A1"]][(k // 2) % 4]
        d = paso * 0.5
        x = seno(np.full(int(d * SR), nota * 2)) * caida(d, 0.18) + seno(np.full(int(d * SR), nota * 4)) * caida(d, 0.1) * 0.3
        emitir(t, lp(x, 900 + 1200 * min(1.0, (t - 6) / 14)), 0.45, 0, 0.1)
        if k % 4 == 3:
            hit(t + paso * 0.5, 0.18)
        t += paso * 0.5
        k += 1
    pad(F(180), F(660), [NOTA["D3"], NOTA["F3"], NOTA["A3"]], 0.22, 900, 3.0, 2.0)
    explosion(F(420), 6.0, 1.0)
    subida(F(560), F(640), 200, 7000, 0.7)
    impacto(F(640), 1.0, 3.0)
    whoosh(F(626), 0.9, 0.7, 200, 6000)


def s2():
    # cero g: brillo flotante, destellos de vidrio, vacío tras el silencio de 660
    t0 = F(668)
    pad(t0, F(1000), [NOTA["D4"], NOTA["A4"], NOTA["C5"], NOTA["F4"]], 0.2, 3500, 3.0, 3.0)
    pad(F(660), F(1200), [NOTA["D2"]], 0.25, 300, 4.0, 3.0)
    arp = [NOTA["D4"], NOTA["F4"], NOTA["A4"], NOTA["C5"], NOTA["D5"], NOTA["A4"], NOTA["F4"], NOTA["E4"]]
    for k in range(34):
        campana(F(700) + k * 0.62, arp[k % len(arp)] * (2 if k % 5 == 4 else 1), 2.6, 0.12, math.sin(k) * 0.7, 0.9)
    whoosh(F(830) - 0.2, 1.4, 0.5, 80, 800)
    sub(F(830), 2.5, 60, 20, 0.7)                        # la gravedad se invierte
    zumbido(F(880), F(925), 6500, 0.06)                   # congelado
    subida(F(1000), F(1200), 500, 9000, 0.6)             # la partícula que crece
    campana(F(1000), NOTA["A5"], 6.0, 0.15)
    subida(F(1150), F(1200), 300, 8000, 0.7)


def s3():
    impacto(F(1200), 1.0, 2.5)
    pad(F(1200), F(1290), [NOTA["D2"], NOTA["A2"]], 0.3, 600, 1.0, 1.0)
    subida(F(1200), F(1290), 250, 7000, 0.6)
    explosion(F(1290), 9.0, 1.2)
    sub(F(1290), 5.0, 55, 18, 1.0)
    # cámara lenta: retumbos largos y resonancias
    for k in range(5):
        metal(F(1350) + k * 1.3, 0.25, 3.0, 55 + 10 * k)
    pad(F(1340), F(1560), [NOTA["D1"], NOTA["A1"], NOTA["F2"]], 0.35, 400, 2.0, 2.0)
    zumbido(F(1560), F(1600), 6800, 0.07)                 # congelado: sólo un pitido
    impacto(F(1625), 1.0, 3.0)                            # reanuda
    subida_inversa(F(1680), F(1740), 0.8)                 # retroceso
    whoosh(F(1680), 2.0, 0.5, 100, 3000, inv=True)
    subida(F(1740), F(1920), 150, 9000, 0.9)             # zoom al interior
    for k in range(12):
        tom(F(1740) + k * 0.5, 80 + 6 * k, 0.4 + 0.04 * k)


def s4():
    impacto(F(1920), 0.9, 2.2)
    pad(F(1925), F(2262), [NOTA["D4"], NOTA["F4"], NOTA["A4"], NOTA["D5"]], 0.2, 5000, 2.0, 2.0)
    pad(F(1920), F(2400), [NOTA["D2"]], 0.25, 350, 3.0, 3.0)
    arp = [NOTA["D5"], NOTA["A4"], NOTA["F5"], NOTA["A4"], NOTA["C5"], NOTA["E5"], NOTA["A4"], NOTA["D5"]]
    t = F(1928)
    k = 0
    while t < F(2250):
        campana(t, arp[k % len(arp)], 2.2, 0.16, math.sin(k * 0.8) * 0.8, 0.9)
        t += 0.34
        k += 1
    for k in range(10):
        bombo(F(1960) + k * 0.68 * 2, 0.5)
    subida(F(2200), F(2262), 400, 9000, 0.7)
    vidrio(F(2262), 1.2, 3.0)
    for k in range(5):
        vidrio(F(2262) + 0.2 * k, 0.5, 2.0)
    sub(F(2262), 2.0, 80, 30, 0.8)
    pad(F(2330), F(2400), [NOTA["A4"], NOTA["D5"], NOTA["F5"]], 0.2, 7000, 1.5, 1.0)
    subida(F(2340), F(2400), 500, 10000, 0.7)


def s5():
    impacto(F(2400), 0.9, 2.5)
    pad(F(2400), F(3000), [NOTA["D2"], NOTA["A2"], NOTA["F3"]], 0.3, 700, 3.0, 2.0)
    # columnas que caen (en dominó): instante en el guion = 80 s + (y−4)/6,5 + 0,9
    for k in range(10):
        yk = 20 + 10 * k
        tc = F(2400) + (yk - 4.0) / 6.5 + 0.9 + 0.25
        if tc < F(2900):
            explosion(tc, 2.5, 0.5 + 0.03 * k)
            hit(tc + 0.1, 0.5)
    t = F(2410)
    k = 0
    while t < F(2780):
        tom(t, 70 + 15 * (k % 3), 0.7)
        if k % 2:
            tom(t + 0.2, 100, 0.35)
        t += 0.5
        k += 1
    for k in range(8):
        metal(F(2450) + k * 1.9, 0.25, 2.5, 90 + 20 * (k % 3))
    whoosh(F(2640), 1.0, 0.6, 100, 2000)                  # rodar
    sub(F(2780), 4.0, 50, 18, 0.9)                        # cámara lenta del salto
    subida(F(2900), F(2999), 300, 9000, 0.8)
    vidrio(F(2950), 0.8, 3.0)


def s6():
    # oscuridad: bajo continuo, latidos, resonancias metálicas, alarma cada 2 s y el anillo final
    pad(F(3000), F(3750), [NOTA["D1"], NOTA["A1"]], 0.4, 250, 4.0, 3.0)
    pad(F(3060), F(3640), [NOTA["D3"], NOTA["F3"], NOTA["Bb1"] * 4], 0.12, 1200, 6.0, 4.0)
    t = F(3010)
    while t < F(3640):
        latido(t, 0.28)
        t += 1.25
    for k in range(10):
        metal(F(3100) + k * 2.7, 0.14 + 0.02 * (k % 3), 4.0, 150 + 25 * (k % 4))
    for k in range(int((F(3640) - F(3000)) / 2.0)):
        campana(F(3000) + k * 2.0 + 0.1, NOTA["F5"] * 2, 0.35, 0.05, 0.5, 0.2)       # alarma roja
    for k in range(6):
        w = bp(noise(2.5), 400, 1800) * np.sin(np.pi * tt(2.5) / 2.5) ** 3
        emitir(F(3100) + k * 4.1, w, 0.08, RNG.uniform(-0.8, 0.8), 0.9)
    subida(F(3640), F(3750), 400, 10000, 0.8)
    campana(F(3640), NOTA["A5"] * 2, 4.0, 0.12)


def s7():
    """Brillante y ascendente. El tramo 4100–4250 se invierte (retroceso del tiempo)."""
    global D, W
    Dg, Wg = D, W
    D = np.zeros_like(Dg)
    W = np.zeros_like(Wg)
    impacto(F(3750), 0.8, 2.0)
    acordes = [[NOTA["D3"], NOTA["A3"], NOTA["D4"], NOTA["Fs4"]], [NOTA["B3"], NOTA["D4"], NOTA["Fs4"], NOTA["B4"]], [NOTA["G3"], NOTA["B3"], NOTA["D4"], NOTA["G4"]], [NOTA["A3"], NOTA["C4"] * 1.122, NOTA["E4"], NOTA["A4"]]]
    for k, ac in enumerate(acordes * 4):
        t0 = F(3752) + k * 3.0
        if t0 < F(4490):
            pad(t0, t0 + 3.6, ac, 0.28, 3500, 0.8, 1.8)
    t = F(3760)
    k = 0
    arp = [NOTA["D4"], NOTA["Fs4"], NOTA["A4"], NOTA["D5"], NOTA["A4"], NOTA["Fs4"]]
    while t < F(4490):
        campana(t, arp[k % len(arp)], 1.6, 0.14, math.sin(k * 0.5) * 0.8, 0.6)
        t += 0.25
        k += 1
    for k in range(40):
        bombo(F(3850) + k * 0.5, 0.55)
    subida(F(3900), F(3950), 300, 8000, 0.5)
    # onda de congelado
    for k in range(4):
        campana(F(4250) + k * 0.4, NOTA["D5"] * 2, 3.0, 0.2, -0.5 + 0.33 * k, 0.9)
    subida(F(4440), F(4499), 300, 11000, 0.8)
    # inversión temporal del tramo 4100–4250
    a, b = int((F(4100) - F(3750)) * SR), int((F(4250) - F(3750)) * SR)
    seg = int(F(3750) * SR)
    s7D = D[:, seg + a:seg + b][:, ::-1].copy()
    s7W = W[:, seg + a:seg + b][:, ::-1].copy()
    D[:, seg + a:seg + b] = s7D
    W[:, seg + a:seg + b] = s7W
    Dg += D
    Wg += W
    D, W = Dg, Wg


def s8():
    impacto(F(4500), 1.0, 3.0)
    pad(F(4500), F(4900), [NOTA["D2"], NOTA["A2"], NOTA["F3"]], 0.3, 900, 1.0, 2.0)
    cortes = [4540, 4580, 4600, 4630, 4650, 4690, 4730, 4750, 4790]
    for c in cortes:
        hit(F(c), 0.8)
        whoosh(F(c) - 0.2, 0.5, 0.35, 400, 7000)
        bombo(F(c), 0.7)
    for k in range(60):                               # percusión que acelera
        tom(F(4500) + k * (0.5 - 0.004 * k), 70 + (k % 4) * 10, 0.55)
    # tape-stop en el congelado
    x = seno(sweep(1.0, 800, 40)) * np.linspace(1, 0, int(SR)).astype(np.float32)
    emitir(F(4560), x, 0.25, 0, 0.5)
    zumbido(F(4700), F(4730), 7000, 0.05)
    # costuras que se agrietan
    for k in range(40):
        t = F(4800) + (k / 40.0) ** 1.4 * 3.5
        x = hp(noise(0.12), 4000) * caida(0.12, 0.03)
        emitir(t, x, 0.25, RNG.uniform(-1, 1), 0.5)
    subida(F(4800), F(4905), 300, 11000, 0.9)
    vidrio(F(4905), 1.4, 4.0)
    for k in range(7):
        vidrio(F(4905) + 0.15 * k, 0.6, 3.0)
    explosion(F(4905), 5.0, 0.9)
    sub(F(4905), 4.0, 70, 22, 1.0)
    pad(F(4950), F(5290), [NOTA["D2"], NOTA["A2"]], 0.35, 250, 2.0, 5.0)
    pad(F(5000), F(5280), [NOTA["D4"], NOTA["F4"], NOTA["A4"]], 0.14, 2500, 4.0, 4.0)
    # el ojo vuelve: latidos del comienzo y descenso final
    for k in range(4):
        latido(F(5145) + k * 1.0, 0.45 - 0.06 * k)
    sub(F(5200), 3.0, 60, 15, 0.5)
    campana(F(5290), NOTA["A5"], 9.0, 0.3, 0.0, 0.9)
    campana(F(5295), NOTA["A5"] * 2, 6.0, 0.1, 0.3, 0.9)


# ───────────────────────────────────────────── mezcla final
def reverb():
    ir_n = int(2.8 * SR)
    t = np.arange(ir_n) / SR
    out = np.zeros_like(W)
    for c in range(2):
        ir = RNG.standard_normal(ir_n) * np.exp(-t / 0.7)
        ir[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
        n = N + ir_n
        nfft = 1 << (n - 1).bit_length()
        r = np.fft.irfft(np.fft.rfft(W[c].astype(np.float64), nfft) * np.fft.rfft(ir, nfft), nfft)[:N]
        out[c] = (r * 0.012).astype(np.float32)
    return out


def curva_maestra():
    g = np.ones(N, dtype=np.float32)

    def hueco(a, b, nivel, suav=0.25):
        i0, i1 = int(a * SR), int(b * SR)
        s = int(suav * SR)
        g[i0:i1] = np.minimum(g[i0:i1], nivel)
        if s > 0:
            g[max(0, i0 - s):i0] = np.minimum(g[max(0, i0 - s):i0], np.linspace(1, nivel, min(s, i0)))
            g[i1:i1 + s] = np.minimum(g[i1:i1 + s], np.linspace(nivel, 1, len(g[i1:i1 + s])))
    hueco(F(654), F(668), 0.06)         # silencio tras la onda de choque
    hueco(F(2994), F(3012), 0.12)       # silencio antes de la oscuridad
    hueco(F(5299), F(5300), 1.0)
    g[int(177.5 * SR):] *= np.linspace(1.0, 0.0, N - int(177.5 * SR)).astype(np.float32) ** 1.5
    g[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR)).astype(np.float32)
    return g


def main(salida):
    for f in (s0, s1, s2, s3, s4, s5, s6, s7, s8):
        print("música", f.__name__, flush=True)
        f()
    print("reverberación", flush=True)
    R = reverb()
    mix = D + R
    mix *= curva_maestra()
    pico = np.max(np.abs(mix))
    mix = np.tanh(mix / pico * 1.6) / np.tanh(1.6) * 0.93
    pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(salida, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("pico antes de limitar:", round(float(pico), 3), "→", salida, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
