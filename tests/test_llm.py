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

        mock_parse.assert_called_once()

def test_api_parse_text_partial_match(client):
    # job_type recognized but area_m2 wasn't mentioned in the text at all —
    # this must NOT be discarded; job_type should still come through.
    # (Text deliberately has no recognizable space keyword, so the
    # deterministic area-hint fallback shouldn't kick in either.)
    with patch("app.routes.parse_free_text") as mock_parse:
        mock_parse.return_value = {
            "job_type": "wall_ceiling_painting",
            "area_m2": None,
            "region": None,
        }

        response = client.post(
            "/api/parse_text",
            json={"text": "prace malarskie"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["job_type"] == "wall_ceiling_painting"
        assert data["area_m2"] is None

def test_api_parse_text_falls_back_to_area_hint(client):
    # LLM found the job type but no area — the route should fill area_m2
    # from the deterministic keyword table and flag it as an assumption,
    # never silently treat it as a confident value.
    with patch("app.routes.parse_free_text") as mock_parse:
        mock_parse.return_value = {
            "job_type": "wall_ceiling_painting",
            "area_m2": None,
            "region": None,
        }

        response = client.post(
            "/api/parse_text",
            json={"text": "malowanie garazu"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["area_m2"] == 15.0
        assert data["area_m2_assumed"] is True
        assert "garaż" in data["area_hint_label"]

def test_api_parse_text_no_hint_available(client):
    # LLM found nothing and the text has no recognizable space keyword —
    # area_m2 stays None, no assumption fields are added.
    with patch("app.routes.parse_free_text") as mock_parse:
        mock_parse.return_value = {
            "job_type": None,
            "area_m2": None,
            "region": None,
        }

        response = client.post(
            "/api/parse_text",
            json={"text": "coś tam coś tam"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["area_m2"] is None
        assert "area_m2_assumed" not in data

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


def test_api_estimate_summary_uses_the_requested_locale(client):
    # Regression test: /api/estimate used to call generate_estimate_summary
    # with locale hardcoded to "pl" no matter what the caller asked for, so
    # an English or Russian client never got a summary in their language.
    with patch("app.routes.generate_estimate_summary") as mock_summary:
        mock_summary.return_value = "mocked"

        client.get("/language/en")
        client.post(
            "/api/estimate",
            json={"job_type": "bathroom_tiling", "area_m2": 4, "region": "pl"},
        )

        _, kwargs = mock_summary.call_args
        assert kwargs.get("locale") == "en"
