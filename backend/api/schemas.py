"""워크벤치 API의 Pydantic v2 요청/응답 모델.

이 형태들은 React 프론트엔드와 공유하는 고정 계약이다. 프론트엔드와
조율 없이 필드명이나 중첩 구조를 변경하지 말 것.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


# -- 공용 스팬 형태 ---------------------------------------------------------


class SpanOut(BaseModel):
    start: int
    end: int
    type: str
    module: str
    text: str
    score: Optional[float] = None


class LabelIn(BaseModel):
    start: int
    end: int
    type: str
    text: str


class DetectionIn(BaseModel):
    start: int
    end: int
    type: str
    module: str
    text: str
    score: Optional[float] = None


# -- /api/modules ---------------------------------------------------------


class ModuleInfo(BaseModel):
    id: str
    display_name: str
    requires_external_network: bool
    description: str


class ModulesResponse(BaseModel):
    modules: List[ModuleInfo]


# -- /api/detect ----------------------------------------------------------


class DetectRequest(BaseModel):
    text: str
    module_ids: List[str]
    synthetic: bool


class DetectResponse(BaseModel):
    results: Dict[str, List[SpanOut]]
    module_errors: Dict[str, str]
    blocked: List[str]


# -- /api/samples ---------------------------------------------------------


class Sample(BaseModel):
    id: str
    text: str
    synthetic: bool


class SamplesResponse(BaseModel):
    samples: List[Sample]


# -- /api/labels ----------------------------------------------------------


class SaveLabelsRequest(BaseModel):
    doc_id: str
    text: str
    labels: List[LabelIn]


class SaveLabelsResponse(BaseModel):
    ok: bool


class LabelDocSummary(BaseModel):
    doc_id: str
    updated_at: str


class LabelsListResponse(BaseModel):
    documents: List[LabelDocSummary]


class LabelDocument(BaseModel):
    doc_id: str
    text: str
    labels: List[LabelIn]
    updated_at: str


# -- /api/evaluate --------------------------------------------------------


class EvaluateRequest(BaseModel):
    labels: List[LabelIn]
    detections: Dict[str, List[DetectionIn]]


class ModuleMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int


class EvaluateResponse(BaseModel):
    metrics: Dict[str, ModuleMetrics]
