# backend/app/schemas/promotion.py
from pydantic import BaseModel

class PromotionRequest(BaseModel):
    store_name: str
    store_category: str
    description: str

class PromotionResponse(BaseModel):
    promotional_text: str
    image_url: str