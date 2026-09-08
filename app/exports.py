from __future__ import annotations

from io import BytesIO
from pathlib import Path


def _rows(estimate: dict) -> list[list[str]]:
    rows = [["Materiały"], ["Pozycja", "Ilość", "J.m.", "Cena jedn.", "Wartość"]]
    for item in estimate["materials"]:
        rows.append([
            item["name"], item["quantity"], item["unit"],
            f'{item["unit_price"]} {item["currency"]}',
            f'{item["total"]} {item["currency"]}',
        ])
    rows.extend([["Robocizna"], ["Pozycja", "Ilość", "J.m.", "Cena jedn.", "Wartość"]])
    for item in estimate["works"]:
        rows.append([
            item["name"], item["quantity"], item["unit"],
            f'{item["unit_price"]} {item["currency"]}',
            f'{item["total"]} {item["currency"]}',
        ])
    rows.extend([
        [], ["Materiały razem", f'{estimate["materials_total"]} {estimate["currency"]}'],
        ["Robocizna razem", f'{estimate["works_total"]} {estimate["currency"]}'],
        ["Razem", f'{estimate["total_price"]} {estimate["currency"]}'],
        ["Szacowany czas", f'{estimate["estimated_duration_days"]} dni roboczych'],
    ])
    return rows


def _heading_lines(estimate: dict) -> list[str]:
    return [
        estimate["job_name"],
        f'Powierzchnia: {estimate["area_m2"]} m² | Region: {estimate["region"]}',
        (
            "Wymiary: "
            f'podłoga {estimate["dimensions"]["floor_m2"]} m², '
            f'ściany {estimate["dimensions"]["wall_m2"]} m², '
            f'obwód {estimate["dimensions"]["perimeter_m"]} m'
        ),
    ]


def _register_pdf_font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_name = "EstimateUnicode"
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    )
    font_path = next((path for path in candidates if Path(path).is_file()), None)
    if font_path is None:
        raise RuntimeError("Brak czcionki Unicode wymaganej do eksportu PDF.")
    pdfmetrics.registerFont(TTFont(font_name, font_path))
    return font_name


def make_xls(estimate: dict) -> BytesIO:
    import xlwt

    workbook = xlwt.Workbook(encoding="utf-8")
    sheet = workbook.add_sheet("Kosztorys")
    title_style = xlwt.easyxf("font: bold on, height 280")
    heading_style = xlwt.easyxf("font: bold on")
    sheet.write(0, 0, "KOSZTORYS", title_style)
    sheet.write(0, 1, estimate["job_name"], title_style)
    sheet.write(1, 0, "Region")
    sheet.write(1, 1, estimate["region"])
    sheet.write(2, 0, "Powierzchnia")
    sheet.write(2, 1, f'{estimate["area_m2"]} m²')
    for row_index, row in enumerate(_rows(estimate), start=4):
        for column_index, value in enumerate(row):
            style = heading_style if row and row[0] in {"Materiały", "Robocizna", "Pozycja", "Razem"} else xlwt.easyxf()
            sheet.write(row_index, column_index, value, style)
    for column_index, width in enumerate((52, 18, 12, 18, 20)):
        sheet.col(column_index).width = width * 256
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def make_docx(estimate: dict) -> BytesIO:
    from docx import Document

    document = Document()
    document.add_heading("Kosztorys", level=0)
    for index, line in enumerate(_heading_lines(estimate)):
        if index == 0:
            document.add_heading(line, level=1)
        else:
            document.add_paragraph(line)
    document.add_heading("Kolejność prac", level=2)
    for step in estimate["sequence"]:
        document.add_paragraph(step["name"], style="List Number")

    for title, items in (("Materiały", estimate["materials"]), ("Robocizna", estimate["works"])):
        document.add_heading(title, level=2)
        table = document.add_table(rows=1, cols=5)
        table.style = "Table Grid"
        for cell, value in zip(table.rows[0].cells, ["Pozycja", "Ilość", "J.m.", "Cena jedn.", "Wartość"]):
            cell.text = value
        for item in items:
            cells = table.add_row().cells
            values = [
                item["name"], item["quantity"], item["unit"],
                f'{item["unit_price"]} {item["currency"]}',
                f'{item["total"]} {item["currency"]}',
            ]
            for cell, value in zip(cells, values):
                cell.text = value

    document.add_heading("Podsumowanie", level=2)
    document.add_paragraph(f'Materiały razem: {estimate["materials_total"]} {estimate["currency"]}')
    document.add_paragraph(f'Robocizna razem: {estimate["works_total"]} {estimate["currency"]}')
    document.add_paragraph(f'Razem: {estimate["total_price"]} {estimate["currency"]}')
    document.add_paragraph(f'Szacowany czas: {estimate["estimated_duration_days"]} dni roboczych')
    output = BytesIO()
    document.save(output)
    output.seek(0)
    return output


def make_pdf(estimate: dict) -> BytesIO:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font_name = _register_pdf_font()
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm)
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = font_name
    story = [Paragraph("Kosztorys", styles["Title"])]
    for line in _heading_lines(estimate):
        story.append(Paragraph(line, styles["Heading2"] if line == estimate["job_name"] else styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Kolejność prac", styles["Heading2"]))
    for index, step in enumerate(estimate["sequence"], start=1):
        story.append(Paragraph(f"{index}. {step['name']}", styles["Normal"]))
    for title, items in (("Materiały", estimate["materials"]), ("Robocizna", estimate["works"])):
        story.append(Paragraph(title, styles["Heading2"]))
        data = [["Pozycja", "Ilość", "J.m.", "Cena jedn.", "Wartość"]]
        data.extend([
            [item["name"], item["quantity"], item["unit"], f'{item["unit_price"]} {item["currency"]}', f'{item["total"]} {item["currency"]}']
            for item in items
        ])
        table = Table(data, repeatRows=1, colWidths=[75 * mm, 22 * mm, 18 * mm, 30 * mm, 30 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3e8dc")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d6d3d1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
        ]))
        story.extend([table, Spacer(1, 8)])
    story.append(Paragraph(
        f'Materiały razem: {estimate["materials_total"]} {estimate["currency"]} | '
        f'Robocizna razem: {estimate["works_total"]} {estimate["currency"]} | '
        f'Razem: {estimate["total_price"]} {estimate["currency"]} | '
        f'Szacowany czas: {estimate["estimated_duration_days"]} dni',
        styles["Heading2"],
    ))
    document.build(story)
    output.seek(0)
    return output