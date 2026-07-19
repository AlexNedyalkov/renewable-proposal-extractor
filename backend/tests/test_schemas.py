import pytest
from pydantic import ValidationError

from app.schemas import ExtractedField, ProposalExtraction


def test_extracted_field_accepts_valid_confidence_levels():
    field = ExtractedField(value=42.5, confidence="high", source_snippet="42.5 MW")

    assert field.value == 42.5
    assert field.confidence == "high"
    assert field.source_snippet == "42.5 MW"


def test_extracted_field_allows_missing_value_and_snippet():
    field = ExtractedField(value=None, confidence="not_found")

    assert field.value is None
    assert field.source_snippet is None


def test_extracted_field_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        ExtractedField(value=1, confidence="very_sure")


def _sample_field(value, snippet):
    return ExtractedField(value=value, confidence="high", source_snippet=snippet)


def test_proposal_extraction_validates_full_sample_dict():
    sample = {
        "project_name": _sample_field("Sunridge Solar Farm", "Sunridge Solar Farm"),
        "location": _sample_field("Nevada, USA", "located in Nevada, USA"),
        "technology_type": _sample_field("solar", "photovoltaic solar"),
        "installed_capacity_mw": _sample_field(150.0, "150 MW installed capacity"),
        "expected_annual_generation_mwh": _sample_field(320000, "320,000 MWh/year"),
        "commercial_operation_date": _sample_field("2027-06-01", "COD of June 2027"),
        "developer_sponsor": _sample_field("Helios Development LLC", "developed by Helios Development LLC"),
        "total_capex_usd": _sample_field(180_000_000, "$180,000,000 total capex"),
        "capex_per_mw": _sample_field(1_200_000, "$1.2M per MW"),
        "expected_irr_percent": _sample_field(11.5, "11.5% IRR"),
        "payback_period_years": _sample_field(8, "8 year payback"),
        "lcoe_usd_per_mwh": _sample_field(28.0, "$28/MWh LCOE"),
        "ppa_price_usd_per_mwh": _sample_field(32.0, "$32/MWh PPA price"),
        "ppa_term_years": _sample_field(20, "20-year PPA"),
        "debt_percent": _sample_field(70.0, "70% debt"),
        "equity_percent": _sample_field(30.0, "30% equity"),
    }

    extraction = ProposalExtraction(**sample)

    assert extraction.project_name.value == "Sunridge Solar Farm"
    assert extraction.expected_irr_percent.confidence == "high"


def test_proposal_extraction_requires_every_field():
    with pytest.raises(ValidationError):
        ProposalExtraction(project_name=_sample_field("Sunridge Solar Farm", None))
