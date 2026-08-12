"""라벨 저장소 테스트: 무손실 왕복(round-trip)과 목록 조회."""

from pathlib import Path

from storage import labels as labels_store


def test_round_trip_is_lossless(tmp_path, monkeypatch):
    monkeypatch.setattr(labels_store, "_LABELS_DIR", tmp_path)
    labels = [
        {"start": 3, "end": 17, "type": "RRN", "text": "990101-1234567"},
        {"start": 0, "end": 3, "type": "NAME", "text": "홍길동"},
    ]
    saved = labels_store.save_document("doc-1", "홍길동 990101-1234567", labels)
    loaded = labels_store.load_document("doc-1")
    assert loaded == saved
    assert loaded["doc_id"] == "doc-1"
    assert loaded["text"] == "홍길동 990101-1234567"
    assert loaded["labels"] == labels
    assert isinstance(loaded["updated_at"], str)


def test_load_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(labels_store, "_LABELS_DIR", tmp_path)
    assert labels_store.load_document("nope") is None


def test_list_documents(tmp_path, monkeypatch):
    monkeypatch.setattr(labels_store, "_LABELS_DIR", tmp_path)
    labels_store.save_document("a", "text a", [])
    labels_store.save_document("b", "text b", [])
    docs = labels_store.list_documents()
    ids = {d["doc_id"] for d in docs}
    assert ids == {"a", "b"}
    for d in docs:
        assert set(d.keys()) == {"doc_id", "updated_at"}


def test_doc_id_is_sanitized(tmp_path, monkeypatch):
    monkeypatch.setattr(labels_store, "_LABELS_DIR", tmp_path)
    labels_store.save_document("../../evil/../id", "x", [])
    # 저장 파일은 반드시 labels 디렉토리 안에 있어야 한다.
    files = list(Path(tmp_path).glob("*.json"))
    assert len(files) == 1
    assert files[0].parent == Path(tmp_path)
    # 동일한 id로 문서를 다시 조회할 수 있어야 한다.
    assert labels_store.load_document("../../evil/../id") is not None
