from src.verificadores.aceleracion import verificar

CASO = {"B": 7, "etapas": [
    {"id": "E1", "t": 10, "c": 3, "d": 4}, {"id": "E2", "t": 8, "c": 4, "d": 5},
    {"id": "E3", "t": 6, "c": 2, "d": 3}, {"id": "E4", "t": 5, "c": 5, "d": 4}]}


def test_salida_correcta():
    s = {"etapas_aceleradas": ["E1", "E2"], "costo_total": 7, "reduccion_total": 9, "duracion_total": 20}
    assert verificar(CASO, s) == []


def test_detecta_suboptima():
    s = {"etapas_aceleradas": ["E2", "E3"], "costo_total": 6, "reduccion_total": 8, "duracion_total": 21}
    assert any("No es óptima" in e for e in verificar(CASO, s))


def test_detecta_presupuesto_excedido_y_totales_falsos():
    s = {"etapas_aceleradas": ["E1", "E4"], "costo_total": 7, "reduccion_total": 8, "duracion_total": 21}
    errores = verificar(CASO, s)
    assert any("Excede el presupuesto" in e for e in errores)
    assert any("costo_total" in e for e in errores)


def test_detecta_etapas_inexistentes_y_repetidas():
    assert verificar(CASO, {"etapas_aceleradas": ["E9"]})
    assert any("repetidas" in e for e in verificar(CASO, {"etapas_aceleradas": ["E1", "E1"]}))


def test_presupuesto_cero():
    assert verificar(CASO | {"B": 0}, {"etapas_aceleradas": [], "duracion_total": 29}) == []


def test_formato_profesora():
    import json
    from pathlib import Path
    caso = json.loads((Path(__file__).parent.parent / "casos/profesora/entrada_G3_mochila_20_nodos.json").read_text())
    # Cualquier salida que no logre 55 de reducción con B = 72 debe marcarse como no óptima.
    errores = verificar(caso, {"etapas_aceleradas": ["E01"]})
    assert any("logra 55" in e for e in errores)
