"""Sistema cinematográfico: cada TOMA es una cámara con movimiento calculado fotograma a fotograma.

Tipos de toma (campo "tipo" en el manifiesto de la escena):
  estatica      cámara fija (desde → objetivo)
  general       plano general fijo con lente angular; admite leve "respiración" (dolly muy lento)
  dolly         travelling en línea recta de `desde` a `hasta`, mirando `objetivo`
  paneo         cámara fija que gira de `objetivo` a `objetivo_final`
  grua          sube/baja (desde → hasta) mientras mira el objetivo (revelación)
  orbita        gira alrededor de `centro` (radio, altura, ángulo inicial → final) — también tomas aéreas
  seguimiento   acompaña a un vehículo/objeto móvil con un desplazamiento en SU marco local (persecución)
  detalle       primer plano / plano detalle que sigue un punto del móvil (rueda, mano, puerta)
  vigilancia    cámara de seguridad: fija, alta, lente angular, barrido lento; el montaje agrega el texto REC
  subjetiva     punto de vista de un móvil (p. ej. conductor): posición y mirada en el marco del vehículo

Puntos ("desde", "hasta", "objetivo", "centro"):
  [x, y, z]                                         posición fija
  {"ancla": "porton", "desp": [0, 0, 1.5]}          ancla del escenario + desplazamiento
  {"movil": "auto", "punto": "capot", "desp": [..]} punto de un móvil (varía en el tiempo)

Óptica: "lente_mm" (35 por defecto), "apertura" (f-stop; activa profundidad de campo con foco en el objetivo),
"temblor" (cámara en mano, metros), "suavizar" (ease-in-out del movimiento, true por defecto).
"""
from __future__ import annotations
import math
import random
from mathutils import Vector
from estudio.blender import kit as K
from estudio.blender.vehiculos import punto_en_vehiculo


class Contexto:
    def __init__(self, anclas: dict, fps: int = 30):
        self.anclas = anclas
        self.moviles: dict[str, dict] = {}       # id -> {"tray": {frame: (pos, rumbo, v)}, "anclas": {...}}
        self.fps = fps
        self.eventos: list[dict] = []           # patadas, goles… (para el sonido y la app)

    def punto(self, spec, frame: int) -> Vector:
        if spec is None:
            raise ValueError("punto vacío")
        if isinstance(spec, (list, tuple)):
            return Vector(spec)
        desp = Vector(spec.get("desp", (0, 0, 0)))
        if "ancla" in spec:
            if spec["ancla"] not in self.anclas:
                raise KeyError(f"Ancla desconocida {spec['ancla']!r}; disponibles: {sorted(self.anclas)}")
            return Vector(self.anclas[spec["ancla"]]) + desp
        if "movil" in spec:
            m = self.moviles[spec["movil"]]
            tray = m["tray"]
            f = min(max(frame, min(tray)), max(tray))
            local = m["anclas"].get(spec.get("punto", ""), (0, 0, 0.8))
            if spec.get("desp_local"):
                l = spec["desp_local"]
                local = (local[0] + l[0], local[1] + l[1], local[2] + l[2])
            return punto_en_vehiculo(tray[f], local) + desp
        raise ValueError(f"Punto no reconocido: {spec}")

    def rumbo(self, movil: str, frame: int) -> float:
        tray = self.moviles[movil]["tray"]
        f = min(max(frame, min(tray)), max(tray))
        return tray[f][1]


def _ease(t, suave=True):
    return K.suavizar(t) if suave else max(0.0, min(1.0, t))


def crear_toma(spec: dict, ctx: Contexto, col=None) -> dict:
    """Crea la cámara de una toma y graba sus claves. Devuelve {"camara", "frame_inicio", "frame_fin"}."""
    fps = ctx.fps
    f0 = int(round(spec["inicio_s"] * fps)) + 1
    f1 = f0 + int(round(spec["duracion_s"] * fps)) - 1
    tipo = spec["tipo"]
    cd = K.bpy.data.cameras.new(f"cam_{spec['id']}")
    cd.lens = spec.get("lente_mm", 35)
    cd.sensor_width = 36
    cd.clip_start = 0.05
    cd.clip_end = 2000
    cam = K.bpy.data.objects.new(f"CAM_{spec['id']}", cd)
    (col or K.coleccion("camaras")).objects.link(cam)
    if spec.get("apertura"):
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = spec["apertura"]
    if spec.get("luz_relleno"):
        # luz práctica "kicker" que viaja con la cámara (como el LED de un operador): ilumina el sujeto cercano
        lr = K.luz(f"relleno_{spec['id']}", "POINT", (0, 0, 0), spec["luz_relleno"], (0.85, 0.9, 1.0),
                   col, radio=0.3, sombra=False)
        lr.parent = cam
        lr.location = (0.4, 0.3, 0.0)
    rnd = random.Random(sum(map(ord, spec["id"])))
    temblor = spec.get("temblor", 0.0)
    fases = [rnd.uniform(0, 6.28) for _ in range(6)]
    suave = spec.get("suavizar", True)
    lente0 = cd.lens
    lente1 = spec.get("lente_final_mm", lente0)

    def objetivo(f, t):
        if tipo == "paneo" and "objetivo_final" in spec:
            return ctx.punto(spec["objetivo"], f).lerp(ctx.punto(spec["objetivo_final"], f), _ease(t, suave))
        return ctx.punto(spec.get("objetivo") or spec.get("centro"), f)

    suav_pos = None
    for f in range(f0, f1 + 1):
        t = (f - f0) / max(1, f1 - f0)
        if tipo in ("estatica", "paneo", "vigilancia"):
            pos = ctx.punto(spec["desde"], f)
        elif tipo in ("dolly", "grua", "general"):
            hasta = spec.get("hasta", spec["desde"])
            pos = ctx.punto(spec["desde"], f).lerp(ctx.punto(hasta, f), _ease(t, suave))
        elif tipo == "orbita":
            c = ctx.punto(spec["centro"], f)
            a = math.radians(spec.get("angulo_inicial", 0) + (spec.get("angulo_final", 90) - spec.get("angulo_inicial", 0)) * _ease(t, suave))
            r = spec.get("radio", 20) + (spec.get("radio_final", spec.get("radio", 20)) - spec.get("radio", 20)) * _ease(t, suave)
            h = spec.get("altura", 8) + (spec.get("altura_final", spec.get("altura", 8)) - spec.get("altura", 8)) * _ease(t, suave)
            pos = c + Vector((math.cos(a) * r, math.sin(a) * r, h))
        elif tipo in ("seguimiento", "detalle", "subjetiva"):
            movil = spec["movil"]
            desp = spec.get("desp_local", (0, -7, 2))
            rumbo = ctx.rumbo(movil, f)
            base = ctx.punto({"movil": movil, "punto": spec.get("punto_base", "")}, f)
            c, s_ = math.cos(rumbo), math.sin(rumbo)
            objetivo_pos = base + Vector((desp[0] * c - desp[1] * s_, desp[0] * s_ + desp[1] * c, desp[2]))
            # la cámara "persigue" con retardo (como un operador real), salvo en subjetiva
            k = spec.get("retardo", 0.12 if tipo == "seguimiento" else 0.35)
            if tipo == "subjetiva" or suav_pos is None:
                suav_pos = objetivo_pos
            else:
                suav_pos = suav_pos.lerp(objetivo_pos, k)
            pos = suav_pos.copy()
        else:
            raise ValueError(f"Tipo de toma desconocido: {tipo}")
        if tipo == "vigilancia":
            # barrido lento de lado a lado
            pass
        if temblor:
            tt = f / fps
            pos = pos + Vector((math.sin(tt * 1.7 + fases[0]) + 0.5 * math.sin(tt * 4.3 + fases[1]),
                                math.sin(tt * 1.3 + fases[2]) + 0.5 * math.sin(tt * 3.7 + fases[3]),
                                math.sin(tt * 2.1 + fases[4]) * 0.6)) * temblor
        cam.location = pos
        if tipo == "subjetiva":
            mira = ctx.punto({"movil": spec["movil"], "punto": spec.get("punto_base", ""),
                              "desp_local": spec.get("mira_local", (0, 30, 0))}, f)
        else:
            mira = objetivo(f, t)
            if tipo == "vigilancia":
                barrido = spec.get("barrido_m", 3.0)
                mira = mira + Vector((math.sin(t * math.pi * 2 * spec.get("barridos", 0.5)) * barrido, 0, 0))
        K.mirar_a(cam, mira)
        if spec.get("inclinacion_deg"):
            cam.rotation_euler.rotate_axis("Z", math.radians(spec["inclinacion_deg"]))
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        if lente1 != lente0:
            cd.lens = lente0 + (lente1 - lente0) * _ease(t, suave)
            cd.keyframe_insert("lens", frame=f)
        if cd.dof.use_dof:
            cd.dof.focus_distance = max(0.1, (mira - pos).length if not spec.get("foco") else
                                        (ctx.punto(spec["foco"], f) - pos).length)
            cd.keyframe_insert("dof.focus_distance", frame=f)
    # marcador de corte en la línea de tiempo
    sc = K.bpy.context.scene
    m = sc.timeline_markers.new(spec["id"], frame=f0)
    m.camera = cam
    return {"camara": cam, "frame_inicio": f0, "frame_fin": f1, "spec": spec}
