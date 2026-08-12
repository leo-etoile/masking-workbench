"""탐지 모듈 자동 탐색(auto-discovery).

레지스트리는 ``modules`` 패키지를 (재귀적으로) 순회하며, 모듈 레벨 ``MODULE`` 객체를
노출하고 그 객체가 :class:`~core.spec.DetectorModule` 프로토콜을 만족하는 모든 하위 모듈을
수집한다. 코어에는 **하드코딩된 모듈 목록이 없다**: ``modules/`` 하위에 ``MODULE`` 객체를
가진 파일을 추가하기만 하면 워크벤치에 자동으로 나타난다.

탐색 규약에 대한 문서는 :mod:`core.spec`를 참고.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, List, Optional

from core.spec import DetectorModule


def _discover() -> Dict[str, DetectorModule]:
    """``modules`` 패키지를 순회하여 {id: module_instance}를 반환한다.

    개별 하위 모듈의 import 오류는 삼켜서, 깨진 파일 하나가 나머지 모듈 로딩을
    막지 못하게 한다. ``MODULE`` 속성이 없는 모듈 파일은 그냥 무시한다.

    호출할 때마다 새로 탐색하므로, 런타임에 추가된 모듈(예: ``modules/``에
    새 파일을 떨어뜨리는 테스트)도 프로세스 재시작 없이 즉시 인식된다.
    """

    import modules as modules_pkg

    found: Dict[str, DetectorModule] = {}
    for module_info in pkgutil.walk_packages(
        modules_pkg.__path__, prefix=modules_pkg.__name__ + "."
    ):
        if module_info.ispkg:
            continue
        try:
            py_module = importlib.import_module(module_info.name)
        except Exception:
            # 깨진 모듈 파일이 나머지 모듈의 탐색을 망가뜨리면 안 된다.
            continue
        candidate = getattr(py_module, "MODULE", None)
        if candidate is None:
            continue
        if not isinstance(candidate, DetectorModule):
            continue
        found[candidate.id] = candidate
    return found


def list_modules() -> List[dict]:
    """탐색된 모든 모듈의 메타데이터를 id 순으로 정렬해 반환한다."""

    modules = _discover()
    return [
        {
            "id": m.id,
            "display_name": m.display_name,
            "requires_external_network": m.requires_external_network,
            "description": m.description,
        }
        for m in sorted(modules.values(), key=lambda m: m.id)
    ]


def get_module(module_id: str) -> Optional[DetectorModule]:
    """주어진 id의 모듈 인스턴스를 반환한다. 없으면 ``None``."""

    return _discover().get(module_id)
