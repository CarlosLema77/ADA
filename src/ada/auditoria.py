"""Parte 2: cobertura mínima de auditoría.

Cada candidato a auditar cubre un conjunto de categorías de riesgo. Se quiere el menor número de
candidatos cuya unión cubra todas las categorías. El problema es NP-difícil; se resuelve con el voraz
"elegir el que cubre más categorías nuevas" (garantía H(d) <= ln r + 1 sobre el óptimo).
"""

import sys

from .errores import InstanciaInfactible


def construir_candidatos(inst):
    """Devuelve (ids, conjuntos): los candidatos y, para cada uno, la lista de índices de categoría que cubre.

    Cada etapa es un candidato a auditar y cubre su lista riesgos_cubiertos_auditoria_completa
    (la profesora confirmó que se usa la auditoría completa; el campo variaciones_auditoria se ignora).
    """
    indice = {cid: k for k, cid in enumerate(inst.categorias)}
    ids = [e.id for e in inst.etapas]
    conjuntos = [[indice[x] for x in e.completa] for e in inst.etapas]
    return ids, conjuntos


def categorias_sin_cubrir(r, conjuntos):
    """Chequeo de factibilidad: índices de las categorías que ningún candidato cubre. Costo O(r + s)."""
    marcada = [False] * r
    for S in conjuntos:
        for k in S:
            marcada[k] = True
    return [k for k in range(r) if not marcada[k]]


def voraz(r, conjuntos, ids=None, categorias=None, con_traza=True):
    """Voraz de cobertura con desempate fijo (gana el candidato que aparece primero en la entrada).

    Devuelve (elegidos, traza) donde `elegidos` son índices de candidato en el orden de elección.
    Con con_traza=False no arma la traza (devuelve None): así se mide el tiempo del algoritmo solo.
    Lanza InstanciaInfactible si alguna categoría no la cubre ningún candidato.
    """
    n = len(conjuntos)
    ids = ids or [str(j) for j in range(n)]
    categorias = categorias or [str(k) for k in range(r)]
    faltantes = categorias_sin_cubrir(r, conjuntos)
    if faltantes:
        nombres = [categorias[k] for k in faltantes]
        raise InstanciaInfactible(
            f"instancia infactible: ningún candidato cubre las categorías {nombres}", nombres
        )

    cubierta = [False] * r
    elegida = [False] * n
    faltan = r
    elegidos = []
    vueltas = []
    while faltan > 0:
        mejor, g_mejor = -1, 0
        ganancias = [] if con_traza else None
        for j in range(n):
            if elegida[j]:
                continue
            g = 0
            for k in conjuntos[j]:
                if not cubierta[k]:
                    g += 1
            if con_traza:
                ganancias.append((g, j))
            if g > g_mejor:
                mejor, g_mejor = j, g
        elegida[mejor] = True
        elegidos.append(mejor)
        nuevas = []
        for k in conjuntos[mejor]:
            if not cubierta[k]:
                cubierta[k] = True
                faltan -= 1
                nuevas.append(categorias[k])
        if not con_traza:
            continue
        mejores = sorted(ganancias, key=lambda x: (-x[0], x[1]))[:5]
        vueltas.append(
            {
                "vuelta": len(vueltas) + 1,
                "elegida": ids[mejor],
                "ganancia": g_mejor,
                "categorias_nuevas": nuevas,
                "cubiertas_acumuladas": r - faltan,
                "faltan": faltan,
                "categorias_faltantes": [categorias[k] for k in range(r) if not cubierta[k]],
                "empatadas_que_perdieron_por_desempate": [ids[j] for g, j in ganancias if g == g_mejor and j != mejor],
                "mejores_candidatos_de_la_vuelta": [
                    {"candidato": ids[j], "ganancia": g} for g, j in mejores
                ],
            }
        )
    if not con_traza:
        return elegidos, None
    traza = {
        "metodo": "voraz_mayor_ganancia",
        "desempate": "gana el candidato que aparece primero en la entrada",
        "vueltas": vueltas,
    }
    return elegidos, traza


def optimo_exacto(r, conjuntos):
    """Tamaño mínimo de una cobertura (búsqueda exacta con poda). Pensado para verificar, no para escalar.

    Devuelve (tamano, indices_de_una_cobertura_minima) o (None, None) si no hay cobertura posible.
    """
    n = len(conjuntos)
    mascaras = [sum(1 << k for k in set(S)) for S in conjuntos]
    todo = (1 << r) - 1
    cubren = [[j for j in range(n) if mascaras[j] >> k & 1] for k in range(r)]
    if any(not lista for lista in cubren):
        return None, None
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 4 * r + 1000))
    mejor = [n + 1, None]

    def buscar(cubierto, elegidos):
        if cubierto == todo:
            if len(elegidos) < mejor[0]:
                mejor[0], mejor[1] = len(elegidos), list(elegidos)
            return
        faltan = todo & ~cubierto
        g_max = max(bin(m & faltan).count("1") for m in mascaras)
        necesarios = -(-bin(faltan).count("1") // g_max)
        if len(elegidos) + necesarios >= mejor[0]:
            return
        k = min((k for k in range(r) if faltan >> k & 1), key=lambda k: len(cubren[k]))
        for j in sorted(cubren[k], key=lambda j: -bin(mascaras[j] & faltan).count("1")):
            elegidos.append(j)
            buscar(cubierto | mascaras[j], elegidos)
            elegidos.pop()

    buscar(0, [])
    return mejor[0], mejor[1]


def resolver(inst, con_traza=True):
    """Resuelve la Parte 2 para una Instancia y devuelve (salida, traza). Sin traza, traza es None."""
    ids, conjuntos = construir_candidatos(inst)
    r = inst.r
    elegidos, traza = voraz(r, conjuntos, ids, inst.categorias, con_traza)
    d = max((len(set(S)) for S in conjuntos), default=0)
    salida = {
        "caso": inst.nombre,
        "metodo": "voraz_mayor_ganancia",
        "n_candidatos": len(conjuntos),
        "r_categorias": r,
        "factible": True,
        "interacciones_elegidas": [ids[j] for j in elegidos],
        "tamano": len(elegidos),
        "d_max_categorias_por_candidato": d,
        "cubre_todas_las_categorias": True,
    }
    return salida, traza
