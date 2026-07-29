from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Confidence = Literal["high", "medium", "low", "not_found"]


class ExtractedField(BaseModel):
    value: Optional[Any] = None
    confidence: Confidence
    source_snippet: Optional[str] = None


class ProposalExtraction(BaseModel):
    # Technical
    project_name: ExtractedField = Field(
        description=(
            "The official name of the renewable energy project itself (e.g. "
            "'Sunridge Solar Farm') — not the developer, sponsor, or lender."
        )
    )
    location: ExtractedField = Field(
        description=(
            "The geographic location of the project — country, plus region / "
            "province / site if stated."
        )
    )
    technology_type: ExtractedField = Field(
        description=(
            "The generation technology — e.g. solar PV, onshore wind, offshore "
            "wind, concentrated solar (CSP), hydro."
        )
    )
    installed_capacity_mw: ExtractedField = Field(
        description=(
            "Installed / nameplate generation capacity, in megawatts (MW). "
            "Convert from GW if needed (x1000). Not annual energy generation."
        )
    )
    expected_annual_generation_mwh: ExtractedField = Field(
        description=(
            "Expected annual electricity generation, in megawatt-hours (MWh). "
            "Convert from GWh if needed (x1000). Not the installed capacity."
        )
    )
    commercial_operation_date: ExtractedField = Field(
        description=(
            "The commercial operation date (COD) — when the project began or is "
            "expected to begin operating. Prefer the actual date over the "
            "scheduled/expected date if both are given."
        )
    )
    developer_sponsor: ExtractedField = Field(
        description=(
            "The company or entity developing / sponsoring the project. Not the "
            "lender, the offtaker, or the project name."
        )
    )

    # Financial
    total_capex_usd: ExtractedField = Field(
        description=(
            "Total capital expenditure / total project cost, in US dollars. "
            "Prefer the actual/final figure over the estimate if both are given."
        )
    )
    capex_per_mw: ExtractedField = Field(
        description=(
            "Capital cost per megawatt of installed capacity, in USD per MW. "
            "Only if stated directly in the document."
        )
    )
    expected_irr_percent: ExtractedField = Field(
        description=(
            "The project's overall internal rate of return (IRR), as a percentage. "
            "Project-level financial IRR only — NOT 'return on equity', 'economic "
            "IRR', or weighted average cost of capital, which are related but "
            "distinct metrics."
        )
    )
    payback_period_years: ExtractedField = Field(
        description=(
            "The payback period — number of years to recover the initial "
            "investment."
        )
    )
    lcoe_usd_per_mwh: ExtractedField = Field(
        description=(
            "Levelized cost of energy (LCOE), in USD per MWh. Convert from $/kWh "
            "if needed (x1000). A cost — not the PPA sale price."
        )
    )
    ppa_price_usd_per_mwh: ExtractedField = Field(
        description=(
            "The power purchase agreement (PPA) price / tariff at which power is "
            "sold, in USD per MWh. Convert from $/kWh if needed (x1000). A sale "
            "price — not the LCOE cost."
        )
    )
    ppa_term_years: ExtractedField = Field(
        description=(
            "The duration of the power purchase agreement (PPA), in years. Not "
            "the loan tenor."
        )
    )
    debt_percent: ExtractedField = Field(
        description=(
            "Debt as a percentage of the total project cost, from the capital "
            "structure / sources-of-funds breakdown. Measured in %. NOT the "
            "debt-to-equity leverage ratio expressed as a multiple like 2.9x."
        )
    )
    equity_percent: ExtractedField = Field(
        description=(
            "Equity as a percentage of the total project cost, from the capital "
            "structure / sources-of-funds breakdown. Measured in %. NOT an "
            "equity-to-debt ratio or leverage multiple."
        )
    )
