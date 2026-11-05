| caso | n | r | d | voraz | optimo | razon | H_d | tiempo_mediana_ms | estado | seleccion |
|---|---|---|---|---|---|---|---|---|---|---|
| 01_ejemplo_a_mano | 5 | 4 | 2 | 2 | 2 | 1.000 | 1.500 | 0.0031 | OK | I1 I3 |
| 02_voraz_no_optimo | 3 | 6 | 4 | 3 | 2 | 1.500 | 2.083 | 0.0030 | OK | I3 I1 I2 |
| 03_reduccion_grafo_5_vertices | 5 | 6 | 3 | 3 | 3 | 1.000 | 1.833 | 0.0032 | OK | b c d |
| 04_una_cubre_todo | 3 | 5 | 5 | 1 | 1 | 1.000 | 2.283 | 0.0021 | OK | I2 |
| 05_r_igual_1 | 3 | 1 | 1 | 1 | 1 | 1.000 | 1.000 | 0.0015 | OK | I2 |
| 06_no_factible | 3 | 5 | 2 |  |  |  |  |  | ERROR: Instancia no factible: ninguna interacción cubre las categorías [4, 5]. No existe auditoría que cubra todo. |  |
| 07_brecha_logaritmica | 5 | 14 | 8 | 3 | 2 | 1.500 | 2.718 | 0.0045 | OK | C3 C2 C1 |
