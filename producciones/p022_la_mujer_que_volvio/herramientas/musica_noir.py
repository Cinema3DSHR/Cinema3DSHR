"""Música original neo-noir lenta (estilo «Max Payne» en espíritu: piano solo, grave, con mucha reverberación y cuerdas bajas que crecen; NO copia ninguna pieza).
Re menor, 56 BPM, progresión Dm – B♭ – Gm – A con melodía de notas largas. Síntesis: piano con inarmonicidad y golpe de martillo, cello/viola con vibrato lento,
pad de armónicos, reverberación de sala por convolución. Uso: from musica_noir import tema"""
import numpy as np
SR = 48000
BPM = 56.0; BEAT = 60.0 / BPM
def mid2f(m): return 440.0 * 2 ** ((m - 69) / 12.0)

def _piano(f, dur, vel, rng):
    m = int(min(dur + 3.0, 7.0) * SR); k = np.arange(m) / SR
    B = 0.00035; s = np.zeros(m)
    for h in range(1, 9):
        fh = f * h * np.sqrt(1 + B * h * h)
        if fh > 9000: break
        dec = (2.2 / (1 + 0.55 * h)) * (1.0 if f < 300 else 0.8) + 0.4
        s += np.sin(2 * np.pi * fh * k + rng.uniform(0, 0.4)) / h ** 1.15 * np.exp(-k / dec) * (1.0 if h < 4 else 0.7)
    mar = rng.standard_normal(m) * np.exp(-k / 0.012) * 0.04 * vel                               # golpe del martillo
    s = s * np.minimum(k / 0.004, 1.0) + mar
    s *= np.minimum(1.0, np.maximum(0.0, (dur + 2.5 - k) / 1.2)) if dur < 3 else 1.0
    return s * vel

def _cuerda(f, dur, g, rng, vib=4.6):
    m = int(dur * SR); k = np.arange(m) / SR
    fi = f * (1 + 0.0035 * np.sin(2 * np.pi * vib * k) * np.minimum(k / 1.5, 1.0))
    ph = 2 * np.pi * np.cumsum(fi) / SR
    s = sum(np.sin(ph * h + rng.uniform(0, 6.28)) / h ** 1.2 for h in range(1, 8))
    return s * np.minimum(k / 2.6, 1.0) * np.minimum((dur - k) / 3.2, 1.0) * g

def _reverb(x, rng, rt60=3.4, mezcla=0.38):
    m = int(rt60 * 1.1 * SR); k = np.arange(m) / SR
    ir = rng.standard_normal((m, 2)) * np.exp(-6.9 * k / rt60)[:, None]
    for c in range(2):                                                                         # la cola se oscurece (absorción del aire)
        X = np.fft.rfft(ir[:, c]); f = np.fft.rfftfreq(m, 1 / SR); X *= 1 / (1 + (f / 2600) ** 2); ir[:, c] = np.fft.irfft(X, m)
    ir[: int(0.012 * SR)] = 0
    N = len(x) + m
    out = np.zeros((len(x), 2))
    for c in range(2):
        y = np.fft.irfft(np.fft.rfft(x[:, c], N) * np.fft.rfft(ir[:, c], N), N)[: len(x)]
        out[:, c] = y
    out *= (np.abs(x).max() / (np.abs(out).max() + 1e-9)) * 0.9
    return x * (1 - mezcla * 0.6) + out * mezcla

# progresión (cada acorde = 8 pulsos): raíz grave, tríada, melodía [(pulso, midi, duración en pulsos, fuerza)]
ACORDES = [
    {"raiz": 38, "tri": (50, 57, 62), "mel": [(0, 69, 3, 0.9), (3, 65, 1, 0.7), (4, 64, 2, 0.75), (6, 62, 2, 0.8)]},          # Dm : A F E D
    {"raiz": 34, "tri": (46, 53, 58), "mel": [(0, 62, 2, 0.8), (2, 65, 2, 0.7), (4, 70, 3, 0.9), (7, 69, 1, 0.65)]},          # B♭ : D F B♭ A
    {"raiz": 43, "tri": (55, 58, 62), "mel": [(0, 67, 3, 0.85), (3, 65, 1, 0.7), (4, 62, 2, 0.75), (6, 58, 2, 0.7)]},          # Gm : G F D B♭
    {"raiz": 45, "tri": (57, 61, 64), "mel": [(0, 64, 2, 0.8), (2, 61, 2, 0.7), (4, 69, 4, 0.9)]},                             # A  : E C♯ A
]

def tema(n, rng, secciones, vol=1.0):
    """secciones: lista de dicts {t0, t1, capas:[...]} con capas entre 'piano', 'melodia', 'cuerdas', 'pad', 'nota_sola'. Devuelve estéreo (n, 2) ya reverberado."""
    out = np.zeros((n, 2))
    def poner(x, t0, pan=0.0, g=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0: return
        seg = x[: n - i]; out[i:i + len(seg), 0] += seg * g * np.sqrt(0.5 * (1 - pan)); out[i:i + len(seg), 1] += seg * g * np.sqrt(0.5 * (1 + pan))
    for sec in secciones:
        t0, t1, capas = sec['t0'], sec['t1'], sec['capas']
        bar = 8 * BEAT; k = 0; t = t0
        while t < t1 - 0.5:
            ac = ACORDES[k % 4]
            if 'nota_sola' in capas:                                                       # unas pocas notas altas, aisladas, con aire entre ellas
                for pul, midi, d, v in ac['mel'][:2]:
                    poner(_piano(mid2f(midi + 12), d * BEAT, 0.35 * v, rng), t + pul * BEAT, 0.25, 0.8)
            if 'piano' in capas:                                                           # raíz grave + tríada arpegiada muy lenta
                poner(_piano(mid2f(ac['raiz']), 8 * BEAT, 0.9, rng), t, -0.2, 0.9)
                for j, m_ in enumerate(ac['tri']):
                    poner(_piano(mid2f(m_), 3 * BEAT, 0.42, rng), t + (0.0 + 0.5 * j) * BEAT * 1.0 + 1.0 * BEAT, -0.1 + 0.1 * j, 0.7)
            if 'melodia' in capas:
                for pul, midi, d, v in ac['mel']:
                    poner(_piano(mid2f(midi), d * BEAT, 0.95 * v, rng), t + pul * BEAT, 0.12, 1.0)
            if 'cuerdas' in capas:
                poner(_cuerda(mid2f(ac['raiz'] + 12), bar + 3.0, 0.20, rng), t, -0.35, 1.0)                  # cello
                poner(_cuerda(mid2f(ac['tri'][0]), bar + 3.0, 0.10, rng, 5.0), t, 0.35, 1.0)                  # viola
            if 'pad' in capas:
                poner(_cuerda(mid2f(ac['tri'][2] + 12), bar + 3.5, 0.05, rng, 3.8), t, 0.0, 1.0)              # armónico agudo, casi inaudible
            t += bar; k += 1
    return _reverb(out * vol, rng)

if __name__ == '__main__':
    import sys, wave
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    rng = np.random.default_rng(31)
    nn = int(dur * SR)
    sec = [{"t0": 0.0, "t1": 18.0, "capas": ["nota_sola", "pad"]}, {"t0": 18.0, "t1": 42.0, "capas": ["piano", "melodia", "pad"]}, {"t0": 42.0, "t1": dur - 6, "capas": ["piano", "melodia", "cuerdas", "pad"]}]
    y = tema(nn, rng, sec)
    y *= np.clip(np.interp(np.arange(nn) / SR, [0, 2, dur - 6, dur], [0, 1, 1, 0]), 0, 1)[:, None]
    y *= 0.9 / (np.abs(y).max() + 1e-9)
    with wave.open(sys.argv[1], 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype('<i2').tobytes())
    print('LISTO', sys.argv[1], dur, 's')
