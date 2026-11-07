#!/usr/bin/env python3
"""Genera los casos PROPIOS de prueba (casos_propios/), en el mismo formato JSON de la profesora.

No son los casos de la profesora: sirven para probar cosas que su archivo no cubre (flujos con rutas
paralelas, cadenas grandes, presupuesto cero, instancia infactible). La semilla es fija, así que correr
este script dos veces produce exactamente los mismos archivos.

Uso:  python generar_casos.py
"""

import json
import random
from pathlib import Path

DESTINO = Path(__file__).resolve().parent / "casos_propios"
NOMBRES_RIESGO = ["sesgo", "privacidad", "formato", "alucinacion", "toxicidad", "seguridad", "trazabilidad",
                  "equidad", "integridad", "transparencia"]


def armar(descripcion, t, c, d, B, aristas, completas, r, ids=None, importancias=None):
    n = len(t)
    ids = ids or [f"E{k + 1:02d}" for k in range(n)]
    cats = [f"R{k + 1:02d}" for k in range(r)]
    etapas = []
    for k in range(n):
        lista = [cats[x] for x in completas[k]]
        mitad = lista[: max(1, len(lista) // 2)] if lista else []
        etapas.append(
            {
                "id": ids[k],
                "duracion_normal": t[k],
                "costo_aceleracion": c[k],
                "reduccion_tiempo_si_acelera": d[k],
                "riesgos_cubiertos_auditoria_completa": lista,
                "variaciones_auditoria": [
                    {"id": "parcial", "costo": 2 + k % 4, "riesgos_cubiertos": mitad},
                    {"id": "completa", "costo": 5 + k % 4, "riesgos_cubiertos": lista},
                ],
            }
        )
    imp = importancias or [1 + (k * 7) % 5 for k in range(r)]
    return {
        "_descripcion": descripcion,
        "parametros": {
            "numero_etapas": n,
            "presupuesto_aceleracion_B": B,
            "presupuesto_conjunto_aceleracion_y_auditoria": B + 30,
            "numero_categorias_riesgo": r,
        },
        "flujo": [{"origen": a, "destino": b} for a, b in (aristas if aristas is not None else
                  [(ids[k], ids[k + 1]) for k in range(n - 1)])],
        "categorias_riesgo": [
            {"id": cats[k], "categoria": NOMBRES_RIESGO[k % len(NOMBRES_RIESGO)] + ("" if k < len(NOMBRES_RIESGO) else f"_{k}"),
             "importancia": imp[k]}
            for k in range(r)
        ],
        "etapas": etapas,
    }


def aleatorios(rng, n, t_rango=(10, 35), c_rango=(4, 17), d_max=13):
    t = [rng.randint(*t_rango) for _ in range(n)]
    c = [rng.randint(*c_rango) for _ in range(n)]
    d = [rng.randint(2, min(d_max, t[k])) for k in range(n)]
    return t, c, d


def conjuntos_factibles(rng, n, r, tam_max):
    conj = [sorted(rng.sample(range(r), rng.randint(1, min(tam_max, r)))) for _ in range(n)]
    cubiertas = set().union(*map(set, conj))
    for k in range(r):  # garantiza que toda categoría la cubra alguien
        if k not in cubiertas:
            conj[rng.randrange(n)].append(k)
    return [sorted(set(s)) for s in conj]


def capas(rng, ids, ancho, densidad=0.5):
    niveles = [ids[i:i + ancho] for i in range(0, len(ids), ancho)]
    aristas = []
    for a, b in zip(niveles, niveles[1:]):
        for u in a:
            for v in b:
                if rng.random() < densidad:
                    aristas.append((u, v))
        for v in b:
            if not any(x[1] == v for x in aristas):
                aristas.append((rng.choice(a), v))
    return aristas


def main():
    DESTINO.mkdir(exist_ok=True)
    rng = random.Random(2026)
    casos = {}

    casos["propio_01_ejemplo_informe_n4"] = armar(
        "Ejemplo 2.1 del informe: 4 etapas en cadena, B=7. Óptimo: acelerar E03 y E04 (ahorro 10, duración 26). "
        "Parte 2: 4 interacciones y 4 categorías.",
        [10, 8, 12, 6], [4, 3, 5, 2], [5, 4, 7, 3], 7, None,
        [[0, 1], [1, 2], [2, 3], [0, 3]], 4)

    casos["propio_02_voraz_no_optimo"] = armar(
        "Ejemplo del informe donde el voraz da 3 y el óptimo es 2 (S1={1,2,3,4}, S2={1,3,5}, S3={2,4,6}).",
        [6, 5, 7], [3, 2, 4], [2, 2, 3], 6, None,
        [[0, 1, 2, 3], [0, 2, 4], [1, 3, 5]], 6)

    casos["propio_03_diamante"] = armar(
        "Flujo con rutas paralelas: A -> {B, C} -> D. B es la rama larga, así que solo acelerar B reduce la duración.",
        [2, 10, 4, 2], [1, 5, 1, 1], [1, 6, 3, 1], 5,
        [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")],
        [[0], [1, 2], [2], [0, 3]], 4, ids=["A", "B", "C", "D"])

    for nombre, n, ancho, B, r in [("propio_04_rutas_paralelas_20", 20, 4, 72, 12),
                                   ("propio_05_rutas_paralelas_30", 30, 3, 100, 15)]:
        ids = [f"E{k + 1:02d}" for k in range(n)]
        t, c, d = aleatorios(rng, n)
        casos[nombre] = armar(
            f"Flujo por capas de ancho {ancho} con {n} etapas (varias rutas paralelas). Se resuelve con el solver general exacto.",
            t, c, d, B, capas(rng, ids, ancho), conjuntos_factibles(rng, n, r, 4), r)

    t, c, d = aleatorios(rng, 200)
    casos["propio_06_cadena_200"] = armar(
        "Cadena de 200 etapas, B=1500, 30 categorías.", t, c, d, 1500, None, conjuntos_factibles(rng, 200, 30, 6), 30)

    t, c, d = aleatorios(rng, 500)
    casos["propio_07_cadena_500"] = armar(
        "Cadena de 500 etapas, B=5000, 60 categorías (prueba de tamaño para el DP).", t, c, d, 5000, None,
        conjuntos_factibles(rng, 500, 60, 8), 60)

    casos["propio_08_infactible"] = armar(
        "La categoría R04 no la cubre ninguna interacción: la Parte 2 debe reportar la instancia como infactible.",
        [5, 6, 7], [2, 3, 4], [1, 2, 3], 4, None, [[0, 1], [1, 2], [0]], 4)

    casos["propio_09_presupuesto_cero"] = armar(
        "B = 0: no se puede acelerar nada y la duración queda igual.",
        [5, 6, 7], [2, 3, 4], [1, 2, 3], 0, None, [[0], [1], [2]], 3)

    n = 40
    ids = [f"E{k + 1:02d}" for k in range(n)]
    t, c, d = aleatorios(rng, n)
    casos["propio_10_paralelo_40_ancho8"] = armar(
        "Caso exigente: 40 etapas por capas de ancho 8 (135 aristas). Muestra que en flujos con muchas rutas paralelas "
        "el solver exacto puede necesitar muchos nodos (el problema es NP-difícil).",
        t, c, d, 150, capas(rng, ids, 8), conjuntos_factibles(rng, n, 20, 5), 20)

    casos["propio_11_reduccion_grafo_5_vertices"] = armar(
        "Instancia que produce la reducción desde Cobertura de Vértices (ejemplo del informe): vértices a..e son "
        "interacciones y las aristas 1=ab 2=ac 3=bc 4=bd 5=ce 6=de son las categorías R01..R06. Óptimo: {b, c, d}.",
        [4, 5, 6, 3, 4], [2, 3, 2, 1, 2], [1, 2, 3, 1, 2], 5, None,
        [[0, 1], [0, 2, 3], [1, 2, 4], [3, 5], [4, 5]], 6, ids=["a", "b", "c", "d", "e"])

    for nombre, caso in casos.items():
        with open(DESTINO / f"{nombre}.json", "w", encoding="utf-8") as f:
            json.dump(caso, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print(f"{len(casos)} casos escritos en {DESTINO}")


if __name__ == "__main__":
    main()
