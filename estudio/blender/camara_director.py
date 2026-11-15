"""Cámaras colocadas por el director en el EDITOR 3D de la app (botón COLOCAR CÁMARA).

El archivo de cada cámara (`producciones/<produccion>/director/camaras/camera_NNN.json`) está SIEMPRE en coordenadas
de Blender, que son las de la escena de producción: X, Y en el piso, Z arriba, metros. Así Claude la aplica sin
conversiones y sin adivinar nada a partir de una captura.

Conversión que hace la app (Godot usa los ejes de glTF: Y arriba):
    punto_blender   = C · punto_godot          con  C = [[1,0,0],[0,0,−1],[0,1,0]]   (x, y, z)_b = (x, −z, y)_g
    rotación_blender = C · rotación_godot      (las cámaras miran a −Z local con +Y arriba en los tres programas)
Óptica: la app captura el FOV vertical de su cámara (Godot ajusta por altura) dentro de una vista 16:9 idéntica al
cuadro del render; Blender usa sensor de 36 mm de ANCHO (sensor_fit AUTO, imagen apaisada):
    fov_h = 2·atan(tan(fov_v/2)·aspecto)        lente_mm = 18 / tan(fov_h/2)

Campos (formato "estudio.camara/1"): camera_id, name, produccion, escena, version_escena, huella_escena, shot,
time_capture, time_start, time_end, position{x,y,z}, rotation{x,y,z} (grados, Euler XYZ de Blender = rotation_euler
de la cámara), quaternion [w,x,y,z], forward{x,y,z}, up{x,y,z}, fov (= fov_v_deg), fov_h_deg, fov_v_deg, lens_mm,
sensor_mm, sensor_fit, aspect, resolution, notes, created, godot{origin, basis} (lo crudo, para auditoría).
"""
from __future__ import annotations
import json
import math
from pathlib import Path

C = ((1, 0, 0), (0, 0, -1), (0, 1, 0))


def _mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _vec(a, v):
    return tuple(sum(a[i][k] * v[k] for k in range(3)) for i in range(3))


def lente_desde_fov_v(fov_v_deg: float, aspecto: float, sensor_mm: float = 36.0) -> tuple[float, float]:
    fov_h = 2 * math.atan(math.tan(math.radians(fov_v_deg) / 2) * aspecto)
    return sensor_mm / 2 / math.tan(fov_h / 2), math.degrees(fov_h)


def desde_godot(origen, base_columnas, fov_v_deg: float, aspecto: float = 16 / 9) -> dict:
    """Misma cuenta que hace la app (sirve para las pruebas). base_columnas: (eje_x, eje_y, eje_z) de la Basis de Godot."""
    G = tuple(tuple(base_columnas[j][i] for j in range(3)) for i in range(3))   # filas
    R = _mul(C, G)
    p = _vec(C, origen)
    lente, fov_h = lente_desde_fov_v(fov_v_deg, aspecto)
    return {"position": dict(zip("xyz", p)), "matriz_blender": R, "fov_v_deg": fov_v_deg, "fov_h_deg": fov_h,
            "lens_mm": lente, "aspect": aspecto}


def leer(ruta) -> dict:
    return json.loads(Path(ruta).read_text())


def matriz(datos: dict):
    """Matriz 4×4 de mundo (mathutils) de la cámara del director, desde su cuaternión (exacto) o su Euler."""
    from mathutils import Matrix, Quaternion, Euler, Vector
    p = datos["position"]
    if datos.get("quaternion"):
        r = Quaternion(datos["quaternion"]).to_matrix()
    else:
        ro = datos["rotation"]
        r = Euler((math.radians(ro["x"]), math.radians(ro["y"]), math.radians(ro["z"])), "XYZ").to_matrix()
    return Matrix.Translation(Vector((p["x"], p["y"], p["z"]))) @ r.to_4x4()


def aplicar(cam, datos: dict, frame: int | None = None):
    """Pone la cámara de Blender exactamente en el punto de vista capturado (posición, orientación y óptica)."""
    cam.rotation_mode = "XYZ"
    cam.matrix_world = matriz(datos)
    cd = cam.data
    cd.sensor_width = float(datos.get("sensor_mm", 36.0))
    cd.sensor_fit = "AUTO"
    cd.lens = float(datos["lens_mm"])
    if frame is not None:
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)
        cd.keyframe_insert("lens", frame=frame)
