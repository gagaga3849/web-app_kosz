from app.config import Config
from app import create_app


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SECRET_KEY = "test"


def test_four_sqm_bathroom_tile_totals(tmp_path):
    class FileConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    app = create_app(FileConfig)
    with app.app_context():
        from app.calculator import calculate_estimate

        result = calculate_estimate(job_type="bathroom_tiling", area_m2="4", region="pl")

    assert result["currency"] == "PLN"
    assert result["job_type"] == "bathroom_tiling"
    assert result["dimensions"]["floor_m2"] == "4"
    assert result["dimensions"]["wall_m2"] == "12"
    assert result["dimensions"]["perimeter_m"] == "8"
    assert result["materials_total"] == "2032.40"
    assert result["works_total"] == "3360.00"
    assert result["total_price"] == "5392.40"
    assert result["estimated_duration_days"] == 3
    assert [step["code"] for step in result["sequence"]] == [
        "prep",
        "hydro",
        "tile_floor",
        "tile_wall",
        "grout",
    ]

    by_code = {item["code"]: item for item in result["materials"]}
    assert by_code["plytki_podlogowe"]["quantity"] == "4.4"
    assert by_code["plytki_podlogowe"]["total"] == "259.60"
    assert by_code["plytki_scienne"]["quantity"] == "13.2"
    assert by_code["plytki_scienne"]["total"] == "910.80"
    assert by_code["klej_c2"]["quantity"] == "80"
    assert by_code["klej_c2"]["total"] == "96.00"


def test_invalid_area_and_unknown_job(tmp_path):
    class FileConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    app = create_app(FileConfig)
    with app.app_context():
        from app.calculator import EstimateError, calculate_estimate
        import pytest

        with pytest.raises(EstimateError):
            calculate_estimate(job_type="bathroom_tiling", area_m2="0", region="pl")
        with pytest.raises(EstimateError):
            calculate_estimate(job_type="nonexistent_job", area_m2="4", region="pl")
        with pytest.raises(EstimateError):
            calculate_estimate(job_type="bathroom_tiling", area_m2="4", region="ua")
