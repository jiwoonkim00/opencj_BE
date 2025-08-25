# backend/app/services/llm_service.py
from typing import Dict, Any
from ..schemas.promotion import PromotionResponse
from ..core.config import settings
import google.generativeai as genai

class LLMService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # 텍스트 생성 전용 모델로 변경
        self.text_model = genai.GenerativeModel('gemini-pro') 

    def generate_promotion(self, store_name: str, description: str) -> PromotionResponse:
        """
        가게 설명과 이름으로 홍보 문구와 이미지를 생성합니다.
        Gemini는 텍스트만 생성하며, 이미지는 임시 URL을 사용합니다.
        """
        # --- 텍스트 생성 로직 (Gemini Pro) ---
        prompt_text = (
            f"'{store_name}'의 홍보 문구를 작성해줘. 다음 내용을 참고해줘: {description}"
            "친절하고 흥미로운 어조로 작성해줘. 50자 이내로."
        )
        try:
            response_text = self.text_model.generate_content(prompt_text).text
        except Exception as e:
            print(f"Gemini 텍스트 생성 실패: {e}")
            response_text = "매력적인 홍보 문구 생성에 실패했습니다."

        # --- 이미지 생성 로직 (Gemini가 직접 이미지 생성을 지원하지 않음) ---
        # Gemini-pro-vision은 이미지를 입력받아 텍스트를 생성하는 모델입니다.
        # 텍스트로 새로운 이미지를 생성하는 기능은 지원하지 않습니다.
        # 따라서, 여기서는 임시 이미지 URL을 반환하거나 별도의 이미지 생성 API를 사용해야 합니다.
        image_url = "https://via.placeholder.com/600x400?text=AI+Generated+Image"
        image_description = f"{store_name} 홍보 이미지 (AI 생성)"

        return PromotionResponse(
            promotional_text=response_text,
            image_url=image_url,
            image_description=image_description
        )