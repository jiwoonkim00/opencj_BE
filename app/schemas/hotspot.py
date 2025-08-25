# backend/app/schemas/hotspot.py

from pydantic import BaseModel
from typing import List, Dict, Any, Union

class HotspotProperties(BaseModel):
    """핫스팟의 속성 데이터 모델"""
    cell_id: str
    target_month: str
    lift: float
    score: float
    reason_ai: Dict[str, str]

class HotspotFeature(BaseModel):
    """핫스팟 GeoJSON Feature 모델"""
    type: str = "Feature"
    geometry: Dict[str, Any]  # GeoJSON Geometry를 위한 딕셔너리
    properties: HotspotProperties

class HotspotGeoJSON(BaseModel):
    """핫스팟 GeoJSON 전체 응답 모델"""
    type: str = "FeatureCollection"
    features: List[HotspotFeature]