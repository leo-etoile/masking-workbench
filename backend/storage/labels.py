"""확정 라벨 문서의 영속화.

문서는 ``doc_id``별로 하나의 JSON 파일로 ``backend/data/labels/`` 아래에
저장된다. ``doc_id``는 안전한 파일명으로 정제(sanitize)되므로 labels
디렉토리 밖으로 절대 벗어날 수 없다.

문서 형태::

    {
        "doc_id": str,
        "text": str,
        "labels": [{"start": int, "end": int, "type": str, "text": str}, ...],
        "updated_at": "<iso-8601 문자열>"
    }

저장 → 불러오기 왕복은 무손실이다.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_LABELS_DIR = Path(__file__).resolve().parents[1] / "data" / "labels"

# 단어 문자, 대시, 점, 한글이 아닌 모든 문자는 언더스코어로 치환한다.
_UNSAFE = re.compile(r"[^A-Za-z0-9._가-힣-]")


def _safe_filename(doc_id: str) -> str:
    """임의의 doc_id를 안전한 파일 basename으로 변환한다."""

    safe = _UNSAFE.sub("_", doc_id).strip("._")
    return safe or "untitled"


def _path_for(doc_id: str) -> Path:
    return _LABELS_DIR / f"{_safe_filename(doc_id)}.json"


def save_document(doc_id: str, text: str, labels: List[dict]) -> dict:
    """라벨 문서를 저장하고 저장된 페이로드를 반환한다.

    ``labels``는 ``{start, end, type, text}`` dict의 리스트다. 저장되는
    ``updated_at`` 타임스탬프는 이 함수에서 ISO-8601(UTC)로 생성한다.
    """

    _LABELS_DIR.mkdir(parents=True, exist_ok=True)
    document = {
        "doc_id": doc_id,
        "text": text,
        "labels": [
            {
                "start": int(label["start"]),
                "end": int(label["end"]),
                "type": str(label["type"]),
                "text": str(label.get("text", "")),
            }
            for label in labels
        ],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _path_for(doc_id).write_text(
        json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return document


def load_document(doc_id: str) -> Optional[dict]:
    """id로 라벨 문서를 불러온다. 없으면 ``None``을 반환한다."""

    path = _path_for(doc_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_documents() -> List[dict]:
    """저장된 모든 문서에 대해 ``[{doc_id, updated_at}, ...]``를 반환한다."""

    if not _LABELS_DIR.exists():
        return []
    docs: List[dict] = []
    for path in sorted(_LABELS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        docs.append(
            {"doc_id": data.get("doc_id"), "updated_at": data.get("updated_at")}
        )
    return docs
