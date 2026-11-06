"""Lectura y validación de casos de auditoría en JSON.

Formato (ver docs/formatos.md):
{
  "nombre": "opcional",
  "r": 4,
  "interacciones": [
    {"id": "I1", "categorias": [1, 2]},
    {"id": "I2", "categorias": [2, 3], "costo": 5}
  ]
}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .modelo import EntradaInvalida, InstanciaAuditoria, Interaccion


def _es_entero(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def instancia_desde_dict(datos: Dict[str, Any], nombre_por_defecto: str = "caso") -> InstanciaAuditoria:
    if not isinstance(datos, dict):
        raise EntradaInvalida("El caso debe ser un objeto JSON.")
    r = datos.get("r")
    if not _es_entero(r) or r < 1:
        raise EntradaInvalida(f"'r' debe ser un entero ≥ 1 (se recibió {r!r}).")
    crudas = datos.get("interacciones")
    if not isinstance(crudas, list) or not crudas:
        raise EntradaInvalida("'interacciones' debe ser una lista no vacía.")

    vistos: set = set()
    interacciones: List[Interaccion] = []
    for pos, it in enumerate(crudas, start=1):
        if not isinstance(it, dict):
            raise EntradaInvalida(f"Interacción #{pos}: debe ser un objeto.")
        ident = str(it.get("id", f"I{pos}"))
        if ident in vistos:
            raise EntradaInvalida(f"Interacción #{pos}: id repetido {ident!r}.")
        vistos.add(ident)
        cats = it.get("categorias")
        if not isinstance(cats, list):
            raise EntradaInvalida(f"Interacción {ident}: 'categorias' debe ser una lista.")
        for k in cats:
            if not _es_entero(k) or not 1 <= k <= r:
                raise EntradaInvalida(
                    f"Interacción {ident}: categoría {k!r} fuera de rango [1, {r}]."
                )
        if len(set(cats)) != len(cats):
            raise EntradaInvalida(f"Interacción {ident}: categorías repetidas {cats}.")
        costo = it.get("costo")
        if costo is not None and (isinstance(costo, bool) or not isinstance(costo, (int, float)) or costo <= 0):
            raise EntradaInvalida(f"Interacción {ident}: 'costo' debe ser un número > 0.")
        interacciones.append(Interaccion(ident, tuple(sorted(cats)), costo))

    nombre = str(datos.get("nombre", nombre_por_defecto))
    return InstanciaAuditoria(nombre, r, tuple(interacciones))


def es_formato_profesora(datos: Any) -> bool:
    return isinstance(datos, dict) and "etapas" in datos and "categorias_riesgo" in datos


def instancia_desde_formato_profesora(datos: Dict[str, Any], nombre: str) -> InstanciaAuditoria:
    """Convierte un caso de la profesora (ej. entrada_G3_mochila_20_nodos.json).

    - Categorías: `categorias_riesgo`, numeradas 1..r en el orden del archivo;
      se conservan sus ids originales ("R01", ...) como etiquetas.
    - Interacciones: cada etapa es una interacción candidata y cubre
      `riesgos_cubiertos_auditoria_completa` (problema base de la Parte 2).
    """
    cats = datos["categorias_riesgo"]
    if not isinstance(cats, list) or not cats:
        raise EntradaInvalida("'categorias_riesgo' debe ser una lista no vacía.")
    etiquetas = [str(c.get("id")) for c in cats]
    if len(set(etiquetas)) != len(etiquetas):
        raise EntradaInvalida(f"Ids de categoría repetidos: {etiquetas}")
    numero = {e: k for k, e in enumerate(etiquetas, start=1)}

    r_declarado = datos.get("parametros", {}).get("numero_categorias_riesgo")
    if r_declarado is not None and r_declarado != len(etiquetas):
        raise EntradaInvalida(
            f"parametros.numero_categorias_riesgo = {r_declarado}, pero hay {len(etiquetas)} categorías.")

    interacciones = []
    for pos, etapa in enumerate(datos["etapas"], start=1):
        ident = etapa.get("id", f"E{pos}")
        riesgos = etapa.get("riesgos_cubiertos_auditoria_completa")
        if not isinstance(riesgos, list):
            raise EntradaInvalida(f"Etapa {ident}: falta 'riesgos_cubiertos_auditoria_completa'.")
        desconocidos = [x for x in riesgos if x not in numero]
        if desconocidos:
            raise EntradaInvalida(f"Etapa {ident}: riesgos que no existen en 'categorias_riesgo': {desconocidos}")
        interacciones.append({"id": ident, "categorias": [numero[x] for x in riesgos]})

    inst = instancia_desde_dict({"r": len(etiquetas), "interacciones": interacciones}, nombre)
    return InstanciaAuditoria(nombre, inst.r, inst.interacciones, tuple(etiquetas))


def leer_instancia(ruta: str | Path) -> InstanciaAuditoria:
    ruta = Path(ruta)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise EntradaInvalida(f"{ruta.name}: JSON mal formado ({e}).") from e
    if es_formato_profesora(datos):
        return instancia_desde_formato_profesora(datos, ruta.stem)
    return instancia_desde_dict(datos, nombre_por_defecto=ruta.stem)
