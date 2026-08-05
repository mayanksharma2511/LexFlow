from fastapi import APIRouter

from app.api.v1.endpoints.cases import router as cases_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.ai import router as ai_router

api_router = APIRouter()

api_router.include_router(cases_router)
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(ai_router)