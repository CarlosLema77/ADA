"""Medición de tiempo por caso: varias repeticiones, se reporta la mediana.

Nota para A: en el tablero este módulo (3-3c) es tuyo; esta es una versión mínima
para que la Parte 2 pueda correr ya. Si la cambias, mantén la firma de `medir`.
"""
from __future__ import annotations

import statistics
import time
from typing import Callable, Dict


def medir(funcion: Callable[[], object], repeticiones: int = 5) -> Dict[str, float]:
    funcion()  # calentamiento, no se cuenta
    tiempos = []
    for _ in range(max(1, repeticiones)):
        t0 = time.perf_counter()
        funcion()
        tiempos.append(time.perf_counter() - t0)
    return {
        "mediana_s": statistics.median(tiempos),
        "min_s": min(tiempos),
        "max_s": max(tiempos),
        "repeticiones": len(tiempos),
    }
