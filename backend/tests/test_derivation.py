from app.derivation import derive_fields
from app.schemas import ProposalExtraction


def _extraction(**overrides):
    """A ProposalExtraction with every field not_found, then apply overrides."""
    base = {
        name: {"value": None, "confidence": "not_found", "source_snippet": None}
        for name in ProposalExtraction.model_fields
    }
    base.update(overrides)
    return ProposalExtraction(**base)


def test_derives_capex_per_mw_when_not_found_and_inputs_present():
    extraction = _extraction(
        total_capex_usd={"value": 13_300_000, "confidence": "high", "source_snippet": "total cost USD 13.3M"},
        installed_capacity_mw={"value": 10, "confidence": "high", "source_snippet": "10 MW plant"},
    )

    result = derive_fields(extraction).capex_per_mw

    assert result.value == 1_330_000
    assert result.confidence == "high"
    # provenance names the operation AND carries both input snippets
    assert "derived" in result.source_snippet
    assert "13.3M" in result.source_snippet
    assert "10 MW" in result.source_snippet


def test_confidence_is_the_weaker_of_the_two_inputs():
    extraction = _extraction(
        total_capex_usd={"value": 100, "confidence": "high", "source_snippet": None},
        installed_capacity_mw={"value": 10, "confidence": "medium", "source_snippet": None},
    )

    assert derive_fields(extraction).capex_per_mw.confidence == "medium"


def test_does_not_override_a_stated_capex_per_mw():
    extraction = _extraction(
        capex_per_mw={"value": 999, "confidence": "high", "source_snippet": "stated USD 999/MW"},
        total_capex_usd={"value": 100, "confidence": "high", "source_snippet": None},
        installed_capacity_mw={"value": 10, "confidence": "high", "source_snippet": None},
    )

    # a stated value wins — it is NOT overwritten by the derived 10
    assert derive_fields(extraction).capex_per_mw.value == 999


def test_skips_when_an_input_is_missing():
    extraction = _extraction(
        total_capex_usd={"value": 100, "confidence": "high", "source_snippet": None},
        # installed_capacity_mw left not_found (value is None)
    )

    assert derive_fields(extraction).capex_per_mw.confidence == "not_found"


def test_guards_against_zero_capacity():
    extraction = _extraction(
        total_capex_usd={"value": 100, "confidence": "high", "source_snippet": None},
        installed_capacity_mw={"value": 0, "confidence": "high", "source_snippet": "0 MW"},
    )

    # no ZeroDivisionError, and nothing derived
    assert derive_fields(extraction).capex_per_mw.confidence == "not_found"
