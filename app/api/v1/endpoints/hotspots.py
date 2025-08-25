# app/api/v1/endpoints/hotspots.py
from fastapi import APIRouter, Query
from typing import List, Dict, Any
from pathlib import Path
import json

from ....schemas.hotspot import HotspotGeoJSON, HotspotFeature
from ....services.map_service import MapService
from ....services.model_service import LSTMForecastService

router = APIRouter()
map_service = MapService()
lstm = LSTMForecastService()


DUMMY_PATH = Path(__file__).resolve().parents[4] / "data" / "dummy_hotspots.json"

@router.get("/next-month", response_model=HotspotGeoJSON)
async def get_next_month_hotspots(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    radius_km: float = Query(5.0, description="반경 (km)")
) -> HotspotGeoJSON:
    try:
        # 1) 주변 셀
        cell_ids = map_service.get_nearby_cells(lat, lng, radius_km)

        feats: List[Dict[str, Any]] = []
        for cid in cell_ids:
            # 2) 최근 seq_len주 feature 로드 (네가 구현한 데이터 소스에 맞춤)
            last_rows = map_service.load_cell_features_last_weeks(cid, weeks=lstm.seq_len)
            if not last_rows or len(last_rows) < lstm.seq_len:
                continue

            # 3) 예측
            y_preds = lstm.forecast(last_rows)  # 길이 out_len
            score = float(sum(y_preds) / len(y_preds))

            polygon = map_service.get_cell_polygon(cid)      # [[lng,lat], ...]
            centroid = map_service.get_cell_centroid(cid)    # (lat, lng)

            feats.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [polygon]},
                "properties": {
                    "cell_id": cid,
                    "score": score,
                    "forecast": y_preds,
                    "centroid": {"lat": centroid[0], "lng": centroid[1]},
                }
            })

        feats.sort(key=lambda f: f["properties"]["score"], reverse=True)
        feats = feats[:30] if len(feats) > 30 else feats
        if not feats:
            raise RuntimeError("no predictions")

        return HotspotGeoJSON(type="FeatureCollection",
                              features=[HotspotFeature(**f) for f in feats])

    except Exception:
        # 실패 시 더미로 폴백
        log.exception(f"hotspots next-month failed: {e}")
        with DUMMY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return HotspotGeoJSON(
            type="FeatureCollection",
            features=[HotspotFeature(**f) for f in data["features"]]
        )
