import tempfile
import unittest
from pathlib import Path

import pandas as pd

from optimization.data_loader import load_dataset


class TestRealDatasetColumns(unittest.TestCase):
    def test_uppercase_real_world_columns_are_normalized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "real_perth.csv"
            pd.DataFrame([
                {
                    "ADDRESS": "1 Example Street",
                    "SUBURB": "Nedlands",
                    "PRICE": 500000,
                    "BEDROOMS": 3,
                    "BATHROOMS": 2,
                    "LAND_AREA": 600,
                    "FLOOR_AREA": 200,
                    "LATITUDE": -31.98,
                    "LONGITUDE": 115.79,
                }
            ]).to_csv(csv_path, index=False)

            df = load_dataset(csv_path)
            self.assertEqual(df["suburb"].iloc[0], "Nedlands")
            self.assertEqual(df["address"].iloc[0], "1 Example Street")
            self.assertAlmostEqual(float(df["latitude"].iloc[0]), -31.98)
            self.assertAlmostEqual(float(df["longitude"].iloc[0]), 115.79)


if __name__ == "__main__":
    unittest.main()
