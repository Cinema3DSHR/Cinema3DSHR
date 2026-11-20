"""p015 «FRACTURA» · biblioteca de Aiden: importa al personaje original de «A la deriva» (armadura, traje, pelo, cara) desde la escena E02 v3
y le retargetea los clips de Mixamo que usa el cortometraje. Guarda todo en un BLEND de biblioteca (acciones con usuario falso) para no repetir
el trabajo lento. Uso: /opt/tools/blendenv/bin/python aiden_clips.py -- <salida_biblioteca.blend>"""
import sys
import json
import time
from pathlib import Path
import bpy

sys.path.insert(0, "/home/user/Cinema3DSHR")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import retarget_dir as RT   # noqa: E402  (conserva la dirección de los huesos: brazos en T → en A)
import os

SALIDA = sys.argv[sys.argv.index("--") + 1]
E02 = "/home/user/trabajo_cine/p011_a_la_deriva/e02/v3/escena.blend"
MIX = Path("/home/user/mixamo-respaldo/animaciones")
CLIPS = {
    "correr": "caminar_correr/Fast_Run_inplace.fbx",
    "salto_carrera": "saltos_parkour/Running_Jump.fbx",
    "salto_grande": "saltos_parkour/Big_Jump.fbx",
    "salto_adelante": "saltos_parkour/Forward_Jump.fbx",
    "voltereta": "saltos_parkour/Running_Forward_Flip_inplace.fbx",
    "mortal_atras": "saltos_parkour/Backflip.fbx",
    "rodar": "saltos_parkour/Dive_Roll.fbx",
    "tornillo": "saltos_parkour/Corkscrew_Evade.fbx",
    "flotar": "otras/Floating.fbx",
    "caida_loop": "caidas_muertes/Fall_B_Loop.fbx",
    "caida": "caidas_muertes/Falling_2.fbx",
    "colgado": "saltos_parkour/Hanging_Idle.fbx",
    "reaccion_frente": "idle_parado/Standing_React_Large_From_Front.fbx",
    "lanzado": "interaccion/Getting_Thrown.fbx",
    "volando_atras": "caidas_muertes/Flying_Back_Death.fbx",
    "golpe": "combate_pelea/Hit_Reaction.fbx",
    "susto": "emociones/Scared.fbx",
    "evasion_aerea": "otras/Aerial_Evade.fbx",
}


def importar_aiden():
    objs = ["PJ_aiden", "Armature", "tripo_node_149bc4a7", "CARA_aiden_ojo_izq", "CARA_aiden_ceja_izq", "CARA_aiden_rubor_izq", "CARA_aiden_ojo_der",
            "CARA_aiden_ceja_der", "CARA_aiden_rubor_der", "CARA_aiden_boca", "CARA_aiden_nariz", "PELO_aiden", "TRAJE_aiden", "CUELLO_TRAJE_aiden",
            "VIVOS_aiden", "CIERRE_aiden"]
    with bpy.data.libraries.load(E02, link=False) as (df, dt):
        dt.objects = [o for o in objs if o in df.objects]
    col = bpy.data.collections.new("AIDEN")
    bpy.context.scene.collection.children.link(col)
    for o in dt.objects:
        if o is not None:
            col.objects.link(o)
    return bpy.data.objects["Armature"]


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
    s = bpy.context.scene
    s.render.fps = 30
    aiden = importar_aiden()
    aiden.name = "Aiden_armadura"
    info = {}
    solo = os.environ.get("CLIPS_SOLO")
    for nombre, rel in CLIPS.items():
        if solo and nombre not in solo.split(","):
            continue
        t0 = time.time()
        try:
            arm, acc, nuevos = importar_clip(MIX / rel)
            f0, f1 = int(acc.frame_range[0]), int(acc.frame_range[1])
            nueva = RT.retarget(arm, acc, aiden, f"aiden_{nombre}", fotogramas=(f0, f1))
            nueva.use_fake_user = True
            info[nombre] = {"frames": f1 - f0 + 1, "f0": f0, "desp": list(nueva.get("desplazamiento_cadera_m", [0, 0, 0])), "s": round(time.time() - t0, 1)}
            for o in nuevos:
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.actions.remove(acc)
        except Exception as e:                     # un clip que falla no tumba la biblioteca
            info[nombre] = {"error": str(e)[:200]}
        print("CLIP", nombre, info[nombre], flush=True)
    aiden.animation_data_clear()
    bpy.context.scene.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
    json.dump(info, open(str(SALIDA) + ".json", "w"), indent=1)
    print("BIBLIOTECA lista", SALIDA)


main()
