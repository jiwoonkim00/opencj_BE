# app/api/v1/endpoints/ai.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from ...services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()

class ForecastInput(BaseModel):
    cell_id: str
    target_month: str
    lift: float
    score: float

class AiCampaignInput(BaseModel):
    store_name: str
    event_type: str
    details: str

@router.post("/ai/explain", response_model=Dict[str, Any])
async def explain_forecast(input: ForecastInput):
    """
    예측 결과에 대한 LLM 요약, 이유, 액션 제안 (JSON)
    """
    explanation = llm_service.generate_explanation(
        input.cell_id, input.target_month, input.lift, input.score
    )
    return explanation

@router.post("/ai/generate-campaign", response_model=Dict[str, Any])
async def generate_campaign(input: AiCampaignInput):
    """
    AI 기반 홍보 카피 및 포스터 생성
    """
    campaign_content = llm_service.generate_campaign(
        input.store_name, input.event_type, input.details
    )
    return campaign_content