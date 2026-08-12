"""Pytest 부트스트랩.

``backend/``를 ``sys.path``에 넣어 ``core``, ``modules``, ``api``, ``storage``가
pytest와 uvicorn(둘 다 ``backend/``에서 실행) 어디서든 동일하게 import되도록
한다. 이 파일이 ``backend/``에 있으므로 해당 디렉토리가 import 루트가 된다.
"""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
