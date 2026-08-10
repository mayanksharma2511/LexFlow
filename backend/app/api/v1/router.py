from fastapi import APIRouter

from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.ai_hybrid import router as ai_hybrid_router
from app.api.v1.endpoints.audit import router as audit_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.cases import router as cases_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.intelligence import router as intelligence_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.websocket import router as websocket_router

api_router = APIRouter()

api_router.include_router(cases_router)
api_router.include_router(users_router)
api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(ai_router)
api_router.include_router(ai_hybrid_router)
api_router.include_router(intelligence_router)
api_router.include_router(audit_router)
api_router.include_router(websocket_router)
