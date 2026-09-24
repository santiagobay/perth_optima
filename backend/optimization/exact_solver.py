"""
exact_solver.py
-----------------
Capa de optimización (parte 2): modelo exacto de asignación con
eliminación de subtours (formulación de Miller, Tucker y Zemlin, 1960).

Formulación matemática implementada
------------------------------------
Conjuntos:
    N = {1, ..., n}            viviendas del subdistrito

Parámetros:
    c_ij = distancia geodésica entre la vivienda i y la vivienda j
           (matriz construida en distances.py)

Variables de decisión:
    x_ij ∈ {0, 1}   para todo i, j ∈ N, i ≠ j
        x_ij = 1 si el recorrido va directamente de la vivienda i a la j
    u_i ∈ ℝ         para todo i ∈ N \\ {1}   (variables auxiliares MTZ,
                     representan la posición de i en el orden de visita)

Función objetivo:
    min  Σ_i Σ_j c_ij * x_ij                     (i ≠ j)

Restricciones de asignación:
    Σ_j x_ij = 1     para todo i ∈ N   (una sola salida por vivienda)
    Σ_i x_ij = 1     para todo j ∈ N   (una sola entrada por vivienda)

Restricciones de eliminación de subtours (Miller, Tucker y Zemlin, 1960):
    u_i - u_j + n * x_ij ≤ n - 1     para todo i, j ∈ N \\ {1}, i ≠ j
    2 ≤ u_i ≤ n                      para todo i ∈ N \\ {1}
    u_1 = 1

Esta es exactamente la formulación que se cita en la sección 3.3 del
documento de la Fase 3: la desigualdad u_i - u_j + n*x_ij ≤ n - 1 impide
que, en la solución óptima, existan dos o más ciclos desconectados entre
sí, obligando a que la solución sea un único recorrido cerrado que visite
las n viviendas.
"""

from __future__ import annotations
import numpy as np
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError


def solve_exact_tsp(distance_matrix: np.ndarray, solver_name: str = "cbc") -> dict:
    """Resuelve el modelo de asignación con restricciones MTZ.

    Pensado para subconjuntos pequeños (10 a 15 viviendas), tal como se
    justificó en la Alternativa 1 de la etapa de contextualización, dado
    el crecimiento factorial del número de rutas posibles.
    """
    n = distance_matrix.shape[0]
    nodes = list(range(n))

    model = pyo.ConcreteModel(name="TSP_asignacion_MTZ")
    model.N = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])

    model.c = pyo.Param(model.arcs, initialize={(i, j): distance_matrix[i][j] for (i, j) in model.arcs})
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(nodes, bounds=(0, n), within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(m.c[i, j] * m.x[i, j] for (i, j) in m.arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_degree_rule(m, i):
        return sum(m.x[i, j] for j in m.N if j != i) == 1
    model.out_degree = pyo.Constraint(model.N, rule=out_degree_rule)

    def in_degree_rule(m, j):
        return sum(m.x[i, j] for i in m.N if i != j) == 1
    model.in_degree = pyo.Constraint(model.N, rule=in_degree_rule)

    def mtz_rule(m, i, j):
        if i == 0 or j == 0 or i == j:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1
    model.mtz = pyo.Constraint(model.N, model.N, rule=mtz_rule)

    model.u[0].fix(1)
    for i in nodes[1:]:
        model.u[i].setlb(2)
        model.u[i].setub(n)

    solver = pyo.SolverFactory(solver_name)
    try:
        result = solver.solve(model, tee=False)
    except ApplicationError as exc:
        raise RuntimeError(
            "No se encontró el ejecutable CBC del solver exacto. Instálalo en tu sistema "
            "(por ejemplo, en Windows con 'winget install coin-or.cbc' o en Linux con "
            "'sudo apt-get install coinor-cbc') para usar el método exacto."
        ) from exc

    status = str(result.solver.termination_condition)

    route = _extract_route(model, nodes)
    total_distance = pyo.value(model.obj)

    return {
        "status": status,
        "route_index": route,
        "total_distance_km": round(total_distance, 3),
        "n_houses": n,
    }


def _extract_route(model, nodes: list[int]) -> list[int]:
    """Reconstruye la secuencia de visita a partir de las variables x_ij
    activas en la solución óptima, comenzando en la vivienda 0."""
    successor = {}
    for (i, j) in model.arcs:
        if pyo.value(model.x[i, j]) is not None and pyo.value(model.x[i, j]) > 0.5:
            successor[i] = j

    route = [0]
    current = 0
    for _ in range(len(nodes) - 1):
        current = successor[current]
        route.append(current)
    route.append(0)  # regreso al punto de partida
    return route
