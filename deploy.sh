# 1. Definir rutas e entrar no directorio local do blog
REPO_DIR="/Users/anxo/Documents/antigravity/sopqblog"
POST_DIR="$REPO_DIR/posts/2026-11-08-optimizacion-avanzada-procesos-quimicos"

cd "$REPO_DIR" || { echo "Erro: Non se puido acceder a $REPO_DIR"; exit 1; }

# 2. Crear o cartafol para a nova entrada
mkdir -p "$POST_DIR"

# 3. Escribir o ficheiro index.qmd completo co estándar do blog
cat << 'EOF' > "$POST_DIR/index.qmd"
---
title: "Optimización Numérica Avanzada en Procesos Químicos: Da Teoría á Práctica con Python, Aspen HYSYS e DWSIM"
subtitle: "Tema 7: Métodos multivariables, Programación Cuadrática Sucesiva (SQP), Lagrangiana Aumentada (ALM) e Enxame de Partículas (PSO)"
author: "Ángel Sánchez (Anxo)"
date: "2026-11-08"
categories: [SOPQ, Optimización, Python, HYSYS, DWSIM, Enxeñaría Química]
image: "pfd_mtbe_plant.jpg"
toc: true
number-sections: true
highlight-style: github
code-fold: show
code-tools: true
---

::: {.callout-note}
## Material Didáctico Interactivo
- **Código executable en Google Colab:** [Abrir en Colab](https://colab.research.google.com/)
- **Caderno de fontes en Gemini Notebook:** [SOPQ - Tema 7](https://gemini.google.com/notebook/dabbf057-563f-4920-a080-63d33bcec7bf)
- **Repositorio do blog:** [GitHub sopqblog](https://github.com/anxosanchez/sopqblog)
:::

# Introdución e Contexto

No marco da materia **Simulación e Optimización de Procesos Químicos (SOPQ)** da Universidade de Vigo, o deseño e operación de plantas industriais actuais require transcender a resolución heurística mediante algoritmos numéricos deterministas e estocásticos rigorosos.

Este artigo desenvolve a formulación matemática, a posta en marcha e a comparativa computacional en **Python (`scipy.optimize`)**, **Aspen HYSYS** e **DWSIM** dos catro paradigmas centrais do Tema 7 da guía docente:

1. **Optimización Multivariable sen Restricións (BFGS / Cuasi-Newton):** Deseño dun reactor CSTR non isotérmico.
2. **Programación Cuadrática Sucesiva (SQP):** Minimización de utilidades nunha columna desbutanizadora con restricións de calidade.
3. **Método da Lagrangiana Aumentada (ALM):** Reconciliación de balances con reciclos complexos sen diverxencia matricial.
4. **Algoritmos Estocásticos e Heurísticos (PSO / Evolución Diferencial):** Resolución global de redes térmicas non convexas.

---

# Casos Prácticos de Aula

## Caso 1: Reactor CSTR Non Isotérmico (BFGS)

Considérase a síntese $A \rightarrow B$ cunha constante de Arrhenius $k(T) = k_0 \exp(-E_a / RT)$. A función de custo total anualizado pondera capital, intercambio térmico e reactivo sen converter:

$$\min_{T, V} f_1(T, V) = 1500 \cdot V^{0.6} + 250 \cdot |Q|^{0.7} + 1.0 \times 10^5 \cdot C_A$$

```{python}
#| label: fig-cstr-opt
#| fig-cap: "Superficie de custo e converxencia BFGS para o reactor CSTR"
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

k0, Ea, R_gas = 1.5e7, 65000.0, 8.314
CA0, v0, DeltaH = 2.0, 10.0, -50000.0
rho, Cp, Tin = 1000.0, 4.184, 298.15
T_ref, V_ref = 300.0, 50.0

def cstr_obj_scaled(z):
    T, V = z[0] * T_ref, z[1] * V_ref
    if T <= 0 or V <= 0: return 1e12
    k = k0 * np.exp(-Ea / (R_gas * T))
    tau = V / v0
    X = (k * tau) / (1.0 + k * tau)
    CA = CA0 * (1.0 - X)
    Q = v0 * rho * Cp * (T - Tin) + (v0 * CA0 * X) * DeltaH
    return 1500.0 * (V**0.6) + 250.0 * (np.abs(Q)**0.7) + 1.0e5 * CA

res_bfgs = minimize(cstr_obj_scaled, [330.0/T_ref, 50.0/V_ref], method='BFGS')
T_opt, V_opt = res_bfgs.x[0] * T_ref, res_bfgs.x[1] * V_ref

T_vals = np.linspace(310, 380, 50)
V_vals = np.linspace(20, 120, 50)
T_grid, V_grid = np.meshgrid(T_vals, V_vals)
Z_grid = np.zeros_like(T_grid)

for i in range(T_grid.shape[0]):
    for j in range(T_grid.shape[1]):
        Z_grid[i, j] = cstr_obj_scaled([T_grid[i, j]/T_ref, V_grid[i, j]/V_ref])

plt.figure(figsize=(7, 5))
cp = plt.contourf(T_grid, V_grid, Z_grid, levels=30, cmap='viridis')
plt.colorbar(cp, label='Custo Total ($)')
plt.plot(T_opt, V_opt, 'r*', markersize=14, label=f'Óptimo ({T_opt:.1f} K, {V_opt:.1f} L)')
plt.xlabel('Temperatura (K)')
plt.ylabel('Volume (L)')
plt.legend()
plt.tight_layout()
plt.show()
