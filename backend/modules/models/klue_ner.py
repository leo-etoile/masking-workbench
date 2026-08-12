"""AI 모듈: 사전학습 개체명 인식(NER) 모델 기반 탐지.

``Leo97/KoELECTRA-small-v3-modu-ner`` (국립국어원 "모두의 말뭉치 2021" 개체명
분석 말뭉치로 파인튜닝된 공개 모델)를 로컬에서 실행해 인물명/장소/기관명을
탐지한다.

핵심 동작
---------
* ``requires_external_network = False`` — 최초 1회 모델 가중치를 로컬 캐시에
  내려받은 뒤에는, 추론 시 네트워크 호출이 전혀 없다.
* ``transformers``/``torch``는 첫 :meth:`detect` 호출 시에만 지연 import하며,
  적재된 파이프라인은 인스턴스당 한 번만 생성해 이후 호출에 재사용한다.
* 모델이 반환하는 15종 BIO 태그 중 PS(인물)→NAME, LC(장소)→ADDRESS,
  OG(기관)→HOSPITAL만 사용한다. 나머지(DT/TI/QT 등)는 규칙 모듈이 이미
  담당하거나 우리 PII 카탈로그 범위 밖이라 무시한다.
* 우아한 실패: 패키지 미설치 또는 모델 로드 실패 시 :meth:`detect`가 명확한
  ``RuntimeError``를 던지고, 파이프라인이 이를 ``module_errors``에 기록한다
  (다른 모듈이나 요청 전체를 죽이지 않는다).

주의: 이 모델은 뉴스/일반 도메인 말뭉치로 학습되어, 진료 자유서술 문맥에서는
오탐/누락이 규칙 모듈보다 많을 수 있다.
"""

from __future__ import annotations

from typing import List

from core.spec import PIIType, Span

MODEL_ID = "Leo97/KoELECTRA-small-v3-modu-ner"

_TAG_TO_TYPE = {
    "PS": PIIType.NAME,
    "LC": PIIType.ADDRESS,
    "OG": PIIType.HOSPITAL,
}


class KlueNERModule:
    id = "klue_ner"
    display_name = "개체명 인식 (KoELECTRA 사전학습)"
    requires_external_network = False
    supported_types = (PIIType.NAME, PIIType.ADDRESS, PIIType.HOSPITAL)
    description = (
        "국립국어원 모두의 말뭉치로 학습된 사전학습 NER 모델(Leo97/KoELECTRA-"
        "small-v3-modu-ner)을 로컬에서 실행. 인물명(PS)→NAME, 장소(LC)→ADDRESS, "
        "기관명(OG)→HOSPITAL로 매핑. 최초 실행 시 모델 파일을 한 번 내려받으며, "
        "이후에는 네트워크 없이 동작. 뉴스/일반 말뭉치 기반이라 진료 문맥에서는 "
        "오탐/누락이 있을 수 있음."
    )

    def __init__(self) -> None:
        self._pipeline = None  # 인스턴스당 1회만 로드되는 지연 싱글턴

    def detect(self, text: str) -> List[Span]:
        if self._pipeline is None:
            self._pipeline = self._load_pipeline()
        try:
            entities = self._pipeline(text)
        except Exception as exc:  # pragma: no cover - 모델별 런타임 오류
            raise RuntimeError(f"klue_ner inference failed: {exc}") from exc
        return self._to_spans(text, entities)

    @staticmethod
    def _load_pipeline():
        try:
            from transformers import pipeline as hf_pipeline
        except ImportError as exc:
            raise RuntimeError(
                "klue_ner requires the 'transformers' and 'torch' packages, "
                "which are not installed."
            ) from exc

        try:
            return hf_pipeline(
                "token-classification",
                model=MODEL_ID,
                aggregation_strategy="simple",
            )
        except Exception as exc:
            raise RuntimeError(
                f"klue_ner failed to load model '{MODEL_ID}': {exc}"
            ) from exc

    @staticmethod
    def _to_spans(text: str, entities) -> List[Span]:
        spans: List[Span] = []
        for entity in entities:
            pii_type = _TAG_TO_TYPE.get(entity.get("entity_group"))
            if pii_type is None:
                continue  # 지원 범위 밖 태그(DT/TI/QT 등)는 무시
            start, end = entity["start"], entity["end"]
            spans.append(
                Span(
                    start=start,
                    end=end,
                    type=pii_type,
                    module=KlueNERModule.id,
                    text=text[start:end],
                    score=float(entity.get("score", 0.0)),
                )
            )
        return spans


MODULE = KlueNERModule()
