from typing import Any, Literal, Optional

from pydantic import BaseModel

Confidence = Literal["high", "medium", "low", "not_found"]


class ExtractedField(BaseModel):
    value: Optional[Any] = None
    confidence: Confidence
    source_snippet: Optional[str] = None


class ProposalExtraction(BaseModel):
    # Technical
    project_name: ExtractedField
    location: ExtractedField
    technology_type: ExtractedField
    installed_capacity_mw: ExtractedField
    expected_annual_generation_mwh: ExtractedField
    commercial_operation_date: ExtractedField
    developer_sponsor: ExtractedField

    # Financial
    total_capex_usd: ExtractedField
    capex_per_mw: ExtractedField
    expected_irr_percent: ExtractedField
    payback_period_years: ExtractedField
    lcoe_usd_per_mwh: ExtractedField
    ppa_price_usd_per_mwh: ExtractedField
    ppa_term_years: ExtractedField
    debt_equity_ratio: ExtractedField
