"""p017 · biblioteca de PERSONAS: Aiden y Kate (de «A la deriva», E02 v3) con los clips de Mixamo que usa el video, retargeteados con
retarget_dir (conserva la dirección de los huesos). Guarda /home/user/millon/personas.blend (+ .json con cuadros y desplazamiento).
Uso: /opt/tools/blendenv/bin/python personas_clips.py -- /home/user/millon/personas.blend"""
import json
import os
import sys
import time
from pathlib import Path
import bpy

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import retarget_dir as RT   # noqa: E402

SALIDA = sys.argv[sys.argv.index("--") + 1]
E02 = "/home/user/trabajo_cine/p011_a_la_deriva/e02/v3/escena.blend"
MIX = Path("/home/user/mixamo-respaldo")
CLIPS = {
    "mensajear": "animaciones/trabajo_acciones/Texting_While_Standing.fbx",
    "sorpresa": "animaciones/emociones/Surprised.fbx",
    "caminar_feliz": "animaciones/emociones/Happy_Walk.fbx",
    "caminar": "packs/Basic_Locomotion_Pack/walking.fbx",
    "festejar": "animaciones/emociones/Standing_Cheering.fbx",
    "victoria": "animaciones/emociones/Victory.fbx",
    "aplaudir": "animaciones/gestos/Standing_Clap_5.fbx",
    "samba": "packs/Free_Test_Pack/samba_dancing.fbx",
    "hiphop": "animaciones/baile/Hip_Hop_Dancing_7.fbx",
    "reir": "animaciones/emociones/Laughing.fbx",
    "senalar": "animaciones/gestos/Pointing_Forward.fbx",
    "pensar": "animaciones/gestos/Thinking.fbx",
    "cargar": "animaciones/trabajo_acciones/Carrying.fbx",
    "feliz": "animaciones/emociones/Happy_Idle_2.fbx",
}
TOPE = {"caminar": 31, "caminar_feliz": 33, "samba": 130, "hiphop": 134, "cargar": 90, "feliz": 87, "sorpresa": 90, "mensajear": 120}
PERSONAS = {
    "aiden": {"raiz": "PJ_aiden", "arm": "Armature", "prefijos": ("aiden",)},
    "kate": {"raiz": "PJ_kate", "arm": "Armature.001", "prefijos": ("kate",)},
}


def importar_persona(nombre, cfg):
    with bpy.data.libraries.load(E02, link=False) as (df, dt):
        dt.objects = [o for o in df.objects if o == cfg["raiz"] or o == cfg["arm"] or any(("_" + p) in o or o.endswith(p) for p in cfg["prefijos"]) and not o.startswith(("CAM_", "marco_", "mesa_", "silla_", "tablet_", "PANTALLA", "racion"))]
    col = bpy.data.collections.new(nombre.upper())
    bpy.context.scene.collection.children.link(col)
    for o in dt.objects:
        if o is not None:
            col.objects.link(o)
    raiz = bpy.data.objects[cfg["raiz"]]
    raiz.animation_data_clear()
    raiz.rotation_mode = "XYZ"
    raiz.location = (0.0, 0.0, 0.0)
    raiz.rotation_euler = (0.0, 0.0, 0.0)      # el retarget debe hacerse con el personaje mirando a −Y como el origen (en E02 la raíz venía girada 180°)
    bpy.context.view_layer.update()
    return bpy.data.objects[cfg["arm"]]


def importar_clip(ruta):
    antes = set(bpy.data.objects)
    acc_antes = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=str(ruta), automatic_bone_orientation=False)
    nuevos = [o for o in bpy.data.objects if o not in antes]
    arm = next(o for o in nuevos if o.type == "ARMATURE")
    acc = next(a for a in bpy.data.actions if a not in acc_antes)
    return arm, acc, nuevos


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    info = {}
    solo = os.environ.get("PERSONA")
    for nombre, cfg in PERSONAS.items():
        if solo and nombre != solo:
            continue
        arm_d = importar_persona(nombre, cfg)
        arm_d.name = f"arm_{nombre}"
        for clip, rel in CLIPS.items():
            t0 = time.time()
            try:
                arm, acc, nuevos = importar_clip(MIX / rel)
                f0, f1 = int(acc.frame_range[0]), int(acc.frame_range[1])
                f1 = min(f1, f0 + TOPE.get(clip, 100) - 1)         # sólo se retargetea lo que se usa (el retarget cuesta ~0,4 s por cuadro)
                nueva = RT.retarget(arm, acc, arm_d, f"{nombre}_{clip}", fotogramas=(f0, f1))
                nueva.use_fake_user = True
                info[f"{nombre}_{clip}"] = {"frames": f1 - f0 + 1, "desp": list(nueva.get("desplazamiento_cadera_m", [0, 0, 0])), "s": round(time.time() - t0, 1)}
                for o in nuevos:
                    bpy.data.objects.remove(o, do_unlink=True)
                bpy.data.actions.remove(acc)
            except Exception as e:
                info[f"{nombre}_{clip}"] = {"error": str(e)[:200]}
            print("CLIP", nombre, clip, info[f"{nombre}_{clip}"], flush=True)
        arm_d.animation_data_clear()
    bpy.context.scene.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
    json.dump(info, open(SALIDA + ".json", "w"), indent=1)
    print("PERSONAS lista", SALIDA)


main()
