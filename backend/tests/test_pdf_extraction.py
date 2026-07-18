import pytest

from app.pdf_extraction import NoExtractableTextError, extract_text


def test_extract_text_joins_all_pages(multipage_text_pdf):
    text = extract_text(multipage_text_pdf)

    assert "Sunridge Solar Farm" in text
    assert "total capex $180,000,000" in text


def test_extract_text_raises_on_pdf_with_no_text(blank_no_text_pdf):
    with pytest.raises(NoExtractableTextError):
        extract_text(blank_no_text_pdf)
