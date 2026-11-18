"""Personajes humanos (serie espacial) sobre los maniquíes del dueño.

Los FBX de Tripo3D (esqueleto mixamorig de 65 huesos, ~0,95 m al importar, miran a −Y) aportan el cuerpo y el
esqueleto (las animaciones de Mixamo andan igual). El estudio les pone:
  · CABEZA ORIGINAL del maniquí (decisión del dueño, 18/11/2026) con piel de dispersión subsuperficial.
  · ROSTRO dibujado con el sistema de los Stickman, estilo anime realista (estudio/blender/cara_anime.py): ojos con
    iris y brillos, párpados, cejas, nariz, labios y rubor; 18 expresiones, boca con la voz, miradas y parpadeo.
  · PELO modelado que subió el dueño (estudio/blender/pelo_modelo.py): él «hair02», ella «SummerGirl».
    (Alternativas guardadas: cabeza MakeHuman con expresiones 3D en cabeza_mh.py/expresiones_3d.py y pelo de hebras
    en pelo_realista.py.)
  · TRAJE DE PRIMERA PIEL (va debajo del traje espacial, que viene después) (estudio/blender/ropa_humana.py).

Manifiesto: {"id": "el", "modelo": "humano:chico", "alto_m": 1.80,
             "cara": {"expresiones": [...], "miradas": [...], "habla": [{"inicio_s": …,
                      "audio": "audio/biblioteca/voz_….mp3", "texto": "…"}]}, "acciones": [...]}
Las rutas de audio van RELATIVAS al repositorio (en GitHub Actions la carpeta del repo tiene otro nombre).
"""
from __future__ import annotations

BASE_SUBIDAS = "mixamo:personajes_pelicula/a_la_deriva"  # respaldo del dueño (antes subidas:un_sueno_de_a_dos)
MODELOS = {
    "humano:chico": {"ref": f"{BASE_SUBIDAS}/chico/tripo_convert_149bc4a7-9bf8-493a-b51e-14da191a88e2.fbx",
                     "alto_modelo": 0.93},
    "humano:chica": {"ref": f"{BASE_SUBIDAS}/chica/tripo_convert_31e45afb-e5aa-4aab-9cc4-3e59349d0581.fbx",
                     "alto_modelo": 0.98},
}

TRAJE = {"prenda": "traje_primera_piel", "color": [0.13, 0.14, 0.16], "acento": [0.15, 0.62, 0.78],
         "paneles": [0.20, 0.21, 0.24]}

PERFILES = {
    "humano:chico": {
        "genero": 1.0, "cara": "el", "piel": (0.80, 0.62, 0.50), "labios": (0.70, 0.47, 0.44), "barba": 0.22,
        "iris": (0.30, 0.20, 0.12), "cejas": (0.07, 0.05, 0.035),
        "pelo_modelo": "hair02", "peinado": "degrade_militar", "pelo": (0.07, 0.05, 0.035), "melanina": 0.86,
        "rojizo": 0.3,
        "vestuario": [TRAJE],
    },
    "humano:chica": {
        "genero": 0.0, "cara": "ella", "piel": (0.86, 0.68, 0.57), "labios": (0.78, 0.46, 0.47), "barba": 0.0,
        "iris": (0.34, 0.21, 0.11), "cejas": (0.15, 0.09, 0.06),
        "pelo_modelo": "summer_girl", "peinado": "largo_suelto", "pelo": (0.16, 0.09, 0.05), "melanina": 0.72,
        "rojizo": 0.45,
        "vestuario": [TRAJE],
    },
}


def _cabeza_propia(pj: dict) -> dict:
    """La cabeza original del maniquí como referencia para el pelo y el cuello del traje (no se modifica):
    una malla auxiliar (fuera de la escena) con las caras que mueve el hueso de la cabeza."""
    import bpy
    from estudio.blender import cabeza_mh as CM
    rep = CM.reposo(pj)
    me0 = pj["malla"].data
    cab = {i for i, p in enumerate(rep["pesos"]) if sum(w for g, w in p.items() if g.startswith("Head")) > 0.5}
    caras = [list(p.vertices) for p in me0.polygons if all(v in cab for v in p.vertices)]
    usados = sorted({v for c in caras for v in c})
    loc = {g: i for i, g in enumerate(usados)}
    me = bpy.data.meshes.new(f"ref_cabeza_{pj['id']}")
    me.from_pydata([tuple(rep["pos"][g]) for g in usados], [], [[loc[v] for v in c] for c in caras])
    me.update()
    ob = bpy.data.objects.new(f"REF_CABEZA_{pj['id']}", me)          # no se enlaza: sólo para medir
    hn, hh = rep["huesos"]["Neck"][0], rep["huesos"]["Head"][0]
    return {"obj": ob, "z_corte": hn.z + (hh.z - hn.z) * 0.3, "rep": rep, "propia": True}


def esculpir_cara(pj: dict, acortar: float = 0.17, menton: float = 0.10, aplanar: float = 1.0, alisar: int = 40):
    """La cara de los maniquíes es larga (mucho mentón): se acorta la parte de abajo de la cara (de la línea de los
    ojos al mentón) y el mentón se lleva un poco hacia atrás. Sólo adelante (la nuca y el cráneo no se tocan) y con
    transición suave hacia el cuello. Se cambia la malla en reposo: el esqueleto y las animaciones siguen igual."""
    import numpy as np
    from estudio.blender import cabeza_mh as CM
    rep = CM.reposo(pj)
    malla, arm = pj["malla"], pj["armadura"]
    M = arm.matrix_world.inverted() @ malla.matrix_world
    P = rep["pos"].copy()
    u = pj["u"]
    cab = [i for i, p in enumerate(rep["pesos"]) if sum(w for g, w in p.items() if g.startswith("Head")) > 0.5]
    H = P[cab]
    top = H[:, 2].max()
    y0, y1 = H[:, 1].min(), H[:, 1].max()
    cy, D = (y0 + y1) / 2, y1 - y0
    menton_z = H[H[:, 1] < cy - 0.25 * D][:, 2].min()
    alto = top - menton_z
    ojos = top - 0.5 * alto
    nariz = ojos - 0.2 * alto
    z_cuello = rep["huesos"]["Neck"][0].z
    for i in range(len(P)):
        x, y, z = P[i]
        if z >= ojos or z < z_cuello:
            continue
        wf = float(np.clip((cy - y) / (0.3 * D) + 0.35, 0, 1))
        wf = wf * wf * (3 - 2 * wf)
        if z >= menton_z:
            dz = acortar * (ojos - z)
        else:                                   # debajo del mentón: se apaga hacia el cuello
            dz = acortar * (ojos - menton_z) * float(np.clip((z - (menton_z - 0.05 * u)) / (0.05 * u), 0, 1))
        fz = float(np.clip((nariz - z) / max(1e-6, nariz - menton_z), 0, 1))
        dy = menton * fz * max(0.0, cy - y)
        P[i] = (x, y + dy * wf, z + dz * wf)
    # ---- aplanar el frente: de las cejas para abajo la cara no puede sobresalir más que la frente (los maniquíes
    # tienen la boca y el mentón adelantados, como un hocico). Línea objetivo: a la altura de las cejas igual que la
    # frente, y retrocediendo de a poco hasta el mentón (1,2 cm); se empuja hacia atrás lo que sobra, más cuanto más
    # adelante está el punto (la nuca y los costados no se mueven).
    if aplanar:
        H2 = P[cab]
        z_ceja = ojos + 0.06 * alto
        banda = np.abs(H2[:, 2] - z_ceja) < 0.012 * u
        y_frente = H2[banda][:, 1].min() if banda.any() else H2[:, 1].min()
        for i in cab:
            x, y, z = P[i]
            if z >= z_ceja or z < z_cuello:
                continue
            f = float(np.clip((z_ceja - z) / max(1e-6, z_ceja - menton_z), 0, 1.3))
            y_obj = y_frente + 0.012 * u * f * aplanar
            # frente de la cara a esta altura
            fila = np.abs(P[cab][:, 2] - z) < 0.006 * u
            y_f = P[cab][fila][:, 1].min() if fila.any() else y
            sobra = y_obj - y_f
            if sobra <= 0:
                continue
            w = float(np.clip((cy - y) / max(1e-6, cy - y_f), 0, 1)) ** 1.5
            P[i, 1] = y + sobra * w * min(1.0, aplanar)
    # ---- alisar la cara: el modelo trae ondulaciones (pozos y lomos) en mejillas y mentón, y el recorte de arriba
    # deja pequeños escalones. Alisado de Taubin (no achica) sólo en la cara, apagándose hacia el cráneo y el cuello.
    if alisar:
        vec = {}
        for poly in malla.data.polygons:
            vs = list(poly.vertices)
            for k in range(len(vs)):
                a_, b_ = vs[k], vs[(k + 1) % len(vs)]
                vec.setdefault(a_, set()).add(b_)
                vec.setdefault(b_, set()).add(a_)
        cab_set = set(cab)
        z_top_cara = ojos + 0.10 * alto
        peso = {}
        for i in cab:
            x, y, z = P[i]
            if z < z_cuello - 0.01 * u or z > z_top_cara + 0.03 * u:
                continue
            adelante = float(np.clip((cy - y) / (0.25 * D) + 0.2, 0, 1))
            alto_w = float(np.clip((z_top_cara + 0.03 * u - z) / (0.03 * u), 0, 1)) * \
                float(np.clip((z - (z_cuello - 0.01 * u)) / (0.03 * u), 0, 1))
            w = adelante * alto_w
            if w > 0:
                peso[i] = w
        idx = np.array(sorted(peso))
        W = np.array([peso[i] for i in idx])
        vecs = [np.array([j for j in vec.get(i, ()) if j in cab_set], dtype=np.int64) for i in idx]
        for it in range(int(alisar)):
            for lam in (0.55, -0.58):
                Q = P.copy()
                for k, i in enumerate(idx):
                    if len(vecs[k]):
                        Q[i] = P[i] + (P[vecs[k]].mean(axis=0) - P[i]) * lam * W[k]
                P = Q
    Mi = np.array(M.inverted())
    co = P @ Mi[:3, :3].T + Mi[:3, 3]
    malla.data.vertices.foreach_set("co", co.astype(np.float32).ravel())
    malla.data.update()


def preparar(pj: dict, spec: dict, fps: int, nf: int, otros: dict | None = None):
    """Cara dibujada (sistema Stickman, estilo anime realista), pelo modelado y traje de un humano recién creado
    por personajes._crear_mixamo. La cabeza es la ORIGINAL del maniquí."""
    from estudio.blender import cara_anime as CA, pelo_modelo as PM, ropa_humana as RH, stickman as SM
    from estudio.blender.cabeza_mh import material_piel
    perfil = {**PERFILES[spec["modelo"]], **spec.get("perfil", {})}
    pj["coleccion"] = pj["malla"].users_collection[0]
    pj["u"] = 1.0 / pj["raiz"].scale.x                      # 1 metro real en unidades del modelo
    pj["perfil"] = perfil
    piel = material_piel(f"piel_{pj['id']}", perfil["piel"], 0.5)
    pj["malla"].data.materials.clear()
    pj["malla"].data.materials.append(piel)
    if perfil.get("acortar_cara", 0.17):
        esculpir_cara(pj, perfil.get("acortar_cara", 0.17), perfil.get("menton_atras", 0.10),
                      perfil.get("aplanar_cara", 1.0), perfil.get("alisar_cara", 40))
    pj["cabeza_humana"] = _cabeza_propia(pj)
    partes = CA.armar(pj, perfil.get("cara", "el" if perfil["genero"] > 0.5 else "ella"), perfil, pj["coleccion"])
    pj["cara"] = partes
    cara = dict(spec.get("cara", {}))
    cara["habla"] = [{**h, "audio": ruta_audio(h["audio"])} if h.get("audio") else h for h in cara.get("habla", [])]
    CA.actuar(partes, cara, fps, nf, semilla=sum(map(ord, pj["id"])))
    if perfil.get("pelo_modelo"):
        PM.poner(pj, perfil["pelo_modelo"], perfil["pelo"], perfil.get("pelo_holgura", 1.12))
    RH.vestir(pj, perfil.get("vestuario", []))
    return pj


def ruta_audio(ruta: str) -> str:
    """Las voces se guardan con la ruta relativa al repositorio; acá se resuelve donde esté el repo."""
    from pathlib import Path
    from estudio import config
    p = Path(ruta)
    return str(config.ruta_recurso(p))
