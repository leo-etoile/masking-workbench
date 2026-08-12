"""규칙 모듈 테스트(긍정 + 부정 사례). 생성된 모든 스팬에 대해
``text[start:end] == span.text`` 불변식을 함께 검증한다."""

import pytest

from modules.rules.date_rule import MODULE as DATE
from modules.rules.email import MODULE as EMAIL
from modules.rules.phone import MODULE as PHONE
from modules.rules.rrn import MODULE as RRN


def _texts(module, text):
    spans = module.detect(text)
    # 불변식: 모든 스팬의 원문 슬라이스는 기록된 text와 일치해야 한다.
    for span in spans:
        assert text[span.start:span.end] == span.text
    return [s.text for s in spans]


# -- 주민등록번호 -----------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("환자 990101-1234567 내원", ["990101-1234567"]),
        ("주민 1234561234567 확인", ["1234561234567"]),
        ("마스킹 900315-1****** 사례", ["900315-1******"]),
        ("완전마스킹 880401-*******", ["880401-*******"]),
    ],
)
def test_rrn_positive(text, expected):
    assert _texts(RRN, text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "숫자 12345678901234567 는 17자리",   # too long, guarded
        "부분 12345-1234567 형식",             # 5-digit front
        "그냥 문장 입니다",
    ],
)
def test_rrn_negative(text):
    assert _texts(RRN, text) == []


# -- 전화번호 ----------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("연락 010-1234-5678 임", ["010-1234-5678"]),
        ("연락 01012345678 임", ["01012345678"]),
        ("연락 010 1234 5678 임", ["010 1234 5678"]),
        ("유선 02-123-4567 임", ["02-123-4567"]),
        ("유선 031-123-4567 임", ["031-123-4567"]),
    ],
)
def test_phone_positive(text, expected):
    assert _texts(PHONE, text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "숫자 12345 만",
        "전화 아님 문장",
    ],
)
def test_phone_negative(text):
    assert _texts(PHONE, text) == []


# -- 날짜 --------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("내원 2021-03-14 확인", ["2021-03-14"]),
        ("생일 1985.07.22 확인", ["1985.07.22"]),
        ("초진 24.02.18 확인", ["24.02.18"]),
        ("진단 2019년 12월 3일 확인", ["2019년 12월 3일"]),
        ("진단 2020년11월9일 확인", ["2020년11월9일"]),
    ],
)
def test_date_positive(text, expected):
    assert _texts(DATE, text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "숫자 20210314 뭉침",
        "날짜 없음 문장",
    ],
)
def test_date_negative(text):
    assert _texts(DATE, text) == []


# -- 이메일 ------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("메일 chulsoo@example.com 로", ["chulsoo@example.com"]),
        ("메일 taewoong.seo@hospital.co.kr 발송", ["taewoong.seo@hospital.co.kr"]),
    ],
)
def test_email_positive(text, expected):
    assert _texts(EMAIL, text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "오타 jiwoo @example.org 임",  # space breaks the address
        "이메일 아님 문장",
    ],
)
def test_email_negative(text):
    assert _texts(EMAIL, text) == []
