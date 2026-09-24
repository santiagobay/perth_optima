import tempfile
import unittest
from pathlib import Path

import pandas as pd

import app as app_module


class TestExactSubsetMode(unittest.TestCase):
    def test_exact_mode_uses_subset_for_large_districts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            rows = []
            for i in range(20):
                rows.append({
                    "ADDRESS": f"{i+1} Test Street",
                    "SUBURB": "Nedlands",
                    "PRICE": 500000 + i,
                    "BEDROOMS": 3,
                    "BATHROOMS": 2,
                    "LATITUDE": -31.95 + i * 0.0001,
                    "LONGITUDE": 115.80 + i * 0.0001,
                })
            csv_path = tmpdir / "district.csv"
            pd.DataFrame(rows).to_csv(csv_path, index=False)

            previous_data_dir = app_module.DATA_DIR
            app_module.DATA_DIR = tmpdir
            try:
                client = app_module.app.test_client()
                response = client.get("/api/route?suburb=Nedlands&mode=exact")
                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertTrue(payload["exact_subset_used"])
                self.assertEqual(payload["exact_subset_size"], 15)
                self.assertEqual(payload["n_houses"], 20)
            finally:
                app_module.DATA_DIR = previous_data_dir


if __name__ == "__main__":
    unittest.main()
