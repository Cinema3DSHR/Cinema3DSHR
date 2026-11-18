"""Arma la receta de la escena e01 de «A la deriva» desde el guion (guion.py) y las voces YA generadas.

Uso:  python producciones/p011_a_la_deriva/herramientas/escenas.py   → escenas/e01/v<k>/escena.json
Las rutas de audio y de las marcas de tiempo van RELATIVAS al repositorio.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).parent))
import guion as G                                      # noqa: E402
from estudio.audio import elevenlabs as E              # noqa: E402

FPS = 30
SENTADO = "mixamo:animaciones/sentado_manejar/"
INICIO_DIALOGO = 8.4
COLA_S = 3.6                                           # después de la última línea: silencio, la Tierra, negro


def _rel(p: Path) -> str:
    return str(p.relative_to(RAIZ))


def armar(version: int = 1) -> dict:
    evs = G.eventos_voz()
    rutas = [E.BIBLIOTECA / f"{E.id_biblioteca(e)}.mp3" for e in evs]
    durs = [E.duracion_s(r) for r in rutas]
    pausa = 0.45
    inicios, t = [], INICIO_DIALOGO
    for (bloque, quien, _, _), d in zip(G.LINEAS, durs):
        if bloque == "kate" and quien == "aiden":
            t += 0.6                                   # la pausa del guion antes de nombrar a Kate
        inicios.append(round(t, 3))
        t += d + pausa
    dur = round(t - pausa + COLA_S, 2)
    nf = int(round(dur * FPS))
    lineas = []
    for (bloque, quien, texto, expr), ev, r, t0, d in zip(G.LINEAS, evs, rutas, inicios, durs):
        alin = E.ruta_alineacion(ev)
        lineas.append({"bloque": bloque, "quien": quien, "texto": texto, "expr": expr, "inicio_s": t0, "dur": d,
                       "audio": _rel(r), "alineacion": _rel(alin) if alin.exists() else None, "ev": ev})
    L = lineas
    t_kate = L[10]["inicio_s"] + L[10]["dur"] * 0.6        # «Keit lleva nueve días…»: aparece SIN RESPUESTA
    t_gancho = L[11]["inicio_s"]

    # ------------------------------------------------------------------ Aiden: sentado, de espaldas
    acciones = [{"clip": SENTADO + "Sitting_Idle.fbx", "inicio_s": 0.0, "pos": [0.0, 0.5, 0.0], "mirando_deg": 90}]
    for ln in L:
        if ln["quien"] == "aiden" and ln["dur"] > 4:
            acciones.append({"clip": SENTADO + "Sitting_Talking.fbx", "inicio_s": ln["inicio_s"], "pos": [0.0, 0.5, 0.0],
                             "mirando_deg": 90, "mezcla_s": 0.6})
            acciones.append({"clip": SENTADO + "Sitting_Idle.fbx", "inicio_s": ln["inicio_s"] + ln["dur"],
                             "pos": [0.0, 0.5, 0.0], "mirando_deg": 90, "mezcla_s": 0.8})
    acciones.append({"clip": SENTADO + "Sitting_Idle_2.fbx", "inicio_s": t_kate - 0.4, "pos": [0.0, 0.5, 0.0],
                     "mirando_deg": 90, "mezcla_s": 1.0})
    expresiones = [{"t": 0.0, "expr": "cansado"}]
    for ln in L:
        expresiones.append({"t": ln["inicio_s"], "expr": ln["expr"], "transicion": 0.6})
    habla = [{"inicio_s": ln["inicio_s"], "audio": ln["audio"], "texto": ln["texto"],
              **({"alineacion": ln["alineacion"]} if ln["alineacion"] else {})} for ln in L if ln["quien"] == "aiden"]
    miradas = []
    for ln in L:
        if ln["quien"] == "eva" and ln["dur"] > 3:
            miradas.append({"t": ln["inicio_s"] + 0.3, "hasta": ln["inicio_s"] + 1.6, "u": 0.0, "v": 0.6})
    miradas.append({"t": t_kate + 0.2, "hasta": t_gancho + 1.0, "u": 0.7, "v": 0.0})       # mira la pantalla de Kate
    miradas.append({"t": t_gancho + 1.0, "hasta": dur, "u": 0.0, "v": -0.6})               # baja la mirada
    aiden = {"id": "aiden", "modelo": "humano:chico", "alto_m": 1.80, "acciones": acciones,
             "cara": {"expresiones": expresiones, "habla": habla, "miradas": miradas}}

    # ------------------------------------------------------------------ tomas (9:16)
    def toma(i, tipo, nombre, t0, t1, **kw):
        return {"id": f"t{i:02d}_{nombre}", "tipo": tipo, "plano": kw.pop("plano", nombre), "inicio_s": round(t0, 3),
                "duracion_s": round(t1 - t0, 3), **kw}
    cortes = [0.0, 4.6, INICIO_DIALOGO, L[2]["inicio_s"], L[4]["inicio_s"], L[6]["inicio_s"] + 6.0, L[8]["inicio_s"],
              L[9]["inicio_s"], t_kate - 0.3, t_gancho + 0.2, L[13]["inicio_s"], dur]
    tomas = [
        toma(1, "paneo", "universo", cortes[0], cortes[1], plano="exterior: la Tierra lejana; la cámara se aleja y "
             "descubre la nave diminuta frente al espacio", desde=[-24, 250, 20], hasta=[12, -46, 13],
             objetivo={"ancla": "tierra"}, objetivo_final={"ancla": "tierra"}, lente_mm=30, lente_final_mm=22),
        toma(2, "dolly", "la_nave", cortes[1], cortes[2], plano="la nave a la deriva; la Tierra y el planeta de "
             "anillos al fondo", desde=[16, -30, 9], hasta=[10, -18, 6], objetivo={"ancla": "nave_exterior"},
             lente_mm=26),
        toma(3, "dolly", "aiden_de_espaldas", cortes[2], cortes[3], plano="interior: Aiden de espaldas frente a la "
             "estación; la Tierra en el ventanal", desde=[0.55, -2.6, 1.75], hasta=[0.35, -1.5, 1.62],
             objetivo={"ancla": "ventanal", "desp": [0, 0, -0.25]}, lente_mm=20),
        toma(4, "dolly", "hombro", cortes[3], cortes[4], plano="sobre el hombro: telemetría y la voz de EVA",
             desde=[0.62, -0.25, 1.52], hasta=[0.5, 0.0, 1.48], objetivo={"ancla": "consola", "desp": [0, 0, 0.15]},
             lente_mm=30),
        toma(5, "paneo", "trayectoria", cortes[4], cortes[5], plano="detalle: la trayectoria, RETORNO NO VIABLE; "
             "sube al núcleo de EVA", desde=[0.35, 1.05, 1.32], hasta=[0.25, 1.15, 1.36],
             objetivo={"ancla": "pantalla_trayectoria"}, objetivo_final={"ancla": "nucleo_eva"}, lente_mm=32),
        toma(6, "dolly", "reflejo", cortes[5], cortes[6], plano="lateral: Aiden contra el ventanal, reflejos de las "
             "pantallas", desde=[-1.55, 1.25, 1.35], hasta=[-1.35, 1.1, 1.38], objetivo={"ancla": "puesto"},
             lente_mm=35),
        toma(7, "dolly", "espalda_media", cortes[6], cortes[7], plano="espalda de Aiden; EVA no puede cambiar las "
             "ecuaciones", desde=[0.3, -1.0, 1.55], hasta=[0.2, -0.75, 1.52], objetivo={"ancla": "puesto"},
             lente_mm=35),
        toma(8, "dolly", "keit", cortes[7], cortes[8], plano="Aiden pide que EVA hable con Kate (de perfil, lejos)",
             desde=[1.5, 0.3, 1.4], hasta=[1.35, 0.4, 1.4], objetivo={"ancla": "puesto"}, lente_mm=40),
        toma(9, "dolly", "sin_respuesta", cortes[8], cortes[9], plano="la pantalla del módulo de Kate: COMUNICACIÓN "
             "SIN RESPUESTA", desde=[-1.7, 0.6, 1.62], hasta=[-2.0, 0.75, 1.62],
             objetivo={"ancla": "kate_pantalla"}, lente_mm=32),
        toma(10, "estatica", "canal", cortes[9], cortes[10], plano="EVA ofrece abrir el canal; Aiden: «No. Déjala»",
             desde=[0.95, -0.35, 1.95], objetivo={"ancla": "puesto", "desp": [0, 0.35, -0.05]}, lente_mm=32),
        toma(11, "dolly", "final", cortes[10], cortes[11], plano="final: Aiden inmóvil; la Tierra pequeña en el "
             "ventanal. Corte a negro", desde=[0.4, -1.6, 1.68], hasta=[0.5, -2.75, 1.78],
             objetivo={"ancla": "ventanal", "desp": [-0.2, 0, -0.2]}, lente_mm=22,
             montaje={"efecto": "fundido_negro", "desde_s": round(cortes[11] - cortes[10] - 1.4, 2),
                      "duracion_s": 1.2}),
    ]

    # ------------------------------------------------------------------ sonido
    voces = []
    for ln in L:
        v = {**ln["ev"], "inicio_s": ln["inicio_s"], "volumen": 1.0}
        v.pop("etiquetas", None)
        if ln["quien"] == "aiden":
            v["movil"] = "aiden"
        voces.append(v)
    sonido = {"generador": "procedural", "ambiente": "nave_interior", "eventos": voces + [
        # música ya generada (85 s, ElevenLabs): se reutiliza tal cual aunque la escena dure un poco más
        {"tipo": "musica", "prompt": "Very subtle ambient space score, 85 seconds, no vocals, no drums: a "
                                     "low warm synth pad and distant soft piano notes, lonely and melancholic, slow, "
                                     "lots of silence, never competing with dialogue", "duracion_s": 85.06,
         "inicio_s": 0.0, "volumen": 0.22},
        {"tipo": "efecto", "prompt": "single soft futuristic computer interface chime, subtle, clean", "duracion_s": 1.0,
         "inicio_s": round(t_kate, 2), "volumen": 0.5}]}

    escena = {
        "tipo": "escena", "id": "p011_a_la_deriva-e01", "produccion": "p011_a_la_deriva", "numero": 1,
        "version": version, "titulo": "A la deriva · E01", "duracion_s": dur,
        "guion": "Documento de producción v1.1 (ver E01_documento_produccion_v1_1.txt). EVA confirma que volver a la "
                 "Tierra ya no es viable; Kate lleva nueve días sin responder.",
        "escenario": {"id": "nave_deriva", "generador": "nave_deriva", "parametros": {"semilla": 11}},
        "eventos": [
            {"accion": "luces_navegacion", "inicio_s": 0.0, "nf": nf, "fps": FPS},
            {"accion": "eva_habla", "inicio_s": 0.0, "nf": nf, "fps": FPS,
             "lineas": [{"inicio_s": ln["inicio_s"], "audio": ln["audio"]} for ln in L if ln["quien"] == "eva"]},
            {"accion": "estado_kate", "inicio_s": round(t_kate, 3)},
        ],
        "vehiculos": [], "personajes": [aiden], "tomas": tomas, "sonido": sonido,
        "render": {"calidad": "revision", "fps": FPS, "vertical": True, "exposicion": 0.0},
        "estado": "borrador", "bloqueada": False, "huella_v": 2,
    }
    return escena


if __name__ == "__main__":
    v = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    e = armar(v)
    out = RAIZ / "producciones/p011_a_la_deriva/escenas/e01" / f"v{v}" / "escena.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(e, ensure_ascii=False, indent=1) + "\n")
    print(out, "duración", e["duracion_s"], "s", "tomas", len(e["tomas"]))
