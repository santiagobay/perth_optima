import unittest
import numpy as np

from optimization.exact_solver import solve_exact_tsp


class TestExactSolver(unittest.TestCase):
    def test_missing_solver_raises_clear_error(self):
        matrix = np.array([
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0],
        ])

        with self.assertRaisesRegex(RuntimeError, "CBC|solver exacto|instalar"):
            solve_exact_tsp(matrix, solver_name="cbc")


if __name__ == "__main__":
    unittest.main()
