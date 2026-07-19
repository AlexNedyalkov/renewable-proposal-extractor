import json
from pathlib import Path

from app.schemas import ProposalExtraction

GROUND_TRUTH_DIR = Path(__file__).parent / "fixtures" / "ground_truth"
REAL_SAMPLES_DIR = Path(__file__).parent / "fixtures" / "real_samples"

_SCHEMA_FIELD_NAMES = set(ProposalExtraction.model_fields.keys())


def test_ground_truth_fixture_exists_for_every_real_sample_pdf():
    sample_stems = {p.stem for p in REAL_SAMPLES_DIR.glob("*.pdf")}
    fixture_stems = {p.stem for p in GROUND_TRUTH_DIR.glob("*.json")}

    assert sample_stems, "expected at least one real sample PDF"
    assert fixture_stems == sample_stems


def test_every_ground_truth_fixture_is_well_formed():
    fixture_paths = list(GROUND_TRUTH_DIR.glob("*.json"))
    assert fixture_paths, "expected at least one ground truth fixture"

    for path in fixture_paths:
        data = json.loads(path.read_text(encoding="utf-8"))

        assert data["source_pdf"] == f"{path.stem}.pdf"
        assert isinstance(data.get("notes"), str)

        fields = data["fields"]
        assert set(fields.keys()) == _SCHEMA_FIELD_NAMES, f"{path.name} field set doesn't match the current schema"

        for field_name, entry in fields.items():
            assert isinstance(entry["expected_found"], bool), f"{path.name}.{field_name}"

            if entry["expected_found"]:
                assert "expected_value" in entry, f"{path.name}.{field_name} missing expected_value"
                assert entry.get("match") in ("exact", "contains"), f"{path.name}.{field_name} bad match strategy"
            else:
                assert "expected_value" not in entry, f"{path.name}.{field_name} not_found fields carry no value"
