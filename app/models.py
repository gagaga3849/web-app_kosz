from decimal import Decimal

from app.extensions import db


class JobType(db.Model):
    __tablename__ = "job_types"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name_pl = db.Column(db.String(255), nullable=False)
    floor_factor = db.Column(db.Numeric(8, 4), nullable=False, default=Decimal("1"))
    wall_factor = db.Column(db.Numeric(8, 4), nullable=False, default=Decimal("0"))
    perimeter_m_per_floor_m2 = db.Column(db.Numeric(8, 4), nullable=False, default=Decimal("0"))


class Material(db.Model):
    __tablename__ = "materials"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name_pl = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(16), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="PLN")
    # Populated by scripts/sync_prices.py. Manually-seeded rows leave these
    # null/default until a real price sync has run against them.
    base_price = db.Column(db.Numeric(12, 4), nullable=True)
    markup_multiplier = db.Column(db.Numeric(8, 4), nullable=False, default=Decimal("1"))


class Work(db.Model):
    __tablename__ = "works"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name_pl = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(16), nullable=False)
    labor_rate = db.Column(db.Numeric(12, 2), nullable=False)
    hours_per_unit = db.Column(db.Numeric(8, 4), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="PLN")
    # Populated by scripts/sync_prices.py, mirrors Material's fields above.
    base_price = db.Column(db.Numeric(12, 4), nullable=True)
    markup_multiplier = db.Column(db.Numeric(8, 4), nullable=False, default=Decimal("1"))


class WorkNorm(db.Model):
    __tablename__ = "work_norms"

    id = db.Column(db.Integer, primary_key=True)
    job_type_id = db.Column(db.Integer, db.ForeignKey("job_types.id"), nullable=False)
    item_kind = db.Column(db.String(16), nullable=False)  # material | work
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=True)
    work_id = db.Column(db.Integer, db.ForeignKey("works.id"), nullable=True)
    qty_per_unit = db.Column(db.Numeric(12, 4), nullable=False)
    applies_to = db.Column(db.String(16), nullable=False)  # floor | wall | perimeter

    job_type = db.relationship("JobType")
    material = db.relationship("Material")
    work = db.relationship("Work")


class RegionalCoefficient(db.Model):
    __tablename__ = "regional_coefficients"

    id = db.Column(db.Integer, primary_key=True)
    region_code = db.Column(db.String(16), unique=True, nullable=False)
    country = db.Column(db.String(2), nullable=False, default="PL")
    coefficient = db.Column(db.Numeric(8, 4), nullable=False, default=Decimal("1"))
    name_pl = db.Column(db.String(255), nullable=False)
