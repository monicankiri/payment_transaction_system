from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Test the root endpoint
def test_read_root():
    # Send a GET request to the root endpoint
    response = client.get("/")
    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    # Assert that the response JSON matches the expected message
    assert response.json() == {
        "message": "Payment Transaction System API is running"
    }