# app/services/model_service.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Sequence, Optional

import json
import numpy as np
import torch
import torch.nn as nn


MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "best_lstm.pt"
META_PATH = MODELS_DIR / "model_meta.json"


class LSTMWrapper(nn.Module):
    """
    저장 형식이 state_dict인 경우를 기본으로 가정.
    (만약 torch.save(model)로 통째 저장했다면 아래 load_model에서 분기 처리함)
    """
    def __init__(self, input_size: int, hidden: int = 64, layers: int = 2, out_len: int = 4):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden, num_layers=layers, batch_first=True)
        self.head = nn.Linear(hidden, out_len)

    def forward(self, x):  # x: (B, T, F)
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        y = self.head(last)  # (B, out_len)
        return y


class LSTMForecastService:
    """
    - model_meta.json 을 읽어 feature 순서/스케일러/seq_len을 적용
    - best_lstm.pt 로드를 싱글톤처럼 1회만 수행
    - 입력: 최근 seq_len 기간의 feature 시계열 (딕셔너리 리스트)
    - 출력: 예측값 벡터(list[float])
    """
    _instance: Optional["LSTMForecastService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_loaded", False):
            return
        if not META_PATH.exists():
            raise FileNotFoundError(f"Meta file not found: {META_PATH}")
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

        with META_PATH.open("r", encoding="utf-8") as f:
            meta = json.load(f)

        # 메타 정보
        self.seq_len: int = int(meta["seq_len"])
        self.input_dim: int = int(meta["input_dim"])
        self.numeric_cols: List[str] = list(meta.get("numeric_cols", []))
        self.binary_cols: List[str] = list(meta.get("binary_cols", []))
        self.feature_order: List[str] = self.numeric_cols + self.binary_cols

        # 스케일러 파라미터 (표준화: (x-mean)/scale )
        self.scaler_mean = np.array(meta.get("scaler_mean", [0.0] * self.input_dim), dtype=np.float32)
        self.scaler_scale = np.array(meta.get("scaler_scale", [1.0] * self.input_dim), dtype=np.float32)
        self.scaler_scale[self.scaler_scale == 0] = 1.0  # 0 division 보호

        # 출력 길이(메타에 없으면 헤드에서 유도)
        self.out_len: int = int(meta.get("out_len", 4))

        # 모델 로드
        self.model = self._load_model()
        self.model.eval()
        self._loaded = True

    def _load_model(self) -> nn.Module:
        # 1) state_dict 저장을 기본 가정
        try:
            model = LSTMWrapper(input_size=self.input_dim, out_len=self.out_len)
            state = torch.load(str(MODEL_PATH), map_location="cpu")
            # 일부 학습 스크립트는 {"state_dict": ...} 형태로 저장
            if isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
            model.load_state_dict(state)
            return model
        except Exception:
            # 2) 통짜 저장(torch.save(model))일 경우
            model = torch.load(str(MODEL_PATH), map_location="cpu")
            return model

    # ---------- 전처리 ----------
    def _to_matrix(self, rows: Sequence[Dict[str, float]]) -> np.ndarray:
        """
        rows: 길이 seq_len의 리스트. 각 원소는 {col: value}
        return: (seq_len, input_dim) float32
        """
        if len(rows) < self.seq_len:
            raise ValueError(f"need at least seq_len({self.seq_len}) rows, got {len(rows)}")

        # 최근 seq_len만 사용
        rows = rows[-self.seq_len:]

        mat = np.zeros((self.seq_len, self.input_dim), dtype=np.float32)
        for t, row in enumerate(rows):
            mat[t] = np.array([float(row.get(col, 0.0)) for col in self.feature_order], dtype=np.float32)

        # 표준화
        mat = (mat - self.scaler_mean) / self.scaler_scale
        return mat

    # ---------- 예측 ----------
    def forecast(self, last_rows: Sequence[Dict[str, float]]) -> List[float]:
        """
        last_rows: 최근 seq_len 기간의 feature 딕셔너리 리스트
        return: 길이 out_len 의 예측값 리스트
        """
        mat = self._to_matrix(last_rows)                       # (T, F)
        x = torch.from_numpy(mat).unsqueeze(0)                 # (1, T, F)
        with torch.no_grad():
            y = self.model(x)                                  # (1, out_len)
        return y.squeeze(0).cpu().numpy().astype(float).tolist()
