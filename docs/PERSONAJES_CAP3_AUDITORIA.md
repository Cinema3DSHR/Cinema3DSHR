# Auditoría de los personajes nuevos (capítulo 3) — 22/11/2026

Origen: 5 partes RAR (`Download.part1–5`) → `Blender2.0.rar`, `Blender3.zip`, `fbx.zip`, `fbx (1).zip`. Son DOS personajes (no tres), cada uno en dos formatos. Todo lo de abajo se probó con los archivos; scripts en `pruebas/personajes_cap3/`. Los modelos y las fotos no van al repo.

| Personaje | Archivos | Origen |
|---|---|---|
| Hombre | `Man03.blend` (rig Rigify, 725 huesos) · `fbx.zip` → `fbx.fbx` (carpeta `Man01.fbm`, 101 huesos) | Character Creator 4 → Blender/FBX |
| Mujer | `Blender2.0.blend` (rig Rigify «5_Rigify») · `fbx (1).zip` → `fbx.fbx` (carpeta `woman03.fbm`, 101 huesos) | ídem |

Nota: el FBX masculino se llama «Man01» y el .blend «Man03»: misma base (14.164 vértices de cuerpo, mismas shape keys), pero no se verificó que sean idénticos de cara/pelo.

## Ficha común (hombre y mujer)
- **Geometría:** cuerpo 14.164 vértices / 28.092 triángulos, dientes 4.842, lengua 592, ojos 1.280, oclusión de ojos y línea de lágrima, pelo 16–18 mil triángulos (hombre «Slicked_Back_Side», mujer «HAIR_»), ropa interior (boxer / corpiño + bombacha). Total ≈ 53–56 mil triángulos. Malla limpia y nítida en las fotos; UV `Channel0` en todas las piezas. No se redujo nada.
- **Materiales:** shaders de Character Creator (grupos `rl_head_shader`, `rl_pbr_shader`, `rl_eye_shader`) con mapas de máscara, normales, SSS, etc. **No traen texturas de color (Diffuse) de piel ni pelo**: por eso se ven grises. El color es un parámetro (`Diffuse Color`, `Iris Color`…): se probó y funciona (foto 3).
- **Esqueleto:** .blend → Rigify (controles IK/FK, 179 huesos de deformación, mandíbula, lengua, ojos). FBX → esqueleto estándar de CC4 de 101 huesos (Hip, Pelvis, Waist, Spine01/02, Clavicle, Upperarm, Forearm, Hand + dedos, Thigh, Calf, Foot, ToeBase, JawRoot, Tongue01–03, L/R_Eye, UpperJaw, huesos de torsión). Compatible con Mixamo.
- **Rostro:** 122 shape keys en el cuerpo (9 visemas `V_*`: Open, Explosive, Dental_Lip, Tight_O, Tight, Wide, Affricate, Lip_Open, None; cejas, párpados, mejillas, nariz, ~40 de boca y labios, serie `A01–A51` estilo ARKit), lengua 20, ojos/lágrima/oclusión 79–81, cejas/pelo de la mujer 160. Párpados, parpadeo y mirada (huesos de ojo independientes) funcionan.
- **Importante:** los shape keys vienen con una acción «Calibration» que los pisa en cada cuadro; hay que quitarla (`shape_keys.animation_data.action = None`) antes de animarlos. La boca abierta de verdad se hace con el hueso de mandíbula (`jaw_master` en Rigify, `JawRoot` en el FBX) + visemas; sólo con shape keys la boca queda casi cerrada (los visemas son sutiles).

## Pruebas hechas
1. **Expresiones** (neutra, sonrisa, sorpresa, enojo, tristeza, ojos cerrados) y **12 formas de boca** (A, O, U, M/B/P, F, E + boca grande): sin deformaciones defectuosas en primer plano.
2. **Mirada** a izquierda/derecha: bien; arriba/abajo con el control `eyes` es muy sutil (ajustar rango).
3. **Color:** piel, pelo, cejas e iris cambiados por parámetro.
4. **Traje espacial en Blender:** se genera automáticamente a partir del cuerpo (sin cabeza/manos/pies, inflado 1 cm, solidify) y **se deforma con el mismo esqueleto**. Es un mono liso de prueba; guantes, botas, cuello, paneles y logos hay que modelarlos/texturizarlos.
5. **Mixamo:** retarget por dirección de huesos (52 huesos mapeados de 52) sobre el esqueleto CC del FBX, con hombre y mujer: caminar, gestos de conversación (hombre), sentada con saludo (mujer). Orientación correcta (miran hacia donde caminan).
6. **Godot 4.7.2:** el GLB exportado desde Blender conserva 101 huesos, 121 blend shapes en el cuerpo (459 en total), y las animaciones de huesos y de blend shapes; al reproducir, `V_Open` llegó a 0,96 en el cuadro esperado. Detalle: el exportador deja una animación por malla (hay que exportar «escena» para tener una sola) y los clips de Mixamo se retargetean en Blender antes de exportar; el retarget nativo de Godot (BoneMap) no se probó.

## Clasificación
- **Hombre: APTO CON LIMITACIONES.** Cara, labios y rig muy buenos. Limitaciones: sin colores de piel/pelo (hay que definirlos), el pelo es de ~17 mil triángulos con transparencia (más lento en Godot), ropa sólo ropa interior, hay que modelar el traje, y los visemas necesitan el hueso de mandíbula para abrir la boca.
- **Mujer: APTO CON LIMITACIONES.** Misma capacidad facial; además cejas/ojos funcionales. Mismas limitaciones (sin color, pelo escultórico sin texturas, ropa interior); la silueta del traje de prueba es muy ceñida: ajustar para no exagerar.
- No se probó: sincronización labial con voz real en español (la cadena existe en la serie: alineaciones por letra → visemas), peso/costo de render del pelo, ni el retarget nativo de Godot.

## Reparto decidido por el dueño (23/11/2026)
- **Aiden** = modelo masculino (`Man03`). **Kate** = modelo nuevo («Woman01», pelo de mechones reales: flequillo, rodete doble y pelo largo; 62 mil triángulos). **EVA** = el modelo femenino anterior (pelo rígido), como HOLOGRAMA transparente (sin objeto que lo proyecte) que aparece, habla y se mueve con animaciones de Mixamo y expresiones faciales.
- **Kate (probada):** mismas shape keys que los otros (122 + 160 + 81…); labios, expresiones, color de piel/pelo (por `Diffuse Color`), traje espacial de prueba y física del pelo (tela con raíces fijas: flequillo, pelo y rodetes por separado) funcionan. Pendientes: cejas (`Female_Flat*`) salían blancas (ya corregido en los scripts, falta repetir las fotos), blanco de los ojos con tinte rosado, interior de la boca oscuro con la boca muy abierta.
- **EVA holograma (probado):** material propio (`pruebas/personajes_cap3/eva.py`): transparencia por Fresnel, líneas de barrido, traje holográfico, ojos con textura emisiva, animación Mixamo (retarget) y parpadeo/habla por shape keys. Falta definición del rostro (nariz y labios), parpadeo/glitch del holograma y su integración en la escena.

## Avances 23/11/2026 (pedido del dueño)
- **Pelo con física continua** (`pelo3.py`): tela con raíces fijas y gravedad; probado con la cabeza mirando abajo y arriba (con pausas): el flequillo cuelga hacia delante al mirar abajo y se abre al mirar arriba; los rodetes acompañan. Sin movimientos bruscos. Aiden y Kate (EVA no tiene el pelo simulado: pelo rígido).
- **Color real** (`colores.py`): piel, pelo, cejas y pestañas por material (versión FBX); fotos de Kate (piel clara, pelo castaño rojizo, cejas y pestañas oscuras, ojos verdes) y Aiden (piel, pelo castaño oscuro).
- **EVA holograma que se construye** (`holo_eva.py`, `eva2.py`): aparece azul de los pies a la cabeza con una línea brillante, se vuelve real (piel, pelo y ojos con sus texturas) también de abajo hacia arriba, parpadea como proyección y se disuelve de arriba hacia abajo. En el estado holográfico no se ve el interior de ojos ni boca (dientes, lengua y córneas quedan ocultos). Escala libre: miniatura sobre la mesa o tamaño real.
- **Guion propuesto del cap. 3** (`producciones/p011_a_la_deriva/herramientas/guion_e03.py`, 33 líneas, 2.240 caracteres), con voces `aiden_es_ar`, `kate_es_ar` y `eva` (las del E02). Sin generar audio todavía.
- **Paquete «Serie especial»** (recibido 23/11): catálogo de Sweet Home 3D con ~78 modelos OBJ (enfermería, laboratorio, consolas, puertas, paneles de pasillo, silla Burke…). Se extrajeron 47; 31 fallaron por archivo incompleto (la parte 2 del RAR parece truncada). Atención: son utilería de *Star Trek (serie original)* (Starfleet, fáser, cráneo klingon, LCARS, transportador): usar sólo piezas genéricas o retexturizar antes de publicar.
