"""FastAPI 엔드포인트 테스트 — TestClient로 모든 라우트를 커버한다."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from storage import labels as labels_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(labels_store, "_LABELS_DIR", tmp_path)


def test_get_modules():
    resp = client.get("/api/modules")
    assert resp.status_code == 200
    ids = {m["id"] for m in resp.json()["modules"]}
    assert {"rule_rrn", "rule_phone", "rule_date", "rule_email", "llm_prompt"} <= ids
    for m in resp.json()["modules"]:
        assert set(m.keys()) == {"id", "display_name", "requires_external_network", "description"}


def test_detect_rule_module():
    body = {
        "text": "환자 990101-1234567 내원 010-0000-1234",
        "module_ids": ["rule_rrn", "rule_phone"],
        "synthetic": True,
    }
    resp = client.post("/api/detect", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert "990101-1234567" in [s["text"] for s in data["results"]["rule_rrn"]]
    assert "010-0000-1234" in [s["text"] for s in data["results"]["rule_phone"]]
    assert data["module_errors"] == {}
    assert data["blocked"] == []


def test_detect_blocks_external_when_not_synthetic():
    body = {"text": "some text", "module_ids": ["llm_prompt"], "synthetic": False}
    resp = client.post("/api/detect", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["blocked"] == ["llm_prompt"]
    assert "llm_prompt" not in data["results"]


def test_get_samples():
    resp = client.get("/api/samples")
    assert resp.status_code == 200
    samples = resp.json()["samples"]
    assert len(samples) >= 12
    for s in samples:
        assert set(s.keys()) == {"id", "text", "synthetic"}
        assert s["synthetic"] is True


def test_labels_save_list_get_round_trip():
    body = {
        "doc_id": "api-doc-1",
        "text": "홍길동 990101-1234567",
        "labels": [
            {"start": 0, "end": 3, "type": "NAME", "text": "홍길동"},
            {"start": 4, "end": 18, "type": "RRN", "text": "990101-1234567"},
        ],
    }
    save = client.post("/api/labels", json=body)
    assert save.status_code == 200
    assert save.json() == {"ok": True}

    listing = client.get("/api/labels")
    assert listing.status_code == 200
    docs = listing.json()["documents"]
    assert any(d["doc_id"] == "api-doc-1" for d in docs)

    got = client.get("/api/labels/api-doc-1")
    assert got.status_code == 200
    doc = got.json()
    assert doc["doc_id"] == "api-doc-1"
    assert doc["text"] == "홍길동 990101-1234567"
    assert doc["labels"] == body["labels"]
    assert isinstance(doc["updated_at"], str)


def test_get_missing_label_document_404():
    resp = client.get("/api/labels/nonexistent")
    assert resp.status_code == 404


def test_evaluate():
    body = {
        "labels": [
            {"start": 0, "end": 3, "type": "NAME", "text": "홍길동"},
            {"start": 4, "end": 18, "type": "RRN", "text": "990101-1234567"},
        ],
        "detections": {
            "rule_rrn": [
                {"start": 4, "end": 18, "type": "RRN", "module": "rule_rrn", "text": "990101-1234567"}
            ]
        },
    }
    resp = client.post("/api/evaluate", json=body)
    assert resp.status_code == 200
    metrics = resp.json()["metrics"]["rule_rrn"]
    # 정확한 RRN 탐지 1개, 골드에는 NAME + RRN이 있음.
    # tp=1, fp=0, fn=1 -> precision=1.0, recall=0.5, f1=2/3
    assert metrics["tp"] == 1
    assert metrics["fp"] == 0
    assert metrics["fn"] == 0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0


def test_evaluate_empty_email_detection_ignores_non_email_gold():
    body = {
        "labels": [
            {"start": 0, "end": 3, "type": "NAME", "text": "홍길동"},
            {"start": 4, "end": 17, "type": "EMAIL", "text": "a@example.com"},
            {"start": 18, "end": 31, "type": "PHONE", "text": "010-0000-0000"},
        ],
        "detections": {"rule_email": []},
    }

    response = client.post("/api/evaluate", json=body)

    assert response.status_code == 200
    metrics = response.json()["metrics"]["rule_email"]
    assert metrics["tp"] == 0
    assert metrics["fp"] == 0
    assert metrics["fn"] == 1
