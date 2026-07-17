from fastapi import FastAPI

app = FastAPI(title="Renewable Proposal Extractor")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
