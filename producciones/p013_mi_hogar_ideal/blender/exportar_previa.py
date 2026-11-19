"""p013 · previsualización para el dueño: GLB exportado DESDE BLENDER + JSON con la línea de tiempo y las cámaras.
Uso: /opt/tools/blendenv/bin/python exportar_previa.py -- <blend> <carpeta_salida> <layout.json> <guion.json>
Los efectos volumétricos (neblina, fuego, cielo) no viajan en el GLB: se muestran en las imágenes fijas."""
import sys
import json
import bpy

blend, out, layout_p, guion_p = sys.argv[sys.argv.index("--") + 1:][:4]
bpy.ops.wm.open_mainfile(filepath=blend)
s = bpy.context.scene
L = json.load(open(layout_p))
G = json.load(open(guion_p))
glb = f"{out}/p013_previa_v1.glb"
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_animations=True, export_lights=True, export_cameras=True,
                          export_apply=True, export_yup=True, export_image_format="JPEG", export_jpeg_quality=80,
                          export_animation_mode="ACTIONS")
cam = bpy.data.objects["Camara"]
muestras = []
for fr in range(0, s.frame_end + 1, 15):
    s.frame_set(fr)
    m = cam.matrix_world
    t = m.translation
    muestras.append({"t": round(fr / 30.0, 3), "pos": [round(v, 3) for v in (t.x, t.z, -t.y)],
                     "mira": [round(v, 3) for v in (-m.col[2].x, -m.col[2].z, m.col[2].y)]})
textos = {b["id"]: b["texto"] for b in G["beats"]}
tomas = [{"nombre": b["id"], "desde_s": b["ini"], "hasta_s": round(b["ini"] + b["dur"], 2), "dice": textos.get(b["id"], "")}
         for b in L["beats"]]
linea = {
    "formato": "estudio.previa_escena/1",
    "produccion": "p013_mi_hogar_ideal", "version": 1,
    "resolucion": "720x1280 (vertical 9:16)", "fps": 30, "duracion_s": round(s.frame_end / 30.0 + 1 / 30.0, 2),
    "cuadros": s.frame_end + 1,
    "audio": None,
    "audio_nota": "Sin audio todavía: los tiempos son ESTIMADOS por cantidad de caracteres (15 por segundo + 0,9 s de pausa). "
                  "Con el audio real de la narradora se re-sincronizan las tomas (python disenio.py --duraciones).",
    "tomas": tomas,
    "cortes": [round(b["ini"], 2) for b in L["beats"][1:]],
    "camara": muestras,
    "camara_vertical_fov_grados": L["camara_vertical_fov"],
    "iluminacion": "sol y cielo animados de día a noche; luces interiores cálidas; neón de la tele y de la cama; luz indirecta; "
                   "luces del jardín, portón, fachada, cochera y calle que se encienden al anochecer (t≈84–88 s); luna",
    "efectos": {"fuego": "chimenea de la sala con llama volumétrica, chispas y luz que parpadea",
                "neblina": "neblina baja en el jardín que crece al anochecer + bruma atmosférica",
                "arboles": "copas sólidas con ruido sobre los árboles de la biblioteca"},
    "decisiones_de_diseno": [
        {"t": 36.0, "dice": "la mesa del comedor se corre 85 cm hacia la ventana"},
        {"t": 43.0, "dice": "la cocina cambia de mesa central a isla con módulo contra el tabique"},
        {"t": 31.0, "dice": "la pared vacía de la sala recibe cuadro y luz indirecta"},
    ],
}
json.dump(linea, open(f"{out}/p013_previa_v1.json", "w"), ensure_ascii=False, indent=1)
print("PREVIA ok", glb)
