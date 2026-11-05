"""Pruebas de la Parte 2: ejemplo a mano, bordes, validación, voraz vs. óptimo y cota H(d)."""
import random

import pytest

from src.parte2_auditoria.factibilidad import es_cobertura
from src.parte2_auditoria.fuerza_bruta import cobertura_optima_fuerza_bruta
from src.parte2_auditoria.lector import instancia_desde_dict
from src.parte2_auditoria.modelo import EntradaInvalida, InstanciaNoFactible
from src.parte2_auditoria.voraz import cobertura_voraz


def inst(r, sets):
    return instancia_desde_dict({"r": r, "interacciones": [
        {"id": f"I{j}", "categorias": s} for j, s in enumerate(sets, 1)]})


def H(d):
    return sum(1 / i for i in range(1, d + 1))


# ---------- Ejemplo resuelto a mano (n = 5, r = 4) ----------
def test_ejemplo_a_mano_con_traza():
    x = inst(4, [[1, 2], [2, 3], [3, 4], [1, 4], [2]])
    res = cobertura_voraz(x)
    assert res.seleccion == ["I1", "I3"]
    p1, p2 = res.traza
    assert (p1.elegida, p1.ganancia, p1.categorias_nuevas, p1.faltantes) == ("I1", 2, [1, 2], [3, 4])
    assert p1.empatadas == ["I2", "I3", "I4"]          # el desempate por posición decidió
    assert (p2.elegida, p2.categorias_nuevas, p2.faltantes) == ("I3", [3, 4], [])
    assert cobertura_optima_fuerza_bruta(x).tamano == 2


# ---------- Bordes ----------
def test_una_interaccion_cubre_todo():
    assert cobertura_voraz(inst(5, [[1, 2], [1, 2, 3, 4, 5], [3]])).seleccion == ["I2"]


def test_r_igual_1_con_vacia_y_repetidas():
    assert cobertura_voraz(inst(1, [[], [1], [1]])).seleccion == ["I2"]


def test_voraz_no_optimo():
    x = inst(6, [[1, 2, 3], [4, 5, 6], [1, 2, 4, 5]])
    assert cobertura_voraz(x).tamano == 3
    assert cobertura_optima_fuerza_bruta(x).tamano == 2


def test_no_factible_reporta_categorias():
    with pytest.raises(InstanciaNoFactible) as e:
        cobertura_voraz(inst(5, [[1, 2], [2, 3]]))
    assert e.value.faltantes == [4, 5]


# ---------- Validación de entrada ----------
@pytest.mark.parametrize("datos", [
    {"r": 0, "interacciones": [{"categorias": []}]},
    {"r": 3, "interacciones": []},
    {"r": 3, "interacciones": [{"categorias": [4]}]},
    {"r": 3, "interacciones": [{"categorias": [1, 1]}]},
    {"r": 3, "interacciones": [{"id": "a", "categorias": [1]}, {"id": "a", "categorias": [2]}]},
    {"r": 3, "interacciones": [{"categorias": [1], "costo": 0}]},
    {"r": "3", "interacciones": [{"categorias": [1]}]},
])
def test_entradas_invalidas(datos):
    with pytest.raises(EntradaInvalida):
        instancia_desde_dict(datos)


# ---------- Aleatorias: voraz siempre cubre y respeta |voraz| ≤ H(d)·OPT ----------
def instancia_aleatoria(rng, n, r, p):
    sets = [[k for k in range(1, r + 1) if rng.random() < p] for _ in range(n)]
    for k in range(1, r + 1):                      # garantiza factibilidad
        if not any(k in s for s in sets):
            sets[rng.randrange(n)].append(k)
    return inst(r, [sorted(s) for s in sets])


def test_voraz_contra_fuerza_bruta_y_cota():
    rng = random.Random(2026)                      # semilla fija: reproducible
    peor = 1.0
    for _ in range(1500):
        n, r = rng.randint(1, 10), rng.randint(1, 12)
        x = instancia_aleatoria(rng, n, r, rng.choice([0.15, 0.3, 0.5]))
        v = cobertura_voraz(x, con_traza=False)
        o = cobertura_optima_fuerza_bruta(x)
        assert es_cobertura(x, v.seleccion)
        assert es_cobertura(x, o.seleccion)
        assert o.tamano <= v.tamano
        assert v.tamano <= H(x.d) * o.tamano + 1e-9
        assert v.tamano <= min(n, r)               # a lo sumo min(n, r) elecciones
        peor = max(peor, v.tamano / o.tamano)
    assert peor >= 1.0


def test_traza_es_coherente():
    rng = random.Random(7)
    for _ in range(200):
        x = instancia_aleatoria(rng, rng.randint(1, 15), rng.randint(1, 20), 0.3)
        res = cobertura_voraz(x)
        acumuladas = 0
        for paso in res.traza:
            assert paso.ganancia == len(paso.categorias_nuevas) >= 1
            acumuladas += paso.ganancia
            assert paso.cubiertas_acumuladas == acumuladas
            assert len(paso.faltantes) == x.r - acumuladas
        assert acumuladas == x.r


# ---------- Caso real de la profesora ----------
def test_caso_profesora_20_etapas():
    from pathlib import Path
    from src.parte2_auditoria.lector import leer_instancia
    x = leer_instancia(Path(__file__).parent.parent / "casos/profesora/entrada_G3_mochila_20_nodos.json")
    assert (x.n, x.r, x.d) == (20, 12, 4)
    assert x.etiqueta(1) == "R01" and x.interacciones[0].id == "E01"
    v = cobertura_voraz(x)
    assert v.seleccion == ["E01", "E16", "E06", "E03"]
    assert cobertura_optima_fuerza_bruta(x).tamano == 4      # no existe auditoría de 3
