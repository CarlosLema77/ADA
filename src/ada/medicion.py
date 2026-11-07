"""Medición de tiempo por caso: varias repeticiones y mediana."""

import statistics
import time


def medir(funcion, repeticiones=5):
    """Ejecuta `funcion()` varias veces. Devuelve (resultado_de_la_ultima, estadisticas_en_ms)."""
    tiempos = []
    resultado = None
    for _ in range(max(1, repeticiones)):
        inicio = time.perf_counter_ns()
        resultado = funcion()
        tiempos.append((time.perf_counter_ns() - inicio) / 1e6)
    return resultado, {
        "repeticiones": len(tiempos),
        "mediana_ms": round(statistics.median(tiempos), 4),
        "minimo_ms": round(min(tiempos), 4),
        "maximo_ms": round(max(tiempos), 4),
    }
