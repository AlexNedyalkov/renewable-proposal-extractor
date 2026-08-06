"""Fill fields that are computed from other fields, in deterministic code.

The LLM extracts what the document *states*; anything that needs arithmetic is
computed here, where math is exact (an LLM is a next-token predictor, not a
calculator). Faithful extraction always wins — we only derive a field the model
left as ``not_found``.

Currently derives one field:
    capex_per_mw = total_capex_usd / installed_capacity_mw
"""

from typing import Any

from app.schemas import ExtractedField, ProposalExtraction

_CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1, "not_found": 0}


def _is_number(value: Any) -> bool:
    # A field's value can be None (not_found) or even a string; only real numbers
    # can be divided. bool is a subclass of int in Python, so exclude it explicitly.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _weaker(a: str, b: str) -> str:
    # A computed value is only as trustworthy as its least-certain input.
    return a if _CONFIDENCE_RANK[a] <= _CONFIDENCE_RANK[b] else b


def derive_fields(extraction: ProposalExtraction) -> ProposalExtraction:
    capex = extraction.capex_per_mw
    total = extraction.total_capex_usd
    capacity = extraction.installed_capacity_mw

    if (
        capex.confidence == "not_found"          # don't overwrite a stated value
        and _is_number(total.value)
        and _is_number(capacity.value)
        and capacity.value > 0                    # never divide by zero
    ):
        extraction.capex_per_mw = ExtractedField(
            value=total.value / capacity.value,
            confidence=_weaker(total.confidence, capacity.confidence),
            source_snippet=(
                "derived = total_capex_usd / installed_capacity_mw. "
                f"total_capex_usd from: {total.source_snippet or 'n/a'} | "
                f"installed_capacity_mw from: {capacity.source_snippet or 'n/a'}"
            ),
        )

    return extraction
