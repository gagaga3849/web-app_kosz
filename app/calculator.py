from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Any

from app.models import JobType, RegionalCoefficient, WorkNorm


MONEY = Decimal("0.01")
QTY = Decimal("0.0001")


class EstimateError(ValueError):
    """User-facing calculation input error (invalid area, unknown job, unknown region)."""


@dataclass(frozen=True)
class LineItem:
    code: str
    name: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    currency: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "unit": self.unit,
            "quantity": _num(self.quantity),
            "unit_price": _money(self.unit_price),
            "total": _money(self.total),
            "currency": self.currency,
        }


def _money(value: Decimal) -> str:
    return str(value.quantize(MONEY, rounding=ROUND_HALF_UP))


def _num(value: Decimal) -> str:
    quantized = value.quantize(QTY, rounding=ROUND_HALF_UP)
    return format(quantized.normalize(), "f")


def _qty_base(job: JobType, area_m2: Decimal, applies_to: str) -> Decimal:
    if applies_to == "floor":
        return area_m2 * job.floor_factor
    if applies_to == "wall":
        return area_m2 * job.wall_factor
    if applies_to == "perimeter":
        return area_m2 * job.perimeter_m_per_floor_m2
    raise EstimateError(f"Nieznany wymiar normy: {applies_to}")


def calculate_estimate(
    *,
    job_type: str,
    area_m2: Decimal | float | str,
    region: str,
    hours_per_day: int = 8,
) -> dict[str, Any]:
    """Deterministic estimate from catalog tables. No LLM, no network."""
    try:
        area = Decimal(str(area_m2))
    except Exception as exc:
        raise EstimateError("Podaj poprawną powierzchnię w m².") from exc

    if area <= 0:
        raise EstimateError("Powierzchnia musi być większa od zera.")
    if area > Decimal("500"):
        raise EstimateError("Powierzchnia jest zbyt duża dla tego kalkulatora.")

    job = JobType.query.filter_by(code=job_type).one_or_none()
    if job is None:
        raise EstimateError("Nieznany rodzaj prac.")

    coeff_row = RegionalCoefficient.query.filter_by(region_code=region).one_or_none()
    if coeff_row is None:
        raise EstimateError("Nieznany region.")
    coefficient = Decimal(coeff_row.coefficient)

    norms = WorkNorm.query.filter_by(job_type_id=job.id).all()
    material_acc: dict[str, dict[str, Any]] = {}
    work_acc: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"quantity": Decimal("0"), "hours": Decimal("0")}
    )

    for norm in norms:
        base = _qty_base(job, area, norm.applies_to)
        qty = Decimal(norm.qty_per_unit) * base
        if norm.item_kind == "material":
            mat = norm.material
            bucket = material_acc.setdefault(
                mat.code,
                {
                    "code": mat.code,
                    "name": mat.name_pl,
                    "unit": mat.unit,
                    "quantity": Decimal("0"),
                    "unit_price": Decimal(mat.unit_price) * coefficient,
                    "currency": mat.currency,
                },
            )
            bucket["quantity"] += qty
        elif norm.item_kind == "work":
            work = norm.work
            bucket = work_acc[work.code]
            bucket["work"] = work
            bucket["quantity"] += qty
            bucket["hours"] += qty * Decimal(work.hours_per_unit)
        else:
            raise EstimateError(f"Nieznany rodzaj pozycji: {norm.item_kind}")

    materials: list[LineItem] = []
    for code in sorted(material_acc):
        row = material_acc[code]
        total = (row["quantity"] * row["unit_price"]).quantize(MONEY, rounding=ROUND_HALF_UP)
        materials.append(
            LineItem(
                code=row["code"],
                name=row["name"],
                unit=row["unit"],
                quantity=row["quantity"],
                unit_price=row["unit_price"].quantize(MONEY, rounding=ROUND_HALF_UP),
                total=total,
                currency=row["currency"],
            )
        )

    works: list[LineItem] = []
    sequence: list[dict[str, Any]] = []
    total_hours = Decimal("0")
    work_rows = sorted(work_acc.values(), key=lambda r: r["work"].sequence_order)
    for row in work_rows:
        work = row["work"]
        unit_price = (Decimal(work.labor_rate) * coefficient).quantize(MONEY, rounding=ROUND_HALF_UP)
        total = (row["quantity"] * unit_price).quantize(MONEY, rounding=ROUND_HALF_UP)
        works.append(
            LineItem(
                code=work.code,
                name=work.name_pl,
                unit=work.unit,
                quantity=row["quantity"],
                unit_price=unit_price,
                total=total,
                currency=work.currency,
            )
        )
        sequence.append({"order": work.sequence_order, "code": work.code, "name": work.name_pl})
        total_hours += row["hours"]

    materials_total = sum((item.total for item in materials), Decimal("0"))
    works_total = sum((item.total for item in works), Decimal("0"))
    grand_total = (materials_total + works_total).quantize(MONEY, rounding=ROUND_HALF_UP)
    duration_days = int(ceil(float(total_hours / Decimal(hours_per_day)))) if total_hours > 0 else 0

    return {
        "job_type": job.code,
        "job_name": job.name_pl,
        "area_m2": _num(area),
        "region": region,
        "currency": "PLN",
        "dimensions": {
            "floor_m2": _num(area * job.floor_factor),
            "wall_m2": _num(area * job.wall_factor),
            "perimeter_m": _num(area * job.perimeter_m_per_floor_m2),
        },
        "materials": [item.as_dict() for item in materials],
        "works": [item.as_dict() for item in works],
        "materials_total": _money(materials_total),
        "works_total": _money(works_total),
        "total_price": _money(grand_total),
        "estimated_labor_hours": _num(total_hours),
        "estimated_duration_days": duration_days,
        "sequence": sequence,
    }


def list_job_types() -> list[JobType]:
    return JobType.query.order_by(JobType.code).all()


def list_regions() -> list[RegionalCoefficient]:
    return RegionalCoefficient.query.order_by(RegionalCoefficient.region_code).all()
