import pytest
from fpdf import FPDF


@pytest.fixture
def multipage_text_pdf(tmp_path):
    pdf = FPDF()
    for page_text in ("Page one: Sunridge Solar Farm proposal.", "Page two: total capex $180,000,000."):
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(text=page_text)

    path = tmp_path / "multipage.pdf"
    pdf.output(str(path))
    return path


@pytest.fixture
def blank_no_text_pdf(tmp_path):
    pdf = FPDF()
    pdf.add_page()

    path = tmp_path / "blank.pdf"
    pdf.output(str(path))
    return path
