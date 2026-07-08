import requests
import json
import time

BASE_URL = "http://localhost:8000"
SESSION_ID = "test-verification-session-123"

def run_tests():
    print("=== AskSQL Upload-Dataset Feature Verification Tests ===")
    
    # 1. Healthcheck
    print("\n1. Testing healthcheck...")
    res = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {res.status_code}, Body: {res.json()}")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # 2. Schema check (initially empty)
    print("\n2. Checking initial schema (should be empty)...")
    res = requests.get(f"{BASE_URL}/api/schema?session_id={SESSION_ID}")
    print(f"Tables: {res.json().get('tables')}")
    assert len(res.json().get("tables", [])) == 0

    # 3. Mount pre-packaged Olist sample dataset
    print("\n3. Seeding session with sample dataset...")
    start_time = time.time()
    res = requests.post(
        f"{BASE_URL}/api/sample",
        json={"session_id": SESSION_ID}
    )
    duration = time.time() - start_time
    print(f"Status: {res.status_code}, Duration: {duration:.2f}s")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    
    tables_created = [t["table_name"] for t in res.json()["tables"]]
    print(f"Tables loaded into session: {tables_created}")
    assert "customers" in tables_created
    assert "orders" in tables_created

    # 4. Verify dynamic schema browser descriptions
    print("\n4. Verifying dynamic schema browser metadata...")
    res = requests.get(f"{BASE_URL}/api/schema?session_id={SESSION_ID}")
    tables = res.json()["tables"]
    print(f"Number of tables loaded: {len(tables)}")
    
    for t in tables[:3]:
        print(f"Table '{t['table_name']}' - Description: {t['description']}")
        print(f"  Columns: {t['columns'][:5]}...")
    assert len(tables) > 0

    # 5. Execute natural language query (SELECT)
    print("\n5. Running natural language query against session DuckDB...")
    query_payload = {
        "question": "How many orders have been placed in total?",
        "session_id": SESSION_ID
    }
    res = requests.post(f"{BASE_URL}/api/query", json=query_payload)
    print(f"Status: {res.status_code}")
    response_data = res.json()
    print(f"Success: {response_data.get('success')}")
    print(f"SQL generated: {response_data.get('sql')}")
    print(f"Explanation: {response_data.get('explanation')}")
    print(f"Results: {response_data.get('results')}")
    assert response_data["success"] is True
    assert len(response_data.get("results", [])) > 0

    # 6. Execute another NL query with join
    print("\n6. Running natural language query requiring JOIN...")
    query_payload = {
        "question": "Show the top 3 cities with the highest number of customers.",
        "session_id": SESSION_ID
    }
    res = requests.post(f"{BASE_URL}/api/query", json=query_payload)
    print(f"Status: {res.status_code}")
    response_data = res.json()
    print(f"Success: {response_data.get('success')}")
    print(f"SQL generated: {response_data.get('sql')}")
    print(f"Results: {response_data.get('results')}")
    assert response_data["success"] is True
    assert len(response_data.get("results", [])) > 0

    # 7. Clear dataset
    print("\n7. Clearing session dataset...")
    res = requests.post(
        f"{BASE_URL}/api/clear",
        json={"session_id": SESSION_ID}
    )
    print(f"Status: {res.status_code}, Body: {res.json()}")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # 8. Verify schema is empty again
    print("\n8. Checking schema list after clearing...")
    res = requests.get(f"{BASE_URL}/api/schema?session_id={SESSION_ID}")
    print(f"Tables: {res.json().get('tables')}")
    assert len(res.json().get("tables", [])) == 0

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
