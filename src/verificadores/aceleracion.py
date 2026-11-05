"""Verificador independiente de la Parte 1 (tarea 3-3d, lo escribe B y revisa A).

No importa nada del código de A: solo lee el caso y la salida según el contrato de
docs/formatos.md y comprueba:
  1. Las etapas aceleradas existen y no se repiten.
  2. El costo total ≤ B.
  3. Los totales reportados (costo, reducción, duración) coinciden con lo recalculado.
  4. (Opcional, n ≤ 20) La reducción es óptima, comparando con fuerza bruta 2^n.

Uso:
  python -m src.verificadores.aceleracion CASO.json SALIDA.json
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List


def _optimo_fuerza_bruta(etapas: List[Dict[str, Any]], B: int) -> int:
    n, mejor = len(etapas), 0
    for k in range(1, n + 1):
        for combo in combinations(range(n), k):
            costo = sum(etapas[i]["c"] for i in combo)
            if costo <= B:
                mejor = max(mejor, sum(etapas[i]["d"] for i in combo))
    return mejor


def normalizar_caso(caso: Dict[str, Any]) -> Dict[str, Any]:
    """Acepta el formato propio ({B, etapas:[{id,t,c,d}]}) o el de la profesora."""
    if "parametros" in caso and caso["etapas"] and "duracion_normal" in caso["etapas"][0]:
        return {"B": caso["parametros"]["presupuesto_aceleracion_B"],
                "etapas": [{"id": e["id"], "t": e["duracion_normal"], "c": e["costo_aceleracion"],
                            "d": e["reduccion_tiempo_si_acelera"]} for e in caso["etapas"]]}
    return caso


def verificar(caso: Dict[str, Any], salida: Dict[str, Any], max_n_optimo: int = 20) -> List[str]:
    """Devuelve la lista de errores encontrados (vacía si todo está bien)."""
    caso = normalizar_caso(caso)
    errores: List[str] = []
    etapas = caso["etapas"]
    B = caso["B"]
    por_id = {str(e["id"]): e for e in etapas}

    elegidas = [str(x) for x in salida["etapas_aceleradas"]]
    if len(set(elegidas)) != len(elegidas):
        errores.append(f"Etapas aceleradas repetidas: {elegidas}")
    desconocidas = [x for x in elegidas if x not in por_id]
    if desconocidas:
        errores.append(f"Etapas que no existen en el caso: {desconocidas}")
        return errores

    costo = sum(por_id[x]["c"] for x in set(elegidas))
    reduccion = sum(por_id[x]["d"] for x in set(elegidas))
    duracion = sum(e["t"] for e in etapas) - reduccion

    if costo > B:
        errores.append(f"Excede el presupuesto: costo {costo} > B = {B}")
    for campo, real in (("costo_total", costo), ("reduccion_total", reduccion), ("duracion_total", duracion)):
        if campo in salida and salida[campo] != real:
            errores.append(f"{campo} reportado = {salida[campo]}, recalculado = {real}")

    if len(etapas) <= max_n_optimo:
        opt = _optimo_fuerza_bruta(etapas, B)
        if reduccion != opt:
            errores.append(f"No es óptima: reducción {reduccion}, la fuerza bruta logra {opt}")
    return errores


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("caso")
    p.add_argument("salida")
    p.add_argument("--max-n-optimo", type=int, default=20)
    a = p.parse_args(argv)
    caso = json.loads(Path(a.caso).read_text(encoding="utf-8"))
    salida = json.loads(Path(a.salida).read_text(encoding="utf-8"))
    errores = verificar(caso, salida, a.max_n_optimo)
    if errores:
        print("FALLA:\n  - " + "\n  - ".join(errores))
        return 1
    print("OK: respeta el presupuesto, los totales coinciden" +
          (" y la reducción es óptima." if len(caso["etapas"]) <= a.max_n_optimo else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
