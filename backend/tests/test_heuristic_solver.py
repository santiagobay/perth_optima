import unittest

import numpy as np

from optimization.heuristic_solver import (
    nearest_neighbor_route,
    rotate_to_start,
    route_length,
    solve_heuristic_tsp,
    two_opt,
)


def circle_matrix(n: int, radius: float = 1.0) -> np.ndarray:
    """Distancias euclídeas entre n puntos equiespaciados sobre una
    circunferencia: el tour óptimo es, por construcción, el perímetro."""
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    points = np.stack([radius * np.cos(angles), radius * np.sin(angles)], axis=1)
    diff = points[:, None, :] - points[None, :, :]
    return np.sqrt((diff ** 2).sum(axis=2))


class TestHeuristicSolver(unittest.TestCase):
    def test_route_is_a_closed_tour_over_every_house(self):
        matrix = circle_matrix(12)
        result = solve_heuristic_tsp(matrix)
        route = result["route_index"]

        self.assertEqual(route[0], 0)
        self.assertEqual(route[-1], 0)
        self.assertCountEqual(route[:-1], list(range(12)))

    def test_two_opt_never_worsens_the_route(self):
        rng = np.random.default_rng(7)
        points = rng.random((25, 2))
        diff = points[:, None, :] - points[None, :, :]
        matrix = np.sqrt((diff ** 2).sum(axis=2))

        initial = nearest_neighbor_route(matrix)
        improved = two_opt(initial, matrix)

        self.assertLessEqual(
            route_length(improved, matrix), route_length(initial, matrix) + 1e-9
        )

    def test_finds_the_perimeter_on_a_circle(self):
        n = 14
        matrix = circle_matrix(n)
        optimal = float(matrix[0, 1] * n)  # perímetro del polígono regular

        result = solve_heuristic_tsp(matrix)

        self.assertAlmostEqual(result["total_distance_km"], round(optimal, 3), places=2)

    def test_reported_distance_matches_the_returned_route(self):
        matrix = circle_matrix(20)
        result = solve_heuristic_tsp(matrix)

        self.assertAlmostEqual(
            result["total_distance_km"],
            round(route_length(result["route_index"], matrix), 3),
            places=3,
        )

    def test_rotate_to_start_preserves_length(self):
        matrix = circle_matrix(10)
        tour = two_opt(nearest_neighbor_route(matrix, 3), matrix)
        rotated = rotate_to_start(tour, 0)

        self.assertEqual(rotated[0], 0)
        self.assertEqual(rotated[-1], 0)
        self.assertAlmostEqual(route_length(rotated, matrix), route_length(tour, matrix))

    def test_single_house_district(self):
        result = solve_heuristic_tsp(np.zeros((1, 1)))

        self.assertEqual(result["route_index"], [0, 0])
        self.assertEqual(result["total_distance_km"], 0.0)

    def test_invalid_start_is_rejected(self):
        with self.assertRaises(ValueError):
            solve_heuristic_tsp(circle_matrix(5), start=9)


if __name__ == "__main__":
    unittest.main()
