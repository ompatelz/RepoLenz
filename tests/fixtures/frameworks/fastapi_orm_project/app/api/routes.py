from fastapi import APIRouter, Depends

from ..dependencies import get_user_service
from ..services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def list_users(service: UserService = Depends(get_user_service)) -> list[dict[str, str]]:
    return service.list_all()


@router.post("/", response_model=dict)
def create_user(data: dict[str, str], service: UserService = Depends(get_user_service)) -> dict[str, str]:
    return service.create(data)
