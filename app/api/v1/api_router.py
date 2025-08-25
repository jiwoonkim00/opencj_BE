# app/api/v1/api_router.py

from fastapi import APIRouter
from .endpoints.health import router as health_router
from .endpoints.hotspots import router as hotspots_router
# 새로 만든 추천 시스템 라우터 추가
from .endpoints.recommend import router as recommend_router

router = APIRouter()
router.include_router(health_router, tags=["core"])
router.include_router(hotspots_router, prefix="/hotspots", tags=["hotspots"])

# 추천 시스템 엔드포인트를 위한 라우터 추가
router.include_router(recommend_router, prefix="/recommend", tags=["recommendation"])