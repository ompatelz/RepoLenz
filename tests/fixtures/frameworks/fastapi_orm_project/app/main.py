from fastapi import FastAPI

from .api.routes import router as api_router

app = FastAPI(title="Demo API")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(api_router, prefix="/api")
