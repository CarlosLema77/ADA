import random

import pytest

from ada import aceleracion
from ada.entrada import leer_instancia
from helpers import (
    CASO_PROFE,
    cadena_aleatoria,
    caso_dict,
    dag_aleatorio,
    duracion_dag,
    optimo_fuerza_bruta,
)


def resolver(t, c, d, B, **kw):
    return aceleracion.resolver(leer_instancia(caso_dict(t, c, d, B)), **kw)[0]


# ------------------------------------------------------------------ ejemplo del informe (n = 4)
def test_ejemplo_de_cuatro_etapas_del_informe():
    s = resolver([10, 8, 12, 6], [4, 3, 5, 2], [5, 4, 7, 3], 7)
    assert s["etapas_aceleradas"] == ["E03", "E04"]
    assert (s["costo_usado"], s["ahorro"], s["duracion_final"], s["duracion_sin_acelerar"]) == (7, 10, 26, 36)
    assert s["metodo"] == "programacion_dinamica_cadena"


def test_caso_de_la_profesora_resultado_de_referencia():
    s, traza = aceleracion.resolver(leer_instancia(CASO_PROFE))
    assert (s["ahorro"], s["duracion_final"], s["duracion_sin_acelerar"], s["costo_usado"]) == (55, 446, 501, 72)
    assert s["etapas_aceleradas"] == ["E02", "E03", "E04", "E06", "E08", "E12"]
    assert s["optimo_probado"] is True
    assert traza["dimension_tabla"] == {"filas": 21, "columnas": 73}
    assert len(traza["tabla_dp"]) == 21 and len(traza["decisiones_reconstruccion"]) == 20


# ------------------------------------------------------------------ casos borde
def test_presupuesto_cero_no_acelera_nada():
    s = resolver([5, 6], [2, 3], [1, 2], 0)
    assert s["etapas_aceleradas"] == [] and s["duracion_final"] == 11


def test_presupuesto_de_sobra_acelera_todo_lo_que_ahorra():
    s = resolver([5, 6, 7], [2, 3, 4], [1, 2, 3], 1000)
    assert s["etapas_aceleradas"] == ["E01", "E02", "E03"] and s["ahorro"] == 6


def test_etapa_sin_ahorro_nunca_se_acelera():
    s = resolver([5, 6], [1, 1], [0, 2], 10)
    assert s["etapas_aceleradas"] == ["E02"]


def test_etapa_mas_cara_que_el_presupuesto_se_ignora():
    s = resolver([5, 6], [50, 3], [5, 2], 10)
    assert s["etapas_aceleradas"] == ["E02"] and s["costo_usado"] == 3


def test_etapa_gratis_con_ahorro_siempre_se_acelera():
    s = resolver([5, 6], [0, 3], [4, 2], 0)
    assert s["etapas_aceleradas"] == ["E01"] and s["costo_usado"] == 0 and s["ahorro"] == 4


def test_una_sola_etapa():
    assert resolver([9], [3], [4], 3)["duracion_final"] == 5
    assert resolver([9], [3], [4], 2)["duracion_final"] == 9


def test_empate_no_acelera_de_mas():
    # acelerar E02 no mejora el ahorro (d=0): la solución no la incluye
    s = resolver([4, 4], [1, 1], [3, 0], 5)
    assert s["etapas_aceleradas"] == ["E01"]


def test_la_salida_es_coherente_consigo_misma():
    s = resolver([10, 8, 12, 6], [4, 3, 5, 2], [5, 4, 7, 3], 7)
    assert s["duracion_final"] == s["duracion_sin_acelerar"] - s["ahorro"]
    assert sum(s["x"].values()) == len(s["etapas_aceleradas"])
    assert s["costo_usado"] <= s["presupuesto_B"]


# ------------------------------------------------------------------ contra fuerza bruta
@pytest.mark.parametrize("semilla", range(3))
def test_dp_de_cadena_contra_fuerza_bruta(semilla):
    rng = random.Random(1000 + semilla)
    for _ in range(250):
        t, c, d, B = cadena_aleatoria(rng)
        s = resolver(t, c, d, B)
        ids = [f"E{k + 1:02d}" for k in range(len(t))]
        aristas = [(ids[k], ids[k + 1]) for k in range(len(t) - 1)]
        mejor = optimo_fuerza_bruta(ids, dict(zip(ids, t)), dict(zip(ids, c)), dict(zip(ids, d)), B, aristas)
        assert s["duracion_final"] == mejor, (t, c, d, B)
        assert s["costo_usado"] <= B


@pytest.mark.parametrize("semilla", range(3))
def test_solver_general_contra_fuerza_bruta_en_dag(semilla):
    rng = random.Random(2000 + semilla)
    for _ in range(150):
        ids, t, c, d, B, aristas = dag_aleatorio(rng)
        inst = leer_instancia(caso_dict(t, c, d, B, aristas=aristas, ids=ids))
        s = aceleracion.resolver(inst)[0]
        td, cd, dd = dict(zip(ids, t)), dict(zip(ids, c)), dict(zip(ids, d))
        assert s["duracion_final"] == optimo_fuerza_bruta(ids, td, cd, dd, B, aristas), (ids, t, c, d, B, aristas)
        assert s["optimo_probado"] is True
        assert s["costo_usado"] <= B
        assert s["duracion_final"] == duracion_dag(ids, td, aristas, set(s["etapas_aceleradas"]), dd)


def test_dp_y_solver_general_coinciden_en_cadenas():
    rng = random.Random(3000)
    for _ in range(200):
        t, c, d, B = cadena_aleatoria(rng)
        inst = leer_instancia(caso_dict(t, c, d, B))
        a = aceleracion.resolver(inst)[0]
        b = aceleracion.resolver(inst, forzar_general=True)[0]
        assert a["metodo"] == "programacion_dinamica_cadena" and b["metodo"] == "ramificacion_y_acotamiento"
        assert a["duracion_final"] == b["duracion_final"]


# ------------------------------------------------------------------ flujos con rutas paralelas
def test_diamante_la_ruta_mas_larga_manda():
    # A -> {B, C} -> D ; B es la rama larga. Solo acelerar B (la rama crítica) reduce la duración.
    ids = ["A", "B", "C", "D"]
    t, c, d = [2, 10, 4, 2], [1, 5, 1, 1], [1, 6, 3, 1]
    inst = leer_instancia(caso_dict(t, c, d, 5, ids=ids, aristas=[("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]))
    s = aceleracion.resolver(inst)[0]
    assert s["metodo"] == "ramificacion_y_acotamiento"
    assert s["duracion_sin_acelerar"] == 14
    assert s["etapas_aceleradas"] == ["B"] or "B" in s["etapas_aceleradas"]
    assert s["duracion_final"] == 8  # A(2)+B(4)+D(2)


def test_acelerar_una_rama_no_critica_no_ayuda():
    ids = ["A", "B", "C"]  # A y B en paralelo, ambos hacia C
    inst = leer_instancia(caso_dict([10, 3, 1], [1, 1, 1], [2, 3, 0], 1, ids=ids, aristas=[("A", "C"), ("B", "C")]))
    s = aceleracion.resolver(inst)[0]
    assert s["etapas_aceleradas"] == ["A"] and s["duracion_final"] == 9


def test_etapas_independientes_sin_aristas():
    ids = ["A", "B"]
    inst = leer_instancia(caso_dict([10, 7], [3, 3], [4, 4], 3, ids=ids, aristas=[]))
    s = aceleracion.resolver(inst)[0]
    assert s["duracion_sin_acelerar"] == 10 and s["duracion_final"] == 7 and s["etapas_aceleradas"] == ["A"]


def test_limite_de_nodos_se_reporta_como_no_probado():
    rng = random.Random(7)
    n = 22
    ids = [f"E{k + 1:02d}" for k in range(n)]
    t = [rng.randint(10, 30) for _ in range(n)]
    c = [rng.randint(3, 9) for _ in range(n)]
    d = [rng.randint(2, 8) for _ in range(n)]
    aristas = [(ids[k], ids[k + 2]) for k in range(n - 2)] + [(ids[k], ids[k + 1]) for k in range(0, n - 1, 3)]
    inst = leer_instancia(caso_dict(t, c, d, 60, ids=ids, aristas=aristas))
    s = aceleracion.resolver(inst, limite_nodos=5)[0]
    assert s["optimo_probado"] is False
    assert s["costo_usado"] <= 60 and s["duracion_final"] <= s["duracion_sin_acelerar"]


def test_la_traza_del_dp_reconstruye_la_misma_solucion():
    inst = leer_instancia(CASO_PROFE)
    s, traza = aceleracion.resolver(inst)
    por_decision = [x["etapa"] for x in traza["decisiones_reconstruccion"] if x["acelerar"]]
    assert por_decision == s["etapas_aceleradas"]
    assert sum(x["costo"] for x in traza["decisiones_reconstruccion"]) == s["costo_usado"]
    ultimo = traza["decisiones_reconstruccion"][0]  # primera etapa de la cadena: presupuesto final
    assert ultimo["presupuesto_despues"] + 0 >= 0
