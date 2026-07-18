import os

import pytest
from dotenv import load_dotenv

from app.llm_extraction import run_extraction
from app.schemas import ProposalExtraction

load_dotenv()

pytestmark = pytest.mark.live

SAMPLE_PROPOSAL_TEXT = """
Project Proposal: Sunridge Solar Farm

Sunridge Solar Farm is a 150 MW photovoltaic solar project located in Nevada,
USA. Total capital expenditure is estimated at $180,000,000. The project is
developed by Helios Development LLC, with commercial operation expected in
June 2027.
"""


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_run_extraction_against_real_anthropic_api():
    result = run_extraction(SAMPLE_PROPOSAL_TEXT)

    extraction = ProposalExtraction(**result)

    assert extraction.project_name.confidence != "not_found"
    assert "sunridge" in (extraction.project_name.value or "").lower()
    assert extraction.total_capex_usd.confidence != "not_found"
