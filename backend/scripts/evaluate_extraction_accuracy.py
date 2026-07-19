"""Measures extraction accuracy against hand-verified ground truth.

Runs the real pipeline (PDF text extraction -> Claude extraction ->
normalization) against each real sample PDF in
tests/fixtures/real_samples/, compares the result field-by-field against
its ground truth fixture in tests/fixtures/ground_truth/, and reports a
per-document and overall accuracy figure.

Costs money (one real Anthropic API call per document) and is not part of
the default test suite. Run manually from the backend/ directory:

    python scripts/evaluate_extraction_accuracy.py
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pdf_extraction import extract_text  # noqa: E402
from app.llm_extraction import run_extraction  # noqa: E402
from app.validation import normalize_extraction  # noqa: E402

REAL_SAMPLES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "real_samples"
GROUND_TRUTH_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "ground_truth"


def field_matches(extracted_field: Dict[str, Any], expectation: Dict[str, Any]) -> Tuple[bool, str]:
    """Compares one extracted field against its ground-truth expectation."""
    actual_confidence = extracted_field.get("confidence")
    actual_value = extracted_field.get("value")
    actual_found = actual_confidence in ("high", "medium", "low")

    if not expectation["expected_found"]:
        if not actual_found:
            return True, "correctly not_found"
        return False, f"expected not_found but got value={actual_value!r}"

    if not actual_found:
        return False, "expected a value but got not_found"

    expected_value = expectation["expected_value"]
    match_strategy = expectation["match"]

    if match_strategy == "exact":
        matched = actual_value == expected_value
    elif match_strategy == "contains":
        matched = isinstance(actual_value, str) and expected_value.lower() in actual_value.lower()
    else:
        raise ValueError(f"unknown match strategy: {match_strategy!r}")

    if matched:
        return True, "matched"
    return False, f"expected {expected_value!r}, got {actual_value!r}"


def score_document(extraction: Dict[str, Any], ground_truth_fields: Dict[str, Any]) -> Dict[str, Any]:
    """Scores one document's extraction against its ground truth fields."""
    field_results = {}
    for field_name, expectation in ground_truth_fields.items():
        extracted_field = extraction.get(field_name, {})
        matched, reason = field_matches(extracted_field, expectation)
        field_results[field_name] = {"matched": matched, "reason": reason}

    total = len(field_results)
    correct = sum(1 for r in field_results.values() if r["matched"])

    return {
        "fields": field_results,
        "correct": correct,
        "total": total,
        "accuracy": correct / total if total else 0.0,
    }


def run_document(pdf_path: Path, ground_truth_path: Path) -> Dict[str, Any]:
    """Runs the real pipeline against one PDF and scores it against ground truth."""
    ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))

    text = extract_text(pdf_path)
    raw_extraction = run_extraction(text)
    extraction = normalize_extraction(raw_extraction).model_dump()

    result = score_document(extraction, ground_truth["fields"])
    result["source_pdf"] = ground_truth["source_pdf"]
    return result


def main() -> None:
    ground_truth_paths = sorted(GROUND_TRUTH_DIR.glob("*.json"))
    if not ground_truth_paths:
        print(f"No ground truth fixtures found in {GROUND_TRUTH_DIR}")
        return

    document_results = []
    for gt_path in ground_truth_paths:
        pdf_path = REAL_SAMPLES_DIR / f"{gt_path.stem}.pdf"
        print(f"Evaluating {pdf_path.name}...")
        document_results.append(run_document(pdf_path, gt_path))

    total_correct = sum(r["correct"] for r in document_results)
    total_fields = sum(r["total"] for r in document_results)
    overall_accuracy = total_correct / total_fields if total_fields else 0.0

    print()
    print(f"Overall accuracy: {total_correct}/{total_fields} ({overall_accuracy:.1%})")
    for r in document_results:
        print(f"  {r['source_pdf']}: {r['correct']}/{r['total']} ({r['accuracy']:.1%})")
        for field_name, field_result in r["fields"].items():
            if not field_result["matched"]:
                print(f"    MISS {field_name}: {field_result['reason']}")


if __name__ == "__main__":
    main()
