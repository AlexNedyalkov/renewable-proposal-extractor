from fastapi import FastAPI

from app.routes.documents import router as documents_router

app = FastAPI(title="Renewable Proposal Extractor")
app.include_router(documents_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
