# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.api_router import router as api_router
from .core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="지역 상권 활성화 플랫폼 백엔드 API",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=None,
    )

    # CORS
    allow_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # v1 라우터 등록
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/")
    async def root():
        return {"message": "Welcome to the API"}

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
