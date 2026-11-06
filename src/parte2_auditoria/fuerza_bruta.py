"""Óptimo exacto por fuerza bruta: prueba subconjuntos de tamaño 1, 2, 3, ...

Sirve para verificar el voraz en instancias pequeñas (cota H(d)) y es la base del
algoritmo exacto de la segunda entrega. Peor caso: Σ_{k=1}^{n} C(n,k) = 2^n - 1
subconjuntos, cada uno con un OR de hasta k máscaras: O(2^n · n) operaciones
sobre enteros de r bits.
"""
from __future__ import annotations

from itertools import combinations

from .factibilidad import verificar_factibilidad
from .modelo import InstanciaAuditoria, ResultadoCobertura


def cobertura_optima_fuerza_bruta(inst: InstanciaAuditoria) -> ResultadoCobertura:
    verificar_factibilidad(inst)
    mascaras = []
    for it in inst.interacciones:
        m = 0
        for k in it.categorias:
            m |= 1 << (k - 1)
        mascaras.append(m)
    universo = (1 << inst.r) - 1

    probados = 0
    for tam in range(1, inst.n + 1):
        for combo in combinations(range(inst.n), tam):   # orden lexicográfico
            probados += 1
            union = 0
            for j in combo:
                union |= mascaras[j]
            if union == universo:
                ids = [inst.interacciones[j].id for j in combo]
                return ResultadoCobertura("fuerza_bruta", ids, tam, subconjuntos_probados=probados)
    raise AssertionError("inalcanzable: la instancia es factible")
