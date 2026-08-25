from app.config import Config
from app import create_app


class FileConfig(Config):
    TESTING = True
    SECRET_KEY = "test"


def test_api_estimate_ok(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    client = create_app(Cfg).test_client()
    response = client.post(
        "/api/estimate",
        json={"job_type": "bathroom_tiling", "area_m2": 4, "region": "pl"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_price"] == "5392.40"
    assert payload["currency"] == "PLN"


def test_api_estimate_invalid_area(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    client = create_app(Cfg).test_client()
    response = client.post(
        "/api/estimate",
        json={"job_type": "bathroom_tiling", "area_m2": -1, "region": "pl"},
    )
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert "stack" not in response.get_json()["error"].lower()


def test_form_round_trip(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    client = create_app(Cfg).test_client()
    response = client.post(
        "/estimate",
        data={"job_type": "bathroom_tiling", "area_m2": "4", "region": "pl"},
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "5392.40" in html
    assert "PLN" in html
