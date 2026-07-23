from fastapi import APIRouter

from app.api.v1.endpoints import demo, explain, health, search

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(search.router, tags=["search"])
router.include_router(explain.router, tags=["explain"])
router.include_router(demo.router, tags=["demo"])
