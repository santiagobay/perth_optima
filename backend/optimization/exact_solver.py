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

SOLVER_MISSING_MESSAGE = (
    "No se encontró el ejecutable CBC del solver exacto. Instálalo en tu sistema "
    "(por ejemplo, en Windows con 'winget install coin-or.cbc' o en Linux con "
    "'sudo apt-get install coinor-cbc') para usar el método exacto."
)

# Condiciones de término con las que sí hay una solución cargada en el modelo.
_ACCEPTABLE_TERMINATIONS = {
    pyo.TerminationCondition.optimal,
    pyo.TerminationCondition.locallyOptimal,
    pyo.TerminationCondition.globallyOptimal,
    pyo.TerminationCondition.feasible,
    pyo.TerminationCondition.maxTimeLimit,
}

DEFAULT_TIME_LIMIT_SECONDS = 60


def solver_is_available(solver_name: str = "cbc") -> bool:
    """Indica si el solver externo está instalado y se puede invocar."""
    try:
        return bool(pyo.SolverFactory(solver_name).available(exception_flag=False))
    except Exception:
        return False


def solve_exact_tsp(
    distance_matrix: np.ndarray,
    solver_name: str = "cbc",
    time_limit_seconds: float | None = DEFAULT_TIME_LIMIT_SECONDS,
) -> dict:
    """Resuelve el modelo de asignación con restricciones MTZ.

    Pensado para subconjuntos pequeños (10 a 15 viviendas), tal como se
    justificó en la Alternativa 1 de la etapa de contextualización, dado
    el crecimiento factorial del número de rutas posibles.

    Lanza RuntimeError (no una excepción interna de Pyomo) cuando el solver
    no está instalado o cuando no devuelve una solución utilizable, para que
    la capa HTTP pueda traducirlo a un mensaje claro.
    """
    n = int(distance_matrix.shape[0])
    if n == 0:
        raise ValueError("La matriz de distancias está vacía.")
    if n == 1:
        # El modelo MTZ es infactible por construcción con un solo nodo
        # (Σ_j x_ij = 1 no tiene ningún arco disponible).
        return {
            "status": "trivial",
            "route_index": [0, 0],
            "total_distance_km": 0.0,
            "n_houses": n,
        }

    nodes = list(range(n))

    model = pyo.ConcreteModel(name="TSP_asignacion_MTZ")
    model.N = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])

    model.c = pyo.Param(
        model.arcs,
        initialize={(i, j): float(distance_matrix[i][j]) for (i, j) in model.arcs},
    )
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

    try:
        solver = pyo.SolverFactory(solver_name)
        if not solver.available(exception_flag=False):
            raise RuntimeError(SOLVER_MISSING_MESSAGE)
    except ApplicationError as exc:
        raise RuntimeError(SOLVER_MISSING_MESSAGE) from exc

    if time_limit_seconds:
        # Evita que una petición HTTP quede bloqueada indefinidamente si se
        # lanza el modelo exacto sobre una instancia demasiado grande.
        try:
            solver.options["sec"] = float(time_limit_seconds)
        except Exception:
            pass

    try:
        result = solver.solve(model, tee=False)
    except ApplicationError as exc:
        raise RuntimeError(SOLVER_MISSING_MESSAGE) from exc

    termination = result.solver.termination_condition
    status = str(termination)
    if termination not in _ACCEPTABLE_TERMINATIONS:
        raise RuntimeError(
            f"El modelo exacto no produjo una solución utilizable (estado del solver: {status})."
        )

    route = _extract_route(model, nodes)
    total_distance = pyo.value(model.obj)

    return {
        "status": status,
        "route_index": route,
        "total_distance_km": round(float(total_distance), 3),
        "n_houses": n,
    }


def _extract_route(model, nodes: list[int]) -> list[int]:
    """Reconstruye la secuencia de visita a partir de las variables x_ij
    activas en la solución óptima, comenzando en la vivienda 0.

    Valida que el resultado sea un único ciclo hamiltoniano. Sin esta
    validación, una solución ausente o con subtours provocaba un KeyError
    opaco (o una ruta silenciosamente incompleta) en lugar de un error
    explicable.
    """
    successor: dict[int, int] = {}
    for (i, j) in model.arcs:
        value = pyo.value(model.x[i, j], exception=False)
        if value is not None and value > 0.5:
            successor[i] = j

    if not successor:
        raise RuntimeError(
            "El solver no devolvió valores para las variables de decisión del modelo exacto."
        )

    route = [0]
    visited = {0}
    current = 0
    for _ in range(len(nodes) - 1):
        nxt = successor.get(current)
        if nxt is None or nxt in visited:
            raise RuntimeError(
                "La solución del modelo exacto no forma un único ciclo que visite todas las viviendas."
            )
        route.append(nxt)
        visited.add(nxt)
        current = nxt

    if successor.get(current) != 0:
        raise RuntimeError(
            "La solución del modelo exacto no regresa a la vivienda de partida."
        )

    route.append(0)  # regreso al punto de partida
    return route
