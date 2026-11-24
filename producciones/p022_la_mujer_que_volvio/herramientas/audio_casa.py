"""Sonido completo de LA CASA (cap. 1, el presente): tormenta contra el ventanal, viento y cortinas, truenos tras cada relámpago, goteo de sangre y de vino, reloj lejano, crepitar del cigarro,
latido y respiración lentos de Gabriel, música triste (piano grave solo, cuerdas oscuras y un drone sucio de textura industrial, al estilo de la tensión de Max Payne 3 pero original),
y la narración de Gabriel (voz siempre sobre el fondo). Procedural, sin créditos. También escribe los subtítulos (.srt).
Uso: python audio_casa.py CASA.json SALIDA.wav [SUBTITULOS.srt]"""
import json, sys, wave
from pathlib import Path
import numpy as np
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).parent))
from estudio.audio import procedural as P  # noqa: E402
import musica_noir as MN  # noqa: E402
SR = P.SR
js = json.load(open(sys.argv[1])); EV = js['eventos']; DUR = float(js['duracion_s'])
n = int(DUR * SR); t = np.arange(n) / SR
rng = np.random.default_rng(777)
mez = np.zeros((n, 2))
def lp(x, fc, o=4):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** o); return np.fft.irfft(X, len(x))
def hp(x, fc, o=4):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 - 1 / (1 + (f / fc) ** o); return np.fft.irfft(X, len(x))
def est(x): return np.stack([x, np.roll(x, int(0.0009 * SR)) * 0.92], axis=1)
def poner(x, t0, g=1.0, pan=0.0): P._poner(mez, x, t0, g, pan)
T_REL = list(EV['relampagos_s'])
# ráfagas de viento: cada trueno trae una ráfaga (el mismo dato que mueve las cortinas en Blender)
rafaga = 0.28 + 0.14 * np.sin(t * 0.31)
for tl in T_REL: rafaga = rafaga + 0.85 * np.exp(-((t - tl - 0.3) / 1.4) ** 2)

# 1) LLUVIA contra el vidrio (gotas secas + velo) y sobre el techo; el exterior suena amortiguado por el ventanal
velo = lp(P._ruido_banda(n, rng, 1800, 9000), 6500) * 0.30 + lp(P._ruido_banda(n, rng, 300, 1500), 900) * 0.22
vid = np.zeros(n)
for i in rng.integers(0, n - 900, int(DUR * 70)):
    k = np.arange(900); vid[i:i + 900] += np.exp(-k / 70) * np.sin(2 * np.pi * rng.uniform(1400, 3800) * k / SR) * rng.uniform(0.15, 0.8)
mez += est((velo * (0.7 + 0.3 * rafaga) + vid * 0.20) * 0.50)
# 2) VIENTO grave que silba por las rendijas y empuja las cortinas
vie = lp(P._ruido_banda(n, rng, 80, 900), 500) * (0.25 + 0.9 * rafaga) * 0.55
sil = hp(lp(P._ruido_banda(n, rng, 500, 2500), 1800), 600) * np.clip(rafaga - 0.4, 0, 1) * 0.5
mez += est(vie + sil * 0.5)
# 3) TRUENOS: 0,5–1,6 s después de cada relámpago (la luz llega antes); más lejanos al principio, más cerca después
def trueno(dur, cerca):
    m = int(dur * SR); k = np.arange(m) / SR
    r = lp(P._ruido_banda(m, rng, 25, 600), 260 + 160 * cerca) * np.exp(-k / (1.1 + 0.9 * cerca))
    cr = hp(lp(P._ruido_banda(m, rng, 200, 4000), 3000), 250) * np.exp(-k / 0.18) * cerca
    return (r * 1.0 + cr * 0.6) * np.minimum(k / 0.04, 1)
for i_, tl in enumerate(T_REL):
    cerca = 0.25 + 0.75 * min(i_ / 6.0, 1.0)
    poner(est(trueno(4.5, cerca))[:, 0], tl + 0.5 + 1.1 * (1 - cerca), 0.9 * (0.45 + 0.55 * cerca), rng.uniform(-0.4, 0.4))
# 4) CORTINAS que se hinchan (susurro de tela) en las ráfagas fuertes
tela = hp(lp(P._ruido_banda(n, rng, 150, 2500), 1600), 140) * np.clip(rafaga - 0.55, 0, 1) ** 1.3 * 0.55
mez += est(tela)
# 5) GOTEO: sangre sobre la madera (cada 1,9 s, tap mate) y vino desde el borde de la mesa (cada 1,35 s, más claro)
def gota(f0, dec, g_, brillo):
    m = int(0.30 * SR); k = np.arange(m) / SR
    return (np.sin(2 * np.pi * (f0 * (1 + 0.8 * np.exp(-k / 0.012))) * k) * np.exp(-k / dec) + brillo * hp(P._ruido_banda(m, rng, 800, 6000), 900) * np.exp(-k / 0.01)) * g_
tg = 0.6
while tg < DUR:
    poner(gota(310, 0.045, 0.55, 0.30), tg, 0.5, -0.5); tg += EV['gota_sangre_cada_s']
tv = 0.2
while tv < DUR:
    poner(gota(620, 0.035, 0.40, 0.45), tv, 0.4, 0.55); tv += EV['gota_vino_cada_s']
# 6) RELOJ de pared lejano (tic-tac lento) y zumbido eléctrico de la lámpara
tic = np.zeros(n)
for i_, tt in enumerate(np.arange(0.7, DUR, 1.0)):
    m = int(0.05 * SR); k = np.arange(m) / SR; i0 = int(tt * SR)
    if i0 + m < n: tic[i0:i0 + m] += hp(P._ruido_banda(m, rng, 600, 5000), 700) * np.exp(-k / 0.008) * (1.0 if i_ % 2 == 0 else 0.7)
mez += est(tic * 0.12 + np.sin(2 * np.pi * 50 * t) * 0.012 + np.sin(2 * np.pi * 100 * t) * 0.006)
# 7) CIGARRO: crepitar leve de la brasa de tanto en tanto
cre = np.zeros(n)
for tt in rng.uniform(1, DUR - 1, int(DUR * 0.7)):
    m = int(0.012 * SR); i0 = int(tt * SR)
    if i0 + m < n: cre[i0:i0 + m] += hp(P._ruido_banda(m, rng, 2500, 9000), 2500) * np.exp(-np.arange(m) / SR / 0.003) * rng.uniform(0.1, 0.4)
mez += est(cre * 0.12)
# 8) LATIDO lento y RESPIRACIÓN pesada de Gabriel (herido, borracho, cansado)
def latido(bpm):
    s = np.zeros(n); ult = -1; fase = np.cumsum(np.full(n, bpm / 60.0)) / SR
    for i in range(1, n):
        if int(fase[i]) != ult:
            ult = int(fase[i])
            for off, am in ((0, 1.0), (int(0.2 * SR), 0.65)):
                m = int(0.14 * SR); k = np.arange(m) / SR
                if i + off + m < n: s[i + off:i + off + m] += np.sin(2 * np.pi * (50 + 28 * np.exp(-k / 0.03)) * k) * np.exp(-k / 0.05) * am
    return s
mez += est(latido(54) * 0.30 * np.interp(t, [0, 6, DUR - 6, DUR], [0, 1, 1, 0.3]))
ciclo = 0.5 - 0.5 * np.cos(2 * np.pi * np.cumsum(np.full(n, 0.20)) / SR)
mez += est(hp(lp(P._ruido_banda(n, rng, 250, 3200), 2800), 300) * ciclo ** 1.5 * 0.20)

# 9) MÚSICA triste y oscura: piano grave solo que se abre, cuerdas, y drone sucio (saturado) que crece lento al final
sec = [{"t0": 0.5, "t1": 20.0, "capas": ["nota_sola", "pad"]}, {"t0": 20.0, "t1": 52.0, "capas": ["piano", "melodia", "pad"]}, {"t0": 52.0, "t1": DUR - 3.0, "capas": ["piano", "melodia", "cuerdas", "pad"]}]
mus = MN.tema(n, np.random.default_rng(57), sec, 1.0)
drone = np.zeros(n)
for f_, g_ in ((36.7, 1.0), (36.9, 0.8), (55.0, 0.5), (73.4, 0.3)):                      # re muy grave, ligeramente desafinado
    drone += np.sin(2 * np.pi * f_ * t + rng.uniform(0, 6.28)) * g_
drone = np.tanh(drone * 1.8) * 0.5 * (0.7 + 0.3 * np.sin(2 * np.pi * t / 13.0))
drone = drone + lp(P._ruido_banda(n, rng, 40, 600), 380) * 0.35                           # textura de ruido ambiental, sin ritmo
mus += np.stack([drone, np.roll(drone, 60)], axis=1) * np.interp(t, [0, 4, 40, DUR - 4, DUR], [0, 0.22, 0.30, 0.55, 0.0])[:, None]
mus *= 0.40 * np.interp(t, [0, 2, DUR - 4, DUR], [0, 1, 1, 0])[:, None]

# 10) VOZ: narración de Gabriel (voces.json, bloque «casa»)
vo = [x for x in json.load(open(Path(__file__).parents[1] / 'audio_cap1' / 'voces.json')) if x['bloque'] == 'casa']
inicios = [5.0, 8.6, 12.0, 14.8, 17.6, 20.6, 24.2, 28.2, 33.0, 35.0, 38.0, 40.3, 43.0, 46.8, 53.5, 56.5, 60.5]
assert len(vo) == len(inicios), (len(vo), len(inicios))
voz = np.zeros((n, 2)); srt = []
def tc(s_): return '%02d:%02d:%02d,%03d' % (int(s_ // 3600), int(s_ % 3600 // 60), int(s_ % 60), int((s_ % 1) * 1000))
for l, ti in zip(vo, inicios):
    x = P._decodificar(RAIZ / l['mp3']); P._poner(voz, x, ti, 1.0, 0.0); srt.append((ti, ti + l['dur_s'] + 0.1, l['texto']))
voz *= 0.85 / (np.abs(voz).max() + 1e-9)
envv = np.minimum(np.convolve(np.abs(voz[:, 0]), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode='same') / 0.06, 1.0)
envv = np.convolve(envv, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode='same')
bajo = mez * 0.66 + mus * 0.55
bajo *= (1.0 - 0.85 * envv)[:, None]
hab = envv > 0.5
print('voz sobre el fondo mientras habla: +%.1f dB' % (20 * np.log10(np.sqrt((voz[hab] ** 2).mean()) / np.sqrt((bajo[hab] ** 2).mean()))))
fin = bajo + voz
fin *= np.clip(np.interp(t, [0, 0.4, DUR - 2.0, DUR], [0, 1, 1, 0]), 0, 1)[:, None]
pico = np.abs(fin).max()
if pico > 0.95: fin *= 0.95 / pico
print('PICO', round(float(np.abs(fin).max()), 3), 'duración', round(DUR, 1), 's')
with wave.open(sys.argv[2], 'wb') as w_:
    w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((np.clip(fin, -1, 1) * 32767).astype('<i2').tobytes())
if len(sys.argv) > 3:
    with open(sys.argv[3], 'w', encoding='utf-8') as f_:
        for i_, (a_, b_, tx) in enumerate(srt, 1): f_.write(f'{i_}\n{tc(a_)} --> {tc(b_)}\n{tx}\n\n')
    print('subtítulos', len(srt))
