"""API package initialization and router aggregation."""

from fastapi import APIRouter
from backend.app.api.investigations import router as investigations_router
from backend.app.api.incidents import router as incidents_router
from backend.app.api.cluster import router as cluster_router
from backend.app.api.evaluation import router as evaluation_router

api_router = APIRouter()
api_router.include_router(investigations_router)
api_router.include_router(incidents_router)
api_router.include_router(cluster_router)
api_router.include_router(evaluation_router)

__all__ = ["api_router"]
