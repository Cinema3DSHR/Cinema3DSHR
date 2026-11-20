# p016 · Dream Racing — McLaren F1: SHOCKWAVE
60 s · 720×1280 · 30 fps · 1800 cuadros. El McLaren F1 del GLB del dueño atraviesa una avenida de vidrieras; su onda expansiva rompe los vidrios en cascada.

## El auto (`blender/coche.py`)
- GLB original sin deformar ni cambiar texturas (sólo se agregó barniz/brillo a la pintura y emisión a los faros y pilotos). Versión F1: las piezas [LM] y las alternativas «(2)» quedan ocultas en una colección aparte, no borradas.
- **Ruedas del lado izquierdo:** el GLB trae sólo las dos del derecho. Se copiaron y se **giraron 180° alrededor de la vertical** (no espejadas), con el pivote en el centro de cada rueda, a la misma altura y distancia del eje. Verificado con renders de ambos costados.
- **Matrículas «3D SHR»** adelante y atrás (textura propia; la trasera usa el rectángulo del modelo, la delantera es una placa nueva sobre el paragolpes).
- Orientación: frente −Y, derecha −X, izquierda +X; el coche avanza hacia su frente.

## Escena
Avenida (`ciudad.py`), física por Python+numpy horneada a claves (`efectos.py`: 2580 fragmentos de vidrio, hojas, piedras, polvo, líneas de flujo), cámaras (`camaras.py`), audio (`audio.py`).
