from fastapi.testclient import TestClient
from fpdf import FPDF

from app.main import app
from app.schemas import ProposalExtraction

client = TestClient(app)


def _field(value, confidence="high", snippet=None):
    return {"value": value, "confidence": confidence, "source_snippet": snippet}


FULL_VALID_RAW = {
    "project_name": _field("Sunridge Solar Farm", snippet="Sunridge Solar Farm"),
    "location": _field("Nevada, USA"),
    "technology_type": _field("solar"),
    "installed_capacity_mw": _field(150.0),
    "expected_annual_generation_mwh": _field(320000),
    "commercial_operation_date": _field("2027-06-01"),
    "developer_sponsor": _field("Helios Development LLC"),
    "total_capex_usd": _field(180_000_000),
    "capex_per_mw": _field(1_200_000),
    "expected_irr_percent": _field(11.5),
    "payback_period_years": _field(8),
    "lcoe_usd_per_mwh": _field(28.0),
    "ppa_price_usd_per_mwh": _field(32.0),
    "ppa_term_years": _field(20),
    "debt_equity_ratio": _field("70:30"),
}


def _make_pdf_bytes(text="Sunridge Solar Farm proposal."):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text=text)
    return bytes(pdf.output())


def _make_blank_pdf_bytes():
    pdf = FPDF()
    pdf.add_page()
    return bytes(pdf.output())


def test_upload_valid_pdf_returns_document_id_and_extraction(monkeypatch):
    monkeypatch.setattr("app.routes.documents.run_extraction", lambda text: FULL_VALID_RAW)

    response = client.post(
        "/api/documents",
        files={"file": ("proposal.pdf", _make_pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert "document_id" in body and body["document_id"]
    assert body["extraction"]["project_name"]["value"] == "Sunridge Solar Farm"
    ProposalExtraction(**body["extraction"])  # round-trips through the schema


def test_upload_rejects_non_pdf_bytes_even_with_pdf_content_type():
    response = client.post(
        "/api/documents",
        files={"file": ("fake.pdf", b"not actually a pdf file", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "invalid_file_type"


def test_upload_rejects_file_exceeding_size_limit(monkeypatch):
    monkeypatch.setattr("app.routes.documents.MAX_FILE_SIZE_BYTES", 10)

    response = client.post(
        "/api/documents",
        files={"file": ("proposal.pdf", _make_pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "file_too_large"


def test_upload_rejects_pdf_with_no_extractable_text():
    response = client.post(
        "/api/documents",
        files={"file": ("blank.pdf", _make_blank_pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "no_extractable_text"
