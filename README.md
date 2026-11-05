# Proyecto Ruta: ADA 2026-B (Grupo 3)

Ruta crítica con aceleración bajo presupuesto (Parte 1, Persona A) y cobertura mínima de auditoría (Parte 2, Persona B).

## Requisitos

- Python 3.11 o superior
- `pip install -r requirements.txt` (solo `pytest`; los algoritmos usan la biblioteca estándar)

## Estructura

```
src/
  parte1_aceleracion/     (Persona A: DP de la mochila)
  parte2_auditoria/       modelo, lector con validación, factibilidad, voraz, fuerza bruta, runner
  comun/medicion.py       tiempo por caso (mediana de varias repeticiones)
  verificadores/          verificador independiente de la Parte 1
casos/profesora/          casos de la profesora, sin modificar (solo lectura)
ejemplos/                 casos propios: ejemplo a mano, bordes, reducción, peor caso
resultados/               salida, traza y tiempo por caso + resumen
tests/                    pytest
docs/                     formalización, reducción y complejidad; formatos de E/S
```

## Uso

Todo se ejecuta desde la carpeta raíz del proyecto.

```bash
# Parte 2 sobre los casos de la profesora (se leen tal como vienen)
python -m src.parte2_auditoria.correr --casos casos/profesora --salida resultados/profesora

# Parte 2 sobre los ejemplos propios
python -m src.parte2_auditoria.correr --casos ejemplos/auditoria --salida resultados/ejemplos_auditoria

# Un solo caso
python -m src.parte2_auditoria.correr --casos ejemplos/auditoria/01_ejemplo_a_mano.json --salida resultados/uno

# Verificar una salida de la Parte 1 (acepta formato propio o el de la profesora)
python -m src.verificadores.aceleracion ejemplos/aceleracion/ejemplo_n4.json ejemplos/aceleracion/ejemplo_n4_salida_correcta.json

# Pruebas
python -m pytest -q
```

Opciones del runner: `--repeticiones N` (por defecto 5) y `--max-n-fuerza-bruta N` (por defecto 20; compara contra el óptimo solo si n ≤ N).

Formatos de entrada, salida y traza: [docs/formatos.md](docs/formatos.md).
