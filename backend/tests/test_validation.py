from app.schemas import ProposalExtraction
from app.validation import normalize_extraction


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


def test_normalize_extraction_preserves_fully_valid_input():
    extraction = normalize_extraction(FULL_VALID_RAW)

    assert isinstance(extraction, ProposalExtraction)
    assert extraction.project_name.value == "Sunridge Solar Farm"
    assert extraction.project_name.confidence == "high"
    assert extraction.total_capex_usd.value == 180_000_000


def test_normalize_extraction_fills_in_missing_fields_as_not_found():
    partial_raw = {
        "project_name": _field("Sunridge Solar Farm"),
        "total_capex_usd": _field(180_000_000),
    }

    extraction = normalize_extraction(partial_raw)

    assert extraction.project_name.value == "Sunridge Solar Farm"
    assert extraction.location.confidence == "not_found"
    assert extraction.location.value is None
    assert extraction.expected_irr_percent.confidence == "not_found"


def test_normalize_extraction_coerces_invalid_confidence_to_not_found():
    raw = dict(FULL_VALID_RAW)
    raw["technology_type"] = _field("solar", confidence="very_sure")

    extraction = normalize_extraction(raw)

    assert extraction.technology_type.confidence == "not_found"
    assert extraction.technology_type.value is None
    # unaffected fields remain untouched
    assert extraction.project_name.value == "Sunridge Solar Farm"


def test_normalize_extraction_coerces_wrong_shaped_field_to_not_found():
    raw = dict(FULL_VALID_RAW)
    raw["installed_capacity_mw"] = "150 MW"  # not a dict at all

    extraction = normalize_extraction(raw)

    assert extraction.installed_capacity_mw.confidence == "not_found"
    assert extraction.installed_capacity_mw.value is None


def test_normalize_extraction_handles_empty_dict_without_raising():
    extraction = normalize_extraction({})

    assert isinstance(extraction, ProposalExtraction)
    assert all(
        getattr(extraction, name).confidence == "not_found"
        for name in ProposalExtraction.model_fields
    )


def test_normalize_extraction_handles_none_without_raising():
    extraction = normalize_extraction(None)

    assert isinstance(extraction, ProposalExtraction)
    assert extraction.project_name.confidence == "not_found"
