import pytest
from unittest.mock import patch
from app.config import Config
from app import create_app

class FileConfig(Config):
    TESTING = True
    SECRET_KEY = "test"

@pytest.fixture
def client(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
    app = create_app(Cfg)
    return app.test_client()

def test_api_parse_text_success(client):
    with patch("app.routes.parse_free_text") as mock_parse:
        mock_parse.return_value = {
            "job_type": "bathroom_tiling",
            "area_m2": 4.0,
            "region": "pl",
            "confidence": True
        }
        
        response = client.post(
            "/api/parse_text",
            json={"text": "Ułóż kafelki w łazience, 4 m²"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["job_type"] == "bathroom_tiling"
        assert data["area_m2"] == 4.0
        assert data["region"] == "pl"
        assert data["confidence"] is True
        
        mock_parse.assert_called_once()

def test_api_parse_text_invalid_payload(client):
    response = client.post(
        "/api/parse_text",
        json={}
    )
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_api_estimate_with_mocked_summary(client):
    with patch("app.routes.generate_estimate_summary") as mock_summary:
        mock_summary.return_value = "This is a beautifully mocked summary."
        
        response = client.post(
            "/api/estimate",
            json={"job_type": "bathroom_tiling", "area_m2": 4, "region": "pl"},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["summary"] == "This is a beautifully mocked summary."
        mock_summary.assert_called_once()
