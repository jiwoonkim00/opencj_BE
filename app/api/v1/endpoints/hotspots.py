# app/api/v1/endpoints/hotspots.py

from fastapi import APIRouter, Query
from typing import List, Dict, Any
from ...schemas.hotspot import HotspotGeoJSON, HotspotFeature
from ...services.map_service import MapService
import json
from pathlib import Path

router = APIRouter()
map_service = MapService()

@router.get("/hotspots/next-month", response_model=HotspotGeoJSON)
async def get_next_month_hotspots(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius_km: float = Query(5.0, description="반경 (km)")
) -> HotspotGeoJSON:
    """
    다음 달 뜰 상권 핫스팟 예측 (GeoJSON 형식)
    """
    file_path = Path(__file__).parent.parent.parent.parent / "data" / "dummy_hotspots.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return HotspotGeoJSON(
        type="FeatureCollection",
        features=[HotspotFeature(**f) for f in data["features"]]
    )

@router.get("/cells/{cell_id}", response_model=Dict[str, Any])
async def get_cell_details(cell_id: str):
    """
    특정 상권 셀의 과거 및 예측 데이터
    """
    return {
        "cell_id": cell_id,
        "past_data": [
            {"week_start": "2025-06-01", "value": 150},
            {"week_start": "2025-06-08", "value": 165},
        ],
        "forecast_data": [
            {"week_start": "2025-09-01", "y_pred": 200, "y_lo": 180, "y_hi": 220},
        ],
        "confidence": 0.85
    }