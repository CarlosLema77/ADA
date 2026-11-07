"""Lectura y validación de los casos (formato JSON de la profesora).

Estructura esperada (las claves que no se mencionan aquí se ignoran):

    parametros: {presupuesto_aceleracion_B, [numero_etapas], [numero_categorias_riesgo],
                 [presupuesto_conjunto_aceleracion_y_auditoria]}
    flujo:      [{origen, destino}, ...]            (también se acepta "caminos")
    etapas:     [{id, duracion_normal, costo_aceleracion, reduccion_tiempo_si_acelera,
                  riesgos_cubiertos_auditoria_completa, variaciones_auditoria}, ...]
                                                     (también se acepta "estaciones")
    categorias_riesgo: [{id, categoria, importancia}, ...]

Cualquier problema produce un ErrorDeEntrada que dice qué campo falla y por qué.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from .errores import ErrorDeEntrada
from .grafo import orden_topologico

CLAVES_ETAPAS = ("etapas", "estaciones")
CLAVES_FLUJO = ("flujo", "caminos")
CLAVES_ORIGEN = ("origen", "desde")
CLAVES_DESTINO = ("destino", "hasta")


@dataclass(frozen=True)
class Etapa:
    id: str
    t: int  # duración normal
    c: int  # costo de acelerar
    d: int  # reducción de tiempo si se acelera
    completa: tuple  # ids de las categorías que cubre la auditoría completa
    variaciones: tuple  # solo se lee; no se usa (se usa la auditoría completa)


@dataclass
class Instancia:
    nombre: str
    etapas: list
    aristas: list  # [(id_origen, id_destino)]
    categorias: list  # ids de categoría, en el orden del archivo
    importancia: dict  # id de categoría -> importancia (si el archivo la trae)
    B: int
    B_conjunto: object  # presupuesto conjunto (variante 2) o None
    advertencias: list = field(default_factory=list)
    orden: list = field(default_factory=list)  # orden topológico (índices de etapa)
    sucesores: list = field(default_factory=list)
    predecesores: list = field(default_factory=list)

    @property
    def n(self):
        return len(self.etapas)

    @property
    def r(self):
        return len(self.categorias)


def _entero(valor, ruta, minimo=None):
    if isinstance(valor, bool):
        raise ErrorDeEntrada(f"{ruta}: debe ser un número entero, llegó {valor!r}")
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    if not isinstance(valor, int):
        raise ErrorDeEntrada(f"{ruta}: debe ser un número entero, llegó {valor!r}")
    if minimo is not None and valor < minimo:
        raise ErrorDeEntrada(f"{ruta}: debe ser >= {minimo}, llegó {valor}")
    return valor


def _lista(raw, claves, ruta):
    for clave in claves:
        if clave in raw:
            valor = raw[clave]
            if not isinstance(valor, list):
                raise ErrorDeEntrada(f"'{clave}' debe ser una lista, llegó {type(valor).__name__}")
            return clave, valor
    return None, None


def _campo(diccionario, claves, ruta):
    for clave in claves:
        if clave in diccionario:
            return diccionario[clave]
    raise ErrorDeEntrada(f"{ruta}: falta la clave '{claves[0]}'")


def _ids_de_riesgos(valor, ruta):
    if not isinstance(valor, list):
        raise ErrorDeEntrada(f"{ruta}: debe ser una lista de identificadores de categoría")
    out = []
    for k, x in enumerate(valor):
        if not isinstance(x, str) or not x:
            raise ErrorDeEntrada(f"{ruta}[{k}]: debe ser un identificador de texto, llegó {x!r}")
        out.append(x)
    return tuple(dict.fromkeys(out))  # sin repetidos, conservando el orden


def leer_instancia(origen, nombre=None):
    """Lee un caso desde un archivo JSON (ruta) o desde un diccionario ya cargado."""
    if isinstance(origen, dict):
        raw = origen
        nombre = nombre or "instancia"
    else:
        ruta_archivo = Path(origen)
        nombre = nombre or ruta_archivo.stem
        try:
            with open(ruta_archivo, encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            raise ErrorDeEntrada(f"no existe el archivo {ruta_archivo}") from None
        except json.JSONDecodeError as e:
            raise ErrorDeEntrada(f"{ruta_archivo.name} no es un JSON válido: {e}") from None
    if not isinstance(raw, dict):
        raise ErrorDeEntrada("el JSON debe ser un objeto con 'parametros', 'flujo' y 'etapas'")

    advertencias = []

    # ---- parámetros
    parametros = raw.get("parametros", {})
    if not isinstance(parametros, dict):
        raise ErrorDeEntrada("'parametros' debe ser un objeto")
    if "presupuesto_aceleracion_B" not in parametros:
        raise ErrorDeEntrada("falta parametros.presupuesto_aceleracion_B")
    B = _entero(parametros["presupuesto_aceleracion_B"], "parametros.presupuesto_aceleracion_B", 0)
    B_conjunto = parametros.get("presupuesto_conjunto_aceleracion_y_auditoria")
    if B_conjunto is not None:
        B_conjunto = _entero(B_conjunto, "parametros.presupuesto_conjunto_aceleracion_y_auditoria", 0)

    # ---- categorías de riesgo
    categorias, importancia = [], {}
    clave_cat, lista_cat = _lista(raw, ("categorias_riesgo",), "categorias_riesgo")
    if lista_cat is not None:
        for k, item in enumerate(lista_cat):
            if isinstance(item, dict):
                cid = item.get("id")
                if "importancia" in item:
                    importancia[cid] = item["importancia"]
            else:
                cid = item
            if not isinstance(cid, str) or not cid:
                raise ErrorDeEntrada(f"categorias_riesgo[{k}]: cada categoría necesita un 'id' de texto")
            if cid in categorias:
                raise ErrorDeEntrada(f"categorias_riesgo: el id '{cid}' está repetido")
            categorias.append(cid)

    # ---- etapas
    clave_etapas, etapas_raw = _lista(raw, CLAVES_ETAPAS, "etapas")
    if etapas_raw is None:
        raise ErrorDeEntrada("falta la lista 'etapas'")
    if not etapas_raw:
        raise ErrorDeEntrada("'etapas' está vacía: se necesita al menos una etapa")
    etapas, vistos = [], set()
    for k, e in enumerate(etapas_raw):
        ruta = f"{clave_etapas}[{k}]"
        if not isinstance(e, dict):
            raise ErrorDeEntrada(f"{ruta}: cada etapa debe ser un objeto")
        eid = e.get("id")
        if not isinstance(eid, str) or not eid:
            raise ErrorDeEntrada(f"{ruta}: falta el 'id' de texto de la etapa")
        if eid in vistos:
            raise ErrorDeEntrada(f"{ruta}: el id de etapa '{eid}' está repetido")
        vistos.add(eid)
        ruta = f"etapa {eid}"
        t = _entero(_campo(e, ("duracion_normal",), ruta), f"{ruta}.duracion_normal", 0)
        c = _entero(_campo(e, ("costo_aceleracion",), ruta), f"{ruta}.costo_aceleracion", 0)
        d = _entero(_campo(e, ("reduccion_tiempo_si_acelera",), ruta), f"{ruta}.reduccion_tiempo_si_acelera", 0)
        if d > t:
            raise ErrorDeEntrada(
                f"{ruta}: reduccion_tiempo_si_acelera ({d}) no puede superar duracion_normal ({t})"
            )
        completa = _ids_de_riesgos(
            e.get("riesgos_cubiertos_auditoria_completa", []), f"{ruta}.riesgos_cubiertos_auditoria_completa"
        )
        # variaciones_auditoria no se usa: la profesora confirmó que se usa la auditoría completa; se lee sin validar
        variaciones = []
        crudas = e.get("variaciones_auditoria", [])
        for v in crudas if isinstance(crudas, list) else []:
            if isinstance(v, dict) and "id" in v:
                costo = v.get("costo")
                riesgos = v.get("riesgos_cubiertos", [])
                variaciones.append(
                    (
                        str(v["id"]),
                        costo if isinstance(costo, int) and not isinstance(costo, bool) else None,
                        tuple(x for x in riesgos if isinstance(x, str)) if isinstance(riesgos, list) else (),
                    )
                )
        etapas.append(Etapa(eid, t, c, d, completa, tuple(variaciones)))

    # ---- universo de categorías
    if lista_cat is None:
        union = []
        for e in etapas:
            union.extend(e.completa)
        categorias = list(dict.fromkeys(union))
        advertencias.append("el archivo no trae 'categorias_riesgo'; se usó la unión de las listas de las etapas")
    conocidas = set(categorias)
    for e in etapas:
        for x in e.completa:
            if x not in conocidas:
                raise ErrorDeEntrada(
                    f"etapa {e.id}: la categoría '{x}' de riesgos_cubiertos_auditoria_completa "
                    "no existe en categorias_riesgo"
                )

    # ---- flujo
    clave_flujo, flujo_raw = _lista(raw, CLAVES_FLUJO, "flujo")
    if flujo_raw is None:
        if len(etapas) > 1:
            raise ErrorDeEntrada(
                "falta la lista 'flujo' (aristas origen -> destino); sin ella no se sabe el orden de las etapas"
            )
        flujo_raw = []
    ids = [e.id for e in etapas]
    aristas, vistas = [], set()
    for k, a in enumerate(flujo_raw):
        ruta = f"{clave_flujo}[{k}]"
        if isinstance(a, dict):
            origen_a = _campo(a, CLAVES_ORIGEN, ruta)
            destino_a = _campo(a, CLAVES_DESTINO, ruta)
        elif isinstance(a, (list, tuple)) and len(a) == 2:
            origen_a, destino_a = a
        else:
            raise ErrorDeEntrada(f"{ruta}: cada arista necesita 'origen' y 'destino'")
        for extremo, nombre_extremo in ((origen_a, "origen"), (destino_a, "destino")):
            if extremo not in ids:
                raise ErrorDeEntrada(f"{ruta}: el {nombre_extremo} '{extremo}' no es una etapa conocida")
        if origen_a == destino_a:
            raise ErrorDeEntrada(f"{ruta}: la etapa '{origen_a}' no puede ir hacia sí misma")
        if (origen_a, destino_a) in vistas:
            advertencias.append(f"arista repetida {origen_a}->{destino_a}; se cuenta una sola vez")
            continue
        vistas.add((origen_a, destino_a))
        aristas.append((origen_a, destino_a))

    # ---- coherencia con los parámetros declarados (solo advertencias)
    declaradas = parametros.get("numero_etapas")
    if declaradas is not None and declaradas != len(etapas):
        advertencias.append(f"parametros.numero_etapas dice {declaradas} pero hay {len(etapas)} etapas")
    declaradas = parametros.get("numero_categorias_riesgo")
    if declaradas is not None and declaradas != len(categorias):
        advertencias.append(
            f"parametros.numero_categorias_riesgo dice {declaradas} pero hay {len(categorias)} categorías"
        )

    orden, sucesores, predecesores = orden_topologico(ids, aristas)
    return Instancia(
        nombre=nombre,
        etapas=etapas,
        aristas=aristas,
        categorias=categorias,
        importancia=importancia,
        B=B,
        B_conjunto=B_conjunto,
        advertencias=advertencias,
        orden=orden,
        sucesores=sucesores,
        predecesores=predecesores,
    )
