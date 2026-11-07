"""Verificadores independientes de las soluciones.

No usan los módulos de los algoritmos ni el lector de casos: releen el JSON original con su propio
código mínimo y recalculan todo desde cero. Si el algoritmo se equivoca en una cuenta, aquí aparece.
"""

import json
from itertools import combinations
from math import comb


def _cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        raw = json.load(f)
    etapas = raw.get("etapas", raw.get("estaciones"))
    flujo = raw.get("flujo", raw.get("caminos", []))
    aristas = []
    for a in flujo:
        if isinstance(a, dict):
            o = a.get("origen", a.get("desde"))
            de = a.get("destino", a.get("hasta"))
        else:
            o, de = a
        aristas.append((o, de))
    return raw, etapas, aristas


def _duracion(ids, t, aristas, pesos_extra=None):
    """Camino más largo por recursión con memoria (otra implementación distinta a la del algoritmo)."""
    preds = {i: [] for i in ids}
    for o, de in aristas:
        preds[de].append(o)
    memo = {}

    def fin(i):
        if i not in memo:
            memo[i] = pesos_extra[i] + max((fin(p) for p in preds[i]), default=0)
        return memo[i]

    import sys

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 4 * len(ids) + 1000))
    return max(fin(i) for i in ids)


def verificar_parte1(ruta_json, salida, exhaustivo_hasta=20):
    """Comprueba la salida de la Parte 1. Devuelve un diccionario con cada chequeo y un 'ok' global."""
    raw, etapas, aristas = _cargar(ruta_json)
    B = raw["parametros"]["presupuesto_aceleracion_B"]
    ids = [e["id"] for e in etapas]
    t = {e["id"]: e["duracion_normal"] for e in etapas}
    c = {e["id"]: e["costo_aceleracion"] for e in etapas}
    d = {e["id"]: e["reduccion_tiempo_si_acelera"] for e in etapas}

    acel = salida["etapas_aceleradas"]
    chequeos = {}
    chequeos["ids_validos_sin_repetidos"] = all(a in t for a in acel) and len(set(acel)) == len(acel)
    if not chequeos["ids_validos_sin_repetidos"]:
        return {"ok": False, "chequeos": chequeos}

    costo = sum(c[a] for a in acel)
    chequeos["costo_recalculado"] = costo
    chequeos["respeta_presupuesto"] = costo <= B
    chequeos["costo_coincide_con_la_salida"] = costo == salida["costo_usado"]

    normal = _duracion(ids, t, aristas, dict(t))
    final = _duracion(ids, t, aristas, {i: t[i] - (d[i] if i in acel else 0) for i in ids})
    chequeos["duracion_sin_acelerar_recalculada"] = normal
    chequeos["duracion_final_recalculada"] = final
    chequeos["duraciones_coinciden_con_la_salida"] = (
        normal == salida["duracion_sin_acelerar"] and final == salida["duracion_final"]
    )
    chequeos["ahorro_coincide"] = normal - final == salida["ahorro"]

    # ¿es óptima? Enumeración exhaustiva solo cuando el tamaño lo permite.
    candidatas = [i for i in ids if d[i] > 0 and c[i] <= B]
    entradas = {i: 0 for i in ids}
    salidas = {i: 0 for i in ids}
    for o, de in aristas:
        salidas[o] += 1
        entradas[de] += 1
    cadena = len(aristas) == len(ids) - 1 and all(v <= 1 for v in entradas.values()) and all(
        v <= 1 for v in salidas.values()
    )
    optimo = None
    if cadena and len(candidatas) <= exhaustivo_hasta + 4:
        # código Gray: cada paso cambia una sola etapa, así que la actualización es O(1)
        m = len(candidatas)
        total = sum(t.values())
        mejor = total
        costo_a = ahorro_a = 0
        estado = [0] * m
        for paso in range(1, 1 << m):
            k = (paso & -paso).bit_length() - 1
            i = candidatas[k]
            if estado[k]:
                estado[k] = 0
                costo_a -= c[i]
                ahorro_a -= d[i]
            else:
                estado[k] = 1
                costo_a += c[i]
                ahorro_a += d[i]
            if costo_a <= B and total - ahorro_a < mejor:
                mejor = total - ahorro_a
        optimo = mejor
    elif len(candidatas) <= 14:
        mejor = normal
        for tam in range(1, len(candidatas) + 1):
            for sub in combinations(candidatas, tam):
                if sum(c[i] for i in sub) <= B:
                    dur = _duracion(ids, t, aristas, {i: t[i] - (d[i] if i in sub else 0) for i in ids})
                    mejor = min(mejor, dur)
        optimo = mejor
    if optimo is None:
        chequeos["optimalidad"] = "no verificada (instancia demasiado grande para enumerar)"
        optima = True
    else:
        chequeos["duracion_optima_por_enumeracion"] = optimo
        chequeos["es_optima"] = optimo == final
        optima = optimo == final

    ok = (
        chequeos["respeta_presupuesto"]
        and chequeos["costo_coincide_con_la_salida"]
        and chequeos["duraciones_coinciden_con_la_salida"]
        and chequeos["ahorro_coincide"]
        and optima
    )
    return {"ok": bool(ok), "chequeos": chequeos}


def verificar_parte2(ruta_json, salida, exhaustivo_hasta=22):
    """Comprueba la salida de la Parte 2: cada etapa es un candidato con su lista de riesgos."""
    raw, etapas, _ = _cargar(ruta_json)
    universo = [x["id"] if isinstance(x, dict) else x for x in raw.get("categorias_riesgo", [])]
    por_id = {e["id"]: set(e.get("riesgos_cubiertos_auditoria_completa", [])) for e in etapas}
    chequeos = {}
    elegidos = salida["interacciones_elegidas"]
    if not universo:
        universo = sorted(set().union(*por_id.values()))
    chequeos["ids_validos_sin_repetidos"] = all(e in por_id for e in elegidos) and len(set(elegidos)) == len(elegidos)
    if not chequeos["ids_validos_sin_repetidos"]:
        return {"ok": False, "chequeos": chequeos}
    cubiertas = set().union(*[por_id[e] for e in elegidos]) if elegidos else set()
    faltan = [u for u in universo if u not in cubiertas]
    chequeos["categorias_sin_cubrir"] = faltan
    chequeos["cubre_todas"] = not faltan
    chequeos["tamano_coincide"] = len(elegidos) == salida["tamano"]

    ids = [e["id"] for e in etapas]
    optimo = None
    if len(ids) <= exhaustivo_hasta and not faltan:
        for k in range(1, len(ids) + 1):
            if any(set().union(*[por_id[i] for i in sub]) >= set(universo) for sub in combinations(ids, k)):
                optimo = k
                break
    if optimo is not None:
        chequeos["optimo_por_enumeracion"] = optimo
        chequeos["brecha_voraz_menos_optimo"] = len(elegidos) - optimo
        d = max((len(s) for s in por_id.values()), default=1) or 1
        H = sum(1 / i for i in range(1, d + 1))
        chequeos["cota_H(d)*optimo"] = round(H * optimo, 4)
        chequeos["cumple_la_cota_de_aproximacion"] = len(elegidos) <= H * optimo + 1e-9
    else:
        chequeos["optimo_por_enumeracion"] = "no calculado (instancia grande o infactible)"
    ok = chequeos["cubre_todas"] and chequeos["tamano_coincide"]
    if optimo is not None:
        ok = ok and chequeos["cumple_la_cota_de_aproximacion"]
    return {"ok": bool(ok), "chequeos": chequeos}
