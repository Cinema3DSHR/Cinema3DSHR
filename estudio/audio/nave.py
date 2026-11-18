"""Ambiente de la nave de «A la deriva» (procedural, sin servicios pagos): ventilación, zumbido grave del casco,
vibración baja, pulsos electrónicos discretos y soniditos suaves de consola. Silencioso y aislado."""
from __future__ import annotations
import numpy as np

from estudio.audio.procedural import SR, _ruido_color


def ambiente_interior(n: int, rng) -> np.ndarray:
    t = np.arange(n) / SR
    # ventilación: ruido rosa en banda media, que «respira» muy lento
    vent = _ruido_color(n, rng, -3.0, 180, 2600) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t + 1.3))
    # zumbido del casco: 50 Hz con armónicos y un batido lento
    hum = (np.sin(2 * np.pi * 50 * t) * 0.6 + np.sin(2 * np.pi * 100.4 * t) * 0.25 + np.sin(2 * np.pi * 150 * t) * 0.1)
    hum *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.11 * t)
    # vibración baja (motores apagados, sistemas vivos)
    vib = _ruido_color(n, rng, -6.0, 20, 90)
    mono = vent * 0.28 + hum * 0.10 + vib * 0.35
    # pulsos electrónicos discretos y sonidos suaves de consola
    k = 0.0
    while True:
        k += rng.uniform(2.5, 6.0)
        i0 = int(k * SR)
        if i0 >= n - SR:
            break
        f = rng.choice([880.0, 1320.0, 1760.0, 660.0])
        dur = rng.uniform(0.05, 0.14)
        m = int(dur * SR)
        tt = np.arange(m) / SR
        tono = np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur * 0.35))
        if rng.random() < 0.35:                               # doble pip
            tono = np.concatenate([tono, np.zeros(int(0.08 * SR)), tono * 0.7])
        j1 = min(n, i0 + len(tono))
        mono[i0:j1] += tono[:j1 - i0] * rng.uniform(0.03, 0.06)
    est = np.stack([mono, mono], 1)
    est[:, 1] = np.roll(est[:, 1], int(0.011 * SR))            # un poco de ancho estéreo
    return est / (np.abs(est).max() + 1e-9)
