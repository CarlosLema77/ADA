"""Constructores de casos y fuerza bruta usados por las pruebas (código aparte del de los algoritmos)."""

import random
from itertools import combinations, product
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CASO_PROFE = RAIZ / "casos" / "entrada_G3_mochila_20_nodos.json"


def caso_dict(t, c, d, B, aristas=None, completas=None, categorias=None, ids=None, extra_params=None):
    """Arma un caso en el formato de la profesora. Por defecto el flujo es una cadena E01->E02->..."""
    n = len(t)
    ids = ids or [f"E{k + 1:02d}" for k in range(n)]
    if aristas is None:
        aristas = [(ids[k], ids[k + 1]) for k in range(n - 1)]
    completas = completas if completas is not None else [[] for _ in range(n)]
    if categorias is None:
        categorias = sorted({x for lista in completas for x in lista})
    etapas = []
    for k in range(n):
        etapas.append(
            {
                "id": ids[k],
                "duracion_normal": t[k],
                "costo_aceleracion": c[k],
                "reduccion_tiempo_si_acelera": d[k],
                "riesgos_cubiertos_auditoria_completa": list(completas[k]),
                "variaciones_auditoria": [
                    {"id": "completa", "costo": 5, "riesgos_cubiertos": list(completas[k])}
                ],
            }
        )
    params = {"numero_etapas": n, "presupuesto_aceleracion_B": B, "numero_categorias_riesgo": len(categorias)}
    params.update(extra_params or {})
    return {
        "parametros": params,
        "flujo": [{"origen": a, "destino": b} for a, b in aristas],
        "categorias_riesgo": [{"id": x, "categoria": x.lower(), "importancia": 1} for x in categorias],
        "etapas": etapas,
    }


def duracion_dag(ids, t, aristas, aceleradas, d):
    """Camino más largo recalculado por fuerza bruta sobre las aristas (recursión con memoria)."""
    preds = {i: [] for i in ids}
    for a, b in aristas:
        preds[b].append(a)
    peso = {i: t[i] - (d[i] if i in aceleradas else 0) for i in ids}
    memo = {}

    def fin(i):
        if i not in memo:
            memo[i] = peso[i] + max((fin(p) for p in preds[i]), default=0)
        return memo[i]

    return max(fin(i) for i in ids)


def optimo_fuerza_bruta(ids, t, c, d, B, aristas):
    """Mínima duración posible probando los 2^n subconjuntos."""
    mejor = None
    for mascara in product([0, 1], repeat=len(ids)):
        sub = {ids[k] for k in range(len(ids)) if mascara[k]}
        if sum(c[i] for i in sub) <= B:
            dur = duracion_dag(ids, t, aristas, sub, d)
            if mejor is None or dur < mejor:
                mejor = dur
    return mejor


def optimo_cobertura(r, conjuntos):
    """Tamaño mínimo de cobertura por fuerza bruta (None si no hay cobertura)."""
    todo = set(range(r))
    for k in range(1, len(conjuntos) + 1):
        for sub in combinations(range(len(conjuntos)), k):
            if set().union(*[set(conjuntos[j]) for j in sub]) >= todo:
                return k
    return None


def cadena_aleatoria(rng, n_max=8):
    n = rng.randint(1, n_max)
    t = [rng.randint(1, 20) for _ in range(n)]
    d = [rng.randint(0, t[i]) for i in range(n)]
    c = [rng.randint(0, 10) for _ in range(n)]
    B = rng.randint(0, 35)
    return t, c, d, B


def dag_aleatorio(rng, n_max=8):
    """DAG aleatorio con los ids barajados (el orden del archivo NO es un orden topológico)."""
    n = rng.randint(1, n_max)
    t = [rng.randint(1, 20) for _ in range(n)]
    d = [rng.randint(0, t[i]) for i in range(n)]
    c = [rng.randint(0, 10) for _ in range(n)]
    B = rng.randint(0, 35)
    nombres = [f"E{k + 1:02d}" for k in range(n)]
    posicion = list(range(n))
    rng.shuffle(posicion)  # posicion[k] = lugar topológico del id k
    aristas = []
    for a in range(n):
        for b in range(n):
            if posicion[a] < posicion[b] and rng.random() < 0.3:
                aristas.append((nombres[a], nombres[b]))
    return nombres, t, c, d, B, aristas
