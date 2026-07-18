from typing import Any, Optional

import anthropic

from app.schemas import ProposalExtraction

MODEL = "claude-sonnet-5"
EXTRACTION_TOOL_NAME = "record_proposal_extraction"

_TOOL_DESCRIPTION = (
    "Record structured financial and technical data extracted from a renewable "
    "energy project proposal document. For every field, set confidence to "
    "'not_found' and value to null if the information is not present in the "
    "document rather than guessing."
)


class ExtractionError(Exception):
    pass


def _build_prompt(document_text: str) -> str:
    return (
        "You are analyzing a renewable energy project proposal document for an "
        "investment analyst. Extract the technical and financial data points "
        "defined by the record_proposal_extraction tool. For each field, provide "
        "a confidence level and, when found, a short verbatim snippet from the "
        "document supporting the extracted value. Do not fabricate values that "
        "are not present in the document.\n\n"
        f"--- DOCUMENT TEXT ---\n{document_text}"
    )


def run_extraction(document_text: str, client: Optional[Any] = None) -> dict:
    client = client or anthropic.Anthropic()
    schema = ProposalExtraction.model_json_schema()

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=[
                {
                    "name": EXTRACTION_TOOL_NAME,
                    "description": _TOOL_DESCRIPTION,
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": EXTRACTION_TOOL_NAME},
            messages=[{"role": "user", "content": _build_prompt(document_text)}],
        )
    except Exception as exc:
        raise ExtractionError(f"Claude API call failed: {exc}") from exc

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    raise ExtractionError("Claude response did not include a tool_use block")
