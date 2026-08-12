"""코어 스펙 테스트: PIIType, Span, validate_spans, DetectorModule."""

from core.spec import DetectorModule, PIIType, Span, validate_spans


def test_piitype_has_required_members():
    for name in ("RRN", "PHONE", "DATE", "NAME", "ADDRESS", "EMAIL", "HOSPITAL"):
        assert hasattr(PIIType, name)
    # str-Enum: 멤버 값이 곧바로 문자열로 직렬화된다.
    assert PIIType.RRN == "RRN"
    assert PIIType.RRN.value == "RRN"


def test_span_defaults():
    span = Span(start=0, end=3, type=PIIType.NAME, module="m")
    assert span.text == ""
    assert span.score is None


def test_validate_spans_normalizes_text():
    text = "홍길동 환자"
    spans = [Span(start=0, end=3, type=PIIType.NAME, module="m", text="wrong")]
    valid = validate_spans(text, spans)
    assert len(valid) == 1
    assert valid[0].text == "홍길동"
    assert text[valid[0].start:valid[0].end] == valid[0].text


def test_validate_spans_drops_out_of_range():
    text = "abc"
    spans = [
        Span(start=-1, end=2, type=PIIType.NAME, module="m"),  # start < 0
        Span(start=0, end=99, type=PIIType.NAME, module="m"),  # end > len
        Span(start=2, end=2, type=PIIType.NAME, module="m"),   # start == end
        Span(start=2, end=1, type=PIIType.NAME, module="m"),   # start > end
    ]
    assert validate_spans(text, spans) == []


def test_validate_spans_drops_bad_type():
    text = "abc"
    bad = Span(start=0, end=1, type="NOT_A_TYPE", module="m")  # type: ignore[arg-type]
    assert validate_spans(text, [bad]) == []


def test_detector_module_protocol_runtime_check():
    class Good:
        id = "x"
        display_name = "X"
        requires_external_network = False
        description = "desc"

        def detect(self, text):
            return []

    class Bad:
        id = "y"

    assert isinstance(Good(), DetectorModule)
    assert not isinstance(Bad(), DetectorModule)
