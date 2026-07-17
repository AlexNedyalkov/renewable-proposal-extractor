# Project Plan and Metrics

## 1. Project Goal
Build a prototype full-stack application that lets an analyst upload a renewable energy project proposal PDF and receive a structured summary of key financial and technical data.

## 2. Scope Summary
Core capabilities:
- Upload PDF through a simple web UI
- Send the document to a Python backend API
- Extract structured fields using an LLM-backed workflow
- Return results in a readable JSON or UI view
- Handle missing fields and validation errors gracefully
- Document setup, testing, and usage clearly

## 3. Delivery Plan
### Phase 1 — Foundation and setup
- Create the repository structure
- Set up backend and frontend scaffolding
- Define the API contract and data model
- Estimate effort: 4-6 hours

### Phase 2 — Backend processing pipeline
- Implement PDF upload endpoint
- Extract text from the PDF
- Build the extraction prompt and response schema
- Validate and normalize extracted fields
- Estimate effort: 10-12 hours

### Phase 3 — Frontend experience
- Build upload page and result view
- Show loading, error, and success states
- Connect the UI to the backend API
- Estimate effort: 6-8 hours

### Phase 4 — Reliability and quality
- Add tests for API and extraction logic
- Improve error handling for malformed or missing documents
- Add README, setup instructions, and AI assistant usage log
- Estimate effort: 6-8 hours

## 4. Suggested Timeline
- Week 1: Foundation, backend API, extraction logic
- Week 1-2: Frontend, testing, documentation
- Total estimated effort: 30-40 hours

## 5. Metrics to Track

| Area | Metric | Target |
| --- | --- | --- |
| Extraction quality | Field extraction accuracy on sample docs | 85%+ |
| Reliability | Graceful handling of missing or low-quality data | 100% of requests return structured errors or fallback values |
| Performance | API response time for small PDFs | P95 under 3 seconds |
| Performance | API response time for larger PDFs | P95 under 10 seconds |
| Quality | Unit test coverage | 80%+ |
| Quality | Smoke test pass rate | 100% on core user flow |
| UX | Upload-to-results flow | Under 5 seconds of visible loading for typical files |
| Delivery | Milestone completion | 100% of planned milestones delivered |

## 6. Success Criteria
The project should be considered successful if:
- A user can upload a PDF and receive structured results
- The extraction includes at least the most important financial and technical fields from the brief
- The app works end-to-end locally with clear setup instructions
- The repository includes documentation, tests, and an AI assistant log

## 7. Risks and Mitigations
- Risk: LLM outputs are inconsistent
  - Mitigation: enforce a strict JSON schema and validation layer
- Risk: PDFs vary in structure and quality
  - Mitigation: support multiple extraction fallbacks and preserve confidence metadata
- Risk: Frontend and backend integration issues
  - Mitigation: define the API contract early and test it with sample payloads

## 8. Recommended Implementation Order
1. Define the output schema
2. Build the backend upload endpoint
3. Add PDF text extraction
4. Integrate the LLM extraction step
5. Add validation and fallback logic
6. Build the UI
7. Add tests and documentation
