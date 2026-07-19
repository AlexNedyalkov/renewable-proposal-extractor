import json

from scripts.evaluate_extraction_accuracy import GROUND_TRUTH_DIR, REAL_SAMPLES_DIR, field_matches, run_document, score_document


def _extracted(value, confidence="high"):
    return {"value": value, "confidence": confidence, "source_snippet": None}


def test_field_matches_correctly_not_found():
    matched, _ = field_matches(_extracted(None, "not_found"), {"expected_found": False})
    assert matched is True


def test_field_matches_fails_when_expected_not_found_but_value_present():
    matched, reason = field_matches(_extracted(220, "high"), {"expected_found": False})
    assert matched is False
    assert "220" in reason


def test_field_matches_fails_when_expected_found_but_actual_not_found():
    matched, reason = field_matches(
        _extracted(None, "not_found"), {"expected_found": True, "expected_value": 220, "match": "exact"}
    )
    assert matched is False


def test_field_matches_exact_numeric_match():
    matched, _ = field_matches(_extracted(220), {"expected_found": True, "expected_value": 220, "match": "exact"})
    assert matched is True


def test_field_matches_exact_numeric_mismatch():
    matched, reason = field_matches(_extracted(200), {"expected_found": True, "expected_value": 220, "match": "exact"})
    assert matched is False
    assert "220" in reason and "200" in reason


def test_field_matches_contains_case_insensitive():
    matched, _ = field_matches(
        _extracted("Monsoon Wind Power Project"),
        {"expected_found": True, "expected_value": "monsoon wind", "match": "contains"},
    )
    assert matched is True


def test_field_matches_contains_no_match():
    matched, _ = field_matches(
        _extracted("Some Other Project"),
        {"expected_found": True, "expected_value": "monsoon wind", "match": "contains"},
    )
    assert matched is False


def test_score_document_aggregates_correct_and_total():
    extraction = {
        "project_name": _extracted("Monsoon Wind Power Project"),
        "installed_capacity_mw": _extracted(600),
        "total_capex_usd": _extracted(None, "not_found"),
    }
    ground_truth_fields = {
        "project_name": {"expected_found": True, "expected_value": "monsoon", "match": "contains"},
        "installed_capacity_mw": {"expected_found": True, "expected_value": 999, "match": "exact"},  # wrong on purpose
        "total_capex_usd": {"expected_found": False},
    }

    result = score_document(extraction, ground_truth_fields)

    assert result["total"] == 3
    assert result["correct"] == 2
    assert result["accuracy"] == 2 / 3
    assert result["fields"]["installed_capacity_mw"]["matched"] is False


def test_score_document_handles_missing_field_in_extraction():
    result = score_document({}, {"project_name": {"expected_found": False}})

    assert result["fields"]["project_name"]["matched"] is True


def _perfect_raw_extraction_for(ground_truth_fields):
    raw = {}
    for field_name, expectation in ground_truth_fields.items():
        if expectation["expected_found"]:
            raw[field_name] = {
                "value": expectation["expected_value"],
                "confidence": "high",
                "source_snippet": "test snippet",
            }
        else:
            raw[field_name] = {"value": None, "confidence": "not_found", "source_snippet": None}
    return raw


def test_run_document_wires_pipeline_together_correctly(monkeypatch):
    gt_path = GROUND_TRUTH_DIR / "triconboston_wind.json"
    ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))
    fake_raw_extraction = _perfect_raw_extraction_for(ground_truth["fields"])

    monkeypatch.setattr(
        "scripts.evaluate_extraction_accuracy.run_extraction",
        lambda text: fake_raw_extraction,
    )

    pdf_path = REAL_SAMPLES_DIR / "triconboston_wind.pdf"
    result = run_document(pdf_path, gt_path)

    assert result["source_pdf"] == "triconboston_wind.pdf"
    assert result["total"] == 16
    assert result["correct"] == 16
    assert result["accuracy"] == 1.0
