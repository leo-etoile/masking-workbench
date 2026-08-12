"""규칙 모듈: 이메일 주소 탐지.

표준 이메일 주소(``local@domain.tld``)를 탐지한다. 문맥 가드로 주변 토큰의
중간에서 매치가 시작되거나 끝나지 않게 한다.
"""

from __future__ import annotations

import re
from typing import List

from core.spec import PIIType, Span

_EMAIL = re.compile(
    r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])"
)


class EmailModule:
    id = "rule_email"
    display_name = "이메일 (규칙)"
    requires_external_network = False
    supported_types = (PIIType.EMAIL,)
    description = "1. local@domain.tld"

    def detect(self, text: str) -> List[Span]:
        spans: List[Span] = []
        for m in _EMAIL.finditer(text):
            spans.append(
                Span(
                    start=m.start(),
                    end=m.end(),
                    type=PIIType.EMAIL,
                    module=self.id,
                    text=m.group(),
                )
            )
        return spans


MODULE = EmailModule()
