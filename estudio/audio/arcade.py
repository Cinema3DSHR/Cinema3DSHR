"""Sonido de los minijuegos de Free Kick Swipe con los audios del propio juego (audio/biblioteca/free_kick_swipe,
copiados de s4muy3ni-lang/Free-Kick-Swipe assets/audio): patada, pique, tablero, botón, trampilla, público.

`duelo(pistas, n)` pone cada evento del duelo de «Al vacío» (los que registra estudio/escenarios/al_vacio.py en
tiempo de la ESCENA) en su lugar de la PELÍCULA (con cámara lenta, `mapa_tiempo`), y el público del juego de fondo.
"""
from __future__ import annotations
import numpy as np
from estudio import config

SR = 48000
DIR = config.RAIZ / "audio" / "biblioteca" / "free_kick_swipe"
_CACHE: dict[str, np.ndarray] = {}


def _wav(nombre: str) -> np.ndarray:
    if nombre not in _CACHE:
        from estudio.audio.procedural import _decodificar
        _CACHE[nombre] = _decodificar(DIR / f"{nombre}.mp3")
    return _CACHE[nombre]


def a_pelicula(mapa, t: float) -> float:
    """Tiempo de la escena → tiempo de la película (inverso del mapa [[película, escena], …])."""
    if not mapa:
        return t
    for (p0, e0), (p1, e1) in zip(mapa, mapa[1:]):
        if e0 <= t <= e1:
            return p0 + (p1 - p0) * (t - e0) / max(1e-9, e1 - e0)
    return t + (mapa[-1][0] - mapa[-1][1])


def _poner(mezcla, x, t, vol, pan, estirar: float = 1.0):
    if estirar != 1.0:                      # cámara lenta: el sonido se estira (más grave), como en el cine
        idx = np.arange(0, len(x) - 1, 1.0 / estirar)
        x = np.interp(idx, np.arange(len(x)), x)
    a = int(t * SR)
    if a >= len(mezcla) or a + len(x) <= 0:
        return
    b = min(len(mezcla), a + len(x))
    seg = x[: b - a] * vol
    mezcla[a:b, 0] += seg * (1 - max(0.0, pan))
    mezcla[a:b, 1] += seg * (1 + min(0.0, pan))


def _factor(mapa, t):
    """Cuánto se estira la escena en el instante t (1 = normal)."""
    if not mapa:
        return 1.0
    for (p0, e0), (p1, e1) in zip(mapa, mapa[1:]):
        if e0 <= t <= e1:
            return (p1 - p0) / max(1e-9, e1 - e0)
    return 1.0


def alarma(dur: float = 2.2) -> np.ndarray:
    """Sirena de alerta de dos tonos (se abre la compuerta): cuadrada suavizada que alterna 880 / 660 Hz cada 0,18 s."""
    tt = np.arange(int(dur * SR)) / SR
    f = np.where((tt // 0.18) % 2 == 0, 880.0, 660.0)
    fase = np.cumsum(2 * np.pi * f / SR)
    x = np.tanh(3.0 * np.sin(fase)) * 0.6 + np.sin(2 * fase) * 0.15
    env = np.minimum(1.0, tt / 0.02) * np.clip((dur - tt) / 0.3, 0, 1)
    return x * env * 0.5


def duelo(pistas: dict, n: int, rng, publico: float = 0.35) -> np.ndarray:
    mezcla = np.zeros((n, 2))
    mapa = pistas.get("mapa_tiempo")
    # público de fondo: el bucle del juego repetido con desfasaje en cada canal
    loop = _wav("crowd_loop")
    for canal, off in ((0, 0), (1, len(loop) // 3)):
        x = np.tile(np.roll(loop, off), n // len(loop) + 2)[:n]
        mezcla[:, canal] += x * publico
    pan_lado = {0: -0.35, 1: 0.35}
    for ev in pistas.get("eventos", []):
        t = a_pelicula(mapa, float(ev["t"]))
        k = _factor(mapa, float(ev["t"]))
        pan = pan_lado.get(ev.get("lado"), 0.0)
        tipo = ev["tipo"]
        if tipo == "patada":
            _poner(mezcla, _wav("kick_hard"), t, 1.0, pan, k)
        elif tipo == "pique":
            _poner(mezcla, _wav("bounce"), t, min(1.0, 0.25 + 0.08 * float(ev.get("impacto", 3))), pan, k)
        elif tipo == "tablero":
            _poner(mezcla, _wav("post"), t, 0.9, pan, k)
            _poner(mezcla, _wav("ooh"), t + 0.15 * k, 0.9, 0.0)
        elif tipo == "roce":
            _poner(mezcla, _wav("mech_click"), t, 0.8, pan, k)
            _poner(mezcla, _wav("ooh"), t + 0.1 * k, 0.9, 0.0)
        elif tipo == "boton":
            _poner(mezcla, _wav("mech_release"), t, 1.0, pan, k)
            _poner(mezcla, _wav("mech_gate"), t + 0.05 * k, 1.0, pan, k)
            _poner(mezcla, alarma(), t + 0.02, 0.55, pan)                 # alerta: se abre la compuerta
        elif tipo == "caida":                                              # el público estalla
            _poner(mezcla, _wav("cheer"), t + 0.15 * k, 1.4, 0.0)
            _poner(mezcla, _wav("cheer"), t + 0.7 * k, 1.0, -0.5)
            _poner(mezcla, _wav("cheer"), t + 1.1 * k, 0.8, 0.5)
        elif tipo == "subida":
            _poner(mezcla, _wav("mech_gate"), t, 0.6, pan)
    return mezcla
