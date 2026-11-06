"""Chequeo de factibilidad: ¿la unión de todas las S_j es U = {1..r}?

Costo: O(r) para inicializar + O(s) para recorrer los subconjuntos + O(r) para
listar faltantes, con s = Σ|S_j| ≤ n·r. Total O(n·r), como exige el PDF (4.3).
"""
from __future__ import annotations

from typing import List

from .modelo import InstanciaAuditoria, InstanciaNoFactible


def categorias_sin_cubrir(inst: InstanciaAuditoria) -> List[int]:
    cubierta = [False] * (inst.r + 1)
    for it in inst.interacciones:
        for k in it.categorias:
            cubierta[k] = True
    return [k for k in range(1, inst.r + 1) if not cubierta[k]]


def verificar_factibilidad(inst: InstanciaAuditoria) -> None:
    """Lanza InstanciaNoFactible con las categorías huérfanas si no es factible."""
    faltantes = categorias_sin_cubrir(inst)
    if faltantes:
        raise InstanciaNoFactible(faltantes)


def es_cobertura(inst: InstanciaAuditoria, ids: List[str]) -> bool:
    """¿Las interacciones con estos ids cubren las r categorías?"""
    por_id = {it.id: it for it in inst.interacciones}
    cubierta = [False] * (inst.r + 1)
    for i in ids:
        for k in por_id[i].categorias:
            cubierta[k] = True
    return all(cubierta[1:])
