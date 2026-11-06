"""Algoritmo voraz para la cobertura mínima de auditoría (Set Cover).

En cada paso elige la interacción que cubre más categorías todavía no cubiertas.

Desempate (fijo y documentado): si varias empatan en ganancia, gana la que
aparece primero en el archivo de entrada (menor posición). Se implementa con la
comparación estricta `ganancia > mejor_ganancia`.

El código sigue el pseudocódigo de docs/parte2_formalizacion.md línea a línea,
para que el conteo de operaciones de T(n, r) se lea directamente aquí.
"""
from __future__ import annotations

from typing import List

from .factibilidad import verificar_factibilidad
from .modelo import InstanciaAuditoria, PasoVoraz, ResultadoCobertura


def cobertura_voraz(inst: InstanciaAuditoria, con_traza: bool = True) -> ResultadoCobertura:
    verificar_factibilidad(inst)                      # O(n·r)
    n, r = inst.n, inst.r
    S = [it.categorias for it in inst.interacciones]

    cubierta = [False] * (r + 1)                      # L1: O(r)
    elegida = [False] * n                             # L2: O(n)
    faltan = r                                        # L3
    seleccion: List[int] = []
    traza: List[PasoVoraz] = []

    while faltan > 0:                                 # L4: p + 1 veces, p ≤ min(n, r)
        mejor, mejor_ganancia = -1, 0                 # L5
        ganancias = [0] * n if con_traza else None
        for j in range(n):                            # L6: n por vuelta
            if elegida[j]:                            # L7
                continue
            g = 0                                     # L8
            for k in S[j]:                            # L9: |S_j| por interacción
                if not cubierta[k]:                   # L10
                    g += 1
            if ganancias is not None:
                ganancias[j] = g
            if g > mejor_ganancia:                    # L11: estricto => desempate por menor posición
                mejor, mejor_ganancia = j, g
        # mejor != -1 está garantizado por la factibilidad (L12)
        elegida[mejor] = True                         # L13
        seleccion.append(mejor)
        nuevas = []
        for k in S[mejor]:                            # L14: |S_mejor|
            if not cubierta[k]:
                cubierta[k] = True
                nuevas.append(k)
        faltan -= len(nuevas)

        if con_traza:
            empatadas = [inst.interacciones[j].id for j in range(n)
                         if j != mejor and not elegida[j] and ganancias[j] == mejor_ganancia]
            traza.append(PasoVoraz(
                paso=len(seleccion),
                elegida=inst.interacciones[mejor].id,
                ganancia=mejor_ganancia,
                categorias_nuevas=nuevas,
                cubiertas_acumuladas=r - faltan,
                faltantes=[k for k in range(1, r + 1) if not cubierta[k]],
                empatadas=empatadas,
            ))

    ids = [inst.interacciones[j].id for j in seleccion]
    return ResultadoCobertura("voraz", ids, len(ids), traza)
