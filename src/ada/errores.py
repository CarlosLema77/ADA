"""Errores propios del proyecto, con mensajes pensados para leerse sin ver el código."""


class ErrorDeEntrada(ValueError):
    """El archivo de entrada no cumple el formato esperado."""


class InstanciaInfactible(ValueError):
    """La instancia no tiene solución (por ejemplo, una categoría que ninguna interacción cubre)."""

    def __init__(self, mensaje, categorias_sin_cubrir=()):
        super().__init__(mensaje)
        self.categorias_sin_cubrir = list(categorias_sin_cubrir)
