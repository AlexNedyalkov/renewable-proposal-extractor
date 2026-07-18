from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.documents import router as documents_router

app = FastAPI(title="Renewable Proposal Extractor")
app.include_router(documents_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

# Mounted last: API routes above are matched first, so this only serves
# paths (like "/" and "/styles.css") that aren't already handled above.
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
