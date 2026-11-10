from starlette.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    print(f"Status code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print(">>> Bước 1 Backend Health Check: THÀNH CÔNG (PASSED) <<<")

if __name__ == "__main__":
    test_health()

