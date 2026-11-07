import random
from math import log

import pytest

from ada import auditoria
from ada.entrada import leer_instancia
from ada.errores import InstanciaInfactible
from helpers import CASO_PROFE, caso_dict, optimo_cobertura


def inst_de(conjuntos, r=None):
    cats = [f"R{k + 1}" for k in range(r if r is not None else (max((max(s) for s in conjuntos if s), default=-1) + 1))]
    completas = [[cats[k] for k in s] for s in conjuntos]
    n = len(conjuntos)
    return leer_instancia(caso_dict([1] * n, [1] * n, [0] * n, 0, completas=completas, categorias=cats))


def test_caso_de_la_profesora_cobertura_de_cuatro():
    s, traza = auditoria.resolver(leer_instancia(CASO_PROFE))
    assert s["tamano"] == 4 and s["interacciones_elegidas"] == ["E01", "E16", "E06", "E03"]
    assert [v["ganancia"] for v in traza["vueltas"]] == [4, 4, 3, 1]
    assert traza["vueltas"][-1]["faltan"] == 0


def test_ejemplo_del_informe_voraz_no_es_optimo():
    inst = inst_de([[0, 1, 2, 3], [0, 2, 4], [1, 3, 5]], r=6)
    s, _ = auditoria.resolver(inst)
    assert s["tamano"] == 3 and s["interacciones_elegidas"] == ["E01", "E02", "E03"]
    assert auditoria.optimo_exacto(6, [[0, 1, 2, 3], [0, 2, 4], [1, 3, 5]])[0] == 2


def test_infactible_nombra_las_categorias_sin_cubrir():
    inst = inst_de([[0], [1]], r=4)
    with pytest.raises(InstanciaInfactible) as e:
        auditoria.resolver(inst)
    assert e.value.categorias_sin_cubrir == ["R3", "R4"]
    assert auditoria.categorias_sin_cubrir(4, [[0], [1]]) == [2, 3]


def test_una_sola_interaccion_cubre_todo():
    s, _ = auditoria.resolver(inst_de([[0, 1, 2], [0], [1]]))
    assert s["tamano"] == 1 and s["interacciones_elegidas"] == ["E01"]


def test_una_sola_categoria():
    s, _ = auditoria.resolver(inst_de([[0], [0]], r=1))
    assert s["interacciones_elegidas"] == ["E01"]


def test_empate_gana_la_primera_en_la_entrada():
    s, _ = auditoria.resolver(inst_de([[0], [0], [0]], r=1))
    assert s["interacciones_elegidas"] == ["E01"]
    s, _ = auditoria.resolver(inst_de([[0, 1], [2, 3]], r=4))
    assert s["interacciones_elegidas"] == ["E01", "E02"]


def test_interacciones_repetidas_y_categorias_repetidas_en_la_lista():
    d = caso_dict([1, 1], [1, 1], [0, 0], 0, completas=[["R1", "R1", "R2"], ["R1", "R2"]], categorias=["R1", "R2"])
    s, traza = auditoria.resolver(leer_instancia(d))
    assert s["tamano"] == 1 and traza["vueltas"][0]["ganancia"] == 2


def test_interaccion_que_no_cubre_nada_nunca_se_elige():
    s, _ = auditoria.resolver(inst_de([[], [0, 1]], r=2))
    assert s["interacciones_elegidas"] == ["E02"]


def test_las_variaciones_de_auditoria_no_cambian_los_candidatos():
    d = caso_dict([1], [1], [0], 0, completas=[["R1", "R2"]], categorias=["R1", "R2"])
    d["etapas"][0]["variaciones_auditoria"] = [
        {"id": "parcial", "costo": 1, "riesgos_cubiertos": ["R1"]},
        {"id": "completa", "costo": 2, "riesgos_cubiertos": ["R1", "R2"]},
    ]
    ids, conj = auditoria.construir_candidatos(leer_instancia(d))
    assert ids == ["E01"] and conj == [[0, 1]]
    # variaciones mal formadas o ausentes no rompen la lectura: el campo no se usa
    d["etapas"][0]["variaciones_auditoria"] = [{"x": 1}, "texto", {"id": "p", "riesgos_cubiertos": "mal"}]
    assert leer_instancia(d).n == 1
    d["etapas"][0].pop("variaciones_auditoria")
    assert leer_instancia(d).n == 1


def aleatorio(rng):
    r = rng.randint(1, 10)
    n = rng.randint(1, 9)
    conj = [rng.sample(range(r), rng.randint(0, r)) for _ in range(n)]
    return r, conj


@pytest.mark.parametrize("semilla", range(3))
def test_voraz_cumple_cobertura_y_cota_contra_fuerza_bruta(semilla):
    rng = random.Random(500 + semilla)
    revisadas = 0
    for _ in range(600):
        r, conj = aleatorio(rng)
        opt = optimo_cobertura(r, conj)
        if opt is None:
            with pytest.raises(InstanciaInfactible):
                auditoria.voraz(r, conj)
            continue
        elegidos, traza = auditoria.voraz(r, conj)
        assert set().union(*[set(conj[j]) for j in elegidos]) == set(range(r))
        assert len(set(elegidos)) == len(elegidos) <= min(len(conj), r)
        d = max(len(set(s)) for s in conj)
        H = sum(1 / i for i in range(1, d + 1))
        assert len(elegidos) <= H * opt + 1e-9
        assert H <= log(r) + 1 + 1e-9 or d == 1
        assert len(elegidos) >= opt
        assert auditoria.optimo_exacto(r, conj)[0] == opt
        revisadas += 1
    assert revisadas > 200


def test_la_traza_de_cada_vuelta_es_consistente():
    inst = leer_instancia(CASO_PROFE)
    _, traza = auditoria.resolver(inst)
    acumulado = 0
    for v in traza["vueltas"]:
        acumulado += v["ganancia"]
        assert v["cubiertas_acumuladas"] == acumulado == inst.r - v["faltan"]
        assert len(v["categorias_nuevas"]) == v["ganancia"]


def test_ejemplo_de_la_reduccion_grafo_de_cinco_vertices():
    # a..e = interacciones; aristas 1=ab 2=ac 3=bc 4=bd 5=ce 6=de = categorías
    conj = [[0, 1], [0, 2, 3], [1, 2, 4], [3, 5], [4, 5]]
    s, _ = auditoria.resolver(inst_de(conj, r=6))
    assert s["interacciones_elegidas"] == ["E02", "E03", "E04"]  # b, c, d
    assert auditoria.optimo_exacto(6, conj)[0] == 3


def test_traza_lista_faltantes_y_todas_las_empatadas():
    s, traza = auditoria.resolver(leer_instancia(CASO_PROFE))
    v1 = traza["vueltas"][0]
    assert len(v1["empatadas_que_perdieron_por_desempate"]) == 11  # 12 etapas con ganancia 4; gana E01
    assert len(v1["categorias_faltantes"]) == v1["faltan"] == 8
    sin, ninguna = auditoria.resolver(leer_instancia(CASO_PROFE), con_traza=False)
    assert ninguna is None and sin == s
