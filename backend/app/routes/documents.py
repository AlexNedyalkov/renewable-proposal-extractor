import os
import tempfile
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.llm_extraction import ExtractionError, run_extraction
from app.pdf_extraction import NoExtractableTextError, extract_text
from app.schemas import ProposalExtraction
from app.store import get_document, save_document
from app.validation import normalize_extraction

router = APIRouter(prefix="/api/documents")

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
_PDF_SIGNATURE = b"%PDF-"


class DocumentAnalysisResponse(BaseModel):
    document_id: str
    extraction: ProposalExtraction


def _error(status_code: int, error: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": error, "message": message})


@router.post("", response_model=DocumentAnalysisResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentAnalysisResponse:
    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise _error(400, "file_too_large", f"File exceeds the {MAX_FILE_SIZE_BYTES} byte limit.")

    if not contents.startswith(_PDF_SIGNATURE):
        raise _error(400, "invalid_file_type", "Only PDF files are supported.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            text = extract_text(tmp_path)
        except NoExtractableTextError as exc:
            raise _error(400, "no_extractable_text", str(exc)) from exc
        except Exception as exc:
            raise _error(500, "pdf_processing_failed", "Failed to process the uploaded PDF.") from exc
    finally:
        if tmp_path:
            os.unlink(tmp_path)

    try:
        raw_extraction = run_extraction(text)
    except ExtractionError as exc:
        raise _error(
            502, "extraction_service_error", "The extraction service failed to process this document."
        ) from exc

    extraction = normalize_extraction(raw_extraction)

    document_id = str(uuid.uuid4())
    save_document(document_id, extraction)

    return DocumentAnalysisResponse(document_id=document_id, extraction=extraction)


@router.get("/{document_id}", response_model=DocumentAnalysisResponse)
async def get_document_analysis(document_id: str) -> DocumentAnalysisResponse:
    extraction = get_document(document_id)

    if extraction is None:
        raise _error(404, "document_not_found", f"No document found with id '{document_id}'.")

    return DocumentAnalysisResponse(document_id=document_id, extraction=extraction)
