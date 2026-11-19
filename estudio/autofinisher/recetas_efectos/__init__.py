"""Biblioteca de recetas de efectos (bpy). Cada receta reconstruye en Blender algo que el GLB no transfiere
(partículas, volúmenes) a partir del vacío FX_* que exporta Godot, y depende SÓLO del número de cuadro: no simula ni
hornea nada, así que cualquier trabajo de render puede empezar en cualquier cuadro y el resultado es el mismo.

Contrato: `aplicar(ancla, parametros, ctx) -> dict`
  ancla       objeto vacío de Godot (su posición/orientación) o None si la receta no lo necesita (relámpago)
  parametros  los de la receta de terminación (se completan con PARAMETROS_POR_DEFECTO de cada módulo)
  ctx         Contexto: fps, colecciones de efectos y auxiliares ocultos, receta completa

Recetas disponibles (las que ya se usaron en una escena real; agregar otras sólo cuando el dueño las pida):
  lluvia     gotas que caen en bucle con viento y se cortan contra superficies elegidas (nodos de geometría)
  fuego      volumen emisivo con ruido 4D que sube y se angosta arriba
  humo       volumen gris que sube
  brasas     chispas emisivas que suben con vaivén y se achican
  relampago  refuerza la emisión del rayo animado que ya viaja en el GLB y le quita la sombra
"""
from __future__ import annotations

from importlib import import_module

RECETAS = ("lluvia", "fuego", "humo", "brasas", "relampago")


def receta(nombre: str):
    if nombre not in RECETAS:
        raise KeyError(f"no hay receta de efecto «{nombre}» (disponibles: {', '.join(RECETAS)})")
    return import_module(f"estudio.autofinisher.recetas_efectos.{nombre}")
