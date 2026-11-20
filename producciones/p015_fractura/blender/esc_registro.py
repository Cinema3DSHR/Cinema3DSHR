"""Registro de constructores de escena."""
import importlib

ESCENAS_CONSTRUCTORES = {}
for _sid, _mod in (("s0", "esc_s0"), ("s1", "esc_s1"), ("s2", "esc_s2"), ("s3", "esc_s3"), ("s4", "esc_s4"), ("s5", "esc_s5"), ("s6", "esc_s6"), ("s7", "esc_s7"), ("s8", "esc_s8")):
    try:
        ESCENAS_CONSTRUCTORES[_sid] = importlib.import_module(_mod).construir
    except ModuleNotFoundError:
        pass
