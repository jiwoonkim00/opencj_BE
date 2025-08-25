# app/api/endpoints/recommend.py

from fastapi import APIRouter, HTTPException
from app.schemas.recommendation_schema import RecommendRequest, RecommendationPayload
from app.services.recommendation_service import provider_search_places, provider_get_weather, call_gemini_json

router = APIRouter()

# 임시: LLM 완전 모의 응답 (for UX testing)
FORCE_MOCK_LLM = False
MOCK_RESPONSE = {
    "summary": "샘플 추천 결과",
    "recommendations": [
        {"id":"mock-cafe-1","name":"샘플 카페 1","address":"샘플 주소","reason":"조용+콘센트","eta_min":7,"expected_stay_min":90,"crowd":"medium","link":""}
    ],
    "missions":[
        {"title":"집중 코딩 45분","steps":["시그니처 라떼 주문","45분 집중","15분 산책"],"reward_hint":"디저트 1개"}
    ]
}

@router.post("/recommend", response_model=RecommendationPayload)
async def recommend(req: RecommendRequest, debug: bool = False):
    """
    이 엔드포인트는 사용자의 프로필과 현재 맥락에 기반하여 장소를 추천하고 미션을 생성합니다.
    """
    try:
        # provider의 정상 동작 여부를 사전 확인합니다.
        _ = await provider_search_places(req.context.category, req.context.lat, req.context.lng, req.context.radius_m)
        _ = await provider_get_weather(req.context.lat, req.context.lng, req.context.when)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provider Error: {e}")

    if debug:
        # 디버그 모드일 경우 LLM을 우회하고 후보 장소만 반환합니다.
        cands = await provider_search_places(req.context.category, req.context.lat, req.context.lng, req.context.radius_m)
        wx = await provider_get_weather(req.context.lat, req.context.lng, req.context.when)
        return {"summary":"debug bypass","recommendations":[],"missions":[],"_debug":{"candidates_len":len(cands),"weather":wx}}

    if FORCE_MOCK_LLM:
        return MOCK_RESPONSE

    # 정상 경로: 후보 장소 및 날씨 정보를 수집하여 Gemini에 전달합니다.
    cands = await provider_search_places(req.context.category, req.context.lat, req.context.lng, req.context.radius_m)
    wx = await provider_get_weather(req.context.lat, req.context.lng, req.context.when)
    return await call_gemini_json(req.user_profile.model_dump(), req.context.model_dump(), cands, wx)

@router.get("/selftest/gemini")
async def selftest_gemini():
    """
    Gemini API가 정상적으로 작동하는지 확인하는 셀프 테스트 엔드포인트입니다.
    """
    import os, json
    import google.generativeai as genai

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        r = await model.generate_content_async(
            "Return a one-line JSON object {\"ok\": true}.",
            generation_config={"response_mime_type": "application/json"},
        )
        return {"ok": True, "model": GEMINI_MODEL, "sample": json.loads(r.text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini selftest failed: {e}")