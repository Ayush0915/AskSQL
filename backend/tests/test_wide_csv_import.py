import unittest
import uuid
import duckdb
from pathlib import Path
import sys

# Ensure backend can be imported
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.upload.csv_parser import parse_and_load_csv, sanitize_identifier
from backend.app.upload.session_manager import get_duckdb_path, clear_session
from backend.app.db.connection import QueryExecutor

class TestWideCSVImport(unittest.TestCase):
    def setUp(self):
        self.session_id = str(uuid.uuid4())
        self.temp_files = []

    def tearDown(self):
        for f in self.temp_files:
            if f.exists():
                try:
                    f.unlink()
                except Exception:
                    pass
        clear_session(self.session_id)

    def test_wide_32_column_csv_import_and_query_execution(self):
        cols = [
            "id", "diagnosis",
            "radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean",
            "compactness_mean", "concavity_mean", "concave points_mean", "symmetry_mean", "fractal_dimension_mean",
            "radius_se", "texture_se", "perimeter_se", "area_se", "smoothness_se",
            "compactness_se", "concavity_se", "concave points_se", "symmetry_se", "fractal_dimension_se",
            "radius_worst", "texture_worst", "perimeter_worst", "area_worst", "smoothness_worst",
            "compactness_worst", "concavity_worst", "concave points_worst", "symmetry_worst", "fractal_dimension_worst"
        ]
        rows = [",".join(cols)]
        for i in range(1, 101):
            diag = "M" if i % 2 == 0 else "B"
            vals = [str(842302 + i), diag] + [str(round(10.0 + i * 0.01 + j * 0.5, 4)) for j in range(30)]
            rows.append(",".join(vals))
            
        csv_file = Path(__file__).parent / f"test_wide_{self.session_id}.csv"
        csv_file.write_text("\n".join(rows), encoding="utf-8")
        self.temp_files.append(csv_file)

        res = parse_and_load_csv(self.session_id, filename="breast_cancer.csv", file_path=csv_file)

        self.assertEqual(res["table_name"], "breast_cancer")
        self.assertEqual(len(res["columns"]), 32)
        self.assertEqual(res["row_count"], 100)

        db_path = get_duckdb_path(self.session_id)
        conn = duckdb.connect(db_path)
        pragma_info = conn.execute("PRAGMA table_info('breast_cancer')").fetchall()
        conn.close()

        self.assertEqual(len(pragma_info), 32)

        # Execute query against 3 arbitrary columns
        executor = QueryExecutor()
        results = executor.execute_query(
            "SELECT radius_mean, texture_mean, diagnosis FROM breast_cancer WHERE diagnosis = 'M' LIMIT 5",
            session_id=self.session_id
        )
        self.assertGreater(len(results), 0)
        self.assertIn("radius_mean", results[0])
        self.assertIn("texture_mean", results[0])
        self.assertIn("diagnosis", results[0])

    def test_column_name_collision_deduplication(self):
        collision_cols = ["Radius-Mean", "radius_mean", "RADIUS_MEAN"]
        seen = set()
        sanitized = []
        for col in collision_cols:
            scol = sanitize_identifier(col, "col")
            base = scol
            counter = 1
            while scol in seen:
                scol = f"{base}_{counter}"
                counter += 1
            seen.add(scol)
            sanitized.append(scol)

        self.assertEqual(sanitized, ["radius_mean", "radius_mean_1", "radius_mean_2"])

    def test_single_source_delimiter_detection_with_quoted_commas(self):
        csv_text = '"Name, Title";"Age";"Department, Sector"\n"Alice, Lead";"30";"R&D, ML"\n'
        csv_file = Path(__file__).parent / f"test_delim_{self.session_id}.csv"
        csv_file.write_text(csv_text, encoding="utf-8")
        self.temp_files.append(csv_file)

        res = parse_and_load_csv(self.session_id, filename="quoted_delim.csv", file_path=csv_file)

        self.assertEqual(len(res["columns"]), 3)
        self.assertEqual(res["columns"], ["name_title", "age", "department_sector"])

if __name__ == "__main__":
    unittest.main()
