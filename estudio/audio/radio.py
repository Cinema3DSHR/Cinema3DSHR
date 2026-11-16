"""Filtro de radio policial: lo que suena una transmisión real, no una voz limpia de estudio.

`filtro(mono, rng)` aplica banda angosta (300–3400 Hz, como un equipo VHF/UHF), compresión fuerte (satura las
consonantes), ruido de estática de fondo, 1–2 cortes breves de señal y un «clic» de apretar/soltar el botón de
transmisión al principio y al final. Sólo se usa en los diálogos de radio (tipo "voz_radio" en procedural.generar);
la música y los efectos quedan limpios.
"""
from __future__ import annotations
import numpy as np

SR = 48000


def _pasa_banda(x: np.ndarray, f_lo: float, f_hi: float) -> np.ndarray:
    """Filtro pasa-banda por FFT (sin scipy): anula todo lo que no esté entre f_lo y f_hi."""
    n = len(x)
    esp = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    # bordes suaves (medio ciclo de coseno) para no sonar como una puerta brusca
    ganancia = np.ones(len(f))
    ancho = 120.0
    ganancia *= np.clip((f - (f_lo - ancho)) / ancho, 0, 1)
    ganancia *= np.clip(((f_hi + ancho) - f) / ancho, 0, 1)
    return np.fft.irfft(esp * ganancia, n)


def _clic(dur_s: float, rng) -> np.ndarray:
    n = int(dur_s * SR)
    ruido = rng.standard_normal(n) * 0.5
    env = np.exp(-np.arange(n) / (SR * 0.01))
    return ruido * env


def filtro(mono: np.ndarray, rng) -> np.ndarray:
    n = len(mono)
    x = _pasa_banda(mono, 320.0, 3100.0)
    pico = np.abs(x).max()
    if pico > 1e-6:
        x = x / pico
    # compresión/saturación (las radios recortan los picos: suena "crujiente")
    x = np.tanh(x * 3.2) * 0.72
    # estática de fondo (ruido de banda, parejo durante toda la transmisión)
    estatica = _pasa_banda(rng.standard_normal(n), 400.0, 3000.0)
    estatica = estatica / max(1e-6, np.abs(estatica).max()) * 0.05
    x = x + estatica
    # 1–2 cortes breves de señal (el equipo pierde el enlace medio segundo)
    for _ in range(rng.integers(0, 2) + 1):
        t0 = rng.uniform(0.15, max(0.16, n / SR - 0.25))
        dur = rng.uniform(0.04, 0.12)
        a, b = int(t0 * SR), int((t0 + dur) * SR)
        if b > a:
            x[a:min(b, n)] *= 0.08
    # pulsación de transmisión: clic al apretar y al soltar el botón
    clic = _clic(0.04, rng)
    x[: len(clic)] += clic * 0.6
    cola = _clic(0.05, rng)
    x[max(0, n - len(cola)):] += cola[: min(len(cola), n)] * 0.5
    # fundido muy corto en los bordes (evita un "clac" al pegar el clip en la mezcla)
    borde = int(0.01 * SR)
    if borde * 2 < n:
        x[:borde] *= np.linspace(0, 1, borde)
        x[-borde:] *= np.linspace(1, 0, borde)
    return np.clip(x, -1.0, 1.0) * 0.85
