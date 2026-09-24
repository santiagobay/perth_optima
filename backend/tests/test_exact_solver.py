import unittest

import numpy as np

from optimization.exact_solver import (
    SOLVER_MISSING_MESSAGE,
    solve_exact_tsp,
    solver_is_available,
)

CBC_AVAILABLE = solver_is_available("cbc")

# Matriz de un cuadrado: el óptimo es recorrer el perímetro (4 * 10 = 40),
# nunca las diagonales.
SQUARE = np.array([
    [0.0, 10.0, 14.0, 10.0],
    [10.0, 0.0, 10.0, 14.0],
    [14.0, 10.0, 0.0, 10.0],
    [10.0, 14.0, 10.0, 0.0],
])


class TestExactSolverWithoutCbc(unittest.TestCase):
    @unittest.skipIf(CBC_AVAILABLE, "CBC está instalado: no se puede simular su ausencia.")
    def test_missing_solver_raises_clear_error(self):
        matrix = np.array([
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0],
        ])

        with self.assertRaisesRegex(RuntimeError, "CBC|solver exacto|Instálalo"):
            solve_exact_tsp(matrix, solver_name="cbc")

    def test_missing_solver_message_is_actionable(self):
        self.assertIn("CBC", SOLVER_MISSING_MESSAGE)
        self.assertIn("apt-get install coinor-cbc", SOLVER_MISSING_MESSAGE)


@unittest.skipUnless(CBC_AVAILABLE, "Requiere el solver CBC instalado en el sistema.")
class TestExactSolverWithCbc(unittest.TestCase):
    def test_solves_square_instance_to_optimality(self):
        result = solve_exact_tsp(SQUARE, solver_name="cbc")

        self.assertAlmostEqual(result["total_distance_km"], 40.0, places=3)
        self.assertEqual(result["n_houses"], 4)

    def test_route_is_a_single_closed_hamiltonian_cycle(self):
        route = solve_exact_tsp(SQUARE, solver_name="cbc")["route_index"]

        self.assertEqual(route[0], 0)
        self.assertEqual(route[-1], 0)
        self.assertEqual(len(route), 5)
        self.assertCountEqual(route[:-1], [0, 1, 2, 3])

    def test_single_house_is_a_trivial_route(self):
        result = solve_exact_tsp(np.zeros((1, 1)), solver_name="cbc")

        self.assertEqual(result["route_index"], [0, 0])
        self.assertEqual(result["total_distance_km"], 0.0)


if __name__ == "__main__":
    unittest.main()
