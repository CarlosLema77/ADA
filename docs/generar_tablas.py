#!/usr/bin/env python3
"""Lee resultados/ y resultados_propios/ y escribe docs/tablas_resultados.tex, que el informe incluye.

Así los números del informe salen de los archivos de resultados y no se copian a mano.
Uso (desde la raíz del repositorio):  python docs/generar_tablas.py
"""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def tex(texto):
    return str(texto).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("&", "\\&").replace("%", "\\%")


def num(x, decimales=3):
    if isinstance(x, float):
        return f"{x:.{decimales}f}".replace(".", "{,}")
    return str(x)


def lista(xs):
    return ", ".join(xs)


def main():
    caso = next((RAIZ / "resultados").glob("caso_01_*"))
    p1 = cargar(caso / "parte1_salida.json")
    t1 = cargar(caso / "parte1_traza.json")
    p2 = cargar(caso / "parte2_salida.json")
    t2 = cargar(caso / "parte2_traza.json")
    tiempos = cargar(caso / "tiempos.json")
    ver = cargar(caso / "verificacion.json")
    n_rep = tiempos["parte1"]["repeticiones"]
    d = p2["d_max_categorias_por_candidato"]
    H = sum(1 / i for i in range(1, d + 1))
    optimo2 = ver["parte2"]["chequeos"]["optimo_por_enumeracion"]

    out = []
    out.append("% Archivo generado por docs/generar_tablas.py: no editar a mano.")
    out.append(f"\\newcommand{{\\VersionEntrega}}{{{tex(p1['version'])}}}")
    out.append(f"\\newcommand{{\\VersionPython}}{{{tex(p1['python'])}}}")
    out.append(f"\\newcommand{{\\NombreCasoProfe}}{{\\texttt{{{tex(p1['archivo'])}}}}}")

    # ---------------------------------------------------------------- resumen del caso de la profesora
    filas = [
        ("\\multicolumn{2}{@{}l}{\\textbf{Parte 1: aceleración}}", None),
        ("Método", {"programacion_dinamica_cadena": "programación dinámica (cadena)", "ramificacion_y_acotamiento": "ramificación y acotamiento"}[p1["metodo"]]),
        ("Etapas / presupuesto $B$", f"{len(p1['x'])} / {p1['presupuesto_B']}"),
        ("Etapas aceleradas", lista(p1["etapas_aceleradas"])),
        ("Costo usado", f"{p1['costo_usado']} de {p1['presupuesto_B']}"),
        ("Duración", f"{p1['duracion_sin_acelerar']} $\\to$ {p1['duracion_final']}"),
        ("Ahorro", p1["ahorro"]),
        ("Óptimo confirmado por enumeración de los $2^{20}$ subconjuntos", "sí" if ver["parte1"]["chequeos"].get("es_optima") else "no"),
        (f"Tiempo (mediana de {n_rep} repeticiones)", f"{num(tiempos['parte1']['mediana_ms'], 4)} ms"),
        ("\\multicolumn{2}{@{}l}{\\textbf{Parte 2: auditoría}}", None),
        ("Candidatos", f"{p2['n_candidatos']} etapas (una por etapa del flujo), $r={p2['r_categorias']}$ categorías"),
        ("Interacciones elegidas (en orden)", lista(p2["interacciones_elegidas"])),
        ("Tamaño de la cobertura", f"{p2['tamano']}"),
        ("Óptimo por enumeración", f"{optimo2}"),
        (f"Cota $H(d)\\cdot |J^*|$ con $d={d}$", f"{num(H * optimo2 if isinstance(optimo2, int) else float('nan'), 2)}"),
        (f"Tiempo (mediana de {n_rep} repeticiones)", f"{num(tiempos['parte2']['mediana_ms'], 4)} ms"),
    ]
    cuerpo = []
    for etiqueta, valor in filas:
        if valor is None:
            previo = "" if not cuerpo else "\\midrule\n"
            cuerpo.append(f"{previo}{etiqueta} \\\\\n\\midrule")
        else:
            cuerpo.append(f"{etiqueta} & {valor} \\\\")
    out.append("\\newcommand{\\TablaProfe}{%\n\\begin{tabular}{@{}p{7.2cm}p{7.6cm}@{}}\n\\toprule\n"
               + "\n".join(cuerpo)
               + "\n\\bottomrule\n\\end{tabular}}")

    # ---------------------------------------------------------------- traza del DP (reconstrucción)
    filas = []
    for dec in reversed(t1["decisiones_reconstruccion"]):
        filas.append(
            f"{dec['etapa']} & {dec['presupuesto_antes']} & {dec['dp_i_b']} & "
            f"{'acelerar' if dec['acelerar'] else 'no'} & {dec['costo']} & {dec['ahorro']} & {dec['presupuesto_despues']} \\\\"
        )
    out.append("\\newcommand{\\TablaTrazaDP}{%\n\\begin{tabular}{@{}lrrlrrr@{}}\n\\toprule\n"
               "Etapa & $b$ antes & $DP[i][b]$ & Decisión & Costo & Ahorro & $b$ después \\\\\n\\midrule\n"
               + "\n".join(filas) + "\n\\bottomrule\n\\end{tabular}}")

    # ---------------------------------------------------------------- traza del voraz
    filas = []
    for v in t2["vueltas"]:
        filas.append(
            f"{v['vuelta']} & {v['elegida']} & {v['ganancia']} & {lista(v['categorias_nuevas'])} & "
            f"{v['cubiertas_acumuladas']} & {v['faltan']} \\\\"
        )
    out.append("\\newcommand{\\TablaTrazaVoraz}{%\n\\begin{tabular}{@{}clrlrr@{}}\n\\toprule\n"
               "Vuelta & Elegida & Ganancia $g^*$ & Categorías nuevas & Cubiertas & Faltan \\\\\n\\midrule\n"
               + "\n".join(filas) + "\n\\bottomrule\n\\end{tabular}}")

    # ---------------------------------------------------------------- casos propios
    resumen = cargar(RAIZ / "resultados_propios" / "resumen.json")["casos"]
    filas = []
    for f in resumen:
        nombre = f["caso"].replace("propio_", "")
        traza = cargar(RAIZ / "resultados_propios" / f["carpeta"] / "parte1_traza.json")
        nodos = traza.get("nodos_explorados", "--")
        metodo = "DP" if f["metodo_parte1"].startswith("programacion") else "B\\&B"
        cob = f["tamano_cobertura"] if f["factible_parte2"] else "infactible"
        t2ms = "--" if f["tiempo_parte2_ms"] is None else num(f["tiempo_parte2_ms"], 3)
        ok = "sí" if f["verifica_parte1"] and f["verifica_parte2"] else "NO"
        filas.append(
            f"\\texttt{{{tex(nombre)}}} & {f['n_etapas']} & {f['aristas']} & {f['B']} & {metodo} & {nodos} & "
            f"{f['duracion_sin_acelerar']}$\\to${f['duracion_final']} & {num(f['tiempo_parte1_ms'], 3)} & {cob} & {t2ms} & {ok} \\\\"
        )
    out.append("\\newcommand{\\TablaPropios}{%\n\\begin{tabular}{@{}lrrrlrrrrrr@{}}\n\\toprule\n"
               "Caso & $n$ & Aristas & $B$ & P1 & Nodos & Duración & ms P1 & $|J|$ & ms P2 & Verif. \\\\\n\\midrule\n"
               + "\n".join(filas) + "\n\\bottomrule\n\\end{tabular}}")

    # ---------------------------------------------------------------- escala del DP: tiempo vs n*B
    puntos = []
    puntos.append(("caso de la profesora", len(p1["x"]), p1["presupuesto_B"], tiempos["parte1"]["mediana_ms"]))
    for f in resumen:
        if f["metodo_parte1"].startswith("programacion") and f["n_etapas"] * f["B"] >= 1000:
            puntos.append((f["caso"].replace("propio_", ""), f["n_etapas"], f["B"], f["tiempo_parte1_ms"]))
    filas = []
    for nombre, n, B, ms in puntos:
        celdas = (n + 1) * (B + 1)
        filas.append(f"\\texttt{{{tex(nombre)}}} & {n} & {B} & {celdas:,} & {num(ms, 3)} & {num(ms * 1e6 / celdas, 1)} \\\\".replace(",", "\\,"))
    out.append("\\newcommand{\\TablaEscalaDP}{%\n\\begin{tabular}{@{}lrrrrr@{}}\n\\toprule\n"
               "Caso & $n$ & $B$ & Celdas $(n+1)(B+1)$ & ms & ns por celda \\\\\n\\midrule\n"
               + "\n".join(filas) + "\n\\bottomrule\n\\end{tabular}}")

    destino = RAIZ / "docs" / "tablas_resultados.tex"
    destino.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"escrito {destino}")


if __name__ == "__main__":
    main()
