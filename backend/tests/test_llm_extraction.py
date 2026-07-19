from types import SimpleNamespace

import pytest

from app.llm_extraction import EXTRACTION_TOOL_NAME, ExtractionError, run_extraction
from app.schemas import ProposalExtraction


class FakeMessages:
    def __init__(self, response_content):
        self._response_content = response_content
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(content=self._response_content)


class FakeClient:
    def __init__(self, response_content):
        self.messages = FakeMessages(response_content)


def _field(value, confidence="high", snippet=None):
    return {"value": value, "confidence": confidence, "source_snippet": snippet}


SAMPLE_TOOL_INPUT = {
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
    "debt_percent": _field(70.0),
    "equity_percent": _field(30.0),
}


def test_run_extraction_returns_tool_input_dict_shaped_like_schema():
    tool_use_block = SimpleNamespace(type="tool_use", name=EXTRACTION_TOOL_NAME, input=SAMPLE_TOOL_INPUT)
    client = FakeClient([tool_use_block])

    result = run_extraction("some document text", client=client)

    assert result == SAMPLE_TOOL_INPUT
    ProposalExtraction(**result)


def test_run_extraction_forces_tool_choice_and_sends_document_text():
    tool_use_block = SimpleNamespace(type="tool_use", name=EXTRACTION_TOOL_NAME, input=SAMPLE_TOOL_INPUT)
    client = FakeClient([tool_use_block])

    run_extraction("unique-document-marker-xyz", client=client)

    kwargs = client.messages.last_kwargs
    assert kwargs["tool_choice"] == {"type": "tool", "name": EXTRACTION_TOOL_NAME}
    assert kwargs["tools"][0]["name"] == EXTRACTION_TOOL_NAME
    assert "unique-document-marker-xyz" in kwargs["messages"][0]["content"]


def test_run_extraction_raises_when_no_tool_use_block_returned():
    text_block = SimpleNamespace(type="text", text="I could not process this document.")
    client = FakeClient([text_block])

    with pytest.raises(ExtractionError):
        run_extraction("doc text", client=client)


class BoomingMessages:
    def create(self, **kwargs):
        raise RuntimeError("simulated network failure calling Anthropic API")


class BoomingClient:
    def __init__(self):
        self.messages = BoomingMessages()


def test_run_extraction_wraps_client_errors_as_extraction_error():
    with pytest.raises(ExtractionError):
        run_extraction("doc text", client=BoomingClient())
