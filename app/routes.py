from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_file, session, url_for

from app.calculator import (
    EstimateError,
    calculate_combined_estimate,
    list_job_types,
    list_regions,
)
from app.area_hints import guess_area_from_text
from app.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, catalog_name, t
from app.llm import parse_free_text, generate_estimate_summary
from app.exports import make_docx, make_pdf, make_xls

bp = Blueprint("main", __name__)

MARKET_OPTIONS = [("pl", "PL · Polska")]
CURRENCY_OPTIONS = [("PLN", "PLN · złoty")]


def _locale() -> str:
    requested = request.args.get("lang")
    if requested in SUPPORTED_LOCALES:
        session["locale"] = requested
    selected = session.get("locale", current_app.config.get("DEFAULT_LOCALE", DEFAULT_LOCALE))
    return selected if selected in SUPPORTED_LOCALES else DEFAULT_LOCALE


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


def _parse_items(data: dict) -> tuple[list[dict[str, str]], str]:
    region = (data.get("region") or current_app.config.get("DEFAULT_REGION", "pl")).strip()
    raw_items = data.get("items")
    if raw_items is None:
        job_type, area, region = _parse_payload(data)
        return [{"job_type": job_type, "area_m2": str(area)}], region
    if not isinstance(raw_items, list):
        raise EstimateError("Lista rodzajów prac jest nieprawidłowa.")

    items = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise EstimateError("Każdy rodzaj prac musi zawierać typ i powierzchnię.")
        job_type, area, _ = _parse_payload(item | {"region": region})
        items.append({"job_type": job_type, "area_m2": str(area)})
    if not items:
        raise EstimateError("Dodaj co najmniej jeden rodzaj prac.")
    return items, region


def _estimate_from_form():
    items, region = _parse_items({
        "items": [
            {"job_type": job_type, "area_m2": area}
            for job_type, area in zip(request.form.getlist("job_type"), request.form.getlist("area_m2"))
        ],
        "region": request.form.get("region"),
    })
    return calculate_combined_estimate(
        items=items,
        region=region,
        hours_per_day=current_app.config["LABOR_HOURS_PER_DAY"],
        locale=_locale(),
    )


def _form_context(**extra):
    locale = _locale()
    job_types = list_job_types()
    regions = list_regions()
    ctx = {
        "t": lambda key: t(key, locale),
        "locale": locale,
        "job_types": job_types,
        "regions": regions,
        "catalog_name": lambda code, fallback: catalog_name(code, fallback, locale),
        "market_options": MARKET_OPTIONS,
        "currency_options": CURRENCY_OPTIONS,
        "selected_market": session.get("market", current_app.config.get("DEFAULT_REGION", "pl")),
        "selected_currency": session.get("currency", current_app.config.get("DEFAULT_CURRENCY", "PLN")),
        "form": {
            "job_type": request.form.get("job_type", "bathroom_tiling"),
            "area_m2": request.form.get("area_m2", "4"),
            "items": list(zip(request.form.getlist("job_type"), request.form.getlist("area_m2"))) or [("bathroom_tiling", "4")],
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


@bp.get("/language/<locale>")
def set_language(locale: str):
    if locale in SUPPORTED_LOCALES:
        session["locale"] = locale
    return redirect(url_for("main.index"))


@bp.get("/preferences")
def preferences():
    if request.args.get("lang") in SUPPORTED_LOCALES:
        session["locale"] = request.args["lang"]
    if request.args.get("market") in {code for code, _ in MARKET_OPTIONS}:
        session["market"] = request.args["market"]
    if request.args.get("currency") in {code for code, _ in CURRENCY_OPTIONS}:
        session["currency"] = request.args["currency"]
    return redirect(url_for("main.index"))


@bp.post("/estimate")
def estimate_form():
    locale = _locale()
    try:
        estimate = _estimate_from_form()
        locale = _locale()
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
        return jsonify({"error": "Oczekiwano JSON z polami items, region."}), 400
    try:
        items, region = _parse_items(data)
        estimate = calculate_combined_estimate(
            items=items,
            region=region,
            hours_per_day=current_app.config["LABOR_HOURS_PER_DAY"],
            locale=_locale(),
        )
        # Generate friendly LLM summary if key is available
        summary = generate_estimate_summary(estimate, locale="pl")
        estimate["summary"] = summary
        return jsonify(estimate)
    except EstimateError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/estimate/export/<file_format>")
def export_estimate(file_format: str):
    generators = {
        "pdf": (make_pdf, "application/pdf", "kosztorys.pdf"),
        "xls": (make_xls, "application/vnd.ms-excel", "kosztorys.xls"),
        "docx": (make_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "kosztorys.docx"),
    }
    generator_info = generators.get(file_format)
    if generator_info is None:
        return jsonify({"error": "Nieobsługiwany format pliku."}), 404
    try:
        estimate = _estimate_from_form()
        generator, mimetype, filename = generator_info
        return send_file(generator(estimate), as_attachment=True, download_name=filename, mimetype=mimetype)
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

    # The LLM found no size at all — fall back to a deterministic keyword
    # guess (no LLM, no network) rather than leaving the user with a blank
    # field and no starting point. Always flagged as an assumption, never
    # treated as a confident match.
    if not result.get("area_m2"):
        hint = guess_area_from_text(text)
        if hint:
            result["area_m2"] = hint["area_m2"]
            result["area_m2_assumed"] = True
            result["area_hint_label"] = hint["label"]

    return jsonify(result)















