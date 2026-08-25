from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, jsonify, render_template, request

from app.calculator import EstimateError, calculate_estimate, list_job_types, list_regions
from app.i18n import DEFAULT_LOCALE, t
from app.llm import parse_free_text, generate_estimate_summary

bp = Blueprint("main", __name__)


def _locale() -> str:
    return current_app.config.get("DEFAULT_LOCALE", DEFAULT_LOCALE)


def _parse_payload(data: dict) -> tuple[str, Decimal, str]:
    job_type = (data.get("job_type") or "").strip()
    region = (data.get("region") or current_app.config.get("DEFAULT_REGION", "pl")).strip()
    raw_area = data.get("area_m2")
    if raw_area is None or str(raw_area).strip() == "":
        raise EstimateError("Podaj powierzchnię w m².")
    try:
        area = Decimal(str(raw_area).replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise EstimateError("Podaj poprawną powierzchnię w m².") from exc
    if not job_type:
        raise EstimateError("Wybierz rodzaj prac.")
    return job_type, area, region


def _form_context(**extra):
    locale = _locale()
    ctx = {
        "t": lambda key: t(key, locale),
        "locale": locale,
        "job_types": list_job_types(),
        "regions": list_regions(),
        "form": {
            "job_type": request.form.get("job_type", "bathroom_tiling"),
            "area_m2": request.form.get("area_m2", "4"),
            "region": request.form.get("region", "pl"),
        },
        "estimate": None,
        "error": None,
    }
    ctx.update(extra)
    return ctx


@bp.get("/")
def index():
    return render_template("index.html", **_form_context())


@bp.post("/estimate")
def estimate_form():
    locale = _locale()
    try:
        job_type, area, region = _parse_payload(request.form)
        estimate = calculate_estimate(
            job_type=job_type,
            area_m2=area,
            region=region,
            hours_per_day=current_app.config["LABOR_HOURS_PER_DAY"],
        )
        # Generate friendly LLM summary if key is available
        summary = generate_estimate_summary(estimate, locale=locale)
        estimate["summary"] = summary
        return render_template("index.html", **_form_context(estimate=estimate))
    except EstimateError as exc:
        return render_template("index.html", **_form_context(error=str(exc))), 400


@bp.post("/api/estimate")
def estimate_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Oczekiwano JSON z polami job_type, area_m2, region."}), 400
    try:
        job_type, area, region = _parse_payload(data)
        estimate = calculate_estimate(
            job_type=job_type,
            area_m2=area,
            region=region,
            hours_per_day=current_app.config["LABOR_HOURS_PER_DAY"],
        )
        # Generate friendly LLM summary if key is available
        summary = generate_estimate_summary(estimate, locale="pl")
        estimate["summary"] = summary
        return jsonify(estimate)
    except EstimateError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/api/parse_text")
def parse_text():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("text"):
        return jsonify({"error": "Oczekiwano JSON z polem text."}), 400
    
    text = data["text"]
    
    # Query database to get available choices dynamically
    job_types = [{"code": j.code, "name": j.name_pl} for j in list_job_types()]
    regions = [{"code": r.region_code, "name": r.name_pl} for r in list_regions()]
    
    result = parse_free_text(text, job_types, regions)
    return jsonify(result)

