"""PUENTE del capítulo 1 (entre el desmayo y la casa) y TARJETA final. La narración «Después de aquella noche…» (bloque «despues» de voces.json, 12 líneas) sobre pantalla negra con grano:
lluvia lejana, viento, un trueno, el piano triste (musica_noir) y el latido que se apaga. Procedural, sin créditos.
Uso: python audio_puente.py SALIDA_PUENTE.wav SALIDA_PUENTE.srt SALIDA_TITULO.wav"""
import json, sys, wave
from pathlib import Path
import numpy as np
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(Path(__file__).parent))
from estudio.audio import procedural as P  # noqa: E402
import musica_noir as MN  # noqa: E402
SR = P.SR
rng = np.random.default_rng(909)
def lp(x, fc, o=4):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** o); return np.fft.irfft(X, len(x))
def est(x): return np.stack([x, np.roll(x, int(0.0009 * SR)) * 0.92], axis=1)
def escribir(ruta, y):
    pico = np.abs(y).max()
    if pico > 0.95: y = y * (0.95 / pico)
    with wave.open(ruta, 'wb') as w_:
        w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())
vo = [x for x in json.load(open(Path(__file__).parents[1] / 'audio_cap1' / 'voces.json')) if x['bloque'] == 'despues']
inicios = [2.0, 7.0, 9.4, 12.4, 14.2, 17.0, 21.0, 27.0, 29.2, 32.0, 36.5, 43.5]
assert len(vo) == len(inicios)
DUR = 50.0; n = int(DUR * SR); t = np.arange(n) / SR
mez = np.zeros((n, 2))
mez += est(lp(P._ruido_banda(n, rng, 1800, 9000), 6500) * 0.16 + lp(P._ruido_banda(n, rng, 250, 1400), 800) * 0.14)                      # lluvia lejana
mez += est(lp(P._ruido_banda(n, rng, 60, 700), 420) * (0.25 + 0.15 * np.sin(2 * np.pi * t / 17.0)) * 0.5)                                 # viento
def trueno(dur):
    m = int(dur * SR); k = np.arange(m) / SR
    return lp(P._ruido_banda(m, rng, 25, 600), 300) * np.exp(-k / 1.8) * np.minimum(k / 0.05, 1)
P._poner(mez, trueno(4.5), 25.5, 0.7, 0.3)
def latido(bpm):
    s = np.zeros(n); ult = -1; fase = np.cumsum(np.full(n, bpm / 60.0)) / SR
    for i in range(1, n):
        if int(fase[i]) != ult:
            ult = int(fase[i])
            for off, am in ((0, 1.0), (int(0.22 * SR), 0.6)):
                m = int(0.14 * SR); k = np.arange(m) / SR
                if i + off + m < n: s[i + off:i + off + m] += np.sin(2 * np.pi * (48 + 26 * np.exp(-k / 0.03)) * k) * np.exp(-k / 0.05) * am
    return s
mez += est(latido(50) * 0.22 * np.interp(t, [0, 3, 40, 50], [0, 1, 1, 0]))
mus = MN.tema(n, np.random.default_rng(88), [{"t0": 0.5, "t1": 24.0, "capas": ["nota_sola", "pad"]}, {"t0": 24.0, "t1": 48.0, "capas": ["piano", "melodia", "pad"]}], 1.0) * 0.42
mus *= np.interp(t, [0, 2, 46, 50], [0, 1, 1, 0])[:, None]
voz = np.zeros((n, 2)); srt = []
def tc(s_): return '%02d:%02d:%02d,%03d' % (int(s_ // 3600), int(s_ % 3600 // 60), int(s_ % 60), int((s_ % 1) * 1000))
for l, ti in zip(vo, inicios):
    P._poner(voz, P._decodificar(RAIZ / l['mp3']), ti, 1.0, 0.0); srt.append((ti, ti + l['dur_s'] + 0.15, l['texto']))
voz *= 0.85 / (np.abs(voz).max() + 1e-9)
envv = np.minimum(np.convolve(np.abs(voz[:, 0]), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode='same') / 0.06, 1.0)
envv = np.convolve(envv, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode='same')
bajo = (mez * 0.7 + mus * 0.55) * (1.0 - 0.85 * envv)[:, None]
hab = envv > 0.5
print('voz sobre el fondo: +%.1f dB' % (20 * np.log10(np.sqrt((voz[hab] ** 2).mean()) / np.sqrt((bajo[hab] ** 2).mean()))))
fin = bajo + voz
fin *= np.clip(np.interp(t, [0, 0.4, DUR - 1.5, DUR], [0, 1, 1, 0]), 0, 1)[:, None]
escribir(sys.argv[1], fin)
with open(sys.argv[2], 'w', encoding='utf-8') as f_:
    for i_, (a_, b_, tx) in enumerate(srt, 1): f_.write(f'{i_}\n{tc(a_)} --> {tc(b_)}\n{tx}\n\n')
# TARJETA final (7 s): piano grave y lluvia que se apaga
nt = int(7.0 * SR); tt = np.arange(nt) / SR
tit = np.zeros((nt, 2))
tit += est(lp(P._ruido_banda(nt, rng, 1800, 9000), 6500) * 0.12 * np.interp(tt, [0, 5, 7], [1, 0.6, 0]))
m2 = MN.tema(nt, np.random.default_rng(5), [{"t0": 0.0, "t1": 7.0, "capas": ["nota_sola", "pad"]}], 1.0) * 0.55
tit += m2 * np.interp(tt, [0, 0.8, 5.5, 7], [0, 1, 1, 0])[:, None]
escribir(sys.argv[3], tit)
print('PUENTE', DUR, 's, TÍTULO 7 s')
