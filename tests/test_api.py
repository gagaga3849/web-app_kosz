from io import BytesIO

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


def test_api_estimate_combines_multiple_work_types(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    client = create_app(Cfg).test_client()
    response = client.post(
        "/api/estimate",
        json={
            "items": [
                {"job_type": "bathroom_tiling", "area_m2": 4},
                {"job_type": "painting", "area_m2": 4},
            ],
            "region": "pl",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["job_type"] == "combined"
    assert payload["area_m2"] == "8"
    assert payload["total_price"] == "5902.20"
    assert {item["code"] for item in payload["works"]} == {
        "prep",
        "hydro",
        "tile_floor",
        "tile_wall",
        "grout",
        "paint_prep",
        "paint_finish",
    }


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


def test_form_exposes_extended_work_catalog_and_search(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    client = create_app(Cfg).test_client()
    html = client.get("/").get_data(as_text=True)

    assert "Szukaj rodzaju prac" in html
    assert "Wyburzanie ścian działowych" in html
    assert "Instalacja kanalizacyjna" in html
    assert "Nowa instalacja elektryczna" in html


def test_estimate_exports_are_downloadable(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    client = create_app(Cfg).test_client()
    data = {"job_type": "bathroom_tiling", "area_m2": "4", "region": "pl"}

    for file_format, content_type, signature in (
        ("pdf", "application/pdf", b"%PDF"),
        ("xls", "application/vnd.ms-excel", b"\xd0\xcf\x11\xe0"),
        ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK"),
    ):
        response = client.post(f"/estimate/export/{file_format}", data=data)
        assert response.status_code == 200
        assert response.content_type == content_type
        assert response.data.startswith(signature)
        assert "attachment" in response.headers["Content-Disposition"]


def test_pdf_export_preserves_polish_characters(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    client = create_app(Cfg).test_client()
    response = client.post(
        "/estimate/export/pdf",
        data={"job_type": "bathroom_tiling", "area_m2": "4", "region": "pl"},
    )

    from pypdf import PdfReader

    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(response.data)).pages)
    assert response.status_code == 200
    assert "Materiały" in text
    assert "Kolejność prac" in text
    assert "ściany" in text
