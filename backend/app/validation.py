from typing import Any

from pydantic import ValidationError

from app.schemas import ExtractedField, ProposalExtraction

_NOT_FOUND = {"value": None, "confidence": "not_found", "source_snippet": None}


def _normalize_field(raw_field: Any) -> ExtractedField:
    if not isinstance(raw_field, dict):
        return ExtractedField(**_NOT_FOUND)

    try:
        return ExtractedField(**raw_field)
    except (ValidationError, TypeError):
        return ExtractedField(**_NOT_FOUND)


def normalize_extraction(raw_dict: Any) -> ProposalExtraction:
    if not isinstance(raw_dict, dict):
        raw_dict = {}

    normalized = {
        field_name: _normalize_field(raw_dict.get(field_name))
        for field_name in ProposalExtraction.model_fields
    }

    return ProposalExtraction(**normalized)
