"""p014 · cámara interior: con la cámara adentro de un auto se oculta su carrocería (a la cámara y a la sombra) —igual que el juego, que no dibuja la
carrocería detrás del capó— y se enciende una luz suave en la cabina. Sin esto el habitáculo queda negro (el techo tapa el sol).
Uso interno de construir.py y retoque_cabina.py. Necesita los datos del JSON de Godot (`auto_con_cabina_por_cuadro`)."""
import bpy


def _cuerpos(raiz, imgs_auto):
    """Mallas de carrocería (con la textura original del auto) y vidrios de un auto."""
    out = []
    for o in raiz.children_recursive:
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            if not m or not m.use_nodes:
                continue
            if m.name == "vidrio_auto" or any(n.type == "TEX_IMAGE" and n.image and n.image.name.split(".")[0] in imgs_auto for n in m.node_tree.nodes):
                out.append(o)
                break
    return out


def cabinas(D, s):
    imgs_auto = {f"{a['id']}_0" for a in D["autos"]}
    log = D["auto_con_cabina_por_cuadro"]
    n = len(log)
    total = {"cuerpos": 0, "luces": 0, "tramos": 0}
    for a in D["autos"]:
        k = a["indice"]
        raiz = bpy.data.objects.get(a["nodo"])
        if raiz is None:
            continue
        # tramos [ini, fin] en que la cámara está adentro de este auto
        tramos, ini = [], None
        for f in range(n):
            ad = (log[f] == k)
            if ad and ini is None:
                ini = f
            if not ad and ini is not None:
                tramos.append((ini, f - 1))
                ini = None
        if ini is not None:
            tramos.append((ini, n - 1))
        if not tramos:
            continue
        cuerpos = _cuerpos(raiz, imgs_auto)
        for o in cuerpos:
            o.visible_camera = True
            o.visible_shadow = True
            o.keyframe_insert("visible_camera", frame=0)
            o.keyframe_insert("visible_shadow", frame=0)
            for (a0, a1) in tramos:
                for prop, v in (("visible_camera", False), ("visible_shadow", False)):
                    setattr(o, prop, v)
                    o.keyframe_insert(prop, frame=a0)
                    setattr(o, prop, True)
                    o.keyframe_insert(prop, frame=min(a1 + 1, n))
        # luz de la cabina
        ld = bpy.data.lights.new(f"Luz_cabina_{k}", "POINT")
        ld.energy = 0.0
        ld.shadow_soft_size = 0.35
        ld.color = (1.0, 0.96, 0.9)
        lo = bpy.data.objects.new(f"Luz_cabina_{k}", ld)
        s.collection.objects.link(lo)
        lo.parent = raiz
        lo.location = (0.0, 0.05, 1.0)
        ld.keyframe_insert("energy", frame=0)
        for (a0, a1) in tramos:
            ld.energy = 0.0
            ld.keyframe_insert("energy", frame=max(a0 - 1, 0))
            ld.energy = 90.0
            ld.keyframe_insert("energy", frame=a0)
            ld.keyframe_insert("energy", frame=a1)
            ld.energy = 0.0
            ld.keyframe_insert("energy", frame=min(a1 + 1, n))
        total["cuerpos"] += len(cuerpos)
        total["luces"] += 1
        total["tramos"] += len(tramos)
    return total
