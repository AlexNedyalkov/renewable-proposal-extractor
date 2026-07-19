# API Contract

Documents the actual implemented request/response shapes of the backend
API as of sprint v1. All example payloads below were captured from the
running application (or from `backend/tests/manual_smoke_test_notes.md`
live runs), not hand-written from the PRD.

Base URL (local dev): `http://127.0.0.1:8000`

## GET /health

Liveness check.

**Response** `200 OK`
```json
{"status": "ok"}
```

## POST /api/documents

Uploads a PDF project proposal, runs the full extraction pipeline
synchronously, and returns the structured result.

**Request**: `multipart/form-data` with a single field `file` (the PDF).

**Response** `200 OK`
```json
{
  "document_id": "1c43ccea-a79d-4b72-98ff-27f64e1f9cbb",
  "extraction": {
    "project_name": {
      "value": "AC Energy Wind Power Project",
      "confidence": "high",
      "source_snippet": "BIM Wind Power Joint Stock Company AC Energy Wind Power Project (Viet Nam)"
    },
    "location": {
      "value": "Ninh Thuan province, Viet Nam",
      "confidence": "high",
      "source_snippet": "an 88-megawatt (MW) wind farm in Ninh Thuan province, Viet Nam"
    },
    "technology_type": { "value": "Wind power (onshore)", "confidence": "high", "source_snippet": "..." },
    "installed_capacity_mw": { "value": 88, "confidence": "high", "source_snippet": "..." },
    "expected_annual_generation_mwh": { "value": 240280, "confidence": "high", "source_snippet": "..." },
    "commercial_operation_date": { "value": "30 September 2021", "confidence": "high", "source_snippet": "..." },
    "developer_sponsor": { "value": "ACEN Vietnam Investments Pte. Ltd. (ACEV) and BIM Energy Holding Corporation (BIMEH)", "confidence": "high", "source_snippet": "..." },
    "total_capex_usd": { "value": null, "confidence": "not_found", "source_snippet": null },
    "capex_per_mw": { "value": null, "confidence": "not_found", "source_snippet": null },
    "expected_irr_percent": { "value": null, "confidence": "not_found", "source_snippet": null },
    "payback_period_years": { "value": null, "confidence": "not_found", "source_snippet": null },
    "lcoe_usd_per_mwh": { "value": null, "confidence": "not_found", "source_snippet": null },
    "ppa_price_usd_per_mwh": { "value": 85, "confidence": "high", "source_snippet": "..." },
    "ppa_term_years": { "value": 20, "confidence": "high", "source_snippet": "..." },
    "debt_percent": { "value": null, "confidence": "not_found", "source_snippet": null },
    "equity_percent": { "value": null, "confidence": "not_found", "source_snippet": null }
  }
}
```

Every field in `extraction` follows the same shape: `value` (any JSON type,
or `null`), `confidence` (`"high" | "medium" | "low" | "not_found"`), and
`source_snippet` (a short verbatim quote from the document, or `null`).
`not_found` fields are never omitted — all 16 fields are always present, so
consumers can render a fixed-shape results table regardless of what the
document contained. See `backend/tests/manual_smoke_test_notes.md` for the
full reasoning behind this design and real-world extraction results across
5 documents.

**Error responses** — all errors follow `{"detail": {"error": <code>, "message": <string>}}`:

| Status | `error` code | Cause |
| --- | --- | --- |
| 400 | `invalid_file_type` | Uploaded bytes don't start with the PDF magic number (`%PDF-`), regardless of the declared `Content-Type` |
| 400 | `file_too_large` | File exceeds 20 MB |
| 400 | `no_extractable_text` | PDF parsed successfully but contains no extractable text (e.g. a scanned image with no text layer) |
| 500 | `pdf_processing_failed` | PDF parsing crashed unexpectedly (e.g. a corrupt file) |
| 502 | `extraction_service_error` | The Claude API call failed (auth, rate limit, timeout, connection error) |

Example (`400 invalid_file_type`):
```json
{"detail": {"error": "invalid_file_type", "message": "Only PDF files are supported."}}
```

## GET /api/documents/{document_id}

Retrieves a previously submitted analysis by ID (in-memory store; results
do not survive a server restart).

**Response** `200 OK`: same `DocumentAnalysisResponse` shape as `POST /api/documents`.

**Response** `404 Not Found`:
```json
{"detail": {"error": "document_not_found", "message": "No document found with id 'does-not-exist'."}}
```

## Drift from the PRD

The PRD (`sprints/v1/PRD.md` §4) described the extraction schema and a
data flow, but didn't fix a few implementation details — captured here to
close the loop:

- **File size limit**: PRD said "a defined size limit" without a number.
  Implemented as 20 MB (`MAX_FILE_SIZE_BYTES` in `routes/documents.py`).
- **File-type validation**: implemented by checking the actual `%PDF-`
  file signature, not the client-supplied `Content-Type` header (which is
  trivially spoofable) — stricter than the PRD implied.
- **Error code names**: the PRD only said "structured error responses"
  and "500/502 error payload"; the concrete `error` codes above
  (`invalid_file_type`, `file_too_large`, `no_extractable_text`,
  `pdf_processing_failed`, `extraction_service_error`, `document_not_found`)
  are new, introduced during Tasks 7-9.
- **`GET /health`**: not mentioned in the PRD's data flow; added in Task 1
  as a standard liveness endpoint, unrelated to the extraction pipeline.
- No other drift — the endpoint paths, the `{document_id, extraction}`
  response wrapper, and the extraction schema all match the PRD as
  designed.

## Schema change (sprint v3)

`debt_equity_ratio` (a free-text field) was replaced with two strictly-typed
numeric fields, `debt_percent` and `equity_percent`. Real-document testing in
sprint v1 found the original field came back in three different formats
across documents ("75:25", a currency amount pair, "2.94x/2.24x"), making it
unusable for direct calculation. The schema is now 16 fields, not 15.
