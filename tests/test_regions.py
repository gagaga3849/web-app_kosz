import pytest

from app.config import Config
from app import create_app
from app.models import RegionalCoefficient
from app.regions_data import VOIVODESHIPS


class FileConfig(Config):
    TESTING = True
    SECRET_KEY = "test"


@pytest.fixture
def app_(tmp_path):
    class Cfg(FileConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
    return create_app(Cfg)


def test_seeds_national_fallback_plus_all_voivodeships(app_):
    with app_.app_context():
        # 1 national fallback ("pl") + 16 voivodeships x (capital + average)
        assert RegionalCoefficient.query.count() == 1 + len(VOIVODESHIPS) * 2
        for v in VOIVODESHIPS:
            capital = RegionalCoefficient.query.filter_by(region_code=v.capital_region_code).one()
            avg = RegionalCoefficient.query.filter_by(region_code=v.avg_region_code).one()
            assert capital.is_capital is True
            assert avg.is_capital is False
            assert capital.voivodeship_code == v.voivodeship_code == avg.voivodeship_code
            # A voivodeship's capital should never be priced below its own
            # average — that would contradict the whole point of splitting
            # them out.
            assert capital.coefficient >= avg.coefficient


def test_warsaw_is_the_most_expensive_region(app_):
    with app_.app_context():
        all_coeffs = {r.region_code: r.coefficient for r in RegionalCoefficient.query.all()}
        assert all_coeffs["mazowieckie_warszawa"] == max(all_coeffs.values())


def test_same_job_prices_differently_by_region(app_):
    client = app_.test_client()
    warsaw = client.post(
        "/api/estimate",
        json={"job_type": "bathroom_tiling", "area_m2": 4, "region": "mazowieckie_warszawa"},
    ).get_json()
    cheapest_avg = client.post(
        "/api/estimate",
        json={"job_type": "bathroom_tiling", "area_m2": 4, "region": "podkarpackie_avg"},
    ).get_json()
    assert float(warsaw["total_price"]) > float(cheapest_avg["total_price"])


def test_unknown_region_still_rejected(app_):
    client = app_.test_client()
    response = client.post(
        "/api/estimate",
        json={"job_type": "bathroom_tiling", "area_m2": 4, "region": "atlantis"},
    )
    assert response.status_code == 400


def test_region_dropdown_has_one_optgroup_per_voivodeship(app_):
    client = app_.test_client()
    html = client.get("/").data.decode()
    for v in VOIVODESHIPS:
        assert f'<optgroup label="{v.name_pl}">' in html
    # National fallback stays a plain top-level option, not inside a group.
    assert 'value="pl"' in html


def test_ensure_regions_is_idempotent_and_never_overwrites_existing_coefficient(app_):
    # Simulates upgrading a database that was seeded before this feature
    # existed: JobType rows are already there, so seed_if_empty() takes the
    # "ensure_*" upgrade path instead of a full reseed.
    from app.seed import ensure_regions
    with app_.app_context():
        row = RegionalCoefficient.query.filter_by(region_code="mazowieckie_warszawa").one()
        row.coefficient = row.coefficient  # noqa: PLW0127 — no-op, just reading it below
        from decimal import Decimal
        row.coefficient = Decimal("9.9999")  # simulate a manually-tuned value
        from app.extensions import db
        db.session.commit()

        ensure_regions()

        reloaded = RegionalCoefficient.query.filter_by(region_code="mazowieckie_warszawa").one()
        assert reloaded.coefficient == Decimal("9.9999")
        # Still exactly one row per code — ensure_regions must not duplicate.
        assert RegionalCoefficient.query.filter_by(region_code="mazowieckie_warszawa").count() == 1
