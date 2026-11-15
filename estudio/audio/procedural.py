"""Sonido procedural (sin servicios pagos): ambientes, motor de vehículos y mecanismos, sincronizados con la escena.

Usa las PISTAS que exporta el director (posición de cada cámara y de cada móvil por fotograma), así el motor sube de
tono con la velocidad real del auto y el volumen y el paneo dependen de la distancia a la cámara de cada toma.
Sólo necesita numpy. Todo lo generado acá es propio (licencia del estudio) y se puede guardar en la biblioteca.

Cuando se autorice ElevenLabs (ver docs/AUDIO.md) los diálogos, voces y efectos especiales vienen de ahí;
este módulo sigue cubriendo ambientes y mecanismos baratos de sintetizar.
"""
from __future__ import annotations
import json
import math
import wave
from pathlib import Path
import numpy as np

SR = 48000


def _ruido_color(n, rng, pendiente_db_oct=-3.0, f_baja=20.0, f_alta=20000.0):
    """Ruido con pendiente espectral (−3 dB/oct rosa, −6 marrón) y banda limitada, filtrado por FFT."""
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = 1.0
    g = (f / 1000.0) ** (pendiente_db_oct / 6.0206)
    g[(f < f_baja) | (f > f_alta)] = 0.0
    y = np.fft.irfft(X * g, n)
    return y / (np.abs(y).max() + 1e-9)


def _env(n, ataque_s, relajo_s):
    e = np.ones(n)
    a, r = int(ataque_s * SR), int(relajo_s * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def _interp_por_frame(valores_por_frame, n, fps):
    """Lleva una curva por fotograma a una curva por muestra."""
    v = np.asarray(valores_por_frame, dtype=float)
    t_f = np.arange(len(v)) / fps
    t_s = np.arange(n) / SR
    return np.interp(t_s, t_f, v)


def _espacial(pistas, fuente_pos_por_frame, n):
    """Ganancia y paneo (−1..1) respecto de la cámara activa en cada fotograma."""
    fps = pistas["fps"]
    cam = pistas["camara_activa"]  # lista por fotograma: [x, y, z, dx, dy] (posición y derecha de cámara)
    g, pan = [], []
    for i, c in enumerate(cam):
        p = fuente_pos_por_frame[min(i, len(fuente_pos_por_frame) - 1)]
        d = math.dist(p, c[:3])
        g.append(1.0 / (1.0 + d / 6.0))
        rx, ry = c[3], c[4]
        lat = ((p[0] - c[0]) * rx + (p[1] - c[1]) * ry) / (d + 1e-6)
        pan.append(max(-1.0, min(1.0, lat)))
    return _interp_por_frame(g, n, fps), _interp_por_frame(pan, n, fps)


def _a_estereo(mono, ganancia, pan):
    izq = mono * ganancia * np.sqrt(0.5 * (1 - pan))
    der = mono * ganancia * np.sqrt(0.5 * (1 + pan))
    return np.stack([izq, der], axis=1)


# ------------------------------------------------------------------------------------------- generadores

def ambiente_noche_suburbio(n, rng):
    viento = _ruido_color(n, rng, -6, 40, 1200) * 0.35
    mod = 0.6 + 0.4 * np.sin(np.arange(n) / SR * 2 * np.pi * 0.07 + rng.uniform(0, 6))
    viento *= mod
    ciudad = _ruido_color(n, rng, -4.5, 30, 400) * 0.12  # rumor lejano de la ciudad
    grillos = np.zeros(n)
    t = 0.0
    while t < n / SR:
        f0 = rng.uniform(4200, 4900)
        for k in range(rng.integers(2, 5)):  # ráfaga de chirridos
            ini = int((t + k * 0.06) * SR)
            dur = int(0.035 * SR)
            if ini + dur >= n:
                break
            tt = np.arange(dur) / SR
            grillos[ini:ini + dur] += np.sin(2 * np.pi * f0 * tt) * np.hanning(dur) * rng.uniform(0.02, 0.06)
        t += rng.uniform(0.35, 1.4)
    mono_bajo = viento + ciudad
    st = np.stack([mono_bajo * 0.9 + grillos * 0.8, mono_bajo * 0.9 + np.roll(grillos, 900) * 0.8], axis=1)
    return st


def ambiente_dia_suburbio(n, rng):
    """Mediodía de barrio residencial: brisa, rumor lejano de tránsito y pájaros (trinos de barrido rápido)."""
    viento = _ruido_color(n, rng, -6, 40, 1500) * 0.3
    viento *= 0.65 + 0.35 * np.sin(np.arange(n) / SR * 2 * np.pi * 0.09 + rng.uniform(0, 6))
    transito = _ruido_color(n, rng, -4.5, 30, 350) * 0.10
    aves = np.zeros(n)
    t = rng.uniform(0.2, 1.0)
    while t < n / SR - 0.5:
        f0 = rng.uniform(2600, 4200)
        for k in range(int(rng.integers(2, 6))):      # trino: notas cortas con barrido descendente
            ini = int((t + k * 0.11) * SR)
            dur = int(0.07 * SR)
            if ini + dur >= n:
                break
            tt = np.arange(dur) / SR
            fi = f0 * (1.0 - 0.18 * tt / 0.07)
            fase = 2 * np.pi * np.cumsum(fi) / SR
            aves[ini:ini + dur] += np.sin(fase) * np.hanning(dur) * rng.uniform(0.03, 0.08)
        t += rng.uniform(1.5, 5.0)
    base = viento + transito
    return np.stack([base + aves * 0.9, base + np.roll(aves, 2400) * 0.9], axis=1)


def motor(pistas, movil, n, rng):
    fps = pistas["fps"]
    m = pistas["moviles"][movil]
    vel = np.abs(np.array([x[3] for x in m]))
    v = _interp_por_frame(vel, n, fps)
    rpm_hz = 28 + v * 5.5  # ralentí ~28 Hz de encendido; sube con la velocidad
    fase = np.cumsum(2 * np.pi * rpm_hz / SR)
    tono = (np.sin(fase) * 0.6 + np.sin(2 * fase) * 0.35 + np.sin(3 * fase + 0.5) * 0.2 + np.sin(0.5 * fase) * 0.25)
    aspereza = _ruido_color(n, rng, -3, 60, 2500) * (0.08 + 0.02 * v)
    carga = 0.45 + np.clip(v / 14.0, 0, 1) * 0.55
    rodado = _ruido_color(n, rng, -2, 300, 6000) * np.clip(v / 10.0, 0, 1) * 0.35  # gomas sobre asfalto mojado
    mono = (tono * 0.5 + aspereza) * carga + rodado
    g, pan = _espacial(pistas, [x[:3] for x in m], n)
    return _a_estereo(mono, g * 1.4, pan)


def mecanismo(pistas, n, rng, inicio_s, duracion_s, pos, tipo="porton_motor"):
    a, b = int(inicio_s * SR), int((inicio_s + duracion_s) * SR)
    b = min(b, n)
    seg = b - a
    out = np.zeros(n)
    if seg <= 0:
        return np.zeros((n, 2))
    tt = np.arange(seg) / SR
    if tipo == "porton_motor":
        zumbido = np.sin(2 * np.pi * 110 * tt) * 0.25 + np.sin(2 * np.pi * 220 * tt) * 0.1
        roce = _ruido_color(seg, rng, -3, 200, 3000) * 0.15
        golpe = np.zeros(seg)
        g_n = int(0.12 * SR)
        golpe[-g_n:] = _ruido_color(g_n, rng, -6, 40, 800) * np.linspace(1, 0, g_n) * 0.8
        out[a:b] = (zumbido + roce) * _env(seg, 0.15, 0.25) + golpe
    else:  # porton_garaje: traqueteo de los paneles al subir
        trq = np.zeros(seg)
        for k in np.arange(0, duracion_s, 0.11):
            i = int(k * SR)
            d = min(int(0.03 * SR), seg - i)
            if d > 0:
                trq[i:i + d] += rng.standard_normal(d) * np.linspace(1, 0, d) * 0.4
        motor_ = np.sin(2 * np.pi * 90 * tt) * 0.2
        out[a:b] = (trq + motor_ + _ruido_color(seg, rng, -6, 50, 600) * 0.15) * _env(seg, 0.1, 0.3)
    fpos = [pos] * len(pistas["camara_activa"])
    g, pan = _espacial(pistas, fpos, n)
    return _a_estereo(out, g * 2.5, pan)


def ambiente_estadio(n, rng):
    """Murmullo de multitud: ruido en banda de voz con oleadas lentas y algún grito lejano."""
    base = _ruido_color(n, rng, -2.5, 180, 2600) * 0.45
    ola = 0.7 + 0.3 * np.sin(np.arange(n) / SR * 2 * np.pi * 0.11 + rng.uniform(0, 6))
    grave = _ruido_color(n, rng, -6, 40, 250) * 0.25
    st = np.stack([base * ola + grave, np.roll(base, 2400) * ola + grave], axis=1)
    return st


def ovacion(n, rng, t0, dur=5.0):
    out = np.zeros((n, 2))
    a = int(t0 * SR)
    b = min(n, a + int(dur * SR))
    if b <= a:
        return out
    seg = b - a
    x = _ruido_color(seg, rng, -1.5, 200, 5000)
    env = np.minimum(1, np.arange(seg) / (0.25 * SR)) * np.exp(-np.arange(seg) / (dur * 0.55 * SR))
    out[a:b, 0] = x * env * 1.6
    out[a:b, 1] = np.roll(x, 1200) * env * 1.6
    return out


def golpe(n, rng, t0, tipo="patada"):
    out = np.zeros(n)
    a = int(t0 * SR)
    if tipo == "patada":
        d = int(0.18 * SR)
        tt = np.arange(d) / SR
        s = np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 28) + rng.standard_normal(d) * np.exp(-tt * 120) * 0.6
    else:  # red: roce de la pelota contra la red
        d = int(0.6 * SR)
        tt = np.arange(d) / SR
        s = _ruido_color(d, rng, -1, 800, 7000) * np.exp(-tt * 6) * 0.7
    b = min(n, a + len(s))
    if b > a:
        out[a:b] = s[: b - a]
    return np.stack([out, out], axis=1)


def _decodificar(ruta: Path) -> np.ndarray:
    """MP3/OGG/WAV → mono float32 a 48 kHz (con ffmpeg)."""
    import subprocess
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").astype(np.float64)


def audio_de_biblioteca(pistas, ev, n, rng=None):
    """Coloca un audio ya generado (voz, efecto o música de la biblioteca) en su momento; si trae `movil`, la
    ganancia y el paneo siguen a ese personaje o vehículo respecto de la cámara activa."""
    from estudio.audio import elevenlabs as EL
    x = _decodificar(EL.ruta_en_biblioteca(ev))
    if ev["tipo"] in ("efecto", "musica") and np.abs(x).max() > 1e-6:
        # los efectos generados salen a niveles muy dispares (medido: pico −36 dB): se llevan a −6 dB de pico
        x = x / np.abs(x).max() * 0.5
    x = x * float(ev.get("volumen", 1.0))
    a = int(ev.get("inicio_s", 0.0) * SR)
    b = min(n, a + len(x))
    if b <= a:
        return np.zeros((n, 2))
    mono = np.zeros(n)
    mono[a:b] = x[: b - a]
    if ev.get("movil") and ev["movil"] in pistas["moviles"]:
        pos = [f[:3] for f in pistas["moviles"][ev["movil"]]]
        g, pan = _espacial(pistas, pos, n)
        return _a_estereo(mono, np.clip(g * 3.0, 0.15, 1.0), pan)
    return np.stack([mono, mono], axis=1) * 0.9   # sin posición: voz en off / música / radio


def generar(manifiesto: dict, pistas: dict, salida: Path) -> Path:
    """Genera la mezcla de efectos+ambiente de la escena (WAV 48 kHz estéreo)."""
    son = manifiesto.get("sonido", {})
    rng = np.random.default_rng(sum(map(ord, manifiesto["id"])) + manifiesto.get("version", 1))
    n = int(manifiesto["duracion_s"] * SR)
    mezcla = np.zeros((n, 2))
    amb = son.get("ambiente")
    if amb == "noche_suburbio":
        mezcla += ambiente_noche_suburbio(n, rng) * 0.5
    elif amb == "dia_suburbio":
        mezcla += ambiente_dia_suburbio(n, rng) * 0.6
    elif amb == "estadio":
        mezcla += ambiente_estadio(n, rng) * 0.35
    for ev in pistas.get("eventos", []):
        if ev["tipo"] == "patada":
            mezcla += golpe(n, rng, ev["t"], "patada") * 0.9
        elif ev["tipo"] == "gol":
            mezcla += golpe(n, rng, ev["t"], "red") * 0.5
            mezcla += ovacion(n, rng, ev["t"] + 0.15, 6.0) * 0.8
    for ev in son.get("eventos", []):
        if ev["tipo"] in ("voz", "efecto", "musica"):
            mezcla += audio_de_biblioteca(pistas, ev, n)
        elif ev["tipo"] == "motor":
            mezcla += motor(pistas, ev["movil"], n, rng) * ev.get("volumen", 1.0)
        elif ev["tipo"] in ("porton_motor", "porton_garaje"):
            pos = pistas["anclas"][ev["ancla"]]
            mezcla += mecanismo(pistas, n, rng, ev["inicio_s"], ev["duracion_s"], pos, ev["tipo"]) * ev.get("volumen", 1.0)
    pico = np.abs(mezcla).max() + 1e-9
    mezcla = mezcla / pico * 0.89
    salida.parent.mkdir(parents=True, exist_ok=True)
    pcm = (mezcla * 32767).astype("<i2")
    with wave.open(str(salida), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return salida


if __name__ == "__main__":
    import sys
    m = json.loads(Path(sys.argv[1]).read_text())
    p = json.loads(Path(sys.argv[2]).read_text())
    print(generar(m, p, Path(sys.argv[3])))
