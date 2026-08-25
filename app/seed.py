from decimal import Decimal

from app.extensions import db
from app.models import JobType, Material, RegionalCoefficient, Work, WorkNorm


def seed_if_empty() -> None:
    if JobType.query.first() is not None:
        return
    seed()


def seed() -> None:
    # -------------------------------------------------------------
    # 1. Job Types
    # -------------------------------------------------------------
    tiling_job = JobType(
        code="bathroom_tiling",
        name_pl="Układanie płytek w łazience (podłoga + ściany)",
        floor_factor=Decimal("1"),
        wall_factor=Decimal("3"),
        perimeter_m_per_floor_m2=Decimal("2"),
    )
    painting_job = JobType(
        code="painting",
        name_pl="Malowanie ścian i sufitów",
        floor_factor=Decimal("1"),  # ceiling
        wall_factor=Decimal("2.5"),  # walls
        perimeter_m_per_floor_m2=Decimal("0"),
    )
    laminate_job = JobType(
        code="laminate_flooring",
        name_pl="Układanie paneli podłogowych z listwami",
        floor_factor=Decimal("1"),
        wall_factor=Decimal("0"),
        perimeter_m_per_floor_m2=Decimal("1.6"),
    )

    db.session.add_all([tiling_job, painting_job, laminate_job])
    db.session.flush()

    # -------------------------------------------------------------
    # 2. Materials
    # -------------------------------------------------------------
    materials = {
        # Bathroom Tiling Materials
        "plytki_podlogowe": Material(
            code="plytki_podlogowe",
            name_pl="Płytki podłogowe 60×60",
            unit="m²",
            unit_price=Decimal("59.00"),
        ),
        "plytki_scienne": Material(
            code="plytki_scienne",
            name_pl="Płytki ścienne 30×60",
            unit="m²",
            unit_price=Decimal("69.00"),
        ),
        "klej_c2": Material(
            code="klej_c2",
            name_pl="Klej do płytek C2",
            unit="kg",
            unit_price=Decimal("1.20"),
        ),
        "fuga": Material(
            code="fuga",
            name_pl="Fuga cementowa",
            unit="kg",
            unit_price=Decimal("8.00"),
        ),
        "grunt": Material(
            code="grunt",
            name_pl="Grunt głęboko penetrujący",
            unit="l",
            unit_price=Decimal("12.00"),
        ),
        "hydroizolacja": Material(
            code="hydroizolacja",
            name_pl="Hydroizolacja podpłytkowa",
            unit="kg",
            unit_price=Decimal("18.00"),
        ),
        "wylewka": Material(
            code="wylewka",
            name_pl="Masa samopoziomująca",
            unit="kg",
            unit_price=Decimal("1.40"),
        ),
        "krzyzyki": Material(
            code="krzyzyki",
            name_pl="Krzyżyki dystansowe 2 mm",
            unit="opk",
            unit_price=Decimal("4.50"),
        ),
        "silikon": Material(
            code="silikon",
            name_pl="Silikon sanitarny",
            unit="szt",
            unit_price=Decimal("16.00"),
        ),
        "listwa": Material(
            code="listwa",
            name_pl="Listwa przejściowa",
            unit="mb",
            unit_price=Decimal("28.00"),
        ),
        "tasma": Material(
            code="tasma",
            name_pl="Taśma uszczelniająca",
            unit="mb",
            unit_price=Decimal("7.50"),
        ),
        "folia": Material(
            code="folia",
            name_pl="Folia ochronna",
            unit="m²",
            unit_price=Decimal("3.50"),
        ),
        "zaprawa": Material(
            code="zaprawa",
            name_pl="Zaprawa wyrównująca",
            unit="kg",
            unit_price=Decimal("1.80"),
        ),
        # Painting Materials
        "grunt_malarski": Material(
            code="grunt_malarski",
            name_pl="Grunt malarski pod farby",
            unit="l",
            unit_price=Decimal("6.00"),
        ),
        "farba_lateksowa": Material(
            code="farba_lateksowa",
            name_pl="Farba lateksowa (biała/kolor)",
            unit="l",
            unit_price=Decimal("15.00"),
        ),
        "folia_malarska": Material(
            code="folia_malarska",
            name_pl="Folia malarska i taśma malarska",
            unit="m²",
            unit_price=Decimal("1.50"),
        ),
        # Laminate Flooring Materials
        "panele_podlogowe": Material(
            code="panele_podlogowe",
            name_pl="Panele podłogowe laminowane AC4",
            unit="m²",
            unit_price=Decimal("45.00"),
        ),
        "podklad_paneli": Material(
            code="podklad_paneli",
            name_pl="Podkład pod panele 3 mm",
            unit="m²",
            unit_price=Decimal("6.50"),
        ),
        "listwy_przypodlogowe": Material(
            code="listwy_przypodlogowe",
            name_pl="Listwy przypodłogowe MDF + klipsy",
            unit="mb",
            unit_price=Decimal("16.00"),
        ),
    }
    db.session.add_all(materials.values())
    db.session.flush()

    # -------------------------------------------------------------
    # 3. Work Items
    # -------------------------------------------------------------
    works = {
        # Tiling works
        "prep": Work(
            code="prep",
            name_pl="Przygotowanie podłoża",
            unit="m²",
            labor_rate=Decimal("25.00"),
            hours_per_unit=Decimal("0.15"),
            sequence_order=1,
        ),
        "hydro": Work(
            code="hydro",
            name_pl="Hydroizolacja",
            unit="m²",
            labor_rate=Decimal("45.00"),
            hours_per_unit=Decimal("0.25"),
            sequence_order=2,
        ),
        "tile_floor": Work(
            code="tile_floor",
            name_pl="Układanie płytek podłogowych",
            unit="m²",
            labor_rate=Decimal("90.00"),
            hours_per_unit=Decimal("0.60"),
            sequence_order=3,
        ),
        "tile_wall": Work(
            code="tile_wall",
            name_pl="Układanie płytek ściennych",
            unit="m²",
            labor_rate=Decimal("110.00"),
            hours_per_unit=Decimal("0.70"),
            sequence_order=4,
        ),
        "grout": Work(
            code="grout",
            name_pl="Fugowanie i silikonowanie",
            unit="m²",
            labor_rate=Decimal("35.00"),
            hours_per_unit=Decimal("0.20"),
            sequence_order=5,
        ),
        # Painting works
        "paint_prep": Work(
            code="paint_prep",
            name_pl="Przygotowanie i gruntowanie ścian/sufitów",
            unit="m²",
            labor_rate=Decimal("12.00"),
            hours_per_unit=Decimal("0.10"),
            sequence_order=1,
        ),
        "paint_finish": Work(
            code="paint_finish",
            name_pl="Malowanie ścian i sufitów (2 warstwy)",
            unit="m²",
            labor_rate=Decimal("20.00"),
            hours_per_unit=Decimal("0.18"),
            sequence_order=2,
        ),
        # Laminate works
        "laminate_prep": Work(
            code="laminate_prep",
            name_pl="Odkurzanie i przygotowanie podłoża",
            unit="m²",
            labor_rate=Decimal("8.00"),
            hours_per_unit=Decimal("0.05"),
            sequence_order=1,
        ),
        "laminate_lay": Work(
            code="laminate_lay",
            name_pl="Układanie podkładu i paneli podłogowych",
            unit="m²",
            labor_rate=Decimal("28.00"),
            hours_per_unit=Decimal("0.22"),
            sequence_order=2,
        ),
        "laminate_skirt": Work(
            code="laminate_skirt",
            name_pl="Montaż listew przypodłogowych",
            unit="mb",
            labor_rate=Decimal("14.00"),
            hours_per_unit=Decimal("0.12"),
            sequence_order=3,
        ),
    }
    db.session.add_all(works.values())
    db.session.flush()

    # -------------------------------------------------------------
    # 4. Work Norms
    # -------------------------------------------------------------
    norms = [
        # Bathroom Tiling Norms
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["plytki_podlogowe"].id, qty_per_unit=Decimal("1.10"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["plytki_scienne"].id, qty_per_unit=Decimal("1.10"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["klej_c2"].id, qty_per_unit=Decimal("5.00"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["klej_c2"].id, qty_per_unit=Decimal("5.00"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["fuga"].id, qty_per_unit=Decimal("0.80"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["fuga"].id, qty_per_unit=Decimal("0.80"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["grunt"].id, qty_per_unit=Decimal("0.15"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["grunt"].id, qty_per_unit=Decimal("0.15"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["hydroizolacja"].id, qty_per_unit=Decimal("1.50"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["hydroizolacja"].id, qty_per_unit=Decimal("1.50"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["wylewka"].id, qty_per_unit=Decimal("1.50"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["krzyzyki"].id, qty_per_unit=Decimal("0.25"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["krzyzyki"].id, qty_per_unit=Decimal("0.25"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["silikon"].id, qty_per_unit=Decimal("0.25"), applies_to="perimeter"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["listwa"].id, qty_per_unit=Decimal("0.25"), applies_to="perimeter"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["tasma"].id, qty_per_unit=Decimal("1.00"), applies_to="perimeter"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["folia"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="material", material_id=materials["zaprawa"].id, qty_per_unit=Decimal("2.00"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="work", work_id=works["prep"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="work", work_id=works["prep"].id, qty_per_unit=Decimal("1.00"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="work", work_id=works["hydro"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="work", work_id=works["hydro"].id, qty_per_unit=Decimal("1.00"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="work", work_id=works["tile_floor"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="work", work_id=works["tile_wall"].id, qty_per_unit=Decimal("1.00"), applies_to="wall"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="work", work_id=works["grout"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=tiling_job.id, item_kind="work", work_id=works["grout"].id, qty_per_unit=Decimal("1.00"), applies_to="wall"),

        # Painting Norms
        WorkNorm(job_type_id=painting_job.id, item_kind="material", material_id=materials["grunt_malarski"].id, qty_per_unit=Decimal("0.10"), applies_to="floor"),  # ceiling
        WorkNorm(job_type_id=painting_job.id, item_kind="material", material_id=materials["grunt_malarski"].id, qty_per_unit=Decimal("0.10"), applies_to="wall"),
        WorkNorm(job_type_id=painting_job.id, item_kind="material", material_id=materials["farba_lateksowa"].id, qty_per_unit=Decimal("0.22"), applies_to="floor"),  # ceiling (2 coats)
        WorkNorm(job_type_id=painting_job.id, item_kind="material", material_id=materials["farba_lateksowa"].id, qty_per_unit=Decimal("0.22"), applies_to="wall"),   # walls (2 coats)
        WorkNorm(job_type_id=painting_job.id, item_kind="material", material_id=materials["folia_malarska"].id, qty_per_unit=Decimal("1.20"), applies_to="floor"),
        WorkNorm(job_type_id=painting_job.id, item_kind="work", work_id=works["paint_prep"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=painting_job.id, item_kind="work", work_id=works["paint_prep"].id, qty_per_unit=Decimal("1.00"), applies_to="wall"),
        WorkNorm(job_type_id=painting_job.id, item_kind="work", work_id=works["paint_finish"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=painting_job.id, item_kind="work", work_id=works["paint_finish"].id, qty_per_unit=Decimal("1.00"), applies_to="wall"),

        # Laminate Flooring Norms
        WorkNorm(job_type_id=laminate_job.id, item_kind="material", material_id=materials["panele_podlogowe"].id, qty_per_unit=Decimal("1.05"), applies_to="floor"),
        WorkNorm(job_type_id=laminate_job.id, item_kind="material", material_id=materials["podklad_paneli"].id, qty_per_unit=Decimal("1.02"), applies_to="floor"),
        WorkNorm(job_type_id=laminate_job.id, item_kind="material", material_id=materials["listwy_przypodlogowe"].id, qty_per_unit=Decimal("1.02"), applies_to="perimeter"),
        WorkNorm(job_type_id=laminate_job.id, item_kind="work", work_id=works["laminate_prep"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=laminate_job.id, item_kind="work", work_id=works["laminate_lay"].id, qty_per_unit=Decimal("1.00"), applies_to="floor"),
        WorkNorm(job_type_id=laminate_job.id, item_kind="work", work_id=works["laminate_skirt"].id, qty_per_unit=Decimal("1.00"), applies_to="perimeter"),
    ]
    db.session.add_all(norms)

    # -------------------------------------------------------------
    # 5. Regional Coefficients
    # -------------------------------------------------------------
    db.session.add(
        RegionalCoefficient(
            region_code="pl",
            country="PL",
            coefficient=Decimal("1.0000"),
            name_pl="Polska (stawka bazowa)",
        )
    )
    db.session.commit()
