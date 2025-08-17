# app/services/llm_service.py

from typing import Dict, Any
from ...core.config import settings

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        
    def generate_explanation(self, cell_id: str, target_month: str, lift: float, score: float) -> Dict[str, Any]:
        """예측 결과에 대한 LLM 설명을 생성하는 목업 메서드"""
        return {
            "summary": f"'{cell_id}' 지역은 다음 달 '{target_month}'에 방문객 증가가 예상됩니다.",
            "reason": f"AI 분석 결과, 평점과 SNS 언급량 증가 지수({lift:.2f})가 높게 나타났습니다. 특히, 주변 대형 축제가 예정되어 있어 유동 인구가 증가할 것으로 보입니다.",
            "action": f"이 기회를 활용해 '축제 방문객 특별 할인 이벤트'를 열어보세요. 관련 SNS 포스팅을 올리고, 포스터를 제작하여 홍보하는 것을 추천합니다.",
            "model_version": "GPT-4o Mock v1.0"
        }

    def generate_campaign(self, store_name: str, event_type: str, details: str) -> Dict[str, Any]:
        """홍보 카피와 포스터 이미지를 생성하는 목업 메서드"""
        poster_url = "https://mockup-image-url.com/poster12345.png" # 목업 이미지 URL
        
        return {
            "campaign_copy": f"📢 {store_name}에서 '{event_type}' 이벤트를 시작합니다! {details}",
            "poster_image_url": poster_url,
            "poster_alt_text": f"'{store_name}'의 '{event_type}' 이벤트 포스터 이미지"
        }