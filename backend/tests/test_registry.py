"""모듈 자동 탐색(discovery) 테스트.

런타임에 완전히 새로운 모듈 파일을 ``modules/``에 떨어뜨리고, 코어 코드
수정 없이 레지스트리가 이를 발견하는지 확인하는 테스트를 포함한다.
"""

import sys
from pathlib import Path

import modules as modules_pkg
from core.registry import get_module, list_modules


def test_lists_builtin_rule_modules():
    ids = {m["id"] for m in list_modules()}
    assert {"rule_rrn", "rule_phone", "rule_date", "rule_email"} <= ids


def test_metadata_shape():
    for meta in list_modules():
        assert set(meta.keys()) == {"id", "display_name", "requires_external_network", "description"}
        assert isinstance(meta["requires_external_network"], bool)


def test_get_module_returns_instance():
    module = get_module("rule_rrn")
    assert module is not None
    assert module.id == "rule_rrn"
    assert get_module("does_not_exist") is None


def test_llm_module_flagged_external():
    module = get_module("llm_prompt")
    assert module is not None
    assert module.requires_external_network is True


def test_new_module_file_is_discovered_without_core_changes():
    modules_dir = Path(modules_pkg.__path__[0])
    new_file = modules_dir / "_tmp_discovery_probe.py"
    module_name = "modules._tmp_discovery_probe"
    new_file.write_text(
        "from core.spec import PIIType, Span\n"
        "class _Probe:\n"
        "    id = 'tmp_probe'\n"
        "    display_name = 'Temp Probe'\n"
        "    requires_external_network = False\n"
        "    description = 'probe'\n"
        "    def detect(self, text):\n"
        "        return []\n"
        "MODULE = _Probe()\n",
        encoding="utf-8",
    )
    try:
        ids = {m["id"] for m in list_modules()}
        assert "tmp_probe" in ids
        assert get_module("tmp_probe") is not None
    finally:
        new_file.unlink()
        sys.modules.pop(module_name, None)
