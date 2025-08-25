# backend/app/api/v1/endpoints/ocr.py
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from ....services.ocr_service import OcrService

router = APIRouter()
ocr_service = OcrService()

@router.post("/authenticate/receipt")
async def authenticate_receipt_with_ocr(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPEG or PNG image.")

    file_content = await file.read()
    
    # 1. OCR 서비스로 이미지 텍스트 추출
    extracted_text = ocr_service.process_receipt_image(file_content)

    # 2. 추출된 텍스트로 가게 정보 검증 (데이터베이스 연동 가정)
    known_stores = ["스타벅스", "파리바게뜨", "교촌치킨"] 
    is_authenticated = ocr_service.authenticate_receipt(extracted_text, known_stores)
    
    return {
        "success": is_authenticated,
        "message": "인증 성공!" if is_authenticated else "인증 실패: 유효하지 않은 영수증입니다.",
        "extracted_text": extracted_text
    }