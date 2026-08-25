from pathlib import Path

from flask import Flask

from app.config import Config
from app.extensions import db
from app.seed import seed_if_empty

_ROOT = Path(__file__).resolve().parent.parent


def create_app(config_class: type = Config) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(_ROOT / "static"),
        static_url_path="/static",
    )
    app.config.from_object(config_class)

    db.init_app(app)

    from app.routes import bp

    app.register_blueprint(bp)

    with app.app_context():
        from app import models  # noqa: F401 — register tables

        db.create_all()
        seed_if_empty()

    @app.cli.command("estimate")
    def estimate_command() -> None:
        """Print the 4 m² bathroom tiling fixture (no HTTP)."""
        from decimal import Decimal

        from app.calculator import calculate_estimate

        result = calculate_estimate(job_type="bathroom_tiling", area_m2=Decimal("4"), region="pl")
        print(result["total_price"], result["currency"])
        print("days:", result["estimated_duration_days"])
        for item in result["materials"]:
            print("M", item["name"], item["quantity"], item["unit"], item["total"])
        for item in result["works"]:
            print("W", item["name"], item["quantity"], item["unit"], item["total"])

    return app
