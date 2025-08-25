# backend/app/services/ocr_service.py
import requests
import json
from fastapi import HTTPException
from ..core.config import settings

class OcrService:
    def __init__(self):
        self.api_url = settings.NAVER_OCR_API_URL
        self.secret_key = settings.NAVER_OCR_SECRET_KEY

    def process_receipt_image(self, file_content: bytes) -> str:
        """Naver Clova OCR API를 호출하여 영수증 텍스트를 추출합니다."""
        headers = {'X-OCR-SECRET': self.secret_key}
        
        files = [
            ('file', ('receipt.jpg', file_content, 'image/jpeg'))
        ]
        
        request_data = {
            'images': [{'format': 'jpeg', 'name': 'receipt'}],
            'lang': 'ko',
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, data={'message': json.dumps(request_data)}, files=files)
            response.raise_for_status()
            
            ocr_result = response.json()
            
            extracted_text = ""
            for image in ocr_result.get('images', []):
                for field in image.get('receipt', {}).get('result', {}).get('subResults', [{}])[0].get('items', []):
                    if 'text' in field.get('name', {}):
                        extracted_text += field['name']['text'] + '\n'
            
            return extracted_text
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"OCR API 호출 실패: {e}")

    def authenticate_receipt(self, extracted_text: str, known_stores: list[str]) -> bool:
        """추출된 텍스트에서 가게 정보를 검증합니다."""
        for store_name in known_stores:
            if store_name in extracted_text:
                return True
        return False