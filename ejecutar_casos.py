#!/usr/bin/env python3
"""Corre la solución base (Parte 1 y Parte 2) sobre los casos y guarda salida, tiempo y traza por caso.

Uso:
    python ejecutar_casos.py                       # todos los .json de casos/  ->  resultados/
    python ejecutar_casos.py casos_propios --salida resultados_propios
    python ejecutar_casos.py casos/mi_caso.json    # un solo archivo

Por cada caso se crea  <salida>/caso_XX_<nombre>/  con:
    parte1_salida.json   parte1_traza.json   parte2_salida.json   parte2_traza.json
    tiempos.json         verificacion.json   traza_legible.txt
y al final  <salida>/resumen.md, resumen.csv y resumen.json.
"""

import argparse
import csv
import json
import platform
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from ada import VERSION, aceleracion, auditoria, verificadores  # noqa: E402
from ada.entrada import leer_instancia  # noqa: E402
from ada.errores import ErrorDeEntrada, InstanciaInfactible  # noqa: E402
from ada.medicion import medir  # noqa: E402


def _guardar(ruta, objeto):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(objeto, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _recolectar(rutas):
    archivos = []
    for ruta in rutas:
        p = Path(ruta)
        if p.is_dir():
            archivos.extend(sorted(p.glob("*.json")))
        elif p.is_file():
            archivos.append(p)
        else:
            print(f"[aviso] no existe {p}", file=sys.stderr)
    return archivos


def _texto_traza(inst, salida1, traza1, salida2, traza2):
    L = []
    L.append(f"CASO {inst.nombre}  (versión {VERSION})")
    L.append(f"n = {inst.n} etapas, r = {inst.r} categorías, B = {inst.B}, aristas del flujo = {len(inst.aristas)}")
    L.append("")
    L.append("== PARTE 1: aceleración ==")
    L.append(f"método: {salida1['metodo']}")
    if salida1["metodo"] == "programacion_dinamica_cadena":
        L.append(f"recurrencia: {traza1['recurrencia']}")
        L.append(f"tabla DP: {traza1['dimension_tabla']['filas']} filas x {traza1['dimension_tabla']['columnas']} columnas")
        L.append("reconstrucción hacia atrás (de la última etapa a la primera):")
        L.append("  etapa  presupuesto_antes  DP[i][b]  decisión   costo  ahorro  presupuesto_después")
        for dec in reversed(traza1["decisiones_reconstruccion"]):
            dp = "-" if dec["dp_i_b"] is None else dec["dp_i_b"]
            L.append(
                f"  {dec['etapa']:<6} {dec['presupuesto_antes']:>17} {str(dp):>9}  "
                f"{'ACELERAR' if dec['acelerar'] else 'no       '} {dec['costo']:>7} {dec['ahorro']:>7} "
                f"{dec['presupuesto_despues']:>19}"
            )
    else:
        L.append(
            f"candidatas={traza1['etapas_candidatas']}  nodos explorados={traza1['nodos_explorados']}  "
            f"podas por cota={traza1['podas_por_cota']}  duración inicial (voraz)={traza1['duracion_solucion_inicial_voraz']}"
        )
        for m in traza1["mejoras_de_la_mejor_solucion"]:
            L.append(f"  mejora en el nodo {m['nodo']}: duración {m['duracion']} con costo {m['costo']}")
    L.append(f"etapas aceleradas: {salida1['etapas_aceleradas']}")
    L.append(
        f"costo usado = {salida1['costo_usado']} de B = {salida1['presupuesto_B']}; duración "
        f"{salida1['duracion_sin_acelerar']} -> {salida1['duracion_final']}  (ahorro {salida1['ahorro']}); "
        f"óptimo probado: {salida1['optimo_probado']}"
    )
    L.append("")
    L.append("== PARTE 2: cobertura de auditoría ==")
    if not salida2.get("factible", True):
        L.append(f"INFACTIBLE: {salida2['mensaje']}")
    else:
        L.append(f"método: voraz de mayor ganancia (desempate: {traza2['desempate']})")
        for v in traza2["vueltas"]:
            L.append(
                f"  vuelta {v['vuelta']}: elige {v['elegida']} (ganancia {v['ganancia']}), "
                f"cubre nuevas {v['categorias_nuevas']}; cubiertas {v['cubiertas_acumuladas']}/{inst.r}, faltan {v['faltan']}"
            )
        L.append(f"interacciones elegidas: {salida2['interacciones_elegidas']}  (tamaño {salida2['tamano']})")
    return "\n".join(L) + "\n"


def procesar_caso(ruta, numero, carpeta_salida, repeticiones, verificar, limite_nodos):
    nombre = ruta.stem
    carpeta = carpeta_salida / f"caso_{numero:02d}_{nombre}"
    carpeta.mkdir(parents=True, exist_ok=True)
    fila = {"caso": nombre, "carpeta": carpeta.name}
    try:
        inst = leer_instancia(ruta)
    except ErrorDeEntrada as e:
        _guardar(carpeta / "error.json", {"caso": nombre, "error_de_entrada": str(e)})
        fila.update({"estado": "ERROR DE ENTRADA", "detalle": str(e)})
        print(f"[{nombre}] ERROR DE ENTRADA: {e}")
        return fila

    # ----- Parte 1
    salida1, traza1 = aceleracion.resolver(inst, traza_completa=True, limite_nodos=limite_nodos)
    _, tiempo1 = medir(lambda: aceleracion.resolver(inst, traza_completa=False, limite_nodos=limite_nodos), repeticiones)

    # ----- Parte 2
    try:
        salida2, traza2 = auditoria.resolver(inst)
        _, tiempo2 = medir(lambda: auditoria.resolver(inst, con_traza=False), repeticiones)
    except InstanciaInfactible as e:
        salida2 = {
            "caso": nombre,
            "factible": False,
            "mensaje": str(e),
            "categorias_sin_cubrir": e.categorias_sin_cubrir,
        }
        traza2, tiempo2 = {}, None

    meta = {"version": VERSION, "python": platform.python_version(), "caso": nombre, "archivo": ruta.name}
    _guardar(carpeta / "parte1_salida.json", {**meta, **salida1})
    _guardar(carpeta / "parte1_traza.json", {**meta, **traza1})
    _guardar(carpeta / "parte2_salida.json", {**meta, **salida2})
    _guardar(carpeta / "parte2_traza.json", {**meta, **traza2})
    _guardar(
        carpeta / "tiempos.json",
        {
            **meta,
            "nota": "tiempo del algoritmo solo (sin leer el archivo ni escribir resultados), mediana de varias repeticiones",
            "parte1": tiempo1,
            "parte2": tiempo2,
        },
    )
    (carpeta / "traza_legible.txt").write_text(_texto_traza(inst, salida1, traza1, salida2, traza2), encoding="utf-8")

    ver1 = ver2 = None
    if verificar:
        ver1 = verificadores.verificar_parte1(ruta, salida1)
        ver2 = verificadores.verificar_parte2(ruta, salida2) if salida2.get("factible", True) else {"ok": True, "chequeos": {"nota": "instancia infactible: no hay cobertura que verificar"}}
        _guardar(carpeta / "verificacion.json", {**meta, "parte1": ver1, "parte2": ver2})

    fila.update(
        {
            "estado": "OK",
            "n_etapas": inst.n,
            "aristas": len(inst.aristas),
            "r_categorias": inst.r,
            "B": inst.B,
            "metodo_parte1": salida1["metodo"],
            "duracion_sin_acelerar": salida1["duracion_sin_acelerar"],
            "duracion_final": salida1["duracion_final"],
            "ahorro": salida1["ahorro"],
            "costo_usado": salida1["costo_usado"],
            "optimo_probado": salida1["optimo_probado"],
            "tiempo_parte1_ms": tiempo1["mediana_ms"],
            "factible_parte2": salida2.get("factible", True),
            "tamano_cobertura": salida2.get("tamano"),
            "interacciones": salida2.get("interacciones_elegidas"),
            "tiempo_parte2_ms": None if tiempo2 is None else tiempo2["mediana_ms"],
            "verifica_parte1": None if ver1 is None else ver1["ok"],
            "verifica_parte2": None if ver2 is None else ver2["ok"],
            "advertencias": inst.advertencias,
        }
    )
    print(
        f"[{nombre}] P1 {salida1['metodo']}: duración {salida1['duracion_sin_acelerar']}->{salida1['duracion_final']} "
        f"(ahorro {salida1['ahorro']}, costo {salida1['costo_usado']}/{inst.B}) {tiempo1['mediana_ms']} ms | "
        f"P2: {'cobertura de ' + str(salida2['tamano']) if salida2.get('factible', True) else 'INFACTIBLE'}"
        + (f" | verificación P1={ver1['ok']} P2={ver2['ok']}" if verificar else "")
    )
    return fila


def escribir_resumenes(filas, carpeta_salida):
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    _guardar(carpeta_salida / "resumen.json", {"version": VERSION, "casos": filas})
    campos = [
        "carpeta", "estado", "n_etapas", "aristas", "r_categorias", "B", "metodo_parte1",
        "duracion_sin_acelerar", "duracion_final", "ahorro", "costo_usado", "optimo_probado", "tiempo_parte1_ms",
        "factible_parte2", "tamano_cobertura", "tiempo_parte2_ms", "verifica_parte1", "verifica_parte2",
    ]
    with open(carpeta_salida / "resumen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    L = [f"# Resumen de resultados (versión {VERSION})", ""]
    L.append("| Caso | n | aristas | r | B | Método P1 | Duración | Ahorro | Costo | ms P1 | Cobertura P2 | ms P2 | Verif. |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for f_ in filas:
        if f_["estado"] != "OK":
            L.append(f"| {f_['carpeta']} | — | — | — | — | {f_['estado']}: {f_['detalle']} | | | | | | | |")
            continue
        cob = f_["tamano_cobertura"] if f_["factible_parte2"] else "infactible"
        ver = "—" if f_["verifica_parte1"] is None else ("OK" if f_["verifica_parte1"] and f_["verifica_parte2"] else "FALLA")
        tiempo2 = "—" if f_["tiempo_parte2_ms"] is None else f_["tiempo_parte2_ms"]
        L.append(
            f"| {f_['carpeta']} | {f_['n_etapas']} | {f_['aristas']} | {f_['r_categorias']} | {f_['B']} | "
            f"{f_['metodo_parte1']} | {f_['duracion_sin_acelerar']} → {f_['duracion_final']} | {f_['ahorro']} | "
            f"{f_['costo_usado']} | {f_['tiempo_parte1_ms']} | {cob} | {tiempo2} | {ver} |"
        )
    (carpeta_salida / "resumen.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rutas", nargs="*", default=[str(RAIZ / "casos")], help="carpetas o archivos .json (por defecto: casos/)")
    ap.add_argument("--salida", default=str(RAIZ / "resultados"), help="carpeta donde se guardan los resultados")
    ap.add_argument("--repeticiones", type=int, default=7, help="repeticiones para medir el tiempo (se reporta la mediana)")
    ap.add_argument("--limite-nodos", type=int, default=aceleracion.LIMITE_NODOS_POR_DEFECTO,
                    help="tope de nodos del solver general de la Parte 1")
    ap.add_argument("--sin-verificar", action="store_true", help="no correr los verificadores independientes")
    args = ap.parse_args(argv)

    archivos = _recolectar(args.rutas)
    if not archivos:
        print("No se encontraron archivos .json para procesar.", file=sys.stderr)
        return 2
    salida = Path(args.salida)
    filas = []
    for k, ruta in enumerate(archivos, start=1):
        filas.append(procesar_caso(ruta, k, salida, args.repeticiones, not args.sin_verificar, args.limite_nodos))
    escribir_resumenes(filas, salida)
    print(f"\nListo: {len(filas)} caso(s). Resultados en {salida}")
    fallas = [f for f in filas if f["estado"] != "OK" or f.get("verifica_parte1") is False or f.get("verifica_parte2") is False]
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
