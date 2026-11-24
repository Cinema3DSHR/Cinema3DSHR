"""Sonido completo del ACCIDENTE (cap. 1): lluvia, motor, derrape, choque, vuelco, zumbido de oídos, balizas, pasos, respiración y latidos, truenos, música original
y la narración de Gabriel ubicada sobre las escenas (voz siempre por encima: fondo −9 dB bajo la voz). Todo procedural (sin créditos). También escribe los subtítulos (.srt).
Uso: python audio_accidente.py ACCIDENTE.json SALIDA.wav [SUBTITULOS.srt]"""
import json, sys, wave, math
from pathlib import Path
import numpy as np
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
from estudio.audio import procedural as P  # noqa: E402
SR = P.SR
js = json.load(open(sys.argv[1])); EV = js['eventos']; DUR = float(js['duracion_s'])
n = int(DUR * SR); t = np.arange(n) / SR
rng = np.random.default_rng(2024)
mez = np.zeros((n, 2))
def lp(x, fc, o=4):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** o); return np.fft.irfft(X, len(x))
def hp(x, fc, o=4):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 - 1 / (1 + (f / fc) ** o); return np.fft.irfft(X, len(x))
def est(x): return np.stack([x, np.roll(x, int(0.0007 * SR)) * 0.9], axis=1)
def env_ventana(a, b, sube=0.3, baja=0.5):                                    # 0→1 entre a y b con rampas
    return np.clip((t - a) / max(sube, 1e-3), 0, 1) * np.clip((b - t) / max(baja, 1e-3), 0, 1)
def poner(x, t0, g=1.0, pan=0.0): P._poner(mez, x, t0, g, pan)

T_SK, T_IM, T_RO, T_RE = EV['derrape_s'], EV['impacto_s'], EV['vuelco_fin_s'], EV['reposo_s']
T_EL, T_SA, T_DE = EV['elena_despedida_s'], EV['gabriel_sale_s'], EV['desmayo_s']

# 1) LLUVIA constante (más fuerte con la tormenta) + goteo sobre chapa después del choque
llu = lp(P._ruido_banda(n, rng, 1500, 9000), 7000) * 0.35 + lp(P._ruido_banda(n, rng, 300, 1500), 900) * 0.25
gotas = np.zeros(n)
for i in rng.integers(0, n - 800, int(DUR * 50)):
    k = np.arange(800); gotas[i:i + 800] += np.exp(-k / 90) * np.sin(2 * np.pi * rng.uniform(900, 2600) * k / SR) * rng.uniform(0.2, 0.9)
mez += est((llu * (0.78 + 0.22 * np.sin(2 * np.pi * t / 19.0)) + gotas * 0.22) * 0.50)

# 2) MOTOR y ruta mojada hasta el derrape; el motor se ahoga después del choque
rpm = 48 + 3 * np.sin(2 * np.pi * t / 9.0) + 1.2 * np.sin(2 * np.pi * t / 2.3)
rpm = rpm + 26 * np.clip((t - T_SK) / 0.8, 0, 1) * (t < T_IM)                         # se revoluciona al despistar
fase = 2 * np.pi * np.cumsum(rpm) / SR
mot = (np.sin(fase) * 0.5 + np.sin(2 * fase) * 0.28 + np.sin(3 * fase) * 0.12) * (0.8 + 0.2 * np.sin(2 * np.pi * 24 * t))
vive = np.clip((T_IM + 0.2 - t) / 0.3, 0, 1)
mez += est(lp(mot, 260) * 0.30 * vive) + est(lp(P._ruido_banda(n, rng, 120, 1800), 700) * (0.28 + 0.05 * np.sin(2 * np.pi * t / 5.3)) * np.clip((T_IM - t) / 0.4, 0, 1))
# limpiaparabrisas hasta el choque
def limpia():
    m = int(0.62 * SR); k = np.arange(m) / SR
    s = lp(P._ruido_banda(m, rng, 400, 3500), 2600) * np.sin(np.pi * k / 0.62) ** 1.5 * 0.55
    for a in (0, m - 1500 - 10): s[a:a + 1500] += np.sin(2 * np.pi * 95 * np.arange(1500) / SR) * np.exp(-np.arange(1500) / 220) * 0.9
    return s
w = limpia(); tt = 0.8
while tt < T_IM + 1.0:
    poner(w, tt, 0.45, -0.15); poner(w[::-1] * 0.9, tt + 0.7, 0.42, -0.15); tt += 1.4

# 3) DERRAPE (chirrido de neumáticos) entre T_SK y T_IM
chi = P._ruido_banda(n, rng, 1400, 3800) * (0.6 + 0.4 * np.sin(2 * np.pi * (6 + 9 * np.clip((t - T_SK) / 1.7, 0, 1)) * t))
mez += est(chi * env_ventana(T_SK, T_IM + 0.05, 0.25, 0.1) * 0.40)
mez += est(lp(P._ruido_banda(n, rng, 60, 400), 300) * env_ventana(T_SK, T_IM, 0.4, 0.2) * 0.30)                      # arrastre de grava

# 4) CHOQUE, VUELCO, VIDRIOS, ROCAS
def golpe_metal(dur=1.4, grave=70, g=1.0):
    m = int(dur * SR); k = np.arange(m) / SR
    cuerpo = np.sin(2 * np.pi * (grave + 90 * np.exp(-k / 0.05)) * k) * np.exp(-k / 0.22)
    chapa = lp(hp(P._ruido_banda(m, rng, 200, 7000), 400), 6000) * np.exp(-k / 0.30)
    crujido = P._ruido_banda(m, rng, 1000, 5000) * np.exp(-k / 0.12) * (np.sin(2 * np.pi * 37 * k) > 0)
    return (cuerpo * 0.9 + chapa * 0.8 + crujido * 0.4) * g
poner(golpe_metal(1.8, 60, 1.0), T_IM, 0.95)
cr = np.zeros(int(2.4 * SR))
for _ in range(90):                                                                    # vidrios que caen y estallan
    i = int(abs(rng.normal(0.1, 0.5)) * SR); i = min(i, len(cr) - 3000); k = np.arange(2600)
    cr[i:i + 2600] += np.sin(2 * np.pi * rng.uniform(3200, 7800) * k / SR) * np.exp(-k / rng.uniform(80, 400)) * rng.uniform(0.1, 0.7)
poner(cr, T_IM + 0.03, 0.30, 0.1)
for tr, g_, p_ in ((T_IM + 0.7, 0.75, -0.1), (T_IM + 1.4, 0.60, 0.15), (T_IM + 2.15, 0.50, -0.1), (T_IM + 2.9, 0.38, 0.1)):  # golpes del vuelco (cada vez más débiles)
    poner(golpe_metal(0.9, 55, g_), tr, 1.0, p_)
poner(lp(P._ruido_banda(int(3.0 * SR), rng, 50, 500), 350) * np.exp(-np.arange(int(3.0 * SR)) / SR / 1.0) * 0.5, T_IM + 0.1, 0.55)          # rodar de piedras
for tp in np.sort(rng.uniform(T_IM + 0.5, T_RO + 1.5, 16)):
    poner(P.impacto(rng), float(tp), float(rng.uniform(0.15, 0.40)), float(rng.uniform(-0.5, 0.5)))
# Elena sale despedida: sólo un golpe de aire y un grito cortado muy lejano (no se muestra)
poner(lp(P._ruido_banda(int(1.1 * SR), rng, 200, 2500), 1500) * np.exp(-np.arange(int(1.1 * SR)) / SR / 0.35) * 0.25, T_EL, 0.7, 0.6)

# 5) ZUMBIDO DE OÍDOS y silencio amortiguado tras el golpe (todo lo demás se «apaga» un rato)
zum = np.sin(2 * np.pi * 4100 * t) * 0.06 + np.sin(2 * np.pi * 3300 * t) * 0.025
zv = np.clip((t - T_IM) / 0.15, 0, 1) * np.exp(-np.clip(t - T_IM - 1.0, 0, None) / 4.2) * (t >= T_IM)
mez += est(zum * zv)
amortigua = 1.0 - 0.80 * np.clip((t - T_IM) / 0.2, 0, 1) * np.clip((T_IM + 7.0 - t) / 5.0, 0, 1) * (t >= T_IM)   # tras el choque el mundo suena lejano y bajo
# (se aplica al final sobre lluvia/efectos, no sobre la voz ni los latidos)

# 6) BALIZAS (relé que hace tic-tac) desde que queda en reposo; vapor del motor
f = T_RE
while f < DUR - 0.5:
    poner(np.sin(2 * np.pi * 2300 * np.arange(int(0.012 * SR)) / SR) * np.exp(-np.arange(int(0.012 * SR)) / (SR * 0.003)), f, 0.10, 0.2)
    poner(np.sin(2 * np.pi * 1700 * np.arange(int(0.012 * SR)) / SR) * np.exp(-np.arange(int(0.012 * SR)) / (SR * 0.003)), f + 0.31, 0.07, 0.2)
    f += 0.625
mez += est(hp(P._ruido_banda(n, rng, 2500, 9000), 3000) * env_ventana(T_IM + 0.3, DUR, 1.0, 3.0) * 0.045)             # siseo de vapor

# 7) TRUENOS a los relámpagos (≈0,8 s después)
for tr in js['eventos']['relampagos_s']:
    m = int(5.0 * SR); k = np.arange(m) / SR
    tru = lp(P._ruido_banda(m, rng, 25, 220), 180) * np.exp(-k / 1.6) * (1 + 0.6 * np.sin(2 * np.pi * 3.1 * k))
    poner(tru, tr + 0.8, 0.7)
    poner(np.exp(-k[:int(0.05 * SR)] / 0.01) * rng.standard_normal(int(0.05 * SR)) * 0.2, tr + 0.0, 0.4)           # chasquido del rayo

# 8) PASOS en el barro/agua y respiración + latidos de Gabriel (primera persona y búsqueda)
paso_bufs = [lp(P._ruido_banda(int(0.28 * SR), rng, 80, 1600), 900) * np.exp(-np.arange(int(0.28 * SR)) / SR / 0.07) for _ in range(4)]
for sg in EV['ruta_gabriel']:
    if sg['clip'] in ('inj_walk', 'sad_walk'):
        ps = 0.62 if sg['clip'] == 'inj_walk' else 0.74; tp = sg['t0'] + 0.2; k = 0
        while tp < sg['t0'] + sg['dur']:
            poner(paso_bufs[k % 4] * (0.8 + 0.4 * ((k % 2) == 0)), tp, 0.55, -0.2 if k % 2 else 0.2); tp += ps; k += 1
    if sg['clip'] == 'exit_car':
        for q in (1.0, 2.1, 3.0, 4.2, 5.0):
            poner(lp(P._ruido_banda(int(0.4 * SR), rng, 60, 700), 500) * np.exp(-np.arange(int(0.4 * SR)) / SR / 0.1), sg['t0'] + q, 0.45)       # puerta, cuerpo apoyándose, el cinturón
def latido(bpm_f, g_f):                                                                  # latidos «lub-dub» graves (BPM variable en el tiempo)
    s = np.zeros(n); fase = np.cumsum(bpm_f / 60.0) / SR; ult = -1
    for i in range(1, n):
        if int(fase[i]) != ult:
            ult = int(fase[i])
            for off, am in ((0, 1.0), (int(0.18 * SR), 0.7)):
                m = int(0.14 * SR); k = np.arange(m) / SR
                if i + off + m < n: s[i + off:i + off + m] += np.sin(2 * np.pi * (52 + 30 * np.exp(-k / 0.03)) * k) * np.exp(-k / 0.05) * am * g_f[i]
    return s
bpm = np.interp(t, [0, T_SK, T_IM, T_IM + 6, T_SA, T_DE - 8, T_DE, T_DE + 3, DUR], [58, 62, 140, 112, 96, 108, 70, 38, 0])
ganancia = np.clip(np.interp(t, [0, T_SK - 0.5, T_SK + 0.5, T_DE, T_DE + 4, DUR], [0, 0, 0.7, 0.9, 0.4, 0.0]), 0, 1)
mez += est(latido(bpm, ganancia) * 0.55)
# respiración: aire que entra y sale (más rápida y áspera mientras corre el pulso)
frec_r = np.interp(t, [0, T_IM, T_SA, T_DE - 8, T_DE, T_DE + 2.5, DUR], [0.0, 0.5, 0.45, 0.55, 0.3, 0.16, 0.0])
fr = np.cumsum(frec_r) / SR; ciclo = 0.5 - 0.5 * np.cos(2 * np.pi * fr)
resp = hp(lp(P._ruido_banda(n, rng, 300, 3500), 3000), 350) * (ciclo ** 1.4) * np.interp(t, [0, T_SK, T_IM + 0.5, T_DE + 2, T_DE + 4, DUR], [0, 0, 0.5, 0.45, 0.1, 0.0])
mez += est(resp * 0.30)

# 9) MÚSICA original: tensión sutil en el viaje, golpe grave en el choque, silencio, tema triste de piano que crece en la búsqueda y se apaga con el desmayo
def cuerda(f_, dur, g_):
    m = int(dur * SR); k = np.arange(m) / SR
    s_ = sum(np.sin(2 * np.pi * f_ * h * k + rng.uniform(0, 6.28)) / h ** 1.3 for h in range(1, 6))
    return s_ * np.minimum(k / 2.5, 1) * np.minimum((dur - k) / 3.0, 1) * g_ * (1 + 0.04 * np.sin(2 * np.pi * 5.2 * k))
def piano(f_, g_):
    m = int(4.0 * SR); k = np.arange(m) / SR
    return (np.sin(2 * np.pi * f_ * k) + 0.5 * np.sin(4 * np.pi * f_ * k) * np.exp(-k / 0.8) + 0.25 * np.sin(6 * np.pi * f_ * k) * np.exp(-k / 0.4)) * np.exp(-k / 1.4) * np.minimum(k / 0.006, 1) * g_
mus = np.zeros((n, 2))
P._poner(mus, cuerda(55.0, T_IM - 1.0, 0.30), 0.5, 1.0, 0.0); P._poner(mus, cuerda(82.4, T_IM - 3.0, 0.16), 2.5, 1.0, 0.0)           # drone bajo que crece hasta el choque
P._poner(mus, np.sin(2 * np.pi * 36 * np.arange(int(3.5 * SR)) / SR) * np.exp(-np.arange(int(3.5 * SR)) / SR / 1.2) * 0.9, T_IM, 1.0, 0.0)  # golpe grave del choque
sys.path.insert(0, str(Path(__file__).parent))
import musica_noir as MN                                                              # tema lento, piano grave y cuerdas con reverberación (original)
sec = [{"t0": 0.5, "t1": T_IM - 0.5, "capas": ["nota_sola", "pad"]},                   # antes del choque: notas aisladas y aire
       {"t0": 22.0, "t1": T_DE - 12.0, "capas": ["piano", "melodia", "pad"]},          # después del silencio: entra el piano
       {"t0": T_DE - 12.0, "t1": T_DE + 4.0, "capas": ["piano", "melodia", "cuerdas", "pad"]}]   # sube con la búsqueda y se apaga con el desmayo
mus += MN.tema(n, np.random.default_rng(31), sec, 1.0) * 0.38
mus *= np.clip(np.interp(t, [0, 1, T_IM - 0.4, T_IM + 0.3, T_IM + 6, 21.5, 24.0, T_DE - 3, T_DE + 2.5, DUR], [0, 0.6, 1.0, 0.0, 0.0, 0.0, 0.8, 1.0, 0.25, 0.0]), 0, 1)[:, None]

# 10) VOZ: narración de Gabriel (voces.json) ubicada sobre las escenas
vo = [x for x in json.load(open(Path(__file__).parents[1] / 'audio_cap1' / 'voces.json')) if x['bloque'] == 'accidente']
inicios = [0.8, 3.2, 6.35, 12.4, 14.4, 22.6, 27.5, 34.0, 37.4, 41.0, 46.0, 52.0, 57.6]
voz = np.zeros((n, 2))
srt = []
def tc(s_): return '%02d:%02d:%02d,%03d' % (int(s_ // 3600), int(s_ % 3600 // 60), int(s_ % 60), int((s_ % 1) * 1000))
for l, ti in zip(vo, inicios):
    x = P._decodificar(RAIZ / l['mp3']); P._poner(voz, x, ti, 1.0, 0.0)
    srt.append((ti, ti + l['dur_s'] + 0.1, l['texto']))
voz *= 0.85 / (np.abs(voz).max() + 1e-9)
envv = np.convolve(np.abs(voz[:, 0]), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode='same'); envv = np.minimum(envv / 0.06, 1.0)
envv = np.convolve(envv, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode='same')

# mezcla: el mundo amortiguado tras el golpe; música aparte; todo baja bajo la voz
mundo = mez * amortigua[:, None]
bajo = mundo * 0.62 + mus * 0.55
bajo *= (1.0 - 0.85 * envv)[:, None]
hab = envv > 0.5
print('voz sobre el fondo mientras habla: +%.1f dB' % (20 * np.log10(np.sqrt((voz[hab] ** 2).mean()) / np.sqrt((bajo[hab] ** 2).mean()))))
fin = bajo + voz
fin *= np.clip(np.interp(t, [0, 0.4, DUR - 2.0, DUR], [0, 1, 1, 0]), 0, 1)[:, None]
pico = np.abs(fin).max()
if pico > 0.95: fin *= 0.95 / pico
print('PICO', round(float(np.abs(fin).max()), 3), 'duración', round(DUR, 1), 's')
pcm = (np.clip(fin, -1, 1) * 32767).astype('<i2')
with wave.open(sys.argv[2], 'wb') as w_:
    w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes(pcm.tobytes())
if len(sys.argv) > 3:
    with open(sys.argv[3], 'w', encoding='utf-8') as f_:
        for i_, (a_, b_, tx) in enumerate(srt, 1): f_.write(f'{i_}\n{tc(a_)} --> {tc(b_)}\n{tx}\n\n')
    print('subtítulos', len(srt))
