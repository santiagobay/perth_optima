import tempfile
import unittest
from pathlib import Path

import pandas as pd

import app as app_module
from optimization.data_loader import clear_dataset_cache
from optimization.distances import clear_matrix_cache
from optimization.exact_solver import solver_is_available

CBC_AVAILABLE = solver_is_available("cbc")


def _write_district(tmpdir: Path, n_rows: int = 20) -> Path:
    rows = [
        {
            "ADDRESS": f"{i + 1} Test Street",
            "SUBURB": "Nedlands",
            "PRICE": 500000 + i,
            "BEDROOMS": 3,
            "BATHROOMS": 2,
            "LATITUDE": -31.95 + i * 0.0001,
            "LONGITUDE": 115.80 + i * 0.0001,
        }
        for i in range(n_rows)
    ]
    csv_path = tmpdir / "district.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return csv_path


class RouteApiTestCase(unittest.TestCase):
    """Base con un dataset temporal de 20 viviendas en Nedlands."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)
        _write_district(self.tmpdir)

        self._previous_data_dir = app_module.DATA_DIR
        app_module.DATA_DIR = self.tmpdir
        clear_dataset_cache()
        clear_matrix_cache()
        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.DATA_DIR = self._previous_data_dir
        clear_dataset_cache()
        clear_matrix_cache()
        self._tmp.cleanup()


@unittest.skipUnless(CBC_AVAILABLE, "El modo exacto requiere el solver CBC instalado.")
class TestExactSubsetMode(RouteApiTestCase):
    def test_exact_mode_uses_subset_for_large_districts(self):
        response = self.client.get("/api/route?suburb=Nedlands&mode=exact")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["exact_subset_used"])
        self.assertEqual(payload["exact_subset_size"], 15)
        self.assertEqual(payload["n_houses"], 20)
        self.assertEqual(len(payload["route"]), 16)  # 15 paradas + regreso al inicio
        self.assertIsNotNone(payload["optimality_gap_percent"])


class TestHeuristicMode(RouteApiTestCase):
    def test_heuristic_covers_the_whole_district(self):
        response = self.client.get("/api/route?suburb=Nedlands&mode=heuristic")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["n_houses"], 20)
        self.assertEqual(len(payload["route"]), 21)
        self.assertEqual(
            payload["route"][0]["house_id"], payload["route"][-1]["house_id"]
        )
        self.assertGreater(payload["total_distance_km"], 0)

    def test_unknown_suburb_returns_404_json(self):
        response = self.client.get("/api/route?suburb=Atlantis")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Atlantis", response.get_json()["error"])

    def test_invalid_mode_returns_400_json(self):
        response = self.client.get("/api/route?suburb=Nedlands&mode=magic")

        self.assertEqual(response.status_code, 400)
        self.assertIn("magic", response.get_json()["error"])

    def test_suburbs_endpoint_reports_house_counts(self):
        response = self.client.get("/api/suburbs")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["suburbs"], ["Nedlands"])
        self.assertEqual(payload["details"], [{"name": "Nedlands", "n_houses": 20}])

    def test_health_endpoint(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
