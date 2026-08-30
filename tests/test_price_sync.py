import json
from decimal import Decimal
from pathlib import Path

from app.config import Config
from app import create_app


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SECRET_KEY = "test"


def _make_app(tmp_path):
    class FileConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"

    return create_app(FileConfig)


def test_sync_reproduces_known_seed_prices(tmp_path):
    """The committed sample CSV's base_price values were back-calculated from
    the current seed prices, so running the real sync against the real sample
    data should reproduce today's unit_price/labor_rate exactly."""
    app = _make_app(tmp_path)
    with app.app_context():
        from app.calculator import calculate_estimate
        from app.models import Material, Work
        from scripts.sync_prices import sync_prices

        before = calculate_estimate(job_type="bathroom_tiling", area_m2="4", region="pl")

        repo_root = Path(__file__).resolve().parent.parent
        summary = sync_prices(
            sekocenbud_path=repo_root / "data" / "sekocenbud_sample.csv",
            markup_path=repo_root / "data" / "retail_markup.json",
        )

        assert summary["updated"] == 29  # 19 materials + 10 works
        assert summary["skipped"] == 0

        after = calculate_estimate(job_type="bathroom_tiling", area_m2="4", region="pl")
        assert after["total_price"] == before["total_price"]

        tile = Material.query.filter_by(code="plytki_podlogowe").first()
        assert tile.base_price == Decimal("49.1667")
        assert tile.markup_multiplier == Decimal("1.20")
        assert tile.unit_price == Decimal("59.00")  # override markup applied

        prep = Work.query.filter_by(code="prep").first()
        assert prep.base_price == Decimal("21.7391")
        assert prep.markup_multiplier == Decimal("1.15")  # default markup applied


def test_sync_skips_unknown_codes_without_crashing(tmp_path):
    app = _make_app(tmp_path)
    with app.app_context():
        from scripts.sync_prices import sync_prices

        csv_path = tmp_path / "partial.csv"
        csv_path.write_text(
            "kind,code,base_price\n"
            "material,plytki_podlogowe,50.00\n"
            "material,nonexistent_material,10.00\n"
        )
        markup_path = tmp_path / "markup.json"
        markup_path.write_text(json.dumps({"default": 1.10, "overrides": {}}))

        summary = sync_prices(sekocenbud_path=csv_path, markup_path=markup_path)

        assert summary["updated"] == 1
        assert summary["skipped"] == 1


def test_dry_run_makes_no_changes(tmp_path):
    app = _make_app(tmp_path)
    with app.app_context():
        from app.models import Material
        from scripts.sync_prices import sync_prices

        original_price = Material.query.filter_by(code="plytki_podlogowe").first().unit_price

        csv_path = tmp_path / "changed.csv"
        csv_path.write_text("kind,code,base_price\nmaterial,plytki_podlogowe,999.00\n")
        markup_path = tmp_path / "markup.json"
        markup_path.write_text(json.dumps({"default": 1.0, "overrides": {}}))

        sync_prices(sekocenbud_path=csv_path, markup_path=markup_path, dry_run=True)

        unchanged = Material.query.filter_by(code="plytki_podlogowe").first()
        assert unchanged.unit_price == original_price
