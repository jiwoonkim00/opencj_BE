# app/services/recommendation_service.py

from __future__ import annotations
import os, json, math, asyncio, re
from typing import Any, Dict, List, Optional

import httpx
import google.generativeai as genai
from pydantic import ValidationError
from fastapi import HTTPException
from app.schemas.recommendation_schema import RecommendationPayload

# --- 환경 변수 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
PROVIDER_PLACES = os.getenv("PROVIDER_PLACES", "mock").lower()
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

if not GEMINI_API_KEY:
    # FastAPI 시작 시점의 오류가 아니라, 함수 호출 시점의 오류로 처리
    print("WARNING: GEMINI_API_KEY not set. Gemini API calls will fail.")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

# --- JSON 파싱 유틸리티 ---
def extract_json_block(text: str) -> dict:
    if not isinstance(text, str):
        raise ValueError("LLM 응답이 문자열이 아닙니다.")
    
    # 중괄호 블록 추출 로직은 원본 코드를 그대로 사용
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    m = re.search(r"\{(?:[^{}]|(?R))*\}+", text, flags=re.DOTALL)
    if not m:
        s = text.find("{")
        e = text.rfind("}")
        if s == -1 or e == -1 or e <= s:
            raise ValueError("JSON 블록을 찾지 못했습니다.")
        candidate = text[s:e+1]
    else:
        candidate = m.group(0)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        cleaned = re.sub(r"//.*?$", "", candidate, flags=re.MULTILINE)
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
        return json.loads(cleaned)

# --- Providers ---
def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))

def _mock_places(lat: float, lng: float, category: str) -> List[Dict[str, Any]]:
    # ... (원본 코드 그대로) ...
    out = []
    for i in range(10):
        out.append({
            "id": f"mock-{category}-{i}",
            "name": f"샘플 {category} {i+1}",
            "address": "청주시 흥덕구 어딘가로 123",
            "lat": lat + (i * 0.0008),
            "lng": lng + (i * 0.0006),
            "rating": round(3.5 + (i % 3) * 0.3, 1),
            "price_level": (i % 5) + 1,
            "features": {
                "power_outlets": i % 2 == 0,
                "quiet": i % 3 != 0,
                "good_for_group": i % 4 == 0,
                "url": None,
                "distance_m": (i + 1) * 120,
            },
        })
    return out

async def _kakao_places(category: str, lat: float, lng: float, radius_m: int) -> List[Dict[str, Any]]:
    # ... (원본 코드 그대로) ...
    if not KAKAO_REST_API_KEY:
        return _mock_places(lat, lng, category)
    # ... (생략) ...
    keyword_map = {"cafe":"카페","brunch":"브런치","korean":"한식","japanese":"일식","dessert":"디저트","bar":"바"}
    keyword = keyword_map.get(category, category)
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=10.0) as s:
        page = 1
        while page <= 2:
            params = {"query": keyword, "x": str(lng), "y": str(lat),
                      "radius": str(min(max(radius_m,100),20000)),
                      "page": page, "size": 15, "sort": "distance"}
            r = await s.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            for d in data.get("documents", []):
                items.append({
                    "id": d.get("id"),
                    "name": d.get("place_name"),
                    "address": d.get("road_address_name") or d.get("address_name"),
                    "lat": float(d.get("y")),
                    "lng": float(d.get("x")),
                    "rating": None,
                    "price_level": None,
                    "features": {
                        "url": d.get("place_url"),
                        "category": d.get("category_group_name"),
                        "distance_m": _haversine_m(lat, lng, float(d.get("y")), float(d.get("x"))),
                    },
                })
            if data.get("meta", {}).get("is_end"):
                break
            page += 1
    return items


async def _openweather(lat: float, lng: float) -> Dict[str, Any]:
    # ... (원본 코드 그대로) ...
    if not OPENWEATHER_API_KEY:
        return {"when":"now","status":"clouds","temp_c":26.0,"rain_prob":0.2}
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat":lat, "lon":lng, "appid":OPENWEATHER_API_KEY, "units":"metric"}
    async with httpx.AsyncClient(timeout=8.0) as s:
        r = await s.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    wx = data.get("weather", [{}])[0].get("main", "Clouds").lower()
    temp = data.get("main", {}).get("temp", None)
    rain = data.get("rain", {}).get("1h", 0.0)
    return {"when":"now","status":wx,"temp_c":temp,"rain_prob":0.6 if rain else 0.1}

async def provider_search_places(category: str, lat: float, lng: float, radius_m: int) -> List[Dict[str, Any]]:
    if PROVIDER_PLACES == "kakao":
        return await _kakao_places(category, lat, lng, radius_m)
    return _mock_places(lat, lng, category)

async def provider_get_weather(lat: float, lng: float, when: str) -> Dict[str, Any]:
    return await _openweather(lat, lng)

# --- Gemini 호출 유틸리티 ---
PROMPT = """당신은 지역 추천 큐레이터입니다.
... (원본 PROMPT 내용 그대로) ...
"""

async def call_gemini_json(user_profile: dict, context: dict, candidates: list, weather: dict) -> dict:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY가 설정되지 않았습니다.")
        
    content = PROMPT.format(
        user_profile=json.dumps(user_profile, ensure_ascii=False),
        context=json.dumps(context, ensure_ascii=False),
        candidates=json.dumps(candidates[:20], ensure_ascii=False),
        weather=json.dumps(weather, ensure_ascii=False),
    )
    
    resp = model.generate_content(
        content,
        generation_config={
            "temperature": 0.15,
            "response_mime_type": "application/json",
        }
    )
    
    text = resp.text or ""
    if not text.strip():
        raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")

    data = extract_json_block(text)

    # 누락 필드 기본값 보정
    for rec in data.get("recommendations", []):
        rec.setdefault("address", "")
        rec.setdefault("link", "")
    
    # 검증
    try:
        payload = RecommendationPayload(**data)
        return payload.model_dump()
    except ValidationError as ve:
        raise HTTPException(status_code=500, detail=f"Schema validation failed: {ve.errors()}")