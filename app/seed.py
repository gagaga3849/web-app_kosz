from decimal import Decimal

from app.extensions import db
from app.models import JobType, Material, RegionalCoefficient, Work, WorkNorm


def seed_if_empty() -> None:
    if JobType.query.first() is not None:
        ensure_extended_catalog()
        return
    seed()


def ensure_extended_catalog() -> None:
    """Upgrade databases created before the extended work catalog existed."""
    job_specs = {
        "demolition_walls": ("Wyburzanie ścian działowych i skuwanie tynków", "wall", "demolition", "material_demolition"),
        "demolition_floor": ("Skucie starej posadzki i wyniesienie gruzu", "floor", "demolition", "material_demolition"),
        "remove_old_paint": ("Usuwanie starej farby ze ścian i sufitów", "wall", "demolition", "material_demolition"),
        "plastering": ("Tynkowanie i wyrównanie ścian", "wall", "plastering_work", "material_plaster"),
        "drywall_partitions": ("Ścianki działowe i zabudowy z płyt g-k", "wall", "drywall_work", "material_drywall"),
        "concrete_screed": ("Wylewka cementowa i wyrównanie podłogi", "floor", "screed_work", "material_screed"),
        "facade_insulation": ("Ocieplenie elewacji styropianem", "wall", "insulation_work", "material_insulation"),
        "roof_insulation": ("Ocieplenie poddasza wełną mineralną", "floor", "insulation_work", "material_insulation"),
        "window_door_installation": ("Montaż okien i drzwi z obróbką", "floor", "window_work", "material_window"),
        "kitchen_installation": ("Montaż mebli kuchennych i blatu", "floor", "kitchen_work", "material_fixtures"),
        "plumbing_water": ("Instalacja wodna: rury zimnej i ciepłej wody", "floor", "plumbing_work", "material_plumbing"),
        "plumbing_sewer": ("Instalacja kanalizacyjna i podejścia odpływowe", "floor", "plumbing_work", "material_plumbing"),
        "bathroom_fixtures": ("Montaż armatury łazienkowej i ceramiki", "floor", "fixture_work", "material_fixtures"),
        "central_heating": ("Instalacja centralnego ogrzewania i grzejników", "floor", "heating_work", "material_heating"),
        "electrical_installation": ("Nowa instalacja elektryczna w mieszkaniu", "floor", "electrical_work", "material_electrical"),
        "electrical_points": ("Gniazda, włączniki i punkty elektryczne", "floor", "electrical_points_work", "material_electrical_points"),
        "electrical_lighting": ("Montaż oświetlenia, lamp i opraw", "floor", "lighting_work", "material_electrical_lighting"),
        "electrical_panel": ("Rozdzielnica, zabezpieczenia i pomiary elektryczne", "floor", "panel_work", "material_electrical_panel"),
    }
    if all(JobType.query.filter_by(code=code).first() for code in job_specs):
        return

    material_specs = {
        "material_demolition": ("Worki, zabezpieczenia i wywóz gruzu", "m²", "18.00"),
        "material_plaster": ("Tynk i masa wyrównująca", "kg", "2.80"),
        "material_drywall": ("Płyty g-k, profile i wkręty", "m²", "42.00"),
        "material_screed": ("Mieszanka do wylewki", "kg", "1.80"),
        "material_insulation": ("Materiał izolacyjny i klej", "m²", "38.00"),
        "material_window": ("Materiały montażowe do stolarki", "szt", "120.00"),
        "material_plumbing": ("Rury, kształtki i zawory instalacji", "m²", "28.00"),
        "material_fixtures": ("Materiały montażowe armatury", "m²", "22.00"),
        "material_heating": ("Rury, rozdzielacze i uchwyty CO", "m²", "35.00"),
        "material_electrical": ("Przewody, peszle i puszki elektryczne", "m²", "32.00"),
        "material_electrical_points": ("Gniazda i włączniki", "szt", "18.00"),
        "material_electrical_lighting": ("Oprawy i akcesoria oświetleniowe", "szt", "65.00"),
        "material_electrical_panel": ("Aparatura rozdzielcza i oznaczenia", "kpl", "480.00"),
    }
    work_specs = {
        "demolition": ("Demontaż, wyburzenia i wywóz odpadów", "m²", "55.00", "0.45"),
        "plastering_work": ("Wykonanie tynku i zatarcie powierzchni", "m²", "48.00", "0.45"),
        "drywall_work": ("Montaż konstrukcji i płyt g-k", "m²", "75.00", "0.60"),
        "screed_work": ("Wykonanie i zatarcie wylewki", "m²", "42.00", "0.30"),
        "insulation_work": ("Montaż izolacji termicznej", "m²", "65.00", "0.45"),
        "window_work": ("Osadzenie i uszczelnienie stolarki", "szt", "380.00", "2.50"),
        "kitchen_work": ("Montaż i poziomowanie zabudowy", "m²", "95.00", "0.70"),
        "plumbing_work": ("Montaż i próba szczelności instalacji", "m²", "85.00", "0.65"),
        "fixture_work": ("Montaż i podłączenie urządzeń", "szt", "180.00", "1.20"),
        "heating_work": ("Montaż instalacji i grzejników CO", "m²", "95.00", "0.70"),
        "electrical_work": ("Wykonanie bruzd, przewodów i połączeń", "m²", "90.00", "0.70"),
        "electrical_points_work": ("Montaż osprzętu elektrycznego", "szt", "55.00", "0.35"),
        "lighting_work": ("Montaż i podłączenie opraw", "szt", "95.00", "0.65"),
        "panel_work": ("Montaż rozdzielnicy i pomiary", "kpl", "850.00", "5.00"),
    }

    materials = {item.code: item for item in Material.query.all()}
    for code, (name, unit, price) in material_specs.items():
        if code not in materials:
            materials[code] = Material(code=code, name_pl=name, unit=unit, unit_price=Decimal(price))
            db.session.add(materials[code])
    works = {item.code: item for item in Work.query.all()}
    for code, (name, unit, rate, hours) in work_specs.items():
        if code not in works:
            works[code] = Work(code=code, name_pl=name, unit=unit, labor_rate=Decimal(rate), hours_per_unit=Decimal(hours), sequence_order=3)
            db.session.add(works[code])
    db.session.flush()

    for code, (name, applies_to, work_code, material_code) in job_specs.items():
        job = JobType.query.filter_by(code=code).first()
        if job is None:
            job = JobType(code=code, name_pl=name, floor_factor=Decimal("1") if applies_to == "floor" else Decimal("0"), wall_factor=Decimal("2.5") if applies_to == "wall" else Decimal("0"))
            db.session.add(job)
            db.session.flush()
        if not WorkNorm.query.filter_by(job_type_id=job.id).first():
            quantity = Decimal("0.25") if code == "window_door_installation" else Decimal("1.00")
            db.session.add_all([
                WorkNorm(job_type_id=job.id, item_kind="material", material_id=materials[material_code].id, qty_per_unit=quantity, applies_to=applies_to),
                WorkNorm(job_type_id=job.id, item_kind="work", work_id=works[work_code].id, qty_per_unit=quantity, applies_to=applies_to),
            ])
    db.session.commit()


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

    additional_jobs = {
        "demolition_walls": JobType(
            code="demolition_walls",
            name_pl="Wyburzanie ścian działowych i skuwanie tynków",
            floor_factor=Decimal("1"),
            wall_factor=Decimal("2"),
        ),
        "demolition_floor": JobType(
            code="demolition_floor",
            name_pl="Skucie starej posadzki i wyniesienie gruzu",
            floor_factor=Decimal("1"),
        ),
        "remove_old_paint": JobType(
            code="remove_old_paint",
            name_pl="Usuwanie starej farby ze ścian i sufitów",
            floor_factor=Decimal("1"),
            wall_factor=Decimal("2.5"),
        ),
        "plastering": JobType(
            code="plastering",
            name_pl="Tynkowanie i wyrównanie ścian",
            floor_factor=Decimal("0"),
            wall_factor=Decimal("2.5"),
        ),
        "drywall_partitions": JobType(
            code="drywall_partitions",
            name_pl="Ścianki działowe i zabudowy z płyt g-k",
            floor_factor=Decimal("1"),
            wall_factor=Decimal("2"),
        ),
        "concrete_screed": JobType(
            code="concrete_screed",
            name_pl="Wylewka cementowa i wyrównanie podłogi",
            floor_factor=Decimal("1"),
        ),
        "facade_insulation": JobType(
            code="facade_insulation",
            name_pl="Ocieplenie elewacji styropianem",
            floor_factor=Decimal("0"),
            wall_factor=Decimal("2.5"),
        ),
        "roof_insulation": JobType(
            code="roof_insulation",
            name_pl="Ocieplenie poddasza wełną mineralną",
            floor_factor=Decimal("1"),
        ),
        "window_door_installation": JobType(
            code="window_door_installation",
            name_pl="Montaż okien i drzwi z obróbką",
            floor_factor=Decimal("1"),
        ),
        "kitchen_installation": JobType(
            code="kitchen_installation",
            name_pl="Montaż mebli kuchennych i blatu",
            floor_factor=Decimal("1"),
        ),
        "plumbing_water": JobType(
            code="plumbing_water",
            name_pl="Instalacja wodna: rury zimnej i ciepłej wody",
            floor_factor=Decimal("1"),
        ),
        "plumbing_sewer": JobType(
            code="plumbing_sewer",
            name_pl="Instalacja kanalizacyjna i podejścia odpływowe",
            floor_factor=Decimal("1"),
        ),
        "bathroom_fixtures": JobType(
            code="bathroom_fixtures",
            name_pl="Montaż armatury łazienkowej i ceramiki",
            floor_factor=Decimal("1"),
        ),
        "central_heating": JobType(
            code="central_heating",
            name_pl="Instalacja centralnego ogrzewania i grzejników",
            floor_factor=Decimal("1"),
        ),
        "electrical_installation": JobType(
            code="electrical_installation",
            name_pl="Nowa instalacja elektryczna w mieszkaniu",
            floor_factor=Decimal("1"),
        ),
        "electrical_points": JobType(
            code="electrical_points",
            name_pl="Gniazda, włączniki i punkty elektryczne",
            floor_factor=Decimal("1"),
        ),
        "electrical_lighting": JobType(
            code="electrical_lighting",
            name_pl="Montaż oświetlenia, lamp i opraw",
            floor_factor=Decimal("1"),
        ),
        "electrical_panel": JobType(
            code="electrical_panel",
            name_pl="Rozdzielnica, zabezpieczenia i pomiary elektryczne",
            floor_factor=Decimal("1"),
        ),
    }

    db.session.add_all([tiling_job, painting_job, laminate_job, *additional_jobs.values()])
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
    materials.update({
        "material_demolition": Material(code="material_demolition", name_pl="Worki, zabezpieczenia i wywóz gruzu", unit="m²", unit_price=Decimal("18.00")),
        "material_plaster": Material(code="material_plaster", name_pl="Tynk i masa wyrównująca", unit="kg", unit_price=Decimal("2.80")),
        "material_drywall": Material(code="material_drywall", name_pl="Płyty g-k, profile i wkręty", unit="m²", unit_price=Decimal("42.00")),
        "material_screed": Material(code="material_screed", name_pl="Mieszanka do wylewki", unit="kg", unit_price=Decimal("1.80")),
        "material_insulation": Material(code="material_insulation", name_pl="Materiał izolacyjny i klej", unit="m²", unit_price=Decimal("38.00")),
        "material_window": Material(code="material_window", name_pl="Materiały montażowe do stolarki", unit="szt", unit_price=Decimal("120.00")),
        "material_plumbing": Material(code="material_plumbing", name_pl="Rury, kształtki i zawory instalacji", unit="m²", unit_price=Decimal("28.00")),
        "material_fixtures": Material(code="material_fixtures", name_pl="Materiały montażowe armatury", unit="m²", unit_price=Decimal("22.00")),
        "material_heating": Material(code="material_heating", name_pl="Rury, rozdzielacze i uchwyty CO", unit="m²", unit_price=Decimal("35.00")),
        "material_electrical": Material(code="material_electrical", name_pl="Przewody, peszle i puszki elektryczne", unit="m²", unit_price=Decimal("32.00")),
        "material_electrical_points": Material(code="material_electrical_points", name_pl="Gniazda i włączniki", unit="szt", unit_price=Decimal("18.00")),
        "material_electrical_lighting": Material(code="material_electrical_lighting", name_pl="Oprawy i akcesoria oświetleniowe", unit="szt", unit_price=Decimal("65.00")),
        "material_electrical_panel": Material(code="material_electrical_panel", name_pl="Aparatura rozdzielcza i oznaczenia", unit="kpl", unit_price=Decimal("480.00")),
    })
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
    works.update({
        "demolition": Work(code="demolition", name_pl="Demontaż, wyburzenia i wywóz odpadów", unit="m²", labor_rate=Decimal("55.00"), hours_per_unit=Decimal("0.45"), sequence_order=1),
        "surface_repair": Work(code="surface_repair", name_pl="Naprawa i przygotowanie powierzchni", unit="m²", labor_rate=Decimal("32.00"), hours_per_unit=Decimal("0.30"), sequence_order=2),
        "plastering_work": Work(code="plastering_work", name_pl="Wykonanie tynku i zatarcie powierzchni", unit="m²", labor_rate=Decimal("48.00"), hours_per_unit=Decimal("0.45"), sequence_order=3),
        "drywall_work": Work(code="drywall_work", name_pl="Montaż konstrukcji i płyt g-k", unit="m²", labor_rate=Decimal("75.00"), hours_per_unit=Decimal("0.60"), sequence_order=3),
        "screed_work": Work(code="screed_work", name_pl="Wykonanie i zatarcie wylewki", unit="m²", labor_rate=Decimal("42.00"), hours_per_unit=Decimal("0.30"), sequence_order=3),
        "insulation_work": Work(code="insulation_work", name_pl="Montaż izolacji termicznej", unit="m²", labor_rate=Decimal("65.00"), hours_per_unit=Decimal("0.45"), sequence_order=3),
        "window_work": Work(code="window_work", name_pl="Osadzenie i uszczelnienie stolarki", unit="szt", labor_rate=Decimal("380.00"), hours_per_unit=Decimal("2.50"), sequence_order=3),
        "kitchen_work": Work(code="kitchen_work", name_pl="Montaż i poziomowanie zabudowy", unit="m²", labor_rate=Decimal("95.00"), hours_per_unit=Decimal("0.70"), sequence_order=3),
        "plumbing_work": Work(code="plumbing_work", name_pl="Montaż i próba szczelności instalacji", unit="m²", labor_rate=Decimal("85.00"), hours_per_unit=Decimal("0.65"), sequence_order=3),
        "fixture_work": Work(code="fixture_work", name_pl="Montaż i podłączenie urządzeń", unit="szt", labor_rate=Decimal("180.00"), hours_per_unit=Decimal("1.20"), sequence_order=3),
        "heating_work": Work(code="heating_work", name_pl="Montaż instalacji i grzejników CO", unit="m²", labor_rate=Decimal("95.00"), hours_per_unit=Decimal("0.70"), sequence_order=3),
        "electrical_work": Work(code="electrical_work", name_pl="Wykonanie bruzd, przewodów i połączeń", unit="m²", labor_rate=Decimal("90.00"), hours_per_unit=Decimal("0.70"), sequence_order=3),
        "electrical_points_work": Work(code="electrical_points_work", name_pl="Montaż osprzętu elektrycznego", unit="szt", labor_rate=Decimal("55.00"), hours_per_unit=Decimal("0.35"), sequence_order=3),
        "lighting_work": Work(code="lighting_work", name_pl="Montaż i podłączenie opraw", unit="szt", labor_rate=Decimal("95.00"), hours_per_unit=Decimal("0.65"), sequence_order=3),
        "panel_work": Work(code="panel_work", name_pl="Montaż rozdzielnicy i pomiary", unit="kpl", labor_rate=Decimal("850.00"), hours_per_unit=Decimal("5.00"), sequence_order=3),
    })
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

    additional_norms = {
        "demolition_walls": ("material_demolition", "demolition", "wall"),
        "demolition_floor": ("material_demolition", "demolition", "floor"),
        "remove_old_paint": ("material_demolition", "demolition", "wall"),
        "plastering": ("material_plaster", "plastering_work", "wall"),
        "drywall_partitions": ("material_drywall", "drywall_work", "wall"),
        "concrete_screed": ("material_screed", "screed_work", "floor"),
        "facade_insulation": ("material_insulation", "insulation_work", "wall"),
        "roof_insulation": ("material_insulation", "insulation_work", "floor"),
        "window_door_installation": ("material_window", "window_work", "floor"),
        "kitchen_installation": ("material_fixtures", "kitchen_work", "floor"),
        "plumbing_water": ("material_plumbing", "plumbing_work", "floor"),
        "plumbing_sewer": ("material_plumbing", "plumbing_work", "floor"),
        "bathroom_fixtures": ("material_fixtures", "fixture_work", "floor"),
        "central_heating": ("material_heating", "heating_work", "floor"),
        "electrical_installation": ("material_electrical", "electrical_work", "floor"),
        "electrical_points": ("material_electrical_points", "electrical_points_work", "floor"),
        "electrical_lighting": ("material_electrical_lighting", "lighting_work", "floor"),
        "electrical_panel": ("material_electrical_panel", "panel_work", "floor"),
    }
    for job_code, (material_code, work_code, applies_to) in additional_norms.items():
        job = additional_jobs[job_code]
        material_quantity = Decimal("1.00") if material_code != "material_window" else Decimal("0.25")
        work_quantity = Decimal("1.00") if work_code != "window_work" else Decimal("0.25")
        norms.extend([
            WorkNorm(
                job_type_id=job.id,
                item_kind="material",
                material_id=materials[material_code].id,
                qty_per_unit=material_quantity,
                applies_to=applies_to,
            ),
            WorkNorm(
                job_type_id=job.id,
                item_kind="work",
                work_id=works[work_code].id,
                qty_per_unit=work_quantity,
                applies_to=applies_to,
            ),
        ])
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
