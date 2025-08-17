# app/main.py

import uvicorn
from fastapi import FastAPI
from .api.v1.api_router import router as api_router
from .core.config import settings

def create_app() -> FastAPI:
    """FastAPI 앱 인스턴스 생성"""
    app = FastAPI(
        title="AI-Based Local Commerce Backend API",
        description="지역 상권 활성화 플랫폼 백엔드 API",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # API 라우터 등록
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/")
    async def root():
        return {"message": "Welcome to the API"}
        
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)