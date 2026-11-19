"""Modalidad 2 (BLEND externo aprobado) sin render: arma un .blend mínimo con el perfil de producción 720p, lo aprueba,
lo incorpora y comprueba que lo publicado sea EXACTAMENTE el archivo aprobado (mismo SHA-256, nunca reescrito), que la
validación y el render por trozos (`--sin-render`) lo acepten, y que se rechace todo lo que no cumple: otro archivo,
un byte cambiado, perfil distinto, texturas sin empaquetar, aprobación repetida y versión ya existente.

    /opt/tools/blendenv/bin/python pruebas/autofinisher/test_blend_externo.py
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
import bpy  # noqa: E402

from estudio.autofinisher import blend_externo as BE, manifiesto as MF, medicion as MD  # noqa: E402
from estudio.autofinisher.validar import validar  # noqa: E402
from estudio.autofinisher.render_trozo import renderizar  # noqa: E402

resultados = []


def caso(nombre, cond, detalle=""):
    resultados.append((nombre, bool(cond)))
    print(("OK    " if cond else "FALLA ") + nombre + (f" — {detalle}" if detalle else ""), flush=True)


def rechaza(fn):
    try:
        fn()
    except (SystemExit, FileExistsError, ValueError) as e:
        return True, str(e)[:160]
    return False, "no rechazó"


def escena(ruta: Path, *, ancho=1280, muestras=6, textura_externa=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps, s.render.fps_base = 30, 1.0
    s.frame_start, s.frame_end = 0, 89                       # 3 s a 30 fps
    cd = bpy.data.cameras.new("Camara")
    cam = bpy.data.objects.new("Camara", cd)
    s.collection.objects.link(cam)
    s.camera = cam
    cam.location = (0, -6, 1.5)
    cam.keyframe_insert("location", frame=0)
    cam.location = (2, -6, 1.5)
    cam.keyframe_insert("location", frame=89)
    bpy.ops.mesh.primitive_cube_add()
    img = bpy.data.images.new("tex_prueba", 8, 8)
    if textura_externa:
        img.source = "FILE"
        img.filepath = "/no/existe/textura.png"
    else:
        img.filepath_raw = str(ruta.with_suffix(".png"))
        img.file_format = "PNG"
        img.save()
        img.source = "FILE"
        img.pack()
    # la imagen la usa un material del cubo (si no, Blender la descarta al guardar por no tener usuarios)
    mat = bpy.data.materials.new("mat_prueba")
    mat.use_nodes = True
    nodo = mat.node_tree.nodes.new("ShaderNodeTexImage")
    nodo.image = img
    mat.node_tree.links.new(nodo.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    bpy.context.active_object.data.materials.append(mat)
    s.render.engine = "CYCLES"
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = ancho, 720, 100
    c = s.cycles
    c.device, c.samples = "CPU", muestras
    c.use_adaptive_sampling, c.adaptive_threshold = True, 0.05
    c.use_denoising, c.denoiser = True, "OPENIMAGEDENOISE"
    c.max_bounces, c.use_light_tree = 6, True
    c.seed, c.use_animated_seed = 4242, False
    bpy.ops.wm.save_as_mainfile(filepath=str(ruta), compress=True)


tmp = Path(tempfile.mkdtemp(prefix="af_externo_"))
prod = tmp / "pXXX_prueba"
prod.mkdir()
(prod / "produccion.json").write_text(json.dumps({"id": "pXXX_prueba", "titulo": "prueba",
                                                   "formato": {"fps": 30, "duracion_s": 3, "resolucion": "1280x720"}}))
bueno = tmp / "aprobado.blend"
escena(bueno)
sha0, bytes0 = MD.sha256(bueno), bueno.stat().st_size

# 1. inspección de sólo lectura
insp = BE.inspeccionar(bueno)
caso("inspección no modifica el archivo", MD.sha256(bueno) == sha0 and bueno.stat().st_size == bytes0)
caso("perfil vertical 720x1280 sólo si la producción lo declara", BE.perfil_de({"resolucion": "720x1280"})["resolucion"] == [720, 1280]
     and BE.perfil_de({"resolucion": "1280x720"}) is BE.PERFIL_720P and BE.perfil_de(None) is BE.PERFIL_720P)
caso("perfil 720p aceptado", BE.problemas(insp, BE.PERFIL_720P, {"fps": 30, "duracion_s": 3, "resolucion": "1280x720"}) == [],
     str(BE.problemas(insp)))
caso("cámara animada detectada", insp["camara"] == "Camara" and insp["camara_animada"])
caso("textura empaquetada detectada", insp["autonomo"] and len(insp["empaquetados"]) >= 1, str(insp["empaquetados"]))

# 2. aprobación
r = BE.aprobar(str(bueno), str(prod), 1, "aprobada, renderizala")
reg_p = Path(r["registro"])
reg = json.loads(reg_p.read_text())
caso("registro con el hash del archivo", reg["blend"]["sha256"] == sha0 and reg["id"] == "pXXX_prueba_v001")
caso("aprobación no modifica el archivo", MD.sha256(bueno) == sha0)
ok, d = rechaza(lambda: BE.aprobar(str(bueno), str(prod), 1, "otra"))
caso("aprobación repetida rechazada", ok, d)

# 3. incorporación
out = tmp / "dist" / "pXXX_prueba_v001"
inc = BE.incorporar(str(bueno), str(reg_p), str(out))
pub = out / "pXXX_prueba_v001.blend"
caso("lo publicado es byte a byte lo aprobado", MD.sha256(pub) == sha0 and pub.read_bytes() == bueno.read_bytes())
m = MF.leer(out / "manifest.json")
caso("manifiesto válido, origen externo y ajustes bloqueados",
     m["origen"] == "blend_externo" and m["ajustes_bloqueados"] and m["revision"]["estado"] == "aprobada"
     and m["archivos"]["blend"]["sha256"] == sha0 and m["render"]["cuadros"] == 90)
ok, d = rechaza(lambda: BE.incorporar(str(bueno), str(reg_p), str(out)))
caso("versión existente no se sobrescribe", ok, d)

# 4. validación y render por trozos (sin render) desde la versión publicada
v = validar(str(pub), str(out / "manifest.json"))
caso("validar acepta la versión", v["ok"], str(v["problemas"]))
rt = renderizar(str(pub), str(out / "manifest.json"), list(range(1, 16)), 1280, 720, 6, str(tmp / "frames"), 1, True)
caso("render-trozo --sin-render recorre los 15 cuadros", rt["procesados"] == 15 and not rt["fallos"])
caso("render-trozo no modificó el archivo", MD.sha256(pub) == sha0)

# 5. rechazos
otro = tmp / "otro.blend"
escena(otro, ancho=1280)
bpy.data.objects["Cube"].location.x = 0.5               # mismo perfil, otra escena
bpy.ops.wm.save_as_mainfile(filepath=str(otro), compress=True)
ok, d = rechaza(lambda: BE.incorporar(str(otro), str(reg_p), str(tmp / "d2")))
caso("otro archivo rechazado (hash distinto)", ok and "no es el aprobado" in d, d)

tocado = tmp / "tocado.blend"
shutil.copyfile(bueno, tocado)
b = bytearray(tocado.read_bytes())
b[len(b) // 2] ^= 0x01
tocado.write_bytes(bytes(b))
ok, d = rechaza(lambda: BE.incorporar(str(tocado), str(reg_p), str(tmp / "d3")))
caso("un byte cambiado se rechaza", ok, d)

mal_res = tmp / "1080.blend"
escena(mal_res, ancho=1920)
ok, d = rechaza(lambda: BE.aprobar(str(mal_res), str(prod), 2, "x"))
caso("resolución distinta de 1280×720 rechazada", ok and "resolucion" in d, d)

mal_m = tmp / "m12.blend"
escena(mal_m, muestras=12)
ok, d = rechaza(lambda: BE.aprobar(str(mal_m), str(prod), 3, "x"))
caso("muestras distintas de 6 rechazadas", ok and "muestras" in d, d)

ext = tmp / "externo.blend"
escena(ext, textura_externa=True)
ok, d = rechaza(lambda: BE.aprobar(str(ext), str(prod), 4, "x"))
caso("textura sin empaquetar rechazada", ok and "externos" in d, d)

caso("ningún rechazo dejó registros nuevos", sorted(p.name for p in (prod / "versiones").iterdir()) == ["v001.aprobacion.json"])

shutil.rmtree(tmp, ignore_errors=True)
fallas = [n for n, ok in resultados if not ok]
print(f"\n{len(resultados) - len(fallas)}/{len(resultados)} casos bien" + (f" — FALLAN: {fallas}" if fallas else ""))
sys.exit(1 if fallas else 0)
