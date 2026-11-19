# Prueba técnica Godot → Blender: «Casa moderna en tormenta» (19/11/2026)

Toma de 30 s, 540x960 vertical, 30 fps (900 cuadros). Un solo movimiento de cámara, de derecha a izquierda y sin
cortes: cocina (0–5 s) → mesas y living (5–10 s) → ventilador (10–14 s) → ventanal, calle, farolas, lluvia y la
camioneta (14–21 s) → tormenta y relámpagos (21–26 s) → hogar (26–30 s).
Por pedido del dueño, el jardín se reemplazó por la **CÓNDOR Kodiak Raid** de Dream Racing (`kodiak.glb`, la camioneta
del arco de hierro en la caja, 958 mil triángulos). Está estacionada en la calle, de cola al ventanal, entre dos
farolas, y le cae la lluvia encima.
**No se hizo ningún render ni se usó GitHub Actions.**

## Entregables

| Qué | Dónde |
|---|---|
| Proyecto de Godot editable | `pruebas/godot_blender/godot/`: `escena/casa_tormenta.tscn` y los scripts de cada etapa en `herramientas/`. La Kodiak no va a Git: se copia de `Rally-Sim-movile/godot/game/models/cars/kodiak.glb` a `godot/modelos/`. También se manda comprimido por el chat. |
| GLB exportado | `godot/salida/casa_tormenta.glb` (47 MB), mandado por el chat. Para Android hay uno liviano con la `kodiak_lo` (2 MB). |
| Proyecto de Blender editable | `blender/casa_tormenta.blend` (37 MB, autónomo), mandado por el chat. Se rehace con `blender/armar.py`. |
| Tiempos | `tiempos.jsonl` (hora UTC de inicio y fin de cada etapa) y `blender/casa_tormenta.json` (segundos de cada script). |
| Qué llegó a Blender | `blender/importado.json` (inspección automática del GLB recién importado). |
| Previa liviana | `previa_godot.mp4`: captura en tiempo real del visor de Godot, **no es el render de Cycles**. |

Cómo rehacer todo:

```bash
cd pruebas/godot_blender/godot && godot --headless --path . -s herramientas/construir.gd
```

```bash
cd pruebas/godot_blender && /opt/tools/blendenv/bin/python blender/armar.py godot/salida/casa_tormenta.glb blender/casa_tormenta.blend
```

## Tiempos reales por etapa

Los tiempos de reloj son los de mi trabajo, anotados con `marca.sh`: escribir, probar, mirar capturas y corregir. Los
tiempos de máquina son lo que tarda el script una vez escrito.

| # | Etapa | Reloj | Máquina | Automático / manual |
|---|---|---|---|---|
| 0 | Elegir el vehículo (el RAR de GTA no sirvió → Kodiak) | ~7 min | — | manual |
| 1 | Construcción en Godot | 4 min 08 s | 0,28 s | manual (script por escena) |
| 2 | Materiales e iluminación | 1 min 05 s | 0,004 s | manual (53 materiales, 7 neones, 16 luces) |
| 3 | Animación | 2 min 48 s | 0,015 s | manual (incluye el arreglo de los edificios que tapaban el cielo) |
| 4 | Preparación de efectos (Godot) | 1 min 31 s | 0,018 s | manual |
| 5 | Exportación GLB | 10 s (+1 min para el liviano) | 1,55 s | **automático** (GLTFDocument) |
| 6 | Importación en Blender | 2 min 25 s | 2,4 s | **automático** (importador glTF) + inspección |
| 7 | Corrección de materiales y luces | ~1 min ¹ | 0,0 s | manual (reglas generales, no por objeto) |
| 8 | Efectos en Blender | 4 min 41 s ² | 0,3 s | manual |
| 9 | Preparación final para Cycles | ~1 min ² | 0,01 s | manual (parámetros del estudio) |
| | **Total de la prueba** | **≈ 25 min** (18 min sin elegir el vehículo) | **≈ 5 s** | |

¹ El script de la etapa 7 lo escribí justo al cerrar la etapa 6; el reloj marca 23 s sólo para probarlo.
² El script de la etapa 9 lo escribí dentro de la ventana de la etapa 8 (su marca da 0 s).

## Lo que pasó bien de Godot a Blender

- **Jerarquía y transformaciones**: 281 nodos con sus nombres (Casa, Cocina, Living, Ventilador → Ventilador_aspas →
  Aspa_n, Hogar, Exterior, Camioneta_Kodiak…). Godot usa Y hacia arriba y Blender Z; el importador lo convierte solo.
- **Geometría**: 220 mallas, 978 mil triángulos. Las primitivas de Godot (cajas, cilindros, esferas) llegan como mallas.
- **La Kodiak**: su malla, su textura (1024², viaja dentro del GLB) y sus ruedas.
- **Materiales PBR**: color, rugosidad, metal, emisión (con su intensidad, por `KHR_materials_emissive_strength`) y la
  textura de la camioneta. Llegaron los 54 materiales.
- **Cámara**: llegó con el campo de visión exacto (68° en vertical, encaje vertical) y sus 901 claves de posición y
  rotación. Están muestreadas cuadro a cuadro y no se deforman.
- **Animaciones**:
  - giro del ventilador: 313 claves de cuaternión;
  - destello del cielo y rayo: claves de escala;
  - **energía del relámpago y del fuego**: llegan por `KHR_animation_pointer`, con un problema de escala (ver abajo).
- **Luces**: llegan las 16 (puntuales, focos de farola y soles) con su tipo, color, posición, dirección y apertura.

## Lo que hubo que rehacer o corregir en Blender

| Elemento | Qué pasó | Qué se hizo |
|---|---|---|
| **fps de la animación** | El importador convierte los segundos con los fps de la escena (24 de fábrica): los 30 s quedaban en 720 cuadros. | Poner 30 fps **antes** de importar (`b6_importar.py`). |
| **Intensidad de las luces** | Godot exporta su «energía» como candelas/lux; Blender la convierte a vatios y quedan en ~0,01 W. | Se recupera la energía de Godot y se pasa a vatios con una escala por tipo (puntual ×60, foco ×120, sol ×0,6). |
| **Claves de energía animadas** | Las de luces puntuales llegan además divididas por 4π (fuego 1,5–2,5 → 0,10–0,16). El sol (relámpago) llega bien. | Factor 4π extra. Medido y verificado: el fuego quedó en 1,7–2,3, como en Godot. |
| **Vidrios** (ventanal, botellas) | Godot los manda con transparencia alfa, sin reflejos ni refracción en Cycles. | Transmisión 1 e IOR 1,45/1,5: el ventanal refleja y refracta. |
| **Ambiente** (WorldEnvironment) | No viaja: llega un vacío. | Mundo de Blender con el mismo azul noche. El «cielo» es la esfera emisiva, que sí llegó. |
| **Lluvia** (9.000 gotas en Godot) | Las partículas no viajan: llega un vacío con su nombre y posición. | Nodos de geometría con la misma caja, cantidad, velocidad (11–14 m/s) y viento (12 cm/m). Las gotas caen en bucle y se cortan al tocar la carrocería de la Kodiak y el techo de la casa. Calcularla cuesta 0,15 s por cuadro. |
| **Colisiones de la lluvia** | Las cajas de colisión de Godot llegan sin tamaño. | Se rehízo la del techo. Para la camioneta se usa su carrocería original: probé copias reducidas al 5 % y al 10 % y quedaban con agujeros (el 8 % y el 3 % de las gotas atravesaban la caja). |
| **Fuego** | Las partículas no viajan. | Volumen con emisión y ruido 4D que sube, más angosto arriba, con rampa rojo → naranja → amarillo. |
| **Humo** | Ídem. | Volumen gris (Principled Volume) que sube del fuego al techo del fogón. |
| **Brasas** | Ídem. | 45 chispas con nodos de geometría (como en Godot) que suben con un vaivén y se achican. |
| **Rayo** | La animación llegó bien (escala). | Sólo se subió su emisión (40 → 60) y se le quitó la sombra. |
| Parámetros de Cycles | — | Los del estudio para 540p (`hd540` vertical, igual que E02), más los pasos de volumen. |

Los efectos de Blender no simulan ni hornean nada: todo depende sólo del número de cuadro. Así cada trabajo de render
puede arrancar en cualquier cuadro y da lo mismo.

## Problemas de compatibilidad encontrados

1. Los **fps** dependen de la escena que recibe (hay que fijarlos antes de importar).
2. Las **unidades de luz** no son equivalentes. Además, las claves animadas por `KHR_animation_pointer` de luces
   puntuales llegan con 1/4π de más (parece un error del importador de Blender 5.3 o del exportador de Godot 4.7).
3. Lo que **no es malla, luz ni cámara** no viaja: partículas, colisiones de partículas, ambiente, niebla y glow.
4. La **transparencia** de Godot no es vidrio en Cycles.
5. Del lado de Godot: `replace_by` mueve los hijos al nodo nuevo. El primer GLB liviano salió con la camioneta pesada
   adentro (49 MB); arreglado, ahora pesa 2 MB.
6. La Kodiak de Dream Racing viene sin ruedas (el juego las arma por código). Se hicieron con las medidas de
   `kodiak.json`: radio 0,4 m, ancho 0,33 m y la posición de los ejes.

## Costo estimado del render final (no medido: no se hizo ningún render de prueba)

- Referencia real: E02 v3 en `video30.yml` a 540x960, 6 muestras, Cycles CPU: 3.998 cuadros en 60 trabajos de 16 a
  24 min, o sea unos **15–20 s por cuadro**.
- Esta escena tiene la misma resolución y muestras, y no tiene personajes. A cambio suma:
  - vidrio con transmisión en gran parte de la toma;
  - dos volúmenes chicos (fuego y humo);
  - 16 luces y neones;
  - la camioneta de 958 mil triángulos;
  - unas 8.000 gotas por cuadro.

  Estimo **20–40 s por cuadro**.
- Total para 900 cuadros: **5 a 10 horas de CPU**.
  - Con 60 trabajos de 15 cuadros cada uno: unos **8–13 min por trabajo**, contando la preparación.
  - Con los ~30 trabajos simultáneos que dio la organización: **unos 15–25 min de reloj**.
  - Son unos 500–800 minutos de Actions. El repositorio es público: no tienen costo.
- Para renderizarlo hace falta un flujo que reciba un `.blend` (`video30.yml` arma la escena desde una receta del
  estudio). Hacerlo y usarlo, sólo con la autorización del dueño.

## Conclusión

Con esta prueba, **Godot sirve para construir y previsualizar rápido** la escena: geometría, materiales, luces, la
cámara y animaciones simples. Lo que viaja por GLB llega casi sin pérdida: jerarquía, mallas, materiales PBR, cámara
con su lente y animaciones de transformación. En cambio, en Blender hay que rehacer siempre:

- los **efectos** (partículas: lluvia, fuego, humo, chispas);
- el **vidrio**;
- el **ambiente**;
- la **escala de las luces**.

Esas reglas ya quedaron en scripts generales (`b7_materiales.py`, `b8_efectos.py`), así que la próxima escena
reutiliza todo y sólo cambia las posiciones, que se toman de los vacíos `FX_*` que exporta Godot.

## Render real (19/11/2026, por orden del dueño)

- Corrida 44464073661 de `render_prueba_godot_blender.yml`: 540x960, 6 muestras, 60 trabajos, 900/900 cuadros sin
  faltantes. Release `prueba_godot_blender` → `casa_tormenta_540p.mp4`.
- **Medido**: 21,75 s por cuadro de media (estimado antes: 20–40). La preparación (Godot → GLB → Blender en Actions)
  tardó 1,5 min. Fueron 14 min de reloj de punta a punta, con hasta 50 trabajos a la vez.
- Para corregir en la próxima prueba: el fuego volumétrico sale tenue en Cycles (se ven más las brasas que las
  llamas); hay que subir su emisión o su densidad.
