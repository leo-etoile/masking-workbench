"""마스킹 테스트 — 겹치는 스팬 처리와 원본 스팬 목록 반환을 포함한다."""

from core.masking import mask
from core.spec import PIIType, Span


def test_basic_substitution():
    text = "환자 990101-1234567 내원"
    spans = [Span(start=3, end=17, type=PIIType.RRN, module="m", text=text[3:17])]
    masked, returned = mask(text, spans)
    assert masked == "환자 [RRN] 내원"
    assert returned == spans


def test_no_spans_returns_original():
    text = "변화 없음"
    masked, returned = mask(text, [])
    assert masked == text
    assert returned == []


def test_multiple_non_overlapping():
    text = "홍길동 010-0000-1234"
    spans = [
        Span(start=0, end=3, type=PIIType.NAME, module="m", text="홍길동"),
        Span(start=4, end=17, type=PIIType.PHONE, module="m", text="010-0000-1234"),
    ]
    masked, _ = mask(text, spans)
    assert masked == "[NAME] [PHONE]"


def test_overlapping_spans_merge_with_first_start_label():
    # 타입이 다른 두 스팬이 겹치는 경우. 먼저 시작하는 스팬(0에서 시작하는
    # NAME)이 병합 영역의 라벨을 차지한다.
    text = "abcdef"
    spans = [
        Span(start=0, end=4, type=PIIType.NAME, module="m", text="abcd"),
        Span(start=2, end=6, type=PIIType.ADDRESS, module="m", text="cdef"),
    ]
    masked, _ = mask(text, spans)
    assert masked == "[NAME]"


def test_overlap_tie_break_prefers_longer_at_same_start():
    # 시작이 같은 경우: 더 긴 스팬의 타입이 병합 영역의 라벨이 된다.
    text = "abcdef"
    spans = [
        Span(start=0, end=2, type=PIIType.PHONE, module="m", text="ab"),
        Span(start=0, end=5, type=PIIType.NAME, module="m", text="abcde"),
    ]
    masked, _ = mask(text, spans)
    assert masked == "[NAME]f"


def test_original_spans_returned_unchanged():
    # 원본 스팬 목록이 변형 없이 두 번째 반환값으로 그대로 돌아와야 한다.
    text = "홍길동 내원"
    span = Span(start=0, end=3, type=PIIType.NAME, module="m", text="홍길동")
    spans = [span]
    original = (span.start, span.end, span.type, span.text)
    _, returned = mask(text, spans)
    assert returned is spans
    assert (span.start, span.end, span.type, span.text) == original
