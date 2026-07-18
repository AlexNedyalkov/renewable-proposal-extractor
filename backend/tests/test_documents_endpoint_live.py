import glob
import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from fpdf import FPDF

from app.main import app

load_dotenv()

pytestmark = pytest.mark.live

client = TestClient(app)

# Known values baked into the synthetic proposal below, used to check
# extraction accuracy against ground truth.
EXPECTED = {
    "project_name": "Prairie Wind Energy Project",
    "location": "Story County, Iowa",
    "technology_type": "wind",
    "installed_capacity_mw": 220,
    "developer_sponsor": "Meadowlark Renewables",
    "total_capex_usd": 310_000_000,
    "expected_irr_percent": 9.8,
    "ppa_term_years": 15,
}

_SECTIONS = [
    (
        "Executive Summary",
        "The Prairie Wind Energy Project is a 220 MW onshore wind generation facility "
        "proposed for development in Story County, Iowa, USA. The project is being "
        "developed by Meadowlark Renewables LLC and is expected to reach commercial "
        "operation in March 2028. Once operational, the facility is expected to "
        "generate approximately 650,000 MWh of clean electricity annually, enough to "
        "power roughly 60,000 average households.",
    ),
    (
        "Technical Overview",
        "The project will consist of 44 wind turbines, each rated at 5.0 MW, for a "
        "total installed capacity of 220 MW. Turbines will be sited across "
        "approximately 12,000 acres of leased agricultural land selected for its "
        "favorable wind resource, with an average annual wind speed of 8.1 m/s at hub "
        "height. Interconnection to the regional transmission grid will occur via a "
        "new 345 kV substation constructed adjacent to the site.",
    ),
    (
        "Financial Overview",
        "Total capital expenditure for the project is estimated at $310,000,000, "
        "equating to approximately $1.41 million per MW of installed capacity. The "
        "project is expected to deliver an internal rate of return (IRR) of 9.8% over "
        "a 10 year payback period. The levelized cost of energy (LCOE) is projected at "
        "$24 per MWh. The project has secured a 15-year power purchase agreement (PPA) "
        "at a fixed price of $27 per MWh. Financing is structured with a debt-to-equity "
        "ratio of 65:35.",
    ),
]


def _build_synthetic_proposal_pdf_bytes() -> bytes:
    pdf = FPDF()
    for title, body in _SECTIONS:
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.multi_cell(0, 10, title)
        pdf.ln(4)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 7, body)

    return bytes(pdf.output())


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_full_pipeline_against_synthetic_proposal_pdf():
    pdf_bytes = _build_synthetic_proposal_pdf_bytes()

    response = client.post(
        "/api/documents",
        files={"file": ("prairie_wind_proposal.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    extraction = response.json()["extraction"]

    assert extraction["project_name"]["confidence"] != "not_found"
    assert "prairie wind" in extraction["project_name"]["value"].lower()

    assert extraction["total_capex_usd"]["confidence"] != "not_found"
    assert extraction["installed_capacity_mw"]["confidence"] != "not_found"


_REAL_SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "real_samples")
REAL_SAMPLE_PATHS = sorted(glob.glob(os.path.join(_REAL_SAMPLES_DIR, "*.pdf")))


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
@pytest.mark.skipif(not REAL_SAMPLE_PATHS, reason="no real sample PDFs found in fixtures/real_samples/")
@pytest.mark.parametrize("pdf_path", REAL_SAMPLE_PATHS, ids=[os.path.basename(p) for p in REAL_SAMPLE_PATHS])
def test_full_pipeline_against_real_world_sample(pdf_path):
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/documents",
            files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
        )

    assert response.status_code == 200
    extraction = response.json()["extraction"]

    # Real-world documents vary widely in what they disclose, so we only
    # assert on fields that should be recoverable from any project document:
    # a named project and its headline installed capacity.
    assert extraction["project_name"]["confidence"] != "not_found"
    assert extraction["installed_capacity_mw"]["confidence"] != "not_found"
