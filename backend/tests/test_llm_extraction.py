import logging
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


def test_run_extraction_omits_temperature_and_uses_system_prompt():
    tool_use_block = SimpleNamespace(type="tool_use", name=EXTRACTION_TOOL_NAME, input=SAMPLE_TOOL_INPUT)
    client = FakeClient([tool_use_block])

    run_extraction("unique-document-marker-xyz", client=client)

    kwargs = client.messages.last_kwargs
    # claude-sonnet-5 deprecated `temperature` — sending it is a 400 error, so
    # we must NOT pass it. (A mock can't catch this; only a real call can — which
    # is how the eval found it. This guards against a regression.)
    assert "temperature" not in kwargs
    # Behavioral rules go in the system message...
    assert "investment analyst" in kwargs["system"]
    # ...and the untrusted document stays out of it (user turn only).
    assert "unique-document-marker-xyz" not in kwargs["system"]


def test_tool_schema_reasons_before_extracting():
    # The wrapper puts `reasoning` first so the model does chain-of-thought
    # before committing to values (JSON is generated top-to-bottom).
    tool_use_block = SimpleNamespace(
        type="tool_use",
        name=EXTRACTION_TOOL_NAME,
        input={"reasoning": "r", "extraction": SAMPLE_TOOL_INPUT},
    )
    client = FakeClient([tool_use_block])

    run_extraction("doc text", client=client)

    schema = client.messages.last_kwargs["tools"][0]["input_schema"]
    props = list(schema["properties"].keys())
    assert props[0] == "reasoning"
    assert "extraction" in props
    assert "reasoning" in schema["required"]


def test_run_extraction_unwraps_reasoning_and_returns_extraction():
    wrapped = {
        "reasoning": "14% is return on equity, not the project IRR.",
        "extraction": SAMPLE_TOOL_INPUT,
    }
    tool_use_block = SimpleNamespace(type="tool_use", name=EXTRACTION_TOOL_NAME, input=wrapped)
    client = FakeClient([tool_use_block])

    result = run_extraction("doc text", client=client)

    assert result == SAMPLE_TOOL_INPUT  # reasoning stripped from the return
    ProposalExtraction(**result)


def test_run_extraction_logs_reasoning_for_observability(caplog):
    wrapped = {
        "reasoning": "debt is stated as a 2.33x leverage ratio, not a percentage.",
        "extraction": SAMPLE_TOOL_INPUT,
    }
    tool_use_block = SimpleNamespace(type="tool_use", name=EXTRACTION_TOOL_NAME, input=wrapped)
    client = FakeClient([tool_use_block])

    with caplog.at_level(logging.INFO):
        run_extraction("doc text", client=client)

    assert "2.33x leverage ratio" in caplog.text


def test_system_prompt_includes_few_shot_reasoning_examples():
    tool_use_block = SimpleNamespace(
        type="tool_use",
        name=EXTRACTION_TOOL_NAME,
        input={"reasoning": "r", "extraction": SAMPLE_TOOL_INPUT},
    )
    client = FakeClient([tool_use_block])

    run_extraction("doc text", client=client)

    system = client.messages.last_kwargs["system"]
    assert "<examples>" in system
    # a confident-extraction example and an ambiguous one both present
    assert "solar PV" in system
    assert "return ON EQUITY" in system


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
