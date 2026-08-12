"""마스킹 워크벤치의 코어 플랫폼 스펙.

이 모듈은 모든 탐지 모듈과 모든 코어 컴포넌트가 따라야 하는 공통 계약을 정의한다.
어디서나 가볍게 import할 수 있도록 프레임워크나 네트워크 의존성을 의도적으로 두지 않는다.

좌표계
------
모든 스팬은 **Python 문자열 기준 codepoint index**를 사용하며, **반개구간(half-open)**
``[start, end)``으로 표현한다. 즉, ``text[span.start:span.end]``는 탐지된 표면 문자열과
정확히 일치한다. 내부적으로 byte offset이나 다른 토크나이저, 서드파티 라이브러리를 쓰는
모듈이라도 스팬을 반환하기 전에 반드시 이 좌표계로 변환해야 한다.

모듈 탐색(discovery) 규약
------------------------
레지스트리(``core.registry``)는 ``modules`` 패키지를 순회하며 탐지 모듈을 자동으로 찾는다.
**규약(문서화된 단 하나의 규약): 각 탐지 python 파일은 모듈 레벨에서 ``MODULE``이라는
이름의 객체를 노출하며**, 이 객체는 :class:`DetectorModule` 프로토콜을 만족한다. ``MODULE``
속성이 없는 파일은 레지스트리가 무시한다. ``get_module()`` 팩토리 규약은 사용하지 않으며,
코어에는 하드코딩된 모듈 목록도 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Protocol, runtime_checkable


class PIIType(str, Enum):
    """모든 모듈이 참조해야 하는 PII 타입 카탈로그.

    ``str``을 상속하므로 각 멤버는 JSON에서 곧바로 문자열 값으로 직렬화된다
    (``PIIType.RRN`` -> ``"RRN"``).
    """

    RRN = "RRN"          # 주민등록번호
    PHONE = "PHONE"      # 전화번호
    DATE = "DATE"        # 날짜
    NAME = "NAME"        # 이름
    ADDRESS = "ADDRESS"  # 주소
    EMAIL = "EMAIL"      # 이메일 주소
    HOSPITAL = "HOSPITAL"  # 병원/기관명


@dataclass
class Span:
    """탐지된 단일 PII 스팬.

    속성
    ----
    start:
        시작 codepoint index (포함).
    end:
        끝 codepoint index (미포함, 반개구간 ``[start, end)``).
    type:
        :class:`PIIType` 중 하나.
    module:
        이 스팬을 생성한 모듈의 id.
    text:
        표면 문자열. 규약을 잘 지키는 모듈이라면 ``source_text[start:end]``와 같다.
    score:
        선택적 신뢰도 점수(``[0, 1]``). 해당 없으면 ``None``.
    """

    start: int
    end: int
    type: PIIType
    module: str
    text: str = ""
    score: Optional[float] = None


@runtime_checkable
class DetectorModule(Protocol):
    """모든 탐지 모듈이 만족해야 하는 인터페이스.

    속성
    ----
    id:
        안정적이고 유일한 식별자(API와 레지스트리에서 사용).
    display_name:
        워크벤치 UI에 표시되는 사람이 읽기 쉬운 이름.
    requires_external_network:
        외부 네트워크(예: LLM API)에 접근하면 ``True``. 파이프라인은 이런 모듈을
        synthetic-only 플래그 뒤로 게이트한다.
    description:
        이 모듈이 어떤 규칙/방식으로 무엇을 탐지하는지에 대한 사람이 읽을 수 있는
        설명. 워크벤치 UI에서 모듈 이름에 마우스를 올렸을 때 툴팁으로 노출된다.
    """

    id: str
    display_name: str
    requires_external_network: bool
    description: str

    def detect(self, text: str) -> List[Span]:
        """``text``에서 탐지한 스팬 목록을 반환한다."""
        ...


def validate_spans(text: str, spans: List[Span]) -> List[Span]:
    """좌표계 계약을 위반하는 스팬을 걸러낸다.

    다음 중 하나라도 해당하면 스팬을 버린다:

    * ``start < 0``
    * ``end > len(text)``
    * ``start >= end`` (빈 구간 또는 뒤집힌 구간)
    * ``type``이 :class:`PIIType`가 아님

    유효한 스팬만 담은 새 리스트를 반환한다. 살아남은 각 스팬의 ``text`` 필드는
    ``text[start:end]``로 정규화되어, 하위 소비자가 ``text[start:end] == span.text``를
    신뢰할 수 있게 한다.
    """

    n = len(text)
    valid: List[Span] = []
    for span in spans:
        if not isinstance(span.type, PIIType):
            continue
        if span.start < 0 or span.end > n:
            continue
        if span.start >= span.end:
            continue
        span.text = text[span.start:span.end]
        valid.append(span)
    return valid
