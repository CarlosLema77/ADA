"""Modelo de datos de la Parte 2: cobertura mínima de auditoría.

Una instancia tiene:
  - r: número de categorías de riesgo, numeradas 1..r (universo U = {1, ..., r}).
  - n interacciones; la interacción j cubre el subconjunto S_j ⊆ U.
  - costo opcional a_j > 0 por interacción (solo lo usa la variante ponderada).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class EntradaInvalida(ValueError):
    """La instancia no cumple el formato o los rangos esperados."""


class InstanciaNoFactible(ValueError):
    """La unión de todas las interacciones no cubre las r categorías."""

    def __init__(self, faltantes: List[int]):
        self.faltantes = faltantes
        super().__init__(
            "Instancia no factible: ninguna interacción cubre las categorías "
            f"{faltantes}. No existe auditoría que cubra todo."
        )


@dataclass(frozen=True)
class Interaccion:
    id: str
    categorias: Tuple[int, ...]  # ordenadas, sin repetir, en [1, r]
    costo: Optional[float] = None


@dataclass(frozen=True)
class InstanciaAuditoria:
    nombre: str
    r: int
    interacciones: Tuple[Interaccion, ...]
    etiquetas: Optional[Tuple[str, ...]] = None   # nombre original de cada categoría (ej. "R01")

    def etiqueta(self, k: int) -> object:
        """Nombre original de la categoría k (1..r); si no hay, el número."""
        return self.etiquetas[k - 1] if self.etiquetas else k

    @property
    def n(self) -> int:
        return len(self.interacciones)

    @property
    def d(self) -> int:
        """Máximo número de categorías que cubre una sola interacción."""
        return max((len(i.categorias) for i in self.interacciones), default=0)

    @property
    def s(self) -> int:
        """Suma de los tamaños de los subconjuntos (s ≤ n·r)."""
        return sum(len(i.categorias) for i in self.interacciones)


@dataclass
class PasoVoraz:
    paso: int
    elegida: str
    ganancia: int                 # categorías nuevas que cubre
    categorias_nuevas: List[int]
    cubiertas_acumuladas: int
    faltantes: List[int]
    empatadas: List[str]          # otras con la misma ganancia (perdieron por desempate)


@dataclass
class ResultadoCobertura:
    algoritmo: str
    seleccion: List[str]          # ids en el orden en que se eligieron
    tamano: int
    traza: List[PasoVoraz] = field(default_factory=list)
    subconjuntos_probados: Optional[int] = None  # solo fuerza bruta
