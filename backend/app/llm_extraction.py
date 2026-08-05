import logging
from typing import Any, Optional

import anthropic
from pydantic import BaseModel, Field

from app.schemas import ProposalExtraction

logger = logging.getLogger(__name__)

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


# Persistent behavioral rules live in the system message — Claude weights it
# most strongly, and it keeps our instructions separate from the (untrusted)
# document, which goes in the user turn.
_SYSTEM_PROMPT = (
    "<role>\n"
    "You are analyzing a renewable energy project proposal document on behalf "
    "of an investment analyst.\n"
    "</role>\n\n"
    "<task>\n"
    "Extract the technical and financial data points defined by the "
    "record_proposal_extraction tool. For each field, provide a confidence "
    "level and, when the value is found, a short verbatim snippet from the "
    "document supporting it.\n"
    "</task>\n\n"
    "<instructions>\n"
    "- Base every value only on the text inside the <document> tags in the user "
    "message.\n"
    "- If a value is not present in the document, set its confidence to "
    "'not_found' and leave the value null — do not guess or fabricate.\n"
    "</instructions>"
)


def _build_user_content(document_text: str) -> str:
    return f"<document>\n{document_text}\n</document>"


class _ReasonedExtraction(BaseModel):
    """Wrapper used *only* to build the tool schema, so the model reasons
    before it commits to values.

    Chain-of-thought is normally free text emitted before the answer — but our
    forced tool_choice sends the model straight into the structured tool call,
    with no room to think first. Declaring ``reasoning`` *before* ``extraction``
    restores it: JSON is generated top-to-bottom, so the model fills
    ``reasoning`` first. It is scratch paper — it improves the values, then we
    log it for observability and return only the extraction.
    """

    reasoning: str = Field(
        description=(
            "Scratch paper. Think step by step here BEFORE filling in the "
            "extraction below. Work through any ambiguous or easily-confused "
            "fields — e.g. whether a stated return is the project IRR versus "
            "return-on-equity, or whether a capital-structure figure is a "
            "percentage versus a leverage ratio/multiple. Reason first, then "
            "fill the extraction to match your reasoning."
        )
    )
    extraction: ProposalExtraction


def run_extraction(document_text: str, client: Optional[Any] = None) -> dict:
    client = client or anthropic.Anthropic()
    schema = _ReasonedExtraction.model_json_schema()

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            temperature=0,
            system=_SYSTEM_PROMPT,
            tools=[
                {
                    "name": EXTRACTION_TOOL_NAME,
                    "description": _TOOL_DESCRIPTION,
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": EXTRACTION_TOOL_NAME},
            messages=[{"role": "user", "content": _build_user_content(document_text)}],
        )
    except Exception as exc:
        raise ExtractionError(f"Claude API call failed: {exc}") from exc

    for block in response.content:
        if block.type == "tool_use":
            tool_input = block.input
            reasoning = tool_input.get("reasoning")
            if reasoning:
                logger.info("Extraction reasoning: %s", reasoning)
            # reasoning is scratch paper for observability only; callers get
            # the 16-field extraction dict
            return tool_input.get("extraction", tool_input)

    raise ExtractionError("Claude response did not include a tool_use block")
