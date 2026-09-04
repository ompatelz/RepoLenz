"""A deliberately non-runnable FastAPI module used for AST-only detection tests."""

from fastapi import APIRouter, Depends, FastAPI

from .dependencies import get_service
from .schemas import HealthResponse, UserResponse

app = FastAPI()
users_router = APIRouter(prefix="/users", tags=["users"])


@app.get("/health", tags=["system"], response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: object = Depends(get_service)) -> UserResponse:
    return await service.get(user_id)


app.include_router(users_router, prefix="/api")
