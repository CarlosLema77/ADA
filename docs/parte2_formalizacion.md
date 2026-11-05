# Parte 2: cobertura mínima de auditoría

Borrador para el informe de la primera entrega (Persona B). Cubre las tareas 1-2, 2-2, 4-1c y 4-1e del tablero. La notación sigue el PDF del proyecto (sección 4.3).

---

## 1. Formalización

**Escenario.** Hay $n$ interacciones candidatas a auditar y $r$ categorías de riesgo (sesgo, fuga de datos personales, fallas de formato, etc.). Auditar una interacción revela todas las categorías de riesgo que contiene. Se quiere auditar el menor número posible de interacciones de modo que cada categoría quede revisada al menos una vez.

**Entrada.**
- Un entero $r \ge 1$ y el universo de categorías $U = \{1, 2, \dots, r\}$.
- Una familia $\mathcal{S} = (S_1, S_2, \dots, S_n)$, donde $S_j \subseteq U$ es el conjunto de categorías que cubre la interacción $j$.

**Salida.** Un conjunto de índices $J \subseteq \{1, \dots, n\}$ (las interacciones a auditar). De forma equivalente, un vector $y \in \{0,1\}^n$ con $y_j = 1 \iff j \in J$.

**Restricción.** Cada categoría queda cubierta:
$$\bigcup_{j \in J} S_j = U \qquad\Longleftrightarrow\qquad \forall k \in U:\ \sum_{j\,:\,k \in S_j} y_j \ge 1 .$$

**Objetivo.** Minimizar $|J| = \sum_{j=1}^{n} y_j$.

**Condición de factibilidad.** Existe al menos una solución si y solo si $\bigcup_{j=1}^{n} S_j = U$. Si se cumple, $J = \{1,\dots,n\}$ ya es una solución, así que el óptimo existe. Si no se cumple, alguna categoría $k$ no aparece en ningún $S_j$ y ninguna auditoría la cubre. El programa comprueba esta condición antes de correr cualquier algoritmo (`factibilidad.py`): marca en un arreglo de $r$ posiciones cada categoría que aparece y luego lista las no marcadas. Cuesta $O(r + s)$, con $s = \sum_j |S_j| \le n \cdot r$, es decir $O(n \cdot r)$.

**Tamaño de la entrada: $(n, r)$.** Una instancia son $n$ subconjuntos de un universo de $r$ elementos. Escrita como matriz de incidencia de $n \times r$ bits (fila $j$, columna $k$ vale 1 si $k \in S_j$), ocupa exactamente $n \cdot r$ bits. Escrita como listas, ocupa $\Theta(s \log r)$ bits con $s \le n \cdot r$. En ambas representaciones lo que crece cuando el problema se hace más grande son $n$ (más interacciones para escoger) y $r$ (más riesgos que cubrir). Además, todos los costos de los algoritmos se expresan en esas dos cantidades. A diferencia de la Parte 1, aquí no hay ningún número cuyo *valor* (y no su cantidad de bits) controle el tiempo: los números de la entrada son índices entre $1$ y $r$. Por eso las cotas polinomiales en $n$ y $r$ son realmente polinomiales en el tamaño de la entrada.

Se usa también $d = \max_j |S_j| \le r$ (el máximo de categorías que cubre una sola interacción), que aparece en la cota del voraz.

**Versión de decisión (AUD-DEC).** Dados $r$, $S_1,\dots,S_n$ y un entero $k \ge 0$: ¿existe $J$ con $|J| \le k$ y $\bigcup_{j\in J} S_j = U$?

---

## 2. NP-dureza: reducción desde Cobertura de Vértices

**Cobertura de Vértices (VC-DEC).** Dados un grafo no dirigido simple $G=(V,E)$ y un entero $k \ge 0$: ¿existe $C \subseteq V$ con $|C| \le k$ tal que toda arista tiene al menos un extremo en $C$? Es NP-completo (Karp, 1972).

**Dirección.** Se demuestra $\text{VC-DEC} \le_p \text{AUD-DEC}$: si AUD-DEC se resolviera en tiempo polinomial, VC-DEC también. La reducción va *desde* el problema conocido *hacia* el nuestro.

### 2.1 Construcción $f(G, k)$

Sean $V = \{v_1,\dots,v_{|V|}\}$ y las aristas numeradas $E = \{e_1, \dots, e_m\}$.

1. **Categorías = aristas:** $r = m$, $U = \{1,\dots,m\}$ (la categoría $\ell$ representa la arista $e_\ell$).
2. **Interacciones = vértices:** $n = |V|$ y, para cada vértice, $S_{v} = \{\ell : v \in e_\ell\}$ (las aristas que tocan a $v$).
3. **Mismo umbral:** $k$.

*Caso borde:* si $E = \emptyset$, la respuesta de VC es SÍ para cualquier $k$. $f$ devuelve una instancia fija que también es SÍ: $r=1$, $S_1=\{1\}$, $k=1$. Esto hace falta porque la entrada exige $r \ge 1$.

**Tiempo de la construcción.** Se crean $|V|$ listas vacías, en $O(|V|)$. Luego se recorre cada arista $e_\ell = \{u, v\}$ y se agrega $\ell$ a $S_u$ y a $S_v$, en $O(1)$ por arista, es decir $O(|E|)$. En total $O(|V| + |E|)$, polinomial.

*Observación:* la instancia construida siempre es factible, porque toda arista tiene un extremo, así que $\bigcup_v S_v = U$. Un vértice aislado produce $S_v = \emptyset$, que es válido.

### 2.2 Correctitud: $G$ tiene una cobertura de vértices de tamaño $\le k$ $\iff$ $f(G,k)$ tiene una auditoría de tamaño $\le k$

**($\Rightarrow$)** Sea $C$ una cobertura de vértices con $|C| \le k$. Tomamos $J = C$, así que $|J| \le k$. Para cualquier categoría $\ell \in U$, la arista $e_\ell$ tiene un extremo $v \in C$ (por ser $C$ cobertura de vértices). Por construcción, $\ell \in S_v$ con $v \in J$. Luego $\bigcup_{v \in J} S_v = U$.

**($\Leftarrow$)** Sea $J$ una auditoría con $|J| \le k$ que cubre $U$. Tomamos $C = J$. Para cualquier arista $e_\ell$, la categoría $\ell$ está cubierta, así que existe $v \in J$ con $\ell \in S_v$. Por construcción, $\ell \in S_v$ significa que $v \in e_\ell$. Luego $v$ es extremo de $e_\ell$ y está en $C$. Toda arista queda cubierta y $|C| \le k$.

Como la construcción es polinomial y preserva la respuesta, $\text{VC-DEC} \le_p \text{AUD-DEC}$, y AUD-DEC es NP-difícil.

### 2.3 AUD-DEC está en NP (por lo tanto, es NP-completo)

Certificado: el conjunto $J$. Verificación: comprobar $|J| \le k$ en $O(n)$ y marcar las categorías de $\bigcup_{j \in J} S_j$ en $O(n \cdot r)$. Es polinomial. Junto con 2.2, AUD-DEC es **NP-completo**. La versión de optimización (encontrar el $J$ mínimo) es **NP-difícil**: resolverla resuelve la de decisión comparando $|J^*|$ con $k$.

### 2.4 Ejemplo paso a paso (grafo de 5 vértices)

$V = \{a,b,c,d,e\}$, $E = \{e_1{=}ab,\ e_2{=}ac,\ e_3{=}bc,\ e_4{=}bd,\ e_5{=}ce,\ e_6{=}de\}$, $k = 3$.

| Vértice → interacción | Aristas que toca → $S_v$ |
|---|---|
| $a$ | $\{1, 2\}$ |
| $b$ | $\{1, 3, 4\}$ |
| $c$ | $\{2, 3, 5\}$ |
| $d$ | $\{4, 6\}$ |
| $e$ | $\{5, 6\}$ |

$C = \{b, c, d\}$ es una cobertura de vértices: $ab$ y $bc$ y $bd$ por $b$; $ac$ y $ce$ por $c$; $de$ por $d$. En la instancia de auditoría, $S_b \cup S_c \cup S_d = \{1,3,4\} \cup \{2,3,5\} \cup \{4,6\} = \{1,\dots,6\}$, también de tamaño 3. No hay cobertura de tamaño 2: cada vértice toca a lo sumo 3 aristas, así que dos vértices cubren 6 aristas solo si son $b$ y $c$, pero esos dos comparten $bc$ y suman 5. La fuerza bruta del programa confirma que el óptimo es 3 (caso `ejemplos/auditoria/03_reduccion_grafo_5_vertices.json`).

---

## 3. Algoritmo voraz y su función de eficiencia

**Idea.** Mientras falten categorías, elegir la interacción que cubre más categorías todavía no cubiertas.

**Desempate (fijo).** Si varias empatan, gana la que aparece primero en la entrada. Así la traza es reproducible: la misma entrada siempre produce la misma salida.

### 3.1 Pseudocódigo con conteo por línea

Sea $p$ el número de vueltas del ciclo principal (interacciones elegidas) y $s = \sum_j |S_j|$.

| Línea | Instrucción | Costo | Veces |
|---|---|---|---|
| L1 | `cubierta[1..r] ← falso` | $c_1$ | $r$ |
| L2 | `elegida[1..n] ← falso` | $c_2$ | $n$ |
| L3 | `faltan ← r` | $c_3$ | $1$ |
| L4 | `mientras faltan > 0` | $c_4$ | $p + 1$ |
| L5 | `mejor ← nulo; g* ← 0` | $c_5$ | $p$ |
| L6 | `para j ← 1..n` | $c_6$ | $p\,(n+1)$ |
| L7 | `si elegida[j]: continuar` | $c_7$ | $p\,n$ |
| L8 | `g ← 0` | $c_8$ | $\le p\,n$ |
| L9 | `para k en S_j` | $c_9$ | $\le p\,(s + n)$ |
| L10 | `si no cubierta[k]: g ← g + 1` | $c_{10}$ | $\le p\,s$ |
| L11 | `si g > g*: mejor ← j; g* ← g` | $c_{11}$ | $\le p\,n$ |
| L13 | `elegida[mejor] ← verdadero; agregar a J` | $c_{13}$ | $p$ |
| L14 | `para k en S_mejor: si no cubierta[k]: marcar; faltan ← faltan − 1` | $c_{14}$ | $\sum_{t=1}^{p} (\lvert S_{\text{mejor}_t}\rvert + 1) \le p\,(d + 1)$ |

*(L12, "si mejor es nulo: error", nunca se ejecuta con efecto porque la factibilidad se comprobó antes.)*

Sumando, con $\alpha = c_9 + c_{10}$, $\beta = c_6 + c_7 + c_8 + c_9 + c_{11}$ y $\gamma, \delta$ constantes que agrupan el resto:

$$T(n, r) \;\le\; \alpha\, p\, s \;+\; \beta\, p\, n \;+\; c_{14}\, p\,(d+1) \;+\; c_1 r + c_2 n + \gamma\, p + \delta .$$

**¿Cuánto vale $p$ como máximo?**
- **$p \le r$:** cada vuelta elige una interacción con $g^* \ge 1$, es decir, cubre al menos una categoría nueva. Eso se cumple porque, si quedan categorías sin cubrir y la instancia es factible, alguna interacción no elegida cubre alguna de ellas. Como solo hay $r$ categorías, hay a lo sumo $r$ vueltas.
- **$p \le n$:** cada vuelta elige una interacción distinta, porque una ya elegida se salta en L7 y además tendría ganancia 0.

Luego $p \le \min(n, r)$. Con $s \le n\,r$ y $d \le r$:

$$T(n, r) \le \alpha \min(n,r)\, n\, r + \beta \min(n,r)\, n + c_{14}\min(n,r)(r+1) + c_1 r + c_2 n + \gamma \min(n,r) + \delta .$$

El término dominante es $\min(n,r) \cdot n \cdot r$, así que

$$\boxed{T(n, r) = O\big(n \cdot r \cdot \min(n, r)\big) \subseteq O(n \cdot r^2)}$$

en el peor caso, más $O(n \cdot r)$ del chequeo de factibilidad, que queda absorbido. Coincide con el PDF (4.3). La cota $O(n\,r^2)$ del documento del proyecto también es correcta, aunque menos ajustada cuando $n < r$.

**Mejor caso:** una interacción cubre todo y queda primera en la búsqueda: $p = 1$ y $T = \Theta(n + s)$.

### 3.2 Cota de aproximación (citada)

**Teorema** (Johnson, 1974; Chvátal, 1979). Sea $J^*$ una cobertura óptima y $J_g$ la del voraz. Entonces
$$|J_g| \le H(d)\,|J^*|, \qquad H(d) = 1 + \tfrac12 + \dots + \tfrac1d,\quad d = \max_j |S_j| .$$
Como $d \le r$, también $|J_g| \le H_r\,|J^*|$, con $H_r \le \ln r + 1$.

*Idea de la prueba (Chvátal):* cuando el voraz elige una interacción que cubre $g$ categorías nuevas, reparte un "precio" de $1/g$ a cada una. La suma de todos los precios es exactamente $|J_g|$. Para cualquier conjunto $S_j$ del óptimo, sus categorías, ordenadas según cuándo se cubrieron, pagan a lo sumo $\tfrac{1}{|S_j|} + \tfrac{1}{|S_j|-1} + \dots + 1 = H(|S_j|) \le H(d)$, porque cuando faltaban $t$ categorías de $S_j$, el voraz eligió algo con ganancia $\ge t$. Sumando sobre las $|J^*|$ interacciones del óptimo, que cubren todo, se obtiene $|J_g| \le H(d)\,|J^*|$.

**Verificación empírica.** `tests/test_auditoria.py` genera 1500 instancias aleatorias con semilla fija ($n \le 10$, $r \le 12$), calcula el óptimo por fuerza bruta y comprueba en todas que $|J_g| \le H(d)\,|J^*|$ y que $|J_g| \le \min(n,r)$. El caso `07_brecha_logaritmica` muestra al voraz eligiendo 3 cuando el óptimo es 2.

---

## 4. Limitaciones

- El voraz no garantiza el óptimo: solo garantiza estar a un factor $H(d)$. Hay instancias en las que se aleja, como `02_voraz_no_optimo` y `07_brecha_logaritmica`.
- La fuerza bruta es exponencial ($2^n - 1$ subconjuntos en el peor caso) y por defecto solo se usa con $n \le 20$, para verificar.
- Los casos de `ejemplos/` son propios. Los de la profesora van en `casos/auditoria/` y se corren con el mismo comando.

## Referencias

- Karp, R. M. (1972). Reducibility among combinatorial problems. En *Complexity of Computer Computations*, 85–103. Plenum Press.
- Johnson, D. S. (1974). Approximation algorithms for combinatorial problems. *Journal of Computer and System Sciences*, 9(3), 256–278.
- Chvátal, V. (1979). A greedy heuristic for the set-covering problem. *Mathematics of Operations Research*, 4(3), 233–235.
