import json
from pathlib import Path

class SchemaMetadata:
    def __init__(self):
        backend_dir = Path(__file__).resolve().parent.parent.parent
        schema_path = backend_dir / "data" / "schema_descriptions.json"
        
        with open(schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.tables = {}
        for table_data in data.get("tables", []):
            table_name = table_data["table_name"]
            self.tables[table_name] = {
                "description": table_data["description"],
                "columns": set(table_data["columns"].keys())
            }

    def get_valid_tables(self) -> set:
        return set(self.tables.keys())

    def get_valid_columns_for_table(self, table_name: str) -> set:
        if table_name in self.tables:
            return self.tables[table_name]["columns"]
        return set()

    def is_valid_table(self, table_name: str) -> bool:
        return table_name in self.tables

    def is_valid_column(self, table_name: str, column_name: str) -> bool:
        if column_name == "*":
            return True
        # If columns is empty or the table is not found, return False
        if table_name not in self.tables:
            return False
        return column_name in self.tables[table_name]["columns"]

schema_metadata = SchemaMetadata()
