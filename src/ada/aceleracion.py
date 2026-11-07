"""Parte 1: aceleración de un flujo de etapas bajo un presupuesto B.

Se elige un subconjunto de etapas a acelerar (cada una cuesta c_i y reduce d_i su duración) de modo que
la duración total del flujo sea mínima y el costo no pase de B.

* Si el flujo es una cadena (todas las etapas en serie), el problema es la mochila 0/1 y se resuelve de
  forma exacta con programación dinámica en O(n * B)  ->  `dp_cadena`.
* Si el flujo tiene rutas paralelas, la duración es la del camino más largo. El problema sigue siendo
  NP-difícil y se resuelve de forma exacta (en el peor caso exponencial) con ramificación y acotamiento
  ->  `ramificar_y_acotar`.

`resolver` escoge el método según la forma del flujo.
"""

import sys

from .grafo import camino_mas_largo, es_cadena

LIMITE_CELDAS_TABLA = 60_000  # tamaño máximo de la tabla DP que se guarda completa en la traza
LIMITE_NODOS_POR_DEFECTO = 3_000_000


# --------------------------------------------------------------------------------------------------
# Cadena: programación dinámica (mochila 0/1)
# --------------------------------------------------------------------------------------------------
def dp_cadena(t, c, d, B, guardar_tabla=True):
    """Mochila 0/1 con peso c[i], valor d[i] y capacidad B, con reconstrucción de la solución.

    DP[i][b] = máximo ahorro usando solo las primeras i etapas con presupuesto b:
        DP[i][b] = max(DP[i-1][b], DP[i-1][b - c_i] + d_i)   si c_i <= b
        DP[i][b] = DP[i-1][b]                                 si c_i > b
    Solo se acelera una etapa si eso mejora ESTRICTAMENTE el ahorro (desempate fijo: ante un empate no se
    acelera). Tiempo O(n * B); memoria O(n * B) bytes para reconstruir.

    Devuelve (ahorro_optimo, decisiones, tabla). `decisiones` va en el orden de la cadena.
    """
    n = len(t)
    previa = [0] * (B + 1)
    toma = [bytearray(B + 1) for _ in range(n)]
    tabla = [previa] if guardar_tabla else None
    for i in range(1, n + 1):
        ci, di = c[i - 1], d[i - 1]
        actual = previa[:]
        fila = toma[i - 1]
        for b in range(ci, B + 1):
            candidato = previa[b - ci] + di
            if candidato > previa[b]:
                actual[b] = candidato
                fila[b] = 1
        previa = actual
        if tabla is not None:
            tabla.append(actual)

    decisiones = []
    b = B
    for i in range(n, 0, -1):
        acelerar = toma[i - 1][b] == 1
        decisiones.append(
            {
                "posicion": i,
                "presupuesto_antes": b,
                "dp_i_b": tabla[i][b] if tabla is not None else None,
                "acelerar": acelerar,
                "costo": c[i - 1] if acelerar else 0,
                "ahorro": d[i - 1] if acelerar else 0,
                "presupuesto_despues": b - (c[i - 1] if acelerar else 0),
            }
        )
        if acelerar:
            b -= c[i - 1]
    decisiones.reverse()
    return previa[B], decisiones, tabla


# --------------------------------------------------------------------------------------------------
# Flujo general: ramificación y acotamiento
# --------------------------------------------------------------------------------------------------
def _ahorro_fraccionario(items, presupuesto):
    """Cota superior entera del ahorro con una mochila fraccionaria. items: lista de (d, c)."""
    ordenados = sorted(items, key=lambda x: (x[1] / x[0]) if x[0] else float("inf"))
    ahorro = 0
    restante = presupuesto
    for di, ci in ordenados:
        if ci <= restante:
            ahorro += di
            restante -= ci
        else:
            if ci > 0:
                ahorro += (restante * di) // ci
            break
    return ahorro


def ramificar_y_acotar(t, c, d, B, orden, predecesores, limite_nodos=LIMITE_NODOS_POR_DEFECTO):
    """Mínima duración de un DAG (camino más largo) con presupuesto B, de forma exacta.

    Se decide etapa por etapa (primero las de mayor ahorro) si se acelera. En cada nodo del árbol hay dos
    cotas inferiores de la duración final: (1) acelerar gratis todas las etapas aún no decididas, y
    (2) el camino más largo con lo decidido hasta ahora, descontando lo que la mochila fraccionaria
    permitiría ahorrar en él con el presupuesto que queda. Se poda si la cota no mejora la mejor solución.
    """
    n = len(t)
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 4 * n + 1000))
    candidatas = [i for i in range(n) if d[i] > 0 and c[i] <= B]
    ramas = sorted(candidatas, key=lambda i: (-d[i], i))
    es_candidata = [False] * n
    for i in candidatas:
        es_candidata[i] = True

    estado = [0] * n  # 1 = acelerada, 0 = no acelerada, -1 = sin decidir (solo candidatas)
    for i in ramas:
        estado[i] = -1

    normal, _ = camino_mas_largo(orden, predecesores, t)

    # ---- solución inicial (voraz): acelerar por razón d/c sobre el camino más largo actual
    mejor = normal
    mejor_x = [0] * n
    mejor_costo = 0
    x_h = [0] * n
    gastado = 0
    for _ in range(len(candidatas)):
        pesos = [t[i] - d[i] * x_h[i] for i in range(n)]
        longitud, camino = camino_mas_largo(orden, predecesores, pesos)
        if longitud < mejor:
            mejor, mejor_x, mejor_costo = longitud, x_h[:], gastado
        opciones = [i for i in camino if es_candidata[i] and not x_h[i] and gastado + c[i] <= B]
        if not opciones:
            break
        elegida = opciones[0]
        for i in opciones[1:]:
            if d[i] * c[elegida] > d[elegida] * c[i]:
                elegida = i
        x_h[elegida] = 1
        gastado += c[elegida]
    else:
        pesos = [t[i] - d[i] * x_h[i] for i in range(n)]
        longitud, _ = camino_mas_largo(orden, predecesores, pesos)
        if longitud < mejor:
            mejor, mejor_x, mejor_costo = longitud, x_h[:], gastado
    duracion_heuristica = mejor

    contadores = {"nodos": 0, "podas_por_cota": 0, "abortado": False}
    mejoras = []

    def explorar(k, costo):
        nonlocal mejor, mejor_x, mejor_costo
        contadores["nodos"] += 1
        if contadores["nodos"] > limite_nodos:
            contadores["abortado"] = True
            return
        # cota 1: todo lo no decidido se acelera gratis
        w1 = [t[i] - d[i] if estado[i] != 0 and es_candidata[i] else t[i] for i in range(n)]
        cota1, _ = camino_mas_largo(orden, predecesores, w1)
        if cota1 >= mejor:
            contadores["podas_por_cota"] += 1
            return
        # solución factible: lo no decidido queda sin acelerar
        w_dec = [t[i] - d[i] if estado[i] == 1 else t[i] for i in range(n)]
        actual, camino = camino_mas_largo(orden, predecesores, w_dec)
        if actual < mejor:
            mejor, mejor_costo = actual, costo
            mejor_x = [1 if estado[i] == 1 else 0 for i in range(n)]
            if len(mejoras) < 200:
                mejoras.append({"nodo": contadores["nodos"], "duracion": actual, "costo": costo})
        if k == len(ramas):
            return
        # cota 2: camino más largo con la mochila fraccionaria sobre lo que queda
        libres = [(d[i], c[i]) for i in camino if estado[i] == -1]
        cota2 = actual - _ahorro_fraccionario(libres, B - costo)
        if cota2 >= mejor:
            contadores["podas_por_cota"] += 1
            return
        s = ramas[k]
        if costo + c[s] <= B:
            estado[s] = 1
            explorar(k + 1, costo + c[s])
            if contadores["abortado"]:
                estado[s] = -1
                return
        estado[s] = 0
        explorar(k + 1, costo)
        estado[s] = -1

    explorar(0, 0)

    traza = {
        "metodo": "ramificacion_y_acotamiento",
        "etapas_candidatas": len(candidatas),
        "duracion_solucion_inicial_voraz": duracion_heuristica,
        "nodos_explorados": contadores["nodos"],
        "podas_por_cota": contadores["podas_por_cota"],
        "limite_nodos": limite_nodos,
        "mejoras_de_la_mejor_solucion": mejoras,
    }
    return normal, mejor, mejor_x, mejor_costo, (not contadores["abortado"]), traza


# --------------------------------------------------------------------------------------------------
# Punto de entrada
# --------------------------------------------------------------------------------------------------
def resolver(inst, traza_completa=True, limite_nodos=LIMITE_NODOS_POR_DEFECTO, forzar_general=False):
    """Resuelve la Parte 1 para una Instancia y devuelve (salida, traza), ambos diccionarios serializables."""
    ids = [e.id for e in inst.etapas]
    t = [e.t for e in inst.etapas]
    c = [e.c for e in inst.etapas]
    d = [e.d for e in inst.etapas]
    B = inst.B
    cadena = es_cadena(inst.orden, inst.sucesores) and not forzar_general

    if cadena:
        orden = inst.orden
        t_o = [t[k] for k in orden]
        c_o = [c[k] for k in orden]
        d_o = [d[k] for k in orden]
        guardar = traza_completa and (len(orden) + 1) * (B + 1) <= LIMITE_CELDAS_TABLA
        ahorro, decisiones, tabla = dp_cadena(t_o, c_o, d_o, B, guardar_tabla=guardar)
        x = [0] * len(ids)
        for dec in decisiones:
            dec["etapa"] = ids[orden[dec["posicion"] - 1]]
            if dec["acelerar"]:
                x[orden[dec["posicion"] - 1]] = 1
        normal = sum(t)
        duracion_final = normal - ahorro
        costo_usado = sum(c[k] for k in range(len(ids)) if x[k])
        optimo_probado = True
        metodo = "programacion_dinamica_cadena"
        traza = {
            "metodo": metodo,
            "recurrencia": "DP[i][b] = max(DP[i-1][b], DP[i-1][b-c_i] + d_i) si c_i <= b; si no, DP[i-1][b]",
            "orden_de_la_cadena": [ids[k] for k in orden],
            "dimension_tabla": {"filas": len(orden) + 1, "columnas": B + 1},
            "celdas": (len(orden) + 1) * (B + 1),
            "decisiones_reconstruccion": decisiones if traza_completa else [],
        }
        if guardar:
            traza["tabla_dp"] = tabla
        elif traza_completa:
            traza["tabla_dp"] = None
            traza["nota_tabla"] = (
                f"la tabla tiene más de {LIMITE_CELDAS_TABLA} celdas y no se guarda completa; "
                "las decisiones de la reconstrucción sí están completas"
            )
    else:
        normal, duracion_final, x, costo_usado, optimo_probado, traza = ramificar_y_acotar(
            t, c, d, B, inst.orden, inst.predecesores, limite_nodos
        )
        ahorro = normal - duracion_final
        metodo = traza["metodo"]
        if not traza_completa:
            traza["mejoras_de_la_mejor_solucion"] = []

    aceleradas = [ids[k] for k in inst.orden if x[k]]
    salida = {
        "caso": inst.nombre,
        "metodo": metodo,
        "presupuesto_B": B,
        "etapas_aceleradas": aceleradas,
        "costo_usado": costo_usado,
        "duracion_sin_acelerar": normal,
        "duracion_final": duracion_final,
        "ahorro": ahorro,
        "optimo_probado": optimo_probado,
        "x": {ids[k]: x[k] for k in range(len(ids))},
    }
    return salida, traza
