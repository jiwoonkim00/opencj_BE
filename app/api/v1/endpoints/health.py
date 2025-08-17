# app/api/v1/endpoints/health.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz")
def health_check():
    """API 서버 상태 확인"""
    return {"status": "ok"}