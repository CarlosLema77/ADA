# Formatos de entrada, salida y traza

> El lector acepta dos formatos y detecta cuál es: el **de la profesora** (`casos/profesora/`) y uno **propio** más corto para los ejemplos (`ejemplos/`).

## Formato de la profesora (ej. `entrada_G3_mochila_20_nodos.json`)

Un solo archivo trae los datos de todo el proyecto. Para la Parte 2 base se usa así:

| Del archivo | En el modelo |
|---|---|
| `categorias_riesgo` (R01…R12) | categorías 1..r en ese orden; en la traza se muestran con su id original |
| cada elemento de `etapas` | una interacción candidata (id = id de la etapa) |
| `riesgos_cubiertos_auditoria_completa` | el subconjunto S_j que cubre |
| `parametros.numero_categorias_riesgo` | se valida contra el número de categorías |

Campos que el problema base no usa y quedan para después: `importancia` de cada categoría, `variaciones_auditoria` (parcial/completa, con costo), `presupuesto_conjunto_aceleracion_y_auditoria` y `flujo` (las aristas; en este caso es una cadena E01→…→E20). La Parte 1 usa `duracion_normal`, `costo_aceleracion`, `reduccion_tiempo_si_acelera` y `parametros.presupuesto_aceleracion_B`.

## Formato propio (ejemplos)

```json
{
  "nombre": "01_ejemplo_a_mano",
  "descripcion": "texto libre, opcional",
  "r": 4,
  "interacciones": [
    {"id": "I1", "categorias": [1, 2]},
    {"id": "I2", "categorias": [2, 3], "costo": 5}
  ]
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `r` | entero | ≥ 1; las categorías son 1..r |
| `interacciones` | lista | no vacía; su orden define el desempate |
| `id` | texto | único; si falta, se usa `I<posición>` |
| `categorias` | lista de enteros | cada uno en [1, r], sin repetir; puede ser vacía |
| `costo` | número | opcional, > 0; solo lo usa la variante ponderada (segunda entrega) |

Si falta alguna regla, el programa se detiene con un mensaje que dice qué interacción y qué campo falló. Si la instancia no es factible, informa qué categorías no cubre nadie.

## Parte 2: resultados por caso (`resultados/<carpeta>/<caso>/`)

**`salida.json`**
```json
{
  "caso": "02_voraz_no_optimo",
  "instancia": {"n": 3, "r": 6, "d": 4, "s": 10},
  "voraz": {"seleccion": ["I3", "I1", "I2"], "tamano": 3, "pasos": 3},
  "tiempo_voraz": {"mediana_s": 4.4e-06, "min_s": 4.1e-06, "max_s": 6.0e-06, "repeticiones": 5},
  "verificacion": {"cubre_las_r_categorias": true},
  "cota": {"H_d": 2.083, "explicacion": "|voraz| ≤ H(d)·OPT (Johnson 1974; Chvátal 1979)"},
  "optimo_fuerza_bruta": {"tamano": 2, "seleccion": ["I1", "I2"], "subconjuntos_probados": 4},
  "comparacion": {"razon_voraz_sobre_optimo": 1.5, "cumple_cota": true}
}
```
El tiempo se mide sin generar traza, con una corrida de calentamiento y luego `--repeticiones` corridas; se reporta la mediana. `optimo_fuerza_bruta` es `null` cuando n supera `--max-n-fuerza-bruta`.

**`traza.json`**: un objeto por paso del voraz.

| Campo | Significado |
|---|---|
| `paso` | número de elección (1, 2, …) |
| `elegida` | id de la interacción elegida |
| `ganancia` | cuántas categorías nuevas cubrió |
| `categorias_nuevas` | cuáles |
| `cubiertas_acumuladas` | total cubierto tras el paso |
| `faltantes` | categorías aún sin cubrir |
| `empatadas` | otras interacciones con la misma ganancia que perdieron por el desempate |

**`resumen.csv` / `resumen.md`** (en la carpeta de salida): una fila por caso con n, r, d, tamaño voraz, óptimo, razón, H(d), tiempo (mediana, ms), estado y selección.

## Parte 1: contrato con A para el verificador de aceleración

Caso (entrada):
```json
{"nombre": "ejemplo_n4", "B": 7,
 "etapas": [{"id": "E1", "t": 10, "c": 3, "d": 4}, {"id": "E2", "t": 8, "c": 4, "d": 5}]}
```
Salida que debe producir el programa de A (los campos extra se ignoran):
```json
{"etapas_aceleradas": ["E1", "E2"], "costo_total": 7, "reduccion_total": 9, "duracion_total": 20}
```
`python -m src.verificadores.aceleracion CASO.json SALIDA.json` comprueba que no haya etapas repetidas ni inexistentes, que el costo sea ≤ B, que los totales coincidan y, si n ≤ 20, que la reducción sea la óptima (fuerza bruta independiente del DP).
