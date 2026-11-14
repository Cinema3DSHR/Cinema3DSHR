"""ElevenLabs: voces (TTS), efectos de sonido y música, con caché PERMANENTE, tope de gasto y registro de uso.

Credencial: nunca está en el repositorio. En la sesión de Claude la inyecta el proxy del entorno (se manda un
valor de relleno en la cabecera `xi-api-key` y el proxy lo reemplaza); en otras máquinas se lee de la variable de
entorno ELEVENLABS_API_KEY. Este módulo no imprime ni guarda la clave.

Política de gasto (config/presupuesto_audio.json):
  - Lo que ya existe en la biblioteca NO se vuelve a generar (la clave de caché es el hash del pedido completo).
  - Antes de generar se estima el costo; `asegurar_escena(..., gastar=False)` sólo informa (modo por defecto).
  - Se respeta una reserva de créditos del mes y un tope por escena.
  - Cada generación queda en audio/ledger.jsonl (fecha, tipo, id, créditos, saldo).

Biblioteca: audio/biblioteca/<id>.mp3 + entrada en catalogo/audio.json (id, nombre, categoría, duración,
procedencia, licencia, etiquetas, variantes, volumen recomendado).
Los créditos de TTS son 1 por carácter (modelo multilingual_v2) o 0,5 (flash); un efecto cuesta ~20 créditos por
segundo con duración fija o 100 con duración automática (estimado; el valor real se lee de la cabecera
`character-cost` cuando la API la manda).
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from estudio import config

API = "https://api.elevenlabs.io"
BIBLIOTECA = config.RAIZ / "audio" / "biblioteca"
LEDGER = config.RAIZ / "audio" / "ledger.jsonl"
CATALOGO_AUDIO = config.CATALOGO / "audio.json"
VOCES = config.RAIZ / "config" / "voces.json"
PRESUPUESTO = config.RAIZ / "config" / "presupuesto_audio.json"
MODELO_TTS = "eleven_multilingual_v2"
FORMATO = "mp3_44100_128"
LICENCIA = ("Generado con la cuenta ElevenLabs del dueño; los derechos de uso comercial dependen del plan "
            "(verificar en los términos del plan antes de publicar)")


class ErrorAudio(RuntimeError):
    pass


# ------------------------------------------------------------------------------------------------ HTTP

def _clave() -> str:
    return os.environ.get("ELEVENLABS_API_KEY") or "proxy-injected"


def _pedir(metodo: str, ruta: str, cuerpo: dict | None = None, binario: bool = False, timeout: int = 120):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(API + ruta, data=datos, method=metodo, headers={
        "xi-api-key": _clave(), "Content-Type": "application/json",
        "Accept": "audio/mpeg" if binario else "application/json", "User-Agent": "3d-film-studio"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            crudo = r.read()
            return (crudo if binario else json.loads(crudo or b"{}")), dict(r.headers)
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")[:400]
        raise ErrorAudio(f"ElevenLabs respondió {e.code} en {ruta}: {detalle}") from None
    except urllib.error.URLError as e:
        raise ErrorAudio(f"No se pudo conectar con ElevenLabs: {e.reason}") from None


# ------------------------------------------------------------------------------------ consultas gratuitas

def suscripcion() -> dict:
    d, _ = _pedir("GET", "/v1/user/subscription")
    return {"plan": d.get("tier"), "estado": d.get("status"), "usados": d.get("character_count"),
            "limite": d.get("character_limit"), "restantes": (d.get("character_limit") or 0) - (d.get("character_count") or 0),
            "reinicia_unix": d.get("next_character_count_reset_unix"), "voces_propias_max": d.get("voice_limit")}


def voces() -> list[dict]:
    d, _ = _pedir("GET", "/v1/voices")
    out = []
    for v in d.get("voices", []):
        l = v.get("labels") or {}
        out.append({"voice_id": v["voice_id"], "nombre": v["name"], "categoria": v.get("category"),
                    "genero": l.get("gender"), "edad": l.get("age"), "acento": l.get("accent"),
                    "uso": l.get("use_case"),
                    "idiomas": sorted({x.get("language") for x in (v.get("verified_languages") or []) if x.get("language")})})
    return out


def modelos() -> list[dict]:
    d, _ = _pedir("GET", "/v1/models")
    return [{"id": m["model_id"], "nombre": m.get("name"), "tts": m.get("can_do_text_to_speech"),
             "idiomas": len(m.get("languages") or [])} for m in (d if isinstance(d, list) else [])]


# ------------------------------------------------------------------------------------------ configuración

def _json(ruta: Path, defecto):
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else defecto


def presupuesto() -> dict:
    return {"reserva_creditos": 3000, "max_por_escena": 4000, **_json(PRESUPUESTO, {})}


def voz_de_rol(rol: str) -> dict:
    cfg = _json(VOCES, {"roles": {}})
    if rol not in cfg["roles"]:
        raise ErrorAudio(f"El rol de voz '{rol}' no está en config/voces.json (hay: {sorted(cfg['roles'])})")
    return cfg["roles"][rol]


# ------------------------------------------------------------------------------------------ caché y catálogo

def _hash(tipo: str, **kw) -> str:
    return hashlib.sha256(json.dumps({"tipo": tipo, **kw}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _pedido_voz(ev: dict) -> dict:
    v = voz_de_rol(ev["rol"]) if ev.get("rol") else {}
    voice_id = ev.get("voice_id") or v.get("voice_id")
    if not voice_id:
        raise ErrorAudio("La voz necesita 'rol' (config/voces.json) o 'voice_id'")
    aj = {**v.get("ajustes", {}), **ev.get("ajustes", {})}
    return {"texto": ev["texto"].strip(), "voice_id": voice_id, "modelo": ev.get("modelo") or v.get("modelo") or MODELO_TTS,
            "ajustes": aj}


def id_biblioteca(ev: dict) -> str:
    """Nombre determinista del archivo para un evento de sonido del manifiesto."""
    if ev["tipo"] == "voz":
        p = _pedido_voz(ev)
        return "voz_" + _hash("voz", **p)
    if ev["tipo"] == "efecto":
        return "sfx_" + _hash("efecto", prompt=ev["prompt"].strip(), duracion=ev.get("duracion_s"))
    if ev["tipo"] == "musica":
        return "mus_" + _hash("musica", prompt=ev["prompt"].strip(), duracion=ev.get("duracion_s"))
    raise ErrorAudio(f"Tipo de evento sin biblioteca: {ev['tipo']}")


def ruta_en_biblioteca(ev: dict) -> Path:
    """Ruta del audio ya generado; si falta, lanza un error claro (la mezcla nunca gasta créditos)."""
    p = BIBLIOTECA / f"{id_biblioteca(ev)}.mp3"
    if not p.exists():
        raise ErrorAudio(f"Falta generar el audio de {ev['tipo']} «{(ev.get('texto') or ev.get('prompt'))[:50]}»: "
                         f"corré `python -m estudio voces <escena.json> --gastar`")
    return p


def duracion_s(ruta: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(ruta)],
                       capture_output=True, text=True, check=True)
    return round(float(json.loads(r.stdout)["format"]["duration"]), 2)


def _registrar(ev: dict, aid: str, ruta: Path, creditos_cabecera: float | None, extra: dict):
    cat = _json(CATALOGO_AUDIO, {"formato": 1, "sonidos": []})
    if not any(s["id"] == aid for s in cat["sonidos"]):
        cat["sonidos"].append({
            "id": aid, "nombre": (ev.get("texto") or ev.get("prompt"))[:80], "categoria": {"voz": "voz", "efecto": "efecto",
                                                                                      "musica": "musica"}[ev["tipo"]],
            "archivo": f"audio/biblioteca/{ruta.name}", "duracion_s": duracion_s(ruta),
            "procedencia": f"ElevenLabs ({extra.get('modelo', 'sound-generation')})", "licencia": LICENCIA,
            "etiquetas": ev.get("etiquetas", []), "variantes": 0, "volumen_db": ev.get("volumen_db", -12), **extra})
        CATALOGO_AUDIO.write_text(json.dumps(cat, ensure_ascii=False, indent=1))
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        # La cabecera `character-cost` NO siempre coincide con el costo real (medido: 17 para un texto de 43 caracteres),
        # y el contador de la suscripción tarda en actualizarse: se guardan las dos cifras. El gasto real es el del
        # panel de ElevenLabs (Usage).
        f.write(json.dumps({"fecha": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "tipo": ev["tipo"],
                            "id": aid, "creditos_estimados": costo_estimado(ev), "creditos_cabecera": creditos_cabecera,
                            "resumen": (ev.get("texto") or ev.get("prompt"))[:60]}, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------------------------------ estimación

def costo_estimado(ev: dict) -> float:
    if ev["tipo"] == "voz":
        factor = 0.5 if "flash" in (ev.get("modelo") or "") else 1.0
        return len(ev["texto"].strip()) * factor
    if ev["tipo"] == "efecto":
        return 20.0 * ev["duracion_s"] if ev.get("duracion_s") else 100.0
    if ev["tipo"] == "musica":
        return 0.0  # se informa aparte: depende del plan (no probado)
    return 0.0


# ------------------------------------------------------------------------------------------ generación

def generar(ev: dict) -> Path:
    """Genera UN audio (si no existe ya) y lo guarda en la biblioteca. Gasta créditos: usar con presupuesto."""
    aid = id_biblioteca(ev)
    ruta = BIBLIOTECA / f"{aid}.mp3"
    if ruta.exists():
        return ruta
    BIBLIOTECA.mkdir(parents=True, exist_ok=True)
    extra: dict = {}
    if ev["tipo"] == "voz":
        p = _pedido_voz(ev)
        cuerpo = {"text": p["texto"], "model_id": p["modelo"]}
        if p["ajustes"]:
            cuerpo["voice_settings"] = p["ajustes"]
        audio, cab = _pedir("POST", f"/v1/text-to-speech/{p['voice_id']}?output_format={FORMATO}", cuerpo, binario=True)
        extra = {"modelo": p["modelo"], "voice_id": p["voice_id"], "texto": p["texto"], "rol": ev.get("rol")}
    elif ev["tipo"] == "efecto":
        cuerpo = {"text": ev["prompt"].strip(), "prompt_influence": ev.get("influencia", 0.5)}
        if ev.get("duracion_s"):
            cuerpo["duration_seconds"] = ev["duracion_s"]
        audio, cab = _pedir("POST", f"/v1/sound-generation?output_format={FORMATO}", cuerpo, binario=True)
        extra = {"prompt": ev["prompt"].strip()}
    elif ev["tipo"] == "musica":
        cuerpo = {"prompt": ev["prompt"].strip(), "music_length_ms": int(ev.get("duracion_s", 30) * 1000)}
        audio, cab = _pedir("POST", f"/v1/music?output_format={FORMATO}", cuerpo, binario=True, timeout=300)
        extra = {"prompt": ev["prompt"].strip()}
    else:
        raise ErrorAudio(f"Tipo no generable: {ev['tipo']}")
    if len(audio) < 1000:
        raise ErrorAudio("ElevenLabs devolvió un audio vacío")
    ruta.write_bytes(audio)
    if len(audio) > 3 * 1024 * 1024:
        print(f"[audio] aviso: {ruta.name} pesa {len(audio) / 1e6:.1f} MB (los grandes conviene publicarlos en Releases)")
    creditos = None
    for k, v in cab.items():
        if k.lower() == "character-cost":
            try:
                creditos = float(v)
            except ValueError:
                pass
    _registrar(ev, aid, ruta, creditos, extra)
    return ruta


def eventos_de_audio(manifiesto: dict) -> list[dict]:
    return [e for e in manifiesto.get("sonido", {}).get("eventos", []) if e.get("tipo") in ("voz", "efecto", "musica")]


def asegurar_escena(manifiesto: dict, gastar: bool = False) -> dict:
    """Revisa qué audios de la escena faltan y, con gastar=True, los genera respetando el presupuesto."""
    pend, listos, costo = [], [], 0.0
    for ev in eventos_de_audio(manifiesto):
        if (BIBLIOTECA / f"{id_biblioteca(ev)}.mp3").exists():
            listos.append(ev)
        else:
            pend.append(ev)
            costo += costo_estimado(ev)
    pres = presupuesto()
    informe = {"ya_en_biblioteca": len(listos), "faltan": len(pend), "creditos_estimados": costo, "generados": 0}
    if not pend or not gastar:
        informe["nota"] = "simulación: no se gastó nada" if pend else "nada que generar"
        return informe
    if costo > pres["max_por_escena"]:
        raise ErrorAudio(f"La escena necesita ~{costo:.0f} créditos y el tope por escena es {pres['max_por_escena']} "
                         "(config/presupuesto_audio.json): pedir autorización al dueño")
    s = suscripcion()
    if s["restantes"] - costo < pres["reserva_creditos"]:
        raise ErrorAudio(f"Quedarían {s['restantes'] - costo:.0f} créditos (< reserva {pres['reserva_creditos']}): no se genera")
    for ev in pend:
        generar(ev)
        informe["generados"] += 1
    informe["saldo_despues"] = suscripcion()["restantes"]
    return informe
