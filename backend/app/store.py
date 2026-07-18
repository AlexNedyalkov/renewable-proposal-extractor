from typing import Dict, Optional

from app.schemas import ProposalExtraction

_documents: Dict[str, ProposalExtraction] = {}


def save_document(document_id: str, extraction: ProposalExtraction) -> None:
    _documents[document_id] = extraction


def get_document(document_id: str) -> Optional[ProposalExtraction]:
    return _documents.get(document_id)
