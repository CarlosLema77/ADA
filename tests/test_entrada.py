import copy
import json

import pytest

from ada.entrada import leer_instancia
from ada.errores import ErrorDeEntrada
from helpers import CASO_PROFE, caso_dict


def base():
    return caso_dict([5, 6, 7], [2, 3, 4], [1, 2, 3], 6, completas=[["R1"], ["R2"], ["R1", "R3"]])


def test_lee_el_caso_de_la_profesora():
    inst = leer_instancia(CASO_PROFE)
    assert (inst.n, inst.r, inst.B, len(inst.aristas)) == (20, 12, 72, 19)
    assert inst.advertencias == []
    assert inst.B_conjunto == 100
    assert [inst.etapas[k].id for k in inst.orden] == [f"E{k:02d}" for k in range(1, 21)]


@pytest.mark.parametrize(
    "cambio, texto",
    [
        (lambda d: d["etapas"].append(copy.deepcopy(d["etapas"][0])), "repetido"),
        (lambda d: d["etapas"][0].update(reduccion_tiempo_si_acelera=99), "no puede superar"),
        (lambda d: d["etapas"][0].update(costo_aceleracion=-1), ">= 0"),
        (lambda d: d["etapas"][0].update(duracion_normal=3.5), "entero"),
        (lambda d: d["etapas"][0].update(duracion_normal=True), "entero"),
        (lambda d: d["etapas"][0].update(duracion_normal="10"), "entero"),
        (lambda d: d["flujo"].append({"origen": "E01", "destino": "E99"}), "no es una etapa conocida"),
        (lambda d: d["flujo"].append({"origen": "E02", "destino": "E02"}), "sí misma"),
        (lambda d: d["flujo"].append({"origen": "E03", "destino": "E01"}), "ciclo"),
        (lambda d: d["etapas"][0].update(riesgos_cubiertos_auditoria_completa=["R9"]), "no existe en categorias_riesgo"),
        (lambda d: d["parametros"].pop("presupuesto_aceleracion_B"), "presupuesto_aceleracion_B"),
        (lambda d: d["parametros"].update(presupuesto_aceleracion_B=-5), ">= 0"),
        (lambda d: d.pop("flujo"), "falta la lista 'flujo'"),
        (lambda d: d.pop("etapas"), "falta la lista 'etapas'"),
        (lambda d: d.update(etapas=[]), "vacía"),
        (lambda d: d["etapas"][1].pop("costo_aceleracion"), "costo_aceleracion"),
    ],
)
def test_entradas_invalidas_dan_mensajes_claros(cambio, texto):
    d = base()
    cambio(d)
    with pytest.raises(ErrorDeEntrada) as e:
        leer_instancia(d)
    assert texto in str(e.value)


def test_json_roto_y_archivo_inexistente(tmp_path):
    malo = tmp_path / "malo.json"
    malo.write_text("{no es json", encoding="utf-8")
    with pytest.raises(ErrorDeEntrada, match="no es un JSON válido"):
        leer_instancia(malo)
    with pytest.raises(ErrorDeEntrada, match="no existe"):
        leer_instancia(tmp_path / "nada.json")


def test_claves_alternativas_y_claves_extra_se_toleran():
    d = base()
    d["estaciones"] = d.pop("etapas")
    d["caminos"] = [{"desde": a["origen"], "hasta": a["destino"]} for a in d.pop("flujo")]
    d["comentario_cualquiera"] = {"x": 1}
    inst = leer_instancia(d)
    assert inst.n == 3 and len(inst.aristas) == 2


def test_orden_topologico_aunque_las_etapas_vengan_desordenadas():
    d = caso_dict([1, 1, 1], [1, 1, 1], [0, 0, 0], 0, ids=["C", "A", "B"], aristas=[("A", "B"), ("B", "C")])
    inst = leer_instancia(d)
    assert [inst.etapas[k].id for k in inst.orden] == ["A", "B", "C"]


def test_advertencias_por_conteos_declarados_y_aristas_repetidas():
    d = base()
    d["parametros"]["numero_etapas"] = 7
    d["flujo"].append(copy.deepcopy(d["flujo"][0]))
    inst = leer_instancia(d)
    assert any("numero_etapas" in a for a in inst.advertencias)
    assert any("repetida" in a for a in inst.advertencias)
    assert len(inst.aristas) == 2


def test_sin_categorias_se_deriva_el_universo():
    d = base()
    d.pop("categorias_riesgo")
    inst = leer_instancia(d)
    assert inst.categorias == ["R1", "R2", "R3"] and inst.advertencias


def test_caso_de_una_sola_etapa_sin_flujo():
    d = caso_dict([5], [2], [3], 4)
    d.pop("flujo")
    inst = leer_instancia(d)
    assert inst.n == 1 and inst.aristas == []


def test_el_archivo_original_no_se_modifica_al_leerlo():
    antes = CASO_PROFE.read_bytes()
    leer_instancia(CASO_PROFE)
    assert CASO_PROFE.read_bytes() == antes
    json.loads(antes)
