from pathlib import Path
from typing import Union

import pdfplumber


class NoExtractableTextError(Exception):
    pass


def extract_text(pdf_path: Union[str, Path]) -> str:
    pages_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)

    text = "\n".join(pages_text).strip()

    if not text:
        raise NoExtractableTextError(
            f"No extractable text found in PDF: {pdf_path}. "
            "It may be a scanned image with no text layer."
        )

    return text
