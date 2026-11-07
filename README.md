# ADA 2026-B · Grupo 3 (Ruta) · Primera entrega

Solución base de los dos problemas del proyecto, en Python, sin librerías externas.

- **Parte 1, aceleración.** Dado un flujo de etapas (duración `t_i`, costo de acelerar `c_i`, reducción `d_i`) y un presupuesto `B`, escoge las etapas a acelerar para minimizar la duración total.
  Si el flujo es una cadena usa programación dinámica (mochila 0/1, tiempo O(n·B)); si tiene rutas paralelas usa ramificación y acotamiento (exacto, exponencial en el peor caso).
- **Parte 2, auditoría.** Escoge el menor número de etapas que cubra todas las categorías de riesgo, con el voraz de mayor ganancia (O(n·r·min(n,r)), factor H(d) del óptimo).

Versión: `entrega1-1.1`. Informe, manual, código y resultados corresponden a esta misma versión.

## Cómo correrlo

Requiere Python 3 (probado con 3.13). Desde la carpeta del repositorio:

```bash
python ejecutar_casos.py                       # casos de la profesora (casos/)  ->  resultados/
python ejecutar_casos.py casos_propios --salida resultados_propios
python -m pytest -q                            # pruebas (necesita: pip install -r requirements.txt)
```

Para probar otros casos basta dejar los `.json` en `casos/` (mismo formato) y volver a correr el primer comando; no hay que editar el código.

Por cada caso se crea `resultados/caso_XX_<nombre>/` con la salida (`parte1_salida.json`, `parte2_salida.json`), el tiempo (`tiempos.json`), la traza (`parte1_traza.json`, `parte2_traza.json`, `traza_legible.txt`) y la verificación independiente (`verificacion.json`). `resultados/resumen.md` resume todos los casos.

Resultado esperado para `casos/entrada_G3_mochila_20_nodos.json`:

| | |
|---|---|
| Parte 1 | acelera E02, E03, E04, E06, E08, E12 · costo 72 de 72 · duración 501 → 446 (ahorro 55) |
| Parte 2 | cobertura de 4: E01, E16, E06, E03 (óptima) |

Los tiempos cambian de una máquina a otra; lo demás es determinista.

## Contenido

| Carpeta o archivo | Qué es |
|---|---|
| `ejecutar_casos.py` | programa principal |
| `src/ada/` | lector de casos, algoritmos de las dos partes, verificadores, medición |
| `tests/` | pruebas automáticas (fuerza bruta, casos borde, errores de entrada) |
| `casos/` | casos de la profesora, sin modificar |
| `casos_propios/`, `generar_casos.py` | casos propios (flujos con rutas paralelas, cadenas grandes, infactible) y su generador |
| `resultados/`, `resultados_propios/` | salida, tiempo y traza por caso |
| `docs/` | `Informe_Tecnico.pdf`, `Manual_Tecnico.pdf` y sus fuentes `.tex` |

Más detalle de formatos, algoritmos y limitaciones en `docs/Manual_Tecnico.pdf`.

## Candidatos a auditar

Confirmado por la profesora: cada etapa es un candidato a auditar y cubre su propia lista `riesgos_cubiertos_auditoria_completa` (se usa la auditoría completa). El campo `variaciones_auditoria` del archivo se lee pero no se usa.
