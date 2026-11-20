"""p016 «McLaren F1: SHOCKWAVE» · tiempos (30 fps, 1800 cuadros = 60 s). El coche mira y avanza hacia −Y; la avenida corre a lo largo de Y."""
FPS = 30
TOTAL = 1800
# mapa de tiempo de simulación: tiempo real hasta que el coche pasa junto a la cámara (cuadro 530), después cámara lenta extrema y regreso a velocidad normal al final
KNOTS_T = [(0, 0.0), (530, 17.667), (545, 18.15), (570, 18.35), (1440, 21.5), (1620, 22.6), (1800, 24.8)]
Y0 = 645.0           # posición inicial del coche (m); pasa por y = 0 en t = 17,667 s
X_CARRIL = 3.0
CUADRO_PASO = 530
