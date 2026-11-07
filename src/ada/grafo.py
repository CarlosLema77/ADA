"""Utilidades de grafos dirigidos acíclicos: orden topológico, detección de cadena y camino más largo."""

import heapq

from .errores import ErrorDeEntrada


def orden_topologico(ids, aristas):
    """Orden topológico determinista (Kahn con desempate por posición en la entrada).

    ids: lista de identificadores de etapa, en el orden del archivo.
    aristas: lista de pares (origen, destino) de identificadores.
    Devuelve (orden, sucesores, predecesores), con índices enteros posiciones de `ids`.
    Lanza ErrorDeEntrada si hay un ciclo. Costo: O(n + m log n).
    """
    n = len(ids)
    indice = {identificador: k for k, identificador in enumerate(ids)}
    sucesores = [[] for _ in range(n)]
    predecesores = [[] for _ in range(n)]
    grado_entrada = [0] * n
    for origen, destino in aristas:
        u, v = indice[origen], indice[destino]
        sucesores[u].append(v)
        predecesores[v].append(u)
        grado_entrada[v] += 1

    listos = [k for k in range(n) if grado_entrada[k] == 0]
    heapq.heapify(listos)
    orden = []
    while listos:
        u = heapq.heappop(listos)
        orden.append(u)
        for v in sucesores[u]:
            grado_entrada[v] -= 1
            if grado_entrada[v] == 0:
                heapq.heappush(listos, v)

    if len(orden) < n:
        en_ciclo = [ids[k] for k in range(n) if grado_entrada[k] > 0]
        raise ErrorDeEntrada(
            "el flujo tiene un ciclo, así que no hay un orden de etapas. "
            f"Etapas atrapadas en el ciclo o detrás de él: {en_ciclo[:10]}"
            + (" ..." if len(en_ciclo) > 10 else "")
        )
    return orden, sucesores, predecesores


def es_cadena(orden, sucesores):
    """True si el flujo es una sola cadena E_1 -> E_2 -> ... -> E_n (todas las etapas en serie)."""
    n = len(orden)
    total_aristas = sum(len(s) for s in sucesores)
    if total_aristas != n - 1:
        return False
    for posicion in range(n - 1):
        if sucesores[orden[posicion]] != [orden[posicion + 1]]:
            return False
    return True


def camino_mas_largo(orden, predecesores, peso):
    """Camino de mayor suma de pesos en un DAG con pesos en los nodos. Costo: O(n + m).

    Devuelve (longitud, camino) con el camino como lista de índices de nodo.
    """
    n = len(orden)
    distancia = [0] * n
    anterior = [-1] * n
    for u in orden:
        mejor = 0
        mejor_p = -1
        for p in predecesores[u]:
            if mejor_p == -1 or distancia[p] > mejor:
                mejor = distancia[p]
                mejor_p = p
        distancia[u] = peso[u] + (mejor if mejor_p != -1 else 0)
        anterior[u] = mejor_p

    fin = max(orden, key=lambda k: (distancia[k], -k)) if n else -1
    longitud = distancia[fin] if n else 0
    camino = []
    actual = fin
    while actual != -1:
        camino.append(actual)
        actual = anterior[actual]
    camino.reverse()
    return longitud, camino
