import json
import random

import ejecutar_casos
from ada import verificadores
from ada import aceleracion
from ada.entrada import leer_instancia
from helpers import CASO_PROFE, caso_dict, dag_aleatorio


def test_corrida_completa_sobre_el_caso_de_la_profesora(tmp_path):
    codigo = ejecutar_casos.main([str(CASO_PROFE), "--salida", str(tmp_path), "--repeticiones", "2"])
    assert codigo == 0
    carpeta = tmp_path / "caso_01_entrada_G3_mochila_20_nodos"
    for nombre in ["parte1_salida.json", "parte1_traza.json", "parte2_salida.json", "parte2_traza.json",
                   "tiempos.json", "verificacion.json", "traza_legible.txt"]:
        assert (carpeta / nombre).exists(), nombre
    p1 = json.loads((carpeta / "parte1_salida.json").read_text(encoding="utf-8"))
    p2 = json.loads((carpeta / "parte2_salida.json").read_text(encoding="utf-8"))
    assert (p1["ahorro"], p1["duracion_final"], p2["tamano"]) == (55, 446, 4)
    assert p1["version"] == "entrega1-1.1"
    tiempos = json.loads((carpeta / "tiempos.json").read_text(encoding="utf-8"))
    assert tiempos["parte1"]["repeticiones"] == 2 and tiempos["parte1"]["mediana_ms"] >= 0
    assert (tmp_path / "resumen.md").exists() and (tmp_path / "resumen.csv").exists()


def test_un_caso_malo_no_tumba_a_los_demas(tmp_path):
    malos = tmp_path / "in"
    malos.mkdir()
    ciclo = caso_dict([1, 1], [1, 1], [0, 0], 0, aristas=[("E01", "E02"), ("E02", "E01")])
    (malos / "a_ciclo.json").write_text(json.dumps(ciclo), encoding="utf-8")
    bueno = caso_dict([5, 6], [2, 3], [1, 2], 3, completas=[["R1"], ["R2"]])
    (malos / "b_bueno.json").write_text(json.dumps(bueno), encoding="utf-8")
    codigo = ejecutar_casos.main([str(malos), "--salida", str(tmp_path / "out"), "--repeticiones", "1"])
    assert codigo == 1  # hubo un caso con error
    assert "ciclo" in json.loads((tmp_path / "out" / "caso_01_a_ciclo" / "error.json").read_text(encoding="utf-8"))["error_de_entrada"]
    assert (tmp_path / "out" / "caso_02_b_bueno" / "parte1_salida.json").exists()


def test_caso_infactible_en_auditoria_se_reporta_sin_romper(tmp_path):
    d = caso_dict([5, 6], [2, 3], [1, 2], 3, completas=[["R1"], ["R1"]], categorias=["R1", "R2"])
    (tmp_path / "inf.json").write_text(json.dumps(d), encoding="utf-8")
    codigo = ejecutar_casos.main([str(tmp_path / "inf.json"), "--salida", str(tmp_path / "out"), "--repeticiones", "1"])
    assert codigo == 0
    p2 = json.loads((tmp_path / "out" / "caso_01_inf" / "parte2_salida.json").read_text(encoding="utf-8"))
    assert p2["factible"] is False and p2["categorias_sin_cubrir"] == ["R2"]


def test_el_verificador_detecta_una_solucion_mala(tmp_path):
    d = caso_dict([10, 8, 12, 6], [4, 3, 5, 2], [5, 4, 7, 3], 7)
    ruta = tmp_path / "c.json"
    ruta.write_text(json.dumps(d), encoding="utf-8")
    salida, _ = aceleracion.resolver(leer_instancia(ruta))
    assert verificadores.verificar_parte1(ruta, salida)["ok"] is True
    # se pasa del presupuesto
    mala = dict(salida, etapas_aceleradas=["E01", "E02", "E03"], costo_usado=12)
    assert verificadores.verificar_parte1(ruta, mala)["ok"] is False
    # respeta el presupuesto pero no es óptima
    peor = dict(salida, etapas_aceleradas=["E04"], costo_usado=2, duracion_final=33, ahorro=3)
    assert verificadores.verificar_parte1(ruta, peor)["ok"] is False
    # mentira en la duración
    mentira = dict(salida, duracion_final=1)
    assert verificadores.verificar_parte1(ruta, mentira)["ok"] is False


def test_verificador_acepta_dag_aleatorios(tmp_path):
    rng = random.Random(99)
    for k in range(25):
        ids, t, c, d, B, aristas = dag_aleatorio(rng)
        ruta = tmp_path / f"d{k}.json"
        ruta.write_text(json.dumps(caso_dict(t, c, d, B, aristas=aristas, ids=ids)), encoding="utf-8")
        salida, _ = aceleracion.resolver(leer_instancia(ruta))
        assert verificadores.verificar_parte1(ruta, salida)["ok"] is True
