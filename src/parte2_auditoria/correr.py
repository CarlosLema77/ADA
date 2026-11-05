"""Corre todos los casos de auditoría de una carpeta y guarda evidencia por caso.

Uso:
  python -m src.parte2_auditoria.correr --casos casos/auditoria --salida resultados/auditoria
  python -m src.parte2_auditoria.correr --casos ejemplos/auditoria --salida resultados/ejemplos_auditoria

Por cada caso X.json escribe en <salida>/X/:
  salida.json  -> selección, tamaño, tiempo, verificación y comparación con el óptimo
  traza.json   -> paso a paso del voraz
y en <salida>/ un resumen.csv y un resumen.md con una fila por caso.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from ..comun.medicion import medir
from .factibilidad import es_cobertura
from .fuerza_bruta import cobertura_optima_fuerza_bruta
from .lector import leer_instancia
from .modelo import EntradaInvalida, InstanciaNoFactible
from .voraz import cobertura_voraz


def armonico(d: int) -> float:
    return sum(1.0 / i for i in range(1, d + 1))


def _paso_con_etiquetas(inst, paso) -> Dict[str, Any]:
    """Traduce los números de categoría a sus ids originales (ej. 3 -> "R03")."""
    d = asdict(paso)
    d["categorias_nuevas"] = [inst.etiqueta(k) for k in paso.categorias_nuevas]
    d["faltantes"] = [inst.etiqueta(k) for k in paso.faltantes]
    return d


def procesar_caso(ruta: Path, carpeta_salida: Path, repeticiones: int, max_n_fb: int) -> Dict[str, Any]:
    fila: Dict[str, Any] = {"caso": ruta.stem}
    try:
        inst = leer_instancia(ruta)
        fila.update(n=inst.n, r=inst.r, d=inst.d)
        resultado = cobertura_voraz(inst, con_traza=True)
    except (EntradaInvalida, InstanciaNoFactible) as e:
        fila["estado"] = f"ERROR: {e}"
        return fila

    # El tiempo se mide sin generar traza, para no inflarlo con el registro.
    tiempo = medir(lambda: cobertura_voraz(inst, con_traza=False), repeticiones)
    valida = es_cobertura(inst, resultado.seleccion)

    optimo = None
    if inst.n <= max_n_fb:
        fb = cobertura_optima_fuerza_bruta(inst)
        optimo = {"tamano": fb.tamano, "seleccion": fb.seleccion,
                  "subconjuntos_probados": fb.subconjuntos_probados}

    H_d = armonico(inst.d)
    salida = {
        "caso": ruta.stem,
        "instancia": {"n": inst.n, "r": inst.r, "d": inst.d, "s": inst.s},
        "voraz": {"seleccion": resultado.seleccion, "tamano": resultado.tamano,
                  "pasos": len(resultado.traza)},
        "tiempo_voraz": tiempo,
        "verificacion": {"cubre_las_r_categorias": valida},
        "cota": {"H_d": H_d, "explicacion": "|voraz| ≤ H(d)·OPT (Johnson 1974; Chvátal 1979)"},
        "optimo_fuerza_bruta": optimo,
    }
    if optimo:
        razon = resultado.tamano / optimo["tamano"]
        salida["comparacion"] = {"razon_voraz_sobre_optimo": razon, "cumple_cota": razon <= H_d + 1e-12}

    destino = carpeta_salida / ruta.stem
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "salida.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    (destino / "traza.json").write_text(
        json.dumps({"caso": ruta.stem, "desempate": "menor posición en la entrada",
                    "pasos": [_paso_con_etiquetas(inst, p) for p in resultado.traza]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")

    fila.update(
        estado="OK" if valida else "COBERTURA INVÁLIDA",
        voraz=resultado.tamano,
        optimo=optimo["tamano"] if optimo else "",
        razon=f"{resultado.tamano / optimo['tamano']:.3f}" if optimo else "",
        H_d=f"{H_d:.3f}",
        tiempo_mediana_ms=f"{tiempo['mediana_s'] * 1000:.4f}",
        seleccion=" ".join(resultado.seleccion),
    )
    return fila


COLUMNAS = ["caso", "n", "r", "d", "voraz", "optimo", "razon", "H_d", "tiempo_mediana_ms", "estado", "seleccion"]


def escribir_resumen(filas: List[Dict[str, Any]], carpeta: Path) -> None:
    with open(carpeta / "resumen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow({c: fila.get(c, "") for c in COLUMNAS})
    lineas = ["| " + " | ".join(COLUMNAS) + " |", "|" + "---|" * len(COLUMNAS)]
    for fila in filas:
        lineas.append("| " + " | ".join(str(fila.get(c, "")) for c in COLUMNAS) + " |")
    (carpeta / "resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Corre el voraz de cobertura sobre una carpeta de casos.")
    p.add_argument("--casos", required=True, help="Carpeta con archivos .json (o un solo archivo)")
    p.add_argument("--salida", required=True, help="Carpeta donde se escriben los resultados")
    p.add_argument("--repeticiones", type=int, default=5)
    p.add_argument("--max-n-fuerza-bruta", type=int, default=20,
                   help="Compara contra el óptimo solo si n ≤ este valor (default 20)")
    a = p.parse_args(argv)

    origen = Path(a.casos)
    archivos = [origen] if origen.is_file() else sorted(origen.glob("*.json"))
    if not archivos:
        print(f"No hay casos .json en {origen}", file=sys.stderr)
        return 1
    carpeta = Path(a.salida)
    carpeta.mkdir(parents=True, exist_ok=True)

    filas = [procesar_caso(r, carpeta, a.repeticiones, a.max_n_fuerza_bruta) for r in archivos]
    escribir_resumen(filas, carpeta)
    for f in filas:
        print(f"{f['caso']:<28} {f.get('estado')}  voraz={f.get('voraz', '-')}  óptimo={f.get('optimo', '-')}")
    print(f"\nResumen en {carpeta / 'resumen.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
