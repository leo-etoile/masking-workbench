"""마스킹 워크벤치의 FastAPI 애플리케이션.

코어 파이프라인, 레지스트리, 저장소, 평가를 React 프론트엔드가 소비하는
HTTP 계약 뒤에 연결한다. Vite 개발 서버(http://localhost:5173)를 위해
CORS가 활성화되어 있다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    DetectRequest,
    DetectResponse,
    EvaluateRequest,
    EvaluateResponse,
    LabelDocument,
    LabelsListResponse,
    ModulesResponse,
    SamplesResponse,
    SaveLabelsRequest,
    SaveLabelsResponse,
    SpanOut,
)
from core import evaluation, pipeline
from core.registry import get_module, list_modules
from core.spec import PIIType, Span
from storage import labels as labels_store

_SAMPLES_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "samples.json"

app = FastAPI(title="EMR Masking Workbench API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _span_to_out(span: Span) -> SpanOut:
    return SpanOut(
        start=span.start,
        end=span.end,
        type=span.type.value,
        module=span.module,
        text=span.text,
        score=span.score,
    )


@app.get("/api/modules", response_model=ModulesResponse)
def get_modules() -> ModulesResponse:
    return ModulesResponse(modules=list_modules())


@app.post("/api/detect", response_model=DetectResponse)
def post_detect(request: DetectRequest) -> DetectResponse:
    result = pipeline.run(request.text, request.module_ids, request.synthetic)
    results = {
        module_id: [_span_to_out(s) for s in spans]
        for module_id, spans in result.results.items()
    }
    return DetectResponse(
        results=results,
        module_errors=result.module_errors,
        blocked=result.blocked,
    )


@app.get("/api/samples", response_model=SamplesResponse)
def get_samples() -> SamplesResponse:
    if not _SAMPLES_PATH.exists():
        return SamplesResponse(samples=[])
    data = json.loads(_SAMPLES_PATH.read_text(encoding="utf-8"))
    return SamplesResponse(samples=data)


@app.post("/api/labels", response_model=SaveLabelsResponse)
def post_labels(request: SaveLabelsRequest) -> SaveLabelsResponse:
    labels_store.save_document(
        request.doc_id,
        request.text,
        [label.model_dump() for label in request.labels],
    )
    return SaveLabelsResponse(ok=True)


@app.get("/api/labels", response_model=LabelsListResponse)
def get_labels() -> LabelsListResponse:
    return LabelsListResponse(documents=labels_store.list_documents())


@app.get("/api/labels/{doc_id}", response_model=LabelDocument)
def get_label_document(doc_id: str) -> LabelDocument:
    document = labels_store.load_document(doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="label document not found")
    return LabelDocument(**document)


@app.post("/api/evaluate", response_model=EvaluateResponse)
def post_evaluate(request: EvaluateRequest) -> EvaluateResponse:
    gold = _labels_to_spans(request.labels)
    detections_by_module = {
        module_id: _detections_to_spans(module_id, dets)
        for module_id, dets in request.detections.items()
    }
    supported_types_by_module = {}
    for module_id in detections_by_module:
        module = get_module(module_id)
        supported_types = getattr(module, "supported_types", None)
        if supported_types is not None:
            supported_types_by_module[module_id] = set(supported_types)
    metrics = evaluation.evaluate(gold, detections_by_module, supported_types_by_module)
    return EvaluateResponse(metrics=metrics)


def _labels_to_spans(labels) -> List[Span]:
    spans: List[Span] = []
    for label in labels:
        pii_type = _coerce_type(label.type)
        if pii_type is None:
            continue
        spans.append(
            Span(
                start=label.start,
                end=label.end,
                type=pii_type,
                module="gold",
                text=label.text,
            )
        )
    return spans


def _detections_to_spans(module_id: str, dets) -> List[Span]:
    spans: List[Span] = []
    for det in dets:
        pii_type = _coerce_type(det.type)
        if pii_type is None:
            continue
        spans.append(
            Span(
                start=det.start,
                end=det.end,
                type=pii_type,
                module=module_id,
                text=det.text,
            )
        )
    return spans


def _coerce_type(value: str):
    try:
        return PIIType(value)
    except ValueError:
        return None
