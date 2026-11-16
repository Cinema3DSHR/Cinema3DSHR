"""Sonidos del propio Dream Rally (audio/biblioteca/dream_rally, copiados de Rally-Sim-movile godot/game/audio/samples):
chirrido de neumáticos, sirena, viento. El motor usa `estudio.audio.tren.motor_rpm` (ya existe, con la clase
"deportivo" para autos de calle/competición y "diesel" para camiones), con las rpm reales de la física.
"""
from __future__ import annotations
import numpy as np
from estudio import config

SR = 48000
DIR = config.RAIZ / "audio" / "biblioteca" / "dream_rally"
_CACHE: dict[str, np.ndarray] = {}


def _wav(nombre: str) -> np.ndarray:
    if nombre not in _CACHE:
        from estudio.audio.procedural import _decodificar
        _CACHE[nombre] = _decodificar(DIR / f"{nombre}.mp3")
    return _CACHE[nombre]


def _tile(x: np.ndarray, n: int) -> np.ndarray:
    return np.tile(x, n // len(x) + 2)[:n]


def _env(n: int, ataque_s: float, relajo_s: float) -> np.ndarray:
    a, r = int(ataque_s * SR), int(relajo_s * SR)
    e = np.ones(n)
    if a > 0:
        e[:min(a, n)] = np.linspace(0, 1, min(a, n))
    if r > 0 and n > r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def derrape(n: int, rng, ventanas: list[tuple[float, float]], volumen: float = 0.8) -> np.ndarray:
    """Chirrido de neumáticos (squeal.wav del juego) en cada ventana [t0, t1] de derrape, con un ataque y un relajo
    suaves (no entra ni sale de golpe) y un leve vaivén de tono (el auto corrige el volante)."""
    base = _wav("squeal")
    mezcla = np.zeros((n, 2))
    for t0, t1 in ventanas:
        dur = max(0.15, t1 - t0)
        m = min(n, int((t0 + dur) * SR)) - max(0, int(t0 * SR))
        if m <= 0:
            continue
        seg = _tile(base, m)
        # vaivén de tono (±6 %): se re-muestrea con un índice que oscila despacio
        idx = np.arange(m) + np.sin(np.arange(m) / SR * 2 * np.pi * 0.7) * SR * 0.02
        idx = np.clip(idx, 0, len(seg) - 1)
        seg = np.interp(idx, np.arange(len(seg)), seg)
        seg = seg * _env(m, 0.08, 0.18) * volumen
        a = max(0, int(t0 * SR))
        b = a + m
        mezcla[a:b, 0] += seg
        mezcla[a:b, 1] += seg
    return mezcla


def sirena(n: int, pistas: dict, movil: str, t0: float, t1: float, volumen: float = 0.75) -> np.ndarray:
    """Sirena del móvil (siren.wav del juego), espacializada por la posición de `movil`; entra y sale con un fundido
    corto para que no aparezca ni desaparezca de golpe."""
    from estudio.audio.procedural import _espacial, _a_estereo
    base = _wav("siren")
    a, b = max(0, int(t0 * SR)), min(n, int(t1 * SR))
    m = b - a
    if m <= 0:
        return np.zeros((n, 2))
    seg = _tile(base, m) * _env(m, 0.4, 0.6) * volumen
    mono = np.zeros(n)
    mono[a:b] = seg
    pos = [f[:3] for f in pistas["moviles"][movil]]
    g, pan = _espacial(pistas, pos, n)
    return _a_estereo(mono, np.clip(g * 2.2, 0.2, 1.0), pan)


def viento(n: int, rng, pistas: dict, movil: str, volumen: float = 0.12) -> np.ndarray:
    """Viento de conducir rápido (wind.wav del juego), con el nivel atado a la velocidad del móvil."""
    from estudio.audio.procedural import _interp_por_frame
    base = _wav("wind")
    fps = pistas["fps"]
    v = _interp_por_frame(np.abs([x[3] for x in pistas["moviles"][movil]]), n, fps)
    seg = _tile(base, n)
    k = np.clip((v - 4.0) / 26.0, 0.0, 1.0) ** 1.4
    mono = seg * k * volumen
    return np.stack([mono, mono], axis=1)


def turbo(n: int, pistas: dict, movil: str, volumen: float = 0.35) -> np.ndarray:
    """Silbido del turbo (turbo.wav del juego): como en Dream Rally, sólo carga mientras el motor acelera fuerte
    (rpm subiendo), no todo el tiempo ni atado a la rpm en sí."""
    from estudio.audio.procedural import _espacial, _a_estereo, _interp_por_frame
    rpm = (pistas.get("rpm") or {}).get(movil)
    if not rpm:
        return np.zeros((n, 2))
    base = _wav("turbo")
    fps = pistas["fps"]
    rpm_m = _interp_por_frame(np.asarray(rpm, dtype=float), n, fps)
    carga = np.clip(np.gradient(rpm_m) * fps / 4000.0, 0.0, 1.0) ** 1.5
    mono = _tile(base, n) * carga * volumen
    pos = [f[:3] for f in pistas["moviles"][movil]]
    g, pan = _espacial(pistas, pos, n)
    return _a_estereo(mono, np.clip(g * 1.8, 0.0, 1.0), pan)


def rotor_helicoptero(n: int, pistas: dict, movil: str, t0: float, volumen: float = 0.5) -> np.ndarray:
    """Aleteo del rotor (síntesis simple: una onda moduladora de baja frecuencia sobre ruido filtrado), desde que el
    helicóptero entra en escena, espacializado por su posición."""
    from estudio.audio.procedural import _espacial, _a_estereo, _ruido_banda
    fps = pistas["fps"]
    a = max(0, int(t0 * fps) * SR // fps)
    tt = np.arange(n) / SR
    chop = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 9.0 * tt))        # ~9 palazos/s (pala principal)
    cuerpo = _ruido_banda(n, np.random.default_rng(7), 60, 600) * 0.6 + _ruido_banda(n, np.random.default_rng(9), 600, 2500) * 0.3
    mono = cuerpo * (0.35 + 0.65 * chop) * volumen
    mono[: max(0, a)] = 0.0
    fade = int(0.6 * SR)
    if a + fade < n:
        mono[a:a + fade] *= np.linspace(0, 1, fade)
    pos = [f[:3] for f in pistas["moviles"][movil]]
    g, pan = _espacial(pistas, pos, n)
    return _a_estereo(mono, np.clip(g * 1.6, 0.0, 1.0), pan)
